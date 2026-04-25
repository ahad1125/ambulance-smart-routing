# Smart Ambulance Routing System

A Django-based emergency routing and algorithm-visualization project for smart ambulance dispatch.

The system simulates emergency response workflows on a city-like road network, compares classical algorithms, and provides interactive map-based visualizations for routing, traversal, MST, sorting, string matching, and multi-stop optimization.

## Highlights

- Interactive emergency simulation with map-based route visualization
- Automatic dispatch mode:
  - selects nearest available ambulance
  - routes to nearest hospital
- Manual routing mode with algorithm selection
- Traffic congestion controls (edge-level weight updates)
- City-like seeded network (mini-city topology, not a simple classroom grid)
- Multiple algorithm demonstration pages for academic analysis

## Algorithms Covered

- **Shortest Path:** Dijkstra, A*, Bellman-Ford, Brute Force
- **Traversal:** BFS, DFS
- **Minimum Spanning Tree:** Prim's, Kruskal's
- **Sorting:** Merge Sort, Quick Sort
- **String Matching:** KMP, Rabin-Karp
- **Dynamic Programming:** Held-Karp style multi-stop optimization (+ brute-force comparison)

## Tech Stack

- Python 3.13
- Django
- Django REST Framework
- django-cors-headers
- SQLite (default)
- Leaflet.js (frontend maps)

## Project Structure

```text
ambulance-smart-routing/
  ambulance_routing/
    manage.py
    db.sqlite3
    ambulance_routing/
      settings.py
      urls.py
    core/
      algorithms/
      management/commands/seed_data.py
      templates/core/
      models.py
      views.py
      urls.py
```

## Setup

> Run commands from the repository root (`ambulance-smart-routing`).

1. Create virtual environment (optional if already created):

```powershell
python -m venv venv
```

2. Activate virtual environment:

```powershell
.\venv\Scripts\activate
```

3. Install dependencies:

```powershell
pip install django djangorestframework django-cors-headers
```

4. Apply migrations:

```powershell
cd ambulance_routing
..\venv\Scripts\python.exe manage.py migrate
```

5. Seed mini-city data:

```powershell
..\venv\Scripts\python.exe manage.py seed_data
```

6. Run development server:

```powershell
..\venv\Scripts\python.exe manage.py runserver
```

Open: [http://127.0.0.1:8000/](http://127.0.0.1:8000/)

## Main Pages

- `/` - Live simulation (dispatch + traffic controls)
- `/compare/` - Shortest-path algorithm comparison
- `/traversal/` - BFS/DFS visual traversal
- `/mst/` - Prim's vs Kruskal's MST
- `/sorting/` - Sorting benchmark and dispatch ranking
- `/search/` - KMP/Rabin-Karp hospital search
- `/multistop/` - DP multi-stop route optimization

## Core API Endpoints

- `GET /api/graph/` - graph nodes, edges, hospitals, ambulances
- `GET /api/nodes/`
- `GET /api/hospitals/`
- `POST /api/route/` - manual route by algorithm
- `POST /api/dispatch/` - automatic dispatch flow
- `POST /api/compare/`
- `POST /api/bfs/`
- `POST /api/dfs/`
- `POST /api/mst/`
- `POST /api/sort/`
- `POST /api/search/`
- `POST /api/multistop/`
- `POST /api/traffic/` - update traffic multiplier for an edge

## Notes for GitHub Publishing

- Recommended: do **not** commit `venv/`
- Recommended: do **not** commit local cache files (`__pycache__/`)
- `db.sqlite3` can be kept for demo data, or removed for a clean fresh setup

## Future Improvements

- Authentication and role-based dashboard
- Real road network ingestion (OpenStreetMap graph import)
- Time-dependent traffic simulation
- Unit/integration test suite expansion
- Dockerized deployment

## License

Add your preferred license (e.g., MIT) before publishing.

