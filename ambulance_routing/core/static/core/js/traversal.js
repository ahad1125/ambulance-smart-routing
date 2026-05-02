/* traversal.js – BFS / DFS Network Analysis page logic */

const API = 'http://127.0.0.1:8000';
let map = L.map('map', { preferCanvas: true }).setView([33.63, 73.06], 13);
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

let bfsLayer  = L.layerGroup().addTo(map);
let dfsLayer  = L.layerGroup().addTo(map);
let baseLayer = L.layerGroup().addTo(map);
let graphData = null;

async function loadGraph() {
  const res = await fetch(`${API}/api/graph/`);
  graphData = await res.json();
  const sel = document.getElementById('startSelect');
  graphData.nodes.forEach(n => {
    const o = document.createElement('option');
    o.value = n.id;
    o.textContent = `${n.id}: ${n.label}`;
    sel.appendChild(o);
  });
  graphData.edges.forEach(e => {
    L.polyline([[e.source_lat, e.source_lon], [e.dest_lat, e.dest_lon]],
      { color: '#94a3b8', weight: 1, opacity: 0.22, smoothFactor: 1 }).addTo(baseLayer);
  });
  graphData.nodes.forEach(n => {
    L.circleMarker([n.latitude, n.longitude],
      { radius: 2, color: '#64748b', fillColor: '#64748b', fillOpacity: 0.25, weight: 0.7 }).addTo(baseLayer);
  });
  graphData.hospitals.forEach(h => {
    L.marker([h.latitude, h.longitude],
      { icon: L.divIcon({ html: '<div style="background:#1e7e34;color:#fff;padding:1px 4px;font-size:10px;border-radius:3px;border:1px solid #fff;">H</div>', iconSize: [18, 16] }) })
      .bindPopup(h.name).addTo(baseLayer);
  });
  if (graphData.nodes.length > 14) {
    document.getElementById('startSelect').value = graphData.nodes[14].id;
  }
}

function animateVisit(nodes, color, layerGroup, delay = 60) {
  nodes.forEach((n, i) => {
    setTimeout(() => {
      L.circleMarker([n.lat, n.lon], { radius: 6, color: '#fff', fillColor: color, fillOpacity: 0.85, weight: 1.5 })
        .bindTooltip(`#${i + 1}: ${n.label} (level/depth: ${n.level !== undefined ? n.level : n.depth})`)
        .addTo(layerGroup);
      if (n.parent && graphData) {
        const parent = nodes.find(p => p.node_id === n.parent);
        if (parent) {
          L.polyline([[parent.lat, parent.lon], [n.lat, n.lon]],
            { color, weight: 2.5, opacity: 0.7 }).addTo(layerGroup);
        }
      }
    }, i * delay);
  });
}

async function runBFS() {
  const startId = parseInt(document.getElementById('startSelect').value);
  bfsLayer.clearLayers();
  const res = await fetch(`${API}/api/bfs/`, {
    method: 'POST', headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ start: startId })
  });
  const data = await res.json();
  if (data.error) { alert(data.error); return; }
  document.getElementById('bfs-nodes').textContent = data.reachable_count;
  document.getElementById('bfs-edges').textContent = data.edges_explored;
  document.getElementById('bfs-time').textContent  = data.execution_time_ms + ' ms';
  animateVisit(data.visited_with_coords, '#1a7bbf', bfsLayer, 80);
  showOrderList(data.visited_with_coords, 'BFS', '#1a7bbf');
}

async function runDFS() {
  const startId = parseInt(document.getElementById('startSelect').value);
  dfsLayer.clearLayers();
  const res = await fetch(`${API}/api/dfs/`, {
    method: 'POST', headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ start: startId })
  });
  const data = await res.json();
  if (data.error) { alert(data.error); return; }
  document.getElementById('dfs-nodes').textContent = data.reachable_count;
  document.getElementById('dfs-edges').textContent = data.edges_explored;
  document.getElementById('dfs-time').textContent  = data.execution_time_ms + ' ms';
  animateVisit(data.visited_with_coords, '#1e7e34', dfsLayer, 80);
  showOrderList(data.visited_with_coords, 'DFS', '#1e7e34');
}

function showOrderList(nodes, label, color) {
  const el = document.getElementById('orderList');
  el.innerHTML =
    `<div style="font-size:11px;color:${color};margin-bottom:6px;font-weight:bold;">${label} TRAVERSAL ORDER</div>` +
    nodes.map((n, i) =>
      `<div class="order-item"><span class="order-idx">${i + 1}.</span>${n.label}</div>`
    ).join('');
}

function clearLayers() {
  bfsLayer.clearLayers();
  dfsLayer.clearLayers();
  ['bfs-nodes', 'bfs-edges', 'bfs-time', 'dfs-nodes', 'dfs-edges', 'dfs-time'].forEach(id => {
    document.getElementById(id).textContent = '—';
  });
  document.getElementById('orderList').innerHTML =
    '<p style="font-size:12px;color:var(--text3);padding:8px;">Run BFS or DFS to see traversal order</p>';
}

loadGraph();
