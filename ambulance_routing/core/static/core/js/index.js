/* index.js – Simulation page logic */

const API = 'http://127.0.0.1:8000';
let map, graphData = null, emergencyMarker = null, routeLayer = null, routeLayerLeg1 = null, routeLayerLeg2 = null;
let hospitalMarkers = [], ambulanceMarkers = [], animatedMarker = null, animationFrame = null;
let selectedSourceNode = null;
let tileLayer = null;
let edgeLayers = new Map();
let selectedEdgeLayer = null;
let explorationLayers = [];

const MAP_TILES = {
  light: {
    url: 'https://{s}.basemaps.cartocdn.com/light_nolabels/{z}/{x}/{y}{r}.png',
    options: { attribution: '© OpenStreetMap © CARTO', subdomains: 'abcd', maxZoom: 20 }
  },
  dark: {
    url: 'https://{s}.basemaps.cartocdn.com/dark_nolabels/{z}/{x}/{y}{r}.png',
    options: { attribution: '© OpenStreetMap © CARTO', subdomains: 'abcd', maxZoom: 20 }
  }
};

map = L.map('map', { zoomControl: true, preferCanvas: true }).setView([33.63, 73.06], 13);

function setMapTheme(theme = 'light') {
  const cfg = MAP_TILES[theme] || MAP_TILES.light;
  if (tileLayer) map.removeLayer(tileLayer);
  tileLayer = L.tileLayer(cfg.url, cfg.options).addTo(map);
}
setMapTheme('light');

const hospitalIcon = L.divIcon({
  className: '',
  html: '<div style="background:#1e7e34;width:16px;height:16px;border-radius:3px;border:2px solid #fff;display:flex;align-items:center;justify-content:center;font-size:10px;">H</div>',
  iconSize: [20, 20], iconAnchor: [10, 10]
});
const ambulanceIcon = L.divIcon({
  className: '',
  html: '<div style="background:#1a56a0;width:16px;height:16px;border-radius:50%;border:2px solid #fff;display:flex;align-items:center;justify-content:center;font-size:11px;">A</div>',
  iconSize: [20, 20], iconAnchor: [10, 10]
});
const emergencyIcon = L.divIcon({
  className: '',
  html: '<div style="background:#c0392b;width:18px;height:18px;border-radius:50%;border:3px solid #fff;"></div>',
  iconSize: [18, 18], iconAnchor: [9, 9]
});

function onDispatchModeChange() {
  const mode = document.getElementById('dispatchMode').value;
  document.getElementById('manualHospitalWrap').style.display = mode === 'manual' ? 'block' : 'none';
  document.getElementById('s-mode').textContent = mode === 'manual' ? 'Manual Hospital' : 'Auto Dispatch';
}

function clearDynamicLayers() {
  [routeLayer, routeLayerLeg1, routeLayerLeg2, animatedMarker].forEach(layer => {
    if (layer) map.removeLayer(layer);
  });
  routeLayer = null;
  routeLayerLeg1 = null;
  routeLayerLeg2 = null;
  animatedMarker = null;
  if (animationFrame) cancelAnimationFrame(animationFrame);
  explorationLayers.forEach(l => map.removeLayer(l));
  explorationLayers = [];
}

async function loadGraph() {
  try {
    const res = await fetch(`${API}/api/graph/`);
    graphData = await res.json();
    document.getElementById('loading').style.display = 'none';

    const sourceSelect = document.getElementById('sourceSelect');
    sourceSelect.innerHTML = '<option value="">Click map or choose node</option>';

    graphData.nodes.forEach(n => {
      L.circleMarker([n.latitude, n.longitude], { radius: 2, color: '#94a3b8', fillColor: '#94a3b8', fillOpacity: 0.3, weight: 0.6 })
        .addTo(map);
      const opt = document.createElement('option');
      opt.value = n.id;
      opt.textContent = `${n.label} (ID ${n.id})`;
      sourceSelect.appendChild(opt);
    });

    graphData.edges.forEach(e => {
      const line = L.polyline([[e.source_lat, e.source_lon], [e.dest_lat, e.dest_lon]],
        { color: '#94a3b8', weight: 3.5, opacity: 0.2, smoothFactor: 1 })
        .bindTooltip(`Edge ${e.id} | ${e.distance.toFixed(2)} km | Traffic: ${e.traffic_weight}x`);
      line.edgeData = e;
      line.on('click', () => selectEdge(e.id, line));
      line.addTo(map);
      edgeLayers.set(e.id, line);
    });

    const destSelect = document.getElementById('destSelect');
    destSelect.innerHTML = '<option value="">Select destination hospital</option>';
    graphData.hospitals.forEach(h => {
      const marker = L.marker([h.latitude, h.longitude], { icon: hospitalIcon })
        .bindPopup(`<b>${h.name}</b><br>Node: ${h.label}<br>ID: ${h.node_id}`)
        .addTo(map);
      hospitalMarkers.push(marker);
      const opt = document.createElement('option');
      opt.value = h.node_id;
      opt.textContent = h.name;
      destSelect.appendChild(opt);
    });

    graphData.ambulances.forEach(a => {
      const marker = L.marker([a.latitude, a.longitude], { icon: ambulanceIcon })
        .bindPopup(`<b>${a.name}</b><br>${a.is_available ? 'Available' : 'Busy'}`)
        .addTo(map);
      ambulanceMarkers.push(marker);
    });
  } catch (e) {
    document.getElementById('loading').textContent = 'Cannot connect to API. Start Django: python manage.py runserver';
    document.getElementById('loading').style.color = '#c0392b';
    document.getElementById('loading').style.display = 'block';
  }
}

