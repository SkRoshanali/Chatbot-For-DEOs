from flask import Flask, render_template, request, jsonify, session, redirect, url_for, send_file
from pymongo import MongoClient
from werkzeug.security import check_password_hash, generate_password_hash
from functools import wraps
from nlp import detect_intent, get_general_response, extract_second_section, extract_threshold, extract_topn
from datetime import datetime, timedelta
import pandas as pd
import pyotp
import qrcode
import pdfplumber
import io
import os
import base64

app = Flask(__name__)
app.secret_key = 'deo_chatbot_secret_key_2024'
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(minutes=15)
app.config['SESSION_REFRESH_EACH_REQUEST'] = False

# ===== MongoDB =====
MONGO_URI = os.environ.get('MONGO_URI', 'mongodb://localhost:27017/')
try:
    client = MongoClient(MONGO_URI, serverSelectionTimeoutMS=5000)
    client.admin.command('ping')
    db = client['deo_chatbot']
    print("[MongoDB] Connected successfully")
except Exception as e:
    print(f"[MongoDB] Connection failed: {e}")
    print("[MongoDB] Make sure MongoDB is running on localhost:27017")
    db = None

# ===== Role-based decorators =====
def login_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if 'user' not in session:
            return redirect(url_for('login'))

        # Check session expiry (15 minutes)
        last_active = session.get('last_active')
        if last_active:
            elapsed = datetime.utcnow() - datetime.fromisoformat(last_active)
            if elapsed > timedelta(minutes=15):
                session.clear()
                return redirect(url_for('login') + '?reason=timeout')

        # Only count page navigations (not API/data calls) toward refresh limit
        is_page_nav = not request.path.startswith('/api/') and not request.path.startswith('/data/')
        refresh_count = session.get('refresh_count', 0)
        if is_page_nav:
            if refresh_count >= 20:  # Increased from 5 to 20
                session.clear()
                return redirect(url_for('login') + '?reason=refresh')
            session['refresh_count'] = refresh_count + 1

        # Update last active timestamp (but NOT for /api/me to avoid timer jumps)
        if request.path != '/api/me':
            session['last_active'] = datetime.utcnow().isoformat()
            session.modified       = True

        return f(*args, **kwargs)
    return decorated

def admin_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if 'user' not in session or session['user'].get('role') not in ('Admin',):
            return jsonify({'success': False, 'message': 'Access denied.'}), 403
        return f(*args, **kwargs)
    return decorated

def deo_or_admin_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if 'user' not in session or session['user'].get('role') not in ('DEO', 'Admin'):
            return jsonify({'success': False, 'message': 'Access denied. DEO or Admin only.'}), 403
        return f(*args, **kwargs)
    return decorated

ROLE_PERMISSIONS = {
    'Admin': ['chat', 'data', 'register', 'export'],
    'DEO':   ['chat', 'data', 'export'],
    'HOD':   ['chat', 'export'],
}

# Return JSON for all errors so fetch() doesn't get HTML
@app.errorhandler(500)
def handle_500(e):
    return jsonify({'success': False, 'message': f'Server error: {str(e)}'}), 500

@app.errorhandler(403)
def handle_403(e):
    return jsonify({'success': False, 'message': 'Access denied.'}), 403

@app.errorhandler(404)
def handle_404(e):
    return jsonify({'success': False, 'message': 'Route not found.'}), 404

# ===== Routes =====
@app.route('/')
def home():
    if 'user' in session:
        return redirect(url_for('chat'))
    return redirect(url_for('login'))

# ===== LOGIN =====
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        data     = request.get_json()
        username = data.get('username')
        password = data.get('password')
        otp      = data.get('otp', '').strip()
        dept     = data.get('department', '')

        user = db.users.find_one({'username': username})

        if not user or not check_password_hash(user['password'], password):
            return jsonify({'success': False, 'message': 'Invalid username or password.'})

        # Verify OTP
        totp = pyotp.TOTP(user['otp_secret'])
        if not totp.verify(otp, valid_window=1):
            return jsonify({'success': False, 'message': 'Invalid OTP. Check Google Authenticator.'})

        session.permanent = True
        session['user'] = {
            'username': user['username'],
            'role':     user['role'],
            'dept':     dept or user['dept']
        }
        session['last_active']   = datetime.utcnow().isoformat()
        session['refresh_count'] = 0
        return jsonify({'success': True})

    return render_template('login.html')

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

@app.route('/chat')
@login_required
def chat():
    return render_template('index.html', role=session['user']['role'], username=session['user']['username'], dept=session['user']['dept'])

# ===== GET QR FOR SINGLE USER =====
@app.route('/setup/qr', methods=['POST'])
def get_user_qr():
    data     = request.get_json()
    if data.get('master') != MASTER_PASSWORD:
        return jsonify({'success': False}), 403
    username = data.get('username')
    u = db.users.find_one({'username': username}, {'_id': 0})
    if not u:
        return jsonify({'success': False, 'message': 'User not found'}), 404

    secret = u.get('otp_secret', '')
    if not secret:
        secret = pyotp.random_base32()
        db.users.update_one({'username': username}, {'$set': {'otp_secret': secret}})

    totp   = pyotp.TOTP(secret)
    uri    = totp.provisioning_uri(name=username, issuer_name='DEO Chatbot')
    img    = qrcode.make(uri)
    buf    = io.BytesIO()
    img.save(buf, format='PNG')
    buf.seek(0)
    qr_b64 = base64.b64encode(buf.getvalue()).decode('utf-8')
    return jsonify({'success': True, 'qr_code': qr_b64})

# ===== SETUP PAGE =====
MASTER_PASSWORD = 'Admin@123'

@app.route('/setup', methods=['GET', 'POST'])
def setup():
    if request.method == 'POST':
        data = request.get_json()
        if data.get('password') != MASTER_PASSWORD:
            return jsonify({'success': False, 'message': 'Wrong master password.'})

        # Return all users with their QR codes
        users = list(db.users.find({}, {'_id': 0, 'password': 0}))
        result = []
        for u in users:
            secret = u.get('otp_secret', '')
            if not secret:
                secret = pyotp.random_base32()
                db.users.update_one({'username': u['username']}, {'$set': {'otp_secret': secret}})
            totp   = pyotp.TOTP(secret)
            uri    = totp.provisioning_uri(name=u['username'], issuer_name='DEO Chatbot')
            img    = qrcode.make(uri)
            buf    = io.BytesIO()
            img.save(buf, format='PNG')
            buf.seek(0)
            qr_b64 = base64.b64encode(buf.getvalue()).decode('utf-8')
            result.append({
                'username': u['username'],
                'role':     u['role'],
                'dept':     u['dept'],
                'qr_code':  qr_b64
            })
        return jsonify({'success': True, 'users': result})

    return render_template('setup.html')

