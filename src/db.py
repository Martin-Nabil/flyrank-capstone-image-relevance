import os
import psycopg
from psycopg.rows import dict_row
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.environ["DATABASE_URL"]

def get_db():
    return psycopg.connect(DATABASE_URL, row_factory=dict_row)

def init_db():
    conn = get_db()
    conn.execute("""
        CREATE TABLE IF NOT EXISTS images (
            id SERIAL PRIMARY KEY,
            filename TEXT NOT NULL UNIQUE,
            category TEXT NOT NULL,
            source_url TEXT,
            tags JSONB,
            caption TEXT,
            primary_subject TEXT,
            confidence FLOAT,
            embedding JSONB,
            needs_review BOOLEAN NOT NULL DEFAULT false,
            processed_at TIMESTAMPTZ,
            created_at TIMESTAMPTZ NOT NULL DEFAULT now()
        )
    """)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS posts (
            id SERIAL PRIMARY KEY,
            title TEXT NOT NULL,
            body TEXT NOT NULL,
            primary_subject TEXT,
            embedding JSONB,
            created_at TIMESTAMPTZ NOT NULL DEFAULT now()
        )
    """)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS suggestions (
            id SERIAL PRIMARY KEY,
            post_id INTEGER NOT NULL REFERENCES posts(id),
            image_id INTEGER NOT NULL REFERENCES images(id),
            similarity_score FLOAT,
            status TEXT NOT NULL DEFAULT 'pending',
            rejection_reason TEXT,
            created_at TIMESTAMPTZ NOT NULL DEFAULT now()
        )
    """)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS cost_log (
            id SERIAL PRIMARY KEY,
            call_type TEXT NOT NULL,
            model TEXT NOT NULL,
            units INTEGER,
            cost_usd FLOAT NOT NULL DEFAULT 0,
            created_at TIMESTAMPTZ NOT NULL DEFAULT now()
        )
    """)
    conn.execute("CREATE INDEX IF NOT EXISTS idx_suggestions_post_id ON suggestions(post_id)")
    conn.execute("CREATE INDEX IF NOT EXISTS idx_suggestions_image_id ON suggestions(image_id)")
    conn.execute("CREATE INDEX IF NOT EXISTS idx_suggestions_status ON suggestions(status)")
    conn.commit()
    conn.close()
    print("Database initialized.")

if __name__ == "__main__":
    init_db()