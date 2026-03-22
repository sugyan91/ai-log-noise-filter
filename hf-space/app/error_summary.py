from collections import Counter
from typing import List, Dict, Optional
from app.parsing import LogEvent

def filter_by_window(events: List[LogEvent], window_minutes: int) -> List[LogEvent]:
    # If timestamps are missing, just return everything (don’t hide data)
    ts_vals = [e.ts_epoch for e in events if e.ts_epoch is not None]
    if not ts_vals:
        return events

    latest = max(ts_vals)
    cutoff = latest - (window_minutes * 60)
    return [e for e in events if e.ts_epoch is None or e.ts_epoch >= cutoff]

def summarize_errors(events: List[LogEvent], include_warn: bool = True) -> List[Dict]:
    levels = {"ERROR"} | ({"WARN"} if include_warn else set())
    counter = Counter()

    for e in events:
        if e.level in levels:
            counter[e.normalized] += 1

    return [{"message": msg, "count": cnt} for msg, cnt in counter.most_common()]

