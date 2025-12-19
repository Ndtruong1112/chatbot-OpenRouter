# Chatbot - OpenRouter
# Hướng dẫn đăng ký, lấy key OpenRouter
**1. Đăng ký tài khoản OpenRouter**

<img width="502" height="679" alt="image" src="https://github.com/user-attachments/assets/141b5c9a-b37e-4cc0-ba60-01ac256b15d3" />

(tại đây bạn có thể chọn 1 trong 3 cách đăng ký nhanh)

**2. Tạo key OpenRouter**
<img width="1287" height="365" alt="image" src="https://github.com/user-attachments/assets/0fe28908-bd70-409e-9ca8-3539064a03e4" /> (chỉ cần thêm tên là tạo được)

**3. Gán key vào code và chạy**

# Hướng dẫn chạy code

Dự án này gồm **2 phiên bản chatbot** viết bằng Python, sử dụng OpenRouter API để gọi các mô hình AI.  
Giao diện được xây dựng bằng **Gradio**.

---

## 🚀 Phiên bản test3.py: Dùng thư viện `openai`

### 📦 Thư viện cần thiết
- `gradio`
- `requests`
- `openai`

### 📝 requirements_v1.txt
- gradio requests openai

### ▶️ Cách chạy
1. Tạo và kích hoạt môi trường ảo:
   ```bash
   python -m venv .venv
   .venv\Scripts\activate   # Windows
   source .venv/bin/activate # macOS/Linux
2. Cài thư viện: 
- pip install -r requirements_v1.txt
3. chạy chatbot:
- python code/test3.py
