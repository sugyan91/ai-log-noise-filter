# Deploy this app on Hugging Face Spaces (no “Streamlit” SDK in the form)

**Shortcut:** the repo root folder **`hf-space/`** already contains a full copy (`Dockerfile`, `app.py`, `requirements.txt`, `app/`, `ui/`, `samples/`, `README.md`) ready to paste into your Space repository. To refresh copies after editing the main app, run `./scripts/sync-hf-space.sh` from the repo root.

The **New Space** form often only offers **Gradio**, **Docker**, and **Static**. Use **Docker** and point Streamlit at port **8501**.

## Steps

1. Go to [Create a new Space](https://huggingface.co/new-space).
2. Choose **SDK: Docker** (not Streamlit).
3. After the repo is created, add these files at the **root** of the Space (same layout as this GitHub repo’s root for app code):
   - `Dockerfile` — copy from `deploy/huggingface/Dockerfile` in this project, **but** change the `COPY` line for `app.py` to `COPY --chown=user app.py ./app.py` (see below).
   - `app.py` — copy from `deploy/huggingface/app.py`.
   - `requirements.txt`, `app/`, `ui/`, `samples/` from this repository.

4. Replace the Space’s `README.md` with the YAML below (merge with your title), or edit the existing YAML block:

```yaml
---
title: AI Log Noise Filter
emoji: 📊
colorFrom: green
colorTo: blue
sdk: docker
app_port: 8501
short_description: Paste logs, cluster errors, optional HF copilot.
---
```

5. **Dockerfile in the Space repo** must copy `app.py` from the Space root (not `deploy/huggingface/`). Use this single change vs the repo version:

```dockerfile
COPY --chown=user app.py ./app.py
```

instead of

```dockerfile
COPY --chown=user deploy/huggingface/app.py ./app.py
```

All other `COPY` lines stay the same (`requirements.txt`, `app`, `ui`, `samples` next to the Dockerfile).

6. Commit and push. Builds are slow on the free tier (ML dependencies).

## Optional: try native Streamlit SDK

Some accounts still support `sdk: streamlit` only via README. You can duplicate an existing Streamlit Space (e.g. search Spaces for “streamlit”) or create a repo and set `sdk: streamlit` in the README YAML; if the build system accepts it, you only need `app.py` + `requirements.txt` at the root. If the UI never offers Streamlit, the Docker path above is the reliable option.
