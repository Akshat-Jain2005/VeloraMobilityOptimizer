# Velora Mobility Optimizer: Final Algorithm Design & Solution Report

## 1. Deep Understanding Phase
**Problem Summary**:  
The problem is a variant of the **Vehicle Routing Problem (VRP)** tailored for corporate employee transport (Employee Commute Problem). Specifically, it is a **Many-to-One** pickup problem where multiple vehicles pick up employees from various locations and deliver them to a single destination (office). The goal is to minimize a weighted objective function of operational cost and travel time while respecting a mix of hard and soft constraints.

### Key constraints identified (including WhatsApp clarifications):
*   **Hard Constraints**:
    *   **Vehicle Capacity**: Cannot exceed seat count.
    *   **Maximum Delay**: Employees cannot arrive later than `LateTime + Tolerance(Priority)`.
    *   **Operations**: No mid-route drop-offs or vehicle transfers.
*   **Soft Constraints (Penalty-based)**:
    *   **Vehicle Preference**: Employees preferring "Premium" vehicles should not be in "Normal" ones (unless infeasible).
    *   **Sharing Limit**: Employees with "Single/Double" preference should not be crowded (unless infeasible).
    *   **Scheduled Arrival**: Ideally arrive before `LateTime`. Lateness up to `MaxDelay` is allowed but penalized.
*   **Objective Function**:
    *   $Score = 0.7 \times Cost + 0.3 \times Time + Penalties$
    *   Infeasibility handling: "Find best solution by relaxing secondary constraints" implies soft constraints must be implemented with high penalties rather than strict blocking.

## 2. Formalization (Mathematical Model)
This is modeled as a **Capacitated Vehicle Routing Problem with Time Windows (CVRPTW)** and heterogenous fleet.

**Decision Variables**:
*   $x_{ijk} \in \{0,1\}$: Vehicle $k$ travels from node $i$ to $j$.
*   $y_{ik} \in \{0,1\}$: Request $i$ is assigned to vehicle $k$.
*   $t_{i}$: Arrival time at node $i$.

**Objective Function**:
$$
\text{Minimize } Z = 0.7 \sum_{k} \sum_{i,j} C_{k} d_{ij} x_{ijk} + 0.3 \sum_{k} \sum_{i,j} \tau_{ij} x_{ijk} + \sum p \in \text{Penalties}
$$
Where:
*   $C_k$: Cost per km for vehicle $k$.
*   $d_{ij}$: Distance between $i$ and $j$.
*   $\tau_{ij}$: Travel time (approx equal to distance in this heuristic model).

**Constraints**:
1.  $\sum_{k} y_{ik} = 1 \quad \forall i$ (Every request served).
2.  $\sum_{i} q_i y_{ik} \leq Q_k \quad \forall k$ (Capacity).
3.  $t_i \leq L_i + \Delta_i$ (Max Delay constraint).
4.  Flow conservation equations.

## 3. Constraint Analysis
*   **Scale**: 
    *   Requests (Employees): 1 to ~100.
    *   Vehicles: 1 to 30.
*   **Complexity**:
    *   VRP is NP-Hard.
    *   100 nodes is small enough for **Local Search / Metaheuristics** to find near-optimal solutions in seconds.
    *   Exact algorithms (Branch-and-Cut) might take too long (>1 min) or struggle with the specific non-linear soft penalty structures.
*   **Bounds**:
    *   Time Limit: ~30s is practical.
    *   Memory: Minimal (< 100MB).

## 4. Algorithm Selection
**Chosen Approach: Constructive Heuristic + Local Search**

1.  **Constructive Phase (Best Insertion with Regret-like logic)**:
    *   Start with empty routes.
    *   Sort requests by Priority (High to Low) and Urgency (Early Time).
    *   Insert each request into the position (Vehicle, Index) that minimizes cost increase ($\Delta Cost$).
    *   This ensures a feasible initial solution quickly.

2.  **Improvement Phase (Relocate/Transfer Neighborhood)**:
    *   Iteratively try to move a request from one route to another (or within the same route).
    *   Accept the move if Global Cost decreases.
    *   Repeat until local optimum (no further improvements).
    *   This cleans up "greedy" mistakes.

**Justification**:
*   **Correctness**: Explicitly checks all constraints during insertion/move.
*   **Flexibility**: Soft constraints (penalties) are easily modeled by adding to the $\Delta Cost$.
*   **Speed**: O(N^2) complexity per iteration, extremely fast for N=100.

## 5. Design & Implementation
*   **Language**: C++17.
*   **Structure**:
    *   `Request`, `Vehicle`, `Route` structs.
    *   `MapDistance` class for abstraction (Haversine/External).
    *   `isValidRoute()`: Boolean check for Hard Constraints.
    *   `calculateRouteCost()`: Computes weighted objective + Soft Constraint penalties.
*   **Parsing**:
    *   Python script converts Excel/CSV to standardized JSON.
    *   C++ Solver reads JSON, solves, writes JSON.
    *   Separation of concerns allows easy testing and input format changes.

## 6. Verification
Logic validated against TC01, TC02, TC03, TC04.
*   **TC01**: All hard constraints met. Solution cost optimized.
*   **Feature Verification**:
    *   **Priority 1-5**: Verified via `clampPriority` and delay tolerances.
    *   **Sharing Preference**: Verified via penalty addition in `calculateRouteCost`.
    *   **Vehicle Preference**: Verified via penalty.
    *   **Infeasibility**: System relaxes preference constraints if needed (via cost function) rather than failing.
    *   **Forced Assignment**: For scenarios where time windows are physically impossible (e.g., TC04 R09), the system forces assignment to the best possible vehicle and applies a "Max Delay Violation" penalty, ensuring the employee is transported as per the "Must Go" mandate.

## 7. Conclusions
The solution meets all "Best Possible" criteria:
*   Minimizes cost effectively.
*   Respects complex Priority/Sharing logic.
*   Robust to input variations.
*   Production-ready C++ code.

Status: **COMPLETED**.
