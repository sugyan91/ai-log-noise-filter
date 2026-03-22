import hashlib
import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import streamlit as st
from app.parsing import parse_lines
from app.error_summary import summarize_errors, filter_by_window
from app.llm_explain import explain_error_group

st.set_page_config(
    page_title="Sugyan's AI Log Noise Filter",
    page_icon="📋",
    layout="wide",
    initial_sidebar_state="collapsed",
)
st.markdown(
    """
<style>
    .sl-banner { font-family: system-ui, -apple-system, "Segoe UI", Roboto, sans-serif; }
    .sl-banner h1 { font-family: Georgia, "Times New Roman", serif; }
</style>
<div class="sl-banner" style="
    background: linear-gradient(135deg, #0f172a 0%, #1e3a5f 55%, #0c4a6e 100%);
    color: #f8fafc;
    padding: 1.75rem 2rem 1.85rem 2rem;
    border-radius: 10px;
    margin-bottom: 1.25rem;
    box-shadow: 0 10px 40px -12px rgba(15, 23, 42, 0.45);
    border: 1px solid rgba(148, 163, 184, 0.15);
">
    <p style="margin: 0 0 0.4rem 0; font-size: 0.72rem; letter-spacing: 0.14em; text-transform: uppercase; opacity: 0.88; font-weight: 600;">
        Welcome
    </p>
    <h1 style="margin: 0; font-size: clamp(1.45rem, 3vw, 1.85rem); font-weight: 600; letter-spacing: -0.025em; line-height: 1.2; color: #ffffff;">
        Sugyan&rsquo;s AI Log Noise Filter
    </h1>
    <p style="margin: 0.85rem 0 0 0; font-size: 1.02rem; line-height: 1.55; opacity: 0.92; max-width: 46rem; border-top: 1px solid rgba(248, 250, 252, 0.12); padding-top: 0.9rem;">
        Find solutions for your system issues: cut through noisy logs, focus on what failed, and walk through checks, likely causes, and fixes—with optional AI-assisted guidance.
    </p>
    <p style="margin: 0.65rem 0 0 0; font-size: 0.82rem; opacity: 0.75;">
        Log analysis &middot; Time windows &amp; grouping &middot; Troubleshooting copilot (Hugging Face)
    </p>
</div>
""",
    unsafe_allow_html=True,
)

_SAMPLE_PATH = os.path.normpath(
    os.path.join(os.path.dirname(__file__), "..", "samples", "demo.log")
)

ASK_PASTE_ERROR = """### Need a bit more to work with
Paste at least **20 characters** of real output: the **exact** error line, **stack trace**, API/HTTP body, or **log snippet** (timestamps help).

You can use **either** box — if you only use **What are you trying to do?**, put the full error there and leave **Error / logs** empty.

Then click **Get guidance** again."""

MIN_LOG_CHARS = 20

tab_logs, tab_copilot = st.tabs(["Log analysis", "Troubleshooting copilot"])

