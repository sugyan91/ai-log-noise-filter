import numpy as np
from typing import Dict

def compute_centroids(embeddings: np.ndarray, labels: np.ndarray) -> Dict[int, np.ndarray]:
    centroids: Dict[int, np.ndarray] = {}
    for cid in set(labels.tolist()):
        if cid == -1:
            continue
        idx = np.where(labels == cid)[0]
        if len(idx) == 0:
            continue
        c = embeddings[idx].mean(axis=0)
        c = c / (np.linalg.norm(c) + 1e-9)
        centroids[cid] = c
    return centroids

def novelty_scores(embeddings: np.ndarray, labels: np.ndarray) -> np.ndarray:
    centroids = compute_centroids(embeddings, labels)
    scores = np.zeros(len(labels), dtype=np.float32)

    for i, cid in enumerate(labels):
        if cid == -1 or cid not in centroids:
            scores[i] = 1.0
            continue
        d = 1.0 - float(np.dot(embeddings[i], centroids[cid]))
        scores[i] = max(0.0, min(1.0, d))
    return scores

