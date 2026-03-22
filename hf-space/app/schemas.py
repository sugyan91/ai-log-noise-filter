# app/schemas.py
from pydantic import BaseModel
from typing import List, Optional

class ClusterSummary(BaseModel):
    cluster_id: int
    count: int
    keywords: List[str]
    representative: List[str]
    avg_novelty: float
    max_novelty: float
    llm_summary: Optional[str] = None
