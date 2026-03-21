"""
main.py — Entry Point
Khởi động FastAPI server và kết nối các module trong hệ thống (như routes, websocket) lại với nhau.

Cấu trúc thư mục:
  app/
    __init__.py
    config.py      — Hằng số cấu hình (port, timeout...)
    state.py       — WORKERS dictionary + heartbeat monitor
    tasks.py       — Danh sách task mẫu
    ws_handler.py  — Xử lý WebSocket từ Extension
    routes.py      — REST API (GET/POST/DELETE)
  static/
    index.html     — Control Panel
  main.py          ← (file này)
"""

import asyncio
import os
from contextlib import asynccontextmanager

# Vô hiệu hóa QuickEdit Mode trên Windows để tránh tình trạng terminal click chuột làm treo server
if os.name == 'nt':
    import ctypes
    kernel32 = ctypes.windll.kernel32
    handle = kernel32.GetStdHandle(-10) # STD_INPUT_HANDLE
    mode = ctypes.c_uint32()
    kernel32.GetConsoleMode(handle, ctypes.byref(mode))
    mode.value &= ~0x0040 # ENABLE_QUICK_EDIT_MODE
    kernel32.SetConsoleMode(handle, mode)

from fastapi import FastAPI, WebSocket
from fastapi.staticfiles import StaticFiles

from app.config import SERVER_HOST, SERVER_PORT, STATIC_DIR
from app.state import heartbeat_monitor
from app.ws_handler import handle_worker_connection
from app.routes import router
from app.database import init_db


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    task = asyncio.create_task(heartbeat_monitor())
    print("🏢 Orchestrator Server đang chạy tại http://localhost:3001")
    print("🔄 Heartbeat Monitor đã khởi động (timeout: 30s)")
    yield
    task.cancel()


app = FastAPI(
    title="Browser Automation Farm — Orchestrator",
    version="1.0.0",
    lifespan=lifespan
)

app.include_router(router)
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")


@app.websocket("/ws/worker")
async def websocket_worker(websocket: WebSocket):
    await handle_worker_connection(websocket)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host=SERVER_HOST, port=SERVER_PORT, reload=True)