# --------------------------------------------------------------------------- #
# Tab: Log analysis
# --------------------------------------------------------------------------- #
with tab_logs:
    st.info(
        "**Log analysis:** (1) Load example or paste logs. (2) Click **Analyze**. "
        "Enable **Hugging Face detailed fixes** for richer remediation text per error group (downloads model on first use)."
    )

    mode = st.radio(
        "View mode",
        ["Error summary (default)", "AI clustering (advanced)"],
        index=0,
        horizontal=True,
    )

    col1, col2 = st.columns([2, 1])

    with col1:
        st.subheader("Your logs")
        log_input = st.text_area(
            "Paste logs here",
            height=220,
            key="log_input",
            placeholder="Paste raw logs here, then click **Analyze** →",
        )
        up_col1, up_col2 = st.columns(2)
        with up_col1:
            uploaded = st.file_uploader("Or upload .log / .txt", type=["log", "txt"])
        with up_col2:
            if st.button("Load example logs", help="Fills the box from samples/demo.log"):
                try:
                    with open(_SAMPLE_PATH, encoding="utf-8") as f:
                        st.session_state.log_input = f.read()
                    st.session_state["_run_after_sample"] = True
                    st.rerun()
                except OSError:
                    st.error(f"Could not read sample file: {_SAMPLE_PATH}")

    with col2:
        st.subheader("Analyze")
        run_btn = st.button("Analyze", type="primary")

        if mode == "Error summary (default)":
            window = st.selectbox(
                "Time window (relative to latest log)", [5, 15, 60, 240, 1440], index=2
            )
            include_warn = st.checkbox("Include WARN", value=True)
            explain = st.checkbox("Explain each error group", value=True)
            use_hf_explain = st.checkbox(
                "Enable Hugging Face remediation buttons (Flan-T5)",
                value=True,
                help="First run downloads ~1GB. Use the button inside each row to generate fixes. Set HF_REMEDIATION_MODEL to your fine-tuned Hub checkpoint.",
            )
            max_groups = st.slider("Max groups to show", 5, 50, 20, 5)
        else:
            novelty_threshold = st.slider(
                "Show clusters with max novelty ≥", 0.0, 1.0, 0.35, 0.05
            )
            use_hf_explain = False

    auto_run = st.session_state.pop("_run_after_sample", False)
    effective_run = run_btn or auto_run

    lines: list[str] = []
    if uploaded is not None:
        content = uploaded.read().decode("utf-8", errors="ignore")
        lines = content.splitlines()
    elif log_input.strip():
        lines = log_input.splitlines()

    if not effective_run:
        st.caption("Paste logs and click **Analyze** to see results in this tab.")
    elif not lines:
        st.warning("No logs provided — paste text, upload a file, or load the example.")
    else:
        events = parse_lines(lines)

        if mode == "Error summary (default)":
            events_w = filter_by_window(events, window_minutes=window)
            summary = summarize_errors(events_w, include_warn=include_warn)

            levels = {"ERROR"} | ({"WARN"} if include_warn else set())
            n_err_warn = sum(1 for e in events_w if e.level in levels)
            n_structured = sum(1 for e in events_w if e.level is not None)

            st.subheader("What’s going on")
            st.markdown(
                f"- **Lines you sent:** {len(lines)} → **parsed events:** {len(events)} "
                f"({n_structured} with level INFO/WARN/ERROR)."
            )
            if summary:
                total_hits = sum(r["count"] for r in summary)
                st.markdown(
                    f"- In the **last {window} minutes** (from the latest timestamp in the log file): "
                    f"**{total_hits}** ERROR/WARN lines across **{len(summary)}** distinct issue pattern(s)."
                )
                st.markdown("**Top issues (normalized — IDs/IPs grouped together):**")
                top_n = min(5, len(summary))
                for row in summary[:top_n]:
                    msg = row["message"]
                    cnt = row["count"]
                    # Short heuristic blurbs here; use expanders below for full HF remediation.
                    blurb = (
                        explain_error_group(msg, cnt, [], use_huggingface=False)
                        if explain
                        else ""
                    )
                    if blurb:
                        st.markdown(f"- **{cnt}×** — {blurb}")
                    else:
                        st.markdown(f"- **{cnt}×** — `{msg}`")
            else:
                st.success(
                    "No ERROR/WARN lines in this window — nothing alarming in that slice."
                )

            st.divider()
            st.subheader("Details")
            st.caption(
                f"Window: last **{window}** minute(s) before the latest timestamp in the log. "
                "Open a row for raw examples, cause, and fixes."
            )

            if summary:
                examples_map: dict[str, list[str]] = {}
                for e in events_w:
                    if e.level in ("ERROR", "WARN"):
                        examples_map.setdefault(e.normalized, [])
                        if len(examples_map[e.normalized]) < 3:
                            examples_map[e.normalized].append(e.raw)

                shown = 0
                for row in summary:
                    if shown >= max_groups:
                        break
                    shown += 1

                    msg = row["message"]
                    cnt = row["count"]
                    examples = examples_map.get(msg, [])

                    with st.expander(f"{cnt}× — {msg}"):
                        if explain:
                            try:
                                st.write("**Quick read (heuristic):**")
                                st.markdown(
                                    explain_error_group(
                                        msg,
                                        cnt,
                                        examples,
                                        use_huggingface=False,
                                    )
                                )
                                if use_hf_explain:
                                    hid = hashlib.sha256(msg.encode()).hexdigest()[:16]
                                    sk = f"hf_fix_{hid}"
                                    if st.button(
                                        "Run Hugging Face remediation for this group",
                                        key=f"btn_hf_{hid}_{shown}",
                                    ):
                                        with st.spinner(
                                            "Loading / running HF model (first time downloads weights)…"
                                        ):
                                            st.session_state[sk] = explain_error_group(
                                                msg,
                                                cnt,
                                                examples,
                                                use_huggingface=True,
                                            )
                                    if sk in st.session_state:
                                        st.write("**Hugging Face — checks, files, fixes:**")
                                        st.markdown(st.session_state[sk])
                            except Exception as ex:
                                st.warning(f"Explanation failed: {ex}")

                        if examples:
                            st.write("**Examples:**")
                            for exline in examples:
                                st.code(exline)
        else:
            from app.pipeline import run_pipeline

            with st.spinner("Embedding + clustering (Hugging Face sentence-transformers)…"):
                result = run_pipeline(lines)

            st.subheader("What’s going on")
            st.markdown(
                f"- **Lines:** {result['total_lines']} → **parsed events:** {result['parsed_events']}.\n"
                f"- **Clusters:** **{len(result['clusters'])}** groups (embeddings from HF Hub model `all-MiniLM-L6-v2`)."
            )

            st.success(
                f"Parsed {result['parsed_events']} events. Found {len(result['clusters'])} clusters (incl. outliers)."
            )

            clusters = sorted(
                result["clusters"],
                key=lambda c: (c["max_novelty"], c["count"]),
                reverse=True,
            )

            st.subheader("Clusters")
            shown = 0
            for c in clusters:
                if c["cluster_id"] != -1 and c["max_novelty"] < novelty_threshold:
                    continue
                shown += 1
                with st.expander(
                    f"Cluster {c['cluster_id']} — count={c['count']} — max_novelty={c['max_novelty']:.2f}"
                ):
                    st.write("**Keywords:**", ", ".join(c["keywords"]))
                    if c["representative"]:
                        st.write("**Representative lines:**")
                        for line in c["representative"]:
                            st.code(line)
            if shown == 0:
                st.info(
                    "No clusters met the novelty threshold. Lower the slider to see more."
                )

