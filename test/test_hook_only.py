#!/usr/bin/env python3
"""Quick test for hook analysis only"""

import sys
import asyncio
sys.path.append('.')

# Load environment variables first
try:
    from dotenv import load_dotenv
    load_dotenv()
    print("✅ Environment variables loaded from .env")
except ImportError:
    print("⚠️ python-dotenv not installed, using system environment")

# Import main first to initialize environment
import main
from viral_ideas_ai_pipeline import ViralIdeasAI
from supabase_integration import SupabaseManager

async def test_hook_analysis():
    print("🎯 **HOOK ANALYSIS TEST**")
    print("=" * 40)
    
    # Initialize
    sb = SupabaseManager()
    ai_processor = ViralIdeasAI()
    
    # Find analysis with transcripts
    result = sb.client.table('viral_analysis_results').select('*').eq('status', 'transcripts_completed').order('created_at', desc=True).limit(1).execute()
    
    if not result.data:
        print("❌ No analysis found")
        return
        
    analysis_id = result.data[0]['id']
    print(f"✅ Testing analysis: {analysis_id[:8]}...")
    
    # Get reels with transcripts
    reel_data = await ai_processor._get_analysis_reels(analysis_id)
    print(f"✅ Found {len(reel_data)} reels with transcripts")
    
    if reel_data:
        # Test hook analysis on first reel
        sample_reel = reel_data[0]
        print(f"📝 Testing hook analysis on: {sample_reel.get('content_id', 'Unknown')}")
        print(f"   Transcript preview: {sample_reel.get('transcript_text', '')[:100]}...")
        
        # Run hook analysis 
        await ai_processor._process_hook_analysis([sample_reel])
        print("✅ Hook analysis completed!")
        
        # Check what was stored
        reel_id = sample_reel.get('id')
        if reel_id:
            updated_reel = sb.client.table('viral_analysis_reels').select('hook_text, power_words').eq('id', reel_id).execute()
            if updated_reel.data:
                hook_text = updated_reel.data[0].get('hook_text', '')
                power_words = updated_reel.data[0].get('power_words', [])
                print(f"📊 Stored hook_text: {hook_text[:100]}...")
                print(f"📊 Stored power_words: {power_words}")
    
    print("\n" + "=" * 40)
    print("🎯 **TEST COMPLETE**")

if __name__ == "__main__":
    asyncio.run(test_hook_analysis())