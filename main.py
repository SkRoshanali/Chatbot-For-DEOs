from fastapi import FastAPI, Request, Depends, HTTPException
from fastapi.responses import JSONResponse, RedirectResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from starlette.middleware.sessions import SessionMiddleware
from werkzeug.security import check_password_hash, generate_password_hash
from datetime import datetime, timedelta
import pyotp, qrcode, pdfplumber, io, os, base64, pandas as pd

from database import init_db
from db_utils import (
    find_user, list_users, create_user, update_user_otp, delete_user,
    get_students, find_student, student_exists,
    insert_student, update_student, delete_student, count_students, bulk_insert_students,
    SUBJECTS
)
from nlp import detect_intent, get_general_response, extract_second_section, extract_threshold, extract_topn

app = FastAPI(title="DEO Chatbot")
app.add_middleware(SessionMiddleware, secret_key=os.environ.get('SECRET_KEY', 'deo_chatbot_secret_key_2024'),
                   max_age=900)
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

MASTER_PASSWORD = os.environ.get('MASTER_PASSWORD', 'Admin@123')

# ── Auth helpers ──────────────────────────────────────────────────

def get_session_user(request: Request):
    return request.session.get('user')

def require_login(request: Request):
    user = request.session.get('user')
    if not user:
        raise HTTPException(status_code=401, detail="Not authenticated")
    last = request.session.get('last_active')
    if last:
        elapsed = datetime.utcnow() - datetime.fromisoformat(last)
        if elapsed > timedelta(minutes=15):
            request.session.clear()
            raise HTTPException(status_code=401, detail="Session expired")
    if request.url.path != '/api/me':
        request.session['last_active'] = datetime.utcnow().isoformat()
    return user

def require_admin(request: Request):
    user = require_login(request)
    if user.get('role') != 'Admin':
        raise HTTPException(status_code=403, detail="Admin only")
    return user

def require_deo_or_admin(request: Request):
    user = require_login(request)
    if user.get('role') not in ('DEO', 'Admin'):
        raise HTTPException(status_code=403, detail="DEO or Admin only")
    return user

# ── QR helper ─────────────────────────────────────────────────────

def _make_qr(username, secret) -> str:
    totp = pyotp.TOTP(secret)
    uri  = totp.provisioning_uri(name=username, issuer_name='DEO Chatbot')
    img  = qrcode.make(uri)
    buf  = io.BytesIO()
    img.save(buf, format='PNG')
    return base64.b64encode(buf.getvalue()).decode()

# ── Startup ───────────────────────────────────────────────────────

@app.on_event("startup")
def startup():
    init_db()
    seed_data()

# ── Pages ─────────────────────────────────────────────────────────

@app.get("/")
def home(request: Request):
    if request.session.get('user'):
        return RedirectResponse('/chat')
    return RedirectResponse('/login')

@app.get("/login")
def login_page(request: Request):
    return templates.TemplateResponse("login.html", {"request": request})

@app.get("/chat")
def chat_page(request: Request):
    user = require_login(request)
    return templates.TemplateResponse("index.html", {
        "request": request, "role": user['role'],
        "username": user['username'], "dept": user['dept']
    })

@app.get("/setup")
def setup_page(request: Request):
    return templates.TemplateResponse("setup.html", {"request": request})

@app.get("/admin/register")
def register_page(request: Request):
    require_admin(request)
    return templates.TemplateResponse("register.html", {"request": request})

@app.get("/data")
def data_page(request: Request):
    user = require_login(request)
    if user['role'] not in ('DEO', 'Admin'):
        return RedirectResponse('/chat')
    return templates.TemplateResponse("data.html", {
        "request": request, "role": user['role'], "username": user['username']
    })

# ── Auth API ──────────────────────────────────────────────────────

@app.post("/login")
async def login(request: Request):
    data     = await request.json()
    username = data.get('username', '')
    password = data.get('password', '')
    otp      = data.get('otp', '').strip()
    dept     = data.get('department', '')

    print(f"[LOGIN] Attempt for user: {username}, dept: {dept}, otp: {otp}")

    user = find_user(username)
    if not user:
        print(f"[LOGIN] User not found: {username}")
        return JSONResponse({'success': False, 'message': 'Invalid username or password.'})
    
    if not check_password_hash(user['password'], password):
        print(f"[LOGIN] Invalid password for user: {username}")
        return JSONResponse({'success': False, 'message': 'Invalid username or password.'})

    # Validate OTP with wider window (2 = 60 seconds before/after)
    totp = pyotp.TOTP(user['otp_secret'])
    current_otp = totp.now()
    print(f"[LOGIN] Expected OTP: {current_otp}, Received: {otp}")
    
    if not totp.verify(otp, valid_window=2):
        print(f"[LOGIN] Invalid OTP for user: {username}")
        return JSONResponse({'success': False, 'message': 'Invalid OTP. Check your Authenticator app.'})

    print(f"[LOGIN] Success for user: {username}")
    request.session['user'] = {
        'username': user['username'],
        'role':     user['role'],
        'dept':     dept or user['dept']
    }
    request.session['last_active'] = datetime.utcnow().isoformat()
    return JSONResponse({'success': True})

@app.get("/logout")
def logout(request: Request):
    request.session.clear()
    return RedirectResponse('/login')

@app.get("/api/me")
def me(request: Request):
    user = require_login(request)
    return JSONResponse({**user, 'last_active': request.session.get('last_active', '')})

