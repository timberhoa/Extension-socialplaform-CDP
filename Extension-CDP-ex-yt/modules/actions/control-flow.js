// ============================================================
//  actions/control-flow.js — Kiểm Soát Luồng
//  if_exists_then | loop_elements
// ============================================================

import { pageEval, waitForSelector } from '../cdp-helpers.js';

// runStep sẽ được inject khi step-runner khởi tạo (tránh circular import)
let _runStep = null;
export function setRunStep(fn) { _runStep = fn; }

export const controlFlowActions = {

  async if_exists_then(tabId, step, results) {
    const { selector, then_steps = [], else_steps = [] } = step;
    if (!selector) throw new Error('"if_exists_then" requires a "selector" field');

    const exists = await pageEval(tabId, `!!document.querySelector(${JSON.stringify(selector)})`);
    console.log(`[STEP:if_exists_then] "${selector}" exists = ${exists}`);

    const branch     = exists ? then_steps : else_steps;
    const branchName = exists ? 'then'     : 'else';

    if (branch.length === 0) {
      console.log(`[STEP:if_exists_then] No "${branchName}" steps — skipping`);
      return;
    }

    console.log(`[STEP:if_exists_then] Running "${branchName}" branch (${branch.length} steps)`);
    for (let bi = 0; bi < branch.length; bi++) {
      const branchResult = await _runStep(tabId, branch[bi]);
      if (branchResult !== null && branchResult !== undefined) {
        results.push({ branch: branchName, step: bi, action: branch[bi].action, data: branchResult });
      }
    }
  },

  async loop_elements(tabId, step, results) {
    const { selector, sub_steps = [], max_items } = step;
    if (!selector)           throw new Error('"loop_elements" requires a "selector" field');
    if (!sub_steps.length)   throw new Error('"loop_elements" requires "sub_steps" array');

    const elements = await pageEval(tabId, `
      Array.from(document.querySelectorAll(${JSON.stringify(selector)})).map((el, i) => ({
        index: i,
        text:  el.innerText?.trim() || '',
        href:  el.href || '',
        value: el.value || '',
        tag:   el.tagName.toLowerCase()
      }))
    `);

    if (!elements || elements.length === 0) {
      console.warn(`[STEP:loop_elements] No elements found for "${selector}"`);
      return;
    }

    const limit = max_items ? Math.min(elements.length, max_items) : elements.length;
    console.log(`[STEP:loop_elements] Found ${elements.length} elements, processing ${limit}`);

    const interpolate = (obj, el) => {
      const str = JSON.stringify(obj)
        .replace(/\{\{index\}\}/g, el.index)
        .replace(/\{\{text\}\}/g,  el.text.replace(/"/g, '\\"'))
        .replace(/\{\{href\}\}/g,  el.href.replace(/"/g, '\\"'))
        .replace(/\{\{value\}\}/g, el.value.replace(/"/g, '\\"'));
      return JSON.parse(str);
    };

    for (let ei = 0; ei < limit; ei++) {
      const el = elements[ei];
      console.log(`[STEP:loop_elements] Item ${ei + 1}/${limit}: "${el.text.substring(0, 40)}"`);

      for (let si = 0; si < sub_steps.length; si++) {
        const subStep = interpolate(sub_steps[si], el);
        try {
          const subResult = await _runStep(tabId, subStep);
          if (subResult !== null && subResult !== undefined) {
            results.push({ loop_index: ei, step: si, action: subStep.action, data: subResult });
          }
        } catch (subErr) {
          console.warn(`[STEP:loop_elements] Item ${ei}, step ${si} failed: ${subErr.message}`);
          results.push({ loop_index: ei, step: si, action: subStep.action, error: subErr.message });
        }
      }
    }
  },
};
