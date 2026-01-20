#!/bin/bash
# Summary view for all test case reports
# Displays all generated reports side-by-side

PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

echo "╔════════════════════════════════════════════════════════════════════════════╗"
echo "║         VELORA MOBILITY OPTIMIZER - ALL TEST CASE RESULTS                  ║"
echo "╚════════════════════════════════════════════════════════════════════════════╝"
echo ""

for i in 1 2 3 4; do
    REPORT="${PROJECT_DIR}/data/tc0${i}_report.txt"
    if [ -f "$REPORT" ]; then
        echo ""
        cat "$REPORT"
        echo ""
        echo "════════════════════════════════════════════════════════════════════════════════"
        echo ""
    fi
done

echo ""
echo "📊 SUMMARY TABLE"
echo "────────────────────────────────────────────────────────────────────────────────"
echo "Test | Requests | Vehicles | Initial Cost | Final Cost | Improvement"
echo "────────────────────────────────────────────────────────────────────────────────"

for i in 1 2 3 4; do
    JSON_OUTPUT="${PROJECT_DIR}/data/json/tc0${i}_output.json"
    JSON_INPUT="${PROJECT_DIR}/data/json/tc0${i}_input.json"
    
    if [ -f "$JSON_OUTPUT" ] && [ -f "$JSON_INPUT" ]; then
        REQ_COUNT=$(cat "$JSON_INPUT" | python3 -c "import sys, json; print(len(json.load(sys.stdin).get('requests', [])))" 2>/dev/null || echo "?")
        VEH_COUNT=$(cat "$JSON_INPUT" | python3 -c "import sys, json; print(len(json.load(sys.stdin).get('vehicles', [])))" 2>/dev/null || echo "?")
        FINAL_COST=$(cat "$JSON_OUTPUT" | python3 -c "import sys, json; print(f\"{json.load(sys.stdin).get('globalCost', 0):.2f}\")" 2>/dev/null || echo "?")
        
        # Try to get initial cost from solver log or estimate
        INITIAL_COST=$(grep "Initial cost:" "${PROJECT_DIR}/data/tc0${i}_solver.log" 2>/dev/null | awk '{print $NF}' || echo "N/A")
        
        printf "TC0%d |    %2s      |     %d      |      N/A       |    $%-8s | N/A\n" "$i" "$REQ_COUNT" "$VEH_COUNT" "$FINAL_COST"
    fi
done

echo "────────────────────────────────────────────────────────────────────────────────"
echo ""
echo "📁 Output Files:"
echo "   JSON Input:  data/json/tc0X_input.json"
echo "   JSON Output: data/json/tc0X_output.json"
echo "   Reports:     data/tc0X_report.txt"
