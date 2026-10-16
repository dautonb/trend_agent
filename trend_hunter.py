import json
import os
import re
import sys
import requests

# ---------------------------------------------------------------------------
# 1. CẤU HÌNH BIẾN MÔI TRƯỜNG (GITHUB SECRETS)
# ---------------------------------------------------------------------------
ORTHOGONAL_API_KEY = os.getenv("ORTHOGONAL_API_KEY")
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")


# ---------------------------------------------------------------------------
# 2. CÁC HÀM XỬ LÝ DỮ LIỆU & TIỆN ÍCH
# ---------------------------------------------------------------------------
def clean_telegram_token(raw_token: str) -> str:
    """Làm sạch và trích xuất đúng chuỗi Telegram Token dạng ID:SECRET."""
    if not raw_token:
        return ""
    token_str = str(raw_token).strip()
    match = re.search(r"(\d+:[A-Za-z0-9_-]+)", token_str)
    return match.group(1) if match else token_str.replace(" ", "")


def find_key_recursive(data, target_keys: list):
    """Duyệt đệ quy qua toàn bộ Object/List để tìm giá trị của key đầu tiên khớp danh sách."""
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


def extract_item_info(item):
    """Trích xuất tiêu đề và đường dẫn từ một mục kết quả."""
    if isinstance(item, str):
        if item.startswith("http"):
            return "Liên kết xu hướng", item
        return item, "#"

    title_keys = [
        "title",
        "name",
        "caption",
        "text",
        "description",
        "summary",
        "headline",
    ]
    url_keys = [
        "url",
        "link",
        "web_url",
        "video_url",
        "href",
        "source",
        "uri",
        "canonicalurl",
    ]

    title = find_key_recursive(item, title_keys) or "Không có tiêu đề"
    url = find_key_recursive(item, url_keys) or "#"

    return title, url


# ---------------------------------------------------------------------------
# 3. HÀM TƯƠNG TÁC TELEGRAM API
# ---------------------------------------------------------------------------
def send_telegram_message(token: str, chat_id: str, text: str):
    """Gửi báo cáo về Telegram Bot."""
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    payload = {
        "chat_id": chat_id,
        "text": text,
        "disable_web_page_preview": False,
    }

    print("\n📤 Đang gửi dữ liệu báo cáo về Telegram...")
    try:
        response = requests.post(url, json=payload, timeout=20)
        print(f" 🗳️ Mã trạng thái Telegram: {response.status_code}")
        if response.status_code != 200:
            print(f" ❌ Chi tiết lỗi Telegram: {response.text}")
        else:
            print(" 🎉 Gửi báo cáo Telegram thành công!")
    except Exception as e:
        print(f" ❌ Kết nối tới Telegram thất bại: {e}")


# ---------------------------------------------------------------------------
# 4. HÀM GỌI ORTHOGONAL API
# ---------------------------------------------------------------------------
def fetch_trending_data(api_key: str, prompt: str) -> str:
    """Truy vấn dữ liệu từ Orthogonal API và định dạng kết quả."""
    endpoint = "https://api.orthogonal.com/v1/search"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }
    payload = {"prompt": prompt, "limit": 5}

    print(f"\n📡 Đang gửi yêu cầu phân tích tới Orthogonal API ({endpoint})...")
    try:
        res = requests.post(
            endpoint, json=payload, headers=headers, timeout=35
        )
        print(f" 🗳️ Mã trạng thái Orthogonal: {res.status_code}")

        if res.status_code != 200:
            print(f" 📄 Phản hồi lỗi: {res.text}")
            return f"⚠️ API trả về lỗi code {res.status_code}:\n{res.text[:500]}"

        json_data = res.json()

        # In log cấu trúc JSON thực tế ra Console của GitHub Actions
        print("\n🔍 CẤU TRÚC JSON PHẢN HỒI:")
        print(json.dumps(json_data, indent=2, ensure_ascii=False))

        items = None
        if isinstance(json_data, list):
            items = json_data
        elif isinstance(json_data, dict):
            for key in ["results", "data", "items", "output", "hits"]:
                if key in json_data and isinstance(json_data[key], list):
                    items = json_data[key]
                    break

        if items is None and isinstance(json_data, dict):
            items = [json_data]

        if not items:
            return "Không tìm thấy nội dung xu hướng nào trong lượt quét này."

        report_blocks = []
        for index, item in enumerate(items, 1):
            title, link = extract_item_info(item)
            report_blocks.append(f"{index}. {title}\n🔗 Link: {link}")

        return "\n\n".join(report_blocks)

    except requests.exceptions.Timeout:
        return "❌ Lỗi: Quá thời gian chờ phản hồi từ Orthogonal API (Timeout)."
    except Exception as e:
        print(f" ❌ Lỗi xử lý Python: {str(e)}")
        return f"❌ Lỗi xử lý dữ liệu hệ thống: {str(e)}"


# ---------------------------------------------------------------------------
# 5. LUỒNG CHẠY CHÍNH (MAIN FUNCTION)
# ---------------------------------------------------------------------------
def main():
    print("============================================")
    print("🤖 KHỞI ĐỘNG HỆ THỐNG AGENT TREND HUNTER")
    print("============================================")

    bot_token = clean_telegram_token(TELEGRAM_TOKEN)
    target_chat_id = str(TELEGRAM_CHAT_ID).strip() if TELEGRAM_CHAT_ID else ""

    if not all([ORTHOGONAL_API_KEY, bot_token, target_chat_id]):
        print("❌ LỖI HỆ THỐNG: Một hoặc nhiều biến môi trường (Secrets) bị thiếu!")
        print(
            f" - ORTHOGONAL_API_KEY: {'Có' if ORTHOGONAL_API_KEY else 'Trống'}"
        )
        print(f" - TELEGRAM_TOKEN: {'Có' if bot_token else 'Trống'}")
        print(f" - TELEGRAM_CHAT_ID: {'Có' if target_chat_id else 'Trống'}")
        sys.exit(1)

    prompt_query = "Find trending TikTok videos and YouTube Shorts right now."
    trend_data = fetch_trending_data(ORTHOGONAL_API_KEY, prompt_query)

    final_report = (
        "🔥 BÁO CÁO XU HƯỚNG TIKTOK & SHORTS 🔥\n\n"
        f"{trend_data}\n\n"
        "⚡ Hệ thống vận hành tự động qua GitHub Actions."
    )

    send_telegram_message(bot_token, target_chat_id, final_report)
    print("============================================")
    print("🎉 HOÀN THÀNH TIẾN TRÌNH TỰ ĐỘNG!")


if __name__ == "__main__":
    main()
