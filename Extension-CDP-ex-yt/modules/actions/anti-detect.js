// ============================================================
//  actions/anti-detect.js — Chống Phát Hiện Bot
//  simulate_human_mouse | random_delay | solve_captcha
// ============================================================

import { cdpSend, pageEval, simulateMouseMove } from '../cdp-helpers.js';
import { delay } from '../utils.js';

export const antiDetectActions = {

  async simulate_human_mouse(tabId, step) {
    const { selector } = step;
    if (!selector) throw new Error('"simulate_human_mouse" requires a "selector" field');
    console.log(`[STEP:simulate_human_mouse] Moving to ${selector}`);

    const boxResult = await cdpSend(tabId, 'Runtime.evaluate', {
      expression: `(function(){
        const el = document.querySelector(${JSON.stringify(selector)});
        if (!el) return null;
        const r = el.getBoundingClientRect();
        return { x: Math.round(r.left + r.width/2), y: Math.round(r.top + r.height/2) };
      })()`,
      returnByValue: true,
    });

    const pos = boxResult?.result?.value;
    if (!pos) throw new Error(`Element not found or not visible: ${selector}`);

    const x0 = Math.round(50 + Math.random() * 200);
    const y0 = Math.round(50 + Math.random() * 150);
    console.log(`[STEP:simulate_human_mouse] Bezier ${x0},${y0} → ${pos.x},${pos.y}`);
    await simulateMouseMove(tabId, x0, y0, pos.x, pos.y);

    await delay(80 + Math.round(Math.random() * 120));
    await cdpSend(tabId, 'Input.dispatchMouseEvent', { type: 'mousePressed', x: pos.x, y: pos.y, button: 'left', clickCount: 1 });
    await delay(60 + Math.round(Math.random() * 80));
    await cdpSend(tabId, 'Input.dispatchMouseEvent', { type: 'mouseReleased', x: pos.x, y: pos.y, button: 'left', clickCount: 1 });
    await delay(300);
  },

  async random_delay(tabId, step) {
    const { min = 500, max = 2000 } = step;
    const waitMs = Math.round(min + Math.random() * (max - min));
    console.log(`[STEP:random_delay] Sleeping ${waitMs}ms (${min}–${max}ms range)`);
    await delay(waitMs);
  },

  async solve_captcha(tabId, step) {
    const { api_key, site_key, page_url, timeout_ms = 120000 } = step;
    if (!api_key || !site_key || !page_url)
      throw new Error('"solve_captcha" requires "api_key", "site_key", "page_url"');

    console.log('[STEP:solve_captcha] Submitting captcha job to 2Captcha...');

    // 1. Submit job
    const submitResp = await fetch(
      `http://2captcha.com/in.php?key=${api_key}&method=userrecaptcha&googlekey=${site_key}&pageurl=${encodeURIComponent(page_url)}&json=1`
    );
    const submitData = await submitResp.json();
    if (submitData.status !== 1) throw new Error(`2Captcha submit failed: ${submitData.request}`);

    const captchaId = submitData.request;
    console.log(`[STEP:solve_captcha] Job ID: ${captchaId}. Waiting...`);

    // 2. Poll mỗi 5 giây
    const deadline = Date.now() + timeout_ms;
    let token = null;
    while (Date.now() < deadline) {
      await delay(5000);
      const pollResp = await fetch(`http://2captcha.com/res.php?key=${api_key}&action=get&id=${captchaId}&json=1`);
      const pollData = await pollResp.json();
      if (pollData.status === 1) {
        token = pollData.request;
        console.log(`[STEP:solve_captcha] ✓ Token received (${token.substring(0, 30)}...)`);
        break;
      }
      console.log(`[STEP:solve_captcha] Still waiting... (${pollData.request})`);
    }

    if (!token) throw new Error('2Captcha timed out — no token received');

    // 3. Bơm token vào trang
    await pageEval(tabId, `
      (function() {
        const el = document.getElementById('g-recaptcha-response');
        if (el) {
          el.style.display = 'block';
          el.value = ${JSON.stringify(token)};
          el.dispatchEvent(new Event('change', { bubbles: true }));
        }
        if (window.___grecaptcha_cfg) {
          const clients = window.___grecaptcha_cfg.clients || {};
          for (const k in clients) {
            for (const j in clients[k]) {
              const cb = clients[k][j]?.callback;
              if (typeof cb === 'function') { try { cb(${JSON.stringify(token)}); } catch(e){} }
            }
          }
        }
      })()
    `);
    console.log('[STEP:solve_captcha] Token injected into page ✓');
    await delay(500);
    return token;
  },
};
