"""
state.py — Bộ nhớ trung tâm (RAM) & Heartbeat
Lưu trữ trạng thái danh sách Worker đang kết nối dưới dạng Object Dictionary và thực thi theo dõi rớt mạng (Timeout).
"""

import asyncio
import time
from datetime import datetime

from .config import HEARTBEAT_TIMEOUT, HEARTBEAT_CHECK_INTERVAL

# ============================================================
# GLOBAL STATE
# Cấu trúc mỗi entry:
# { "ws", "state", "last_ping", "last_ping_iso", "connected_at", "task_running" }
# ============================================================
WORKERS: dict = {}


def register_worker(worker_id: str, websocket) -> bool:
    """Đăng ký worker mới hoặc cập nhật khi reconnect. Returns True nếu là worker mới."""
    now_iso = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    is_new = worker_id not in WORKERS

    if is_new:
        WORKERS[worker_id] = {
            "ws": websocket,
            "state": "IDLE",
            "last_ping": time.time(),
            "last_ping_iso": now_iso,
            "connected_at": now_iso,
            "task_running": None,
        }
    else:
        WORKERS[worker_id]["ws"] = websocket
        WORKERS[worker_id]["state"] = "IDLE"
        WORKERS[worker_id]["last_ping"] = time.time()
        WORKERS[worker_id]["last_ping_iso"] = now_iso

    return is_new


def update_ping(worker_id: str) -> bool:
    """Cập nhật heartbeat. Returns True nếu phục hồi từ HUNG."""
    was_hung = WORKERS[worker_id]["state"] == "HUNG"
    WORKERS[worker_id]["last_ping"] = time.time()
    WORKERS[worker_id]["last_ping_iso"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    if was_hung:
        WORKERS[worker_id]["state"] = "IDLE"
    return was_hung


def update_state(worker_id: str, new_state: str, task_id: str | None = None):
    """Cập nhật trạng thái worker."""
    WORKERS[worker_id]["state"] = new_state
    WORKERS[worker_id]["task_running"] = task_id


def set_offline(worker_id: str):
    """Đánh dấu worker là OFFLINE khi WebSocket đóng."""
    if worker_id in WORKERS:
        WORKERS[worker_id]["state"] = "OFFLINE"
        WORKERS[worker_id]["ws"] = None


def get_workers_list() -> list:
    """Trả về danh sách sạch (không kèm ws object) cho REST API."""
    return [
        {
            "worker_id": wid,
            "state": info["state"],
            "last_ping": info.get("last_ping_iso", "—"),
            "connected_at": info.get("connected_at", "—"),
            "task_running": info.get("task_running"),
        }
        for wid, info in WORKERS.items()
    ]


async def heartbeat_monitor():
    """Background task: kiểm tra mỗi 5s, set HUNG nếu > 30s không ping."""
    while True:
        await asyncio.sleep(HEARTBEAT_CHECK_INTERVAL)
        now = time.time()
        for wid, info in list(WORKERS.items()):
            if info.get("ws") is None:
                continue
            elapsed = now - info.get("last_ping", now)
            if elapsed > HEARTBEAT_TIMEOUT and info["state"] not in ("HUNG", "OFFLINE"):
                print(f"⏰ Worker [{wid[:8]}] không ping sau {elapsed:.0f}s → HUNG")
                WORKERS[wid]["state"] = "HUNG"
