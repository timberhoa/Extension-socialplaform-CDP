// popup.js — CDP RPA Worker (v1.1.0 with Debug tab)

// ─── DOM refs ─────────────────────────────────────────────────
const dot          = document.getElementById('dot');
const connStatus   = document.getElementById('conn-status');
const connUrl      = document.getElementById('conn-url');
const statDone     = document.getElementById('stat-done');
const statFail     = document.getElementById('stat-fail');
const statRunning  = document.getElementById('stat-running');
const logBox       = document.getElementById('log-box');
const toggleEl     = document.getElementById('main-toggle');
const toggleLabel  = document.getElementById('toggle-label');
const btnClear     = document.getElementById('btn-clear');
const btnClearShots= document.getElementById('btn-clear-shots');
const uptimeText   = document.getElementById('uptime-text');
const shotGallery  = document.getElementById('shot-gallery');
const shotCount    = document.getElementById('shot-count');
const dlogList     = document.getElementById('dlog-list');
const dlogCount    = document.getElementById('dlog-count');
const lightbox     = document.getElementById('lightbox');
const lightboxImg  = document.getElementById('lightbox-img');

// ─── Tab switching ────────────────────────────────────────────
document.querySelectorAll('.tab-btn').forEach(btn => {
  btn.addEventListener('click', () => {
    document.querySelectorAll('.tab-btn').forEach(b => b.classList.remove('active'));
    document.querySelectorAll('.tab-panel').forEach(p => p.classList.remove('active'));
    btn.classList.add('active');
    document.getElementById(`tab-${btn.dataset.tab}`).classList.add('active');
    if (btn.dataset.tab === 'debug') refreshDebug();
  });
});

// ─── Lightbox ────────────────────────────────────────────────
lightbox.addEventListener('click', () => lightbox.classList.remove('open'));

// ─── Helpers ──────────────────────────────────────────────────

function setConnUI(state) {
  dot.className        = `dot ${state}`;
  connStatus.className = `conn-status ${state}`;
  connStatus.textContent = { connected: 'Connected', connecting: 'Connecting…', disconnected: 'Disconnected' }[state] ?? state;
}

function addLog(text, type = 'info') {
  const placeholder = logBox.querySelector('.log-line.info');
  if (placeholder?.textContent.includes('Waiting')) placeholder.remove();

  const now  = new Date().toLocaleTimeString('en-GB', { hour12: false });
  const line = document.createElement('div');
  line.className   = `log-line ${type}`;
  line.textContent = `[${now}] ${text}`;
  logBox.appendChild(line);
  while (logBox.children.length > 60) logBox.removeChild(logBox.firstChild);
  logBox.scrollTop = logBox.scrollHeight;
}

// ─── Debug: Screenshots ───────────────────────────────────────

function renderScreenshots(list) {
  shotCount.textContent = list.length;
  if (!list || list.length === 0) {
    shotGallery.innerHTML = '<div class="no-data">No screenshots yet</div>';
    return;
  }
  shotGallery.innerHTML = '';
  list.forEach(({ filename, dataUrl, ts }) => {
    const age = ts ? new Date(ts).toLocaleTimeString('en-GB', { hour12: false }) : '';
    const item = document.createElement('div');
    item.className = 'shot-item';
    item.innerHTML = `
      <div class="shot-title">
        <span>${filename}</span>
        <span>${age} <a class="dl-link" href="${dataUrl}" download="${filename}">⬇ Save</a></span>
      </div>
      <img class="shot-img" src="${dataUrl}" alt="${filename}" />
    `;
    item.querySelector('.shot-img').addEventListener('click', () => {
      lightboxImg.src = dataUrl;
      lightbox.classList.add('open');
    });
    shotGallery.appendChild(item);
  });
}

// ─── Debug: log_message entries ────────────────────────────────

function renderDebugLogs(list) {
  dlogCount.textContent = list.length;
  if (!list || list.length === 0) {
    dlogList.innerHTML = '<div class="no-data">No debug messages yet</div>';
    return;
  }
  dlogList.innerHTML = '';
  list.slice(0, 50).forEach(({ timestamp, level, message }) => {
    const time = timestamp ? new Date(timestamp).toLocaleTimeString('en-GB', { hour12: false }) : '';
    const item = document.createElement('div');
    item.className = `dlog-item ${level}`;
    item.innerHTML = `<div class="dlog-time">[${time}] ${level.toUpperCase()}</div><div class="dlog-msg">${message}</div>`;
    dlogList.appendChild(item);
  });
}

// ─── Refresh debug tab ────────────────────────────────────────

async function refreshDebug() {
  chrome.storage.local.get(['screenshots', 'debugLogs'], (res) => {
    renderScreenshots(res.screenshots || []);
    renderDebugLogs(res.debugLogs || []);
  });
}

// ─── Pull state from background ───────────────────────────────

async function refreshState() {
  let resp;
  try {
    resp = await chrome.runtime.sendMessage({ type: 'GET_STATE' });
  } catch {
    setConnUI('disconnected');
    addLog('Background not reachable', 'error');
    return;
  }
  if (!resp) return;

  setConnUI(resp.wsState);
  connUrl.textContent     = resp.wsUrl ?? 'ws://localhost:3001';
  statDone.textContent    = resp.stats.done;
  statFail.textContent    = resp.stats.failed;
  statRunning.textContent = resp.stats.running > 0 ? resp.stats.running : '—';
  toggleEl.checked        = resp.enabled;
  toggleLabel.textContent = resp.enabled ? 'ON' : 'OFF';

  if (resp.logs && resp.logs.length) {
    logBox.innerHTML = '';
    resp.logs.forEach(({ text, type }) => addLog(text, type));
  }
}

// ─── Toggle ──────────────────────────────────────────────────

toggleEl.addEventListener('change', async () => {
  const enabled = toggleEl.checked;
  toggleLabel.textContent = enabled ? 'ON' : 'OFF';
  addLog(enabled ? 'Worker enabled' : 'Worker paused', enabled ? 'success' : 'warn');
  await chrome.runtime.sendMessage({ type: 'SET_ENABLED', enabled });
  await refreshState();
});

// ─── Clear buttons ────────────────────────────────────────────

btnClear.addEventListener('click', async () => {
  logBox.innerHTML = '<div class="log-line info">Log cleared</div>';
  await chrome.runtime.sendMessage({ type: 'CLEAR_LOGS' });
});

btnClearShots.addEventListener('click', () => {
  chrome.storage.local.set({ screenshots: [], debugLogs: [] }, () => {
    renderScreenshots([]);
    renderDebugLogs([]);
  });
});

// ─── Poll ─────────────────────────────────────────────────────

refreshState();
refreshDebug();
const polling = setInterval(refreshState, 1500);
window.addEventListener('unload', () => clearInterval(polling));
