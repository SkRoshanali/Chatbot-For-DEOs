"""
All database query helpers — keeps main.py clean.
Every function returns plain dicts (no MySQL Row objects).
"""
from database import get_conn, put_conn

SUBJECTS = ['CN', 'SE', 'ADS', 'PDC']

# ── Helpers ───────────────────────────────────────────────────────

def _row_to_dict(cursor, row):
    from datetime import datetime
    cols = [d[0] for d in cursor.description]
    result = dict(zip(cols, row))
    # Convert datetime objects to ISO format strings for JSON serialization
    for key, value in result.items():
        if isinstance(value, datetime):
            result[key] = value.isoformat()
    return result

def _rows_to_dicts(cursor, rows):
    from datetime import datetime
    cols = [d[0] for d in cursor.description]
    results = [dict(zip(cols, r)) for r in rows]
    # Convert datetime objects to ISO format strings for JSON serialization
    for result in results:
        for key, value in result.items():
            if isinstance(value, datetime):
                result[key] = value.isoformat()
    return results

def _attach_subjects(conn, students: list) -> list:
    """Attach subject_marks dict to each student row."""
    if not students:
        return students
    rolls = [s['roll'] for s in students]
    fmt   = ','.join(['%s'] * len(rolls))
    cur   = conn.cursor()
    cur.execute(
        f"SELECT roll, subject, attendance, internal, external "
        f"FROM subject_marks WHERE roll IN ({fmt})",
        rolls
    )
    marks = {}
    for roll, subj, att, int_, ext in cur.fetchall():
        marks.setdefault(roll, {})[subj] = {'attendance': att, 'internal': int_, 'external': ext}
    cur.close()
    for s in students:
        s['subjects'] = marks.get(s['roll'], {})
    return students

# ── Users ─────────────────────────────────────────────────────────

def find_user(username: str) -> dict:
    conn = get_conn()
    cur  = conn.cursor()
    cur.execute("SELECT * FROM users WHERE username=%s", (username,))
    row = cur.fetchone()
    result = _row_to_dict(cur, row) if row else None
    cur.close(); put_conn(conn)
    return result

def list_users() -> list:
    conn = get_conn()
    cur  = conn.cursor()
    cur.execute("SELECT id, username, role, dept, created_at FROM users")
    rows = _rows_to_dicts(cur, cur.fetchall())
    cur.close(); put_conn(conn)
    return rows

def create_user(username, hashed_pw, role, dept, otp_secret):
    conn = get_conn()
    cur  = conn.cursor()
    cur.execute(
        "INSERT INTO users (username, password, role, dept, otp_secret) VALUES (%s,%s,%s,%s,%s)",
        (username, hashed_pw, role, dept, otp_secret)
    )
    conn.commit(); cur.close(); put_conn(conn)

def update_user_otp(username, secret):
    conn = get_conn()
    cur  = conn.cursor()
    cur.execute("UPDATE users SET otp_secret=%s WHERE username=%s", (secret, username))
    conn.commit(); cur.close(); put_conn(conn)

def update_user_theme(username, theme):
    conn = get_conn()
    cur  = conn.cursor()
    cur.execute("UPDATE users SET theme_pref=%s WHERE username=%s", (theme, username))
    conn.commit(); cur.close(); put_conn(conn)

def update_user_email(username, email, password):
    conn = get_conn()
    cur  = conn.cursor()
    cur.execute("UPDATE users SET sender_email=%s, sender_pw=%s WHERE username=%s", (email, password, username))
    conn.commit(); cur.close(); put_conn(conn)

def delete_user(username):
    conn = get_conn()
    cur  = conn.cursor()
    cur.execute("DELETE FROM users WHERE username=%s", (username,))
    conn.commit(); cur.close(); put_conn(conn)

# ── Students ──────────────────────────────────────────────────────

def _build_filter(dept, section=None, semester=None, batch=None, search=None):
    clauses, params = [], []
    if dept and dept != 'ALL':
        clauses.append("department=%s"); params.append(dept)
    if section:
        clauses.append("section=%s"); params.append(section.upper())
    if semester:
        clauses.append("semester=%s"); params.append(str(semester))
    if batch:
        clauses.append("batch=%s"); params.append(batch)
    if search:
        clauses.append("(name LIKE %s OR roll LIKE %s)")
        params += [f'%{search}%', f'%{search}%']
    where = ("WHERE " + " AND ".join(clauses)) if clauses else ""
    return where, params

def get_students(dept='ALL', section=None, semester=None, batch=None, search=None) -> list:
    conn  = get_conn()
    cur   = conn.cursor()
    where, params = _build_filter(dept, section, semester, batch, search)
    cur.execute(f"SELECT * FROM students {where} ORDER BY roll", params)
    rows  = _rows_to_dicts(cur, cur.fetchall())
    cur.close()
    rows  = _attach_subjects(conn, rows)
    put_conn(conn)
    return rows

