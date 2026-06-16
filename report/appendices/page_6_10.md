# PHỤ LỤC B. KỊCH BẢN KIỂM THỬ CHI TIẾT (TEST CASES)

## 1. Phương pháp và Quy trình kiểm thử
Hệ thống **VocalMind** áp dụng quy trình kiểm thử nghiêm ngặt bao gồm Kiểm thử đơn vị (Unit Test) cho các hàm xử lý logic nghiệp vụ và Kiểm thử tích hợp (Integration Test) cho luồng tương tác end-to-end giữa Client và Server.

*   **Phía Backend:** Sử dụng thư viện `pytest` làm khung chạy kiểm thử (test runner). Các bài kiểm thử tập trung vào tính đúng đắn của việc giải mã âm thanh nhị phân, gọi suy luận mô hình ASR, TTS và hoạt động lưu trữ bộ nhớ của Mem0.
*   **Phía Frontend:** Sử dụng thư viện `flutter_test` kết hợp kiểm thử trạng thái BLoC (`bloc_test`) để kiểm tra máy trạng thái của `VoiceCaptureCubit` khi người dùng cấp/từ chối quyền micro hoặc khi mạng gặp lỗi.

---

## 2. Kịch bản kiểm thử đơn vị phía Backend (Pytest)

### Kịch bản TC-B1: Kiểm thử giải mã âm thanh thô (Audio Decoding)
*   **Mục tiêu:** Đảm bảo hàm `decode_audio_bytes` của `AsrService` giải mã chính xác file ghi âm nhị phân sang định dạng NumPy mảng float32.
*   **Dữ liệu đầu vào:** Một tệp tin âm thanh ghi âm mẫu định dạng `.m4a` chứa 5 giây tiếng nói.
*   **Kết quả kỳ vọng:**
    *   Hàm không ném ra ngoại lệ.
    *   Mảng trả về có kiểu dữ liệu là `np.float32`.
    *   Tần số lấy mẫu nhận diện được chính xác (ví dụ: 16000Hz hoặc 48000Hz).
*   **Lệnh chạy test:** `pytest tests/test_asr.py`

### Kịch bản TC-B2: Kiểm thử xác thực chuỗi văn bản TTS đầu vào (TTS Input Validation)
*   **Mục tiêu:** Đảm bảo hệ thống phát hiện và ngăn chặn các yêu cầu tổng hợp giọng nói chứa văn bản rỗng hoặc quá dài vượt quá cấu hình cho phép.
*   **Dữ liệu đầu vào:**
    *   Yêu cầu 1: Text = `""` (Rỗng).
    *   Yêu cầu 2: Text chứa chuỗi ký tự dài 5000 từ (vượt quá giới hạn cấu hình `max_text_length = 1000`).
*   **Kết quả kỳ vọng:**
    *   Yêu cầu 1: Hệ thống trả về mã lỗi HTTP 422 hoặc ném lỗi `ValueError("Text must not be empty.")`.
    *   Yêu cầu 2: Hệ thống từ chối xử lý và báo lỗi độ dài văn bản vượt giới hạn.

---

## 3. Kịch bản kiểm thử trạng thái phía Frontend (Flutter App)

Nhóm phát triển đã xây dựng các bài test chạy tự động trên Flutter để kiểm tra tính nhất quán trong phản hồi giao diện của `VoiceCaptureCubit`:

### Kịch bản TC-F1: Trạng thái khi người dùng từ chối quyền truy cập Microphone
*   **Mục tiêu:** Đảm bảo ứng dụng phát hiện quyền mic bị từ chối và hiển thị thông tin lỗi chính xác tới người dùng.
*   **Quy trình thực hiện:**
    1.  Mô phỏng (Mock) lớp `PermissionService` trả về trạng thái `AppPermissionStatus.denied` khi yêu cầu quyền micro.
    2.  Gọi hàm `cubit.startRecording()`.
*   **Kết quả kỳ vọng (Kiểm tra dòng trạng thái phát ra):**
    *   Trạng thái Cubit chuyển từ `VoiceCaptureStatus.idle` sang `VoiceCaptureStatus.failure`.
    *   Lỗi ghi nhận trong trạng thái là `VoiceCaptureFailure.microphoneDenied`.
    *   Màn hình cập nhật hiển thị thông báo yêu cầu cấp quyền micro.

### Kịch bản TC-F2: Trạng thái khi gặp sự cố mạng trong lúc tải file âm thanh lên Server
*   **Mục tiêu:** Đảm bảo ứng dụng xử lý tốt ngoại lệ kết nối mạng bị ngắt (Timeout hoặc Bad Request) và không làm treo ứng dụng.
*   **Quy trình thực hiện:**
    1.  Cấp quyền micro thành công.
    2.  Mô phỏng (Mock) `TranscriptionApi` ném ra lỗi ngoại lệ `Timeout` hoặc `NetworkError` khi gọi phương thức gửi dữ liệu.
    3.  Gọi hàm `cubit.stopRecording()`.
*   **Kết quả kỳ vọng (Kiểm tra dòng trạng thái phát ra):**
    *   Cubit phát ra trạng thái `VoiceCaptureStatus.uploading`.
    *   Khi API báo lỗi, Cubit lập tức phát ra trạng thái `VoiceCaptureStatus.failure`.
    *   Lỗi ghi nhận tương ứng là `VoiceCaptureFailure.network`.
    *   Giao diện hiển thị nút micrô kèm thông báo lỗi kết nối mạng màu đỏ để người dùng bấm thử lại.

---

## 4. Hướng dẫn chạy kiểm thử tự động toàn bộ hệ thống
Để kiểm thử độ tin cậy của mã nguồn trước khi tích hợp liên tục (CI/CD), lập trình viên thực hiện các lệnh sau:

### Chạy test Backend:
```bash
cd backend
pytest -v
```

### Chạy test Frontend:
```bash
cd app
flutter test
```
