# Algorithm Design

## Hybrid Optimization Strategy

The Velora Mobility Optimizer uses a two-phase hybrid metaheuristic approach to solve the Vehicle Routing Problem with Time Windows (VRPTW).

### Phase 1: Constructive Heuristic (Greedy + Regret)
To generate a high-quality initial solution quickly:
1. **Sorting**: Requests are sorted by Priority (P1 > P5) and then by Time Window strings (tightest first).
2. **Parallel Selection**: The algorithm attempts to insert higher-priority requests first.
3. **Best Insertion**: For each request, the solver evaluates all possible positions in all valid routes.
   - It checks **Time Feasibility** (Arrival Time + Service Time <= Window End + Tolerance).
   - It checks **Capacity**.
   - It calculates the **Marginal Cost** (Increase in total distance/time).
4. **Forced Insertion Fallback**: If a request cannot be inserted feasibly (e.g., due to tight time window), the system relaxes the time constraint and forces insertion at the position of minimum violation. This ensures complete service coverage at the cost of solution quality penalties.

### Phase 2: Simulated Annealing (Metaheuristic)
To escape local optima and refine the solution:
- **Objective**: Minimize `Global Cost = w1 * TotalDistance + w2 * TotalTime + Penalties`.
- **Mechanism**:
    - **Initial Temperature ($T_0$)**: 200.0
    - **Cooling Rate ($\alpha$)**: 0.99
    - **Iterations**: 5000
    - **Metropolis Criterion**: 
      $$ P(accept) = \begin{cases} 1 & \text{if } \Delta E < 0 \\ e^{-\Delta E / T} & \text{if } \Delta E > 0 \end{cases} $$
- **Neighborhood Operators**:
    - **Relocate**: Removes a random request from its current route and inserts it into a different route (or different position) using Best-Fit logic.
    - **Swap** (Implicit via Relocate sequences): Over many iterations, requests swap routes.
    
### Cost Function
$$ Cost = (\sum Distance \times C_{km}) + (\sum Time \times C_{time}) + \sum (Violation \times P_{penalty}) $$

- **Distance**: Euclidean or Real-road distance (via OSRM).
- **Time**: Travel time + Service time.
- **Violation**: Weighted heavily (e.g., 10000) for Time Window violations in forced assignments.

## Handling Edge Cases

### Laggy Map API
- **Problem**: External Distance Matrix APIs can be slow or fail.
- **Solution**: A **Circuit Breaker** pattern.
    - Set `CURLOPT_TIMEOUT` to 100ms.
    - If a request times out or fails 3 times, the system globally disables the API and falls back to **Haversine Distance** for the remainder of the session.

### "Impossible" Requests (TC04 Case)
- **Problem**: Employee 9 has a travel time of 45m but a window of 30m.
- **Solution**: 
    1. Try Strict Insertion -> Fails.
    2. Try Forced Insertion -> Succeeds with Penalty.
    3. Report: "Violation: 15m delay (Forced)".

## Complexity
- **Time Complexity**: $O(Iter \times N \times V)$ where $N$ is requests, $V$ is vehicles. With $N=100, Iter=5000$, this runs in < 2 seconds on modern hardware.
- **Space Complexity**: $O(N + V)$ for storing the solution state.
