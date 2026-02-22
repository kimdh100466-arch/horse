from __future__ import annotations

import re
from pathlib import Path

import pandas as pd
import requests
import yaml
from bs4 import BeautifulSoup


REQUIRED_GROUPS = {
    "schedule": ["경주계획", "경주일정", "경주계획표"],
    "entry": ["출전표", "출전마", "entry"],
    "result": ["경주결과", "상세성적", "경주기록", "raceresult"],
}
BOOST_KWS = ["레이팅", "기수", "조교사", "최근", "통산", "트랙", "날씨", "거리", "등급"]


def build_selected_apis(catalog_path: str = "data/catalog/catalog.csv") -> list[dict]:
    df = pd.read_csv(catalog_path)
    df["text"] = (df["dataset_name"].fillna("") + " " + df["summary"].fillna("")).str.lower()

    chosen_idx: set[int] = set()
    for _, kws in REQUIRED_GROUPS.items():
        pool = df[df["text"].apply(lambda t: any(k.lower() in t for k in kws))]
        if not pool.empty:
            chosen_idx.add(int(pool.index[0]))

    scored: list[tuple[int, int]] = []
    for idx, row in df.iterrows():
        text = row["text"]
        req_hit = any(any(k.lower() in text for k in kws) for kws in REQUIRED_GROUPS.values())
        score = (10 if req_hit else 0) + sum(1 for k in BOOST_KWS if k.lower() in text)
        if score > 0:
            scored.append((int(idx), score))

    for idx, _ in sorted(scored, key=lambda x: x[1], reverse=True)[:12]:
        chosen_idx.add(idx)

    selected: list[dict] = []
    for idx in sorted(chosen_idx):
        row = df.iloc[idx]
        meta = _parse_detail(str(row.get("detail_url", "")))
        selected.append(
            {
                "name": row["dataset_name"],
                "detail_url": row.get("detail_url", ""),
                "base_url": meta.get("base_url", ""),
                "required_params": meta.get("required_params", ["serviceKey", "pageNo", "numOfRows"]),
                "date_param_candidates": ["srchYmd", "raceYmd", "rcDate", "stDate"],
                "meet_param": "meet",
                "default_query": {"numOfRows": 999, "pageNo": 1},
                "key_fields": [],
                "response_type_hint": meta.get("response_type_hint", "json_or_xml"),
                "notes": "자동 생성 초안. base_url/파라미터를 상세페이지 기준으로 꼭 점검하세요.",
            }
        )

    return selected


def _parse_detail(url: str) -> dict:
    if not url.startswith("http"):
        return {}
    try:
        html = requests.get(url, timeout=20).text
    except Exception:  # noqa: BLE001
        return {}

    soup = BeautifulSoup(html, "html.parser")
    text = soup.get_text(" ", strip=True)

    candidates = re.findall(r"https?://[^\s\"']+", text)
    api_url = ""
    for c in candidates:
        if "api" in c.lower() or "openapi" in c.lower():
            api_url = c
            break
    if not api_url and candidates:
        api_url = candidates[0]

    required_params = re.findall(r"([A-Za-z_][A-Za-z0-9_]*)\s*\(필수\)", text)
    return {
        "base_url": api_url,
        "required_params": required_params,
        "response_type_hint": "json_or_xml",
    }


def main() -> None:
    selected = build_selected_apis()
    path = Path("selected_apis.yaml")
    path.write_text(yaml.safe_dump({"apis": selected}, allow_unicode=True, sort_keys=False), encoding="utf-8")
    print(f"Wrote {path} ({len(selected)} APIs)")


if __name__ == "__main__":
    main()
