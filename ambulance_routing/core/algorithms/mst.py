

import heapq  # For Prim's priority queue
import time


# ─────────────────────────────────────────────────────────────
# 1. PRIM'S ALGORITHM
# ─────────────────────────────────────────────────────────────

def prims(graph):

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


    def __init__(self, elements):
        # Each element is its own parent initially (one-node components)
        self.parent = {e: e for e in elements}
        # Rank is used to keep the tree balanced during union
        self.rank   = {e: 0 for e in elements}

    def find(self, x):

        if self.parent[x] != x:
            # Recursively find root, then compress the path
            self.parent[x] = self.find(self.parent[x])
        return self.parent[x]

    def union(self, x, y):

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
