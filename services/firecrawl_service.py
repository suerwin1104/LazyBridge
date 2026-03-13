"""
Firecrawl 整合服務 — 為 LazyBridge 提供 LLM 友好的網頁數據擷取能力

核心功能：
  1. Scrape  — 單頁抓取，產出乾淨 Markdown（取代 raw HTML）
  2. Crawl   — 全站爬取，自動將每一頁轉為 Markdown 並匯入 RAG
  3. Map     — 網站地圖偵察，快速列出所有 URL

設計方針：
  - 優先使用自架版 (Self-hosted)，免費且無 API 限制
  - 付費的 Cloud API 作為備援或 Agent 自主選擇
  - 所有抓取結果自動寫入 local_rag 知識庫
"""
import asyncio
import os
import re
from datetime import datetime
from typing import Dict, List, Optional
from core.config import log


# ==============================================================
#  設定
# ==============================================================

# 自架版 URL（Docker 本地部署）
FIRECRAWL_SELF_HOSTED_URL = os.getenv("FIRECRAWL_URL", "http://localhost:3002")

# Cloud API Key（可選，用於 Cloud 模式或備援）
FIRECRAWL_API_KEY = os.getenv("FIRECRAWL_API_KEY", "")

# 預設使用模式：self_hosted 或 cloud
FIRECRAWL_MODE = os.getenv("FIRECRAWL_MODE", "self_hosted")

# 爬取限制
MAX_CRAWL_PAGES = int(os.getenv("FIRECRAWL_MAX_PAGES", "50"))
CRAWL_TIMEOUT = int(os.getenv("FIRECRAWL_CRAWL_TIMEOUT", "300"))  # 秒


# ==============================================================
#  核心服務
# ==============================================================

