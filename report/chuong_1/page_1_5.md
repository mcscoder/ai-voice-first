# CHƯƠNG 1. GIỚI THIỆU ĐỀ TÀI

## 1.1. Lý do chọn đề tài (Motivation)

### 1.1.1. Bối cảnh chuyển đổi số và sự bùng nổ của Trí tuệ Nhân tạo
Trong kỷ nguyên chuyển đổi số toàn cầu và sự phát triển vượt bậc của cuộc Cách mạng Công nghiệp 4.0, dữ liệu và tri thức cá nhân đang gia tăng với tốc độ chóng mặt. Mỗi cá nhân hằng ngày phải tiếp nhận, xử lý và lưu trữ một lượng lớn thông tin từ công việc, học tập đến các mối quan hệ xã hội và kế hoạch cá nhân. Việc quản lý hiệu quả nguồn tri thức này trở thành một yếu tố quyết định năng suất làm việc và chất lượng cuộc sống của mỗi người. 

Song song với đó, Trí tuệ Nhân tạo (AI), đặc biệt là các Mô hình Ngôn ngữ Lớn (LLM) và các công nghệ xử lý giọng nói như Nhận dạng giọng nói (ASR - Automatic Speech Recognition), Tổng hợp giọng nói (TTS - Text-to-Speech), đang định hình lại cách thức con người tương tác với máy tính. Giao diện người dùng bằng giọng nói (VUI - Voice User Interface) đang dần thay thế hoặc bổ trợ mạnh mẽ cho các giao diện đồ họa truyền thống (GUI), mang lại trải nghiệm tự nhiên, rảnh tay (hands-free) và cá nhân hóa sâu sắc.

### 1.1.2. Hạn chế của các giải pháp quản lý tri thức truyền thống
Hiện nay, trên thị trường có rất nhiều công cụ quản lý tri thức cá nhân (PKM - Personal Knowledge Management) nổi tiếng như Notion, Obsidian, Evernote hay Google Keep. Tuy nhiên, các ứng dụng này vẫn tồn tại những rào cản lớn đối với người dùng:
1.  **Ma sát nhập liệu cao (High Input Friction):** Người dùng bắt buộc phải mở ứng dụng, gõ bàn phím để ghi lại thông tin. Điều này tốn thời gian và làm gián đoạn mạch tư duy hoặc các hoạt động thực tế (như đang di chuyển trên đường, đang nấu ăn, hoặc đang họp).
2.  **Khó ghi nhận ý tưởng thoáng qua (Fleeting Thoughts):** Những ý tưởng sáng tạo hay thông tin cần nhớ thường xuất hiện bất chợt và biến mất rất nhanh. Nếu quy trình mở app và gõ chữ quá phức tạp, người dùng sẽ có xu hướng bỏ qua, dẫn đến thất thoát tri thức.
3.  **Thiếu tính chủ động và suy luận:** Các ứng dụng ghi chú truyền thống chỉ hoạt động như một kho lưu trữ tĩnh ("nhớ hộ"). Chúng không hiểu được ngữ nghĩa sâu xa của ghi chú, không tự động liên kết các ký ức liên quan và không thể nhắc nhở người dùng một cách thông minh dựa trên ngữ cảnh thực tế.

### 1.1.3. Nhu cầu về giải pháp Voice-First và Trí nhớ thứ hai (Second Brain)
Để giải quyết triệt để các hạn chế trên, nhu cầu về một hệ thống "Second Brain" hướng giọng nói (Voice-First) là vô cùng cấp thiết. Hệ thống này cần phải:
*   Cho phép ghi chép nhanh chóng chỉ bằng cách nói.
*   Hiểu được nội dung nói bằng ngôn ngữ tự nhiên để tự động phân loại, tổ chức thông tin.
*   Xây dựng một đồ thị ký ức (Memory Graph) để liên kết các thông tin rời rạc theo thời gian, mối quan hệ và chủ đề.
*   Phản hồi lại người dùng bằng giọng nói tự nhiên, tạo cảm giác như đang trò chuyện với một trợ lý con người.

