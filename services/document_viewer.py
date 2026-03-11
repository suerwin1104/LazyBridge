import os
import shutil
import markdown
import mammoth
import mammoth
from core.config import log, REPORTS_BASE_URL

# Shared CSS for glassmorphic design
VIEWER_CSS = """
:root {
    --primary: #38bdf8;
    --bg: #0f172a;
    --card-bg: rgba(30, 41, 59, 0.7);
    --text: #f8fafc;
}
body {
    font-family: 'Inter', -apple-system, sans-serif;
    background: var(--bg);
    color: var(--text);
    margin: 0;
    padding: 40px 20px;
    display: flex;
    flex-direction: column;
    align-items: center;
    min-height: 100vh;
    background-image: 
        radial-gradient(at 0% 0%, rgba(56, 189, 248, 0.15) 0, transparent 50%), 
        radial-gradient(at 100% 100%, rgba(56, 189, 248, 0.1) 0, transparent 50%);
}
.container {
    max-width: 1000px;
    width: 100%;
    background: var(--card-bg);
    backdrop-filter: blur(12px);
    -webkit-backdrop-filter: blur(12px);
    border: 1px solid rgba(255, 255, 255, 0.1);
    border-radius: 24px;
    padding: 40px;
    box-shadow: 0 10px 30px -10px rgba(0, 0, 0, 0.5);
}
h1, h2, h3 { color: var(--primary); }
a { color: #60A5FA; text-decoration: none; border-bottom: 1px dotted #60A5FA; }
code { background: rgba(255,255,255,0.1); padding: 2px 4px; border-radius: 4px; }
pre { background: rgba(0,0,0,0.3); padding: 15px; border-radius: 8px; overflow-x: auto; }
img { max-width: 100%; border-radius: 12px; }
"""

HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="zh-TW">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{title}</title>
    <style>{css}</style>
</head>
<body>
    <div class="container">
        {content}
    </div>
</body>
</html>
"""

def get_web_link(file_path):
    """將文件轉為網頁格式並返回 localhost 網址。"""
    if not os.path.exists(file_path):
        return None
    
    filename = os.path.basename(file_path)
    ext = os.path.splitext(filename)[1].lower()
    report_dir = "reports"
    os.makedirs(report_dir, exist_ok=True)
    
    target_filename = filename
    if ext == ".md":
        target_filename = filename.replace(".md", ".html")
        with open(file_path, "r", encoding="utf-8") as f:
            md_content = f.read()
        html_content = markdown.markdown(md_content, extensions=['fenced_code', 'tables'])
        full_html = HTML_TEMPLATE.format(title=filename, css=VIEWER_CSS, content=html_content)
        with open(os.path.join(report_dir, target_filename), "w", encoding="utf-8") as f:
            f.write(full_html)
            
    elif ext == ".docx":
        target_filename = filename.replace(".docx", ".html")
        with open(file_path, "rb") as f:
            result = mammoth.convert_to_html(f)
            html_content = result.value
        full_html = HTML_TEMPLATE.format(title=filename, css=VIEWER_CSS, content=html_content)
        with open(os.path.join(report_dir, target_filename), "w", encoding="utf-8") as f:
            f.write(full_html)
            
    elif ext in [".pdf", ".html", ".png", ".jpg", ".jpeg"]:
        shutil.copy2(file_path, os.path.join(report_dir, filename))
        target_filename = filename
    else:
        # 其他格式直接複製當作下載
        shutil.copy2(file_path, os.path.join(report_dir, filename))
        target_filename = filename

    return f"{REPORTS_BASE_URL}/{target_filename}"

if __name__ == "__main__":
    # Test
    test_file = "test.md"
    with open(test_file, "w") as f: f.write("# Hello World\nThis is a test.")
    print(f"Link: {get_web_link(test_file)}")
