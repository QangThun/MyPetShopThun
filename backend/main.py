from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
import json
import os
import re
import smtplib
from email.mime.text import MIMEText
from email.header import Header
from datetime import datetime
from groq import Groq
from dotenv import load_dotenv
from shop_data import SYSTEM_INSTRUCTION, SHOP_INFO, SERVICES

load_dotenv()

app = FastAPI()

# Cấu hình CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount static files cho ảnh
try:
    app.mount("/static", StaticFiles(directory="static"), name="static")
except:
    print("⚠️  Thư mục 'static' chưa tồn tại")

client = Groq(api_key=os.getenv("GROQ_API_KEY"))
ORDER_FILE = "orders.json"

# Thông tin đăng nhập demo
USERS = {
    "khachhang": "123",
    "admin": "admin123"
}

# --- MODELS ---
class LoginRequest(BaseModel):
    username: str
    password: str

class ChatRequest(BaseModel):
    message: str
    history: list
    selected_services: list = []  # Track selected services

class ConfirmOrderRequest(BaseModel):
    order: dict
    history: list

class StyleAnalysisRequest(BaseModel):
    image_base64: str
    message: str

# --- HÀM HỖ TRỢ ---
def save_order_to_file(order_data):
    """Lưu đơn hàng vào file JSON"""
    if os.path.exists(ORDER_FILE):
        with open(ORDER_FILE, "r", encoding="utf-8") as f:
            try:
                orders = json.load(f)
            except:
                orders = []
    else:
        orders = []
    
    order_data["created_at"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    orders.append(order_data)
    
    with open(ORDER_FILE, "w", encoding="utf-8") as f:
        json.dump(orders, f, ensure_ascii=False, indent=4)
    
    print(f"✅ Đã lưu đơn hàng cho {order_data.get('name')}")

def send_email_task(order_data):
    """Gửi email thông báo đơn hàng mới"""
    sender = os.getenv("EMAIL_GUI")
    pwd = os.getenv("MAT_KHAU_UNG_DUNG")
    receiver = os.getenv("EMAIL_NHAN")

    if not sender or not pwd:
        print("❌ Thiếu thông tin Email")
        return

    time_now = datetime.now().strftime("%H:%M - %d/%m/%Y")
    subject = f"🔔 [ĐƠN MỚI] Khách {order_data.get('name', 'Ẩn danh')} chốt đơn!"

    body = f"""
    Kính gửi Chủ Shop,
    
    Khách hàng vừa chốt đơn qua Chatbot Mimi!
    ----------------------------
    ⏰ Thời gian: {time_now}
    👤 Tên: {order_data.get('name')}
    📞 SĐT: {order_data.get('phone')}
    🐕 Dịch vụ: {order_data.get('service')}
    📅 Lịch hẹn: {order_data.get('time')}
    💰 Giá tạm tính: {order_data.get('price')}
    ----------------------------
    """

    msg = MIMEText(body, 'plain', 'utf-8')
    msg['Subject'] = Header(subject, 'utf-8')
    msg['From'] = sender
    msg['To'] = receiver

    try:
        with smtplib.SMTP_SSL('smtp.gmail.com', 465) as s:
            s.login(sender, pwd)
            s.sendmail(sender, receiver, msg.as_string())
        print(f"✅ Đã gửi email thành công cho khách: {order_data.get('name')}")
    except Exception as e:
        print(f"❌ Lỗi gửi mail: {e}")

# --- API ENDPOINTS ---

@app.get("/api/services")
def get_services():
    """API lấy danh sách dịch vụ"""
    return {"services": SERVICES}

@app.post("/api/login")
def login(data: LoginRequest):
    """API đăng nhập - trả về role của user"""
    if data.username in USERS and USERS[data.username] == data.password:
        return {"role": "admin" if data.username == "admin" else "user"}
    raise HTTPException(status_code=401, detail="Sai thông tin đăng nhập")

@app.post("/api/chat")
def chat(data: ChatRequest, background_tasks: BackgroundTasks):
    """API chat với Mimi - xử lý đơn hàng với lựa chọn dịch vụ"""
    try:
        # Gửi tin nhắn tới AI
        messages = [{"role": "system", "content": SYSTEM_INSTRUCTION}] + data.history
        messages.append({"role": "user", "content": data.message})

        completion = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=messages,
            temperature=0.6
        )

        bot_reply = completion.choices[0].message.content

        # Kiểm tra và tách đơn hàng
        match = re.search(r'\|\|JSON_START\|\|(.*?)\|\|JSON_END\|\|', bot_reply, re.DOTALL)

        order_info = None
        if match:
            try:
                json_str = match.group(1)
                order_info = json.loads(json_str)

                # Lưu đơn hàng vào file
                save_order_to_file(order_info)

                # Gửi email chạy ngầm
                background_tasks.add_task(send_email_task, order_info)

                # Xóa JSON khỏi tin nhắn hiển thị
                bot_reply = bot_reply.replace(match.group(0), "").strip()
            except Exception as e:
                print(f"Lỗi xử lý đơn hàng: {e}")

        # Always return services - they're always visible on frontend
        return {
            "reply": bot_reply,
            "order_data": order_info,
            "services": SERVICES
        }

    except Exception as e:
        error_str = str(e)
        print(f"Lỗi API chat: {e}")

        # Handle rate limit error
        if "429" in error_str or "rate limit" in error_str.lower():
            reply = "⚠️ Hệ thống tạm bận (đã đạt giới hạn). Vui lòng chờ một lát rồi thử lại!"
        else:
            reply = "❌ Lỗi kết nối. Vui lòng thử lại sau."

        return {
            "reply": reply,
            "order_data": None,
            "show_services": False
        }

