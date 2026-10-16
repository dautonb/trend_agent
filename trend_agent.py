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
    """
    Duyệt đệ quy qua toàn bộ Object/List để tìm giá trị của key đầu tiên khớp danh sách.
    """
    if isinstance(data, dict):
        for key, value in data.items():
            if key.lower() in target_keys and value:
                if isinstance(value, str) and value.strip():
                    return value.strip()
        # Tìm tiếp trong các dict/list con
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

    # Danh sách các tên field tiêu đề phổ biến
    title_keys = [
        "title",
        "name",
        "caption",
        "text",
        "description",
        "summary",
        "headline",
    ]
    # Danh sách các tên field đường dẫn phổ biến
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
