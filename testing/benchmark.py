#!/usr/bin/env python3
"""
Velora Mobility Optimizer - Benchmarking & Verification Tool

This tool provides comprehensive benchmarking and verification for the
optimization solver outputs against input specifications.

Features:
- Verifies all calculations in reports against input/output JSON files
- Benchmarks solver performance across test cases
- Generates detailed metrics and comparisons
- Validates time windows, costs, and route feasibility
- Outputs results in multiple formats (console, JSON, CSV)

Usage:
    python benchmark.py                    # Run all test cases
    python benchmark.py tc01               # Run specific test case
    python benchmark.py --output json      # Output as JSON
    python benchmark.py --save             # Save results to file
"""

import json
import math
import sys
import argparse
from datetime import datetime
from pathlib import Path
from dataclasses import dataclass, field, asdict
from typing import Dict, List, Optional, Tuple
import csv


# ============================================================================
# DATA CLASSES
# ============================================================================

@dataclass
class EmployeeMetrics:
    """Metrics for a single employee."""
    employee_id: str
    vehicle_id: str
    baseline_cost: float
    optimized_cost: float
    savings: float
    savings_pct: float
    baseline_time: int
    optimized_time: float
    pickup_time: float
    dropoff_time: float
    early_time: float
    late_time: float
    delay_minutes: float
    status: str  # "on-time", "delay", "late"
    priority: int
    distance_km: float


@dataclass
class VehicleMetrics:
    """Metrics for a single vehicle."""
    vehicle_id: str
    vehicle_type: str
    fuel_type: str
    capacity: int
    cost_per_km: float
    total_distance: float
    total_cost: float
    total_time: float
    stops_count: int
    passengers_served: int
    utilization_pct: float


@dataclass
class TestCaseMetrics:
    """Comprehensive metrics for a test case."""
    test_case: str
    timestamp: str
    
    # Summary metrics
    total_employees: int
    total_vehicles_available: int
    vehicles_used: int
    unassigned_count: int
    
    # Cost metrics
    total_baseline_cost: float
    total_optimized_cost: float
    ctc_cost: float  # Cost to Company
    total_savings: float
    savings_percentage: float
    
    # Time metrics
    total_baseline_time: int
    total_optimized_time: float
    total_distance_km: float
    
    # Penalty metrics
    total_penalty_cost: float
    global_objective: float
    
    # Status counts
    on_time_count: int
    delay_count: int
    late_count: int
    
    # Detailed metrics
    employee_metrics: List[EmployeeMetrics] = field(default_factory=list)
    vehicle_metrics: List[VehicleMetrics] = field(default_factory=list)
    
    # Validation
    is_valid: bool = True
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)


@dataclass
class BenchmarkSummary:
    """Summary across all test cases."""
    timestamp: str
    test_cases: List[TestCaseMetrics]
    
    # Aggregates
    total_employees_all: int = 0
    total_baseline_all: float = 0
    total_optimized_all: float = 0
    total_savings_all: float = 0
    avg_savings_pct: float = 0
    
    # Best/Worst performers
    best_savings_tc: str = ""
    best_savings_pct: float = 0
    worst_savings_tc: str = ""
    worst_savings_pct: float = 100


# ============================================================================
# UTILITY FUNCTIONS
# ============================================================================

