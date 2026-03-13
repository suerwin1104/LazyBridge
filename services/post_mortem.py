"""
失敗後自動反思引擎 (Post-Mortem Evolution) — 受 MetaClaw 啟發

核心概念：
  - 當任務失敗（丟出 Exception、API 降級、超時等）時，
    自動分析失敗原因，萃取出一條新的「技能」存入技能庫
  - 下一次遇到類似任務時，SkillManager 會自動注入這條經驗教訓
  - 讓系統真正做到「吃一塹長一智」

技術實現：
  - 使用 AI Engine 分析失敗上下文
  - 產出結構化的「防護技能 (Guard Skill)」
  - 同時將反思結論存入 MemoryEntry (category="post_mortem") 做永久記錄
"""
import json
import traceback
from datetime import datetime
from typing import Dict, Optional
from sqlalchemy import select, desc, func
from core.database import AsyncSessionLocal
from models.memory import MemoryEntry
from core.config import log
from services.ai_engine import get_ai_response_async
from services.skill_manager import add_skill


# ==============================================================
#  核心：失敗分析與技能演化
# ==============================================================

async def analyze_failure(
    task_type: str,
    payload: Dict,
    error: Exception,
    context: Dict = None
) -> Optional[Dict]:
    """
    分析一次任務失敗，產出：
      1. 結構化的失敗報告 (Post-Mortem Report)
      2. 一條新的防護技能 (Guard Skill)

    Args:
        task_type: 失敗的任務類型 (ask, cdp_ask, command...)
        payload: 任務的原始 payload
        error: 捕獲到的 Exception
        context: 額外上下文 (如 start_time, tokens 等)

    Returns:
        生成的反思報告 dict，或 None (如果分析本身失敗)
    """
    context = context or {}

    try:
        # 1. 組裝失敗上下文
        error_trace = traceback.format_exception(type(error), error, error.__traceback__)
        error_str = "".join(error_trace[-3:])  # 只取最後 3 行，避免太長

        user_message = payload.get("message", payload.get("task", "N/A"))
        if len(user_message) > 300:
            user_message = user_message[:300] + "..."

        failure_context = (
            f"Task Type: {task_type}\n"
            f"User Message: {user_message}\n"
            f"Error Type: {type(error).__name__}\n"
            f"Error Message: {str(error)}\n"
            f"Stack Trace (last 3 frames):\n{error_str}\n"
        )

        # 2. 檢查是否已有類似的 Post-Mortem（避免重複分析）
        if await _is_duplicate_failure(task_type, str(error)):
            log(f"⏭️ [PostMortem] 類似失敗已分析過，跳過重複反思: {type(error).__name__}")
            return None

        # 3. 呼叫 AI 進行失敗分析
        analysis_prompt = (
            "You are a senior software reliability engineer performing a post-mortem analysis.\n"
            "Analyze the following task failure and produce TWO outputs:\n\n"
            "=== FAILURE CONTEXT ===\n"
            f"{failure_context}\n"
            "=== END CONTEXT ===\n\n"
            "OUTPUT 1 - Root Cause Analysis (in Traditional Chinese):\n"
            "Briefly explain what went wrong and why.\n\n"
            "OUTPUT 2 - Guard Skill (in JSON format):\n"
            "Generate a preventive skill that would help avoid this failure in the future.\n"
            "The JSON must follow this schema:\n"
            '{"name": "skill name", "trigger": "when to activate this skill", '
            '"instruction": "specific handling instructions", "tags": ["tag1", "tag2"]}\n\n'
            "Respond in this exact format:\n"
            "---ROOT_CAUSE---\n<your analysis>\n---GUARD_SKILL---\n<your JSON>"
        )

        ai_result = await get_ai_response_async(
            analysis_prompt,
            system_prompt="You are a reliability engineer. Be concise and actionable."
        )
        analysis_text = ai_result.get("text", "")

        # 4. 解析 AI 回覆
        root_cause, guard_skill = _parse_analysis(analysis_text, task_type, error)

        # 5. 儲存 Post-Mortem 報告
        report = {
            "task_type": task_type,
            "error_type": type(error).__name__,
            "error_msg": str(error)[:200],
            "root_cause": root_cause,
            "guard_skill_name": guard_skill.get("name", ""),
            "analyzed_at": datetime.utcnow().isoformat(),
            "user_message_preview": user_message[:100],
        }

        await _save_post_mortem(report)

        # 6. 將防護技能注入技能庫
        guard_skill["source"] = "post_mortem"
        guard_skill["created_at"] = datetime.utcnow().isoformat()
        guard_skill["usage_count"] = 0
        guard_skill["effectiveness"] = 0.5  # 初始中立值

        await add_skill(guard_skill)
        log(f"🛡️ [PostMortem] 新防護技能已生成: {guard_skill.get('name', 'Unknown')}")

        return report

    except Exception as analysis_error:
        # 反思引擎本身失敗時，不能讓它拖垮主流程
        log(f"⚠️ [PostMortem] 反思分析自身發生錯誤 (不影響主流程): {analysis_error}")
        # 退而求其次：存一條簡單的 fallback 技能
        await _save_fallback_skill(task_type, error)
        return None


