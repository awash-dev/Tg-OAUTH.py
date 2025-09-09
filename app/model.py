from .db import cursor, conn

# Sessions table
cursor.execute("""
CREATE TABLE IF NOT EXISTS sessions (
    phone TEXT PRIMARY KEY,
    string_session TEXT NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
)
""")

# Users table
cursor.execute("""
CREATE TABLE IF NOT EXISTS users (
    phone TEXT PRIMARY KEY,
    telegram_id BIGINT NOT NULL,
    username TEXT,
    first_name TEXT,
    last_name TEXT,
    bio TEXT,
    profile_photo TEXT,
    last_seen TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
)
""")

conn.commit()
