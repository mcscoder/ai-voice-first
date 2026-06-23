# PHỤ LỤC A. HƯỚNG DẪN CÀI ĐẶT VÀ CẤU HÌNH HỆ THỐNG

## 1. Yêu cầu phần cứng và môi trường chạy thử

### 1.1. Cấu hình phía Server (Backend)
Để hệ thống xử lý nhận dạng và tổng hợp giọng nói không bị trễ, máy chủ dịch vụ yêu cầu cấu hình khuyến nghị như sau:
*   **Hệ điều hành:** Linux Ubuntu 20.04 LTS hoặc cao hơn.
*   **Bộ xử lý (CPU):** Intel Xeon hoặc AMD Ryzen 8 cores (khuyến nghị).
*   **Bộ nhớ trong (RAM):** 16 GB trở lên.
*   **Bộ xử lý đồ họa (GPU):** NVIDIA GPU hỗ trợ kiến trúc CUDA; môi trường chạy thử hiện tại sử dụng RTX 2080S với 8GB VRAM.
*   **Môi trường:** Python phiên bản >= 3.12, quản lý thư viện bằng công cụ `uv`.

### 1.2. Cấu hình phía Client (Frontend)
*   **Hệ điều hành thiết bị di động:** Android 9.0 (API Level 28) trở lên hoặc iOS 15.0 trở lên.
*   **Môi trường phát triển:** Flutter SDK phiên bản >= 3.8.0, Dart SDK >= 3.0.

---

## 2. Hướng dẫn cài đặt chi tiết phía Backend

### Bước 2.1: Sao chép mã nguồn và truy cập thư mục
Mở terminal và di chuyển vào thư mục dự án backend:
```bash
git clone <repository_url>
cd ai-voice-first/backend
```

### Bước 2.2: Cài đặt công cụ quản lý uv và tạo môi trường ảo
Sử dụng công cụ `uv` để khởi tạo môi trường và cài đặt các phụ thuộc một cách nhanh chóng:
```bash
# Cài đặt uv toàn cục (nếu chưa có)
curl -LsSf https://astral.sh/uv/install.sh | sh

# Tạo môi trường ảo python
uv venv

# Kích hoạt môi trường ảo
source .venv/bin/activate
```

### Bước 2.3: Đồng bộ hóa các thư viện phụ thuộc
Hệ thống sẽ đọc file `pyproject.toml` để cài đặt tự động các gói thư viện bao gồm `fastapi`, `uvicorn`, `qwen-asr`, `vieneu`, `mem0ai`:
```bash
uv sync
```

### Bước 2.4: Cấu hình biến môi trường (`backend/.env`)
Tạo một tệp tin `.env` trong thư mục `backend/` để cấu hình các khóa API và thư mục bộ nhớ:
```env
# Môi trường chạy ứng dụng (development/production)
APP_ENV=development

# Khóa API để gọi mô hình ngôn ngữ lớn (LLM) cho Mem0
DEEPSEEK_API_KEY=your_deepseek_api_key_here

# Cấu hình cổng chạy máy chủ
PORT=8000
HOST=0.0.0.0
```

### Bước 2.5: Khởi chạy máy chủ Backend
Chạy file `main.py` để khởi động máy chủ FastAPI:
```bash
python main.py
```
Máy chủ sẽ lắng nghe tại cổng `http://localhost:8000`. Bạn có thể truy cập `http://localhost:8000/docs` để xem tài liệu API chi tiết dạng Swagger UI.

---

## 3. Hướng dẫn cài đặt chi tiết phía Frontend (Flutter App)

### Bước 3.1: Di chuyển vào thư mục app và cài đặt gói phụ thuộc
```bash
cd ../app
flutter pub get
```

### Bước 3.2: Cấu hình biến môi trường di động (`app/.env`)
Tạo tệp tin cấu hình `.env` tại thư mục gốc của Flutter Client để định tuyến kết nối tới máy chủ backend:
```env
# Địa chỉ URL của máy chủ Backend FastAPI đã khởi chạy
BACKEND_URL=http://<IP_MAY_CHU_BACKEND>:8000
```
*Lưu ý:* Nếu chạy giả lập (Emulator/Simulator), có thể sử dụng IP `http://10.0.2.2:8000` (đối với giả lập Android) hoặc `http://localhost:8000` (đối với giả lập iOS).

### Bước 3.3: Khởi chạy mã nguồn trên thiết bị di động
Kết nối thiết bị di động hoặc mở máy ảo giả lập, sau đó chạy lệnh:
```bash
flutter run
```
Hệ thống sẽ tiến hành biên dịch mã nguồn và cài đặt trực tiếp ứng dụng VocalMind lên thiết bị.
