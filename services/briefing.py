"""
每日晨報組裝模組。
整合 Google Workspace（Gmail、Calendar）與 Apify 趨勢新聞。
"""
import os
import re
from datetime import datetime
from services.google_workspace import fetch_unread_emails, fetch_today_events
from services.apify_news import get_apify_news
from core.config import log

BRIEFING_HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="zh-TW">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>每日晨報 - {date}</title>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;600&display=swap" rel="stylesheet">
    <style>
        :root {{
            --primary: #38bdf8;
            --bg: #0f172a;
            --card-bg: rgba(30, 41, 59, 0.7);
            --text: #f8fafc;
        }}
        body {{
            font-family: 'Inter', sans-serif;
            background: var(--bg);
            color: var(--text);
            margin: 0;
            padding: 40px 20px;
            display: flex;
            flex-direction: column;
            align-items: center;
            min-height: 100vh;
            background-image: 
                radial-gradient(at 0% 0%, rgba(56, 189, 248, 0.15) 0, transparent 50%), 
                radial-gradient(at 100% 100%, rgba(56, 189, 248, 0.1) 0, transparent 50%);
        }}
        .container {{
            max-width: 900px;
            width: 100%;
        }}
        header {{
            text-align: center;
            margin-bottom: 50px;
            animation: fadeInDown 0.8s ease-out;
        }}
        h1 {{
            font-size: 3rem;
            margin: 0;
            background: linear-gradient(to right, #38bdf8, #818cf8);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            font-weight: 600;
        }}
        .date {{
            font-size: 1.2rem;
            color: #94a3b8;
            margin-top: 10px;
        }}
        .section {{
            background: var(--card-bg);
            backdrop-filter: blur(12px);
            -webkit-backdrop-filter: blur(12px);
            border: 1px solid rgba(255, 255, 255, 0.1);
            border-radius: 24px;
            padding: 30px;
            margin-bottom: 30px;
            box-shadow: 0 10px 30px -10px rgba(0, 0, 0, 0.5);
            transition: transform 0.3s ease, box-shadow 0.3s ease;
            animation: fadeInUp 0.8s ease-out both;
        }}
        .section:hover {{
            transform: translateY(-5px);
            box-shadow: 0 20px 40px -15px rgba(0, 0, 0, 0.6);
        }}
        h2 {{
            color: var(--primary);
            font-size: 1.5rem;
            margin-top: 0;
            display: flex;
            align-items: center;
            gap: 12px;
            border-bottom: 1px solid rgba(56, 189, 248, 0.2);
            padding-bottom: 10px;
        }}
        .content {{
            line-height: 1.8;
            font-size: 1.1rem;
            color: #cbd5e1;
        }}
        .item {{
            margin-bottom: 15px;
            padding-left: 20px;
            position: relative;
        }}
        .item::before {{
            content: "•";
            color: var(--primary);
            position: absolute;
            left: 0;
        }}
        footer {{
            text-align: center;
            margin-top: 50px;
            color: #64748b;
            font-size: 0.9rem;
            font-style: italic;
        }}
        @keyframes fadeInDown {{
            from {{ opacity: 0; transform: translateY(-30px); }}
            to {{ opacity: 1; transform: translateY(0); }}
        }}
        @keyframes fadeInUp {{
            from {{ opacity: 0; transform: translateY(30px); }}
            to {{ opacity: 1; transform: translateY(0); }}
        }}
    </style>
</head>
<body>
    <div class="container">
        <header>
            <h1>Morning Briefing</h1>
            <div class="date">{date}</div>
        </header>
        
        {sections_html}

        <footer>
            *本報告由 Antigravity AI 即時生成。*
        </footer>
    </div>
</body>
</html>
"""

def get_briefing_data(include_emails=True, include_calendar=True, include_news=True):
    """獲取結構化晨報數據。"""
    today = datetime.now().strftime("%Y-%m-%d")
    data = {
        "date": today,
        "sections": []
    }

    # 1. 未讀郵件
    if include_emails:
        emails = fetch_unread_emails(max_results=3)
        content = [f"📧 {e['subject']}" for e in emails] if emails else ["今日無未讀郵件"]
        data["sections"].append({
            "title": "未讀郵件",
            "icon": "📩",
            "items": content
        })

    # 2. 今日行程
    if include_calendar:
        events = fetch_today_events()
        content = [f"⏰ {e['time']}: {e['summary']}" for e in events] if events else ["今日無行程"]
        data["sections"].append({
            "title": "今日行程",
            "icon": "📅",
            "items": content
        })

    # 3. 趨勢新聞
    if include_news:
        log("正在抓取趨勢新聞...")
        categories = {
            "全球重點科技新聞": f"{today} 全球 重點 科技 新聞",
            "台灣重點新聞": f"{today} 台灣 重點 新聞"
        }
        news_text = get_apify_news(categories=categories)
        # 簡單解析新聞文本轉為 items
        news_items = [n.strip() for n in news_text.split('\n') if n.strip() and not n.startswith('**')]
        data["sections"].append({
            "title": "趨勢新聞",
            "icon": "🚀",
            "items": news_items[:10]  # 限制數量
        })

    return data

def generate_briefing_html(data):
    """生成 HTML 版本的晨報。"""
    sections_html = ""
    for idx, section in enumerate(data["sections"]):
        parsed_items = []
        for item in section["items"]:
            if "http" in item:
                url_start = item.find("http")
                prefix = item[:url_start]
                url = item[url_start:].strip()
                item_html = f'{prefix}<a href="{url}" target="_blank" style="color: #60A5FA; text-decoration: none; border-bottom: 1px dotted #60A5FA; padding-bottom: 2px;">{url}</a>'
                parsed_items.append(f'<div class="item">{item_html}</div>')
            else:
                parsed_items.append(f'<div class="item">{item}</div>')
        
        items_html = "".join(parsed_items)
        sections_html += f"""
        <div class="section" style="animation-delay: {idx * 0.15}s">
            <h2>{section['icon']} {section['title']}</h2>
            <div class="content">
                {items_html}
            </div>
        </div>
        """
    
    html = BRIEFING_HTML_TEMPLATE.format(date=data["date"], sections_html=sections_html)
    
    os.makedirs("reports", exist_ok=True)
    filename = f"reports/briefing_{data['date'].replace('-', '')}.html"
    with open(filename, "w", encoding="utf-8") as f:
        f.write(html)
    
    return filename

def format_briefing_text(data):
    """將結構化數據轉換為純文字格式。"""
    report_sections = [f"**📅 {data['date']} 每日重點摘要**\n"]
    
    for section in data["sections"]:
        items_text = "\n".join(section["items"])
        report_sections.append(f"**【{section['title']}】**\n{items_text}")
    
    report_sections.append("\n*新聞彙整已由 AI 即時生成並發送至您的 Discord。*")
    return "\n".join(report_sections)

def get_briefing(include_emails=True, include_calendar=True, include_news=True):
    """相容舊版的純文字晨報。"""
    data = get_briefing_data(include_emails, include_calendar, include_news)
    return format_briefing_text(data)

if __name__ == "__main__":
    test_data = get_briefing_data()
    path = generate_briefing_html(test_data)
    print(f"Generated HTML briefing at: {path}")
