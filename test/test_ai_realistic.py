#!/usr/bin/env python3
"""
Realistic AI Pipeline Test
==========================
Test the AI pipeline with real data from the database
"""

import sys
import asyncio
import json
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
from viral_ideas_ai_pipeline import process_viral_analysis
from supabase_integration import SupabaseManager

async def test_ai_pipeline():
    print("🧪 **REALISTIC AI PIPELINE TEST**")
    print("=" * 50)
    
    # Initialize Supabase
    sb = SupabaseManager()
    
    # 1. Find an analysis ready for AI
    print("\n1. FINDING ANALYSIS READY FOR AI:")
    # Look for analyses where transcripts are completed but AI hasn't run yet
    result = sb.client.table('viral_analysis_results').select('*').eq('status', 'transcripts_completed').order('created_at', desc=True).limit(1).execute()
    
    if not result.data:
        print("❌ No analysis with status 'transcripts_completed' found")
        
        # Get any recent analysis and check its status
        print("\n🔧 Checking for any recent analysis...")
        any_analysis = sb.client.table('viral_analysis_results').select('*').order('created_at', desc=True).limit(1).execute()
        if not any_analysis.data:
            print("❌ No analysis found at all")
            return
            
        analysis_id = any_analysis.data[0]['id']
        current_status = any_analysis.data[0]['status']
        print(f"Latest analysis: {analysis_id}")
        print(f"Current status: {current_status}")
        
        # Use this analysis for testing
        print("🧪 Using this analysis for testing...")
        
    else:
        analysis_id = result.data[0]['id']
        print(f"✅ Found analysis ready for AI: {analysis_id}")
    
    # 2. Check the reels data
    print(f"\n2. CHECKING REELS DATA FOR {analysis_id[:8]}...:")
    reels = sb.client.table('viral_analysis_reels').select('*').eq('analysis_id', analysis_id).execute()
    
    print(f"   Total reels: {len(reels.data)}")
    
    # Count transcripts - check the correct columns from schema
    completed_transcripts = [r for r in reels.data if r.get('transcript_completed') == True]
    print(f"   Completed transcripts: {len(completed_transcripts)}")
    
    # Also check if any reels have actual transcript data in the content table
    print(f"   Checking content table for transcript data...")
    
    if len(completed_transcripts) < 3:
        print("⚠️  Not enough completed transcripts, but let's check content table...")
        
        # Check content table for transcript data
        for reel in reels.data[:3]:  # Check first 3 reels
            content_id = reel.get('content_id')
            if content_id:
                content_result = sb.client.table('content').select('transcript, transcript_available').eq('content_id', content_id).execute()
                if content_result.data and content_result.data[0].get('transcript'):
                    print(f"   ✅ Found transcript for {content_id}")
                    completed_transcripts.append(reel)
        
        print(f"   Total with transcripts: {len(completed_transcripts)}")
    
    if len(completed_transcripts) == 0:
        print("❌ No transcripts available for AI analysis")
        return
    
    # Show sample transcript
    sample_reel = completed_transcripts[0]
    print(f"   Sample reel ID: {sample_reel.get('content_id', 'Unknown')}")
    
    # Get actual transcript from content table to show structure
    content_result = sb.client.table('content').select('transcript').eq('content_id', sample_reel.get('content_id')).execute()
    if content_result.data and content_result.data[0].get('transcript'):
        transcript_data = content_result.data[0]['transcript']
        
        # Extract text like the AI pipeline does
        if isinstance(transcript_data, dict) and 'content' in transcript_data:
            text_segments = []
            for segment in transcript_data['content']:
                if 'text' in segment:
                    text_segments.append(segment['text'])
            transcript_text = ' '.join(text_segments)
        else:
            transcript_text = str(transcript_data)
        
        print(f"   Sample transcript length: {len(transcript_text)} chars")
        print(f"   Sample (first 150 chars): {transcript_text[:150]}...")
    else:
        print("   No transcript data found")
    
    # 3. Test AI Processing
    print(f"\n3. RUNNING AI ANALYSIS:")
    print(f"   Analysis ID: {analysis_id}")
    print("   Starting AI processing...")
    
    try:
        # This is the actual function that fails in the real pipeline
        ai_success = await process_viral_analysis(analysis_id)
        
        if ai_success:
            print("✅ AI Analysis completed successfully!")
            
            # 4. Check what was created
            print("\n4. CHECKING AI RESULTS:")
            
            # Check analysis results
            results = sb.client.table('viral_analysis_results').select('*').eq('analysis_id', analysis_id).execute()
            print(f"   Analysis results: {len(results.data)} records")
            
            if results.data:
                latest_result = results.data[-1]  # Get the latest
                print(f"   Latest result ID: {latest_result['id'][:8]}...")
                print(f"   AI Status: {latest_result.get('ai_status', 'None')}")
                
                # Print a snippet of the analysis
                if latest_result.get('analysis_summary'):
                    summary = latest_result['analysis_summary']
                    print(f"   Analysis summary (first 200 chars): {str(summary)[:200]}...")
            
            # Check viral ideas
            ideas = sb.client.table('viral_ideas').select('*').eq('analysis_id', analysis_id).execute()
            print(f"   Viral ideas generated: {len(ideas.data)}")
            
            if ideas.data:
                sample_idea = ideas.data[0]
                print(f"   Sample idea: {sample_idea.get('idea_title', 'No title')}")
            
            # Check scripts
            scripts = sb.client.table('generated_scripts').select('*').eq('analysis_id', analysis_id).execute()
            print(f"   Generated scripts: {len(scripts.data)}")
            
            if scripts.data:
                sample_script = scripts.data[0]
                print(f"   Sample script: {sample_script.get('script_title', 'No title')}")
            
        else:
            print("❌ AI Analysis failed")
            
    except Exception as e:
        print(f"❌ AI Analysis error: {e}")
        import traceback
        traceback.print_exc()
    
    print("\n" + "=" * 50)
    print("🎯 **TEST COMPLETE**")

if __name__ == "__main__":
    asyncio.run(test_ai_pipeline())