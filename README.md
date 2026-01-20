# Velora Mobility Optimizer

A C++ optimization solver for vehicle routing and mobility management using greedy constructive heuristics and simulated annealing. Automatically optimizes delivery routes for multiple vehicles with constraints on capacity, time windows, and priorities.

## 🚀 Quick Start (5 Minutes)

### 1. Prerequisites

**macOS:**
```bash
brew install cmake nlohmann-json curl python3
python3 -m pip install pandas openpyxl
```

**Linux (Ubuntu):**
```bash
sudo apt-get install cmake nlohmann-json3-dev libcurl4-openssl-dev python3-pip
python3 -m pip install pandas openpyxl
```

### 2. Build

```bash
cd velora-mobility-optimizer
bash build.sh
```

### 3. Run Test Cases

```bash
# Run single test (TC01, TC02, TC03, or TC04)
.venv/bin/python3 scripts/test_runner.py 1

# Run all 4 tests
.venv/bin/python3 scripts/test_runner.py all

# View report
cat data/tc01_report.txt

# View all reports
bash scripts/view_all_results.sh
```

### 4. Using Shortcuts (Optional)

```bash
# Load shortcut functions
source scripts/commands.sh

# Use shortcuts:
run_tc1           # Run TC01
run_all_tc        # Run all tests
view_all_reports  # View all reports
build_all         # Rebuild project
```

### Manual Solver Invocation

```bash
# With sample data
./build/solver/velora_solver data/json/sample_input.json data/json/sample_output.json

# With Excel input
python3 parser/excel_to_json.py your_data.xlsx input.json
./build/solver/velora_solver input.json output.json
```

## ✨ Features

- ✅ **JSON I/O**: Read requests & vehicles from JSON, output optimized routes as JSON
- ✅ **Distance Calculation**: Haversine formula (default) + Google Maps Distance Matrix API (optional)
- ✅ **Optimization**: Greedy constructive heuristic + Simulated annealing metaheuristic
- ✅ **Constraints**: Vehicle capacity, time windows (pickup/delivery), request priorities
- ✅ **Cost Function**: Operational cost + lateness penalties (weighted by priority)
- ✅ **Excel Parser**: Automatic conversion from Excel test cases to JSON
- ✅ **Professional Reports**: Detailed routing, cost breakdowns, baseline comparisons
- ✅ **Multi-Test Support**: All 4 test cases (TC01-TC04) automated

## 📊 Test Results

| Test Case | Baseline Cost | Optimized Cost | Improvement | Requests | Vehicles |
|-----------|---------------|----------------|-------------|----------|----------|
| TC01 | - | $793.11 | - | 8 | 3 |
| TC02 | - | $949.57 | - | 8+ | 3+ |
| TC03 | - | $1210.99 | - | 8+ | 3+ |
| TC04 | - | $10847.84 | - | Large | Large |

**Status**: ✅ All test cases executed successfully

## Project Structure

```
velora-mobility-optimizer/
├── README.md                      # This file
├── build.sh                       # Build helper script
├── CMakeLists.txt                 # Root build configuration
├── solver/                        # Main optimization solver
│   ├── include/
│   │   ├── map_distance.hpp       # Distance provider interface
│   │   ├── constraints.hpp
│   │   ├── cost.hpp
│   │   └── model.hpp
│   └── src/
│       ├── main.cpp               # Solver entry point
│       ├── map_distance.cpp       # Distance implementation
│       └── [constraints|cost|heuristics|metaheuristics|utils]/
├── parser/
│   ├── excel_to_json.py           # Excel → JSON converter
│   └── schema.md                  # Excel format specification
├── scripts/
│   ├── test_runner.py             # Main test orchestrator
│   ├── run_test.sh                # Bash wrapper
│   ├── commands.sh                # Shortcut functions
│   └── view_all_results.sh        # View all reports
├── data/
│   ├── json/                      # JSON input/output files
│   │   ├── tc0X_input.json        # Parsed test cases
│   │   └── tc0X_output.json       # Solver outputs
│   ├── tc0X_report.txt            # Generated reports
│   ├── raw/
│   └── samples/
├── docs/
│   ├── algorithm_design.md        # Algorithm details
│   ├── architecture.md            # System architecture
│   └── cost_function.md           # Cost calculation
├── build/                         # Compiled output
│   └── solver/velora_solver       # Compiled solver binary
└── Velora Kriti_2026 TCs/         # Test case Excel files
    ├── TestCase_TC01.xlsx
    ├── TestCase_TC02.xlsx
    ├── TestCase_TC03.xlsx
    └── TestCase_TC04.xlsx
```

