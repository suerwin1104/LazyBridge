import asyncio
import os
import json
from typing import List, Dict, Any, Optional
from datetime import datetime
from core.config import log
from services.local_rag import LocalRAGService

try:
    from agent_reach.core import AgentReach
    AGENT_REACH_AVAILABLE = True
except ImportError:
    AGENT_REACH_AVAILABLE = False

class SocialService:
    """
    Social Media Data Acquisition Service using Agent-Reach.
    Provides searching and scraping for X, Reddit, GitHub, etc.
    """
    
    _instance = None
    
    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super(SocialService, cls).__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self, rag_service: Optional[LocalRAGService] = None):
        if self._initialized:
            return
            
        self.rag = rag_service
        self.client = None
        if AGENT_REACH_AVAILABLE:
            try:
                self.client = AgentReach()
                log("👀 [Social] Agent-Reach client initialized.")
            except Exception as e:
                log(f"❌ [Social] Failed to initialize Agent-Reach: {e}")
        else:
            log("⚠️ [Social] Agent-Reach library not found.")
            
        self._initialized = True

    async def search(self, query: str, platform: str = "twitter", limit: int = 10) -> Dict[str, Any]:
        """
        Search for posts on a specific platform.
        Platforms: twitter, reddit, github, youtube, google
        """
        if not self.client:
            return {"status": "error", "message": "Agent-Reach not available"}

        log(f"🔎 [Social] Searching {platform}: {query}")
        try:
            results = []
            if platform == "twitter" or platform == "x":
                # Note: Requires cookies for full results
                results = await self.client.search_twitter(query, limit=limit)
            elif platform == "reddit":
                results = await self.client.search_reddit(query, limit=limit)
            elif platform == "github":
                results = await self.client.search_github(query, limit=limit)
            elif platform == "youtube":
                results = await self.client.search_youtube(query, limit=limit)
            else:
                # Generic fallback
                results = await self.client.search(query, platform=platform, limit=limit)

            return {
                "status": "success",
                "platform": platform,
                "query": query,
                "results": results,
                "count": len(results) if isinstance(results, list) else 0
            }
        except Exception as e:
            log(f"❌ [Social] Search failed: {e}")
            return {"status": "error", "message": str(e)}

    async def configure(self, platform: str, value: str) -> Dict[str, Any]:
        """
        Configure platform-specific settings (e.g. twitter cookies).
        """
        if not self.client:
            return {"status": "error", "message": "Agent-Reach not available"}

        try:
            if platform == "twitter" or platform == "x":
                # 調用 SDK 的 configure twitter-cookies
                # 注意: SDK 可能沒有直接的 Python API 給這個，可能需要透過 CLI 或直接設 config 文件
                # 根據研究，CLI 是 agent-reach configure twitter-cookies
                # 我們可以嘗試模擬或調用 subprocess
                process = await asyncio.create_subprocess_exec(
                    "agent-reach", "configure", "twitter-cookies", value,
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE
                )
                stdout, stderr = await process.communicate()
                if process.returncode == 0:
                    return {"status": "success", "message": "Twitter cookies configured."}
                else:
                    return {"status": "error", "message": stderr.decode()}
            
            return {"status": "error", "message": f"Configuration for {platform} not supported via API yet."}
        except Exception as e:
            return {"status": "error", "message": str(e)}

    async def read_and_inject(self, url: str, inject_to_rag: bool = True) -> Dict[str, Any]:
        """
        Read content from a specific URL and optionally inject into RAG.
        """
        if not self.client:
            return {"status": "error", "message": "Agent-Reach not available"}

        log(f"📖 [Social] Reading: {url}")
        try:
            content = await self.client.read(url)
            
            if not content:
                return {"status": "error", "message": "No content fetched"}

            # Basic metadata extraction
            title = url
            if "github.com" in url:
                title = f"GitHub: {url.split('/')[-1]}"
            elif "reddit.com" in url:
                title = f"Reddit: {url.split('/')[-1]}"

            if inject_to_rag and self.rag:
                await self._inject_to_rag(url, title, content)

            return {
                "status": "success",
                "url": url,
                "title": title,
                "content_preview": content[:200],
                "char_count": len(content)
            }
        except Exception as e:
            log(f"❌ [Social] Read failed: {e}")
            return {"status": "error", "message": str(e)}

    async def _inject_to_rag(self, url: str, title: str, content: str):
        """Helper to inject long content into RAG."""
        if not self.rag:
            return
            
        log(f"📥 [Social] Injecting {title} into RAG...")
        
        # Simple chunking
        chunks = self._chunk_text(content, max_chunk_size=800)
        
        documents = []
        metadatas = []
        
        for i, chunk in enumerate(chunks):
            documents.append(chunk)
            metadatas.append({
                "text": chunk[:200],
                "source": url,
                "title": title,
                "chunk_index": i,
                "created_at": datetime.utcnow().isoformat(),
                "type": "social_reach"
            })
            
        await self.rag.add_documents(documents, metadatas)
        log(f"✅ [Social] Injected {len(documents)} chunks.")

    def _chunk_text(self, text: str, max_chunk_size: int = 800) -> List[str]:
        """Split text into manageable chunks."""
        if not text:
            return []
        
        paragraphs = text.split('\n\n')
        chunks = []
        current_chunk = ""
        
        for p in paragraphs:
            if len(current_chunk) + len(p) < max_chunk_size:
                current_chunk += p + "\n\n"
            else:
                if current_chunk:
                    chunks.append(current_chunk.strip())
                current_chunk = p + "\n\n"
        
        if current_chunk:
            chunks.append(current_chunk.strip())
            
        return chunks
