import asyncio
import os
from core.config import log

async def run_chub_command(command: str) -> tuple[bool, str]:
    """執行 chub CLI 指令並回傳結果。"""
    full_cmd = f"chub {command}"
    log(f"🔎 執行 Context Hub 指令: {full_cmd}")
    
    try:
        # 使用 shell=True 執行，因為 npx/npm 裝的全域套件可能需要系統 PATH 解析
        process = await asyncio.create_subprocess_shell(
            full_cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        stdout, stderr = await process.communicate()
        
        if process.returncode == 0:
            return True, stdout.decode('utf-8').strip()
        else:
            return False, stderr.decode('utf-8').strip()
    except Exception as e:
        log(f"❌ 執行 chub 失敗: {e}")
        return False, str(e)


async def search_chub(query: str) -> str:
    """搜尋 Context Hub 上的文件。"""
    success, result = await run_chub_command(f"search \"{query}\"")
    if success:
        return f"✅ **搜尋結果:**\n```\n{result}\n```"
    return f"❌ **搜尋失敗:**\n```\n{result}\n```"


async def get_chub(doc_id: str, lang: str = "py") -> tuple[bool, str]:
    """抓取 Context Hub 的特定文件。"""
    cmd = f"get {doc_id}"
    if lang:
        cmd += f" --lang {lang}"
        
    success, result = await run_chub_command(cmd)
    if success:
        from services.memory_engine import save_custom_memory
        # 存入 Memory Engine，讓未來的 AI prompt 能夠擷取到
        await save_custom_memory(title=f"chub-{doc_id}", content=result)
        return True, f"✅ **文件已成功抓取並存入 Memory Engine (標題: chub-{doc_id}):**\n\n擷取部分內容預覽:\n```markdown\n{result[:500]}...\n```"
    return False, f"❌ **抓取失敗:**\n```\n{result}\n```"


async def annotate_chub(doc_id: str, note: str) -> str:
    """為 Context Hub 文件加入本地註解 (學習筆記)。"""
    # note 必須是字串，且用引號包起來處理空白
    # 注意處理引號跳脫
    safe_note = note.replace('"', '\\"')
    success, result = await run_chub_command(f"annotate {doc_id} \"{safe_note}\"")
    
    if success:
        return f"✅ **註解已成功加入:**\n```\n{result}\n```"
    return f"❌ **註解失敗:**\n```\n{result}\n```"
