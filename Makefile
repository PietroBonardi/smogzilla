.PHONY: install test test-unit test-integration test-e2e coverage notebook

## install -- install the local package + dev requirements into .venv
install:
	.venv/bin/pip install -e .
	.venv/bin/pip install -r requirements.txt -r requirements-dev.txt

## test -- run unit + integration suite
test:
	.venv/bin/pytest -m "unit or integration"

## test-unit -- run unit layer only
test-unit:
	.venv/bin/pytest -m unit

## test-integration -- run integration layer only
test-integration:
	.venv/bin/pytest -m integration

## test-e2e -- run e2e layer (currently skipped; ptb version mismatch)
test-e2e:
	.venv/bin/pytest -m e2e

## coverage -- test + coverage report
coverage:
	.venv/bin/pytest -m "unit or integration" \
	    --cov=bot --cov=config --cov=formatter \
	    --cov=handlers --cov=scrapers --cov=utils \
	    --cov-report=term-missing

## notebook -- launch jupyter
notebook:
	.venv/bin/jupyter notebook notebooks/
