#!/bin/bash
set -e

echo "🔧 Formatting Python code with black and isort..."

echo "Running black..."
uv run --python 3.11 black .

echo "Running isort..."
uv run --python 3.11 isort .

echo "✅ Code formatting complete!"