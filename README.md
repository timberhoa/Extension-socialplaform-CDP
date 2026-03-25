# 🤖 Browser Automation Farm (CDP)

> **⚠️ Status:** Under Active Development

A stealth browser automation system that sends commands directly into **real user browsers** via Chrome Extension + WebSocket, bypassing bot-detection systems that catch Selenium/Playwright.

**→ No fake browsers. No headless. Real browser fingerprints.**

---

## 🎯 What It Does

| Feature | Description |
|---------|-------------|
| 🌐 **Real Browser Automation** | Uses actual Chrome/Edge/Brave — undetectable by bot-detection |
| 🧑‍💻 **Distributed Workers** | Multiple browsers/machines run tasks in parallel |
| 📋 **JSON Task Definition** | Define multi-step workflows as JSON, no coding needed |
| 🎨 **Gemini AI Image Gen** | Generate images by borrowing a real Gemini session |
| 💓 **Heartbeat Monitor** | Auto-detects offline/hung workers |
| 🔁 **Auto Reconnect** | Extension reconnects automatically on disconnect |
| 📊 **Web Control Panel** | Full web dashboard to manage workers, tasks, results |
| 🗄️ **SQLite History** | All task results and generated images are stored locally |
| 🐳 **Docker Support** | One-command server deployment |
| 🔐 **GPM Login Integration** | Open/close browser profiles via GPM Login (port 19995) |

---

## 🏛️ Architecture

```
┌─────────────────────────────────────────────────────┐
│              Admin / User                            │
│         http://localhost:3001  (Control Panel)       │
└──────────────────────┬──────────────────────────────┘
                       │ REST API (HTTP)
                       ▼
┌─────────────────────────────────────────────────────┐
│        ORCHESTRATOR SERVER  (FastAPI · Python)       │
│                   Port: 3001                         │
│                                                      │
│  routes.py   ←  REST endpoints (assign, results…)   │
│  state.py    ←  WORKERS{} dict + heartbeat monitor   │
│  ws_handler  ←  WebSocket 2-way relay                │
│  tasks.py    ←  Task store (built-in + custom JSON)  │
│  database.py ←  SQLite CRUD                          │
│  gemini_client ← Server-side Gemini image generation │
└──────────────────────┬──────────────────────────────┘
                       │ WebSocket  ws://localhost:3001/ws/worker
                       ▼
┌─────────────────────────────────────────────────────┐
│       CHROME EXTENSION WORKER  (runs in browser)     │
│                                                      │
│  background.js  (Service Worker)                     │
│  ├── identity.js   → persistent UUID                 │
│  ├── websocket.js  → WS connect · heartbeat 10s      │
│  ├── executor.js   → receive task · open CDP tab     │
│  ├── step-runner.js→ dispatch each action            │
│  └── actions/                                        │
│       ├── basic          navigate · click · type     │
│       ├── advanced       JS eval · upload · save     │
│       ├── anti-detect    human mouse · random delay  │
│       ├── control-flow   loop · if/else              │
│       ├── keyboard       hotkeys · enter · hover     │
│       ├── reporting      screenshot · assert · log   │
│       └── gemini-image-gen  steal Gemini session     │
└─────────────────────────────────────────────────────┘
```

---

## 📂 Project Structure

```
CDP/
├── Extension-CDP-ex-yt/              # Chrome Extension (Worker)
│   ├── manifest.json                 # Manifest V3
│   ├── background.js                 # Service Worker entry point
│   ├── popup.html / popup.js         # Extension popup UI
│   └── modules/
│       ├── config.js                 # WS_URL, workerId constants
│       ├── identity.js               # UUID generation & storage
│       ├── websocket.js              # WS connect, heartbeat, reconnect
│       ├── executor.js               # Task execution coordinator
│       ├── step-runner.js            # Per-step action dispatcher
│       ├── cdp-helpers.js            # Chrome Debugger API helpers
│       └── actions/                  # Action modules (see table below)
│
├── Local-temporary-extension-3001/   # Orchestrator Server (FastAPI)
│   ├── main.py                       # Entry point
│   ├── requirements.txt
│   ├── Dockerfile / docker-compose.yml
│   ├── app/
│   │   ├── config.py                 # Port, timeouts
│   │   ├── state.py                  # Worker state machine
│   │   ├── routes.py                 # All REST API endpoints
│   │   ├── ws_handler.py             # WebSocket handler
│   │   ├── tasks.py                  # Built-in sample tasks
│   │   ├── database.py               # SQLite CRUD
│   │   ├── gemini_client.py          # Gemini image generation
│   │   └── gemini_config.py          # Gemini settings load/save
│   ├── static/
│   │   ├── index.html                # Control Panel Web UI
│   │   └── images/                   # Generated images saved here
│   └── data/
│       └── custom_tasks.json         # User-created tasks (persistent)
│
├── README.md
└── LICENSE
```

---

## 🚀 Quick Start

### 1. Start the Orchestrator Server

```bash
cd Local-temporary-extension-3001

# Create & activate virtual env
python -m venv .venv

# Windows
.\.venv\Scripts\activate
# macOS / Linux
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Run server
python main.py
```

**Or with Docker:**
```bash
cd Local-temporary-extension-3001
docker-compose up
```

Server will be available at **`http://localhost:3001`**

---

### 2. Install Chrome Extension (Worker)

1. Open your browser and go to `chrome://extensions/`
2. Enable **Developer mode** (top-right toggle)
3. Click **Load unpacked** → select the `Extension-CDP-ex-yt/` folder
4. The extension auto-connects via WebSocket to `ws://localhost:3001/ws/worker`
5. Check the Control Panel — your browser should appear as a worker

---

### 3. Assign a Task