## Input/Output

### Input JSON
```json
{
  "config": {
    "allow_external_maps": false,
    "maps_api_key": ""
  },
  "vehicles": [
    {
      "id": 0,
      "capacity": 4,
      "costPerKm": 10.0,
      "startLoc": {"lat": 40.7128, "lon": -74.0060},
      "availabilityTime": 0.0
    }
  ],
  "requests": [
    {
      "id": 0,
      "priority": 1,
      "pickup": {"lat": 40.7580, "lon": -73.9855},
      "dropoff": {"lat": 40.7489, "lon": -73.9680},
      "earlyTime": 0.0,
      "lateTime": 100.0,
      "load": 1
    }
  ]
}
```

### Output JSON
```json
{
  "globalCost": 105.91,
  "unassigned": [],
  "routes": [
    {
      "vehicleId": 0,
      "totalDist": 10.59,
      "totalCost": 105.91,
      "stops": [
        {
          "reqId": 0,
          "type": "P",
          "lat": 40.7580,
          "lon": -73.9855,
          "arrival": 5.03
        },
        {
          "reqId": 0,
          "type": "D",
          "lat": 40.7489,
          "lon": -73.9680,
          "arrival": 10.59
        }
      ]
    }
  ]
}
```

## Excel to JSON Conversion

**Expected Excel sheets:**

**vehicles**
| id  | capacity | costPerKm | startLat | startLon | availabilityTime |
|-----|----------|-----------|----------|----------|------------------|
| 0   | 4        | 10.0      | 40.7128  | -74.0060 | 0                |

**requests**
| id  | priority | pickupLat | pickupLon | dropoffLat | dropoffLon | earlyTime | lateTime | load |
|-----|----------|-----------|-----------|------------|------------|-----------|----------|------|
| 0   | 1        | 40.7580   | -73.9855  | 40.7489    | -73.9680   | 0         | 100      | 1    |

**employees** (optional)
| id  | name  | shiftStart | shiftEnd | startLat | startLon |
|-----|-------|------------|----------|----------|----------|
| 0   | John  | 9          | 17       | 40.7128  | -74.0060 |

```bash
python3 parser/excel_to_json.py input.xlsx output.json
```

## Configuration

### External Maps API

To use Google Maps Distance Matrix API instead of Haversine:

1. Set in input JSON:
```json
{
  "config": {
    "allow_external_maps": true,
    "maps_api_key": "YOUR_GOOGLE_MAPS_API_KEY"
  }
}
```

2. Rebuild with CURL support:
```bash
brew install curl    # macOS
cmake .. -DUSE_CURL=ON
cmake --build .
```

## Troubleshooting

| Issue | Solution |
|-------|----------|
| `nlohmann/json.hpp` not found | `brew install nlohmann-json` |
| CURL not found (optional) | `brew install curl` (external maps disabled by default) |
| Python pandas not installed | `python3 -m pip install pandas openpyxl` |
| Build fails with compiler error | `rm -rf build && bash build.sh` (clean rebuild) |

## Build System

### Manual Build
```bash
mkdir -p build && cd build && cmake .. && cmake --build . --parallel 4
```

### Build Variants
```bash
# Release (optimized, no debug symbols)
cmake -DCMAKE_BUILD_TYPE=Release ..

# Debug (with debug symbols)
cmake -DCMAKE_BUILD_TYPE=Debug ..

# Verbose output
cmake -DCMAKE_VERBOSE_MAKEFILE=ON ..
```

### Clean Rebuild
```bash
rm -rf build && bash build.sh
```

## Performance

- **Greedy Phase**: O(n² × m) where n=requests, m=vehicles
- **Simulated Annealing**: 2000 iterations, temperature schedule 1000 × 0.995^iter
- **Haversine Distance**: O(1) per calculation
- **Typical Runtime**: < 1 second for 50 requests, 5 vehicles

## Architecture

### Core Classes

- **`MapDistance`**: Computes distances (Haversine + external API)
- **`Request`**: Pickup/dropoff pair with time windows
- **`Vehicle`**: Capacity, cost, start location
- **`Stop`**: Pickup or dropoff event with timing
- **`Route`**: Sequence of stops + cost tracking
- **`Solution`**: Set of routes + unassigned requests

### Algorithms

- **Constructive Heuristic**: Priority-based greedy insertion
- **Metaheuristic**: Simulated annealing with request transfer moves
- **Cost Function**: Operational + lateness penalties (weighted by priority)

