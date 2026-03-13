import asyncio
import datetime
from services.metrics import get_summary_stats
from core.config import log

async def generate_html_report():
    stats = await get_summary_stats(days=7)
    if not stats:
        log("❌ Failed to get metrics for report.")
        return

    total_tokens = stats.get("total_tokens", 0)
    avg_latency = stats.get("avg_latency", 0)
    dist = stats.get("status_distribution", {})
    
    success_count = dist.get("success", 0)
    error_count = dist.get("error", 0)
    total_count = success_count + error_count
    success_rate = (success_count / total_count * 100) if total_count > 0 else 0
    
    # Define a mock quota for visualization if not found
    quota_limit = 1000000  # 1M tokens
    usage_percent = (total_tokens / quota_limit * 100) if quota_limit > 0 else 0

    html_content = f"""
<!DOCTYPE html>
<html lang="zh-TW">
<head>
    <meta charset="UTF-8">
    <title>Antigravity 模型使用報告</title>
    <style>
        body {{ font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; background-color: #0f172a; color: #f8fafc; padding: 40px; }}
        .card {{ background: rgba(30, 41, 59, 0.7); border-radius: 16px; padding: 24px; box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1); max-width: 600px; margin: 0 auto; border: 1px solid rgba(255, 255, 255, 0.1); }}
        h1 {{ color: #38bdf8; text-align: center; }}
        .metric {{ margin: 20px 0; }}
        .label {{ color: #94a3b8; font-size: 0.9rem; }}
        .value {{ font-size: 1.5rem; font-weight: bold; color: #f1f5f9; }}
        .progress-container {{ background: #334155; border-radius: 8px; height: 12px; margin-top: 8px; }}
        .progress-bar {{ background: linear-gradient(90deg, #38bdf8, #818cf8); height: 100%; border-radius: 8px; width: {usage_percent}%; }}
        .status-success {{ color: #10b981; }}
        .status-error {{ color: #ef4444; }}
    </style>
</head>
<body>
    <div class="card">
        <h1>📊 Antigravity 使用報告</h1>
        <div class="metric">
            <div class="label">📅 最近 7 天 Token 消耗</div>
            <div class="value">{total_tokens:,} / {quota_limit:,}</div>
            <div class="progress-container"><div class="progress-bar"></div></div>
        </div>
        <div class="metric">
            <div class="label">⏱️ 平均延遲</div>
            <div class="value">{avg_latency:.2f} ms</div>
        </div>
        <div class="metric">
            <div class="label">📈 任務狀態</div>
            <div class="value">
                <span class="status-success">成功: {success_count}</span> | 
                <span class="status-error">失敗: {error_count}</span>
                (成功率: {success_rate:.1f}%)
            </div>
        </div>
        <div style="text-align: center; color: #64748b; font-size: 0.8rem; margin-top: 30px;">
            報告生成時間: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
        </div>
    </div>
</body>
</html>
"""
    with open("reports/usage_report.html", "w", encoding="utf-8") as f:
        f.write(html_content)
    log("✅ Usage report generated: reports/usage_report.html")

if __name__ == "__main__":
    asyncio.run(generate_html_report())
