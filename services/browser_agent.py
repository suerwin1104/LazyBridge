import asyncio
import os
from typing import Optional, Dict, Any
from browser_use import Agent, Browser
from core.config import ANTHROPIC_API_KEY, OPENAI_API_KEY, GEMINI_API_KEY, log

class BrowserAgentService:
    """
    Service wrapper for browser-use to enable high-level AI browser automation.
    Integrates with the existing Antigravity CDP session.
    """
    
    def __init__(self, cdp_url: str = "http://localhost:9222"):
        self.cdp_url = cdp_url
        self.browser = Browser(
            cdp_url=self.cdp_url,
            # We don't want to close the browser as it's shared
            headless=False # Visible in Antigravity
        )

    def _get_llm(self):
        """Auto-detect and return the most appropriate LLM based on available config."""
        anthropic_key = os.getenv("ANTHROPIC_API_KEY")
        openai_key = os.getenv("OPENAI_API_KEY")
        gemini_key = os.getenv("GEMINI_API_KEY")

        if anthropic_key:
            from browser_use.llm import ChatAnthropic
            return ChatAnthropic(model="claude-3-5-sonnet-latest", temperature=0)
        elif openai_key:
            from browser_use.llm import ChatOpenAI
            return ChatOpenAI(model="gpt-4o", temperature=0)
        elif gemini_key:
            from browser_use.llm import ChatGoogle
            return ChatGoogle(model="gemini-1.5-flash", temperature=0)
        
        # Fallback to a clear error if no key is found
        raise ValueError("No LLM API key found in environment variables (ANTHROPIC_API_KEY, OPENAI_API_KEY, or GEMINI_API_KEY)")

    async def run_task(self, task_description: str, model_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Runs an autonomous browser task using the specified LLM.
        """
        log(f"Starting browser-use task: {task_description}")
        
        try:
            llm = self._get_llm()
            
            agent = Agent(
                task=task_description,
                llm=llm,
                browser=self.browser
            )
            
            history = await agent.run()
            
            # Extract final result from history
            final_result = history.final_result()
            
            return {
                "status": "success",
                "result": final_result,
                "history": [h.model_dump() for h in history.history]
            }
        except Exception as e:
            log(f"Error in browser-use task: {str(e)}")
            return {
                "status": "error",
                "message": str(e)
            }

async def browse_and_summarize(task: str):
    """Utility function for quick browsing tasks."""
    service = BrowserAgentService()
    return await service.run_task(task)

if __name__ == "__main__":
    # Test script entry
    async def test():
        res = await browse_and_summarize("Find the latest news about OpenAI Sora and summarize it in 3 bullet points.")
        print(res)
    
    asyncio.run(test())
