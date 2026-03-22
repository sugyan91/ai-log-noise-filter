# app/parsing.py
import json
import re
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Optional, List, Tuple

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

# Linux syslog / messages (RFC 3164-ish), optional <PRI> prefix.
# Month: abbreviated or full English name (Feb / February).
_SYSLOG_TS = (
    r"(?P<ts>(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\s+"
    r"\d{1,2}\s+\d{1,2}:\d{2}:\d{2})"
)
# Mar 22 14:05:01 hostname sshd[12345]: error: PAM ...
# <34>Mar 22 14:05:01 hostname tag: message
SYSLOG_RE = re.compile(
    r"^(?:<(?P<pri>\d{1,3})>\s*)?"
    + _SYSLOG_TS
    + r"\s+(?P<host>\S+)\s+"
    r"(?P<tag>[\w.\-]+(?:\[\d+\])?):\s*(?P<msg>.*)$"
)

# Same as syslog but **no** "tag:" — message is everything after hostname (common in copies/pastes).
RELAXED_SYSLOG_RE = re.compile(
    r"^(?:<(?P<pri>\d{1,3})>\s*)?"
    + _SYSLOG_TS
    + r"\s+(?P<host>\S+)\s+"
    r"(?P<rest>.+)$"
)

# ISO-ish timestamp + host + "tag: msg" (common in journal exports / some aggregators)
# TZ: Z, +00:00, +0000
ISO_HOST_TAG_RE = re.compile(
    r"^(?P<ts>\d{4}-\d{2}-\d{2}[T ]\d{2}:\d{2}:\d{2}(?:\.\d+)?(?:Z|[+-]\d{2}:?\d{2}|[+-]\d{4})?)\s+"
    r"(?P<host>\S+)\s+"
    r"(?P<tag>[\w.\-]+(?:\[\d+\])?):\s*(?P<msg>.*)$"
)

# ISO timestamp at start, then free text (no "host tag:" required)
ISO_THEN_REST_RE = re.compile(
    r"^(?P<ts>\d{4}-\d{2}-\d{2}[T ]\d{2}:\d{2}:\d{2}(?:\.\d+)?(?:Z|[+-]\d{2}:?\d{2}|[+-]\d{4})?)\s+"
    r"(?P<rest>.+)$"
)

# dmesg / kernel ring buffer
DMESG_RE = re.compile(r"^\[\s*\d+\.\d+\]\s*(?P<msg>.+)$")

# Kubernetes / glog style: E0301 12:34:56.789012    1234 file.go:88] message
KLOG_RE = re.compile(
    r"^(?P<lvl>[IWEFP])\d{4}\s+\d{1,2}:\d{2}:\d{2}\.\d+\s+.*$"
)

_ERROR_HINT = re.compile(
    r"(?:\berror\b|\berrors\b|\bfailed\b|\bfailure\b|\bfail\b|\bfatal\b|\bcritical\b|\bcrit\b|"
    r"\bexception\b|\bpanic\b|\bdenied\b|\brefused\b|errno\s*=|i/o error|input/output error|"
    r"segmentation fault|out of memory|\boom\b|\btraceback\b|\bunhandled\b|\binvalid\b|"
    r"\bunable to\b|\bcannot\b|\bcan't\b|\bcould not\b|\bcouldn't\b|\bpermission denied\b|"
    r"\bunauthorized\b|\bforbidden\b|\bnot permitted\b|\btimed out\b|\btimeout\b|\bunreachable\b|"
    r"\bno such file\b|\bnot found\b|\bmount failed\b|\bbroken pipe\b|\bconnection reset\b|"
    r"\bssl\b.*\berror\b|\btls\b.*\bfail)",
    re.I,
)
_WARN_HINT = re.compile(
    r"(?:\bwarn(?:ing)?s?\b|\bdeprecated\b|\bcaution\b)",
    re.I,
)

