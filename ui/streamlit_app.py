import hashlib
import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import streamlit as st
from app.parsing import parse_lines
from app.error_summary import summarize_errors, filter_by_window
from app.llm_explain import explain_error_group


def _inject_global_style() -> None:
    st.markdown(
        """
<style>
    /* Log textarea — grey placeholder */
    [data-testid="stTextArea"] textarea::placeholder {
        color: #94a3b8 !important;
        opacity: 1 !important;
        font-size: 0.95rem !important;
    }
    [data-testid="stTextArea"] textarea {
        font-size: 0.92rem !important;
    }

    .stTabs [data-baseweb="tab-list"] {
        gap: 8px;
        background: linear-gradient(180deg, #f1f5f9 0%, #e2e8f0 100%);
        padding: 8px 10px 0 10px;
        border-radius: 12px 12px 0 0;
        border: 1px solid #cbd5e1;
        border-bottom: none;
    }
    .stTabs [data-baseweb="tab-list"] button[data-baseweb="tab"] {
        border-radius: 10px 10px 0 0 !important;
        padding: 11px 20px !important;
        font-size: 0.9rem !important;
        font-family: system-ui, -apple-system, "Segoe UI", Roboto, sans-serif !important;
        letter-spacing: 0.02em;
        border: 2px solid transparent !important;
        transition: background 0.18s ease, color 0.18s ease, box-shadow 0.18s ease;
        /* Default (inactive): same mint / forest as Log analysis — both tab labels match */
        background: linear-gradient(180deg, #ecfdf5 0%, #d1fae5 100%) !important;
        color: #065f46 !important;
        border-color: #6ee7b7 !important;
    }
    .stTabs [data-baseweb="tab-list"] button[data-baseweb="tab"]:hover {
        background: linear-gradient(180deg, #d1fae5 0%, #a7f3d0 100%) !important;
        color: #064e3b !important;
    }
    /* Selected tab — teal (overrides hover + idle) */
    .stTabs [data-baseweb="tab-list"] button[data-baseweb="tab"][aria-selected="true"] {
        background: linear-gradient(135deg, #0d9488 0%, #0f766e 55%, #115e59 100%) !important;
        color: #f0fdfa !important;
        border-color: #2dd4bf !important;
        font-weight: 700 !important;
        box-shadow: 0 8px 24px rgba(13, 148, 136, 0.4);
    }
    .stTabs [data-baseweb="tab-list"] button[data-baseweb="tab"][aria-selected="true"]:hover {
        background: linear-gradient(135deg, #0f766e 0%, #115e59 55%, #134e4a 100%) !important;
        color: #f0fdfa !important;
    }

    /* Platform source grid — uniform chip buttons inside st.container(border=True) */
    [data-testid="stVerticalBlockBorderWrapper"] div[data-testid="column"] .stButton > button {
        width: 100% !important;
        min-height: 2.95rem !important;
        font-size: 0.78rem !important;
        font-weight: 600 !important;
        line-height: 1.2 !important;
        padding: 0.45rem 0.5rem !important;
        border-radius: 8px !important;
        text-align: center !important;
    }
</style>
""",
        unsafe_allow_html=True,
    )


