import asyncio
import datetime
import os
import sys
import redis
import json

# Add project root to sys.path
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PROJECT_ROOT not in sys.path:
    sys.path.append(PROJECT_ROOT)

from dotenv import load_dotenv
load_dotenv(os.path.join(PROJECT_ROOT, ".env"))

from services.metrics import get_summary_stats
from core.config import log, REDIS_URL, TASK_QUEUE, REPORTS_BASE_URL

async def generate_usage_report():
    """Generates the HTML usage report for Antigravity model quota and performance."""
    log("🔄 Generating Usage Report...")
    
    # Check Redis for status
    try:
        r = redis.from_url(REDIS_URL, decode_responses=True)
        q_len = r.llen(TASK_QUEUE)
    except Exception as e:
        log(f"⚠️ Redis Connection Check Failed during report gen: {e}")
        q_len = "Unknown"

    try:
        stats = await get_summary_stats(days=7)
    except Exception as e:
        import traceback
        log(f"❌ Failed to get metrics for report: {e}\n{traceback.format_exc()}")
        return False
    
    if not stats:
        log("⚠️ No metrics found, using zero stats for report.")
        stats = {
            "total_tokens": 0,
            "avg_latency": 0,
            "status_distribution": {"success": 0},
            "model_usage": {}
        }

    total_tokens = stats.get("total_tokens") or 0
    avg_latency = stats.get("avg_latency") or 0
    dist = stats.get("status_distribution") or {}
    
    success_count = dist.get("success", 0)
    error_count = dist.get("error", 0)
    total_count = success_count + error_count
    success_rate = (success_count / total_count * 100) if total_count > 0 else 0
    model_usage = stats.get("model_usage", {})
    
    quota_limit = 1000000 
    usage_percent = (total_tokens / quota_limit * 100) if quota_limit > 0 else 0

    # Create model usage rows
    model_rows_html = ""
    if model_usage:
        for model, tokens in model_usage.items():
            model_rows_html += f"""
            <div style="display: flex; justify-content: space-between; padding: 10px 0; border-bottom: 1px solid rgba(255,255,255,0.05);">
                <span style="color: #f1f5f9;">{model}</span>
                <span style="color: #38bdf8; font-weight: 500;">{tokens:,}</span>
            </div>
            """
    else:
        model_rows_html = '<div style="color: #64748b; font-size: 0.9rem; padding: 10px 0;">尚無各模型使用數據</div>'

    html_content = f"""
<!DOCTYPE html>
<html lang="zh-TW">
<head>
    <meta charset="UTF-8">
    <title>Antigravity 系統診斷與使用報告</title>
    <style>
        body {{ font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; background-color: #0f172a; color: #f8fafc; padding: 40px; line-height: 1.6; }}
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
            
            <div style="margin-top: 25px;">
                <div class="label" style="margin-bottom: 10px;">各模型使用細節</div>
                {model_rows_html}
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
                        <span class="status-pill {'bg-success' if q_len == 0 or q_len == 'Unknown' else 'bg-error'}">
                            {('運行正常' if q_len == 0 or q_len == 'Unknown' else '序列壅塞')}
                        </span>
                    </div>
                </div>
            </div>
        </div>

        <div style="text-align: center; color: #64748b; font-size: 0.8rem; margin-top: 20px;">
            報告更新時間: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')} | LazyBridge OS
        </div>
    </div>
</body>
</html>
"""
    report_path = os.path.join(PROJECT_ROOT, "reports/usage_report.html")
    os.makedirs(os.path.dirname(report_path), exist_ok=True)
    try:
        with open(report_path, "w", encoding="utf-8") as f:
            f.write(html_content)
        log(f"✅ Usage report updated: {report_path}")
        return True
    except Exception as e:
        log(f"❌ Failed to write report file: {e}")
        return False

if __name__ == "__main__":
    asyncio.run(generate_usage_report())
