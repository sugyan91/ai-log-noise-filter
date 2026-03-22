#!/bin/bash
set -e
cd "$(dirname "$0")"

if [ ! -d venv ]; then
  osascript -e 'display dialog "No venv found. Open README.md — Run locally — then try again." buttons {"OK"} default button "OK" with title "AI Log Noise Filter"'
  exit 1
fi

source venv/bin/activate
exec streamlit run ui/streamlit_app.py
