.PHONY: install ingest test lint clean

install:
	pip install -r requirements.txt

ingest:
	python -m ingestion.who_ingest

test:
	pytest tests/ -v --tb=short

lint:
	ruff check ingestion/ tests/

clean:
	find . -type d -name __pycache__ -exec rm -rf {} +
	find . -name "*.pyc" -delete