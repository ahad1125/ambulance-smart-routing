"""
core/views.py — All API endpoints + page views for the Smart Ambulance Routing System.
"""

import json
import time
from django.http import JsonResponse
from django.shortcuts import render
from django.views.decorators.csrf import csrf_exempt

from core.models import Node, Edge, Hospital, Ambulance, EmergencyRequest
from core.algorithms.graph_builder import build_graph
from core.algorithms.shortest_path import dijkstra, astar, bellman_ford, brute_force
from core.algorithms.traversal import bfs, dfs
from core.algorithms.mst import prims, kruskals
from core.algorithms.dp_multistop import dp_multistop, brute_force_multistop, build_dist_matrix


def cors(response):
    response["Access-Control-Allow-Origin"] = "*"
    response["Access-Control-Allow-Methods"] = "GET, POST, OPTIONS"
    response["Access-Control-Allow-Headers"] = "Content-Type"
    return response

def json_ok(data): 
    return cors(JsonResponse(data, safe=False))
def json_err(msg, status=400):
    return cors(JsonResponse({"error": msg}, status=status))


# ─────────────────────────────────────────────────────────────
# PAGE VIEWS — serve HTML templates
# ─────────────────────────────────────────────────────────────

def page_index(request):     
    return render(request, 'core/index.html')
def page_compare(request):
    return render(request, 'core/compare.html')
def page_traversal(request):
    return render(request, 'core/traversal.html')
def page_mst(request):
    return render(request, 'core/mst.html')
def page_multistop(request):
    return render(request, 'core/multistop.html')


@csrf_exempt
def graph_info(request):
    if request.method == "OPTIONS":
        return cors(JsonResponse({}))
    nodes = list(Node.objects.values('id', 'label', 'latitude', 'longitude'))
    edges = []
    for e in Edge.objects.select_related('source', 'destination').all():
        edges.append({"id": e.id, "source": e.source.id, "destination": e.destination.id,
                      "source_lat": e.source.latitude, "source_lon": e.source.longitude,
                      "dest_lat": e.destination.latitude, "dest_lon": e.destination.longitude,
                      "distance": e.distance, "travel_time": e.travel_time, "traffic_weight": e.traffic_weight})
    hospitals = []
    for h in Hospital.objects.select_related('node').all():
        hospitals.append({"id": h.id, "name": h.name, "node_id": h.node.id,
                          "label": h.node.label, "latitude": h.node.latitude, "longitude": h.node.longitude})
    ambulances = []
    for a in Ambulance.objects.select_related('node').all():
        ambulances.append({"id": a.id, "name": a.name, "node_id": a.node.id,
                           "latitude": a.node.latitude, "longitude": a.node.longitude, "is_available": a.is_available})
    return json_ok({"node_count": len(nodes), "edge_count": len(edges),
                    "nodes": nodes, "edges": edges, "hospitals": hospitals, "ambulances": ambulances})


@csrf_exempt
def hospitals_list(request):
    if request.method == "OPTIONS":
        return cors(JsonResponse({}))
    hospitals = []
    for h in Hospital.objects.select_related('node').all():
        hospitals.append({"id": h.id, "name": h.name, "node_id": h.node.id,
                          "label": h.node.label, "latitude": h.node.latitude, "longitude": h.node.longitude})
    return json_ok(hospitals)


@csrf_exempt
def nodes_list(request):
    if request.method == "OPTIONS":
        return cors(JsonResponse({}))
    return json_ok(list(Node.objects.values('id', 'label', 'latitude', 'longitude')))


