import os
import json

"""
tasks.py — Kho lưu trữ Task JSON mẫu
Cấu hình các luồng tự động hoá (navigate, wait, evaluate) dưới dạng kịch bản JSON tĩnh và custom_tasks.
"""

SAMPLE_TASKS = [
    {
        "task_id": "google_search_demo",
        "name": "🔍 Google Search — 'browser automation'",
        "steps": [
            {"action": "goto", "url": "https://www.google.com"},
            {"action": "wait_for_selector", "selector": "textarea[name='q']", "timeout": 10000},
            {"action": "type_text", "selector": "textarea[name='q']", "text": "browser automation python"},
            {"action": "click", "selector": "input[name='btnK']"},
            {"action": "wait_for_selector", "selector": "#search", "timeout": 15000},
            {
                "action": "evaluate_script",
                "script": "Array.from(document.querySelectorAll('h3')).slice(0,5).map(el => el.innerText)"
            }
        ]
    },
    {
        "task_id": "youtube_search_demo",
        "name": "🎬 YouTube Search — Lấy 10 kết quả video",
        "steps": [
            # ── Bước 1: Vào YouTube ──
            {"action": "goto", "url": "https://www.youtube.com"},

            # ── Bước 2: Đợi ô tìm kiếm xuất hiện ──
            {"action": "wait_for_selector", "selector": "input[name='search_query']", "timeout": 15000},

            # ── Bước 3: Click vào ô tìm kiếm ──
            {"action": "click", "selector": "input[name='search_query']"},

            # ── Bước 4: Nhập từ khóa tìm kiếm ──
            {"action": "type_text", "selector": "input[name='search_query']", "text": "lofi hip hop radio"},

            # ── Bước 5: Nhấn Enter để thực hiện tìm kiếm ──
            {"action": "press_enter", "selector": "input[name='search_query']"},

            # ── Bước 6: Đợi trang kết quả tìm kiếm xuất hiện ──
            {"action": "wait_for_selector", "selector": "ytd-video-renderer", "timeout": 20000},

            # ── Bước 6.1: Cuộn trang để ép YouTube tải thêm nội dung (Lazy load) ──
            {"action": "scroll", "direction": "down", "pixels": 1500},
            {"action": "random_delay", "min": 1500, "max": 2500},
            {"action": "scroll", "direction": "down", "pixels": 1500},
            {"action": "random_delay", "min": 1500, "max": 2500},
            {"action": "scroll", "direction": "down", "pixels": 1500},
            {"action": "random_delay", "min": 1000, "max": 2000},

            # ── Bước 7: Trích xuất lấy 30 kết quả video đầu tiên bằng JS ──
            # Dùng document.evaluate() với XPath: //ytd-video-renderer
            # Lấy title qua .//a[@id='video-title'] và URL qua .//a[@id='video-title']/@href
            {
                "action": "evaluate_script",
                "script": (
                    "(function() {"
                    "  const data = [];"
                    "  const videoRenderers = document.evaluate("
                    "    '//ytd-video-renderer',"
                    "    document, null,"
                    "    XPathResult.ORDERED_NODE_SNAPSHOT_TYPE, null"
                    "  );"
                    "  for (let i = 0; i < Math.min(videoRenderers.snapshotLength, 30); i++) {"
                    "    const renderer = videoRenderers.snapshotItem(i);"
                    "    if (!renderer) continue;"
                    "    const titleEl = renderer.querySelector('#video-title');"
                    "    const title = titleEl ? titleEl.innerText.trim() : '';"
                    "    const url   = (titleEl && titleEl.href) ? titleEl.href : '';"
                    "    if (title) data.push({ index: i + 1, title, url });"
                    "  }"
                    "  return JSON.stringify(data, null, 2);"
                    "})()"
                )
            }
        ]
    },
    {
        "task_id": "wikipedia_demo",
        "name": "📚 Wikipedia — Lấy tiêu đề bài viết",
        "steps": [
            {"action": "goto", "url": "https://en.wikipedia.org/wiki/Web_scraping"},
            {"action": "wait_for_selector", "selector": "#firstHeading", "timeout": 10000},
            {
                "action": "evaluate_script",
                "script": "document.querySelector('#firstHeading')?.innerText"
            },
            {
                "action": "evaluate_script",
                "script": "Array.from(document.querySelectorAll('#mw-content-text .mw-heading h2')).slice(0,5).map(el => el.innerText)"
            }
        ]
    },
    {
        "task_id": "scroll_enter_demo",
        "name": "🖱️ Cuộn & Nhấn Enter — 'wikipedia search'",
        "steps": [
            {"action": "goto", "url": "https://vi.wikipedia.org/"},
            {"action": "wait_for_selector", "selector": "input[name='search']", "timeout": 10000},
            {"action": "type_text", "selector": "input[name='search']", "text": "Hà Nội"},
            {"action": "press_enter", "selector": "input[name='search']"},
            {"action": "wait_for_selector", "selector": "#firstHeading", "timeout": 10000},
            {"action": "scroll", "direction": "down", "pixels": 800},
            {"action": "evaluate_script", "script": "document.querySelector('#firstHeading').innerText"}
        ]
    },
    {
        "task_id": "anti_detection_demo",
        "name": "🛡️ Anti-Detection Demo — Google (Human Mouse + Delay)",
        "steps": [
            {"action": "goto", "url": "https://www.google.com"},
            {"action": "wait_for_selector", "selector": "textarea[name='q']", "timeout": 10000},
            {"action": "random_delay", "min": 800, "max": 2000},
            {"action": "simulate_human_mouse", "selector": "textarea[name='q']"},
            {"action": "type_text", "selector": "textarea[name='q']", "text": "browser automation anti detection"},
            {"action": "random_delay", "min": 500, "max": 1500},
            {"action": "press_enter", "selector": "textarea[name='q']"},
            {"action": "wait_for_selector", "selector": "#search", "timeout": 15000},
            {"action": "scroll", "direction": "down", "pixels": 600},
            {"action": "random_delay", "min": 1000, "max": 3000},
            {
                "action": "evaluate_script",
                "script": "Array.from(document.querySelectorAll('h3')).slice(0,5).map(el => el.innerText)"
            }
        ]
    },
    {
        "task_id": "hover_keyboard_demo",
        "name": "🖱️ Hover & Keyboard — Wikipedia Menu",
        "steps": [
            {"action": "goto", "url": "https://en.wikipedia.org/wiki/Main_Page"},
            {"action": "wait_for_selector", "selector": "#n-mainpage-description", "timeout": 10000},
            {"action": "hover", "selector": "#n-mainpage-description"},
            {"action": "random_delay", "min": 500, "max": 1200},
            {"action": "keyboard_shortcut", "key": "Tab"},
            {"action": "random_delay", "min": 300, "max": 800},
            {"action": "keyboard_shortcut", "key": "a", "ctrl": True},
            {"action": "evaluate_script", "script": "document.title"}
        ]
    },
    {
        "task_id": "upload_file_demo",
        "name": "📁 Upload File — tmpfiles.org",
        "steps": [
            {"action": "goto", "url": "https://tmpfiles.org/"},
            {"action": "wait_for_selector", "selector": "input[type='file']", "timeout": 10000},
            {
                "action": "upload_file",
                "selector": "input[type='file']",
                "file_path": "C:\\Windows\\System32\\drivers\\etc\\hosts"
            },
            {"action": "random_delay", "min": 500, "max": 1000},
            {"action": "evaluate_script", "script": "document.querySelector('input[type=file]')?.files[0]?.name"}
        ]
    },
    {
        "task_id": "if_exists_demo",
        "name": "🔀 Rẽ nhánh — Đóng Popup Google nếu có",
        "steps": [
            {"action": "goto", "url": "https://www.google.com"},
            {"action": "wait_for_selector", "selector": "body", "timeout": 8000},
            {
                "action": "if_exists_then",
                "selector": "div[role='dialog'] button",
                "then_steps": [
                    {"action": "click", "selector": "div[role='dialog'] button"},
                    {"action": "random_delay", "min": 300, "max": 700}
                ],
                "else_steps": [
                    {"action": "evaluate_script", "script": "'No popup found — continuing normally'"}
                ]
            },
            {"action": "evaluate_script", "script": "document.title"}
        ]
    },
    {
        "task_id": "loop_elements_demo",
        "name": "🔁 Lặp phần tử — Crawl link Wikipedia",
        "steps": [
            {"action": "goto", "url": "https://en.wikipedia.org/wiki/Python_(programming_language)"},
            {"action": "wait_for_selector", "selector": "#mw-content-text p a", "timeout": 10000},
            {
                "action": "loop_elements",
                "selector": "#mw-content-text p a",
                "max_items": 8,
                "sub_steps": [
                    {
                        "action": "evaluate_script",
                        "script": "JSON.stringify({ index: {{index}}, text: '{{text}}', href: '{{href}}' })"
                    }
                ]
            }
        ]
    },
    {
        "task_id": "debug_report_demo",
        "name": "🧪 Báo cáo & Gỡ lỗi — Wikipedia Python",
        "steps": [
            {"action": "log_message", "message": "🚀 Bắt đầu task kiểm tra Wikipedia", "level": "info"},
            {"action": "goto", "url": "https://en.wikipedia.org/wiki/Python_(programming_language)"},
            {"action": "wait_for_selector", "selector": "h1", "timeout": 10000},

            # Chụp ảnh màn hình ngay khi trang tải xong
            {"action": "take_screenshot", "label": "page_loaded"},

            # Khẳng định tiêu đề đúng — nếu sai task sẽ dừng và báo lỗi
            {"action": "assert_text", "selector": "h1", "expected": "Python", "contains": True},
            {"action": "log_message", "message": "✅ Tiêu đề trang đúng", "level": "info"},

            # Lưu dữ liệu quan trọng vào results để trả về server
            {"action": "save_to_results", "key": "page_title",       "script": "document.title"},
            {"action": "save_to_results", "key": "heading_text",     "script": "document.querySelector('h1')?.innerText"},
            {"action": "save_to_results", "key": "paragraph_count",  "script": "document.querySelectorAll('#mw-content-text p').length"},
            {"action": "save_to_results", "key": "first_paragraph",  "script": "document.querySelector('#mw-content-text p')?.innerText?.substring(0, 200)"},

            # Cuộn xuống rồi chụp ảnh lần 2 để gỡ lỗi
            {"action": "scroll", "direction": "down", "pixels": 800},
            {"action": "random_delay", "min": 500, "max": 1000},
            {"action": "take_screenshot", "label": "after_scroll"},

            {"action": "log_message", "message": "✅ Task hoàn thành — dữ liệu đã lưu vào results", "level": "info"}
        ]
    },
    {
        "task_id": "gemini_gen_image",
        "name": "🎨 Lấy Auth & Tạo ảnh Gemini",
        "category": "gemini",
        "steps": [
            {"action": "log_message", "message": "🔐 Bắt đầu lấy Auth Info từ Gemini...", "level": "info"},
            {
                "action": "get_gemini_auth",
                "prompt": "{prompt}"
            },
            {"action": "log_message", "message": "✅ Đã lấy xong Auth. Server tiếp tục xử lý...", "level": "info"}
        ]
    }
]

