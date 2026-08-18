const PAGE_SIZE = 12;
let allEntries = [];
let activeLevels = new Set();
let searchTerm = "";
let sortAsc = true;
let page = 0;
let levelChart, timelineChart;

const LEVEL_COLORS = {
  ERROR: "#ff6b6b", CRITICAL: "#ff4757", FATAL: "#c0392b",
  WARN: "#f5b942", INFO: "#5fd68a", DEBUG: "#7fa7ef",
  TRACE: "#a29bfe", UNKNOWN: "#9aa5bd",
};

// ---------- error handling ----------
function showError(message) {
  console.error(message);
  const errorDiv = document.getElementById("errorMessage");
  if (!errorDiv) {
    const div = document.createElement("div");
    div.id = "errorMessage";
    div.className = "error-banner";
    document.body.insertBefore(div, document.body.firstChild);
  }
  document.getElementById("errorMessage").innerHTML = `<strong>Error:</strong> ${message}`;
  document.getElementById("errorMessage").style.display = "block";
}

function clearError() {
  const errorDiv = document.getElementById("errorMessage");
  if (errorDiv) errorDiv.style.display = "none";
}

// ---------- data loading ----------
async function loadUrl(url) {
  try {
    const res = await fetch(url);
    if (!res.ok) {
      const data = await res.json();
      throw new Error(data.error || `HTTP ${res.status}`);
    }
    return res.json();
  } catch (e) {
    showError(`Failed to load data: ${e.message}`);
    throw e;
  }
}

async function loadFile(file) {
  try {
    const fd = new FormData();
    fd.append("file", file);
    const res = await fetch("/api/upload", { method: "POST", body: fd });
    if (!res.ok) {
      const data = await res.json();
      throw new Error(data.error || `HTTP ${res.status}`);
    }
    return res.json();
  } catch (e) {
    showError(`Failed to upload file: ${e.message}`);
    throw e;
  }
}

function render(data) {
  if (data.error) {
    showError(data.error);
    return;
  }
  clearError();
  allEntries = data.entries;
  activeLevels = new Set(Object.keys(data.stats.level_counts));
  page = 0;
  document.getElementById("dashboard").hidden = false;
  document.getElementById("fileInfo").textContent =
    `${data.filename} — ${data.stats.total} entries parsed`;
  renderStats(data.stats);
  renderCharts(data.stats);
  renderTopLists(data.stats);
  renderLevelFilters(data.stats.level_counts);
  renderTable();
}

// ---------- stats & charts ----------
function renderStats(s) {
  document.getElementById("statTotal").textContent = s.total;
  document.getElementById("statErrors").textContent = s.errors;
  document.getElementById("statWarnings").textContent = s.warnings;
  document.getElementById("statRate").textContent = s.error_rate + "%";
}

function renderCharts(s) {
  const labels = Object.keys(s.level_counts);
  const colors = labels.map(l => LEVEL_COLORS[l] || "#9aa5bd");
  levelChart?.destroy();
  levelChart = new Chart(document.getElementById("levelChart"), {
    type: "doughnut",
    data: { labels, datasets: [{ data: Object.values(s.level_counts), backgroundColor: colors, borderColor: "#18223a", borderWidth: 3 }] },
    options: {
      plugins: { legend: { position: "bottom", labels: { color: "#c4cfe6" } }, title: { display: true, text: "Level Distribution", color: "#e4e9f2" } },
      onClick: (_, els) => {
        if (!els.length) return;
        toggleLevel(labels[els[0].index]);
      },
    },
  });

  timelineChart?.destroy();
  timelineChart = new Chart(document.getElementById("timelineChart"), {
    type: "line",
    data: {
      labels: Object.keys(s.timeline),
      datasets: [{ label: "Events", data: Object.values(s.timeline), borderColor: "#5b8def", backgroundColor: "rgba(91,141,239,.2)", fill: true, tension: .3 }],
    },
    options: {
      plugins: { legend: { display: false }, title: { display: true, text: "Events Over Time", color: "#e4e9f2" } },
      scales: { x: { ticks: { color: "#8fa3c8" } }, y: { ticks: { color: "#8fa3c8" }, beginAtZero: true } },
    },
  });
}

