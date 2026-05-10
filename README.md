# XGreekScore
 
A full-stack archival and search platform for UBC GreekRank forum posts. Scrapes, stores, and serves forum posts including those since deleted from the site, uses a Next.js frontend backed by SQLite.
 
## Architecture
 
```
xsgreekscore/
├── main.py        # CLI entry point 
├── scraper.py     # Async Playwright scraper with configurable concurrency
├── db.py          # SQLite schema, WAL mode, deduplication on insert
├── utils.py       # Playwright element helpers
└── frontend/      # Next.js 16 App Router
    ├── app/
    │   ├── page.tsx            # Infinite-scroll grid with keyword + date search
    │   ├── posts/[id]/page.tsx # Post detail with reply thread
    │   └── api/posts/          # REST API routes
    └── lib/db.ts               # better-sqlite3 query layer
```
 
## Stack
 
| Layer | Technology |
|---|---|
| Scraper | Python 3.14, Playwright (Chromium), asyncio |
| Storage | SQLite (WAL mode), better-sqlite3 |
| Frontend | Next.js 16, TypeScript, Tailwind CSS |
| Runtime | Node.js, Python venv |
 
## Database Schema
 
```sql
CREATE TABLE posts (
    id      INTEGER PRIMARY KEY AUTOINCREMENT,
    title   TEXT    NOT NULL,
    link    TEXT    UNIQUE NOT NULL,
    date    TEXT,
    content TEXT,
    deleted INTEGER NOT NULL DEFAULT 0
);
 
CREATE TABLE replies (
    id      INTEGER PRIMARY KEY AUTOINCREMENT,
    post_id INTEGER NOT NULL REFERENCES posts(id),
    author  TEXT,
    date    TEXT,
    content TEXT
);
```