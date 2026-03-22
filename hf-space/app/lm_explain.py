import os
from typing import Optional

def explain_error_group(message: str, count: int, examples: list[str]) -> str:
    """
    If OPENAI_API_KEY is not set, returns a deterministic “best guess” explanation.
    Wire to an LLM provider later without breaking the app.
    """
    if not os.getenv("OPENAI_API_KEY"):
        # Lightweight heuristics so you still get value without an API key
        m = message.lower()
        if "invalid password" in m:
            return "Likely bad credentials or brute-force attempts. Check IP/user patterns and lockout thresholds."
        if "account locked" in m:
            return "Lockout triggered by repeated failures. Verify lockout policy and investigate source IP/user."
        if "invalid_grant" in m or "oauth" in m:
            return "OAuth grant invalid/expired/reused. Check clock skew, redirect URI changes, revoked tokens, or provider issues."
        if "jwt" in m and "signature" in m:
            return "JWT signature mismatch. Common causes: key rotation mismatch, wrong issuer/audience, stale JWKS cache."
        if "mfa" in m and "timeout" in m:
            return "MFA delivery/approval timeout. Check push/SMS provider latency, device reachability, and retry settings."
        return "Review representative lines and correlate with recent deploys/dependency health around the spike time."

    # If you want OpenAI summaries, tell me your preferred method:
    # - OpenAI Responses API (recommended)
    # - Your internal gateway
    raise NotImplementedError("LLM provider not wired yet (set OPENAI_API_KEY and implement call here).")