def _hero_banner() -> None:
    svg_server = """<svg width="52" height="52" viewBox="0 0 48 48" xmlns="http://www.w3.org/2000/svg" aria-hidden="true"><defs><linearGradient id="g1" x1="0" y1="0" x2="1" y2="1"><stop offset="0%" stop-color="#38bdf8"/><stop offset="100%" stop-color="#0284c7"/></linearGradient></defs><rect x="7" y="5" width="34" height="38" rx="4" fill="#1e293b" stroke="url(#g1)" stroke-width="1.5"/><rect x="11" y="9" width="26" height="5" rx="1" fill="#334155"/><rect x="11" y="17" width="26" height="5" rx="1" fill="#334155"/><rect x="11" y="25" width="26" height="5" rx="1" fill="#334155"/><rect x="11" y="33" width="26" height="5" rx="1" fill="#475569"/><circle cx="34" cy="11" r="2" fill="#22c55e"/></svg>"""
    svg_net = """<svg width="58" height="52" viewBox="0 0 56 48" xmlns="http://www.w3.org/2000/svg" aria-hidden="true"><circle cx="14" cy="24" r="7" fill="#0ea5e9" opacity="0.9"/><circle cx="42" cy="10" r="6" fill="#38bdf8"/><circle cx="42" cy="38" r="6" fill="#38bdf8"/><path d="M20 24 L36 12" stroke="#7dd3fc" stroke-width="2.5" fill="none"/><path d="M20 24 L36 36" stroke="#7dd3fc" stroke-width="2.5" fill="none"/><path d="M42 16 L42 32" stroke="#7dd3fc" stroke-width="2" fill="none" opacity="0.6"/></svg>"""
    st.markdown(
        f"""
<div class="sl-banner" style="font-family: system-ui, -apple-system, 'Segoe UI', Roboto, sans-serif;">
    <div style="
        display: flex;
        flex-wrap: wrap;
        align-items: stretch;
        gap: 1.25rem;
        background: linear-gradient(135deg, #0f172a 0%, #1e3a5f 50%, #0c4a6e 100%);
        color: #f8fafc;
        padding: 1.5rem 1.75rem;
        border-radius: 12px;
        margin-bottom: 0.75rem;
        box-shadow: 0 12px 40px -10px rgba(15, 23, 42, 0.5);
        border: 1px solid rgba(148, 163, 184, 0.2);
    ">
        <div style="flex: 1; min-width: 220px;">
            <p style="margin: 0 0 0.35rem 0; font-size: 0.7rem; letter-spacing: 0.14em; text-transform: uppercase; opacity: 0.88; font-weight: 700;">
                Welcome
            </p>
            <h1 style="margin: 0; font-family: Georgia, 'Times New Roman', serif; font-size: clamp(1.4rem, 2.8vw, 1.9rem); font-weight: 600; letter-spacing: -0.02em; color: #fff;">
                Sugyan&rsquo;s AI Log Noise Filter
            </h1>
            <p style="margin: 0.75rem 0 0 0; font-size: 1rem; line-height: 1.55; opacity: 0.9; max-width: 38rem;">
                Find practical answers for <strong>servers</strong>, <strong>networks</strong>, and <strong>apps</strong>—paste logs or errors, see what matters, and get guided fixes.
            </p>
        </div>
        <div style="display: flex; align-items: center; gap: 0.5rem; opacity: 0.95;">
            <div title="Servers & hosts">{svg_server}</div>
            <div title="Network & dependencies">{svg_net}</div>
        </div>
    </div>
    <div style="
        margin-bottom: 1rem;
        padding: 12px 14px;
        background: linear-gradient(90deg, #f0f9ff 0%, #faf5ff 100%);
        border-radius: 10px;
        border: 1px solid #bae6fd;
        font-size: 0.88rem;
        color: #334155;
        line-height: 1.5;
    ">
        <strong style="color:#0c4a6e;">Tip:</strong> Open <strong>Log analysis</strong> and click a <strong>colored source chip</strong> — we’ll drop a starter template into the paste box so you can add your logs right away.
        <span style="opacity:0.85;"> Not sure? Choose <strong>General</strong>.</span>
    </div>
</div>
""",
        unsafe_allow_html=True,
    )


st.set_page_config(
    page_title="Sugyan's AI Log Noise Filter",
    page_icon="📋",
    layout="wide",
    initial_sidebar_state="expanded",
)
_inject_global_style()
_hero_banner()

# Start with an empty log box until user pastes or picks a template / example.
if "log_input" not in st.session_state:
    st.session_state.log_input = ""

_SAMPLE_PATH = os.path.normpath(
    os.path.join(os.path.dirname(__file__), "..", "samples", "demo.log")
)

ASK_PASTE_ERROR = """### Need a bit more to work with
Paste at least **20 characters** of real output: the **exact** error line, **stack trace**, API/HTTP body, or **log snippet** (timestamps help).

You can use **either** box — if you only use **What are you trying to do?**, put the full error there and leave **Error / logs** empty.

Then click **Get guidance** again."""

MIN_LOG_CHARS = 20

