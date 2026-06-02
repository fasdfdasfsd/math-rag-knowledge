#!/bin/bash
set -e

echo "=== Stage 1: Lint ==="
uv run ruff format --check src/ tests/
uv run ruff check src/ tests/
uv run mypy --strict src/

echo "=== Stage 2: Test ==="
uv run pytest --cov=src --cov-fail-under=80 -v

echo "=== Stage 3: Security ==="
uv run pip-audit --strict

echo "=== ALL STAGES PASSED ==="
