# Velora Mobility Optimizer

A high-performance C++ solver for the Vehicle Routing Problem (VRP) with Employee Transport Constraints. It optimizes pickup and drop-off routes for corporate mobility, handling capacity, strict time windows, priority tolerances, and infeasibility via forced assignments.

## 🚀 Features

*   **Hybrid Algorithm**: Combines a **Greedy Constructive Heuristic** with **Simulated Annealing** (SA) to find near-optimal solutions.
*   **Realistic Constraints**:
    *   **Hard**: Vehicle Capacity, Safety.
    *   **Soft**: Priority-based Time Tolerances (P1: 5min ... P5: 30min).
*   **Infeasibility Handling**: "Forced Assignment" strategy ensures no employee is left behind, even if it violates windows (with penalties).
*   **Robust Map Service**:
    *   **External API** Support (Google/OSRM).
    *   **Circuit Breaker**: Auto-switches to Haversine * 1.4x (Road Factor) if API lags (>100ms) or fails.
*   **Automated Testing**: Full pipeline from Excel Input -> Solver -> Text Reports.

---

## 🛠️ Quick Start (2 Minutes)

### 1. Prerequisites
**macOS**:
```bash
brew install cmake nlohmann-json curl python3
python3 -m pip install pandas openpyxl
```

### 2. Build
```bash
cd velora-mobility-optimizer
bash build.sh
```

### 3. Run All Test Cases
```bash
python3 scripts/test_runner.py all
```
*This parses Excel files, runs the solver, and generates text reports in `data/`.*

### 4. View Results
```bash
bash scripts/view_all_results.sh
```

---

## 📂 Project Structure

```
velora-mobility-optimizer/
├── build.sh                       # One-click build script
├── solver/                        # Core C++17 Optimization Engine
│   ├── src/
│   │   ├── main.cpp               # Logic: Heuristics + Simulated Annealing
│   │   └── map_distance.cpp       # Map Service + Circuit Breaker
│   └── include/
├── scripts/
│   ├── test_runner.py             # Pipeline Orchestrator (Excel -> Solver -> Report)
│   ├── run_test.sh                # Wrapper script
│   └── view_all_results.sh        # Result visualizer
├── data/
│   ├── json/                      # JSON Input/Output storage
│   ├── tc01_report.txt            # Human-readable Analysis Reports
│   └── ...
├── docs/
│   ├── algorithm_design.md        # Math & Logic explained
│   └── architecture.md            # System Component diagram
└── Velora Kriti_2026 TCs/         # Original Excel Data Sources
```

---

## ⚙️ Configuration

Input JSON files allow configuration of weights and map behavior:

```json
"config": {
  "allow_external_maps": true,  
  "maps_api_key": "",            // Leave empty to test Fail-Fast logic
  "tolerances": { 
     "1": 5, "2": 10, "3": 15, "4": 20, "5": 30 
  }
}
```
*   **Note**: If `allow_external_maps` is true but key is empty, the system defaults to `Haversine Distance * 1.4` to simulate realistic road conditions.

---

## 📊 Performance & Optimization

*   **TC01**: ~ $551 (3 Vehicles)
*   **TC04**: Handles "Impossible Request" (Emp 09) via Forced Assignment + Penalty.
*   **Speed**: Solves standard cases (< 50 reqs) in < 200ms.

---

## 🧪 Testing

To run a specific test case (e.g., TC03):
```bash
python3 scripts/test_runner.py 3
```

To see the generated report:
```bash
cat data/tc03_report.txt
```

---

**License**: Proprietary / Velora Kriti 2026
