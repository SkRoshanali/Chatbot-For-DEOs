from fastapi import FastAPI, Request, Depends, HTTPException
from fastapi.responses import JSONResponse, RedirectResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from starlette.middleware.sessions import SessionMiddleware
from werkzeug.security import check_password_hash, generate_password_hash
from datetime import datetime, timedelta, timezone
from contextlib import asynccontextmanager
import pyotp, qrcode, pdfplumber, io, os, base64, pandas as pd, re, pathlib

from database import init_db
from db_utils import (
    find_user, list_users, create_user, update_user_otp, delete_user,
    get_students, find_student, student_exists,
    insert_student, update_student, delete_student, count_students, bulk_insert_students,
    SUBJECTS, put_conn, get_conn
)
from nlp import detect_intent, get_general_response, extract_second_section, extract_threshold, extract_topn
from email_service_demo import send_low_attendance_alert, send_poor_performance_alert, send_bulk_report

# Use absolute paths so Vercel serverless can locate files regardless of cwd
BASE_DIR = pathlib.Path(__file__).parent.resolve()

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    try:
        init_db()
        seed_data()
    except Exception as e:
        print(f"[Startup] Warning: {e}")
    yield
    # Shutdown (nothing needed)

app = FastAPI(title="DEO Chatbot", lifespan=lifespan)

# Session timeout configuration (in minutes) — Now 20 mins absolute
SESSION_TIMEOUT_MINUTES = int(os.environ.get('SESSION_TIMEOUT', 20))

app.add_middleware(SessionMiddleware, secret_key=os.environ.get('SECRET_KEY', 'deo_chatbot_secret_key_2024'),
                   max_age=SESSION_TIMEOUT_MINUTES * 60)  # Convert minutes to seconds
app.mount("/static", StaticFiles(directory=str(BASE_DIR / "static")), name="static")

# Initialize Jinja2Templates with disabled caching
import jinja2
jinja_env = jinja2.Environment(
    loader=jinja2.FileSystemLoader(str(BASE_DIR / "templates")),
    cache_size=0  # Disable caching completely
)
templates = Jinja2Templates(env=jinja_env)

MASTER_PASSWORD = os.environ.get('MASTER_PASSWORD', 'Admin@123')

# ── Auth helpers ──────────────────────────────────────────────────

def get_session_user(request: Request):
    return request.session.get('user')

def require_login(request: Request):
    user = request.session.get('user')
    if not user:
        raise HTTPException(status_code=401, detail="Not authenticated")
    
    # Absolute session timeout check (20 minutes from login)
    login_time = request.session.get('login_time')
    if login_time:
        start_dt = datetime.fromisoformat(login_time)
        if start_dt.tzinfo is None:
            start_dt = start_dt.replace(tzinfo=timezone.utc)
        elapsed = datetime.now(timezone.utc) - start_dt
        timeout_minutes = int(os.environ.get('SESSION_TIMEOUT', 20))
        if elapsed > timedelta(minutes=timeout_minutes):
            request.session.clear()
            raise HTTPException(status_code=401, detail="Session expired")
    
    # We no longer update last_active because the user wants an absolute 20-min countdown
    
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

def require_write_access(request: Request):
    """Require write access (Admin or DEO only)"""
    user = require_login(request)
    if user.get('role') not in ('DEO', 'Admin'):
        raise HTTPException(status_code=403, detail="Write access denied. View-only role.")
    return user

def can_write(user: dict) -> bool:
    """Check if user has write permissions"""
    return user.get('role') in ('Admin', 'DEO')

def can_send_notifications(user: dict) -> bool:
    """Check if user can send email notifications"""
    return user.get('role') in ('Admin', 'DEO', 'HOD')

def can_manage_users(user: dict) -> bool:
    """Check if user can manage other users"""
    return user.get('role') == 'Admin'

# ── QR helper ─────────────────────────────────────────────────────

def _make_qr(username, secret) -> str:
    totp = pyotp.TOTP(secret)
    uri  = totp.provisioning_uri(name=username, issuer_name='DEO Chatbot')
    img  = qrcode.make(uri)
    buf  = io.BytesIO()
    img.save(buf, format='PNG')
    return base64.b64encode(buf.getvalue()).decode()

# ── Startup ───────────────────────────────────────────────────────

# Startup is now handled by the lifespan context manager above

# ── Pages ─────────────────────────────────────────────────────────

@app.get("/")
def home(request: Request):
    if request.session.get('user'):
        return RedirectResponse('/console')
    return RedirectResponse('/login')

@app.get("/favicon.ico")
def favicon():
    from fastapi.responses import Response
    # 1x1 transparent PNG — 204 causes Content-Length crash with SessionMiddleware
    TRANSPARENT_PNG = (
        b'\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01'
        b'\x08\x06\x00\x00\x00\x1f\x15\xc4\x89\x00\x00\x00\nIDATx\x9cc\x00\x01'
        b'\x00\x00\x05\x00\x01\r\n-\xb4\x00\x00\x00\x00IEND\xaeB`\x82'
    )
    return Response(content=TRANSPARENT_PNG, media_type="image/png",
                    headers={"Cache-Control": "public, max-age=86400"})

