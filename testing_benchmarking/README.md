# Testing & Benchmarking

This folder contains tools for testing, verification, and benchmarking the Velora Mobility Optimizer.

## Benchmark Tool

### Usage

```bash
# Run all test cases with console output
python testing_benchmarking/benchmark.py

# Run specific test cases
python testing_benchmarking/benchmark.py tc01 tc02

# Output as JSON
python testing_benchmarking/benchmark.py --output json

# Output as CSV
python testing_benchmarking/benchmark.py --output csv

# Save results to file
python testing_benchmarking/benchmark.py --save

# Save as JSON file
python testing_benchmarking/benchmark.py --save --output json

# Specify custom output directory
python testing_benchmarking/benchmark.py --save --output-dir ./results
```

### Output Formats

1. **Console** (default): Human-readable formatted report
2. **JSON**: Complete structured data for programmatic use
3. **CSV**: Tabular data for spreadsheet analysis

### Metrics Collected

#### Test Case Level
- Total employees and vehicles
- Baseline vs optimized costs
- Savings (absolute and percentage)
- On-time/delay/late counts
- Total distance and time
- Penalty costs

#### Employee Level
- Individual cost comparison
- Time window compliance
- Delay minutes
- Priority handling
- Vehicle assignment

#### Vehicle Level
- Route distance and cost
- Passengers served
- Capacity utilization
- Fuel type and category

### Results Directory

When using `--save`, results are stored in `testing_benchmarking/results/` with timestamps:
- `benchmark_YYYYMMDD_HHMMSS.txt` (console format)
- `benchmark_YYYYMMDD_HHMMSS.json` (JSON format)
- `benchmark_YYYYMMDD_HHMMSS.csv` (CSV format)
- `benchmark_YYYYMMDD_HHMMSS_employees.csv` (detailed employee data with JSON output)

## Verification Features

The benchmark tool also verifies:
- Cost calculations match solver output
- Time windows are correctly evaluated
- Shared cost splitting is accurate
- Route distances are consistent
- Summary metrics are correct
