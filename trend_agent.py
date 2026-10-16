import json
import os
import re
import sys
import requests

ORTHOGONAL_API_KEY = os.getenv("ORTHOGONAL_API_KEY")
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")


def extract_clean_token(raw_token):
    if not raw_token:
        return ""
    raw_str = str(raw_token).strip()
    match = re.search(r"(\d+:[A-Za-z0-9_-]+)", raw_str)
    return match.group(1) if match else raw_str.replace(" ", "")


token = extract_clean_token(TELEGRAM_TOKEN)
chat_id = str(TELEGRAM_CHAT_ID).strip() if TELEGRAM_CHAT_ID else ""


def send_telegram_message(text):
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    payload = {"chat_id": chat_id, "text": text}
    try:
        res = requests.post(url, json=payload, timeout=15)
        if res.status_code != 200:
            print(f"❌ Lỗi gửi Telegram: {res.text}")
    except Exception as e:
        print(f"❌ Lỗi kết nối Telegram: {e}")


def extract_url(item):
    """Tìm đường link từ mọi key khả thi trong object."""
    if isinstance(item, str) and item.startswith("http"):
        return item
    if isinstance(item, dict):
        for key in [
            "url",
            "link",
            "web_url",
            "href",
            "video_url",
            "source",
            "uri",
        ]:
            val = item.get(key)
            if val and isinstance(val, str) and val.startswith("http"):
                return val
        # Quét sâu hơn vào các dict con (như item['metadata']['url'])
        for val in item.values():
            if isinstance(val, dict):
                sub_url = extract_url(val)
                if sub_url != "#":
                    return sub_url
    return "#"


def extract_title(item):
    """Tìm tiêu đề/nội dung từ mọi key khả thi trong object."""
    if isinstance(item, str):
        return item
    if isinstance(item, dict):
        for key in [
            "title",
            "name",
            "text",
            "caption",
            "description",
            "summary",
            "query",
        ]:
            val = item.get(key)
            if val and isinstance(val, str):
                return val
    return "Không tìm thấy tiêu đề"


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

        if response.status_code != 200:
            return f"⚠️ API trả về lỗi status {response.status_code}: {response.text}"

        data = response.json()

        # In log JSON chi tiết trên GitHub Actions
        print("🔍 FULL API RESPONSE:")
        print(json.dumps(data, indent=2, ensure_ascii=False))

        # Lấy danh sách kết quả (hỗ trợ nhiều chuẩn response khác nhau)
        results = (
            data.get("results")
            or data.get("data")
            or data.get("items")
            or data
        )

        if not isinstance(results, list):
            # Nếu trả về dạng dict đơn, gửi thẳng JSON về để debug
            return f"ℹ️ Cấu trúc dữ liệu nhận được:\n{json.dumps(data, indent=2, ensure_ascii=False)[:3000]}"

        if not results:
            return "Không tìm thấy xu hướng TikTok & Shorts nào mới trong lượt quét này."

        report_lines = []
        for idx, item in enumerate(results, 1):
            title = extract_title(item)
            link = extract_url(item)
            report_lines.append(f"{idx}. {title}\n🔗 Link: {link}")

        return "\n\n".join(report_lines)

    except Exception as e:
        print(f"❌ Lỗi xử lý Python: {str(e)}")
        return f"❌ Lỗi hệ thống: {str(e)}"


def main():
    if not all([ORTHOGONAL_API_KEY, token, chat_id]):
        print("❌ Lỗi: Cấu hình Secrets chưa đủ.")
        sys.exit(1)

    prompt_query = (
        "Find trending TikTok videos and YouTube Shorts right now."
    )
    raw_report = call_orthogonal_agent(prompt_query)

    telegram_report = (
        "🔥 BÁO CÁO XU HƯỚNG TIKTOK & SHORTS 🔥\n\n"
        f"{raw_report}\n\n"
        "⚡ Hệ thống vận hành tự động qua GitHub Actions."
    )

    send_telegram_message(telegram_report)


if __name__ == "__main__":
    main()
