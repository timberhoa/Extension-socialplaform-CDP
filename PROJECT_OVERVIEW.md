# 🗺️ PROJECT OVERVIEW — Browser Automation Farm (CDP)

> **Ngày cập nhật:** 2026-03-25  
> **Trạng thái dự án:** Under Development  
> **Tài liệu này:** Mô tả toàn bộ cấu trúc và cơ chế hoạt động của dự án (không bao gồm thư mục `reverse_api_web`).

---

## 📌 Mục tiêu Dự án

**Browser Automation Farm** là hệ thống tự động hóa trình duyệt web thông qua **Chrome Extension** kết hợp với **Orchestrator Server (FastAPI)**. Thay vì dùng Selenium/Playwright truyền thống (dễ bị phát hiện là bot), hệ thống **gửi lệnh trực tiếp vào trình duyệt thật của người dùng** qua WebSocket và Chrome DevTools Protocol (CDP), giúp né được các hệ thống bot-detection.

---

## 🗂️ Cấu trúc Thư mục (Toàn bộ)

```
CDP/
├── Extension-CDP-ex-yt/              # Chrome Extension (Worker — chạy trên trình duyệt)
│   ├── manifest.json                 # Manifest V3 — khai báo quyền & entry point
│   ├── background.js                 # Service Worker: entry point, boot extension
│   ├── popup.html                    # Giao diện popup của extension
│   ├── popup.js                      # Logic điều khiển popup UI
│   ├── icons/                        # Icon 16/32/48/128px
│   └── modules/                      # Logic chính được tách module
│       ├── config.js                 # Hằng số & state singleton (WS_URL, workerId...)
│       ├── identity.js               # Sinh/lưu UUID bền vững cho Worker
│       ├── websocket.js              # Kết nối WS, heartbeat, state reporting
│       ├── executor.js               # Điều phối thực thi toàn bộ Task
│       ├── step-runner.js            # Chạy từng Step đơn lẻ (dispatch theo action)
│       ├── cdp-helpers.js            # Helper giao tiếp với Chrome Debugger API
│       ├── message-handler.js        # chrome.runtime.onMessage (nhận từ popup)
│       ├── utils.js                  # Tiện ích (pushLog, format...)
│       └── actions/                  # Các nhóm hành động được tác vụ hóa
│           ├── basic.js              # goto, click, type_text, wait_for_selector
│           ├── advanced.js           # evaluate_script, upload_file, save_to_results
│           ├── anti-detect.js        # simulate_human_mouse, random_delay
│           ├── control-flow.js       # loop_elements, if_exists_then
│           ├── keyboard.js           # press_enter, keyboard_shortcut, hover
│           ├── gemini-image-gen.js   # get_gemini_auth (lấy cookies/token Gemini)
│           └── reporting.js          # log_message, assert_text, take_screenshot
│
├── Local-temporary-extension-3001/   # Orchestrator Server (FastAPI — Python)
│   ├── main.py                       # Entry point: khởi động server, lifespan hooks
│   ├── requirements.txt              # Thư viện Python cần thiết
│   ├── Dockerfile                    # Containerize server
│   ├── docker-compose.yml            # Compose: chạy server bằng Docker
│   ├── database.sqlite               # SQLite database (tự sinh ra lúc chạy)
│   ├── app/                          # Package logic chính
│   │   ├── __init__.py
│   │   ├── config.py                 # Hằng số (port 3001, heartbeat timeout 30s)
│   │   ├── state.py                  # WORKERS dict + heartbeat monitor (async)
│   │   ├── routes.py                 # REST API endpoints (GET/POST/DELETE)
│   │   ├── ws_handler.py             # Xử lý kết nối WebSocket 2 chiều
│   │   ├── tasks.py                  # Kho Task mẫu (SAMPLE_TASKS) + custom tasks
│   │   ├── database.py               # SQLite CRUD (task_results, image_results)
│   │   ├── gemini_client.py          # Gọi Gemini API server-side để tạo ảnh
│   │   └── gemini_config.py          # Load/save cấu hình Gemini (JSON file)
│   ├── static/
│   │   ├── index.html                # Control Panel Web UI (dashboard quản lý)
│   │   └── images/                   # Ảnh Gemini được generate lưu tại đây
│   └── data/
│       └── custom_tasks.json         # Custom tasks do người dùng tạo (persistent)
│
├── README.md                         # Hướng dẫn cài đặt & sử dụng nhanh
└── LICENSE
```

