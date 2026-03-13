"""
Social Media Integration Skill.
Handles FB Page / IG Business draft generation and preview.
"""
import os
import json
import facebook
# from instagrapi import Client  # Future IG support
from core.config import log, REPORTS_BASE_URL
from services.ai_engine import get_ai_response_async

class SocialMediaManager:
    def __init__(self):
        self.fb_token = os.getenv("FB_PAGE_ACCESS_TOKEN")
        self.ig_user_id = os.getenv("IG_BUSINESS_ACCOUNT_ID")
        self.auto_post = os.getenv("ENABLE_AUTO_POST", "false").lower() == "true"
        self.graph = None
        if self.fb_token:
            try:
                self.graph = facebook.GraphAPI(access_token=self.fb_token)
            except Exception as e:
                log(f"FB Graph initialization failed: {e}")

    async def generate_draft(self, topic: str, target: str = "all"):
        """Generate a social media post draft using the AI engine."""
        prompt = f"你現在是我的私人秘書 Mandy。請針對『{topic}』這個主題，寫一篇適合發布在 {target} (如 FB/IG) 的社群貼文。\n" \
                 "特點：文字要有觀點、俐落、避開 AI 官腔。包含適當的 Emoji 和 Hashtags。\n" \
                 "請同時提供一段供 DALL-E 3 使用的配圖提示詞 (Image Prompt)。"
        
        result = await get_ai_response_async(prompt)
        return result.get("text", "AI 無法產生內容。")

    async def list_pages(self):
        """List managed FB pages for the token."""
        if not self.graph:
            return {"error": "Missing FB token"}
        try:
            pages = self.graph.get_object('me/accounts')
            return pages
        except Exception as e:
            log(f"FB List Pages failed: {e}")
            return {"error": str(e)}

    def preview_post(self, content: str):
        """Save a preview of the post to the reports directory."""
        os.makedirs("reports", exist_ok=True)
        filename = "reports/social_draft_preview.md"
        with open(filename, "w", encoding="utf-8") as f:
            f.write(f"# Social Media Draft Preview\n\n{content}")
        return f"{REPORTS_BASE_URL}/social_draft_preview.html"

# Singleton instance
social_manager = SocialMediaManager()
