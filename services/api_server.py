from aiohttp import web
import json
import os
from services.monitor import monitor
from services.local_rag import local_rag
from core.config import log, REPORTS_BASE_URL

async def handle_knowledge_export(request):
    """將本地知識庫打包成位元組流匯出。"""
    data = local_rag.export_knowledge()
    if data:
        return web.Response(body=data, content_type='application/octet-stream')
    return web.Response(status=404, text="No knowledge to export")

async def handle_knowledge_import(request):
    """接收外部知識庫位元組流並匯入。"""
    try:
        data = await request.read()
        success = local_rag.import_knowledge(data)
        if success:
            return web.json_response({"status": "success", "message": "Knowledge synced"})
        return web.json_response({"status": "error", "message": "Import failed"}, status=500)
    except Exception as e:
        return web.json_response({"status": "error", "message": str(e)}, status=500)

async def handle_stats(request):
    """回傳系統即時統計數據。"""
    stats = await monitor.get_stats()
    return web.json_response(stats)

async def handle_index(request):
    """回傳儀表板首頁。"""
    # 使用絕對路徑確保讀取正確
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    dashboard_path = os.path.join(base_dir, 'web', 'dashboard.html')
    if os.path.exists(dashboard_path):
        return web.FileResponse(dashboard_path)
    return web.Response(text=f"<h1>Dashboard not found at {dashboard_path}</h1>", content_type='text/html')

async def start_api_server(port=8088):
    """啟動 aiohttp 伺服器。"""
    app = web.Application()
    
    # 設置 API 路由
    app.router.add_get('/api/stats', handle_stats)
    app.router.add_get('/api/knowledge/export', handle_knowledge_export)
    app.router.add_post('/api/knowledge/import', handle_knowledge_import)
    app.router.add_get('/', handle_index)
    
    # 設置靜態檔案路由 (用於查看報表)
    if not os.path.exists('reports'):
        os.makedirs('reports', exist_ok=True)
    app.router.add_static('/reports/', path='reports', name='reports')
    
    runner = web.AppRunner(app)
    await runner.setup()
    
    # 允許從 0.0.0.0 連線 (Tailscale/LAN 支援)
    site = web.TCPSite(runner, '0.0.0.0', port)
    
    log(f"🌐 [Omni-View] API Server & Dashboard 啟動於埠號: {port}")
    await site.start()
    
    return runner
