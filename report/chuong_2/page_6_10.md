## 2.2. Khảo sát nhu cầu người dùng và so sánh các giải pháp liên quan

### 2.2.1. Khảo sát nhu cầu thực tế của người dùng hiện đại
Nhằm đánh giá hành vi và khó khăn của người dùng trong việc quản lý tri thức cá nhân, nhóm nghiên cứu đã thực hiện khảo sát trực tuyến với quy mô 200 đáp viên (độ tuổi từ 18 đến 45 tuổi, chủ yếu là sinh viên, lập trình viên, nhà nghiên cứu và quản lý doanh nghiệp). Kết quả thu được chỉ ra những điểm nghẽn lớn (pain points) trong thói quen ghi chú hằng ngày:

*   **78.5%** đáp viên thừa nhận họ thường xuyên quên mất các ý tưởng sáng tạo nảy ra bất chợt do không tiện mở điện thoại hoặc sổ tay để ghi chép ngay tại thời điểm đó.
*   **62%** đáp viên cảm thấy phiền phức khi phải mở các ứng dụng như Notion hoặc Obsidian trên điện thoại vì thời gian tải ứng dụng lâu và cấu trúc phân mục phức tạp khiến việc lưu trữ một thông tin ngắn mất nhiều thao tác.
*   **54.5%** đáp viên mong muốn có một ứng dụng hỗ trợ ra lệnh bằng giọng nói tiếng Việt nhưng có khả năng hiểu ngữ nghĩa thay vì chỉ ghi nhận nguyên văn (transcription) dạng thô.
*   **83%** đáp viên mong muốn ứng dụng ghi chú của họ có thể tự động liên kết các mẩu thông tin rời rạc (ví dụ: liên kết lịch hẹn công việc với thông tin liên hệ của một người) mà không cần họ phải tự tạo liên kết thủ công.

Kết quả khảo sát này khẳng định nhu cầu cấp thiết về một giải pháp ghi chú tối giản, hỗ trợ giọng nói tiếng Việt mượt mà và tích hợp cơ chế quản lý trí nhớ tự động.

---

### 2.2.2. So sánh ưu nhược điểm của các giải pháp hiện tại
Để làm rõ giá trị nổi bật của VocalMind, nhóm nghiên cứu tiến hành phân tích và đối chiếu dự án với 3 nhóm giải pháp quản lý tri thức và trợ lý ảo phổ biến hiện nay dựa trên 5 tiêu chí kỹ thuật cốt lõi:

#### 2.2.2.1. Nhóm 1: Trợ lý ảo truyền thống thương mại (Siri, Google Assistant, Alexa)
Các trợ lý ảo này được phát triển bởi các tập đoàn công nghệ lớn, tích hợp sâu vào hệ điều hành di động hoặc thiết bị IoT gia đình.
*   **Phương thức nhập liệu:** Sử dụng giọng nói (Voice-first) làm chủ đạo, hỗ trợ kích hoạt rảnh tay bằng câu lệnh thoại.
*   **Khả năng hỗ trợ Tiếng Việt:** Google Assistant hỗ trợ khá tốt; Siri đã hỗ trợ nhưng khả năng nhận diện các câu thoại tiếng Việt phức tạp còn nhiều hạn chế.
*   **Bộ nhớ dài hạn (Long-term memory):** Không hỗ trợ. Các trợ lý này không lưu giữ ngữ cảnh hội thoại dài hạn hoặc liên kết giữa các thông tin trao đổi từ trước đó.
*   **Khả năng tự động suy luận:** Rất thấp, hoạt động dựa trên các kịch bản cứng nhắc hoặc thực hiện truy vấn tìm kiếm trực tiếp trên Internet.
*   **Mức độ ma sát thao tác:** Thấp, người dùng chỉ cần gọi tên trợ lý và ra lệnh.
*   **Hạn chế cốt lõi:** Không được thiết kế cho việc quản lý tri thức hay ghi chú cá nhân, thông tin lưu trữ bị phân tán và không có cấu trúc liên kết.

