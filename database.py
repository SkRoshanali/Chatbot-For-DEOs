"""
MySQL database connection and schema setup.
Uses mysql-connector-python with a simple connection pool.
"""
import os
import mysql.connector
from mysql.connector import pooling

DB_CONFIG = {
    'host':     os.environ.get('MYSQL_HOST',     'localhost'),
    'port':     int(os.environ.get('MYSQL_PORT', 3306)),
    'user':     os.environ.get('MYSQL_USER',     'root'),
    'password': os.environ.get('MYSQL_PASSWORD', 'nandu3742L@'),
    'database': os.environ.get('MYSQL_DATABASE', 'deo_chatbot'),
}

_pool = None

def get_pool():
    global _pool
    if _pool is None:
        _pool = pooling.MySQLConnectionPool(
            pool_name='deo_pool',
            pool_size=10,
            **DB_CONFIG
        )
    return _pool

def get_conn():
    return get_pool().get_connection()

# ── Schema ────────────────────────────────────────────────────────

CREATE_DB_SQL = f"CREATE DATABASE IF NOT EXISTS `{DB_CONFIG['database']}`"

SCHEMA_SQL = """
CREATE TABLE IF NOT EXISTS users (
    id          INT AUTO_INCREMENT PRIMARY KEY,
    username    VARCHAR(64)  NOT NULL UNIQUE,
    password    VARCHAR(256) NOT NULL,
    role        ENUM('Admin','DEO','HOD') NOT NULL DEFAULT 'DEO',
    dept        VARCHAR(32)  NOT NULL DEFAULT 'CSE',
    otp_secret  VARCHAR(64)  NOT NULL,
    created_at  DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS students (
    id          INT AUTO_INCREMENT PRIMARY KEY,
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
    created_at  DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at  DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS subject_marks (
    id          INT AUTO_INCREMENT PRIMARY KEY,
    roll        VARCHAR(20)  NOT NULL,
    subject     VARCHAR(16)  NOT NULL,
    attendance  INT          NOT NULL DEFAULT 0,
    internal    INT          NOT NULL DEFAULT 0,
    external    INT          NOT NULL DEFAULT 0,
    UNIQUE KEY uq_roll_subject (roll, subject),
    FOREIGN KEY (roll) REFERENCES students(roll) ON DELETE CASCADE
);
"""

def init_db():
    """Create database and tables if they don't exist."""
    # Connect without database first to create it
    cfg = {k: v for k, v in DB_CONFIG.items() if k != 'database'}
    conn = mysql.connector.connect(**cfg)
    cur  = conn.cursor()
    cur.execute(CREATE_DB_SQL)
    conn.commit()
    cur.close()
    conn.close()

    # Now connect with database and create tables
    conn = mysql.connector.connect(**DB_CONFIG)
    cur  = conn.cursor()
    for stmt in SCHEMA_SQL.strip().split(';'):
        stmt = stmt.strip()
        if stmt:
            cur.execute(stmt)
    conn.commit()
    cur.close()
    conn.close()
    print("[MySQL] Schema ready.")
