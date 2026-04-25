"""
core/algorithms/mst.py

PURPOSE:
  Implements Prim's and Kruskal's algorithms to find the
  Minimum Spanning Tree (MST) of the road network.

WHAT IS AN MST?
  Given a connected, weighted graph, an MST is a subset of edges that:
    1. Connects ALL nodes (spanning)
    2. Has NO cycles (tree)
    3. Has the MINIMUM total weight of all such spanning trees

USE CASE IN THIS PROJECT:
  "What is the minimum total road length needed to connect all hospitals?"
  If you're building new roads to connect hospitals, the MST tells you
  the cheapest way to do it with zero redundancy.

GREEDY APPROACH:
  Both Prim's and Kruskal's are GREEDY algorithms:
  they always pick the locally best option (cheapest edge) at each step.
  The Greedy Choice Property guarantees this produces a globally optimal result.

CLO COVERAGE:
  CLO 6: Greedy design strategy
  CLO 7: MST algorithms
  CLO 3/5: Big-O complexity analysis
"""

import heapq  # For Prim's priority queue
import time


# ─────────────────────────────────────────────────────────────
# 1. PRIM'S ALGORITHM
# ─────────────────────────────────────────────────────────────

def prims(graph):
    """
    Finds the MST by growing ONE tree from an arbitrary starting node.

    HOW IT WORKS:
      1. Start from any node. Add it to the MST set.
      2. Find the minimum-weight edge that connects the MST set to
         a node NOT yet in the MST set.
      3. Add that edge and the new node to the MST set.
      4. Repeat until all nodes are in the MST.

    ANALOGY: It's like building a road network starting from one city —
    at each step you build the cheapest possible road to a new city.

    WHY USE A PRIORITY QUEUE?
      At each step we need the minimum-weight edge crossing the cut.
      A min-heap lets us get that minimum in O(log E) instead of O(E).

    TIME COMPLEXITY:  O((V + E) log V) with a binary heap
      - Each node added to MST: V heap pops = O(V log V)
      - Each edge pushed to heap: E pushes = O(E log V)

    SPACE COMPLEXITY: O(V + E) — heap can hold all edges

    BEST FOR: Dense graphs (many edges) where V is small relative to E.
    """
    start_time = time.time()
    nodes = graph.all_nodes()

    if not nodes:
        return {"mst_edges": [], "total_weight": 0}

    # Track which nodes are already in the MST
    in_mst = set()

    # mst_edges: list of (u, v, weight) tuples forming the MST
    mst_edges = []
    total_weight = 0

    # Start from the first node
    start = nodes[0]
    in_mst.add(start)

    # Min-heap of (weight, from_node, to_node)
    # Initially: push all edges from the start node
    heap = []
    for neighbour, weight in graph.get_neighbours(start):
        heapq.heappush(heap, (weight, start, neighbour))

    edges_examined = 0

    while heap and len(in_mst) < len(nodes):
        # Get the cheapest edge crossing the cut
        weight, u, v = heapq.heappop(heap)
        edges_examined += 1

        # If v is already in MST, this edge would create a cycle — skip it
        if v in in_mst:
            continue

        # Add v to the MST
        in_mst.add(v)
        mst_edges.append((u, v, weight))
        total_weight += weight

        # Push all edges from v to nodes NOT yet in MST
        for neighbour, w in graph.get_neighbours(v):
            if neighbour not in in_mst:
                heapq.heappush(heap, (w, v, neighbour))

    elapsed_ms = round((time.time() - start_time) * 1000, 3)

    # Build a list with coordinate info for the frontend to draw on the map
    mst_with_coords = []
    for u, v, w in mst_edges:
        mst_with_coords.append({
            "from_node":  u,
            "to_node":    v,
            "weight":     round(w, 4),
            "from_coords": list(graph.coords.get(u, [0, 0])),
            "to_coords":   list(graph.coords.get(v, [0, 0])),
        })

    return {
        "algorithm":       "Prim's",
        "mst_edges":       mst_with_coords,
        "total_weight":    round(total_weight, 4),
        "nodes_in_mst":    len(in_mst),
        "edges_in_mst":    len(mst_edges),
        "edges_examined":  edges_examined,
        "execution_time_ms": elapsed_ms,
        "complexity":      "O((V+E) log V)",
        "space":           "O(V+E)",
        "best_for":        "Dense graphs",
    }


# ─────────────────────────────────────────────────────────────
# UNION-FIND (Disjoint Set Union) — used by Kruskal's
# ─────────────────────────────────────────────────────────────

