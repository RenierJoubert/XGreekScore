import Database from "better-sqlite3";
import path from "path";

// TODO(comment): why this path only works when the server is started from inside frontend/
const DB_PATH = path.resolve(process.cwd(), "../greekrank.db");

let _db: Database.Database | null = null;

// TODO(comment): why one shared read-only connection (the scraper is the only writer)
export function getDb(): Database.Database {
  if (!_db) {
    _db = new Database(DB_PATH, { readonly: true });
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
  cluster_id: number;
  cluster_hash: string | null;
}

export interface Reply {
  id: number;
  post_id: number;
  author: string;
  date: string;
  content: string;
  cluster_hash: string | null;
}

export interface PostsResult {
  posts: Post[];
  total: number;
  page: number;
  page_size: number;
  total_pages: number;
}

const PAGE_SIZE = 20;

// TODO(comment): what each filter does, and that they combine with AND
export function queryPosts(params: {
  q?: string;
  from?: string;
  to?: string;
  page?: number;
  cluster?: string;
  reply_cluster?: string;
}): PostsResult {
  const db = getDb();
  const { q, from, to, page = 1, cluster, reply_cluster } = params;
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
    conditions.push("p.date < date(?, '+1 day')");
    args.push(to);
  }
  if (cluster) {
    conditions.push("p.cluster_hash = ?");
    args.push(cluster);
  }
  if (reply_cluster) {
    conditions.push("p.id IN (SELECT post_id FROM replies WHERE cluster_hash = ?)");
    args.push(reply_cluster);
  }

  const where = conditions.length ? `WHERE ${conditions.join(" AND ")}` : "";

  const total = (
    db.prepare(`SELECT COUNT(*) as n FROM posts p ${where}`).get(...args) as { n: number }
  ).n;

  // TODO(comment): why p.id is in the ORDER BY (posts with the same timestamp would otherwise shuffle between pages)
  const posts = db.prepare(
    `SELECT p.*, COUNT(r.id) as reply_count
     FROM posts p
     LEFT JOIN replies r ON r.post_id = p.id
     ${where}
     GROUP BY p.id
     ORDER BY p.date DESC, p.id DESC
     LIMIT ? OFFSET ?`
  ).all(...args, PAGE_SIZE, offset) as Post[];

  return { posts, total, page, page_size: PAGE_SIZE, total_pages: Math.ceil(total / PAGE_SIZE) };
}

export function getPost(id: number): (Post & { replies: Reply[] }) | null {
  const db = getDb();

  const post = db.prepare("SELECT * FROM posts WHERE id = ?").get(id) as Omit<Post, "reply_count"> | undefined;
  if (!post) return null;

  const replies = db.prepare(
    "SELECT * FROM replies WHERE post_id = ? ORDER BY id ASC"
  ).all(id) as Reply[];

  return { ...post, reply_count: replies.length, replies };
}
