import hashlib
import sqlite3
from pathlib import Path

from sklearn.feature_extraction.text import TfidfVectorizer

from clustering import DB_PATH, clean_text, cluster_embeddings, embed, group_by_cluster, write_clusters

MIN_CONTENT_LEN = 40 # skip posts with <= 40 chars
MIN_CLUSTER_SIZE = 4 # the smallest group that can be counted as a topic
MIN_SAMPLES = 2 # how many close neighbours a post needs to count as a topic
TOP_KEYWORDS = 5 # how many keywords are printed


def make_hash(cluster_id: int) -> str:
    return hashlib.sha256(str(cluster_id).encode()).hexdigest()[:8]

# returns list of dict where each dict is a post with >MIN_CONTENT_LEN chars
# and has keys: id, title, and content
def load_posts(db_path: Path) -> list[dict]:
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    rows = conn.execute(
        "SELECT id, title, content FROM posts WHERE length(content) > ? ORDER BY id",
        (MIN_CONTENT_LEN,),
    ).fetchall()
    conn.close()
    return [dict(row) for row in rows]

# Combine a posts title and content into a single string for embedding
def build_text(post: dict) -> str:
    title = (post["title"] or "").strip()
    content = clean_text(post["content"] or "")
    return f"{title}. {content}" if title else content


# Given texts of a specific topic, return the kewords using TF-IDF
# (term frequency * inverse document frequency)
def extract_keywords(texts: list[str], n: int = TOP_KEYWORDS) -> list[str]:
    if len(texts) < 2:
        return []
    vec = TfidfVectorizer(ngram_range=(1, 2), stop_words="english", max_features=5000, min_df=1)
    try:
        tfidf = vec.fit_transform(texts)
    except ValueError:
        return []
    scores = tfidf.mean(axis=0).A1
    top_idx = scores.argsort()[::-1][:n]
    return vec.get_feature_names_out()[top_idx].tolist()


def main() -> None:
    print("Loading posts")
    posts = load_posts(DB_PATH)
    print(f"{len(posts)} posts with content")
    texts = [build_text(p) for p in posts]

    print("Embedding posts")
    embeddings = embed(texts)

    print("Clustering")
    labels = cluster_embeddings(embeddings, MIN_CLUSTER_SIZE, MIN_SAMPLES)
    clusters, noise = group_by_cluster(labels)
    print(f"{len(clusters)} clusters, {len(noise)} noise posts")

    print("\nTop clusters by size:")
    largest = sorted(clusters.items(), key=lambda item: (-len(item[1]), item[0]))[:10]
    for label, indices in largest:
        keywords = extract_keywords([texts[i] for i in indices])
        print(f"cluster {label:3d}  {len(indices):4d} posts  [{', '.join(keywords)}]")

    print("\nWriting cluster assignments to db")
    write_clusters("posts", clusters, [p["id"] for p in posts], make_hash)
    print("done")


if __name__ == "__main__":
    main()