class UnionFind:
    """
    A data structure that tracks connected components.

    OPERATIONS:
      find(x) → returns the "representative" (root) of x's component
      union(x, y) → merges the components of x and y

    WHY IT'S NEEDED:
      Kruskal's adds edges in order of increasing weight.
      Before adding an edge (u, v), we need to check: are u and v
      already connected? If yes, adding this edge would create a cycle.
      UnionFind answers "are they connected?" in nearly O(1).

    OPTIMISATIONS:
      1. Union by rank: attach smaller tree under larger tree
         → keeps the tree shallow → faster find()
      2. Path compression: when doing find(), make all nodes on the path
         point directly to root → even faster future finds()

    TIME COMPLEXITY:  O(α(n)) per operation, where α is the inverse
                      Ackermann function — essentially constant.
    """

    def __init__(self, elements):
        # Each element is its own parent initially (one-node components)
        self.parent = {e: e for e in elements}
        # Rank is used to keep the tree balanced during union
        self.rank   = {e: 0 for e in elements}

    def find(self, x):
        """
        Returns the root (representative) of x's component.
        Uses PATH COMPRESSION: after finding root, make x point directly to it.
        """
        if self.parent[x] != x:
            # Recursively find root, then compress the path
            self.parent[x] = self.find(self.parent[x])
        return self.parent[x]

    def union(self, x, y):
        """
        Merges the components of x and y.
        Uses UNION BY RANK to keep the tree balanced.
        Returns False if x and y were already in the same component (cycle!).
        """
        root_x = self.find(x)
        root_y = self.find(y)

        # Already in the same component → adding this edge would make a cycle
        if root_x == root_y:
            return False

        # Attach smaller rank tree under larger rank tree
        if self.rank[root_x] < self.rank[root_y]:
            self.parent[root_x] = root_y
        elif self.rank[root_x] > self.rank[root_y]:
            self.parent[root_y] = root_x
        else:
            # Equal rank: pick one as root and increase its rank
            self.parent[root_y] = root_x
            self.rank[root_x] += 1

        return True  # Successfully merged — edge is valid for MST


# ─────────────────────────────────────────────────────────────
# 2. KRUSKAL'S ALGORITHM
# ─────────────────────────────────────────────────────────────

def kruskals(graph):
    """
    Finds the MST by sorting ALL edges and greedily adding the cheapest
    edge that doesn't create a cycle.

    HOW IT WORKS:
      1. Sort ALL edges by weight (cheapest first).
      2. For each edge (u, v) in order:
           - If u and v are in different components → add edge to MST (safe)
           - If u and v are already connected → skip (would create cycle)
      3. Stop when MST has V-1 edges (all nodes connected).

    USES UNION-FIND to check in O(α(n)) ≈ O(1) whether adding an edge
    would create a cycle.

    TIME COMPLEXITY:  O(E log E)
      - Sorting E edges: O(E log E)
      - Union-Find operations: nearly O(E)
      - Total: dominated by sorting → O(E log E)
      Note: O(E log E) ≈ O(E log V) since E ≤ V²

    SPACE COMPLEXITY: O(V + E) — store all edges, UnionFind for all nodes

    BEST FOR: Sparse graphs (few edges) since we sort all edges first.

    COMPARE WITH PRIM'S:
      Prim's grows one tree → better for dense graphs
      Kruskal's sorts all edges → better for sparse graphs
      For our Lahore grid, both give the SAME MST (just computed differently)
    """
    start_time = time.time()
    nodes = graph.all_nodes()

    if not nodes:
        return {"mst_edges": [], "total_weight": 0}

    # Collect ALL edges from the graph into a flat list
    all_edges = []
    for u in nodes:
        for v, weight in graph.get_neighbours(u):
            all_edges.append((weight, u, v))

    # ── Step 1: Sort all edges by weight (cheapest first) ──
    # TIME: O(E log E)
    all_edges.sort(key=lambda x: x[0])

    # ── Step 2: Process edges greedily ──
    uf = UnionFind(nodes)
    mst_edges = []
    total_weight = 0
    edges_examined = 0

    for weight, u, v in all_edges:
        edges_examined += 1

        # Try to add this edge — union() returns False if it creates a cycle
        if uf.union(u, v):
            mst_edges.append((u, v, weight))
            total_weight += weight

        # MST is complete when it has exactly V-1 edges
        if len(mst_edges) == len(nodes) - 1:
            break

    elapsed_ms = round((time.time() - start_time) * 1000, 3)

    # Build response with coordinates for frontend map drawing
    mst_with_coords = []
    for u, v, w in mst_edges:
        mst_with_coords.append({
            "from_node":   u,
            "to_node":     v,
            "weight":      round(w, 4),
            "from_coords": list(graph.coords.get(u, [0, 0])),
            "to_coords":   list(graph.coords.get(v, [0, 0])),
        })

    return {
        "algorithm":       "Kruskal's",
        "mst_edges":       mst_with_coords,
        "total_weight":    round(total_weight, 4),
        "nodes_in_mst":    len(set([e["from_node"] for e in mst_with_coords] +
                                   [e["to_node"]   for e in mst_with_coords])),
        "edges_in_mst":    len(mst_edges),
        "edges_examined":  edges_examined,
        "execution_time_ms": elapsed_ms,
        "complexity":      "O(E log E)",
        "space":           "O(V+E)",
        "best_for":        "Sparse graphs",
    }