@app.get("/health")
def health_check():
    return JSONResponse({"status": "ok", "version": "2024-04-13-fixed"})

# ── Explicit static file routes (Vercel-safe) ──────────────────────

@app.get("/static/modern-style.css")
def serve_modern_css():
    from fastapi.responses import FileResponse
    return FileResponse(str(BASE_DIR / "static" / "modern-style.css"), media_type="text/css")

@app.get("/static/style.css")
def serve_style_css():
    from fastapi.responses import FileResponse
    return FileResponse(str(BASE_DIR / "static" / "style.css"), media_type="text/css")

@app.get("/static/script.js")
def serve_script_js():
    from fastapi.responses import FileResponse
    return FileResponse(str(BASE_DIR / "static" / "script.js"), media_type="application/javascript")

@app.get("/static/theme-toggle.js")
def serve_theme_toggle_js():
    from fastapi.responses import FileResponse
    return FileResponse(str(BASE_DIR / "static" / "theme-toggle.js"), media_type="application/javascript")

@app.get("/static/images/bot-icon.svg")
def serve_bot_icon():
    from fastapi.responses import FileResponse
    return FileResponse(str(BASE_DIR / "static" / "images" / "bot-icon.svg"), media_type="image/svg+xml")

@app.get("/static/images/university-bg.jpg")
def serve_university_bg():
    from fastapi.responses import FileResponse
    return FileResponse(str(BASE_DIR / "static" / "images" / "university-bg.jpg"), media_type="image/jpeg")

@app.get("/login")
def login_page(request: Request):
    return templates.TemplateResponse(request, "login_embedded.html")

@app.get("/chat")
def chat_page(request: Request):
    user = require_login(request)
    return templates.TemplateResponse(
        request, "index.html", {
            "role": user['role'],
            "username": user['username'], "dept": user['dept']
        }
    )

@app.get("/console")
def console_page(request: Request):
    user = require_login(request)
    return templates.TemplateResponse(
        request, "console.html", {
            "role": user['role'],
            "username": user['username'], "dept": user['dept']
        }
    )

@app.get("/setup")
def setup_page(request: Request):
    return templates.TemplateResponse(request, "setup.html")

@app.get("/admin/register")
def register_page(request: Request):
    require_admin(request)
    return templates.TemplateResponse(request, "register.html")

@app.get("/admin/users-management")
def user_management_page(request: Request):
    require_admin(request)
    return templates.TemplateResponse(request, "user_management.html")

@app.get("/data")
def data_page(request: Request):
    user = require_login(request)
    # Everyone can view, but only Admin/DEO can edit
    can_edit = can_write(user)
    return templates.TemplateResponse(
        request, "data.html", {
            "role": user['role'], "username": user['username'], "can_edit": can_edit
        }
    )

@app.get("/dashboard")
def dashboard_page(request: Request):
    user = require_login(request)
    return templates.TemplateResponse(
        request, "dashboard.html", {
            "role": user['role'], "username": user['username'], "dept": user['dept']
        }
    )

@app.get("/notifications")
def notifications_page(request: Request):
    user = require_login(request)
    # Allow Admin, DEO, and HOD to access notifications
    if user['role'] not in ('Admin', 'DEO', 'HOD'):
        return RedirectResponse('/console')
    return templates.TemplateResponse(
        request, "notifications.html", {
            "role": user['role'], "username": user['username'], "dept": user['dept']
        }
    )

@app.get("/emails/viewer")
def email_viewer_page(request: Request):
    user = require_login(request)
    # Allow Admin, DEO, and HOD to view emails
    if user['role'] not in ('Admin', 'DEO', 'HOD'):
        return RedirectResponse('/console')
    return templates.TemplateResponse(
        request, "email_viewer.html", {
            "role": user['role'], "username": user['username'], "dept": user['dept']
        }
    )

@app.get("/api/emails/demo")
def get_demo_emails(request: Request):
    """Get all demo emails"""
    require_login(request)
    from email_service_demo import EmailLog
    return JSONResponse({'success': True, 'emails': EmailLog.get_all()})

