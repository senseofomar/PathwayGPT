import sqlite3
import uuid
from datetime import datetime

DB_NAME = "bookfriend.db"


def get_db():
    """Connect to the database (creates it if missing)."""
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row  # Allows accessing columns by name
    return conn


def init_db():
    """Create the tables if they don't exist."""
    conn = get_db()
    c = conn.cursor()

    # 1. Users Table (Who is talking?)
    c.execute('''
              CREATE TABLE IF NOT EXISTS users
              (
                  id
                  TEXT
                  PRIMARY
                  KEY,
                  username
                  TEXT,
                  created_at
                  TEXT
              )
              ''')

    # 2. Books Table (What are they reading?)
    c.execute('''
              CREATE TABLE IF NOT EXISTS books
              (
                  id
                  TEXT
                  PRIMARY
                  KEY,
                  title
                  TEXT,
                  filename
                  TEXT,
                  index_path
                  TEXT,
                  processed_at
                  TEXT
              )
              ''')

    # 3. Chat History (Context for the AI)
    c.execute('''
              CREATE TABLE IF NOT EXISTS messages
              (
                  id
                  INTEGER
                  PRIMARY
                  KEY
                  AUTOINCREMENT,
                  user_id
                  TEXT,
                  book_id
                  TEXT,
                  sender
                  TEXT, -- 'user' or 'bot'
                  content
                  TEXT,
                  chapter_limit
                  INTEGER,
                  timestamp
                  TEXT,
                  FOREIGN
                  KEY
              (
                  user_id
              ) REFERENCES users
              (
                  id
              ),
                  FOREIGN KEY
              (
                  book_id
              ) REFERENCES books
              (
                  id
              )
                  )
              ''')

    conn.commit()
    conn.close()
    print("✅ Database initialized (Tables: users, books, messages).")


# === Helper Functions for the API ===

def register_book(title, filename, index_path):
    """Save a new book's metadata."""
    conn = get_db()
    book_id = str(uuid.uuid4())[:8]  # Short ID like 'a1b2c3d4'
    conn.execute(
        "INSERT INTO books (id, title, filename, index_path, processed_at) VALUES (?, ?, ?, ?, ?)",
        (book_id, title, filename, index_path, datetime.now().isoformat())
    )
    conn.commit()
    conn.close()
    return book_id


def log_message(user_id, book_id, sender, content, chapter_limit=0):
    """Save a chat message to history."""
    conn = get_db()
    conn.execute(
        "INSERT INTO messages (user_id, book_id, sender, content, chapter_limit, timestamp) VALUES (?, ?, ?, ?, ?, ?)",
        (user_id, book_id, sender, content, chapter_limit, datetime.now().isoformat())
    )
    conn.commit()
    conn.close()


def get_chat_history(user_id, book_id, limit=6):
    """Retrieve recent context for the AI."""
    conn = get_db()
    cursor = conn.execute('''
                          SELECT sender, content
                          FROM messages
                          WHERE user_id = ?
                            AND book_id = ?
                          ORDER BY id DESC LIMIT ?
                          ''', (user_id, book_id, limit))

    rows = cursor.fetchall()
    conn.close()

    # Return in reverse order (chronological) for the AI
    history = [{"role": r["sender"], "content": r["content"]} for r in rows]
    return history[::-1]