function renderTopLists(s) {
  document.getElementById("topErrors").innerHTML =
    s.top_errors.map(([msg, n]) => `<li><span>×${n}</span>${escapeHtml(msg)}</li>`).join("") || "<li>None</li>";
  document.getElementById("topSources").innerHTML =
    s.top_sources.map(([src, n]) => `<li><span>×${n}</span>${escapeHtml(src)}</li>`).join("") || "<li>None</li>";
}

// ---------- table ----------
function renderLevelFilters(levelCounts) {
  const box = document.getElementById("levelFilters");
  box.innerHTML = "";
  for (const lvl of Object.keys(levelCounts).sort()) {
    const chip = document.createElement("span");
    chip.className = "chip active";
    chip.textContent = lvl;
    chip.onclick = () => toggleLevel(lvl);
    chip.dataset.level = lvl;
    box.appendChild(chip);
  }
}

function toggleLevel(lvl) {
  activeLevels.has(lvl) ? activeLevels.delete(lvl) : activeLevels.add(lvl);
  document.querySelectorAll(".chip").forEach(c =>
    c.classList.toggle("active", activeLevels.has(c.dataset.level)));
  page = 0;
  renderTable();
}

function filtered() {
  return allEntries.filter(e =>
    activeLevels.has(e.level) &&
    (!searchTerm || e.message.toLowerCase().includes(searchTerm) || e.source.toLowerCase().includes(searchTerm))
  ).sort((a, b) => {
    const ta = a.timestamp || "", tb = b.timestamp || "";
    return sortAsc ? ta.localeCompare(tb) : tb.localeCompare(ta);
  });
}

function renderTable() {
  const rows = filtered();
  const pages = Math.max(1, Math.ceil(rows.length / PAGE_SIZE));
  page = Math.min(page, pages - 1);
  const slice = rows.slice(page * PAGE_SIZE, (page + 1) * PAGE_SIZE);
  document.getElementById("logBody").innerHTML = slice.map(e =>
    `<tr><td>${escapeHtml(e.timestamp || "-")}</td>` +
    `<td><span class="badge ${e.level}">${e.level}</span></td>` +
    `<td>${escapeHtml(e.source)}</td>` +
    `<td class="msg">${escapeHtml(e.message)}</td></tr>`).join("");
  document.getElementById("pageInfo").textContent = `Page ${page + 1} / ${pages} (${rows.length} rows)`;
  document.getElementById("prevPage").disabled = page === 0;
  document.getElementById("nextPage").disabled = page >= pages - 1;
}

function escapeHtml(s) {
  return s.replace(/[&<>"']/g, c => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]));
}

// ---------- events ----------
document.getElementById("sampleBtn").onclick = async () => {
  try {
    render(await loadUrl("/api/sample"));
  } catch (e) {
    // Error already shown by loadUrl
  }
};

document.getElementById("fileInput").onchange = async e => {
  if (e.target.files[0]) {
    try {
      render(await loadFile(e.target.files[0]));
    } catch (e) {
      // Error already shown by loadFile
    }
  }
};

const dz = document.getElementById("dropzone");
dz.ondragover = e => { e.preventDefault(); dz.classList.add("dragover"); };
dz.ondragleave = () => dz.classList.remove("dragover");
dz.ondrop = async e => {
  e.preventDefault();
  dz.classList.remove("dragover");
  if (e.dataTransfer.files[0]) {
    try {
      render(await loadFile(e.dataTransfer.files[0]));
    } catch (e) {
      // Error already shown by loadFile
    }
  }
};

document.getElementById("searchBox").oninput = e => {
  searchTerm = e.target.value.toLowerCase();
  page = 0;
  renderTable();
};

document.getElementById("sortTime").onclick = () => {
  sortAsc = !sortAsc;
  renderTable();
};

document.getElementById("prevPage").onclick = () => { page--; renderTable(); };
document.getElementById("nextPage").onclick = () => { page++; renderTable(); };