# ==============================================================
#  輕量級反思 (不呼叫 AI，用於 API Key 不可用的場景)
# ==============================================================

async def quick_reflect(task_type: str, error: Exception, payload: Dict = None):
    """
    免 AI 的快速反思：基於錯誤模式匹配，直接生成簡單的防護技能。
    適用於 AI Engine 本身掛掉、或沒有 API Key 的情境。
    """
    payload = payload or {}
    error_name = type(error).__name__
    error_msg = str(error)[:200]

    # 常見錯誤模式 → 對應的防護策略
    PATTERN_MAP = {
        "TimeoutError": {
            "name": f"Timeout Guard - {task_type}",
            "trigger": f"執行 {task_type} 類型任務時",
            "instruction": (
                f"此任務類型 ({task_type}) 曾發生超時錯誤。\n"
                "建議：1) 檢查網路連線  2) 縮短請求內容  3) 增加重試間隔"
            ),
            "tags": [task_type, "timeout", "reliability"],
        },
        "ConnectionError": {
            "name": f"Connection Guard - {task_type}",
            "trigger": f"執行 {task_type} 類型任務且涉及外部 API 時",
            "instruction": (
                f"此任務類型 ({task_type}) 曾發生連線錯誤。\n"
                "建議：1) 確認服務端狀態  2) 啟用斷路器保護  3) 準備降級方案"
            ),
            "tags": [task_type, "connection", "reliability"],
        },
        "JSONDecodeError": {
            "name": f"JSON Parse Guard - {task_type}",
            "trigger": f"執行 {task_type} 類型任務且需要解析 JSON 時",
            "instruction": (
                f"此任務類型 ({task_type}) 曾因 JSON 解析失敗而出錯。\n"
                "建議：1) 在 Prompt 中強調只回傳純 JSON  2) 增加 JSON 提取寬容度  3) 準備 fallback 模板"
            ),
            "tags": [task_type, "json", "parsing"],
        },
    }

    # 匹配模式
    skill_template = PATTERN_MAP.get(error_name)
    if not skill_template:
        skill_template = {
            "name": f"Error Guard - {task_type} ({error_name})",
            "trigger": f"執行 {task_type} 任務時，可能遭遇 {error_name}",
            "instruction": (
                f"此任務 ({task_type}) 曾發生 {error_name} 錯誤: {error_msg}\n"
                "建議謹慎處理，增加錯誤捕獲與降級方案。"
            ),
            "tags": [task_type, "error", error_name.lower()],
        }

    skill_template["source"] = "post_mortem"
    skill_template["created_at"] = datetime.utcnow().isoformat()
    skill_template["usage_count"] = 0
    skill_template["effectiveness"] = 0.5

    await add_skill(skill_template)
    log(f"⚡ [PostMortem] 快速反思完成，已生成防護技能: {skill_template['name']}")


# ==============================================================
#  查詢與統計
# ==============================================================

async def get_post_mortem_stats() -> Dict:
    """取得反思統計資料"""
    try:
        async with AsyncSessionLocal() as session:
            # 總數
            count_stmt = select(func.count(MemoryEntry.id)).filter(
                MemoryEntry.category == "post_mortem"
            )
            count_result = await session.execute(count_stmt)
            total = count_result.scalar() or 0

            # 最近 5 筆
            recent_stmt = (
                select(MemoryEntry)
                .filter(MemoryEntry.category == "post_mortem")
                .order_by(desc(MemoryEntry.created_at))
                .limit(5)
            )
            recent_result = await session.execute(recent_stmt)
            recent = recent_result.scalars().all()

            return {
                "total_analyses": total,
                "recent": [
                    {
                        "title": e.title,
                        "created_at": e.created_at.isoformat() if e.created_at else None,
                        "preview": e.content[:100]
                    }
                    for e in recent
                ]
            }
    except Exception as e:
        log(f"❌ [PostMortem] 取得統計失敗: {e}")
        return {"total_analyses": 0, "recent": []}