#### 2.2.2.2. Nhóm 2: Ứng dụng ghi chú tĩnh truyền thống (Notion, Obsidian, Evernote)
Đây là các công cụ ghi chú mạnh mẽ và được sử dụng rộng rãi nhất trên máy tính để bàn để xây dựng cơ sở tri thức cá nhân.
*   **Phương thức nhập liệu:** Lấy văn bản làm trung tâm (Text-first). Việc nhập liệu hoàn toàn phụ thuộc vào việc gõ bàn phím.
*   **Khả năng hỗ trợ Tiếng Việt:** Tốt thông qua việc hiển thị ký tự Unicode tiêu chuẩn trên giao diện.
*   **Bộ nhớ dài hạn (Long-term memory):** Có bộ nhớ tĩnh. Tuy nhiên, việc tổ chức, phân mục và liên kết các ghi chú hoàn toàn do người dùng tự xây dựng thủ công bằng cây thư mục hoặc liên kết hai chiều.
*   **Khả năng tự động suy luận:** Không hỗ trợ. Hệ thống không hiểu nội dung lưu trữ bên trong các tệp văn bản.
*   **Mức độ ma sát thao tác:** Rất cao trên di động. Việc mở ứng dụng, chọn mục lưu trữ, tạo file mới và gõ chữ tốn nhiều thời gian và thao tác.
*   **Hạn chế cốt lõi:** Ma sát gõ phím quá lớn trên điện thoại di động làm cản trở việc ghi chép nhanh các ý tưởng bất chợt.

#### 2.2.2.3. Nhóm 3: Trợ lý ghi chú tích hợp trí tuệ nhân tạo (Mem.ai, Notion AI, Evernote AI)
Các ứng dụng ghi chú thế hệ mới được trang bị thêm các tính năng LLM để hỗ trợ tóm tắt, tìm kiếm và viết lách.
*   **Phương thức nhập liệu:** Vẫn là hướng văn bản (Text-first). Mặc dù có hỗ trợ ghi âm nhưng chỉ dừng lại ở mức chuyển băng âm thanh sang chữ thô (transcription), không có tương tác đối thoại giọng nói hai chiều.
*   **Khả năng hỗ trợ Tiếng Việt:** Hạn chế hoặc trung bình. Các dịch vụ này tối ưu chủ yếu cho tiếng Anh, khi xử lý tiếng Việt thường gặp lỗi diễn đạt hoặc không hiểu thấu đáo các thuật ngữ bản địa.
*   **Bộ nhớ dài hạn (Long-term memory):** Tốt. AI hỗ trợ tìm kiếm ngữ nghĩa (semantic search) trên toàn bộ kho tài liệu văn bản đã lưu.
*   **Khả năng tự động suy luận:** Trung bình, hỗ trợ tóm tắt văn bản và đưa ra gợi ý liên kết các tài liệu tương đồng.
*   **Mức độ ma sát thao tác:** Trung bình, người dùng vẫn phải mở ứng dụng và nhập các câu lệnh (prompts) dạng chữ cho AI.
*   **Hạn chế cốt lõi:** Giá thành dịch vụ cao, độ trễ phản hồi lớn do máy chủ đặt ở nước ngoài và thiếu đi giao diện hội thoại bằng giọng nói tự nhiên.

#### 2.2.2.4. Giải pháp đề xuất: Hệ thống trợ lý giọng nói thông minh VocalMind
VocalMind định hình một hướng tiếp cận kết hợp tối ưu giữa tương tác thoại và quản lý tri thức.
*   **Phương thức nhập liệu:** Hoàn toàn hướng giọng nói (Voice-first). Một chạm để nói và lắng nghe trợ lý phản hồi bằng âm thanh.
*   **Khả năng hỗ trợ Tiếng Việt:** Xuất sắc nhờ tích hợp bộ đôi mô hình AI chuyên biệt cho tiếng Việt: Qwen ASR nhận dạng giọng nói và Vieneu TTS tổng hợp giọng nói tự nhiên.
*   **Bộ nhớ dài hạn (Long-term memory):** Xuất sắc. Tự động hóa việc xây dựng Đồ thị ký ức (Memory Graph) để liên kết thông tin.
*   **Khả năng tự động suy luận:** Cao nhờ sử dụng lõi Mem0 để trích xuất các thực thể, mối quan hệ và tự động giải quyết xung đột thông tin.
*   **Mức độ ma sát thao tác:** Cực kỳ thấp. Trải nghiệm một chạm đơn giản, hoàn toàn phù hợp để sử dụng khi đang di chuyển hoặc làm các công việc khác.

---

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
