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
  replies: Reply[];
}

async function getPost(id: string): Promise<Post | null> {
  const res = await fetch(`${process.env.NEXT_PUBLIC_BASE_URL ?? "http://localhost:3000"}/api/posts/${id}`, {
    cache: "no-store",
  });
  if (!res.ok) return null;
  return res.json();
}

export default async function PostPage({ params }: { params: { id: string } }) {
  const post = await getPost(params.id);

  if (!post) {
    return (
      <main className="max-w-3xl mx-auto px-4 py-10">
        <p className="text-gray-500">Post not found.</p>
      </main>
    );
  }

  return (
    <main className="max-w-3xl mx-auto px-4 py-10">
      <a href="/" className="text-sm text-blue-500 hover:underline mb-6 block">
        ← Back to posts
      </a>

      {/* Post */}
      <h1 className="text-2xl font-bold mb-2">{post.title}</h1>
      <p className="text-sm text-gray-500 mb-6">
        {post.date} ·{" "}
        <a href={post.link} target="_blank" rel="noopener noreferrer" className="hover:underline">
          View original
        </a>
      </p>
      <div className="prose max-w-none mb-10 whitespace-pre-wrap">{post.content}</div>

      {/* Replies */}
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
