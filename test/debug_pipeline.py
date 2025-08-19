#!/usr/bin/env python3
"""
Debug script to trace the entire viral analysis pipeline
"""

import sys
import os
sys.path.append('.')

from supabase_integration import SupabaseClient

def main():
    print("🔍 **DEBUGGING VIRAL ANALYSIS PIPELINE**")
    print("=" * 50)
    
    # Initialize Supabase client
    sb = SupabaseClient()
    
    # 1. Check latest analysis
    print("\n1. CHECKING LATEST ANALYSIS:")
    result = sb.supabase.table('viral_analysis_latest').select('*').order('created_at', desc=True).limit(1).execute()
    if not result.data:
        print("❌ No analysis found!")
        return
    
    analysis = result.data[0]
    analysis_id = analysis['id']
    print(f"✅ Latest Analysis ID: {analysis_id}")
    print(f"   Status: {analysis['status']}")
    print(f"   Created: {analysis['created_at']}")
    
    # 2. Check reels and transcripts
    print("\n2. CHECKING REELS AND TRANSCRIPTS:")
    reels = sb.supabase.table('viral_analysis_reels').select('*').eq('analysis_id', analysis_id).execute()
    print(f"   Total reels: {len(reels.data)}")
    
    transcript_completed = 0
    transcript_pending = 0
    for reel in reels.data:
        if reel.get('transcript_status') == 'completed':
            transcript_completed += 1
        else:
            transcript_pending += 1
    
    print(f"   Transcripts completed: {transcript_completed}")
    print(f"   Transcripts pending: {transcript_pending}")
    
    # Show a sample transcript
    completed_reels = [r for r in reels.data if r.get('transcript_status') == 'completed']
    if completed_reels:
        sample_reel = completed_reels[0]
        print(f"   Sample transcript length: {len(str(sample_reel.get('transcript_text', '')))}")
        print(f"   Sample reel has hook_analysis: {bool(sample_reel.get('hook_analysis'))}")
    
    # 3. Check analysis results
    print("\n3. CHECKING ANALYSIS RESULTS:")
    results = sb.supabase.table('viral_analysis_results').select('*').eq('analysis_id', analysis_id).execute()
    print(f"   Analysis results records: {len(results.data)}")
    
    if results.data:
        for i, result in enumerate(results.data):
            print(f"   Result {i+1}: ID={result['id'][:8]}...")
            print(f"                AI Status: {result.get('ai_status', 'None')}")
            print(f"                Created: {result['created_at']}")
    
    # 4. Check viral ideas
    print("\n4. CHECKING VIRAL IDEAS:")
    ideas = sb.supabase.table('viral_ideas').select('*').eq('analysis_id', analysis_id).execute()
    print(f"   Viral ideas generated: {len(ideas.data)}")
    
    # 5. Check scripts
    print("\n5. CHECKING GENERATED SCRIPTS:")
    scripts = sb.supabase.table('generated_scripts').select('*').eq('analysis_id', analysis_id).execute()
    print(f"   Generated scripts: {len(scripts.data)}")
    
    # 6. Check if we can trigger AI manually
    print("\n6. CHECKING AI TRIGGER CONDITIONS:")
    
    # Check if status allows AI processing
    if analysis['status'] != 'transcripts_completed':
        print(f"   ❌ Status is '{analysis['status']}', should be 'transcripts_completed'")
        return
    else:
        print("   ✅ Status is 'transcripts_completed'")
    
    # Check if we have enough transcripts
    if transcript_completed < 5:
        print(f"   ❌ Only {transcript_completed} transcripts completed, need at least 5")
        return
    else:
        print(f"   ✅ Have {transcript_completed} completed transcripts")
    
    # Check if AI already ran
    if results.data and any(r.get('ai_status') == 'completed' for r in results.data):
        print("   ⚠️  AI already completed for this analysis")
    else:
        print("   ✅ AI has not run yet - ready to trigger!")
    
    print("\n" + "=" * 50)
    print("🎯 **ANALYSIS COMPLETE**")
    
    # Show the actual issue
    if transcript_completed >= 5 and analysis['status'] == 'transcripts_completed':
        if not results.data or not any(r.get('ai_status') == 'completed' for r in results.data):
            print("🚨 **ISSUE FOUND**: AI should have triggered but didn't!")
            print("   This analysis is ready for AI processing.")
            
            # Check if processor is running
            print("\n7. CHECKING PROCESSOR STATUS:")
            print("   Let's see if the viral processor is even checking this analysis...")
            
            # Try to import the AI pipeline
            print("\n8. TESTING AI PIPELINE IMPORT:")
            try:
                import viral_ideas_ai_pipeline
                print("   ✅ AI pipeline imports successfully")
                print(f"   ✅ ViralIdeasAI class available: {hasattr(viral_ideas_ai_pipeline, 'ViralIdeasAI')}")
                print(f"   ✅ process_viral_analysis function available: {hasattr(viral_ideas_ai_pipeline, 'process_viral_analysis')}")
            except Exception as e:
                print(f"   ❌ AI pipeline import failed: {e}")
                print("   🔧 This is likely the root cause!")
    
if __name__ == "__main__":
    main()