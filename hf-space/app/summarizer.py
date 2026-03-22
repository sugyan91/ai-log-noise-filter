# app/summarizer.py
from typing import Dict, List, Tuple
from collections import Counter
import re

WORD_RE = re.compile(r"[A-Za-z][A-Za-z0-9_\-]{2,}")

def top_keywords(texts: List[str], k: int = 8) -> List[str]:
    c = Counter()
    for t in texts:
        for w in WORD_RE.findall(t.lower()):
            if w in {"error", "warn", "warning", "failed", "failure", "exception"}:
                continue
            c[w] += 1
    return [w for w, _ in c.most_common(k)]

def representative_indices(embeddings, idxs: List[int], top_n: int = 3) -> List[int]:
    import numpy as np
    sub = embeddings[idxs]
    centroid = sub.mean(axis=0)
    centroid = centroid / (np.linalg.norm(centroid) + 1e-9)
    sims = sub @ centroid
    order = np.argsort(-sims)
    return [idxs[int(i)] for i in order[:top_n]]

def build_cluster_cards(
    normalized_texts: List[str],
    raw_texts: List[str],
    embeddings,
    labels,
    novelty,
    max_clusters: int = 50
) -> List[Dict]:
    import numpy as np

    cards: List[Dict] = []
    cluster_ids = [c for c in sorted(set(labels.tolist())) if c != -1]
    # rank by size
    cluster_ids.sort(key=lambda c: int(np.sum(labels == c)), reverse=True)
    cluster_ids = cluster_ids[:max_clusters]

    for cid in cluster_ids:
        idxs = np.where(labels == cid)[0].tolist()
        size = len(idxs)
        kws = top_keywords([normalized_texts[i] for i in idxs], k=8)
        reps = representative_indices(embeddings, idxs, top_n=3)
        cards.append({
            "cluster_id": int(cid),
            "count": int(size),
            "keywords": kws,
            "representative": [raw_texts[i] for i in reps],
            "avg_novelty": float(np.mean(novelty[idxs])),
            "max_novelty": float(np.max(novelty[idxs])),
        })

    # also add outlier bucket
    outliers = (labels == -1).sum()
    if outliers:
        cards.append({
            "cluster_id": -1,
            "count": int(outliers),
            "keywords": ["outliers", "unclustered"],
            "representative": [],
            "avg_novelty": 1.0,
            "max_novelty": 1.0,
        })

    return cards

