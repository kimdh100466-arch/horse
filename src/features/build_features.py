from __future__ import annotations

from pathlib import Path

import pandas as pd


LEAKAGE_COLUMNS = ["payout", "odds_final", "rank_confirmed", "dividend"]


def build_features(processed_root: str = "data/processed") -> pd.DataFrame:
    root = Path(processed_root)
    entries_path = root / "entries.parquet"
    results_path = root / "results.parquet"

    entries = pd.read_parquet(entries_path) if entries_path.exists() else pd.DataFrame()
    results = pd.read_parquet(results_path) if results_path.exists() else pd.DataFrame()

    for c in LEAKAGE_COLUMNS:
        if c in entries.columns:
            entries = entries.drop(columns=[c])

    df = entries.copy()
    for col in ["rating", "carried_weight", "jockey_winrate_recent", "trainer_winrate_recent", "horse_recent_form"]:
        if col not in df.columns:
            df[col] = 0.0

    if "finish_position" in results.columns and "horse_id" in results.columns:
        win = results.assign(target_win=(results["finish_position"] == 1).astype(int))[["horse_id", "target_win"]]
        df = df.merge(win, on="horse_id", how="left")
    else:
        df["target_win"] = 0

    df["target_win"] = df["target_win"].fillna(0).astype(int)
    (root / "features.parquet").parent.mkdir(parents=True, exist_ok=True)
    df.to_parquet(root / "features.parquet", index=False)
    return df
