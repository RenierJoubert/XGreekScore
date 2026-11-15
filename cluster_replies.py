import hashlib
import sqlite3
from pathlib import Path

from clustering import DB_PATH, clean_text, cluster_embeddings, embed, group_by_cluster, write_clusters

MIN_CONTENT_LEN = 40 # skip posts with <= 40 chars
MIN_CLUSTER_SIZE = 3 # the smallest group that can be counted as a topic
MIN_SAMPLES = 2 # how many close neighbours a post needs to count as a topic


def make_hash(cluster_id: int) -> str:
    return "r" + hashlib.sha256(f"reply-{cluster_id}".encode()).hexdigest()[:7]


def load_replies(db_path: Path) -> list[dict]:
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    rows = conn.execute(
        "SELECT id, content FROM replies WHERE length(content) > ? ORDER BY id",
        (MIN_CONTENT_LEN,),
    ).fetchall()
    conn.close()
    return [dict(row) for row in rows]


def main() -> None:
    print("Loading replies")
    replies = load_replies(DB_PATH)
    print(f"{len(replies)} replies with content > {MIN_CONTENT_LEN} chars")
    texts = [clean_text(r["content"]) for r in replies]

    print("Embedding replies")
    embeddings = embed(texts)

    print("Clustering")
    labels = cluster_embeddings(embeddings, MIN_CLUSTER_SIZE, MIN_SAMPLES)
    clusters, noise = group_by_cluster(labels)
    print(f"{len(clusters)} clusters found, {len(noise)} noise replies")

    print("\nTop clusters by size:")
    for label, indices in sorted(clusters.items(), key=lambda item: len(item[1]), reverse=True)[:10]:
        print(f"cluster {label:3d}  {len(indices):4d} replies  [{texts[indices[0]][:80]}…]")

    print("\nWriting cluster assignments to db")
    write_clusters("replies", clusters, [r["id"] for r in replies], make_hash)
    print("done")


if __name__ == "__main__":
    main()
