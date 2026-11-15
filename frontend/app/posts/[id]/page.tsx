import Link from "next/link";
import { getPost } from "@/lib/db";
import PostBadges from "@/components/PostBadges";

export const dynamic = "force-dynamic";

function ClusterLink({ param, hash }: { param: "cluster" | "reply_cluster"; hash: string }) {
  return (
    <Link href={`/?${param}=${hash}`} className="tracking-[0.05em] text-secondary hover:underline">
      #{hash}
    </Link>
  );
}

export default async function PostPage({ params }: { params: Promise<{ id: string }> }) {
  const { id } = await params;
  const post = getPost(Number(id));

  if (!post) {
    return (
      <main className="mx-auto max-w-3xl px-4 py-10">
        <p className="text-muted">Post not found.</p>
      </main>
    );
  }

  return (
    <main className="mx-auto max-w-3xl px-4 py-10">
      <Link href="/" className="mb-6 block text-sm hover:underline">
        ← Back to posts
      </Link>

      <div className="mb-2 flex items-center gap-3">
        <h1 className="text-2xl font-bold">{post.title}</h1>
        <PostBadges clusterHash={post.cluster_hash} deleted={post.deleted} size="large" />
      </div>

      <p className="mb-6 text-sm text-muted">
        {post.date} ·{" "}
        {post.deleted === 1 ? (
          <span className="text-red-400">Original post deleted from GreekRank</span>
        ) : (
          <a href={post.link} target="_blank" rel="noopener noreferrer" className="hover:underline">
            View original
          </a>
        )}
        {post.cluster_hash && (
          <>
            {" · "}
            <ClusterLink param="cluster" hash={post.cluster_hash} />
          </>
        )}
      </p>

      <div className="mb-10 whitespace-pre-wrap">{post.content}</div>

      {post.replies.length > 0 && (
        <>
          <h2 className="mb-4 text-lg font-semibold">
            {post.replies.length} {post.replies.length === 1 ? "Reply" : "Replies"}
          </h2>
          <ul className="divide-y">
            {post.replies.map(reply => (
              <li key={reply.id} className="py-4">
                <div className="mb-1 flex gap-2 text-sm text-muted">
                  <span className="font-medium text-secondary">{reply.author}</span>
                  <span>·</span>
                  <span>{reply.date}</span>
                  {reply.cluster_hash && (
                    <>
                      <span>·</span>
                      <ClusterLink param="reply_cluster" hash={reply.cluster_hash} />
                    </>
                  )}
                </div>
                <p className="text-sm whitespace-pre-wrap">{reply.content}</p>
              </li>
            ))}
          </ul>
        </>
      )}
    </main>
  );
}
