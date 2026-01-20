#!/bin/bash
# Quick command reference for Velora Testing
# Source this file or run commands directly

PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Build commands
build_all() {
    echo "Building Velora Mobility Optimizer..."
    cd "${PROJECT_DIR}"
    bash build.sh
}

clean() {
    echo "Cleaning build artifacts..."
    rm -rf "${PROJECT_DIR}/build"
    echo "✓ Build directory cleaned"
}

rebuild() {
    clean
    build_all
}

# Test commands
run_tc1() {
    echo "Running Test Case 1..."
    python3 "${PROJECT_DIR}/scripts/test_runner.py" 1
}

run_tc2() {
    echo "Running Test Case 2..."
    python3 "${PROJECT_DIR}/scripts/test_runner.py" 2
}

run_tc3() {
    echo "Running Test Case 3..."
    python3 "${PROJECT_DIR}/scripts/test_runner.py" 3
}

run_tc4() {
    echo "Running Test Case 4..."
    python3 "${PROJECT_DIR}/scripts/test_runner.py" 4
}

run_all_tc() {
    echo "Running ALL Test Cases..."
    python3 "${PROJECT_DIR}/scripts/test_runner.py" all
}

# View results
view_tc1_report() {
    cat "${PROJECT_DIR}/data/tc01_report.txt"
}

view_tc2_report() {
    cat "${PROJECT_DIR}/data/tc02_report.txt"
}

view_tc3_report() {
    cat "${PROJECT_DIR}/data/tc03_report.txt"
}

view_tc4_report() {
    cat "${PROJECT_DIR}/data/tc04_report.txt"
}

view_all_reports() {
    for i in {1..4}; do
        file="${PROJECT_DIR}/data/tc0${i}_report.txt"
        if [ -f "$file" ]; then
            echo ""
            cat "$file"
        fi
    done
}

# Utility commands
status() {
    echo "=== Build Status ==="
    if [ -f "${PROJECT_DIR}/build/solver/velora_solver" ]; then
        echo "✅ Solver: BUILT"
        ls -lh "${PROJECT_DIR}/build/solver/velora_solver"
    else
        echo "❌ Solver: NOT BUILT"
    fi
    echo ""
    echo "=== Test Case Files ==="
    ls -lh "${PROJECT_DIR}/Velora Kriti_2026 TCs"/*.xlsx 2>/dev/null || echo "No test cases found"
    echo ""
    echo "=== Reports Generated ==="
    ls -lh "${PROJECT_DIR}/data"/tc*_report.txt 2>/dev/null || echo "No reports yet"
}

show_help() {
    cat << 'EOF'
╔════════════════════════════════════════════════════════════════════════════╗
║           Velora Mobility Optimizer - Command Reference                    ║
╚════════════════════════════════════════════════════════════════════════════╝

BUILD COMMANDS:
  build_all              Build the entire project
  rebuild                Clean and rebuild
  clean                  Remove build artifacts

TEST COMMANDS:
  run_tc1                Run Test Case 1 (TC01)
  run_tc2                Run Test Case 2 (TC02)
  run_tc3                Run Test Case 3 (TC03)
  run_tc4                Run Test Case 4 (TC04)
  run_all_tc             Run all test cases

VIEW RESULTS:
  view_tc1_report        Display TC01 text report
  view_tc2_report        Display TC02 text report
  view_tc3_report        Display TC03 text report
  view_tc4_report        Display TC04 text report
  view_all_reports       Display all reports

UTILITY:
  status                 Show build and test status
  show_help              Show this help message

EXAMPLES:
  source commands.sh && build_all && run_all_tc
  source commands.sh && run_tc1 && view_tc1_report
  source commands.sh && clean && rebuild && run_all_tc && view_all_reports

DIRECT COMMANDS (no sourcing needed):
  python3 scripts/test_runner.py 1        Run TC01
  python3 scripts/test_runner.py all      Run all test cases
  bash scripts/run_test.sh 1              Run TC01 via bash
  bash scripts/run_test.sh all            Run all test cases via bash

OUTPUT FILES:
  data/tc01_input.json               Input JSON for TC01
  data/tc01_output.json              Output JSON for TC01
  data/tc01_report.txt               Human-readable report for TC01

EOF
}

# If script is sourced with no arguments, show help
if [ "${BASH_SOURCE[0]}" == "${0}" ]; then
    case "${1:-help}" in
        build)      build_all ;;
        rebuild)    rebuild ;;
        clean)      clean ;;
        tc1)        run_tc1 ;;
        tc2)        run_tc2 ;;
        tc3)        run_tc3 ;;
        tc4)        run_tc4 ;;
        all)        run_all_tc ;;
        status)     status ;;
        help|*)     show_help ;;
    esac
else
    # Script was sourced, functions are available
    :
fi
