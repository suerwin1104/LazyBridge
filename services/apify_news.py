"""
Apify 新聞趨勢抓取模組。
使用 Google Search Scraper Actor 取得即時新聞。
"""
import time

import requests
from datetime import datetime

from core.config import get_apify_token


def get_apify_news(categories=None):
    """
    透過 Apify Google Search Scraper 抓取分類新聞。
    categories: 字典格式 {"標題1": "搜尋字串1", "標題2": "搜尋字串2"}
    """
    token = get_apify_token()
    if not token:
        return "\n⚠️ 未設定 Apify Token，無法抓取趨勢新聞。\n"

    if categories is None:
        today_str = datetime.now().strftime("%Y-%m-%d")
        categories = {"每日趨勢分析": f"{today_str} 科技趨勢 產業分析 重大新聞"}

    actor_id = "apify/google-search-scraper"
    run_url = (
        f"https://api.apify.com/v2/acts/{actor_id.replace('/', '~')}/runs?token={token}"
    )

    # 將多個查詢合併，一行一個
    queries_list = list(categories.values())
    queries_str = "\n".join(queries_list)

    payload = {
        "queries": queries_str,
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

        all_news_text = []
        if results and isinstance(results, list):
            # 每一個 result 對應一個 query
            for i, category_title in enumerate(categories.keys()):
                if i < len(results):
                    organic = results[i].get("organicResults", [])
                    category_news = []
                    for item in organic[:3]:
                        title = item.get("title")
                        url = item.get("url")
                        category_news.append(f"📌 **{title}**\n🔗 {url}")
                    
                    if category_news:
                        all_news_text.append(f"**【{category_title}】**\n" + "\n\n".join(category_news))

        if all_news_text:
            return "\n\n" + "\n\n".join(all_news_text)
        return "\n今日無可用趨勢分析新聞。\n"
    except Exception as e:
        return f"\n⚠️ 新聞抓取發生錯誤: {str(e)}\n"

