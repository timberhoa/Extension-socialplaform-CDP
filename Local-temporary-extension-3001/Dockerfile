FROM python:3.11-slim

# Thiết lập thư mục làm việc trong container
WORKDIR /app

# Copy requirements và cài đặt thư viện
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy toàn bộ mã nguồn vào container
COPY . .

# Expose cổng 3001 ra ngoài
EXPOSE 3001

# Lệnh khởi chạy server
CMD ["python", "main.py"]