async def get_recent_post_mortems(limit: int = 5) -> list:
    """取得最近的反思報告"""
    try:
        async with AsyncSessionLocal() as session:
            stmt = (
                select(MemoryEntry)
                .filter(MemoryEntry.category == "post_mortem")
                .order_by(desc(MemoryEntry.created_at))
                .limit(limit)
            )
            result = await session.execute(stmt)
            entries = result.scalars().all()
            return [json.loads(e.content) for e in entries]
    except Exception as e:
        log(f"❌ [PostMortem] 取得報告失敗: {e}")
        return []


# ==============================================================
#  內部輔助函式
# ==============================================================

def _parse_analysis(text: str, task_type: str, error: Exception) -> tuple:
    """
    解析 AI 的反思回覆，提取 root_cause 和 guard_skill。
    如果解析失敗，回傳合理的 fallback。
    """
    root_cause = "分析結果無法解析"
    guard_skill = {
        "name": f"Auto Guard - {task_type}",
        "trigger": f"執行 {task_type} 類型任務時",
        "instruction": f"此任務曾失敗 ({type(error).__name__})，請謹慎處理。",
        "tags": [task_type, "auto_guard"],
    }

    try:
        if "---ROOT_CAUSE---" in text and "---GUARD_SKILL---" in text:
            parts = text.split("---GUARD_SKILL---")
            root_part = parts[0].split("---ROOT_CAUSE---")[-1].strip()
            skill_part = parts[1].strip()

            root_cause = root_part

            # 嘗試從 skill_part 提取 JSON
            import re
            json_match = re.search(r'\{[\s\S]*\}', skill_part)
            if json_match:
                parsed = json.loads(json_match.group())
                if "name" in parsed and "instruction" in parsed:
                    guard_skill = parsed
                    # 確保有 tags
                    if "tags" not in guard_skill:
                        guard_skill["tags"] = [task_type, "auto_guard"]
        else:
            # AI 沒有遵循格式，把整個回覆當作 root cause
            root_cause = text[:500]

    except Exception as parse_err:
        log(f"⚠️ [PostMortem] 解析 AI 回覆失敗: {parse_err}")

    return root_cause, guard_skill


async def _is_duplicate_failure(task_type: str, error_msg: str) -> bool:
    """檢查最近 1 小時內是否已有相同的 post-mortem"""
    try:
        from datetime import timedelta
        async with AsyncSessionLocal() as session:
            cutoff = datetime.utcnow() - timedelta(hours=1)
            stmt = (
                select(MemoryEntry)
                .filter(
                    MemoryEntry.category == "post_mortem",
                    MemoryEntry.created_at >= cutoff
                )
                .order_by(desc(MemoryEntry.created_at))
                .limit(5)
            )
            result = await session.execute(stmt)
            recent = result.scalars().all()

            # 簡單的文字比對去重
            short_err = error_msg[:80]
            for entry in recent:
                if short_err in entry.content:
                    return True

            return False
    except Exception:
        return False


async def _save_post_mortem(report: Dict):
    """儲存反思報告到資料庫"""
    try:
        async with AsyncSessionLocal() as session:
            title = f"PM-{report['task_type']}-{report['error_type']}-{datetime.utcnow().strftime('%Y%m%d%H%M')}"
            entry = MemoryEntry(
                category="post_mortem",
                title=title,
                content=json.dumps(report, ensure_ascii=False, indent=2)
            )
            session.add(entry)
            await session.commit()
            log(f"📝 [PostMortem] 反思報告已儲存: {title}")
    except Exception as e:
        log(f"❌ [PostMortem] 儲存報告失敗: {e}")


async def _save_fallback_skill(task_type: str, error: Exception):
    """當 AI 分析失敗時，存一條簡單的 fallback 技能"""
    await quick_reflect(task_type, error)
