# AI Log Noise Filter

A pragmatic SRE-focused tool to reduce log noise and surface what matters.

## On your resume (for interviewers)

1. **Host the code** on a public GitHub (or GitLab) repository and put the **HTTPS clone URL** in your resume or portfolio, e.g. `https://github.com/<you>/ai-log-noise-filter`.
2. **Optional:** Add one line under the project: *“Clone, follow README → Run locally,”* so reviewers know they do not need your machine.
3. **Optional:** Record a **30–60s screen capture** (paste logs → run → summary) and link it from the repo README or your portfolio; some reviewers skim before installing.

This repo is self-contained: no database required. Heuristic explanations work offline; **optional Hugging Face** models download on first use for deeper remediation text.

## Features
- ERROR/WARN aggregation with counts
- Time-window filtering
- **Troubleshooting copilot** tab: describe your goal, paste errors/logs → HF text model suggests checks, files/consoles, and fixes
- Heuristic explanations + **on-demand Hugging Face (Flan-T5)** remediation per error group
- Optional AI clustering + novelty detection (**sentence-transformers** / HF Hub embeddings)

## Hugging Face models & fine-tuning

| Purpose | Default model | Override |
|--------|----------------|----------|
| Log clustering embeddings | `sentence-transformers/all-MiniLM-L6-v2` | Edit `app/embedding.py` |
| Remediation / copilot text | `google/flan-t5-base` | Env **`HF_REMEDIATION_MODEL`** (any compatible `text2text-generation` checkpoint on the Hub) |

To use a **fine-tuned** model: train Flan-T5 (or similar seq2seq) with Hugging Face `Trainer` / TRL on your (prompt, answer) pairs, push the checkpoint to the Hub, then set `HF_REMEDIATION_MODEL=your-org/your-model`.

## Prerequisites

- **Python 3.10+** (3.11 recommended)
- Network for **`pip install`** and first-time **Hugging Face** downloads (embeddings for clustering; **Flan-T5** for copilot / remediation — can take several minutes and ~1GB+ disk)

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

The UI opens in your browser (usually `http://localhost:8501`). Use **Log analysis** for paste → **Analyze**, or **Troubleshooting copilot** for natural-language goals + pasted errors (HF text model).

**Quick test:** **Load example logs** → **Analyze**; or open **Troubleshooting copilot**, describe a goal, paste a fake error line, **Get guidance**.

### Notes for reviewers

- **Error summary** heuristics run offline; **Hugging Face** remediation downloads **Flan-T5** (~1GB) on first use.
- **AI clustering** downloads embedding weights on first use; start with a small paste for a quick tryout.
- **`HF_REMEDIATION_MODEL`:** optional; point to your Hub checkpoint after fine-tuning.
- **`OPENAI_API_KEY`:** not used if unset; HF paths do not require it.
