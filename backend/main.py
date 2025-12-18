from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from dotenv import load_dotenv

from ai_logic import chat_with_ai, extract_services_from_history
from api_data import (
    validate_login,
    get_services,
    save_order_to_file,
    send_email_task,
    confirm_order,
    get_all_orders,
    get_stats
)

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


# --- MODELS ---
class LoginRequest(BaseModel):
    username: str
    password: str


class ChatRequest(BaseModel):
    message: str
    history: list
    selected_services: list = []


class ConfirmOrderRequest(BaseModel):
    order: dict
    history: list


class ExtractServicesRequest(BaseModel):
    history: list


# --- API ENDPOINTS ---

@app.get("/api/services")
def get_services_endpoint():
    """API lấy danh sách dịch vụ"""
    return get_services()


@app.post("/api/login")
def login(data: LoginRequest):
    """API đăng nhập - trả về role của user"""
    result = validate_login(data.username, data.password)
    if result:
        return result
    raise HTTPException(status_code=401, detail="Sai thông tin đăng nhập")


@app.post("/api/chat")
def chat(data: ChatRequest, background_tasks: BackgroundTasks):
    """API chat với Mimi - xử lý đơn hàng với lựa chọn dịch vụ"""
    result = chat_with_ai(data.message, data.history, data.selected_services)
    
    # Nếu có đơn hàng, lưu vào file và gửi email
    if result.get("order_data"):
        save_order_to_file(result["order_data"])
        background_tasks.add_task(send_email_task, result["order_data"])
    
    return result


@app.post("/api/confirm-order")
def confirm_order_endpoint(data: ConfirmOrderRequest, background_tasks: BackgroundTasks):
    """API xác nhận và lưu đơn hàng"""
    result = confirm_order(data.order)
    
    # Nếu xác nhận thành công, gửi email
    if result.get("success"):
        background_tasks.add_task(send_email_task, data.order)
    
    return result


@app.post("/api/extract-services")
def extract_services(data: ExtractServicesRequest):
    """API trích xuất dịch vụ từ lịch sử chat"""
    return extract_services_from_history(data.history)


@app.get("/api/orders")
def get_orders():
    """API lấy danh sách tất cả đơn hàng"""
    return get_all_orders()


@app.get("/api/stats")
def get_stats_endpoint():
    """API lấy thống kê: tổng đơn, tổng doanh thu, đơn hôm nay"""
    return get_stats()