# Click a chip → inserts this text into the log box so users can paste underneath.
PLATFORM_SCAFFOLDS: dict[str, str] = {
    "general": (
        "# ⭐ General — not sure what you have?\n"
        "# Paste ANYTHING below: errors, stack traces, ticket text, screenshots copied as text, "
        "or mixed logs. We’ll try to detect timestamps and severity.\n\n"
    ),
    "rhel": (
        "# Red Hat / RHEL\n"
        "# Paste: journalctl, /var/log/messages, audit.log, dnf/yum, sosreport, OpenShift node logs…\n\n"
    ),
    "windows": (
        "# Windows\n"
        "# Paste: Event Viewer export, Get-WinEvent, IIS, AD / DNS, PowerShell errors…\n\n"
    ),
    "linux": (
        "# Linux (syslog)\n"
        "# Paste: /var/log/syslog, auth.log, kern.log, Debian/Ubuntu/SUSE style lines…\n\n"
    ),
    "macos": (
        "# macOS\n"
        "# Paste: log show --style syslog, Console.app export, unified logging…\n\n"
    ),
    "k8s": (
        "# Kubernetes / containers\n"
        "# Paste: kubectl logs, pod describe, ingress, API server, CNI, Helm install output…\n\n"
    ),
    "aws": (
        "# Amazon Web Services (AWS)\n"
        "# Paste: CloudWatch log snippets, CloudTrail JSON, Lambda, ECS task logs…\n\n"
    ),
    "azure": (
        "# Microsoft Azure\n"
        "# Paste: App Insights / Log Analytics export, Activity Log, AKS pod logs…\n\n"
    ),
    "gcp": (
        "# Google Cloud (GCP)\n"
        "# Paste: Cloud Logging export, GKE workload logs, Cloud Run…\n\n"
    ),
    "docker": (
        "# Docker / containerd\n"
        "# Paste: docker logs, docker compose, build output…\n\n"
    ),
    "vmware": (
        "# VMware\n"
        "# Paste: ESXi hostd / vmkernel, vCenter events, vSAN / NSX excerpts…\n\n"
    ),
    "apps": (
        "# Apps — JSON / APIs / microservices\n"
        "# Paste: one JSON object per line, API gateway logs, structured app logs…\n\n"
    ),
}


def _platform_chip_button(
    label: str,
    plat_key: str,
    *,
    primary: bool = False,
    tip: str = "",
) -> None:
    """Clickable chip: loads a paste template into ``st.session_state.log_input``."""
    help_txt = tip or (
        f"Insert a starter template for this source. Paste your real log lines below the # comment lines."
    )
    if st.button(
        label,
        key=f"plat_{plat_key}",
        use_container_width=True,
        type="primary" if primary else "secondary",
        help=help_txt,
    ):
        st.session_state.log_input = PLATFORM_SCAFFOLDS.get(
            plat_key, PLATFORM_SCAFFOLDS["general"]
        )
        st.toast("Template loaded — paste your logs under the comment lines.")
        st.rerun()


WINDOW_CHOICES: list[tuple[int, str]] = [
    (5, "5 min — only the very latest activity"),
    (15, "15 min — short incident window"),
    (60, "1 hour — good default for most pastes"),
    (240, "4 hours — longer shift / rollout"),
    (1440, "24 hours — full day before newest log time"),
]

with st.sidebar:
    st.markdown("### How this app works")
    st.markdown(
        """
**Log analysis**  
Click a **source chip** (e.g. **General**, **RHEL**, **Windows**) to drop a paste template, add your logs, then **Run analysis**. The app groups repeated errors and can narrow the time window.

**Right-hand panel (when you analyze)**  
- **How far back to look** — We find the **newest timestamp** in your file, then only keep lines in that many **minutes before** it. *Example:* 60 min = “last hour of the story,” not clock time on your PC.  
- **How many error types to show** — Each “type” is one pattern (IDs and IPs are merged). Lower = shorter report.

**Troubleshooting copilot**  
Describe what you’re doing and paste the **exact** error; the HF model suggests checks and fixes.

---
*Red Hat®, RHEL®, and Windows® are trademarks of their owners. This tool is independent and not endorsed by them.*
        """
    )

