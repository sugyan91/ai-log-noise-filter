import os, sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import streamlit as st
from app.parsing import parse_lines
from app.error_summary import summarize_errors, filter_by_window
from app.pipeline import run_pipeline
from app.llm_explain import explain_error_group

st.set_page_config(page_title="AI Log Noise Filter", layout="wide")
st.title("AI Log Noise Filter")

# Default view = Error summary
mode = st.radio(
    "View mode",
    ["Error summary (default)", "AI clustering (advanced)"],
    index=0,
    horizontal=True
)

col1, col2 = st.columns([2, 1])

if "log_text" not in st.session_state:
    st.session_state.log_text = ""

with col1:
    st.subheader("Input logs")
    st.session_state.log_text = st.text_area(
        "Paste logs here",
        value=st.session_state.log_text,
        height=300,
        key="log_text_area",
        placeholder="Paste raw logs here...",
    )
    uploaded = st.file_uploader("Or upload a .log/.txt file", type=["log", "txt"])

with col2:
    st.subheader("Controls")
    run_btn = st.button("Run analysis", type="primary")

    if mode == "Error summary (default)":
        window = st.selectbox("Time window (relative to latest log)", [5, 15, 60, 240, 1440], index=2)
        include_warn = st.checkbox("Include WARN", value=True)
        explain = st.checkbox("Explain each error group", value=True)
        max_groups = st.slider("Max groups to show", 5, 50, 20, 5)
    else:
        novelty_threshold = st.slider("Show clusters with max novelty ≥", 0.0, 1.0, 0.35, 0.05)

lines = []
if uploaded is not None:
    content = uploaded.read().decode("utf-8", errors="ignore")
    lines = content.splitlines()
elif st.session_state.log_text.strip():
    lines = st.session_state.log_text.splitlines()

if not run_btn:
    st.info("Paste logs or upload a file, then click **Run analysis**.")
    st.stop()

if not lines:
    st.warning("No logs provided.")
    st.stop()

events = parse_lines(lines)

if mode == "Error summary (default)":
    # time window filter
    events_w = filter_by_window(events, window_minutes=window)
    summary = summarize_errors(events_w, include_warn=include_warn)

    st.subheader("Error summary")
    st.caption(f"Showing last {window} minute(s) relative to the latest timestamp found in the log file.")

    if not summary:
        st.success("No ERROR/WARN logs found in this window 🎉")
        st.stop()

    # Build a quick lookup for examples per normalized message
    examples_map = {}
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
                    st.write("**Explanation / probable cause:**")
                    st.write(explain_error_group(msg, cnt, examples))
                except Exception as ex:
                    st.warning(f"Explanation failed: {ex}")

            if examples:
                st.write("**Examples:**")
                for exline in examples:
                    st.code(exline)

else:
    with st.spinner("Embedding + clustering..."):
        result = run_pipeline(lines)

    st.success(f"Parsed {result['parsed_events']} events. Found {len(result['clusters'])} clusters (incl. outliers).")

    clusters = sorted(
        result["clusters"],
        key=lambda c: (c["max_novelty"], c["count"]),
        reverse=True
    )

    st.subheader("Clusters")
    shown = 0
    for c in clusters:
        if c["cluster_id"] != -1 and c["max_novelty"] < novelty_threshold:
            continue
        shown += 1
        with st.expander(f"Cluster {c['cluster_id']} — count={c['count']} — max_novelty={c['max_novelty']:.2f}"):
            st.write("**Keywords:**", ", ".join(c["keywords"]))
            if c["representative"]:
                st.write("**Representative lines:**")
                for line in c["representative"]:
                    st.code(line)
    if shown == 0:
        st.info("No clusters met the novelty threshold. Lower the slider to see more.")