class FirecrawlService:
    """
    Firecrawl 封裝服務。
    支援 self-hosted 和 cloud 兩種模式，並自動將結果匯入 local_rag。
    """

    def __init__(self):
        self._app = None

    def _get_client(self):
        """延遲初始化 Firecrawl client。"""
        if self._app is None:
            try:
                from firecrawl import FirecrawlApp
            except ImportError:
                raise RuntimeError(
                    "firecrawl-py 未安裝。請執行: pip install firecrawl-py"
                )

            if FIRECRAWL_MODE == "cloud" and FIRECRAWL_API_KEY:
                log("🔥 [Firecrawl] 使用 Cloud API 模式")
                self._app = FirecrawlApp(api_key=FIRECRAWL_API_KEY)
            else:
                log(f"🔥 [Firecrawl] 使用 Self-Hosted 模式: {FIRECRAWL_SELF_HOSTED_URL}")
                self._app = FirecrawlApp(
                    api_url=FIRECRAWL_SELF_HOSTED_URL,
                    api_key=FIRECRAWL_API_KEY or "fc-dummy"  # self-hosted 仍需傳 key
                )

        return self._app

    # ----------------------------------------------------------
    #  Scrape：單頁抓取
    # ----------------------------------------------------------

    async def scrape(
        self,
        url: str,
        formats: List[str] = None,
        inject_to_rag: bool = True
    ) -> Dict:
        """
        抓取單一 URL，回傳乾淨的 Markdown。

        Args:
            url: 目標 URL
            formats: 輸出格式，預設 ['markdown']
            inject_to_rag: 是否自動寫入 RAG 知識庫

        Returns:
            {"url": str, "markdown": str, "title": str, "status": str}
        """
        formats = formats or ["markdown"]

        try:
            app = self._get_client()
            log(f"🔥 [Firecrawl] Scraping: {url}")

            # 在 thread 中執行同步 API（避免阻塞 event loop）
            # SDK v2 使用 app.scrape
            result = await asyncio.to_thread(
                app.scrape, url, formats=formats
            )

            # 處理物件或字典回傳
            markdown = getattr(result, "markdown", "") or (result.get("markdown", "") if isinstance(result, dict) else "")
            metadata = getattr(result, "metadata", {}) or (result.get("metadata", {}) if isinstance(result, dict) else {})
            title = metadata.get("title", url) if isinstance(metadata, dict) else getattr(metadata, "title", url)

            if not markdown:
                return {
                    "url": url,
                    "markdown": "",
                    "title": title,
                    "status": "empty",
                    "message": "頁面無內容或無法解析"
                }

            # 自動寫入 RAG
            if inject_to_rag and markdown:
                await self._inject_to_rag(url, title, markdown)

            return {
                "url": url,
                "markdown": markdown,
                "title": title,
                "status": "success",
                "char_count": len(markdown)
            }

        except Exception as e:
            log(f"❌ [Firecrawl] Scrape 失敗: {e}")
            return {
                "url": url,
                "markdown": "",
                "title": "",
                "status": "error",
                "message": str(e)
            }

    # ----------------------------------------------------------
    #  Crawl：全站爬取
    # ----------------------------------------------------------

    async def crawl(
        self,
        url: str,
        max_pages: int = None,
        include_paths: List[str] = None,
        exclude_paths: List[str] = None,
        inject_to_rag: bool = True
    ) -> Dict:
        """
        爬取整個網站，將每一頁轉為 Markdown 並匯入 RAG。

        Args:
            url: 起始 URL
            max_pages: 最大頁數
            include_paths: 只爬取匹配的路徑 (glob pattern)
            exclude_paths: 排除的路徑 (glob pattern)
            inject_to_rag: 是否自動寫入 RAG

        Returns:
            {"url": str, "pages_crawled": int, "pages_injected": int, "status": str}
        """
        max_pages = max_pages or MAX_CRAWL_PAGES

        try:
            app = self._get_client()
            log(f"🔥 [Firecrawl] 開始全站爬取: {url} (最多 {max_pages} 頁)")

            params = {
                "limit": max_pages,
                "scrapeOptions": {"formats": ["markdown"]},
            }
            if include_paths:
                params["includePaths"] = include_paths
            if exclude_paths:
                params["excludePaths"] = exclude_paths

            # 使用同步 crawl（自帶 polling）
            # SDK v2 使用 app.crawl
            crawl_result = await asyncio.to_thread(
                app.crawl,
                url,
                limit=max_pages,
                scrape_options={"formats": ["markdown"]},
                include_paths=include_paths,
                exclude_paths=exclude_paths,
                poll_interval=5
            )

            # 處理結果 (crawl_result 可能包含 'data' 列表)
            pages = getattr(crawl_result, "data", []) or (crawl_result.get("data", []) if isinstance(crawl_result, dict) else [])
            pages_crawled = len(pages)
            pages_injected = 0

            if inject_to_rag and pages:
                documents = []
                metadatas = []

                for page in pages:
                    md = getattr(page, "markdown", "") or (page.get("markdown", "") if isinstance(page, dict) else "")
                    meta = getattr(page, "metadata", {}) or (page.get("metadata", {}) if isinstance(page, dict) else {})
                    
                    page_url = meta.get("sourceURL", "") if isinstance(meta, dict) else getattr(meta, "sourceURL", "")
                    page_title = meta.get("title", page_url) if isinstance(meta, dict) else getattr(meta, "title", page_url)

                    if md and len(md) > 50:
                        chunks = self._chunk_text(md, max_chunk_size=800)
                        for i, chunk in enumerate(chunks):
                            documents.append(chunk)
                            metadatas.append({
                                "text": chunk[:200],
                                "source": page_url,
                                "title": page_title,
                                "chunk_index": i,
                                "crawled_at": datetime.utcnow().isoformat(),
                                "type": "firecrawl_crawl"
                            })

                if documents:
                    from services.local_rag import local_rag
                    await local_rag.add_documents(documents, metadatas)
                    pages_injected = len(documents)
                    log(f"📚 [Firecrawl] 已將 {pages_injected} 個片段匯入 RAG 知識庫")

            log(f"✅ [Firecrawl] 全站爬取完成: {pages_crawled} 頁, {pages_injected} 片段已入庫")

            return {
                "url": url,
                "pages_crawled": pages_crawled,
                "pages_injected": pages_injected,
                "status": "success"
            }

        except Exception as e:
            log(f"❌ [Firecrawl] Crawl 失敗: {e}")
            return {
                "url": url,
                "pages_crawled": 0,
                "pages_injected": 0,
                "status": "error",
                "message": str(e)
            }

    # ----------------------------------------------------------
    #  Map：網站地圖偵察
    # ----------------------------------------------------------

    async def map_site(self, url: str) -> Dict:
        """
        快速掃描網域，列出所有 URL。
        適合在全站爬取前做「偵察」，決定爬取範圍。

        Returns:
            {"url": str, "urls": List[str], "total": int, "status": str}
        """
        try:
            app = self._get_client()
            log(f"🔥 [Firecrawl] Mapping: {url}")

            # SDK v2 使用 app.map
            result = await asyncio.to_thread(app.map, url)

            # 處理結果 (通常是 MapData 帶有 links 列表)
            urls = getattr(result, "links", []) or (result.get("links", []) if isinstance(result, dict) else [])
            if not urls and not isinstance(result, (dict, list)):
                # 如果 result 本身就是列表 (舊版行為)
                urls = result if isinstance(result, list) else []
            
            total = len(urls)

            log(f"🗺️ [Firecrawl] Map 完成: 發現 {total} 個 URL")

            return {
                "url": url,
                "urls": urls[:100],  # 限制回傳量
                "total": total,
                "status": "success"
            }

        except Exception as e:
            log(f"❌ [Firecrawl] Map 失敗: {e}")
            return {
                "url": url,
                "urls": [],
                "total": 0,
                "status": "error",
                "message": str(e)
            }

    # ----------------------------------------------------------
    #  內部工具
    # ----------------------------------------------------------

    async def _inject_to_rag(self, url: str, title: str, markdown: str):
        """將單一頁面的 Markdown 分段後寫入 RAG。"""
        try:
            from services.local_rag import local_rag

            chunks = self._chunk_text(markdown, max_chunk_size=800)
            documents = []
            metadatas = []

            for i, chunk in enumerate(chunks):
                documents.append(chunk)
                metadatas.append({
                    "text": chunk[:200],
                    "source": url,
                    "title": title,
                    "chunk_index": i,
                    "crawled_at": datetime.utcnow().isoformat(),
                    "type": "firecrawl_scrape"
                })

            if documents:
                await local_rag.add_documents(documents, metadatas)
                log(f"📚 [Firecrawl] 已將 {len(documents)} 個片段從 {title} 匯入 RAG")

        except Exception as e:
            log(f"⚠️ [Firecrawl] RAG 寫入失敗 (不影響主流程): {e}")

    @staticmethod
    def _chunk_text(text: str, max_chunk_size: int = 800) -> List[str]:
        """
        將長文本切成適合 RAG 的片段。
        優先按段落邊界切割，避免截斷語意。
        """
        if len(text) <= max_chunk_size:
            return [text]

        chunks = []
        # 按雙換行 (段落) 分割
        paragraphs = re.split(r'\n{2,}', text)
        current_chunk = ""

        for para in paragraphs:
            para = para.strip()
            if not para:
                continue

            if len(current_chunk) + len(para) + 2 <= max_chunk_size:
                current_chunk += ("\n\n" + para if current_chunk else para)
            else:
                if current_chunk:
                    chunks.append(current_chunk)

                # 單段落本身超長：強制按 max_chunk_size 切割
                if len(para) > max_chunk_size:
                    for i in range(0, len(para), max_chunk_size):
                        chunks.append(para[i:i + max_chunk_size])
                    current_chunk = ""
                else:
                    current_chunk = para

        if current_chunk:
            chunks.append(current_chunk)

        return chunks

    def health_check(self) -> Dict:
        """檢查 Firecrawl 服務是否可用。"""
        try:
            import requests
            if FIRECRAWL_MODE == "self_hosted":
                resp = requests.get(f"{FIRECRAWL_SELF_HOSTED_URL}/", timeout=5)
                return {
                    "mode": "self_hosted",
                    "url": FIRECRAWL_SELF_HOSTED_URL,
                    "status": "online" if resp.status_code < 500 else "error",
                    "status_code": resp.status_code
                }
            else:
                return {
                    "mode": "cloud",
                    "has_api_key": bool(FIRECRAWL_API_KEY),
                    "status": "configured" if FIRECRAWL_API_KEY else "no_api_key"
                }
        except Exception as e:
            return {
                "mode": FIRECRAWL_MODE,
                "status": "offline",
                "error": str(e)
            }


# 全域單例
firecrawl_service = FirecrawlService()
