import os
import re
import json
from groq import Groq
from dotenv import load_dotenv
from shop_data import SYSTEM_INSTRUCTION, SERVICES, get_system_instruction_with_emotion

load_dotenv()

client = Groq(api_key=os.getenv("GROQ_API_KEY"))


def detect_emotion(message: str, history: list):
    """
    Phát hiện cảm xúc của khách hàng bằng Groq AI

    Args:
        message: Tin nhắn từ người dùng
        history: Lịch sử chat

    Returns:
        str: Một trong ['annoyed', 'worried', 'happy', 'neutral']
    """
    try:
        history_text = "\n".join([f"{msg['role']}: {msg['content']}" for msg in history[-3:]]) if history else ""

        emotion_prompt = f"""Phân tích cảm xúc của khách hàng từ tin nhắn cuối cùng.

Lịch sử chat gần đây:
{history_text}

Tin nhắn hiện tại: {message}

Xác định cảm xúc chính của khách hàng là gì?

Danh sách cảm xúc:
1. "annoyed" - Khách bực bội, khó chịu, không hài lòng
2. "worried" - Khách lo lắng, sợ hãi (thú cưng bệnh, sợ đau, lo lắng về sức khỏe)
3. "happy" - Khách vui vẻ, hài lòng, tích cực
4. "neutral" - Khách trung lập, đặt câu hỏi thường, không thể hiện cảm xúc rõ

CH CHỉ trả lại MỘT trong 4 từ trên, không giải thích thêm. Ví dụ: "annoyed"""

        completion = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[
                {"role": "system", "content": "Bạn là chuyên gia phân tích cảm xúc. Hãy xác định cảm xúc của khách hàng dựa trên lời nói của họ."},
                {"role": "user", "content": emotion_prompt}
            ],
            temperature=0.3,
            max_tokens=20
        )

        emotion_text = completion.choices[0].message.content.strip().lower()

        # Kiểm tra kết quả
        emotions = ['annoyed', 'worried', 'happy', 'neutral']
        for emotion in emotions:
            if emotion in emotion_text:
                print(f"Detected emotion: {emotion}")
                return emotion

        return "neutral"

    except Exception as e:
        print(f"Lỗi phát hiện cảm xúc: {e}")
        return "neutral"


def chat_with_ai(message: str, history: list, selected_services: list = []):
    """
    Chat với Groq AI và trích xuất đơn hàng nếu có
    Tự động phát hiện cảm xúc và điều chỉnh response phù hợp

    Args:
        message: Tin nhắn từ người dùng
        history: Lịch sử chat
        selected_services: Danh sách dịch vụ đã chọn

    Returns:
        dict: {reply, order_data, services, emotion}
    """
    try:
        # Phát hiện cảm xúc của khách
        emotion = detect_emotion(message, history)

        # Điều chỉnh system instruction dựa trên cảm xúc
        adjusted_system_instruction = get_system_instruction_with_emotion(emotion)

        messages = [{"role": "system", "content": adjusted_system_instruction}] + history
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
            "services": SERVICES,
            "emotion": emotion
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
    Chỉ trích xuất từ tin nhắn người dùng mới nhất (chứa từ khóa xác nhận)

    Args:
        history: Lịch sử chat

    Returns:
        dict: {services: [list of extracted services]}
    """
    try:
        # Lấy tin nhắn người dùng mới nhất (tin nhắn xác nhận)
        last_user_message = None
        for msg in reversed(history):
            if msg.get('role') == 'user':
                last_user_message = msg.get('content', '')
                break

        if not last_user_message:
            return {"services": []}

        # First try: Keyword matching for service names
        extracted_by_keyword = []
        message_lower = last_user_message.lower()

        # Score each service based on how many keywords from its name appear in the message
        service_scores = []

        for service_key, service_data in SERVICES.items():
            for sub in service_data.get('sub_services', []):
                service_name = sub['name'].lower()

                # Exact match - highest priority
                if service_name in message_lower:
                    service_scores.append((5, {
                        'service_key': service_key,
                        'sub_id': sub['id'],
                        'name': sub['name'],
                        'price': sub['price']
                    }))
                    continue

                # Count how many keywords match
                service_keywords = [w for w in service_name.split() if len(w) > 2]
                matching_keywords = sum(1 for keyword in service_keywords if keyword in message_lower)

                # Only include if at least 2 keywords match (e.g., "phòng" + "thường")
                # This prevents matching just "phòng" for both "Phòng Thường" and "Phòng VIP"
                if len(service_keywords) > 0 and matching_keywords == len(service_keywords):
                    service_scores.append((matching_keywords, {
                        'service_key': service_key,
                        'sub_id': sub['id'],
                        'name': sub['name'],
                        'price': sub['price']
                    }))

        # Sort by score (descending) and extract
        service_scores.sort(key=lambda x: x[0], reverse=True)
        extracted_by_keyword = [service for _, service in service_scores]

        # Remove duplicates (same service mentioned multiple times)
        unique_by_id = {}
        for service in extracted_by_keyword:
            if service['sub_id'] not in unique_by_id:
                unique_by_id[service['sub_id']] = service

        extracted_by_keyword = list(unique_by_id.values())

        # If we found services via keyword matching, return them
        if extracted_by_keyword:
            print(f"Found services via keyword matching: {extracted_by_keyword}")
            return {"services": extracted_by_keyword}

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

        extraction_prompt = f"""Bạn là trợ lý phân tích dịch vụ thú cưng. Hãy TRÍCH XUẤT những dịch vụ mà khách hàng đề cập TRONG TIN NHẮN XÁC NHẬN NÀY (không phải toàn bộ lịch sử).

