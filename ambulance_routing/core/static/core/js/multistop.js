/* multistop.js – Multi-Stop DP Routing page logic */

const API = 'http://127.0.0.1:8000';
const map = L.map('map', { preferCanvas: true }).setView([31.5204, 74.3587], 13);
let tileLayer = null;

const MAP_TILES = {
  light: { url: 'https://{s}.basemaps.cartocdn.com/light_nolabels/{z}/{x}/{y}{r}.png', options: { attribution: '© OpenStreetMap © CARTO', subdomains: 'abcd', maxZoom: 20 } },
  dark: { url: 'https://{s}.basemaps.cartocdn.com/dark_nolabels/{z}/{x}/{y}{r}.png', options: { attribution: '© OpenStreetMap © CARTO', subdomains: 'abcd', maxZoom: 20 } }
};

function setMapTheme(theme = 'light') {
  const cfg = MAP_TILES[theme] || MAP_TILES.light;
  if (tileLayer) map.removeLayer(tileLayer);
  tileLayer = L.tileLayer(cfg.url, cfg.options).addTo(map);
}
setMapTheme('light');

let selectedStops = [];
let allNodes = [];
let graphData = null;
let dpLayer = null, bfLayer = null, markerLayers = [];
let baseEdgeLayer = null;
let routeRunner = null;
let animFrame = null;
let stopMarkers = {};
let previewMarker = null;

async function loadGraph() {
  try {
    const r = await fetch(`${API}/api/graph/`);
    graphData = await r.json();
    allNodes = graphData.nodes || [];
    const lines = (graphData.edges || []).map(e => [[e.source_lat, e.source_lon], [e.dest_lat, e.dest_lon]]);
    baseEdgeLayer = L.polyline(lines, { color: '#94a3b8', opacity: 0.2, weight: 3.5, smoothFactor: 1 }).addTo(map);

    // Draw small node markers so all nodes are visible on the map
    allNodes.forEach(n => {
      L.circleMarker([n.latitude, n.longitude], {
        radius: 3, color: '#94a3b8', fillColor: '#94a3b8',
        fillOpacity: 0.4, weight: 0.8
      }).addTo(map);
    });
    const sel = document.getElementById('stopSelect');
    sel.innerHTML = allNodes.map(n => `<option value="${n.id}">${n.label}</option>`).join('');
    if (allNodes.length > 0) {
      const lats = allNodes.map(n => n.latitude);
      const lons = allNodes.map(n => n.longitude);
      map.fitBounds([[Math.min(...lats), Math.min(...lons)], [Math.max(...lats), Math.max(...lons)]], { padding: [30, 30] });
    }
  } catch (e) { console.error('Graph load failed:', e); }
}

function addStop() {
  const sel = document.getElementById('stopSelect');
  const id = parseInt(sel.value);
  const label = sel.options[sel.selectedIndex]?.text || `Node ${id}`;
  if (selectedStops.find(s => s.id === id)) return;
  if (selectedStops.length >= 8) { alert('Maximum 8 stops'); return; }
  selectedStops.push({ id, label });
  renderStopsList();
  placeStopMarker(id, label, selectedStops.length);
  clearPreviewMarker();
}

function removeStop(id) {
  selectedStops = selectedStops.filter(s => s.id !== id);
  if (stopMarkers[id]) { map.removeLayer(stopMarkers[id]); delete stopMarkers[id]; }
  refreshAllStopMarkers();
  renderStopsList();
}

function renderStopsList() {
  const el = document.getElementById('stopsList');
  if (!selectedStops.length) {
    el.innerHTML = '<span style="font-size:11px;color:var(--text3)">Add at least 2 stops</span>';
    return;
  }
  el.innerHTML = selectedStops.map((s, i) => `
    <div class="stop-tag">
      <span class="stop-tag-name">${i + 1}. ${s.label}</span>
      <span class="stop-remove" onclick="removeStop(${s.id})">x</span>
    </div>
  `).join('');
}

function nearestNode(lat, lon) {
  let best = null, bestDist = Infinity;
  allNodes.forEach(n => {
    const d = Math.hypot(n.latitude - lat, n.longitude - lon);
    if (d < bestDist) { bestDist = d; best = n; }
  });
  return best;
}