@app.post("/api/emails/demo/clear")
def clear_demo_emails(request: Request):
    """Clear all demo emails"""
    require_deo_or_admin(request)
    from email_service_demo import EmailLog
    EmailLog.clear()
    return JSONResponse({'success': True, 'message': 'All emails cleared'})

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

    # Validate OTP with wider window (4 = 2 minutes before/after to handle clock drift)
    totp = pyotp.TOTP(user['otp_secret'])
    current_otp = totp.now()
    print(f"[LOGIN] Expected OTP: {current_otp}, Received: {otp}")
    
    # Allow bypass with master OTP "000000" for testing/recovery
    MASTER_OTP = os.environ.get('MASTER_OTP', '000000')
    
    if otp == MASTER_OTP:
        print(f"[LOGIN] Master OTP used for user: {username}")
    elif not totp.verify(otp, valid_window=4):
        print(f"[LOGIN] Invalid OTP for user: {username}. Current valid: {current_otp}")
        return JSONResponse({'success': False, 'message': f'Invalid OTP. Your Authenticator should show: check app. Try re-scanning QR at /setup'})

    print(f"[LOGIN] Success for user: {username}")
    request.session['user'] = {
        'username': user['username'],
        'role':     user['role'],
        'dept':     dept or user['dept'],
        'theme':    user.get('theme_pref', 'light')
    }
    request.session['login_time'] = datetime.now(timezone.utc).isoformat()
    return JSONResponse({'success': True})

@app.get("/logout")
def logout(request: Request):
    request.session.clear()
    return RedirectResponse('/login')

@app.get("/api/me")
def me(request: Request):
    user = require_login(request)
    # Re-fetch user from DB to get latest prefs
    db_user = find_user(user['username'])
    return JSONResponse({
        'username': user['username'],
        'role':     user['role'],
        'dept':     user['dept'],
        'theme':    db_user.get('theme_pref', 'light') if db_user else 'light',
        'sender_email': db_user.get('sender_email', '') if db_user else '',
        'login_time': request.session.get('login_time', '')
    })

@app.post("/api/user/theme")
async def api_update_theme(request: Request):
    user = require_login(request)
    data = await request.json()
    theme = data.get('theme', 'light')
    from db_utils import update_user_theme
    update_user_theme(user['username'], theme)
    request.session['user']['theme'] = theme
    return JSONResponse({'success': True})

@app.post("/api/user/email")
async def api_update_email(request: Request):
    user = require_login(request)
    data = await request.json()
    email = data.get('email', '')
    password = data.get('password', '')
    from db_utils import update_user_email
    update_user_email(user['username'], email, password)
    return JSONResponse({'success': True})

@app.get("/api/chat/history")
def get_chat_history_api(request: Request):
    user = require_login(request)
    conn = get_conn(); cur = conn.cursor()
    cur.execute("SELECT query FROM chat_history WHERE username=%s ORDER BY created_at DESC LIMIT 10", (user['username'],))
    history = [r[0] for r in cur.fetchall()]
    cur.close(); put_conn(conn)
    return JSONResponse({'success': True, 'history': history[::-1]})

@app.post("/api/chat/history")
async def save_chat_history_api(request: Request):
    user = require_login(request)
    data = await request.json()
    query = data.get('query', '')
    if not query: return JSONResponse({'success': False})
    
    conn = get_conn(); cur = conn.cursor()
    # Insert new
    cur.execute("INSERT INTO chat_history (username, query) VALUES (%s, %s)", (user['username'], query))
    # Keep only 10 (Sliding cycle)
    cur.execute("""
        DELETE FROM chat_history 
        WHERE id IN (
            SELECT id FROM chat_history 
            WHERE username = %s 
            ORDER BY created_at DESC 
            OFFSET 10
        )
    """, (user['username'],))
    conn.commit(); cur.close(); put_conn(conn)
    return JSONResponse({'success': True})

@app.get("/api/dbstatus")
def db_status(request: Request):
    require_login(request)
    try:
        return JSONResponse({'success': True, 'connected': True, 'student_count': count_students()})
    except Exception as e:
        return JSONResponse({'success': False, 'connected': False, 'error': str(e)})

@app.get("/api/otp-debug")
def otp_debug(request: Request, username: str = "deo_cse"):
    """Debug route - shows current valid OTP for a user. Remove in production."""
    from database import get_conn as _gc, put_conn as _pc
    conn = _gc()
    cur  = conn.cursor()
    cur.execute("SELECT username, otp_secret FROM users WHERE username=%s", (username,))
    row = cur.fetchone()
    cur.close(); _pc(conn)
    if not row:
        return JSONResponse({'error': 'User not found'})
    uname, secret = row
    totp = pyotp.TOTP(secret)
    return JSONResponse({
        'username': uname,
        'current_otp': totp.now(),
        'secret': secret,
        'provisioning_uri': totp.provisioning_uri(uname, issuer_name="SmartDEO"),
        'server_time': datetime.now(timezone.utc).isoformat(),
        'valid_window_otps': [totp.at(datetime.now(timezone.utc), i) for i in range(-4, 5)]
    })

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

# ── DB Viewer ─────────────────────────────────────────────────────

