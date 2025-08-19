#!/usr/bin/env python3
"""Test that AI pipeline data is properly formatted for frontend consumption"""

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

async def test_frontend_data_expectations():
    print("🖥️ **FRONTEND DATA EXPECTATIONS TEST**")
    print("=" * 60)
    
    # Initialize
    sb = SupabaseManager()
    ai_processor = ViralIdeasAI()
    
    # Find analysis with AI results
    result = sb.client.table('viral_analysis_results').select('*').eq('status', 'ai_completed').order('created_at', desc=True).limit(1).execute()
    
    if not result.data:
        print("❌ No completed AI analysis found")
        print("🔧 Let's run a quick AI analysis first...")
        
        # Find an analysis ready for AI
        pending_result = sb.client.table('viral_analysis_results').select('*').eq('status', 'transcripts_completed').order('created_at', desc=True).limit(1).execute()
        
        if not pending_result.data:
            print("❌ No analysis ready for AI processing")
            return
            
        analysis_id = pending_result.data[0]['id']
        print(f"🔄 Running AI analysis on: {analysis_id[:8]}...")
        
        # Run AI analysis
        from viral_ideas_ai_pipeline import process_viral_analysis
        success = await process_viral_analysis(analysis_id)
        
        if not success:
            print("❌ AI analysis failed")
            return
            
        print("✅ AI analysis completed")
        result = sb.client.table('viral_analysis_results').select('*').eq('id', analysis_id).execute()
    
    analysis_data = result.data[0]
    analysis_id = analysis_data['id']
    
    print(f"📊 Testing data for analysis: {analysis_id[:8]}...")
    
    # Test 1: Check viral_analysis_results data
    print("\n1️⃣ CHECKING VIRAL ANALYSIS RESULTS:")
    print(f"   Status: {analysis_data.get('status')}")
    print(f"   Total reels analyzed: {analysis_data.get('total_reels_analyzed', 0)}")
    print(f"   Primary reels: {analysis_data.get('primary_reels_count', 0)}")
    print(f"   Competitor reels: {analysis_data.get('competitor_reels_count', 0)}")
    print(f"   Has viral_ideas: {bool(analysis_data.get('viral_ideas'))}")
    print(f"   Has trending_patterns: {bool(analysis_data.get('trending_patterns'))}")
    print(f"   Has hook_analysis: {bool(analysis_data.get('hook_analysis'))}")
    print(f"   Has raw_ai_output: {bool(analysis_data.get('raw_ai_output'))}")
    
    # Test 2: Check viral_ideas data (what frontend expects)
    print("\n2️⃣ CHECKING VIRAL IDEAS DATA:")
    ideas_result = sb.client.table('viral_ideas').select(
        'id, idea_text, idea_rank, explanation, category, confidence_score, power_words'
    ).eq('analysis_id', analysis_id).order('idea_rank').execute()
    
    frontend_expected_idea_fields = ['id', 'idea_text', 'idea_rank', 'explanation', 'category', 'confidence_score', 'power_words']
    
    if ideas_result.data:
        print(f"   Found {len(ideas_result.data)} viral ideas")
        for i, idea in enumerate(ideas_result.data[:2]):  # Show first 2
            print(f"   Idea {i+1}:")
            for field in frontend_expected_idea_fields:
                value = idea.get(field)
                status = "✅" if value is not None else "❌"
                print(f"     {status} {field}: {str(value)[:50]}{'...' if str(value) and len(str(value)) > 50 else ''}")
    else:
        print("   ❌ No viral ideas found")
    
    # Test 3: Check scripts data (what frontend expects)
    print("\n3️⃣ CHECKING SCRIPTS DATA:")
    scripts_result = sb.client.table('viral_scripts').select(
        'id, script_title, script_content, script_type, estimated_duration, target_audience, primary_hook, call_to_action, status'
    ).eq('analysis_id', analysis_id).order('created_at', desc=True).execute()
    
    frontend_expected_script_fields = ['id', 'script_title', 'script_content', 'script_type', 'estimated_duration', 'target_audience', 'primary_hook', 'call_to_action', 'status']
    
    if scripts_result.data:
        print(f"   Found {len(scripts_result.data)} scripts")
        for i, script in enumerate(scripts_result.data[:1]):  # Show first script
            print(f"   Script {i+1}:")
            for field in frontend_expected_script_fields:
                value = script.get(field)
                status = "✅" if value is not None else "❌"
                print(f"     {status} {field}: {str(value)[:50]}{'...' if str(value) and len(str(value)) > 50 else ''}")
    else:
        print("   ❌ No scripts found")
    
    # Test 4: Check analyzed reels data (what frontend expects for reel display)
    print("\n4️⃣ CHECKING ANALYZED REELS DATA:")
    reels_result = sb.client.table('viral_analysis_reels').select(
        'content_id, reel_type, username, rank_in_selection, view_count_at_analysis, like_count_at_analysis, comment_count_at_analysis, transcript_completed, hook_text, power_words'
    ).eq('analysis_id', analysis_id).order('reel_type, rank_in_selection').execute()
    
    frontend_expected_reel_fields = ['content_id', 'reel_type', 'username', 'rank_in_selection', 'view_count_at_analysis', 'like_count_at_analysis', 'transcript_completed', 'hook_text', 'power_words']
    
    if reels_result.data:
        print(f"   Found {len(reels_result.data)} analyzed reels")
        primary_reels = [r for r in reels_result.data if r.get('reel_type') == 'primary']
        competitor_reels = [r for r in reels_result.data if r.get('reel_type') == 'competitor']
        print(f"   - Primary reels: {len(primary_reels)}")
        print(f"   - Competitor reels: {len(competitor_reels)}")
        
        # Show sample reel data
        sample_reel = reels_result.data[0]
        print(f"   Sample reel ({sample_reel.get('reel_type', 'unknown')}):")
        for field in frontend_expected_reel_fields:
            value = sample_reel.get(field)
            status = "✅" if value is not None else "❌"
            print(f"     {status} {field}: {str(value)[:50]}{'...' if str(value) and len(str(value)) > 50 else ''}")
    else:
        print("   ❌ No analyzed reels found")
    
    # Test 5: Simulate backend API response format
    print("\n5️⃣ SIMULATING BACKEND API RESPONSE:")
    api_response = {
        'analysis': analysis_data,
        'viral_ideas': ideas_result.data or [],
        'scripts': scripts_result.data or [],
        'analyzed_reels': reels_result.data or []
    }
    
    print(f"   API Response structure:")
    print(f"   ✅ analysis: {len(api_response['analysis'])} fields")
    print(f"   ✅ viral_ideas: {len(api_response['viral_ideas'])} items")
    print(f"   ✅ scripts: {len(api_response['scripts'])} items")
    print(f"   ✅ analyzed_reels: {len(api_response['analyzed_reels'])} items")
    
    # Test 6: Check for missing data that frontend might need
    print("\n6️⃣ FRONTEND DATA COMPLETENESS CHECK:")
    
    issues = []
    
    # Check if we have enough data for a good frontend experience
    if len(api_response['viral_ideas']) == 0:
        issues.append("❌ No viral ideas - frontend will show fallback examples")
    
    if len(api_response['scripts']) == 0:
        issues.append("❌ No scripts - frontend won't be able to show generated content")
    
    if len(api_response['analyzed_reels']) == 0:
        issues.append("❌ No analyzed reels - frontend can't show which reels were used")
    
    # Check if reels have hook analysis
    reels_with_hooks = [r for r in api_response['analyzed_reels'] if r.get('hook_text')]
    if len(reels_with_hooks) == 0:
        issues.append("❌ No reels have hook analysis - missing AI analysis data")
    
    # Check if trending patterns exist
    if not analysis_data.get('trending_patterns'):
        issues.append("❌ No trending patterns - frontend won't show winning patterns")
    
    if issues:
        print("   Issues found:")
        for issue in issues:
            print(f"   {issue}")
    else:
        print("   ✅ All data looks complete for frontend consumption!")
    
    print("\n" + "=" * 60)
    print("🎯 **FRONTEND DATA TEST COMPLETE**")
    
    # Summary
    print(f"\n📋 **SUMMARY:**")
    print(f"✅ Analysis Status: {analysis_data.get('status')}")
    print(f"✅ Viral Ideas: {len(api_response['viral_ideas'])} generated")
    print(f"✅ Scripts: {len(api_response['scripts'])} generated")
    print(f"✅ Analyzed Reels: {len(api_response['analyzed_reels'])} with hook analysis")
    print(f"✅ Hook Analysis: {len(reels_with_hooks)} reels have hook text")
    
    if len(issues) == 0:
        print("\n🎉 **ALL DATA IS READY FOR FRONTEND!**")
    else:
        print(f"\n⚠️ **{len(issues)} ISSUES NEED ATTENTION**")

if __name__ == "__main__":
    asyncio.run(test_frontend_data_expectations())