@app.post("/api/confirm-order")
def confirm_order(data: ConfirmOrderRequest, background_tasks: BackgroundTasks):
    """API xác nhận và lưu đơn hàng"""
    try:
        order_info = data.order

        # Validate order data
        if not all(key in order_info for key in ['name', 'phone', 'service', 'time', 'price']):
            return {
                "success": False,
                "reply": "❌ Thông tin đơn hàng không đầy đủ"
            }

        # Save order to file
        save_order_to_file(order_info)

        # Send email asynchronously
        background_tasks.add_task(send_email_task, order_info)

        return {
            "success": True,
            "reply": f"✅ Cảm ơn {order_info.get('name')}! Đơn hàng đã được xác nhận. Chúng tôi sẽ liên hệ với bạn sớm!"
        }

    except Exception as e:
        print(f"Lỗi xác nhận đơn hàng: {e}")
        return {
            "success": False,
            "reply": f"❌ Có lỗi xảy ra: {str(e)}"
        }

@app.post("/api/analyze-style")
def analyze_style(data: StyleAnalysisRequest, background_tasks: BackgroundTasks):
    """API phân tích kiểu cắt từ ảnh - sử dụng Vision AI"""
    
    system_prompt = f"""
    Bạn là Chuyên gia Tạo mẫu tóc thú cưng (Pet Stylist) của Pet Lovers Spa.
    {SHOP_INFO}
    
    NHIỆM VỤ CỦA BẠN KHI NHÌN ẢNH:
    1. Phân tích phong cách cắt tỉa trong ảnh (Ví dụ: Kiểu Teddy Bear tròn trịa, Kiểu Nhật, Kiểu Summer Cut...).
    2. Xác nhận với khách: "Dạ, đây là [Tên Kiểu] ạ, mẫu này rất hợp với các bé...".
    3. KIỂM TRA THÔNG TIN ĐẶT LỊCH:
       - Nếu có Tên + Giờ hẹn: CHỐT ĐƠN bằng JSON
       - Nếu chưa: Hãy khen mẫu và hỏi khách muốn đặt lịch lúc nào

    QUY TẮC JSON (Nếu đủ thông tin):
    ||JSON_START||
    {
        "name": "Tên khách",
        "phone": "SĐT",
        "service": "Tên kiểu cắt",
        "time": "Giờ hẹn",
        "price": "Giá tiền"
    }
    ||JSON_END||
    """

    try:
        completion = client.chat.completions.create(
            model="llama-3.2-11b-vision-preview",
            messages=[
                {"role": "system", "content": system_prompt},
                {
                    "role": "user", 
                    "content": [
                        {"type": "text", "text": data.message},
                        {
                            "type": "image_url", 
                            "image_url": {"url": data.image_base64}
                        }
                    ]
                }
            ],
            temperature=0.5,
            max_tokens=600
        )
        
        bot_reply = completion.choices[0].message.content
        
        # Tách và lưu đơn hàng nếu có
        match = re.search(r'\|\|JSON_START\|\|(.*?)\|\|JSON_END\|\|', bot_reply, re.DOTALL)
        if match:
            try:
                json_str = match.group(1)
                order_data = json.loads(json_str)
                save_order_to_file(order_data)
                background_tasks.add_task(send_email_task, order_data)
                bot_reply = bot_reply.replace(match.group(0), "").strip()
            except:
                pass
                
        return {"reply": bot_reply}

    except Exception as e:
        print(f"Lỗi Vision API: {e}")
        return {"reply": f"Lỗi phân tích ảnh: {str(e)}"}


@app.get("/api/orders")
def get_orders():
    """API lấy danh sách tất cả đơn hàng"""
    try:
        if not os.path.exists(ORDER_FILE):
            return {"orders": []}

        with open(ORDER_FILE, "r", encoding="utf-8") as f:
            orders = json.load(f)

        return {"orders": orders}
    except Exception as e:
        print(f"Lỗi lấy đơn hàng: {e}")
        return {"orders": []}

@app.get("/api/stats")
def get_stats():
    """API lấy thống kê: tổng đơn, tổng doanh thu, đơn hôm nay"""
    try:
        if not os.path.exists(ORDER_FILE):
            return {
                "total_orders": 0,
                "total_revenue": 0,
                "today_orders": 0,
                "today_revenue": 0,
                "orders": []
            }

        with open(ORDER_FILE, "r", encoding="utf-8") as f:
            orders = json.load(f)

        # Tính toán thống kê
        total_orders = len(orders)
        total_revenue = 0
        today_orders = 0
        today_revenue = 0
        today_date = datetime.now().strftime("%Y-%m-%d")

        for order in orders:
            # Tính doanh thu tổng
            price_str = order.get("price", "0").replace("k", "").replace("K", "").strip()
            try:
                price = float(price_str) * 1000
            except:
                price = 0
            total_revenue += price

            # Tính đơn hôm nay
            created_at = order.get("created_at", "")
            if created_at.startswith(today_date):
                today_orders += 1
                today_revenue += price

        return {
            "total_orders": total_orders,
            "total_revenue": int(total_revenue),
            "today_orders": today_orders,
            "today_revenue": int(today_revenue),
            "orders": orders
        }
    except Exception as e:
        print(f"Lỗi tính thống kê: {e}")
        return {
            "total_orders": 0,
            "total_revenue": 0,
            "today_orders": 0,
            "today_revenue": 0,
            "orders": []
        }