function placeStopMarker(nodeId, label, number) {
  const node = allNodes.find(n => n.id === nodeId);
  if (!node) return;
  if (stopMarkers[nodeId]) map.removeLayer(stopMarkers[nodeId]);
  const icon = L.divIcon({
    className: '',
    html: `<div class="stop-marker-icon">${number}</div>`,
    iconSize: [26, 26], iconAnchor: [13, 13]
  });
  const marker = L.marker([node.latitude, node.longitude], { icon, zIndexOffset: 1000 })
    .bindTooltip(`Stop ${number}: ${label}`, { permanent: false })
    .addTo(map);
  stopMarkers[nodeId] = marker;
}

function refreshAllStopMarkers() {
  Object.values(stopMarkers).forEach(m => map.removeLayer(m));
  stopMarkers = {};
  selectedStops.forEach((s, i) => placeStopMarker(s.id, s.label, i + 1));
}

function clearAllStopMarkers() {
  Object.values(stopMarkers).forEach(m => map.removeLayer(m));
  stopMarkers = {};
  clearPreviewMarker();
}

function clearPreviewMarker() {
  if (previewMarker) { map.removeLayer(previewMarker); previewMarker = null; }
}

// Show preview when dropdown selection changes
document.addEventListener('DOMContentLoaded', () => {
  const sel = document.getElementById('stopSelect');
  if (sel) {
    sel.addEventListener('change', () => {
      clearPreviewMarker();
      const id = parseInt(sel.value);
      if (isNaN(id)) return;
      if (selectedStops.find(s => s.id === id)) return;
      const node = allNodes.find(n => n.id === id);
      if (!node) return;
      const icon = L.divIcon({
        className: '',
        html: `<div class="preview-marker-icon">?</div>`,
        iconSize: [22, 22], iconAnchor: [11, 11]
      });
      previewMarker = L.marker([node.latitude, node.longitude], { icon, zIndexOffset: 900 })
        .bindTooltip(`Preview: ${node.label}`, { permanent: false })
        .addTo(map);
      map.panTo([node.latitude, node.longitude], { animate: true });
    });
  }
});

async function runDP() {
  if (selectedStops.length < 2) { alert('Add at least 2 stops'); return; }
  document.getElementById('loading').style.display = 'block';
  clearRoutes();
  try {
    const r = await fetch(`${API}/api/multistop/`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ stops: selectedStops.map(s => s.id) })
    });
    const data = await r.json();
    document.getElementById('loading').style.display = 'none';
    if (data.error) { alert(data.error); return; }
    renderResults(data);
  } catch (e) {
    document.getElementById('loading').style.display = 'none';
    console.error(e);
    alert('API call failed. Make sure Django is running on 127.0.0.1:8000');
  }
}

function renderResults(data) {
  const dp = data.dp;
  const bf = data.brute_force;
  const n = selectedStops.length;

  document.getElementById('dp-dist').textContent = dp.total_distance != null ? dp.total_distance.toFixed(2) + ' km' : '—';
  document.getElementById('dp-states').textContent = dp.states_explored ?? '—';
  document.getElementById('dp-time').textContent = dp.execution_time_ms != null ? dp.execution_time_ms + ' ms' : '—';

  document.getElementById('bf-dist').textContent = bf.total_distance != null ? bf.total_distance.toFixed(2) + ' km' : '—';
  document.getElementById('bf-states').textContent = bf.permutations_tried ?? '—';
  document.getElementById('bf-time').textContent = bf.execution_time_ms != null ? bf.execution_time_ms + ' ms' : '—';

  const dpCoords = dp.path_coords || [];
  document.getElementById('dpRoute').innerHTML = dpCoords.map((c, i) =>
    i < dpCoords.length - 1
      ? `<div class="route-step"><span style="color:var(--green)">${c.label}</span><span class="route-arrow"> → </span></div>`
      : `<div class="route-step"><span style="color:var(--green)">${c.label}</span></div>`
  ).join('');

  clearMarkers();
  dpCoords.forEach((c, i) => {
    const icon = L.divIcon({
      className: '',
      html: `<div style="width:24px;height:24px;border-radius:50%;background:${i === 0 ? 'var(--green)' : '#fff'};border:2px solid var(--green);display:flex;align-items:center;justify-content:center;font-size:11px;font-weight:bold;color:${i === 0 ? '#fff' : 'var(--green)'};">${i + 1}</div>`,
      iconSize: [24, 24], iconAnchor: [12, 12]
    });
    const m = L.marker([c.lat, c.lon], { icon }).addTo(map);
    m.bindTooltip(`Stop ${i + 1}: ${c.label}`, { permanent: false });
    markerLayers.push(m);
  });

  // Use detailed_path_coords (follows actual graph edges) for polyline
  const detailedCoords = dp.detailed_path_coords || dpCoords;
  if (detailedCoords.length >= 2) {
    const latlngs = detailedCoords.map(c => [c.lat, c.lon]);
    dpLayer = L.polyline(latlngs, { color: '#1e7e34', weight: 4, opacity: 0.9 }).addTo(map);
    map.fitBounds(dpLayer.getBounds(), { padding: [40, 40] });
    animateRoute(latlngs);
  }

  const nFact = factorial(n);
  const dpOps = Math.pow(2, n) * n * n;
  document.getElementById('ov-dp').textContent = dp.total_distance?.toFixed(2) + ' km' || '—';
  document.getElementById('ov-bf').textContent = bf.total_distance?.toFixed(2) + ' km' || '—';
  document.getElementById('ov-dp-t').textContent = (dp.execution_time_ms ?? '—') + ' ms';
  document.getElementById('ov-bf-t').textContent = (bf.execution_time_ms ?? '—') + ' ms';
  document.getElementById('ov-nfact').textContent = nFact.toLocaleString();
  document.getElementById('ov-dpops').textContent = Math.round(dpOps).toLocaleString();
  document.getElementById('compOverlay').style.display = 'block';
}