# ===== ADMIN — Register User =====
@app.route('/admin/register', methods=['GET', 'POST'])
@admin_required
def register():
    if request.method == 'POST':
        data     = request.get_json()
        username = data.get('username', '').strip()
        password = data.get('password', '').strip()
        role     = data.get('role', 'DEO')
        dept     = data.get('dept', 'CSE')

        if db.users.find_one({'username': username}):
            return jsonify({'success': False, 'message': 'Username already exists.'})

        secret = pyotp.random_base32()
        db.users.insert_one({
            'username':   username,
            'password':   generate_password_hash(password),
            'role':       role,
            'dept':       dept,
            'otp_secret': secret
        })

        # Generate QR code
        totp     = pyotp.TOTP(secret)
        otp_uri  = totp.provisioning_uri(name=username, issuer_name='DEO Chatbot')
        img      = qrcode.make(otp_uri)
        buf      = io.BytesIO()
        img.save(buf, format='PNG')
        buf.seek(0)
        qr_b64   = base64.b64encode(buf.getvalue()).decode('utf-8')

        return jsonify({'success': True, 'qr_code': qr_b64, 'secret': secret, 'username': username})

    return render_template('register.html')

# ===== Current User Info =====
@app.route('/api/me')
@login_required
def me():
    return jsonify({
        **session['user'],
        'last_active': session.get('last_active', '')
    })

# ===== DB STATUS CHECK (for debugging) =====
@app.route('/api/dbstatus')
@login_required
def db_status():
    try:
        count = db.students.count_documents({})
        return jsonify({'success': True, 'connected': True, 'student_count': count})
    except Exception as e:
        return jsonify({'success': False, 'connected': False, 'error': str(e)})

# ===== ADMIN — List Users =====
@app.route('/admin/users')
@admin_required
def list_users():
    users = list(db.users.find({}, {'_id': 0, 'password': 0, 'otp_secret': 0}))
    return jsonify(users)

# ===== ADMIN — Delete User =====
@app.route('/admin/delete', methods=['POST'])
@admin_required
def delete_user():
    data = request.get_json()
    db.users.delete_one({'username': data.get('username')})
    return jsonify({'success': True})

# ===== Report API =====
SUBJECTS = ['CN', 'SE', 'ADS', 'PDC']

def _subj_data(s, subj):
    return (s.get('subjects') or {}).get(subj, {'attendance': 0, 'internal': 0, 'external': 0})

def _pool(dept, section=None):
    f = {} if dept == 'ALL' else {'department': dept}
    if section:
        f['section'] = section.upper()
    return list(db.students.find(f, {'_id': 0}))

