import asyncio
import aiohttp
import json
from typing import List, Dict, Any, Optional
from core.config import log

class PinchTabService:
    """
    Service for interacting with the PinchTab HTTP API.
    PinchTab is a high-performance browser automation bridge for AI agents.
    """
    
    def __init__(self, base_url: str = "http://localhost:9867", token: Optional[str] = None):
        self.base_url = base_url.rstrip('/')
        self.token = token
        self.headers = {"Content-Type": "application/json"}
        if self.token:
            self.headers["Authorization"] = f"Bearer {self.token}"

    async def _request(self, method: str, path: str, data: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        url = f"{self.base_url}{path}"
        try:
            async with aiohttp.ClientSession(headers=self.headers) as session:
                async with session.request(method, url, json=data) as response:
                    if response.status >= 400:
                        error_text = await response.text()
                        log(f"❌ [PinchTab] Error {response.status}: {error_text}")
                        return {"status": "error", "code": response.status, "message": error_text}
                    return await response.json()
        except Exception as e:
            log(f"❌ [PinchTab] Request failed: {e}")
            return {"status": "error", "message": str(e)}

    async def get_health(self) -> Dict[str, Any]:
        return await self._request("GET", "/health")

    async def list_instances(self) -> List[Dict[str, Any]]:
        res = await self._request("GET", "/instances")
        return res.get("instances", []) if isinstance(res, dict) else []

    async def launch_instance(self, name: str = "default", mode: str = "headless") -> Dict[str, Any]:
        data = {"name": name, "mode": mode}
        return await self._request("POST", "/instances/launch", data)

    async def stop_instance(self, instance_id: str) -> Dict[str, Any]:
        return await self._request("POST", f"/instances/{instance_id}/stop")

    async def open_tab(self, instance_id: str, url: str) -> Dict[str, Any]:
        data = {"url": url}
        return await self._request("POST", f"/instances/{instance_id}/tabs/open", data)

    async def get_tabs(self, instance_id: str) -> List[Dict[str, Any]]:
        res = await self._request("GET", f"/instances/{instance_id}/tabs")
        return res.get("tabs", []) if isinstance(res, dict) else []

    async def navigate(self, tab_id: str, url: str) -> Dict[str, Any]:
        data = {"kind": "navigate", "url": url}
        return await self._request("POST", f"/tabs/{tab_id}/action", data)

    async def get_snapshot(self, tab_id: str, filter: str = "interactive") -> Dict[str, Any]:
        """Gets the accessibility tree snapshot (token-efficient)."""
        return await self._request("GET", f"/tabs/{tab_id}/snapshot?filter={filter}")

    async def get_text(self, tab_id: str) -> Dict[str, Any]:
        return await self._request("GET", f"/tabs/{tab_id}/text")

    async def perform_action(self, tab_id: str, kind: str, ref: str, text: Optional[str] = None) -> Dict[str, Any]:
        """
        Perform an action on an element.
        Kinds: click, type, press, focus, hover, etc.
        """
        data = {"kind": kind, "ref": ref}
        if text:
            data["text"] = text
        return await self._request("POST", f"/tabs/{tab_id}/action", data)

    async def get_stealth_status(self, tab_id: str) -> Dict[str, Any]:
        return await self._request("GET", f"/tabs/{tab_id}/stealth-status")

    async def quick_browse(self, url: str) -> Dict[str, Any]:
        """Helper to quickly launch an instance, open a tab, and get text."""
        log(f"🌐 [PinchTab] Quick browsing: {url}")
        
        # 1. Launch instance
        launch_res = await self.launch_instance(name=f"quick_{int(asyncio.get_event_loop().time())}")
        if launch_res.get("status") == "error":
            return launch_res
        
        instance_id = launch_res.get("id")
        
        try:
            # 2. Open tab
            tab_res = await self.open_tab(instance_id, url)
            if tab_res.get("status") == "error":
                return tab_res
            
            tab_id = tab_res.get("tabId")
            
            # 3. Wait a bit for load (PinchTab doesn't always wait for networkIdle)
            await asyncio.sleep(3)
            
            # 4. Get text
            text_res = await self.get_text(tab_id)
            
            # 5. Get snapshot for AI context
            snapshot_res = await self.get_snapshot(tab_id)
            
            return {
                "status": "success",
                "instance_id": instance_id,
                "tab_id": tab_id,
                "text": text_res.get("text"),
                "snapshot": snapshot_res.get("snapshot")
            }
        finally:
            # We might want to keep it open, but for quick_browse we stop it to save resources
            # unless told otherwise. Let's keep it open for now but return the ID.
            pass

# Singleton instance
_pinchtab_service = None

def get_pinchtab_service() -> PinchTabService:
    global _pinchtab_service
    if _pinchtab_service is None:
        _pinchtab_service = PinchTabService()
    return _pinchtab_service
