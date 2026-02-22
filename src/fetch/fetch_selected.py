from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import yaml

from src.fetch.kra_client import KRAClient
from src.utils.dates import date_range


def fetch_selected(start: str, end: str, meets: str = "all", config_path: str = "selected_apis.yaml") -> None:
    config = yaml.safe_load(Path(config_path).read_text(encoding="utf-8"))
    apis = config.get("apis", [])
    client = KRAClient()

    for api in apis:
        base_url = api.get("base_url")
        if not base_url:
            continue

        api_name = _safe_name(api.get("name", "api"))
        out_dir = Path("data/raw") / api_name
        out_dir.mkdir(parents=True, exist_ok=True)

        for d in date_range(start, end):
            params = _build_params(api, d, meets)
            payload = client.get(base_url, params=params, force_json=True)
            (out_dir / f"{d}.json").write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def _build_params(api: dict[str, Any], date_compact: str, meets: str) -> dict[str, Any]:
    params: dict[str, Any] = dict(api.get("default_query", {}))
    if "pageNo" not in params:
        params["pageNo"] = 1
    if "numOfRows" not in params:
        params["numOfRows"] = 999

    date_candidates = api.get("date_param_candidates", ["srchYmd", "raceYmd", "rcDate", "stDate"])
    date_param = date_candidates[0] if date_candidates else "srchYmd"
    params[date_param] = date_compact

    meet_key = api.get("meet_param", "meet")
    if meet_key:
        params[meet_key] = meets

    # 필수 파라미터가 명시돼 있으면 빈 값이라도 키를 맞춰준다(수동 보정 용이)
    for p in api.get("required_params", []):
        if p in {"serviceKey", "ServiceKey"}:
            continue
        params.setdefault(p, "")

    return params


def _safe_name(name: str) -> str:
    return "".join(ch if ch.isalnum() else "_" for ch in name).strip("_").lower()
