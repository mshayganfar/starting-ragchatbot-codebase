#!/bin/bash
set -e

echo "🔍 Running code quality checks..."

echo "Running flake8 linter..."
uv run --python 3.11 flake8 backend/ tests/ *.py --max-line-length=88 --extend-ignore=E203,E501,W503,E402,F401,F811,F841

echo "Checking black formatting..."
uv run --python 3.11 black --check .

echo "Checking isort import sorting..."
uv run --python 3.11 isort --check-only .

echo "✅ All quality checks passed!"