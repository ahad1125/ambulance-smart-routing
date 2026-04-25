"""
core/urls.py — URL patterns for the Smart Ambulance Routing project.

HOW DJANGO ROUTING WORKS:
  - ambulance_routing/urls.py includes this file.
  - Each path() maps a URL to a view function in core/views.py.

STRUCTURE:
  /                     → Home / Simulation page (index.html)
  /compare/             → Algorithm Comparison page
  /traversal/           → BFS/DFS Network Analysis page
  /mst/                 → Minimum Spanning Tree page
  /sorting/             → Sorting Benchmark page
  /search/              → Hospital Search (String Matching) page
  /multistop/           → Multi-Stop DP Routing page

  /api/graph/           → Graph data (nodes, edges, hospitals, ambulances)
  /api/nodes/           → Node list
  /api/hospitals/       → Hospital list
  /api/route/           → Find shortest route (Dijkstra / A* / Bellman-Ford / Brute Force)
  /api/compare/         → Compare all algorithms side-by-side
  /api/bfs/             → BFS traversal from a start node
  /api/dfs/             → DFS traversal from a start node
  /api/mst/             → Prim's and Kruskal's MST
  /api/sort/            → Sort hospitals benchmark (Merge Sort vs Quick Sort)
  /api/search/          → Hospital name search (KMP + Rabin-Karp)
  /api/multistop/       → Multi-stop route (DP Held-Karp + Brute Force)
  /api/traffic/         → Update edge traffic weight
"""

from django.urls import path
from core import views

urlpatterns = [
    # ── Page views (serve HTML templates) ─────────────────────
    path('',             views.page_index,      name='index'),
    path('compare/',     views.page_compare,    name='compare'),
    path('traversal/',   views.page_traversal,  name='traversal'),
    path('mst/',         views.page_mst,        name='mst'),
    path('sorting/',     views.page_sorting,    name='sorting'),
    path('search/',      views.page_search,     name='search'),
    path('multistop/',   views.page_multistop,  name='multistop'),

    # ── API endpoints (return JSON) ────────────────────────────
    path('api/graph/',     views.graph_info,           name='api-graph'),
    path('api/nodes/',     views.nodes_list,            name='api-nodes'),
    path('api/hospitals/', views.hospitals_list,        name='api-hospitals'),
    path('api/route/',     views.find_route,            name='api-route'),
    path('api/dispatch/',  views.auto_dispatch,         name='api-dispatch'),
    path('api/compare/',   views.compare_algorithms,    name='api-compare'),
    path('api/bfs/',       views.run_bfs,               name='api-bfs'),
    path('api/dfs/',       views.run_dfs,               name='api-dfs'),
    path('api/mst/',       views.run_mst,               name='api-mst'),
    path('api/sort/',      views.sort_hospitals_view,   name='api-sort'),
    path('api/search/',    views.search_hospital_names, name='api-search'),
    path('api/multistop/', views.multistop_route,       name='api-multistop'),
    path('api/traffic/',   views.update_traffic,        name='api-traffic'),
]
