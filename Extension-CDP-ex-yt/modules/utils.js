// ============================================================
//  utils.js — Tiện ích dùng chung toàn hệ thống
// ============================================================

import { activityLogs, MAX_LOGS } from './config.js';

/**
 * Chờ ms milliseconds.
 * @param {number} ms
 */
export function delay(ms) {
  return new Promise((resolve) => setTimeout(resolve, ms));
}

/**
 * Ghi log vào activityLogs (hiển thị trên popup) và console.
 * @param {string} text
 * @param {'info'|'success'|'warn'|'error'} type
 */
export function pushLog(text, type = 'info') {
  const now = new Date().toLocaleTimeString('en-GB', { hour12: false });
  activityLogs.push({ text, type });
  if (activityLogs.length > MAX_LOGS) activityLogs.shift();
  console.log(`[LOG:${type.toUpperCase()}] ${now} ${text}`);
}
