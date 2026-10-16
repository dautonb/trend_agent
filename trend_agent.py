import os
import re
import sys
import requests

# Nạp trực tiếp biến cấu hình từ GitHub Actions / Environment
ORTHOGONAL_API_KEY = os.getenv("ORTHOGONAL_API_KEY")
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")


def extract_clean_token(raw_token):
    """Trích xuất token Telegram chuẩn ngay cả khi người dùng dán kèm URL."""
    if not raw_token:
        return ""
    raw_str = str(raw_token).strip()
    match = re.search(r"(\d+:[A-Za-z0-9_-]+)", raw_str)
    if match:
        return match.group(1)
    return raw_str.replace(" ", "")


token = extract_clean_token(TELEGRAM_TOKEN)
chat_id = str(TELEGRAM_CHAT_ID).strip() if TELEGRAM_CHAT_ID else ""


def send_telegram_message(text):
    """Gửi tin nhắn báo cáo qua Telegram Bot API."""
    # SỬA LỖI 1: Thêm 'api.' và tiền tố 'bot' vào URL Telegram
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    payload = {"chat_id": chat_id, "text": text}

    print("\n📤 Đang gửi dữ liệu báo cáo về Telegram...")
    try:
        res = requests.post(url, json=payload, timeout=15)
        print(f" 🗳️ Mã phản hồi nhận được từ Telegram: {res.status_code}")
        if res.status_code != 200:
            print(f" 📄 Chi tiết phản hồi lỗi: {res.text}")
    except Exception as e:
        print(f"❌ Kết nối mạng thất bại hoặc URL bị lỗi cấu trúc: {e}")


def call_orthogonal_agent(prompt_text):
    url = "https://api.orthogonal.com/v1/search"
    headers = {
        "Authorization": f"Bearer {ORTHOGONAL_API_KEY}",
        "Content-Type": "application/json",
    }
    payload = {"prompt": prompt_text, "limit": 3}

    print("\n📡 Đang gửi yêu cầu phân tích dữ liệu tới Orthogonal API...")
    try:
        response = requests.post(
            url, json=payload, headers=headers, timeout=30
        )
        print(
            f" 🗳️ Mã phản hồi nhận được từ Orthogonal: {response.status_code}"
        )

        if response.status_code != 200:
            print(
                f" 📄 Chi tiết phản hồi lỗi từ Orthogonal: {response.text}"
            )
            return None

        data = response.json()

        # In log thực tế ra console của GitHub Actions để kiểm tra cấu trúc
        print(f"🔍 Cấu trúc dữ liệu JSON trả về: {data}")

        results = data.get("results", [])
        if not results:
            return "Không tìm thấy xu hướng TikTok & Shorts nào mới trong lượt quét này."

        report_lines = []
        for idx, item in enumerate(results, 1):
            # Tự động lấy tiêu đề theo nhiều key phổ biến khác nhau
            title = (
                item.get("title")
                or item.get("name")
                or item.get("text")
                or item.get("caption")
                or "Không có tiêu đề"
            )

            # Tự động lấy URL theo nhiều key phổ biến khác nhau
            link = (
                item.get("url")
                or item.get("link")
                or item.get("web_url")
                or "#"
            )

            report_lines.append(f"{idx}. {title}\n🔗 Link: {link}")

        return "\n\n".join(report_lines)

    except Exception as e:
        print(f"❌ Lỗi kết nối hoặc xử lý dữ liệu Python: {str(e)}")
        return None


def main():
    print("🤖 Khởi động tiến trình Agent Trend Hunter...")

    if not all([ORTHOGONAL_API_KEY, token, chat_id]):
        print("❌ Lỗi: Cấu hình hệ thống Secrets đang trống hoặc thiếu biến.")
        sys.exit(1)

    prompt_query = (
        "Find trending TikTok videos and YouTube Shorts right now."
    )
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
