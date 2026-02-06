# 🚗 Velora Mobility Optimizer

<p align="center">
  <strong>An intelligent vehicle routing and ride-pooling optimization system</strong>
</p>

<p align="center">
  <a href="#features">Features</a> •
  <a href="#quick-start">Quick Start</a> •
  <a href="#usage">Usage</a> •
  <a href="#architecture">Architecture</a> •
  <a href="#performance">Performance</a>
</p>

---

## 📋 Overview

Velora Mobility Optimizer is a high-performance vehicle routing solution that minimizes transportation costs while respecting employee preferences and time constraints. The system uses a hybrid approach combining greedy heuristics with simulated annealing metaheuristics to achieve **74-87% cost savings** compared to individual transport baselines.

### Key Capabilities

- **Intelligent Ride Pooling**: Groups compatible employees based on routes, time windows, and sharing preferences
- **Multi-Constraint Optimization**: Handles vehicle capacity, time windows, priority levels, and vehicle preferences
- **Cost Sharing**: Fair cost distribution among passengers based on shared distance
- **Real-Time Reporting**: Detailed reports with per-employee breakdowns

---

## ✨ Features

| Feature | Description |
|---------|-------------|
| 🎯 **Multi-objective Optimization** | Balances cost minimization with time efficiency |
| 🚙 **Vehicle Preference Matching** | Respects employee preferences (EV, sedan, SUV, etc.) |
| ⏰ **Time Window Constraints** | Priority-based delay tolerances (0-30 min based on priority) |
| 👥 **Sharing Preferences** | Single, double, triple, or unlimited sharing options |
| 📊 **Comprehensive Analytics** | Benchmarking, verification, and detailed reports |
| 🔄 **Full Pipeline Automation** | Excel → JSON → Solver → Report in one command |

---

## 🚀 Quick Start

### Prerequisites

- **macOS/Linux** (Windows: use WSL)
- **CMake** 3.16+
- **C++17** compatible compiler (clang++/g++)
- **Python** 3.8+
- **pandas** and **openpyxl** (for Excel parsing)

### Installation

```bash
# Clone the repository
git clone <repository-url>
cd velora-mobility-optimizer

# Create Python virtual environment (recommended)
python3 -m venv .venv
source .venv/bin/activate
pip install pandas openpyxl

# Build the C++ solver
bash build.sh

# Verify installation
python velora.py status
```

### Run Your First Test

```bash
# Run test case 1 (full pipeline)
python velora.py run 1

# View the generated report
cat data/tc01_report.txt

# Run benchmarks on all test cases
python velora.py benchmark
```

---

## 📖 Usage

### Unified CLI Tool (`velora.py`)

The project provides a single unified CLI tool that handles all operations:

```bash
python velora.py <command> [options]
```

#### Commands

| Command | Description | Example |
|---------|-------------|---------|
| `run <TC\|all>` | Run test case(s) through full pipeline | `python velora.py run 1` |
| `benchmark` | Run benchmarks and verification | `python velora.py benchmark --save` |
| `report <file>` | Generate report from solver output | `python velora.py report data/json/tc01_output.json` |
| `convert <file>` | Convert Excel to JSON | `python velora.py convert "TC/TestCase_TC01.xlsx"` |
| `status` | Show build status and file counts | `python velora.py status` |
| `help` | Show detailed help | `python velora.py help` |

#### Run Test Cases

```bash
# Run single test case
python velora.py run 1       # Runs TC01
python velora.py run 2       # Runs TC02

# Run all test cases
python velora.py run all
```

The `run` command executes the complete pipeline:
1. **Convert**: Excel test case → JSON input
2. **Solve**: Run C++ optimizer
3. **Report**: Generate human-readable report

#### Benchmark & Verification

```bash
# Console output (default)
python velora.py benchmark

# Save to file
python velora.py benchmark --save

# Different output formats
python velora.py benchmark --output json --save
python velora.py benchmark --output csv --save

# Specific test cases only
python velora.py benchmark tc01 tc02
```

