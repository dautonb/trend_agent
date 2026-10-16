import os
import requests
import sys

# Đọc cấu hình từ biến môi trường của GitHub
ORTHOGONAL_API_KEY = os.getenv("ORTHOGONAL_API_KEY")
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

# Kiểm tra xem GitHub đã truyền đủ Secret vào chưa
print("🔍 [KIỂM TRA CẤU HÌNH SECRETS]")
print(f" - ORTHOGONAL_API_KEY: {'Đã nhận ✅' if ORTHOGONAL_API_KEY else 'TRỐNG/THIẾU ❌'}")
print(f" - TELEGRAM_TOKEN: {'Đã nhận ✅' if TELEGRAM_TOKEN else 'TRỐNG/THIẾU ❌'}")
print(f" - TELEGRAM_CHAT_ID: {'Đã nhận ✅' if TELEGRAM_CHAT_ID else 'TRỐNG/THIẾU ❌'}")

if not all([ORTHOGONAL_API_KEY, TELEGRAM_TOKEN, TELEGRAM_CHAT_ID]):
    print("❌ Lỗi: Thiếu cấu hình Secrets trên GitHub. Vui lòng kiểm tra lại Bước 1!")
    sys.exit(1)

def call_orthogonal_agent(prompt):
    url = "https://orthogonal.com"
    headers = {
        "Authorization": f"Bearer {ORTHOGONAL_API_KEY}",
        "Content-Type": "application/json"
    }
    payload = {"prompt": prompt}
    
    print("\n📡 Đang gửi yêu cầu quét xu hướng tới Orthogonal API...")
    try:
        response = requests.post(url, json=payload, headers=headers)
        print(f" 🗳️ Phản hồi từ Orthogonal - Mã trạng thái (Status Code): {response.status_code}")
        response.raise_for_status()
        return response.json().get("result", "Không tìm thấy trường 'result' trong dữ liệu trả về.")
    except Exception as e:
        print(f"❌ Lỗi kết nối Orthogonal: {str(e)}")
        if 'response' in locals() and response.text:
            print(f" 📄 Chi tiết lỗi hệ thống: {response.text}")
        return None

def send_telegram_message(text):
    url = f"https://telegram.org{TELEGRAM_TOKEN}/sendMessage"
    payload = {
        "chat_id": TELEGRAM_CHAT_ID,
        "text": text,
        "parse_mode": "Markdown"
    }
    print("📤 Đang chuyển tiếp báo cáo về ứng dụng Telegram...")
    try:
        res = requests.post(url, json=payload)
        print(f" 🗳️ Phản hồi từ Telegram - Mã trạng thái (Status Code): {res.status_code}")
        if res.status_code != 200:
            print(f" 📄 Chi tiết lỗi Telegram: {res.text}")
    except Exception as e:
        print(f"❌ Không thể kết nối tới máy chủ Telegram: {e}")

def main():
    print("🤖 Khởi động tiến trình Agent Trend Hunter...")
    
    prompt_request = (
        "Find the top 3 trending TikTok videos and top 3 trending YouTube Shorts right now. "
        "For each video, provide the title/description and video URL."
    )
    
    raw_report = call_orthogonal_agent(prompt_request)
    
    if not raw_report:
        print("🛑 Tiến trình dừng lại do không lấy được dữ liệu xu hướng.")
        sys.exit(1)
        
    telegram_report = (
        "🔥 *BÁO CÁO XU HƯỚNG TIKTOK & SHORTS* 🔥\n\n"
        f"{raw_report}\n\n"
        "⚡ _Hệ thống tự động vận hành định kỳ._"
    )
    
    send_telegram_message(telegram_report)
    print("🎉 Tiến trình xử lý hoàn tất!")

if __name__ == "__main__":
    main()
