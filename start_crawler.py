#!/usr/bin/env python3
"""
Simple crawler startup script - self-contained version
"""
import asyncio
import sys
import os

# Load environment variables from .env file
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    print("Warning: python-dotenv not installed. Install with: pip install python-dotenv")
    print("Or set environment variables manually")

async def start_discovery():
    """Start simple profile discovery - get similar profiles and queue 4 best ones"""
    
    # Import the enhanced crawler with Supabase support
    from network_crawler import create_crawler
    
    print("🚀 Starting Instagram Network Discovery...")
    print("🎯 Simple discovery: find similar profiles and queue 4 best ones")
    
    # Check if Supabase is available
    try:
        from supabase_integration import SupabaseManager
        supabase_available = True
        print("☁️ Supabase integration: AVAILABLE")
    except:
        supabase_available = False
        print("💾 Storage: CSV only (Supabase not configured)")
    
    # Create crawler with simple config
    crawler = await create_crawler()
    
    # Get the starting profile (resume or default)
    start_profile = crawler.get_resume_profile()
    
    print(f"📍 Starting from: @{start_profile}")
    print(f"🎯 Will queue max 4 accounts for scraping")
    
    # Check RapidAPI key
    api_key = os.getenv('RAPIDAPI_KEY') or os.getenv('INSTAGRAM_SCRAPER_API_KEY')
    if not api_key:
        print("⚠️ Warning: No RapidAPI key found")
        print("   Set RAPIDAPI_KEY or INSTAGRAM_SCRAPER_API_KEY environment variable")
        return
    
    # Start discovery
    try:
        result = await crawler.start_discovery([start_profile])
        print("\n✅ Discovery completed!")
        print(f"🔍 Similar found: {result.similar_found} profiles")
        print(f"🎯 Selected: {result.selected} profiles")
        print(f"📋 Queued for scraping: {result.queued} accounts")
        print(f"⏭️ Duplicates skipped: {result.skipped_duplicates}")
        
        if result.queued > 0:
            print(f"\n🎉 Success! {result.queued} profiles added to queue")
            if supabase_available and crawler.use_supabase:
                if crawler.supabase and crawler.supabase.keep_local_csv:
                    print("☁️ Profiles saved to both Supabase and CSV")
                else:
                    print("☁️ Profiles saved to Supabase")
            else:
                print("💾 Profiles saved to local queue")
            print("\n📋 Start the queue processor to begin scraping:")
            print("   python queue_processor.py --start")
        
    except Exception as e:
        print(f"❌ Discovery failed: {e}")

if __name__ == "__main__":
    asyncio.run(start_discovery())