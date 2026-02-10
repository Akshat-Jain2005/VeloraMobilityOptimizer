# Velora Mobility Optimizer — Backend API

Optimization engine for corporate employee transportation. Accepts Excel/JSON input, runs a C++ VRPTW solver, and returns optimized vehicle routes via a REST API.

## Architecture

```
Client (Browser / curl)
  │
  │  HTTP Request (POST /api/optimize)
  ▼
┌─────────────────────────────────────────────────────┐
│  Node.js + Express  (server.js — port 3000)         │
│                                                     │
│  1. Receive uploaded Excel file                     │
│  2. Spawn Python parser (excel_to_json.py)          │
│     Excel → JSON                                    │
│  3. Spawn C++ solver (velora_solver)                │
│     JSON → Optimized JSON                           │
│  4. Return result to client                         │
└─────────────────────────────────────────────────────┘
```

## Prerequisites

You need these installed on your system:

| Tool       | Version  | Check command         | Install (Ubuntu)                                    |
|------------|----------|-----------------------|-----------------------------------------------------|
| Node.js    | v18+     | `node --version`      | `curl -fsSL https://deb.nodesource.com/setup_20.x \| sudo -E bash - && sudo apt install -y nodejs` |
| Python 3   | 3.8+     | `python3 --version`   | `sudo apt install python3 python3-pip`              |
| pandas     | 2.0+     | `python3 -c "import pandas"` | `pip install -r requirements.txt`             |
| openpyxl   | 3.1+     | `python3 -c "import openpyxl"` | (included in requirements.txt)              |
| C++ build tools | —   | `g++ --version`       | `sudo apt install build-essential cmake`            |
| nlohmann-json | —     | —                     | `sudo apt install nlohmann-json3-dev`               |

## Setup (Step by Step)

### 1. Clone the repository

```bash
git clone <your-repo-url>
cd velora-mobility-optimizer
```

### 2. Build the C++ solver

```bash
mkdir -p build && cd build
cmake .. -DCMAKE_BUILD_TYPE=Release
make -j$(nproc)
cd ..
```

This creates the binary at `build/solver/velora_solver`.

### 3. Install Python dependencies

```bash
pip install -r requirements.txt
```

### 4. Set up the backend

```bash
cd backend

# Install Node.js dependencies
npm install

# Create the solver and parser folders inside backend
mkdir -p solver parser

# Copy the compiled C++ binary
cp ../build/solver/velora_solver ./solver/
chmod +x ./solver/velora_solver

# Copy the Python parser
cp ../parser/excel_to_json.py ./parser/

# Copy the env folder (contains .env for API keys)
cp -r ../env ./

# Create your .env file
cp .env.example .env
```

### 5. (Optional) Configure Maps API

Edit `.env` if you have a maps API key:

```
MAPS_API_KEY=your_key_here
```

Leave it blank to use Haversine distance (works fine, no API needed).

### 6. Start the server

```bash
npm start
```

You should see:

```
==================================================
  VELORA MOBILITY OPTIMIZER — Backend API
==================================================
  Server:  http://localhost:3000
  Health:  http://localhost:3000/api/health
  API:     POST http://localhost:3000/api/optimize
==================================================
```

## API Endpoints

### Health Check

```bash
curl http://localhost:3000/api/health
```

Returns server status and checks if solver + parser are in place.

### Optimize from Excel (Full Pipeline)

Upload an Excel file (.xlsx) with sheets: `employees`, `vehicles`, `baseline`, `metadata`.

```bash
curl -X POST http://localhost:3000/api/optimize \
  -F "file=@/path/to/TestCase_TC01.xlsx"
```

### Optimize from JSON (Skip Parser)

Send pre-built JSON directly to the solver:

```bash
curl -X POST http://localhost:3000/api/optimize/json \
  -H "Content-Type: application/json" \
  -d @data/json/tc01_input.json
```

### Fetch Past Result

Every job returns a `jobId`. Use it to fetch the result later:

```bash
curl http://localhost:3000/api/results/<jobId>
```

## Response Format

```json
{
  "jobId": "4215c001-02f3-4a7c-a376-c04cf753e5d8",
  "status": "success",
  "elapsedSeconds": 6.25,
  "result": {
    "summary": {
      "globalCost": 829.73,
      "totalDistance": 71.78,
      "totalMoneyCost": 837.77,
      "totalPenaltyCost": 167.99,
      "totalTime": 250.99,
      "unassignedCount": 0,
      "vehiclesUsed": 2
    },
    "routes": [
      {
        "vehicleId": 0,
        "vehicleIdStr": "V01",
        "totalDist": 41.80,
        "totalTime": 109.92,
        "totalCost": 417.97,
        "stops": [
          {
            "reqId": 5,
            "employeeId": "E06",
            "type": "pickup",
            "lat": 12.95,
            "lon": 77.62,
            "arrivalTime": 495.0
          }
        ]
      }
    ],
    "requestDetails": [
      {
        "id": 0,
        "employeeId": "E01",
        "priority": 1,
        "earlyTime": 510,
        "lateTime": 570,
        "vehiclePreference": "premium",
        "sharingLimit": 1
      }
    ],
    "unassigned": []
  }
}
```