@app.get("/admin/db")
def db_viewer(request: Request, table: str = "students"):
    require_login(request)
    from database import get_conn as _gc, put_conn as _pc
    from psycopg2.extras import RealDictCursor
    conn = _gc()
    cur  = conn.cursor(cursor_factory=RealDictCursor)

    allowed = {"students": "students", "subject_marks": "subject_marks", "users": "users"}
    if table not in allowed:
        table = "students"

    cur.execute(f'SELECT * FROM "{table}" LIMIT 500')
    rows = cur.fetchall()
    cur.execute(f'SELECT count(*) as total FROM "{table}"')
    total = cur.fetchone()["total"]
    cur.close()
    _pc(conn)

    # Convert datetime objects to strings
    for row in rows:
        for k, v in row.items():
            if hasattr(v, 'isoformat'):
                row[k] = v.isoformat()

    # Hide sensitive columns for users table
    HIDDEN_COLS = {'password', 'otp_secret'}
    cols = [c for c in (list(rows[0].keys()) if rows else []) if c not in HIDDEN_COLS]

    rows_html = ""
    for row in rows:
        cells = "".join(f"<td>{row[c]}</td>" for c in cols)
        rows_html += f"<tr>{cells}</tr>"

    headers_html = "".join(f"<th>{c}</th>" for c in cols)

    tabs_html = ""
    for t in ["students", "subject_marks", "users"]:
        active = "active" if t == table else ""
        tabs_html += f'<a href="/admin/db?table={t}" class="tab-link {active}">{t}</a>'

    html = f"""<!DOCTYPE html>
<html>
<head>
  <title>DB Viewer — {table}</title>
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <style>
    * {{ box-sizing: border-box; margin: 0; padding: 0; }}
    body {{ font-family: 'Segoe UI', sans-serif; background: #0f0f23; color: #e0e0e0; padding: 20px; }}
    h1 {{ font-size: 1.4rem; color: #667eea; margin-bottom: 16px; }}
    .meta {{ font-size: 0.85rem; color: #a0a0b8; margin-bottom: 16px; }}
    .tabs {{ display: flex; gap: 8px; margin-bottom: 20px; }}
    .tab-link {{
      padding: 8px 20px; border-radius: 6px; text-decoration: none;
      background: #1a1a35; color: #a0a0b8; border: 1px solid #2d2d50;
      font-size: 0.875rem; transition: all 0.2s;
    }}
    .tab-link:hover {{ background: #667eea; color: white; }}
    .tab-link.active {{ background: linear-gradient(135deg,#667eea,#764ba2); color: white; border-color: transparent; }}
    .table-wrap {{ overflow-x: auto; border-radius: 10px; box-shadow: 0 4px 20px rgba(0,0,0,0.4); }}
    table {{ width: 100%; border-collapse: collapse; font-size: 0.8rem; background: #1a1a35; }}
    thead {{ background: linear-gradient(135deg,#667eea,#764ba2); position: sticky; top: 0; }}
    th {{ padding: 10px 14px; text-align: left; color: white; font-weight: 700;
          text-transform: uppercase; font-size: 0.7rem; letter-spacing: 0.05em; white-space: nowrap; }}
    td {{ padding: 8px 14px; border-bottom: 1px solid #2d2d50; white-space: nowrap; color: #ccc; }}
    tr:nth-child(even) td {{ background: rgba(102,126,234,0.04); }}
    tr:hover td {{ background: rgba(102,126,234,0.1); }}
    td:first-child {{ color: #667eea; font-weight: 600; font-family: monospace; }}
    .back {{ display: inline-block; margin-top: 20px; padding: 8px 18px;
             background: #667eea; color: white; border-radius: 6px; text-decoration: none; font-size: 0.875rem; }}
    .back:hover {{ background: #764ba2; }}
    .search-bar {{ margin-bottom: 16px; }}
    .search-bar input {{
      padding: 8px 14px; background: #1a1a35; border: 1px solid #2d2d50;
      border-radius: 6px; color: #e0e0e0; font-size: 0.875rem; width: 300px;
    }}
    .search-bar input:focus {{ outline: none; border-color: #667eea; }}
  </style>
</head>
<body>
  <h1>🗄️ Database Viewer</h1>
  <div class="meta">Table: <strong>{table}</strong> &nbsp;|&nbsp; Showing up to 500 of <strong>{total}</strong> rows</div>
  <div class="tabs">{tabs_html}</div>
  <div class="search-bar">
    <input type="text" id="searchBox" placeholder="🔍 Filter rows..." oninput="filterTable(this.value)">
  </div>
  <div class="table-wrap">
    <table id="dbTable">
      <thead><tr>{headers_html}</tr></thead>
      <tbody id="tableBody">{rows_html}</tbody>
    </table>
  </div>
  <a href="/console" class="back">← Back to Dashboard</a>
  <script>
    function filterTable(q) {{
      q = q.toLowerCase();
      document.querySelectorAll('#tableBody tr').forEach(row => {{
        row.style.display = row.textContent.toLowerCase().includes(q) ? '' : 'none';
      }});
    }}
  </script>
</body>
</html>"""
    from fastapi.responses import HTMLResponse
    return HTMLResponse(html)

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

    # ── CRUD via chatbot ──────────────────────────────────────────
    if intent == 'add_student':
        if not can_write(user):
            return JSONResponse({'success': True, 'report_type': 'general',
                'message': '🚫 You do not have permission to add students. Contact Admin or DEO.'})
        # Parse fields from query
        roll_m = re.search(r'\b(231FA\d{5}|[A-Z]{2,5}\d{3,5})\b', query, re.IGNORECASE)
        name_m = re.search(r'name[:\s]+([A-Za-z\s]+?)(?:,|roll|section|dept|$)', query, re.IGNORECASE)
        sec_m  = re.search(r'sec(?:tion)?[-\s]*(\d{1,2})', query, re.IGNORECASE)
        if not roll_m:
            return JSONResponse({'success': True, 'report_type': 'general',
                'message': '⚠️ Please provide a roll number to add a student.\nExample: *add student roll 231FA00999 name John Doe section SEC-1*'})
        new_roll = roll_m.group(0).upper()
        new_name = name_m.group(1).strip() if name_m else 'Unknown'
        new_sec  = f"SEC-{sec_m.group(1)}" if sec_m else 'SEC-1'
        if student_exists(new_roll):
            return JSONResponse({'success': True, 'report_type': 'general',
                'message': f'⚠️ Student with roll number **{new_roll}** already exists.'})
        insert_student({'roll': new_roll, 'name': new_name, 'section': new_sec,
            'department': dept, 'semester': '3', 'batch': '2023-27',
            'cgpa': 0, 'attendance': 0, 'backlogs': 0, 'internal': 0, 'external': 0,
            'subjects': {s: {'attendance':0,'internal':0,'external':0} for s in ['CN','SE','ADS','PDC']}})
        return JSONResponse({'success': True, 'report_type': 'general',
            'message': f'✅ Student **{new_name}** ({new_roll}) added to {new_sec} successfully.\nGo to Data Management to fill in marks and attendance.'})

    if intent == 'delete_student':
        if not can_write(user):
            return JSONResponse({'success': True, 'report_type': 'general',
                'message': '🚫 You do not have permission to delete students.'})
        roll_m = re.search(r'\b(231FA\d{5}|[A-Z]{2,5}\d{3,5})\b', query, re.IGNORECASE)
        if not roll_m:
            return JSONResponse({'success': True, 'report_type': 'general',
                'message': '⚠️ Please provide a roll number to delete.\nExample: *delete student 231FA00001*'})
        del_roll = roll_m.group(0).upper()
        s = find_student(del_roll)
        if not s:
            return JSONResponse({'success': True, 'report_type': 'general',
                'message': f'⚠️ No student found with roll number **{del_roll}**.'})
        delete_student(del_roll)
        return JSONResponse({'success': True, 'report_type': 'general',
            'message': f'✅ Student **{s["name"]}** ({del_roll}) has been deleted successfully.'})

    if intent in ('update_student', 'update_student_section'):
        if not can_write(user):
            return JSONResponse({'success': True, 'report_type': 'general',
                'message': '🚫 You do not have permission to update students.'})
        roll_m = re.search(r'\b(231FA\d{5}|[A-Z]{2,5}\d{3,5})\b', query, re.IGNORECASE)
        if not roll_m:
            return JSONResponse({'success': True, 'report_type': 'general',
                'message': '⚠️ Please provide a roll number to update.\nExample: *update 231FA00001 section to SEC-3*'})
        upd_roll = roll_m.group(0).upper()
        s = find_student(upd_roll)
        if not s:
            return JSONResponse({'success': True, 'report_type': 'general',
                'message': f'⚠️ No student found with roll number **{upd_roll}**.'})
        updates = {}
        # Section update
        from nlp import extract_target_section
        target_sec = extract_target_section(query)
        if target_sec:
            updates['section'] = target_sec
        # Attendance update
        att_m = re.search(r'attendance[:\s]+(\d+)', query, re.IGNORECASE)
        if att_m: updates['attendance'] = int(att_m.group(1))
        # CGPA update
        cgpa_m = re.search(r'cgpa[:\s]+([\d.]+)', query, re.IGNORECASE)
        if cgpa_m: updates['cgpa'] = float(cgpa_m.group(1))
        # Name update
        name_m2 = re.search(r'name[:\s]+([A-Za-z\s]+?)(?:,|roll|section|dept|$)', query, re.IGNORECASE)
        if name_m2: updates['name'] = name_m2.group(1).strip()
        if not updates:
            return JSONResponse({'success': True, 'report_type': 'general',
                'message': f'⚠️ Nothing to update for **{upd_roll}**. Specify what to change.\nExamples:\n• *update 231FA00001 section to SEC-5*\n• *update 231FA00001 attendance 85*\n• *update 231FA00001 cgpa 7.5*'})
        update_student(upd_roll, updates)
        changes = ', '.join(f'{k}={v}' for k, v in updates.items())
        return JSONResponse({'success': True, 'report_type': 'general',
            'message': f'✅ Student **{s["name"]}** ({upd_roll}) updated: {changes}'})

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

    if intent == 'pass_fail_report':
        pool = get_students(dept=dept, section=section_nlp, semester=sem)
        passed = [s for s in pool if s.get('result','') == 'Pass' or (s.get('cgpa',0) >= 5.0 and s.get('backlogs',0) == 0)]
        failed = [s for s in pool if s.get('result','') == 'Fail' or s.get('cgpa',0) < 5.0]
        q_low2 = query.lower()
        if 'fail' in q_low2:
            data = failed
            label = f'Failed Students ({len(failed)} found)'
        elif 'pass' in q_low2:
            data = passed
            label = f'Passed Students ({len(passed)} found)'
        else:
            data = pool
            label = f'Result Report — Pass: {len(passed)}, Fail: {len(failed)}'
        return JSONResponse({'success': True, 'report_type': 'pass_fail_report',
            'label': label, 'passed': len(passed), 'failed': len(failed),
            'section': section_nlp.upper() if section_nlp else 'All',
            'data': data})

    if intent == 'grade_report':
        pool = get_students(dept=dept, section=section_nlp)
        from db_utils import get_conn as _dbc
        conn2 = _dbc()
        cur2  = conn2.cursor()
        rolls = [s['roll'] for s in pool]
        if rolls:
            fmt2 = ','.join(['%s']*len(rolls))
            cur2.execute(f"SELECT roll, subject, grade, total, internal, external FROM subject_marks WHERE roll IN ({fmt2})", rolls)
            grade_rows = cur2.fetchall()
        else:
            grade_rows = []
        cur2.close(); conn2.close()
        grade_data = [{'roll': r[0], 'subject': r[1], 'grade': r[2], 'total': r[3], 'internal': r[4], 'external': r[5]} for r in grade_rows]
        return JSONResponse({'success': True, 'report_type': 'grade_report',
            'section': section_nlp.upper() if section_nlp else 'All',
            'count': len(grade_data), 'data': grade_data})

    if intent == 'department_info':
        from database import get_conn as _dgc
        conn3 = _dgc()
        cur3  = conn3.cursor(dictionary=True)
        cur3.execute("SELECT * FROM departments")
        depts = cur3.fetchall()
        cur3.close(); conn3.close()
        if not depts:
            return JSONResponse({'success': True, 'report_type': 'general',
                'message': 'Department info: CSE (HOD: Dr. Rao), ECE (HOD: Dr. Kumar)'})
        return JSONResponse({'success': True, 'report_type': 'department_info', 'data': depts})

    if intent == 'subject_info':
        from database import get_conn as _sgc
        conn4 = _sgc()
        cur4  = conn4.cursor(dictionary=True)
        if sem:
            cur4.execute("SELECT * FROM subjects WHERE semester=%s AND department=%s", (sem, dept))
        else:
            cur4.execute("SELECT * FROM subjects WHERE department=%s", (dept,))
        subjs = cur4.fetchall()
        cur4.close(); conn4.close()
        if not subjs:
            return JSONResponse({'success': True, 'report_type': 'general',
                'message': 'No subjects found. Upload subject data via Data Management.'})
        return JSONResponse({'success': True, 'report_type': 'subject_info', 'data': subjs})

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

