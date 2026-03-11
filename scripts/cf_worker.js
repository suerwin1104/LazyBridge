/**
 * Cloudflare Worker: Multi-Service Dynamic Link Hub Redirector
 * 
 * 功能: 
 * 1. 識別請求路徑 (例如 /hbms/)。
 * 2. 從 KV 讀取對應服務的最新隨機網址 (例如 link_hbms)。
 * 3. 將訪問者 302 跳轉到該網址。
 * 
 * 設定方式:
 * - 在 Cloudflare Worker 設定中，綁定一個 KV Namespace 命名為 'LINKS'。
 */

export default {
    async fetch(request, env, ctx) {
        const url = new URL(request.url);
        const path = url.pathname;

        let serviceKey = "link_report"; // 預設服務 (8080)
        let finalPath = path;

        // --- 路由邏輯 (依照優先順序判斷) ---

        if (path.startsWith("/hbms/")) {
            serviceKey = "link_hbms";
            // 如果需要去除前綴，可以開啟下一行
            // finalPath = path.replace(/^\/hbms/, ''); 
        } else if (path.startsWith("/other/")) {
            serviceKey = "link_other";
        }

        // 1. 從 KV 讀取目標網址
        const targetBaseUrl = await env.LINKS.get(serviceKey);

        if (!targetBaseUrl) {
            return new Response(`⚠️ 尚未同步服務 '${serviceKey}'。請確保本地已啟動對應服務並執行 link_sync_multi.py。`, {
                status: 503,
                headers: { "Content-Type": "text/plain; charset=utf-8" }
            });
        }

        // 2. 組合最終跳轉網址 (確保斜線正確)
        const search = url.search;
        const redirectUrl = targetBaseUrl.replace(/\/$/, '') + finalPath + search;

        return Response.redirect(redirectUrl, 302);
    },
};
