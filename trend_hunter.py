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
# 2. CÁC HÀM XỬ LÝ DỮ LIỆU VÀ TRÍCH XUẤT NÂNG CAO
# ---------------------------------------------------------------------------
def clean_telegram_token(raw_token: str) -> str:
    """Làm sạch và trích xuất chuỗi Telegram Token chuẩn."""
    if not raw_token:
        return ""
    token_str = str(raw_token).strip()
    match = re.search(r"(\d+:[A-Za-z0-9_-]+)", token_str)
    return match.group(1) if match else token_str.replace(" ", "")


def find_key_recursive(data, target_keys: list):
    """Duyệt đệ quy tìm giá trị của key khớp danh sách."""
    if isinstance(data, dict):
        for key, value in data.items():
            if key.lower() in target_keys and value:
                if isinstance(value, str) and value.strip():
                    return value.strip()
                elif isinstance(value, list) and value:
                    return value
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


def format_item_to_html(idx: int, item) -> str:
    """Bóc tách chi tiết và định dạng từng xu hướng thành khối HTML Telegram."""
    if isinstance(item, str):
        return f"<b>{idx}. Nội dung xu hướng:</b>\n{item}"

    # Trích xuất dữ liệu cơ bản
    title = find_key_recursive(item, ["title", "topic", "name", "headline", "caption"]) or "Chủ đề xu hướng mới"
    url = find_key_recursive(item, ["url", "link", "web_url", "video_url", "source"]) or "#"
    summary = find_key_recursive(item, ["description", "summary", "snippet", "text", "content"]) or "Chưa có mô tả chi tiết."
    
    # Trích xuất hoặc tạo Insight / Ý tưởng sáng tạo
    insight = find_key_recursive(item, ["insight", "why_trending", "reason"]) or "Nội dung mang tính giải trí cao, bắt trend âm thanh hoặc thách thức (challenge) đang lan truyền mạnh."
    action_idea = find_key_recursive(item, ["idea", "hook", "actionable_takeaway"]) or "Tạo video ngắn 15s tái hiện lại tình huống trên với góc nhìn cá nhân hoặc hài hước."
    
    # Trích xuất Hashtags
    hashtags = find_key_recursive(item, ["hashtags", "tags"])
    if isinstance(hashtags, list):
        tag_str = " ".join([f"#{t.replace('#', '')}" for t in hashtags])
    elif isinstance(hashtags, str):
        tag_str = hashtags
    else:
        tag_str = "#Viral #TikTokTrend #ShortsTrend #TrendingNow"

    # Xây dựng block HTML
    link_html = f'<a href="{url}">Xem chi tiết / Link gốc</a>' if url != "#" else '<i>Không có link trực tiếp</i>'
    
    html_block = (
        f"🔥 <b>{idx}. {title}</b>\n"
        f"📝 <b>Tóm tắt:</b> {summary[:250]}\n"
        f"💡 <b>Tại sao HOT:</b> {insight}\n"
        f"🎬 <b>Gợi ý góc làm video:</b> {action_idea}\n"
        f"🏷️ <b>Hashtags:</b> <code>{tag_str}</code>\n"
        f"🔗 <b>Nguồn:</b> {link_html}"
    )
    return html_block


# ---------------------------------------------------------------------------
# 3. HÀM GỬI TELEGRAM (HỖ TRỢ HTML)
# ---------------------------------------------------------------------------
def send_telegram_html_message(token: str, chat_id: str, html_text: str):
    """Gửi báo cáo về Telegram với định dạng HTML định dạng đẹp."""
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    payload = {
        "chat_id": chat_id,
        "text": html_text,
        "parse_mode": "HTML",
        "disable_web_page_preview": True,
    }

    print("\n📤 Đang gửi dữ liệu báo cáo HTML về Telegram...")
    try:
        response = requests.post(url, json=payload, timeout=20)
        print(f" 🗳️ Mã trạng thái Telegram: {response.status_code}")
        if response.status_code != 200:
            print(f" ❌ Chi tiết lỗi Telegram: {response.text}")
            # Dự phòng gửi lại dạng text thường nếu HTML bị lỗi thẻ đóng
            payload.pop("parse_mode")
            requests.post(url, json=payload, timeout=20)
        else:
            print(" 🎉 Gửi báo cáo Telegram thành công!")
    except Exception as e:
        print(f" ❌ Kết nối tới Telegram thất bại: {e}")


