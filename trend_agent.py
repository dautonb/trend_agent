import os
import requests
import sys

# Đọc cấu hình từ GitHub
ORTHOGONAL_API_KEY = os.getenv("ORTHOGONAL_API_KEY")
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

# Tự động dọn dẹp khoảng trắng, ký tự rác
clean_token = str(TELEGRAM_TOKEN).strip().replace("*", "")
clean_chat_id = str(TELEGRAM_CHAT_ID).strip().replace("*", "")

def send_telegram_message(text):
    """Hàm gửi tin nhắn Telegram an toàn"""
    url = f"https://telegram.org{clean_token}/sendMessage"
    payload = {
        "chat_id": clean_chat_id,
        "text": text
    }
    print(f"📤 Đang gửi tin nhắn qua Telegram đến ID {clean_chat_id}...")
    try:
        res = requests.post(url, json=payload)
        print(f" 🗳️ Mã phản hồi Telegram: {res.status_code}")
        if res.status_code != 200:
            print(f" 📄 Chi tiết lỗi Telegram: {res.text}")
    except Exception as e:
        print(f"❌ Không thể kết nối vật lý đến Telegram: {e}")

def call_orthogonal_agent(prompt_text):
    """Hàm gọi API Orthogonal và phân tích dữ liệu linh hoạt"""
    url = "https://orthogonal.com"
    headers = {
        "Authorization": f"Bearer {ORTHOGONAL_API_KEY}",
        "Content-Type": "application/json"
    }
    payload = {
        "prompt": prompt_text,
        "limit": 5
    }
    
    print("\n📡 Đang gọi Orthogonal API...")
    try:
        response = requests.post(url, json=payload, headers=headers)
        print(f" 🗳️ Mã phản hồi Orthogonal: {response.status_code}")
        
        if response.status_code != 200:
            error_msg = f"⚠️ Lỗi API Orthogonal (Mã {response.status_code}): {response.text[:200]}"
            send_telegram_message(error_msg)
            return None
            
        data = response.json()
        
        # IN TOÀN BỘ DỮ LIỆU ĐỂ KIỂM TRA TRONG LOG GITHUB
        print("📄 CẤU TRÚC DỮ LIỆU TRẢ VỀ THỰC TẾ:")
        print(data)
        
        # Thử nghiệm bóc tách linh hoạt các dạng cấu trúc dữ liệu JSON khác nhau
        results = data.get("results") or data.get("data") or data.get("output")
        
        if not results:
            # Nếu Orthogonal trả về dạng chuỗi văn bản trực tiếp
            if isinstance(data, dict) and "result" in data:
                return str(data["result"])
            return "Trống dữ liệu: Orthogonal không trả về danh sách kết quả mảng."
            
        if isinstance(results, str):
            return results
            
        # Nếu trả về dạng danh sách mảng chuẩn
        report_lines = []
        for idx, item in enumerate(results, 1):
            if isinstance(item, dict):
                title = item.get("title") or item.get("description") or "Không có tiêu đề"
                link = item.get("url") or item.get("link") or "#"
                report_lines.append(f"{idx}. {title}\n🔗 Link: {link}")
            else:
                report_lines.append(f"{idx}. {str(item)}")
                
        return "\n\n".join(report_lines)
        
    except Exception as e:
        print(f"❌ Lỗi xử lý Python: {str(e)}")
        send_telegram_message(f"❌ Agent bị sập do lỗi xử lý code: {str(e)}")
        return None

def main():
    print("🤖 Khởi động Agent Trend Hunter...")
    
    # Kiểm tra Key nhanh
    if not all([ORTHOGONAL_API_KEY, TELEGRAM_TOKEN, TELEGRAM_CHAT_ID]):
        print("❌ Thất bại: Thiếu biến Secrets.")
        sys.exit(1)
        
    prompt_query = "Find the top 3 trending TikTok videos and top 3 trending YouTube Shorts right now."
    raw_report = call_orthogonal_agent(prompt_query)
    
    if not raw_report:
        raw_report = "⚠️ Không thể phân tích xu hướng hoặc API đối tác trả về rỗng."
        
    telegram_report = (
        "🔥 BÁO CÁO XU HƯỚNG TIKTOK & SHORTS 🔥\n\n"
        f"{raw_report}\n\n"
        "⚡ Vận hành tự động qua GitHub Actions."
    )
    
    # Ép buộc phải gửi tin nhắn về Telegram bằng mọi giá
    send_telegram_message(telegram_report)
    print("🎉 Tiến trình hoàn tất thành công!")

if __name__ == "__main__":
    main()
