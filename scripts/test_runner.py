#!/usr/bin/env python3
"""
Test case runner for Velora Mobility Optimizer
Reads test case Excel files, converts to JSON, runs solver, and produces clean text reports.
"""

import sys
import json
import os
import subprocess
from pathlib import Path

# Get project root for venv Python path
PROJECT_ROOT = Path(__file__).parent.parent.absolute()
VENV_PYTHON = PROJECT_ROOT / ".venv" / "bin" / "python3"
PYTHON_CMD = str(VENV_PYTHON) if VENV_PYTHON.exists() else "python3"

def run_test_case(tc_number):
    """
    Run a single test case.
    
    Args:
        tc_number: Test case number (e.g., 1, 2, 3, 4)
    
    Returns:
        dict with results
    """
    
    # Get project root (parent of scripts directory)
    project_root = Path(__file__).parent.parent.absolute()
    tc_dir = project_root / "Velora Kriti_2026 TCs"
    
    # Find test case file
    tc_file = tc_dir / f"TestCase_TC{tc_number:02d}.xlsx"
    
    if not tc_file.exists():
        print(f"❌ Test case file not found: {tc_file}")
        print(f"   Available test cases: {list(tc_dir.glob('TestCase_*.xlsx'))}")
        return None
    
    print(f"📋 Running Test Case: TC{tc_number:02d}")
    print(f"   Input file: {tc_file}")
    
    # Output files
    json_input = PROJECT_ROOT / "data" / "json" / f"tc{tc_number:02d}_input.json"
    json_output = PROJECT_ROOT / "data" / "json" / f"tc{tc_number:02d}_output.json"
    txt_report = PROJECT_ROOT / "data" / f"tc{tc_number:02d}_report.txt"
    
    # Create data dirs
    json_input.parent.mkdir(parents=True, exist_ok=True)
    txt_report.parent.mkdir(parents=True, exist_ok=True)
    
    # Step 1: Convert Excel to JSON
    print(f"   [1/3] Converting Excel → JSON...")
    try:
        result = subprocess.run(
            [PYTHON_CMD, str(PROJECT_ROOT / "parser" / "excel_to_json.py"), 
             str(tc_file), str(json_input)],
            capture_output=True,
            text=True,
            timeout=60
        )
        if result.returncode != 0:
            print(f"❌ Excel conversion failed: {result.stderr}")
            return None
        print(f"   ✓ JSON created: {json_input}")
    except subprocess.TimeoutExpired:
        print(f"❌ Excel conversion timed out (>60s)")
        return None
    except Exception as e:
        print(f"❌ Excel conversion error: {e}")
        return None
    
    # Step 2: Run solver
    print(f"   [2/3] Running optimization solver...")
    solver_path = PROJECT_ROOT / "build" / "solver" / "velora_solver"
    
    if not solver_path.exists():
        print(f"❌ Solver not found: {solver_path}")
        print(f"   Run: bash build.sh")
        return None
    
    try:
        result = subprocess.run(
            [str(solver_path), str(json_input), str(json_output)],
            capture_output=True,
            text=True,
            timeout=60
        )
        
        solver_warnings = []
        if result.stderr:
            for line in result.stderr.split('\n'):
                if line.strip():
                    solver_warnings.append(line)
                    # Print to console if meaningful warning
                    if "Warning" in line or "Failed" in line or "API" in line:
                         print(f"   ⚠️ {line}")

        if result.returncode != 0:
            print(f"❌ Solver failed: {result.stderr}")
            return None
        
        # Print solver output
        if result.stdout:
            for line in result.stdout.strip().split('\n'):
                print(f"   {line}")
        
        print(f"   ✓ Solution created: {json_output}")
    except Exception as e:
        print(f"❌ Solver error: {e}")
        return None
    
    # Step 3: Parse JSON and create text report
    print(f"   [3/3] Generating text report...")
    try:
        with open(json_output, 'r') as f:
            solution = json.load(f)
        
        # Load input for comparison
        with open(json_input, 'r') as f:
            input_data = json.load(f)
        
        # Generate report
        report = generate_report(tc_number, input_data, solution, json_input, json_output, solver_warnings)
        
        with open(txt_report, 'w') as f:
            f.write(report)
        
        print(f"   ✓ Report created: {txt_report}")
    except Exception as e:
        print(f"❌ Report generation failed: {e}")
        return None
    
    print(f"✅ Test case TC{tc_number:02d} completed successfully\n")
    
    return {
        'test_case': tc_number,
        'json_input': str(json_input),
        'json_output': str(json_output),
        'txt_report': str(txt_report),
        'solution': solution
    }


