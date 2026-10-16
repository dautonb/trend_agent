import os
import requests

# Lấy các biến môi trường cấu hình từ GitHub Secrets
ORTHOGONAL_API_KEY = os.getenv("ORTHOGONAL_API_KEY")
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

def call_orthogonal_agent(prompt):
    """Gọi Unified API của Orthogonal để AI tự tìm và xử lý endpoint phù hợp"""
    url = "https://orthogonal.com"
    headers = {
        "Authorization": f"Bearer {ORTHOGONAL_API_KEY}",
        "Content-Type": "application/json"
    }
    # Lợi thế của Orthogonal là bạn chỉ cần đưa prompt bằng văn bản tự nhiên, 
    # hệ thống tự định tuyến đến API TikTok/YouTube Shorts tốt nhất trong catalog.
    payload = {
        "prompt": prompt
    }
    
    try:
        response = requests.post(url, json=payload, headers=headers)
        response.raise_for_status()
        return response.json().get("result", "Không có dữ liệu trả về.")
    except Exception as e:
        return f"Lỗi gọi Orthogonal API: {str(e)}"

def send_telegram_message(text):
    """Gửi báo cáo kết quả về Bot Telegram"""
    url = f"https://telegram.org{TELEGRAM_TOKEN}/sendMessage"
    payload = {
        "chat_id": TELEGRAM_CHAT_ID,
        "text": text,
        "parse_mode": "Markdown"
    }
    try:
        requests.post(url, json=payload)
    except Exception as e:
        print(f"Lỗi gửi Telegram: {e}")

def main():
    print("🤖 Agent Trend Hunter bắt đầu hoạt động...")
    
    # Kịch bản yêu cầu Orthogonal quét cả TikTok lẫn Shorts
    prompt_request = (
        "Find the top 3 trending TikTok videos and top 3 trending YouTube Shorts right now. "
        "For each video, provide the title/description, video URL, and a brief 1-sentence summary "
        "of what the trend or audio is about based on its transcript."
    )
    
    # 1. Thu thập và phân tích trend từ Orthogonal
    raw_report = call_orthogonal_agent(prompt_request)
    
    # 2. Biên tập lại định dạng tin nhắn cho đẹp mắt
    telegram_report = (
        "🔥 *BÁO CÁO XU HƯỚNG TIKTOK & SHORTS* 🔥\n"
        f"📅 _Cập nhật lúc: Chạy tự động định kỳ_\n\n"
        f"{raw_report}\n\n"
        "⚡ _Agent được vận hành bởi Orthogonal & GitHub Actions._"
    )
    
    # 3. Bắn về Telegram
    send_telegram_message(telegram_report)
    print("✅ Đã gửi báo cáo về Telegram thành công!")

if __name__ == "__main__":
    main()
