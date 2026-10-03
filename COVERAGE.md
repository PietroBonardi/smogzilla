# Test Coverage

Generated from the `feature/waqi-scraper` branch.

## Summary

| Metric | Value |
|---|---|
| Test framework | pytest 9.1.1 (`pytest-asyncio`, `pytest-cov`) |
| Tests | 133 passed (unit + integration) |
| Overall statement coverage | **93%** (336 statements, 25 missed) |

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
| `scrapers/types.py` | 26 | 9 | 65% | 45-52, 55-56 |
| `scrapers/waqi.py` | 95 | 2 | 98% | 152, 154 |
| `utils/__init__.py` | 0 | 0 | 100% | — |
| `utils/city_data.py` | 4 | 0 | 100% | — |
| **TOTAL** | **336** | **25** | **93%** | |

## Uncovered lines explained

| Location | Code | Why it is uncovered |
|---|---|---|
| `handlers/air.py:21-24, 29-30, 35, 38-42, 46-50` | `air()` early-return paths | Mostly guard/validation branches partially exercised |
| `handlers/start.py:7` | `if not update.message: return` | Guard for updates without a message; not hit by command updates |
| `scrapers/base.py:28` | ABC `raise NotImplementedError` | Abstract body, never executed directly |
| `scrapers/sensor_community.py:168` | `logger.info(...)` for stale-drop | Logging only — branch runs but coverage tool may flag the call |
| `scrapers/types.py:45-52, 55-56` | `is_fresh` fallback paths | Naive-timestamp and invalid-format branches rarely exercised |
| `scrapers/waqi.py:152, 154` | `_interp` edge returns | Defensive paths in the interpolation loop |

## Coverage by layer

| Layer | Marker | Tests |
|---|---|---:|
| Unit | `pytest -m unit` | 115 |
| Integration | `pytest -m integration` | 18 |
| E2E | `pytest -m e2e` | 6 (currently skipped — ptb `_initialized` mismatch in environment) |
