import asyncio
import os
import sys
import time
sys.path.append(os.getcwd())

from services.briefing import get_briefing_data

async def verify():
    print("Testing Briefing Data Extraction...")
    start_time = time.time()
    
    # 測試個別功能
    print("\n--- Testing Email ---")
    t0 = time.time()
    from services.google_workspace import fetch_unread_emails
    emails = fetch_unread_emails(max_results=3)
    print(f"Emails found: {len(emails)}, Time: {time.time()-t0:.2f}s")
    
    print("\n--- Testing Calendar ---")
    t0 = time.time()
    from services.google_workspace import fetch_today_events
    events = fetch_today_events()
    print(f"Events found: {len(events)}, Time: {time.time()-t0:.2f}s")
    
    print("\n--- Testing Apify News ---")
    t0 = time.time()
    from services.apify_news import get_apify_news
    news = get_apify_news()
    print(f"News length: {len(news) if news else 0}, Time: {time.time()-t0:.2f}s")

    print(f"\nTotal Time: {time.time()-start_time:.2f}s")

if __name__ == "__main__":
    asyncio.run(verify())
