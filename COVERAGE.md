# Test Coverage

Generated from the `main` branch at commit `903f134`.

## Summary

| Metric | Value |
|---|---|
| Test framework | pytest 9.1.1 (`pytest-asyncio`, `pytest-cov`) |
| Tests | 80 passed |
| Overall statement coverage | **96%** (210 statements, 8 missed) |

## Reproduce

```bash
pip install -r requirements-dev.txt
pytest --cov=bot --cov=config --cov=formatter \
       --cov=handlers --cov=scrapers --cov=utils \
       --cov-report=term-missing
```

## Per-file coverage

| Name | Stmts | Miss | Cover | Missing |
|---|---:|---:|---:|---|
| `bot.py` | 23 | 6 | 74% | 15, 33-36, 40 |
| `config.py` | 8 | 0 | 100% | — |
| `formatter.py` | 59 | 0 | 100% | — |
| `handlers/__init__.py` | 0 | 0 | 100% | — |
| `handlers/air.py` | 22 | 1 | 95% | 9 |
| `handlers/cities.py` | 6 | 0 | 100% | — |
| `handlers/start.py` | 6 | 1 | 83% | 7 |
| `scrapers/__init__.py` | 0 | 0 | 100% | — |
| `scrapers/sensor_community.py` | 77 | 0 | 100% | — |
| `utils/__init__.py` | 0 | 0 | 100% | — |
| `utils/city_data.py` | 9 | 0 | 100% | — |
| **TOTAL** | **210** | **8** | **96%** | |

## Uncovered lines explained

| Location | Code | Why it is uncovered |
|---|---|---|
| `bot.py:15` | `error_handler` body | The error handler is registered but no test triggers a handler exception. |
| `bot.py:33-36` | `main()` | Starts real long-polling against Telegram; intentionally not exercised in tests. |
| `bot.py:40` | `if __name__ == "__main__"` guard | Module entrypoint, not run under pytest. |
| `handlers/air.py:9` | `if not update.message: return` | Guard for updates without a message; not hit by command updates. |
| `handlers/start.py:7` | `if not update.message: return` | Same guard as above. |

All remaining application logic — scraper parsing, retry behavior, statistics,
status bands, alerting, city data, and the full command dispatch path — is
covered.

## Coverage by layer

| Layer | Marker | Tests |
|---|---|---:|
| Unit | `pytest -m unit` | 64 |
| Integration | `pytest -m integration` | 10 |
| E2E | `pytest -m e2e` | 6 |
