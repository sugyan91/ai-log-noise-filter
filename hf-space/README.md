---
title: AI Log Noise Filter
emoji: 📊
colorFrom: green
colorTo: blue
sdk: docker
app_port: 8501
short_description: Paste logs, cluster errors, optional Hugging Face copilot.
---

# AI Log Noise Filter (Streamlit)

The `Dockerfile` downloads **`requirements.txt`** and **`samples/demo.log`** from GitHub during build, so your Space repo does **not** need those files locally (you still need **`app/`**, **`ui/`**, **`app.py`**, and this **`Dockerfile`**).

This folder is a **ready-to-push** copy for [Hugging Face Spaces](https://huggingface.co/docs/hub/spaces-overview) using the **Docker** SDK.

## Push to your Space

1. Create a Space with SDK **Docker** on [huggingface.co/new-space](https://huggingface.co/new-space).
2. Clone your Space repo and **copy the entire contents of this `hf-space` folder** into it (replace existing files), or add this folder as remote — see below.
3. Commit and push:

```bash
git add -A
git commit -m "Deploy Streamlit app"
git push
```

## One-line copy from a full clone of the GitHub repo

If you have the main repo cloned and want to refresh this bundle from `main`:

```bash
# from repository root (parent of hf-space/)
rsync -a --delete hf-space/ /path/to/your-hf-space-clone/
```

Then `cd` to your HF clone, commit, and push.

## Source of truth

The canonical app lives in the main project; this directory is duplicated for easy uploads. After changing `app/`, `ui/`, or `requirements.txt` in the main repo, refresh `hf-space/` (or re-run your sync) before redeploying.
