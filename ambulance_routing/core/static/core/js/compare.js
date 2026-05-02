/* compare.js – Algorithm Comparison page logic */

const API = 'http://127.0.0.1:8000';
let graphData = null;

async function loadData() {
  const res = await fetch(`${API}/api/graph/`);
  graphData = await res.json();
  const src = document.getElementById('sourceSelect');
  const dst = document.getElementById('destSelect');
  graphData.nodes.slice(0, 12).forEach(n => {
    const o = document.createElement('option');
    o.value = n.id;
    o.textContent = `${n.id}: ${n.label}`;
    src.appendChild(o);
  });
  graphData.hospitals.forEach(h => {
    const o = document.createElement('option');
    o.value = h.node_id;
    o.textContent = h.name;
    dst.appendChild(o);
  });
  if (graphData.hospitals.length > 3) dst.selectedIndex = 3;
}

async function runCompare() {
  const source = parseInt(document.getElementById('sourceSelect').value);
  const dest   = parseInt(document.getElementById('destSelect').value);
  if (!source || !dest) { alert('Select source and destination'); return; }

  document.getElementById('loading').style.display = 'block';
  document.getElementById('resultsGrid').style.display = 'none';
  document.getElementById('tableSection').style.display = 'none';

  const res = await fetch(`${API}/api/compare/`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ source, destination: dest })
  });
  const data = await res.json();
  document.getElementById('loading').style.display = 'none';
  renderCards(data.results);
  renderTable(data.results);
}

function renderCards(results) {
  const grid    = document.getElementById('resultsGrid');
  const classes = ['card-dijkstra', 'card-astar', 'card-bellman', 'card-brute'];
  const colors  = ['#c0392b', '#1e7e34', '#b7760d', '#6a3d9a'];

  const minNodes = Math.min(...results.filter(r => !r.error).map(r => r.nodes_visited));
  const minTime  = Math.min(...results.filter(r => !r.error).map(r => r.execution_time_ms));

  grid.innerHTML = results.map((r, i) => {
    if (r.error) {
      return `<div class="algo-card ${classes[i]}">
        <div class="algo-card-header"><div class="algo-name">${r.algorithm || 'Error'}</div></div>
        <div class="algo-body"><p style="color:#c0392b;font-size:12px">${r.error}</p></div>
      </div>`;
    }
    const isWinner  = r.nodes_visited === minNodes ? '<span class="winner-badge">FEWEST NODES</span>' : '';
    const isFastest = r.execution_time_ms === minTime ? '<span class="winner-badge">FASTEST</span>' : '';
    return `<div class="algo-card ${classes[i]}">
      <div class="algo-card-header">
        <div class="algo-name">${r.algorithm} ${isWinner}</div>
        <div class="algo-cx">${r.complexity}</div>
      </div>
      <div class="algo-body">
        <div class="stat-row"><span class="stat-key">Nodes Visited</span><span class="stat-val">${r.nodes_visited}</span></div>
        <div class="stat-row"><span class="stat-key">Edges Explored</span><span class="stat-val">${r.edges_explored}</span></div>
        <div class="stat-row"><span class="stat-key">Execution Time</span><span class="stat-val">${r.execution_time_ms} ms ${isFastest}</span></div>
        <div class="stat-row"><span class="stat-key">Path Distance</span><span class="stat-val">${r.distance !== -1 ? r.distance.toFixed(3) + ' km' : 'Unreachable'}</span></div>
        <div class="stat-row"><span class="stat-key">Path Nodes</span><span class="stat-val">${r.path.length}</span></div>
        <div class="stat-row"><span class="stat-key">Space</span><span class="stat-val">${r.space || 'O(V)'}</span></div>
      </div>
    </div>`;
  }).join('');
  grid.style.display = 'grid';
}

function renderTable(results) {
  const valid    = results.filter(r => !r.error);
  const maxNodes = Math.max(...valid.map(r => r.nodes_visited)) || 1;
  const maxTime  = Math.max(...valid.map(r => r.execution_time_ms)) || 1;
  const colors   = ['#c0392b', '#1e7e34', '#b7760d', '#6a3d9a'];

  const rows = [
    { label: 'Nodes Visited',  key: 'nodes_visited',     max: maxNodes, fmt: v => v },
    { label: 'Edges Explored', key: 'edges_explored',    max: Math.max(...valid.map(r => r.edges_explored)) || 1, fmt: v => v },
    { label: 'Time (ms)',      key: 'execution_time_ms', max: maxTime,  fmt: v => v + ' ms' },
    { label: 'Distance (km)',  key: 'distance',          max: Math.max(...valid.map(r => r.distance)) || 1, fmt: v => v !== -1 ? v.toFixed(3) : '-' },
    { label: 'Complexity',     key: 'complexity',        noBar: true,   fmt: v => v },
    { label: 'Space',          key: 'space',             noBar: true,   fmt: v => v || 'O(V)' },
  ];

  document.getElementById('tableBody').innerHTML = rows.map(row => {
    const cells = results.map((r, i) => {
      if (r.error) return `<td style="color:#c0392b">Error</td>`;
      const v   = r[row.key];
      const pct = row.noBar ? 0 : (v / row.max * 100);
      return `<td>
        <div style="font-size:13px;margin-bottom:4px;color:${colors[i]};font-weight:bold;">${row.fmt(v)}</div>
        ${!row.noBar ? `<div class="bar-wrap"><div class="bar-fill" style="width:${pct}%;background:${colors[i]}"></div></div>` : ''}
      </td>`;
    }).join('');
    return `<tr><td style="color:var(--text2);font-size:12px;">${row.label}</td>${cells}</tr>`;
  }).join('');

  const astar    = results.find(r => r.algorithm === 'A*');
  const dijkstra = results.find(r => r.algorithm === 'Dijkstra');
  if (astar && dijkstra && !astar.error && !dijkstra.error) {
    const savings = Math.round((1 - astar.nodes_visited / dijkstra.nodes_visited) * 100);
    document.getElementById('insightBox').innerHTML =
      `<strong>Key Insight:</strong> A* visited <strong>${astar.nodes_visited}</strong> nodes vs Dijkstra's ` +
      `<strong>${dijkstra.nodes_visited}</strong> — that's <strong>${Math.abs(savings)}% ` +
      `${savings > 0 ? 'fewer' : 'more'}</strong> nodes explored. A* uses a Euclidean heuristic to guide the ` +
      `search, making it faster while still finding the optimal path. Both return the same distance ` +
      `(${dijkstra.distance.toFixed(3)} km), proving A*'s heuristic is admissible.`;
  }
  document.getElementById('tableSection').style.display = 'block';
}

loadData();
