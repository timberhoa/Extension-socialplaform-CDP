// ============================================================
//  actions/keyboard.js — Cuộn trang & Bàn phím
//  scroll | press_enter | keyboard_shortcut
// ============================================================

import { cdpSend, pageEval } from '../cdp-helpers.js';
import { delay } from '../utils.js';

export const keyboardActions = {

  async scroll(tabId, step) {
    const { direction, pixels = 500 } = step;
    console.log(`[STEP:scroll] Scrolling ${direction || 'down'} by ${pixels}px`);
    await pageEval(tabId, `
      (function() {
        if ('${direction}' === 'up') {
          window.scrollBy(0, -${pixels});
        } else if ('${direction}' === 'bottom') {
          window.scrollTo(0, document.body.scrollHeight);
        } else {
          window.scrollBy(0, ${pixels}); // default: down
        }
      })()
    `);
    await delay(500);
  },

  async press_enter(tabId, step) {
    const { selector } = step;
    if (!selector) throw new Error('"press_enter" requires a "selector" field');
    console.log(`[STEP:press_enter] Pressing Enter on ${selector}`);

    await pageEval(tabId, `
      (function() {
        const el = document.querySelector(${JSON.stringify(selector)});
        if (!el) throw new Error('Element not found: ' + ${JSON.stringify(selector)});
        el.focus();
        const opts = { key: 'Enter', code: 'Enter', keyCode: 13, which: 13, bubbles: true };
        el.dispatchEvent(new KeyboardEvent('keydown',  opts));
        el.dispatchEvent(new KeyboardEvent('keypress', opts));
        el.dispatchEvent(new KeyboardEvent('keyup',    opts));
      })()
    `);
    await delay(500);
  },

  async keyboard_shortcut(tabId, step) {
    const { key, ctrl = false, shift = false, alt = false, selector } = step;
    if (!key) throw new Error('"keyboard_shortcut" requires a "key" field');
    console.log(`[STEP:keyboard_shortcut] ${ctrl?'Ctrl+':''}${shift?'Shift+':''}${alt?'Alt+':''}${key}`);

    if (selector) {
      await pageEval(tabId, `document.querySelector(${JSON.stringify(selector)})?.focus()`);
      await delay(100);
    }

    const modifiers = (ctrl ? 2 : 0) | (alt ? 1 : 0) | (shift ? 8 : 0);
    const cdpKey    = { key, code: `Key${key.toUpperCase()}`, modifiers };
    await cdpSend(tabId, 'Input.dispatchKeyEvent', { type: 'keyDown', ...cdpKey });
    await delay(30);
    await cdpSend(tabId, 'Input.dispatchKeyEvent', { type: 'keyUp',   ...cdpKey });
    await delay(200);
  },
};