@csrf_exempt
def find_route(request):
    if request.method == "OPTIONS":
        return cors(JsonResponse({}))
    try:
        data = json.loads(request.body)
    except Exception:
        return json_err("Invalid JSON")
    source = data.get("source")
    destination = data.get("destination")
    algorithm = data.get("algorithm", "dijkstra")
    use_traffic = data.get("use_traffic", False)
    if source is None or destination is None:
        return json_err("source and destination required")
    try:
        source = int(source)
        destination = int(destination)
    except Exception:
        return json_err("source and destination must be integers")
    graph = build_graph(use_traffic=use_traffic)
    if source not in graph.adj:
        return json_err(f"Node {source} not found")
    if destination not in graph.adj:
        return json_err(f"Node {destination} not found")
    algo_map = {"dijkstra": dijkstra, "astar": astar, "bellman_ford": bellman_ford, "brute_force": brute_force}
    fn = algo_map.get(algorithm)
    if fn is None:
        return json_err(f"Unknown algorithm: {algorithm}")
    try:
        result = fn(graph, source, destination)
    except ValueError as e:
        return json_err(str(e))
    path_coords = []
    for node_id in result.get("path", []):
        if node_id in graph.coords:
            lat, lon = graph.coords[node_id]
            path_coords.append({"node_id": node_id, "lat": lat, "lon": lon,
                                 "label": graph.node_label.get(node_id, str(node_id))})
    result["path_coords"] = path_coords
    result["explored_edges_coords"] = _explored_edges_coords(graph, result.get("explored_edges", []))
    result["source"] = source
    result["destination"] = destination
    return json_ok(result)


def _path_coords(graph, path):
    coords = []
    for node_id in path:
        if node_id in graph.coords:
            lat, lon = graph.coords[node_id]
            coords.append({
                "node_id": node_id,
                "lat": lat,
                "lon": lon,
                "label": graph.node_label.get(node_id, str(node_id)),
            })
    return coords


def _explored_edges_coords(graph, explored_edges):
    """Convert (from_id, to_id) tuples to coordinate dicts for frontend visualization."""
    coords = []
    for (u, v) in explored_edges:
        if u in graph.coords and v in graph.coords:
            coords.append({
                "from_lat": graph.coords[u][0], "from_lon": graph.coords[u][1],
                "to_lat": graph.coords[v][0], "to_lon": graph.coords[v][1],
            })
    return coords


