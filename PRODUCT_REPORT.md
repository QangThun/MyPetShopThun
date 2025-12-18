# Báo Cáo Sản Phẩm: Pet Lovers Spa & Hotel - AI Chatbot

## 📋 I. Thông Tin Chung

**Tên Sản Phẩm:** Pet Lovers Spa & Hotel - AI Chatbot (Mimi)

**Mô Tả:** Hệ thống chatbot AI tiếng Việt giúp khách hàng đặt lịch dịch vụ spa, cắt tạo kiểu, và khách sạn cho thú cưng. Tích hợp phát hiện cảm xúc để cung cấp trải nghiệm khách hàng tốt hơn.

**Thời Gian Phát Triển:** Q4 2025

---

## 🛠️ II. Công Nghệ & Framework

### Backend
| Công Nghệ | Phiên Bản | Mục Đích |
|-----------|----------|---------|
| **FastAPI** | - | Web framework chính cho API |
| **Python** | 3.8+ | Ngôn ngữ lập trình backend |
| **Groq API** | - | AI model (Llama-3.3-70b) cho chat và phát hiện cảm xúc |
| **Uvicorn** | - | ASGI server để chạy FastAPI |
| **Pydantic** | - | Validation dữ liệu input/output |
| **python-dotenv** | - | Quản lý environment variables |
| **smtplib** | - | Gửi email thông báo đơn hàng |

### Frontend
| Công Nghệ | Phiên Bản | Mục Đích |
|-----------|----------|---------|
| **React** | 19.2.0 | UI framework chính |
| **React-DOM** | 19.2.0 | Render React components |
| **Vite** | 7.2.4 | Build tool & dev server |
| **ESLint** | 9.39.1 | Code linting |
| **Vanilla CSS** | - | Styling (không dùng Tailwind/Bootstrap) |

### Kiến Trúc Tổng Quan
```
┌─────────────────────────────────────┐
│     Frontend (React + Vite)         │
│  - CustomerChat Component            │
│  - AdminDashboard Component          │
│  - Login Component                   │
└──────────────┬──────────────────────┘
               │
         HTTP/REST API
               │
┌──────────────▼──────────────────────┐
│     Backend (FastAPI)               │
│  - main.py (Routing & CORS)         │
│  - ai_logic.py (AI Chat & Emotion)  │
│  - api_data.py (CRUD & Stats)       │
│  - shop_data.py (Data Models)       │
└──────────────┬──────────────────────┘
               │
        External Services
        ├─ Groq AI (LLM Chat)
        └─ Gmail SMTP (Email)
```

---

## 📁 III. Cấu Trúc File & Chức Năng

### Backend Files

#### 1. **main.py** (117 dòng)
- **Chức Năng:** Routing chính, thiết lập CORS, gọi hàm từ ai_logic & api_data
- **API Endpoints:**
  - `POST /api/login` - Xác thực người dùng
  - `POST /api/chat` - Chat với AI Mimi
  - `POST /api/extract-services` - Trích xuất dịch vụ từ chat
  - `POST /api/confirm-order` - Xác nhận đơn hàng
  - `GET /api/services` - Lấy danh sách dịch vụ
  - `GET /api/orders` - Lấy tất cả đơn hàng
  - `GET /api/stats` - Lấy thống kê doanh số

#### 2. **ai_logic.py** (200+ dòng)
- **Chức Năng:** Xử lý AI, chat, phát hiện cảm xúc
- **Hàm Chính:**
  - `detect_emotion(message, history)` - Phát hiện cảm xúc khách (annoyed, worried, happy, neutral)
  - `chat_with_ai(message, history, selected_services)` - Chat với Groq AI
  - `extract_services_from_history(history)` - Trích xuất dịch vụ từ lịch sử chat

#### 3. **api_data.py** (233 dòng)
- **Chức Năng:** Xử lý dữ liệu, CRUD, thống kê
- **Hàm Chính:**
  - `validate_login(username, password)` - Xác thực đăng nhập
  - `save_order_to_file(order_data)` - Lưu đơn hàng JSON
  - `send_email_task(order_data)` - Gửi email thông báo
  - `confirm_order(order_info)` - Xác nhận đơn hàng
  - `get_all_orders()` - Lấy tất cả đơn hàng
  - `get_stats()` - Tính thống kê (tổng đơn, doanh thu, đơn hôm nay)

