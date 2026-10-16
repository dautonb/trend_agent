import os
import requests
import sys

# Đọc cấu hình từ biến môi trường của GitHub Actions
ORTHOGONAL_API_KEY = os.getenv("ORTHOGONAL_API_KEY")
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

print("🔍 [KIỂM TRA CẤU HÌNH SECRETS]")
print(f" - ORTHOGONAL_API_KEY: {'Đã nhận ✅' if ORTHOGONAL_API_KEY else 'TRỐNG/THIẾU ❌'}")
print(f" - TELEGRAM_TOKEN: {'Đã nhận ✅' if TELEGRAM_TOKEN else 'TRỐNG/THIẾU ❌'}")
print(f" - TELEGRAM_CHAT_ID: {'Đã nhận ✅' if TELEGRAM_CHAT_ID else 'TRỐNG/THIẾU ❌'}")

if not all([ORTHOGONAL_API_KEY, TELEGRAM_TOKEN, TELEGRAM_CHAT_ID]):
    print("❌ Lỗi: Thiếu cấu hình Secrets trên GitHub. Không thể tiếp tục.")
    sys.exit(1)

def call_orthogonal_agent(prompt_text):
    # Sửa đổi endpoint sang /v1/search để xử lý prompt tự nhiên theo tài liệu Orthogonal
    url = "https://api.orthogonal.com/v1/search"
    headers = {
        "Authorization": f"Bearer {ORTHOGONAL_API_KEY}",
        "Content-Type": "application/json"
    }
    # Payload chuẩn theo đặc tả API của Orthogonal dành cho Agentic Search
    payload = {
        "prompt": prompt_text,
        "limit": 5
    }
    
    print("\n📡 Đang gửi yêu cầu quét xu hướng tới Orthogonal API...")
    try:
        response = requests.post(url, json=payload, headers=headers)
        print(f" 🗳️ Phản hồi từ Orthogonal - Mã trạng thái (Status Code): {response.status_code}")
        
        if response.status_code != 200:
            print(f" 📄 Chi tiết phản hồi từ hệ thống: {response.text}")
            return None
            
        data = response.json()
        # Trích xuất dữ liệu mảng kết quả trả về từ Unified API
        results = data.get("results", [])
        if not results:
            return "Không tìm thấy xu hướng TikTok & Shorts nào mới trong lượt quét này."
            
        # Gom kết quả thành khối văn bản sạch
        report_lines = []
        for idx, item in enumerate(results, 1):
            title = item.get("title", "Không có tiêu đề")
            source = item.get("source_title", "Nguồn tổng hợp")
            link = item.get("url", "#")
            report_lines.append(f"{idx}. [{source}] {title}\n🔗 Liên kết: {link}")
            
        return "\n\n".join(report_lines)
        
    except Exception as e:
        print(f"❌ Lỗi kết nối Orthogonal: {str(e)}")
        return None

def send_telegram_message(text):
    url = f"https://telegram.org{TELEGRAM_TOKEN}/sendMessage"
    
    # Loại bỏ parse_mode="Markdown" để tránh lỗi sập đường truyền 400 Bad Request
    payload = {
        "chat_id": str(TELEGRAM_CHAT_ID).strip(),
        "text": text
    }
    print("📤 Đang chuyển tiếp báo cáo về ứng dụng Telegram...")
    try:
        res = requests.post(url, json=payload)
        print(f" 🗳️ Phản hồi từ Telegram - Mã trạng thái (Status Code): {res.status_code}")
        if res.status_code != 200:
            print(f" 📄 Chi tiết lỗi cấu hình Telegram: {res.text}")
    except Exception as e:
        print(f"❌ Không thể kết nối tới máy chủ Telegram: {e}")

def main():
    print("🤖 Khởi động tiến trình Agent Trend Hunter...")
    
    prompt_query = "Find the top 3 trending TikTok videos and top 3 trending YouTube Shorts right now."
    
    raw_report = call_orthogonal_agent(prompt_query)
    
    if not raw_report:
        print("🛑 Tiến trình dừng lại do lỗi xử lý dữ liệu từ đối tác.")
        sys.exit(1)
        
    telegram_report = (
        "🔥 BÁO CÁO XU HƯỚNG TIKTOK & SHORTS 🔥\n\n"
        f"{raw_report}\n\n"
        "⚡ Hệ thống tự động vận hành định kỳ qua GitHub Actions."
    )
    
    send_telegram_message(telegram_report)
    print("🎉 Tiến trình kết thúc thành công!")

if __name__ == "__main__":
    main()