## Excel Input Format

The Excel file must contain these sheets:

### Sheet: `employees`

| Column             | Type   | Example    | Description                    |
|--------------------|--------|------------|--------------------------------|
| employee_id        | string | E01        | Unique employee identifier     |
| priority           | int    | 1          | 1 (highest) to 5 (lowest)     |
| pickup_lat         | float  | 12.9352    | Pickup latitude                |
| pickup_lng         | float  | 77.6245    | Pickup longitude               |
| drop_lat           | float  | 12.9716    | Dropoff latitude               |
| drop_lng           | float  | 77.5946    | Dropoff longitude              |
| earliest_pickup    | time   | 08:30      | Earliest pickup time (HH:MM)  |
| latest_drop        | time   | 09:30      | Latest dropoff time (HH:MM)   |
| vehicle_preference | string | premium    | "premium", "normal", or "any" |
| sharing_preference | string | single     | "single", "double", or "triple"|

### Sheet: `vehicles`

| Column          | Type   | Example  | Description                  |
|-----------------|--------|----------|------------------------------|
| vehicle_id      | string | V01      | Unique vehicle identifier    |
| fuel_type       | string | electric | "petrol", "diesel", "electric"|
| vehicle_type    | string | 4W       | "2W", "4W", or "van"        |
| capacity        | int    | 3        | Max passengers               |
| cost_per_km     | float  | 10.0     | Cost per kilometer           |
| avg_speed_kmph  | float  | 30.0     | Average speed in km/h        |
| current_lat     | float  | 12.935   | Vehicle start latitude       |
| current_lng     | float  | 77.62    | Vehicle start longitude      |
| available_from  | time   | 08:00    | Availability time (HH:MM)   |
| category        | string | premium  | "premium" or "normal"        |

### Sheet: `baseline`

| Column            | Type   | Example | Description                       |
|-------------------|--------|---------|-----------------------------------|
| employee_id       | string | E01     | Employee identifier               |
| baseline_cost     | float  | 420.0   | Individual cab cost (Ola/Uber)    |
| baseline_time_min | float  | 45.0    | Individual cab time in minutes    |

### Sheet: `metadata`

| Key                        | Value     | Description                        |
|----------------------------|-----------|------------------------------------|
| test_case_id               | TC_01     | Test case identifier               |
| city                       | Bengaluru | City name                          |
| distance_method            | haversine | Distance calculation method        |
| allow_external_maps        | true      | Enable external map API            |
| priority_1_max_delay_min   | 5         | Max delay tolerance for P1 (mins)  |
| priority_2_max_delay_min   | 10        | Max delay tolerance for P2 (mins)  |
| priority_3_max_delay_min   | 15        | Max delay tolerance for P3 (mins)  |
| priority_4_max_delay_min   | 20        | Max delay tolerance for P4 (mins)  |
| priority_5_max_delay_min   | 30        | Max delay tolerance for P5 (mins)  |
| objective_cost_weight      | 0.7       | Weight for cost in objective       |
| objective_time_weight      | 0.3       | Weight for time in objective       |

## Folder Structure

```
backend/
├── server.js              ← Express server entry point
├── package.json           ← Node.js dependencies
├── requirements.txt       ← Python dependencies
├── .env                   ← Environment variables (API keys etc.)
├── .env.example           ← Template for .env
├── .gitignore             ← Files excluded from git
├── routes/
│   └── optimize.js        ← API route handlers
├── middleware/
│   └── upload.js          ← File upload config (Multer)
├── services/
│   ├── parser.js          ← Spawns Python excel_to_json.py
│   └── solver.js          ← Spawns C++ velora_solver binary
├── solver/
│   └── velora_solver      ← Compiled C++ binary (not in git)
├── parser/
│   └── excel_to_json.py   ← Python Excel-to-JSON converter
├── uploads/               ← Temporary uploaded files (auto-cleaned)
└── outputs/               ← Solver results (fetchable by jobId)
```

## Troubleshooting

| Problem | Solution |
|---------|----------|
| `solver/velora_solver not found` | Run the C++ build step and copy the binary |
| `Parser failed` | Check Python + pandas + openpyxl are installed |
| `Permission denied` | Run `chmod +x solver/velora_solver` |
| `ECONNREFUSED` | Server isn't running — run `npm start` first |
| `File type not supported` | Only .xlsx, .xls, .csv are accepted |

## Important Notes

- The C++ binary (`velora_solver`) is compiled for a specific OS/architecture. If you're on a different machine, you must recompile from source using the build step above.
- Output files are stored in `outputs/` and persist until manually deleted.
- The server runs on port 3000 by default. Change it in `.env`.
