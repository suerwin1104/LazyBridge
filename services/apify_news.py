"""
Apify 新聞趨勢抓取模組。
使用 Google Search Scraper Actor 取得即時新聞。
"""
import time

import requests
from datetime import datetime

from core.config import get_apify_token


def get_apify_news():
    """透過 Apify Google Search Scraper 抓取趨勢新聞，回傳格式化文字。"""
    token = get_apify_token()
    if not token:
        return "\n⚠️ 未設定 Apify Token，無法抓取趨勢新聞。\n"

    actor_id = "apify/google-search-scraper"
    run_url = (
        f"https://api.apify.com/v2/acts/{actor_id.replace('/', '~')}/runs?token={token}"
    )

    today_str = datetime.now().strftime("%Y-%m-%d")
    payload = {
        "queries": f"{today_str} 科技趨勢 產業分析 重大新聞",
        "maxPagesPerQuery": 1,
        "resultsPerPage": 3,
        "tbs": "qdr:d",  # 過去 24 小時
        "proxyConfiguration": {"useApifyProxy": True},
    }

    try:
        resp = requests.post(run_url, json=payload, timeout=30).json()
        run_id = resp.get("data", {}).get("id")
        dataset_id = resp.get("data", {}).get("defaultDatasetId")

        if not run_id:
            return "\n❌ 無法啟動新聞抓取 Actor。\n"

        # 等待執行結束（最多 2 分鐘）
        status_url = f"https://api.apify.com/v2/actor-runs/{run_id}?token={token}"
        for _ in range(12):
            time.sleep(10)
            status_resp = requests.get(status_url).json()
            status = status_resp.get("data", {}).get("status")
            if status == "SUCCEEDED":
                break
            if status in ["FAILED", "ABORTED", "TIMED-OUT"]:
                return "\n❌ 新聞抓取執行失敗。\n"
        else:
            return "\n⏱️ 新聞抓取執行超時。\n"

        # 讀取結果
        results_url = (
            f"https://api.apify.com/v2/datasets/{dataset_id}/items?token={token}"
        )
        results = requests.get(results_url).json()

        news_list = []
        if results and isinstance(results, list):
            organic = results[0].get("organicResults", [])
            for item in organic[:3]:
                title = item.get("title")
                url = item.get("url")
                news_list.append(f"📌 **{title}**\n🔗 {url}")

        if news_list:
            return "\n\n**【每日趨勢分析】**\n" + "\n\n".join(news_list)
        return "\n今日無可用趨勢分析新聞。\n"
    except Exception as e:
        return f"\n⚠️ 新聞抓取發生錯誤: {str(e)}\n"
