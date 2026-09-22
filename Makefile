.PHONY: help install install-dev test test-cov format lint clean build upload

VENV ?= .venv
PY := $(VENV)/bin
LOCALBIN ?= $(HOME)/.local/bin

help:
	@echo "denv - per-project env store + .env redactor"
	@echo ""
	@echo "Available targets:"
	@echo "  install      - venv + editable install + symlink 'denv' onto ~/.local/bin"
	@echo "  install-dev  - install + dev dependencies (pytest, black, ...)"
	@echo "  test         - Run tests"
	@echo "  test-cov     - Run tests with coverage report"
	@echo "  format       - Format code with black and isort"
	@echo "  lint         - Run linters (flake8, mypy)"
	@echo "  clean        - Remove build artifacts"
	@echo "  build        - Build distribution packages"
	@echo "  upload       - Upload to PyPI (requires credentials)"

# venv-local install; symlink the console script onto $PATH (the ~/.local/bin
# convention). Re-run any time; the symlink tracks the venv shim in place.
install:
	python3 -m venv $(VENV)
	$(PY)/pip install -e . -q
	mkdir -p $(LOCALBIN)
	ln -sfn $(CURDIR)/$(VENV)/bin/denv $(LOCALBIN)/denv
	@echo "installed: $(LOCALBIN)/denv -> $(CURDIR)/$(VENV)/bin/denv"

install-dev: install
	$(PY)/pip install -r requirements-dev.txt -q

test:
	$(PY)/pytest

test-cov:
	$(PY)/pytest --cov=denv --cov-report=html --cov-report=term

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
