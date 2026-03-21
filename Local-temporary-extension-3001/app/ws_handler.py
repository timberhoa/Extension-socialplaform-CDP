"""
ws_handler.py — Xử lý kết nối WebSocket
Điều phối thông tin liên lạc 2 chiều giữa Server và Extension Worker: Tiếp nhận kết quả task, cập nhật log báo lỗi và quản lý ping-pong.
"""

import asyncio
import json

from fastapi import WebSocket, WebSocketDisconnect

from .state import register_worker, update_ping, update_state, set_offline
from .database import save_task_result, save_image_result


async def handle_worker_connection(websocket: WebSocket):
    """Vòng đời đầy đủ của một kết nối WebSocket từ Extension."""
    await websocket.accept()
    worker_id = None

    try:
        # Bước 1: Nhận message register
        raw = await asyncio.wait_for(websocket.receive_text(), timeout=10)
        data = json.loads(raw)

        if data.get("type") != "register" or not data.get("worker_id"):
            await websocket.send_text(json.dumps({
                "error": "Message đầu tiên phải là 'register' và có 'worker_id'"
            }))
            await websocket.close()
            return

        worker_id = data["worker_id"]

        # Bước 2: Đăng ký vào WORKERS
        is_new = register_worker(worker_id, websocket)
        print(f"[+] Worker {'MỚI' if is_new else 'RECONNECT'}: [{worker_id[:8]}]")

        # Bước 3: Xác nhận đăng ký
        await websocket.send_text(json.dumps({
            "type": "registered",
            "worker_id": worker_id,
            "message": "Chào mừng bạn đến với Orchestrator!"
        }))

        # Bước 4: Vòng lặp nhận messages
        while True:
            raw = await websocket.receive_text()
            data = json.loads(raw)
            msg_type = data.get("type")

            if msg_type == "ping":
                _handle_ping(worker_id)
            elif msg_type == "state_update":
                _handle_state_update(worker_id, data)
            elif msg_type == "task_result":
                _handle_task_result(worker_id, data)
            elif msg_type == "gemini_result":
                _handle_gemini_result(worker_id, data)
            else:
                print(f"❓ Message không rõ từ [{worker_id[:8]}]: {msg_type}")

    except WebSocketDisconnect:
        pass
    except asyncio.TimeoutError:
        print("⏱️ Worker timeout khi register — đóng kết nối")
    except Exception as e:
        print(f"❌ Lỗi WebSocket: {e}")
    finally:
        if worker_id:
            set_offline(worker_id)
            print(f"[-] Worker [{worker_id[:8]}] → OFFLINE")


def _handle_ping(worker_id: str):
    was_hung = update_ping(worker_id)
    if was_hung:
        print(f"💚 Worker [{worker_id[:8]}] phục hồi HUNG → IDLE")


def _handle_state_update(worker_id: str, data: dict):
    new_state = data.get("state", "IDLE")
    task_id = data.get("task_id")
    update_state(worker_id, new_state, task_id)
    print(f"⚙️  Worker [{worker_id[:8]}] → {new_state}"
          + (f" (task: {task_id})" if task_id else ""))


