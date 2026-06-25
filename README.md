# Hệ thống học Lịch sử Việt Nam bằng Hybrid GraphRAG

## 1. Giới thiệu dự án

Đây là project xây dựng chatbot hỗ trợ học tập và tra cứu kiến thức Lịch sử Việt Nam. Hệ thống cho phép người dùng nhập câu hỏi bằng ngôn ngữ tự nhiên, sau đó trả lời dựa trên dữ liệu lịch sử đã được xử lý từ tài liệu văn bản, PDF và đồ thị tri thức.

Dự án sử dụng mô hình Hybrid GraphRAG, kết hợp hai hướng truy xuất dữ liệu:

- **Vector Search**: tìm các đoạn văn bản lịch sử có nội dung gần nghĩa với câu hỏi của người dùng.
- **Knowledge Graph**: truy vấn các thực thể và mối quan hệ lịch sử trong Neo4j bằng Cypher.

Nhờ sự kết hợp này, hệ thống có thể vừa khai thác ngữ cảnh từ văn bản, vừa phân tích được quan hệ giữa các nhân vật, sự kiện, tổ chức và địa danh lịch sử.

Các thành phần chính của project:

- `src/app.py`: giao diện web bằng Streamlit và luồng xử lý hỏi đáp chính.
- `src/chatbot.py`: phiên bản chatbot chạy trên terminal.
- `scripts/`: các script phục vụ xử lý dữ liệu, trích xuất đồ thị, import dữ liệu vào Neo4j và tạo vector index.
- `data/`: chứa dữ liệu thô, dữ liệu đã chia chunk và dữ liệu đồ thị đã trích xuất.
- `requirements.txt`: danh sách thư viện Python cần cài đặt.

Công nghệ sử dụng:

- Python
- Streamlit
- Neo4j
- LangChain
- OpenAI Chat Model
- OpenAI Embeddings
- Neo4j Vector Index

## 2. Hướng dẫn cài đặt và chạy chương trình

### 2.1. Yêu cầu môi trường

Trước khi chạy chương trình, cần cài đặt:

- Python 3.10 trở lên
- Neo4j
- Tài khoản/API key OpenAI
- Git hoặc công cụ tải mã nguồn project

### 2.2. Cài đặt thư viện

Mở terminal tại thư mục gốc của project:

```bash
cd D:\HistoryChatbot
```

Tạo môi trường ảo:

```bash
python -m venv .venv
```

Kích hoạt môi trường ảo trên Windows:

```bash
.venv\Scripts\activate
```

Cài đặt các thư viện cần thiết:

```bash
pip install -r requirements.txt
```

### 2.3. Cấu hình biến môi trường

Tạo file `.env` ở thư mục gốc của project và thêm các biến sau:

```env
NEO4J_URI=bolt://localhost:7687
NEO4J_USERNAME=neo4j
NEO4J_PASSWORD=your_neo4j_password
OPENAI_API_KEY=your_openai_api_key
OPENAI_CHAT_MODEL=gpt-5.4-mini
```

Trong đó:

- `NEO4J_URI`: địa chỉ kết nối đến Neo4j.
- `NEO4J_USERNAME`: tên đăng nhập Neo4j.
- `NEO4J_PASSWORD`: mật khẩu Neo4j.
- `OPENAI_API_KEY`: API key dùng để gọi mô hình AI và tạo embedding.
- `OPENAI_CHAT_MODEL`: model dùng để sinh câu trả lời, ví dụ `gpt-5.4-mini` hoặc `gpt-5.5`.

### 2.4. Chuẩn bị dữ liệu cho Neo4j

Nếu Neo4j chưa có dữ liệu, cần import dữ liệu đồ thị và vector vào database.

Import dữ liệu đồ thị:

```bash
python scripts/import_to_neo4j.py
```

Import dữ liệu vector:

```bash
python scripts/import_vectors.py
```

Lưu ý: trước khi chạy các script trên, cần đảm bảo Neo4j đang hoạt động và file `.env` đã được cấu hình đúng.

### 2.5. Chạy giao diện web

Sau khi cài đặt và cấu hình xong, chạy ứng dụng Streamlit:

```bash
streamlit run src/app.py
```

Khi chạy thành công, Streamlit sẽ mở ứng dụng tại địa chỉ:

```text
http://localhost:8501
```

Người dùng có thể nhập câu hỏi lịch sử vào ô chat để hệ thống truy xuất dữ liệu và sinh câu trả lời.

### 2.6. Chạy chatbot trên terminal

Ngoài giao diện web, có thể chạy chatbot trực tiếp trên terminal:

```bash
python src/chatbot.py
```

Để thoát khỏi chatbot terminal, nhập một trong các lệnh:

```text
thoat
exit
quit
```

### 2.7. Một số lỗi thường gặp

Nếu không kết nối được Neo4j:

- Kiểm tra Neo4j đã chạy chưa.
- Kiểm tra lại `NEO4J_URI`, `NEO4J_USERNAME`, `NEO4J_PASSWORD`.

Nếu lỗi khi gọi OpenAI:

- Kiểm tra `OPENAI_API_KEY`.
- Kiểm tra kết nối mạng.
- Kiểm tra hạn mức tài khoản OpenAI.

Nếu thiếu thư viện:

```bash
pip install -r requirements.txt
```

Nếu Streamlit không chạy:

```bash
python -m streamlit run src/app.py
```
