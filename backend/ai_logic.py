import os
import re
import json
from groq import Groq
from dotenv import load_dotenv
from shop_data import SYSTEM_INSTRUCTION, SERVICES

load_dotenv()

client = Groq(api_key=os.getenv("GROQ_API_KEY"))


def chat_with_ai(message: str, history: list, selected_services: list = []):
    """
    Chat với Groq AI và trích xuất đơn hàng nếu có
    
    Args:
        message: Tin nhắn từ người dùng
        history: Lịch sử chat
        selected_services: Danh sách dịch vụ đã chọn
    
    Returns:
        dict: {reply, order_data, services}
    """
    try:
        messages = [{"role": "system", "content": SYSTEM_INSTRUCTION}] + history
        messages.append({"role": "user", "content": message})

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
                # Xóa JSON khỏi tin nhắn hiển thị
                bot_reply = bot_reply.replace(match.group(0), "").strip()
            except Exception as e:
                print(f"Lỗi xử lý đơn hàng: {e}")

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


def extract_services_from_history(history: list):
    """
    Trích xuất dịch vụ từ lịch sử chat bằng AI
    
    Args:
        history: Lịch sử chat
    
    Returns:
        dict: {services: [list of extracted services]}
    """
    try:
        history_text = "\n".join([f"{msg['role']}: {msg['content']}" for msg in history])

        # List all available services for matching
        all_services_list = []
        for service_key, service_data in SERVICES.items():
            for sub in service_data.get('sub_services', []):
                all_services_list.append({
                    'service_key': service_key,
                    'sub_id': sub['id'],
                    'name': sub['name'],
                    'price': sub['price']
                })

        extraction_prompt = f"""Bạn là trợ lý phân tích dịch vụ thú cưng. Hãy TRÍCH XUẤT TẤT CẢ những dịch vụ mà khách hàng đã đề cập hoặc đã chọn trong toàn bộ cuộc trò chuyện.

QUAN TRỌNG: Hãy tìm tất cả các dịch vụ được nhắc đến, kể cả những dịch vụ được nêu ở đầu cuộc trò chuyện!

Lịch sử chat:
{history_text}

Danh sách TẤT CẢ dịch vụ có sẵn:
{json.dumps(all_services_list, ensure_ascii=False, indent=2)}

HƯỚNG DẪN:
1. Tìm tất cả tên dịch vụ được đề cập trong chat (bất kỳ nơi nào)
2. So sánh với danh sách dịch vụ có sẵn
3. Trả lại TẤT CẢ những dịch vụ khớp với tên trong chat

Hãy trả lại JSON với cấu trúc:
{{
    "services": [
        {{"service_key": "spa", "sub_id": "spa_1", "name": "Tên Dịch Vụ", "price": "200k"}},
        {{"service_key": "hotel", "sub_id": "hotel_1", "name": "Phòng Thường", "price": "150k/ngày"}},
        ...
    ]
}}

QUAN TRỌNG: Bao gồm tất cả các dịch vụ được nêu, không bỏ sót bất cứ dịch vụ nào!"""

        completion = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[
                {"role": "system", "content": "Bạn là trợ lý phân tích chuyên nghiệp. Hãy trích xuất TẤT CẢ dịch vụ từ cuộc trò chuyện một cách chính xác và đầy đủ."},
                {"role": "user", "content": extraction_prompt}
            ],
            temperature=0.2,
            max_tokens=1000
        )

        response_text = completion.choices[0].message.content
        print(f"Extraction response: {response_text}")

        # Extract JSON from response
        json_match = re.search(r'\{[\s\S]*\}', response_text)
        if json_match:
            try:
                result = json.loads(json_match.group(0))
                services = result.get("services", [])
                print(f"Extracted services: {services}")
                return {"services": services}
            except json.JSONDecodeError as je:
                print(f"JSON decode error: {je}")

        return {"services": []}

    except Exception as e:
        print(f"Lỗi trích xuất dịch vụ: {e}")
        return {"services": []}
