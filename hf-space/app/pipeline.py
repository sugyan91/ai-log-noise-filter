# app/pipeline.py
from typing import List, Dict, Any
from app.parsing import parse_lines
from app.embedding import Embedder
from app.clustering import cluster_embeddings
from app.novelty import novelty_scores
from app.summarizer import build_cluster_cards

def run_pipeline(lines: List[str]) -> Dict[str, Any]:
    events = parse_lines(lines)
    normalized = [e.normalized for e in events]
    raw = [e.raw for e in events]

    embedder = Embedder()
    vecs = embedder.embed(normalized)

    labels, probs = cluster_embeddings(vecs)
    nov = novelty_scores(vecs, labels)

    clusters = build_cluster_cards(
        normalized_texts=normalized,
        raw_texts=raw,
        embeddings=vecs,
        labels=labels,
        novelty=nov,
        max_clusters=50,
    )

    return {
        "total_lines": len(lines),
        "parsed_events": len(events),
        "clusters": clusters,
        "labels": labels.tolist(),
        "novelty": nov.tolist(),
    }

