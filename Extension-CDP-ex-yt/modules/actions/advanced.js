// ============================================================
//  actions/advanced.js — Tương Tác Nâng Cao
//  hover | drag_and_drop | upload_file
// ============================================================

import { cdpSend, pageEval, simulateMouseMove } from '../cdp-helpers.js';
import { delay } from '../utils.js';

export const advancedActions = {

  async hover(tabId, step) {
    const { selector } = step;
    if (!selector) throw new Error('"hover" requires a "selector" field');
    console.log(`[STEP:hover] Hovering over ${selector}`);

    const hoverPos = await cdpSend(tabId, 'Runtime.evaluate', {
      expression: `(function(){
        const el = document.querySelector(${JSON.stringify(selector)});
        if (!el) return null;
        const r = el.getBoundingClientRect();
        return { x: Math.round(r.left + r.width/2), y: Math.round(r.top + r.height/2) };
      })()`,
      returnByValue: true,
    });
    const pos = hoverPos?.result?.value;
    if (!pos) throw new Error(`Element not found: ${selector}`);

    const hx0 = Math.round(50 + Math.random() * 200);
    const hy0 = Math.round(50 + Math.random() * 150);
    await simulateMouseMove(tabId, hx0, hy0, pos.x, pos.y);

    await pageEval(tabId, `
      (function() {
        const el = document.querySelector(${JSON.stringify(selector)});
        if (!el) return;
        el.dispatchEvent(new MouseEvent('mouseover',  { bubbles: true, cancelable: true }));
        el.dispatchEvent(new MouseEvent('mouseenter', { bubbles: true }));
      })()
    `);
    await delay(600);
  },

  async drag_and_drop(tabId, step) {
    const { source_selector, target_selector } = step;
    if (!source_selector || !target_selector)
      throw new Error('"drag_and_drop" requires "source_selector" and "target_selector"');
    console.log(`[STEP:drag_and_drop] ${source_selector} => ${target_selector}`);

    const coords = await cdpSend(tabId, 'Runtime.evaluate', {
      expression: `(function(){
        const s = document.querySelector(${JSON.stringify(source_selector)});
        const t = document.querySelector(${JSON.stringify(target_selector)});
        if (!s || !t) return null;
        const sr = s.getBoundingClientRect();
        const tr = t.getBoundingClientRect();
        return {
          sx: Math.round(sr.left + sr.width/2),  sy: Math.round(sr.top  + sr.height/2),
          tx: Math.round(tr.left + tr.width/2),  ty: Math.round(tr.top  + tr.height/2)
        };
      })()`,
      returnByValue: true,
    });
    const c = coords?.result?.value;
    if (!c) throw new Error('Could not get coordinates for drag_and_drop');

    await cdpSend(tabId, 'Input.dispatchMouseEvent', { type: 'mousePressed', x: c.sx, y: c.sy, button: 'left', clickCount: 1 });
    await delay(80);

    for (let i = 1; i <= 20; i++) {
      const t  = i / 20;
      const mx = Math.round(c.sx + (c.tx - c.sx) * t + (Math.random() - 0.5) * 3);
      const my = Math.round(c.sy + (c.ty - c.sy) * t + (Math.random() - 0.5) * 3);
      await cdpSend(tabId, 'Input.dispatchMouseEvent', { type: 'mouseMoved', x: mx, y: my, button: 'left' });
      await delay(15 + Math.round(Math.random() * 10));
    }

    await delay(80);
    await cdpSend(tabId, 'Input.dispatchMouseEvent', { type: 'mouseReleased', x: c.tx, y: c.ty, button: 'left', clickCount: 1 });
    await delay(400);
  },

  async upload_file(tabId, step) {
    const { selector, file_path } = step;
    if (!selector || !file_path)
      throw new Error('"upload_file" requires "selector" and "file_path"');
    console.log(`[STEP:upload_file] ${file_path} => ${selector}`);

    const exists = await cdpSend(tabId, 'Runtime.evaluate', {
      expression: `document.querySelector(${JSON.stringify(selector)}) !== null`,
      returnByValue: true,
    });
    if (!exists?.result?.value) throw new Error(`File input not found: ${selector}`);

    await cdpSend(tabId, 'DOM.enable');
    const docNode  = await cdpSend(tabId, 'DOM.getDocument', { depth: 0 });
    const queryRes = await cdpSend(tabId, 'DOM.querySelector', {
      nodeId: docNode.root.nodeId,
      selector,
    });
    await cdpSend(tabId, 'DOM.setFileInputFiles', {
      nodeId: queryRes.nodeId,
      files:  [file_path],
    });
    await delay(500);
    console.log('[STEP:upload_file] File assigned successfully');
  },
};