@app.get("/api/dashboard")
async def get_dashboard(request: Request):
    """Dashboard API with analytics data"""
    user = require_login(request)
    dept = user['dept']
    
    # Get all students for the department
    students = get_students(dept=dept)
    
    if not students:
        return JSONResponse({
            'success': True,
            'stats': {'total_students': 0, 'avg_cgpa': 0, 'avg_attendance': 0, 'low_attendance': 0},
            'subject_performance': [],
            'attendance_distribution': {'above_85': 0, 'between_75_85': 0, 'below_75': 0},
            'cgpa_distribution': {'above_8': 0, 'between_6_8': 0, 'below_6': 0},
            'section_performance': []
        })
    
    total = len(students)
    
    # Calculate stats
    avg_cgpa = sum(s.get('cgpa', 0) for s in students) / total
    avg_attendance = sum(s.get('attendance', 0) for s in students) / total
    low_attendance = sum(1 for s in students if s.get('attendance', 0) < 75)
    
    # Subject performance
    subject_perf = []
    for subj in SUBJECTS:
        externals = [_subj_data(s, subj)['external'] for s in students]
        internals = [_subj_data(s, subj)['internal'] for s in students]
        subject_perf.append({
            'subject': subj,
            'avg_external': round(sum(externals) / len(externals), 1),
            'avg_internal': round(sum(internals) / len(internals), 1)
        })
    
    # Attendance distribution
    above_85 = sum(1 for s in students if s.get('attendance', 0) >= 85)
    between_75_85 = sum(1 for s in students if 75 <= s.get('attendance', 0) < 85)
    below_75 = sum(1 for s in students if s.get('attendance', 0) < 75)
    
    # CGPA distribution
    above_8 = sum(1 for s in students if s.get('cgpa', 0) >= 8)
    between_6_8 = sum(1 for s in students if 6 <= s.get('cgpa', 0) < 8)
    below_6 = sum(1 for s in students if s.get('cgpa', 0) < 6)
    
    # Section performance
    sections = {}
    for s in students:
        sec = s.get('section', 'Unknown')
        if sec not in sections:
            sections[sec] = []
        sections[sec].append(s)
    
    section_perf = []
    for sec in sorted(sections.keys()):
        sec_students = sections[sec]
        section_perf.append({
            'section': sec,
            'avg_cgpa': round(sum(s.get('cgpa', 0) for s in sec_students) / len(sec_students), 2),
            'count': len(sec_students)
        })
    
    return JSONResponse({
        'success': True,
        'stats': {
            'total_students': total,
            'avg_cgpa': round(avg_cgpa, 2),
            'avg_attendance': round(avg_attendance, 1),
            'low_attendance': low_attendance
        },
        'subject_performance': subject_perf,
        'attendance_distribution': {
            'above_85': above_85,
            'between_75_85': between_75_85,
            'below_75': below_75
        },
        'cgpa_distribution': {
            'above_8': above_8,
            'between_6_8': between_6_8,
            'below_6': below_6
        },
        'section_performance': section_perf
    })