Chính vì những lý do trên, nhóm tác giả quyết định thực hiện đề tài: **"VocalMind: Hệ thống trợ lý ghi nhớ thông minh bằng giọng nói (Voice-First Personal Knowledge Management & Second Brain)"**. Đề tài không chỉ giải quyết bài toán kỹ thuật mà còn hướng đến việc xây dựng một sản phẩm khởi nghiệp đổi mới sáng tạo tiềm năng trong năm 2026.

---

## 1.2. Mục tiêu đề tài (Objectives & Contributions)

### 1.2.1. Mục tiêu tổng quát
Mục tiêu tổng quát của đề tài là nghiên cứu, thiết kế và xây dựng thành công giải pháp trợ lý ghi nhớ cá nhân thông minh hoạt động theo cơ chế hướng giọng nói (Voice-First). Sản phẩm cuối cùng là một hệ thống hoàn chỉnh gồm ứng dụng di động (Client) và hệ thống máy chủ dịch vụ AI (Backend), có khả năng ứng dụng thực tế cao và định hướng thương mại hóa theo mô hình sản phẩm dịch vụ số (SaaS).

### 1.2.2. Mục tiêu cụ thể
Để đạt được mục tiêu tổng quát, đề tài tập trung giải quyết các mục tiêu cụ thể sau:
1.  **Phân tích bài toán PKM:** Nghiên cứu hành vi ghi chép và nhu cầu ghi nhớ của người dùng hiện đại để xác định các tính năng cốt lõi.
2.  **Thiết kế và xây dựng hệ thống Client-Server:** 
    *   Phát triển ứng dụng di động đa nền tảng bằng **Flutter** với giao diện UI tối giản, trực quan, tối ưu cho các thao tác chạm và nói.
    *   Xây dựng hệ thống máy chủ hiệu năng cao bằng **FastAPI** (Python) hỗ trợ xử lý dữ liệu âm thanh và kết nối các dịch vụ AI một cách nhanh chóng.
3.  **Tích hợp công nghệ AI tiên tiến:**
    *   Tích hợp mô hình **Qwen ASR** chuyển đổi giọng nói tiếng Việt/Anh sang văn bản với độ chính xác cao.
    *   Tích hợp mô hình **Vieneu TTS** chuyển đổi văn bản câu trả lời thành giọng nói tiếng Việt tự nhiên, truyền cảm.
    *   Ứng dụng thư viện quản lý trí nhớ **Mem0** để lưu trữ thông tin dưới dạng đồ thị tri thức, tự động cập nhật và suy luận ngữ cảnh dựa trên lịch sử trò chuyện.
4.  **Thử nghiệm và tối ưu hóa:** Đo lường các chỉ số hiệu năng kỹ thuật như thời gian xử lý phản hồi (end-to-end latency) và độ chính xác của mô hình để đảm bảo trải nghiệm người dùng liền mạch.
5.  **Xây dựng mô hình kinh doanh khởi nghiệp:** Đề xuất mô hình kinh doanh Canvas (Business Model Canvas) và chiến lược tiếp cận thị trường (Go-To-Market) cho sản phẩm VocalMind.

---

## 1.3. Đối tượng và Phạm vi đề tài (Scopes)

### 1.3.1. Đối tượng nghiên cứu và đối tượng người dùng
*   **Đối tượng nghiên cứu:** Các công nghệ nhận dạng giọng nói (ASR), tổng hợp giọng nói (TTS), kiến trúc mô hình ngôn ngữ lớn (LLM), các giải pháp lưu trữ trí nhớ ngữ cảnh (Contextual Memory Systems) và quy trình thiết kế ứng dụng Voice-First.
*   **Đối tượng người dùng mục tiêu:** 
    *   Nhân viên văn phòng, quản lý dự án thường xuyên phải xử lý thông tin và họp hành.
    *   Nhà sáng tạo nội dung, nhà văn, nhà nghiên cứu cần ghi lại ý tưởng nhanh chóng.
    *   Những người bận rộn muốn quản lý tài chính cá nhân, mối quan hệ và nhắc nhở rảnh tay.

