"""
routes.py — REST API Endpoints
Cung cấp các API HTTP (GET, POST, DELETE) cho Front-end Control Panel xử lý giao diện hiển thị danh sách Tasks, Workers và Kết quả.
"""

import json
import asyncio
import httpx
from typing import Optional

from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse
from pydantic import BaseModel

from .state import WORKERS, get_workers_list
from .tasks import get_tasks_summary, get_task_by_id
from .gemini_config import get_gemini_api_config, load_gemini_config, save_gemini_config

router = APIRouter()


class AssignRequest(BaseModel):
    task_id: str
    worker_ids: list[str]


class GenImgRequest(BaseModel):
    prompt: str
    worker_ids: list[str]


@router.get("/")
async def serve_control_panel():
    return FileResponse("static/index.html")


@router.get("/workers")
async def get_workers():
    return get_workers_list()


@router.get("/tasks")
async def get_tasks():
    from .tasks import get_tasks_summary
    return get_tasks_summary()

@router.get("/tasks/{task_id}")
async def get_task_details(task_id: str):
    from .tasks import get_task_by_id
    task = get_task_by_id(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Không tìm thấy kịch bản")
    return task

@router.post("/tasks")
async def save_task(task_data: dict):
    from .tasks import custom_tasks, save_custom_tasks
    
    task_id = task_data.get("task_id")
    if not task_id:
        raise HTTPException(status_code=400, detail="Thiếu task_id")
        
    # Cập nhật hoặc thêm mới custom task
    for idx, t in enumerate(custom_tasks):
        if t["task_id"] == task_id:
            custom_tasks[idx] = task_data
            save_custom_tasks()
            return {"status": "success", "message": f"Đã cập nhật kịch bản {task_id}"}
            
    custom_tasks.append(task_data)
    save_custom_tasks()
    return {"status": "success", "message": f"Đã lưu kịch bản {task_id} mới"}

@router.delete("/tasks/{task_id}")
async def delete_task(task_id: str):
    from .tasks import custom_tasks, save_custom_tasks
    for idx, t in enumerate(custom_tasks):
        if t["task_id"] == task_id:
            custom_tasks.pop(idx)
            save_custom_tasks()
            return {"status": "success", "message": f"Đã xóa kịch bản {task_id}"}
    raise HTTPException(status_code=404, detail="Không tìm thấy kịch bản (chỉ có thể xóa kịch bản tùy chỉnh)")

from .database import get_all_results, delete_result, get_image_results

@router.get("/results")
async def get_results(page: int = 1, limit: int = 15):
    offset = (page - 1) * limit
    return get_all_results(offset, limit)

@router.delete("/results/{result_id}")
async def delete_task_result(result_id: int):
    success = delete_result(result_id)
    if success:
        return {"status": "success", "message": f"Deleted result {result_id}"}
    raise HTTPException(status_code=404, detail=f"Result {result_id} không tồn tại")


@router.post("/gen-img")
async def generate_image(req: GenImgRequest):
    """Nhận prompt + worker_ids, inject Gemini API config, dispatch task."""
    # Lấy config API Gemini từ gemini_config.py
    cfg = get_gemini_api_config()

    # Lấy template task và inject params động
    from .tasks import get_task_by_id
    task_template = get_task_by_id("gemini_gen_image")
    if task_template is None:
        raise HTTPException(status_code=500, detail="Task 'gemini_gen_image' chưa được cấu hình")

    # Deep-copy và inject giá trị thực vào từng step
    import copy
    steps = copy.deepcopy(task_template["steps"])
    for step in steps:
        for key in ["prompt", "endpoint", "bl", "model_code"]:
            if step.get(key) == f"{{{key}}}":
                if key == "prompt":
                    step[key] = req.prompt
                else:
                    step[key] = cfg.get(key)

    payload = json.dumps({
        "type": "task",
        "task": {
            "task_id": "gemini_gen_image",
            "steps":   steps,
        }
    })

    assigned_workers = []
    errors = []

    for wid in req.worker_ids:
        if wid not in WORKERS:
            errors.append(f"Worker '{wid}' không tồn tại")
            continue

        worker = WORKERS[wid]
        if worker["state"] != "IDLE":
            errors.append(f"Worker '{wid}' đang '{worker['state']}'")
            continue
        if worker.get("ws") is None:
            errors.append(f"Worker '{wid}' không có kết nối WS")
            continue

        try:
            await worker["ws"].send_text(payload)
            assigned_workers.append(wid)
            print(f"🎨 Gen-img dispatch → Worker [{wid[:8]}] prompt='{req.prompt[:50]}'") 
        except Exception as e:
            errors.append(f"Worker '{wid}' lỗi gửi: {e}")

    if not assigned_workers and errors:
        raise HTTPException(status_code=400, detail="Không thể tạo ảnh. Lỗi: " + "; ".join(errors))

    return {
        "status": "dispatched", 
        "prompt": req.prompt,
        "assigned_to": assigned_workers,
        "errors": errors
    }


@router.get("/gen-img/results")
async def get_gen_img_results(page: int = 1, limit: int = 20):
    """Trả về danh sách ảnh đã generate cho UI gallery."""
    offset = (page - 1) * limit
    return get_image_results(offset, limit)


@router.post("/assign_task")
async def assign_task(req: AssignRequest):
    task_data = get_task_by_id(req.task_id)
    if task_data is None:
        raise HTTPException(status_code=404, detail=f"Task '{req.task_id}' không tồn tại")

    assigned_workers = []
    errors = []

    for wid in req.worker_ids:
        if wid not in WORKERS:
            errors.append(f"Worker '{wid}' không tồn tại")
            continue

        worker = WORKERS[wid]

        if worker["state"] != "IDLE":
            errors.append(f"Worker '{wid}' đang '{worker['state']}'")
            continue
            
        if worker.get("ws") is None:
            errors.append(f"Worker '{wid}' không có WebSocket")
            continue

        try:
            payload = json.dumps({
                "type": "task",
                "task": {"task_id": task_data["task_id"], "steps": task_data["steps"]}
            })
            await worker["ws"].send_text(payload)
            assigned_workers.append(wid)
            print(f"🚀 Giao Task '{req.task_id}' → Worker [{wid[:8]}]")
        except Exception as e:
            errors.append(f"Worker '{wid}' lỗi gửi: {str(e)}")

    if not assigned_workers and errors:
        raise HTTPException(status_code=400, detail="Không thể giao task. Lỗi: " + "; ".join(errors))

    return {
        "status": "assigned", 
        "task_id": req.task_id, 
        "assigned_to": assigned_workers,
        "errors": errors
    }


@router.delete("/workers/{worker_id}")
async def delete_worker(worker_id: str):
    if worker_id not in WORKERS:
        raise HTTPException(status_code=404, detail=f"Worker '{worker_id}' không tồn tại")

    ws = WORKERS[worker_id].get("ws")
    if ws:
        try:
            await ws.close()
        except Exception:
            pass

    del WORKERS[worker_id]
    print(f"🗑️  Đã xóa Worker [{worker_id[:8]}]")
    return {"status": "deleted", "worker_id": worker_id}


@router.get("/api/settings/gemini")
async def get_settings_gemini():
    return load_gemini_config()

@router.post("/api/settings/gemini")
async def update_settings_gemini(settings: dict):
    success = save_gemini_config(settings)
    if success:
        return {"status": "success", "message": "Đã lưu cấu hình Gemini"}
    raise HTTPException(status_code=500, detail="Không thể lưu cấu hình")


# ─────────────────────────────────────────
#  GPM Login Integration
# ─────────────────────────────────────────

GPM_BASE = "http://127.0.0.1:19995"
GPM_TIMEOUT = 30  # seconds per request


class GpmProfileRequest(BaseModel):
    profile_ids: list[str]


@router.get("/api/gpm/profiles")
async def gpm_list_profiles(group_id: Optional[int] = None, page: int = 1, per_page: int = 100):
    """Lấy danh sách profiles từ GPM Login và kiểm tra trạng thái đang chạy."""
    try:
        async with httpx.AsyncClient(timeout=GPM_TIMEOUT) as client:
            params = {"page": page, "per_page": per_page}
            if group_id is not None:
                params["group_id"] = group_id
            
            res = await client.get(
                f"{GPM_BASE}/api/v3/profiles",
                params=params
            )
            res.raise_for_status()
            data = res.json()
            
            # Extract profile list based on GPM API response format
            profiles = data.get("data", []) if isinstance(data, dict) else data
            
            # Cross-reference with active WORKERS to determine if it's currently running
            from .state import WORKERS
            
            # Helper to check if a profile is running based on connected workers
            def is_profile_running(p):
                # If worker explicitly provides a profile_id
                for wid, wdata in WORKERS.items():
                    if wdata.get("profile_id") == p["id"]:
                        return True
                    # GPM profiles often have the extension attached natively with worker_id = profile name
                    if wid == p["name"] or wid.startswith(p["name"] + "_"):
                        return True
                    if wid == p["id"] or wid.startswith(p["id"] + "_"):
                        return True
                return False
                
            for p in profiles:
                p["is_running"] = is_profile_running(p)
                
            if isinstance(data, dict):
                data["data"] = profiles
                return data
            return profiles
            
    except httpx.ConnectError:
        raise HTTPException(
            status_code=503,
            detail="Không thể kết nối GPM Login. Hãy chắc chắn GPM đang chạy (port 19995)."
        )
    except httpx.HTTPStatusError as e:
        raise HTTPException(status_code=e.response.status_code, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Lỗi GPM: {str(e)}")



async def _start_one(client: httpx.AsyncClient, profile_id: str) -> dict:
    """Mở 1 profile, trả về kết quả kèm profile_id."""
    try:
        res = await client.get(
            f"{GPM_BASE}/api/v3/profiles/start/{profile_id}",
            timeout=GPM_TIMEOUT
        )
        data = res.json()
        return {"profile_id": profile_id, "success": data.get("success", False), "data": data}
    except Exception as e:
        return {"profile_id": profile_id, "success": False, "error": str(e)}


async def _close_one(client: httpx.AsyncClient, profile_id: str) -> dict:
    """Đóng 1 profile."""
    try:
        res = await client.get(
            f"{GPM_BASE}/api/v3/profiles/close/{profile_id}",
            timeout=GPM_TIMEOUT
        )
        data = res.json()
        return {"profile_id": profile_id, "success": data.get("success", False), "data": data}
    except Exception as e:
        return {"profile_id": profile_id, "success": False, "error": str(e)}


@router.post("/api/gpm/start")
async def gpm_start_profiles(req: GpmProfileRequest):
    """Mở nhiều GPM profiles song song."""
    if not req.profile_ids:
        raise HTTPException(status_code=400, detail="Cần ít nhất 1 profile_id")
    try:
        async with httpx.AsyncClient() as client:
            results = await asyncio.gather(
                *[_start_one(client, pid) for pid in req.profile_ids]
            )
        ok = [r for r in results if r.get("success")]
        fail = [r for r in results if not r.get("success")]
        return {"status": "done", "opened": ok, "failed": fail}
    except httpx.ConnectError:
        raise HTTPException(status_code=503, detail="Không thể kết nối GPM Login.")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Lỗi GPM: {str(e)}")


@router.post("/api/gpm/close")
async def gpm_close_profiles(req: GpmProfileRequest):
    """Đóng nhiều GPM profiles song song."""
    if not req.profile_ids:
        raise HTTPException(status_code=400, detail="Cần ít nhất 1 profile_id")
    try:
        async with httpx.AsyncClient() as client:
            results = await asyncio.gather(
                *[_close_one(client, pid) for pid in req.profile_ids]
            )
        ok = [r for r in results if r.get("success")]
        fail = [r for r in results if not r.get("success")]
        return {"status": "done", "closed": ok, "failed": fail}
    except httpx.ConnectError:
        raise HTTPException(status_code=503, detail="Không thể kết nối GPM Login.")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Lỗi GPM: {str(e)}")


# ── GPM: Danh sách nhóm ──
# GET /api/v3/groups
@router.get("/api/gpm/groups")
async def gpm_list_groups():
    """Lấy danh sách nhóm profiles từ GPM Login."""
    try:
        async with httpx.AsyncClient(timeout=GPM_TIMEOUT) as client:
            res = await client.get(f"{GPM_BASE}/api/v3/groups")
            res.raise_for_status()
            return res.json()
    except httpx.ConnectError:
        raise HTTPException(status_code=503, detail="Không thể kết nối GPM Login (port 19995).")
    except httpx.HTTPStatusError as e:
        raise HTTPException(status_code=e.response.status_code, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Lỗi GPM: {str(e)}")


# ── GPM: Lấy thông tin 1 profile ──
# GET /api/v3/profiles/{id}
@router.get("/api/gpm/profile/{profile_id}")
async def gpm_get_profile(profile_id: str):
    """Lấy thông tin chi tiết 1 profile."""
    try:
        async with httpx.AsyncClient(timeout=GPM_TIMEOUT) as client:
            res = await client.get(f"{GPM_BASE}/api/v3/profiles/{profile_id}")
            res.raise_for_status()
            return res.json()
    except httpx.ConnectError:
        raise HTTPException(status_code=503, detail="Không thể kết nối GPM Login (port 19995).")
    except httpx.HTTPStatusError as e:
        raise HTTPException(status_code=e.response.status_code, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Lỗi GPM: {str(e)}")


# ── GPM: Tạo profile mới ──
# POST /api/v3/profiles/create
@router.post("/api/gpm/profiles/create")
async def gpm_create_profile(body: dict):
    """Tạo profile mới trong GPM Login.

    Body fields (profile_name bắt buộc, còn lại tuỳ chọn):
      profile_name, group_name, browser_core (chromium/firefox),
      browser_name (Chrome/Firefox), browser_version,
      is_random_browser_version, raw_proxy, startup_urls,
      is_masked_font, is_noise_canvas, is_noise_webgl,
      is_noise_client_rect, is_noise_audio_context,
      is_random_screen, is_masked_webgl_data, is_masked_media_device,
      is_random_os, os, webrtc_mode (1=Off, 2=Base on IP), user_agent
    """
    try:
        async with httpx.AsyncClient(timeout=GPM_TIMEOUT) as client:
            res = await client.post(f"{GPM_BASE}/api/v3/profiles/create", json=body)
            res.raise_for_status()
            return res.json()
    except httpx.ConnectError:
        raise HTTPException(status_code=503, detail="Không thể kết nối GPM Login (port 19995).")
    except httpx.HTTPStatusError as e:
        raise HTTPException(status_code=e.response.status_code, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Lỗi GPM: {str(e)}")


# ── GPM: Cập nhật profile ──
# POST /api/v3/profiles/update/{profile_id}
@router.post("/api/gpm/profiles/update/{profile_id}")
async def gpm_update_profile(profile_id: str, body: dict):
    """Cập nhật thông tin profile (chỉ gửi field muốn thay đổi).

    Body fields (không bắt buộc):
      profile_name, group_id, raw_proxy, startup_urls, note, color,
      user_agent, is_noise_canvas, is_noise_webgl,
      is_noise_client_rect, is_noise_audio_context
    """
    try:
        async with httpx.AsyncClient(timeout=GPM_TIMEOUT) as client:
            res = await client.post(
                f"{GPM_BASE}/api/v3/profiles/update/{profile_id}",
                json=body
            )
            res.raise_for_status()
            return res.json()
    except httpx.ConnectError:
        raise HTTPException(status_code=503, detail="Không thể kết nối GPM Login (port 19995).")
    except httpx.HTTPStatusError as e:
        raise HTTPException(status_code=e.response.status_code, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Lỗi GPM: {str(e)}")


# ── GPM: Xóa profile ──
# GET /api/v3/profiles/delete/{profile_id}?mode=1|2
@router.delete("/api/gpm/profiles/{profile_id}")
async def gpm_delete_profile(profile_id: str, mode: int = 1):
    """Xóa profile.

    mode: 1 = chỉ xóa DB, 2 = xóa DB + nơi lưu trữ (file/S3)
    """
    try:
        async with httpx.AsyncClient(timeout=GPM_TIMEOUT) as client:
            res = await client.get(
                f"{GPM_BASE}/api/v3/profiles/delete/{profile_id}",
                params={"mode": mode}
            )
            res.raise_for_status()
            return res.json()
    except httpx.ConnectError:
        raise HTTPException(status_code=503, detail="Không thể kết nối GPM Login (port 19995).")
    except httpx.HTTPStatusError as e:
        raise HTTPException(status_code=e.response.status_code, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Lỗi GPM: {str(e)}")