@app.get("/api/export/all")
def export_all_students(request: Request, fmt: str = "xlsx"):
    """GET endpoint — export all students for the logged-in user's dept"""
    user = require_login(request)
    students = get_students(dept=user['dept'])
    if not students:
        raise HTTPException(404, "No students found")
    # Flatten subjects into columns
    rows = []
    for s in students:
        row = {k: v for k, v in s.items() if k != 'subjects'}
        subj = s.get('subjects') or {}
        for sub in ['CN', 'SE', 'ADS', 'PDC']:
            d = subj.get(sub, {})
            row[f'{sub}_att']  = d.get('attendance', 0)
            row[f'{sub}_int']  = d.get('internal', 0)
            row[f'{sub}_ext']  = d.get('external', 0)
        rows.append(row)
    df = pd.DataFrame(rows)
    if fmt == 'csv':
        out = io.StringIO(); df.to_csv(out, index=False); out.seek(0)
        return StreamingResponse(io.BytesIO(out.getvalue().encode()), media_type='text/csv',
            headers={'Content-Disposition': 'attachment; filename=all_students.csv'})
    out = io.BytesIO()
    with pd.ExcelWriter(out, engine='openpyxl') as w:
        df.to_excel(w, index=False, sheet_name='Students')
    out.seek(0)
    return StreamingResponse(out,
        media_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
        headers={'Content-Disposition': 'attachment; filename=all_students.xlsx'})

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