@app.route('/api/report', methods=['POST'])
@login_required
def get_report():
    from collections import defaultdict
    data     = request.get_json()
    query    = data.get('query', '')
    sem_ui   = data.get('semester', '')
    batch_ui = data.get('batch', '')
    dept     = session['user']['dept']

    if query == '__keepalive__':
        return jsonify({'success': True, 'report_type': 'general', 'message': ''})

    intent, sem_nlp, batch_nlp, roll_nlp, section_nlp, subject_nlp, qualifier_nlp = detect_intent(query)
    sem   = sem_nlp   or sem_ui
    batch = batch_nlp or batch_ui
    q_low = query.lower()

    if intent == 'general':
        return jsonify({'success': True, 'report_type': 'general', 'message': get_general_response(query)})

    # ── Student lookup ─────────────────────────────────────────────
    if intent == 'student_lookup' and roll_nlp:
        s = db.students.find_one({'roll': roll_nlp.upper()}, {'_id': 0})
        if not s:
            return jsonify({'success': True, 'report_type': 'empty',
                'message': f'No student found with roll number {roll_nlp.upper()}.'})
        return jsonify({'success': True, 'report_type': 'student_lookup', 'data': s})

    # ── Section lookup ─────────────────────────────────────────────
    if intent == 'section_lookup' and section_nlp:
        sec_students = list(db.students.find({'section': section_nlp.upper()}, {'_id': 0}))
        if not sec_students:
            return jsonify({'success': True, 'report_type': 'empty',
                'message': f'No students found in {section_nlp.upper()}.'})
        return jsonify({'success': True, 'report_type': 'section_lookup',
            'data': sec_students, 'section': section_nlp.upper()})

    # ── Subject + Section ──────────────────────────────────────────
    if intent == 'subject_section_attendance' and subject_nlp:
        sec_filter = {'section': section_nlp.upper()} if section_nlp else {}
        if dept != 'ALL':
            sec_filter['department'] = dept
        pool = list(db.students.find(sec_filter, {'_id': 0}))
        if not pool:
            return jsonify({'success': True, 'report_type': 'empty',
                'message': f'No students found in {section_nlp.upper() if section_nlp else "selected section"}.'})
        subj = subject_nlp.upper()
        rows = []
        for s in pool:
            sd = _subj_data(s, subj)
            rows.append({'roll': s['roll'], 'name': s['name'], 'section': s.get('section', ''),
                'subject': subj, 'attendance': sd.get('attendance', 0),
                'internal': sd.get('internal', 0), 'external': sd.get('external', 0)})
        n = len(rows)
        return jsonify({'success': True, 'report_type': 'subject_section_attendance',
            'subject': subj, 'section': section_nlp.upper() if section_nlp else 'All', 'data': rows,
            'summary': {'count': n,
                'avg_att': round(sum(r['attendance'] for r in rows) / n, 1),
                'avg_int': round(sum(r['internal']   for r in rows) / n, 1),
                'avg_ext': round(sum(r['external']   for r in rows) / n, 1),
                'above_75': sum(1 for r in rows if r['attendance'] >= 75),
                'below_75': sum(1 for r in rows if r['attendance'] < 75)}})

    # ── Subject Filter ─────────────────────────────────────────────
    if intent == 'subject_filter' and subject_nlp:
        sec_filter = {} if dept == 'ALL' else {'department': dept}
        if section_nlp:
            sec_filter['section'] = section_nlp.upper()
        pool = list(db.students.find(sec_filter, {'_id': 0}))
        if not pool:
            return jsonify({'success': True, 'report_type': 'empty', 'message': 'No students found.'})
        subj      = subject_nlp.upper()
        qualifier = qualifier_nlp or 'low'
        fa = any(w in q_low for w in ['attend', 'attendance', 'present', 'absent'])
        fm = any(w in q_low for w in ['mark', 'marks', 'score', 'result', 'internal', 'external', 'grade'])
        focus = 'attendance' if fa and not fm else 'marks' if fm and not fa else 'all'
        rows = []
        for s in pool:
            sd   = _subj_data(s, subj)
            att  = sd.get('attendance', 0)
            int_ = sd.get('internal', 0)
            ext_ = sd.get('external', 0)
            if qualifier == 'low':
                match = (att < 75) if focus == 'attendance' else (ext_ < 40 or int_ < 20) if focus == 'marks' else (att < 75 or ext_ < 40)
            elif qualifier == 'high':
                match = (att >= 85) if focus == 'attendance' else (ext_ >= 60 and int_ >= 30) if focus == 'marks' else (att >= 75 and ext_ >= 60)
            else:
                match = (60 <= att < 85) if focus == 'attendance' else (40 <= ext_ < 60) if focus == 'marks' else (60 <= att < 85 and 40 <= ext_ < 60)
            if match:
                rows.append({'roll': s['roll'], 'name': s['name'], 'section': s.get('section', ''),
                    'subject': subj, 'attendance': att, 'internal': int_, 'external': ext_, 'focus': focus})
        if not rows:
            tier = {'low': 'weak/low', 'high': 'top/excellent', 'average': 'average'}.get(qualifier, qualifier)
            scope = f' in {section_nlp.upper()}' if section_nlp else ''
            return jsonify({'success': True, 'report_type': 'empty',
                'message': f'No {tier} students found for {subj}{scope}.'})
        sk = 'attendance' if focus == 'attendance' else 'external'
        rows.sort(key=lambda r: r[sk], reverse=(qualifier == 'high'))
        return jsonify({'success': True, 'report_type': 'subject_filter', 'subject': subj,
            'qualifier': qualifier, 'focus': focus,
            'section': section_nlp.upper() if section_nlp else 'All',
            'count': len(rows), 'data': rows})

    # ── Section Toppers ────────────────────────────────────────────
    if intent == 'section_toppers' and section_nlp:
        pool = _pool(dept, section_nlp)
        if not pool:
            return jsonify({'success': True, 'report_type': 'empty',
                'message': f'No students in {section_nlp.upper()}.'})
        n = extract_topn(query)
        if subject_nlp:
            subj = subject_nlp.upper()
            pool.sort(key=lambda x: _subj_data(x, subj).get('external', 0), reverse=True)
            top = pool[:n]
            rows = [{'rank': i+1, 'roll': s['roll'], 'name': s['name'],
                'section': s.get('section', ''), 'subject': subj,
                'external': _subj_data(s, subj).get('external', 0),
                'internal': _subj_data(s, subj).get('internal', 0),
                'attendance': _subj_data(s, subj).get('attendance', 0)} for i, s in enumerate(top)]
            return jsonify({'success': True, 'report_type': 'section_toppers',
                'section': section_nlp.upper(), 'subject': subj, 'data': rows})
        else:
            pool.sort(key=lambda x: x.get('cgpa', 0), reverse=True)
            top = pool[:n]
            rows = [{'rank': i+1, 'roll': s['roll'], 'name': s['name'],
                'section': s.get('section', ''), 'cgpa': s.get('cgpa', 0),
                'attendance': s.get('attendance', 0)} for i, s in enumerate(top)]
            return jsonify({'success': True, 'report_type': 'section_toppers',
                'section': section_nlp.upper(), 'subject': None, 'data': rows})

    # ── Section Backlogs ───────────────────────────────────────────
    if intent == 'section_backlogs' and section_nlp:
        pool = _pool(dept, section_nlp)
        import re as _re
        m = _re.search(r'\b(\d+)\b', query)
        threshold = int(m.group(1)) if m else 2
        rows = [s for s in pool if s.get('backlogs', 0) > threshold]
        if not rows:
            return jsonify({'success': True, 'report_type': 'empty',
                'message': f'No students with more than {threshold} backlogs in {section_nlp.upper()}.'})
        return jsonify({'success': True, 'report_type': 'section_backlogs',
            'section': section_nlp.upper(), 'threshold': threshold,
            'count': len(rows), 'data': rows})

    # ── Section Performance Report ─────────────────────────────────
    if intent == 'section_performance' and section_nlp:
        pool = _pool(dept, section_nlp)
        if not pool:
            return jsonify({'success': True, 'report_type': 'empty',
                'message': f'No students in {section_nlp.upper()}.'})
        n = len(pool)
        subj_stats = []
        for subj in SUBJECTS:
            vals_ext = [_subj_data(s, subj).get('external', 0) for s in pool]
            vals_int = [_subj_data(s, subj).get('internal', 0) for s in pool]
            vals_att = [_subj_data(s, subj).get('attendance', 0) for s in pool]
            subj_stats.append({'subject': subj,
                'avg_external': round(sum(vals_ext)/n, 1),
                'avg_internal': round(sum(vals_int)/n, 1),
                'avg_attend':   round(sum(vals_att)/n, 1),
                'pass_rate':    round(sum(1 for v in vals_ext if v >= 40)/n*100, 1),
                'low_attend':   sum(1 for v in vals_att if v < 75)})
        avg_cgpa = round(sum(s.get('cgpa', 0) for s in pool)/n, 2)
        avg_att  = round(sum(s.get('attendance', 0) for s in pool)/n, 1)
        return jsonify({'success': True, 'report_type': 'section_performance',
            'section': section_nlp.upper(), 'count': n,
            'avg_cgpa': avg_cgpa, 'avg_attendance': avg_att,
            'subjects': subj_stats, 'data': pool})

    # ── Section CGPA Filter ────────────────────────────────────────
    if intent == 'section_cgpa_filter' and section_nlp:
        pool = _pool(dept, section_nlp)
        threshold = extract_threshold(query) or 8.5
        above = 'above' in q_low or 'greater' in q_low or 'more than' in q_low or 'over' in q_low
        rows = [s for s in pool if (s.get('cgpa', 0) >= threshold if above else s.get('cgpa', 0) < threshold)]
        direction = 'above' if above else 'below'
        if not rows:
            return jsonify({'success': True, 'report_type': 'empty',
                'message': f'No students with CGPA {direction} {threshold} in {section_nlp.upper()}.'})
        rows.sort(key=lambda x: x.get('cgpa', 0), reverse=above)
        return jsonify({'success': True, 'report_type': 'section_cgpa_filter',
            'section': section_nlp.upper(), 'threshold': threshold,
            'direction': direction, 'count': len(rows), 'data': rows})

    # ── Compare Sections ───────────────────────────────────────────
    if intent == 'compare_sections':
        sec2 = extract_second_section(query)
        sec1 = section_nlp
        if not sec1 or not sec2:
            return jsonify({'success': True, 'report_type': 'empty',
                'message': 'Please specify two sections to compare (e.g. SEC-1 and SEC-2).'})
        pool1 = _pool(dept, sec1)
        pool2 = _pool(dept, sec2)
        def sec_summary(pool, sec, subj=None):
            if not pool:
                return {'section': sec, 'count': 0}
            n = len(pool)
            if subj:
                vals_ext = [_subj_data(s, subj).get('external', 0) for s in pool]
                vals_int = [_subj_data(s, subj).get('internal', 0) for s in pool]
                vals_att = [_subj_data(s, subj).get('attendance', 0) for s in pool]
                return {'section': sec, 'count': n, 'subject': subj,
                    'avg_external': round(sum(vals_ext)/n, 1),
                    'avg_internal': round(sum(vals_int)/n, 1),
                    'avg_attend':   round(sum(vals_att)/n, 1),
                    'pass_rate':    round(sum(1 for v in vals_ext if v >= 40)/n*100, 1)}
            return {'section': sec, 'count': n,
                'avg_cgpa':    round(sum(s.get('cgpa', 0) for s in pool)/n, 2),
                'avg_attend':  round(sum(s.get('attendance', 0) for s in pool)/n, 1),
                'avg_external': round(sum(s.get('external', 0) for s in pool)/n, 1)}
        subj = subject_nlp.upper() if subject_nlp else None
        return jsonify({'success': True, 'report_type': 'compare_sections',
            'subject': subj,
            'sec1': sec_summary(pool1, sec1.upper(), subj),
            'sec2': sec_summary(pool2, sec2.upper(), subj)})

    # ── Subject Failure Rate ───────────────────────────────────────
    if intent == 'subject_failure_rate':
        all_s = _pool(dept)
        if not all_s:
            return jsonify({'success': True, 'report_type': 'empty', 'message': 'No students found.'})
        stats = []
        for subj in SUBJECTS:
            vals_ext = [_subj_data(s, subj).get('external', 0) for s in all_s]
            vals_int = [_subj_data(s, subj).get('internal', 0) for s in all_s]
            n = len(vals_ext)
            fail_count = sum(1 for v in vals_ext if v < 40)
            stats.append({'subject': subj, 'count': n,
                'fail_count':   fail_count,
                'fail_rate':    round(fail_count/n*100, 1),
                'avg_external': round(sum(vals_ext)/n, 1),
                'avg_internal': round(sum(vals_int)/n, 1)})
        stats.sort(key=lambda x: x['fail_rate'], reverse=True)
        return jsonify({'success': True, 'report_type': 'subject_failure_rate', 'data': stats})

    # ── Marks Distribution ─────────────────────────────────────────
    if intent == 'marks_distribution' and subject_nlp:
        sec_filter = {'section': section_nlp.upper()} if section_nlp else {}
        if dept != 'ALL':
            sec_filter['department'] = dept
        pool = list(db.students.find(sec_filter, {'_id': 0}))
        if not pool:
            return jsonify({'success': True, 'report_type': 'empty', 'message': 'No students found.'})
        subj = subject_nlp.upper()
        buckets = {'0-39': 0, '40-49': 0, '50-59': 0, '60-69': 0, '70-79': 0, '80-89': 0, '90-100': 0}
        rows = []
        for s in pool:
            sd  = _subj_data(s, subj)
            ext = sd.get('external', 0)
            rows.append({'roll': s['roll'], 'name': s['name'], 'section': s.get('section', ''),
                'external': ext, 'internal': sd.get('internal', 0), 'attendance': sd.get('attendance', 0)})
            if ext < 40:   buckets['0-39']   += 1
            elif ext < 50: buckets['40-49']  += 1
            elif ext < 60: buckets['50-59']  += 1
            elif ext < 70: buckets['60-69']  += 1
            elif ext < 80: buckets['70-79']  += 1
            elif ext < 90: buckets['80-89']  += 1
            else:          buckets['90-100'] += 1
        n = len(rows)
        return jsonify({'success': True, 'report_type': 'marks_distribution',
            'subject': subj, 'section': section_nlp.upper() if section_nlp else 'All',
            'count': n, 'buckets': buckets, 'data': rows})

    # ── Subject Trend Across Sections ─────────────────────────────
    if intent == 'subject_trend' and subject_nlp:
        all_s = _pool(dept)
        subj  = subject_nlp.upper()
        sec_groups = {}
        for s in all_s:
            sec = s.get('section', '?')
            sec_groups.setdefault(sec, []).append(s)
        trend = []
        for sec in sorted(sec_groups.keys(), key=lambda x: int(x.replace('SEC-','')) if x.replace('SEC-','').isdigit() else 99):
            grp = sec_groups[sec]
            n   = len(grp)
            vals_ext = [_subj_data(s, subj).get('external', 0) for s in grp]
            vals_att = [_subj_data(s, subj).get('attendance', 0) for s in grp]
            trend.append({'section': sec, 'count': n,
                'avg_external': round(sum(vals_ext)/n, 1),
                'avg_attend':   round(sum(vals_att)/n, 1),
                'pass_rate':    round(sum(1 for v in vals_ext if v >= 40)/n*100, 1)})
        return jsonify({'success': True, 'report_type': 'subject_trend',
            'subject': subj, 'data': trend})

    # ── Perfect Attendance ─────────────────────────────────────────
    if intent == 'perfect_attendance':
        all_s = _pool(dept)
        rows  = [s for s in all_s if s.get('attendance', 0) >= 100]
        if not rows:
            return jsonify({'success': True, 'report_type': 'empty',
                'message': 'No students with perfect (100%) attendance found.'})
        return jsonify({'success': True, 'report_type': 'perfect_attendance',
            'count': len(rows), 'data': rows})

    # ── Section Stats ──────────────────────────────────────────────
    if intent == 'section_stats':
        all_s = _pool(dept)
        sec_groups = {}
        for s in all_s:
            sec = s.get('section', '?')
            sec_groups.setdefault(sec, []).append(s)
        stats = []
        for sec in sorted(sec_groups.keys(), key=lambda x: int(x.replace('SEC-','')) if x.replace('SEC-','').isdigit() else 99):
            grp = sec_groups[sec]
            n   = len(grp)
            stats.append({'section': sec, 'count': n,
                'avg_cgpa':    round(sum(s.get('cgpa', 0) for s in grp)/n, 2),
                'avg_attend':  round(sum(s.get('attendance', 0) for s in grp)/n, 1),
                'above_75':    sum(1 for s in grp if s.get('attendance', 0) >= 75),
                'below_75':    sum(1 for s in grp if s.get('attendance', 0) < 75)})
        return jsonify({'success': True, 'report_type': 'section_stats', 'data': stats})

    # ── Department Summary ─────────────────────────────────────────
    if intent == 'dept_summary':
        all_s = _pool(dept)
        if not all_s:
            return jsonify({'success': True, 'report_type': 'empty', 'message': 'No students found.'})
        n = len(all_s)
        subj_stats = []
        for subj in SUBJECTS:
            vals_ext = [_subj_data(s, subj).get('external', 0) for s in all_s]
            vals_att = [_subj_data(s, subj).get('attendance', 0) for s in all_s]
            subj_stats.append({'subject': subj,
                'avg_external': round(sum(vals_ext)/n, 1),
                'avg_attend':   round(sum(vals_att)/n, 1),
                'pass_rate':    round(sum(1 for v in vals_ext if v >= 40)/n*100, 1)})
        return jsonify({'success': True, 'report_type': 'dept_summary',
            'count': n,
            'avg_cgpa':    round(sum(s.get('cgpa', 0) for s in all_s)/n, 2),
            'avg_attend':  round(sum(s.get('attendance', 0) for s in all_s)/n, 1),
            'avg_internal': round(sum(s.get('internal', 0) for s in all_s)/n, 1),
            'avg_external': round(sum(s.get('external', 0) for s in all_s)/n, 1),
            'subjects': subj_stats})

    # ── Predict Backlog ────────────────────────────────────────────
    if intent == 'predict_backlog':
        sec_filter = {} if dept == 'ALL' else {'department': dept}
        if section_nlp:
            sec_filter['section'] = section_nlp.upper()
        pool = list(db.students.find(sec_filter, {'_id': 0}))
        subj = subject_nlp.upper() if subject_nlp else None
        rows = []
        for s in pool:
            if subj:
                sd  = _subj_data(s, subj)
                att = sd.get('attendance', 0)
                ext = sd.get('external', 0)
                int_ = sd.get('internal', 0)
                risk_score = (1 if att < 75 else 0) + (1 if ext < 50 else 0) + (1 if int_ < 25 else 0)
                if risk_score >= 2:
                    rows.append({'roll': s['roll'], 'name': s['name'], 'section': s.get('section', ''),
                        'subject': subj, 'attendance': att, 'internal': int_, 'external': ext,
                        'risk_score': risk_score})
            else:
                att  = s.get('attendance', 0)
                cgpa = s.get('cgpa', 0)
                blg  = s.get('backlogs', 0)
                risk_score = (1 if att < 75 else 0) + (1 if cgpa < 6 else 0) + (1 if blg > 0 else 0)
                if risk_score >= 2:
                    rows.append({'roll': s['roll'], 'name': s['name'], 'section': s.get('section', ''),
                        'cgpa': cgpa, 'attendance': att, 'backlogs': blg, 'risk_score': risk_score})
        rows.sort(key=lambda x: x['risk_score'], reverse=True)
        if not rows:
            return jsonify({'success': True, 'report_type': 'empty',
                'message': 'No students identified as backlog risk.'})
        return jsonify({'success': True, 'report_type': 'predict_backlog',
            'subject': subj, 'section': section_nlp.upper() if section_nlp else 'All',
            'count': len(rows), 'data': rows})

    # ── Internal Filter ────────────────────────────────────────────
    if intent == 'internal_filter' and subject_nlp:
        sec_filter = {} if dept == 'ALL' else {'department': dept}
        if section_nlp:
            sec_filter['section'] = section_nlp.upper()
        pool = list(db.students.find(sec_filter, {'_id': 0}))
        subj      = subject_nlp.upper()
        threshold = extract_threshold(query) or 20
        above     = any(w in q_low for w in ['above', 'more than', 'greater', 'over'])
        rows = []
        for s in pool:
            int_ = _subj_data(s, subj).get('internal', 0)
            if (int_ > threshold if above else int_ < threshold):
                rows.append({'roll': s['roll'], 'name': s['name'], 'section': s.get('section', ''),
                    'subject': subj, 'internal': int_,
                    'external': _subj_data(s, subj).get('external', 0),
                    'attendance': _subj_data(s, subj).get('attendance', 0)})
        direction = 'above' if above else 'below'
        if not rows:
            return jsonify({'success': True, 'report_type': 'empty',
                'message': f'No students scoring {direction} {threshold} in {subj} internals.'})
        rows.sort(key=lambda x: x['internal'], reverse=above)
        return jsonify({'success': True, 'report_type': 'internal_filter',
            'subject': subj, 'threshold': threshold, 'direction': direction,
            'count': len(rows), 'data': rows})

    # ── Standard filters (uses section_nlp if present) ────────────
    filters = {} if dept == 'ALL' else {'department': dept}
    if sem:         filters['semester'] = str(sem)
    if batch:       filters['batch']    = batch
    if section_nlp: filters['section']  = section_nlp.upper()

    students = list(db.students.find(filters, {'_id': 0}))

    if (sem or batch) and not students:
        label = f'Semester {sem}' if sem else f'Batch {batch}'
        return jsonify({'success': True, 'report_type': 'empty',
            'message': f'No students found for {label}.'})

    if intent == 'average_marks':
        if not students:
            return jsonify({'success': True, 'report_type': 'empty', 'message': 'No students found.'})
        count = len(students)
        return jsonify({'success': True, 'report_type': 'average_marks', 'data': students,
            'averages': {'semester': f'Semester {sem}' if sem else 'All Semesters', 'count': count,
                'internal':   round(sum(s.get('internal', 0)   for s in students)/count, 1),
                'external':   round(sum(s.get('external', 0)   for s in students)/count, 1),
                'cgpa':       round(sum(s.get('cgpa', 0)       for s in students)/count, 2),
                'attendance': round(sum(s.get('attendance', 0) for s in students)/count, 1)}})

    if intent == 'subject_performance':
        if not students:
            return jsonify({'success': True, 'report_type': 'empty', 'message': 'No students found.'})
        perf = []
        for subj in SUBJECTS:
            vals_int = [_subj_data(s, subj).get('internal', 0)   for s in students if 'subjects' in s]
            vals_ext = [_subj_data(s, subj).get('external', 0)   for s in students if 'subjects' in s]
            vals_att = [_subj_data(s, subj).get('attendance', 0) for s in students if 'subjects' in s]
            if not vals_int: continue
            n = len(vals_int)
            perf.append({'subject': subj, 'count': n,
                'avg_internal': round(sum(vals_int)/n, 1),
                'avg_external': round(sum(vals_ext)/n, 1),
                'avg_attend':   round(sum(vals_att)/n, 1),
                'pass_rate':    round(sum(1 for v in vals_ext if v >= 40)/n*100, 1),
                'low_attend':   sum(1 for v in vals_att if v < 75)})
        return jsonify({'success': True, 'report_type': 'subject_performance', 'data': perf})

    if intent == 'subject_attendance':
        if not students:
            return jsonify({'success': True, 'report_type': 'empty', 'message': 'No students found.'})
        result = []
        for subj in SUBJECTS:
            vals = [_subj_data(s, subj).get('attendance', 0) for s in students if 'subjects' in s]
            if not vals: continue
            n = len(vals)
            result.append({'subject': subj, 'count': n,
                'avg_attend': round(sum(vals)/n, 1),
                'above_75':   sum(1 for v in vals if v >= 75),
                'below_75':   sum(1 for v in vals if v < 75)})
        return jsonify({'success': True, 'report_type': 'subject_attendance', 'data': result, 'students': students})

    if intent == 'section_attendance':
        all_s = list(db.students.find({} if dept == 'ALL' else {'department': dept}, {'_id': 0}))
        sec_groups = {}
        for s in all_s:
            sec_groups.setdefault(s.get('section', '?'), []).append(s)
        sections = []
        for sec in sorted(sec_groups.keys(), key=lambda x: int(x.replace('SEC-','')) if x.replace('SEC-','').isdigit() else 99):
            grp = sec_groups[sec]; count = len(grp)
            sections.append({'section': sec, 'total': count,
                'avg_attend': round(sum(x.get('attendance', 0) for x in grp)/count, 1),
                'above_75':   sum(1 for x in grp if x.get('attendance', 0) >= 75),
                'below_75':   sum(1 for x in grp if x.get('attendance', 0) < 75)})
        return jsonify({'success': True, 'report_type': 'section_attendance', 'data': sections})

    if intent == 'department_attendance':
        all_s = list(db.students.find({}, {'_id': 0}))
        dept_groups = {}
        for s in all_s:
            dept_groups.setdefault(s.get('department', '?'), []).append(s)
        result = []
        for d in sorted(dept_groups.keys()):
            grp = dept_groups[d]; count = len(grp)
            result.append({'department': d, 'count': count,
                'avg_attend': round(sum(x.get('attendance', 0) for x in grp)/count, 1),
                'below_75':   sum(1 for x in grp if x.get('attendance', 0) < 75),
                'above_85':   sum(1 for x in grp if x.get('attendance', 0) >= 85)})
        return jsonify({'success': True, 'report_type': 'department_attendance', 'data': result})

    if intent == 'cgpa_distribution':
        if not students:
            return jsonify({'success': True, 'report_type': 'empty', 'message': 'No students found.'})
        dept_groups = {}
        for s in students:
            dept_groups.setdefault(s.get('department', '?'), []).append(s)
        dist = []
        for d in sorted(dept_groups.keys()):
            grp = dept_groups[d]; count = len(grp)
            dist.append({'department': d, 'count': count,
                'avg_cgpa': round(sum(x.get('cgpa', 0) for x in grp)/count, 2),
                'above_8':  sum(1 for x in grp if x.get('cgpa', 0) >= 8),
                'above_6':  sum(1 for x in grp if 6 <= x.get('cgpa', 0) < 8),
                'below_6':  sum(1 for x in grp if x.get('cgpa', 0) < 6)})
        return jsonify({'success': True, 'report_type': 'cgpa_distribution', 'data': dist})

    if intent == 'pending_completions':
        pending = [s for s in students if s.get('backlogs', 0) > 0]
        if not pending:
            return jsonify({'success': True, 'report_type': 'empty',
                'message': 'No students with pending course completions.'})
        return jsonify({'success': True, 'report_type': 'pending_completions', 'data': pending})

    if intent == 'low_attendance':
        students = [s for s in students if s.get('attendance', 100) < 75]
    elif intent == 'backlogs':
        students = [s for s in students if s.get('backlogs', 0) > 0]
    elif intent == 'repeated_subjects':
        students = [s for s in students if s.get('backlogs', 0) > 0]
    elif intent == 'toppers':
        students = sorted(students, key=lambda x: x.get('cgpa', 0), reverse=True)[:10]
    elif intent == 'rankings':
        students = sorted(students, key=lambda x: x.get('cgpa', 0), reverse=True)
    elif intent == 'risk':
        students = [s for s in students if s.get('cgpa', 10) < 6 or s.get('backlogs', 0) >= 2 or s.get('attendance', 100) < 65]
    elif intent == 'top_performers':
        students = [s for s in students if s.get('cgpa', 0) >= 8.5 and s.get('attendance', 0) >= 85]

    if not students:
        label = f'Semester {sem}' if sem else 'selected filters'
        return jsonify({'success': True, 'report_type': 'empty',
            'message': f'No students found for {label}.'})

    return jsonify({'success': True, 'report_type': intent, 'data': students, 'semester': sem})



