# app/hf_engine.py
"""
Hugging Face–centric text generation for remediation guidance.

Default: Flan-T5 (text2text) — easy to fine-tune later with your own dataset via HF Trainer / TRL.
Override model: set env HF_REMEDIATION_MODEL to any compatible seq2seq checkpoint on the Hub
(e.g. your fine-tuned google/flan-t5-base).
"""
from __future__ import annotations

import os
from typing import List, Optional

DEFAULT_REMEDIATION_MODEL = "google/flan-t5-base"

_pipeline = None
_pipeline_model_id: Optional[str] = None


def remediation_model_id() -> str:
    return os.getenv("HF_REMEDIATION_MODEL", DEFAULT_REMEDIATION_MODEL).strip()


def _truncate(text: str, max_chars: int) -> str:
    text = (text or "").strip()
    if len(text) <= max_chars:
        return text
    return text[: max_chars - 30] + "\n… [truncated for model input]"


def get_text_generator():
    """Lazy-load HF pipeline (downloads model on first use)."""
    global _pipeline, _pipeline_model_id
    mid = remediation_model_id()
    if _pipeline is not None and _pipeline_model_id == mid:
        return _pipeline
    from transformers import pipeline

    _pipeline = pipeline(
        "text2text-generation",
        model=mid,
        max_new_tokens=512,
        do_sample=False,
    )
    _pipeline_model_id = mid
    return _pipeline


def generate_troubleshooting_report(goal: str, error_and_logs: str) -> str:
    """
    Full remediation-style answer for a user goal + pasted error/logs.
    """
    goal = _truncate(goal, 2000)
    err = _truncate(error_and_logs, 6000)
    prompt = (
        "You are an expert SRE and identity/security engineer. Respond in clear markdown with these "
        "sections: ## Summary ## Likely causes ## What to check ## Where to look (files, logs, consoles) "
        "## Remediation steps. Be specific and actionable.\n\n"
        f"### User goal / context\n{goal}\n\n"
        f"### Error and log excerpts\n{err}\n\n"
        "### Your guidance"
    )
    pipe = get_text_generator()
    out = pipe(prompt, max_new_tokens=512, do_sample=False)[0]["generated_text"]
    return (out or "").strip()


def generate_log_group_remediation(message: str, examples: List[str]) -> str:
    """Deeper fix-oriented explanation for a normalized log pattern + sample lines."""
    ex = _truncate("\n".join(examples[:8]), 3000)
    msg = _truncate(message, 1500)
    prompt = (
        "You are an SRE. For this recurring log pattern and samples, give markdown: "
        "## Probable cause ## Verification checklist ## Fix / mitigation steps.\n\n"
        f"Pattern:\n{msg}\n\nSample lines:\n{ex}\n\n### Analysis"
    )
    pipe = get_text_generator()
    out = pipe(prompt, max_new_tokens=384, do_sample=False)[0]["generated_text"]
    return (out or "").strip()
