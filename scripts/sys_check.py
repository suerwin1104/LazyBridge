import asyncio
import datetime
import os
import sys
import redis
import json

# Add project root to sys.path
sys.path.append(os.getcwd())

from services.metrics import get_summary_stats
from core.config import log, REDIS_URL, TASK_QUEUE, REPORTS_BASE_URL

async def run_diagnostics():
    log("--- System Diagnostics ---")
    
    # Check Redis
    try:
        r = redis.from_url(REDIS_URL)
        q_len = r.llen(TASK_QUEUE)
        log(f"✅ Redis Connected. Queue '{TASK_QUEUE}' length: {q_len}")
        if q_len > 0:
            log(f"⚠️ Warning: There are {q_len} tasks waiting in the queue. Worker might be slow or stuck.")
    except Exception as e:
        log(f"❌ Redis Connection Failed: {e}")

    # Generate Report
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
    
    quota_limit = 1000000 
    usage_percent = (total_tokens / quota_limit * 100) if quota_limit > 0 else 0

    html_content = f"""
<!DOCTYPE html>
<html lang="zh-TW">
<head>
    <meta charset="UTF-8">
    <title>Antigravity 系統診斷與使用報告</title>
    <style>
        body {{ font-family: 'Inter', sans-serif; background-color: #0f172a; color: #f8fafc; padding: 40px; line-height: 1.6; }}
        .container {{ max-width: 800px; margin: 0 auto; }}
        .header {{ text-align: center; margin-bottom: 40px; }}
        .card {{ background: rgba(30, 41, 59, 0.7); border-radius: 20px; padding: 30px; border: 1px solid rgba(255, 255, 255, 0.1); backdrop-filter: blur(10px); margin-bottom: 20px; }}
        h1, h2 {{ color: #38bdf8; margin-top: 0; }}
        .metric-grid {{ display: grid; grid-template-columns: 1fr 1fr; gap: 20px; }}
        .metric {{ margin-bottom: 20px; }}
        .label {{ color: #94a3b8; font-size: 0.85rem; text-transform: uppercase; letter-spacing: 0.05em; }}
        .value {{ font-size: 1.8rem; font-weight: 600; color: #f1f5f9; }}
        .progress-container {{ background: #334155; border-radius: 10px; height: 14px; margin-top: 10px; overflow: hidden; }}
        .progress-bar {{ background: linear-gradient(90deg, #38bdf8, #818cf8); height: 100%; width: {min(usage_percent, 100)}%; transition: width 0.5s ease; }}
        .status-pill {{ display: inline-block; padding: 4px 12px; border-radius: 20px; font-size: 0.8rem; font-weight: 600; }}
        .bg-success {{ background: rgba(16, 185, 129, 0.2); color: #10b981; }}
        .bg-error {{ background: rgba(239, 68, 68, 0.2); color: #ef4444; }}
        .status-box {{ display: flex; align-items: center; gap: 10px; margin-top: 10px; }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>📊 系統運行報告</h1>
            <p style="color: #64748b;">Antigravity 模型監控與序列診斷</p>
        </div>

        <div class="card">
            <h2>⚡ 模型額度消耗 (Token Usage)</h2>
            <div class="metric">
                <div class="label">最近 7 天累計消耗</div>
                <div class="value">{total_tokens:,} <span style="font-size: 1rem; color: #64748b;">/ {quota_limit:,}</span></div>
                <div class="progress-container"><div class="progress-bar"></div></div>
                <div style="text-align: right; font-size: 0.85rem; color: #94a3b8; margin-top: 5px;">已使用 {usage_percent:.1f}%</div>
            </div>
        </div>

        <div class="metric-grid">
            <div class="card">
                <h2>📈 任務效能</h2>
                <div class="metric">
                    <div class="label">平均延遲</div>
                    <div class="value">{avg_latency:.0f} <span style="font-size: 1rem;">ms</span></div>
                </div>
                <div class="metric">
                    <div class="label">任務成功率</div>
                    <div class="value">{success_rate:.1f}%</div>
                </div>
            </div>
            <div class="card">
                <h2>🛠️ 序列狀態</h2>
                <div class="metric">
                    <div class="label">目前待處理任務</div>
                    <div class="value">{q_len}</div>
                    <div class="status-box">
                        <span class="status-pill {'bg-success' if q_len == 0 else 'bg-error'}">
                            {'運行正常' if q_len < 5 else '序列壅塞'}
                        </span>
                    </div>
                </div>
            </div>
        </div>

        <div style="text-align: center; color: #64748b; font-size: 0.8rem; margin-top: 20px;">
            報告生成時間: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')} | LazyBridge OS
        </div>
    </div>
</body>
</html>
"""
    report_path = "reports/usage_report.html"
    os.makedirs("reports", exist_ok=True)
    with open(report_path, "w", encoding="utf-8") as f:
        f.write(html_content)
    log(f"✅ Usage report generated: {report_path}")

if __name__ == "__main__":
    asyncio.run(run_diagnostics())