**Sample Output:**
```
==========================================================================================
                    VELORA BENCHMARK REPORT
==========================================================================================
Generated: 2025-01-15 10:30:45

TC       Emp   Veh      Baseline     Optimized    Savings      %        Status
------------------------------------------------------------------------------------------
TC01     8     3/10     $3,200       $619.30      $2,580.70    80.6%    8✓ 0⚠ 0✗
TC02     11    4/15     $4,945       $716.48      $4,228.52    85.5%    11✓ 0⚠ 0✗
TC03     15    5/20     $6,450       $836.77      $5,613.23    87.0%    15✓ 0⚠ 0✗
TC04     12    4/12     $4,420       $1,118.16    $3,301.84    74.7%    12✓ 0⚠ 0✗
------------------------------------------------------------------------------------------
TOTAL    46              $19,015      $3,290.71    $15,724.29   82.7%
```

#### Generate Reports

```bash
# Generate and print report
python velora.py report data/json/tc01_output.json

# Save to specific file
python velora.py report data/json/tc01_output.json my_report.txt
```

#### Convert Excel Files

```bash
# Convert with auto-naming
python velora.py convert "Velora Kriti_2026 TCs/TestCase_TC01.xlsx"

# Specify output path
python velora.py convert input.xlsx data/json/custom_input.json
```

---

## 📁 Project Structure

```
velora-mobility-optimizer/
├── velora.py                    # 🎯 Unified CLI tool (main entry point)
├── build.sh                     # Build script for C++ solver
├── README.md                    # This file
│
├── solver/                      # C++ optimization engine
│   ├── CMakeLists.txt
│   ├── include/
│   │   ├── model.hpp           # Data structures
│   │   ├── constraints.hpp     # Constraint validation
│   │   ├── cost.hpp            # Cost calculations
│   │   ├── heuristics.hpp      # Greedy constructive heuristics
│   │   └── metaheuristics.hpp  # Simulated annealing
│   ├── src/
│   │   ├── main.cpp            # Solver entry point
│   │   ├── constraints/        # Constraint implementations
│   │   ├── cost/               # Cost function implementations
│   │   ├── heuristics/         # Heuristic algorithms
│   │   ├── metaheuristics/     # SA implementation
│   │   └── utils/              # JSON I/O, distance calculations
│   └── tests/                  # Unit tests
│
├── parser/                      # Excel to JSON parser
│   ├── excel_to_json.py        # Standalone parser (also in velora.py)
│   └── schema.md               # JSON schema documentation
│
├── scripts/                     # Additional scripts
│   ├── test_runner.py          # Pipeline orchestration (legacy)
│   ├── json_to_report.py       # Report generation (legacy)
│   └── generate_tc05.py        # Test data generator
│
├── testing_benchmarking/        # Benchmarking module
│   ├── benchmark.py            # Detailed benchmark tool
│   ├── README.md               # Benchmark documentation
│   └── results/                # Saved benchmark results
│
├── data/
│   ├── json/                   # Generated JSON files
│   │   ├── tc01_input.json
│   │   ├── tc01_output.json
│   │   └── ...
│   ├── raw/                    # Raw data files
│   └── samples/                # Sample data
│
├── Velora Kriti_2026 TCs/      # Test case Excel files
│   ├── TestCase_TC01.xlsx
│   ├── TestCase_TC02.xlsx
│   ├── TestCase_TC03.xlsx
│   └── TestCase_TC04.xlsx
│
├── docs/                        # Documentation
│   ├── architecture.md         # System architecture
│   ├── algorithm_design.md     # Algorithm details
│   ├── cost_function.md        # Cost function specification
│   └── Final_Report.md         # Project report
│
├── frontend/                    # Web frontend (if applicable)
│   └── src/
│
└── backend/                     # API backend (if applicable)
    └── src/
```

---

## ⚙️ Configuration

### Test Case Excel Format

Test cases should have the following sheets:

#### `metadata` Sheet
| key | value |
|-----|-------|
| `priority_1_delay_tolerance` | 0 |
| `priority_2_delay_tolerance` | 5 |
| `priority_3_delay_tolerance` | 15 |
| `objective_cost_weight` | 0.7 |
| `objective_time_weight` | 0.3 |

#### `vehicles` Sheet
| Column | Description |
|--------|-------------|
| `vehicle_id` | Unique identifier (V01, V02, ...) |
| `vehicle_type` | sedan, suv, ev, any |
| `fuel_type` | petrol, diesel, electric, cng |
| `capacity` | Number of passengers (1-6) |
| `cost_per_km` | Cost rate per kilometer |
| `avg_speed_kmph` | Average speed |
| `current_lat/lng` | Starting location |
| `available_from` | Availability time (HH:MM) |