@app.get("/api/dbstatus")
def db_status(request: Request):
    require_login(request)
    try:
        return JSONResponse({'success': True, 'connected': True, 'student_count': count_students()})
    except Exception as e:
        return JSONResponse({'success': False, 'connected': False, 'error': str(e)})

# ── Setup / QR ────────────────────────────────────────────────────

@app.post("/setup")
async def setup_post(request: Request):
    data = await request.json()
    if data.get('password') != MASTER_PASSWORD:
        return JSONResponse({'success': False, 'message': 'Wrong master password.'})
    users  = list_users()
    result = []
    for u in users:
        user_full = find_user(u['username'])
        secret    = user_full.get('otp_secret', '')
        if not secret:
            secret = pyotp.random_base32()
            update_user_otp(u['username'], secret)
        result.append({**u, 'qr_code': _make_qr(u['username'], secret)})
    return JSONResponse({'success': True, 'users': result})

@app.post("/setup/qr")
async def get_user_qr(request: Request):
    data = await request.json()
    if data.get('master') != MASTER_PASSWORD:
        raise HTTPException(403)
    user = find_user(data.get('username', ''))
    if not user:
        raise HTTPException(404, "User not found")
    secret = user.get('otp_secret') or pyotp.random_base32()
    if not user.get('otp_secret'):
        update_user_otp(user['username'], secret)
    return JSONResponse({'success': True, 'qr_code': _make_qr(user['username'], secret)})

# ── Admin ─────────────────────────────────────────────────────────

@app.post("/admin/register")
async def register_user(request: Request):
    require_admin(request)
    data     = await request.json()
    username = data.get('username', '').strip()
    password = data.get('password', '').strip()
    role     = data.get('role', 'DEO')
    dept     = data.get('dept', 'CSE')
    if find_user(username):
        return JSONResponse({'success': False, 'message': 'Username already exists.'})
    secret = pyotp.random_base32()
    create_user(username, generate_password_hash(password), role, dept, secret)
    return JSONResponse({'success': True, 'qr_code': _make_qr(username, secret),
                         'secret': secret, 'username': username})

@app.get("/admin/users")
def admin_list_users(request: Request):
    require_admin(request)
    return JSONResponse(list_users())

@app.post("/admin/delete")
async def admin_delete_user(request: Request):
    require_admin(request)
    data = await request.json()
    delete_user(data.get('username'))
    return JSONResponse({'success': True})

# ── Report helpers ────────────────────────────────────────────────

def _subj_data(s, subj):
    return (s.get('subjects') or {}).get(subj, {'attendance': 0, 'internal': 0, 'external': 0})

def _pool(dept, section=None):
    return get_students(dept=dept, section=section)

# ── Report API ────────────────────────────────────────────────────

