"""
Memory Engine 核心服務 (資料庫版本)
取代原有的 Node.js Hooks，將 Context 與 Pitfalls 直接儲存於 SQLAlchemy 資料庫。
"""
import os
import json
import logging
from datetime import datetime, timedelta
from typing import List, Dict, Optional

from sqlalchemy import select, desc
from core.database import AsyncSessionLocal
from models.memory import MemoryEntry
from core.config import log
from services.ai_engine import get_ai_response_async

async def get_memory_context() -> str:
    """從資料庫取得最近的 Session 與踩坑紀錄，組合為給 AI 的 Prompt 上下文。"""
    output = []
    try:
        async with AsyncSessionLocal() as session:
            # 1. 取得最近的 Session (7天內)
            now = datetime.utcnow()
            week_ago = now - timedelta(days=7)
            
            latest_session_stmt = (
                select(MemoryEntry)
                .filter(MemoryEntry.category == "session", MemoryEntry.created_at >= week_ago)
                .order_by(desc(MemoryEntry.created_at))
                .limit(1)
            )
            result = await session.execute(latest_session_stmt)
            latest_sess = result.scalar_one_or_none()
            
            if latest_sess:
                output.append(f"[Memory Engine] 上次工作摘要（{latest_sess.title}）：\n{latest_sess.content}")
            else:
                output.append("[Memory Engine] 沒有找到最近的工作紀錄，這是全新的開始！")
                
            # 2. 取得最近踩坑 (3天內)
            three_days_ago = now - timedelta(days=3)
            pitfall_stmt = (
                select(MemoryEntry)
                .filter(MemoryEntry.category == "pitfall", MemoryEntry.created_at >= three_days_ago)
                .order_by(desc(MemoryEntry.created_at))
                .limit(1)
            )
            p_result = await session.execute(pitfall_stmt)
            latest_pitfall = p_result.scalar_one_or_none()
            
            if latest_pitfall:
                # 只取前 20 行
                brief = "\n".join(latest_pitfall.content.split('\n')[:20])
                output.append(f"\n[Auto Learn] 最近踩坑紀錄：\n{brief}")
                
            # 3. 自訂筆記 (例如全局的 todo)
            todo_stmt = (
                select(MemoryEntry)
                .filter(MemoryEntry.category == "custom", MemoryEntry.title == "todo")
            )
            todo_result = await session.execute(todo_stmt)
            todo = todo_result.scalar_one_or_none()
            todo = todo_result.scalar_one_or_none()
            if todo:
                output.append(f"\n[Custom Memory] 待辦事項：\n{todo.content}")

            # 4. 取得最近的語意教訓 (Strategic Compaction)
            lesson_stmt = (
                select(MemoryEntry)
                .filter(MemoryEntry.category == "semantic_lesson")
                .order_by(desc(MemoryEntry.created_at))
                .limit(1)
            )
            lesson_result = await session.execute(lesson_stmt)
            lesson = lesson_result.scalar_one_or_none()
            if lesson:
                output.insert(0, f"[Strategic Compaction] 核心記憶與語意教訓：\n{lesson.content}\n")
                
    except Exception as e:
        log(f"❌ get_memory_context 異常: {e}")
        output.append("[Memory Engine] 載入記憶時發生問題，但不影響正常使用")
        
    return "\n".join(output)

async def auto_detect_pitfalls(user_messages: List[str], tools_used: List[str], response: str) -> Optional[List[Dict]]:
    """簡單的踩坑偵測：判斷 AI 是否嘗試使用某些工具但失敗，或是被使用者糾正。"""
    pitfalls = []
    
    # 訊號 1: 使用者糾正
    correction_keywords = [
        'wrong', 'not this', 'revert', 'undo', "that's not",
        '不對', '錯了', '改回來', '不是這個', '回復', '撤銷',
        '重來', '重做', '不要這樣', '取消', '不是我要的'
    ]
    
    for msg in user_messages:
        if any(kw in msg for kw in correction_keywords):
            pitfalls.append({
                "type": "user-correction",
                "description": f"User correction detected: {msg[:80]}",
                "target": ""
            })
            
    # 這裡的邏輯可以再擴充，例如分析呼叫歷史找出 'error-then-fix'
    # 目前先提供基礎範本
    
    return pitfalls

