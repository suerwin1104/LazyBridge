"""
每日晨報組裝模組。
整合 Google Workspace（Gmail、Calendar）與 Apify 趨勢新聞。
"""
from datetime import datetime

from services.google_workspace import fetch_unread_emails, fetch_today_events
from services.apify_news import get_apify_news


def get_briefing():
    """產生每日重點摘要文字，包含未讀郵件、今日行程與趨勢新聞。"""
    today = datetime.now().strftime("%Y-%m-%d")

    # 1. 未讀郵件
    emails = fetch_unread_emails(max_results=3)
    if emails:
        email_text = "".join(f"📧 {e['subject']}\n" for e in emails)
    else:
        email_text = "今日無未讀郵件\n"

    # 2. 今日行程
    events = fetch_today_events()
    if events:
        cal_text = "".join(f"⏰ {e['time']}: {e['summary']}\n" for e in events)
    else:
        cal_text = "今日無行程\n"

    # 3. 趨勢新聞
    print("正在抓取趨勢新聞...")
    news_text = get_apify_news()

    # 4. 組合報告
    report = (
        f"**📅 {today} 每日重點摘要**\n\n"
        f"**【未讀郵件】**\n{email_text}\n"
        f"**【今日行程】**\n{cal_text}"
        f"{news_text}\n\n"
        f"*新聞彙整已由 AI 即時生成並發送至您的 Discord。*"
    )
    return report


if __name__ == "__main__":
    try:
        report = get_briefing()
        print("RESULT_START")
        print(report)
        print("RESULT_END")
    except Exception as e:
        print(f"Error in main: {e}")
