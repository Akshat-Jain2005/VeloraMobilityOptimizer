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
    import matplotlib.ticker as ticker
except ImportError:
    print("Error: matplotlib is required. Install with: pip install matplotlib")
    sys.exit(1)


def _rolling_mean(data, window):
    """Simple rolling mean for smoothing noisy current-cost trace."""
    if len(data) <= window:
        return data
    out = []
    acc = sum(data[:window])
    for i in range(window, len(data)):
        out.append(acc / window)
        acc += data[i] - data[i - window]
    out.append(acc / window)
    # pad the front with the raw values so lengths match
    return data[: window - 1] + out


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

    # ── Smoothed current cost (rolling average, adaptive window) ────────────
    window = max(5, len(iterations) // 60)
    smoothed = _rolling_mean(current_costs, window)

    # ── Detect first and last improvement iterations ────────────────────────
    first_improv = None
    last_improv = None
    prev_best = best_costs[0]
    for i, b in enumerate(best_costs):
        if b < prev_best:
            if first_improv is None:
                first_improv = iterations[i]
            last_improv = iterations[i]
            prev_best = b

    # ── Figure ──────────────────────────────────────────────────────────────
    fig, ax1 = plt.subplots(figsize=(13, 6))
    fig.patch.set_facecolor("#fafafa")
    ax1.set_facecolor("#ffffff")

    # Raw current cost (very faint)
    ax1.plot(iterations, current_costs, color="#bfdbfe", alpha=0.25, linewidth=0.4,
             label="_nolegend_")
    # Smoothed current cost
    ax1.plot(iterations, smoothed, color="#60a5fa", alpha=0.75, linewidth=1.0,
             label=f"Current cost (smoothed, w={window})")
    # Best cost (bold)
    ax1.plot(iterations, best_costs, color="#1e40af", linewidth=2.0,
             label="Best cost")

    # Improvement markers
    if first_improv is not None:
        ax1.axvline(first_improv, color="#16a34a", linewidth=0.8, linestyle=":",
                     alpha=0.7, label=f"First improvement (iter {first_improv})")
    if last_improv is not None and last_improv != first_improv:
        ax1.axvline(last_improv, color="#dc2626", linewidth=0.8, linestyle=":",
                     alpha=0.7, label=f"Last improvement (iter {last_improv})")

    ax1.set_xlabel("Iteration", fontsize=11, fontweight="medium")
    ax1.set_ylabel("Cost", fontsize=11, fontweight="medium")
    ax1.set_title("Simulated Annealing Convergence", fontsize=14, fontweight="bold",
                  pad=12)

    # Thousands separator on y-axis
    ax1.yaxis.set_major_formatter(ticker.FuncFormatter(lambda x, _: f"{x:,.0f}"))
    ax1.xaxis.set_major_formatter(ticker.FuncFormatter(lambda x, _: f"{int(x):,}"))

    # Temperature on secondary axis
    ax2 = ax1.twinx()
    ax2.plot(iterations, temperatures, color="#f87171", alpha=0.35, linewidth=0.9,
             linestyle="--", label="Temperature")
    ax2.set_ylabel("Temperature", fontsize=11, color="#dc2626", fontweight="medium")
    ax2.tick_params(axis="y", labelcolor="#dc2626")
    ax2.yaxis.set_major_formatter(ticker.FuncFormatter(lambda x, _: f"{x:,.0f}"))

    # Combined legend (compact)
    lines1, labels1 = ax1.get_legend_handles_labels()
    lines2, labels2 = ax2.get_legend_handles_labels()
    ax1.legend(lines1 + lines2, labels1 + labels2, loc="upper right", fontsize=8,
               framealpha=0.9, edgecolor="#d1d5db")

    # ── Key statistics box ──────────────────────────────────────────────────
    best_final = min(best_costs)
    initial_best = best_costs[0]
    improvement_pct = ((initial_best - best_final) / initial_best * 100) if initial_best > 0 else 0
    stats_text = (
        f"Total iterations : {iterations[-1]:,}\n"
        f"Initial cost     : {initial_best:,.1f}\n"
        f"Best cost        : {best_final:,.1f}\n"
        f"Improvement      : {improvement_pct:.1f}%\n"
        f"T\u2080 = {temperatures[0]:,.1f}   T_final = {temperatures[-1]:,.1f}"
    )
    ax1.text(
        0.02, 0.58, stats_text, transform=ax1.transAxes, fontsize=8.5,
        verticalalignment="top", fontfamily="monospace",
        bbox=dict(boxstyle="round,pad=0.5", facecolor="#fef3c7",
                  edgecolor="#d97706", alpha=0.9, linewidth=0.8),
    )

    ax1.grid(True, alpha=0.15, linewidth=0.5)
    ax1.spines["top"].set_visible(False)
    ax2.spines["top"].set_visible(False)
    fig.tight_layout()

    # Save PNG next to the CSV
    png_path = path.with_suffix(".png")
    fig.savefig(png_path, dpi=180, bbox_inches="tight")
    print(f"Plot saved: {png_path}")

    plt.close(fig)
    return str(png_path)


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python plot_convergence.py <convergence.csv>")
        sys.exit(1)
    plot_convergence(sys.argv[1])
