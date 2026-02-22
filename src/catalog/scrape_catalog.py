from __future__ import annotations

import re
from dataclasses import dataclass, asdict
from pathlib import Path

import pandas as pd
import requests
from bs4 import BeautifulSoup

BASE = "https://www.data.go.kr/tcs/dss/selectDataSetList.do"


@dataclass
class CatalogRow:
    dataset_name: str
    data_pk: str
    detail_url: str
    provider: str
    updated_at: str
    provide_type: str
    summary: str
    category: str


def classify_text(text: str) -> str:
    rules = {
        "schedule": ["경주계획", "경주일정", "계획표"],
        "entry": ["출전표", "출전마", "entry"],
        "result": ["경주결과", "상세성적", "경주기록", "raceResult", "성적"],
        "horse": ["경주마", "말 성적", "통산"],
        "jockey": ["기수"],
        "trainer": ["조교사"],
        "rating": ["레이팅"],
    }
    t = text.lower()
    for name, kws in rules.items():
        if any(k.lower() in t for k in kws):
            return name
    return "other"


def scrape_catalog(max_pages: int = 30) -> pd.DataFrame:
    rows: list[CatalogRow] = []
    for page in range(1, max_pages + 1):
        params = {"dType": "API", "keyword": "한국마사회", "pageIndex": page}
        html = requests.get(BASE, params=params, timeout=20).text
        soup = BeautifulSoup(html, "html.parser")
        cards = soup.select("ul.result-list li") or soup.select(".result-list li")
        if not cards:
            break

        for c in cards:
            name_tag = c.select_one("a")
            if not name_tag:
                continue
            name = name_tag.get_text(strip=True)
            href = name_tag.get("href", "")
            m = re.search(r"(dataPk|publicDataPk)=([0-9]+)", href)
            data_pk = m.group(2) if m else ""
            detail_url = href if href.startswith("http") else f"https://www.data.go.kr{href}"
            meta = " ".join(x.get_text(" ", strip=True) for x in c.select("span, p, dd"))
            rows.append(
                CatalogRow(
                    dataset_name=name,
                    data_pk=data_pk,
                    detail_url=detail_url,
                    provider="한국마사회" if "한국마사회" in meta else "",
                    updated_at=_extract_date(meta),
                    provide_type="오픈API",
                    summary=meta,
                    category=classify_text(f"{name} {meta}"),
                )
            )
    return pd.DataFrame([asdict(r) for r in rows]).drop_duplicates(subset=["data_pk", "dataset_name"])


def _extract_date(text: str) -> str:
    m = re.search(r"(20\d{2}[.-]\d{2}[.-]\d{2})", text)
    return m.group(1).replace(".", "-") if m else ""


def main() -> None:
    df = scrape_catalog()
    out_dir = Path("data/catalog")
    out_dir.mkdir(parents=True, exist_ok=True)
    df.to_csv(out_dir / "catalog.csv", index=False, encoding="utf-8-sig")
    df.to_json(out_dir / "catalog.json", force_ascii=False, orient="records", indent=2)
    print(f"Saved {len(df)} rows")


if __name__ == "__main__":
    main()
