// ============================================================
//  cdp-helpers.js — Lớp trừu tượng cho Chrome DevTools Protocol
// ============================================================

import { delay } from './utils.js';

/**
 * Gửi lệnh CDP đến tab chỉ định.
 * @param {number} tabId
 * @param {string} method  VD: 'Runtime.evaluate', 'Page.navigate'
 * @param {object} params
 * @returns {Promise<any>}
 */
export function cdpSend(tabId, method, params = {}) {
  return new Promise((resolve, reject) => {
    chrome.debugger.sendCommand({ tabId }, method, params, (result) => {
      if (chrome.runtime.lastError) {
        reject(new Error(`[CDP] ${method} failed: ${chrome.runtime.lastError.message}`));
      } else {
        resolve(result);
      }
    });
  });
}

/**
 * Chạy JavaScript trong trang và trả về giá trị.
 * @param {number} tabId
 * @param {string} expression  JS expression (không phải statement)
 * @returns {Promise<any>}
 */
export async function pageEval(tabId, expression) {
  const result = await cdpSend(tabId, 'Runtime.evaluate', {
    expression,
    returnByValue: true,
    awaitPromise:  false,
  });

  if (result.exceptionDetails) {
    const msg =
      result.exceptionDetails.exception?.description ||
      JSON.stringify(result.exceptionDetails);
    throw new Error(`[pageEval] Script threw: ${msg}`);
  }
  return result.result?.value;
}

/**
 * Chờ selector xuất hiện trong DOM.
 * @param {number} tabId
 * @param {string} selector   CSS selector
 * @param {number} timeout    ms tối đa (mặc định 10000)
 */
export async function waitForSelector(tabId, selector, timeout = 10000) {
  const interval    = 300;
  const maxAttempts = Math.ceil(timeout / interval);

  for (let i = 0; i < maxAttempts; i++) {
    const exists = await pageEval(
      tabId,
      `!!document.querySelector(${JSON.stringify(selector)})`
    );
    if (exists) return;
    await delay(interval);
  }
  throw new Error(`Selector not found within ${timeout}ms: "${selector}"`);
}

/**
 * Chờ mạng idle (không còn request đang chờ).
 * @param {number} tabId
 * @param {number} quietMs    ms không có request mới thì coi là idle
 * @param {number} maxWaitMs  Hard timeout
 */
export function waitForNetworkIdle(tabId, quietMs = 1000, maxWaitMs = 15000) {
  return new Promise((resolve) => {
    let pendingCount = 0;
    let idleTimer    = null;
    let hardTimer    = null;

    function done() {
      clearTimeout(idleTimer);
      clearTimeout(hardTimer);
      chrome.debugger.onEvent.removeListener(handler);
      resolve();
    }

    function resetIdleTimer() {
      clearTimeout(idleTimer);
      idleTimer = setTimeout(done, quietMs);
    }

    function handler(debuggeeId, method) {
      if (debuggeeId.tabId !== tabId) return;
      if (method === 'Network.requestWillBeSent') {
        pendingCount++;
        clearTimeout(idleTimer);
        idleTimer = null;
      } else if (
        method === 'Network.loadingFinished' ||
        method === 'Network.loadingFailed'   ||
        method === 'Network.responseReceived'
      ) {
        pendingCount = Math.max(0, pendingCount - 1);
        if (pendingCount === 0) resetIdleTimer();
      }
    }

    chrome.debugger.onEvent.addListener(handler);
    resetIdleTimer();
    hardTimer = setTimeout(() => {
      console.warn(`[NetworkIdle] Hard timeout after ${maxWaitMs}ms. Continuing anyway.`);
      done();
    }, maxWaitMs);
  });
}

/**
 * Di chuyển chuột từ (x0,y0) đến (x1,y1) theo đường cong Bezier bậc 2.
 * Tạo chuyển động tự nhiên, chống phát hiện bot.
 * @param {number} steps  Số bước trung gian (mặc định 18)
 */
export async function simulateMouseMove(tabId, x0, y0, x1, y1, steps = 18) {
  const cx = x0 + (x1 - x0) * 0.5 + (Math.random() - 0.5) * 80;
  const cy = y0 + (y1 - y0) * 0.5 + (Math.random() - 0.5) * 80;

  for (let i = 0; i <= steps; i++) {
    const t = i / steps;
    // B(t) = (1-t)^2*P0 + 2(1-t)t*P1 + t^2*P2
    const x = Math.round((1 - t) ** 2 * x0 + 2 * (1 - t) * t * cx + t ** 2 * x1);
    const y = Math.round((1 - t) ** 2 * y0 + 2 * (1 - t) * t * cy + t ** 2 * y1);
    await cdpSend(tabId, 'Input.dispatchMouseEvent', { type: 'mouseMoved', x, y });
    await delay(10 + Math.round(Math.random() * 15));
  }
}

/**
 * Gõ từng ký tự thông qua CDP Input.dispatchKeyEvent để giả lập người thật.
 * @param {number} tabId
 * @param {string} text
 * @param {number} delayMs Thời gian nghỉ mặc định giữa mỗi phím (sẽ có +- random nội bộ)
 */
export async function simulateType(tabId, text, delayMs = 50) {
  for (const char of text) {
    // 1. Gửi keyDown
    await cdpSend(tabId, 'Input.dispatchKeyEvent', {
      type: 'keyDown',
      text: char,
      unmodifiedText: char,
      key: char
    });

    // Khoảng nghỉ siêu nhỏ giữa lúc cắm phím và nhả phím
    await delay(10 + Math.random() * 20);

    // 2. Gửi keyUp
    await cdpSend(tabId, 'Input.dispatchKeyEvent', {
      type: 'keyUp',
      key: char
    });

    // 3. Nghỉ ngẫu nhiên trước khi gõ phím tiếp theo
    const randomFactor = Math.random() * (delayMs * 0.5); // +- 50%
    const actualDelay = delayMs + (Math.random() > 0.5 ? randomFactor : -randomFactor);
    await delay(Math.max(10, actualDelay)); // Ít nhất là 10ms
  }
}
