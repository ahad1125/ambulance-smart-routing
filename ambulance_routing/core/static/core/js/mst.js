/* mst.js – Minimum Spanning Tree page logic */

const API = 'http://127.0.0.1:8000';
const map = L.map('map', { preferCanvas: true }).setView([31.5204, 74.3587], 13);
let tileLayer = null;

const MAP_TILES = {
  light: { url: 'https://{s}.basemaps.cartocdn.com/light_nolabels/{z}/{x}/{y}{r}.png', options: { attribution: '© OpenStreetMap © CARTO', subdomains: 'abcd', maxZoom: 20 } },
  dark:  { url: 'https://{s}.basemaps.cartocdn.com/dark_nolabels/{z}/{x}/{y}{r}.png',  options: { attribution: '© OpenStreetMap © CARTO', subdomains: 'abcd', maxZoom: 20 } }
};

function setMapTheme(theme = 'light') {
  const cfg = MAP_TILES[theme] || MAP_TILES.light;
  if (tileLayer) map.removeLayer(tileLayer);
  tileLayer = L.tileLayer(cfg.url, cfg.options).addTo(map);
}
setMapTheme('light');

let allEdgesLayer = null, primsLayer = null, kruskalsLayer = null;
let nodeMarkers = [];
let graphData   = null;

async function loadGraph() {
  try {
    const r = await fetch(`${API}/api/graph/`);
    graphData = await r.json();
    drawAllEdges();
    drawNodes();
    if (graphData.nodes && graphData.nodes.length > 0) {
      const lats = graphData.nodes.map(n => n.latitude);
      const lons = graphData.nodes.map(n => n.longitude);
      map.fitBounds([[Math.min(...lats), Math.min(...lons)], [Math.max(...lats), Math.max(...lons)]], { padding: [30, 30] });
    }
  } catch (e) { console.error('Graph load failed:', e); }
}

function drawAllEdges() {
  if (!graphData) return;
  if (allEdgesLayer) map.removeLayer(allEdgesLayer);
  const lines = graphData.edges.map(e => [[e.source_lat, e.source_lon], [e.dest_lat, e.dest_lon]]);
  allEdgesLayer = L.polyline(lines, { color: '#94a3b8', opacity: 0.18, weight: 1.2, smoothFactor: 1 }).addTo(map);
}

function drawNodes() {
  if (!graphData) return;
  nodeMarkers.forEach(m => map.removeLayer(m));
  nodeMarkers = [];
  const hospitalIds = new Set((graphData.hospitals || []).map(h => h.node_id));
  for (const n of graphData.nodes) {
    const isHosp = hospitalIds.has(n.id);
    const icon = L.divIcon({
      className: '',
      html: isHosp
        ? `<div style="width:10px;height:10px;border-radius:50%;background:#c0392b;border:2px solid #fff;"></div>`
        : `<div style="width:6px;height:6px;border-radius:50%;background:#64748b;border:1px solid #94a3b8;"></div>`,
      iconSize:   [isHosp ? 10 : 6, isHosp ? 10 : 6],
      iconAnchor: [isHosp ? 5  : 3, isHosp ? 5  : 3]
    });
    const m = L.marker([n.latitude, n.longitude], { icon }).addTo(map);
    m.bindTooltip(`<b>${n.label}</b>${isHosp ? '<br>Hospital' : ''}`);
    nodeMarkers.push(m);
  }
}

async function runPrims() {
  if (primsLayer) { map.removeLayer(primsLayer); primsLayer = null; }
  document.getElementById('loading').style.display = 'block';
  try {
    const r    = await fetch(`${API}/api/mst/`);
    const data = await r.json();
    const result = data.prims;
    document.getElementById('loading').style.display = 'none';
    document.getElementById('prims-edges').textContent  = result.mst_edge_count || result.mst_edges_enriched?.length || '—';
    document.getElementById('prims-weight').textContent = result.total_weight ? result.total_weight.toFixed(2) : '—';
    document.getElementById('prims-time').textContent   = result.execution_time_ms ? result.execution_time_ms + ' ms' : '—';
    drawMST(result.mst_edges_enriched || [], '#6a3d9a', 'prims');
    showEdgeList(result.mst_edges_enriched || [], '#6a3d9a');
  } catch (e) {
    document.getElementById('loading').style.display = 'none';
    console.error(e);
  }
}

async function runKruskals() {
  if (kruskalsLayer) { map.removeLayer(kruskalsLayer); kruskalsLayer = null; }
  document.getElementById('loading').style.display = 'block';
  try {
    const r    = await fetch(`${API}/api/mst/`);
    const data = await r.json();
    const result = data.kruskals;
    document.getElementById('loading').style.display = 'none';
    document.getElementById('kruskal-edges').textContent  = result.mst_edge_count || result.mst_edges_enriched?.length || '—';
    document.getElementById('kruskal-weight').textContent = result.total_weight ? result.total_weight.toFixed(2) : '—';
    document.getElementById('kruskal-time').textContent   = result.execution_time_ms ? result.execution_time_ms + ' ms' : '—';
    drawMST(result.mst_edges_enriched || [], '#b7760d', 'kruskals');
    showEdgeList(result.mst_edges_enriched || [], '#b7760d');
  } catch (e) {
    document.getElementById('loading').style.display = 'none';
    console.error(e);
  }
}

function drawMST(edges, color, which) {
  const lines = edges.map(e => [[e.from_lat, e.from_lon], [e.to_lat, e.to_lon]]);
  const layer = L.polyline(lines, { color, weight: 3, opacity: 0.9 }).addTo(map);
  if (which === 'prims') primsLayer = layer;
  else kruskalsLayer = layer;
}

function showEdgeList(edges, color) {
  const el = document.getElementById('edgeList');
  if (!edges.length) {
    el.innerHTML = '<span style="font-size:11px;color:var(--text3);padding:8px;display:block;">No edges</span>';
    return;
  }
  el.innerHTML = edges.map(e =>
    `<div class="edge-item">
      <span style="color:${color}">${e.from_label} &rarr; ${e.to_label}</span>
      <span style="color:var(--text3)">${e.weight?.toFixed ? e.weight.toFixed(2) : e.weight}</span>
    </div>`
  ).join('');
}

function clearMST() {
  if (primsLayer)    { map.removeLayer(primsLayer);    primsLayer    = null; }
  if (kruskalsLayer) { map.removeLayer(kruskalsLayer); kruskalsLayer = null; }
  ['prims-edges', 'prims-weight', 'prims-time', 'kruskal-edges', 'kruskal-weight', 'kruskal-time']
    .forEach(id => document.getElementById(id).textContent = '—');
  document.getElementById('edgeList').innerHTML =
    '<span style="font-size:11px;color:var(--text3);padding:8px;display:block;">Run an algorithm to see edges</span>';
}

loadGraph();
