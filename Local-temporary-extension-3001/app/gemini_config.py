"""
gemini_config.py — Cấu Hình Payload Gemini Image Generation

Lưu trữ các giá trị hard-coded (endpoint, build label, model code) cần thiết cho Gemini API Request.
Cách cập nhật tham khảo ở thư mục `reverse_api_web/` khi payload bị thay đổi từ phía Google.
"""

# ──────────────────────────────────────────────────────────────
#  ENDPOINT — URL gốc của StreamGenerate (không bao gồm query params)
#  Ví dụ sau khi reverse:
#    https://gemini.google.com/_/BardChatUi/data/batchexecute
#  hoặc:
#    https://gemini.google.com/u/0/_/BardChatUi/data/batchexecute
# ──────────────────────────────────────────────────────────────
GEMINI_ENDPOINT = "https://gemini.google.com/_/BardChatUi/data/assistant.lamda.BardFrontendService/StreamGenerate"

# ──────────────────────────────────────────────────────────────
#  BL (Build Label) — thay đổi mỗi vài ngày
#  Capture ngày 2026-03-18: "boq_assistant-bard-web-server_20260313.06_p1"
#  Extension sẽ tự extract từ page nếu được, config này là fallback.
# ──────────────────────────────────────────────────────────────
GEMINI_BL = "boq_assistant-bard-web-server_20260313.06_p1"

# ──────────────────────────────────────────────────────────────
#  MODEL CODE — mã model dùng để generate ảnh
#  Ví dụ: "gemini-2.0-flash-exp", "gemini-2.0-pro-exp"
# ──────────────────────────────────────────────────────────────
GEMINI_MODEL_CODE = "gemini-2.0-flash-exp"

# ──────────────────────────────────────────────────────────────
#  F_SID — Session ID (thường lấy từ cookie __Secure-1PSIDTS)
#  Để trống để extension tự sinh ngẫu nhiên
# ──────────────────────────────────────────────────────────────
GEMINI_F_SID = ""

# ──────────────────────────────────────────────────────────────
#  Timeout cho request tạo ảnh (giây)
# ──────────────────────────────────────────────────────────────
GEMINI_REQUEST_TIMEOUT = 90


def get_gemini_api_config() -> dict:
    """Trả về dict config đủ để dispatch task cho Extension Worker."""
    return {
        "endpoint":   GEMINI_ENDPOINT,
        "bl":         GEMINI_BL,
        "model_code": GEMINI_MODEL_CODE,
        "f_sid":      GEMINI_F_SID or None,
    }