---

## 🏛️ Kiến trúc Hệ thống

```
┌─────────────────────────────────────────────────────────────────────┐
│                        NGƯỜI DÙNG / ADMIN                           │
│                   http://localhost:3001/                             │
│                      (Control Panel UI)                              │
└───────────────────────────────┬─────────────────────────────────────┘
                                │  REST API (HTTP)
                                ▼
┌─────────────────────────────────────────────────────────────────────┐
│               ORCHESTRATOR SERVER (FastAPI — Python)                 │
│                        Port: 3001                                    │
│                                                                      │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────────────────┐  │
│  │  routes.py   │  │  state.py    │  │     database.py           │  │
│  │  REST API    │  │  WORKERS{}   │  │  SQLite (task_results,    │  │
│  │  endpoints   │  │  Heartbeat   │  │         image_results)    │  │
│  └──────────────┘  └──────────────┘  └──────────────────────────┘  │
│  ┌──────────────┐  ┌───────────────────────────────────────────┐    │
│  │  tasks.py    │  │         ws_handler.py                     │    │
│  │  Task store  │  │  Xử lý WebSocket 2 chiều                  │    │
│  │  (JSON defs) │  │  ping/pong | state_update | task_result   │    │
│  └──────────────┘  └───────────────────────────────────────────┘    │
│  ┌──────────────────────────────────────────────────────────────┐   │
│  │              gemini_client.py                                 │   │
│  │  Gọi Gemini API server-side (tạo ảnh AI) bằng cookies        │   │
│  └──────────────────────────────────────────────────────────────┘   │
└───────────────────────────────┬─────────────────────────────────────┘
                                │  WebSocket: ws://localhost:3001/ws/worker
                                │  (2-way realtime communication)
                                ▼
┌─────────────────────────────────────────────────────────────────────┐
│           CHROME EXTENSION WORKER (Chạy trên trình duyệt)           │
│                  (Extension-CDP-ex-yt)                               │
│                                                                      │
│  background.js (Service Worker)                                      │
│  ├── identity.js   → sinh & lưu UUID bền vững                        │
│  ├── websocket.js  → kết nối WS, heartbeat mỗi 10s, auto-reconnect   │
│  ├── executor.js   → nhận task, mở tab CDP, chạy steps               │
│  ├── step-runner.js→ dispatch từng action đến đúng module            │
│  └── actions/      → thực thi hành động trên trang web thật          │
│       ├── basic    → navigate, click, type, wait                     │
│       ├── advanced → JS eval, upload file, save results              │
│       ├── anti-detect → mouse simulation, random delay               │
│       ├── control-flow → loop, if/else branches                      │
│       ├── keyboard → hotkeys, enter, hover                           │
│       ├── reporting → screenshot, assert, log                        │
│       └── gemini-image-gen → lấy auth cookies từ Gemini             │
└─────────────────────────────────────────────────────────────────────┘
```

---

## 🔄 Luồng Hoạt động Chi tiết

### 1. Khởi động

```
[Server] python main.py
  → init_db()           : Tạo bảng SQLite (task_results, image_results)
  → heartbeat_monitor() : Background task kiểm tra worker timeout mỗi 5s
  → FastAPI listen :3001
  
[Extension] background.js bootstrap()
  → getOrCreateWorkerId() : Sinh/load UUID từ chrome.storage.local
  → connect()             : Kết nối WebSocket tới ws://localhost:3001/ws/worker
  → Gửi {"type":"register", "worker_id":"<uuid>"}
  → Server trả {"type":"registered"} → Worker sẵn sàng
  → Bắt đầu heartbeat: gửi {"type":"ping"} mỗi 10s
```

### 2. Giao Task (Assign Task)

