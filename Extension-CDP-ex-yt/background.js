// ============================================================
//  background.js — Entry Point (ES Module Service Worker)
//  Tất cả logic đã được tách vào ./modules/
// ============================================================

import { getOrCreateWorkerId } from './modules/identity.js';
import { connect }             from './modules/websocket.js';
import './modules/message-handler.js';   // đăng ký chrome.runtime.onMessage

// ─── Boot ────────────────────────────────────────────────────
(async function bootstrap() {
  await getOrCreateWorkerId();
  connect();
  console.log('[BOOT] CDP RPA Worker started (modular mode)');
})();

// ─── Keep-alive: phòng Service Worker bị suspend ─────────────
// Strategy: setInterval ngắn (20 s) để giữ SW sống trong khi có task
setInterval(() => {
  chrome.runtime.getPlatformInfo(() => { /* noop */ });
}, 20_000);
