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
    cgpa        FLOAT        NOT NULL DEFAULT 0,
    attendance  INT          NOT NULL DEFAULT 0,
    backlogs    INT          NOT NULL DEFAULT 0,
    internal    INT          NOT NULL DEFAULT 0,
    external    INT          NOT NULL DEFAULT 0,
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
    id          SERIAL PRIMARY KEY,
    roll        VARCHAR(20)  NOT NULL,
    subject     VARCHAR(16)  NOT NULL,
    attendance  INT          NOT NULL DEFAULT 0,
    internal    INT          NOT NULL DEFAULT 0,
    external    INT          NOT NULL DEFAULT 0,
    UNIQUE (roll, subject),
    FOREIGN KEY (roll) REFERENCES students(roll) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_subject ON subject_marks (subject);
CREATE INDEX IF NOT EXISTS idx_roll_subject ON subject_marks (roll, subject);
"""

def init_db():
    """Create tables if they don't exist."""
    print("[PostgreSQL] Initializing schema...")
    conn = None
    try:
        conn = get_conn()
        cur  = conn.cursor()
        for stmt in SCHEMA_SQL.strip().split(';'):
            stmt = stmt.strip()
            if stmt:
                cur.execute(stmt)
        conn.commit()
        cur.close()
        print("[PostgreSQL] Schema ready.")
    except Exception as e:
        print(f"[PostgreSQL] Error initializing DB: {e}")
        if conn:
            conn.rollback()
    finally:
        if conn:
            put_conn(conn)
