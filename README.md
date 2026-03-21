# Browser Automation Farm (CDP)

> **⚠️ Ghi chú:** Dự án hiện tại đang trong quá trình phát triển (Under Development).

Browser Automation Farm là một hệ thống tự động hóa trình duyệt web thông qua Chrome Extension kết hợp với một Orchestrator Server (FastAPI). Thay vì sử dụng Selenium hay Playwright truyền thống dễ bị phát hiện (bot detection), hệ thống này gửi lệnh trực tiếp vào các trình duyệt thật của người dùng thông qua WebSocket và Extension.

---

## 🏗 Cấu trúc thư mục (Directory Tree)

Dự án được chia thành 2 phần chính: **Orchestrator Server** và **Chrome Extension**.

```text
CDP/
├── Local-temporary-extension-3001/    # Orchestrator Server (Quản lý và điều phối)
│   ├── app/                           # Chứa logic chính của server
│   │   ├── __init__.py                
│   │   ├── config.py                  # Cấu hình hằng số (Port, DB path, timeout...)
│   │   ├── database.py                # Xử lý SQLite (Lưu kết quả task, image generation)
│   │   ├── gemini_client.py           # Gọi ngầm Gemini API từ server thay vì extension
│   │   ├── routes.py                  # Các REST API endpoints (quản lý HTTP request)
│   │   ├── state.py                   # State management (Quản lý trạng thái worker: IDLE, BUSY...)
│   │   ├── tasks.py                   # Danh sách các kịch bản tự động hóa (scrape, gen ảnh...)
│   │   └── ws_handler.py              # Quản lý kết nối WebSockets 2 chiều giữa Server và Extension
│   ├── static/                        # Chứa các file frontend cho bảng điều khiển
│   │   └── index.html                 # Control Panel trực quan (web dashboard/UI quản lý)
│   ├── main.py                        # Entry point khởi chạy server FastAPI
│   └── requirements.txt               # Các thư viện Python cần thiết
│
├── README.md                          # Tài liệu hướng dẫn cấu trúc và sử dụng (File này)
└── ...
```

---

## 🚀 Hướng dẫn Cài đặt và Sử dụng

### 1. Cài đặt Orchestrator Server

1. **Cài đặt Python 3.9+** nếu chưa có.
2. Mở terminal và di chuyển vào thư mục server:
   ```bash
   cd Local-temporary-extension-3001
   ```
3. Tạo môi trường ảo (khuyến nghị) và kích hoạt:
   ```bash
   python -m venv .venv
   
   # Windows
   .\.venv\Scripts\activate
   
   # macOS/Linux
   source .venv/bin/activate
   ```
4. Cài đặt các thư viện cần thiết:
   ```bash
   pip install -r requirements.txt
   ```
5. Khởi chạy Server:
   ```bash
   python main.py
   ```
   *Server sẽ chạy tại cổng `3001`.*

6. **Mở Bảng điều khiển (Control Panel):** Để thuận tiện điều phối, bạn truy cập địa chỉ `http://localhost:3001/static/index.html` bằng trình duyệt để xem giao diện quản lý máy chủ.

### 2. Cài đặt Chrome Extension (Worker)
> Khi bạn có extension sẵn (hoặc tự build), làm theo các bước sau để trình duyệt kết nối với Orchestrator Server.

1. Mở trình duyệt Chrome / Cốc Cốc / Edge / Brave...
2. Truy cập vào trang quản lý tiện ích: `chrome://extensions/`.
3. Bật **Chế độ dành cho nhà phát triển (Developer mode)** ở góc trên bên phải.
4. Click vào nút **Tải tiện ích đã giải nén (Load unpacked)**.
5. Chọn thư mục chứa mã nguồn của Chrome Extension.
6. Khi extension được tải lên thành công, nó sẽ tự động kết nối qua WebSocket tới Orchestrator Server (với điều kiện Server đang bật). Bạn có thể quay lại Control Panel để kiểm tra danh sách Worker.

### 3. Cách giao việc (Assign Task)

1. Mở Control Panel (`http://localhost:3001/static/index.html`).
2. Xem danh sách các **Worker (Trình duyệt)** đang online và ở trạng thái `IDLE`.
3. Tìm các kịch bản tự động hóa bạn muốn chạy (VD: Lấy mã DOM, tương tác giao diện hoặc tạo ảnh bằng AI) trong danh sách **Tasks**.
4. Bấm **Assign** và chọn các Worker đang rảnh để phân phối tiến trình làm việc cho các tab tương ứng.
5. Theo dõi kết quả trả về trong bảng "Lịch sử Kết Quả". Bạn có thể xem chi tiết dữ liệu JSON hoặc tải xuống file CSV kết quả tùy theo thuộc tính của task.

---

## 👨‍💻 Tác giả

Dự án này được phát triển và bảo trì bởi **tôi và đội ngũ hỗ trợ Osoverse**.
Cảm ơn bạn đã sử dụng và đóng góp cho Hệ thống Tự động hóa Trình duyệt của chúng tôi!
