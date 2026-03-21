"""
gemini_config.py — Cấu hình động Gemini Image Generation

Lưu trữ các giá trị hard-coded (endpoint, build label, model code, payload) 
được chuyển sang JSON để Control Panel có quyền chỉnh sửa.
"""

import os
import json

CONFIG_FILE = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "gemini_settings.json")

# Đây là cấu hình mặc định (đang hoạt động hiện tại) 
# Hệ thống sẽ TỰ ĐỘNG điền nếu file chưa tồn tại (chọn cách không để trống theo yêu cầu).
DEFAULT_CONFIG = {
    "endpoint": "https://gemini.google.com/_/BardChatUi/data/assistant.lamda.BardFrontendService/StreamGenerate",
    "bl": "boq_assistant-bard-web-server_20260313.06_p1",
    "model_code": "gemini-2.0-flash-exp",
    "f_sid": "",
    "cookies": {
        "__Secure-1PSID": "",
        "__Secure-1PSIDTS": ""
    },
    "timeout": 120,
    "model_header": {
        "x-goog-ext-73010989-jspb": "[0]",
        "x-goog-ext-525001261-jspb": '[1,null,null,null,"",null,null,0,[4],null,null,2]',
        "x-goog-ext-525005358-jspb": '["{request_uuid}",1]',
        "x-goog-ext-73010990-jspb": "[0]"
    },
    "image_gen_fields": {
        "1": ["vi"],
        "6": [1],
        "10": 1,
        "11": 0,
        "17": [[0]],
        "18": 0,
        "27": 1,
        "30": [4],
        "41": [1],
        "49": 14,
        "53": 0,
        "59": "{request_uuid}",
        "61": [],
        "68": 2
    }
}

import copy

def load_gemini_config() -> dict:
    os.makedirs(os.path.dirname(CONFIG_FILE), exist_ok=True)
    if not os.path.exists(CONFIG_FILE):
        return copy.deepcopy(DEFAULT_CONFIG)
    try:
        with open(CONFIG_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
            # Merge with default config to ensure all keys exist
            config = copy.deepcopy(DEFAULT_CONFIG)
            for k, v in data.items():
                if k in ["model_header", "image_gen_fields", "cookies"] and isinstance(v, dict):
                    config[k].update(v)  # type: ignore
                elif isinstance(k, str):
                    config[k] = v  # type: ignore
            return config
    except Exception as e:
        print(f"Error loading gemini_settings.json: {e}")
        return copy.deepcopy(DEFAULT_CONFIG)

def save_gemini_config(new_config: dict) -> bool:
    os.makedirs(os.path.dirname(CONFIG_FILE), exist_ok=True)
    try:
        with open(CONFIG_FILE, "w", encoding="utf-8") as f:
            json.dump(new_config, f, ensure_ascii=False, indent=4)
        return True
    except Exception as e:
        print(f"Error saving gemini_settings.json: {e}")
        return False

def get_gemini_api_config() -> dict:
    """Trả về dict config một số trường cũ tương thích nếu cần thiết."""
    cfg = load_gemini_config()
    return {
        "endpoint":   cfg.get("endpoint"),
        "bl":         cfg.get("bl"),
        "model_code": cfg.get("model_code"),
        "f_sid":      cfg.get("f_sid") or None,
    }
