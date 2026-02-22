#!/usr/bin/env bash
#
# VELORA MOBILITY OPTIMIZER - Complete Pipeline Script
# 
# This script runs the ENTIRE pipeline:
#   1. Load environment variables (API keys)
#   2. Convert Excel test data to JSON
#   3. Build the C++ solver
#   4. Run solver on each test case
#   5. Generate SA convergence plots
#   6. Convert JSON output to human-readable reports
#
# Usage: ./build.sh [test_case_number]
#   - No args: run all test cases (01-05)
#   - With arg: run specific test case (e.g., ./build.sh 03)
#
set -euo pipefail

PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BUILD_DIR="${PROJECT_DIR}/build"
ENV_FILE="${PROJECT_DIR}/env/.env"
DATA_DIR="${PROJECT_DIR}/data"
JSON_DIR="${DATA_DIR}/json"
PARSER_DIR="${PROJECT_DIR}/parser"
SCRIPTS_DIR="${PROJECT_DIR}/scripts"
TC_DIR="${PROJECT_DIR}/Velora Kriti_2026 TCs"

# Prefer project virtualenv Python when available
if [ -x "${PROJECT_DIR}/.venv/bin/python" ]; then
    VELORA_PYTHON_BIN="${PROJECT_DIR}/.venv/bin/python"
else
    VELORA_PYTHON_BIN="python3"
fi

