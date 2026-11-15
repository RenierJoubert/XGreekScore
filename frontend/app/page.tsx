"use client";

import { useState, useEffect, useRef, useCallback, Suspense } from "react";
import { useSearchParams, useRouter } from "next/navigation";
import Image from "next/image";
import type { Post, PostsResult } from "@/lib/db";
import PostCard from "@/components/PostCard";
import logo from "@/public/eye.png";

const LOAD_MORE_DISTANCE_PX = 600;

const dateInputClass =
  "flex-1 border border-border bg-transparent px-3 py-2 text-xs text-secondary outline-none scheme-dark";

function HomeContent() {
  const searchParams = useSearchParams();
  const router = useRouter();

  const cluster = searchParams.get("cluster") ?? "";
  const replyCluster = searchParams.get("reply_cluster") ?? "";

  const [query, setQuery] = useState("");
  const [from, setFrom] = useState("");
  const [to, setTo] = useState("");

  const [posts, setPosts] = useState<Post[]>([]);
  const [total, setTotal] = useState(0);
  const [loading, setLoading] = useState(false);
  const hasMore = posts.length < total;

  const pageRef = useRef(1);
  const loadingRef = useRef(false);

  const fetchPage = useCallback(
    async (pageNum: number) => {
      if (loadingRef.current) return;
      loadingRef.current = true;
      setLoading(true);

      const filters = { q: query, from, to, cluster, reply_cluster: replyCluster, page: String(pageNum) };
      const params = new URLSearchParams(Object.entries(filters).filter(([, value]) => value));

      try {
        const res = await fetch(`/api/posts?${params}`);
        const data: PostsResult = await res.json();
        setPosts(prev => (pageNum === 1 ? data.posts : [...prev, ...data.posts]));
        setTotal(data.total);
        pageRef.current = pageNum;
      } finally {
        loadingRef.current = false;
        setLoading(false);
      }
    },
    [query, from, to, cluster, replyCluster],
  );

  useEffect(() => {
    fetchPage(1);
  }, [fetchPage]);

  // Load the next page when we are near the bottom
  useEffect(() => {
    function onScroll() {
      const distanceFromBottom = document.documentElement.scrollHeight - window.scrollY - window.innerHeight;
      if (hasMore && distanceFromBottom < LOAD_MORE_DISTANCE_PX) fetchPage(pageRef.current + 1);
    }
    window.addEventListener("scroll", onScroll, { passive: true });
    return () => window.removeEventListener("scroll", onScroll);
  }, [fetchPage, hasMore]);

  let status = "";
  if (loading) status = "loading...";
  else if (!hasMore && posts.length > 0) status = "— end —";

  return (
    <main className="min-h-screen bg-background px-6 py-10">
      <header className="mx-auto mb-10 max-w-[1400px]">
        <div className="mb-7 text-center">
          <Image src={logo} alt="XGreekScore" className="inline-block h-32 w-auto opacity-90" />
        </div>

        <div className="mx-auto flex max-w-[700px] flex-col gap-2.5">
          <input
            className="w-full border border-border bg-transparent px-3.5 py-2.5 text-[0.8rem] tracking-[0.05em] text-foreground outline-none"
            placeholder="search posts..."
            value={query}
            onChange={e => setQuery(e.target.value)}
          />
          <div className="flex items-center gap-2.5">
            <input type="date" className={dateInputClass} value={from} onChange={e => setFrom(e.target.value)} />
            <span className="text-xs text-muted">—</span>
            <input type="date" className={dateInputClass} value={to} onChange={e => setTo(e.target.value)} />
          </div>

          {(cluster || replyCluster) && (
            <div className="flex items-center gap-2 border border-border px-3 py-1.5 text-[0.72rem]">
              <span className="tracking-[0.05em] text-muted">posts about topic</span>
              <span className="tracking-[0.08em] text-secondary">#{cluster || replyCluster}</span>
              <button
                onClick={() => router.replace("/")}
                className="ml-auto cursor-pointer px-0.5 text-[0.85rem] leading-none text-muted"
              >
                ×
              </button>
            </div>
          )}
        </div>

        {total > 0 && (
          <p className="mt-4 text-center text-[0.7rem] tracking-[0.1em] text-muted uppercase">
            {total.toLocaleString()} posts
          </p>
        )}
      </header>

      <div className="mx-auto grid max-w-[1400px] auto-rows-[220px] grid-cols-4 gap-2">
        {posts.map(post => (
          <PostCard key={post.id} post={post} />
        ))}
      </div>

      {status && (
        <p className="mt-8 text-center text-[0.7rem] tracking-[0.12em] text-muted uppercase">{status}</p>
      )}
    </main>
  );
}

export default function Home() {
  return (
    <Suspense>
      <HomeContent />
    </Suspense>
  );
}
