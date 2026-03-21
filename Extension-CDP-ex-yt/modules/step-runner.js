// ============================================================
//  step-runner.js — Dispatcher: runStep()
//  Gộp tất cả ACTION_MAP từ các action module
// ============================================================

import { basicActions }       from './actions/basic.js';
import { keyboardActions }    from './actions/keyboard.js';
import { antiDetectActions }  from './actions/anti-detect.js';
import { advancedActions }    from './actions/advanced.js';
import { controlFlowActions, setRunStep } from './actions/control-flow.js';
import { reportingActions }   from './actions/reporting.js';
import { geminiImageActions } from './actions/gemini-image-gen.js';

// ─── Hợp nhất tất cả action vào một map ──────────────────────
const ACTION_MAP = {
  ...basicActions,
  ...keyboardActions,
  ...antiDetectActions,
  ...advancedActions,
  ...controlFlowActions,
  ...reportingActions,
  ...geminiImageActions,
};

/**
 * Chạy một step đơn lẻ.
 * Control-flow actions (if_exists_then, loop_elements) nhận thêm `results`
 * để có thể push kết quả sub-step vào mảng results của task.
 *
 * @param {number}   tabId
 * @param {object}   step   — { action, ...params }
 * @param {Array}    results — mảng results của task (dùng cho control flow)
 * @returns {Promise<any>}  — giá trị trả về (crawled data, screenshot info, …) hoặc null
 */
export async function runStep(tabId, step, results = []) {
  const { action } = step;
  console.log(`[STEP] → ${action}`, step);

  const handler = ACTION_MAP[action];
  if (!handler) {
    console.warn(`[STEP] Unknown action: "${action}" — skipping`);
    return null;
  }

  // Control-flow handlers cần truyền results để push sub-step data
  const isControlFlow = action === 'if_exists_then' || action === 'loop_elements';
  const result = isControlFlow
    ? await handler(tabId, step, results)
    : await handler(tabId, step);

  return result ?? null;
}

// Inject runStep vào control-flow module (tránh circular import)
setRunStep(runStep);