async def save_session_memory(user_messages: List[str], ai_response: str, tools_used: List[str] = None):
    """將這次對話總結儲存至資料庫的 session 類別中，並觸發自動學習。"""
    if not user_messages:
        return
        
    tools_used = tools_used or []
    
    try:
        now = datetime.utcnow()
        date_str = now.strftime("%Y-%m-%d")
        time_str = now.strftime("%H:%M")
        
        recent_messages = user_messages[-5:]
        main_topic = " | ".join([m[:60] for m in user_messages[:3]])
        
        summary_lines = [
            f"# Session: {date_str}",
            f"**Time:** {time_str} | **Messages:** {len(user_messages)} | **Tools:** {len(tools_used)}",
            "",
            "## What was done",
            main_topic or "No clear topic detected",
            "",
            "## Key requests",
            "\n".join(f"- {m}" for m in recent_messages),
            "",
            "## Tools used",
            ", ".join(tools_used) if tools_used else "None"
        ]
        
        content = "\n".join(summary_lines)
        title = f"{date_str}-session"
        
        async with AsyncSessionLocal() as session:
            # 儲存 Session
            entry = MemoryEntry(category="session", title=title, content=content)
            session.add(entry)
            
            # 偵測與儲存踩坑
            pitfalls = await auto_detect_pitfalls(user_messages, tools_used, ai_response)
            if pitfalls:
                p_date = now.strftime("%Y%m%d")
                p_content = f"# Pitfall Record {date_str}\n\n## Issues Detected\n"
                for p in pitfalls:
                    p_content += f"### {p['type']}\n- {p['description']}\n\n"
                    
                p_entry = MemoryEntry(category="pitfall", title=f"auto-pitfall-{p_date}", content=p_content)
                session.add(p_entry)
                log(f"⚠️ 偵測到 {len(pitfalls)} 項潛在踩坑，已自動儲存至 Memory Engine")
                
            await session.commit()
            log(f"✅ Session 摘要已存至資料庫: {title}")
            
    except Exception as e:
        log(f"❌ save_session_memory 異常: {e}")

async def get_memory_list(category: str = None) -> List[Dict]:
    """獲取特定分類的記憶列表供查詢"""
    try:
         async with AsyncSessionLocal() as session:
            stmt = select(MemoryEntry).order_by(desc(MemoryEntry.created_at)).limit(20)
            if category:
                stmt = stmt.filter(MemoryEntry.category == category)
                
            result = await session.execute(stmt)
            entries = result.scalars().all()
            return [entry.to_dict() for entry in entries]
    except Exception as e:
        log(f"❌ get_memory_list 異常: {e}")
        return []

async def save_custom_memory(title: str, content: str):
    """手動儲存自訂重點"""
    try:
         async with AsyncSessionLocal() as session:
            # 檢查是否已存在
            stmt = select(MemoryEntry).filter(MemoryEntry.category == "custom", MemoryEntry.title == title)
            result = await session.execute(stmt)
            existing = result.scalar_one_or_none()
            
            if existing:
                existing.content = content
                existing.created_at = datetime.utcnow()
            else:
                entry = MemoryEntry(category="custom", title=title, content=content)
                session.add(entry)
                
            await session.commit()
            log(f"✅ 自訂記憶已儲存: {title}")
            return True
    except Exception as e:
        log(f"❌ save_custom_memory 異常: {e}")
        return False

async def compact_sessions(days_old: int = 1):
    """將過舊的 Session 日誌壓縮成為 Semantic Lesson，並刪除原始日誌。"""
    try:
         async with AsyncSessionLocal() as session:
            cutoff = datetime.utcnow() - timedelta(days=days_old)
            stmt = select(MemoryEntry).filter(
                MemoryEntry.category == "session", 
                MemoryEntry.created_at < cutoff
            ).order_by(MemoryEntry.created_at)
            
            result = await session.execute(stmt)
            old_sessions = result.scalars().all()
            
            if not old_sessions:
                log("📌 [Strategic Compaction] 狀態良好，沒有需要壓縮的過期 Session。")
                return
                
            log(f"🗜️ [Strategic Compaction] 找到 {len(old_sessions)} 筆過期 Session，準備執行知識壓縮...")
            
            combined_text = "\\n\\n--- Session Log ---\\n\\n".join([s.content for s in old_sessions])
            
            prompt = (
                "Please summarize Key Takeaways and Semantic Lessons from the following conversation logs. "
                "Focus on decisions made, facts learned, user preferences, and any persistent architecture/coding rules established. "
                "Output the result in clear markdown format.\\n\\n"
                f"{combined_text[:12000]}"
            )
            
            ai_result = await get_ai_response_async(prompt)
            summary_text = ai_result["text"]
            
            # 儲存壓縮後的 Semantic Lesson
            date_str = datetime.utcnow().strftime("%Y-%m-%d")
            lesson_entry = MemoryEntry(
                category="semantic_lesson",
                title=f"Lesson-{date_str}",
                content=summary_text
            )
            session.add(lesson_entry)
            
            # 刪除舊的
            for s in old_sessions:
                await session.delete(s)
                
            await session.commit()
            log("✅ [Strategic Compaction] 過期 Session 壓縮成功，已轉化為 Semantic Lesson。")
            
    except Exception as e:
        log(f"❌ compact_sessions 異常: {e}")
