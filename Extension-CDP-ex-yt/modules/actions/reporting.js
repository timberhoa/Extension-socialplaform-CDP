// ============================================================
//  actions/reporting.js — Báo Cáo & Gỡ Lỗi
//  take_screenshot | log_message | assert_text | save_to_results
// ============================================================

import { cdpSend, pageEval, waitForSelector } from '../cdp-helpers.js';
import { pushLog } from '../utils.js';

export const reportingActions = {

  async take_screenshot(tabId, step) {
    const { label = 'screenshot' } = step;
    const { data } = await cdpSend(tabId, 'Page.captureScreenshot', {
      format: 'png',
      quality: 80,
      captureBeyondViewport: false,
    });

    const timestamp = new Date().toISOString().replace(/[:.]/g, '-');
    const filename  = `${label}_${timestamp}.png`;
    const dataUrl   = `data:image/png;base64,${data}`;

    // Lưu vào chrome.storage.local — popup sẽ đọc để hiển thị
    await new Promise(resolve => {
      chrome.storage.local.get(['screenshots'], (res) => {
        const list = res.screenshots || [];
        list.unshift({ filename, dataUrl, ts: Date.now() });
        if (list.length > 20) list.length = 20;   // giữ tối đa 20 ảnh
        chrome.storage.local.set({ screenshots: list }, resolve);
      });
    });

    const sizeKB = Math.round(data.length * 0.75 / 1024);
    pushLog(`📷 Screenshot: ${filename} (${sizeKB} KB)`, 'info');
    console.log(`[STEP:take_screenshot] Saved "${filename}" (${sizeKB} KB)`);
    return { filename, size_kb: sizeKB };
  },

  async log_message(_tabId, step) {
    const { message = '', level = 'info' } = step;
    if (!message) throw new Error('"log_message" requires a "message" field');

    const timestamp = new Date().toISOString();
    const emoji     = level === 'warn' ? '⚠️' : level === 'error' ? '❌' : 'ℹ️';

    // Ghi vào activity log → hiển thị trong popup
    pushLog(`${emoji} ${message}`, level === 'warn' ? 'warn' : level === 'error' ? 'error' : 'info');
    console.log(`[STEP:log_message] [${level.toUpperCase()}] ${message}`);

    // Lưu riêng debug log list để popup tab Debug có thể hiển thị đầy đủ
    await new Promise(resolve => {
      chrome.storage.local.get(['debugLogs'], (res) => {
        const list = res.debugLogs || [];
        list.unshift({ timestamp, level, message });
        if (list.length > 200) list.length = 200;
        chrome.storage.local.set({ debugLogs: list }, resolve);
      });
    });

    return { timestamp, level, message };
  },

  async assert_text(tabId, step) {
    const { selector, expected, contains = true, case_sensitive = false } = step;
    if (!selector)             throw new Error('"assert_text" requires "selector"');
    if (expected === undefined) throw new Error('"assert_text" requires "expected"');

    await waitForSelector(tabId, selector, step.timeout || 5000);
    const actual = await pageEval(
      tabId,
      `document.querySelector(${JSON.stringify(selector)})?.innerText?.trim() || ''`
    );

    const a = case_sensitive ? actual    : (actual    || '').toLowerCase();
    const e = case_sensitive ? expected  : (expected  || '').toLowerCase();

    const passed = contains ? a.includes(e) : a === e;
    const mode   = contains ? 'contains'    : 'equals';

    if (!passed) {
      const msg = `[assert_text] FAILED — "${selector}" ${mode} "${expected}" but got: "${actual}"`;
      pushLog(`❌ Assert FAILED: ${selector}`, 'error');
      throw new Error(msg);
    }

    pushLog(`✅ Assert PASSED: ${selector} ${mode} "${expected}"`, 'success');
    console.log(`[STEP:assert_text] ✅ PASSED — "${selector}" ${mode} "${expected}"`);
    return { selector, expected, actual, mode, passed: true };
  },

  async save_to_results(tabId, step) {
    const { key, script } = step;
    if (!key)    throw new Error('"save_to_results" requires "key"');
    if (!script) throw new Error('"save_to_results" requires "script"');

    const value = await pageEval(tabId, script);
    const entry = { key, value, timestamp: new Date().toISOString() };
    pushLog(`💾 Saved: ${key} = ${JSON.stringify(value).substring(0, 40)}`, 'info');
    console.log(`[STEP:save_to_results] "${key}" = ${JSON.stringify(value)}`);
    return entry;
  },
};
