from __future__ import annotations

import hashlib
import json
import os
import time
from pathlib import Path
from typing import Any

import requests

from src.utils.parse import parse_mixed_payload


class KRAClient:
    def __init__(self, cache_dir: str = "data/raw/cache", timeout: int = 20, max_retries: int = 4):
        self.service_key = os.getenv("KRA_SERVICE_KEY")
        if not self.service_key:
            raise RuntimeError("KRA_SERVICE_KEY 환경변수가 필요합니다.")
        self.timeout = timeout
        self.max_retries = max_retries
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.session = requests.Session()

    def get(self, url: str, params: dict[str, Any], force_json: bool = True, rate_sleep: float = 0.2) -> Any:
        merged = dict(params)
        merged["serviceKey"] = self.service_key

        cache_key = self._cache_key(url, merged, force_json)
        cache_path = self.cache_dir / f"{cache_key}.json"
        if cache_path.exists():
            return json.loads(cache_path.read_text(encoding="utf-8"))

        # 1) json 강제 시도 2) 실패 시 원본 포맷 재시도
        attempt_modes = [True, False] if force_json else [False]
        last_err: Exception | None = None
        for use_json_hint in attempt_modes:
            req_params = dict(merged)
            if use_json_hint:
                req_params.setdefault("_type", "json")
            for attempt in range(self.max_retries):
                try:
                    resp = self.session.get(url, params=req_params, timeout=self.timeout)
                    resp.raise_for_status()
                    parsed = parse_mixed_payload(resp.text)
                    cache_path.write_text(json.dumps(parsed, ensure_ascii=False, indent=2), encoding="utf-8")
                    time.sleep(rate_sleep)
                    return parsed
                except Exception as e:  # noqa: BLE001
                    last_err = e
                    time.sleep((2**attempt) * 0.7)

        raise RuntimeError(f"API 호출 실패: {url}") from last_err

    @staticmethod
    def _cache_key(url: str, params: dict[str, Any], force_json: bool) -> str:
        raw = f"{url}|{json.dumps(params, sort_keys=True, ensure_ascii=False)}|force_json={force_json}"
        return hashlib.sha256(raw.encode("utf-8")).hexdigest()
