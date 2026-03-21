// ============================================================
//  message-handler.js — Popup ↔ Background Communication
// ============================================================

import * as cfg            from './config.js';
import { pushLog }         from './utils.js';
import { connect }         from './websocket.js';
import { activityLogs }    from './config.js';

chrome.runtime.onMessage.addListener((msg, _sender, sendResponse) => {

  // Popup hỏi trạng thái worker
  if (msg.type === 'GET_STATE') {
    sendResponse({
      wsState:  cfg.wsState,
      wsUrl:    cfg.WS_URL,
      enabled:  cfg.workerEnabled,
      workerId: cfg.workerId,
      stats:    { ...cfg.stats },
      logs:     activityLogs.slice(-60),
    });
    return true;
  }

  // Popup bật/tắt worker
  if (msg.type === 'SET_ENABLED') {
    cfg.setWorkerEnabled(!!msg.enabled);
    pushLog(cfg.workerEnabled ? 'Worker enabled by user' : 'Worker paused by user', 'warn');
    if (cfg.workerEnabled && (!cfg.ws || cfg.ws.readyState !== WebSocket.OPEN)) {
      connect();
    }
    sendResponse({ ok: true, enabled: cfg.workerEnabled });
    return true;
  }

  // Popup xoá log
  if (msg.type === 'CLEAR_LOGS') {
    activityLogs.length = 0;
    sendResponse({ ok: true });
    return true;
  }
});