QUAN TRỌNG: Chỉ trích xuất những dịch vụ được đề cập TỪ TRONG TIN NHẮN HIỆN TẠI, không phải từ các tin nhắn trước!

Tin nhắn xác nhận từ khách hàng:
"{last_user_message}"

Danh sách TẤT CẢ dịch vụ có sẵn:
{json.dumps(all_services_list, ensure_ascii=False, indent=2)}

HƯỚNG DẪN:
1. Tìm tên dịch vụ được đề cập TRONG TIN NHẮN TRÊN
2. So sánh với danh sách dịch vụ có sẵn
3. Trả lại CHỈ những dịch vụ khớp

Hãy trả lại JSON với cấu trúc:
{{
    "services": [
        {{"service_key": "hotel", "sub_id": "hotel_1", "name": "Phòng Thường", "price": "150k/ngày"}},
        ...
    ]
}}

Nếu không tìm thấy dịch vụ nào, trả lại: {{"services": []}}"""

        completion = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[
                {"role": "system", "content": "Bạn là trợ lý phân tích chuyên nghiệp. Hãy trích xuất dịch vụ CHỈ từ tin nhắn hiện tại, không phải từ toàn bộ lịch sử."},
                {"role": "user", "content": extraction_prompt}
            ],
            temperature=0.2,
            max_tokens=500
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


def extract_customer_info_from_history(history: list):
    """
    Trích xuất thông tin khách hàng từ lịch sử chat bằng AI

    Args:
        history: Lịch sử chat

    Returns:
        dict: {name, phone, petName, petType, time} - các trường có thể rỗng nếu không tìm thấy
    """
    try:
        # Tạo full chat history text
        history_text = "\n".join([f"{msg['role']}: {msg['content']}" for msg in history])

        if not history_text.strip():
            return {"name": "", "phone": "", "petName": "", "petType": "", "time": ""}

        extraction_prompt = f"""Bạn là trợ lý trích xuất thông tin khách hàng. Hãy trích xuất các thông tin sau từ lịch sử chat:
- Tên khách hàng
- Số điện thoại
- Tên thú cưng
- Loại thú cưng (Chó, Mèo, v.v.)
- Giờ hẹn/thời gian

Lịch sử chat:
{history_text}

HƯỚNG DẪN:
1. Tìm tất cả thông tin có sẵn trong chat
2. Nếu không tìm thấy, để trống (không điền "không biết" hay "N/A")
3. Trả lại JSON có cấu trúc chính xác

Hãy trả lại JSON:
{{
    "name": "Tên khách (nếu tìm thấy, nếu không để trống)",
    "phone": "SĐT (nếu tìm thấy, nếu không để trống)",
    "petName": "Tên thú cưng (nếu tìm thấy, nếu không để trống)",
    "petType": "Loại thú cưng như Chó/Mèo (nếu tìm thấy, nếu không để trống)",
    "time": "Giờ hẹn (nếu tìm thấy, nếu không để trống)"
}}

CHỈ TRẢ LẠI JSON, KHÔNG CÓ LỜI GIẢI THÍCH."""

        completion = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[
                {"role": "system", "content": "Bạn là trợ lý trích xuất thông tin chuyên nghiệp. Hãy trích xuất thông tin khách hàng từ cuộc trò chuyện một cách chính xác."},
                {"role": "user", "content": extraction_prompt}
            ],
            temperature=0.2,
            max_tokens=300
        )

        response_text = completion.choices[0].message.content
        print(f"Customer info extraction response: {response_text}")

        # Extract JSON from response
        json_match = re.search(r'\{[\s\S]*\}', response_text)
        if json_match:
            try:
                result = json.loads(json_match.group(0))
                extracted_info = {
                    "name": result.get("name", ""),
                    "phone": result.get("phone", ""),
                    "petName": result.get("petName", ""),
                    "petType": result.get("petType", ""),
                    "time": result.get("time", "")
                }
                print(f"Extracted customer info: {extracted_info}")
                return extracted_info
            except json.JSONDecodeError as je:
                print(f"JSON decode error: {je}")

        return {"name": "", "phone": "", "petName": "", "petType": "", "time": ""}

    except Exception as e:
        print(f"Lỗi trích xuất thông tin khách hàng: {e}")
        return {"name": "", "phone": "", "petName": "", "petType": "", "time": ""}
