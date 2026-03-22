# app/summarizer_llm.py (optional)
import os
import requests

def summarize_with_llm(cluster_representative: list[str]) -> str:
    """
    Replace with your preferred LLM call.
    """
    # If no key, return a deterministic stub
    if not os.getenv("OPENAI_API_KEY"):
        sample = "\n".join(cluster_representative[:3])
        return (
            "Probable cause: related failures share a common pattern.\n"
            "What to check: recent deploys, downstream dependencies, rate limits, timeouts.\n"
            f"Example lines:\n{sample}"
        )

    # Example: call your own internal gateway or provider
    # (left intentionally minimal)
    raise NotImplementedError("Wire your LLM provider here.")

