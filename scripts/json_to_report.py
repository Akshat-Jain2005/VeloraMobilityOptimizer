#!/usr/bin/env python3
"""
JSON to Report Converter for Velora Mobility Optimizer

Converts solver JSON output to a human-readable text report.
Includes baseline comparison, vehicle details, cost sharing, and per-employee analysis.

Cost Types:
- Baseline Cost: What the employee would pay individually (Ola/Uber/Rapido prices)
- Optimized Cost: Employee's share of the shared ride cost
- CTC (Cost to Company): Total operational cost for the company

When employees share a ride, the cost for each segment is divided among passengers.
"""

import json
import sys
import math
from datetime import datetime, timedelta
from pathlib import Path


def minutes_to_time(minutes: float) -> str:
    """Convert minutes from midnight to HH:MM format."""
    if minutes is None or minutes <= 0:
        return "N/A"
    hours = int(minutes // 60)
    mins = int(minutes % 60)
    return f"{hours:02d}:{mins:02d}"


def haversine_distance(lat1, lon1, lat2, lon2):
    """
    Calculate road distance between two points in km.
    
    Uses Haversine formula for great-circle distance, then applies 1.4x road factor
    to approximate actual road distance (roads are not straight lines).
    
    This MUST match the solver's distance calculation (MapDistance fallback).
    If solver uses real API, this will still be used for report estimates.
    """
    R = 6371.0  # Earth radius in km
    lat1_rad = math.radians(lat1)
    lat2_rad = math.radians(lat2)
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = math.sin(dlat/2)**2 + math.cos(lat1_rad) * math.cos(lat2_rad) * math.sin(dlon/2)**2
    c = 2 * math.asin(min(1.0, math.sqrt(a)))
    return R * c * 1.4  # 1.4x road factor - MUST match solver's MapDistance


def calculate_shared_costs(routes, vehicle_map, request_map):
    """
    Calculate per-employee cost with proper sharing.
    
    Logic: For each segment of the route, divide the segment cost by the number
    of passengers in the vehicle during that segment.
    
    Returns: dict mapping employee_id -> their_share_of_cost
    """
    employee_costs = {}
    
    for route in routes:
        stops = route.get("stops", [])
        if len(stops) < 2:
            continue
        
        vehicle_idx = route.get("vehicleId", 0)
        vehicle_info = vehicle_map.get(vehicle_idx, {})
        cost_per_km = vehicle_info.get("cost_per_km", 10)
        
        # Track who is in the vehicle at each point
        passengers_in_vehicle = set()
        
        for i in range(len(stops)):
            stop = stops[i]
            emp_id = stop.get("employeeId")
            stop_type = stop.get("type")
            
            if stop_type == "pickup":
                passengers_in_vehicle.add(emp_id)
            
            # Calculate segment cost to NEXT stop (if exists)
            if i < len(stops) - 1:
                next_stop = stops[i + 1]
                
                # Distance from this stop to next
                dist = haversine_distance(
                    stop.get("lat", 0), stop.get("lon", 0),
                    next_stop.get("lat", 0), next_stop.get("lon", 0)
                )
                
                segment_cost = dist * cost_per_km
                
                # Divide segment cost among passengers currently in vehicle
                if passengers_in_vehicle:
                    cost_per_passenger = segment_cost / len(passengers_in_vehicle)
                    for passenger in passengers_in_vehicle:
                        if passenger not in employee_costs:
                            employee_costs[passenger] = 0
                        employee_costs[passenger] += cost_per_passenger
            
            if stop_type == "dropoff":
                passengers_in_vehicle.discard(emp_id)
    
    return employee_costs


def generate_report(output_json_path: str, input_json_path: str = None, report_path: str = None):
    """Generate a detailed text report from solver JSON output."""
    
    with open(output_json_path, 'r') as f:
        output_data = json.load(f)
    
    # Try to find and load the corresponding input JSON for baseline data
    input_data = None
    if input_json_path and Path(input_json_path).exists():
        with open(input_json_path, 'r') as f:
            input_data = json.load(f)
    else:
        # Try to infer input path from output path
        output_path = Path(output_json_path)
        possible_input = output_path.parent / output_path.name.replace('_output', '_input')
        if possible_input.exists():
            with open(possible_input, 'r') as f:
                input_data = json.load(f)
    
    lines = []
    lines.append("=" * 80)
    lines.append("              VELORA MOBILITY OPTIMIZER - SOLUTION REPORT")
    lines.append("=" * 80)
    lines.append(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    lines.append(f"Output file: {output_json_path}")
    if input_data:
        lines.append(f"Input file: {input_json_path or 'auto-detected'}")
    lines.append("")
    
    # Build lookup tables from input data
    baseline_map = {}  # employee_id -> {cost, time}
    vehicle_map = {}   # vehicle_id (int) -> vehicle details
    request_map = {}   # req_id -> request details from input
    
    if input_data:
        # Baseline data (market pricing - Ola/Uber/Rapido)
        for b in input_data.get("baseline", []):
            emp_id = b.get("employee_id", "")
            baseline_map[emp_id] = {
                "cost": b.get("baseline_cost", 0),
                "time": b.get("baseline_time_min", 0)
            }
        
        # Vehicle details
        for v in input_data.get("vehicles", []):
            vehicle_map[v.get("id")] = {
                "vehicle_id": v.get("vehicle_id", ""),
                "fuel_type": v.get("fuel_type", "unknown"),
                "vehicle_type": v.get("vehicle_type", v.get("type", "unknown")),
                "capacity": v.get("capacity", 0),
                "cost_per_km": v.get("costPerKm", 0),
                "speed": v.get("avg_speed_kmph", 30),
                "category": v.get("category", ""),
                "start_lat": v.get("startLoc", {}).get("lat", 0),
                "start_lon": v.get("startLoc", {}).get("lon", 0)
            }
        
        # Request details from input
        for r in input_data.get("requests", []):
            request_map[r.get("id")] = {
                "employee_id": r.get("employee_id", ""),
                "priority": r.get("priority", 3),
                "early_time": r.get("earlyTime", 0),
                "late_time": r.get("lateTime", 1440),
                "vehicle_pref": r.get("vehiclePreference", "any"),
                "sharing_limit": r.get("sharingLimit", 100),
                "pickup": r.get("pickup", {}),
                "dropoff": r.get("dropoff", {})
            }
    
    # Request details from output
    output_request_map = {}
    for req in output_data.get("requestDetails", []):
        output_request_map[req.get("id")] = req
    
    routes = output_data.get("routes", [])
    
    # Calculate shared costs per employee
    employee_shared_costs = calculate_shared_costs(routes, vehicle_map, request_map)
    
    # Summary section
    summary = output_data.get("summary", {})
    ctc = summary.get('totalMoneyCost', 0)  # Cost to Company
    
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
    
    # Baseline comparison if available
    if baseline_map:
        total_baseline_cost = sum(b["cost"] for b in baseline_map.values())
        total_baseline_time = sum(b["time"] for b in baseline_map.values())
        savings = total_baseline_cost - ctc
        savings_pct = (savings / total_baseline_cost * 100) if total_baseline_cost > 0 else 0
        lines.append("")
        lines.append(f"  === COST COMPARISON (vs Individual Cabs) ===")
        lines.append(f"  Total Baseline Cost:       {total_baseline_cost:,.2f} (Ola/Uber/Rapido prices)")
        lines.append(f"  Total Baseline Time:       {total_baseline_time:,.0f} min (sum of individual trips)")
        lines.append(f"  Optimized CTC:             {ctc:,.2f}")
        lines.append(f"  Net Savings:               {savings:,.2f} ({savings_pct:.1f}%)")
    lines.append("")
    
    # Routes section
    active_routes = [r for r in routes if r.get("stops")]
    
    lines.append("-" * 80)
    lines.append(f"VEHICLE ROUTES ({len(active_routes)} active vehicles)")
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
            lines.append(f"│  Type: {vehicle_info.get('vehicle_type', 'N/A')} | Fuel: {vehicle_info.get('fuel_type', 'N/A')} | Category: {vehicle_info.get('category', 'N/A')}")
            lines.append(f"│  Capacity: {vehicle_info.get('capacity', 'N/A')} | Speed: {vehicle_info.get('speed', 'N/A')} km/h | Cost: {vehicle_info.get('cost_per_km', 'N/A')}/km")
            lines.append(f"│  Start Location: ({vehicle_info.get('start_lat', 0):.4f}, {vehicle_info.get('start_lon', 0):.4f})")
        lines.append(f"│  Route Distance: {route.get('totalDist', 0):.2f} km | Route Time: {route.get('totalTime', 0):.1f} min")
        lines.append(f"│  Route Cost (CTC contribution): {route.get('totalCost', 0):.2f}")
        lines.append("│")
        lines.append("│  Stops:")
        lines.append("│  " + "-" * 74)
        lines.append(f"│  {'#':<3} {'Type':<8} {'Employee':<10} {'Time':<7} {'Wait':<6} {'Location':<25}")
        lines.append("│  " + "-" * 74)
        
        for i, stop in enumerate(stops, 1):
            stop_type = stop.get("type", "?").capitalize()
            emp_id = stop.get("employeeId", f"Req{stop.get('reqId')}")
            arr_time = minutes_to_time(stop.get("arrivalTime", 0))
            wait_time = f"{stop.get('waitTime', 0):.0f}m" if stop.get('waitTime', 0) > 0 else "-"
            lat, lon = stop.get("lat", 0), stop.get("lon", 0)
            loc = f"({lat:.4f}, {lon:.4f})"
            
            lines.append(f"│  {i:<3} {stop_type:<8} {emp_id:<10} {arr_time:<7} {wait_time:<6} {loc:<25}")
        
        lines.append("└" + "─" * 79)
    
    # Build employee -> assignment mapping
    employee_assignments = {}
    for route in routes:
        vehicle_idx = route.get("vehicleId", 0)
        vehicle_str = route.get("vehicleIdStr", f"V{vehicle_idx:02d}")
        vehicle_info = vehicle_map.get(vehicle_idx, {})
        
        for stop in route.get("stops", []):
            emp_id = stop.get("employeeId", f"Req{stop.get('reqId')}")
            req_id = stop.get("reqId")
            
            if emp_id not in employee_assignments:
                employee_assignments[emp_id] = {
                    "vehicle": vehicle_str,
                    "vehicle_idx": vehicle_idx,
                    "vehicle_info": vehicle_info,
                    "req_id": req_id,
                    "pickup_time": None,
                    "dropoff_time": None,
                    "pickup_loc": None,
                    "dropoff_loc": None
                }
            
            if stop.get("type") == "pickup":
                employee_assignments[emp_id]["pickup_time"] = stop.get("arrivalTime")
                employee_assignments[emp_id]["pickup_loc"] = (stop.get("lat"), stop.get("lon"))
            elif stop.get("type") == "dropoff":
                employee_assignments[emp_id]["dropoff_time"] = stop.get("arrivalTime")
                employee_assignments[emp_id]["dropoff_loc"] = (stop.get("lat"), stop.get("lon"))
    
    # Detailed Employee Assignment Section
    lines.append("")
    lines.append("-" * 80)
    lines.append("DETAILED EMPLOYEE ASSIGNMENTS")
    lines.append("-" * 80)
    
    # Check for unfeasible assignments
    unfeasible_employees = []
    
    for emp_id, info in sorted(employee_assignments.items()):
        req_id = info.get("req_id")
        req_info = request_map.get(req_id, output_request_map.get(req_id, {}))
        baseline = baseline_map.get(emp_id, {})
        vehicle_info = info.get("vehicle_info", {})
        
        pickup_time = info.get("pickup_time")
        dropoff_time = info.get("dropoff_time")
        pickup_loc = info.get("pickup_loc")
        dropoff_loc = info.get("dropoff_loc")
        
        # Check for unfeasibility
        is_unfeasible = False
        unfeasibility_reason = ""
        
        if pickup_time is None or dropoff_time is None:
            is_unfeasible = True
            unfeasibility_reason = "Missing pickup or dropoff"
        elif dropoff_time < pickup_time:
            is_unfeasible = True
            unfeasibility_reason = "Dropoff occurs before pickup (SOLVER BUG)"
        elif dropoff_time <= 0:
            is_unfeasible = True
            unfeasibility_reason = "Invalid dropoff time"
        
        if is_unfeasible:
            unfeasible_employees.append((emp_id, unfeasibility_reason))
            continue
        
        # Calculate metrics
        # Optimized Time = Time employee spends in vehicle (includes detours for other passengers)
        optimized_time = (dropoff_time - pickup_time) if pickup_time and dropoff_time else 0
        
        # Road distance (pickup to dropoff, using Haversine * 1.4 road factor)
        if pickup_loc and dropoff_loc:
            direct_distance = haversine_distance(pickup_loc[0], pickup_loc[1], dropoff_loc[0], dropoff_loc[1])
        else:
            direct_distance = 0
        
        # Optimized cost = their share of shared ride cost
        optimized_cost = employee_shared_costs.get(emp_id, 0)
        
        # Baseline values (individual cab)
        baseline_cost = baseline.get("cost", 0)
        baseline_time = baseline.get("time", 0)
        
        # Employee's savings
        emp_savings = baseline_cost - optimized_cost
        emp_savings_pct = (emp_savings / baseline_cost * 100) if baseline_cost > 0 else 0
        
        lines.append("")
        lines.append(f"  Employee: {emp_id}")
        lines.append(f"  ├─ Priority: P{req_info.get('priority', '?')}")
        lines.append(f"  ├─ Time Window: {minutes_to_time(req_info.get('earlyTime', req_info.get('early_time', 0)))} - {minutes_to_time(req_info.get('lateTime', req_info.get('late_time', 0)))}")
        lines.append(f"  ├─ Vehicle Preference: {req_info.get('vehiclePreference', req_info.get('vehicle_pref', 'any'))}")
        lines.append(f"  ├─ Sharing Preference: Max {req_info.get('sharingLimit', req_info.get('sharing_limit', 'any'))} passengers")
        lines.append(f"  │")
        lines.append(f"  ├─ Assigned Vehicle: {info.get('vehicle')}")
        if vehicle_info:
            lines.append(f"  │  └─ {vehicle_info.get('vehicle_type', 'N/A')} | {vehicle_info.get('fuel_type', 'N/A')} | {vehicle_info.get('category', 'N/A')}")
        lines.append(f"  │")
        lines.append(f"  ├─ Pickup Time: {minutes_to_time(pickup_time)}")
        lines.append(f"  ├─ Dropoff Time: {minutes_to_time(dropoff_time)}")
        lines.append(f"  ├─ Road Distance: {direct_distance:.2f} km (pickup → dropoff)")
        lines.append(f"  │")
        
        # Check if on-time
        late_time = req_info.get("lateTime", req_info.get("late_time", 1440))
        if dropoff_time and dropoff_time <= late_time:
            status = "✓ ON-TIME"
        elif dropoff_time and dropoff_time <= late_time + 15:
            status = "⚠ MINOR DELAY"
        else:
            delay = (dropoff_time - late_time) if dropoff_time else 0
            status = f"✗ LATE by {delay:.0f} min"
        lines.append(f"  ├─ Status: {status}")
        lines.append(f"  │")
        
        # Cost and Time comparison
        lines.append(f"  ├─ BASELINE (Individual Cab - Ola/Uber/Rapido):")
        lines.append(f"  │  ├─ Cost: {baseline_cost:.2f}")
        lines.append(f"  │  └─ Time: {baseline_time:.0f} min")
        lines.append(f"  │")
        lines.append(f"  └─ OPTIMIZED (Shared Ride):")
        lines.append(f"     ├─ Cost: {optimized_cost:.2f} (shared)")
        lines.append(f"     ├─ Time: {optimized_time:.0f} min (includes shared ride detours)")
        lines.append(f"     └─ Savings: {emp_savings:.2f} ({emp_savings_pct:.1f}%)")
    
    # Unfeasible employees section
    if unfeasible_employees:
        lines.append("")
        lines.append("-" * 80)
        lines.append("⚠⚠⚠ UNFEASIBLE ASSIGNMENTS (ERRORS) ⚠⚠⚠")
        lines.append("-" * 80)
        for emp_id, reason in unfeasible_employees:
            req_id = employee_assignments.get(emp_id, {}).get("req_id")
            req_info = request_map.get(req_id, output_request_map.get(req_id, {}))
            baseline = baseline_map.get(emp_id, {})
            
            lines.append("")
            lines.append(f"  ❌ Employee: {emp_id}")
            lines.append(f"     Reason: {reason}")
            lines.append(f"     Priority: P{req_info.get('priority', '?')}")
            lines.append(f"     Time Window: {minutes_to_time(req_info.get('earlyTime', req_info.get('early_time', 0)))} - {minutes_to_time(req_info.get('lateTime', req_info.get('late_time', 0)))}")
            if baseline:
                lines.append(f"     Baseline Cost: {baseline.get('cost', 0)} | Baseline Time: {baseline.get('time', 0)} min")
            lines.append(f"     ACTION REQUIRED: This employee needs manual assignment or constraint relaxation!")
    
    # Unassigned requests
    unassigned = output_data.get("unassigned", [])
    if unassigned:
        lines.append("")
        lines.append("-" * 80)
        lines.append(f"⚠ UNASSIGNED EMPLOYEES ({len(unassigned)})")
        lines.append("-" * 80)
        lines.append("")
        lines.append("  The following employees could NOT be assigned to any vehicle:")
        lines.append("  This may be due to insufficient vehicles, capacity, or time constraints.")
        lines.append("")
        
        for req_id in unassigned:
            req_info = request_map.get(req_id, output_request_map.get(req_id, {}))
            emp_id = req_info.get("employeeId", req_info.get("employee_id", f"Request {req_id}"))
            baseline = baseline_map.get(emp_id, {})
            
            lines.append(f"  ❌ {emp_id}")
            lines.append(f"     Priority: P{req_info.get('priority', '?')}")
            lines.append(f"     Time Window: {minutes_to_time(req_info.get('earlyTime', req_info.get('early_time', 0)))} - {minutes_to_time(req_info.get('lateTime', req_info.get('late_time', 0)))}")
            lines.append(f"     Vehicle Preference: {req_info.get('vehiclePreference', req_info.get('vehicle_pref', 'any'))}")
            if baseline:
                lines.append(f"     Baseline Cost: {baseline.get('cost', 0)} | Baseline Time: {baseline.get('time', 0)} min")
            lines.append(f"     STATUS: ABSOLUTELY UNFEASIBLE - Manual intervention required!")
            lines.append("")
    
    # Summary table
    lines.append("")
    lines.append("-" * 80)
    lines.append("QUICK REFERENCE TABLE")
    lines.append("-" * 80)
    lines.append("")
    header = f"{'Emp':<6} {'Veh':<5} {'Type':<5} {'Fuel':<7} {'Base$':<8} {'Opt$':<8} {'Save$':<8} {'BaseT':<6} {'OptT':<6} {'Status':<10}"
    lines.append(header)
    lines.append("-" * len(header))
    
    for emp_id, info in sorted(employee_assignments.items()):
        vehicle_info = info.get("vehicle_info", {})
        pickup_time = info.get("pickup_time")
        dropoff_time = info.get("dropoff_time")
        
        # Skip unfeasible for this table
        if pickup_time is None or dropoff_time is None or dropoff_time < pickup_time or dropoff_time <= 0:
            continue
        
        optimized_time = (dropoff_time - pickup_time) if pickup_time and dropoff_time else 0
        optimized_cost = employee_shared_costs.get(emp_id, 0)
        
        baseline = baseline_map.get(emp_id, {})
        baseline_cost = baseline.get("cost", 0)
        baseline_time = baseline.get("time", 0)
        emp_savings = baseline_cost - optimized_cost
        
        req_id = info.get("req_id")
        req_info = request_map.get(req_id, output_request_map.get(req_id, {}))
        late_time = req_info.get("lateTime", req_info.get("late_time", 1440))
        
        if dropoff_time <= late_time:
            status = "On-time"
        elif dropoff_time <= late_time + 15:
            status = "Delay"
        else:
            status = "LATE"
        
        v_type = vehicle_info.get('vehicle_type', 'N/A')[:4]
        fuel = vehicle_info.get('fuel_type', 'N/A')[:6]
        
        lines.append(f"{emp_id:<6} {info.get('vehicle', 'N/A'):<5} {v_type:<5} {fuel:<7} {baseline_cost:<8.0f} {optimized_cost:<8.1f} {emp_savings:<8.1f} {baseline_time:<6.0f} {optimized_time:<6.0f} {status:<10}")
    
    # Add unfeasible to table
    for emp_id, reason in unfeasible_employees:
        baseline = baseline_map.get(emp_id, {})
        baseline_cost = baseline.get("cost", 0)
        baseline_time = baseline.get("time", 0)
        lines.append(f"{emp_id:<6} {'ERR':<5} {'-':<5} {'-':<7} {baseline_cost:<8.0f} {'N/A':<8} {'N/A':<8} {baseline_time:<6.0f} {'N/A':<6} {'UNFEASIBLE':<10}")
    
    # Add unassigned to table
    for req_id in unassigned:
        req_info = request_map.get(req_id, output_request_map.get(req_id, {}))
        emp_id = req_info.get("employeeId", req_info.get("employee_id", f"Req{req_id}"))
        baseline = baseline_map.get(emp_id, {})
        baseline_cost = baseline.get("cost", 0)
        baseline_time = baseline.get("time", 0)
        lines.append(f"{emp_id:<6} {'NONE':<5} {'-':<5} {'-':<7} {baseline_cost:<8.0f} {'N/A':<8} {'N/A':<8} {baseline_time:<6.0f} {'N/A':<6} {'UNASSIGNED':<10}")
    
    # Final totals
    lines.append("-" * len(header))
    total_baseline = sum(baseline_map.get(e, {}).get("cost", 0) for e in employee_assignments)
    total_optimized = sum(employee_shared_costs.get(e, 0) for e in employee_assignments if e not in dict(unfeasible_employees))
    total_savings = total_baseline - total_optimized
    lines.append(f"{'TOTAL':<6} {'':<5} {'':<5} {'':<7} {total_baseline:<8.0f} {total_optimized:<8.1f} {total_savings:<8.1f}")
    
    lines.append("")
    lines.append("=" * 80)
    lines.append("NOTES:")
    lines.append("- Base$ = Baseline cost (individual cab like Ola/Uber/Rapido)")
    lines.append("- Opt$ = Optimized cost (employee's share of shared ride)")
    lines.append("- Save$ = Savings per employee (Base$ - Opt$)")
    lines.append("- BaseT = Baseline time (individual cab)")
    lines.append("- OptT = Optimized time (may be higher due to shared ride detours)")
    lines.append("- CTC = Cost to Company = Total operational cost")
    lines.append("=" * 80)
    lines.append("END OF REPORT")
    lines.append("=" * 80)
    
    report_text = "\n".join(lines)
    
    # Write or print
    if report_path:
        with open(report_path, 'w') as f:
            f.write(report_text)
        print(f"Report written to: {report_path}")
    else:
        print(report_text)
    
    return report_text


def main():
    if len(sys.argv) < 2:
        print("Usage: python json_to_report.py <output.json> [report.txt]")
        print("  The script will auto-detect the corresponding input JSON for baseline data.")
        sys.exit(1)
    
    output_json_path = sys.argv[1]
    report_path = sys.argv[2] if len(sys.argv) > 2 else None
    
    if not Path(output_json_path).exists():
        print(f"Error: File not found: {output_json_path}")
        sys.exit(1)
    
    generate_report(output_json_path, report_path=report_path)


if __name__ == "__main__":
    main()
