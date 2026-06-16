# CHƯƠNG 2. TỔNG QUAN TÀI LIỆU VÀ CƠ SỞ LÝ THUYẾT

## 2.1. Tổng quan lĩnh vực và thị trường liên quan

### 2.1.1. Xu hướng phát triển của Trí tuệ Nhân tạo hội thoại (Conversational AI)
Trí tuệ nhân tạo hội thoại (Conversational AI) đã trải qua nhiều giai đoạn phát triển quan trọng, từ các hệ thống dựa trên luật (rule-based) đơn giản đến các trợ lý ảo sử dụng mô hình học máy và gần đây nhất là kỷ nguyên của các Mô hình Ngôn ngữ Lớn (LLM - Large Language Models). 

Trong giai đoạn đầu, các trợ lý như Siri (Apple), Google Assistant hay Alexa (Amazon) đã mở ra khái niệm giao tiếp với máy tính bằng giọng nói. Tuy nhiên, các hệ thống này thường hoạt động theo các kịch bản cứng nhắc hoặc các lệnh đơn lẻ ("hẹn giờ", "mở nhạc", "hỏi thời tiết"). Chúng gặp khó khăn lớn trong việc duy trì ngữ cảnh của cuộc trò chuyện kéo dài và hoàn toàn không có khả năng tự động học hỏi hoặc nhớ lại các chi tiết cá nhân một cách thông minh nếu không được lập trình sẵn trong cơ sở dữ liệu.

Sự xuất hiện của các kiến trúc Transformer và các LLM như GPT-4, Gemini, Claude đã thay đổi hoàn toàn cục diện này. Khả năng hiểu ngôn ngữ tự nhiên (NLU - Natural Language Understanding) và tạo lập văn bản (NLG - Natural Language Generation) của máy tính đã tiệm cận mức độ của con người. Trợ lý AI hiện nay không chỉ hiểu lệnh mà còn hiểu được cảm xúc, ẩn ý và có khả năng suy luận logic phức tạp. Xuuyên hướng công nghệ năm 2026 hướng tới các hệ thống AI hội thoại có độ trễ cực thấp, giọng nói tự nhiên biểu cảm, và đặc biệt là hệ thống bộ nhớ động cá nhân hóa (Personalized Dynamic Memory) giúp trợ lý thực sự hiểu sâu sắc về thói quen, sở thích và thông tin của từng người dùng cụ thể.

### 2.1.2. Thị trường Quản lý tri thức cá nhân (Personal Knowledge Management - PKM)
Quản lý tri thức cá nhân (PKM) là quy trình thu thập, phân loại, lưu trữ, tìm kiếm và chia sẻ tri thức của một cá nhân để phục vụ cho công việc và cuộc sống. Thị trường các ứng dụng PKM đang chứng kiến sự tăng trưởng mạnh mẽ do nhu cầu làm việc từ xa, học tập suốt đời và áp lực xử lý thông tin ngày càng tăng.

Các ứng dụng PKM hiện đại có thể chia làm ba thế hệ chính:
1.  **Thế hệ thứ nhất (Folder-based):** Tiêu biểu là Evernote, OneNote. Lưu trữ thông tin dưới dạng các tệp tin và thư mục phân cấp tuyến tính. Rất dễ sử dụng ban đầu nhưng nhanh chóng trở nên lộn xộn và khó tìm kiếm khi khối lượng ghi chép tăng lên.
2.  **Thế hệ thứ hai (Graph-based & Bi-directional linking):** Tiêu biểu là Obsidian, Roam Research. Sử dụng liên kết hai chiều để kết nối các ghi chú lại với nhau, tạo ra một mạng lưới tri thức (knowledge graph) tương tự như cách bộ não con người hoạt động. Tuy nhiên, thế hệ này đòi hỏi người dùng có kỹ năng tổ chức cao và tốn rất nhiều công sức để tự liên kết thủ công.
3.  **Thế hệ thứ ba (AI-powered):** Tiêu biểu là Notion AI, Mem.ai. Tích hợp AI để hỗ trợ tóm tắt văn bản, viết lách, và tìm kiếm thông minh.

Mặc dù các ứng dụng PKM thế hệ thứ ba đã rất thông minh, chúng vẫn là các hệ thống **"Text-First"** - tức là lấy văn bản nhập từ bàn phím làm trung tâm. Rất ít ứng dụng tập trung giải quyết bài toán **"Voice-First"** một cách triệt để, tức là cho phép người dùng xây dựng và truy hồi "Second Brain" của họ hoàn toàn bằng giọng nói một cách tự nhiên và liền mạch.

### 2.1.3. Khoảng trống thị trường và Cơ hội khởi nghiệp
Khoảng trống thị trường lớn nhất hiện nay nằm ở giao điểm giữa **Trí tuệ Nhân tạo hội thoại** và **Quản lý tri thức cá nhân bằng giọng nói**:
*   **Trợ lý ảo thông dụng** (Siri, Google Assistant) thì thiếu bộ nhớ dài hạn cá nhân hóa sâu sắc và không tập trung vào tính năng ghi chép/quản lý tri thức.
*   **Ứng dụng ghi chú** (Notion, Obsidian) thì quá phức tạp để nhập liệu bằng giọng nói khi đang di chuyển và thiếu đi khả năng phản hồi chủ động bằng giọng nói (Voice feedback).

Đây là cơ hội vàng cho sản phẩm **VocalMind**. Bằng cách cung cấp một giao diện hoàn toàn bằng giọng nói, kết hợp với bộ nhớ dài hạn thông minh dạng đồ thị (được hỗ trợ bởi Mem0), VocalMind giải quyết bài toán nhập liệu rảnh tay và quản lý thông tin chủ động. Người dùng có thể nói "Minh nợ tôi 60 nghìn đồng", và vài ngày sau chỉ cần hỏi "Có ai nợ tiền tôi không?" thì hệ thống sẽ truy xuất chính xác thông tin từ bộ nhớ dài hạn và trả lời bằng giọng nói tự nhiên của Vieneu TTS. Đây chính là điểm cốt lõi tạo nên giá trị đổi mới sáng tạo và lợi thế cạnh tranh của sản phẩm trên thị trường công nghệ số.