1. Open **Control Panel** → `http://localhost:3001/`
2. Browse the **Tasks** list (built-in demos + your custom tasks)
3. Select one or more **IDLE workers**
4. Click **Assign** → monitor progress in real time
5. View results in the **Results History** table

---

## 📡 REST API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/` | Serve Control Panel |
| `GET` | `/workers` | List all workers & status |
| `DELETE` | `/workers/{id}` | Disconnect/remove a worker |
| `GET` | `/tasks` | All tasks (summary, no steps) |
| `GET` | `/tasks/{id}` | Single task with full steps |
| `POST` | `/tasks` | Create/update a custom task |
| `DELETE` | `/tasks/{id}` | Delete a custom task |
| `POST` | `/assign_task` | Assign task to worker(s) |
| `GET` | `/results` | Task result history (paginated) |
| `DELETE` | `/results/{id}` | Delete a result entry |
| `POST` | `/gen-img` | Start Gemini image generation |
| `GET` | `/gen-img/results` | Gallery of generated images |
| `GET` | `/api/settings/gemini` | Get Gemini config |
| `POST` | `/api/settings/gemini` | Save Gemini config |
| `GET` | `/api/gpm/profiles` | List GPM Login profiles |
| `POST` | `/api/gpm/profiles/{id}/open` | Open a GPM profile |
| `POST` | `/api/gpm/profiles/{id}/close` | Close a GPM profile |

Full interactive API docs (Swagger UI): **`http://localhost:3001/docs`**

---

## 📨 WebSocket Protocol

### Extension → Server

| `type` | Payload | Meaning |
|--------|---------|---------|
| `register` | `{worker_id, agent}` | Register new worker |
| `ping` | `{worker_id}` | Heartbeat every 10s |
| `state_update` | `{state, task_id?}` | BUSY / IDLE / ERROR |
| `task_result` | `{task_id, status, results[]}` | Task execution result |

### Server → Extension

| `type` | Payload | Meaning |
|--------|---------|---------|
| `registered` | `{worker_id, message}` | Confirm registration |
| `task` | `{task: {task_id, steps[]}}` | Dispatch task to worker |

---

## ⚙️ Worker State Machine

```
                  WS Connected
                       │
                       ▼
                    [IDLE] ◄─────────────────┐
                       │                      │
          Task Assigned│                      │ Task Done
                       ▼                      │
                    [BUSY] ───────────────────┘
                       │
      WS Closed        │   >30s no ping
                       ▼         │
                  [OFFLINE]   [HUNG] → auto-recover → [IDLE]
```

---

## 🧩 Built-in Sample Tasks

| task_id | Description |
|---------|-------------|
| `google_search_demo` | Search Google, extract top 5 h3 results |
| `youtube_search_demo` | YouTube search, extract 30 video titles (lazy-load) |
| `wikipedia_demo` | Fetch Wikipedia title & sections |
| `scroll_enter_demo` | Scroll page + press Enter |
| `anti_detection_demo` | Simulate human mouse movement + random delay |
| `hover_keyboard_demo` | Hover menu + Ctrl+A shortcut |
| `upload_file_demo` | Upload file via `input[type=file]` |
| `if_exists_demo` | Conditional: close popup if exists, else skip |
| `loop_elements_demo` | Loop CSS elements, crawl links |
| `debug_report_demo` | Screenshot + assert text + save_to_results |
| `gemini_gen_image` | Steal Gemini session → server generates AI image |

---

## 🎭 Available Actions (Extension)

| Category | Actions |
|----------|---------|
| **basic** | `goto`, `wait_for_selector`, `click`, `type_text`, `scroll` |
| **advanced** | `evaluate_script`, `upload_file`, `save_to_results` |
| **anti-detect** | `simulate_human_mouse`, `random_delay` |
| **control-flow** | `if_exists_then`, `loop_elements` |
| **keyboard** | `press_enter`, `keyboard_shortcut`, `hover` |
| **reporting** | `take_screenshot`, `assert_text`, `log_message` |
| **gemini-image-gen** | `get_gemini_auth` |

---

## 🗄️ Database (SQLite)

File: `Local-temporary-extension-3001/database.sqlite`

**`task_results`** — task execution history  
**`image_results`** — Gemini-generated image records

---

## 🔑 Key Configuration

**Server** (`app/config.py`):
```python
SERVER_PORT = 3001
HEARTBEAT_TIMEOUT = 30        # seconds before worker marked HUNG
HEARTBEAT_CHECK_INTERVAL = 5  # check frequency in seconds
```

**Extension** (`modules/config.js`):
```javascript
WS_URL = 'ws://localhost:3001/ws/worker'
RECONNECT_DELAY_MS    = 5000   // retry after disconnect
HEARTBEAT_INTERVAL_MS = 10000  // ping every 10s
```

**GPM Login** — runs on port `19995` (default). Manage browser profiles directly from the Control Panel.

---

## 🔒 Chrome Extension Permissions

| Permission | Reason |
|-----------|--------|
| `debugger` | Attach CDP debugger to control tabs |
| `tabs` | Create and close tabs |
| `storage` | Persist worker UUID across restarts |
| `cookies` | Read cookies for Gemini auth |
| `scripting` | Inject scripts into pages |
| `<all_urls>` | Host permission — access any URL |

---

## 📦 Python Dependencies

```
fastapi       — Async web framework
uvicorn       — ASGI server
websockets    — WebSocket support
httpx         — Async HTTP client
gemini-webapi — Unofficial Gemini API wrapper (image gen)
Pillow        — Image processing & conversion
```

---

## 👨‍💻 Author

Developed and maintained by **Osoverse Team**.  
For detailed architecture docs, see [PROJECT_OVERVIEW.md](./PROJECT_OVERVIEW.md).
