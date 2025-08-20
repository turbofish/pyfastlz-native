# Makefile for pyfastlz-native

.PHONY: help install install-dev lint format type-check test test-cov clean pre-commit-install pre-commit-run all-checks

# Default target
help:
	@echo "Available commands:"
	@echo "  install          Install the package"
	@echo "  install-dev      Install package with development dependencies"
	@echo "  lint             Run ruff linter"
	@echo "  format           Run ruff formatter"
	@echo "  type-check       Run mypy type checker"
	@echo "  test             Run pytest tests"
	@echo "  test-cov         Run tests with coverage report"
	@echo "  pre-commit-install  Install pre-commit hooks"
	@echo "  pre-commit-run   Run pre-commit on all files"
	@echo "  all-checks       Run all quality checks (lint, format, type-check)"
	@echo "  clean            Clean build artifacts and caches"

# Installation targets
install:
	pip install -e .

install-dev:
	pip install -e ".[dev]"

# Linting and formatting
lint:
	ruff check src/ --fix

format:
	ruff format src/

# Type checking
type-check:
	mypy src/

# Testing
test:
	pytest

test-cov:
	pytest --cov=src/fastlz_native --cov-report=html --cov-report=term

# Pre-commit
pre-commit-install:
	pre-commit install

pre-commit-run:
	pre-commit run --all-files

# Combined quality checks
all-checks: lint format type-check
	@echo "All quality checks completed!"

# Cleanup
clean:
	rm -rf build/
	rm -rf dist/
	rm -rf *.egg-info/
	rm -rf .pytest_cache/
	rm -rf .mypy_cache/
	rm -rf .ruff_cache/
	rm -rf htmlcov/
	rm -rf .coverage
	rm -rf env/
	rm -rf venv/
	rm -rf .venv/
	rm -rf .test_env/
	rm -f debug_*.py
	rm -f run_*.py
	rm -f simple_*.py
	rm -f find_*.py
	find . -type d -name __pycache__ -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete
	find . -type f -name "*.pyo" -delete
