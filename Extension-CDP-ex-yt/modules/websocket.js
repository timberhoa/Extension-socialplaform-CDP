// ============================================================
//  websocket.js — Kết nối WebSocket, Heartbeat, State Reporting
// ============================================================

import {
  WS_URL, RECONNECT_DELAY_MS, HEARTBEAT_INTERVAL_MS,
  ws, workerId, workerEnabled,
  setWs, setWsState, setReconnectTimer, setHeartbeatTimer,
  reconnectTimer, heartbeatTimer,
} from './config.js';
import { pushLog }             from './utils.js';
import { getOrCreateWorkerId } from './identity.js';
import { executeTask }         from './executor.js';

// ─── Heartbeat ───────────────────────────────────────────────

export function startHeartbeat() {
  stopHeartbeat();
  const timer = setInterval(() => {
    // Đọc ws/workerId trực tiếp từ module config (live binding)
    const { ws: _ws, workerId: _id } = getState();
    if (_ws && _ws.readyState === WebSocket.OPEN && _id) {
      _ws.send(JSON.stringify({ type: 'ping', worker_id: _id }));
    }
  }, HEARTBEAT_INTERVAL_MS);
  setHeartbeatTimer(timer);
}

export function stopHeartbeat() {
  if (heartbeatTimer) {
    clearInterval(heartbeatTimer);
    setHeartbeatTimer(null);
  }
}

// ─── State Reporting ─────────────────────────────────────────

export function sendStateUpdate(state, taskId = null) {
  const { ws: _ws, workerId: _id } = getState();
  if (_ws && _ws.readyState === WebSocket.OPEN && _id) {
    const msg = { type: 'state_update', worker_id: _id, state };
    if (taskId) msg.task_id = taskId;
    _ws.send(JSON.stringify(msg));
    console.log(`[STATE] Sent state: ${state}`);
  }
}

// ─── WebSocket Connection ────────────────────────────────────

export async function connect() {
  const { ws: _ws, workerId: _id } = getState();
  if (_ws && (_ws.readyState === WebSocket.OPEN || _ws.readyState === WebSocket.CONNECTING)) return;

  // Đảm bảo đã có workerId
  const id = _id || await getOrCreateWorkerId();

  setWsState('connecting');
  console.log('[WS] Connecting to', WS_URL);
  pushLog('Connecting to server…', 'info');

  const socket = new WebSocket(WS_URL);
  setWs(socket);

  socket.onopen = () => {
    setWsState('connected');
    console.log('[WS] Connected to server');
    pushLog(`Connected! Worker ID: ${id.substring(0, 8)}…`, 'success');

    const { reconnectTimer: rt } = getState();
    if (rt) { clearTimeout(rt); setReconnectTimer(null); }

    socket.send(JSON.stringify({
      type: 'register',
      worker_id: id,
      agent: 'cdp-extension-v1',
    }));

    startHeartbeat();
  };

  socket.onmessage = async (event) => {
    let data;
    try { data = JSON.parse(event.data); }
    catch (e) { console.error('[WS] Failed to parse message:', e); return; }

    if (data.type === 'registered') {
      console.log('[WS] Registered successfully:', data.message);
      pushLog('Registered with server ✓', 'success');
      return;
    }

    if (data.type === 'task' && data.task) {
      const { workerEnabled: en } = getState();
      if (!en) {
        console.log('[WS] Worker disabled — ignoring task', data.task.task_id);
        pushLog(`Task ${data.task.task_id} ignored (worker OFF)`, 'warn');
        return;
      }
      console.log('[TASK] Received task:', data.task.task_id);
      pushLog(`Task received: ${data.task.task_id}`, 'info');
      await executeTask(data.task);
      return;
    }

    if (data.error) {
      console.error('[WS] Server error:', data.error);
      pushLog(`Server: ${data.error}`, 'error');
    }
  };

  socket.onerror = (err) => {
    console.error('[WS] Socket error:', err);
  };

  socket.onclose = () => {
    setWsState('disconnected');
    console.warn('[WS] Connection closed. Reconnecting in', RECONNECT_DELAY_MS, 'ms…');
    pushLog('Disconnected — will retry in 5s', 'warn');
    setWs(null);
    stopHeartbeat();
    scheduleReconnect();
  };
}

export function scheduleReconnect() {
  const { reconnectTimer: rt } = getState();
  if (rt) return;
  const timer = setTimeout(() => {
    setReconnectTimer(null);
    connect();
  }, RECONNECT_DELAY_MS);
  setReconnectTimer(timer);
}

/** Giữ service worker sống bằng cách reconnect mỗi 20s nếu cần. */
export function keepAlive() {
  setInterval(() => {
    const { ws: _ws } = getState();
    if (!_ws || _ws.readyState !== WebSocket.OPEN) connect();
  }, 20000);
}

// ─── Helper: đọc live state từ config module ─────────────────
// Cần đọc trực tiếp vì ES module exports là live bindings (readonly từ ngoài)
import * as cfg from './config.js';
function getState() {
  return {
    ws:             cfg.ws,
    workerId:       cfg.workerId,
    workerEnabled:  cfg.workerEnabled,
    reconnectTimer: cfg.reconnectTimer,
    heartbeatTimer: cfg.heartbeatTimer,
  };
}