@csrf_exempt
def auto_dispatch(request):
    if request.method == "OPTIONS":
        return cors(JsonResponse({}))

    try:
        data = json.loads(request.body)
    except Exception:
        return json_err("Invalid JSON")

    source = data.get("source")
    algorithm = data.get("algorithm", "dijkstra")
    use_traffic = data.get("use_traffic", False)
    if source is None:
        return json_err("source required")
    try:
        source = int(source)
    except Exception:
        return json_err("source must be integer")

    graph = build_graph(use_traffic=use_traffic)
    if source not in graph.adj:
        return json_err(f"Node {source} not found")

    algo_map = {"dijkstra": dijkstra, "astar": astar, "bellman_ford": bellman_ford, "brute_force": brute_force}
    fn = algo_map.get(algorithm)
    
    if fn is None:
        return json_err(f"Unknown algorithm: {algorithm}")

    available_ambulances = Ambulance.objects.select_related("node").filter(is_available=True)
    if not available_ambulances.exists():
        return json_err("No available ambulances")

    hospitals = Hospital.objects.select_related("node").all()
    if not hospitals.exists():
        return json_err("No hospitals found")

    best_ambulance = None
    best_ambulance_route = None
    for ambulance in available_ambulances:
        try:
            route = fn(graph, ambulance.node.id, source)
        except Exception:
            continue
        dist = route.get("distance", -1)
        if dist == -1:
            continue
        if best_ambulance_route is None or dist < best_ambulance_route.get("distance", float("inf")):
            best_ambulance = ambulance
            best_ambulance_route = route

    if best_ambulance is None or best_ambulance_route is None:
        return json_err("No reachable available ambulance for this request")

    best_hospital = None
    best_hospital_route = None
    for hospital in hospitals:
        try:
            route = fn(graph, source, hospital.node.id)
        except Exception:
            continue
        dist = route.get("distance", -1)
        if dist == -1:
            continue
        if best_hospital_route is None or dist < best_hospital_route.get("distance", float("inf")):
            best_hospital = hospital
            best_hospital_route = route

    if best_hospital is None or best_hospital_route is None:
        return json_err("No reachable hospital from this emergency node")

    ambulance_path = best_ambulance_route.get("path", [])
    hospital_path = best_hospital_route.get("path", [])
    combined_path = ambulance_path + (hospital_path[1:] if hospital_path else [])

    total_distance = round(
        float(best_ambulance_route.get("distance", 0)) + float(best_hospital_route.get("distance", 0)),
        3,
    )
    total_nodes = int(best_ambulance_route.get("nodes_visited", 0)) + int(best_hospital_route.get("nodes_visited", 0))
    total_edges = int(best_ambulance_route.get("edges_explored", 0)) + int(best_hospital_route.get("edges_explored", 0))
    total_time_ms = round(
        float(best_ambulance_route.get("execution_time_ms", 0)) + float(best_hospital_route.get("execution_time_ms", 0)),
        3,
    )

    EmergencyRequest.objects.create(
        patient_node_id=source,
        ambulance=best_ambulance,
        hospital=best_hospital,
        total_distance=total_distance,
    )

    return json_ok({
        "mode": "auto_dispatch",
        "algorithm": best_hospital_route.get("algorithm", algorithm),
        "source": source,
        "ambulance": {
            "id": best_ambulance.id,
            "name": best_ambulance.name,
            "node_id": best_ambulance.node.id,
            "label": best_ambulance.node.label,
        },
        "hospital": {
            "id": best_hospital.id,
            "name": best_hospital.name,
            "node_id": best_hospital.node.id,
            "label": best_hospital.node.label,
        },
        "legs": {
            "ambulance_to_patient": {
                "distance": best_ambulance_route.get("distance", -1),
                "path": ambulance_path,
                "path_coords": _path_coords(graph, ambulance_path),
            },
            "patient_to_hospital": {
                "distance": best_hospital_route.get("distance", -1),
                "path": hospital_path,
                "path_coords": _path_coords(graph, hospital_path),
            },
        },
        "path": combined_path,
        "path_coords": _path_coords(graph, combined_path),
        "explored_edges_coords": (
            _explored_edges_coords(graph, best_ambulance_route.get("explored_edges", []))
            + _explored_edges_coords(graph, best_hospital_route.get("explored_edges", []))
        ),
        "distance": total_distance,
        "nodes_visited": total_nodes,
        "edges_explored": total_edges,
        "execution_time_ms": total_time_ms,
        "complexity": best_hospital_route.get("complexity", ""),
        "dispatch_summary": (
            f"{best_ambulance.name} assigned. "
            f"Nearest hospital: {best_hospital.name}."
        ),
    })


@csrf_exempt
def compare_algorithms(request):
    if request.method == "OPTIONS":
        return cors(JsonResponse({}))
    try:
        data = json.loads(request.body)
    except Exception:
        return json_err("Invalid JSON")
    source = data.get("source")
    destination = data.get("destination")
    use_traffic = data.get("use_traffic", False)
    if source is None or destination is None:
        return json_err("source and destination required")
    try:
        source = int(source)
        destination = int(destination)
    except Exception:
        return json_err("source and destination must be integers")
    graph = build_graph(use_traffic=use_traffic)
    results = []
    for algo_name, fn in [("dijkstra", dijkstra), ("astar", astar), ("bellman_ford", bellman_ford), ("brute_force", brute_force)]:
        try:
            r = fn(graph, source, destination)
            path_coords = []
            for node_id in r.get("path", []):
                if node_id in graph.coords:
                    lat, lon = graph.coords[node_id]
                    path_coords.append({"node_id": node_id, "lat": lat, "lon": lon,
                                        "label": graph.node_label.get(node_id, str(node_id))})
            r["path_coords"] = path_coords
            results.append(r)
        except Exception as e:
            results.append({"algorithm": algo_name, "error": str(e)})
    return json_ok({"source": source, "destination": destination, "results": results})


