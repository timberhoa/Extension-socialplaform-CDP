"""
config.py — Cấu hình toàn cục
Chỉnh sửa ở đây khi cần thay đổi port giao tiếp, thư mục tĩnh, và các mốc thời gian heartbeat (timeout).
"""

# Heartbeat
HEARTBEAT_TIMEOUT = 30          # Giây — nếu > 30s không ping → HUNG
HEARTBEAT_CHECK_INTERVAL = 5    # Giây — tần suất server kiểm tra

# Server
SERVER_HOST = "0.0.0.0"
SERVER_PORT = 3001
STATIC_DIR = "static"
