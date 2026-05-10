"use client";

import { useState, useEffect, useRef, useCallback } from "react";
import Link from "next/link";

interface Post {
  id: number;
  title: string;
  date: string;
  content: string;
  reply_count: number;
  deleted: number;
}

interface Result {
  posts: Post[];
  total: number;
  page: number;
  total_pages: number;
}

const CARD_H = 220;

export default function Home() {
  const [query, setQuery] = useState("");
  const [from, setFrom]   = useState("");
  const [to, setTo]       = useState("");

  const [posts, setPosts]         = useState<Post[]>([]);
  const [total, setTotal]         = useState(0);
  const [loading, setLoading]     = useState(false);

  const pageRef     = useRef(1);
  const hasMoreRef  = useRef(true);
  const loadingRef  = useRef(false);
  const sentinelRef = useRef<HTMLDivElement>(null);

  // Store latest filter values in refs so the observer closure always sees them
  const queryRef = useRef(query);
  const fromRef  = useRef(from);
  const toRef    = useRef(to);
  useEffect(() => { queryRef.current = query; }, [query]);
  useEffect(() => { fromRef.current  = from;  }, [from]);
  useEffect(() => { toRef.current    = to;    }, [to]);

  const fetchPage = useCallback(async (pageNum: number, reset: boolean) => {
    if (loadingRef.current) return;
    loadingRef.current = true;
    setLoading(true);

    const params = new URLSearchParams();
    if (queryRef.current) params.set("q", queryRef.current);
    if (fromRef.current)  params.set("from", fromRef.current);
    if (toRef.current)    params.set("to", toRef.current);
    params.set("page", String(pageNum));

    try {
      const res  = await fetch(`/api/posts?${params}`);
      const data: Result = await res.json();

      setPosts(prev => {
        const combined = reset ? data.posts : [...prev, ...data.posts];
        const seen = new Set<number>();
        return combined.filter(p => {
          if (seen.has(p.id)) return false;
          seen.add(p.id);
          return true;
        });
      });

      setTotal(data.total);
      pageRef.current    = pageNum;
      hasMoreRef.current = pageNum < data.total_pages;
    } finally {
      loadingRef.current = false;
      setLoading(false);
    }
  }, []);

  // Reset and reload when filters change
  useEffect(() => {
    pageRef.current    = 1;
    hasMoreRef.current = true;
    fetchPage(1, true);
  }, [query, from, to, fetchPage]);

  // Infinite scroll set to fire when user is within 600px of the bottom
  useEffect(() => {
    const onScroll = () => {
      const distFromBottom = document.documentElement.scrollHeight - window.scrollY - window.innerHeight;
      if (distFromBottom < 600 && hasMoreRef.current && !loadingRef.current) {
        fetchPage(pageRef.current + 1, false);
      }
    };
    window.addEventListener("scroll", onScroll, { passive: true });
    return () => window.removeEventListener("scroll", onScroll);
  }, [fetchPage]);

  return (
    <main style={{ minHeight: "100vh", background: "var(--light)", padding: "2.5rem 1.5rem" }}>

      {/* Header */}
      <header style={{ maxWidth: "1400px", margin: "0 auto 2.5rem" }}>
        <div style={{ textAlign: "center", marginBottom: "1.75rem" }}>
          <img
            src="/eye.png"
            alt="XGreekScore"
            style={{
              height: "clamp(8rem, 5vw, 10rem)",
              width: "auto",
              display: "inline-block",
              opacity: 0.9,
            }}
          />
        </div>

        <div style={{ display: "flex", flexDirection: "column", gap: "0.625rem", maxWidth: "700px", margin: "0 auto" }}>
          <input
            style={{
              background: "transparent", border: "1px solid var(--gray)",
              borderRadius: "6px", padding: "0.6rem 0.875rem",
              color: "var(--tertiary)", fontSize: "0.8rem",
              letterSpacing: "0.05em", width: "100%", outline: "none",
            }}
            placeholder="search posts..."
            value={query}
            onChange={e => setQuery(e.target.value)}
          />
          <div style={{ display: "flex", gap: "0.625rem", alignItems: "center" }}>
            <input type="date" style={{
              flex: 1, background: "transparent", border: "1px solid var(--gray)",
              borderRadius: "6px", padding: "0.5rem 0.75rem", color: "var(--dark)",
              fontSize: "0.75rem", outline: "none", colorScheme: "dark",
            }} value={from} onChange={e => setFrom(e.target.value)} />
            <span style={{ color: "var(--darkgray)", fontSize: "0.75rem" }}>—</span>
            <input type="date" style={{
              flex: 1, background: "transparent", border: "1px solid var(--gray)",
              borderRadius: "6px", padding: "0.5rem 0.75rem", color: "var(--dark)",
              fontSize: "0.75rem", outline: "none", colorScheme: "dark",
            }} value={to} onChange={e => setTo(e.target.value)} />
          </div>
        </div>

        {total > 0 && (
          <p style={{
            textAlign: "center", marginTop: "1rem", fontSize: "0.7rem",
            color: "var(--darkgray)", letterSpacing: "0.1em", textTransform: "uppercase",
          }}>
            {total.toLocaleString()} posts
          </p>
        )}
      </header>

      {/* Grid */}
      <div style={{
        maxWidth: "1400px",
        margin: "0 auto",
        display: "grid",
        gridTemplateColumns: "repeat(4, 1fr)",
        gridAutoRows: `${CARD_H}px`,
        border: "1px solid var(--gray)",
        borderRadius: "10px",
        overflow: "hidden",
      }}>
        {posts.map(post => (
          <Link
            key={post.id}
            href={`/posts/${post.id}`}
            style={{
              textDecoration: "none",
              display: "block",
              overflow: "hidden",
              borderRight: "1px solid var(--gray)",
              borderBottom: "1px solid var(--gray)",
            }}
          >
            <article
              style={{
                background: "var(--light)",
                padding: "1.125rem",
                height: `${CARD_H}px`,
                display: "flex",
                flexDirection: "column",
                gap: "0.5rem",
                overflow: "hidden",
                transition: "background 0.15s",
                cursor: "pointer",
                boxSizing: "border-box",
              }}
              onMouseEnter={e => (e.currentTarget.style.background = "#111113")}
              onMouseLeave={e => (e.currentTarget.style.background = "var(--light)")}
            >
              <div style={{ display: "flex", alignItems: "flex-start", gap: "0.5rem", flexShrink: 0 }}>
                <h2 style={{
                  fontSize: "0.8rem", fontWeight: 500, color: "var(--tertiary)",
                  lineHeight: 1.4, margin: 0, flex: 1, letterSpacing: "0.02em",
                  overflow: "hidden", display: "-webkit-box",
                  WebkitLineClamp: 2, WebkitBoxOrient: "vertical",
                }}>
                  {post.title}
                </h2>
                {post.deleted === 1 && (
                  <span style={{
                    fontSize: "0.6rem", fontWeight: 700, color: "#09090a",
                    background: "#ef4444", padding: "0.1rem 0.4rem",
                    borderRadius: "3px", letterSpacing: "0.08em", flexShrink: 0,
                  }}>
                    DELETED
                  </span>
                )}
              </div>

              <p style={{
                fontSize: "0.72rem", color: "var(--dark)", lineHeight: 1.55,
                margin: 0, flex: 1, overflow: "hidden",
                display: "-webkit-box", WebkitLineClamp: 5, WebkitBoxOrient: "vertical",
              }}>
                {post.content}
              </p>

              <div style={{
                display: "flex", justifyContent: "space-between", alignItems: "center",
                flexShrink: 0, paddingTop: "0.5rem", borderTop: "1px solid var(--highlight)",
              }}>
                <span style={{ fontSize: "0.75rem", color: "var(--darkgray)", letterSpacing: "0.04em" }}>
                  {post.date?.slice(0, 10)}
                </span>
                <span style={{ fontSize: "0.75rem", color: "var(--darkgray)", letterSpacing: "0.04em" }}>
                  {post.reply_count} {post.reply_count === 1 ? "reply" : "replies"}
                </span>
              </div>
            </article>
          </Link>
        ))}
      </div>

      {/* Sentinel — observer watches this to trigger next page */}
      <div ref={sentinelRef} style={{ height: "1px", marginTop: "2rem" }} />

      {loading && (
        <p style={{
          textAlign: "center", marginTop: "2rem", fontSize: "0.7rem",
          color: "var(--darkgray)", letterSpacing: "0.12em", textTransform: "uppercase",
        }}>
          loading...
        </p>
      )}

      {!hasMoreRef.current && posts.length > 0 && !loading && (
        <p style={{
          textAlign: "center", marginTop: "2rem", fontSize: "0.7rem",
          color: "var(--darkgray)", letterSpacing: "0.12em", textTransform: "uppercase",
        }}>
          — end —
        </p>
      )}
    </main>
  );
}
