#!/bin/bash
# Test case runner script for Velora Mobility Optimizer
# Usage: ./run_test.sh <TC_NUMBER>
#   or   ./run_test.sh all

set -e

PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
SOLVER="${PROJECT_DIR}/build/solver/velora_solver"
PYTHON_RUNNER="${PROJECT_DIR}/scripts/test_runner.py"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}======================================${NC}"
echo -e "${BLUE}Velora Test Case Runner${NC}"
echo -e "${BLUE}======================================${NC}"
echo ""

# Check if solver is built
if [ ! -f "${SOLVER}" ]; then
    echo -e "${RED}❌ Solver not found: ${SOLVER}${NC}"
    echo "   Build it first: bash build.sh"
    exit 1
fi

# Check if Python runner exists
if [ ! -f "${PYTHON_RUNNER}" ]; then
    echo -e "${RED}❌ Python runner not found: ${PYTHON_RUNNER}${NC}"
    exit 1
fi

# Run test cases
if [ $# -eq 0 ]; then
    echo -e "${YELLOW}Usage: $0 <TC_NUMBER>${NC}"
    echo ""
    echo "Examples:"
    echo "  $0 1         # Run TC01"
    echo "  $0 2         # Run TC02"
    echo "  $0 all       # Run all test cases"
    echo ""
    exit 0
fi

cd "${PROJECT_DIR}"
python3 "${PYTHON_RUNNER}" "$@"

echo ""
echo -e "${GREEN}✅ Done! Check data/ for results${NC}"
