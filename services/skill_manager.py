"""
動態技能管理器 (Skill Manager) — 受 MetaClaw 啟發

核心概念：
  - 將「靜態指令 (rules/)」進化為「動態技能庫」
  - 每一條技能包含：觸發條件、具體指令、來源（手動 / 自動演化）
  - 任務處理時，根據當前 query 語意匹配最相關的技能，動態注入到 system prompt

技能庫儲存：
  - 資料庫 (MemoryEntry, category="skill")
  - 本地 RAG 索引 (FAISS, bge-m3) 用於語意檢索
"""
import os
import json
from datetime import datetime
from typing import List, Dict, Optional
from sqlalchemy import select, desc
from core.database import AsyncSessionLocal
from models.memory import MemoryEntry
from core.config import log
from services.local_rag import local_rag


# ==============================================================
#  初始化：從 rules/ 目錄載入靜態規則，轉化為技能種子
# ==============================================================
RULES_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "rules")

# 技能的結構化格式
SKILL_TEMPLATE = {
    "name": "",           # 技能名稱
    "trigger": "",        # 觸發描述（語意匹配依據）
    "instruction": "",    # 具體指令內容
    "source": "manual",   # manual | auto_evolved | post_mortem
    "usage_count": 0,     # 被注入的次數
    "effectiveness": 0.0, # 有效率 (成功次數 / 注入次數)
    "created_at": "",
    "tags": [],           # 分類標籤
}


async def seed_skills_from_rules():
    """
    冷啟動：掃描 rules/ 目錄下的 .md 文件，將靜態規則轉為動態技能種子。
    僅在技能庫為空時執行一次。
    """
    try:
        async with AsyncSessionLocal() as session:
            # 檢查是否已有技能
            stmt = select(MemoryEntry).filter(MemoryEntry.category == "skill").limit(1)
            result = await session.execute(stmt)
            if result.scalar_one_or_none():
                log("📚 [SkillManager] 技能庫已有資料，跳過種子初始化")
                return

        # 掃描 rules/ 目錄
        if not os.path.exists(RULES_DIR):
            log("⚠️ [SkillManager] rules/ 目錄不存在")
            return

        seed_count = 0
        for root, dirs, files in os.walk(RULES_DIR):
            for fname in files:
                if not fname.endswith(".md"):
                    continue

                fpath = os.path.join(root, fname)
                with open(fpath, "r", encoding="utf-8") as f:
                    content = f.read()

                # 從路徑推導標籤 (e.g., rules/common/humanize.md → ["common", "humanize"])
                rel_path = os.path.relpath(fpath, RULES_DIR)
                tags = [p.replace(".md", "") for p in rel_path.replace("\\", "/").split("/")]

                skill_name = fname.replace(".md", "").replace("_", " ").title()

                skill_data = {
                    "name": skill_name,
                    "trigger": f"任務涉及 {' / '.join(tags)} 相關操作時適用",
                    "instruction": content,
                    "source": "manual",
                    "usage_count": 0,
                    "effectiveness": 0.0,
                    "created_at": datetime.utcnow().isoformat(),
                    "tags": tags,
                }

                await add_skill(skill_data)
                seed_count += 1

        log(f"🌱 [SkillManager] 從 rules/ 載入了 {seed_count} 個技能種子")

    except Exception as e:
        log(f"❌ [SkillManager] 技能種子初始化失敗: {e}")


# ==============================================================
#  CRUD 操作
# ==============================================================

async def add_skill(skill_data: Dict) -> bool:
    """新增一條技能到資料庫 + RAG 索引"""
    try:
        name = skill_data.get("name", "Unnamed Skill")
        content = json.dumps(skill_data, ensure_ascii=False, indent=2)

        async with AsyncSessionLocal() as session:
            # 檢查同名技能是否已存在
            stmt = select(MemoryEntry).filter(
                MemoryEntry.category == "skill",
                MemoryEntry.title == name
            )
            result = await session.execute(stmt)
            existing = result.scalar_one_or_none()

            if existing:
                existing.content = content
                existing.created_at = datetime.utcnow()
                log(f"🔄 [SkillManager] 技能已更新: {name}")
            else:
                entry = MemoryEntry(category="skill", title=name, content=content)
                session.add(entry)
                log(f"➕ [SkillManager] 技能已新增: {name}")

            await session.commit()

        # 建立 RAG 檢索文本 = 技能名稱 + 觸發條件 + 標籤 + 指令摘要
        rag_text = (
            f"[Skill: {name}] "
            f"觸發條件: {skill_data.get('trigger', '')} | "
            f"標籤: {', '.join(skill_data.get('tags', []))} | "
            f"指令: {skill_data.get('instruction', '')[:200]}"
        )
        await local_rag.add_documents(
            [rag_text],
            [{"category": "skill", "skill_name": name, "text": rag_text}]
        )

        return True

    except Exception as e:
        log(f"❌ [SkillManager] 新增技能失敗: {e}")
        return False


async def get_all_skills() -> List[Dict]:
    """取得所有技能列表"""
    try:
        async with AsyncSessionLocal() as session:
            stmt = (
                select(MemoryEntry)
                .filter(MemoryEntry.category == "skill")
                .order_by(desc(MemoryEntry.created_at))
            )
            result = await session.execute(stmt)
            entries = result.scalars().all()
            return [json.loads(e.content) for e in entries]
    except Exception as e:
        log(f"❌ [SkillManager] 獲取技能列表失敗: {e}")
        return []