# ---------------------------------------------------------------------------
# 4. HÀM TƯƠNG TÁC ORTHOGONAL API CHUYÊN SÂU
# ---------------------------------------------------------------------------
def fetch_deep_trending_analysis(api_key: str) -> str:
    """Truy vấn dữ liệu xu hướng kèm phân tích chuyên sâu từ Orthogonal API."""
    endpoint = "https://api.orthogonal.com/v1/search"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }
    
    # SỬA LỖI: Dùng Triple-Quotes (""") để viết chuỗi nhiều dòng an toàn
    prompt_query = """Identify top 3 viral video trends on TikTok and YouTube Shorts today. For each trend, provide:
1. Trend Title and Summary
2. Direct URL or link if available
3. Why it is trending (Insight)
4. A creative content idea or hook for a creator to replicate it
5. Relevant hashtags."""
    
    payload = {"prompt": prompt_query, "limit": 3}

    print("\n📡 Đang gửi yêu cầu phân tích chuyên sâu tới Orthogonal API...")
    try:
        res = requests.post(endpoint, json=payload, headers=headers, timeout=40)
        print(f" 🗳️ Mã trạng thái Orthogonal: {res.status_code}")

        if res.status_code != 200:
            return f"⚠️ API trả về lỗi code {res.status_code}:\n<code>{res.text[:300]}</code>"

        json_data = res.json()

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
            block = format_item_to_html(index, item)
            report_blocks.append(block)

        return "\n\n───────────────\n\n".join(report_blocks)

    except requests.exceptions.Timeout:
        return "❌ Lỗi: Quá thời gian chờ phản hồi từ Orthogonal API (Timeout)."
    except Exception as e:
        return f"❌ Lỗi xử lý dữ liệu hệ thống: {str(e)}"


# ---------------------------------------------------------------------------
# 5. LUỒNG CHẠY CHÍNH (MAIN FUNCTION)
# ---------------------------------------------------------------------------
def main():
    print("============================================")
    print("🤖 KHỞI ĐỘNG HỆ THỐNG AGENT TREND HUNTER PRO")
    print("============================================")

    bot_token = clean_telegram_token(TELEGRAM_TOKEN)
    target_chat_id = str(TELEGRAM_CHAT_ID).strip() if TELEGRAM_CHAT_ID else ""

    if not all([ORTHOGONAL_API_KEY, bot_token, target_chat_id]):
        print("❌ LỖI HỆ THỐNG: Một hoặc nhiều biến môi trường (Secrets) bị thiếu!")
        sys.exit(1)

    # 1. Thu thập dữ liệu xu hướng & phân tích
    analysis_report = fetch_deep_trending_analysis(ORTHOGONAL_API_KEY)

    # 2. Đóng gói báo cáo hoàn chỉnh với định dạng HTML
    final_html_report = (
        "🚀 <b>BÁO CÁO XU HƯỚNG TIKTOK & SHORTS HÀNG NGÀY</b> 🚀\n"
        "<i>Phân tích tự động bởi Agent Trend Hunter</i>\n\n"
        f"{analysis_report}\n\n"
        "⚡ <i>Hệ thống vận hành tự động qua GitHub Actions.</i>"
    )

    # 3. Gửi tin nhắn về Telegram
    send_telegram_html_message(bot_token, target_chat_id, final_html_report)
    print("============================================")
    print("🎉 HOÀN THÀNH TIẾN TRÌNH TỰ ĐỘNG!")


if __name__ == "__main__":
    main()
