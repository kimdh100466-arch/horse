from __future__ import annotations

import json
from pathlib import Path

import pandas as pd


def evaluate_probs(df: pd.DataFrame, prob_col: str = "win_prob") -> dict:
    y = df.get("target_win", pd.Series([0] * len(df))).astype(float)
    p = df.get(prob_col, pd.Series([0.0] * len(df))).clip(1e-8, 1 - 1e-8)
    logloss = float((-(y * p.map(lambda v: __import__("math").log(v)) + (1 - y) * (1 - p).map(lambda v: __import__("math").log(v)))).mean())
    brier = float(((p - y) ** 2).mean())

    race_col = "race_id" if "race_id" in df.columns else "date"
    top_pred = df.sort_values(prob_col, ascending=False).groupby(race_col).head(1)
    top1 = float(top_pred.get("target_win", pd.Series([0] * len(top_pred))).mean()) if len(top_pred) else 0.0

    calib = calibration_table(df, prob_col)
    return {"logloss": logloss, "brier": brier, "top1_accuracy": top1, "calibration": calib.to_dict(orient="records")}


def calibration_table(df: pd.DataFrame, prob_col: str, bins: int = 10) -> pd.DataFrame:
    tmp = df.copy()
    tmp["bin"] = pd.cut(tmp[prob_col], bins=bins, labels=False, include_lowest=True)
    out = tmp.groupby("bin", dropna=True).agg(pred_mean=(prob_col, "mean"), actual_mean=("target_win", "mean"), n=("target_win", "size")).reset_index()
    return out


def save_report(metrics: dict, out_dir: str = "reports") -> None:
    p = Path(out_dir)
    p.mkdir(parents=True, exist_ok=True)
    (p / "metrics.json").write_text(json.dumps(metrics, ensure_ascii=False, indent=2), encoding="utf-8")
    pd.DataFrame([metrics]).drop(columns=["calibration"], errors="ignore").to_csv(p / "summary.csv", index=False, encoding="utf-8-sig")