function animateRoute(latlngs) {
  if (!latlngs || latlngs.length < 2) return;
  if (routeRunner) map.removeLayer(routeRunner);
  if (animFrame) cancelAnimationFrame(animFrame);
  routeRunner = L.circleMarker(latlngs[0], {
    radius: 7, color: '#fff', weight: 2,
    fillColor: '#1a56a0', fillOpacity: 1, pane: 'markerPane',
  }).addTo(map);
  const durationPerSegment = parseInt(document.getElementById('animSpeed').value || '620', 10);
  let segmentIndex = 0;
  let segmentStart = performance.now();
  function frame(now) {
    const from = latlngs[segmentIndex];
    const to = latlngs[segmentIndex + 1];
    if (!from || !to) return;
    const t = Math.min(1, (now - segmentStart) / durationPerSegment);
    const lat = from[0] + (to[0] - from[0]) * t;
    const lon = from[1] + (to[1] - from[1]) * t;
    routeRunner.setLatLng([lat, lon]);
    if (t >= 1) {
      segmentIndex += 1;
      segmentStart = now;
      if (segmentIndex >= latlngs.length - 1) return;
    }
    animFrame = requestAnimationFrame(frame);
  }
  animFrame = requestAnimationFrame(frame);
}

function factorial(n) {
  let r = 1; for (let i = 2; i <= n; i++) r *= i; return r;
}

function clearMarkers() {
  markerLayers.forEach(m => map.removeLayer(m));
  markerLayers = [];
}

function clearRoutes() {
  if (dpLayer) { map.removeLayer(dpLayer); dpLayer = null; }
  if (bfLayer) { map.removeLayer(bfLayer); bfLayer = null; }
  if (routeRunner) { map.removeLayer(routeRunner); routeRunner = null; }
  if (animFrame) cancelAnimationFrame(animFrame);
  clearMarkers();
}

function clearAll() {
  clearRoutes();
  clearAllStopMarkers();
  selectedStops = [];
  renderStopsList();
  ['dp-dist', 'dp-states', 'dp-time', 'bf-dist', 'bf-states', 'bf-time']
    .forEach(id => document.getElementById(id).textContent = '—');
  document.getElementById('dpRoute').innerHTML = '';
  document.getElementById('compOverlay').style.display = 'none';
}

map.on('click', (e) => {
  if (!allNodes.length) return;
  const best = nearestNode(e.latlng.lat, e.latlng.lng);
  if (!best) return;
  if (selectedStops.find(s => s.id === best.id)) return;
  if (selectedStops.length >= 8) { alert('Maximum 8 stops'); return; }
  const label = `${best.label} (ID ${best.id})`;
  selectedStops.push({ id: best.id, label });
  renderStopsList();
  placeStopMarker(best.id, label, selectedStops.length);
  clearPreviewMarker();
});

loadGraph();
