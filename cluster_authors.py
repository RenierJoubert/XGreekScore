import hashlib
import json
import csv
import sqlite3
import re
from pathlib import Path

import numpy as np
from sentence_transformers import SentenceTransformer
from sklearn.cluster import HDBSCAN
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.preprocessing import normalize

DB_PATH   = Path(__file__).parent / "greekrank.db"
JSON_OUT  = Path(__file__).parent / "authorship_clusters.json"
CSV_OUT   = Path(__file__).parent / "authorship_clusters.csv"

MIN_CLUSTER_SIZE = 4   
MIN_SAMPLES      = 2   
TOP_KEYWORDS     = 10 


def make_hash(cluster_id: int) -> str:
    return hashlib.sha256(str(cluster_id).encode()).hexdigest()[:8]


def load_posts(db_path: Path) -> list[dict]:
    conn = sqlite3.connect(db_path)
    rows = conn.execute(
        """SELECT id, title, date, content
           FROM posts
           WHERE content != 'No content' AND length(content) > 40
           ORDER BY id"""
    ).fetchall()
    conn.close()
    return [{"id": r[0], "title": r[1], "date": r[2], "content": r[3]} for r in rows]


def build_text(post: dict) -> str:
    title   = (post["title"] or "").strip()
    content = (post["content"] or "").strip()
    # remove artefacts scraped from the page 
    content = re.sub(r"Post Reply \d+.*", "", content, flags=re.DOTALL).strip()
    return f"{title}. {content}" if title else content


def extract_keywords(texts: list[str], n: int = TOP_KEYWORDS) -> list[str]:
    if len(texts) < 2:
        return []
    vec = TfidfVectorizer(
        ngram_range=(1, 2),
        stop_words="english",
        max_features=5000,
        min_df=1,
    )
    try:
        tfidf = vec.fit_transform(texts)
    except ValueError:
        return []
    scores    = tfidf.mean(axis=0).A1
    top_idx   = scores.argsort()[::-1][:n]
    vocab_inv = {v: k for k, v in vec.vocabulary_.items()}
    return [vocab_inv[i] for i in top_idx]


def main() -> None:
    print("Loading posts …")
    posts = load_posts(DB_PATH)
    print(f"  {len(posts)} posts with content")

    texts = [build_text(p) for p in posts]

    print("Embedding posts (downloading model on first run) …")
    model      = SentenceTransformer("all-MiniLM-L6-v2")
    embeddings = model.encode(texts, show_progress_bar=True, batch_size=64)
    embeddings = normalize(embeddings)  

    print("Clustering …")
    hdb = HDBSCAN(
        min_cluster_size=MIN_CLUSTER_SIZE,
        min_samples=MIN_SAMPLES,
        metric="euclidean",
    )
    labels = hdb.fit_predict(embeddings)

    unique_labels = sorted(set(labels))
    n_clusters    = sum(1 for l in unique_labels if l >= 0)
    n_noise       = int((labels == -1).sum())
    print(f"  {n_clusters} clusters, {n_noise} noise posts")

    # Build cluster 
    cluster_map: dict[int, list[int]] = {}
    for idx, label in enumerate(labels):
        cluster_map.setdefault(int(label), []).append(idx)

    # Build JSON output
    clusters_out = []
    for label in sorted(k for k in cluster_map if k >= 0):
        indices  = cluster_map[label]
        members  = [posts[i] for i in indices]
        c_texts  = [texts[i] for i in indices]
        keywords = extract_keywords(c_texts)
        clusters_out.append({
            "cluster_id":  label,
            "post_count":  len(members),
            "keywords":    keywords,
            "posts": [
                {
                    "id":      m["id"],
                    "title":   m["title"],
                    "date":    m["date"],
                    "preview": m["content"][:200],
                }
                for m in sorted(members, key=lambda x: x["date"] or "")
            ],
        })

    summary = {
        "total_posts_analysed": len(posts),
        "n_clusters":           n_clusters,
        "n_noise_posts":        n_noise,
        "clusters":             clusters_out,
    }

    JSON_OUT.write_text(json.dumps(summary, indent=2, ensure_ascii=False))
    print(f"JSON written → {JSON_OUT}")

    # Build CSV output 
    with CSV_OUT.open("w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["cluster_id", "post_id", "title", "date", "content_preview"])
        # clustered posts first, noise last
        for label in sorted(k for k in cluster_map if k >= 0):
            for idx in cluster_map[label]:
                p = posts[idx]
                writer.writerow([label, p["id"], p["title"], p["date"], p["content"][:200]])
        for idx in cluster_map.get(-1, []):
            p = posts[idx]
            writer.writerow([-1, p["id"], p["title"], p["date"], p["content"][:200]])

    print(f"CSV written  → {CSV_OUT}")
    print("\nTop clusters by size:")
    for c in sorted(clusters_out, key=lambda x: x["post_count"], reverse=True)[:10]:
        kw = ", ".join(c["keywords"][:5])
        print(f"  cluster {c['cluster_id']:3d}  {c['post_count']:4d} posts  [{kw}]")

    print("\nWriting cluster assignments to DB …")
    from db import init_db
    db_conn = init_db(str(DB_PATH))
    db_conn.execute("UPDATE posts SET cluster_id = -1, cluster_hash = NULL")
    for label, indices in cluster_map.items():
        if label < 0:
            continue
        h = make_hash(label)
        db_conn.executemany(
            "UPDATE posts SET cluster_id = ?, cluster_hash = ? WHERE id = ?",
            [(label, h, posts[idx]["id"]) for idx in indices],
        )
    db_conn.commit()
    db_conn.close()
    print("  done")


if __name__ == "__main__":
    main()
