# app/parsing.py
import re
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Optional, List

# Patterns used for normalization (reduce noise from IDs, IPs, etc.)
UUID_RE = re.compile(r"\b[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}\b", re.I)
IP_RE = re.compile(r"\b(?:\d{1,3}\.){3}\d{1,3}\b")
HEX_RE = re.compile(r"\b0x[0-9a-f]+\b", re.I)
LONG_NUM_RE = re.compile(r"\b\d{5,}\b")
PATH_RE = re.compile(r"(/[^ ]+)+")
EMAIL_RE = re.compile(r"\b[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}\b", re.I)

# Expected log format (MVP):
# 2025-03-12T09:01:11Z INFO auth-service Message here key=value ...
LOG_LINE_RE = re.compile(
    r"^(?P<ts>\S+)\s+(?P<level>INFO|WARN|ERROR)\s+(?P<service>[\w\-]+)\s+(?P<msg>.*)$"
)

@dataclass
class LogEvent:
    raw: str
    normalized: str
    timestamp: Optional[str] = None
    level: Optional[str] = None
    service: Optional[str] = None
    ts_epoch: Optional[float] = None

def normalize_message(msg: str) -> str:
    """
    Normalize a log message by removing high-cardinality tokens while preserving meaning.
    """
    s = msg.strip()
    s = UUID_RE.sub("<UUID>", s)
    s = IP_RE.sub("<IP>", s)
    s = HEX_RE.sub("<HEX>", s)
    s = LONG_NUM_RE.sub("<NUM>", s)
    s = EMAIL_RE.sub("<EMAIL>", s)
    s = PATH_RE.sub("<PATH>", s)
    s = re.sub(r"\s+", " ", s)
    return s

def _parse_ts_epoch(ts: str) -> Optional[float]:
    """
    Parse ISO timestamp to epoch seconds. Supports 'Z' suffix.
    Returns None if parsing fails.
    """
    try:
        if ts.endswith("Z"):
            dt = datetime.fromisoformat(ts.replace("Z", "+00:00"))
        else:
            dt = datetime.fromisoformat(ts)
            if dt.tzinfo is None:
                dt = dt.replace(tzinfo=timezone.utc)
        return dt.timestamp()
    except Exception:
        return None

def parse_lines(lines: List[str]) -> List[LogEvent]:
    """
    Parse raw log lines into LogEvents.
    - Extracts timestamp/level/service when the line matches the expected format.
    - Normalizes only the message portion (not timestamp/level/service).
    """
    events: List[LogEvent] = []

    for line in lines:
        raw = line.rstrip("\n")
        if not raw.strip():
            continue

        m = LOG_LINE_RE.match(raw)

        if m:
            ts = m.group("ts")
            level = m.group("level")
            service = m.group("service")
            msg = m.group("msg")
            ts_epoch = _parse_ts_epoch(ts)

            events.append(
                LogEvent(
                    raw=raw,
                    normalized=normalize_message(msg),
                    timestamp=ts,
                    level=level,
                    service=service,
                    ts_epoch=ts_epoch,
                )
            )
        else:
            # Fallback: treat the whole line as message if it doesn't match the pattern
            events.append(
                LogEvent(
                    raw=raw,
                    normalized=normalize_message(raw),
                    timestamp=None,
                    level=None,
                    service=None,
                    ts_epoch=None,
                )
            )

    return events