def generate_report(tc_number, input_data, solution, json_in_path, json_out_path, warnings=None):
    """
    Generate a clean text report from solution JSON.
    """
    
    vehicles = input_data.get('vehicles', [])
    requests = input_data.get('requests', [])
    routes = solution.get('routes', [])
    unassigned = solution.get('unassigned', [])
    global_cost = solution.get('globalCost', 0)
    baseline_data = input_data.get('baseline', [])
    
    report = []
    report.append("=" * 80)
    report.append(f"VELORA MOBILITY OPTIMIZER - TEST CASE TC{tc_number:02d}")
    if warnings:
        for w in warnings:
            if "Warning" in w or "Failed" in w:
                report.append(f"⚠️  SYSTEM WARNING: {w}") 

    report.append("=" * 80)
    report.append("")
    
    # Input Summary
    report.append("INPUT SUMMARY")
    report.append("-" * 80)
    report.append(f"Total Requests:    {len(requests)}")
    report.append(f"Total Vehicles:    {len(vehicles)}")
    report.append("")
    
    # Vehicle Details
    report.append("VEHICLES:")
    for v in vehicles:
        report.append(f"  V{v.get('id', '?'):02d} | Capacity: {v.get('capacity', '?'):3d} | "
                     f"Cost/km: ${v.get('costPerKm', 0):.2f} | "
                     f"Start: ({v.get('startLoc', {}).get('lat', 0):.4f}, "
                     f"{v.get('startLoc', {}).get('lon', 0):.4f})")
    report.append("")
    
    # Request Details
    report.append("REQUESTS:")
    for r in requests:
        priority_val = r.get('priority', '?')
        # Display as P1, P2 ... P5
        priority_text = f"P{priority_val}" if str(priority_val).isdigit() else str(priority_val)
        
        report.append(f"  R{r.get('id', '?'):02d} | Priority: {priority_text:6s} | Load: {r.get('load', 1)} | "
                     f"Window: [{r.get('earlyTime', 0):6.1f}, {r.get('lateTime', 1e6):8.1f}]")
    report.append("")
    
    # Optimization Results
    report.append("=" * 80)
    report.append("OPTIMIZATION RESULTS")
    report.append("=" * 80)
    report.append(f"Global Cost:       ${global_cost:.2f}")
    report.append(f"Routes Assigned:   {len(routes)}")
    report.append(f"Requests Assigned: {sum(len(r.get('stops', []))//2 for r in routes)}")
    report.append(f"Requests Unassigned: {len(unassigned)}")
    report.append("")
    
    # Baseline Comparison
    if baseline_data:
        report.append("BASELINE COMPARISON")
        report.append("-" * 80)
        baseline_total = 0.0
        for baseline_entry in baseline_data:
            baseline_cost = float(baseline_entry.get('baseline_cost', baseline_entry.get('baseline_Cost', 0)))
            baseline_total += baseline_cost
        
        if baseline_total > 0:
            improvement = baseline_total - global_cost
            improvement_pct = (improvement / baseline_total * 100)
            
            report.append(f"  Baseline Total Cost:   ${baseline_total:10.2f}")
            report.append(f"  Optimized Total Cost:  ${global_cost:10.2f}")
            report.append(f"  - Improvement:         ${improvement:10.2f}  ({improvement_pct:+.1f}%)")
            report.append("")
    
    # Route Details
    report.append("DETAILED ROUTES")
    report.append("-" * 80)
    
    for route in routes:
        v_id = route.get('vehicleId', '?')
        total_cost = route.get('totalCost', 0)
        total_dist = route.get('totalDist', 0)
        stops = route.get('stops', [])
        
        if not stops:
            report.append(f"Vehicle V{v_id:02d}: (EMPTY)")
            continue
        
        report.append(f"Vehicle V{v_id:02d}:")
        report.append(f"  Total Distance: {total_dist:.2f} km")
        report.append(f"  Total Cost:     ${total_cost:.2f}")
        report.append(f"  Stops: {len(stops)}")
        report.append("")
        
        for i, stop in enumerate(stops, 1):
            req_id = stop.get('reqId', '?')
            stop_type = "PICKUP" if stop.get('type', '') == 'P' else "DROPOFF"
            arrival = stop.get('arrival', 0)
            lat = stop.get('lat', 0)
            lon = stop.get('lon', 0)
            
            # Find request for time window info
            req_info = next((r for r in requests if r.get('id') == req_id), {})
            time_window = f"[{req_info.get('earlyTime', 0):.1f}, {req_info.get('lateTime', 1e6):.1f}]"
            
            report.append(f"    {i}. {stop_type:7s} Request R{req_id:02d} @ {arrival:7.2f} | "
                         f"Window: {time_window} | ({lat:.4f}, {lon:.4f})")
        report.append("")
    
    # Unassigned Requests & Infeasibility Analysis
    report.append("INFEASIBILITY ANALYSIS & RELAXED CONSTRAINTS")
    report.append("-" * 80)
    
    has_infeasibility_info = False
    
    # Check for unassigned
    if unassigned:
        has_infeasibility_info = True
        report.append("UNASSIGNED REQUESTS (HARD INFEASIBILITY):")
        for req_id in unassigned:
            req = next((r for r in requests if r.get('id') == req_id), {})
            p_val = req.get('priority', '?')
            report.append(f"  [!] R{req_id:02d} (P{p_val}) could not be assigned.")
            report.append(f"      Reason: Strictly violates Time Window or Max Delay limits even with soft relaxations.")
        report.append("")
    
    # Check for relaxed constraints (Soft Infeasibility)
    relaxed_found = False
    report.append("RELAXED CONSTRAINTS (SOFT INFEASIBILITY):")
    for route in routes:
        v_id = route.get('vehicleId', '?')
        # Find vehicle object
        vehicle = next((v for v in vehicles if v.get('id') == v_id), {})
        v_type = vehicle.get('type', 'any').lower()
        
        # Track load for sharing limits
        current_load = 0
        active_reqs = []
        
        # Re-simulate to find violations
        stops = route.get('stops', [])
        # Sort stops by arrival? They should be sorted.
        
        for stop in stops:
            req_id = stop.get('reqId')
            req = next((r for r in requests if r.get('id') == req_id), {})
            
            # 0. Check Max Delay Violation (Forced Infeasibility)
            if stop.get('type') == 'D': # Dropoff
                late_time = req.get('lateTime', 1e6)
                arrival = stop.get('arrival', 0)
                p_val = int(req.get('priority', 3))
                
                # Get max delay for this priority
                tolerances = input_data.get('config', {}).get('tolerances', {})
                max_delay_allowed = float(tolerances.get(str(p_val), 30))
                
                delay = max(0, arrival - late_time)
                if delay > max_delay_allowed + 0.01: # Epsilon
                     relaxed_found = True
                     has_infeasibility_info = True
                     report.append(f"  [!!] MAX DELAY CONSTRAINT VIOLATED (Forced): Req R{req_id:02d} (P{p_val})")
                     report.append(f"       Arrival: {arrival:.1f} | Window End: {late_time:.1f} | Delay: {delay:.1f}m (Allowed: {max_delay_allowed}m)")
                     report.append(f"       Action: Employee transported despite infeasible timeline (as per 'must go' instruction).")

            # 1. Vehicle Preference Check
            if stop.get('type') == 'P': # Pickup
                pref = req.get('vehiclePreference', 'any').lower()
                if pref != 'any' and v_type != 'any' and pref != v_type:
                    relaxed_found = True
                    has_infeasibility_info = True
                    report.append(f"  [~] Vehicle Preference Relaxed: Req R{req_id:02d} (Pref: {pref}) assigned to V{v_id:02d} (Type: {v_type})")
            
            # 2. Sharing Limit Check
            if stop.get('type') == 'P':
                current_load += req.get('load', 1)
                active_reqs.append(req)
            else:
                current_load -= req.get('load', 1)
                active_reqs = [r for r in active_reqs if r.get('id') != req_id]
                
            # Check for everyone currently in car
            for active in active_reqs:
                limit = active.get('sharingLimit', 100)
                if current_load > limit:
                    # Avoid spamming multiple times for same violation?
                    # simple heuristic: just report it
                    relaxed_found = True
                    has_infeasibility_info = True
                    report.append(f"  [~] Sharing Limit Relaxed: Req R{active.get('id'):02d} (Limit: {limit}) in vehicle with load {current_load}")

    if not relaxed_found:
        report.append("  No soft constraints were relaxed.")
    
    report.append("")
    
    # Cost Breakdown
    report.append("COST BREAKDOWN")
    report.append("-" * 80)
    route_costs = [r.get('totalCost', 0) for r in routes]
    unassigned_cost = len(unassigned) * 10000.0
    
    total_route_cost = sum(route_costs)
    for i, route in enumerate(routes):
        v_id = route.get('vehicleId', '?')
        cost = route.get('totalCost', 0)
        pct = (cost / global_cost * 100) if global_cost > 0 else 0
        report.append(f"  Vehicle V{v_id:02d}:      ${cost:10.2f}  ({pct:5.1f}%)")
    
    if unassigned:
        pct = (unassigned_cost / global_cost * 100) if global_cost > 0 else 0
        report.append(f"  Unassigned Penalty: ${unassigned_cost:10.2f}  ({pct:5.1f}%)")
    
    report.append("-" * 80)
    report.append(f"  TOTAL:             ${global_cost:10.2f}  (100.0%)")
    report.append("")
    
    # File references
    report.append("FILE REFERENCES")
    report.append("-" * 80)
    report.append(f"Input JSON:  {json_in_path}")
    report.append(f"Output JSON: {json_out_path}")
    report.append("")
    report.append("=" * 80)
    
    return "\n".join(report)


def main():
    if len(sys.argv) < 2:
        print("Usage: python3 test_runner.py <TC_NUMBER>")
        print("")
        print("Examples:")
        print("  python3 test_runner.py 1      # Run TC01")
        print("  python3 test_runner.py 2      # Run TC02")
        print("  python3 test_runner.py all    # Run all test cases")
        print("")
        sys.exit(1)
    
    arg = sys.argv[1].lower()
    
    if arg == 'all':
        print("🧪 Running ALL test cases...")
        print("")
        for tc in [1, 2, 3, 4]:
            run_test_case(tc)
    else:
        try:
            tc_num = int(arg)
            run_test_case(tc_num)
        except ValueError:
            print(f"❌ Invalid test case number: {arg}")
            sys.exit(1)


if __name__ == '__main__':
    main()