async def delete_skill(skill_name: str) -> bool:
    """刪除指定技能"""
    try:
        async with AsyncSessionLocal() as session:
            stmt = select(MemoryEntry).filter(
                MemoryEntry.category == "skill",
                MemoryEntry.title == skill_name
            )
            result = await session.execute(stmt)
            entry = result.scalar_one_or_none()
            if entry:
                await session.delete(entry)
                await session.commit()
                log(f"🗑️ [SkillManager] 技能已刪除: {skill_name}")
                return True
            else:
                log(f"⚠️ [SkillManager] 找不到技能: {skill_name}")
                return False
    except Exception as e:
        log(f"❌ [SkillManager] 刪除技能失敗: {e}")
        return False


# ==============================================================
#  核心功能：動態技能注入
# ==============================================================

async def inject_skills(query: str, task_type: str = "", top_k: int = 3) -> str:
    """
    根據當前任務的語意，從技能庫中檢索最相關的技能，
    組裝成可以直接拼接到 system prompt 的指令片段。

    Args:
        query: 使用者的原始訊息或任務描述
        task_type: 任務類別 (ask, cdp_ask, command, etc.)
        top_k: 最多注入幾條技能

    Returns:
        組裝好的技能指令字串 (可直接附加到 system prompt)
    """
    try:
        # 組合檢索 query：原始問題 + 任務類型
        search_query = f"{query} {task_type}".strip()

        # 使用 RAG 語意搜尋找相關技能
        hits = await local_rag.search(search_query, top_k=top_k * 2)  # 多取一些再過濾

        # 過濾只保留 category=skill 的結果
        skill_hits = [
            h for h in hits
            if h.get("metadata", {}).get("category") == "skill"
        ][:top_k]

        if not skill_hits:
            return ""

        # 組裝注入內容
        sections = ["\n[Dynamic Skills - 根據任務自動注入的處理指導]"]

        for i, hit in enumerate(skill_hits, 1):
            skill_name = hit["metadata"].get("skill_name", "Unknown")
            score = hit.get("score", 0)

            # 從資料庫取得完整技能內容
            skill_data = await _get_skill_data(skill_name)
            if not skill_data:
                continue

            instruction = skill_data.get("instruction", "")
            # 截取合理長度，避免過多 token 消耗
            if len(instruction) > 500:
                instruction = instruction[:500] + "..."

            sections.append(
                f"### Skill #{i}: {skill_name}\n"
                f"{instruction}"
            )

            # 更新使用計數 (非同步背景執行，不阻塞主流程)
            await _increment_skill_usage(skill_name)

        if len(sections) <= 1:
            return ""

        result = "\n".join(sections)
        log(f"🎯 [SkillManager] 已注入 {len(sections) - 1} 條動態技能")
        return result

    except Exception as e:
        log(f"❌ [SkillManager] 技能注入失敗: {e}")
        return ""


async def record_skill_outcome(task_type: str, query: str, success: bool):
    """
    記錄技能注入後的任務結果，用於更新技能的有效率 (effectiveness)。
    """
    try:
        hits = await local_rag.search(f"{query} {task_type}", top_k=3)
        skill_hits = [
            h for h in hits
            if h.get("metadata", {}).get("category") == "skill"
        ]

        for hit in skill_hits:
            skill_name = hit["metadata"].get("skill_name")
            if not skill_name:
                continue

            async with AsyncSessionLocal() as session:
                stmt = select(MemoryEntry).filter(
                    MemoryEntry.category == "skill",
                    MemoryEntry.title == skill_name
                )
                result = await session.execute(stmt)
                entry = result.scalar_one_or_none()
                if not entry:
                    continue

                data = json.loads(entry.content)
                usage = data.get("usage_count", 0)

                if usage > 0:
                    # 計算新的有效率 (Exponential Moving Average)
                    old_eff = data.get("effectiveness", 0.5)
                    alpha = 0.3  # 新結果的權重
                    new_eff = alpha * (1.0 if success else 0.0) + (1 - alpha) * old_eff
                    data["effectiveness"] = round(new_eff, 3)

                entry.content = json.dumps(data, ensure_ascii=False, indent=2)
                await session.commit()

    except Exception as e:
        log(f"❌ [SkillManager] 記錄技能成效失敗: {e}")


# ==============================================================
#  內部輔助函式
# ==============================================================

async def _get_skill_data(skill_name: str) -> Optional[Dict]:
    """從資料庫讀取完整的技能 JSON"""
    try:
        async with AsyncSessionLocal() as session:
            stmt = select(MemoryEntry).filter(
                MemoryEntry.category == "skill",
                MemoryEntry.title == skill_name
            )
            result = await session.execute(stmt)
            entry = result.scalar_one_or_none()
            if entry:
                return json.loads(entry.content)
            return None
    except Exception as e:
        log(f"❌ [SkillManager] 讀取技能 {skill_name} 失敗: {e}")
        return None


async def _increment_skill_usage(skill_name: str):
    """遞增技能的使用次數"""
    try:
        async with AsyncSessionLocal() as session:
            stmt = select(MemoryEntry).filter(
                MemoryEntry.category == "skill",
                MemoryEntry.title == skill_name
            )
            result = await session.execute(stmt)
            entry = result.scalar_one_or_none()
            if entry:
                data = json.loads(entry.content)
                data["usage_count"] = data.get("usage_count", 0) + 1
                entry.content = json.dumps(data, ensure_ascii=False, indent=2)
                await session.commit()
    except Exception as e:
        log(f"⚠️ [SkillManager] 更新技能使用次數失敗: {e}")
