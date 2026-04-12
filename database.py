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
    id          INT AUTO_INCREMENT PRIMARY KEY,
    branchcode  INT          NOT NULL UNIQUE,
    shortname   VARCHAR(16)  NOT NULL UNIQUE,
    fullname    VARCHAR(128) NOT NULL DEFAULT '',
    hod         VARCHAR(128) NOT NULL DEFAULT '',
    created_at  DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_shortname (shortname)
);

CREATE TABLE IF NOT EXISTS subjects (
    id          INT AUTO_INCREMENT PRIMARY KEY,
    subject_code VARCHAR(16) NOT NULL UNIQUE,
    subject_name VARCHAR(128) NOT NULL,
    credits     INT          NOT NULL DEFAULT 3,
    semester    VARCHAR(4)   NOT NULL DEFAULT '1',
    department  VARCHAR(32)  NOT NULL DEFAULT 'CSE',
    INDEX idx_subject_code (subject_code),
    INDEX idx_semester (semester),
    INDEX idx_department (department)
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
    result      ENUM('Pass','Fail','Pending') NOT NULL DEFAULT 'Pending',
    created_at  DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at  DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX idx_roll (roll),
    INDEX idx_section (section),
    INDEX idx_department (department),
    INDEX idx_semester (semester),
    INDEX idx_batch (batch),
    INDEX idx_cgpa (cgpa),
    INDEX idx_attendance (attendance),
    INDEX idx_dept_section (department, section),
    INDEX idx_name (name),
    INDEX idx_result (result)
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
    id            INT AUTO_INCREMENT PRIMARY KEY,
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
    UNIQUE KEY uq_roll_subject (roll, subject),
    FOREIGN KEY (roll) REFERENCES students(roll) ON DELETE CASCADE,
    INDEX idx_subject (subject),
    INDEX idx_roll_subject (roll, subject),
    INDEX idx_grade (grade)
);

CREATE INDEX IF NOT EXISTS idx_subject ON subject_marks (subject);
CREATE INDEX IF NOT EXISTS idx_roll_subject ON subject_marks (roll, subject);
"""

def init_db():
    """Create database and tables if they don't exist."""
    cfg = {k: v for k, v in DB_CONFIG.items() if k != 'database'}
    conn = mysql.connector.connect(**cfg)
    cur  = conn.cursor()
    cur.execute(CREATE_DB_SQL)
    conn.commit()
    cur.close()
    conn.close()

    conn = mysql.connector.connect(**DB_CONFIG)
    cur  = conn.cursor()
    for stmt in SCHEMA_SQL.strip().split(';'):
        stmt = stmt.strip()
        if stmt:
            try:
                cur.execute(stmt)
            except Exception:
                pass

    # Add missing columns to existing tables (safe ALTER)
    migrations = [
        "ALTER TABLE students ADD COLUMN IF NOT EXISTS result ENUM('Pass','Fail','Pending') NOT NULL DEFAULT 'Pending'",
        "ALTER TABLE students ADD COLUMN IF NOT EXISTS current_year INT NOT NULL DEFAULT 1",
        "ALTER TABLE subject_marks ADD COLUMN IF NOT EXISTS subject_code VARCHAR(16) NOT NULL DEFAULT ''",
        "ALTER TABLE subject_marks ADD COLUMN IF NOT EXISTS total_classes INT NOT NULL DEFAULT 0",
        "ALTER TABLE subject_marks ADD COLUMN IF NOT EXISTS attended INT NOT NULL DEFAULT 0",
        "ALTER TABLE subject_marks ADD COLUMN IF NOT EXISTS total INT NOT NULL DEFAULT 0",
        "ALTER TABLE subject_marks ADD COLUMN IF NOT EXISTS grade VARCHAR(4) NOT NULL DEFAULT ''",
    ]
    for m in migrations:
        try:
            cur.execute(m)
        except Exception:
            pass

    conn.commit()
    cur.close()
    conn.close()

    # Seed departments and subjects
    _seed_departments_subjects()
    print("[MySQL] Schema ready.")


def _seed_departments_subjects():
    """Seed departments and subjects tables from Excel data."""
    conn = mysql.connector.connect(**DB_CONFIG)
    cur  = conn.cursor()

    # Departments from Excel
    departments = [
        (4, 'CSE', 'Computer Science & Engineering', 'Dr. Rao'),
        (2, 'ECE', 'Electronics & Communication Engineering', 'Dr. Kumar'),
        (3, 'MECH', 'Mechanical Engineering', ''),
        (5, 'CIVIL', 'Civil Engineering', ''),
        (6, 'MBA', 'Master of Business Administration', ''),
    ]
    for d in departments:
        try:
            cur.execute(
                "INSERT IGNORE INTO departments (branchcode, shortname, fullname, hod) VALUES (%s,%s,%s,%s)", d)
        except Exception:
            pass

    # Subjects from Excel (mapped to our subject codes)
    subjects = [
        ('CSE2',  'DBMS',  3, '3', 'CSE'),
        ('CSE3',  'OS',    4, '4', 'CSE'),
        ('CSE4',  'CN',    3, '5', 'CSE'),
        ('CSE5',  'Maths', 4, '6', 'CSE'),
        ('CSE6',  'DSA',   3, '7', 'CSE'),
        ('CSE7',  'DBMS',  4, '8', 'CSE'),
        ('CSE8',  'OS',    3, '1', 'CSE'),
        ('CSE9',  'CN',    4, '2', 'CSE'),
        ('CSE10', 'Maths', 3, '3', 'CSE'),
        ('CSE11', 'DSA',   4, '4', 'CSE'),
        ('CSE12', 'DBMS',  3, '5', 'CSE'),
        ('CSE13', 'OS',    4, '6', 'CSE'),
        ('CSE14', 'CN',    3, '7', 'CSE'),
        ('CSE15', 'Maths', 4, '8', 'CSE'),
    ]
    for s in subjects:
        try:
            cur.execute(
                "INSERT IGNORE INTO subjects (subject_code, subject_name, credits, semester, department) VALUES (%s,%s,%s,%s,%s)", s)
        except Exception:
            pass

    conn.commit()
    cur.close()
    conn.close()
