"""
core/algorithms/dp_multistop.py

PURPOSE:
  Dynamic Programming solution for the Multi-Stop Ambulance Routing problem.
  Given a list of stops (patient locations), find the optimal visit order
  that minimises total travel distance.

  This is a variant of the Travelling Salesman Problem (TSP) solved using
  DP with bitmask memoisation — the Held-Karp algorithm.

DESIGN STRATEGY: Dynamic Programming
  Classic DP properties:
    1. Optimal Substructure: the optimal path through all stops includes
       optimal sub-paths through subsets of stops.
    2. Overlapping Subproblems: the same (visited_mask, current_node) state
       appears in many different orderings — we cache the result.

BITMASK REPRESENTATION:
  With n stops, we represent "which stops have been visited" as an n-bit integer.
  e.g. for n=4: mask=0110 means stops 1 and 2 visited, stops 0 and 3 not yet.
  This gives 2^n possible subsets — the DP table has 2^n × n entries.

TIME COMPLEXITY:  O(2^n × n²)
  - 2^n possible subsets of stops
  - n choices of current stop in each subset
  - n transitions from each state
  Much better than O(n!) brute force: for n=10, 2^10×100=102400 vs 10!=3628800

SPACE COMPLEXITY: O(2^n × n)
  The memoisation table stores 2^n × n entries.

PRACTICAL LIMIT:
  Works well for n ≤ 15 stops. For n > 15, use heuristics (nearest-neighbour).
  For this project we cap at 8 stops.

CLO COVERAGE:
  CLO 6: Dynamic Programming design strategy
  CLO 3/5: Time/space complexity analysis
"""

import time
import itertools


# ─────────────────────────────────────────────────────────────
# BRUTE FORCE MULTI-STOP — O(n!) — for comparison
# ─────────────────────────────────────────────────────────────

def brute_force_multistop(dist_matrix, stop_names):
    """
    Try every possible ordering of stops. O(n!) — infeasible for n > 10.

    Used on the Multi-Stop page to show WHY we need DP.
    For 5 stops: 5! = 120 orderings checked.
    For 8 stops: 8! = 40,320 orderings checked.
    For 12 stops: 12! = 479,001,600 orderings — impossible.
    """
    start_time = time.time()
    n = len(stop_names)

    if n == 0:
        return {"total_distance": 0, "order": [], "orderings_checked": 0, "time_ms": 0}

    indices = list(range(n))
    best_dist = float('inf')
    best_order = None
    orderings_checked = 0

    # Try every permutation of stop indices
    for perm in itertools.permutations(indices):
        orderings_checked += 1
        total = 0
        for i in range(len(perm) - 1):
            total += dist_matrix[perm[i]][perm[i + 1]]
        if total < best_dist:
            best_dist = total
            best_order = list(perm)

    elapsed_ms = round((time.time() - start_time) * 1000, 3)

    return {
        "algorithm": "Brute Force",
        "total_distance": round(best_dist, 3) if best_dist != float('inf') else -1,
        "order": [stop_names[i] for i in best_order] if best_order else [],
        "order_indices": best_order or [],
        "orderings_checked": orderings_checked,
        "execution_time_ms": elapsed_ms,
        "complexity": f"O(n!) = O({n}!) = {orderings_checked:,} orderings",
        "space": "O(n)",
    }


# ─────────────────────────────────────────────────────────────
# DP MULTI-STOP (Held-Karp) — O(2^n × n²)
# ─────────────────────────────────────────────────────────────

