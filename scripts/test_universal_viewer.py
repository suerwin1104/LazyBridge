import os
import sys
import asyncio

sys.path.append(os.getcwd())

from services.document_viewer import get_web_link

def test_viewer():
    print("🚀 Testing Universal Web Document Viewer...")
    
    # Test Markdown
    md_file = "test_report.md"
    with open(md_file, "w", encoding="utf-8") as f:
        f.write("# 測試報告\n\n這是一個測試 Markdown 轉換為網頁的範例。\n\n- 優點 1\n- 優點 2")
    
    md_link = get_web_link(md_file)
    print(f"✅ Markdown link: {md_link}")
    
    # Test HTML (Direct copy)
    html_file = "test_doc.html"
    with open(html_file, "w", encoding="utf-8") as f:
        f.write("<html><body><h1>Hello HTML</h1></body></html>")
    
    html_link = get_web_link(html_file)
    print(f"✅ HTML link: {html_link}")
    
    # Clean up local test files (keeping reports/)
    os.remove(md_file)
    os.remove(html_file)
    
    print("\n✨ Verification Complete!")

if __name__ == "__main__":
    test_viewer()
