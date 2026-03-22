"""HF Space entry: Streamlit loads this file; real UI lives in ui/streamlit_app.py."""
import runpy
from pathlib import Path

_root = Path(__file__).resolve().parent
runpy.run_path(str(_root / "ui" / "streamlit_app.py"), run_name="__main__")
