"""
Neon PostgreSQL database connection and schema setup.
Uses psycopg2 with a simple connection pool.
"""
import os
import psycopg2
from psycopg2 import pool
from urllib.parse import urlparse
from dotenv import load_dotenv

# Load .env variables
load_dotenv()

# Get connection string from .env
DATABASE_URL = os.environ.get('DATABASE_URL')

# Fallback components if DATABASE_URL is not set
POSTGRES_HOST = os.environ.get('POSTGRES_HOST', 'localhost')
POSTGRES_PORT = os.environ.get('POSTGRES_PORT', 5432)
POSTGRES_USER = os.environ.get('POSTGRES_USER', 'postgres')
POSTGRES_PASSWORD = os.environ.get('POSTGRES_PASSWORD', '')
POSTGRES_DATABASE = os.environ.get('POSTGRES_DATABASE', 'deo_chatbot')

_pool = None

def get_pool():
    global _pool
    if _pool is None:
        if DATABASE_URL:
            _pool = psycopg2.pool.SimpleConnectionPool(
                1, 20,
                DATABASE_URL,
                sslmode='require'
            )
        else:
            _pool = psycopg2.pool.SimpleConnectionPool(
                1, 20,
                host=POSTGRES_HOST,
                port=POSTGRES_PORT,
                user=POSTGRES_USER,
                password=POSTGRES_PASSWORD,
                database=POSTGRES_DATABASE,
                sslmode='require'
            )
    return _pool

def get_conn():
    return get_pool().getconn()

def put_conn(conn):
    if _pool:
        _pool.putconn(conn)

# ── Schema ────────────────────────────────────────────────────────

SCHEMA_SQL = """
CREATE TABLE IF NOT EXISTS departments (
    id          SERIAL PRIMARY KEY,
    branchcode  INT          NOT NULL UNIQUE,
    shortname   VARCHAR(16)  NOT NULL UNIQUE,
    fullname    VARCHAR(128) NOT NULL DEFAULT '',
    hod         VARCHAR(128) NOT NULL DEFAULT '',
    created_at  TIMESTAMP    NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS subjects (
    id          SERIAL PRIMARY KEY,
    subject_code VARCHAR(16) NOT NULL UNIQUE,
    subject_name VARCHAR(128) NOT NULL,
    credits     INT          NOT NULL DEFAULT 3,
    semester    VARCHAR(4)   NOT NULL DEFAULT '1',
    department  VARCHAR(32)  NOT NULL DEFAULT 'CSE'
);

CREATE TABLE IF NOT EXISTS users (
    id          SERIAL PRIMARY KEY,
    username    VARCHAR(64)  NOT NULL UNIQUE,
    password    VARCHAR(256) NOT NULL,
    role        VARCHAR(32)  NOT NULL DEFAULT 'Others',
    dept        VARCHAR(32)  NOT NULL DEFAULT 'CSE',
    otp_secret  VARCHAR(64)  NOT NULL,
    theme_pref  VARCHAR(10)  NOT NULL DEFAULT 'light',
    sender_email VARCHAR(128) NULL,
    sender_pw    VARCHAR(128) NULL,
    created_at  TIMESTAMP    NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_users_username ON users (username);
CREATE INDEX IF NOT EXISTS idx_users_role ON users (role);
CREATE INDEX IF NOT EXISTS idx_users_dept ON users (dept);

CREATE TABLE IF NOT EXISTS students (
    id          SERIAL PRIMARY KEY,
    roll        VARCHAR(20)  NOT NULL UNIQUE,
    name        VARCHAR(128) NOT NULL,
    section     VARCHAR(16)  NOT NULL,
    department  VARCHAR(32)  NOT NULL DEFAULT 'CSE',
    semester    VARCHAR(4)   NOT NULL DEFAULT '3',
    batch       VARCHAR(16)  NOT NULL DEFAULT '2023-27',
    current_year INT         NOT NULL DEFAULT 1,
    cgpa        FLOAT        NOT NULL DEFAULT 0,
    attendance  INT          NOT NULL DEFAULT 0,
    backlogs    INT          NOT NULL DEFAULT 0,
    internal    INT          NOT NULL DEFAULT 0,
    external    INT          NOT NULL DEFAULT 0,
    result      VARCHAR(32)  NOT NULL DEFAULT 'Pending',
    created_at  TIMESTAMP    NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at  TIMESTAMP    NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_roll ON students (roll);
CREATE INDEX IF NOT EXISTS idx_section ON students (section);
CREATE INDEX IF NOT EXISTS idx_department ON students (department);
CREATE INDEX IF NOT EXISTS idx_semester ON students (semester);
CREATE INDEX IF NOT EXISTS idx_batch ON students (batch);
CREATE INDEX IF NOT EXISTS idx_cgpa ON students (cgpa);
CREATE INDEX IF NOT EXISTS idx_attendance ON students (attendance);
CREATE INDEX IF NOT EXISTS idx_dept_section ON students (department, section);
CREATE INDEX IF NOT EXISTS idx_name ON students (name);

CREATE TABLE IF NOT EXISTS subject_marks (
    id            SERIAL PRIMARY KEY,
    roll          VARCHAR(20)  NOT NULL,
    subject       VARCHAR(16)  NOT NULL,
    subject_code  VARCHAR(16)  NOT NULL DEFAULT '',
    attendance    INT          NOT NULL DEFAULT 0,
    total_classes INT          NOT NULL DEFAULT 0,
    attended      INT          NOT NULL DEFAULT 0,
    internal      INT          NOT NULL DEFAULT 0,
    external      INT          NOT NULL DEFAULT 0,
    total         INT          NOT NULL DEFAULT 0,
    grade         VARCHAR(4)   NOT NULL DEFAULT '',
    UNIQUE (roll, subject),
    CONSTRAINT fk_roll FOREIGN KEY (roll) REFERENCES students(roll) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_subject ON subject_marks (subject);
CREATE INDEX IF NOT EXISTS idx_roll_subject ON subject_marks (roll, subject);

CREATE TABLE IF NOT EXISTS chat_history (
    id          SERIAL PRIMARY KEY,
    username    VARCHAR(64) NOT NULL,
    query       TEXT NOT NULL,
    created_at  TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX IF NOT EXISTS idx_chat_username ON chat_history (username);
"""

