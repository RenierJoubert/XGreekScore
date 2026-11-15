import sqlite3


def init_db(db_path: str) -> sqlite3.Connection:
    conn = sqlite3.connect(db_path)
    # WAL mode so the frontend can read while the scraper is writing
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
            id           INTEGER PRIMARY KEY AUTOINCREMENT,
            post_id      INTEGER NOT NULL REFERENCES posts(id),
            author       TEXT,
            date         TEXT,
            content      TEXT,
            cluster_id   INTEGER DEFAULT -1,
            cluster_hash TEXT
        );

        -- Replies need to be unique because rescrapes revisit old posts to pick up their new replies
        CREATE UNIQUE INDEX IF NOT EXISTS replies_no_duplicates
            ON replies (post_id, author, date, content);
    """)
    conn.commit()
    return conn

# Insert the given post and return its row id, if it already exists just return the row id
def insert_post(conn: sqlite3.Connection, title: str, link: str, date: str, content: str) -> int:

    conn.execute(
        "INSERT INTO posts (title, link, date, content) VALUES (?, ?, ?, ?) ON CONFLICT (link) DO NOTHING",
        (title, link, date, content),
    )
    conn.commit()
    return conn.execute("SELECT id FROM posts WHERE link = ?", (link,)).fetchone()[0]


def insert_reply(conn: sqlite3.Connection, post_id: int, author: str, date: str, content: str) -> bool:
    cur = conn.execute(
        "INSERT INTO replies (post_id, author, date, content) VALUES (?, ?, ?, ?) ON CONFLICT DO NOTHING",
        (post_id, author, date, content),
    )
    conn.commit()
    return cur.rowcount == 1

# Compares the most recent scraped urls with the set of all scraped urls,
# updates deletion status if an old post url is not contained in the new set,
# or if an old post reappears. We can only be accurate once the entire site is
# scraped so if no reached_end ensures that. 
def mark_deleted_posts(
    conn: sqlite3.Connection, found_links: set[str], reached_end: bool
) -> tuple[int, int]:

    if not reached_end:
        print("scrape did not cleanly reach the end of the listing ")
        return 0, 0


    # Load recent scraped links into temp table
    conn.execute("CREATE TEMP TABLE IF NOT EXISTS _seen_links (link TEXT PRIMARY KEY)")
    conn.execute("DELETE FROM _seen_links") # incase the table is holding old urls
    conn.executemany("INSERT OR IGNORE INTO _seen_links VALUES (?)", [(link,) for link in found_links])

    # if an old url isnt in the new set it was deleted
    cur = conn.execute("""
        UPDATE posts SET deleted = 1
        WHERE link NOT IN (SELECT link FROM _seen_links) AND deleted = 0
    """)
    newly_deleted = cur.rowcount

    # if an old post was deleted by is in the new set, it wasnt deleted
    cur = conn.execute("""
        UPDATE posts SET deleted = 0
        WHERE link IN (SELECT link FROM _seen_links) AND deleted = 1
    """)
    restored = cur.rowcount

    conn.commit()
    return newly_deleted, restored