#### 4. **shop_data.py** (231 dòng)
- **Chức Năng:** Dữ liệu sản phẩm, system instruction cho AI
- **Dữ Liệu:**
  - `SERVICES` - 3 loại dịch vụ chính (Spa, Cắt Tạo Kiểu, Khách Sạn)
    - 8 dịch vụ con với giá cụ thể
  - `SHOP_INFO` - Thông tin cửa hàng
  - `BASE_SYSTEM_INSTRUCTION` - Hướng dẫn AI cơ bản
  - `get_system_instruction_with_emotion(emotion)` - Instruction phù hợp theo cảm xúc

### Frontend Files

#### 1. **App.jsx** (26 dòng)
- **Chức Năng:** Router chính, quản lý role (admin/customer/login)
- **Logic:** Hiển thị Login / AdminDashboard / CustomerChat dựa trên role

#### 2. **CustomerChat.jsx** (456 dòng)
- **Chức Năng:** Giao diện chat cho khách hàng
- **Features:**
  - Chat realtime với AI Mimi
  - Lựa chọn dịch vụ bằng buttons
  - Phát hiện từ khóa chốt đơn
  - Form nhập thông tin khách hàng
  - Modal xác nhận đơn hàng
  - Hiển thị hóa đơn khi chốt xong
- **State Management:**
  - `messages` - Lịch sử chat
  - `selectedServices` - Dịch vụ đã chọn
  - `showInfoForm` - Hiển thị form thông tin
  - `showOrderConfirm` - Hiển thị modal xác nhận
  - `customerInfo` - Thông tin khách (tên, SĐT, thú cưng, giờ hẹn)

#### 3. **AdminDashboard.jsx**
- **Chức Năng:** Dashboard admin xem đơn hàng & thống kê
- **Features:**
  - Hiển thị tất cả đơn hàng
  - Thống kê: Tổng đơn, tổng doanh thu, đơn hôm nay

#### 4. **Login.jsx**
- **Chức Năng:** Đăng nhập (khách hàng / admin)
- **Accounts Demo:**
  - `admin / admin123` - Admin account
  - `khachhang / 123` - Customer account

---

## 🧠 IV. Mô Hình AI & Emotion Detection

### Mô Hình AI
- **Provider:** Groq API
- **Model:** Llama-3.3-70b-versatile
- **Ngôn Ngữ:** Tiếng Việt
- **Temperature:** 0.6 (cho chat), 0.2-0.3 (cho trích xuất/emotion)

### Phát Hiện Cảm Xúc (4 loại)
| Cảm Xúc | Behavior AI |
|---------|-----------|
| **annoyed** | Xin lỗi, hỗ trợ nhanh gọn, không kéo dài |
| **worried** | Trấn an chi tiết, giải thích an toàn |
| **happy** | Gợi ý upsell combo dịch vụ |
| **neutral** | Tư vấn tiêu chuẩn |

### Quy Trình Chat
```
BƯỚC 1: Chào & hỏi dịch vụ
BƯỚC 2: Khách chọn dịch vụ (buttons hoặc chat)
BƯỚC 3: Gợi ý dịch vụ thêm
BƯỚC 4: Khách nói từ khóa chốt → Hiện form thông tin
BƯỚC 5: Form được điền → Hiện modal xác nhận
BƯỚC 6: Xác nhận → Lưu đơn hàng + Gửi email
```

---

## 📊 V. Dữ Liệu & Model

### Dịch Vụ (SERVICES)
```
SPA (3 loại):
  - Thơm Tho (< 5kg): 200k
  - Sạch Sẽ (5-10kg): 350k
  - Siêu Cấp (> 10kg): 500k

CẮT TẠO KIỂU (5 loại):
  - Teddy Bear: 300k
  - Nhật (Japanese): 300k
  - Summer Cut: 250k
  - Bờm Sư Tử: 300k
  - Trái Tim: 350k

KHÁCH SẠN (2 loại):
  - Phòng Thường: 150k/ngày
  - Phòng VIP: 300k/ngày
```

### Order Data Model
```json
{
  "name": "Tên khách",
  "phone": "SĐT",
  "petName": "Tên thú cưng",
  "petType": "Loại thú cưng",
  "service": "Danh sách dịch vụ",
  "time": "Giờ hẹn",
  "price": "Tổng giá",
  "created_at": "Timestamp"
}
```

### Login Model
```python
USERS = {
  "khachhang": "123",
  "admin": "admin123"
}
```

---

## 🚀 VI. Features Chính

