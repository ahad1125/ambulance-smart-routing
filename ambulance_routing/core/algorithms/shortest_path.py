

import heapq  # Python's built-in min-heap (priority queue)
import time
from collections import deque


# ─────────────────────────────────────────────────────────────
# HELPER: reconstruct path from predecessor dict
# ─────────────────────────────────────────────────────────────

def _reconstruct_path(prev, start_id, end_id):

    path = []
    current = end_id

    # Walk backwards until we hit None (start node has no predecessor)
    while current is not None:
        path.append(current)
        current = prev.get(current)  # .get returns None if key doesn't exist

    path.reverse()  # We built it backwards, so reverse it

    # Sanity check: if path doesn't start at start_id, no path was found
    if not path or path[0] != start_id:
        return []

    return path


# ─────────────────────────────────────────────────────────────
# 1. DIJKSTRA'S ALGORITHM
# ─────────────────────────────────────────────────────────────

def dijkstra(graph, start_id, end_id):

    start_time = time.time()

    # Initialise all distances to infinity (unknown)
    dist = {node: float('inf') for node in graph.all_nodes()}
    dist[start_id] = 0  # Distance to start node is 0

    # prev[v] = the node we came from to reach v (for path reconstruction)
    prev = {node: None for node in graph.all_nodes()}

    # Min-heap: each entry is (distance, node_id)
    # heapq in Python is a MIN-heap: heappop() gives the smallest element
    heap = [(0, start_id)]

    nodes_visited = 0   # How many nodes we fully processed
    edges_explored = 0  # How many edges we examined
    explored_edges = []  # Track (u, v) for every edge examined — used by frontend visualization

    while heap:
        # Pop the node with the smallest current known distance
        current_dist, u = heapq.heappop(heap)

        # IMPORTANT: If we've already found a better path to u, skip this stale entry
        # This can happen because Python's heapq doesn't support decrease-key
        if current_dist > dist[u]:
            continue

        nodes_visited += 1

        # Early exit: once we reach the destination, we're done
        if u == end_id:
            break

        # Relax all edges leaving u
        for v, weight in graph.get_neighbours(u):
            edges_explored += 1
            explored_edges.append((u, v))  # Record this edge exploration
            new_dist = dist[u] + weight

            # If this path to v is shorter than what we knew before → update
            if new_dist < dist[v]:
                dist[v] = new_dist
                prev[v] = u
                heapq.heappush(heap, (new_dist, v))

    elapsed_ms = round((time.time() - start_time) * 1000, 3)
    path = _reconstruct_path(prev, start_id, end_id)

    return {
        "algorithm":       "Dijkstra",
        "path":            path,                   # List of node IDs
        "distance":        dist[end_id] if dist[end_id] != float('inf') else -1,
        "nodes_visited":   nodes_visited,
        "edges_explored":  edges_explored,
        "explored_edges":  explored_edges,          # For frontend visualization
        "execution_time_ms": elapsed_ms,
        "complexity":      "O((V+E) log V)",       # Shown in the stats panel
        "space":           "O(V)",
    }


# ─────────────────────────────────────────────────────────────
# 2. A* ALGORITHM
# ─────────────────────────────────────────────────────────────

def astar(graph, start_id, end_id):

    start_time = time.time()

    # g_cost[v] = actual cost from start to v
    g_cost = {node: float('inf') for node in graph.all_nodes()}
    g_cost[start_id] = 0

    # f_cost[v] = g_cost[v] + heuristic(v, end)
    # This is what the heap sorts by
    f_cost = {node: float('inf') for node in graph.all_nodes()}
    f_cost[start_id] = graph.heuristic(start_id, end_id)

    prev = {node: None for node in graph.all_nodes()}

    # Min-heap sorted by f_cost
    heap = [(f_cost[start_id], start_id)]

    nodes_visited = 0
    edges_explored = 0
    explored_edges = []  # Track (u, v) for every edge examined

    while heap:
        current_f, u = heapq.heappop(heap)

        # Skip stale heap entries (same logic as Dijkstra)
        if current_f > f_cost[u]:
            continue

        nodes_visited += 1

        # Reached the goal!
        if u == end_id:
            break

        for v, weight in graph.get_neighbours(u):
            edges_explored += 1
            explored_edges.append((u, v))  # Record this edge exploration
            tentative_g = g_cost[u] + weight

            # If this path to v is better → update both g and f costs
            if tentative_g < g_cost[v]:
                g_cost[v] = tentative_g
                # f = actual cost so far + estimated remaining cost
                f_cost[v] = tentative_g + graph.heuristic(v, end_id)
                prev[v] = u
                heapq.heappush(heap, (f_cost[v], v))

    elapsed_ms = round((time.time() - start_time) * 1000, 3)
    path = _reconstruct_path(prev, start_id, end_id)

    return {
        "algorithm":       "A*",
        "path":            path,
        "distance":        g_cost[end_id] if g_cost[end_id] != float('inf') else -1,
        "nodes_visited":   nodes_visited,
        "edges_explored":  edges_explored,
        "explored_edges":  explored_edges,          # For frontend visualization
        "execution_time_ms": elapsed_ms,
        "complexity":      "O(b^d) — near-linear with Euclidean heuristic",
        "space":           "O(V)",
    }


