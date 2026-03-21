// ============================================================
//  actions/basic.js — 5 Action Cơ Bản
//  goto | wait_for_selector | type_text | click | evaluate_script
// ============================================================

import { cdpSend, pageEval, waitForSelector, waitForNetworkIdle, simulateType } from '../cdp-helpers.js';
import { delay } from '../utils.js';

export const basicActions = {

  async goto(tabId, step) {
    if (!step.url) throw new Error('"goto" requires a "url" field');
    console.log(`[STEP:goto] Navigating to ${step.url}`);

    const loadedPromise = new Promise((resolve) => {
      const timer = setTimeout(() => {
        chrome.debugger.onEvent.removeListener(onLoad);
        resolve();
      }, 20000);

      function onLoad(debuggeeId, method) {
        if (debuggeeId.tabId === tabId && method === 'Page.loadEventFired') {
          clearTimeout(timer);
          chrome.debugger.onEvent.removeListener(onLoad);
          resolve();
        }
      }
      chrome.debugger.onEvent.addListener(onLoad);
    });

    await cdpSend(tabId, 'Page.navigate', { url: step.url });
    await loadedPromise;
    console.log('[STEP:goto] Page.loadEventFired received');
    await waitForNetworkIdle(tabId, 1000, 10000);
    console.log('[STEP:goto] Network idle — page fully ready');
  },

  async wait_for_selector(tabId, step) {
    const { selector, timeout = 10000 } = step;
    if (!selector) throw new Error('"wait_for_selector" requires a "selector" field');
    await waitForSelector(tabId, selector, timeout);
  },

  async type_text(tabId, step) {
    const { selector, text, delayMs = 50 } = step;
    if (!selector || text === undefined)
      throw new Error('"type_text" requires "selector" and "text"');

    // 1. Focus vào element
    await pageEval(tabId, `document.querySelector(${JSON.stringify(selector)})?.focus()`);
    await delay(100);

    // 2. Clear textbox nếu cần (tùy chọn update sau) 
    await pageEval(tabId, `
      (function() {
        const el = document.querySelector(${JSON.stringify(selector)});
        if (el) el.value = "";
      })()
    `);
    await delay(50);

    // 3. Sử dụng Native CDP để gõ từng phím giống người thật
    await simulateType(tabId, text, delayMs);
    await delay(300);
  },

  async click(tabId, step) {
    const { selector } = step;
    if (!selector) throw new Error('"click" requires a "selector" field');

    await pageEval(tabId, `
      (function() {
        const el = document.querySelector(${JSON.stringify(selector)});
        if (!el) throw new Error('Element not found: ' + ${JSON.stringify(selector)});
        el.focus();
        el.click();
      })()
    `);
    await delay(500);
  },

  async evaluate_script(tabId, step) {
    const { script } = step;
    if (!script) throw new Error('"evaluate_script" requires a "script" field');
    const wrapped = `(function(){ return (${script}); })()`;
    const value = await pageEval(tabId, wrapped);
    console.log('[STEP] evaluate_script result:', value);
    return value;
  },
};
