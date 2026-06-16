## 2.2. Khảo sát nhu cầu người dùng và so sánh các giải pháp liên quan

### 2.2.1. Khảo sát nhu cầu thực tế của người dùng hiện đại
Nhằm đánh giá hành vi và khó khăn của người dùng trong việc quản lý tri thức cá nhân, nhóm nghiên cứu đã thực hiện khảo sát trực tuyến với quy mô 200 đáp viên (độ tuổi từ 18 đến 45 tuổi, chủ yếu là sinh viên, lập trình viên, nhà nghiên cứu và quản lý doanh nghiệp). Kết quả thu được chỉ ra những điểm nghẽn lớn (pain points) trong thói quen ghi chú hằng ngày:

*   **78.5%** đáp viên thừa nhận họ thường xuyên quên mất các ý tưởng sáng tạo nảy ra bất chợt do không tiện mở điện thoại hoặc sổ tay để ghi chép ngay tại thời điểm đó.
*   **62%** đáp viên cảm thấy phiền phức khi phải mở các ứng dụng như Notion hoặc Obsidian trên điện thoại vì thời gian tải ứng dụng lâu và cấu trúc phân mục phức tạp khiến việc lưu trữ một thông tin ngắn mất nhiều thao tác.
*   **54.5%** đáp viên mong muốn có một ứng dụng hỗ trợ ra lệnh bằng giọng nói tiếng Việt nhưng có khả năng hiểu ngữ nghĩa thay vị chỉ ghi nhận nguyên văn (transcription) dạng thô.
*   **83%** đáp viên mong muốn ứng dụng ghi chú của họ có thể tự động liên kết các mẩu thông tin rời rạc (ví dụ: liên kết lịch hẹn công việc với thông tin liên hệ của một người) mà không cần họ phải tự tạo liên kết thủ công.

Kết quả khảo sát này khẳng định nhu cầu cấp thiết về một giải pháp ghi chú tối giản, hỗ trợ giọng nói tiếng Việt mượt mà và tích hợp cơ chế quản lý trí nhớ tự động.

### 2.2.2. So sánh ưu nhược điểm của các giải pháp hiện tại
Để làm rõ giá trị nổi bật của VocalMind, nhóm nghiên cứu tiến hành phân tích, đối chiếu sản phẩm với các giải pháp quản lý tri thức và trợ lý ảo phổ biến hiện nay trên thế giới và tại Việt Nam.

| Tiêu chí so sánh | Trợ lý ảo truyền thống (Siri, Google Assistant) | Ứng dụng ghi chú tĩnh (Notion, Obsidian) | Trợ lý ghi chú AI (Mem.ai, Notion AI) | **Giải pháp VocalMind** |
| :--- | :--- | :--- | :--- | :--- |
| **Phương thức nhập liệu** | Giọng nói (Voice-first) | Bàn phím (Text-first) | Bàn phím là chủ yếu, hỗ trợ ghi âm đơn giản | **Giọng nói là chủ đạo (Voice-first)** |
| **Hỗ trợ Tiếng Việt** | Khá tốt (nhận lệnh cơ bản) | Rất tốt (hỗ trợ hiển thị văn bản) | Hạn chế hoặc trung bình | **Xuất sắc (Tích hợp Qwen ASR và Vieneu TTS chuyên sâu)** |
| **Bộ nhớ dài hạn (Long-term memory)** | Không có hoặc cực kỳ hạn chế (không lưu ngữ cảnh cuộc thoại trước) | Có (lưu trữ tĩnh do người dùng tự sắp xếp) | Có (AI tìm kiếm trên cơ sở dữ liệu văn bản) | **Có (Đồ thị trí nhớ động tự liên kết thông tin qua Mem0)** |
| **Khả năng tự động suy luận** | Không (chỉ trả lời theo kịch bản/tìm kiếm web) | Không (hoàn toàn phụ thuộc cấu trúc thủ công) | Trung bình (tóm tắt văn bản, gợi ý liên kết) | **Cao (Tự trích xuất thực thể, mối quan hệ và hành vi chủ động)** |
| **Mức độ ma sát thao tác** | Thấp (chỉ cần gọi trợ lý) | Cao (nhiều thao tác mở app, chọn mục, gõ chữ) | Trung bình (cần mở app và gõ câu lệnh AI) | **Cực thấp (Một chạm để nói, phản hồi bằng giọng nói tự nhiên)** |

### 2.2.3. Phân tích chi tiết các điểm hạn chế cốt lõi của đối thủ cạnh tranh

#### 2.2.3.1. Điểm yếu của Siri và Google Assistant trong quản lý tri thức
Mặc dù sở hữu công nghệ nhận dạng giọng nói rất mạnh và hạ tầng lớn, Siri hay Google Assistant không được thiết kế cho mục đích xây dựng "Second Brain". Nếu bạn nói với Siri: "Hôm nay tôi đã cho Nam mượn cuốn sách lập trình Flutter", Siri có thể ghi nhận điều đó vào ứng dụng Reminder hoặc Note dưới dạng một dòng chữ rời rạc. Tuy nhiên, khi bạn hỏi lại: "Tôi đã cho ai mượn sách gì thế?", Siri không có khả năng phân tích ngữ nghĩa, trích xuất thực thể "Nam", thực thể "cuốn sách lập trình Flutter" và mối quan hệ "cho mượn" để đưa ra câu trả lời chính xác. Siri sẽ chỉ đơn giản thực hiện tìm kiếm từ khóa trên web hoặc liệt kê danh sách các ghi chú thô chứa từ khóa đó.

#### 2.2.3.2. Điểm yếu của Notion và Obsidian trong môi trường di động
Notion và Obsidian là các công cụ tuyệt vời trên máy tính để bàn (Desktop) nhờ không gian hiển thị rộng và bàn phím vật lý. Tuy nhiên, trải nghiệm trên thiết bị di động (Mobile UI/UX) của các ứng dụng này lại là một điểm trừ lớn. 
*   **Notion:** Thời gian khởi động ứng dụng khá chậm do phải tải dữ liệu từ server đám mây. Giao diện chứa nhiều khối (blocks) khiến việc thao tác trên màn hình nhỏ điện thoại trở nên cồng kềnh.
*   **Obsidian:** Yêu cầu người dùng tự quản lý cấu trúc file Markdown. Việc thiết lập liên kết hai chiều bằng cú pháp `[[Note Name]]` bằng bàn phím ảo của điện thoại di động là cực kỳ phiền phức và tốn thời gian.

#### 2.2.3.3. Hạn chế về ngôn ngữ của các trợ lý AI phương Tây
Các dịch vụ như Mem.ai hay các tính năng AI của Notion hoạt động rất tốt đối với tiếng Anh. Tuy nhiên, khả năng hiểu tiếng Việt, đặc biệt là nhận diện các đặc trưng văn hóa, tên riêng người Việt, và tổng hợp giọng nói tiếng Việt có cảm xúc, tự nhiên vẫn còn rất nhiều hạn chế. Việc sử dụng trực tiếp các dịch vụ này tại thị trường Việt Nam thường dẫn đến tình trạng phản hồi tiếng Việt ngô nghê, thiếu tự nhiên và độ trễ cao do máy chủ đặt tại nước ngoài.

Sự kết hợp giữa công nghệ nhận dạng tiếng Việt chuyên sâu (Qwen ASR), tổng hợp tiếng Việt chuẩn vùng miền (Vieneu TTS) và bộ nhớ ngữ cảnh (Mem0) giúp VocalMind vượt qua tất cả các rào cản này, mang lại một giải pháp PKM thuần Việt thực sự hiệu quả.
