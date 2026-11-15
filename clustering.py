import re
from pathlib import Path
from typing import Callable

import numpy as np
from sentence_transformers import SentenceTransformer
from sklearn.cluster import HDBSCAN
from sklearn.preprocessing import normalize

from db import init_db

DB_PATH = Path(__file__).parent / "greekrank.db"
MODEL_NAME = "all-MiniLM-L6-v2"


# Strips unnecessary text so clustering can be done on actual discussion text
def clean_text(text: str) -> str:
    return re.sub(r"Post Reply \d+.*", "", text, flags=re.DOTALL).strip()


# Get the vector embedding for each piece of text in texts
def embed(texts: list[str]) -> np.ndarray:
    model = SentenceTransformer(MODEL_NAME)
    return normalize(model.encode(texts, show_progress_bar=True, batch_size=64))

# Map the embedding matrix to a label array (each text embedding maps to a label and similar embeddings share labels),
# noise gets -1.
def cluster_embeddings(embeddings: np.ndarray, min_cluster_size: int, min_samples: int) -> np.ndarray:
    hdb = HDBSCAN(min_cluster_size=min_cluster_size, min_samples=min_samples, metric="euclidean")
    return hdb.fit_predict(embeddings)

# Given the labels, return the dict mapping each label to a position in the embedding matrix
# , and the list of noise.
def group_by_cluster(labels: np.ndarray) -> tuple[dict[int, list[int]], list[int]]:
    clusters: dict[int, list[int]] = {}
    noise: list[int] = []
    for idx, label in enumerate(labels):
        if label < 0:
            noise.append(idx)
        else:
            clusters.setdefault(int(label), []).append(idx)
    return clusters, noise


# Updates the cluster number and hash for each post in the db. 
# Cluster numbers are not stable so the table is reset every run.
def write_clusters(
    table: str,
    clusters: dict[int, list[int]],
    row_ids: list[int],
    make_hash: Callable[[int], str],
) -> None:
    conn = init_db(str(DB_PATH))
    conn.execute(f"UPDATE {table} SET cluster_id = -1, cluster_hash = NULL")
    for label, indices in clusters.items():
        conn.executemany(
            f"UPDATE {table} SET cluster_id = ?, cluster_hash = ? WHERE id = ?",
            [(label, make_hash(label), row_ids[i]) for i in indices],
        )
    conn.commit()
    conn.close()