### 1.3.2. Phạm vi công nghệ
Hệ thống VocalMind được xây dựng và vận hành dựa trên các công nghệ cụ thể trong bảng dưới đây:

| Thành phần | Công nghệ lựa chọn | Vai trò trong hệ thống |
| :--- | :--- | :--- |
| **Frontend Mobile App** | Flutter (Dart) | Xây dựng giao diện người dùng di động, quản lý ghi âm và phát âm thanh phản hồi. |
| **State Management** | Hydrated BLoC (Cubit) | Quản lý trạng thái ứng dụng và tự động lưu giữ cấu hình người dùng offline. |
| **Backend API Server** | FastAPI (Python) | Cung cấp các RESTful API endpoints không đồng bộ, xử lý logic luồng và định tuyến dữ liệu. |
| **ASR Engine** | Qwen ASR (`Qwen3ASRModel`) | Nhận dạng âm thanh tải lên và chuyển dịch thành văn bản tiếng Việt/Anh. |
| **TTS Engine** | Vieneu TTS (`Vieneu` SDK) | Tổng hợp câu trả lời dạng chữ thành âm thanh dạng WAV. |
| **Memory Engine** | Mem0 (`mem0ai`) | Quản lý trí nhớ dài hạn/ngắn hạn của người dùng, lưu trữ vector ngữ cảnh và cập nhật tri thức hội thoại. |
| **LLM Provider** | DeepSeek (`deepseek-v4-flash`) | Sinh phản hồi hội thoại ngắn gọn dựa trên prompt ngữ cảnh từ Mem0. |

### 1.3.3. Giới hạn hệ thống và môi trường triển khai
*   **Ngôn ngữ hỗ trợ:** Tập trung tối ưu cho tiếng Việt và tiếng Anh.
*   **Môi trường mạng:** Đòi hỏi kết nối Internet để truyền tải dữ liệu âm thanh giữa Client và Server (do các mô hình AI chạy tập trung trên server để đảm bảo hiệu năng).
*   **Môi trường triển khai:** Backend chạy trên môi trường Linux Ubuntu hỗ trợ GPU CUDA; ứng dụng di động chạy tốt trên hệ điều hành Android và iOS.

---

## 1.4. Ý nghĩa thực tiễn của đề tài

### 1.4.1. Giải quyết vấn đề thực tế của đời sống
VocalMind giải phóng đôi tay và đôi mắt của người dùng khỏi màn hình điện thoại khi cần ghi chép. Ứng dụng giúp giảm thiểu "ma sát nhận thức" (cognitive friction), khuyến khích mọi người lưu trữ tri thức cá nhân nhiều hơn và có hệ thống hơn. Việc lưu lại thông tin tài chính (nợ nần), các mối quan hệ (sinh nhật, sở thích bạn bè) giúp người dùng quản lý cuộc sống khoa học và tránh được các sai sót đáng tiếc do hay quên.

### 1.4.2. Khả năng triển khai và mở rộng thương mại (Startup Potential)
Sản phẩm sở hữu tiềm năng khởi nghiệp đổi mới sáng tạo rất lớn nhờ tính độc đáo và công nghệ hiện đại:
*   **Tính linh hoạt cao:** Backend hướng dịch vụ giúp dễ dàng thay thế hoặc nâng cấp các mô hình AI (ASR, TTS, LLM) khi có công nghệ mới tốt hơn mà không ảnh hưởng tới ứng dụng di động.
*   **Khả năng nhân rộng (Scalability):** Có thể đóng gói backend dưới dạng Docker container và triển khai lên các dịch vụ đám mây (AWS, Google Cloud) để phục vụ hàng triệu người dùng cùng lúc.
*   **Mô hình kinh doanh khả thi:** Dễ dàng triển khai mô hình B2C (trợ lý cá nhân trả phí tháng) hoặc B2B (tích hợp trợ lý giọng nói vào hệ thống nội bộ của doanh nghiệp để ghi biên bản cuộc họp tự động).
