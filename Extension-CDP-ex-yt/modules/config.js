// ============================================================
//  config.js — Hằng số và State toàn cục (Singleton)
//  Tất cả module khác import từ đây, không tự define state riêng
// ============================================================

// ─── Hằng số kết nối ─────────────────────────────────────────
export const WS_URL               = 'ws://localhost:3001/ws/worker';
export const RECONNECT_DELAY_MS   = 5000;
export const HEARTBEAT_INTERVAL_MS = 10000;

// ─── State WebSocket ──────────────────────────────────────────
export let ws             = null;
export let reconnectTimer = null;
export let heartbeatTimer = null;
export let workerId       = null;   // UUID bất biến — lưu trong chrome.storage.local

// ─── State Worker ────────────────────────────────────────────
export let workerEnabled = true;
export let wsState       = 'disconnected';

// ─── Thống kê và Log ─────────────────────────────────────────
export const stats       = { done: 0, failed: 0, running: 0 };
export const MAX_LOGS    = 60;
export const activityLogs = [];

// ─── Setters (vì ES module exports là live bindings, cần setter) ──
export function setWs(value)            { ws = value; }
export function setWorkerId(value)      { workerId = value; }
export function setWorkerEnabled(value) { workerEnabled = value; }
export function setWsState(value)       { wsState = value; }
export function setReconnectTimer(v)    { reconnectTimer = v; }
export function setHeartbeatTimer(v)    { heartbeatTimer = v; }
