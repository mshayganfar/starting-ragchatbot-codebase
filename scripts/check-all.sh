#!/bin/bash
set -e

echo "🚀 Running complete quality check suite..."

./scripts/format.sh
./scripts/lint.sh
./scripts/test.sh

echo "🎉 All quality checks and tests completed successfully!"