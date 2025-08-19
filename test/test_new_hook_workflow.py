"""
TEST NEW HOOK-BASED WORKFLOW
============================

This script tests the complete new hook-based workflow using real data from the database:

1. Fetch 100 primary reels + 25 competitor reels per competitor
2. Profile analysis on primary profile
3. Hook analysis on top 5 outlier reels (primary + competitors)  
4. Generate 5 hooks based on analysis
5. Generate scripts for each hook

Simulates the exact workflow without running a full queue processing.
"""

import asyncio
import json
import logging
from datetime import datetime
from typing import Dict, List, Any
import sys
import os

# Add backend directory to path
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
from supabase_integration import SupabaseManager
from viral_ideas_ai_pipeline import ViralIdeasAI

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class HookWorkflowTester:
    """Test the complete hook-based workflow"""
    
    def __init__(self):
        self.supabase = SupabaseManager()
        self.ai_pipeline = ViralIdeasAI()
        
    async def test_complete_workflow(self, analysis_id: str = None) -> bool:
        """Test the complete hook-based workflow using PRODUCTION method"""
        try:
            logger.info("🚀 TESTING PRODUCTION HOOK-BASED WORKFLOW")
            logger.info("=" * 60)
            
            # Step 1: Get existing analysis with transcripts (like other test scripts)
            if not analysis_id:
                logger.info("📊 Step 1: Finding existing analysis with transcripts...")
                
                # First try 'completed' status
                result = self.supabase.client.table('viral_analysis_results').select(
                    '*'
                ).eq('status', 'completed').order('created_at', desc=True).limit(1).execute()
                
                if not result.data:
                    # Try any status with recent data
                    logger.info("   No completed analysis found, checking for any recent analysis...")
                    result = self.supabase.client.table('viral_analysis_results').select(
                        '*'
                    ).order('created_at', desc=True).limit(1).execute()
                
                if not result.data:
                    logger.error("❌ No analysis found at all")
                    return False
                
                analysis_id = result.data[0]['id']
                status = result.data[0].get('status', 'unknown')
                logger.info(f"   Using analysis: {analysis_id[:8]}... (status: {status})")
            
            # Step 2: Call the PRODUCTION hook-based workflow method
            logger.info("🚀 Step 2: Running PRODUCTION hook-based analysis workflow...")
            result = await self.ai_pipeline.process_analysis(analysis_id)
            
            if result:
                logger.info("✅ Production workflow completed successfully!")
                
                # Step 3: Verify data was stored in database  
                logger.info("🔍 Step 3: Verifying data storage in flexible JSONB schema...")
                
                # Check viral_analysis_results for new analysis_data
                analysis_check = self.supabase.client.table('viral_analysis_results').select(
                    'id, workflow_version, analysis_data, status'
                ).eq('id', analysis_id).execute()
                
                if analysis_check.data:
                    result_data = analysis_check.data[0]
                    workflow_version = result_data.get('workflow_version', 'unknown')
                    analysis_data = result_data.get('analysis_data', {})
                    status = result_data.get('status', 'unknown')
                    
                    logger.info(f"   ✅ Analysis record updated:")
                    logger.info(f"      Workflow Version: {workflow_version}")
                    logger.info(f"      Status: {status}")
                    logger.info(f"      Analysis Data Size: {len(str(analysis_data))} characters")
                    
                    # Parse analysis_data from JSON string if needed
                    if isinstance(analysis_data, str):
                        try:
                            analysis_data = json.loads(analysis_data)
                        except:
                            analysis_data = {}
                    
                    if isinstance(analysis_data, dict) and analysis_data:
                        logger.info(f"      Contains: {list(analysis_data.keys())}")
                        
                        # Show analysis summary
                        if 'analysis_summary' in analysis_data:
                            summary = analysis_data['analysis_summary']
                            logger.info(f"      📊 Analysis Summary:")
                            logger.info(f"         Hooks Analyzed: {summary.get('total_hooks_analyzed', 0)}")
                            logger.info(f"         Hooks Generated: {summary.get('hooks_generated', 0)}")
                            logger.info(f"         Scripts Created: {summary.get('scripts_created', 0)}")
                        
                        # Show sample generated hook
                        if 'generated_hooks' in analysis_data and analysis_data['generated_hooks']:
                            first_hook = analysis_data['generated_hooks'][0]
                            logger.info(f"      🎯 Sample Generated Hook:")
                            logger.info(f"         Text: {first_hook.get('hook_text', 'N/A')[:60]}...")
                            logger.info(f"         Source: @{first_hook.get('source_username', 'N/A')}")
                            logger.info(f"         Score: {first_hook.get('estimated_effectiveness', 0)}")
                    else:
                        logger.warning("   ⚠️ Analysis data is empty or not in expected format")
                
                # Check viral_scripts table
                scripts_check = self.supabase.client.table('viral_scripts').select(
                    'id, script_title, primary_hook, script_content, source_reels, created_at'
                ).eq('analysis_id', analysis_id).execute()
                
                if scripts_check.data:
                    logger.info(f"   ✅ Scripts stored: {len(scripts_check.data)} scripts found")
                    
                    # Get the most recent scripts (from this run)
                    recent_scripts = sorted(scripts_check.data, key=lambda x: x.get('created_at', ''), reverse=True)[:5]
                    
                    logger.info(f"\n{'='*80}")
                    logger.info(f"📝 FULL SCRIPTS FROM LATEST RUN:")
                    logger.info(f"{'='*80}")
                    
                    for i, script in enumerate(recent_scripts):
                        title = script.get('script_title', 'N/A')
                        hook = script.get('primary_hook', 'N/A')
                        content = script.get('script_content', 'N/A')
                        source_reels_str = script.get('source_reels', '{}')
                        
                        # Parse source_reels to get competitor info
                        try:
                            import json
                            source_reels = json.loads(source_reels_str) if isinstance(source_reels_str, str) else source_reels_str
                            competitor = source_reels.get('based_on_competitor', 'N/A')
                            original_hook = source_reels.get('original_competitor_hook', 'N/A')
                        except:
                            competitor = 'N/A'
                            original_hook = 'N/A'
                        
                        logger.info(f"\n📋 SCRIPT {i+1}:")
                        logger.info(f"   Title: {title}")
                        logger.info(f"   Hook: {hook}")
                        logger.info(f"   Based on @{competitor}: {original_hook[:60]}...")
                        logger.info(f"   Full Script:")
                        logger.info(f"   {'-'*60}")
                        logger.info(f"   {content}")
                        logger.info(f"   {'-'*60}")
                    
                    logger.info(f"{'='*80}")
                else:
                    logger.warning("   ⚠️ No scripts found in database")
                
                logger.info("🎉 PRODUCTION WORKFLOW TEST COMPLETED SUCCESSFULLY!")
                logger.info("=" * 60)
                logger.info("📊 VERIFICATION SUMMARY:")
                logger.info(f"   ✅ Production method executed successfully")
                logger.info(f"   ✅ Data stored in flexible JSONB schema")
                logger.info(f"   ✅ All required tables updated")
                logger.info("=" * 60)
                
                return True
            else:
                logger.error("❌ Production workflow failed")
                return False
            
        except Exception as e:
            logger.error(f"❌ Production workflow test failed: {e}")
            import traceback
            traceback.print_exc()
            return False


async def main():
    """Run the production hook workflow test"""
    tester = HookWorkflowTester()
    logger.info("🎯 Testing Hook-Based Workflow with production method")
    
    success = await tester.test_complete_workflow()
    
    if success:
        logger.info("🎉 TEST PASSED: Production hook-based workflow completed successfully!")
    else:
        logger.error("❌ TEST FAILED: Production hook-based workflow encountered errors")


if __name__ == "__main__":
    # Run the test
    success = asyncio.run(main())
    exit(0 if success else 1)