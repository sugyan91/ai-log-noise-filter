# AI Log Noise Filter

A pragmatic SRE-focused tool to reduce log noise and surface what matters.

## On your resume (for interviewers)

1. **Host the code** on a public GitHub (or GitLab) repository and put the **HTTPS clone URL** in your resume or portfolio, e.g. `https://github.com/<you>/ai-log-noise-filter`.
2. **Optional:** Add one line under the project: *“Clone, follow README → Run locally,”* so reviewers know they do not need your machine.
3. **Optional:** Record a **30–60s screen capture** (paste logs → run → summary) and link it from the repo README or your portfolio; some reviewers skim before installing.

This repo is self-contained: no database, no API keys required for the default flow (explanations use built-in heuristics unless you wire an LLM yourself).

## Features
- ERROR/WARN aggregation with counts
- Time-window filtering
- Human-readable explanations (offline or LLM-backed)
- Optional AI clustering + novelty detection

## Prerequisites

- **Python 3.10+** (3.11 recommended)
- Network access for **`pip install`** (and the first run of **AI clustering**, which downloads an embedding model — can take a few minutes)

## Run locally

**macOS / Linux**

```bash
git clone https://github.com/<you>/ai-log-noise-filter.git
cd ai-log-noise-filter
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
streamlit run ui/streamlit_app.py
```

**Windows (PowerShell)**

```powershell
git clone https://github.com/<you>/ai-log-noise-filter.git
cd ai-log-noise-filter
python -m venv venv
.\venv\Scripts\Activate.ps1
pip install -r requirements.txt
streamlit run ui\streamlit_app.py
```

The UI opens in your browser (usually `http://localhost:8501`). Click **Run analysis** after pasting logs or uploading a file.

**Quick test:** upload `samples/demo.log` or paste its contents, then use **Error summary (default)** with **Run analysis**.

### Notes for reviewers

- **Error summary** mode runs fully offline after install.
- **AI clustering (advanced)** pulls ML dependencies and may download a model on first use; use a smaller paste first if you want a faster tryout.
- **`OPENAI_API_KEY`:** leave unset for heuristic explanations. The code path for a live LLM is not implemented in this repo; setting the key alone will not enable a remote model.