def init_db():
    """Create database and tables if they don't exist."""
    conn = get_conn()
    cur  = conn.cursor()
    try:
        # Split SCHEMA_SQL by semicolon and execute each statement
        for stmt in SCHEMA_SQL.strip().split(';'):
            stmt = stmt.strip()
            if stmt:
                try:
                    cur.execute(stmt)
                except Exception as e:
                    print(f"[Schema Error] {e}")
        conn.commit()
    except Exception as e:
        print(f"[Init DB Error] {e}")
        conn.rollback()
    finally:
        cur.close()
        put_conn(conn)

    # Seed departments and subjects
    _seed_departments_subjects()
    print("[PostgreSQL] Schema ready.")


def _seed_departments_subjects():
    """Seed departments and subjects tables."""
    conn = get_conn()
    cur  = conn.cursor()

    try:
        # Departments
        departments = [
            (4, 'CSE', 'Computer Science & Engineering', 'Dr. Rao'),
            (2, 'ECE', 'Electronics & Communication Engineering', 'Dr. Kumar'),
            (3, 'MECH', 'Mechanical Engineering', ''),
            (5, 'CIVIL', 'Civil Engineering', ''),
            (6, 'MBA', 'Master of Business Administration', ''),
        ]
        for d in departments:
            cur.execute(
                "INSERT INTO departments (branchcode, shortname, fullname, hod) VALUES (%s,%s,%s,%s) ON CONFLICT (shortname) DO NOTHING", d)

        # Subjects
        subjects = [
            ('CSE2',  'DBMS',  3, '3', 'CSE'),
            ('CSE3',  'OS',    4, '4', 'CSE'),
            ('CSE4',  'CN',    3, '5', 'CSE'),
            ('CSE5',  'Maths', 4, '6', 'CSE'),
            ('CSE6',  'DSA',   3, '7', 'CSE'),
            ('CSE8',  'OS',    3, '1', 'CSE'),
            ('CSE9',  'CN',    4, '2', 'CSE'),
        ]
        for s in subjects:
            cur.execute(
                "INSERT INTO subjects (subject_code, subject_name, credits, semester, department) VALUES (%s,%s,%s,%s,%s) ON CONFLICT (subject_code) DO NOTHING", s)

        conn.commit()
    except Exception as e:
        print(f"[Seed Error] {e}")
        conn.rollback()
    finally:
        cur.close()
        put_conn(conn)
