"""
routes.py — REST API Endpoints
Cung cấp các API HTTP (GET, POST, DELETE) cho Front-end Control Panel xử lý giao diện hiển thị danh sách Tasks, Workers và Kết quả.
"""

import json

from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse
from pydantic import BaseModel

from .state import WORKERS, get_workers_list
from .tasks import get_tasks_summary, get_task_by_id
from .gemini_config import get_gemini_api_config

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