function nearestNode(lat, lon) {
  let best = null, bestDist = Infinity;
  graphData.nodes.forEach(n => {
    const d = Math.hypot(n.latitude - lat, n.longitude - lon);
    if (d < bestDist) { bestDist = d; best = n; }
  });
  return best;
}

function selectSourceFromDropdown() {
  if (!graphData) return;
  const sourceId = parseInt(document.getElementById('sourceSelect').value);
  if (!sourceId) return;
  const node = graphData.nodes.find(n => n.id === sourceId);
  if (!node) return;
  selectedSourceNode = sourceId;
  if (emergencyMarker) map.removeLayer(emergencyMarker);
  emergencyMarker = L.marker([node.latitude, node.longitude], { icon: emergencyIcon }).addTo(map);
  emergencyMarker.bindPopup(`<b>Emergency</b><br>Source node: ${node.label} (ID ${node.id})`).openPopup();
  map.panTo([node.latitude, node.longitude]);
}

function selectEdge(edgeId, lineLayer) {
  document.getElementById('edgeIdInput').value = edgeId;
  const e = lineLayer.edgeData;
  document.getElementById('edgeSelectionHint').textContent =
    `Selected edge ${edgeId}: ${e.source} -> ${e.destination} (${e.traffic_weight}x)`;
}

map.on('click', function (e) {
  if (!graphData) return;
  clearDynamicLayers();
  if (emergencyMarker) map.removeLayer(emergencyMarker);
  emergencyMarker = L.marker([e.latlng.lat, e.latlng.lng], { icon: emergencyIcon }).addTo(map);
  const best = nearestNode(e.latlng.lat, e.latlng.lng);
  selectedSourceNode = best.id;
  document.getElementById('sourceSelect').value = String(best.id);
  emergencyMarker.bindPopup(`<b>Emergency</b><br>Nearest node: ${best.label} (ID ${best.id})`).openPopup();
});

function updateStats(data) {
  document.getElementById('s-algo').textContent = data.algorithm || '—';
  document.getElementById('s-nodes').textContent = data.nodes_visited ?? '—';
  document.getElementById('s-edges').textContent = data.edges_explored ?? '—';
  document.getElementById('s-time').textContent = (data.execution_time_ms ?? '—') + (data.execution_time_ms !== undefined ? ' ms' : '');
  document.getElementById('s-dist').textContent = data.distance !== -1 ? Number(data.distance).toFixed(2) + ' km' : 'Unreachable';
  document.getElementById('s-path').textContent = (data.path?.length ?? 0) + ' nodes';
  document.getElementById('s-cx').textContent = data.complexity || '—';
}

function animateMarkerAlongPath(latlngs, durationPerSegment = 650) {
  if (!latlngs || latlngs.length < 2) return;
  if (animatedMarker) map.removeLayer(animatedMarker);
  animatedMarker = L.marker(latlngs[0], { icon: ambulanceIcon, zIndexOffset: 2000 }).addTo(map);

  let segmentIndex = 0;
  let segmentStart = performance.now();

  function frame(now) {
    const from = latlngs[segmentIndex];
    const to = latlngs[segmentIndex + 1];
    if (!from || !to) return;
    const t = Math.min(1, (now - segmentStart) / durationPerSegment);
    const lat = from[0] + (to[0] - from[0]) * t;
    const lon = from[1] + (to[1] - from[1]) * t;
    animatedMarker.setLatLng([lat, lon]);
    if (t >= 1) {
      segmentIndex += 1;
      segmentStart = now;
      if (segmentIndex >= latlngs.length - 1) return;
    }
    animationFrame = requestAnimationFrame(frame);
  }
  animationFrame = requestAnimationFrame(frame);
}

function animateExploration(exploredEdges, delayMs = 35) {
  return new Promise(resolve => {
    if (!exploredEdges || exploredEdges.length === 0) { resolve(); return; }
    let i = 0;
    function drawNext() {
      if (i >= exploredEdges.length) { resolve(); return; }
      const e = exploredEdges[i];
      const line = L.polyline(
        [[e.from_lat, e.from_lon], [e.to_lat, e.to_lon]],
        { color: '#b7760d', weight: 2, opacity: 0.5, dashArray: '6 4' }
      ).addTo(map);
      explorationLayers.push(line);
      i++;
      setTimeout(drawNext, delayMs);
    }
    drawNext();
  });
}