# ===== Export API =====
@app.route('/api/export', methods=['POST'])
@login_required
def export_report():
    data        = request.get_json()
    students    = data.get('data', [])
    fmt         = data.get('format', 'csv')
    report_type = data.get('report_type', 'report')

    if not students:
        return jsonify({'success': False, 'message': 'No data'}), 400

    df = pd.DataFrame(students)

    if fmt == 'csv':
        output = io.StringIO()
        df.to_csv(output, index=False)
        output.seek(0)
        return send_file(io.BytesIO(output.getvalue().encode()), mimetype='text/csv',
                         as_attachment=True, download_name=f'{report_type}.csv')
    elif fmt == 'excel':
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            df.to_excel(writer, index=False, sheet_name='Report')
        output.seek(0)
        return send_file(output,
                         mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
                         as_attachment=True, download_name=f'{report_type}.xlsx')

    return jsonify({'success': False}), 400

# ===== DATA MANAGEMENT PAGE =====
@app.route('/data')
@login_required
def data_page():
    role = session['user']['role']
    if role not in ('DEO', 'Admin'):
        return redirect(url_for('chat'))
    return render_template('data.html', role=role, username=session['user']['username'])

# ===== GET ALL STUDENTS =====
@app.route('/data/students', methods=['GET'])
@login_required
def get_students():
    dept     = session['user']['dept']
    search   = request.args.get('search', '')
    filters  = {} if dept == 'ALL' else {'department': dept}
    if search:
        filters['$or'] = [
            {'name': {'$regex': search, '$options': 'i'}},
            {'roll': {'$regex': search, '$options': 'i'}}
        ]
    students = list(db.students.find(filters, {'_id': 0}))
    return jsonify({'success': True, 'data': students})