@csrf_exempt
def run_bfs(request):
    if request.method == "OPTIONS":
        return cors(JsonResponse({}))
    try:
        data = json.loads(request.body)
    except Exception:
        return json_err("Invalid JSON")
    start_id = data.get("start")
    if start_id is None:
        return json_err("start required")
    try:
        start_id = int(start_id)
    except Exception:
        return json_err("start must be integer")
    graph = build_graph()
    if start_id not in graph.adj:
        return json_err(f"Node {start_id} not found")
    result = bfs(graph, start_id)
    visited_with_coords = []
    for node_id in result.get("visited_order", []):
        coords = graph.coords.get(node_id, (0, 0))
        visited_with_coords.append({"node_id": node_id, "label": graph.node_label.get(node_id, str(node_id)),
                                    "lat": coords[0], "lon": coords[1],
                                    "level": result["levels"].get(node_id, 0),
                                    "parent": result["parent"].get(node_id)})
    result["visited_with_coords"] = visited_with_coords
    return json_ok(result)


@csrf_exempt
def run_dfs(request):
    if request.method == "OPTIONS":
        return cors(JsonResponse({}))
    try:
        data = json.loads(request.body)
    except Exception:
        return json_err("Invalid JSON")
    start_id = data.get("start")
    if start_id is None:
        return json_err("start required")
    try:
        start_id = int(start_id)
    except Exception:
        return json_err("start must be integer")
    graph = build_graph()
    if start_id not in graph.adj:
        return json_err(f"Node {start_id} not found")
    result = dfs(graph, start_id)
    visited_with_coords = []
    for node_id in result.get("visited_order", []):
        coords = graph.coords.get(node_id, (0, 0))
        visited_with_coords.append({"node_id": node_id, "label": graph.node_label.get(node_id, str(node_id)),
                                    "lat": coords[0], "lon": coords[1],
                                    "depth": result["depth"].get(node_id, 0),
                                    "parent": result["parent"].get(node_id)})
    result["visited_with_coords"] = visited_with_coords
    return json_ok(result)


@csrf_exempt
def run_mst(request):
    if request.method == "OPTIONS":
        return cors(JsonResponse({}))
    graph = build_graph()
    prim_result = prims(graph)
    kruskal_result = kruskals(graph)
    def enrich(mst_edges, g):
        enriched = []
        for edge in mst_edges:
            if isinstance(edge, dict):
                u = edge.get("from_node")
                v = edge.get("to_node")
                w = edge.get("weight", 0)
            else:
                u, v, w = edge
            uc = g.coords.get(u, (0, 0))
            vc = g.coords.get(v, (0, 0))
            enriched.append({"from": u, "to": v, "weight": w,
                              "from_label": g.node_label.get(u, str(u)), "to_label": g.node_label.get(v, str(v)),
                              "from_lat": uc[0], "from_lon": uc[1], "to_lat": vc[0], "to_lon": vc[1]})
        return enriched
    prim_result["mst_edges_enriched"] = enrich(prim_result.get("mst_edges", []), graph)
    kruskal_result["mst_edges_enriched"] = enrich(kruskal_result.get("mst_edges", []), graph)
    return json_ok({"prims": prim_result, "kruskals": kruskal_result})


