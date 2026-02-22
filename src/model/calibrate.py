from __future__ import annotations

import pandas as pd


def calibrate_isotonic(df: pd.DataFrame, prob_col: str = "win_prob") -> pd.DataFrame:
    try:
        from sklearn.isotonic import IsotonicRegression
    except Exception:  # noqa: BLE001
        return df

    if prob_col not in df.columns or "target_win" not in df.columns:
        return df

    ir = IsotonicRegression(out_of_bounds="clip")
    x = df[prob_col].fillna(0).to_numpy()
    y = df["target_win"].fillna(0).to_numpy()
    df = df.copy()
    df[f"{prob_col}_cal"] = ir.fit_transform(x, y)
    return df
