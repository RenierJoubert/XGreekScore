import sqlite3


def init_db(db_path: str) -> sqlite3.Connection:
    conn = sqlite3.connect(db_path)
    conn.execute("PRAGMA journal_mode=WAL")
    conn.executescript("""
        CREATE TABLE IF NOT EXISTS posts (
            id      INTEGER PRIMARY KEY AUTOINCREMENT,
            title   TEXT    NOT NULL,
            link    TEXT    UNIQUE NOT NULL,
            date    TEXT,
            content TEXT
        );

        CREATE TABLE IF NOT EXISTS replies (
            id      INTEGER PRIMARY KEY AUTOINCREMENT,
            post_id INTEGER NOT NULL REFERENCES posts(id),
            author  TEXT,
            date    TEXT,
            content TEXT
        );
    """)
    conn.commit()
    return conn


def insert_post(conn: sqlite3.Connection, title: str, link: str, date: str, content: str) -> int | None:
    """
    Insert a post and return its row id.
    Returns the existing row id if the link is already in the DB (duplicate).
    """
    try:
        cur = conn.execute(
            "INSERT INTO posts (title, link, date, content) VALUES (?, ?, ?, ?)",
            (title, link, date, content),
        )
        conn.commit()
        return cur.lastrowid
    except sqlite3.IntegrityError:
        row = conn.execute("SELECT id FROM posts WHERE link = ?", (link,)).fetchone()
        return row[0] if row else None


def insert_reply(conn: sqlite3.Connection, post_id: int, author: str, date: str, content: str) -> None:
    conn.execute(
        "INSERT INTO replies (post_id, author, date, content) VALUES (?, ?, ?, ?)",
        (post_id, author, date, content),
    )
    conn.commit()