# ── Email Notifications ───────────────────────────────────────────

@app.post("/api/notifications/send")
async def send_notification(request: Request):
    """Send email notification for specific students"""
    user = require_login(request)
    
    # Check if user can send notifications
    if not can_send_notifications(user):
        return JSONResponse({'success': False, 'message': 'You do not have permission to send notifications'})
    
    data = await request.json()
    
    notification_type = data.get('type', 'low_attendance')
    recipient_email = data.get('email', '')
    students = data.get('students', [])
    sender_role = user.get('role', 'DEO')  # Get sender's role
    
    if not recipient_email:
        return JSONResponse({'success': False, 'message': 'Recipient email required'})
    
    if not students:
        return JSONResponse({'success': False, 'message': 'No students selected'})
    
    sent_count = 0
    failed_count = 0
    errors = []
    
    for student_roll in students:
        student = find_student(student_roll)
        if not student:
            failed_count += 1
            errors.append(f"Student {student_roll} not found")
            continue
        
        try:
            if notification_type == 'low_attendance':
                success = send_low_attendance_alert(student, recipient_email, sender_role)
            elif notification_type == 'poor_performance':
                success = send_poor_performance_alert(student, recipient_email, sender_role)
            else:
                failed_count += 1
                errors.append(f"Invalid notification type: {notification_type}")
                continue
            
            if success:
                sent_count += 1
            else:
                failed_count += 1
                errors.append(f"Failed to send email for {student['name']}")
        except Exception as e:
            failed_count += 1
            errors.append(f"Error sending to {student['name']}: {str(e)}")
    
    message = f'Sent {sent_count} notifications'
    if failed_count > 0:
        message += f', {failed_count} failed'
    
    return JSONResponse({
        'success': sent_count > 0,
        'message': message,
        'sent': sent_count,
        'failed': failed_count,
        'errors': errors if errors else None
    })

