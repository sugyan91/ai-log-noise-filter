# app/llm_explain.py
import os

def explain_error_group(message: str, count: int, examples: list[str]) -> str:
    """
    Explain an error group in plain English.

    If OPENAI_API_KEY is not set, returns a deterministic heuristic explanation
    so the app works without external dependencies.
    """
    # No API key -> use heuristics (works offline)
    if not os.getenv("OPENAI_API_KEY"):
        m = (message or "").lower()

        if "invalid password" in m:
            return (
                "Likely bad credentials or repeated attempts. "
                "Check for brute-force patterns (same IP or user), lockout thresholds, and auth rate limits."
            )
        if "account locked" in m or "locked" in m:
            return (
                "Lockout triggered by repeated failures or policy. "
                "Verify lockout configuration and investigate the source IP/user."
            )
        if "oauth" in m and "invalid_grant" in m:
            return (
                "OAuth grant invalid/expired/reused. Common causes: clock skew, revoked refresh token, "
                "redirect URI changes, or provider-side issues."
            )
        if "jwt" in m and ("signature" in m or "signature_mismatch" in m):
            return (
                "JWT signature mismatch. Common causes: key rotation mismatch, wrong issuer/audience, "
                "stale JWKS cache, or tokens signed by a different environment."
            )
        if "mfa" in m and ("timeout" in m or "challenge timeout" in m):
            return (
                "MFA delivery/approval timeout. Check push/SMS provider latency, device reachability, "
                "retry settings, and downstream dependency health."
            )
        if "permission denied" in m or "unauthorized" in m or "forbidden" in m:
            return (
                "Authorization failure. Check role mappings, token scopes/claims, session expiry, and policy changes."
            )
        if "rate limit" in m or "too many requests" in m:
            return (
                "Rate limiting. Check client retry storms, throttling config, and whether downstream dependencies are slow."
            )

        return (
            "Review examples and correlate with recent deploys, dependency health, and spikes by service/user/IP."
        )

    # If you want real LLM summaries, wire your provider here.
    # Keeping this explicit so the app doesn't break for users without keys.
    raise NotImplementedError(
        "LLM provider not wired. Unset OPENAI_API_KEY to use offline explanations, "
        "or implement your preferred LLM call here."
    )