def find_student(roll: str) -> dict:
    conn = get_conn()
    cur  = conn.cursor()
    cur.execute("SELECT * FROM students WHERE roll=%s", (roll.upper(),))
    row  = cur.fetchone()
    if not row:
        cur.close(); put_conn(conn); return None
    s = _row_to_dict(cur, row)
    cur.close()
    s = _attach_subjects(conn, [s])[0]
    put_conn(conn)
    return s

def student_exists(roll: str) -> bool:
    conn = get_conn()
    cur  = conn.cursor()
    cur.execute("SELECT 1 FROM students WHERE roll=%s", (roll.upper(),))
    exists = cur.fetchone() is not None
    cur.close(); put_conn(conn)
    return exists

def _upsert_subjects(conn, roll, subjects: dict):
    cur = conn.cursor()
    for subj, vals in subjects.items():
        cur.execute(
            """INSERT INTO subject_marks (roll, subject, attendance, internal, external)
               VALUES (%s,%s,%s,%s,%s)
               ON CONFLICT (roll, subject) DO UPDATE SET
                 attendance=EXCLUDED.attendance,
                 internal=EXCLUDED.internal,
                 external=EXCLUDED.external""",
            (roll, subj, vals.get('attendance', 0), vals.get('internal', 0), vals.get('external', 0))
        )
    cur.close()

def insert_student(s: dict):
    conn = get_conn()
    cur  = conn.cursor()
    cur.execute(
        """INSERT INTO students
           (roll,name,section,department,semester,batch,cgpa,attendance,backlogs,internal,external)
           VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)""",
        (s['roll'].upper(), s['name'], s.get('section','SEC-1').upper(),
         s.get('department','CSE').upper(), str(s.get('semester','1')),
         s.get('batch',''), float(s.get('cgpa',0)), int(s.get('attendance',0)),
         int(s.get('backlogs',0)), int(s.get('internal',0)), int(s.get('external',0)))
    )
    conn.commit()
    cur.close()
    if s.get('subjects'):
        _upsert_subjects(conn, s['roll'].upper(), s['subjects'])
        conn.commit()
    put_conn(conn)

def update_student(roll: str, s: dict):
    conn = get_conn()
    cur  = conn.cursor()
    cur.execute(
        """UPDATE students SET
           name=%s, section=%s, department=%s, semester=%s, batch=%s,
           cgpa=%s, attendance=%s, backlogs=%s, internal=%s, external=%s,
           updated_at=CURRENT_TIMESTAMP
           WHERE roll=%s""",
        (s['name'], s.get('section', s.get('section','SEC-1')).upper(),
         s.get('department', s.get('department','CSE')).upper(), str(s.get('semester', s.get('semester','1'))),
         s.get('batch', s.get('batch','')), float(s.get('cgpa', s.get('cgpa',0))), 
         int(s.get('attendance', s.get('attendance',0))),
         int(s.get('backlogs', s.get('backlogs',0))), int(s.get('internal', s.get('internal',0))), 
         int(s.get('external', s.get('external',0))),
         roll.upper())
    )
    conn.commit()
    cur.close()
    if s.get('subjects'):
        _upsert_subjects(conn, roll.upper(), s['subjects'])
        conn.commit()
    put_conn(conn)

def delete_student(roll: str):
    conn = get_conn()
    cur  = conn.cursor()
    cur.execute("DELETE FROM students WHERE roll=%s", (roll.upper(),))
    conn.commit(); cur.close(); put_conn(conn)

def count_students() -> int:
    conn = get_conn()
    cur  = conn.cursor()
    cur.execute("SELECT COUNT(*) FROM students")
    n = cur.fetchone()[0]
    cur.close(); put_conn(conn)
    return n

def bulk_insert_students(students: list):
    """Fast bulk insert used by seed_data."""
    conn = get_conn()
    cur  = conn.cursor()
    cur.executemany(
        """INSERT INTO students
           (roll,name,section,department,semester,batch,cgpa,attendance,backlogs,internal,external)
           VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
           ON CONFLICT (roll) DO NOTHING""",
        [(s['roll'], s['name'], s['section'], s['department'], s['semester'],
          s['batch'], s['cgpa'], s['attendance'], s['backlogs'], s['internal'], s['external'])
         for s in students]
    )
    conn.commit()
    cur.close()
    # Insert subject marks
    cur = conn.cursor()
    rows = []
    for s in students:
        for subj, vals in s.get('subjects', {}).items():
            rows.append((s['roll'], subj, vals['attendance'], vals['internal'], vals['external']))
    if rows:
        cur.executemany(
            """INSERT INTO subject_marks (roll, subject, attendance, internal, external)
               VALUES (%s,%s,%s,%s,%s)
               ON CONFLICT (roll, subject) DO NOTHING""",
            rows
        )
        conn.commit()
    cur.close(); put_conn(conn)