```
[Admin] Mở http://localhost:3001 → Control Panel
  → Chọn Task trong danh sách (ví dụ: google_search_demo)
  → Chọn Worker(s) đang IDLE
  → Nhấn "Assign"
  
[Server] POST /assign_task
  → Xác minh task tồn tại (tasks.py)
  → Xác minh worker tồn tại & state == "IDLE"
  → Gửi qua WebSocket: {"type":"task", "task": {task_id, steps: [...]}}
  
[Extension] ws_handler nhận message type=="task"
  → executor.executeTask(task)
  → Gửi state_update BUSY → server
  → Mở tab mới (background, ẩn)
  → Attach Chrome Debugger (CDP v1.3)
  → Bật Page.enable, Runtime.enable, Network.enable
  → Chạy từng step tuần tự qua step-runner.js
  → Gửi {"type":"task_result", status, results:[...]} về server
  → Dọn dẹp: CDP Page.close → debugger.detach
  → Gửi state_update IDLE → server

[Server] _handle_task_result()
  → Lưu vào SQLite (task_results)
  → Cập nhật WORKERS[id].state = "IDLE"
```

### 3. Task Đặc Biệt: Tạo Ảnh Gemini

```
[Admin] Nhập prompt → POST /gen-img
  → Server inject Gemini config vào steps của task "gemini_gen_image"
  → Gửi task qua WS tới worker(s)
  
[Extension] Thực thi action "get_gemini_auth"
  → Mở tab Gemini, lấy cookies + snlm0e + bl token
  → Gửi {"type":"task_result", action:"get_gemini_auth", data:{cookies, snlm0e, bl}}
  
[Server] ws_handler phát hiện gemini_auth_result trong kết quả
  → asyncio.create_task(async_gen_image())   # bất đồng bộ, không block
  → gemini_client.generate_gemini_image(prompt, cookies, snlm0e, bl)
  → Dùng gemini-webapi library để gọi API
  → Download ảnh → save vào static/images/
  → Lưu vào image_results (SQLite)
  → Cập nhật WORKERS[id].state = "IDLE"
```

---

## 📡 REST API Endpoints

| Method | Endpoint | Mô tả |
|--------|----------|-------|
| `GET` | `/` | Phục vụ Control Panel (`static/index.html`) |
| `GET` | `/workers` | Danh sách tất cả workers & trạng thái |
| `DELETE` | `/workers/{worker_id}` | Xóa/ngắt kết nối worker |
| `GET` | `/tasks` | Danh sách tasks (rút gọn, không có steps) |
| `GET` | `/tasks/{task_id}` | Chi tiết 1 task (có steps) |
| `POST` | `/tasks` | Lưu/cập nhật custom task |
| `DELETE` | `/tasks/{task_id}` | Xóa custom task |
| `POST` | `/assign_task` | Giao task cho worker(s) |
| `GET` | `/results` | Lịch sử kết quả task (phân trang) |
| `DELETE` | `/results/{result_id}` | Xóa 1 kết quả |
| `POST` | `/gen-img` | Khởi tạo tạo ảnh Gemini |
| `GET` | `/gen-img/results` | Gallery ảnh đã generate |
| `GET` | `/api/settings/gemini` | Lấy config Gemini |
| `POST` | `/api/settings/gemini` | Lưu config Gemini |

---

## 📨 WebSocket Message Protocol

### Extension → Server

| `type` | Payload | Ý nghĩa |
|--------|---------|---------|
| `register` | `{worker_id, agent}` | Đăng ký worker mới |
| `ping` | `{worker_id}` | Heartbeat mỗi 10s |
| `state_update` | `{state, task_id?}` | Cập nhật trạng thái (BUSY/IDLE/ERROR) |
| `task_result` | `{task_id, status, results[], error?}` | Kết quả thực thi task |
| `gemini_result` | `{prompt, status, image_urls[], error?}` | Kết quả tạo ảnh (legacy) |

### Server → Extension

| `type` | Payload | Ý nghĩa |
|--------|---------|---------|
| `registered` | `{worker_id, message}` | Xác nhận đăng ký thành công |
| `task` | `{task: {task_id, steps[]}}` | Giao task thực thi |

---

## 🧩 Danh sách Task Mẫu (SAMPLE_TASKS)

| task_id | Mô tả |
|---------|-------|
| `google_search_demo` | Tìm kiếm Google, lấy 5 kết quả h3 |
| `youtube_search_demo` | Tìm kiếm YouTube, lấy 30 video (XPath, lazy load) |
| `wikipedia_demo` | Lấy tiêu đề & phần mục Wikipedia |
| `scroll_enter_demo` | Cuộn trang + nhấn Enter |
| `anti_detection_demo` | Mô phỏng chuột người dùng thật + random delay |
| `hover_keyboard_demo` | Hover menu + hotkey Ctrl+A |
| `upload_file_demo` | Upload file qua input[type=file] |
| `if_exists_demo` | Rẽ nhánh: đóng popup nếu có, bỏ qua nếu không |
| `loop_elements_demo` | Lặp qua các phần tử CSS, crawl link |
| `debug_report_demo` | Chụp ảnh màn hình, assert text, save_to_results |
| `gemini_gen_image` | Lấy auth từ Gemini tab → Server tạo ảnh AI |