# Determine which test cases to run
if [ $# -gt 0 ]; then
    CASES=("$1")
else
    CASES=("01" "02" "03" "04" "05")
fi

echo "=============================================================="
echo "  VELORA MOBILITY OPTIMIZER - Complete Pipeline"
echo "=============================================================="
echo "  Project: ${PROJECT_DIR}"
echo "  Test cases: ${CASES[*]}"
echo "=============================================================="
echo ""

# Ensure Python interpreter is valid even if env/.env sets PYTHON_BIN for deployment
if [ ! -x "$VELORA_PYTHON_BIN" ] && [ "$VELORA_PYTHON_BIN" != "python3" ]; then
    if [ -x "${PROJECT_DIR}/.venv/bin/python" ]; then
        VELORA_PYTHON_BIN="${PROJECT_DIR}/.venv/bin/python"
    else
        VELORA_PYTHON_BIN="python3"
    fi
fi

echo "      Python interpreter: ${VELORA_PYTHON_BIN}"
echo ""

# ============================================================
# STEP 1: Load environment variables
# ============================================================
echo "[1/6] Loading environment variables..."
if [ -f "$ENV_FILE" ]; then
    echo "      Loading from: $ENV_FILE"
    set -a
    # shellcheck disable=SC1090
    source "$ENV_FILE"
    set +a
    if [ -n "${MAPS_API_KEY:-}" ]; then
        echo "      ✓ MAPS_API_KEY is set"
    else
        echo "      ⚠ MAPS_API_KEY not set (using Haversine fallback)"
    fi
else
    echo "      ⚠ No env/.env found (using Haversine distance)"
fi
echo ""

# ============================================================
# STEP 2: Convert Excel test cases to JSON
# ============================================================
echo "[2/6] Converting Excel → JSON..."
mkdir -p "$JSON_DIR"

for CASE in "${CASES[@]}"; do
    EXCEL_PATH="${TC_DIR}/TestCase_TC${CASE}.xlsx"
    JSON_OUT="${JSON_DIR}/tc${CASE}_input.json"
    
    if [ -f "$EXCEL_PATH" ]; then
        echo "      TC${CASE}: $EXCEL_PATH → $JSON_OUT"
        "$VELORA_PYTHON_BIN" "${PARSER_DIR}/excel_to_json.py" "$EXCEL_PATH" "$JSON_OUT"
    else
        echo "      ⚠ TC${CASE}: Excel file not found, skipping"
    fi
done
echo ""

# ============================================================
# STEP 3: Build C++ solver
# ============================================================
echo "[3/6] Building C++ solver..."
mkdir -p "$BUILD_DIR"

# Force reconfigure if CMakeCache doesn't exist or is stale
if [ ! -f "${BUILD_DIR}/CMakeCache.txt" ]; then
    echo "      Configuring CMake..."
    cmake -S "${PROJECT_DIR}" -B "${BUILD_DIR}" -DCMAKE_BUILD_TYPE=Release
fi

echo "      Compiling..."
cmake --build "${BUILD_DIR}" -j$(sysctl -n hw.ncpu 2>/dev/null || echo 4)

if [ -f "${BUILD_DIR}/solver/velora_solver" ]; then
    echo "      ✓ Solver built successfully"
else
    echo "      ✗ ERROR: Solver binary not found!"
    exit 1
fi
echo ""

# ============================================================
# STEP 4: Run solver on each test case
# ============================================================
echo "[4/6] Running solver on test cases..."

for CASE in "${CASES[@]}"; do
    JSON_IN="${JSON_DIR}/tc${CASE}_input.json"
    JSON_OUT="${JSON_DIR}/tc${CASE}_output.json"
    CSV_OUT="${JSON_DIR}/tc${CASE}_convergence.csv"
    
    if [ -f "$JSON_IN" ]; then
        echo "      TC${CASE}: Solving..."
        "${BUILD_DIR}/solver/velora_solver" "$JSON_IN" "$JSON_OUT" "$CSV_OUT"
        echo "      TC${CASE}: ✓ Output: $JSON_OUT"
        [ -f "$CSV_OUT" ] && echo "      TC${CASE}: ✓ Convergence CSV: $CSV_OUT"
    else
        echo "      ⚠ TC${CASE}: Input not found, skipping"
    fi
done
echo ""

# ============================================================
# STEP 5: Generate SA convergence plots
# ============================================================
echo "[5/6] Generating SA convergence plots..."

for CASE in "${CASES[@]}"; do
    CSV_OUT="${JSON_DIR}/tc${CASE}_convergence.csv"
    if [ -f "$CSV_OUT" ]; then
        echo "      TC${CASE}: Plotting convergence..."
        if "$VELORA_PYTHON_BIN" "${SCRIPTS_DIR}/plot_convergence.py" "$CSV_OUT"; then
            :
        else
            echo "      ⚠ TC${CASE}: Plot generation failed (is matplotlib installed?)"
        fi
    else
        echo "      ⚠ TC${CASE}: Convergence CSV not found, skipping"
    fi
done
echo ""

# ============================================================
# STEP 6: Generate text reports
# ============================================================
echo "[6/6] Generating text reports..."

for CASE in "${CASES[@]}"; do
    JSON_OUT="${JSON_DIR}/tc${CASE}_output.json"
    REPORT="${DATA_DIR}/tc${CASE}_report.txt"
    
    if [ -f "$JSON_OUT" ]; then
        echo "      TC${CASE}: Generating report..."
        "$VELORA_PYTHON_BIN" "${SCRIPTS_DIR}/json_to_report.py" "$JSON_OUT" "$REPORT"
    else
        echo "      ⚠ TC${CASE}: Output JSON not found, skipping"
    fi
done
echo ""

# ============================================================
# Summary
# ============================================================
echo "=============================================================="
echo "  PIPELINE COMPLETE"
echo "=============================================================="
echo ""
echo "  Distance Calculation Mode:"
if [ -n "${MAPS_API_KEY:-}" ]; then
    echo "    ✓ Using Google Maps API (real road distances)"
else
    echo "    ⚠ Using Haversine × 1.4 (road distance approximation)"
    echo "      To use real distances, add MAPS_API_KEY to env/.env"
fi
echo ""
echo "  Generated files:"
for CASE in "${CASES[@]}"; do
    JSON_OUT="${JSON_DIR}/tc${CASE}_output.json"
    REPORT="${DATA_DIR}/tc${CASE}_report.txt"
    CSV_OUT="${JSON_DIR}/tc${CASE}_convergence.csv"
    PNG_OUT="${JSON_DIR}/tc${CASE}_convergence.png"
    [ -f "$JSON_OUT" ] && echo "    - ${JSON_OUT}"
    [ -f "$REPORT" ] && echo "    - ${REPORT}"
    [ -f "$CSV_OUT" ] && echo "    - ${CSV_OUT}"
    [ -f "$PNG_OUT" ] && echo "    - ${PNG_OUT}"
done
echo ""
echo "  To view a report:"
echo "    cat ${DATA_DIR}/tc01_report.txt"
echo ""
echo "=============================================================="