async function runManualRoute(sourceNode, algo) {
  const dest = document.getElementById('destSelect').value;
  if (!dest) { alert('Select a destination hospital in manual mode'); return; }
  
  const useTraffic = document.getElementById('useTraffic').checked;
  const res = await fetch(`${API}/api/route/`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ source: sourceNode, destination: parseInt(dest), algorithm: algo, use_traffic: useTraffic })
  });
  const data = await res.json();
  if (data.error) { alert('Error: ' + data.error); return; }

  if (document.getElementById('showExploration').checked) {
    await animateExploration(data.explored_edges_coords || []);
  }

  const latlngs = data.path_coords.map(p => [p.lat, p.lon]);
  const colors = { dijkstra: '#c0392b', astar: '#1e7e34', bellman_ford: '#e07b00', brute_force: '#6a3d9a' };
  routeLayer = L.polyline(latlngs, { color: colors[algo] || '#c0392b', weight: 5, opacity: 0.9 }).addTo(map);
  if (latlngs.length) map.fitBounds(routeLayer.getBounds(), { padding: [40, 40] });
  animateMarkerAlongPath(latlngs, 520);
  updateStats(data);
}

async function runAutoDispatch(sourceNode, algo) {
  const useTraffic = document.getElementById('useTraffic').checked;
  const res = await fetch(`${API}/api/dispatch/`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ source: sourceNode, algorithm: algo, use_traffic: useTraffic })
  });
  const data = await res.json();
  if (data.error) { alert('Error: ' + data.error); return; }

  if (document.getElementById('showExploration').checked) {
    await animateExploration(data.explored_edges_coords || []);
  }

  const leg1 = data.legs.ambulance_to_patient.path_coords.map(p => [p.lat, p.lon]);
  const leg2 = data.legs.patient_to_hospital.path_coords.map(p => [p.lat, p.lon]);
  const fullPath = data.path_coords.map(p => [p.lat, p.lon]);

  routeLayerLeg1 = L.polyline(leg1, { color: '#1a7bbf', weight: 5, opacity: 0.95, dashArray: '10 8' }).addTo(map);
  routeLayerLeg2 = L.polyline(leg2, { color: '#e07b00', weight: 5, opacity: 0.95 }).addTo(map);

  const bounds = [...leg1, ...leg2];
  if (bounds.length) map.fitBounds(bounds, { padding: [45, 45] });

  animateMarkerAlongPath(fullPath, 560);
  updateStats(data);
  document.getElementById('s-mode').textContent = 'Auto Dispatch';

  if (emergencyMarker) {
    emergencyMarker.bindPopup(
      `<b>Emergency</b><br>${data.dispatch_summary}<br>Ambulance: ${data.ambulance.name}<br>Hospital: ${data.hospital.name}`
    ).openPopup();
  }
}

async function findRoute() {
  if (!selectedSourceNode) { alert('Click map first to set emergency location'); return; }
  clearDynamicLayers();
  const algo = document.getElementById('algoSelect').value;
  const mode = document.getElementById('dispatchMode').value;
  if (mode === 'manual') {
    document.getElementById('s-mode').textContent = 'Manual Hospital';
    await runManualRoute(selectedSourceNode, algo);
  } else {
    await runAutoDispatch(selectedSourceNode, algo);
  }
}

function clearMap() {
  clearDynamicLayers();
  if (emergencyMarker) { map.removeLayer(emergencyMarker); emergencyMarker = null; }
  selectedSourceNode = null;
  document.getElementById('s-mode').textContent =
    document.getElementById('dispatchMode').value === 'manual' ? 'Manual Hospital' : 'Auto Dispatch';
  ['s-algo', 's-nodes', 's-edges', 's-time', 's-dist', 's-path', 's-cx'].forEach(id => {
    document.getElementById(id).textContent = '—';
  });
}

function updateTrafficDisplay(v) {
  document.getElementById('trafficVal').textContent = parseFloat(v).toFixed(1) + 'x';
}

async function applyTraffic() {
  const edgeId = parseInt(document.getElementById('edgeIdInput').value);
  const tw = parseFloat(document.getElementById('trafficSlider').value);
  if (!edgeId) { alert('Enter an Edge ID first (hover over a road on the map)'); return; }
  const res = await fetch(`${API}/api/traffic/`, {
    method: 'POST', headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ edge_id: edgeId, traffic_weight: tw })
  });
  const d = await res.json();
  if (d.error) { alert(d.error); return; }
  const selectedLayer = edgeLayers.get(edgeId);
  if (selectedLayer && selectedLayer.edgeData) {
    selectedLayer.edgeData.traffic_weight = tw;
    selectedLayer.bindTooltip(`Edge ${edgeId} | ${selectedLayer.edgeData.distance.toFixed(2)} km | Traffic: ${tw}x`);
  }
  document.getElementById('edgeSelectionHint').textContent = `Edge ${edgeId} updated to ${tw.toFixed(1)}x`;
  alert(`${d.message}\n\nRun Simulation again to compare route changes.`);
}

loadGraph();
