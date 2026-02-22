from __future__ import annotations

import math
from pathlib import Path

import pandas as pd
import yaml


DEFAULT_WEIGHTS = {
    "rating": 0.35,
    "carried_weight": -0.2,
    "jockey_winrate_recent": 0.2,
    "trainer_winrate_recent": 0.15,
    "horse_recent_form": -0.1,
}


def predict_baseline(
    features: pd.DataFrame,
    config_path: str = "config.yaml",
    weights_override: dict[str, float] | None = None,
) -> pd.DataFrame:
    weights = weights_override or _load_weights(config_path)
    df = features.copy()
    for k in weights:
        if k not in df.columns:
            df[k] = 0.0

    df["score"] = sum(df[k].fillna(0) * w for k, w in weights.items())
    race_col = "race_id" if "race_id" in df.columns else "date"
    df["win_prob"] = df.groupby(race_col)["score"].transform(_softmax)
    return df


def _softmax(series: pd.Series) -> pd.Series:
    vals = series.astype(float).tolist()
    m = max(vals) if vals else 0.0
    exps = [math.exp(v - m) for v in vals]
    s = sum(exps) or 1.0
    return pd.Series([e / s for e in exps], index=series.index)


def _load_weights(config_path: str) -> dict[str, float]:
    path = Path(config_path)
    if path.exists():
        obj = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
        return obj.get("baseline_weights", DEFAULT_WEIGHTS)
    return DEFAULT_WEIGHTS
