"""
Google Workspace CLI (gws) 封裝模組。
統一 Gmail 與 Google Calendar 的呼叫邏輯。
"""
import json
import subprocess
from datetime import datetime


def run_gws(cmd_list):
    """執行 gws CLI 指令並回傳 JSON 結果。"""
    try:
        result = subprocess.run(
            cmd_list,
            capture_output=True,
            text=True,
            check=True,
            shell=True,
            encoding="utf-8",
            errors="replace",
            timeout=30,
        )
        return json.loads(result.stdout)
    except Exception as e:
        return {"error": str(e)}


def fetch_unread_emails(max_results=3):
    """取得未讀郵件的主旨清單。"""
    emails = run_gws([
        "gws", "gmail", "users", "messages", "list",
        "--params",
        json.dumps({"userId": "me", "q": "is:unread newer_than:1d", "maxResults": max_results}),
        "--format", "json",
    ])

    results = []
    if "messages" in emails:
        for msg in emails["messages"]:
            detail = run_gws([
                "gws", "gmail", "users", "messages", "get",
                "--params",
                json.dumps({"userId": "me", "id": msg["id"]}),
                "--format", "json",
            ])
            headers = detail.get("payload", {}).get("headers", [])
            subject = next(
                (h["value"] for h in headers if h["name"] == "Subject"),
                "無標題",
            )
            sender = next(
                (h["value"] for h in headers if h["name"] == "From"),
                "(未知寄件者)",
            )
            results.append({"subject": subject, "sender": sender})
    return results


def fetch_today_events():
    """取得今日的 Google Calendar 行程。"""
    today = datetime.now().strftime("%Y-%m-%d")
    cal = run_gws([
        "gws", "calendar", "events", "list",
        "--params",
        json.dumps({
            "calendarId": "primary",
            "timeMin": f"{today}T00:00:00Z",
            "timeMax": f"{today}T23:59:59Z",
            "singleEvents": True,
            "orderBy": "startTime",
        }),
        "--format", "json",
    ])

    results = []
    if "items" in cal:
        for item in cal["items"]:
            start = item.get("start", {}).get(
                "dateTime", item.get("start", {}).get("date", "")
            )
            time_str = start[11:16] if "T" in start else "全天"
            results.append({
                "time": time_str,
                "summary": item.get("summary", "(無標題)"),
            })
    return results
