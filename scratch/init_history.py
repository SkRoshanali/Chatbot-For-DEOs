import os
import psycopg2
from dotenv import load_dotenv

load_dotenv()

def create_history_table():
    url = os.environ.get('DATABASE_URL')
    if not url:
        print("DATABASE_URL not found")
        return

    try:
        conn = psycopg2.connect(url)
        cur = conn.cursor()
        cur.execute("""
            CREATE TABLE IF NOT EXISTS chat_history (
                id SERIAL PRIMARY KEY,
                username VARCHAR(50) NOT NULL,
                query TEXT NOT NULL,
                created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
            );
        """)
        conn.commit()
        cur.close()
        conn.close()
        print("Success: Chat history table is ready.")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    create_history_table()