@csrf_exempt
def multistop_route(request):
    if request.method == "OPTIONS":
        return cors(JsonResponse({}))
    try:
        data = json.loads(request.body)
    except Exception:
        return json_err("Invalid JSON")
    stop_ids = data.get("stops", [])
    if not stop_ids or len(stop_ids) < 2:
        return json_err("At least 2 stop node IDs required")
    if len(stop_ids) > 8:
        return json_err("Maximum 8 stops")
    try:
        stop_ids = [int(s) for s in stop_ids]
    except Exception:
        return json_err("All stop IDs must be integers")
    graph = build_graph()
    for sid in stop_ids:
        if sid not in graph.adj:
            return json_err(f"Node {sid} not found")
    stop_names = [graph.node_label.get(sid, f"Node {sid}") for sid in stop_ids]
    dist_matrix = build_dist_matrix(graph, stop_ids, dijkstra)
    dp_result = dp_multistop(dist_matrix, stop_names)
    bf_result = brute_force_multistop(dist_matrix, stop_names)
    def enrich(indices, ids, g):
        out = []
        for i in indices:
            nid = ids[i]
            c = g.coords.get(nid, (0, 0))
            out.append({"node_id": nid, "label": g.node_label.get(nid, str(nid)), "lat": c[0], "lon": c[1]})
        return out

    def build_detailed_path(indices, ids, g):
        """Run Dijkstra between each consecutive pair of stops and collect
        all intermediate node coordinates so the polyline follows real edges."""
        if len(indices) < 2:
            return enrich(indices, ids, g)
        detailed = []
        for seg_idx in range(len(indices) - 1):
            src_id = ids[indices[seg_idx]]
            dst_id = ids[indices[seg_idx + 1]]
            leg = dijkstra(g, src_id, dst_id)
            leg_path = leg.get("path", [])
            if not leg_path:
                # Fallback: straight line between the two stops
                leg_path = [src_id, dst_id]
            # For the first segment include the start node;
            # for subsequent segments skip the first node (it's the same
            # as the previous segment's last node) to avoid duplicates.
            start = 0 if seg_idx == 0 else 1
            for node_id in leg_path[start:]:
                c = g.coords.get(node_id, (0, 0))
                detailed.append({
                    "node_id": node_id,
                    "lat": c[0],
                    "lon": c[1],
                    "label": g.node_label.get(node_id, str(node_id)),
                })
        return detailed

    dp_result["path_coords"] = enrich(dp_result.get("order_indices", []), stop_ids, graph)
    bf_result["path_coords"] = enrich(bf_result.get("order_indices", []), stop_ids, graph)

    # Detailed path that follows actual graph edges (for polyline drawing)
    dp_result["detailed_path_coords"] = build_detailed_path(
        dp_result.get("order_indices", []), stop_ids, graph)
    bf_result["detailed_path_coords"] = build_detailed_path(
        bf_result.get("order_indices", []), stop_ids, graph)

    return json_ok({"stops": stop_names, "stop_ids": stop_ids, "dist_matrix": dist_matrix,
                    "dp": dp_result, "brute_force": bf_result})


@csrf_exempt
def update_traffic(request):
    if request.method == "OPTIONS":
        return cors(JsonResponse({}))
    try:
        data = json.loads(request.body)
    except Exception:
        return json_err("Invalid JSON")
    edge_id = data.get("edge_id")
    traffic_weight = data.get("traffic_weight")
    if edge_id is None or traffic_weight is None:
        return json_err("edge_id and traffic_weight required")
    try:
        edge_id = int(edge_id)
        traffic_weight = float(traffic_weight)
    except Exception:
        return json_err("Invalid types")
    if not (0.1 <= traffic_weight <= 10.0):
        return json_err("traffic_weight must be 0.1–10.0")
    try:
        edge = Edge.objects.get(id=edge_id)
    except Edge.DoesNotExist:
        return json_err(f"Edge {edge_id} not found")
    old = edge.traffic_weight
    edge.traffic_weight = traffic_weight
    edge.save()
    return json_ok({"edge_id": edge_id, "source": edge.source.label, "destination": edge.destination.label,
                    "old_traffic_weight": old, "new_traffic_weight": traffic_weight,
                    "effective_distance": round(edge.distance * traffic_weight, 3),
                    "message": f"Traffic weight updated: {edge.source.label} → {edge.destination.label} ({old}x → {traffic_weight}x)"})