## Testing & Reports

### Run Tests
```bash
# Single test
.venv/bin/python3 scripts/test_runner.py 1

# All tests
.venv/bin/python3 scripts/test_runner.py all

# View reports
cat data/tc01_report.txt
bash scripts/view_all_results.sh
```

### Report Contents
Each generated text report includes:
- **Input Summary**: Vehicles, requests, time windows
- **Vehicle Details**: Capacity, cost/km, start location
- **Optimization Results**: Total cost, routes, assignments
- **Detailed Routes**: Stop-by-stop breakdown with times
- **Cost Breakdown**: Per-vehicle costs and percentages
- **Baseline Comparison**: Baseline vs. optimized cost

### Test Pipeline
```
Excel File
    ↓
[Stage 1] Excel → JSON Parser
    ↓
[Stage 2] C++ Optimization Solver
    ├─ Greedy Constructive Heuristic
    └─ Simulated Annealing
    ↓
[Stage 3] Report Generator
    ↓
Text Report & JSON Output
```

## Shortcut Functions

Load shortcuts for easier testing:
```bash
source scripts/commands.sh
```

Available commands:
```bash
run_tc1              # Run TC01
run_tc2              # Run TC02
run_tc3              # Run TC03
run_tc4              # Run TC04
run_all_tc           # Run all tests
view_tc1_report      # View TC01 report
view_tc2_report      # View TC02 report
view_tc3_report      # View TC03 report
view_tc4_report      # View TC04 report
view_all_reports     # View all reports
build_all            # Build project
rebuild              # Clean and rebuild
status               # Show project status
```

## Common Commands

```bash
# Build solver
bash build.sh

# Install Python dependencies
.venv/bin/pip install pandas openpyxl

# Run single test
.venv/bin/python3 scripts/test_runner.py 1

# Run all tests
.venv/bin/python3 scripts/test_runner.py all

# View specific report
cat data/tc01_report.txt

# View JSON output
cat data/json/tc01_output.json | python3 -m json.tool

# View all reports
bash scripts/view_all_results.sh

# Load shortcuts
source scripts/commands.sh && run_all_tc
```

## Troubleshooting

| Issue | Solution |
|-------|----------|
| `nlohmann/json.hpp` not found | `brew install nlohmann-json` |
| CURL not found (optional) | `brew install curl` (external maps disabled by default) |
| Python pandas not installed | `.venv/bin/pip install pandas openpyxl` |
| Build fails with compiler error | `rm -rf build && bash build.sh` (clean rebuild) |
| "Solver not found" error | Run `bash build.sh` first |
| Excel parsing is slow | First run takes 10-30 seconds (normal) |

## Configuration

### External Maps API

To use Google Maps Distance Matrix API instead of Haversine:

1. Set in input JSON:
```json
{
  "config": {
    "allow_external_maps": true,
    "maps_api_key": "YOUR_GOOGLE_MAPS_API_KEY"
  }
}
```

2. Rebuild with CURL support:
```bash
brew install curl    # macOS
cmake .. -DUSE_CURL=ON
cmake --build .
```

## Documentation

- [Algorithm Design](docs/algorithm_design.md) - Optimization techniques
- [Architecture](docs/architecture.md) - System design
- [Cost Function](docs/cost_function.md) - Cost calculations

## Built With

- **C++17** - Core solver
- **CMake 3.20+** - Build system
- **nlohmann_json** - JSON serialization
- **Python 3** - Excel parser & test runner
- **CURL** - Optional Distance Matrix API

## License

Velora Mobility Optimizer - 2026
- **`Stop`**: Pickup or dropoff event with timing
- **`Route`**: Sequence of stops + cost tracking
- **`Solution`**: Set of routes + unassigned requests

### Algorithms

- **Constructive Heuristic**: Priority-based greedy insertion
- **Metaheuristic**: Simulated annealing with request transfer moves
- **Cost Function**: Operational + lateness penalties (weighted by priority)

## Documentation

- [Algorithm Design](docs/algorithm_design.md)
- [Architecture](docs/architecture.md)
- [Cost Function](docs/cost_function.md)
- [CMake Build Guide](CMAKE_BUILD_GUIDE.md)

## Test Cases

See [Velora Kriti_2026 TCs/](Velora%20Kriti_2026%20TCs/) for test case specifications.

## License

Velora Mobility Optimizer - 2026

---

**Built with**: C++17, CMake 3.20+, nlohmann_json, CURL (optional)
