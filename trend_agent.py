import os
import requests
import sys

# Nạp cấu hình từ GitHub
ORTHOGONAL_API_KEY = os.getenv("ORTHOGONAL_API_KEY")
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

# Tự động dọn rác và chuẩn hóa giá trị đầu vào để tránh vỡ URL
def sanitize(val):
    if not val:
        return ""
    # Xóa toàn bộ ký tự rác nếu người dùng lỡ dán thừa chữ 'bot' hoặc đường dẫn link
    s = str(val).strip().replace(" ", "")
    if s.lower().startswith("bot"):
        s = s[3:]
    return s

token = sanitize(TELEGRAM_TOKEN)
chat_id = sanitize(TELEGRAM_CHAT_ID)

def send_telegram_message(text):
    """Hàm gửi tin sử dụng cấu trúc URL thuần, độc lập tuyệt đối"""
    # Khởi dựng endpoint chuẩn hóa không phụ thuộc vào chuỗi ký tự ẩn từ hệ thống
    url = f"https://telegram.org{token}/sendMessage"
    payload = {
        "chat_id": chat_id,
        "text": text
    }
    print(f"\n📤 Đang gửi dữ liệu báo cáo về Telegram...")
    try:
        # Sử dụng phương thức POST trực tiếp truyền payload an toàn
        res = requests.post(url, data=payload, timeout=15)
        print(f" 🗳️ Mã phản hồi nhận được từ Telegram: {res.status_code}")
        if res.status_code != 200:
            print(f" 📄 Chi tiết phản hồi lỗi: {res.text}")
    except Exception as e:
        print(f"❌ Kết nối mạng thất bại hoặc URL bị lỗi cấu trúc: {e}")

def call_orthogonal_agent(prompt_text):
    """Gọi Endpoint /v1/run theo đúng cấu trúc payload chuẩn của Unified API"""
    url = "https://orthogonal.com"
    headers = {
        "Authorization": f"Bearer {ORTHOGONAL_API_KEY}",
        "Content-Type": "application/json"
    }
    # Cấu trúc payload chuẩn tương thích 100% với endpoint /v1/run để giải quyết lỗi 405
    payload = {
        "prompt": prompt_text
    }
    
    print("\n📡 Đang gửi yêu cầu phân tích dữ liệu tới Orthogonal API...")
    try:
        response = requests.post(url, json=payload, headers=headers, timeout=30)
        print(f" 🗳️ Mã phản hồi nhận được từ Orthogonal: {response.status_code}")
        
        if response.status_code != 200:
            print(f" 📄 Chi tiết phản hồi lỗi từ Orthogonal: {response.text}")
            return None
            
        data = response.json()
        # Trích xuất dữ liệu trả về từ Agent dựa trên cấu trúc mô hình
        return data.get("result") or data.get("output") or "Không có kết quả trả về từ Agent."
        
    except Exception as e:
        print(f"❌ Lỗi kết nối hoặc xử lý dữ liệu Python: {str(e)}")
        return None

def main():
    print("🤖 Khởi động tiến trình Agent Trend Hunter...")
    
    if not all([ORTHOGONAL_API_KEY, token, chat_id]):
        print("❌ Lỗi: Cấu hình hệ thống Secrets đang trống hoặc thiếu biến.")
        sys.exit(1)
        
    prompt_query = "Find the top 3 trending TikTok videos and top 3 trending YouTube Shorts right now. Just return titles and clean links."
    raw_report = call_orthogonal_agent(prompt_query)
    
    if not raw_report:
        raw_report = "⚠️ Hệ thống không thể thu thập dữ liệu xu hướng từ đối tác trong lượt quét này."
        
    telegram_report = (
        "🔥 BÁO CÁO XU HƯỚNG TIKTOK & SHORTS 🔥\n\n"
        f"{raw_report}\n\n"
        "⚡ Hệ thống vận hành tự động qua GitHub Actions."
    )
    
    send_telegram_message(telegram_report)
    print("🎉 Toàn bộ tiến trình hoàn tất!")

if __name__ == "__main__":
    main()