---

## ⚙️ Trạng thái Worker (State Machine)

```
                    Kết nối WS thành công
                           │
                           ▼
                        [IDLE] ◄──────────────────┐
                           │                       │
           Server giao Task│                       │Task xong
                           ▼                       │
                        [BUSY] ─────────────────── ┘
                           │
           Mất kết nối WS  │   > 30s không ping
                           ▼         │
                       [OFFLINE]   [HUNG] → phục hồi → [IDLE]
```

- **IDLE**: Sẵn sàng nhận task mới
- **BUSY**: Đang thực thi task
- **HUNG**: Không nhận được heartbeat >30s (tự phục hồi khi ping lại)
- **OFFLINE**: WebSocket đã đóng

---

## 🎭 Hành động (Actions) Extension

### 📁 `actions/basic.js`
| Action | Tham số | Mô tả |
|--------|---------|-------|
| `goto` | `url` | Điều hướng tới URL |
| `wait_for_selector` | `selector, timeout` | Chờ CSS selector xuất hiện |
| `click` | `selector` | Click phần tử |
| `type_text` | `selector, text` | Nhập văn bản vào input |
| `scroll` | `direction, pixels` | Cuộn trang (up/down) |

### 📁 `actions/advanced.js`
| Action | Tham số | Mô tả |
|--------|---------|-------|
| `evaluate_script` | `script` | Chạy JS trong tab, trả về kết quả |
| `upload_file` | `selector, file_path` | Upload file qua input |
| `save_to_results` | `key, script` | Lưu giá trị JS vào kết quả cuối |

### 📁 `actions/anti-detect.js`
| Action | Tham số | Mô tả |
|--------|---------|-------|
| `simulate_human_mouse` | `selector` | Di chuyển chuột mô phỏng người thật |
| `random_delay` | `min, max` | Delay ngẫu nhiên (ms) |

### 📁 `actions/control-flow.js`
| Action | Tham số | Mô tả |
|--------|---------|-------|
| `if_exists_then` | `selector, then_steps, else_steps` | Rẽ nhánh điều kiện |
| `loop_elements` | `selector, max_items, sub_steps` | Lặp qua phần tử DOM |

### 📁 `actions/keyboard.js`
| Action | Tham số | Mô tả |
|--------|---------|-------|
| `press_enter` | `selector` | Nhấn phím Enter |
| `keyboard_shortcut` | `key, ctrl?, shift?` | Tổ hợp phím |
| `hover` | `selector` | Di chuột vào phần tử |

### 📁 `actions/reporting.js`
| Action | Tham số | Mô tả |
|--------|---------|-------|
| `take_screenshot` | `label` | Chụp ảnh màn hình (lưu kết quả) |
| `assert_text` | `selector, expected, contains?` | Kiểm tra nội dung |
| `log_message` | `message, level` | Ghi log (info/warn/error) |

### 📁 `actions/gemini-image-gen.js`
| Action | Tham số | Mô tả |
|--------|---------|-------|
| `get_gemini_auth` | `prompt` | Mở Gemini, lấy cookies+token, báo server |

---

## 🗄️ Cơ sở Dữ liệu (SQLite)

**File:** `Local-temporary-extension-3001/database.sqlite`

### Bảng `task_results`
| Cột | Kiểu | Mô tả |
|-----|------|-------|
| `id` | INTEGER PK | Auto-increment |
| `task_id` | TEXT | ID task đã chạy |
| `worker_id` | TEXT | UUID của worker |
| `status` | TEXT | `completed` / `failed` / `error` |
| `result_data` | TEXT | JSON chứa kết quả từng step |
| `error_message` | TEXT | Thông báo lỗi (nếu có) |
| `created_at` | TIMESTAMP | Thời điểm lưu |