# ===== ADD STUDENT =====
@app.route('/data/add', methods=['POST'])
@login_required
def add_student():
    if session['user']['role'] not in ('DEO', 'Admin'):
        return jsonify({'success': False, 'message': 'Access denied.'}), 403
    s = request.get_json()
    if db.students.find_one({'roll': s.get('roll')}):
        return jsonify({'success': False, 'message': 'Roll number already exists.'})
    internal = int(s.get('internal', 0))
    external = int(s.get('external', 0))
    attendance = int(s.get('attendance', 0))

    def sv(key, fallback):
        v = s.get(key, '')
        try: return int(float(v)) if str(v).strip() not in ('', 'None') else fallback
        except: return fallback

    db.students.insert_one({
        'roll':       s.get('roll','').upper(),
        'name':       s.get('name',''),
        'section':    s.get('section','SEC-1'),
        'department': s.get('department','CSE'),
        'semester':   s.get('semester','1'),
        'batch':      s.get('batch',''),
        'cgpa':       float(s.get('cgpa', 0)),
        'attendance': attendance,
        'backlogs':   int(s.get('backlogs', 0)),
        'internal':   internal,
        'external':   external,
        'subjects': {
            'CN':  {'attendance': sv('cn_att',attendance),  'internal': sv('cn_int',internal),  'external': sv('cn_ext',external)},
            'SE':  {'attendance': sv('se_att',attendance),  'internal': sv('se_int',internal),  'external': sv('se_ext',external)},
            'ADS': {'attendance': sv('ads_att',attendance), 'internal': sv('ads_int',internal), 'external': sv('ads_ext',external)},
            'PDC': {'attendance': sv('pdc_att',attendance), 'internal': sv('pdc_int',internal), 'external': sv('pdc_ext',external)},
        }
    })
    return jsonify({'success': True, 'message': 'Student added successfully.'})