#### `employees` Sheet
| Column | Description |
|--------|-------------|
| `employee_id` | Unique identifier (E01, E02, ...) |
| `priority` | 1 (VIP), 2 (Standard), 3 (Flexible) |
| `vehicle_preference` | sedan, suv, ev, any |
| `sharing_preference` | single, double, triple, unlimited |
| `pickup_lat/lng` | Pickup location |
| `dropoff_lat/lng` | Dropoff location |
| `earliest_pickup_time` | Earliest pickup (HH:MM) |
| `latest_dropoff_time` | Latest dropoff deadline (HH:MM) |
| `baseline_cost` | Cost for individual transport |
| `baseline_time_min` | Time for individual transport |

### JSON Configuration

Input JSON files allow configuration of weights and map behavior:

```json
{
  "config": {
    "allow_external_maps": true,
    "maps_api_key": "",
    "tolerances": {
      "1": 0, "2": 5, "3": 15, "4": 20, "5": 30
    },
    "weights": {
      "cost": 0.7,
      "time": 0.3
    }
  }
}
```

---

## 🔧 Algorithm

### Overview

The optimization uses a two-phase approach:

1. **Greedy Construction**: Build initial solution by iteratively assigning requests to vehicles based on insertion cost
2. **Simulated Annealing**: Improve solution through local search with probabilistic acceptance of worse solutions

### Cost Function

```
GlobalCost = CTC + PenaltyCost

Where:
  CTC = Σ (segment_distance × cost_per_km) for all route segments
  PenaltyCost = Σ delay_penalty for violations
```

**Cost Sharing**: Each route segment's cost is divided equally among passengers currently in the vehicle.

### Constraints

| Constraint | Description |
|------------|-------------|
| **Capacity** | Vehicle load ≤ capacity at all times |
| **Time Windows** | Arrival ≤ latest_time + tolerance(priority) |
| **Vehicle Preference** | Match employee preference to vehicle type |
| **Sharing Limit** | Max passengers ≤ sharing preference |
| **Precedence** | Pickup must occur before dropoff |

---

## 📊 Performance

### Benchmark Results

| Test Case | Employees | Baseline | Optimized | Savings |
|-----------|-----------|----------|-----------|---------|
| TC01 | 8 | $3,200 | $619 | **80.6%** |
| TC02 | 11 | $4,945 | $716 | **85.5%** |
| TC03 | 15 | $6,450 | $837 | **87.0%** |
| TC04 | 12 | $4,420 | $1,118 | **74.7%** |

**Average Savings: 82%**

### Solver Performance

- **TC01 (8 employees)**: ~0.5 seconds
- **TC02 (11 employees)**: ~1 second
- **TC03 (15 employees)**: ~2 seconds
- **TC04 (12 employees)**: ~1.5 seconds

---

## 📝 Scripts Reference

### Main Tool

| Script | Purpose |
|--------|---------|
| `velora.py` | **Unified CLI** - Run tests, benchmarks, reports, conversions |

### Additional Scripts

| Script | Purpose |
|--------|---------|
| `parser/excel_to_json.py` | Standalone Excel to JSON converter |
| `scripts/test_runner.py` | Legacy pipeline orchestrator |
| `scripts/json_to_report.py` | Legacy report generator |
| `scripts/generate_tc05.py` | Generate large test cases (100 employees) |
| `testing_benchmarking/benchmark.py` | Detailed benchmarking with multiple output formats |

### Build Scripts

| Script | Purpose |
|--------|---------|
| `build.sh` | Build C++ solver |

---

## 🔍 Troubleshooting

### Common Issues

**Solver not found**
```bash
# Rebuild the solver
bash build.sh
```

**Missing Python packages**
```bash
pip install pandas openpyxl
```

**Permission denied**
```bash
chmod +x velora.py build.sh
```

**Test case not found**
```bash
# Check available test cases
ls "Velora Kriti_2026 TCs/"
```

### Checking Status

```bash
python velora.py status
```

This shows:
- Solver build status
- Python environment
- Available test cases
- Generated outputs and reports

---

## 📚 Documentation

- [Architecture Overview](docs/architecture.md)
- [Algorithm Design](docs/algorithm_design.md)
- [Cost Function Specification](docs/cost_function.md)
- [JSON Schema](parser/schema.md)

---

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit changes (`git commit -m 'Add amazing feature'`)
4. Push to branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

---

## 📄 License

This project is developed for Kriti 2026.

---

<p align="center">
  <strong>Velora Mobility Optimizer</strong> - Intelligent Transportation Optimization
</p>
