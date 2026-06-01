.PHONY: help install install-dev test test-cov format lint clean build upload

help:
	@echo "denv - Environment file redaction tool"
	@echo ""
	@echo "Available targets:"
	@echo "  install      - Install package"
	@echo "  install-dev  - Install package in development mode with dev dependencies"
	@echo "  test         - Run tests"
	@echo "  test-cov     - Run tests with coverage report"
	@echo "  format       - Format code with black and isort"
	@echo "  lint         - Run linters (flake8, mypy)"
	@echo "  clean        - Remove build artifacts"
	@echo "  build        - Build distribution packages"
	@echo "  upload       - Upload to PyPI (requires credentials)"

install:
	pip install .

install-dev:
	pip install -e .
	pip install -r requirements-dev.txt

test:
	pytest

test-cov:
	pytest --cov=denv --cov-report=html --cov-report=term

format:
	black src/ tests/
	isort src/ tests/

lint:
	flake8 src/ tests/
	mypy src/

clean:
	rm -rf build/
	rm -rf dist/
	rm -rf *.egg-info
	rm -rf .pytest_cache
	rm -rf .coverage
	rm -rf htmlcov/
	find . -type d -name __pycache__ -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete

build: clean
	python -m build

upload: build
	python -m twine upload dist/*