@app.post("/api/report")
async def get_report(request: Request):
    user     = require_login(request)
    data     = await request.json()
    query    = data.get('query', '')
    sem_ui   = data.get('semester', '')
    batch_ui = data.get('batch', '')
    dept     = user['dept']

    if query == '__keepalive__':
        return JSONResponse({'success': True, 'report_type': 'general', 'message': ''})

    intent, sem_nlp, batch_nlp, roll_nlp, section_nlp, subject_nlp, qualifier_nlp = detect_intent(query)
    sem   = sem_nlp   or sem_ui
    batch = batch_nlp or batch_ui
    q_low = query.lower()

    if intent == 'general':
        return JSONResponse({'success': True, 'report_type': 'general', 'message': get_general_response(query)})

    if intent == 'student_lookup' and roll_nlp:
        s = find_student(roll_nlp.upper())
        if not s:
            return JSONResponse({'success': True, 'report_type': 'empty',
                'message': f'No student found with roll number {roll_nlp.upper()}.'})
        return JSONResponse({'success': True, 'report_type': 'student_lookup', 'data': s})

    if intent == 'section_lookup' and section_nlp:
        rows = get_students(dept=dept, section=section_nlp)
        if not rows:
            return JSONResponse({'success': True, 'report_type': 'empty',
                'message': f'No students found in {section_nlp.upper()}.'})
        return JSONResponse({'success': True, 'report_type': 'section_lookup',
            'data': rows, 'section': section_nlp.upper()})

    if intent == 'subject_section_attendance' and subject_nlp:
        pool = get_students(dept=dept, section=section_nlp)
        if not pool:
            return JSONResponse({'success': True, 'report_type': 'empty',
                'message': f'No students found in {section_nlp.upper() if section_nlp else "selected section"}.'})
        subj = subject_nlp.upper()
        rows = [{'roll': s['roll'], 'name': s['name'], 'section': s.get('section',''),
                 'subject': subj, **_subj_data(s, subj)} for s in pool]
        n = len(rows)
        return JSONResponse({'success': True, 'report_type': 'subject_section_attendance',
            'subject': subj, 'section': section_nlp.upper() if section_nlp else 'All', 'data': rows,
            'summary': {'count': n,
                'avg_att':  round(sum(r['attendance'] for r in rows)/n, 1),
                'avg_int':  round(sum(r['internal']   for r in rows)/n, 1),
                'avg_ext':  round(sum(r['external']   for r in rows)/n, 1),
                'above_75': sum(1 for r in rows if r['attendance'] >= 75),
                'below_75': sum(1 for r in rows if r['attendance'] < 75)}})

    if intent == 'subject_filter' and subject_nlp:
        pool      = get_students(dept=dept, section=section_nlp)
        subj      = subject_nlp.upper()
        qualifier = qualifier_nlp or 'low'
        fa    = any(w in q_low for w in ['attend','attendance','present','absent'])
        fm    = any(w in q_low for w in ['mark','marks','score','result','internal','external','grade'])
        focus = 'attendance' if fa and not fm else 'marks' if fm and not fa else 'all'
        rows  = []
        for s in pool:
            sd   = _subj_data(s, subj)
            att, int_, ext_ = sd['attendance'], sd['internal'], sd['external']
            if qualifier == 'low':
                match = (att < 75) if focus == 'attendance' else (ext_ < 40 or int_ < 20) if focus == 'marks' else (att < 75 or ext_ < 40)
            elif qualifier == 'high':
                match = (att >= 85) if focus == 'attendance' else (ext_ >= 60 and int_ >= 30) if focus == 'marks' else (att >= 75 and ext_ >= 60)
            else:
                match = (60 <= att < 85) if focus == 'attendance' else (40 <= ext_ < 60) if focus == 'marks' else (60 <= att < 85 and 40 <= ext_ < 60)
            if match:
                rows.append({'roll': s['roll'], 'name': s['name'], 'section': s.get('section',''),
                    'subject': subj, 'attendance': att, 'internal': int_, 'external': ext_, 'focus': focus})
        if not rows:
            tier  = {'low': 'weak/low', 'high': 'top/excellent', 'average': 'average'}.get(qualifier, qualifier)
            scope = f' in {section_nlp.upper()}' if section_nlp else ''
            return JSONResponse({'success': True, 'report_type': 'empty',
                'message': f'No {tier} students found for {subj}{scope}.'})
        rows.sort(key=lambda r: r['attendance' if focus == 'attendance' else 'external'], reverse=(qualifier == 'high'))
        return JSONResponse({'success': True, 'report_type': 'subject_filter', 'subject': subj,
            'qualifier': qualifier, 'focus': focus,
            'section': section_nlp.upper() if section_nlp else 'All', 'count': len(rows), 'data': rows})

    if intent == 'section_toppers' and section_nlp:
        pool = _pool(dept, section_nlp)
        if not pool:
            return JSONResponse({'success': True, 'report_type': 'empty', 'message': f'No students in {section_nlp.upper()}.'})
        n = extract_topn(query)
        if subject_nlp:
            subj = subject_nlp.upper()
            pool.sort(key=lambda x: _subj_data(x, subj)['external'], reverse=True)
            rows = [{'rank': i+1, 'roll': s['roll'], 'name': s['name'], 'section': s.get('section',''),
                     'subject': subj, **_subj_data(s, subj)} for i, s in enumerate(pool[:n])]
            return JSONResponse({'success': True, 'report_type': 'section_toppers',
                'section': section_nlp.upper(), 'subject': subj, 'data': rows})
        pool.sort(key=lambda x: x.get('cgpa', 0), reverse=True)
        rows = [{'rank': i+1, 'roll': s['roll'], 'name': s['name'], 'section': s.get('section',''),
                 'cgpa': s.get('cgpa', 0), 'attendance': s.get('attendance', 0)} for i, s in enumerate(pool[:n])]
        return JSONResponse({'success': True, 'report_type': 'section_toppers',
            'section': section_nlp.upper(), 'subject': None, 'data': rows})

    if intent == 'section_backlogs' and section_nlp:
        import re as _re
        pool      = _pool(dept, section_nlp)
        m         = _re.search(r'\b(\d+)\b', query)
        threshold = int(m.group(1)) if m else 2
        rows      = [s for s in pool if s.get('backlogs', 0) > threshold]
        if not rows:
            return JSONResponse({'success': True, 'report_type': 'empty',
                'message': f'No students with more than {threshold} backlogs in {section_nlp.upper()}.'})
        return JSONResponse({'success': True, 'report_type': 'section_backlogs',
            'section': section_nlp.upper(), 'threshold': threshold, 'count': len(rows), 'data': rows})

    if intent == 'section_performance' and section_nlp:
        pool = _pool(dept, section_nlp)
        if not pool:
            return JSONResponse({'success': True, 'report_type': 'empty', 'message': f'No students in {section_nlp.upper()}.'})
        n = len(pool)
        subj_stats = []
        for subj in SUBJECTS:
            ve = [_subj_data(s, subj)['external']   for s in pool]
            vi = [_subj_data(s, subj)['internal']   for s in pool]
            va = [_subj_data(s, subj)['attendance'] for s in pool]
            subj_stats.append({'subject': subj,
                'avg_external': round(sum(ve)/n, 1), 'avg_internal': round(sum(vi)/n, 1),
                'avg_attend':   round(sum(va)/n, 1),
                'pass_rate':    round(sum(1 for v in ve if v >= 40)/n*100, 1),
                'low_attend':   sum(1 for v in va if v < 75)})
        return JSONResponse({'success': True, 'report_type': 'section_performance',
            'section': section_nlp.upper(), 'count': n,
            'avg_cgpa': round(sum(s.get('cgpa',0) for s in pool)/n, 2),
            'avg_attendance': round(sum(s.get('attendance',0) for s in pool)/n, 1),
            'subjects': subj_stats, 'data': pool})

    if intent == 'section_cgpa_filter' and section_nlp:
        pool      = _pool(dept, section_nlp)
        threshold = extract_threshold(query) or 8.5
        above     = any(w in q_low for w in ['above','greater','more than','over'])
        rows      = [s for s in pool if (s.get('cgpa',0) >= threshold if above else s.get('cgpa',0) < threshold)]
        direction = 'above' if above else 'below'
        if not rows:
            return JSONResponse({'success': True, 'report_type': 'empty',
                'message': f'No students with CGPA {direction} {threshold} in {section_nlp.upper()}.'})
        rows.sort(key=lambda x: x.get('cgpa',0), reverse=above)
        return JSONResponse({'success': True, 'report_type': 'section_cgpa_filter',
            'section': section_nlp.upper(), 'threshold': threshold,
            'direction': direction, 'count': len(rows), 'data': rows})

    if intent == 'compare_sections':
        sec1 = section_nlp
        sec2 = extract_second_section(query)
        if not sec1 or not sec2:
            return JSONResponse({'success': True, 'report_type': 'empty',
                'message': 'Please specify two sections to compare (e.g. SEC-1 and SEC-2).'})
        def sec_summary(pool, sec, subj=None):
            if not pool: return {'section': sec, 'count': 0}
            n = len(pool)
            if subj:
                ve = [_subj_data(s, subj)['external']   for s in pool]
                vi = [_subj_data(s, subj)['internal']   for s in pool]
                va = [_subj_data(s, subj)['attendance'] for s in pool]
                return {'section': sec, 'count': n, 'subject': subj,
                    'avg_external': round(sum(ve)/n,1), 'avg_internal': round(sum(vi)/n,1),
                    'avg_attend': round(sum(va)/n,1), 'pass_rate': round(sum(1 for v in ve if v>=40)/n*100,1)}
            return {'section': sec, 'count': n,
                'avg_cgpa':    round(sum(s.get('cgpa',0) for s in pool)/n, 2),
                'avg_attend':  round(sum(s.get('attendance',0) for s in pool)/n, 1),
                'avg_external': round(sum(s.get('external',0) for s in pool)/n, 1)}
        subj = subject_nlp.upper() if subject_nlp else None
        return JSONResponse({'success': True, 'report_type': 'compare_sections', 'subject': subj,
            'sec1': sec_summary(_pool(dept, sec1), sec1.upper(), subj),
            'sec2': sec_summary(_pool(dept, sec2), sec2.upper(), subj)})

    if intent == 'subject_failure_rate':
        all_s = _pool(dept)
        if not all_s:
            return JSONResponse({'success': True, 'report_type': 'empty', 'message': 'No students found.'})
        stats = []
        for subj in SUBJECTS:
            ve = [_subj_data(s, subj)['external'] for s in all_s]
            vi = [_subj_data(s, subj)['internal'] for s in all_s]
            n  = len(ve); fc = sum(1 for v in ve if v < 40)
            stats.append({'subject': subj, 'count': n, 'fail_count': fc,
                'fail_rate': round(fc/n*100,1), 'avg_external': round(sum(ve)/n,1), 'avg_internal': round(sum(vi)/n,1)})
        stats.sort(key=lambda x: x['fail_rate'], reverse=True)
        return JSONResponse({'success': True, 'report_type': 'subject_failure_rate', 'data': stats})

    if intent == 'marks_distribution' and subject_nlp:
        pool = get_students(dept=dept, section=section_nlp)
        if not pool:
            return JSONResponse({'success': True, 'report_type': 'empty', 'message': 'No students found.'})
        subj    = subject_nlp.upper()
        buckets = {'0-39':0,'40-49':0,'50-59':0,'60-69':0,'70-79':0,'80-89':0,'90-100':0}
        rows    = []
        for s in pool:
            sd  = _subj_data(s, subj); ext = sd['external']
            rows.append({'roll': s['roll'], 'name': s['name'], 'section': s.get('section',''), **sd})
            if ext < 40: buckets['0-39'] += 1
            elif ext < 50: buckets['40-49'] += 1
            elif ext < 60: buckets['50-59'] += 1
            elif ext < 70: buckets['60-69'] += 1
            elif ext < 80: buckets['70-79'] += 1
            elif ext < 90: buckets['80-89'] += 1
            else: buckets['90-100'] += 1
        return JSONResponse({'success': True, 'report_type': 'marks_distribution',
            'subject': subj, 'section': section_nlp.upper() if section_nlp else 'All',
            'count': len(rows), 'buckets': buckets, 'data': rows})

    if intent == 'subject_trend' and subject_nlp:
        all_s  = _pool(dept); subj = subject_nlp.upper()
        groups = {}
        for s in all_s:
            groups.setdefault(s.get('section','?'), []).append(s)
        trend = []
        for sec in sorted(groups, key=lambda x: int(x.replace('SEC-','')) if x.replace('SEC-','').isdigit() else 99):
            grp = groups[sec]; n = len(grp)
            ve  = [_subj_data(s, subj)['external']   for s in grp]
            va  = [_subj_data(s, subj)['attendance'] for s in grp]
            trend.append({'section': sec, 'count': n,
                'avg_external': round(sum(ve)/n,1), 'avg_attend': round(sum(va)/n,1),
                'pass_rate': round(sum(1 for v in ve if v>=40)/n*100,1)})
        return JSONResponse({'success': True, 'report_type': 'subject_trend', 'subject': subj, 'data': trend})

    if intent == 'perfect_attendance':
        rows = [s for s in _pool(dept) if s.get('attendance',0) >= 100]
        if not rows:
            return JSONResponse({'success': True, 'report_type': 'empty',
                'message': 'No students with perfect (100%) attendance found.'})
        return JSONResponse({'success': True, 'report_type': 'perfect_attendance', 'count': len(rows), 'data': rows})

    if intent == 'section_stats':
        all_s  = _pool(dept); groups = {}
        for s in all_s:
            groups.setdefault(s.get('section','?'), []).append(s)
        stats = []
        for sec in sorted(groups, key=lambda x: int(x.replace('SEC-','')) if x.replace('SEC-','').isdigit() else 99):
            grp = groups[sec]; n = len(grp)
            stats.append({'section': sec, 'count': n,
                'avg_cgpa':   round(sum(s.get('cgpa',0) for s in grp)/n, 2),
                'avg_attend': round(sum(s.get('attendance',0) for s in grp)/n, 1),
                'above_75':   sum(1 for s in grp if s.get('attendance',0) >= 75),
                'below_75':   sum(1 for s in grp if s.get('attendance',0) < 75)})
        return JSONResponse({'success': True, 'report_type': 'section_stats', 'data': stats})

    if intent == 'dept_summary':
        all_s = _pool(dept)
        if not all_s:
            return JSONResponse({'success': True, 'report_type': 'empty', 'message': 'No students found.'})
        n = len(all_s)
        subj_stats = []
        for subj in SUBJECTS:
            ve = [_subj_data(s, subj)['external']   for s in all_s]
            va = [_subj_data(s, subj)['attendance'] for s in all_s]
            subj_stats.append({'subject': subj, 'avg_external': round(sum(ve)/n,1),
                'avg_attend': round(sum(va)/n,1), 'pass_rate': round(sum(1 for v in ve if v>=40)/n*100,1)})
        return JSONResponse({'success': True, 'report_type': 'dept_summary', 'count': n,
            'avg_cgpa':    round(sum(s.get('cgpa',0) for s in all_s)/n, 2),
            'avg_attend':  round(sum(s.get('attendance',0) for s in all_s)/n, 1),
            'avg_internal': round(sum(s.get('internal',0) for s in all_s)/n, 1),
            'avg_external': round(sum(s.get('external',0) for s in all_s)/n, 1),
            'subjects': subj_stats})

    if intent == 'predict_backlog':
        pool = get_students(dept=dept, section=section_nlp)
        subj = subject_nlp.upper() if subject_nlp else None
        rows = []
        for s in pool:
            if subj:
                sd = _subj_data(s, subj)
                rs = (1 if sd['attendance']<75 else 0)+(1 if sd['external']<50 else 0)+(1 if sd['internal']<25 else 0)
                if rs >= 2:
                    rows.append({'roll': s['roll'], 'name': s['name'], 'section': s.get('section',''),
                        'subject': subj, **sd, 'risk_score': rs})
            else:
                rs = (1 if s.get('attendance',0)<75 else 0)+(1 if s.get('cgpa',0)<6 else 0)+(1 if s.get('backlogs',0)>0 else 0)
                if rs >= 2:
                    rows.append({'roll': s['roll'], 'name': s['name'], 'section': s.get('section',''),
                        'cgpa': s.get('cgpa',0), 'attendance': s.get('attendance',0),
                        'backlogs': s.get('backlogs',0), 'risk_score': rs})
        rows.sort(key=lambda x: x['risk_score'], reverse=True)
        if not rows:
            return JSONResponse({'success': True, 'report_type': 'empty', 'message': 'No students identified as backlog risk.'})
        return JSONResponse({'success': True, 'report_type': 'predict_backlog',
            'subject': subj, 'section': section_nlp.upper() if section_nlp else 'All',
            'count': len(rows), 'data': rows})

    if intent == 'internal_filter' and subject_nlp:
        pool      = get_students(dept=dept, section=section_nlp)
        subj      = subject_nlp.upper()
        threshold = extract_threshold(query) or 20
        above     = any(w in q_low for w in ['above','more than','greater','over'])
        rows      = []
        for s in pool:
            sd = _subj_data(s, subj)
            if (sd['internal'] > threshold if above else sd['internal'] < threshold):
                rows.append({'roll': s['roll'], 'name': s['name'], 'section': s.get('section',''),
                    'subject': subj, **sd})
        direction = 'above' if above else 'below'
        if not rows:
            return JSONResponse({'success': True, 'report_type': 'empty',
                'message': f'No students scoring {direction} {threshold} in {subj} internals.'})
        rows.sort(key=lambda x: x['internal'], reverse=above)
        return JSONResponse({'success': True, 'report_type': 'internal_filter',
            'subject': subj, 'threshold': threshold, 'direction': direction, 'count': len(rows), 'data': rows})

    # ── Standard filters ──────────────────────────────────────────
    students = get_students(dept=dept, section=section_nlp, semester=sem, batch=batch)

    if (sem or batch) and not students:
        label = f'Semester {sem}' if sem else f'Batch {batch}'
        return JSONResponse({'success': True, 'report_type': 'empty', 'message': f'No students found for {label}.'})

    if intent == 'average_marks':
        if not students:
            return JSONResponse({'success': True, 'report_type': 'empty', 'message': 'No students found.'})
        count = len(students)
        return JSONResponse({'success': True, 'report_type': 'average_marks', 'data': students,
            'averages': {'semester': f'Semester {sem}' if sem else 'All Semesters', 'count': count,
                'internal':   round(sum(s.get('internal',0)   for s in students)/count, 1),
                'external':   round(sum(s.get('external',0)   for s in students)/count, 1),
                'cgpa':       round(sum(s.get('cgpa',0)       for s in students)/count, 2),
                'attendance': round(sum(s.get('attendance',0) for s in students)/count, 1)}})

    if intent == 'subject_performance':
        perf = []
        for subj in SUBJECTS:
            vi = [_subj_data(s, subj)['internal']   for s in students if 'subjects' in s]
            ve = [_subj_data(s, subj)['external']   for s in students if 'subjects' in s]
            va = [_subj_data(s, subj)['attendance'] for s in students if 'subjects' in s]
            if not vi: continue
            n = len(vi)
            perf.append({'subject': subj, 'count': n,
                'avg_internal': round(sum(vi)/n,1), 'avg_external': round(sum(ve)/n,1),
                'avg_attend': round(sum(va)/n,1), 'pass_rate': round(sum(1 for v in ve if v>=40)/n*100,1),
                'low_attend': sum(1 for v in va if v < 75)})
        return JSONResponse({'success': True, 'report_type': 'subject_performance', 'data': perf})

    if intent == 'subject_attendance':
        result = []
        for subj in SUBJECTS:
            vals = [_subj_data(s, subj)['attendance'] for s in students if 'subjects' in s]
            if not vals: continue
            n = len(vals)
            result.append({'subject': subj, 'count': n, 'avg_attend': round(sum(vals)/n,1),
                'above_75': sum(1 for v in vals if v>=75), 'below_75': sum(1 for v in vals if v<75)})
        return JSONResponse({'success': True, 'report_type': 'subject_attendance', 'data': result, 'students': students})

    if intent == 'section_attendance':
        all_s  = get_students(dept=dept); groups = {}
        for s in all_s:
            groups.setdefault(s.get('section','?'), []).append(s)
        sections = []
        for sec in sorted(groups, key=lambda x: int(x.replace('SEC-','')) if x.replace('SEC-','').isdigit() else 99):
            grp = groups[sec]; count = len(grp)
            sections.append({'section': sec, 'total': count,
                'avg_attend': round(sum(x.get('attendance',0) for x in grp)/count,1),
                'above_75': sum(1 for x in grp if x.get('attendance',0)>=75),
                'below_75': sum(1 for x in grp if x.get('attendance',0)<75)})
        return JSONResponse({'success': True, 'report_type': 'section_attendance', 'data': sections})

    if intent == 'department_attendance':
        all_s  = get_students(); groups = {}
        for s in all_s:
            groups.setdefault(s.get('department','?'), []).append(s)
        result = []
        for d in sorted(groups):
            grp = groups[d]; count = len(grp)
            result.append({'department': d, 'count': count,
                'avg_attend': round(sum(x.get('attendance',0) for x in grp)/count,1),
                'below_75': sum(1 for x in grp if x.get('attendance',0)<75),
                'above_85': sum(1 for x in grp if x.get('attendance',0)>=85)})
        return JSONResponse({'success': True, 'report_type': 'department_attendance', 'data': result})

    if intent == 'cgpa_distribution':
        groups = {}
        for s in students:
            groups.setdefault(s.get('department','?'), []).append(s)
        dist = []
        for d in sorted(groups):
            grp = groups[d]; count = len(grp)
            dist.append({'department': d, 'count': count,
                'avg_cgpa': round(sum(x.get('cgpa',0) for x in grp)/count,2),
                'above_8': sum(1 for x in grp if x.get('cgpa',0)>=8),
                'above_6': sum(1 for x in grp if 6<=x.get('cgpa',0)<8),
                'below_6': sum(1 for x in grp if x.get('cgpa',0)<6)})
        return JSONResponse({'success': True, 'report_type': 'cgpa_distribution', 'data': dist})

    if intent == 'pending_completions':
        pending = [s for s in students if s.get('backlogs',0) > 0]
        if not pending:
            return JSONResponse({'success': True, 'report_type': 'empty', 'message': 'No students with pending course completions.'})
        return JSONResponse({'success': True, 'report_type': 'pending_completions', 'data': pending})

    if intent == 'low_attendance':   students = [s for s in students if s.get('attendance',100) < 75]
    elif intent == 'backlogs':        students = [s for s in students if s.get('backlogs',0) > 0]
    elif intent == 'repeated_subjects': students = [s for s in students if s.get('backlogs',0) > 0]
    elif intent == 'toppers':         students = sorted(students, key=lambda x: x.get('cgpa',0), reverse=True)[:10]
    elif intent == 'rankings':        students = sorted(students, key=lambda x: x.get('cgpa',0), reverse=True)
    elif intent == 'risk':            students = [s for s in students if s.get('cgpa',10)<6 or s.get('backlogs',0)>=2 or s.get('attendance',100)<65]
    elif intent == 'top_performers':  students = [s for s in students if s.get('cgpa',0)>=8.5 and s.get('attendance',0)>=85]

    if not students:
        label = f'Semester {sem}' if sem else 'selected filters'
        return JSONResponse({'success': True, 'report_type': 'empty', 'message': f'No students found for {label}.'})

    return JSONResponse({'success': True, 'report_type': intent, 'data': students, 'semester': sem})

