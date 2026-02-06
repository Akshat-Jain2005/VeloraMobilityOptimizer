#!/usr/bin/env python3
"""
Velora Mobility Optimizer - Unified CLI Tool

A single command-line interface for all Velora operations:
- Running test cases (Excel → JSON → Solver → Report)
- Benchmarking and verification
- Report generation
- Excel to JSON conversion

Usage:
    python velora.py run [TC_NUMBER|all]     Run test case(s)
    python velora.py benchmark [OPTIONS]     Run benchmarks
    python velora.py report <output.json>    Generate report from JSON
    python velora.py convert <input.xlsx>    Convert Excel to JSON
    python velora.py status                  Show project status
    python velora.py help                    Show detailed help

Examples:
    python velora.py run 1                   # Run TC01
    python velora.py run all                 # Run all test cases
    python velora.py benchmark --save        # Run and save benchmarks
    python velora.py status                  # Check solver build status
"""

import sys
import os
import json
import math
import subprocess
import argparse
from pathlib import Path
from datetime import datetime
from dataclasses import dataclass, field
from typing import Dict, List, Optional

# ============================================================================
# CONFIGURATION
# ============================================================================

PROJECT_ROOT = Path(__file__).parent.absolute()
VENV_PYTHON = PROJECT_ROOT / ".venv" / "bin" / "python3"
PYTHON_CMD = str(VENV_PYTHON) if VENV_PYTHON.exists() else "python3"
SOLVER_PATH = PROJECT_ROOT / "build" / "solver" / "velora_solver"
DATA_DIR = PROJECT_ROOT / "data"
JSON_DIR = DATA_DIR / "json"
TC_DIR = PROJECT_ROOT / "Velora Kriti_2026 TCs"

# ============================================================================
# UTILITY FUNCTIONS
# ============================================================================

def print_header(title: str):
    """Print a formatted header."""
    print("\n" + "=" * 70)
    print(f"  {title}")
    print("=" * 70)

def print_success(msg: str):
    print(f"✅ {msg}")

def print_error(msg: str):
    print(f"❌ {msg}")

def print_warning(msg: str):
    print(f"⚠️  {msg}")

def print_info(msg: str):
    print(f"ℹ️  {msg}")

