#!/usr/bin/env python3
"""
Test Script for Duplicate Handling Fixes
========================================

This script tests the fixes implemented for the viral pipeline duplicate handling issues:

1. Improved upsert conflict resolution (shortcode vs content_id)
2. Pre-insert duplicate checking 
3. Enhanced data verification with warnings system
4. Better error recovery with individual record saves

Author: AI Assistant
Date: 2024
"""

import asyncio
import json
import logging
from datetime import datetime
from typing import Dict, List, Any

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def test_duplicate_handling_fixes():
    """Test the duplicate handling improvements"""
    print("🧪 Testing Duplicate Handling Fixes")
    print("=" * 50)
    
    try:
        from supabase_integration import SupabaseManager
        
        # Initialize Supabase
        supabase = SupabaseManager()
        
        print("✅ Supabase connection established")
        
        # Test 1: Test duplicate detection
        print("\n1️⃣ Testing duplicate shortcode detection...")
        
        # Create test content with duplicate shortcodes
        test_content = [
            {
                'content_id': 'test_001',
                'shortcode': 'ABC123TEST',
                'username': 'test_user',
                'description': 'Test content 1',
                'view_count': 1000,
                'like_count': 100,
                'comment_count': 10,
                'date_posted': datetime.utcnow().isoformat()
            },
            {
                'content_id': 'test_002', 
                'shortcode': 'ABC123TEST',  # Duplicate shortcode
                'username': 'test_user',
                'description': 'Test content 2 (duplicate)',
                'view_count': 2000,
                'like_count': 200,
                'comment_count': 20,
                'date_posted': datetime.utcnow().isoformat()
            }
        ]
        
        # Test the improved save_content_batch method
        print("   Testing improved save_content_batch with duplicate detection...")
        
        # Create a test profile first
        test_profile = {
            'username': 'test_user',
            'profile_name': 'Test User',
            'followers': 10000,
            'following': 500,
            'post_count': 100,
            'profile_image_url': 'https://example.com/test.jpg',
            'bio': 'Test user for duplicate handling',
            'is_verified': False,
            'is_private': False,
            'account_type': 'personal'
        }
        
        profile_id = await supabase.save_primary_profile(test_profile)
        if profile_id:
            print(f"   ✅ Test profile created: {profile_id}")
            
            # Test content save with duplicates
            saved_count = await supabase.save_content_batch(test_content, profile_id, 'test_user')
            print(f"   📊 Saved {saved_count}/2 content records (should handle duplicate)")
            
            # Test 2: Test improved verification
            print("\n2️⃣ Testing improved data verification...")
            
            verification = await supabase.verify_data_integrity(
                profile_id, 
                2,  # Expected 2 records
                0,  # No secondary profiles expected
                'test_user'
            )
            
            print(f"   Verification success: {verification['success']}")
            print(f"   Content count: {verification['content_count']}/{verification['expected_content']}")
            print(f"   Secondary count: {verification['secondary_count']}/{verification['expected_secondary']}")
            
            if verification.get('warnings'):
                print("   ⚠️ Warnings:")
                for warning in verification['warnings']:
                    print(f"      • {warning}")
            
            if verification.get('errors'):
                print("   🚨 Errors:")
                for error in verification['errors']:
                    print(f"      • {error}")
            
            # Test 3: Test individual save fallback
            print("\n3️⃣ Testing individual save fallback...")
            
            # Create content that might cause batch failure
            problematic_content = [
                {
                    'content_id': 'test_003',
                    'shortcode': 'DEF456TEST',
                    'username': 'test_user',
                    'description': 'Test individual save',
                    'view_count': 500,
                    'like_count': 50,
                    'comment_count': 5,
                    'date_posted': datetime.utcnow().isoformat()
                }
            ]
            
            # Test individual save method
            individual_saved = await supabase._save_content_individually(
                problematic_content, profile_id, 'test_user'
            )
            print(f"   📊 Individual save: {individual_saved}/1 records")
            
            # Cleanup test data
            print("\n🧹 Cleaning up test data...")
            cleanup_success = await supabase.rollback_failed_save(profile_id, 'test_user')
            print(f"   Cleanup success: {cleanup_success}")
            
        else:
            print("   ❌ Failed to create test profile")
            
    except ImportError:
        print("❌ Supabase integration not available - cannot run tests")
        print("   Make sure you have the required environment variables set:")
        print("   - SUPABASE_URL")
        print("   - SUPABASE_SERVICE_ROLE_KEY")
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
    
    print("\n" + "=" * 50)
    print("🧪 Duplicate Handling Test Complete")

async def test_viral_processor_improvements():
    """Test the viral processor improvements"""
    print("\n🔬 Testing Viral Processor Improvements")
    print("=" * 50)
    
    try:
        from viral_ideas_processor import ViralIdeasProcessor
        
        processor = ViralIdeasProcessor()
        
        # Test schema compliance with missing profile
        print("1️⃣ Testing improved schema compliance...")
        
        await processor._verify_schema_compliance('nonexistent_user', True)
        print("   ✅ Schema compliance test completed (check logs for details)")
        
        # Test reel count functionality
        print("\n2️⃣ Testing reel count retrieval...")
        
        count = await processor._get_reel_count('test_user')
        print(f"   📊 Reel count for test_user: {count}")
        
    except Exception as e:
        print(f"❌ Viral processor test failed: {e}")
        import traceback
        traceback.print_exc()
    
    print("=" * 50)
    print("🔬 Viral Processor Test Complete")

def print_fixes_summary():
    """Print a summary of all implemented fixes"""
    print("\n📋 SUMMARY OF IMPLEMENTED FIXES")
    print("=" * 60)
    
    fixes = [
        "✅ Fixed upsert conflict resolution (shortcode vs content_id)",
        "✅ Added pre-insert duplicate detection",
        "✅ Implemented individual record save fallback",
        "✅ Enhanced data verification with warnings system", 
        "✅ Improved viral processor error handling",
        "✅ Added content count verification for existing users",
        "✅ Relaxed secondary profiles validation for viral analysis",
        "✅ Better schema compliance checking with rollback detection"
    ]
    
    for fix in fixes:
        print(f"  {fix}")
    
    print("\n📊 EXPECTED IMPROVEMENTS:")
    improvements = [
        "• Duplicate shortcode errors should be eliminated",
        "• Partial saves should be allowed with warnings instead of failures",
        "• Batch failures should not lose all data (individual fallback)",
        "• Viral analysis should continue even after profile rollbacks",
        "• Better logging and error reporting for debugging"
    ]
    
    for improvement in improvements:
        print(f"  {improvement}")
    
    print("=" * 60)

async def main():
    """Main test runner"""
    print("🚀 VIRAL PIPELINE DUPLICATE HANDLING FIXES TEST")
    print("=" * 60)
    print("Testing the fixes for the @mindset.therapy pipeline failure...")
    print()
    
    # Run tests
    await test_duplicate_handling_fixes()
    await test_viral_processor_improvements()
    
    # Print summary
    print_fixes_summary()

if __name__ == "__main__":
    asyncio.run(main())