import sqlite3

DB_NAME = "cloud_storage.db"

def get_db_connection():
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn

def init_db():
    conn = get_db_connection()
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE NOT NULL,
        password_hash TEXT NOT NULL,
        role TEXT NOT NULL DEFAULT 'user',
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP
    )''')
    c.execute('''CREATE TABLE IF NOT EXISTS files (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        original_name TEXT NOT NULL,
        file_identifier TEXT UNIQUE NOT NULL,
        file_size INTEGER DEFAULT 0,
        file_hash TEXT,
        storage_mode TEXT DEFAULT 'distributed',
        upload_time DATETIME DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (user_id) REFERENCES users (id)
    )''')
    c.execute('''CREATE TABLE IF NOT EXISTS file_parts (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        file_id INTEGER NOT NULL,
        part_name TEXT NOT NULL,
        node TEXT NOT NULL,
        sequence_order INTEGER NOT NULL,
        size INTEGER NOT NULL,
        original_chunk_size INTEGER DEFAULT 0,
        FOREIGN KEY (file_id) REFERENCES files (id) ON DELETE CASCADE
    )''')
    conn.commit()
    conn.close()

if __name__ == "__main__":
    init_db()
