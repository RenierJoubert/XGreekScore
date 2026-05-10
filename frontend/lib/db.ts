import Database from "better-sqlite3";
import path from "path";

const DB_PATH = path.resolve(process.cwd(), "../greekrank.db");

let _db: Database.Database | null = null;

export function getDb(): Database.Database {
  if (!_db) {
    _db = new Database(DB_PATH, { readonly: true });
    _db.pragma("journal_mode = WAL");
  }
  return _db;
}

export interface Post {
  id: number;
  title: string;
  link: string;
  date: string;
  content: string;
  reply_count: number;
  deleted: number;
}

export interface Reply {
  id: number;
  post_id: number;
  author: string;
  date: string;
  content: string;
}

export interface PostsResult {
  posts: Post[];
  total: number;
  page: number;
  page_size: number;
  total_pages: number;
}

const PAGE_SIZE = 20;

export function queryPosts(params: {
  q?: string;
  from?: string;
  to?: string;
  page?: number;
}): PostsResult {
  const db = getDb();
  const { q, from, to, page = 1 } = params;
  const offset = (page - 1) * PAGE_SIZE;

  const conditions: string[] = [];
  const args: unknown[] = [];

  if (q) {
    conditions.push("(p.title LIKE ? OR p.content LIKE ?)");
    args.push(`%${q}%`, `%${q}%`);
  }
  if (from) {
    conditions.push("p.date >= ?");
    args.push(from);
  }
  if (to) {
    conditions.push("p.date <= ?");
    args.push(to);
  }

  const where = conditions.length ? `WHERE ${conditions.join(" AND ")}` : "";

  const total = (
    db.prepare(`SELECT COUNT(*) as n FROM posts p ${where}`).get(...args) as { n: number }
  ).n;

  const posts = db.prepare(
    `SELECT p.*, COUNT(r.id) as reply_count
     FROM posts p
     LEFT JOIN replies r ON r.post_id = p.id
     ${where}
     GROUP BY p.id
     ORDER BY p.date DESC
     LIMIT ? OFFSET ?`
  ).all(...args, PAGE_SIZE, offset) as Post[];

  return { posts, total, page, page_size: PAGE_SIZE, total_pages: Math.ceil(total / PAGE_SIZE) };
}

export function getPost(id: number): (Post & { replies: Reply[] }) | null {
  const db = getDb();

  const post = db.prepare(
    `SELECT p.*, COUNT(r.id) as reply_count
     FROM posts p
     LEFT JOIN replies r ON r.post_id = p.id
     WHERE p.id = ?
     GROUP BY p.id`
  ).get(id) as Post | undefined;

  if (!post) return null;

  const replies = db.prepare(
    "SELECT * FROM replies WHERE post_id = ? ORDER BY id ASC"
  ).all(id) as Reply[];

  return { ...post, replies };
}
