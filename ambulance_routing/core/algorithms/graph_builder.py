"""
core/algorithms/graph_builder.py

PURPOSE:
  Builds an in-memory Graph object from the database (Node + Edge tables).
  Every algorithm (Dijkstra, BFS, MST, etc.) works on this Graph object —
  they do NOT query the database directly. This separation keeps algorithms
  clean and testable without Django.

HOW IT WORKS:
  1. We query all Nodes and Edges from SQLite.
  2. We create a Graph object and add each node/edge to it.
  3. The Graph uses an adjacency list: { node_id: [(neighbor_id, weight), ...] }
  4. We also store coordinates (lat/lon) for the A* heuristic and map display.

ADJACENCY LIST EXPLAINED:
  Instead of a 2D matrix (expensive for sparse graphs), we store
  each node's neighbours as a list. For a road network with thousands
  of nodes but only a few roads per intersection, this is much more
  memory-efficient.

  Example:
    adj = {
      1: [(2, 5.0), (3, 7.0)],   # node 1 connects to 2 (5km) and 3 (7km)
      2: [(4, 3.0)],               # node 2 connects to 4 (3km)
    }
"""

import math
from core.models import Node, Edge


# ─────────────────────────────────────────────────────────────
# GRAPH CLASS — the core data structure used by all algorithms
# ─────────────────────────────────────────────────────────────

class Graph:
    def __init__(self):
        # adj[node_id] = list of (neighbour_id, weight) tuples
        # We use node database IDs (integers) as keys
        self.adj = {}

        # coords[node_id] = (latitude, longitude)
        # Needed by A* for the Euclidean heuristic
        self.coords = {}

        # node_label[node_id] = "N_0_0" — for display in frontend
        self.node_label = {}

    def add_node(self, node_id, lat, lon, label):
        """Register a node. Creates an empty neighbour list if not yet present."""
        if node_id not in self.adj:
            self.adj[node_id] = []
        self.coords[node_id] = (lat, lon)
        self.node_label[node_id] = label

    def add_edge(self, src_id, dst_id, weight):
        """
        Add a directed edge from src_id → dst_id with the given weight.
        We call this twice (src→dst and dst→src) for bidirectional roads.
        """
        if src_id in self.adj:
            self.adj[src_id].append((dst_id, weight))

    def get_neighbours(self, node_id):
        """Return list of (neighbour_id, weight) for a given node."""
        return self.adj.get(node_id, [])

    def all_nodes(self):
        """Return a list of all node IDs in the graph."""
        return list(self.adj.keys())

    def heuristic(self, a_id, b_id):
        """
        Haversine straight-line distance (in km) between two nodes.

        WHY HAVERSINE?
          - Returns distance in KILOMETRES — the same unit as edge weights.
            The old Euclidean-in-degrees heuristic returned ~0.01 for nodes
            that are ~1 km apart, making it negligible and A* ≈ Dijkstra.
          - Still ADMISSIBLE: straight-line distance never exceeds road
            distance, so A* is guaranteed to find the optimal path.
          - Haversine accounts for Earth's curvature, giving an accurate
            great-circle distance even at city scale.

        HOW IT WORKS:
          Uses the Haversine formula:
            a = sin²(Δlat/2) + cos(lat1) · cos(lat2) · sin²(Δlon/2)
            c = 2 · atan2(√a, √(1−a))
            d = R · c          where R = 6371 km (Earth's radius)

        TIME COMPLEXITY: O(1) — constant, just arithmetic.
        """
        if a_id not in self.coords or b_id not in self.coords:
            return 0  # Fallback: if coords missing, heuristic = 0 → A* behaves like Dijkstra

        lat1, lon1 = self.coords[a_id]
        lat2, lon2 = self.coords[b_id]

        # Convert degrees to radians
        lat1_r, lon1_r = math.radians(lat1), math.radians(lon1)
        lat2_r, lon2_r = math.radians(lat2), math.radians(lon2)

        dlat = lat2_r - lat1_r
        dlon = lon2_r - lon1_r

        # Haversine formula
        a = math.sin(dlat / 2) ** 2 + \
            math.cos(lat1_r) * math.cos(lat2_r) * math.sin(dlon / 2) ** 2
        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))

        R = 6371.0  # Earth's radius in km
        return R * c


# ─────────────────────────────────────────────────────────────
# BUILD GRAPH FROM DATABASE
# ─────────────────────────────────────────────────────────────

def build_graph(use_traffic=False):
    """
    Queries all Nodes and Edges from SQLite and builds an in-memory Graph.

    PARAMETER:
      use_traffic (bool): If True, multiply edge weight by traffic_weight.
                          This is used by the Traffic Control page to show
                          how Bellman-Ford handles variable edge weights.

    RETURNS:
      A fully populated Graph object ready for any algorithm.

    TIME COMPLEXITY: O(V + E) — we visit every node and edge once.
    SPACE COMPLEXITY: O(V + E) — we store the full graph in memory.
    """
    graph = Graph()

    # ── Step 1: Add all nodes ──────────────────────────────────
    # We use the DB primary key (id) as the node identifier in algorithms.
    # This avoids string comparisons and keeps things fast.
    for node in Node.objects.all():
        graph.add_node(node.id, node.latitude, node.longitude, node.label)

    # ── Step 2: Add all edges ──────────────────────────────────
    # select_related('source', 'destination') fetches the related Node
    # objects in one SQL query instead of N+1 queries — much faster.
    for edge in Edge.objects.select_related('source', 'destination').all():
        # Choose the weight based on traffic toggle
        if use_traffic:
            weight = edge.distance * edge.traffic_weight  # Apply congestion multiplier
        else:
            weight = edge.distance                         # Raw distance in km

        # Directed edge: source → destination
        graph.add_edge(edge.source.id, edge.destination.id, weight)

    return graph