# ===== UPDATE STUDENT =====
@app.route('/data/update', methods=['POST'])
@login_required
def update_student():
    if session['user']['role'] not in ('DEO', 'Admin'):
        return jsonify({'success': False, 'message': 'Access denied.'}), 403
    s    = request.get_json()
    roll = s.pop('roll', None)
    if not roll:
        return jsonify({'success': False, 'message': 'Roll number required.'})
    internal   = int(s.get('internal', 0))
    external   = int(s.get('external', 0))
    attendance = int(s.get('attendance', 0))

    def sv(key, fallback):
        v = s.get(key, '')
        try: return int(float(v)) if str(v).strip() not in ('', 'None') else fallback
        except: return fallback

    db.students.update_one({'roll': roll}, {'$set': {
        'name':       s.get('name',''),
        'section':    s.get('section','SEC-1'),
        'department': s.get('department','CSE'),
        'semester':   s.get('semester','1'),
        'batch':      s.get('batch',''),
        'cgpa':       float(s.get('cgpa', 0)),
        'attendance': attendance,
        'backlogs':   int(s.get('backlogs', 0)),
        'internal':   internal,
        'external':   external,
        'subjects': {
            'CN':  {'attendance': sv('cn_att',attendance),  'internal': sv('cn_int',internal),  'external': sv('cn_ext',external)},
            'SE':  {'attendance': sv('se_att',attendance),  'internal': sv('se_int',internal),  'external': sv('se_ext',external)},
            'ADS': {'attendance': sv('ads_att',attendance), 'internal': sv('ads_int',internal), 'external': sv('ads_ext',external)},
            'PDC': {'attendance': sv('pdc_att',attendance), 'internal': sv('pdc_int',internal), 'external': sv('pdc_ext',external)},
        }
    }})
    return jsonify({'success': True, 'message': 'Student updated successfully.'})

