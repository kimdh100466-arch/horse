from __future__ import annotations

import argparse
from pathlib import Path

from src.catalog.fetch_dataset_meta import main as generate_selected
from src.catalog.scrape_catalog import main as generate_catalog
from src.clean.normalize import normalize_raw_to_tables
from src.fetch.fetch_selected import fetch_selected


def run(start: str, end: str, meets: str, catalog_only: bool = False) -> None:
    if not Path("data/catalog/catalog.csv").exists():
        generate_catalog()
    if not Path("selected_apis.yaml").exists():
        generate_selected()

    if catalog_only:
        return

    fetch_selected(start=start, end=end, meets=meets)
    normalize_raw_to_tables()


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description="KRA OpenAPI pipeline")
    ap.add_argument("--start", required=True)
    ap.add_argument("--end", required=True)
    ap.add_argument("--meets", default="all")
    ap.add_argument("--catalog-only", action="store_true")
    args = ap.parse_args()
    run(args.start, args.end, args.meets, catalog_only=args.catalog_only)
