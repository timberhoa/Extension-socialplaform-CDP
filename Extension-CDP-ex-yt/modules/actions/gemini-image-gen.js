// ============================================================
//  gemini-image-gen.js — Action: get_gemini_auth
//
//  1. Mở/Tìm tab gemini.google.com
//  2. Đọc cookies của `.google.com`
//  3. Lấy biến window.WIZ_global_data.SNlM0e từ DOM
//  4. Trả về cho Server 3001
// ============================================================

import { pushLog } from '../utils.js';

async function handleGetGeminiAuth(_tabId, step) {
  pushLog(`🔐 [Gemini] Bắt đầu trích xuất Auth Token...`, 'info');

  // Mở tab
  const tab = await new Promise((res, rej) =>
    chrome.tabs.create({ url: 'https://gemini.google.com/app', active: false }, (t) =>
      chrome.runtime.lastError ? rej(new Error(chrome.runtime.lastError.message)) : res(t)
    )
  );

  // Đợi tab load xong
  await new Promise((resolve) => {
    const listener = (tabId, info) => {
      if (tabId === tab.id && info.status === 'complete') {
        chrome.tabs.onUpdated.removeListener(listener);
        resolve();
      }
    };
    chrome.tabs.onUpdated.addListener(listener);
    setTimeout(() => {
      chrome.tabs.onUpdated.removeListener(listener);
      resolve();
    }, 15000); // timeout 15s
  });

  // Đợi thêm tí cho script khởi tạo
  await new Promise((r) => setTimeout(r, 1000));

  let authData = { cookies: '', snlm0e: '', bl: '' };

  try {
    // 1. Lấy SNlM0e
    const scriptResult = await new Promise((res, rej) => {
      chrome.scripting.executeScript(
        {
          target: { tabId: tab.id },
          world: 'MAIN',
          func: async () => {
            return new Promise((r) => {
              let attempts = 0;
              const check = () => {
                if (window.WIZ_global_data && window.WIZ_global_data.SNlM0e) {
                  r({ 
                    ok: true, 
                    snlm0e: window.WIZ_global_data.SNlM0e,
                    bl: window.WIZ_global_data.cfb2h || ""
                  });
                } else {
                  attempts++;
                  // Đợi tối đa 50*200ms = 10 giây
                  if (attempts > 50) r({ error: 'NO_WIZ_GLOBAL_DATA' });
                  else setTimeout(check, 200);
                }
              };
              check();
            });
          }
        },
        (results) => {
          if (chrome.runtime.lastError) rej(new Error(chrome.runtime.lastError.message));
          else res(results && results[0] ? results[0].result : { error: 'NO_RESULT' });
        }
      );
    });

    if (scriptResult && scriptResult.ok) {
      authData.snlm0e = scriptResult.snlm0e;
      authData.bl = scriptResult.bl;
    } else {
      pushLog(`⚠️ [Gemini] Lỗi trích xuất SNlM0e/bl: ${scriptResult?.error}`, 'warning');
    }

    // 2. Lấy cookies
    const cookies = await new Promise((res) => {
      chrome.cookies.getAll({ url: 'https://gemini.google.com' }, (cks) => res(cks || []));
    });

    if (cookies.length === 0) {
      throw new Error('[get_gemini_auth] Không tìm thấy cookies của .google.com. Vui lòng đăng nhập Google.');
    }

    authData.cookies = cookies.map(c => `${c.name}=${c.value}`).join('; ');

  } finally {
    // Luôn đóng tab
    await new Promise((r) => chrome.tabs.remove(tab.id, r));
  }

  if (!authData.cookies) {
    throw new Error('[get_gemini_auth] Lỗi không trích xuất được cookie');
  }

  pushLog(`✅ [Gemini] Đã lấy được auth info (cookies length: ${authData.cookies.length}, có SNlM0e: ${!!authData.snlm0e})`, 'success');

  return {
    type: 'gemini_auth_result',
    cookies: authData.cookies,
    snlm0e: authData.snlm0e,
    bl: authData.bl,
    prompt: step.prompt,
    status: 'success'
  };
}

export const geminiImageActions = {
  get_gemini_auth: handleGetGeminiAuth,
};
