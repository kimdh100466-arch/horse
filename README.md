# KRA OpenAPI 경마 1착 확률 연구 파이프라인

연구/시뮬레이션 목적 프로젝트입니다. 베팅 유도/픽 추천 용도로 사용하지 않습니다.

## 핵심 원칙
- `KRA_SERVICE_KEY`는 환경변수로만 사용 (`.env`/쉘 export), 코드 하드코딩 금지.
- 누수 방지: 경주 종료 후 확정되는 값(확정 배당/사후 확정치)은 피처에서 제외.
- API 응답 JSON/XML 혼재 대응 (`src/utils/parse.py`).
- API 실패 대비: 재시도, 지수 백오프, 파일 캐시 적용 (`src/fetch/kra_client.py`).

## 딱 하나만 실행하면 되는 명령
```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
export KRA_SERVICE_KEY="발급받은_서비스키"

python run_one.py \
  --start 20250101 \
  --end 20250131 \
  --meets all \
  --strategy none \
  --weight rating=0.40 \
  --weight carried_weight=-0.15 \
  --weight jockey_winrate_recent=0.20 \
  --weight trainer_winrate_recent=0.15 \
  --weight horse_recent_form=-0.10
```

위 **한 번의 실행**으로 아래를 순서대로 수행합니다.
1. catalog 생성(없으면)
2. selected_apis.yaml 생성(없으면)
3. 공공데이터 OpenAPI 호출 및 `data/raw` 저장
4. 정규화 `data/processed` 저장
5. baseline 확률 계산(입력한 가중치 사용)
6. 백테스트 및 리포트 저장

## 가중치 튜닝 반복 실행 예시
```bash
# 데이터 재수집 없이 가중치만 바꿔 빠르게 반복
python run_one.py --start 20250101 --end 20250131 --skip-fetch \
  --weight rating=0.45 --weight carried_weight=-0.20

python run_one.py --start 20250101 --end 20250131 --skip-fetch \
  --weight rating=0.30 --weight carried_weight=-0.05
```

## 산출물
- `reports/metrics.json`
- `reports/summary.csv`
- `reports/last_run_weights.json`
- (옵션) `reports/simulation.csv`