# ===== DELETE STUDENT =====
@app.route('/data/delete', methods=['POST'])
@login_required
def delete_student():
    if session['user']['role'] not in ('DEO', 'Admin'):
        return jsonify({'success': False, 'message': 'Access denied.'}), 403
    roll = request.get_json().get('roll')
    db.students.delete_one({'roll': roll})
    return jsonify({'success': True, 'message': 'Student deleted.'})

# ===== UPLOAD FILE =====
@app.route('/data/upload', methods=['POST'])
@login_required
def upload_file():
    if session['user']['role'] not in ('DEO', 'Admin'):
        return jsonify({'success': False, 'message': 'Access denied.'}), 403
    if 'file' not in request.files:
        return jsonify({'success': False, 'message': 'No file provided.'})

    file  = request.files['file']
    fname = file.filename.lower()
    print(f"[UPLOAD] Received file: {fname}")

    if db is None:
        return jsonify({'success': False, 'message': 'Database not connected. Start MongoDB first.'})

    def safe_str(val, default=''):
        s = str(val).strip()
        return default if s.lower() in ('nan', 'none', '') else s

    def safe_float(val, default=0.0):
        try:
            s = str(val).strip()
            return float(s) if s.lower() not in ('nan', 'none', '') else default
        except:
            return default

    def safe_int(val, default=0):
        try:
            s = str(val).strip()
            return int(float(s)) if s.lower() not in ('nan', 'none', '') else default
        except:
            return default

    try:
        if fname.endswith('.csv'):
            df = pd.read_csv(file)
        elif fname.endswith('.xlsx') or fname.endswith('.xls'):
            xl = pd.ExcelFile(file, engine='openpyxl')
            df = xl.parse(xl.sheet_names[0])
        elif fname.endswith('.pdf'):
            rows = []
            headers = []
            with pdfplumber.open(file) as pdf:
                for page in pdf.pages:
                    for table in page.extract_tables():
                        if not headers:
                            headers = [str(h).lower().strip() for h in table[0]]
                        for row in table[1:]:
                            rows.append(dict(zip(headers, row)))
            df = pd.DataFrame(rows)
        else:
            return jsonify({'success': False, 'message': 'Unsupported format. Use .xlsx, .csv or .pdf'})

        # Normalize column names
        df.columns = [
            str(c).lower().strip().replace(' ', '_').replace('\n', '').replace('\r', '')
            for c in df.columns
        ]

        # Handle alternate column names
        aliases = {
            'dept': 'department', 'dep': 'department',
            'sem': 'semester',
            'roll_no': 'roll', 'roll_number': 'roll', 'rollno': 'roll',
            'student_name': 'name', 'full_name': 'name',
            'gpa': 'cgpa',
            'attend': 'attendance',
            'backlog': 'backlogs',
            'int_marks': 'internal', 'internal_marks': 'internal',
            'ext_marks': 'external', 'external_marks': 'external',
            'sec': 'section',
        }
        df.rename(columns=aliases, inplace=True)

        print(f"[UPLOAD] Columns: {list(df.columns)}, Rows: {len(df)}")

        df.dropna(how='all', inplace=True)

        if 'roll' not in df.columns or 'name' not in df.columns:
            return jsonify({
                'success': False,
                'message': f'Missing "roll" or "name" column. Found columns: {list(df.columns)}'
            })

        inserted = updated = skipped = 0

        for _, row in df.iterrows():
            roll = safe_str(row.get('roll', ''), '').upper()
            if not roll:
                skipped += 1
                continue

            doc = {
                'roll':       roll,
                'name':       safe_str(row.get('name', ''), 'Unknown'),
                'section':    safe_str(row.get('section', ''), 'SEC-1').upper(),
                'department': safe_str(row.get('department', ''), 'CSE').upper(),
                'semester':   str(safe_int(row.get('semester', 1), 1)),
                'batch':      safe_str(row.get('batch', ''), ''),
                'cgpa':       safe_float(row.get('cgpa', 0)),
                'attendance': safe_int(row.get('attendance', 0)),
                'backlogs':   safe_int(row.get('backlogs', 0)),
                'internal':   safe_int(row.get('internal', 0)),
                'external':   safe_int(row.get('external', 0)),
                'subjects': {
                    'CN':  {
                        'attendance': safe_int(row.get('cn_attendance', row.get('attendance', 0))),
                        'internal':   safe_int(row.get('cn_internal',   row.get('internal', 0))),
                        'external':   safe_int(row.get('cn_external',   row.get('external', 0))),
                    },
                    'SE':  {
                        'attendance': safe_int(row.get('se_attendance', row.get('attendance', 0))),
                        'internal':   safe_int(row.get('se_internal',   row.get('internal', 0))),
                        'external':   safe_int(row.get('se_external',   row.get('external', 0))),
                    },
                    'ADS': {
                        'attendance': safe_int(row.get('ads_attendance', row.get('attendance', 0))),
                        'internal':   safe_int(row.get('ads_internal',   row.get('internal', 0))),
                        'external':   safe_int(row.get('ads_external',   row.get('external', 0))),
                    },
                    'PDC': {
                        'attendance': safe_int(row.get('pdc_attendance', row.get('attendance', 0))),
                        'internal':   safe_int(row.get('pdc_internal',   row.get('internal', 0))),
                        'external':   safe_int(row.get('pdc_external',   row.get('external', 0))),
                    },
                }
            }

            if db.students.find_one({'roll': roll}):
                db.students.update_one({'roll': roll}, {'$set': doc})
                updated += 1
            else:
                db.students.insert_one(doc)
                inserted += 1

        print(f"[UPLOAD] Done — Inserted:{inserted} Updated:{updated} Skipped:{skipped}")
        return jsonify({
            'success': True,
            'message': f'✅ Done! {inserted} added, {updated} updated, {skipped} skipped.'
        })

    except Exception as e:
        import traceback
        print(f"[UPLOAD] ERROR:\n{traceback.format_exc()}")
        return jsonify({'success': False, 'message': f'Error: {str(e)}'})


