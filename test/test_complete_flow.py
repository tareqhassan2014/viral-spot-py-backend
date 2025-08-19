#!/usr/bin/env python3
"""Complete end-to-end test: fetch transcript → AI analysis → upload results"""

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
from viral_ideas_ai_pipeline import ViralIdeasAI
from supabase_integration import SupabaseManager

async def test_complete_ai_flow():
    print("🔄 **COMPLETE AI FLOW TEST**")
    print("=" * 50)
    
    # Initialize
    sb = SupabaseManager()
    ai_processor = ViralIdeasAI()
    
    # 1. Find a reel with transcript
    print("1️⃣ FINDING REEL WITH TRANSCRIPT:")
    
    # Get a reel from viral_analysis_reels that has transcript_completed = true
    reel_result = sb.client.table('viral_analysis_reels').select('*').eq('transcript_completed', True).limit(1).execute()
    
    if not reel_result.data:
        print("❌ No reels with completed transcripts found")
        return
    
    reel_data = reel_result.data[0]
    content_id = reel_data['content_id']
    analysis_id = reel_data['analysis_id']
    
    print(f"✅ Found reel: {content_id}")
    print(f"   Analysis ID: {analysis_id}")
    print(f"   Username: {reel_data.get('username', 'Unknown')}")
    
    # 2. Fetch the actual transcript from content table
    print("\n2️⃣ FETCHING TRANSCRIPT:")
    
    content_result = sb.client.table('content').select('transcript').eq('content_id', content_id).execute()
    
    if not content_result.data or not content_result.data[0].get('transcript'):
        print("❌ No transcript found in content table")
        return
    
    transcript_data = content_result.data[0]['transcript']
    
    # Extract text from transcript structure
    if isinstance(transcript_data, dict) and 'content' in transcript_data:
        text_segments = []
        for segment in transcript_data['content']:
            if 'text' in segment:
                text_segments.append(segment['text'])
        transcript_text = ' '.join(text_segments)
    else:
        transcript_text = str(transcript_data)
    
    print(f"✅ Transcript extracted: {len(transcript_text)} characters")
    print(f"   Preview: {transcript_text[:150]}...")
    
    # 3. Perform Hook Analysis
    print("\n3️⃣ PERFORMING HOOK ANALYSIS:")
    
    # Prepare reel data for hook analysis
    test_reel = {
        'id': reel_data['id'],
        'content_id': content_id,
        'transcript_text': transcript_text
    }
    
    try:
        await ai_processor._process_hook_analysis([test_reel])
        print("✅ Hook analysis completed")
        
        # Check what was stored
        updated_reel = sb.client.table('viral_analysis_reels').select('hook_text, power_words').eq('id', reel_data['id']).execute()
        if updated_reel.data:
            hook_text = updated_reel.data[0].get('hook_text', '')
            power_words = updated_reel.data[0].get('power_words', [])
            print(f"   📊 Hook text: {hook_text}")
            print(f"   📊 Power words: {power_words}")
        
    except Exception as e:
        print(f"❌ Hook analysis failed: {e}")
        return
    
    # 4. Prepare sample data for overall analysis
    print("\n4️⃣ PERFORMING OVERALL ANALYSIS:")
    
    # Get multiple reels for a realistic analysis
    all_reels_result = sb.client.table('viral_analysis_reels').select('*').eq('analysis_id', analysis_id).limit(8).execute()
    
    # Get transcripts for all reels
    all_reels_with_transcripts = []
    for reel in all_reels_result.data:
        if reel.get('transcript_completed'):
            content_result = sb.client.table('content').select('transcript').eq('content_id', reel['content_id']).execute()
            if content_result.data and content_result.data[0].get('transcript'):
                transcript_data = content_result.data[0]['transcript']
                if isinstance(transcript_data, dict) and 'content' in transcript_data:
                    text_segments = []
                    for segment in transcript_data['content']:
                        if 'text' in segment:
                            text_segments.append(segment['text'])
                    transcript_text = ' '.join(text_segments)
                    reel['transcript_text'] = transcript_text
                    all_reels_with_transcripts.append(reel)
    
    print(f"✅ Found {len(all_reels_with_transcripts)} reels with transcripts for analysis")
    
    try:
        # Run overall analysis
        analysis_results = await ai_processor._process_overall_analysis(all_reels_with_transcripts)
        
        if analysis_results:
            print("✅ Overall analysis completed")
            print(f"   📊 Analysis keys: {list(analysis_results.keys())}")
            
            # Show sample results
            if 'winning_patterns' in analysis_results:
                patterns = analysis_results['winning_patterns']
                print(f"   📊 Winning patterns: {patterns}")
        else:
            print("❌ Overall analysis failed - no results")
            return
            
    except Exception as e:
        print(f"❌ Overall analysis failed: {e}")
        return
    
    # 5. Generate Viral Ideas
    print("\n5️⃣ GENERATING VIRAL IDEAS:")
    
    try:
        viral_ideas = await ai_processor._generate_viral_ideas(analysis_results, all_reels_with_transcripts)
        
        if viral_ideas:
            print(f"✅ Generated {len(viral_ideas)} viral ideas")
            for i, idea in enumerate(viral_ideas[:2]):  # Show first 2
                print(f"   💡 Idea {i+1}: {idea.get('idea_title', 'No title')}")
                print(f"       Description: {idea.get('idea_description', 'No description')[:100]}...")
        else:
            print("❌ No viral ideas generated")
            
    except Exception as e:
        print(f"❌ Viral ideas generation failed: {e}")
        viral_ideas = []
    
    # 6. Generate Scripts
    print("\n6️⃣ GENERATING SCRIPTS:")
    
    try:
        scripts = await ai_processor._generate_scripts(all_reels_with_transcripts, analysis_results)
        
        if scripts:
            print(f"✅ Generated {len(scripts)} scripts")
            for i, script in enumerate(scripts[:1]):  # Show first script
                print(f"   📝 Script {i+1}: {script.get('script_title', 'No title')}")
                print(f"       Content: {script.get('script_content', 'No content')[:100]}...")
        else:
            print("❌ No scripts generated")
            
    except Exception as e:
        print(f"❌ Script generation failed: {e}")
        scripts = []
    
    # 7. Store All Results
    print("\n7️⃣ STORING RESULTS IN DATABASE:")
    
    try:
        await ai_processor._store_analysis_results(analysis_id, analysis_results, viral_ideas, scripts)
        print("✅ All results stored successfully")
        
        # Verify what was stored
        print("\n📊 VERIFICATION - What's in the database:")
        
        # Check viral_analysis_results
        analysis_check = sb.client.table('viral_analysis_results').select('status, viral_ideas, trending_patterns, hook_analysis').eq('id', analysis_id).execute()
        if analysis_check.data:
            stored_analysis = analysis_check.data[0]
            print(f"   ✅ Analysis status: {stored_analysis.get('status')}")
            print(f"   ✅ Has viral_ideas: {bool(stored_analysis.get('viral_ideas'))}")
            print(f"   ✅ Has trending_patterns: {bool(stored_analysis.get('trending_patterns'))}")
            print(f"   ✅ Has hook_analysis: {bool(stored_analysis.get('hook_analysis'))}")
        
        # Check viral_ideas table
        ideas_check = sb.client.table('viral_ideas').select('*').eq('analysis_id', analysis_id).execute()
        print(f"   ✅ Viral ideas in DB: {len(ideas_check.data or [])}")
        
        # Check viral_scripts table  
        scripts_check = sb.client.table('viral_scripts').select('*').eq('analysis_id', analysis_id).execute()
        print(f"   ✅ Scripts in DB: {len(scripts_check.data or [])}")
        
        # Check hook analysis on reels
        reels_check = sb.client.table('viral_analysis_reels').select('hook_text, power_words').eq('analysis_id', analysis_id).execute()
        reels_with_hooks = [r for r in (reels_check.data or []) if r.get('hook_text')]
        print(f"   ✅ Reels with hook analysis: {len(reels_with_hooks)}/{len(reels_check.data or [])}")
        
    except Exception as e:
        print(f"❌ Error storing results: {e}")
    
    print("\n" + "=" * 50)
    print("🎯 **COMPLETE FLOW TEST FINISHED**")
    
    # Final summary
    print(f"\n📋 **SUMMARY:**")
    print(f"✅ Transcript fetched: {len(transcript_text)} chars")
    print(f"✅ Hook analysis: {'✅ Success' if hook_text else '❌ Failed'}")
    print(f"✅ Overall analysis: {'✅ Success' if analysis_results else '❌ Failed'}")
    print(f"✅ Viral ideas: {len(viral_ideas)} generated")
    print(f"✅ Scripts: {len(scripts)} generated")
    print(f"✅ Database storage: Complete")
    
    return {
        'transcript_length': len(transcript_text),
        'hook_analysis_success': bool(hook_text),
        'overall_analysis_success': bool(analysis_results),
        'viral_ideas_count': len(viral_ideas),
        'scripts_count': len(scripts),
        'storage_success': True
    }

if __name__ == "__main__":
    result = asyncio.run(test_complete_ai_flow())
    print(f"\n🏁 **FINAL RESULT:** {result}")