# ─────────────────────────────────────────────────────────────
# 3. BELLMAN-FORD ALGORITHM
# ─────────────────────────────────────────────────────────────

def bellman_ford(graph, start_id, end_id):

    start_time = time.time()

    nodes = graph.all_nodes()
    V = len(nodes)

    # Initialise all distances to infinity
    dist = {node: float('inf') for node in nodes}
    dist[start_id] = 0

    prev = {node: None for node in nodes}

    # SPFA specific structures
    queue = deque([start_id])
    in_queue = {start_id}
    update_count = {node: 0 for node in nodes}

    nodes_visited = 0
    edges_explored = 0
    explored_edges = []  # Track (u, v) for every edge examined

    while queue:
        u = queue.popleft()
        in_queue.remove(u)
        nodes_visited += 1

        for v, weight in graph.get_neighbours(u):
            edges_explored += 1
            explored_edges.append((u, v))  # Record this edge exploration
            new_dist = dist[u] + weight

            if new_dist < dist[v]:
                dist[v] = new_dist
                prev[v] = u

                # Negative cycle detection
                update_count[v] += 1
                if update_count[v] >= V:
                    raise ValueError(f"Negative cycle detected involving nodes {u} → {v}")

                # If v isn't already waiting in the queue, add it
                if v not in in_queue:
                    queue.append(v)
                    in_queue.add(v)

    elapsed_ms = round((time.time() - start_time) * 1000, 3)
    path = _reconstruct_path(prev, start_id, end_id)

    return {
        "algorithm":       "Bellman-Ford (SPFA)",
        "path":            path,
        "distance":        dist[end_id] if dist[end_id] != float('inf') else -1,
        "nodes_visited":   nodes_visited,
        "edges_explored":  edges_explored,
        "explored_edges":  explored_edges,          # For frontend visualization
        "execution_time_ms": elapsed_ms,
        "complexity":      "O(E) avg, O(V×E) worst",
        "space":           "O(V)",
    }


# ─────────────────────────────────────────────────────────────
# 4. BRUTE FORCE — to show WHY we need efficient algorithms
# ─────────────────────────────────────────────────────────────

def brute_force(graph, start_id, end_id, max_nodes=10):

    start_time = time.time()
    nodes_visited = [0]
    edges_explored = [0]
    explored_edges = []  # Track (u, v) for every edge examined
    best_path = [None]
    best_dist = [float('inf')]

    # Limit to a small neighbourhood to keep brute force feasible
    # We only include nodes reachable within max_nodes hops
    reachable = set()
    queue = [start_id]
    while queue and len(reachable) < max_nodes:
        n = queue.pop()
        if n in reachable:
            continue
        reachable.add(n)
        for nb, _ in graph.get_neighbours(n):
            queue.append(nb)

    def dfs(current, visited, current_dist, current_path):
        """Recursive DFS exploring all paths."""
        nodes_visited[0] += 1

        if current == end_id:
            # Found a complete path to the destination
            if current_dist < best_dist[0]:
                best_dist[0] = current_dist
                best_path[0] = current_path[:]
            return

        for neighbour, weight in graph.get_neighbours(current):
            edges_explored[0] += 1
            explored_edges.append((current, neighbour))  # Record this edge exploration
            if neighbour not in visited and neighbour in reachable:
                visited.add(neighbour)
                current_path.append(neighbour)
                dfs(neighbour, visited, current_dist + weight, current_path)
                # BACKTRACK: undo the choice and try the next neighbour
                current_path.pop()
                visited.remove(neighbour)

    # Start DFS from start_id
    dfs(start_id, {start_id}, 0, [start_id])

    elapsed_ms = round((time.time() - start_time) * 1000, 3)

    return {
        "algorithm":       "Brute Force",
        "path":            best_path[0] or [],
        "distance":        best_dist[0] if best_dist[0] != float('inf') else -1,
        "nodes_visited":   nodes_visited[0],
        "edges_explored":  edges_explored[0],
        "explored_edges":  explored_edges,          # For frontend visualization
        "execution_time_ms": elapsed_ms,
        "complexity":      "O(n!) — factorial, infeasible for large graphs",
        "space":           "O(n) recursion stack",
    }