### ✅ Chức Năng Đã Implement
1. **Chat Realtime** - AI Mimi trả lời tiếng Việt
2. **Emotion Detection** - Phát hiện cảm xúc → điều chỉnh tone
3. **Service Selection** - Chọn dịch vụ bằng buttons hoặc chat
4. **Smart Order Detection** - Phát hiện từ khóa chốt đơn
5. **Form Validation** - Yêu cầu đầy đủ thông tin trước khi chốt
6. **Order Confirmation** - Modal xác nhận chi tiết
7. **Email Notification** - Gửi email thông báo đơn hàng (Gmail SMTP)
8. **Order History** - Lưu tất cả đơn hàng vào JSON
9. **Admin Dashboard** - Xem đơn hàng & thống kê
10. **Login System** - Phân quyền admin/customer

### 🔄 Emotion-Based Responses
- **Annoyed Customer** → Nhẹ nhàng, xin lỗi, ưu tiên hỗ trợ
- **Worried Customer** → Trấn an, tư vấn chi tiết về sức khỏe
- **Happy Customer** → Gợi ý combo dịch vụ (upsell)
- **Neutral Customer** → Tư vấn tiêu chuẩn

---

## 💾 VII. Data Storage

- **Orders:** `backend/orders.json` (JSON file local)
- **Services:** In-memory từ `shop_data.py`
- **Config:** `backend/.env` (email credentials, API keys)

---

## 🔐 VIII. Security & Best Practices

- ✅ CORS enabled cho frontend access
- ✅ Pydantic validation cho tất cả input
- ✅ Environment variables cho sensitive data (API keys, email)
- ✅ Background tasks cho email (không chặn request)
- ✅ Error handling & rate limit detection

---

## 📈 IX. Thống Kê & Metrics

**Dữ Liệu Theo Dõi:**
- Tổng số đơn hàng
- Tổng doanh thu
- Số đơn hôm nay
- Doanh thu hôm nay
- Chi tiết từng đơn (tên, SĐT, dịch vụ, giá, giờ hẹn)

---

## 🎯 X. Lợi Ích Sản Phẩm

### Cho Khách Hàng
- ✨ Trải nghiệm chat tự nhiên, thân thiết
- 🧠 AI hiểu cảm xúc → phục vụ tốt hơn
- ⏰ Nhanh chóng đặt lịch 24/7
- 📱 Dễ sử dụng, giao diện thân thiện

### Cho Shop
- 📊 Tự động nhận đơn qua email
- 💰 Tăng tỷ lệ conversion (upsell combos)
- 📈 Thống kê doanh số real-time
- 🤖 Giảm nhân lực tư vấn

---

## 📝 XI. Tập Tin Cấu Hình

```
backend/
  ├─ main.py
  ├─ ai_logic.py
  ├─ api_data.py
  ├─ shop_data.py
  ├─ requirements.txt
  ├─ .env (not in repo)
  └─ orders.json

frontend/
  ├─ package.json
  ├─ vite.config.js
  ├─ eslint.config.js
  ├─ src/
  │  ├─ App.jsx
  │  ├─ main.jsx
  │  ├─ App.css
  │  ├─ index.css
  │  └─ components/
  │     ├─ Login.jsx (+ .css)
  │     ├─ CustomerChat.jsx (+ .css)
  │     └─ AdminDashboard.jsx (+ .css)
```

---

## 🚀 XII. Cách Chạy

### Backend
```bash
cd backend
pip install -r requirements.txt
uvicorn main:app --reload --host 127.0.0.1 --port 8000
```

### Frontend
```bash
cd frontend
npm install
npm run dev
```

---

## 📊 XIII. Tóm Tắt Metrics

| Metric | Giá Trị |
|--------|--------|
| **Backend Files** | 4 files (main, ai_logic, api_data, shop_data) |
| **Frontend Files** | 3 components (Login, CustomerChat, AdminDashboard) |
| **API Endpoints** | 7 endpoints (login, chat, extract, confirm, services, orders, stats) |
| **AI Models** | 1 (Llama-3.3-70b via Groq) |
| **Emotion Types** | 4 (annoyed, worried, happy, neutral) |
| **Services** | 3 categories, 8 sub-services |
| **Backend Framework** | FastAPI |
| **Frontend Framework** | React 19 |
| **Database** | JSON file (orders.json) |
| **Authentication** | Basic (demo users) |

---

## 🎓 Kết Luận

Sản phẩm Pet Lovers Spa & Hotel Chatbot là một hệ thống hoàn chỉnh kết hợp AI, emotion detection, và quản lý đơn hàng. Tập trung vào trải nghiệm khách hàng tốt hơn thông qua hiểu biết cảm xúc, và tăng doanh số qua gợi ý smart (upsell).

**Công nghệ:** FastAPI + React + Groq AI + Emotion Detection  
**Mục đích:** Chatbot đặt lịch thú cưng tự động với AI tiếng Việt  
**Lợi ích chính:** Tăng CSKH, tăng conversion, giảm nhân lực
