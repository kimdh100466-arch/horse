from __future__ import annotations

import argparse

import pandas as pd

from src.backtest.metrics import evaluate_probs, save_report
from src.backtest.simulate import simulate_profit
from src.features.build_features import build_features
from src.model.baseline import predict_baseline
from src.model.calibrate import calibrate_isotonic
from src.model.ml import train_ml


def run(start: str, end: str, model: str, strategy: str) -> None:
    _ = (start, end)
    features = build_features()

    if model == "ml":
        mdl, pred = train_ml(features)
        if mdl is None:
            pred = predict_baseline(features)
    else:
        pred = predict_baseline(features)

    pred = calibrate_isotonic(pred, prob_col="win_prob" if "win_prob" in pred.columns else "win_prob_ml")
    prob_col = "win_prob_cal" if "win_prob_cal" in pred.columns else ("win_prob_ml" if "win_prob_ml" in pred.columns else "win_prob")

    metrics = evaluate_probs(pred, prob_col=prob_col)
    save_report(metrics)

    sim = simulate_profit(pred, prob_col=prob_col, strategy=strategy)
    if not sim.empty:
        sim.to_csv("reports/simulation.csv", index=False, encoding="utf-8-sig")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--start", required=True)
    ap.add_argument("--end", required=True)
    ap.add_argument("--model", default="baseline", choices=["baseline", "ml"])
    ap.add_argument("--strategy", default="none", choices=["none", "top1", "threshold"])
    args = ap.parse_args()
    run(args.start, args.end, args.model, args.strategy)
