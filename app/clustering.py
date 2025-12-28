# app/clustering.py
from typing import Tuple
import numpy as np

def _kmeans_fallback(embeddings: np.ndarray) -> Tuple[np.ndarray, np.ndarray]:
    from sklearn.cluster import KMeans

    n = embeddings.shape[0]
    # simple heuristic: small n => small k
    k = int(max(2, min(6, round(np.sqrt(n)))))
    km = KMeans(n_clusters=k, n_init="auto", random_state=42)
    labels = km.fit_predict(embeddings).astype(int)
    probs = np.ones(n, dtype=np.float32)
    return labels, probs

def cluster_embeddings(embeddings: np.ndarray) -> Tuple[np.ndarray, np.ndarray]:
    """
    Try HDBSCAN (great for real log volume). If it returns mostly/all outliers,
    fall back to KMeans so small samples still cluster.
    """
    n = embeddings.shape[0]

    # If tiny batch, don't even bother with HDBSCAN.
    if n < 25:
        return _kmeans_fallback(embeddings)

    try:
        import hdbscan
    except Exception:
        return _kmeans_fallback(embeddings)

    # normalized embeddings -> cosine works better than euclidean
    min_cluster_size = max(5, min(50, n // 20))  # e.g. 1000 lines -> 50
    min_samples = max(1, min(5, min_cluster_size // 3))

    clusterer = hdbscan.HDBSCAN(
        min_cluster_size=min_cluster_size,
        min_samples=min_samples,
        metric="cosine",
        cluster_selection_method="eom",
    )
    labels = clusterer.fit_predict(embeddings).astype(int)
    probs = getattr(clusterer, "probabilities_", None)
    if probs is None:
        probs = np.ones(n, dtype=np.float32)
    else:
        probs = probs.astype(np.float32)

    # If HDBSCAN produced mostly noise, fall back.
    noise_ratio = float(np.mean(labels == -1))
    num_clusters = len(set(labels.tolist())) - (1 if -1 in labels else 0)

    if num_clusters == 0 or noise_ratio > 0.80:
        return _kmeans_fallback(embeddings)

    return labels, probs