# ── Export ────────────────────────────────────────────────────────

@app.post("/api/export")
async def export_report(request: Request):
    require_login(request)
    data        = await request.json()
    students    = data.get('data', [])
    fmt         = data.get('format', 'csv')
    report_type = data.get('report_type', 'report')
    if not students:
        raise HTTPException(400, "No data")
    df = pd.DataFrame(students)
    if fmt == 'csv':
        out = io.StringIO(); df.to_csv(out, index=False); out.seek(0)
        return StreamingResponse(io.BytesIO(out.getvalue().encode()), media_type='text/csv',
            headers={'Content-Disposition': f'attachment; filename={report_type}.csv'})
    out = io.BytesIO()
    with pd.ExcelWriter(out, engine='openpyxl') as w:
        df.to_excel(w, index=False, sheet_name='Report')
    out.seek(0)
    return StreamingResponse(out,
        media_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
        headers={'Content-Disposition': f'attachment; filename={report_type}.xlsx'})

# ── Data Management ───────────────────────────────────────────────

@app.get("/data/students")
def api_get_students(request: Request, search: str = ''):
    user = require_login(request)
    rows = get_students(dept=user['dept'], search=search or None)
    # Convert datetime objects to strings for JSON serialization
    for row in rows:
        if 'created_at' in row and row['created_at']:
            row['created_at'] = row['created_at'].isoformat() if hasattr(row['created_at'], 'isoformat') else str(row['created_at'])
        if 'updated_at' in row and row['updated_at']:
            row['updated_at'] = row['updated_at'].isoformat() if hasattr(row['updated_at'], 'isoformat') else str(row['updated_at'])
    return JSONResponse({'success': True, 'data': rows})