def dp_multistop(dist_matrix, stop_names):
    """
    Held-Karp DP algorithm: finds optimal multi-stop visit order.

    HOW IT WORKS:
      State: dp[mask][i] = minimum cost to visit all stops in `mask`,
             ending at stop i.
      mask is an integer: bit j set → stop j has been visited.

      Base case:  dp[1 << i][i] = 0  (start at stop i, cost 0)
      Transition: dp[mask | (1 << j)][j] = dp[mask][i] + dist[i][j]
                  for all j not in mask

      We try every possible starting stop and pick the best.

    PARAMETERS:
      dist_matrix : n×n matrix where dist_matrix[i][j] = distance from stop i to j
      stop_names  : list of n stop name strings (for display)

    RETURNS:
      dict with optimal order, total distance, and algorithm stats
    """
    start_time = time.time()
    n = len(stop_names)

    if n == 0:
        return {"total_distance": 0, "order": [], "time_ms": 0}

    if n == 1:
        return {
            "algorithm": "DP (Held-Karp)",
            "total_distance": 0,
            "order": [stop_names[0]],
            "order_indices": [0],
            "execution_time_ms": 0,
            "complexity": "O(2^n × n²)",
            "space": f"O(2^{n} × {n})",
            "dp_states": 1,
            "transitions": 0,
        }

    # dp[mask][i] = min cost to reach stop i having visited all stops in mask
    INF = float('inf')
    dp = [[INF] * n for _ in range(1 << n)]
    parent = [[-1] * n for _ in range(1 << n)]

    # Count DP operations for stats display
    dp_states = 0
    transitions = 0

    # ── Try every possible starting stop ────────────────────
    best_overall = INF
    best_start = 0

    for start in range(n):
        # Initialize: start at `start`, only it is visited
        dp[1 << start][start] = 0

    # ── Fill DP table ────────────────────────────────────────
    for mask in range(1, 1 << n):
        for i in range(n):
            if not (mask >> i & 1):
                continue  # Stop i not in this mask
            if dp[mask][i] == INF:
                continue

            dp_states += 1

            # Try going to each unvisited stop j
            for j in range(n):
                if mask >> j & 1:
                    continue  # Already visited j

                transitions += 1
                new_mask = mask | (1 << j)
                new_cost = dp[mask][i] + dist_matrix[i][j]

                if new_cost < dp[new_mask][j]:
                    dp[new_mask][j] = new_cost
                    parent[new_mask][j] = i

    # ── Find best ending stop (all stops visited) ────────────
    full_mask = (1 << n) - 1
    best_end = -1

    for i in range(n):
        if dp[full_mask][i] < best_overall:
            best_overall = dp[full_mask][i]
            best_end = i

    # ── Reconstruct path ─────────────────────────────────────
    path = []
    if best_end != -1:
        mask = full_mask
        cur = best_end
        while cur != -1:
            path.append(cur)
            prev = parent[mask][cur]
            mask = mask ^ (1 << cur)
            cur = prev
        path.reverse()

    elapsed_ms = round((time.time() - start_time) * 1000, 3)

    return {
        "algorithm": "DP (Held-Karp)",
        "total_distance": round(best_overall, 3) if best_overall != INF else -1,
        "order": [stop_names[i] for i in path],
        "order_indices": path,
        "execution_time_ms": elapsed_ms,
        "complexity": f"O(2^n × n²) = O(2^{n} × {n}²) = {(1<<n)*n*n:,} max ops",
        "space": f"O(2^{n} × {n})",
        "dp_states": dp_states,
        "transitions": transitions,
    }


# ─────────────────────────────────────────────────────────────
# HELPER: build distance matrix from graph + stop node IDs
# ─────────────────────────────────────────────────────────────

def build_dist_matrix(graph, node_ids, shortest_path_fn):
    """
    Build an n×n distance matrix by running Dijkstra between every pair.

    Parameters:
      graph          : the Graph object
      node_ids       : list of n node IDs (the stops)
      shortest_path_fn : e.g. dijkstra function from shortest_path.py

    Returns:
      n×n matrix (list of lists), or None if any pair is unreachable
    """
    n = len(node_ids)
    matrix = [[0.0] * n for _ in range(n)]

    for i in range(n):
        for j in range(n):
            if i == j:
                matrix[i][j] = 0.0
            else:
                result = shortest_path_fn(graph, node_ids[i], node_ids[j])
                d = result.get("distance", -1)
                matrix[i][j] = d if d != -1 else 999999.0

    return matrix


# ─────────────────────────────────────────────────────────────
# STANDALONE TEST
# ─────────────────────────────────────────────────────────────

if __name__ == "__main__":
    # Test with 5 stops (manually specified distance matrix)
    stops = ["Emergency", "Hospital A", "Hospital B", "Hospital C", "Depot"]
    dist = [
        [0,   3.2, 5.1, 7.4, 2.1],
        [3.2, 0,   2.3, 4.1, 5.0],
        [5.1, 2.3, 0,   1.9, 3.8],
        [7.4, 4.1, 1.9, 0,   6.2],
        [2.1, 5.0, 3.8, 6.2, 0  ],
    ]

    dp_result = dp_multistop(dist, stops)
    bf_result = brute_force_multistop(dist, stops)

    print("=== DP Result ===")
    print(f"  Order:    {' → '.join(dp_result['order'])}")
    print(f"  Distance: {dp_result['total_distance']} km")
    print(f"  Time:     {dp_result['execution_time_ms']} ms")
    print(f"  States:   {dp_result['dp_states']}")

    print("\n=== Brute Force Result ===")
    print(f"  Order:    {' → '.join(bf_result['order'])}")
    print(f"  Distance: {bf_result['total_distance']} km")
    print(f"  Orderings checked: {bf_result['orderings_checked']}")

    assert abs(dp_result['total_distance'] - bf_result['total_distance']) < 0.001, \
        "DP and Brute Force disagree!"
    print("\n✅ Both agree on optimal distance")
