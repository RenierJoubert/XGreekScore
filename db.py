import sqlite3


def init_db(db_path: str) -> sqlite3.Connection:
    conn = sqlite3.connect(db_path)
    conn.execute("PRAGMA journal_mode=WAL")
    conn.executescript("""
        CREATE TABLE IF NOT EXISTS posts (
            id           INTEGER PRIMARY KEY AUTOINCREMENT,
            title        TEXT    NOT NULL,
            link         TEXT    UNIQUE NOT NULL,
            date         TEXT,
            content      TEXT,
            deleted      INTEGER DEFAULT 0,
            cluster_id   INTEGER DEFAULT -1,
            cluster_hash TEXT
        );

        CREATE TABLE IF NOT EXISTS replies (
            id      INTEGER PRIMARY KEY AUTOINCREMENT,
            post_id INTEGER NOT NULL REFERENCES posts(id),
            author  TEXT,
            date    TEXT,
            content TEXT
        );
    """)
    cols = {row[1] for row in conn.execute("PRAGMA table_info(posts)")}
    if "deleted" not in cols:
        conn.execute("ALTER TABLE posts ADD COLUMN deleted INTEGER DEFAULT 0")
    if "cluster_id" not in cols:
        conn.execute("ALTER TABLE posts ADD COLUMN cluster_id INTEGER DEFAULT -1")
    if "cluster_hash" not in cols:
        conn.execute("ALTER TABLE posts ADD COLUMN cluster_hash TEXT")
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


def mark_deleted_posts(conn: sqlite3.Connection, found_links: set[str]) -> tuple[int, int]:
    """
    Compares found_links against the DB to sync the deleted flag.
    Posts absent from found_links are marked deleted=1.
    Posts that reappeared (deleted=1 but present in found_links) are restored to deleted=0.
    Returns (newly_deleted, restored).

    Guard: if found_links has fewer than 50 entries the scrape likely failed
    partway through, so this function is a no-op to avoid false positives.
    """
    if len(found_links) < 50:
        print(f"  [deletion sweep] only {len(found_links)} links found — skipping to avoid false deletions")
        return 0, 0

    conn.execute("CREATE TEMP TABLE IF NOT EXISTS _seen_links (link TEXT PRIMARY KEY)")
    conn.execute("DELETE FROM _seen_links")
    conn.executemany("INSERT OR IGNORE INTO _seen_links VALUES (?)", [(l,) for l in found_links])

    cur = conn.execute("""
        UPDATE posts SET deleted = 1
        WHERE link NOT IN (SELECT link FROM _seen_links) AND deleted = 0
    """)
    newly_deleted = cur.rowcount

    cur = conn.execute("""
        UPDATE posts SET deleted = 0
        WHERE link IN (SELECT link FROM _seen_links) AND deleted = 1
    """)
    restored = cur.rowcount

    conn.commit()
    return newly_deleted, restored
