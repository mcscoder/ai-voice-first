# TÓM TẮT ĐỀ TÀI (EXECUTIVE SUMMARY)

## 1. Tóm tắt đề tài (Summary)
Đề tài **VocalMind** xây dựng một hệ thống trợ lý ghi nhớ thông minh hướng giọng nói (Voice-first Personal Knowledge Management) hoạt động như một "Trí óc thứ hai" (Second Brain) cho người dùng. Khác với các ứng dụng ghi chú truyền thống bằng văn bản vốn đòi hỏi thao tác nhập liệu phức tạp bằng bàn phím, VocalMind cho phép người dùng tương tác hoàn toàn bằng giọng nói tự nhiên thông qua ứng dụng di động Flutter. Backend của hệ thống được xây dựng trên nền tảng FastAPI (Python), tích hợp các mô hình học sâu tiên tiến bao gồm **Qwen ASR** cho nhận dạng giọng nói, **Vieneu** cho tổng hợp giọng nói tiếng Việt tự nhiên và **Mem0** làm lõi quản lý ký ức hội thoại dạng đồ thị (Memory Graph). Hệ thống có khả năng tự động trích xuất thông tin, tổ chức và liên kết các ký ức theo thời gian và ngữ cảnh, hỗ trợ nhắc nhở chủ động và phản hồi hội thoại thông minh.

## 2. Phương pháp nghiên cứu (Methodology)
Nghiên cứu được triển khai theo quy trình phát triển sản phẩm Agile/Scrum kết hợp tư duy khởi nghiệp tinh gọn (Lean Startup). Các phương pháp chính bao gồm:
*   **Khảo sát và Phân tích Yêu cầu:** Phân tích ma sát trong quy trình quản lý tri thức cá nhân (PKM) hiện tại và lập biểu đồ hành trình khách hàng.
*   **Thiết kế Kiến trúc Hệ thống:** Áp dụng mô hình Client-Server hướng dịch vụ microservices nhẹ, giao tiếp qua RESTful API không đồng bộ (Async API).
*   **Tích hợp Trí tuệ Nhân tạo:** Sử dụng học máy chuyển giao (Transfer Learning) và mô hình ngôn ngữ lớn (LLM) thông qua thư viện Mem0 để xây dựng bộ nhớ có ngữ cảnh.
*   **Thử nghiệm và Đánh giá:** Đánh giá hiệu năng dựa trên độ trễ phản hồi (latency), độ chính xác của ASR (Word Error Rate - WER) và khảo sát sự hài lòng của người dùng cuối.

## 3. Các kết quả chính đạt được (Findings)
*   **Ứng dụng Di động:** Phát triển thành công ứng dụng Flutter với giao diện tối giản, tối ưu hóa cho tương tác giọng nói, sử dụng Cubit làm giải pháp quản lý trạng thái mượt mà.
*   **Hệ thống Backend:** Xây dựng hệ thống FastAPI có khả năng xử lý luồng âm thanh đa phương tiện (qua PyAV), tích hợp mô hình nhận dạng tiếng Việt Qwen ASR và tổng hợp giọng nói Vieneu với thời gian phản hồi dưới 2.5 giây.
*   **Công nghệ Trí nhớ thông minh:** Ứng dụng thành công Mem0 để ghi nhận ký ức người dùng một cách nhất quán, có khả năng tự động suy luận và liên kết các sự kiện liên quan (nợ nần, kế hoạch, mối quan hệ).

## 4. Đề xuất và Định hướng Khởi nghiệp (Recommendations)
*   **Định hướng Thương mại hóa:** Triển khai sản phẩm theo mô hình SaaS (Software as a Service) với hai phiên bản: Miễn phí (giới hạn dung lượng bộ nhớ) và Trả phí (bộ nhớ không giới hạn, tùy chỉnh tính cách trợ lý, đồng bộ hóa đa thiết bị).
*   **Kế hoạch Phát triển:** Tối ưu hóa mô hình AI để chạy offline (Edge AI) giúp bảo vệ quyền riêng tư tuyệt đối cho người dùng, và tích hợp các thiết bị đeo thông minh (wearables).