@app.post("/data/add")
async def api_add_student(request: Request):
    require_deo_or_admin(request)
    s = await request.json()
    if student_exists(s.get('roll', '')):
        return JSONResponse({'success': False, 'message': 'Roll number already exists.'})

    def sv(key, fb=0):
        v = s.get(key, '')
        try: return int(float(v)) if str(v).strip() not in ('','None','nan') else fb
        except: return fb

    att = sv('attendance'); int_ = sv('internal'); ext = sv('external')
    insert_student({**s,
        'subjects': {
            'CN':  {'attendance': sv('cn_att',att),  'internal': sv('cn_int',int_),  'external': sv('cn_ext',ext)},
            'SE':  {'attendance': sv('se_att',att),  'internal': sv('se_int',int_),  'external': sv('se_ext',ext)},
            'ADS': {'attendance': sv('ads_att',att), 'internal': sv('ads_int',int_), 'external': sv('ads_ext',ext)},
            'PDC': {'attendance': sv('pdc_att',att), 'internal': sv('pdc_int',int_), 'external': sv('pdc_ext',ext)},
        }
    })
    return JSONResponse({'success': True, 'message': 'Student added successfully.'})

@app.post("/data/update")
async def api_update_student(request: Request):
    require_deo_or_admin(request)
    s    = await request.json()
    roll = s.pop('roll', None)
    if not roll:
        return JSONResponse({'success': False, 'message': 'Roll number required.'})

    def sv(key, fb=0):
        v = s.get(key, '')
        try: return int(float(v)) if str(v).strip() not in ('','None','nan') else fb
        except: return fb

    att = sv('attendance'); int_ = sv('internal'); ext = sv('external')
    update_student(roll, {**s,
        'subjects': {
            'CN':  {'attendance': sv('cn_att',att),  'internal': sv('cn_int',int_),  'external': sv('cn_ext',ext)},
            'SE':  {'attendance': sv('se_att',att),  'internal': sv('se_int',int_),  'external': sv('se_ext',ext)},
            'ADS': {'attendance': sv('ads_att',att), 'internal': sv('ads_int',int_), 'external': sv('ads_ext',ext)},
            'PDC': {'attendance': sv('pdc_att',att), 'internal': sv('pdc_int',int_), 'external': sv('pdc_ext',ext)},
        }
    })
    return JSONResponse({'success': True, 'message': 'Student updated successfully.'})

