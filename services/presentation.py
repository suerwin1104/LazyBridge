import os
import re
from core.config import log

HTML_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>{title}</title>
    <style>
        body {{ font-family: 'Inter', sans-serif; background: #0f172a; color: #f8fafc; margin: 0; display: flex; align-items: center; justify-content: center; height: 100vh; overflow: hidden; }}
        .slide {{ background: #1e293b; border-radius: 12px; padding: 40px; box-shadow: 0 4px 6px -1px rgb(0 0 0 / 0.1); max-width: 800px; width: 90%; text-align: left; opacity: 0; transform: translateY(20px); transition: all 0.5s ease; position: absolute; }}
        .slide.active {{ opacity: 1; transform: translateY(0); z-index: 10; }}
        h1 {{ color: #38bdf8; font-size: 2.5rem; margin-bottom: 20px; }}
        p {{ line-height: 1.6; font-size: 1.2rem; }}
        .nav {{ position: fixed; bottom: 20px; display: flex; gap: 10px; }}
        button {{ background: #334155; border: none; color: white; padding: 10px 20px; border-radius: 6px; cursor: pointer; transition: background 0.3s; }}
        button:hover {{ background: #475569; }}
    </style>
</head>
<body>
    {slides_html}
    <div class="nav">
        <button onclick="prevSlide()">Prev</button>
        <button onclick="nextSlide()">Next</button>
    </div>
    <script>
        let currentSlide = 0;
        const slides = document.querySelectorAll('.slide');
        function showSlide(n) {{
            slides[currentSlide].classList.remove('active');
            currentSlide = (n + slides.length) % slides.length;
            slides[currentSlide].classList.add('active');
        }}
        function nextSlide() {{ showSlide(currentSlide + 1); }}
        function prevSlide() {{ showSlide(currentSlide - 1); }}
        showSlide(0);
        document.addEventListener('keydown', (e) => {{
            if (e.key === 'ArrowRight') nextSlide();
            if (e.key === 'ArrowLeft') prevSlide();
        }});
    </script>
</body>
</html>
"""

async def generate_presentation(title: str, sections: list) -> str:
    """Generates an HTML presentation and returns the file path."""
    slides_html = ""
    for i, section in enumerate(sections):
        active_class = "active" if i == 0 else ""
        content_html = section.get('content', '').replace('\\n', '<br>')
        slides_html += f'''
        <div class="slide {active_class}">
            <h1>{section.get('title', 'Slide')}</h1>
            <p>{content_html}</p>
        </div>
        '''
    
    html_content = HTML_TEMPLATE.format(title=title, slides_html=slides_html)
    
    # Save to a dedicated reports folder
    os.makedirs("reports", exist_ok=True)
    # 清理檔名：移除 Windows 不允許的字元
    safe_title = re.sub(r'[\\/:*?"<>|，。、；：！]', '', title)
    safe_title = safe_title.lower().replace(' ', '_')[:60]
    if not safe_title:
        safe_title = "presentation"
    filename = f"reports/presentation_{safe_title}.html"
    
    with open(filename, "w", encoding="utf-8") as f:
        f.write(html_content)
    
    # 在 Windows 上使用標準 localhost:8080
    url = f"http://localhost:8080/{os.path.basename(filename)}"
    log(f"🎨 [PresentationBuilder] HTML Presentation generated: {filename} -> {url}")
    return url
