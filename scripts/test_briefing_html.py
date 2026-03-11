import asyncio
import os
import sys
sys.path.append(os.getcwd())

from services.briefing import get_briefing_data, generate_briefing_html

async def verify():
    print("Testing Briefing Data Extraction...")
    data = get_briefing_data()
    print(f"Date: {data['date']}")
    print(f"Sections found: {len(data['sections'])}")
    
    print("\nTesting HTML Generation...")
    html_path = generate_briefing_html(data)
    print(f"HTML generated at: {html_path}")
    
    if os.path.exists(html_path):
        print("✅ Success: HTML file exists.")
        size = os.path.getsize(html_path)
        print(f"File size: {size} bytes")
        
        with open(html_path, "r", encoding="utf-8") as f:
            content = f.read()
            if "Morning Briefing" in content and "class=\"section\"" in content:
                print("✅ Success: HTML content looks correct.")
            else:
                print("❌ Error: HTML content missing expected markers.")
    else:
        print("❌ Error: HTML file not found.")

if __name__ == "__main__":
    asyncio.run(verify())