@app.post("/data/delete")
async def api_delete_student(request: Request):
    require_deo_or_admin(request)
    data = await request.json()
    delete_student(data.get('roll', ''))
    return JSONResponse({'success': True, 'message': 'Student deleted.'})

@app.post("/data/upload")
async def api_upload_file(request: Request):
    require_deo_or_admin(request)
    from fastapi import UploadFile, File
    form  = await request.form()
    file  = form.get('file')
    if not file:
        return JSONResponse({'success': False, 'message': 'No file provided.'})
    fname   = file.filename.lower()
    content = await file.read()

    def ss(val, d=''): s=str(val).strip(); return d if s.lower() in ('nan','none','') else s
    def sf(val, d=0.0):
        try: s=str(val).strip(); return float(s) if s.lower() not in ('nan','none','') else d
        except: return d
    def si(val, d=0):
        try: s=str(val).strip(); return int(float(s)) if s.lower() not in ('nan','none','') else d
        except: return d

    try:
        if fname.endswith('.csv'):
            df = pd.read_csv(io.BytesIO(content))
        elif fname.endswith(('.xlsx','.xls')):
            xl = pd.ExcelFile(io.BytesIO(content), engine='openpyxl')
            df = xl.parse(xl.sheet_names[0])
        elif fname.endswith('.pdf'):
            rows, headers = [], []
            with pdfplumber.open(io.BytesIO(content)) as pdf:
                for page in pdf.pages:
                    for table in page.extract_tables():
                        if not headers: headers = [str(h).lower().strip() for h in table[0]]
                        for row in table[1:]: rows.append(dict(zip(headers, row)))
            df = pd.DataFrame(rows)
        else:
            return JSONResponse({'success': False, 'message': 'Unsupported format. Use .xlsx, .csv or .pdf'})

        df.columns = [str(c).lower().strip().replace(' ','_').replace('\n','') for c in df.columns]
        aliases = {'dept':'department','dep':'department','sem':'semester','roll_no':'roll',
                   'roll_number':'roll','rollno':'roll','student_name':'name','full_name':'name',
                   'gpa':'cgpa','attend':'attendance','backlog':'backlogs',
                   'int_marks':'internal','internal_marks':'internal',
                   'ext_marks':'external','external_marks':'external','sec':'section'}
        df.rename(columns=aliases, inplace=True)
        df.dropna(how='all', inplace=True)
        if 'roll' not in df.columns or 'name' not in df.columns:
            return JSONResponse({'success': False,
                'message': f'Missing "roll" or "name" column. Found: {list(df.columns)}'})

        inserted = updated = skipped = 0
        for _, row in df.iterrows():
            roll = ss(row.get('roll',''), '').upper()
            if not roll: skipped += 1; continue
            att = si(row.get('attendance',0)); int_ = si(row.get('internal',0)); ext = si(row.get('external',0))
            doc = {'roll': roll, 'name': ss(row.get('name',''),'Unknown'),
                'section': ss(row.get('section',''),'SEC-1').upper(),
                'department': ss(row.get('department',''),'CSE').upper(),
                'semester': str(si(row.get('semester',1),1)), 'batch': ss(row.get('batch',''),''),
                'cgpa': sf(row.get('cgpa',0)), 'attendance': att, 'backlogs': si(row.get('backlogs',0)),
                'internal': int_, 'external': ext,
                'subjects': {
                    'CN':  {'attendance': si(row.get('cn_attendance',att)),  'internal': si(row.get('cn_internal',int_)),  'external': si(row.get('cn_external',ext))},
                    'SE':  {'attendance': si(row.get('se_attendance',att)),  'internal': si(row.get('se_internal',int_)),  'external': si(row.get('se_external',ext))},
                    'ADS': {'attendance': si(row.get('ads_attendance',att)), 'internal': si(row.get('ads_internal',int_)), 'external': si(row.get('ads_external',ext))},
                    'PDC': {'attendance': si(row.get('pdc_attendance',att)), 'internal': si(row.get('pdc_internal',int_)), 'external': si(row.get('pdc_external',ext))},
                }}
            if student_exists(roll):
                update_student(roll, doc); updated += 1
            else:
                insert_student(doc); inserted += 1

        return JSONResponse({'success': True,
            'message': f'✅ Done! {inserted} added, {updated} updated, {skipped} skipped.'})
    except Exception as e:
        return JSONResponse({'success': False, 'message': f'Error: {str(e)}'})

