# Smart Ambulance Routing System

A Django-based emergency routing and algorithm-visualization project for smart ambulance dispatch.

The system simulates emergency response workflows on a city-like road network (Rawalpindi/Islamabad area), compares classical algorithms, and provides interactive map-based visualizations for routing, traversal, MST, and multi-stop optimization.

## Highlights

- Interactive emergency simulation with real-time map visualization
- **Automatic dispatch** — selects nearest available ambulance and nearest hospital
- **Manual routing** — user picks hospital, system finds shortest path
- **Algorithm exploration visualization** — animated edge-by-edge search process
- Traffic congestion controls (per-edge weight updates)
- City-like seeded network (71 nodes, 362 edges — radial mini-city topology)
- Multiple algorithm demonstration pages for academic analysis

## Algorithms Covered

| Category | Algorithms | Complexity |
|---|---|---|
| **Shortest Path** | Dijkstra, A* (Haversine heuristic), Bellman-Ford, Brute Force | O((V+E) log V), O(b^d), O(VE), O(n!) |
| **Graph Traversal** | BFS, DFS | O(V + E) |
| **Minimum Spanning Tree** | Prim's (min-heap), Kruskal's (Union-Find) | O((V+E) log V), O(E log E) |
| **Dynamic Programming** | Held-Karp multi-stop optimization (bitmask DP) | O(2^n × n²) |
| **Brute Force** | Multi-stop permutation search | O(n!) |

## Data Structures Used

- **Adjacency List** — graph representation (sparse, O(V+E) space)
- **Min-Heap / Priority Queue** — Dijkstra, A*, Prim's
- **Queue (deque)** — BFS
- **Stack** — DFS
- **Union-Find (Disjoint Set Union)** — Kruskal's (with path compression + union by rank)
- **Hash Map / Dictionary** — distance tables, predecessor tracking
- **Bitmask Array** — Held-Karp DP table (2^n × n states)

## Tech Stack

- **Backend:** Python 3.x, Django 5.x
- **Database:** SQLite
- **Frontend:** HTML5, CSS3, JavaScript (ES6+)
- **Maps:** Leaflet.js (OpenStreetMap / CARTO tiles)

## Project Structure

```
ambulance-smart-routing/
├── ambulance_routing/
│   ├── manage.py
│   ├── db.sqlite3
│   ├── ambulance_routing/
│   │   ├── settings.py
│   │   └── urls.py
│   └── core/
│       ├── models.py                  # Node, Edge, Hospital, Ambulance, EmergencyRequest
│       ├── views.py                   # API endpoints + page views
│       ├── urls.py                    # URL routing
│       ├── algorithms/
│       │   ├── graph_builder.py       # Graph class (adjacency list) + Haversine heuristic
│       │   ├── shortest_path.py       # Dijkstra, A*, Bellman-Ford, Brute Force
│       │   ├── traversal.py           # BFS, DFS
│       │   ├── mst.py                 # Prim's, Kruskal's + Union-Find
│       │   └── dp_multistop.py        # Held-Karp DP + Brute Force TSP
│       ├── templates/core/
│       │   ├── index.html             # Simulation page
│       │   ├── compare.html           # Algorithm comparison
│       │   ├── traversal.html         # BFS/DFS visualization
│       │   ├── mst.html               # MST visualization
│       │   └── multistop.html         # Multi-stop DP routing
│       ├── static/core/
│       │   ├── css/                   # Page stylesheets
│       │   └── js/                    # Page scripts
│       └── management/commands/
│           └── seed_data.py           # Database seeding (mini-city generator)
└── PROJECT_DOCUMENTATION.txt          # Detailed project documentation
```

## Setup

1. Create and activate virtual environment:

```bash
python -m venv venv
# Windows:
venv\Scripts\activate
# Mac/Linux:
source venv/bin/activate
```

2. Install dependencies:

```bash
pip install django
```

3. Apply migrations and seed data:

```bash
cd ambulance_routing
python manage.py migrate
python manage.py seed_data
```

4. Run the development server:

```bash
python manage.py runserver
```

5. Open in browser: [http://127.0.0.1:8000/](http://127.0.0.1:8000/)

## Pages

| URL | Page | Description |
|---|---|---|
| `/` | Simulation | Emergency dispatch with route visualization and traffic controls |
| `/compare/` | Algorithm Comparison | Side-by-side comparison of all shortest-path algorithms |
| `/traversal/` | BFS/DFS | Animated graph traversal visualization |
| `/mst/` | MST | Prim's vs Kruskal's Minimum Spanning Tree |
| `/multistop/` | Multi-Stop DP | Optimal multi-stop routing (Held-Karp DP vs Brute Force) |

## API Endpoints

| Method | Endpoint | Description |
|---|---|---|
| GET | `/api/graph/` | Full graph data (nodes, edges, hospitals, ambulances) |
| GET | `/api/nodes/` | Node list |
| GET | `/api/hospitals/` | Hospital list |
| POST | `/api/route/` | Shortest path (source, destination, algorithm) |
| POST | `/api/dispatch/` | Auto dispatch (nearest ambulance + hospital) |
| POST | `/api/compare/` | Compare all 4 algorithms on same route |
| POST | `/api/bfs/` | BFS traversal from start node |
| POST | `/api/dfs/` | DFS traversal from start node |
| GET | `/api/mst/` | Prim's + Kruskal's MST |
| POST | `/api/multistop/` | Multi-stop DP + Brute Force (list of stop IDs) |
| POST | `/api/traffic/` | Update edge traffic weight |

## Key Implementation Details

### A* Heuristic — Haversine Formula
The A* heuristic uses the **Haversine great-circle formula** to compute straight-line distance in **kilometres** (same unit as edge weights). This makes A* visit **79% fewer nodes** than Dijkstra while finding the same optimal path. The heuristic is admissible (never overestimates), guaranteeing optimality.

### Multi-Stop Route Visualization
The DP multi-stop page builds a distance matrix by running Dijkstra between all stop pairs, then uses Held-Karp bitmask DP to find the optimal visit order. The route is visualized by running Dijkstra between each consecutive stop pair and drawing the full intermediate path — so the polyline follows actual graph edges, not straight lines.

### City Graph Generation
The `seed_data.py` command generates a radial city layout with a CBD center node and 5 concentric rings of 14 nodes each. Ring roads, radial arterials, and randomized local connectors create a realistic road network topology.

## License

MIT
