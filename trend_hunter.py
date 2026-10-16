import json
import os
import re
import sys
import requests

# Nạp trực tiếp biến cấu hình từ GitHub
ORTHOGONAL_API_KEY = os.getenv("ORTHOGONAL_API_KEY")
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")


def extract_clean_token(raw_token):
    """Tự động trích xuất chuỗi mã Token thô kể cả khi người dùng dán nhầm nguyên đường link"""
    if not raw_token:
        return ""
    raw_str = str(raw_token).strip()
    match = re.search(r"(\d+:[A-Za-z0-9_-]+)", raw_str)
    if match:
        return match.group(1)
    return raw_str.replace(" ", "")


token = extract_clean_token(TELEGRAM_TOKEN)
chat_id = str(TELEGRAM_CHAT_ID).strip() if TELEGRAM_CHAT_ID else ""


def find_key_recursive(data, target_keys: list):
    """Duyệt đệ quy tìm giá trị của key khớp danh sách."""
    if isinstance(data, dict):
        for key, value in data.items():
            if key.lower() in target_keys and value:
                if isinstance(value, str) and value.strip():
                    return value.strip()
        for value in data.values():
            res = find_key_recursive(value, target_keys)
            if res:
                return res
    elif isinstance(data, list):
        for item in data:
            res = find_key_recursive(item, target_keys)
            if res:
                return res
    return None


def send_telegram_message(text):
    """Gửi dữ liệu qua phương thức truyền tải độc lập an toàn"""
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    payload = {
        "chat_id": chat_id,
        "text": text,
        "parse_mode": "HTML",
        "disable_web_page_preview": True,
    }

    print("\n📤 Đang gửi dữ liệu báo cáo về Telegram...")
    try:
        res = requests.post(url, json=payload, timeout=20)
        print(f" 🗳️ Mã phản hồi nhận được từ Telegram: {res.status_code}")
        if res.status_code != 200:
            print(f" 📄 Chi tiết phản hồi lỗi: {res.text}")
            # Dự phòng gửi dạng text thường nếu HTML bị lỗi thẻ đóng
            payload.pop("parse_mode")
            requests.post(url, json=payload, timeout=20)
    except Exception as e:
        print(f"❌ Kết nối mạng thất bại hoặc URL bị lỗi cấu trúc: {e}")


def call_orthogonal_agent(prompt_text):
    """Sử dụng Endpoint /v1/search để truy vấn các công cụ Tech & AI Tools mới"""
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
        print("\n🔍 CẤU TRÚC JSON PHẢN HỒI:")
        print(json.dumps(data, indent=2, ensure_ascii=False))

        # Tìm danh sách kết quả
        results = None
        if isinstance(data, list):
            results = data
        elif isinstance(data, dict):
            for key in ["results", "data", "items", "output", "hits"]:
                if key in data and isinstance(data[key], list):
                    results = data[key]
                    break

        if results is None and isinstance(data, dict):
            results = [data]

        if not results:
            return "Không tìm thấy công cụ AI/Tech mới nào trong lượt quét này."

        report_lines = []
        for idx, item in enumerate(results, 1):
            if isinstance(item, str):
                title = f"Công cụ Tech #{idx}"
                desc = item
                link = "#"
            else:
                title = (
                    find_key_recursive(item, ["name", "title", "headline"])
                    or f"Công cụ AI / Tech #{idx}"
                )
                desc = (
                    find_key_recursive(
                        item, ["description", "summary", "text", "caption"]
                    )
                    or "Công cụ hỗ trợ tự động hóa và phát triển ứng dụng."
                )
                link = (
                    find_key_recursive(
                        item, ["url", "link", "web_url", "href", "source"]
                    )
                    or "#"
                )

            link_html = (
                f'<a href="{link}">Truy cập Website / Docs</a>'
                if link != "#"
                else "<i>Đang cập nhật link</i>"
            )

            block = (
                f"🛠️ <b>{idx}. {title}</b>\n"
                f"📝 <b>Mô tả:</b> {desc[:250]}\n"
                f"🔗 <b>Tài liệu:</b> {link_html}"
            )
            report_lines.append(block)

        return "\n\n───────────────\n\n".join(report_lines)

    except Exception as e:
        print(f"❌ Lỗi kết nối hoặc xử lý dữ liệu Python: {str(e)}")
        return None


def main():
    print("🤖 Khởi động tiến trình Agent Trend Hunter...")

    if not all([ORTHOGONAL_API_KEY, token, chat_id]):
        print("❌ Lỗi: Cấu hình hệ thống Secrets đang trống hoặc thiếu biến.")
        sys.exit(1)

    # Thay đổi mục tiêu prompt: Tập trung tìm kiếm công cụ AI & API thay vì TikTok
    prompt_query = (
        "Find top 3 innovative AI tools, developer APIs, or automation frameworks released recently. "
        "Provide their name, description, and website URL."
    )

    raw_report = call_orthogonal_agent(prompt_query)

    if not raw_report:
        raw_report = "⚠️ Hệ thống không thể thu thập dữ liệu công cụ từ đối tác trong lượt quét này."

    telegram_report = (
        "⚡ <b>BÁO CÁO CÔNG NGHỆ & AI TOOLS HÀNG NGÀY</b> ⚡\n\n"
        f"{raw_report}\n\n"
        "⚡ Hệ thống vận hành tự động qua GitHub Actions."
    )

    send_telegram_message(telegram_report)
    print("🎉 Toàn bộ tiến trình hoàn tất!")


if __name__ == "__main__":
    main()