# ===== DOWNLOAD TEMPLATE =====
@app.route('/data/template')
@login_required
def download_template():
    df = pd.DataFrame([{
        'roll': '231FA00001', 'name': 'Student Name', 'section': 'SEC-1',
        'department': 'CSE', 'semester': '3', 'batch': '2023-27', 'cgpa': 8.5,
        'attendance': 85, 'backlogs': 0, 'internal': 42, 'external': 70,
        'cn_attendance': 85, 'cn_internal': 42, 'cn_external': 70,
        'se_attendance': 80, 'se_internal': 40, 'se_external': 68,
        'ads_attendance': 88, 'ads_internal': 44, 'ads_external': 72,
        'pdc_attendance': 82, 'pdc_internal': 41, 'pdc_external': 69,
    }])
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df.to_excel(writer, index=False, sheet_name='Students')
    output.seek(0)
    return send_file(output,
                     mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
                     as_attachment=True, download_name='student_template.xlsx')

# ===== Seed Data =====
import random

FIRST_NAMES = [
    'Aarav','Aditya','Akash','Ajay','Ananya','Anjali','Arjun','Aryan','Bhavya','Chetan',
    'Deepak','Divya','Farhan','Gayatri','Harish','Ishaan','Jaya','Kiran','Kavitha','Lakshmi',
    'Manish','Meera','Nisha','Nikhil','Pooja','Priya','Rahul','Ravi','Rohan','Rohini',
    'Sachin','Sandeep','Sneha','Srinivas','Suresh','Swathi','Tanvi','Uday','Vikram','Vishal',
    'Yamini','Yash','Zara','Sai','Naveen','Mounika','Lokesh','Keerthi','Jyothi','Harsha',
    'Gopal','Faisal','Eswar','Durga','Chandra','Bhanu','Arun','Amrutha','Abhishek','Abhinav',
]
LAST_NAMES = [
    'Sharma','Reddy','Kumar','Patel','Singh','Nair','Iyer','Gupta','Joshi','Rao',
    'Verma','Pillai','Menon','Babu','Naidu','Yadav','Mishra','Tiwari','Pandey','Shetty',
]

def make_student(idx, section_num):
    roll = f'231FA{idx:05d}'
    random.seed(idx)
    fname = FIRST_NAMES[idx % len(FIRST_NAMES)]
    lname = LAST_NAMES[idx % len(LAST_NAMES)]
    name  = f'{fname} {lname}'

    base_attend = random.randint(55, 98)
    base_int    = random.randint(20, 50)
    base_ext    = random.randint(30, 100)
    backlogs    = 0 if base_ext >= 40 and base_int >= 20 else random.randint(1, 3)

    def vary(val, lo, hi):
        return max(lo, min(hi, val + random.randint(-8, 8)))

    subjects = {
        'CN':  {'attendance': vary(base_attend,0,100), 'internal': vary(base_int,0,50), 'external': vary(base_ext,0,100)},
        'SE':  {'attendance': vary(base_attend,0,100), 'internal': vary(base_int,0,50), 'external': vary(base_ext,0,100)},
        'ADS': {'attendance': vary(base_attend,0,100), 'internal': vary(base_int,0,50), 'external': vary(base_ext,0,100)},
        'PDC': {'attendance': vary(base_attend,0,100), 'internal': vary(base_int,0,50), 'external': vary(base_ext,0,100)},
    }

    avg_ext = sum(s['external'] for s in subjects.values()) / 4
    avg_int = sum(s['internal'] for s in subjects.values()) / 4
    cgpa    = round(min(10, (avg_int/50)*4 + (avg_ext/100)*6), 2)

    return {
        'roll':       roll,
        'name':       name,
        'section':    f'SEC-{section_num}',
        'department': 'CSE',
        'semester':   '3',
        'batch':      '2023-27',
        'cgpa':       cgpa,
        'attendance': base_attend,
        'backlogs':   backlogs,
        'internal':   base_int,
        'external':   base_ext,
        'subjects':   subjects,
    }

def seed_data():
    if db.users.count_documents({}) == 0:
        users = [
            {'username': 'deo_cse', 'password': 'cse123',   'role': 'DEO',   'dept': 'CSE'},
            {'username': 'hod_cse', 'password': 'hod123',   'role': 'HOD',   'dept': 'CSE'},
            {'username': 'admin',   'password': 'admin123', 'role': 'Admin', 'dept': 'ALL'},
        ]
        for u in users:
            secret = pyotp.random_base32()
            db.users.insert_one({
                'username':   u['username'],
                'password':   generate_password_hash(u['password']),
                'role':       u['role'],
                'dept':       u['dept'],
                'otp_secret': secret
            })
            totp = pyotp.TOTP(secret)
            uri  = totp.provisioning_uri(name=u['username'], issuer_name='DEO Chatbot')
            print(f"\n[{u['username']}] Scan this URI in Google Authenticator:")
            print(f"  {uri}")
            print(f"  Secret: {secret}")

    # Always reseed students with new schema (drop old data)
    db.students.drop()
    students = []
    idx = 1
    for sec in range(1, 20):   # SEC-1 to SEC-19
        for _ in range(20):    # 20 students per section
            students.append(make_student(idx, sec))
            idx += 1
    db.students.insert_many(students)
    print(f"\nSeeded {len(students)} students across 19 sections (231FA00001–231FA00380).")

if __name__ == '__main__':
    seed_data()
    app.run(debug=True, port=5000)
