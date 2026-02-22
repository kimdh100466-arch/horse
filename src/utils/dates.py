from __future__ import annotations

from datetime import datetime, timedelta
from typing import Iterator


def ymd_to_compact(date_str: str) -> str:
    if len(date_str) == 8 and date_str.isdigit():
        return date_str
    return datetime.strptime(date_str, "%Y-%m-%d").strftime("%Y%m%d")


def compact_to_ymd(date_str: str) -> str:
    return datetime.strptime(date_str, "%Y%m%d").strftime("%Y-%m-%d")


def date_range(start: str, end: str) -> Iterator[str]:
    s = datetime.strptime(ymd_to_compact(start), "%Y%m%d")
    e = datetime.strptime(ymd_to_compact(end), "%Y%m%d")
    cur = s
    while cur <= e:
        yield cur.strftime("%Y%m%d")
        cur += timedelta(days=1)
