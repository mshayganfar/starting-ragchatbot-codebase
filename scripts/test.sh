#!/bin/bash
set -e

echo "🧪 Running tests..."

echo "Running pytest..."
uv run --python 3.11 pytest tests/ -v

echo "✅ All tests passed!"