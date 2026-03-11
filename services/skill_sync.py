import os
import requests
from core.config import log

BASE_RAW_URL = "https://raw.githubusercontent.com/openclaw/skills/main/skills"
SKILLS_DIR = os.path.join(os.getcwd(), "skills")

async def download_skill(owner, slug):
    """
    Downloads SKILL.md and _meta.json for a specific skill from openclaw/skills repo.
    """
    skill_path = os.path.join(SKILLS_DIR, f"{owner}-{slug}")
    os.makedirs(skill_path, exist_ok=True)
    
    files_to_download = ["SKILL.md", "_meta.json"]
    downloaded_files = []
    
    for filename in files_to_download:
        url = f"{BASE_RAW_URL}/{owner}/{slug}/{filename}"
        log(f"📥 Downloading {filename} from {url}...")
        
        try:
            response = requests.get(url, timeout=10)
            if response.status_code == 200:
                with open(os.path.join(skill_path, filename), "w", encoding="utf-8") as f:
                    f.write(response.text)
                downloaded_files.append(filename)
                log(f"✅ Successfully downloaded {filename}")
            else:
                log(f"⚠️ Failed to download {filename}: HTTP {response.status_code}")
        except Exception as e:
            log(f"❌ Error downloading {filename}: {e}")
            
    if "SKILL.md" in downloaded_files:
        return True, f"Successfully installed skill: {owner}-{slug}"
    else:
        return False, f"Failed to download core SKILL.md for {owner}/{slug}"