def minutes_to_time(minutes: float) -> str:
    """Convert minutes from midnight to HH:MM format."""
    if minutes is None or minutes <= 0:
        return "N/A"
    hours = int(minutes // 60)
    mins = int(minutes % 60)
    return f"{hours:02d}:{mins:02d}"

def haversine_distance(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Calculate road distance between two points in km (with 1.4x road factor)."""
    R = 6371.0
    lat1_rad, lat2_rad = math.radians(lat1), math.radians(lat2)
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = math.sin(dlat/2)**2 + math.cos(lat1_rad)*math.cos(lat2_rad)*math.sin(dlon/2)**2
    c = 2 * math.asin(min(1.0, math.sqrt(a)))
    return R * c * 1.4

def check_solver():
    """Check if solver is built."""
    return SOLVER_PATH.exists()

def check_venv():
    """Check if virtual environment exists."""
    return VENV_PYTHON.exists()

# ============================================================================
# EXCEL TO JSON CONVERTER
# ============================================================================

def convert_excel_to_json(input_xlsx: Path, output_json: Path) -> bool:
    """Convert Excel test case to JSON format."""
    try:
        import pandas as pd
    except ImportError:
        print_error("pandas not installed. Run: pip install pandas openpyxl")
        return False
    
    def time_to_minutes(time_obj):
        import datetime as dt
        if isinstance(time_obj, dt.time):
            return time_obj.hour * 60 + time_obj.minute
        elif isinstance(time_obj, str):
            try:
                h, m = time_obj.split(':')
                return int(h) * 60 + int(m)
            except:
                return 0.0
        elif isinstance(time_obj, (int, float)):
            return float(time_obj)
        return 0.0
    
    def get_sharing_limit(val):
        if not val or not isinstance(val, str): return 100
        v = val.lower().strip()
        if 'single' in v: return 1
        if 'double' in v: return 2
        if 'triple' in v: return 3
        return 100
    
    def normalize_text(val, default=""):
        return str(val).strip() if val is not None else default
    
    xls = pd.ExcelFile(input_xlsx)
    result = {"config": {"allow_external_maps": True, "maps_api_key": ""}}
    
    # Parse metadata
    if 'metadata' in xls.sheet_names:
        df = xls.parse('metadata')
        tolerances = {}
        weights = {"cost": 0.7, "time": 0.3}
        for _, r in df.iterrows():
            key = str(r.get('key', '')).strip().lower()
            val = r.get('value')
            if 'priority' in key and 'delay' in key:
                try:
                    prio = int(''.join(filter(str.isdigit, key)))
                    tolerances[str(prio)] = int(val)
                except: pass
            elif key == 'objective_cost_weight':
                weights['cost'] = float(val)
            elif key == 'objective_time_weight':
                weights['time'] = float(val)
            elif key == 'allow_external_maps':
                result['config']['allow_external_maps'] = str(val).lower() == 'true'
        if tolerances:
            result['config']['tolerances'] = tolerances
        result['config']['weights'] = weights
    
    # Parse vehicles
    if 'vehicles' in xls.sheet_names:
        df = xls.parse('vehicles')
        vehicles = []
        for idx, r in df.where(pd.notnull(df), None).to_dict(orient='records').__iter__():
            pass
        for idx, r in enumerate(df.where(pd.notnull(df), None).to_dict(orient='records')):
            vehicle_type = normalize_text(r.get('vehicle_type', r.get('type', 'any'))).lower()
            v = {
                'id': idx,
                'vehicle_id': r.get('vehicle_id', f'V{idx:02d}'),
                'fuel_type': normalize_text(r.get('fuel_type', '')),
                'vehicle_type': vehicle_type,
                'capacity': int(r.get('capacity', 4) or 4),
                'type': vehicle_type,
                'costPerKm': float(r.get('cost_per_km', r.get('costPerKm', 1.0)) or 1.0),
                'avg_speed_kmph': float(r.get('avg_speed_kmph', 30.0) or 30.0),
                'startLoc': {
                    'lat': float(r.get('current_lat', r.get('startLat', 0.0)) or 0.0),
                    'lon': float(r.get('current_lng', r.get('startLon', 0.0)) or 0.0)
                },
                'availabilityTime': time_to_minutes(r.get('available_from', 0)),
                'category': normalize_text(r.get('category', ''))
            }
            vehicles.append(v)
        result['vehicles'] = vehicles
    
    # Parse requests/employees
    if 'employees' in xls.sheet_names:
        df = xls.parse('employees')
        requests = []
        employees = []
        baseline = []
        
        for idx, r in enumerate(df.where(pd.notnull(df), None).to_dict(orient='records')):
            emp_id = r.get('employee_id', f'E{idx+1:02d}')
            
            req = {
                'id': idx,
                'employee_id': emp_id,
                'priority': int(r.get('priority', 3) or 3),
                'vehiclePreference': normalize_text(r.get('vehicle_preference', 'any')).lower(),
                'sharingLimit': get_sharing_limit(r.get('sharing_preference')),
                'pickup': {
                    'lat': float(r.get('pickup_lat', 0.0) or 0.0),
                    'lon': float(r.get('pickup_lng', 0.0) or 0.0)
                },
                'dropoff': {
                    'lat': float(r.get('dropoff_lat', 0.0) or 0.0),
                    'lon': float(r.get('dropoff_lng', 0.0) or 0.0)
                },
                'earlyTime': time_to_minutes(r.get('earliest_pickup_time', 0)),
                'lateTime': time_to_minutes(r.get('latest_dropoff_time', 1440)),
                'load': 1
            }
            requests.append(req)
            
            employees.append({
                'id': idx,
                'name': emp_id,
                'shiftStart': 0.0,
                'shiftEnd': 24.0,
                'startLoc': {'lat': 0.0, 'lon': 0.0}
            })
            
            baseline.append({
                'employee_id': emp_id,
                'baseline_cost': float(r.get('baseline_cost', 0) or 0),
                'baseline_time_min': int(r.get('baseline_time_min', 0) or 0)
            })
        
        result['requests'] = requests
        result['employees'] = employees
        result['baseline'] = baseline
    
    # Write output
    output_json.parent.mkdir(parents=True, exist_ok=True)
    with open(output_json, 'w') as f:
        json.dump(result, f, indent=2)
    
    return True

# ============================================================================
# REPORT GENERATOR
# ============================================================================

def calculate_shared_costs(routes: List[dict], vehicle_map: dict) -> Dict[str, float]:
    """Calculate per-employee cost with proper sharing."""
    employee_costs = {}
    
    for route in routes:
        stops = route.get("stops", [])
        if len(stops) < 2:
            continue
        
        vehicle_idx = route.get("vehicleId", 0)
        vehicle_info = vehicle_map.get(vehicle_idx, {})
        cost_per_km = vehicle_info.get("cost_per_km", 10)
        
        passengers_in_vehicle = set()
        
        for i in range(len(stops)):
            stop = stops[i]
            emp_id = stop.get("employeeId")
            stop_type = stop.get("type")
            
            if stop_type == "pickup":
                passengers_in_vehicle.add(emp_id)
            elif stop_type == "dropoff":
                passengers_in_vehicle.discard(emp_id)
            
            if i < len(stops) - 1:
                next_stop = stops[i + 1]
                dist = haversine_distance(
                    stop.get("lat", 0), stop.get("lon", 0),
                    next_stop.get("lat", 0), next_stop.get("lon", 0)
                )
                segment_cost = dist * cost_per_km
                
                if passengers_in_vehicle:
                    cost_per_passenger = segment_cost / len(passengers_in_vehicle)
                    for passenger in passengers_in_vehicle:
                        employee_costs[passenger] = employee_costs.get(passenger, 0) + cost_per_passenger
    
    return employee_costs

def generate_report(output_json: Path, input_json: Path = None, report_path: Path = None) -> str:
    """Generate text report from solver output."""
    with open(output_json) as f:
        output_data = json.load(f)
    
    # Find input file
    input_data = None
    if input_json and input_json.exists():
        with open(input_json) as f:
            input_data = json.load(f)
    else:
        possible_input = output_json.parent / output_json.name.replace('_output', '_input')
        if possible_input.exists():
            with open(possible_input) as f:
                input_data = json.load(f)
    
    lines = []
    lines.append("=" * 80)
    lines.append("              VELORA MOBILITY OPTIMIZER - SOLUTION REPORT")
    lines.append("=" * 80)
    lines.append(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    lines.append(f"Output file: {output_json}")
    lines.append("")
    
    # Build lookup tables
    baseline_map = {}
    vehicle_map = {}
    request_map = {}
    
    if input_data:
        for b in input_data.get("baseline", []):
            baseline_map[b.get("employee_id", "")] = {
                "cost": b.get("baseline_cost", 0),
                "time": b.get("baseline_time_min", 0)
            }
        
        for v in input_data.get("vehicles", []):
            vehicle_map[v.get("id")] = {
                "vehicle_id": v.get("vehicle_id", ""),
                "fuel_type": v.get("fuel_type", "unknown"),
                "vehicle_type": v.get("vehicle_type", "unknown"),
                "capacity": v.get("capacity", 0),
                "cost_per_km": v.get("costPerKm", 0),
                "speed": v.get("avg_speed_kmph", 30),
                "category": v.get("category", ""),
                "start_lat": v.get("startLoc", {}).get("lat", 0),
                "start_lon": v.get("startLoc", {}).get("lon", 0)
            }
        
        for r in input_data.get("requests", []):
            request_map[r.get("id")] = r
    
    routes = output_data.get("routes", [])
    summary = output_data.get("summary", {})
    
    # Calculate shared costs
    employee_shared_costs = calculate_shared_costs(routes, vehicle_map)
    
    # Summary section
    ctc = summary.get('totalMoneyCost', 0)
    lines.append("-" * 80)
    lines.append("SUMMARY")
    lines.append("-" * 80)
    lines.append(f"  CTC (Cost to Company):     {ctc:,.2f}")
    lines.append(f"  Total Penalty Cost:        {summary.get('totalPenaltyCost', 0):,.2f}")
    lines.append(f"  Global Objective:          {summary.get('globalCost', 0):,.2f}")
    lines.append(f"  Total Distance:            {summary.get('totalDistance', 0):,.2f} km")
    lines.append(f"  Total Time:                {summary.get('totalTime', 0):,.1f} minutes")
    lines.append(f"  Vehicles Used:             {summary.get('vehiclesUsed', 0)}")
    lines.append(f"  Unassigned Requests:       {summary.get('unassignedCount', 0)}")
    
    if baseline_map:
        total_baseline = sum(b["cost"] for b in baseline_map.values())
        total_baseline_time = sum(b["time"] for b in baseline_map.values())
        savings = total_baseline - ctc
        savings_pct = (savings / total_baseline * 100) if total_baseline > 0 else 0
        lines.append("")
        lines.append(f"  === COST COMPARISON ===")
        lines.append(f"  Total Baseline Cost:       {total_baseline:,.2f}")
        lines.append(f"  Optimized CTC:             {ctc:,.2f}")
        lines.append(f"  Net Savings:               {savings:,.2f} ({savings_pct:.1f}%)")
    lines.append("")
    
    # Routes section
    active_routes = [r for r in routes if r.get("stops")]
    lines.append("-" * 80)
    lines.append(f"VEHICLE ROUTES ({len(active_routes)} active)")
    lines.append("-" * 80)
    
    for route in routes:
        stops = route.get("stops", [])
        if not stops:
            continue
        
        vehicle_idx = route.get("vehicleId", 0)
        vehicle_str = route.get("vehicleIdStr", f"V{vehicle_idx:02d}")
        vehicle_info = vehicle_map.get(vehicle_idx, {})
        
        lines.append("")
        lines.append(f"┌─ Vehicle: {vehicle_str}")
        if vehicle_info:
            lines.append(f"│  Type: {vehicle_info.get('vehicle_type', 'N/A')} | Fuel: {vehicle_info.get('fuel_type', 'N/A')} | Cost: {vehicle_info.get('cost_per_km', 'N/A')}/km")
        lines.append(f"│  Distance: {route.get('totalDist', 0):.2f} km | Cost: {route.get('totalCost', 0):.2f}")
        lines.append("│  Stops:")
        
        for i, stop in enumerate(stops, 1):
            stop_type = stop.get("type", "?").upper()[:1]
            emp_id = stop.get("employeeId", "?")
            arr_time = minutes_to_time(stop.get("arrivalTime", 0))
            lines.append(f"│    {i}. [{stop_type}] {emp_id} @ {arr_time}")
        
        lines.append("└" + "─" * 60)
    
    # Quick reference table
    employee_assignments = {}
    for route in routes:
        vehicle_str = route.get("vehicleIdStr", f"V{route.get('vehicleId', 0):02d}")
        for stop in route.get("stops", []):
            emp_id = stop.get("employeeId")
            if emp_id not in employee_assignments:
                employee_assignments[emp_id] = {"vehicle": vehicle_str, "pickup": None, "dropoff": None, "req_id": stop.get("reqId")}
            if stop.get("type") == "pickup":
                employee_assignments[emp_id]["pickup"] = stop.get("arrivalTime")
            elif stop.get("type") == "dropoff":
                employee_assignments[emp_id]["dropoff"] = stop.get("arrivalTime")
    
    lines.append("")
    lines.append("-" * 80)
    lines.append("QUICK REFERENCE TABLE")
    lines.append("-" * 80)
    lines.append("")
    lines.append(f"{'Emp':<6} {'Veh':<5} {'Base$':<8} {'Opt$':<8} {'Save$':<8} {'Status':<10}")
    lines.append("-" * 50)
    
    total_opt = 0
    for emp_id, info in sorted(employee_assignments.items()):
        baseline = baseline_map.get(emp_id, {})
        baseline_cost = baseline.get("cost", 0)
        opt_cost = employee_shared_costs.get(emp_id, 0)
        total_opt += opt_cost
        save = baseline_cost - opt_cost
        
        req_id = info.get("req_id")
        req = request_map.get(req_id, {})
        late_time = req.get("lateTime", 1440)
        dropoff = info.get("dropoff", 0) or 0
        
        status = "On-time" if dropoff <= late_time else ("Delay" if dropoff <= late_time + 15 else "LATE")
        
        lines.append(f"{emp_id:<6} {info['vehicle']:<5} {baseline_cost:<8.0f} {opt_cost:<8.1f} {save:<8.1f} {status:<10}")
    
    lines.append("-" * 50)
    total_baseline = sum(baseline_map.get(e, {}).get("cost", 0) for e in employee_assignments)
    lines.append(f"{'TOTAL':<6} {'':<5} {total_baseline:<8.0f} {total_opt:<8.1f} {total_baseline - total_opt:<8.1f}")
    lines.append("")
    lines.append("=" * 80)
    lines.append("END OF REPORT")
    lines.append("=" * 80)
    
    report_text = "\n".join(lines)
    
    if report_path:
        with open(report_path, 'w') as f:
            f.write(report_text)
    
    return report_text

# ============================================================================
# TEST RUNNER
# ============================================================================

def run_test_case(tc_number: int) -> bool:
    """Run a single test case through the full pipeline."""
    tc_file = TC_DIR / f"TestCase_TC{tc_number:02d}.xlsx"
    
    if not tc_file.exists():
        print_error(f"Test case file not found: {tc_file}")
        return False
    
    print(f"\n📋 Running Test Case: TC{tc_number:02d}")
    print(f"   Input: {tc_file}")
    
    json_input = JSON_DIR / f"tc{tc_number:02d}_input.json"
    json_output = JSON_DIR / f"tc{tc_number:02d}_output.json"
    txt_report = DATA_DIR / f"tc{tc_number:02d}_report.txt"
    
    JSON_DIR.mkdir(parents=True, exist_ok=True)
    
    # Step 1: Convert Excel to JSON
    print("   [1/3] Converting Excel → JSON...")
    if not convert_excel_to_json(tc_file, json_input):
        return False
    print_success(f"JSON created: {json_input.name}")
    
    # Step 2: Run solver
    print("   [2/3] Running solver...")
    if not SOLVER_PATH.exists():
        print_error(f"Solver not found. Run: bash build.sh")
        return False
    
    try:
        result = subprocess.run(
            [str(SOLVER_PATH), str(json_input), str(json_output)],
            capture_output=True, text=True, timeout=120
        )
        if result.returncode != 0:
            print_error(f"Solver failed: {result.stderr}")
            return False
        
        with open(json_output) as f:
            output = json.load(f)
        
        cost = output.get('summary', {}).get('totalMoneyCost', output.get('globalCost', 0))
        penalty = output.get('summary', {}).get('totalPenaltyCost', 0)
        print_success(f"Solver complete: cost=${cost:.2f}, penalty=${penalty:.2f}")
        
    except subprocess.TimeoutExpired:
        print_error("Solver timed out (>120s)")
        return False
    except Exception as e:
        print_error(f"Solver error: {e}")
        return False
    
    # Step 3: Generate report
    print("   [3/3] Generating report...")
    generate_report(json_output, json_input, txt_report)
    print_success(f"Report: {txt_report.name}")
    
    return True

def run_all_test_cases():
    """Run all available test cases."""
    tc_files = list(TC_DIR.glob("TestCase_TC*.xlsx"))
    if not tc_files:
        print_error(f"No test cases found in {TC_DIR}")
        return
    
    tc_numbers = []
    for f in tc_files:
        try:
            num = int(f.stem.replace("TestCase_TC", ""))
            tc_numbers.append(num)
        except:
            pass
    
    tc_numbers.sort()
    print_header(f"Running {len(tc_numbers)} Test Cases")
    
    results = []
    for tc in tc_numbers:
        success = run_test_case(tc)
        results.append((tc, success))
    
    print_header("Summary")
    for tc, success in results:
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"  TC{tc:02d}: {status}")

# ============================================================================
# BENCHMARKING
# ============================================================================

@dataclass
class BenchmarkResult:
    test_case: str
    employees: int
    vehicles_used: int
    vehicles_available: int
    baseline_cost: float
    optimized_cost: float
    savings: float
    savings_pct: float
    on_time: int
    delay: int
    late: int

def run_benchmark(test_cases: List[int] = None, save: bool = False, output_format: str = "console") -> None:
    """Run benchmarks on test cases."""
    if test_cases is None:
        test_cases = [1, 2, 3, 4]
    
    results = []
    
    for tc in test_cases:
        input_file = JSON_DIR / f"tc{tc:02d}_input.json"
        output_file = JSON_DIR / f"tc{tc:02d}_output.json"
        
        if not input_file.exists() or not output_file.exists():
            continue
        
        with open(input_file) as f:
            input_data = json.load(f)
        with open(output_file) as f:
            output_data = json.load(f)
        
        # Build maps
        vehicle_map = {v['id']: {'cost_per_km': v.get('costPerKm', 10)} for v in input_data.get('vehicles', [])}
        baseline_map = {b['employee_id']: b for b in input_data.get('baseline', [])}
        request_map = {r['id']: r for r in input_data.get('requests', [])}
        
        routes = output_data.get('routes', [])
        summary = output_data.get('summary', {})
        
        # Calculate shared costs
        employee_costs = calculate_shared_costs(routes, vehicle_map)
        
        # Count statuses
        on_time = delay = late = 0
        for route in routes:
            for stop in route.get('stops', []):
                if stop.get('type') == 'dropoff':
                    req = request_map.get(stop.get('reqId'), {})
                    late_time = req.get('lateTime', 1440)
                    arr = stop.get('arrivalTime', 0)
                    if arr <= late_time:
                        on_time += 1
                    elif arr <= late_time + 15:
                        delay += 1
                    else:
                        late += 1
        
        total_baseline = sum(b.get('baseline_cost', 0) for b in baseline_map.values())
        total_opt = sum(employee_costs.values())
        
        results.append(BenchmarkResult(
            test_case=f"TC{tc:02d}",
            employees=len(input_data.get('requests', [])),
            vehicles_used=summary.get('vehiclesUsed', 0),
            vehicles_available=len(input_data.get('vehicles', [])),
            baseline_cost=total_baseline,
            optimized_cost=total_opt,
            savings=total_baseline - total_opt,
            savings_pct=(total_baseline - total_opt) / total_baseline * 100 if total_baseline > 0 else 0,
            on_time=on_time,
            delay=delay,
            late=late
        ))
    
    # Output
    if output_format == "json":
        output = json.dumps([r.__dict__ for r in results], indent=2)
    elif output_format == "csv":
        lines = ["test_case,employees,vehicles_used,baseline,optimized,savings,savings_pct,on_time,delay,late"]
        for r in results:
            lines.append(f"{r.test_case},{r.employees},{r.vehicles_used},{r.baseline_cost:.2f},{r.optimized_cost:.2f},{r.savings:.2f},{r.savings_pct:.2f},{r.on_time},{r.delay},{r.late}")
        output = "\n".join(lines)
    else:
        lines = []
        lines.append("")
        lines.append("=" * 90)
        lines.append("                    VELORA BENCHMARK REPORT")
        lines.append("=" * 90)
        lines.append(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        lines.append("")
        lines.append(f"{'TC':<8} {'Emp':<5} {'Veh':<8} {'Baseline':<12} {'Optimized':<12} {'Savings':<12} {'%':<8} {'Status'}")
        lines.append("-" * 90)
        
        for r in results:
            status = f"{r.on_time}✓ {r.delay}⚠ {r.late}✗"
            lines.append(f"{r.test_case:<8} {r.employees:<5} {r.vehicles_used}/{r.vehicles_available:<5} ${r.baseline_cost:<11,.0f} ${r.optimized_cost:<11,.2f} ${r.savings:<11,.2f} {r.savings_pct:<7.1f}% {status}")
        
        lines.append("-" * 90)
        
        total_base = sum(r.baseline_cost for r in results)
        total_opt = sum(r.optimized_cost for r in results)
        total_save = sum(r.savings for r in results)
        avg_pct = total_save / total_base * 100 if total_base > 0 else 0
        
        lines.append(f"{'TOTAL':<8} {sum(r.employees for r in results):<5} {'':<8} ${total_base:<11,.0f} ${total_opt:<11,.2f} ${total_save:<11,.2f} {avg_pct:<7.1f}%")
        lines.append("")
        lines.append("=" * 90)
        
        output = "\n".join(lines)
    
    if save:
        results_dir = PROJECT_ROOT / "testing_benchmarking" / "results"
        results_dir.mkdir(parents=True, exist_ok=True)
        ext = {"json": ".json", "csv": ".csv"}.get(output_format, ".txt")
        filepath = results_dir / f"benchmark_{datetime.now().strftime('%Y%m%d_%H%M%S')}{ext}"
        with open(filepath, 'w') as f:
            f.write(output)
        print(f"Results saved to: {filepath}")
    else:
        print(output)

# ============================================================================
# STATUS
# ============================================================================

def show_status():
    """Show project status."""
    print_header("Velora Mobility Optimizer - Status")
    
    # Check solver
    if check_solver():
        print_success(f"Solver built: {SOLVER_PATH}")
    else:
        print_error(f"Solver not built. Run: bash build.sh")
    
    # Check Python environment
    if check_venv():
        print_success(f"Virtual environment: {VENV_PYTHON}")
    else:
        print_warning("No virtual environment found (using system Python)")
    
    # Check test cases
    tc_files = list(TC_DIR.glob("TestCase_TC*.xlsx"))
    print_info(f"Test cases available: {len(tc_files)}")
    
    # Check outputs
    json_outputs = list(JSON_DIR.glob("tc*_output.json"))
    reports = list(DATA_DIR.glob("tc*_report.txt"))
    print_info(f"Solver outputs: {len(json_outputs)}")
    print_info(f"Reports generated: {len(reports)}")
    
    print("")

# ============================================================================
# MAIN CLI
# ============================================================================

def show_help():
    """Show detailed help."""
    help_text = """
╔══════════════════════════════════════════════════════════════════════════════╗
║                    VELORA MOBILITY OPTIMIZER - CLI TOOL                      ║
╚══════════════════════════════════════════════════════════════════════════════╝

COMMANDS:

  run [TC|all]          Run test case(s) through full pipeline
                        Examples:
                          velora.py run 1        Run TC01
                          velora.py run all      Run all test cases

  benchmark [OPTIONS]   Run benchmarks and verification
                        Options:
                          --save              Save results to file
                          --output FORMAT     Output format (console/json/csv)
                          tc01 tc02 ...       Specific test cases
                        Examples:
                          velora.py benchmark
                          velora.py benchmark --save --output json
                          velora.py benchmark tc01 tc02

  report <file.json>    Generate report from solver output JSON
                        Example:
                          velora.py report data/json/tc01_output.json

  convert <file.xlsx>   Convert Excel test case to JSON
                        Example:
                          velora.py convert "Velora Kriti_2026 TCs/TestCase_TC01.xlsx"

  status                Show project build status and available files

  help                  Show this help message

WORKFLOW:

  1. Build solver:      bash build.sh
  2. Run test case:     python velora.py run 1
  3. View report:       cat data/tc01_report.txt
  4. Run benchmarks:    python velora.py benchmark

FILES:

  Input Excel:          Velora Kriti_2026 TCs/TestCase_TC*.xlsx
  JSON Input:           data/json/tc*_input.json
  JSON Output:          data/json/tc*_output.json
  Reports:              data/tc*_report.txt
  Benchmark Results:    testing_benchmarking/results/
"""
    print(help_text)

def main():
    if len(sys.argv) < 2:
        show_help()
        return
    
    command = sys.argv[1].lower()
    
    if command == "help" or command == "--help" or command == "-h":
        show_help()
    
    elif command == "status":
        show_status()
    
    elif command == "run":
        if len(sys.argv) < 3:
            print("Usage: velora.py run [TC_NUMBER|all]")
            return
        
        arg = sys.argv[2].lower()
        if arg == "all":
            run_all_test_cases()
        else:
            try:
                tc_num = int(arg.replace("tc", ""))
                run_test_case(tc_num)
            except ValueError:
                print_error(f"Invalid test case: {arg}")
    
    elif command == "benchmark":
        # Parse benchmark arguments
        save = "--save" in sys.argv or "-s" in sys.argv
        output_format = "console"
        
        if "--output" in sys.argv:
            idx = sys.argv.index("--output")
            if idx + 1 < len(sys.argv):
                output_format = sys.argv[idx + 1]
        elif "-o" in sys.argv:
            idx = sys.argv.index("-o")
            if idx + 1 < len(sys.argv):
                output_format = sys.argv[idx + 1]
        
        # Parse test case numbers
        test_cases = []
        for arg in sys.argv[2:]:
            if arg.startswith("-"):
                continue
            if arg in ["console", "json", "csv"]:
                continue
            try:
                tc = int(arg.lower().replace("tc", ""))
                test_cases.append(tc)
            except:
                pass
        
        if not test_cases:
            test_cases = None  # Will default to [1,2,3,4]
        
        run_benchmark(test_cases, save, output_format)
    
    elif command == "report":
        if len(sys.argv) < 3:
            print("Usage: velora.py report <output.json> [report.txt]")
            return
        
        output_json = Path(sys.argv[2])
        report_path = Path(sys.argv[3]) if len(sys.argv) > 3 else None
        
        if not output_json.exists():
            print_error(f"File not found: {output_json}")
            return
        
        report = generate_report(output_json, report_path=report_path)
        if not report_path:
            print(report)
        else:
            print_success(f"Report written to: {report_path}")
    
    elif command == "convert":
        if len(sys.argv) < 3:
            print("Usage: velora.py convert <input.xlsx> [output.json]")
            return
        
        input_xlsx = Path(sys.argv[2])
        output_json = Path(sys.argv[3]) if len(sys.argv) > 3 else JSON_DIR / f"{input_xlsx.stem}.json"
        
        if not input_xlsx.exists():
            print_error(f"File not found: {input_xlsx}")
            return
        
        if convert_excel_to_json(input_xlsx, output_json):
            print_success(f"Converted to: {output_json}")
    
    else:
        print_error(f"Unknown command: {command}")
        print("Run 'python velora.py help' for usage.")

if __name__ == "__main__":
    main()
