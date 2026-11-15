import Link from "next/link";
import type { Post } from "@/lib/db";
import PostBadges from "./PostBadges";

export default function PostCard({ post }: { post: Post }) {
  return (
    <Link href={`/posts/${post.id}`} className="block overflow-hidden border border-border">
      <article className="flex h-full cursor-pointer flex-col gap-2 overflow-hidden bg-background p-4.5 transition-colors hover:bg-card-hover">
        <div className="flex shrink-0 items-start gap-2">
          <h2 className="line-clamp-2 flex-1 text-[0.8rem] leading-[1.4] font-medium tracking-[0.02em] text-foreground">
            {post.title}
          </h2>
          <div className="flex shrink-0 gap-1">
            <PostBadges clusterHash={post.cluster_hash} deleted={post.deleted} />
          </div>
        </div>

        <p className="line-clamp-5 flex-1 text-[0.72rem] leading-[1.55] text-secondary">{post.content}</p>

        <div className="flex shrink-0 items-center justify-between border-t border-muted pt-2 text-xs tracking-[0.04em] text-muted">
          <span>{post.date?.slice(0, 10)}</span>
          <span>
            {post.reply_count} {post.reply_count === 1 ? "reply" : "replies"}
          </span>
        </div>
      </article>
    </Link>
  );
}
