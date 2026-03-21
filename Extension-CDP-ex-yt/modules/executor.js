// ============================================================
//  executor.js — Chạy toàn bộ Task
// ============================================================

import { cdpSend }         from './cdp-helpers.js';
import { runStep }         from './step-runner.js';
import { sendStateUpdate } from './websocket.js';
import { pushLog }         from './utils.js';
import * as cfg            from './config.js';

/**
 * Thực thi một task đầy đủ:
 * 1. Mở tab mới
 * 2. Gắn CDP debugger
 * 3. Bật các CDP domains cần thiết
 * 4. Chạy từng step tuần tự
 * 5. Gửi kết quả về server
 * 6. Dọn dẹp (detach, đóng tab)
 *
 * @param {{ task_id: string, steps: object[] }} task
 */
export async function executeTask(task) {
  const { task_id, steps } = task;
  let tab = null;
  const results = [];
  cfg.stats.running++;

  pushLog(`Starting task: ${task_id}`, 'info');
  sendStateUpdate('BUSY', task_id);

  try {
    // 1. Mở tab mới (ẩn background)
    tab = await new Promise((res, rej) =>
      chrome.tabs.create({ url: 'about:blank', active: false }, (t) =>
        chrome.runtime.lastError ? rej(new Error(chrome.runtime.lastError.message)) : res(t)
      )
    );
    console.log(`[TASK:${task_id}] Opened tab #${tab.id}`);

    // 2. Attach CDP debugger
    await new Promise((res, rej) =>
      chrome.debugger.attach({ tabId: tab.id }, '1.3', () =>
        chrome.runtime.lastError ? rej(new Error(chrome.runtime.lastError.message)) : res()
      )
    );
    console.log(`[TASK:${task_id}] Debugger attached`);

    // 3. Enable CDP domains
    await cdpSend(tab.id, 'Page.enable');
    await cdpSend(tab.id, 'Runtime.enable');
    await cdpSend(tab.id, 'Network.enable');

    // 4. Chạy từng step
    for (let i = 0; i < steps.length; i++) {
      const step = steps[i];
      console.log(`[TASK:${task_id}] Step ${i + 1}/${steps.length}: ${step.action}`);
      try {
        const stepResult = await runStep(tab.id, step, results);
        if (stepResult !== null && stepResult !== undefined) {
          results.push({ step: i, action: step.action, data: stepResult });
        }
      } catch (stepErr) {
        console.error(`[TASK:${task_id}] Step ${i + 1} FAILED:`, stepErr.message);
        results.push({ step: i, action: step.action, error: stepErr.message });
        // Dừng task nếu goto thất bại (không thể tiếp tục không có trang)
        if (step.action === 'goto') break;
      }
    }

    const hasError = results.some(r => r.error);
    const finalStatus = hasError ? 'failed' : 'completed';
    const firstError = hasError ? results.find(r => r.error).error : null;

    // 5. Gửi kết quả về server
    const payload = JSON.stringify({
      type: 'task_result',
      task_id,
      worker_id: cfg.workerId,
      status: finalStatus,
      error: firstError,
      results,
    });

    if (cfg.ws && cfg.ws.readyState === WebSocket.OPEN) {
      cfg.ws.send(payload);
      console.log(`[TASK:${task_id}] Results sent to server (Status: ${finalStatus})`);
      if (hasError) {
        cfg.stats.failed++;
        pushLog(`Task finished with errors: ${task_id}`, 'error');
      } else {
        cfg.stats.done++;
        pushLog(`Task done: ${task_id}`, 'success');
      }
    } else {
      console.error(`[TASK:${task_id}] WebSocket not open — results lost!`);
      pushLog(`Task ${task_id}: WS closed, results lost`, 'error');
    }

    sendStateUpdate('IDLE');

  } catch (err) {
    console.error(`[TASK:${task_id}] Fatal error:`, err.message);
    cfg.stats.failed++;
    pushLog(`Task failed: ${task_id} — ${err.message}`, 'error');

    const errorPayload = JSON.stringify({
      type: 'task_result',
      task_id,
      worker_id: cfg.workerId,
      status: 'failed',
      error: err.message,
      results,
    });
    if (cfg.ws && cfg.ws.readyState === WebSocket.OPEN) cfg.ws.send(errorPayload);
    sendStateUpdate('ERROR', task_id);

  } finally {
    cfg.stats.running = Math.max(0, cfg.stats.running - 1);

    // 6. Dọn dẹp
    if (tab) {
      // Sử dụng CDP để đóng tab thay vì chrome.tabs.remove
      try {
        await cdpSend(tab.id, 'Page.close');
        console.log(`[TASK:${task_id}] Tab #${tab.id} closed via CDP Page.close`);
      } catch (err) {
        console.warn('[CLEANUP] CDP close warning (có thể do tab đã đóng):', err.message);
      }

      await new Promise((res) =>
        chrome.debugger.detach({ tabId: tab.id }, () => {
          // Bỏ qua lỗi detach nếu tab đã bị đóng bởi CDP ở trên
          res();
        })
      ).catch(() => {});
    }
  }
}