CUSTOM_TASKS_FILE = "data/custom_tasks.json"
custom_tasks = []

def load_custom_tasks():
    global custom_tasks
    if os.path.exists(CUSTOM_TASKS_FILE):
        try:
            with open(CUSTOM_TASKS_FILE, "r", encoding="utf-8") as f:
                custom_tasks = json.load(f)
        except Exception as e:
            print(f"Lỗi khi load {CUSTOM_TASKS_FILE}: {e}")
            custom_tasks = []
    else:
        custom_tasks = []

def save_custom_tasks():
    os.makedirs(os.path.dirname(CUSTOM_TASKS_FILE), exist_ok=True)
    with open(CUSTOM_TASKS_FILE, "w", encoding="utf-8") as f:
        json.dump(custom_tasks, f, ensure_ascii=False, indent=2)

# Khởi tạo nạp custom tasks khi chạy
load_custom_tasks()

def get_all_tasks():
    return SAMPLE_TASKS + custom_tasks

def get_task_by_id(task_id: str) -> dict | None:
    """Tìm task theo task_id. Trả về None nếu không tìm thấy."""
    for task in get_all_tasks():
        if task["task_id"] == task_id:
            return task
    return None


def get_tasks_summary() -> list:
    """Trả về danh sách rút gọn (không có steps) cho REST API."""
    return [
        {"task_id": t.get("task_id"), "name": t.get("name"), "steps_count": len(t.get("steps", [])), "category": t.get("category", "sample" if t in SAMPLE_TASKS else "custom")}
        for t in get_all_tasks()
    ]
