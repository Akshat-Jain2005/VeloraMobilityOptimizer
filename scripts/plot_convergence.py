#!/usr/bin/env python3
"""
Plot SA convergence from a CSV log file.

Usage:
    python scripts/plot_convergence.py <convergence.csv>

Reads iteration,current_cost,best_cost,temperature and produces a PNG plot.
"""

import sys
import csv
from pathlib import Path

try:
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
except ImportError:
    print("Error: matplotlib is required. Install with: pip install matplotlib")
    sys.exit(1)


def plot_convergence(csv_path: str):
    path = Path(csv_path)
    if not path.exists():
        print(f"Error: file not found: {csv_path}")
        sys.exit(1)

    iterations = []
    current_costs = []
    best_costs = []
    temperatures = []

    with open(path) as f:
        reader = csv.DictReader(f)
        for row in reader:
            iterations.append(int(row["iteration"]))
            current_costs.append(float(row["current_cost"]))
            best_costs.append(float(row["best_cost"]))
            temperatures.append(float(row["temperature"]))

    if not iterations:
        print("Error: no data in CSV")
        sys.exit(1)

    fig, ax1 = plt.subplots(figsize=(12, 6))

    # Cost lines
    ax1.plot(iterations, current_costs, color="#93c5fd", alpha=0.5, linewidth=0.5, label="Current cost")
    ax1.plot(iterations, best_costs, color="#1d4ed8", linewidth=1.5, label="Best cost")
    ax1.set_xlabel("Iteration")
    ax1.set_ylabel("Cost")
    ax1.set_title("Simulated Annealing Convergence")

    # Temperature on secondary axis
    ax2 = ax1.twinx()
    ax2.plot(iterations, temperatures, color="#ef4444", alpha=0.3, linewidth=0.8, linestyle="--", label="Temperature")
    ax2.set_ylabel("Temperature", color="#ef4444")
    ax2.tick_params(axis="y", labelcolor="#ef4444")

    # Combined legend
    lines1, labels1 = ax1.get_legend_handles_labels()
    lines2, labels2 = ax2.get_legend_handles_labels()
    ax1.legend(lines1 + lines2, labels1 + labels2, loc="upper right")

    ax1.grid(True, alpha=0.3)
    fig.tight_layout()

    # Save PNG next to the CSV
    png_path = path.with_suffix(".png")
    fig.savefig(png_path, dpi=150)
    print(f"Plot saved: {png_path}")

    plt.close(fig)
    return str(png_path)


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python plot_convergence.py <convergence.csv>")
        sys.exit(1)
    plot_convergence(sys.argv[1])
