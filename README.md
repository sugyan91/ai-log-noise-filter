# AI Log Noise Filter

A pragmatic SRE-focused tool to reduce log noise and surface what matters.

## Features
- ERROR/WARN aggregation with counts
- Time-window filtering
- Human-readable explanations (offline or LLM-backed)
- Optional AI clustering + novelty detection

## Run locally

```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
streamlit run ui/streamlit_app.py

