import json
import re
from core.config import log
from services.ai_engine import get_ai_response_async

class PlannerEngine:
    """引擎：將大任務拆解成子任務隊列。"""
    
    PLANNER_PROMPT = """
    You are the 'Great Planner' for the HBMS (Honey Bridge Management System).
    Your job is to take a complex user request and decompose it into a sequence of actionable sub-tasks.
    
    Sub-task types available:
    - 'ask': High-level reasoning or report writing.
    - 'web_browse': Researching information on the web.
    - 'command': Executing terminal commands (file ops, deployments).
    - 'scrape': Extracting data from specific URLs.
    
    RESPONSE FORMAT (STRICT JSON):
    {
        "plan_title": "Short title",
        "sub_tasks": [
            {"type": "task_type", "payload": {"message/task/command": "content"}, "description": "Why this step?"}
        ]
    }
    """

    async def decompose_task(self, big_task_desc):
        """呼叫 AI 進行任務拆解。"""
        log(f"🧠 [Planner] 正在拆解大任務: {big_task_desc[:50]}...")
        
        prompt = f"{self.PLANNER_PROMPT}\n\nUser Request: {big_task_desc}"
        
        try:
            ai_result = await get_ai_response_async(prompt)
            text = ai_result["text"]
            
            # 提取 JSON
            json_match = re.search(r'\{.*\}', text, re.DOTALL)
            if json_match:
                plan = json.loads(json_match.group(0))
                log(f"✅ [Planner] 拆解成功: {plan.get('plan_title')} ({len(plan.get('sub_tasks', []))} steps)")
                return plan
        except Exception as e:
            log(f"❌ [Planner] 拆解失敗: {e}")
            
        return None

planner = PlannerEngine()