@app.post("/api/notifications/bulk-report")
async def send_bulk_report_email(request: Request):
    """Send bulk performance report"""
    user = require_login(request)
    
    # Check if user can send notifications
    if not can_send_notifications(user):
        return JSONResponse({'success': False, 'message': 'You do not have permission to send notifications'})
    
    data = await request.json()
    
    recipient_email = data.get('email', '')
    sender_role = user.get('role', 'DEO')  # Get sender's role
    
    if not recipient_email:
        return JSONResponse({'success': False, 'message': 'Recipient email required'})
    
    # Get statistics
    dept = user['dept']
    students = get_students(dept=dept)
    
    if not students:
        return JSONResponse({'success': False, 'message': 'No students found'})
    
    total = len(students)
    avg_cgpa = round(sum(s.get('cgpa', 0) for s in students) / total, 2)
    avg_attendance = round(sum(s.get('attendance', 0) for s in students) / total, 1)
    low_attendance = sum(1 for s in students if s.get('attendance', 0) < 75)
    at_risk = sum(1 for s in students if s.get('cgpa', 0) < 6 or s.get('attendance', 0) < 65)
    with_backlogs = sum(1 for s in students if s.get('backlogs', 0) > 0)
    
    report_data = {
        'total_students': total,
        'avg_cgpa': avg_cgpa,
        'avg_attendance': avg_attendance,
        'low_attendance': low_attendance,
        'at_risk': at_risk,
        'with_backlogs': with_backlogs
    }
    
    try:
        success = send_bulk_report(recipient_email, report_data, sender_role)
        
        if success:
            return JSONResponse({'success': True, 'message': 'Report sent successfully'})
        else:
            return JSONResponse({'success': False, 'message': 'Failed to send report. Check email configuration.'})
    except Exception as e:
        return JSONResponse({'success': False, 'message': f'Error sending report: {str(e)}'})

@app.get("/api/notifications/at-risk")
async def get_at_risk_students(request: Request):
    """Get list of at-risk students for notifications"""
    user = require_login(request)
    dept = user['dept']
    
    students = get_students(dept=dept)
    
    # Filter at-risk students
    low_attendance = [s for s in students if s.get('attendance', 0) < 75]
    poor_performance = [s for s in students if s.get('cgpa', 0) < 6]
    with_backlogs = [s for s in students if s.get('backlogs', 0) > 0]
    
    return JSONResponse({
        'success': True,
        'low_attendance': low_attendance,
        'poor_performance': poor_performance,
        'with_backlogs': with_backlogs
    })


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
    require_write_access(request)
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
    require_write_access(request)
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
    require_write_access(request)
    data = await request.json()
    delete_student(data.get('roll', ''))
    return JSONResponse({'success': True, 'message': 'Student deleted.'})

@app.post("/data/upload")
async def api_upload_file(request: Request):
    require_write_access(request)
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
            print(f"[Seed] Created user: {uname} (Secret: {secret})")

    # Seed students only if table is empty
    if count_students() == 0:
        # Try to seed from sample_students.xlsx if it exists
        if os.path.exists('sample_students.xlsx'):
            try:
                print("[Seed] Found sample_students.xlsx, importing to database...")
                df = pd.read_excel('sample_students.xlsx')
                # Basic normalization of columns
                df.columns = [c.lower().strip() for c in df.columns]
                students = []
                for _, row in df.iterrows():
                    students.append({
                        'roll': str(row.get('roll', '')).upper(),
                        'name': row.get('name', 'Unknown'),
                        'section': row.get('section', 'SEC-1'),
                        'department': row.get('department', 'CSE'),
                        'semester': str(row.get('semester', '3')),
                        'batch': str(row.get('batch', '2023-27')),
                        'cgpa': float(row.get('cgpa', 0)),
                        'attendance': int(row.get('attendance', 0)),
                        'backlogs': int(row.get('backlogs', 0)),
                        'internal': int(row.get('internal', 0)),
                        'external': int(row.get('external', 0)),
                        'subjects': {s: {'attendance': int(row.get('attendance', 0)), 
                                        'internal': int(row.get('internal', 0)), 
                                        'external': int(row.get('external', 0))} 
                                     for s in ['CN', 'SE', 'ADS', 'PDC']}
                    })
                bulk_insert_students(students)
                print(f"[Seed] Successfully imported {len(students)} students from Excel.")
            except Exception as e:
                print(f"[Seed] Error importing Excel: {e}. Falling back to random generation.")
                _seed_random()
        else:
            _seed_random()
    else:
        print(f"[Seed] Students already exist in database, skipping seed.")

def _seed_random():
    print("[Seed] Generating random student data...")
    students = []
    idx = 1
    for sec in range(1, 20):
        for _ in range(20):
            students.append(_make_student(idx, sec))
            idx += 1
    bulk_insert_students(students)
    print(f"[Seed] {len(students)} students seeded randomly across 19 sections.")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)