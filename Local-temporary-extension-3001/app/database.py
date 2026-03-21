"""
database.py — Quản lý Cơ sở dữ liệu SQLite
Khởi tạo cấu trúc bảng (schema) và cung cấp các hàm (CRUD) để lưu/đọc dữ liệu kết quả test (bao gồm cả lịch sử tạo ảnh).
"""
import sqlite3
import json
from datetime import datetime
import os

DB_PATH = "database.sqlite"

def get_connection():
    """Tạo kết nối tới SQLite database."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    """Khởi tạo các bảng nếu chưa tồn tại."""
    conn = get_connection()
    cursor = conn.cursor()
    
    # Bảng lưu kết quả các task chạy từ Worker Extension
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS task_results (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            task_id TEXT NOT NULL,
            worker_id TEXT NOT NULL,
            status TEXT NOT NULL,
            result_data TEXT,
            error_message TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    # Bảng lưu ảnh generate từ Gemini
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS image_results (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            prompt TEXT NOT NULL,
            worker_id TEXT NOT NULL,
            status TEXT NOT NULL DEFAULT 'pending',
            image_urls TEXT,
            error_message TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    conn.commit()
    conn.close()
    print(f"📦 Đã khởi tạo Database SQLite ({DB_PATH})")

def save_task_result(task_id: str, worker_id: str, status: str, result_data: str | None = None, error_message: str | None = None):
    """Lưu trữ kết quả từ WebSocket message vào DB."""
    conn = get_connection()
    cursor = conn.cursor()
    
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    cursor.execute('''
        INSERT INTO task_results (task_id, worker_id, status, result_data, error_message, created_at)
        VALUES (?, ?, ?, ?, ?, ?)
    ''', (task_id, worker_id, status, result_data, error_message, now))
    
    conn.commit()
    conn.close()

def get_all_results(offset: int = 0, limit: int = 15):
    """Lấy danh sách các kết quả trong khoảng offset/limit cho Frontend."""
    conn = get_connection()
    cursor = conn.cursor()
    
    # Lấy tổng số dòng để hỗ trợ UI phân trang
    cursor.execute('SELECT COUNT(*) as total FROM task_results')
    total_row = cursor.fetchone()
    total = total_row['total'] if total_row else 0

    cursor.execute('''
        SELECT id, task_id, worker_id, status, result_data, error_message, created_at
        FROM task_results
        ORDER BY id DESC
        LIMIT ? OFFSET ?
    ''', (limit, offset))
    
    rows = cursor.fetchall()
    conn.close()
    
    results = []
    for r in rows:
        results.append({
            "id": r["id"],
            "task_id": r["task_id"],
            "worker_id": r["worker_id"],
            "status": r["status"],
            "result_data": r["result_data"],
            "error_message": r["error_message"],
            "created_at": r["created_at"]
        })
    
    return {
        "total": total,
        "data": results
    }

def delete_result(result_id: int):
    """Xóa một kết quả trong DB theo ID."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('DELETE FROM task_results WHERE id = ?', (result_id,))
    conn.commit()
    deleted = cursor.rowcount > 0
    conn.close()
    return deleted


def save_image_result(prompt: str, worker_id: str, status: str,
                      image_urls: list | None = None,
                      error_message: str | None = None) -> int:
    """Lưu kết quả tạo ảnh Gemini vào bảng image_results."""
    conn = get_connection()
    cursor = conn.cursor()
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    urls_json = json.dumps(image_urls, ensure_ascii=False) if image_urls else None
    cursor.execute('''
        INSERT INTO image_results (prompt, worker_id, status, image_urls, error_message, created_at)
        VALUES (?, ?, ?, ?, ?, ?)
    ''', (prompt, worker_id, status, urls_json, error_message, now))
    conn.commit()
    row_id = cursor.lastrowid or 0
    conn.close()
    return row_id


def get_image_results(offset: int = 0, limit: int = 20) -> dict:
    """Lấy danh sách ảnh đã generate cho UI gallery."""
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute('SELECT COUNT(*) as total FROM image_results')
    row = cursor.fetchone()
    total = row['total'] if row else 0

    cursor.execute('''
        SELECT id, prompt, worker_id, status, image_urls, error_message, created_at
        FROM image_results
        ORDER BY id DESC
        LIMIT ? OFFSET ?
    ''', (limit, offset))

    rows = cursor.fetchall()
    conn.close()

    data = []
    for r in rows:
        urls = []
        if r['image_urls']:
            try:
                urls = json.loads(r['image_urls'])
            except Exception:
                urls = []
        data.append({
            "id":            r['id'],
            "prompt":        r['prompt'],
            "worker_id":     r['worker_id'],
            "status":        r['status'],
            "image_urls":    urls,
            "error_message": r['error_message'],
            "created_at":    r['created_at'],
        })

    return {"total": total, "data": data}
