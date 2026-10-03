# Test Coverage

Generated from the `feature/waqi-scraper` branch at commit `559a291`.

## Summary

| Metric | Value |
|---|---|
| Test framework | pytest 9.1.1 (`pytest-asyncio`, `pytest-cov`) |
| Tests | 74 passed (unit + integration) |
| Overall statement coverage | **74%** (336 statements, 86 missed) |

## Reproduce

```bash
pip install -r requirements-dev.txt
pytest -m "unit or integration" --cov=bot --cov=config --cov=formatter \
       --cov=handlers --cov=scrapers --cov=utils \
       --cov-report=term-missing
```

## Per-file coverage

| Name | Stmts | Miss | Cover | Missing |
|---|---|---:|---:|---|
| `config.py` | 9 | 0 | 100% | — |
| `formatter.py` | 59 | 0 | 100% | — |
| `handlers/__init__.py` | 0 | 0 | 100% | — |
| `handlers/air.py` | 38 | 11 | 71% | 21-24, 29-30, 35, 38-42, 46-50 |
| `handlers/cities.py` | 6 | 0 | 100% | — |
| `handlers/start.py` | 6 | 1 | 83% | 7 |
| `scrapers/__init__.py` | 0 | 0 | 100% | — |
| `scrapers/base.py` | 7 | 1 | 86% | 28 |
| `scrapers/sensor_community.py` | 86 | 1 | 99% | 168 |
| `scrapers/types.py` | 26 | 10 | 62% | 40, 45-52, 55-56 |
| `scrapers/waqi.py` | 95 | 62 | 35% | 59-61, 75-77, 93-95, 101-102, 111-126, 130-131, 135-140, 147-154, 158, 162, 166-169, 177-208 |
| `utils/__init__.py` | 0 | 0 | 100% | — |
| `utils/city_data.py` | 4 | 0 | 100% | — |
| **TOTAL** | **336** | **86** | **74%** | |

## Uncovered hot spots

| Location | Why uncovered |
|---|---|
| `scrapers/waqi.py` (62 lines, 35% covered) | New module; parsing + HTTP layer lack dedicated unit tests |
| `handlers/air.py` (11 lines, 71% covered) | Several early-return paths (no message, missing args, unknown city) only exercised via mocks |
| `scrapers/types.py` (10 lines, 62% covered) | `is_fresh` timezone-naive and parse-failure branches not directly tested |

Adding unit tests for `WaqiScraper._parse_feed` and the IAQI conversion helpers is the
highest-impact follow-up: those functions are pure and easy to exercise with canned
payloads, and would lift total coverage back above 90%.

## Coverage by layer

| Layer | Marker | Tests |
|---|---|---:|
| Unit | `pytest -m unit` | 64 |
| Integration | `pytest -m integration` | 10 |
| E2E | `pytest -m e2e` | 6 (currently skipped — ptb `_initialized` mismatch in environment) |