# --------------------------------------------------------------------------- #
# Tab: Troubleshooting copilot (HF text generation)
# --------------------------------------------------------------------------- #
with tab_copilot:
    st.markdown(
        "Describe your **goal** (e.g. CyberArk root password rotation failing). "
        "The assistant’s **first** priority is to get **real error output** — paste logs or the exact message below."
    )

    if "copilot_msgs" not in st.session_state:
        st.session_state.copilot_msgs = [
            {
                "role": "assistant",
                "content": (
                    "Hi — I’m powered by a **Hugging Face** text model (default: `google/flan-t5-base`).\n\n"
                    "**Please paste the error message, stack trace, or relevant log lines** in the "
                    "**Error / logs** box. Then click **Get guidance** so I can list what to check, "
                    "which files or consoles to open, and suggested fixes."
                ),
            }
        ]

    for msg in st.session_state.copilot_msgs:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])

    st.text_area(
        "What are you trying to do?",
        height=120,
        key="copilot_goal",
        placeholder="e.g. CyberArk root password rotation keeps failing… (optional if the full error is below)",
    )
    st.text_area(
        "Error / logs (paste here)",
        height=200,
        key="copilot_errors",
        placeholder="Paste the exact error text, PVWA/CPM/Vault log lines, API response, etc. "
        "If you only have one blob, you can paste it all in this box and briefly describe in the box above.",
    )

    col_a, col_b = st.columns(2)
    with col_a:
        go = st.button("Get guidance", type="primary", key="copilot_go")
    with col_b:
        if st.button("Clear chat", key="copilot_clear"):
            st.session_state.pop("copilot_msgs", None)
            st.session_state.pop("_copilot_last_submit", None)
            st.rerun()

    # When the button fires, always read from session_state (reliable). Return values from
    # text_area can be empty on the same run as the click in some Streamlit versions.
    if go:
        g = st.session_state.get("copilot_goal", "") or ""
        e = st.session_state.get("copilot_errors", "") or ""
        g = g.strip()
        e = e.strip()

        # Effective blob for the model: prefer error box, else goal-only paste (common mistake).
        paste = e if e else g
        goal_for_prompt = g if g else "(User pasted technical details only — infer intent from the excerpt.)"

        if not paste:
            st.warning("Paste your error or logs in **Error / logs**, or put the full text in **What are you trying to do?**")
        elif len(paste) < MIN_LOG_CHARS:
            st.session_state.copilot_msgs.append(
                {
                    "role": "user",
                    "content": f"**Goal:** {g or '_(empty)_'}\n\n**Error / logs:**\n{e or '_(empty)_'}",
                }
            )
            st.session_state.copilot_msgs.append(
                {"role": "assistant", "content": ASK_PASTE_ERROR}
            )
            st.rerun()
        else:
            submit_key = hash((goal_for_prompt[:2000], paste[:4000]))
            if st.session_state.get("_copilot_last_submit") == submit_key:
                st.toast("Already processed this request — scroll up in the chat.")
            else:
                st.session_state.copilot_msgs.append(
                    {
                        "role": "user",
                        "content": f"**Goal:** {goal_for_prompt}\n\n**Error / logs:**\n{paste}",
                    }
                )
                try:
                    from app.hf_engine import generate_troubleshooting_report

                    st.info(
                        "**Working…** First run can download **~1GB** (Flan-T5) — this may take several minutes with no UI updates until it finishes."
                    )
                    with st.spinner(
                        "Running Hugging Face model (download + inference — please wait)…"
                    ):
                        answer = generate_troubleshooting_report(goal_for_prompt, paste)
                    if not (answer or "").strip():
                        answer = (
                            "_The model returned an empty string. Try a shorter paste, "
                            "or set `HF_REMEDIATION_MODEL` to another `text2text-generation` model._"
                        )
                    st.session_state.copilot_msgs.append(
                        {"role": "assistant", "content": answer}
                    )
                    st.session_state["_copilot_last_submit"] = submit_key
                except Exception as ex:
                    st.session_state.copilot_msgs.append(
                        {
                            "role": "assistant",
                            "content": (
                                f"**Model error:** `{type(ex).__name__}: {ex}`\n\n"
                                "Check: `pip install transformers accelerate`, disk space, network, and `HF_REMEDIATION_MODEL`. "
                                "If you’re offline, the first download cannot complete."
                            ),
                        }
                    )
                    st.session_state["_copilot_last_submit"] = submit_key
                st.toast("Response added — scroll the chat above.")
            st.rerun()

    st.caption(
        "Models: `HF_REMEDIATION_MODEL` (text fixes, default Flan-T5) · clustering uses `sentence-transformers/all-MiniLM-L6-v2`. "
        "For training: fine-tune the same Flan-T5 class on HF and point the env var to your repo."
    )
