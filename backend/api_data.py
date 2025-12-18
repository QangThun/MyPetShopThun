import os
import json
from datetime import datetime
import smtplib
from email.mime.text import MIMEText
from email.header import Header
from shop_data import SHOP_INFO, SERVICES

ORDER_FILE = "orders.json"

# Thông tin đăng nhập demo
USERS = {
    "khachhang": "123",
    "admin": "123"
}


def validate_login(username: str, password: str):
    """
    Xác thực đăng nhập người dùng
    
    Args:
        username: Tên đăng nhập
        password: Mật khẩu
    
    Returns:
        dict: {role: 'admin'|'user'} hoặc None nếu sai
    """
    if username in USERS and USERS[username] == password:
        return {"role": "admin" if username == "admin" else "user"}
    return None


def get_services():
    """
    Lấy danh sách dịch vụ
    
    Returns:
        dict: {services: SERVICES}
    """
    return {"services": SERVICES}


def save_order_to_file(order_data):
    """
    Lưu đơn hàng vào file JSON
    
    Args:
        order_data: Thông tin đơn hàng
    
    Returns:
        None
    """
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
    """
    Gửi email thông báo đơn hàng mới
    
    Args:
        order_data: Thông tin đơn hàng
    
    Returns:
        None
    """
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


def confirm_order(order_info):
    """
    Xác nhận và lưu đơn hàng
    
    Args:
        order_info: Thông tin đơn hàng
    
    Returns:
        dict: {success: bool, reply: str}
    """
    try:
        # Validate order data
        if not all(key in order_info for key in ['name', 'phone', 'service', 'time', 'price']):
            return {
                "success": False,
                "reply": "❌ Thông tin đơn hàng không đầy đủ"
            }

        # Save order to file
        save_order_to_file(order_info)

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


def get_all_orders():
    """
    Lấy danh sách tất cả đơn hàng
    
    Returns:
        dict: {orders: [list of orders]}
    """
    try:
        if not os.path.exists(ORDER_FILE):
            return {"orders": []}

        with open(ORDER_FILE, "r", encoding="utf-8") as f:
            orders = json.load(f)

        return {"orders": orders}
    except Exception as e:
        print(f"Lỗi lấy đơn hàng: {e}")
        return {"orders": []}


def get_stats():
    """
    Lấy thống kê: tổng đơn, tổng doanh thu, đơn hôm nay
    
    Returns:
        dict: {total_orders, total_revenue, today_orders, today_revenue, orders}
    """
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