def _handle_task_result(worker_id: str, data: dict):
    task_id = data.get("task_id", "?")
    status = data.get("status", "unknown")
    error_message = data.get("error")
    results_array = data.get("results", [])

    should_save_task_result = True

    if task_id == "gemini_gen_image":
        # Chúng ta đã chạy API ngầm server-side cho task này rồi,
        # kết quả trả về từ extension client chỉ là báo hiệu nó đã chạy placeholder.
        # Không gán IDLE ở đây để tránh bị task khác chèn vào!
        should_save_task_result = False
    else:
        update_state(worker_id, "IDLE")

    print(f"✅ [KẾT QUẢ] Worker [{worker_id[:8]}] — Task '{task_id}': {status}")

    result_data = None
    spawned_async = False

    if status == "completed":
        print(f"   [Thành công] Có {len(results_array)} bước trả về dữ liệu:")
        for res in results_array:
            print(f"   → Step {res.get('step')} ({res.get('action')}):")
            if "data" in res:
                try:
                    # Nếu là chuỗi JSON thì parse ra cho đẹp
                    parsed_data = json.loads(res["data"])
                    formatted = json.dumps(parsed_data, indent=2, ensure_ascii=False)
                    for line in formatted.split('\n'):
                        print("       " + line)
                except Exception:
                    print(f"       {res['data']}")
            if "error" in res:
                print(f"       LỖI: {res['error']}")

        result_data = json.dumps(results_array, ensure_ascii=False)

        # Auto-extract ảnh từ bước get_gemini_auth nếu có
        for res in results_array:
            if res.get("action") == "get_gemini_auth" and isinstance(res.get("data"), dict):
                step_data = res["data"]
                if step_data.get("type") == "gemini_auth_result":
                    prompt = step_data.get("prompt", "")
                    cookies = step_data.get("cookies", "")
                    snlm0e = step_data.get("snlm0e", "")
                    bl = step_data.get("bl", "")

                    async def async_gen_image():
                        import os
                        import time
                        import httpx
                        from .gemini_client import generate_gemini_image
                        print(f"   ⏳ [Server-side] Bắt đầu gọi Gemini API cho prompt: {prompt[:30]}...")
                        urls = await generate_gemini_image(prompt, cookies, snlm0e, auth_bl=bl)
                        if urls:
                            local_urls = []
                            os.makedirs("static/images", exist_ok=True)
                            
                            cookie_dict = {}
                            for c in cookies.split(";"):
                                if "=" in c:
                                    k, v = c.strip().split("=", 1)
                                    cookie_dict[k] = v
                            
                            local_urls = []
                            remote_urls_to_download = []
                            
                            for u in urls:
                                if u.startswith("/static/"):
                                    local_urls.append(u)
                                else:
                                    remote_urls_to_download.append(u)

                            if remote_urls_to_download:
                                headers = {"User-Agent": "Mozilla/5.0", "Referer": "https://gemini.google.com/"}
                                async with httpx.AsyncClient(timeout=30.0, follow_redirects=True) as client:
                                    for i, url in enumerate(remote_urls_to_download):
                                        try:
                                            print(f"   [Download] Đang tải ảnh fallback về Local: {url}")
                                            resp = await client.get(url, headers=headers, cookies=cookie_dict)
                                            if resp.status_code == 200:
                                                filename = f"gen_fallback_{int(time.time()*100)}_{i}.jpg"
                                                filepath = os.path.join("static", "images", filename)
                                                with open(filepath, "wb") as f:
                                                    f.write(resp.content)
                                                local_urls.append(f"/static/images/{filename}")
                                            else:
                                                print(f"Lỗi tải ảnh fallback {url}: {resp.status_code}")
                                        except Exception as e:
                                            print(f"Lỗi tải ảnh fallback {url}: {e}")
                                        
                            if local_urls:
                                save_image_result(
                                    worker_id=worker_id,
                                    prompt=prompt,
                                    image_urls=local_urls,
                                    status="success",
                                    error_message=None,
                                )
                                print(f"   🖼️  Đã tải và lưu {len(local_urls)} ảnh từ Server cho task {task_id}")
                                save_task_result(task_id, worker_id, "completed", json.dumps([{"step": 1, "action": "Tải Ảnh", "data": local_urls}], ensure_ascii=False))
                            else:
                                save_image_result(
                                    worker_id=worker_id,
                                    prompt=prompt,
                                    image_urls=[],
                                    status="error",
                                    error_message="Lỗi khi tải ảnh từ host Gemini về Local",
                                )
                                save_task_result(task_id, worker_id, "error", None, "Lỗi khi tải ảnh từ host Gemini về Local")
                        else:
                            save_image_result(
                                worker_id=worker_id,
                                prompt=prompt,
                                image_urls=[],
                                status="error",
                                error_message="Không parse được ảnh từ Gemini",
                            )
                            print(f"   ❌ Thất bại tạo ảnh từ Server cho task {task_id}")
                            save_task_result(task_id, worker_id, "error", None, "Không parse được ảnh từ Gemini")
                            
                        # Mở khóa worker sau khi xong task Gemini
                        update_state(worker_id, "IDLE")

                    asyncio.create_task(async_gen_image())
                    spawned_async = True
    else:
        print(f"   Lỗi: {error_message}")
    
    # Lưu vào database
    if should_save_task_result:
        save_task_result(task_id, worker_id, status, result_data, error_message)
    elif task_id == "gemini_gen_image" and not spawned_async:
        # Lỗi xảy ra trước khi sinh được async_gen_image, vd: lỗi auth
        save_task_result(task_id, worker_id, "error", None, error_message or "Không lấy được kết quả từ trình duyệt.")
        update_state(worker_id, "IDLE")


def _handle_gemini_result(worker_id: str, data: dict):
    """
    Xử lý message gemini_result từ Extension.
    Extension gửi dạng:
      {
        "type": "gemini_result",
        "task_id": "...",
        "prompt": "...",
        "status": "success" | "error",
        "image_urls": [...],   # khi success
        "error": "..."         # khi error
      }
    Hoặc được bao gồm trong task_result.results[] dưới dạng step data.
    """
    prompt         = data.get("prompt", "")
    status         = data.get("status", "error")
    image_urls     = data.get("image_urls", [])
    error_message  = data.get("error") or data.get("error_message")

    if status == "success" and image_urls:
        print(f"🎨 [Gemini] Worker [{worker_id[:8]}] tạo ảnh thành công: {len(image_urls)} ảnh")
        for i, url in enumerate(image_urls, 1):
            print(f"   [{i}] {url[:80]}...")
    else:
        print(f"❌ [Gemini] Worker [{worker_id[:8]}] lỗi tạo ảnh: {error_message}")

    row_id = save_image_result(
        prompt=prompt,
        worker_id=worker_id,
        status=status,
        image_urls=image_urls if image_urls else None,
        error_message=error_message,
    )
    print(f"💾 [Gemini] Đã lưu image_result id={row_id}")