tab_logs, tab_copilot = st.tabs(
    [
        "📊  Log analysis",
        "📊  Troubleshooting copilot",
    ]
)

# --------------------------------------------------------------------------- #
# Tab: Log analysis
# --------------------------------------------------------------------------- #
with tab_logs:
    st.success(
        "**Step 1:** Paste logs (or load sample). **Step 2:** Adjust options on the **right** if needed. "
        "**Step 3:** Click **Run analysis**."
    )

    mode = st.radio(
        "What do you want?",
        ["Summarize errors & warnings (recommended)", "Group similar lines with AI (advanced)"],
        index=0,
        horizontal=True,
        help="Error summary counts ERROR/WARN. AI clustering uses embeddings to find themes (heavier).",
    )
    mode_is_summary = mode.startswith("Summarize")

    col1, col2 = st.columns([2, 1])

    with col1:
        st.markdown(
            """
<div style="
    background: linear-gradient(135deg, #f0fdf4 0%, #ecfeff 100%);
    border: 1px solid #a7f3d0;
    border-radius: 12px;
    padding: 10px 14px;
    margin-bottom: 10px;
    font-size: 0.9rem;
    color: #334155;
">
    <strong style="color:#047857;">Log source</strong> — optional chips below insert a short header; then add your lines. 
    <span style="color:#64748b;">Not sure? Click <strong>General</strong>.</span>
</div>
""",
            unsafe_allow_html=True,
        )

        with st.container(border=True):
            st.markdown(
                "<div style='font-weight:700;font-size:0.95rem;color:#0f172a;margin-bottom:2px;'>"
                "Choose platform <span style='font-weight:500;color:#64748b;font-size:0.82rem;'>"
                "(same-size tiles — hover for details)</span></div>",
                unsafe_allow_html=True,
            )
            g4 = st.columns(4)
            with g4[0]:
                _platform_chip_button(
                    "⭐ General",
                    "general",
                    primary=True,
                    tip="Not sure what you have? Inserts a neutral template — paste any errors or logs below.",
                )
            with g4[1]:
                _platform_chip_button(
                    "Red Hat",
                    "rhel",
                    tip="RHEL / Fedora family: journalctl, /var/log/messages, audit, OpenShift nodes, dnf…",
                )
            with g4[2]:
                _platform_chip_button(
                    "Windows",
                    "windows",
                    tip="Event Viewer export, Get-WinEvent, IIS, AD, PowerShell errors…",
                )
            with g4[3]:
                _platform_chip_button(
                    "Linux",
                    "linux",
                    tip="syslog-style: /var/log/syslog, auth.log, Debian/Ubuntu/SUSE…",
                )

            g4b = st.columns(4)
            with g4b[0]:
                _platform_chip_button(
                    "macOS",
                    "macos",
                    tip="log show, Console.app export, unified logging…",
                )
            with g4b[1]:
                _platform_chip_button(
                    "Kubernetes",
                    "k8s",
                    tip="kubectl logs, pod describe, ingress, API server, Helm…",
                )
            with g4b[2]:
                _platform_chip_button(
                    "AWS",
                    "aws",
                    tip="CloudWatch, CloudTrail JSON, Lambda, ECS…",
                )
            with g4b[3]:
                _platform_chip_button(
                    "Azure",
                    "azure",
                    tip="App Insights, Log Analytics, Activity Log, AKS…",
                )

            g4c = st.columns(4)
            with g4c[0]:
                _platform_chip_button(
                    "GCP",
                    "gcp",
                    tip="Cloud Logging, GKE, Cloud Run…",
                )
            with g4c[1]:
                _platform_chip_button(
                    "Docker",
                    "docker",
                    tip="docker logs, compose, build output…",
                )
            with g4c[2]:
                _platform_chip_button(
                    "VMware",
                    "vmware",
                    tip="ESXi hostd/vmkernel, vCenter, vSAN/NSX snippets…",
                )
            with g4c[3]:
                _platform_chip_button(
                    "JSON / API",
                    "apps",
                    tip="Structured app logs, one JSON object per line, API gateways…",
                )

        st.markdown("##### 📄 Your log text")
        log_input = st.text_area(
            "Paste logs here",
            height=260,
            label_visibility="collapsed",
            key="log_input",
            placeholder="Paste your logs here and hit the Run analysis button",
        )
        up_col1, up_col2 = st.columns(2)
        with up_col1:
            uploaded = st.file_uploader("Upload .log / .txt", type=["log", "txt"])
        with up_col2:
            if st.button(
                "📥 Load example logs",
                help="Fills the box from samples/demo.log",
                type="tertiary",
            ):
                try:
                    with open(_SAMPLE_PATH, encoding="utf-8") as f:
                        st.session_state.log_input = f.read()
                    st.session_state["_run_after_sample"] = True
                    st.rerun()
                except OSError:
                    st.error(f"Could not read sample file: {_SAMPLE_PATH}")

    with col2:
        st.markdown(
            """
<div style="
    background: linear-gradient(180deg, #f8fafc 0%, #f1f5f9 100%);
    border: 1px solid #cbd5e1;
    border-radius: 12px;
    padding: 14px 16px 16px 16px;
    margin-bottom: 8px;
">
    <div style="display:flex; align-items:center; gap:8px; margin-bottom:10px;">
        <span style="font-size:1.35rem;">⚙️</span>
        <span style="font-weight:700; font-size:1.05rem; color:#0f172a;">Analysis settings</span>
    </div>
    <p style="margin:0 0 12px 0; font-size:0.82rem; color:#475569; line-height:1.45;">
        These only affect the <strong>next</strong> run. Tip: start with defaults, then narrow the time window if the file spans days.
    </p>
</div>
""",
            unsafe_allow_html=True,
        )
        run_btn = st.button("▶ Run analysis", type="primary", use_container_width=True)

        if mode_is_summary:
            window = st.selectbox(
                "How far back from the newest log line?",
                options=[x[0] for x in WINDOW_CHOICES],
                format_func=lambda m: next(lbl for v, lbl in WINDOW_CHOICES if v == m),
                index=2,
                help=(
                    "We detect the latest timestamp in your paste. Only ERROR/WARN lines inside this many "
                    "minutes *before* that time are used for the summary. Lines without times are kept."
                ),
            )
            include_warn = st.checkbox(
                "Count WARNING lines too",
                value=True,
                help="If off, only ERROR-level lines are grouped.",
            )
            explain = st.checkbox(
                "Show quick explanations (built-in rules)",
                value=True,
            )
            use_hf_explain = st.checkbox(
                "Allow Hugging Face deep-dive per error (button in each row)",
                value=True,
                help="First use downloads the Flan-T5 model (~1 GB).",
            )
            max_groups = st.slider(
                "How many different error types to list?",
                5,
                50,
                20,
                5,
                help=(
                    "Each type is one normalized pattern (same message with different IPs/IDs counts as one). "
                    "Increase if you have many distinct failures."
                ),
            )
        else:
            novelty_threshold = st.slider(
                "Show only clusters this “interesting” or higher (0–1)",
                0.0,
                1.0,
                0.35,
                0.05,
                help="Higher = fewer clusters shown; each cluster is a group of similar log lines (AI).",
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
        st.caption("Paste logs and click **Run analysis**.")
    elif not lines:
        st.warning("No logs provided — paste text, upload a file, or load the example.")
    else:
        events = parse_lines(lines)

        if mode_is_summary:
            events_w = filter_by_window(events, window_minutes=window)
            summary = summarize_errors(events_w, include_warn=include_warn)

            levels = {"ERROR"} | ({"WARN"} if include_warn else set())
            n_err_warn = sum(1 for e in events_w if e.level in levels)
            n_structured = sum(1 for e in events_w if e.level is not None)

            st.subheader("📌 What’s going on")
            st.markdown(
                f"- **Lines you sent:** {len(lines)} → **parsed events:** {len(events)} "
                f"({n_structured} with a detected level)."
            )
            if summary:
                total_hits = sum(r["count"] for r in summary)
                st.markdown(
                    f"- Using **{window} minutes** before the **newest** timestamp in your file: "
                    f"**{total_hits}** ERROR/WARN lines → **{len(summary)}** distinct issue pattern(s)."
                )
                st.markdown("**Top issues (IDs/IPs merged into one pattern):**")
                top_n = min(5, len(summary))
                for row in summary[:top_n]:
                    msg = row["message"]
                    cnt = row["count"]
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
            st.subheader("📂 Details")
            st.caption(
                f"Time filter: last **{window} minutes** before the latest timestamp. Open a row for samples and fixes."
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
                                st.write("**Quick read (built-in rules):**")
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
                                        "🤗 Run Hugging Face remediation for this group",
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
                            st.write("**Example lines:**")
                            for exline in examples:
                                st.code(exline)
        else:
            from app.pipeline import run_pipeline

            with st.spinner("Embedding + clustering (Hugging Face sentence-transformers)…"):
                result = run_pipeline(lines)

            st.subheader("📌 What’s going on")
            st.markdown(
                f"- **Lines:** {result['total_lines']} → **parsed events:** {result['parsed_events']}.\n"
                f"- **Clusters:** **{len(result['clusters'])}** (embeddings: `all-MiniLM-L6-v2` on Hugging Face Hub)."
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
    st.success(
        "**Step 1:** Describe what you’re fixing. **Step 2:** Paste the **exact** error or log snippet. "
        "**Step 3:** Click **Get guidance**."
    )

    st.markdown(
        """
<div style="
    background: linear-gradient(135deg, #f0fdf4 0%, #ecfeff 100%);
    border: 1px solid #a7f3d0;
    border-radius: 12px;
    padding: 10px 14px;
    margin-bottom: 10px;
    font-size: 0.9rem;
    font-family: system-ui, -apple-system, 'Segoe UI', Roboto, sans-serif;
    color: #334155;
">
    <strong style="color:#047857;">Troubleshooting copilot</strong> — same style as Log analysis above. 
    Describe your situation (CyberArk, AD, Linux service, etc.), then paste the <strong>exact</strong> error or log lines so the model can suggest checks and fixes.
</div>
""",
        unsafe_allow_html=True,
    )

    if "copilot_msgs" not in st.session_state:
        st.session_state.copilot_msgs = [
            {
                "role": "assistant",
                "content": (
                    "Hi — I use a **Hugging Face** model (**`google/flan-t5-base`** by default).\n\n"
                    "**Paste the error message, stack trace, or log lines** in **Error / logs**, then click **Get guidance**."
                ),
            }
        ]

    for msg in st.session_state.copilot_msgs:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])

    st.markdown("##### 📄 Your goal & error text")
    st.caption(
        "Same typography as Log analysis — use the boxes below, then **Get guidance** (like **Run analysis** on the other tab)."
    )

    st.text_area(
        "What are you trying to do?",
        height=120,
        key="copilot_goal",
        placeholder="e.g. Root password rotation in CyberArk keeps failing on RHEL…",
    )
    st.text_area(
        "Error / logs (paste here)",
        height=200,
        key="copilot_errors",
        placeholder="Paste exact output: PVWA, Vault, Windows Event, journalctl, API JSON, etc.",
    )

    col_a, col_b = st.columns(2)
    with col_a:
        go = st.button("▶ Get guidance", type="primary", key="copilot_go", use_container_width=True)
    with col_b:
        if st.button("Clear chat", key="copilot_clear", type="tertiary", use_container_width=True):
            st.session_state.pop("copilot_msgs", None)
            st.session_state.pop("_copilot_last_submit", None)
            st.rerun()

    if go:
        g = st.session_state.get("copilot_goal", "") or ""
        e = st.session_state.get("copilot_errors", "") or ""
        g = g.strip()
        e = e.strip()

        paste = e if e else g
        goal_for_prompt = g if g else "(User pasted technical details only — infer intent from the excerpt.)"

        if not paste:
            st.warning(
                "Paste your error or logs in **Error / logs**, or put the full text in **What are you trying to do?**"
            )
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
                        "**Working…** First run can download **~1GB** (Flan-T5) — may take several minutes."
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
        "Models: `HF_REMEDIATION_MODEL` (text) · clustering: `all-MiniLM-L6-v2`. "
        "Not affiliated with Red Hat or Microsoft."
    )
