from __future__ import annotations

import pandas as pd


def train_ml(features: pd.DataFrame) -> tuple[object | None, pd.DataFrame]:
    try:
        from lightgbm import LGBMClassifier
    except Exception:  # noqa: BLE001
        return None, features

    cols = [c for c in ["rating", "carried_weight", "jockey_winrate_recent", "trainer_winrate_recent", "horse_recent_form"] if c in features.columns]
    if not cols or "target_win" not in features.columns:
        return None, features

    df = features.sort_values(by=["date"] if "date" in features.columns else cols)
    cut = int(len(df) * 0.8)
    train, valid = df.iloc[:cut], df.iloc[cut:]

    model = LGBMClassifier(n_estimators=200, learning_rate=0.05)
    model.fit(train[cols], train["target_win"])
    valid = valid.copy()
    valid["win_prob_ml"] = model.predict_proba(valid[cols])[:, 1]
    return model, valid
