"""
core/algorithms/traversal.py

PURPOSE:
  Implements BFS (Breadth-First Search) and DFS (Depth-First Search)
  for the Network Analysis page.

USE CASES IN THIS PROJECT:
  - BFS: Find which hospitals are reachable from a given node, and at
         what minimum number of hops. Shows shortest path in UNWEIGHTED graphs.
  - DFS: Explore the road network depth-first. Good for checking connectivity
         and detecting unreachable areas.

KEY DIFFERENCE FROM SHORTEST PATH ALGORITHMS:
  BFS/DFS ignore edge WEIGHTS — they only care about connectivity.
  Dijkstra/A* care about weights (distance/time).
  So BFS finds "fewest edges" not "shortest distance".

CLO COVERAGE:
  CLO 7: Graph traversal algorithms
  CLO 1/2: Show different exploration orders and reachability
"""

from collections import deque  # deque = double-ended queue, used for BFS
import time


# ─────────────────────────────────────────────────────────────
# 1. BFS — Breadth-First Search
# ─────────────────────────────────────────────────────────────

def bfs(graph, start_id):
    """
    Explores the graph level by level starting from start_id.

    HOW IT WORKS:
      1. Start by adding start_id to a queue.
      2. Dequeue the front node, mark it visited, add all unvisited neighbours to queue.
      3. Repeat until queue is empty.

      The queue ensures we process nodes in order of distance (hops):
      - Level 0: start node
      - Level 1: immediate neighbours
      - Level 2: neighbours of neighbours
      - etc.

    WHY QUEUE (FIFO) and not STACK?
      A FIFO queue gives BFS its "level by level" property.
      A LIFO stack would give DFS behaviour.

    RETURNS:
      - visited_order: nodes in the order they were first discovered
      - level: which level/hop each node is at from start
      - parent: predecessor dict (for path reconstruction)
      - reachable: set of all reachable node IDs

    TIME COMPLEXITY:  O(V + E)
      Each node is enqueued/dequeued once: O(V)
      Each edge is examined once: O(E)

    SPACE COMPLEXITY: O(V) — the queue and visited set
    """
    start_time = time.time()

    # Track which nodes we've already visited
    visited = set()
    visited.add(start_id)

    # BFS uses a QUEUE (first in, first out)
    # deque is faster than list for .popleft() — O(1) vs O(n)
    queue = deque([start_id])

    # Record the order nodes were discovered
    visited_order = [start_id]

    # level[v] = number of hops from start to v
    level = {start_id: 0}

    # parent[v] = which node discovered v (for path drawing)
    parent = {start_id: None}

    edges_explored = 0

    while queue:
        # Dequeue from the FRONT (FIFO — this is what makes it BFS)
        u = queue.popleft()

        for v, _ in graph.get_neighbours(u):  # _ = weight (ignored in BFS)
            edges_explored += 1

            if v not in visited:
                visited.add(v)
                queue.append(v)                     # Add to BACK of queue
                visited_order.append(v)
                level[v] = level[u] + 1             # One more hop from start
                parent[v] = u

    elapsed_ms = round((time.time() - start_time) * 1000, 3)

    return {
        "algorithm":       "BFS",
        "start_node":      start_id,
        "visited_order":   visited_order,            # Nodes in discovery order
        "levels":          level,                    # Hop count from start
        "parent":          parent,                   # For drawing traversal tree
        "reachable_count": len(visited),
        "edges_explored":  edges_explored,
        "execution_time_ms": elapsed_ms,
        "complexity":      "O(V + E)",
        "space":           "O(V)",
    }


# ─────────────────────────────────────────────────────────────
# 2. DFS — Depth-First Search
# ─────────────────────────────────────────────────────────────

def dfs(graph, start_id):
    """
    Explores the graph as deep as possible before backtracking.

    HOW IT WORKS:
      1. Start at start_id, push it onto a STACK.
      2. Pop the top node, mark it visited, push all unvisited neighbours.
      3. Repeat — this always explores the DEEPEST unvisited path first.

    WHY STACK (LIFO) and not QUEUE?
      A LIFO stack gives DFS its "go deep first" property.
      The last pushed neighbour is processed first → we dive deep before backtracking.

    DIFFERENCE FROM BFS:
      BFS explores all nodes at depth 1 before depth 2.
      DFS goes all the way to depth N, then backtracks.
      On the network analysis page you can see this difference visually.

    USES IN THIS PROJECT:
      - Check if all hospitals are connected to the emergency point
      - Find connected components (unreachable zones)
      - Show a different traversal order compared to BFS

    TIME COMPLEXITY:  O(V + E) — same as BFS
    SPACE COMPLEXITY: O(V) — the stack can hold at most V nodes
    """
    start_time = time.time()

    visited = set()
    visited.add(start_id)

    # DFS uses a STACK (last in, first out)
    # Python list used as stack: .append() to push, .pop() to pop from end
    stack = [start_id]

    visited_order = []
    parent = {start_id: None}
    depth = {start_id: 0}  # How deep each node is in the DFS tree

    edges_explored = 0

    while stack:
        # Pop from the END (LIFO — this is what makes it DFS)
        u = stack.pop()

        # Check again since a node might have been added to stack multiple times
        if u in visited and u != start_id:
            # If already visited (and not start), we already recorded it
            pass

        if u not in [start_id] and u not in visited:
            visited.add(u)

        visited_order.append(u)

        for v, _ in graph.get_neighbours(u):
            edges_explored += 1

            if v not in visited:
                visited.add(v)
                stack.append(v)                           # Push to TOP of stack
                parent[v] = u
                depth[v] = depth.get(u, 0) + 1

    elapsed_ms = round((time.time() - start_time) * 1000, 3)

    # Remove duplicate start node that gets added at beginning
    clean_order = list(dict.fromkeys(visited_order))  # Preserve order, remove duplicates

    return {
        "algorithm":       "DFS",
        "start_node":      start_id,
        "visited_order":   clean_order,
        "depth":           depth,
        "parent":          parent,
        "reachable_count": len(visited),
        "edges_explored":  edges_explored,
        "execution_time_ms": elapsed_ms,
        "complexity":      "O(V + E)",
        "space":           "O(V)",
    }
