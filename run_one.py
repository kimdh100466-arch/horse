from __future__ import annotations

import argparse
import json
from pathlib import Path

from src.backtest.metrics import evaluate_probs, save_report
from src.backtest.simulate import simulate_profit
from src.catalog.fetch_dataset_meta import main as generate_selected
from src.catalog.scrape_catalog import main as generate_catalog
from src.clean.normalize import normalize_raw_to_tables
from src.features.build_features import build_features
from src.fetch.fetch_selected import fetch_selected
from src.model.baseline import DEFAULT_WEIGHTS, predict_baseline


def parse_weights(items: list[str]) -> dict[str, float]:
    weights = dict(DEFAULT_WEIGHTS)
    for item in items:
        if "=" not in item:
            raise ValueError(f"가중치 형식 오류: {item} (예: rating=0.4)")
        k, v = item.split("=", 1)
        weights[k.strip()] = float(v.strip())
    return weights


def run_once(start: str, end: str, meets: str, strategy: str, weights: dict[str, float], skip_fetch: bool) -> dict:
    if not Path("data/catalog/catalog.csv").exists():
        generate_catalog()
    if not Path("selected_apis.yaml").exists():
        generate_selected()

    if not skip_fetch:
        fetch_selected(start=start, end=end, meets=meets)
        normalize_raw_to_tables()

    features = build_features()
    pred = predict_baseline(features, weights_override=weights)

    metrics = evaluate_probs(pred, prob_col="win_prob")
    metrics["weights"] = weights
    save_report(metrics, out_dir="reports")

    sim = simulate_profit(pred, prob_col="win_prob", strategy=strategy)
    if not sim.empty:
        sim.to_csv("reports/simulation.csv", index=False, encoding="utf-8-sig")

    return metrics


def main() -> None:
    ap = argparse.ArgumentParser(description="단일 실행: 수집+학습(베이스라인)+시뮬레이션")
    ap.add_argument("--start", required=True)
    ap.add_argument("--end", required=True)
    ap.add_argument("--meets", default="all")
    ap.add_argument("--strategy", default="none", choices=["none", "top1", "threshold"])
    ap.add_argument("--skip-fetch", action="store_true", help="기존 data/raw, data/processed를 재사용")
    ap.add_argument(
        "--weight",
        action="append",
        default=[],
        help="가중치 오버라이드. 여러 번 지정 가능 (예: --weight rating=0.4 --weight carried_weight=-0.1)",
    )
    args = ap.parse_args()

    weights = parse_weights(args.weight)
    metrics = run_once(
        start=args.start,
        end=args.end,
        meets=args.meets,
        strategy=args.strategy,
        weights=weights,
        skip_fetch=args.skip_fetch,
    )
    Path("reports").mkdir(parents=True, exist_ok=True)
    Path("reports/last_run_weights.json").write_text(json.dumps(weights, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(metrics, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
