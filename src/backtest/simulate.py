from __future__ import annotations

import pandas as pd


def simulate_profit(df: pd.DataFrame, prob_col: str = "win_prob", odds_col: str = "odds", strategy: str = "none", threshold: float = 0.2) -> pd.DataFrame:
    if strategy == "none" or odds_col not in df.columns:
        return pd.DataFrame()

    tmp = df.copy()
    if strategy == "top1":
        race_col = "race_id" if "race_id" in tmp.columns else "date"
        tmp = tmp.sort_values(prob_col, ascending=False).groupby(race_col).head(1)
    elif strategy == "threshold":
        tmp = tmp[tmp[prob_col] >= threshold]

    tmp["stake"] = 1.0
    tmp["pnl"] = tmp.apply(lambda r: (r[odds_col] - 1.0) if r.get("target_win", 0) == 1 else -1.0, axis=1)
    tmp["cum_pnl"] = tmp["pnl"].cumsum()
    return tmp
