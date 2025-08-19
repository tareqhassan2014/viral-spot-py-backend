#!/usr/bin/env python3
"""
Simple Similar Profiles API
==========================

Lightweight API for fetching and caching similar profiles with optimized loading.
Stores profile images in Supabase bucket for fast CDN delivery.
"""

import os
import asyncio
import logging
import requests
import uuid
from typing import List, Dict, Optional, Tuple
from pathlib import Path
import tempfile
from datetime import datetime, timedelta

# Import existing modules
try:
    from supabase_integration import SupabaseManager
    from network_crawler import RapidAPIClient
    import config
    SUPABASE_AVAILABLE = True
except ImportError as e:
    SUPABASE_AVAILABLE = False
    print(f"⚠️ Dependencies not available: {e}")

logger = logging.getLogger(__name__)

class SimpleSimilarProfilesAPI:
    """Lightweight API for similar profiles with fast caching"""
    
    def __init__(self):
        """Initialize with Supabase and API clients"""
        if not SUPABASE_AVAILABLE:
            raise RuntimeError("Required dependencies not available")
        
        self.supabase = SupabaseManager()
        self.api_client = RapidAPIClient()
        
        # Cache settings
        self.cache_duration_hours = 24  # Cache similar profiles for 24 hours
        self.max_similar_profiles = 80  # Support up to 80 similar profiles
        
        logger.info("✅ Simple Similar Profiles API initialized")
    
    async def get_similar_profiles(self, username: str, limit: int = 20, force_refresh: bool = False) -> Dict:
        """
        Get similar profiles for a username - returns cached or fetches new
        
        Args:
            username: Target username to find similar profiles for
            limit: Number of profiles to return (max 80)
            force_refresh: Force refresh from API even if cached
            
        Returns:
            Dict with success, data (list of profiles), and metadata
        """
        try:
            username = username.lower().replace('@', '')
            limit = min(limit, self.max_similar_profiles)
            
            logger.info(f"🔍 Getting similar profiles for @{username} (limit: {limit})")
            
            # Check cache first (unless force refresh)
            if not force_refresh:
                cached_profiles = await self._get_cached_similar_profiles(username, limit)
                if cached_profiles:
                    logger.info(f"✅ Returning {len(cached_profiles)} cached similar profiles")
                    return {
                        'success': True,
                        'data': cached_profiles,
                        'cached': True,
                        'total': len(cached_profiles),
                        'username': username
                    }
            
            # Fetch fresh data if no cache or force refresh
            logger.info(f"🚀 Fetching fresh similar profiles for @{username}")
            fresh_profiles = await self._fetch_and_cache_similar_profiles(username, limit)
            
            return {
                'success': True,
                'data': fresh_profiles,
                'cached': False,
                'total': len(fresh_profiles),
                'username': username
            }
            
        except Exception as e:
            logger.error(f"❌ Error getting similar profiles for @{username}: {e}")
            return {
                'success': False,
                'data': [],
                'error': str(e),
                'username': username
            }
    
    async def _get_cached_similar_profiles(self, username: str, limit: int) -> Optional[List[Dict]]:
        """Get similar profiles from cache if recent enough"""
        try:
            # Check for recent cached profiles
            cutoff_time = datetime.now() - timedelta(hours=self.cache_duration_hours)
            
            response = self.supabase.client.table('similar_profiles').select('''
                similar_username,
                similar_name,
                profile_image_path,
                profile_image_url,
                similarity_rank,
                image_downloaded,
                created_at
            ''').eq('primary_username', username).eq('image_downloaded', True).gte('created_at', cutoff_time.isoformat()).order('similarity_rank').limit(limit).execute()
            
            if not response.data:
                logger.info(f"📭 No recent cached similar profiles found for @{username}")
                return None
            
            # Convert to API format
            profiles = []
            for profile in response.data:
                # Get CDN URL for profile image
                profile_image_url = None
                if profile.get('profile_image_path'):
                    profile_image_url = self.supabase.client.storage.from_('profile-images').get_public_url(profile['profile_image_path'])
                elif profile.get('profile_image_url'):
                    profile_image_url = profile['profile_image_url']
                
                profiles.append({
                    'username': profile['similar_username'],
                    'name': profile.get('similar_name', profile['similar_username']),
                    'profile_image_url': profile_image_url,
                    'rank': profile.get('similarity_rank', 0)
                })
            
            logger.info(f"📋 Found {len(profiles)} cached similar profiles for @{username}")
            return profiles
            
        except Exception as e:
            logger.error(f"❌ Error getting cached similar profiles: {e}")
            return None
    
    async def _fetch_similar_profiles_with_retry(self, username: str, limit: int, max_retries: int = 2) -> List[Dict]:
        """
        Enhanced retry logic for fetching similar profiles
        
        Tries multiple strategies:
        1. Original username
        2. Username variations (if original fails)
        3. Different retry delays
        """
        original_username = username
        
        # Strategy 1: Try original username with retries
        for attempt in range(max_retries):
            try:
                if attempt > 0:
                    delay = min(5, 2 ** attempt)  # Progressive delay: 2s, 4s
                    logger.info(f"🔄 Retry attempt {attempt + 1}/{max_retries} for @{username} after {delay}s delay...")
                    await asyncio.sleep(delay)
                
                # The RapidAPIClient already has its own retry logic (2 attempts)
                logger.info(f"🎯 Attempting to fetch similar profiles for @{username} (attempt {attempt + 1})")
                similar_profiles_raw = self.api_client.get_similar_profiles(username, limit)
                
                if similar_profiles_raw and len(similar_profiles_raw) > 0:
                    logger.info(f"✅ Successfully fetched {len(similar_profiles_raw)} profiles on attempt {attempt + 1}")
                    return similar_profiles_raw
                else:
                    logger.warning(f"⚠️ Got {len(similar_profiles_raw) if similar_profiles_raw else 0} profiles on attempt {attempt + 1}")
                    
            except Exception as e:
                logger.error(f"❌ Error on attempt {attempt + 1} for @{username}: {e}")
                if attempt == max_retries - 1:
                    logger.error(f"❌ All attempts failed for @{username}")
        
        # Strategy 2: Try username variations if original failed
        username_variations = self._get_username_variations(original_username)
        for variation in username_variations:
            try:
                logger.info(f"🔄 Trying username variation: @{variation}")
                similar_profiles_raw = self.api_client.get_similar_profiles(variation, limit)
                
                if similar_profiles_raw and len(similar_profiles_raw) > 0:
                    logger.info(f"✅ Success with variation @{variation}: {len(similar_profiles_raw)} profiles")
                    return similar_profiles_raw
                    
            except Exception as e:
                logger.warning(f"⚠️ Variation @{variation} failed: {e}")
                continue
        
        logger.error(f"❌ All retry strategies failed for @{original_username}")
        return []
    
    def _get_username_variations(self, username: str) -> List[str]:
        """Generate username variations to try if original fails"""
        variations = []
        
        # Remove any existing @ symbol and clean
        clean_username = username.lower().replace('@', '').strip()
        
        # Try variations only if username has certain characteristics
        if len(clean_username) > 3:
            # Try without numbers at the end
            import re
            without_numbers = re.sub(r'\d+$', '', clean_username)
            if without_numbers != clean_username and len(without_numbers) > 2:
                variations.append(without_numbers)
            
            # Try without underscores/dots
            without_special = clean_username.replace('_', '').replace('.', '')
            if without_special != clean_username and len(without_special) > 2:
                variations.append(without_special)
        
        # Limit to 2-3 variations to avoid too many API calls
        return variations[:2]
    
    async def _fetch_and_cache_similar_profiles(self, username: str, limit: int) -> List[Dict]:
        """Fetch similar profiles from API and cache with images - with enhanced retry logic"""
        try:
            batch_id = str(uuid.uuid4())
            logger.info(f"🔄 Starting fresh fetch for @{username} (batch: {batch_id[:8]})")
            
            # Step 1: Fetch similar profiles from API with enhanced retry logic
            similar_profiles_raw = await self._fetch_similar_profiles_with_retry(username, limit)
            
            if not similar_profiles_raw:
                logger.warning(f"⚠️ No similar profiles returned from API for @{username} after all retry attempts")
                return []
            
            logger.info(f"📥 API returned {len(similar_profiles_raw)} similar profiles")
            
            # Step 2: Process each profile and download images in parallel
            processed_profiles = await self._process_similar_profiles_batch(
                username, similar_profiles_raw, batch_id
            )
            
            logger.info(f"✅ Successfully processed {len(processed_profiles)} similar profiles")
            return processed_profiles
            
        except Exception as e:
            logger.error(f"❌ Error fetching and caching similar profiles: {e}")
            return []
    
    async def _process_similar_profiles_batch(self, primary_username: str, profiles_raw: List[Dict], batch_id: str) -> List[Dict]:
        """Process a batch of similar profiles with parallel image downloading"""
        processed_profiles = []
        
        # Process profiles in smaller batches for better performance
        batch_size = 10
        for i in range(0, len(profiles_raw), batch_size):
            batch = profiles_raw[i:i + batch_size]
            
            # Process batch in parallel
            tasks = [
                self._process_single_similar_profile(primary_username, profile, i + j + 1, batch_id)
                for j, profile in enumerate(batch)
            ]
            
            batch_results = await asyncio.gather(*tasks, return_exceptions=True)
            
            # Collect successful results
            for result in batch_results:
                if isinstance(result, dict) and result.get('success'):
                    processed_profiles.append(result['data'])
        
        return processed_profiles
    
    async def _process_single_similar_profile(self, primary_username: str, profile_raw: Dict, rank: int, batch_id: str) -> Dict:
        """Process a single similar profile - download image and save to DB"""
        try:
            similar_username = profile_raw.get('username', '').replace('@', '')
            similar_name = profile_raw.get('full_name') or profile_raw.get('name') or similar_username
            profile_pic_url = profile_raw.get('profile_pic_url', '')
            
            if not similar_username:
                return {'success': False, 'error': 'No username'}
            
            logger.info(f"🔄 Processing @{similar_username} (rank {rank})")
            
            # Download and upload profile image
            profile_image_path = None
            profile_image_url = None
            image_downloaded = False
            
            if profile_pic_url:
                try:
                    # Download image to temp file
                    temp_path = await self._download_profile_image(profile_pic_url, similar_username)
                    
                    if temp_path:
                        # Upload to Supabase bucket
                        bucket_path = f"similar/{primary_username}/{similar_username}_profile.jpg"
                        profile_image_path = await self.supabase.upload_image_to_bucket(
                            temp_path, 'profile-images', bucket_path
                        )
                        
                        if profile_image_path:
                            # Get CDN URL
                            profile_image_url = self.supabase.client.storage.from_('profile-images').get_public_url(profile_image_path)
                            image_downloaded = True
                            logger.info(f"✅ Image uploaded for @{similar_username}")
                        
                        # Cleanup temp file
                        try:
                            os.unlink(temp_path)
                        except:
                            pass
                            
                except Exception as e:
                    logger.warning(f"⚠️ Failed to download image for @{similar_username}: {e}")
            
            # Save to database
            db_record = {
                'primary_username': primary_username,
                'similar_username': similar_username,
                'similar_name': similar_name,
                'profile_image_path': profile_image_path,
                'profile_image_url': profile_image_url,
                'similarity_rank': rank,
                'batch_id': batch_id,
                'image_downloaded': image_downloaded,
                'fetch_failed': not image_downloaded and bool(profile_pic_url)
            }
            
            # Upsert to database
            self.supabase.client.table('similar_profiles').upsert(
                db_record, on_conflict='primary_username,similar_username'
            ).execute()
            
            # Return formatted response
            return {
                'success': True,
                'data': {
                    'username': similar_username,
                    'name': similar_name,
                    'profile_image_url': profile_image_url,
                    'rank': rank
                }
            }
            
        except Exception as e:
            logger.error(f"❌ Error processing @{similar_username}: {e}")
            return {'success': False, 'error': str(e)}
    
    async def _download_profile_image(self, image_url: str, username: str) -> Optional[str]:
        """Download profile image to temporary file"""
        try:
            # Create temp file
            temp_dir = tempfile.gettempdir()
            temp_filename = f"profile_{username}_{uuid.uuid4().hex[:8]}.jpg"
            temp_path = os.path.join(temp_dir, temp_filename)
            
            # Download image
            response = requests.get(image_url, timeout=30, stream=True)
            response.raise_for_status()
            
            with open(temp_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)
            
            return temp_path
            
        except Exception as e:
            logger.error(f"❌ Failed to download image from {image_url}: {e}")
            return None
    
    async def add_manual_profile(self, primary_username: str, target_username: str) -> Dict:
        """Add a specific profile manually to similar profiles"""
        try:
            primary_username = primary_username.lower().replace('@', '')
            target_username = target_username.lower().replace('@', '')
            
            logger.info(f"📝 Adding manual profile @{target_username} for @{primary_username}")
            
            # Check if profile already exists
            existing = self.supabase.client.table('similar_profiles').select('*').eq('primary_username', primary_username).eq('similar_username', target_username).execute()
            
            if existing.data:
                profile = existing.data[0]
                return {
                    'success': True,
                    'data': {
                        'username': profile['similar_username'],
                        'name': profile['similar_name'],
                        'profile_image_url': profile['profile_image_url'],
                        'rank': profile['similarity_rank']
                    },
                    'message': 'Profile already exists',
                    'cached': True
                }
            
            # Fetch profile data from Instagram API  
            logger.info(f"🔍 Fetching profile data for @{target_username} using Instagram API")
            profile_data = await self._fetch_basic_profile_data(target_username)
            
            if not profile_data:
                logger.warning(f"⚠️ Instagram API couldn't fetch @{target_username}, trying fallback method")
                
                # Fallback: Create a minimal profile entry so user can still add the competitor
                profile_data = {
                    'username': target_username,
                    'full_name': target_username.replace('_', ' ').replace('.', ' ').title(),
                    'profile_pic_url': None  # No image available
                }
                
                logger.info(f"🔄 Using fallback profile data for @{target_username}")
            
            logger.info(f"✅ Profile data fetched successfully for @{target_username}: {profile_data.get('full_name', 'Unknown')}")
            
            # Generate unique batch ID for manual addition
            batch_id = str(uuid.uuid4())
            
            # Process the profile (download image, etc.)
            logger.info(f"🔄 Processing profile for storage: @{target_username}")
            result = await self._process_single_similar_profile(
                primary_username, profile_data, 999, batch_id  # Use high rank for manual additions
            )
            
            logger.info(f"📊 Profile processing result for @{target_username}: {result.get('success', False)}")
            
            if result.get('success'):
                logger.info(f"✅ Manual profile @{target_username} successfully added and stored")
                return {
                    'success': True,
                    'data': result['data'],
                    'message': f'Successfully added @{target_username}',
                    'cached': False
                }
            else:
                error_msg = result.get('error', 'Failed to process profile')
                logger.error(f"❌ Failed to process profile @{target_username}: {error_msg}")
                return {
                    'success': False,
                    'error': error_msg
                }
                
        except Exception as e:
            logger.error(f"❌ Error adding manual profile @{target_username}: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    async def _fetch_basic_profile_data(self, username: str) -> Optional[Dict]:
        """Fetch basic profile data from Instagram API using the same method as PrimaryProfileFetch"""
        try:
            # Get API credentials from environment
            rapidapi_key = os.getenv('RAPIDAPI_KEY') or os.getenv('INSTAGRAM_SCRAPER_API_KEY')
            api_host = os.getenv('INSTAGRAM_SCRAPER_API_HOST', 'instagram-scraper-stable-api.p.rapidapi.com')
            
            if not rapidapi_key:
                logger.error("❌ No RapidAPI key available for profile fetching")
                return None
            
            # Use the same API endpoint and method as PrimaryProfileFetch
            url = f"https://{api_host}/ig_get_fb_profile.php"
            payload = f"username_or_url={username}"
            
            headers = {
                'x-rapidapi-key': rapidapi_key,
                'x-rapidapi-host': api_host,
                'Content-Type': "application/x-www-form-urlencoded"
            }
            
            logger.info(f"🔍 Fetching profile data for @{username} from Instagram API")
            
            response = requests.post(url, data=payload, headers=headers, timeout=30)
            
            if response.status_code == 200:
                profile_data = response.json()
                
                # Extract the relevant profile information
                if profile_data and 'username' in profile_data:
                    result = {
                        'username': profile_data.get('username', username),
                        'full_name': profile_data.get('full_name') or profile_data.get('profile_name') or username,
                        'profile_pic_url': profile_data.get('profile_pic_url'),
                    }
                    
                    logger.info(f"✅ Successfully fetched profile data for @{username}")
                    return result
                else:
                    logger.warning(f"⚠️ Profile data for @{username} is incomplete or invalid")
                    return None
            else:
                logger.warning(f"❌ Profile fetch failed for @{username}: HTTP {response.status_code}")
                logger.debug(f"Response: {response.text}")
                return None
                
        except requests.exceptions.Timeout:
            logger.error(f"⏰ Timeout fetching profile data for @{username}")
            return None
        except requests.exceptions.RequestException as e:
            logger.error(f"🌐 Network error fetching profile data for @{username}: {e}")
            return None
        except Exception as e:
            logger.error(f"❌ Error fetching basic profile data for @{username}: {e}")
            return None

    async def clear_cache_for_profile(self, username: str) -> Dict:
        """Clear cached similar profiles for a username"""
        try:
            username = username.lower().replace('@', '')
            
            # Delete from database
            self.supabase.client.table('similar_profiles').delete().eq('primary_username', username).execute()
            
            # Note: We're not deleting images from storage bucket here
            # as they might be expensive to re-download. Images will be overwritten on next fetch.
            
            logger.info(f"🗑️ Cleared similar profiles cache for @{username}")
            
            return {
                'success': True,
                'message': f'Cache cleared for @{username}'
            }
            
        except Exception as e:
            logger.error(f"❌ Error clearing cache for @{username}: {e}")
            return {
                'success': False,
                'error': str(e)
            }

# Global instance
simple_similar_api = None

def get_similar_api():
    """Get or create global API instance"""
    global simple_similar_api
    if simple_similar_api is None:
        simple_similar_api = SimpleSimilarProfilesAPI()
    return simple_similar_api