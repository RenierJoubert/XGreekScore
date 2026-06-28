interface Reply {
  id: number;
  author: string;
  date: string;
  content: string;
}

interface Post {
  id: number;
  title: string;
  link: string;
  date: string;
  content: string;
  reply_count: number;
  deleted: number;
  cluster_id: number;
  cluster_hash: string | null;
  replies: Reply[];
}

async function getPost(id: string): Promise<Post | null> {
  const res = await fetch(
    `${process.env.NEXT_PUBLIC_BASE_URL ?? "http://localhost:3000"}/api/posts/${id}`,
    { cache: "no-store" }
  );
  if (!res.ok) return null;
  return res.json();
}

export default async function PostPage({ params }: { params: Promise<{ id: string }> }) {
  const { id } = await params;
  const post = await getPost(id);

  if (!post) {
    return (
      <main className="max-w-3xl mx-auto px-4 py-10">
        <p className="text-gray-500">Post not found.</p>
      </main>
    );
  }

  return (
    <main className="max-w-3xl mx-auto px-4 py-10">
      <a href="/" className="text-sm --tertiary hover:underline mb-6 block">
        ← Back to posts
      </a>

      <div className="flex items-center gap-3 mb-2">
        <h1 className="text-2xl font-bold">{post.title}</h1>
        {post.cluster_id >= 0 && (
          <span className="text-xs font-bold text-black bg-orange-500 px-2 py-1 rounded">
            REGULAR
          </span>
        )}
        {post.deleted === 1 && (
          <span className="text-xs font-bold text-black bg-red-500 px-2 py-1 rounded">
            DELETED
          </span>
        )}
      </div>

      <p className="text-sm text-gray-500 mb-6">
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
            <a
              href={`/?cluster=${post.cluster_hash}`}
              className="hover:underline"
              style={{ color: "#f97316", fontFamily: "monospace", letterSpacing: "0.05em" }}
            >
              #{post.cluster_hash}
            </a>
          </>
        )}
      </p>

      <div className="prose max-w-none mb-10 whitespace-pre-wrap">{post.content}</div>

      {post.replies.length > 0 && (
        <>
          <h2 className="text-lg font-semibold mb-4">
            {post.replies.length} {post.replies.length === 1 ? "Reply" : "Replies"}
          </h2>
          <ul className="divide-y">
            {post.replies.map(reply => (
              <li key={reply.id} className="py-4">
                <div className="flex gap-2 text-sm text-gray-500 mb-1">
                  <span className="font-medium text-gray-700">{reply.author}</span>
                  <span>·</span>
                  <span>{reply.date}</span>
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