### Bảng `image_results`
| Cột | Kiểu | Mô tả |
|-----|------|-------|
| `id` | INTEGER PK | Auto-increment |
| `prompt` | TEXT | Prompt người dùng nhập |
| `worker_id` | TEXT | UUID của worker đã xử lý |
| `status` | TEXT | `success` / `error` / `pending` |
| `image_urls` | TEXT | JSON array đường dẫn ảnh local |
| `error_message` | TEXT | Thông báo lỗi (nếu có) |
| `created_at` | TIMESTAMP | Thời điểm lưu |

---

## 🚀 Hướng dẫn Cài đặt & Chạy

### Server (Orchestrator)

```bash
cd Local-temporary-extension-3001

# Tạo và kích hoạt môi trường ảo
python -m venv .venv
# Windows:
.\.venv\Scripts\activate
# macOS/Linux:
source .venv/bin/activate

# Cài thư viện
pip install -r requirements.txt

# Chạy server
python main.py
# → http://localhost:3001
```

**Hoặc dùng Docker:**
```bash
cd Local-temporary-extension-3001
docker-compose up
```

### Chrome Extension (Worker)

1. Mở `chrome://extensions/`
2. Bật **Developer mode**
3. Click **Load unpacked** → chọn thư mục `Extension-CDP-ex-yt/`
4. Extension tự kết nối WS tới `ws://localhost:3001/ws/worker`

### Kiểm tra

- **Control Panel:** `http://localhost:3001/`
- **API Docs:** `http://localhost:3001/docs` (FastAPI Swagger tự động)

---

## 🔑 Cấu hình Quan trọng

### Server (`app/config.py`)
```python
HEARTBEAT_TIMEOUT = 30        # Giây — worker không ping → HUNG
HEARTBEAT_CHECK_INTERVAL = 5  # Giây — tần suất kiểm tra
SERVER_HOST = "0.0.0.0"
SERVER_PORT = 3001
```

### Extension (`modules/config.js`)
```javascript
WS_URL = 'ws://localhost:3001/ws/worker'
RECONNECT_DELAY_MS   = 5000   // Thử reconnect sau 5s
HEARTBEAT_INTERVAL_MS = 10000 // Ping server mỗi 10s
```

### Gemini Config (`gemini_settings.json`)
- Lưu cookies `__Secure-1PSID`, `__Secure-1PSIDTS` của tài khoản Google
- Cấu hình model, timeout, payload structure
- Có thể chỉnh qua UI tại `Settings → Gemini Config`

---

## 📦 Thư viện Python Chính

```
fastapi         — Web framework async
uvicorn         — ASGI server
websockets      — WebSocket support
sqlite3         — Built-in Python (không cần install)
gemini-webapi   — Unofficial Gemini API wrapper (tạo ảnh)
httpx           — HTTP client async (download ảnh)
Pillow (PIL)    — Xử lý & convert ảnh (PNG/WEBP)
```

---

## 🔒 Quyền Chrome Extension (manifest.json)

| Permission | Lý do |
|-----------|-------|
| `debugger` | Attach CDP debugger vào tab để điều khiển |
| `tabs` | Tạo/đóng tab mới |
| `storage` | Lưu UUID worker bền vững |
| `cookies` | Đọc cookies (dùng cho Gemini auth) |
| `scripting` | Inject script vào trang |
| `<all_urls>` | Host permission — truy cập mọi URL |

---

## 🧪 Tính năng Nổi bật

| Tính năng | Mô tả |
|-----------|-------|
| **Real Browser Automation** | Dùng trình duyệt thật → né bot detection |
| **Distributed Workers** | Nhiều trình duyệt/máy chạy song song |
| **Task JSON Definition** | Định nghĩa task bằng JSON step-by-step |
| **Custom Tasks** | Tạo và lưu task tùy chỉnh qua UI |
| **Gemini Image Gen** | Tạo ảnh AI bằng cách mượn session Gemini |
| **Heartbeat Monitor** | Tự động phát hiện worker offline/hung |
| **Auto Reconnect** | Extension tự reconnect khi mất kết nối |
| **Control Panel** | Web UI quản lý toàn bộ system |
| **SQLite History** | Lịch sử task & ảnh có thể xem/xóa |
| **Docker Support** | Chạy server trong container dễ dàng |

---

*Tài liệu này được tổng hợp từ toàn bộ source code của dự án. Để biết hướng dẫn cài đặt nhanh, xem [README.md](./README.md).*
