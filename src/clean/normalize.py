from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pandas as pd


def normalize_raw_to_tables(raw_root: str = "data/raw", out_root: str = "data/processed") -> None:
    raw_path = Path(raw_root)
    out_path = Path(out_root)
    out_path.mkdir(parents=True, exist_ok=True)

    entries, results, races = [], [], []
    for fp in raw_path.rglob("*.json"):
        obj = json.loads(fp.read_text(encoding="utf-8"))
        flat = _flatten(obj)
        row = {"source": fp.parent.name, "date": fp.stem, **flat}
        txt = (fp.parent.name + str(flat)).lower()
        if "result" in txt or "성적" in txt:
            results.append(row)
        elif "entry" in txt or "출전" in txt:
            entries.append(row)
        else:
            races.append(row)

    for name, rows in [("races", races), ("entries", entries), ("results", results)]:
        df = pd.DataFrame(rows)
        if not df.empty:
            df.to_parquet(out_path / f"{name}.parquet", index=False)
            df.to_csv(out_path / f"{name}.csv", index=False, encoding="utf-8-sig")


def _flatten(obj: Any, prefix: str = "") -> dict[str, Any]:
    out: dict[str, Any] = {}
    if isinstance(obj, dict):
        for k, v in obj.items():
            out.update(_flatten(v, f"{prefix}{k}_"))
    elif isinstance(obj, list):
        if obj:
            out.update(_flatten(obj[0], prefix))
    else:
        out[prefix[:-1] if prefix else "value"] = obj
    return out