# level=error, severity=warn, "level":"ERROR"
_LEVEL_KV_RE = re.compile(
    r'(?:^|[\s,{])(?P<k>level|severity|loglevel|log\.level|priority)\s*[:=]\s*'
    r'(?:"(?P<qv>[^"]+)"|\'(?P<qs>[^\']+)\'|(?P<qw>\w+))',
    re.I,
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

def _normalize_iso_timestamp(ts: str) -> str:
    """Space between date/time -> T; trailing +0000 / -0700 -> +00:00 / -07:00 for fromisoformat."""
    t = ts.strip()
    if len(t) >= 19 and t[10] == " " and t[:10].count("-") == 2:
        t = t[:10] + "T" + t[11:]
    m = re.search(r"([+-])(\d{2})(\d{2})$", t)
    if m and ":" not in t[m.start() :]:
        t = t[: m.start()] + f"{m.group(1)}{m.group(2)}:{m.group(3)}"
    return t


def _parse_ts_epoch(ts: str) -> Optional[float]:
    """
    Parse ISO timestamp to epoch seconds. Supports 'Z' suffix.
    Returns None if parsing fails.
    """
    try:
        t = _normalize_iso_timestamp(ts)
        if t.endswith("Z"):
            dt = datetime.fromisoformat(t.replace("Z", "+00:00"))
        else:
            dt = datetime.fromisoformat(t)
            if dt.tzinfo is None:
                dt = dt.replace(tzinfo=timezone.utc)
        return dt.timestamp()
    except Exception:
        return None


def _parse_syslog_ts(ts: str) -> Optional[float]:
    """Parse 'Mar 22 14:05:01' / 'February 7 13:12:04' (year assumed: this year, else last year)."""
    ts = " ".join(ts.split())
    now = datetime.now(timezone.utc)
    for year in (now.year, now.year - 1):
        for fmt in ("%b %d %H:%M:%S %Y", "%B %d %H:%M:%S %Y"):
            try:
                dt = datetime.strptime(f"{ts} {year}", fmt)
                return dt.replace(tzinfo=timezone.utc).timestamp()
            except ValueError:
                continue
    return None


def _level_from_syslog_pri(pri_str: Optional[str]) -> Optional[str]:
    if not pri_str:
        return None
    try:
        pri = int(pri_str)
    except ValueError:
        return None
    sev = pri % 8
    if sev <= 3:
        return "ERROR"
    if sev == 4:
        return "WARN"
    return "INFO"


def _infer_level_from_keywords(text: str) -> Optional[str]:
    if not text:
        return None
    if _ERROR_HINT.search(text):
        return "ERROR"
    if _WARN_HINT.search(text):
        return "WARN"
    return None


def _infer_level_from_kv(text: str) -> Optional[str]:
    if not text:
        return None
    for m in _LEVEL_KV_RE.finditer(text):
        v = (m.group("qv") or m.group("qs") or m.group("qw") or "").strip().lower()
        if v in ("error", "err", "critical", "crit", "fatal", "emergency", "emerg", "alert", "severe"):
            return "ERROR"
        if v in ("warn", "warning", "deprecated"):
            return "WARN"
        if v in ("info", "informational", "information", "notice", "debug", "trace", "verbose"):
            return "INFO"
    return None


def _infer_any_level(msg: str, raw: str) -> Optional[str]:
    parts = (
        _infer_level_from_kv(raw),
        _infer_level_from_keywords(msg),
        _infer_level_from_keywords(raw),
    )
    best: Optional[str] = None
    for c in parts:
        best = _stronger_level(best, c)
    return best


def _split_tag_and_message(rest: str) -> Tuple[Optional[str], str]:
    rest = rest.strip()
    m = re.match(r"^(?P<tag>[\w.\-]+(?:\[\d+\])?):\s*(?P<msg>.*)$", rest)
    if m:
        return m.group("tag"), m.group("msg")
    m2 = re.match(r"^(?P<tag>[\w.\-]+\[\d+\])\s+(?P<msg>.+)$", rest)
    if m2:
        return m2.group("tag"), m2.group("msg")
    return None, rest


def _level_from_klog_line(raw: str) -> Optional[str]:
    m = KLOG_RE.match(raw)
    if not m:
        return None
    c = m.group("lvl").upper()
    if c in ("E", "F"):
        return "ERROR"
    if c == "W":
        return "WARN"
    return "INFO"


def _map_level_string(s: Optional[str]) -> Optional[str]:
    if not s:
        return None
    v = s.strip().lower()
    if v.isdigit():
        n = int(v)
        if n <= 3:
            return "ERROR"
        if n == 4:
            return "WARN"
        return "INFO"
    if v in ("error", "err", "critical", "crit", "fatal", "emergency", "emerg", "alert", "severe"):
        return "ERROR"
    if v in ("warn", "warning", "deprecated"):
        return "WARN"
    if v in ("info", "information", "informational", "notice", "debug", "trace", "verbose"):
        return "INFO"
    return None


def _try_json_log_line(raw: str) -> Optional[LogEvent]:
    s = raw.strip()
    if not s.startswith("{"):
        return None
    try:
        obj = json.loads(s)
    except json.JSONDecodeError:
        return None
    if not isinstance(obj, dict):
        return None

    msg = None
    for k in ("message", "msg", "text", "@message", "MESSAGE", "log", "event", "raw"):
        v = obj.get(k)
        if isinstance(v, str) and v.strip():
            msg = v
            break
    if msg is None:
        nested = obj.get("log", obj.get("json", obj.get("fields")))
        if isinstance(nested, dict):
            for k in ("message", "msg", "original"):
                v = nested.get(k)
                if isinstance(v, str) and v.strip():
                    msg = v
                    break

    lv_raw = None
    for k in ("level", "severity", "log.level", "priority", "PRIORITY", "syslog_priority"):
        if k in obj:
            v = obj[k]
            if isinstance(v, (str, int)):
                lv_raw = str(v)
            break
    if lv_raw is None:
        nested = obj.get("log", obj.get("json"))
        if isinstance(nested, dict):
            for k in ("level", "severity"):
                if k in nested:
                    v = nested[k]
                    if isinstance(v, (str, int)):
                        lv_raw = str(v)
                    break

    if msg is None and lv_raw is None:
        return None
    if msg is None:
        msg = s[:500]

    level = _map_level_string(lv_raw)
    level = _stronger_level(level, _infer_any_level(msg, s))
    ts_raw = None
    ts_epoch = None
    for k in ("timestamp", "time", "@timestamp", "ts", "datetime"):
        v = obj.get(k)
        if isinstance(v, str) and v.strip():
            ts_raw = v
            ts_epoch = _parse_ts_epoch(v)
            break

    svc = None
    for k in ("service", "app", "program", "ident", "SYSLOG_IDENTIFIER"):
        v = obj.get(k)
        if isinstance(v, str) and v.strip():
            svc = v.strip()
            break

    return LogEvent(
        raw=raw,
        normalized=normalize_message(msg),
        timestamp=ts_raw,
        level=level,
        service=svc,
        ts_epoch=ts_epoch,
    )


def _stronger_level(a: Optional[str], b: Optional[str]) -> Optional[str]:
    rank = {"INFO": 1, "WARN": 2, "ERROR": 3}
    ra, rb = rank.get(a or "", 0), rank.get(b or "", 0)
    if rb > ra:
        return b
    return a if ra > 0 else b


def _service_from_syslog_tag(tag: str) -> str:
    return re.sub(r"\[\d+\]$", "", tag).strip() or "syslog"

def parse_lines(lines: List[str]) -> List[LogEvent]:
    """
    Parse raw log lines into LogEvents.
    - Structured app logs: ISO + INFO|WARN|ERROR + service + message.
    - Linux syslog / messages: MMM DD hh:mm:ss host … (optional <PRI>).
    - ISO-prefixed lines, JSON log lines, dmesg, klog-style prefixes.
    - Fallback: whole-line normalization + level from fields/keywords in text.
    """
    events: List[LogEvent] = []

    for line in lines:
        raw = line.replace("\r\n", "\n").rstrip("\n").strip()
        if raw.startswith("\ufeff"):
            raw = raw[1:].strip()
        if not raw:
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
            continue

        je = _try_json_log_line(raw)
        if je is not None:
            events.append(je)
            continue

        m = SYSLOG_RE.match(raw)
        if m:
            ts = m.group("ts")
            msg = m.group("msg")
            tag = m.group("tag")
            pri_level = _level_from_syslog_pri(m.group("pri"))
            level = _stronger_level(pri_level, _infer_any_level(msg, raw))
            ts_epoch = _parse_syslog_ts(ts)
            events.append(
                LogEvent(
                    raw=raw,
                    normalized=normalize_message(msg),
                    timestamp=ts,
                    level=level,
                    service=_service_from_syslog_tag(tag),
                    ts_epoch=ts_epoch,
                )
            )
            continue

        m = ISO_HOST_TAG_RE.match(raw)
        if m:
            ts_raw = m.group("ts")
            msg = m.group("msg")
            tag = m.group("tag")
            level = _infer_any_level(msg, raw)
            ts_epoch = (
                _parse_ts_epoch(_normalize_iso_timestamp(ts_raw))
                if re.match(r"^\d{4}-\d{2}-\d{2}", ts_raw)
                else None
            )
            events.append(
                LogEvent(
                    raw=raw,
                    normalized=normalize_message(msg),
                    timestamp=ts_raw,
                    level=level,
                    service=_service_from_syslog_tag(tag),
                    ts_epoch=ts_epoch,
                )
            )
            continue

        m = ISO_THEN_REST_RE.match(raw)
        if m:
            ts_raw = m.group("ts")
            rest = m.group("rest")
            ts_epoch = (
                _parse_ts_epoch(_normalize_iso_timestamp(ts_raw))
                if re.match(r"^\d{4}-\d{2}-\d{2}", ts_raw)
                else None
            )
            level = _infer_any_level(rest, raw)
            events.append(
                LogEvent(
                    raw=raw,
                    normalized=normalize_message(rest),
                    timestamp=ts_raw,
                    level=level,
                    service=None,
                    ts_epoch=ts_epoch,
                )
            )
            continue

        m = DMESG_RE.match(raw)
        if m:
            msg = m.group("msg")
            level = _infer_any_level(msg, raw)
            events.append(
                LogEvent(
                    raw=raw,
                    normalized=normalize_message(msg),
                    timestamp=None,
                    level=level,
                    service="kernel",
                    ts_epoch=None,
                )
            )
            continue

        kl = _level_from_klog_line(raw)
        if kl is not None:
            level = _stronger_level(kl, _infer_any_level(raw, raw))
            events.append(
                LogEvent(
                    raw=raw,
                    normalized=normalize_message(raw),
                    timestamp=None,
                    level=level,
                    service="klog",
                    ts_epoch=None,
                )
            )
            continue

        m = RELAXED_SYSLOG_RE.match(raw)
        if m:
            ts_raw = m.group("ts")
            pri_level = _level_from_syslog_pri(m.group("pri"))
            ts_epoch = _parse_syslog_ts(ts_raw)
            tag, msg = _split_tag_and_message(m.group("rest"))
            svc = _service_from_syslog_tag(tag) if tag else None
            level = _stronger_level(pri_level, _infer_any_level(msg, raw))
            events.append(
                LogEvent(
                    raw=raw,
                    normalized=normalize_message(msg),
                    timestamp=ts_raw,
                    level=level,
                    service=svc,
                    ts_epoch=ts_epoch,
                )
            )
            continue

        level = _infer_any_level(raw, raw)
        events.append(
            LogEvent(
                raw=raw,
                normalized=normalize_message(raw),
                timestamp=None,
                level=level,
                service=None,
                ts_epoch=None,
            )
        )

    return events

