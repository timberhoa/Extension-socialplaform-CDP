// ============================================================
//  identity.js — Quản lý Worker UUID
// ============================================================

import { setWorkerId } from './config.js';

/**
 * Lần đầu cài đặt: tự sinh UUID và lưu vào chrome.storage.local.
 * Các lần sau: đọc lại đúng UUID đã lưu → đảm bảo worker_id bất biến.
 * @returns {Promise<string>} worker UUID
 */
export function getOrCreateWorkerId() {
  return new Promise((resolve) => {
    chrome.storage.local.get(['worker_id'], (result) => {
      if (result.worker_id) {
        console.log('[ID] Loaded existing worker_id:', result.worker_id);
        setWorkerId(result.worker_id);
        resolve(result.worker_id);
      } else {
        const newId = crypto.randomUUID();
        chrome.storage.local.set({ worker_id: newId }, () => {
          console.log('[ID] Generated new worker_id:', newId);
          setWorkerId(newId);
          resolve(newId);
        });
      }
    });
  });
}
