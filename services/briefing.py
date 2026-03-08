"""
每日晨報組裝模組。
整合 Google Workspace（Gmail、Calendar）與 Apify 趨勢新聞。
"""
from datetime import datetime

from services.google_workspace import fetch_unread_emails, fetch_today_events
from services.apify_news import get_apify_news


def get_briefing(include_emails=True, include_calendar=True, include_news=True):
    """產生每日重點摘要文字，支援參數化自訂內容。"""
    today = datetime.now().strftime("%Y-%m-%d")
    report_sections = [f"**📅 {today} 每日重點摘要**\n"]

    # 1. 未讀郵件
    if include_emails:
        emails = fetch_unread_emails(max_results=3)
        email_text = "".join(f"📧 {e['subject']}\n" for e in emails) if emails else "今日無未讀郵件\n"
        report_sections.append(f"**【未讀郵件】**\n{email_text}")

    # 2. 今日行程
    if include_calendar:
        events = fetch_today_events()
        cal_text = "".join(f"⏰ {e['time']}: {e['summary']}\n" for e in events) if events else "今日無行程\n"
        report_sections.append(f"**【今日行程】**\n{cal_text}")

    # 3. 趨勢新聞
    if include_news:
        print("正在抓取趨勢新聞...")
        news_text = get_apify_news()
        report_sections.append(news_text)

    # 4. 組合報告
    report_sections.append("\n*新聞彙整已由 AI 即時生成並發送至您的 Discord。*")
    return "\n".join(report_sections)


if __name__ == "__main__":
    try:
        report = get_briefing()
        print("RESULT_START")
        print(report)
        print("RESULT_END")
    except Exception as e:
        print(f"Error in main: {e}")
