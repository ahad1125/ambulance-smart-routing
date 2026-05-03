

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

        if node_id not in self.adj:
            self.adj[node_id] = []
        self.coords[node_id] = (lat, lon)
        self.node_label[node_id] = label

    def add_edge(self, src_id, dst_id, weight):

        if src_id in self.adj:
            self.adj[src_id].append((dst_id, weight))

    def get_neighbours(self, node_id):
        """Return list of (neighbour_id, weight) for a given node."""
        return self.adj.get(node_id, [])

    def all_nodes(self):
        """Return a list of all node IDs in the graph."""
        return list(self.adj.keys())

    def heuristic(self, a_id, b_id):

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