def haversine_distance(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """
    Calculate road distance between two points in km.
    Uses Haversine formula with 1.4x road factor to approximate actual road distance.
    """
    R = 6371.0  # Earth radius in km
    lat1_rad = math.radians(lat1)
    lat2_rad = math.radians(lat2)
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = math.sin(dlat/2)**2 + math.cos(lat1_rad)*math.cos(lat2_rad)*math.sin(dlon/2)**2
    c = 2 * math.asin(min(1.0, math.sqrt(a)))
    return R * c * 1.4  # 1.4x road factor - matches solver's MapDistance


def minutes_to_time(minutes: float) -> str:
    """Convert minutes from midnight to HH:MM format."""
    if minutes is None or minutes <= 0:
        return "N/A"
    hours = int(minutes // 60)
    mins = int(minutes % 60)
    return f"{hours:02d}:{mins:02d}"


def format_currency(value: float) -> str:
    """Format value as currency."""
    return f"${value:,.2f}"


def format_percentage(value: float) -> str:
    """Format value as percentage."""
    return f"{value:.1f}%"


# ============================================================================
# CORE BENCHMARKING LOGIC
# ============================================================================

class Benchmarker:
    """Main benchmarking class."""
    
    def __init__(self, base_path: Path):
        self.base_path = base_path
        self.data_path = base_path / "data"
        self.json_path = base_path / "data" / "json"
    
    def calculate_shared_costs(self, routes: List[dict], vehicle_map: dict) -> Dict[str, float]:
        """
        Calculate per-employee cost with proper sharing.
        
        For each segment of the route, divide the segment cost by the number
        of passengers in the vehicle during that segment.
        """
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
                
                # Update passengers BEFORE calculating segment cost
                if stop_type == "pickup":
                    passengers_in_vehicle.add(emp_id)
                elif stop_type == "dropoff":
                    passengers_in_vehicle.discard(emp_id)
                
                # Calculate segment cost to NEXT stop
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
                            if passenger not in employee_costs:
                                employee_costs[passenger] = 0
                            employee_costs[passenger] += cost_per_passenger
        
        return employee_costs
    
    def benchmark_test_case(self, tc_num: int) -> Optional[TestCaseMetrics]:
        """Run benchmark for a single test case."""
        tc_id = f"tc{tc_num:02d}"
        
        input_file = self.json_path / f"{tc_id}_input.json"
        output_file = self.json_path / f"{tc_id}_output.json"
        
        if not input_file.exists() or not output_file.exists():
            return None
        
        with open(input_file) as f:
            input_data = json.load(f)
        with open(output_file) as f:
            output_data = json.load(f)
        
        # Build lookup maps
        vehicle_map = {}
        for v in input_data.get("vehicles", []):
            vehicle_map[v.get("id")] = {
                "vehicle_id": v.get("vehicle_id", f"V{v.get('id'):02d}"),
                "fuel_type": v.get("fuel_type", "unknown"),
                "vehicle_type": v.get("vehicle_type", v.get("type", "unknown")),
                "capacity": v.get("capacity", 0),
                "cost_per_km": v.get("costPerKm", 0),
                "speed": v.get("avg_speed_kmph", 30),
                "category": v.get("category", ""),
            }
        
        request_map = {}
        for r in input_data.get("requests", []):
            request_map[r.get("id")] = {
                "employee_id": r.get("employee_id", ""),
                "priority": r.get("priority", 3),
                "early_time": r.get("earlyTime", 0),
                "late_time": r.get("lateTime", 1440),
                "pickup": r.get("pickup", {}),
                "dropoff": r.get("dropoff", {})
            }
        
        baseline_map = {}
        for b in input_data.get("baseline", []):
            baseline_map[b.get("employee_id", "")] = {
                "cost": b.get("baseline_cost", 0),
                "time": b.get("baseline_time_min", 0)
            }
        
        routes = output_data.get("routes", [])
        summary = output_data.get("summary", {})
        
        # Calculate shared costs
        employee_shared_costs = self.calculate_shared_costs(routes, vehicle_map)
        
        # Build employee assignments
        employee_assignments = {}
        for route in routes:
            vehicle_idx = route.get("vehicleId", 0)
            vehicle_str = route.get("vehicleIdStr", f"V{vehicle_idx:02d}")
            
            for stop in route.get("stops", []):
                emp_id = stop.get("employeeId")
                req_id = stop.get("reqId")
                
                if emp_id not in employee_assignments:
                    employee_assignments[emp_id] = {
                        "vehicle": vehicle_str,
                        "vehicle_idx": vehicle_idx,
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
        
        # Calculate employee metrics
        employee_metrics = []
        on_time = delay = late = 0
        
        for emp_id, info in sorted(employee_assignments.items()):
            req_id = info.get("req_id")
            req_info = request_map.get(req_id, {})
            baseline = baseline_map.get(emp_id, {})
            
            pickup_time = info.get("pickup_time") or 0
            dropoff_time = info.get("dropoff_time") or 0
            pickup_loc = info.get("pickup_loc")
            dropoff_loc = info.get("dropoff_loc")
            
            # Skip invalid
            if dropoff_time <= 0 or dropoff_time < pickup_time:
                continue
            
            optimized_time = dropoff_time - pickup_time
            optimized_cost = employee_shared_costs.get(emp_id, 0)
            baseline_cost = baseline.get("cost", 0)
            baseline_time = baseline.get("time", 0)
            savings = baseline_cost - optimized_cost
            savings_pct = (savings / baseline_cost * 100) if baseline_cost > 0 else 0
            
            late_time = req_info.get("late_time", 1440)
            early_time = req_info.get("early_time", 0)
            delay_minutes = max(0, dropoff_time - late_time)
            
            if dropoff_time <= late_time:
                status = "on-time"
                on_time += 1
            elif dropoff_time <= late_time + 15:
                status = "delay"
                delay += 1
            else:
                status = "late"
                late += 1
            
            distance = 0
            if pickup_loc and dropoff_loc:
                distance = haversine_distance(pickup_loc[0], pickup_loc[1], dropoff_loc[0], dropoff_loc[1])
            
            employee_metrics.append(EmployeeMetrics(
                employee_id=emp_id,
                vehicle_id=info.get("vehicle", ""),
                baseline_cost=baseline_cost,
                optimized_cost=optimized_cost,
                savings=savings,
                savings_pct=savings_pct,
                baseline_time=baseline_time,
                optimized_time=optimized_time,
                pickup_time=pickup_time,
                dropoff_time=dropoff_time,
                early_time=early_time,
                late_time=late_time,
                delay_minutes=delay_minutes,
                status=status,
                priority=req_info.get("priority", 3),
                distance_km=distance
            ))
        
        # Calculate vehicle metrics
        vehicle_metrics = []
        for route in routes:
            stops = route.get("stops", [])
            if not stops:
                continue
            
            vehicle_idx = route.get("vehicleId", 0)
            v_info = vehicle_map.get(vehicle_idx, {})
            
            passengers = set()
            for stop in stops:
                if stop.get("type") == "pickup":
                    passengers.add(stop.get("employeeId"))
            
            vehicle_metrics.append(VehicleMetrics(
                vehicle_id=route.get("vehicleIdStr", f"V{vehicle_idx:02d}"),
                vehicle_type=v_info.get("vehicle_type", "unknown"),
                fuel_type=v_info.get("fuel_type", "unknown"),
                capacity=v_info.get("capacity", 0),
                cost_per_km=v_info.get("cost_per_km", 0),
                total_distance=route.get("totalDist", 0),
                total_cost=route.get("totalCost", 0),
                total_time=route.get("totalTime", 0),
                stops_count=len(stops),
                passengers_served=len(passengers),
                utilization_pct=(len(passengers) / v_info.get("capacity", 1) * 100) if v_info.get("capacity", 1) > 0 else 0
            ))
        
        # Calculate totals
        total_baseline = sum(baseline_map.get(e, {}).get("cost", 0) for e in employee_assignments)
        total_baseline_time = sum(baseline_map.get(e, {}).get("time", 0) for e in employee_assignments)
        total_optimized = sum(employee_shared_costs.get(e, 0) for e in employee_assignments)
        total_savings = total_baseline - total_optimized
        savings_pct = (total_savings / total_baseline * 100) if total_baseline > 0 else 0
        
        return TestCaseMetrics(
            test_case=tc_id.upper(),
            timestamp=datetime.now().isoformat(),
            total_employees=len(employee_assignments),
            total_vehicles_available=len(input_data.get("vehicles", [])),
            vehicles_used=summary.get("vehiclesUsed", 0),
            unassigned_count=summary.get("unassignedCount", 0),
            total_baseline_cost=total_baseline,
            total_optimized_cost=total_optimized,
            ctc_cost=summary.get("totalMoneyCost", 0),
            total_savings=total_savings,
            savings_percentage=savings_pct,
            total_baseline_time=total_baseline_time,
            total_optimized_time=summary.get("totalTime", 0),
            total_distance_km=summary.get("totalDistance", 0),
            total_penalty_cost=summary.get("totalPenaltyCost", 0),
            global_objective=summary.get("globalCost", 0),
            on_time_count=on_time,
            delay_count=delay,
            late_count=late,
            employee_metrics=employee_metrics,
            vehicle_metrics=vehicle_metrics
        )
    
    def run_all_benchmarks(self, test_cases: List[int] = [1, 2, 3, 4, 5]) -> BenchmarkSummary:
        """Run benchmarks for all or specified test cases."""
        if test_cases is None:
            test_cases = [1, 2, 3, 4, 5]  # Default test cases
        
        results = []
        for tc in test_cases:
            metrics = self.benchmark_test_case(tc)
            if metrics:
                results.append(metrics)
        
        # Calculate aggregates
        summary = BenchmarkSummary(
            timestamp=datetime.now().isoformat(),
            test_cases=results
        )
        
        if results:
            summary.total_employees_all = sum(r.total_employees for r in results)
            summary.total_baseline_all = sum(r.total_baseline_cost for r in results)
            summary.total_optimized_all = sum(r.total_optimized_cost for r in results)
            summary.total_savings_all = sum(r.total_savings for r in results)
            summary.avg_savings_pct = (summary.total_savings_all / summary.total_baseline_all * 100) if summary.total_baseline_all > 0 else 0
            
            # Find best/worst
            best = max(results, key=lambda x: x.savings_percentage)
            worst = min(results, key=lambda x: x.savings_percentage)
            summary.best_savings_tc = best.test_case
            summary.best_savings_pct = best.savings_percentage
            summary.worst_savings_tc = worst.test_case
            summary.worst_savings_pct = worst.savings_percentage
        
        return summary


# ============================================================================
# OUTPUT FORMATTERS
# ============================================================================

class ConsoleFormatter:
    """Format benchmark results for console output."""
    
    @staticmethod
    def format_summary(summary: BenchmarkSummary) -> str:
        lines = []
        
        lines.append("")
        lines.append("=" * 100)
        lines.append("                    VELORA MOBILITY OPTIMIZER - BENCHMARK REPORT")
        lines.append("=" * 100)
        lines.append(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        lines.append("")
        
        # Overall Summary
        lines.append("─" * 100)
        lines.append("OVERALL SUMMARY")
        lines.append("─" * 100)
        lines.append(f"  Test Cases Run:        {len(summary.test_cases)}")
        lines.append(f"  Total Employees:       {summary.total_employees_all}")
        lines.append(f"  Total Baseline Cost:   {format_currency(summary.total_baseline_all)}")
        lines.append(f"  Total Optimized Cost:  {format_currency(summary.total_optimized_all)}")
        lines.append(f"  Total Savings:         {format_currency(summary.total_savings_all)} ({format_percentage(summary.avg_savings_pct)})")
        lines.append(f"  Best Performance:      {summary.best_savings_tc} ({format_percentage(summary.best_savings_pct)} savings)")
        lines.append(f"  Worst Performance:     {summary.worst_savings_tc} ({format_percentage(summary.worst_savings_pct)} savings)")
        lines.append("")
        
        # Per Test Case Summary
        lines.append("─" * 100)
        lines.append("TEST CASE COMPARISON")
        lines.append("─" * 100)
        lines.append("")
        
        header = f"{'TC':<8} {'Emp':<5} {'Veh':<8} {'Baseline':<12} {'Optimized':<12} {'Savings':<12} {'Pct':<8} {'OnTime':<8} {'Delay':<8} {'Late':<8}"
        lines.append(header)
        lines.append("-" * len(header))
        
        for tc in summary.test_cases:
            veh_str = f"{tc.vehicles_used}/{tc.total_vehicles_available}"
            lines.append(
                f"{tc.test_case:<8} "
                f"{tc.total_employees:<5} "
                f"{veh_str:<8} "
                f"${tc.total_baseline_cost:<11,.0f} "
                f"${tc.total_optimized_cost:<11,.2f} "
                f"${tc.total_savings:<11,.2f} "
                f"{tc.savings_percentage:<7.1f}% "
                f"{tc.on_time_count:<8} "
                f"{tc.delay_count:<8} "
                f"{tc.late_count:<8}"
            )
        
        lines.append("-" * len(header))
        lines.append("")
        
        # Detailed per test case
        for tc in summary.test_cases:
            lines.extend(ConsoleFormatter.format_test_case(tc))
        
        lines.append("=" * 100)
        lines.append("END OF BENCHMARK REPORT")
        lines.append("=" * 100)
        
        return "\n".join(lines)
    
    @staticmethod
    def format_test_case(tc: TestCaseMetrics) -> List[str]:
        lines = []
        
        lines.append("─" * 100)
        lines.append(f"TEST CASE: {tc.test_case}")
        lines.append("─" * 100)
        lines.append("")
        
        # Summary box
        lines.append(f"  Employees: {tc.total_employees} | Vehicles: {tc.vehicles_used}/{tc.total_vehicles_available} | Distance: {tc.total_distance_km:.2f} km")
        lines.append(f"  CTC: {format_currency(tc.ctc_cost)} | Penalty: {format_currency(tc.total_penalty_cost)} | Objective: {format_currency(tc.global_objective)}")
        lines.append(f"  Savings: {format_currency(tc.total_savings)} ({format_percentage(tc.savings_percentage)})")
        lines.append("")
        
        # Employee table
        lines.append("  EMPLOYEE METRICS:")
        emp_header = f"  {'Emp':<6} {'Veh':<5} {'P':<3} {'Baseline':<10} {'Optimized':<10} {'Savings':<10} {'%':<7} {'Status':<10} {'Delay':<8}"
        lines.append(emp_header)
        lines.append("  " + "-" * (len(emp_header) - 2))
        
        for emp in tc.employee_metrics:
            delay_str = f"{emp.delay_minutes:.0f}m" if emp.delay_minutes > 0 else "-"
            lines.append(
                f"  {emp.employee_id:<6} "
                f"{emp.vehicle_id:<5} "
                f"P{emp.priority:<2} "
                f"${emp.baseline_cost:<9,.0f} "
                f"${emp.optimized_cost:<9,.2f} "
                f"${emp.savings:<9,.2f} "
                f"{emp.savings_pct:<6.1f}% "
                f"{emp.status.upper():<10} "
                f"{delay_str:<8}"
            )
        
        lines.append("")
        
        # Vehicle table
        lines.append("  VEHICLE METRICS:")
        veh_header = f"  {'Veh':<6} {'Type':<6} {'Fuel':<8} {'Cap':<5} {'$/km':<6} {'Dist':<10} {'Cost':<10} {'Pax':<5} {'Util':<8}"
        lines.append(veh_header)
        lines.append("  " + "-" * (len(veh_header) - 2))
        
        for v in tc.vehicle_metrics:
            lines.append(
                f"  {v.vehicle_id:<6} "
                f"{v.vehicle_type[:5]:<6} "
                f"{v.fuel_type[:7]:<8} "
                f"{v.capacity:<5} "
                f"{v.cost_per_km:<6.1f} "
                f"{v.total_distance:<10.2f} "
                f"${v.total_cost:<9,.2f} "
                f"{v.passengers_served:<5} "
                f"{v.utilization_pct:<7.1f}%"
            )
        
        lines.append("")
        
        return lines


class JSONFormatter:
    """Format benchmark results as JSON."""
    
    @staticmethod
    def format_summary(summary: BenchmarkSummary) -> str:
        def convert(obj):
            if hasattr(obj, '__dict__'):
                return {k: convert(v) for k, v in obj.__dict__.items()}
            elif isinstance(obj, list):
                return [convert(i) for i in obj]
            else:
                return obj
        
        return json.dumps(convert(summary), indent=2)


class CSVFormatter:
    """Format benchmark results as CSV."""
    
    @staticmethod
    def format_employee_metrics(summary: BenchmarkSummary) -> str:
        output = []
        headers = [
            "test_case", "employee_id", "vehicle_id", "priority",
            "baseline_cost", "optimized_cost", "savings", "savings_pct",
            "baseline_time", "optimized_time", "status", "delay_minutes"
        ]
        output.append(",".join(headers))
        
        for tc in summary.test_cases:
            for emp in tc.employee_metrics:
                row = [
                    tc.test_case, emp.employee_id, emp.vehicle_id, str(emp.priority),
                    f"{emp.baseline_cost:.2f}", f"{emp.optimized_cost:.2f}",
                    f"{emp.savings:.2f}", f"{emp.savings_pct:.2f}",
                    str(emp.baseline_time), f"{emp.optimized_time:.2f}",
                    emp.status, f"{emp.delay_minutes:.2f}"
                ]
                output.append(",".join(row))
        
        return "\n".join(output)
    
    @staticmethod
    def format_summary_table(summary: BenchmarkSummary) -> str:
        output = []
        headers = [
            "test_case", "employees", "vehicles_used", "vehicles_available",
            "baseline_cost", "optimized_cost", "ctc_cost", "savings", "savings_pct",
            "on_time", "delay", "late", "distance_km", "penalty_cost"
        ]
        output.append(",".join(headers))
        
        for tc in summary.test_cases:
            row = [
                tc.test_case, str(tc.total_employees),
                str(tc.vehicles_used), str(tc.total_vehicles_available),
                f"{tc.total_baseline_cost:.2f}", f"{tc.total_optimized_cost:.2f}",
                f"{tc.ctc_cost:.2f}", f"{tc.total_savings:.2f}",
                f"{tc.savings_percentage:.2f}",
                str(tc.on_time_count), str(tc.delay_count), str(tc.late_count),
                f"{tc.total_distance_km:.2f}", f"{tc.total_penalty_cost:.2f}"
            ]
            output.append(",".join(row))
        
        return "\n".join(output)


# ============================================================================
# MAIN ENTRY POINT
# ============================================================================

def main():
    parser = argparse.ArgumentParser(
        description="Velora Mobility Optimizer - Benchmarking & Verification Tool",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python benchmark.py                    # Run all test cases, console output
  python benchmark.py tc01 tc02          # Run specific test cases
  python benchmark.py --output json      # Output as JSON
  python benchmark.py --output csv       # Output as CSV
  python benchmark.py --save             # Save results to file
  python benchmark.py --save --output json  # Save as JSON file
        """
    )
    
    parser.add_argument(
        "test_cases", nargs="*", default=[],
        help="Specific test cases to run (e.g., tc01 tc02). Runs all if not specified."
    )
    parser.add_argument(
        "--output", "-o", choices=["console", "json", "csv"], default="console",
        help="Output format (default: console)"
    )
    parser.add_argument(
        "--save", "-s", action="store_true",
        help="Save results to file instead of printing"
    )
    parser.add_argument(
        "--output-dir", default=None,
        help="Directory for output files (default: testing_benchmarking/results)"
    )
    
    args = parser.parse_args()
    
    # Determine base path
    script_path = Path(__file__).resolve()
    base_path = script_path.parent.parent  # Go up from testing_benchmarking to project root
    
    # Parse test cases
    if args.test_cases:
        test_cases = []
        for tc in args.test_cases:
            tc_lower = tc.lower()
            if tc_lower.startswith("tc"):
                try:
                    test_cases.append(int(tc_lower[2:]))
                except ValueError:
                    print(f"Warning: Invalid test case '{tc}', skipping")
            elif tc_lower.isdigit():
                test_cases.append(int(tc_lower))
            else:
                print(f"Warning: Invalid test case '{tc}', skipping")
    else:
        test_cases = [1, 2, 3, 4]  # Default
    
    # Run benchmarks
    benchmarker = Benchmarker(base_path)
    summary = benchmarker.run_all_benchmarks(test_cases)
    
    if not summary.test_cases:
        print("No valid test cases found. Ensure input/output JSON files exist in data/json/")
        sys.exit(1)
    
    # Format output
    if args.output == "json":
        output = JSONFormatter.format_summary(summary)
        ext = ".json"
    elif args.output == "csv":
        output = CSVFormatter.format_summary_table(summary)
        ext = ".csv"
    else:
        output = ConsoleFormatter.format_summary(summary)
        ext = ".txt"
    
    # Save or print
    if args.save:
        output_dir = Path(args.output_dir) if args.output_dir else script_path.parent / "results"
        output_dir.mkdir(parents=True, exist_ok=True)
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"benchmark_{timestamp}{ext}"
        output_path = output_dir / filename
        
        with open(output_path, "w") as f:
            f.write(output)
        
        print(f"Results saved to: {output_path}")
        
        # Also save CSV employee details if JSON output
        if args.output == "json":
            csv_path = output_dir / f"benchmark_{timestamp}_employees.csv"
            with open(csv_path, "w") as f:
                f.write(CSVFormatter.format_employee_metrics(summary))
            print(f"Employee details saved to: {csv_path}")
    else:
        print(output)


if __name__ == "__main__":
    main()