# ── Seed Data ─────────────────────────────────────────────────────

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

def _make_student(idx, section_num):
    random.seed(idx)
    fname = FIRST_NAMES[idx % len(FIRST_NAMES)]
    lname = LAST_NAMES[idx % len(LAST_NAMES)]
    ba    = random.randint(55, 98)
    bi    = random.randint(20, 50)
    be    = random.randint(30, 100)
    def vary(v, lo, hi): return max(lo, min(hi, v + random.randint(-8, 8)))
    subjects = {
        'CN':  {'attendance': vary(ba,0,100), 'internal': vary(bi,0,50), 'external': vary(be,0,100)},
        'SE':  {'attendance': vary(ba,0,100), 'internal': vary(bi,0,50), 'external': vary(be,0,100)},
        'ADS': {'attendance': vary(ba,0,100), 'internal': vary(bi,0,50), 'external': vary(be,0,100)},
        'PDC': {'attendance': vary(ba,0,100), 'internal': vary(bi,0,50), 'external': vary(be,0,100)},
    }
    avg_ext = sum(s['external'] for s in subjects.values()) / 4
    avg_int = sum(s['internal'] for s in subjects.values()) / 4
    cgpa    = round(min(10, (avg_int/50)*4 + (avg_ext/100)*6), 2)
    return {
        'roll': f'231FA{idx:05d}', 'name': f'{fname} {lname}',
        'section': f'SEC-{section_num}', 'department': 'CSE',
        'semester': '3', 'batch': '2023-27', 'cgpa': cgpa,
        'attendance': ba, 'backlogs': 0 if be >= 40 and bi >= 20 else random.randint(1,3),
        'internal': bi, 'external': be, 'subjects': subjects,
    }

def seed_data():
    from werkzeug.security import generate_password_hash
    # Seed users only if none exist
    if not find_user('admin'):
        default_users = [
            ('deo_cse', 'cse123',   'DEO',   'CSE'),
            ('hod_cse', 'hod123',   'HOD',   'CSE'),
            ('admin',   'admin123', 'Admin', 'ALL'),
        ]
        for uname, pwd, role, dept in default_users:
            secret = pyotp.random_base32()
            create_user(uname, generate_password_hash(pwd), role, dept, secret)
            totp = pyotp.TOTP(secret)
            uri  = totp.provisioning_uri(name=uname, issuer_name='DEO Chatbot')
            print(f"\n[{uname}] Google Authenticator URI:\n  {uri}\n  Secret: {secret}")

    # Seed students only if table is empty
    if count_students() == 0:
        students = []
        idx = 1
        for sec in range(1, 20):
            for _ in range(20):
                students.append(_make_student(idx, sec))
                idx += 1
        bulk_insert_students(students)
        print(f"\n[Seed] {len(students)} students seeded across 19 sections.")
    else:
        print(f"[Seed] Students already exist, skipping seed.")
