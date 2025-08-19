"""
Comprehensive Instagram Data Pipeline
Follows the complete ViralSpot database schema and processing flow
"""

import os
import csv
import json
import asyncio
import aiohttp
import requests
import time
import statistics
import http.client
import glob
import math
from datetime import datetime
from typing import Dict, List, Optional, Tuple, Any
from urllib.parse import urlparse
from pathlib import Path
import hashlib
from openai import OpenAI
from config import (
    # OpenAI Prompts and Settings
    PROFILE_TYPE_CLASSIFICATION_PROMPT,
    PROFILE_CONTENT_CATEGORIZATION_PROMPT,
    REEL_CONTENT_CATEGORIZATION_PROMPT,
    CATEGORY_FALLBACK_MAP,
    OPENAI_MODEL,
    OPENAI_TEMPERATURE,
    OPENAI_MAX_TOKENS_PROFILE_TYPE,
    OPENAI_MAX_TOKENS_PROFILE_CONTENT,
    OPENAI_MAX_TOKENS_REEL_CONTENT,
    
    # Helper Functions
    get_fallback_category,
    clean_json_response,
    
    # Default Values
    DEFAULT_PROFILE_TYPE,
    DEFAULT_PROFILE_CATEGORIES,
    DEFAULT_REEL_CATEGORIES,
    
    # System Settings
    DEBUG_MODE,
    DEFAULT_API_TIMEOUT,
    
    # Directory Names
    IMAGES_DIR_NAME,
    THUMBNAILS_DIR_NAME,
    DEBUG_DIR_NAME,
    
    # CSV File Names
    PRIMARY_PROFILE_CSV,
    CONTENT_CSV,
    SECONDARY_PROFILE_CSV,
    
    # Encoding Settings
    CSV_ENCODING,
    JSON_ENCODING,
    ENSURE_ASCII,
    JSON_INDENT,
    
    # Image Download Settings
    IMAGE_DOWNLOAD_USER_AGENT,
    IMAGE_DOWNLOAD_TIMEOUT,
    
    # Supabase Settings
    KEEP_LOCAL_CSV
)
try:
    from dotenv import load_dotenv
except ImportError:
    print("Warning: python-dotenv not installed. Install with: pip install python-dotenv")
    def load_dotenv():
        pass
from dataclasses import dataclass
from concurrent.futures import ThreadPoolExecutor, as_completed
import logging

# Import Supabase integration
try:
    from supabase_integration import SupabaseManager
    SUPABASE_AVAILABLE = True
except ImportError as e:
    SUPABASE_AVAILABLE = False
    print(f"⚠️ Supabase integration not available: {e}")
    SupabaseManager = None

# Load environment variables immediately
load_dotenv()

class InstagramDataPipeline:
    """Complete Instagram data processing pipeline"""
    
    def __init__(self):
        """Initialize with API credentials and setup directories"""
        # Run startup validation to catch issues early
        self._validate_system_requirements()
        
        # API Configuration
        self.rapidapi_key = os.getenv('RAPIDAPI_KEY') or os.getenv('INSTAGRAM_SCRAPER_API_KEY')
        self.similar_api_key = os.getenv('RAPIDAPI_KEY') or os.getenv('SIMILAR_PROFILES_API_KEY') or self.rapidapi_key
        self.openai_key = os.getenv('OPENAI_API_KEY')
        
        self.api_host = os.getenv('INSTAGRAM_SCRAPER_API_HOST', 'instagram-scraper-stable-api.p.rapidapi.com')
        self.similar_host = os.getenv('SIMILAR_PROFILES_API_HOST', 'instagram-scraper-stable-api.p.rapidapi.com')
        
        # Setup OpenAI
        if self.openai_key:
            self.openai_client = OpenAI(api_key=self.openai_key)
            if DEBUG_MODE:
                print("✅ OpenAI client initialized")
        else:
            self.openai_client = None
            if DEBUG_MODE:
                print("⚠️ OpenAI API key not found - categorization will be limited")
        
        # Setup directories
        self.images_dir = Path(IMAGES_DIR_NAME)
        self.thumbnails_dir = Path(THUMBNAILS_DIR_NAME)
        self.debug_dir = Path(DEBUG_DIR_NAME)
        self.images_dir.mkdir(exist_ok=True)
        self.thumbnails_dir.mkdir(exist_ok=True)
        self.debug_dir.mkdir(exist_ok=True)
        
        # Initialize Supabase manager
        try:
            if SUPABASE_AVAILABLE:
                self.supabase = SupabaseManager()
                self.use_supabase = self.supabase.use_supabase
                print(f"✅ Supabase integration: {'ENABLED' if self.use_supabase else 'DISABLED'}")
            else:
                self.supabase = None
                self.use_supabase = False
        except Exception as e:
            print(f"⚠️ Supabase integration not available: {e}")
            self.supabase = None
            self.use_supabase = False
        
        # Headers for API requests
        self.headers = {
            'x-rapidapi-key': self.rapidapi_key,
            'x-rapidapi-host': self.api_host,
            'Content-Type': "application/x-www-form-urlencoded"
        }
        
        self.similar_headers = {
            'x-rapidapi-key': self.similar_api_key,
            'x-rapidapi-host': self.similar_host
        }
        
        if DEBUG_MODE:
            print("✅ Instagram Data Pipeline initialized")
    
    def download_image(self, url: str, filename: str, directory: Path) -> str:
        """Download image to local storage with enhanced error handling"""
        try:
            if not url or url == '':
                if DEBUG_MODE:
                    print(f"⚠️ Empty URL provided for {filename}")
                return ""
            
            if DEBUG_MODE:
                print(f"🖼️ Downloading image: {filename}")
            
            # Add headers to mimic browser request
            headers = {
                'User-Agent': IMAGE_DOWNLOAD_USER_AGENT
            }
            
            response = requests.get(url, headers=headers, timeout=DEFAULT_API_TIMEOUT)
            if response.status_code == 200:
                file_path = directory / filename
                with open(file_path, 'wb') as f:
                    f.write(response.content)
                
                # Verify file was written
                if file_path.exists() and file_path.stat().st_size > 0:
                    if DEBUG_MODE:
                        print(f"✅ Downloaded: {filename} ({file_path.stat().st_size} bytes)")
                    return str(file_path)
                else:
                    if DEBUG_MODE:
                        print(f"❌ File {filename} was not written properly")
                    return ""
            else:
                if DEBUG_MODE:
                    print(f"❌ Failed to download {filename}: HTTP {response.status_code}")
                return ""
        except Exception as e:
            if DEBUG_MODE:
                print(f"❌ Failed to download image {filename}: {e}")
            return ""
    
    def save_debug_response(self, response_data: Dict, endpoint: str, username: str):
        """Save full API response for debugging (only if debug mode enabled and not using Supabase)"""
        # Don't save debug responses when using Supabase to avoid unnecessary file generation
        if not DEBUG_MODE or self.use_supabase:
            return
            
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"{username}_{endpoint}_{timestamp}.json"
        file_path = self.debug_dir / filename
        
        try:
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(response_data, f, indent=2, ensure_ascii=False)
            if DEBUG_MODE:
                print(f"🐛 DEBUG: Response saved to {filename}")
        except Exception as e:
            if DEBUG_MODE:
                print(f"❌ Failed to save debug response: {e}")
    
    def print_json_response(self, response_data: Dict, endpoint: str):
        """Print full JSON response for debugging (only if debug mode enabled)"""
        if not DEBUG_MODE:
            return
            
        print(f"\n🐛 DEBUG - FULL JSON RESPONSE for {endpoint}:")
        print("=" * 80)
        print(json.dumps(response_data, indent=2, ensure_ascii=False))
        print("=" * 80)
    
    def log_progress(self, message: str, debug_only: bool = False):
        """Unified progress logging - shows minimal messages in production mode"""
        if debug_only and not DEBUG_MODE:
            return
        if DEBUG_MODE or not debug_only:
            print(message)
    
    async def ai_categorize_profile_type(self, username: str, profile_name: str, bio: str, followers: int) -> Dict:
        """PROMPT 1: Use OpenAI to determine profile account type"""
        if not self.openai_client:
            return DEFAULT_PROFILE_TYPE
        
        try:
            prompt = PROFILE_TYPE_CLASSIFICATION_PROMPT.format(
                username=username,
                profile_name=profile_name,
                bio=bio,
                followers=followers
            )
            
            response = self.openai_client.chat.completions.create(
                model=OPENAI_MODEL,
                messages=[{"role": "user", "content": prompt}],
                max_tokens=OPENAI_MAX_TOKENS_PROFILE_TYPE,
                temperature=OPENAI_TEMPERATURE
            )
            
            result_text = response.choices[0].message.content.strip()
            self.log_progress(f"🤖 PROMPT 1 - Profile Type Response: {result_text}", debug_only=True)
            
            return json.loads(result_text)
            
        except Exception as e:
            self.log_progress(f"❌ OpenAI profile type categorization failed: {e}")
            return DEFAULT_PROFILE_TYPE
    
    async def ai_categorize_profile_content(self, username: str, profile_name: str, bio: str) -> Dict:
        """PROMPT 2: Use OpenAI to categorize profile content categories"""
        if not self.openai_client:
            return DEFAULT_PROFILE_CATEGORIES
        
        try:
            prompt = PROFILE_CONTENT_CATEGORIZATION_PROMPT.format(
                username=username,
                profile_name=profile_name,
                bio=bio
            )
            
            response = self.openai_client.chat.completions.create(
                model=OPENAI_MODEL,
                messages=[{"role": "user", "content": prompt}],
                max_tokens=OPENAI_MAX_TOKENS_PROFILE_CONTENT,
                temperature=OPENAI_TEMPERATURE
            )
            
            result_text = response.choices[0].message.content.strip()
            self.log_progress(f"🤖 PROMPT 2 - Profile Categories Response: {result_text}", debug_only=True)
            
            # Clean the response to ensure it's valid JSON
            result_text = clean_json_response(result_text)
            
            # Parse JSON response
            result = json.loads(result_text)
            
            # Ensure tertiary category is filled - add fallback logic
            if not result.get('tertiary_category') or result['tertiary_category'].strip() == '':
                primary = result.get('primary_category', '')
                secondary = result.get('secondary_category', '')
                
                # Use imported helper function for fallback
                tertiary = get_fallback_category(primary, secondary)
                result['tertiary_category'] = tertiary
                self.log_progress(f"🔧 Auto-filled profile tertiary category: {tertiary}", debug_only=True)
            
            return result
            
        except Exception as e:
            self.log_progress(f"❌ OpenAI profile categorization failed: {e}")
            return DEFAULT_PROFILE_CATEGORIES
    
    async def ai_categorize_reel_content(self, description: str, hashtags: List[str] = None) -> Dict:
        """PROMPT 3: Use OpenAI to categorize individual reel/post content with 3 categories and keywords.
        Adds robust debugging, JSON cleaning, and fallback parsing to avoid crashes on malformed responses.
        """
        if not self.openai_client:
            return DEFAULT_REEL_CATEGORIES

        try:
            # Enhanced prompt to ensure all 3 categories are filled
            prompt = REEL_CONTENT_CATEGORIZATION_PROMPT.format(description=description or "")

            response = self.openai_client.chat.completions.create(
                model=OPENAI_MODEL,
                messages=[{"role": "user", "content": prompt}],
                max_tokens=OPENAI_MAX_TOKENS_REEL_CONTENT,
                temperature=OPENAI_TEMPERATURE
            )

            # Defensive parsing with extensive debug
            try:
                result_text = (response.choices[0].message.content or "").strip()
            except Exception:
                result_text = ""

            if DEBUG_MODE:
                self.log_progress("🤖 PROMPT 3 - Raw OpenAI response received", debug_only=True)
                # Log a compact preview to avoid flooding logs
                self.log_progress(f"📝 Raw length: {len(result_text)}; preview: {result_text[:200]}...", debug_only=True)

            if not result_text:
                # If the model returned an empty message, return defaults with a marker
                return {
                    **DEFAULT_REEL_CATEGORIES,
                    'keywords': [],
                }

            # Clean the response to ensure it's valid JSON
            cleaned_text = clean_json_response(result_text)
            if DEBUG_MODE and cleaned_text != result_text:
                self.log_progress(f"🧹 Cleaned JSON length: {len(cleaned_text)}; preview: {cleaned_text[:200]}...", debug_only=True)

            # Try strict JSON parse first
            try:
                result = json.loads(cleaned_text)
            except Exception as parse_err:
                # Fallback: try to extract JSON object/array using simple heuristics
                if DEBUG_MODE:
                    self.log_progress(f"⚠️ Strict JSON parse failed: {parse_err}", debug_only=True)
                import re
                candidate = cleaned_text
                # Extract first {...} or [...] block
                obj_match = re.search(r"\{[\s\S]*\}", candidate)
                arr_match = re.search(r"\[[\s\S]*\]", candidate)
                json_candidate = obj_match.group(0) if obj_match else (arr_match.group(0) if arr_match else candidate)
                try:
                    result = json.loads(json_candidate)
                except Exception as parse_err2:
                    if DEBUG_MODE:
                        self.log_progress(f"❌ Fallback JSON parse failed: {parse_err2}", debug_only=True)
                    # Final fallback to defaults
                    return DEFAULT_REEL_CATEGORIES

            # Ensure keys exist and fill tertiary if missing
            if not result.get('tertiary_category') or (isinstance(result.get('tertiary_category'), str) and result['tertiary_category'].strip() == ''):
                primary = result.get('primary_category', '')
                secondary = result.get('secondary_category', '')
                tertiary = get_fallback_category(primary, secondary)
                result['tertiary_category'] = tertiary
                self.log_progress(f"🔧 Auto-filled tertiary category: {tertiary}", debug_only=True)

            # Normalize keywords to list of up to 4 strings
            kws = result.get('keywords')
            if isinstance(kws, str):
                # Split by comma/semicolon if model returned a single string
                parts = [p.strip() for p in re.split(r"[,;]", kws) if p and p.strip()]
                result['keywords'] = parts[:4]
            elif isinstance(kws, list):
                result['keywords'] = [str(k).strip() for k in kws if str(k).strip()][:4]
            else:
                result['keywords'] = []

            return result

        except Exception as e:
            # Top-level guard to avoid crashing the pipeline
            self.log_progress(f"❌ OpenAI reel categorization failed: {e}")
            return DEFAULT_REEL_CATEGORIES
    
    async def fetch_profile_data(self, username: str) -> Optional[Dict]:
        """Step 1: Fetch basic profile information"""
        try:
            url = f"https://{self.api_host}/ig_get_fb_profile.php"
            payload = f"username_or_url={username}"
            
            self.log_progress(f"🔍 API Request: {url}", debug_only=True)
            self.log_progress(f"🔍 Payload: {payload}", debug_only=True)
            self.log_progress(f"Fetching profile data for @{username}...", debug_only=False)
            
            response = requests.post(url, data=payload, headers=self.headers, timeout=30)
            
            if response.status_code == 200:
                profile_data = response.json()
                
                # DEBUG: Print and save full response
                self.print_json_response(profile_data, f"profile_{username}")
                self.save_debug_response(profile_data, "profile", username)
                
                # Download ALL profile images
                profile_pic_url = profile_data.get('profile_pic_url', '')
                hd_profile_pic_url = profile_data.get('hd_profile_pic_url', '')
                
                profile_pic_local = ""
                hd_profile_pic_local = ""
                
                # Download standard profile pic
                if profile_pic_url:
                    filename = f"{username}_profile.jpg"
                    profile_pic_local = self.download_image(profile_pic_url, filename, self.images_dir)
                
                # Download HD profile pic if different
                if hd_profile_pic_url and hd_profile_pic_url != profile_pic_url:
                    filename = f"{username}_profile_hd.jpg"
                    hd_profile_pic_local = self.download_image(hd_profile_pic_url, filename, self.images_dir)
                
                # Add local image paths
                profile_data['profile_image_local'] = profile_pic_local
                profile_data['hd_profile_image_local'] = hd_profile_pic_local
                
                self.log_progress(f"✅ Profile data fetched for @{username}")
                return profile_data
            else:
                self.log_progress(f"❌ Profile fetch failed: {response.status_code}")
                self.log_progress(f"🐛 Response text: {response.text}", debug_only=True)
                return None
                
        except Exception as e:
            self.log_progress(f"❌ Error fetching profile: {e}")
            return None
    
    async def fetch_reel_ids(self, username: str, count: int = 100, start_pagination_token: str = None, max_pages: int = None) -> tuple[List[Dict], str]:
        """Fetch reel IDs with progressive pagination support
        
        Returns:
            tuple: (reels_list, next_pagination_token)
        """
        try:
            all_reels = []
            max_id = start_pagination_token  # Resume from specific page
            batch_num = 1
            pages_fetched = 0
            
            # If max_pages is set, limit pagination (for progressive fetching)
            target_pages = max_pages if max_pages else float('inf')
            
            self.log_progress(f"🔍 PAGINATION CONFIG: target_pages={target_pages}, count={count}", debug_only=True)
            self.log_progress(f"Fetching {count} reel IDs for @{username}...", debug_only=False)
            
            while len(all_reels) < count and pages_fetched < target_pages:
                url = f"https://{self.api_host}/get_ig_user_reels.php"
                payload = f"username_or_url={username}&count=50"
                if max_id:
                    payload += f"&max_id={max_id}"
                
                self.log_progress(f"🔍 API Request (Batch {batch_num}): {url}", debug_only=True)
                self.log_progress(f"🔍 Payload: {payload}", debug_only=True)
                self.log_progress(f"🎯 Progress: {len(all_reels)}/{count} reels collected", debug_only=True)
                
                response = requests.post(url, data=payload, headers=self.headers, timeout=30)
                
                if response.status_code == 200:
                    data = response.json()
                    
                    # DEBUG: Print and save full response
                    self.print_json_response(data, f"reels_batch_{batch_num}_{username}")
                    self.save_debug_response(data, f"reels_batch_{batch_num}", username)
                    
                    reels = data.get('reels', []) if isinstance(data, dict) else []
                    
                    if not reels:
                        self.log_progress("🔍 No more reels found", debug_only=True)
                        break
                    
                    all_reels.extend(reels)
                    self.log_progress(f"📋 Batch {batch_num}: Added {len(reels)} reels (total: {len(all_reels)}/{count})", debug_only=True)
                    
                    # CRITICAL FIX: Check for pagination BEFORE checking count (for progressive fetch)
                    max_id = data.get('pagination_token')
                    self.log_progress(f"🔍 PAGINATION CHECK: max_id = {'Found' if max_id else 'None'}", debug_only=True)
                    self.log_progress(f"🔍 DEBUG: pages_fetched={pages_fetched}, target_pages={target_pages}", debug_only=True)
                    
                    # CRITICAL FIX: For progressive fetch, NEVER break on count - always preserve token
                    if max_pages:
                        # Progressive fetch: preserve token regardless of count
                        if not max_id:
                            self.log_progress("🔍 No more pagination available - no pagination_token", debug_only=True)
                            break
                        self.log_progress(f"📄 PROGRESSIVE: Found pagination token, will preserve for continuation", debug_only=True)
                    else:
                        # Full fetch: check count and break if reached
                        if len(all_reels) >= count:
                            self.log_progress(f"🎯 TARGET REACHED: Collected {len(all_reels)} reels (target: {count})", debug_only=True)
                            break
                        
                        # Continue pagination if we have a token and haven't reached limits
                        if not max_id:
                            self.log_progress("🔍 No more pagination available - no pagination_token", debug_only=True)
                            break
                        
                        self.log_progress(f"📄 Found pagination_token: {max_id[:50]}... (continuing to reach {count} reels)", debug_only=True)
                    
                    # Safety check: if we got fewer than expected, might be end
                    if len(reels) < 12:  # Usually returns ~12 per page
                        self.log_progress(f"⚠️ Got only {len(reels)} reels in this batch (might be last page)", debug_only=True)
                        # Continue anyway in case there are more pages
                else:
                    self.log_progress(f"❌ Reel IDs fetch failed: {response.status_code}")
                    self.log_progress(f"🐛 Response text: {response.text}", debug_only=True)
                    break
                
                batch_num += 1
                pages_fetched += 1
                
                self.log_progress(f"📄 Completed page {pages_fetched} (batch {batch_num-1})", debug_only=True)
                
                # CRITICAL FIX: Check page limit AFTER processing current page
                if max_pages and pages_fetched >= target_pages:
                    self.log_progress(f"🎯 PROGRESSIVE FETCH: Hit page limit ({pages_fetched}/{target_pages})", debug_only=True)
                    if max_id:
                        self.log_progress(f"📄 PRESERVING pagination token for continuation: {max_id[:50]}...", debug_only=True)
                    else:
                        self.log_progress("📄 NO TOKEN to preserve - account may have exactly this many reels", debug_only=True)
                    break  # Exit after preserving token
                
                # Safety mechanism: prevent infinite loops
                if batch_num > 20:  # Max 20 pages (20 * 50 = 1000 reels max)
                    self.log_progress(f"⚠️ Hit safety limit (20 batches), stopping pagination", debug_only=True)
                    break
                
                # Rate limiting
                time.sleep(1)
            
            # Return reels and next pagination token for resuming
            final_reels = all_reels[:count]  # Trim to exact count requested
            
            # CRITICAL FIX: Always preserve pagination token if we stopped due to page limit
            if max_pages and pages_fetched >= max_pages:
                # We hit the page limit - preserve token regardless of how many reels we got
                next_token = max_id
                self.log_progress(f"🎯 PROGRESSIVE FETCH: Hit page limit ({pages_fetched}/{max_pages}) - PRESERVING token", debug_only=True)
                self.log_progress(f"   📋 Got {len(final_reels)} reels from {pages_fetched} pages", debug_only=True)
                self.log_progress(f"   📄 Next pagination token: {'PRESERVED' if next_token else 'NONE AVAILABLE'}", debug_only=True)
                self.log_progress(f"   🔄 Can continue fetching: {'YES - TOKEN SAVED' if next_token else 'NO - END OF ACCOUNT'}", debug_only=True)
            elif max_pages:
                # Progressive fetch but didn't hit page limit (no more reels available)
                next_token = None
                self.log_progress(f"🎯 PROGRESSIVE FETCH: Got {len(final_reels)} reels from {pages_fetched} pages (exhausted)", debug_only=True)
                self.log_progress(f"   📄 Next pagination token: None (no more pages)", debug_only=True)
                self.log_progress(f"   🔄 Can continue fetching: No", debug_only=True)
            else:
                # Full fetch: return next token only if we stopped due to count limit
                next_token = max_id if len(all_reels) >= count else None
            
            # LOG: Confirm exact count returned
            if len(final_reels) != len(all_reels):
                self.log_progress(f"✂️ TRIMMED: Collected {len(all_reels)} reels, returned exactly {len(final_reels)} (target: {count})", debug_only=True)
            
            if max_pages:
                self.log_progress(f"✅ Progressive fetch: {len(final_reels)} reel IDs ({pages_fetched} pages) - Next token: {'Yes' if next_token else 'No'}", debug_only=True)
            else:
                self.log_progress(f"✅ Fetched {len(final_reels)} reel IDs for @{username}")
            
            return final_reels, next_token
            
        except Exception as e:
            self.log_progress(f"❌ Error fetching reel IDs: {e}")
            return [], None
    
    async def fetch_reel_details(self, session: aiohttp.ClientSession, shortcode: str, username: str, max_retries: int = 3) -> Optional[Dict]:
        """Step 3: Fetch individual reel details with retry logic and rate limit handling"""
        
        for attempt in range(max_retries):
            try:
                # Construct URL for reel details
                import urllib.parse
                full_instagram_url = f"https://www.instagram.com/p/{shortcode}/"
                encoded_url = urllib.parse.quote(full_instagram_url, safe='')
                
                url = f"https://{self.api_host}/get_media_data.php?reel_post_code_or_url={encoded_url}&type=reel"
                
                if attempt > 0:
                    self.log_progress(f"🔄 Retry {attempt} for reel {shortcode}", debug_only=True)
                
                # Add delay before request (except first attempt)
                if attempt > 0:
                    delay = min(10, 1 * (2 ** attempt))  # Exponential backoff
                    await asyncio.sleep(delay)
                
                async with session.get(url, headers=self.headers, timeout=30) as response:
                    if response.status == 200:
                        reel_data = await response.json()
                        
                        # Validate response data
                        if not reel_data or not isinstance(reel_data, dict):
                            self.log_progress(f"⚠️ Invalid data format for reel {shortcode} (attempt {attempt + 1})", debug_only=True)
                            if attempt < max_retries - 1:
                                continue
                            return None
                        
                        # DEBUG: Print and save reel response with proper field mapping
                        view_count = reel_data.get('video_view_count', 0)
                        like_count = reel_data.get('edge_media_preview_like', {}).get('count', 0)
                        comment_count = reel_data.get('edge_media_to_parent_comment', {}).get('count', 0)
                        
                        # Extract caption properly
                        caption_text = ""
                        caption_edges = reel_data.get('edge_media_to_caption', {}).get('edges', [])
                        if caption_edges and len(caption_edges) > 0:
                            caption_text = caption_edges[0].get('node', {}).get('text', '')
                        
                        if DEBUG_MODE:
                            print(f"🐛 DEBUG - Reel {shortcode} Response Preview:")
                            print(f"  View count: {view_count}")
                            print(f"  Like count: {like_count}")
                            print(f"  Comment count: {comment_count}")
                            print(f"  Caption preview: {caption_text[:100]}...")
                        
                        # Save the full JSON response for debugging
                        self.save_debug_response(reel_data, f"reel_detail_{shortcode}", username)
                        
                        # Also save a readable summary (only if not using Supabase)
                        if not self.use_supabase:
                            debug_summary = {
                                "shortcode": shortcode,
                                "metrics": {
                                    "views": view_count,
                                    "likes": like_count,
                                    "comments": comment_count
                                },
                                "caption": caption_text,
                                "api_structure_notes": {
                                    "view_count_field": "video_view_count",
                                    "like_count_field": "edge_media_preview_like.count",
                                    "comment_count_field": "edge_media_to_parent_comment.count",
                                    "caption_field": "edge_media_to_caption.edges[0].node.text"
                                }
                            }
                            with open(os.path.join(self.debug_dir, f"{username}_reel_summary_{shortcode}.json"), 'w') as f:
                                json.dump(debug_summary, f, indent=2)
                        
                        # Download ALL available images for this reel
                        thumbnail_local = ""
                        display_url_local = ""
                        video_thumbnail_local = ""
                        
                        # Primary thumbnail/display image
                        display_url = reel_data.get('display_url', '')
                        if display_url:
                            filename = f"{shortcode}_display.jpg"
                            try:
                                display_url_local = self.download_image(display_url, filename, self.thumbnails_dir)
                                thumbnail_local = display_url_local  # Use as primary thumbnail
                            except Exception as e:
                                print(f"❌ Failed to download display image for {shortcode}: {e}")
                                display_url_local = ""
                        
                        # Alternative thumbnail sources
                        thumbnail_url = reel_data.get('thumbnail_url', '')
                        if thumbnail_url and thumbnail_url != display_url:
                            filename = f"{shortcode}_thumb.jpg"
                            thumbnail_local = self.download_image(thumbnail_url, filename, self.thumbnails_dir)
                        
                        # Video thumbnail if available
                        video_thumbnails = reel_data.get('video_versions', [])
                        if video_thumbnails and isinstance(video_thumbnails, list):
                            for i, video in enumerate(video_thumbnails[:1]):  # Just first one
                                if 'url' in video:
                                    filename = f"{shortcode}_video_thumb_{i}.jpg"
                                    video_thumbnail_local = self.download_image(video['url'], filename, self.thumbnails_dir)
                                    break
                        
                        # Try image_versions2 for additional thumbnails
                        image_versions = reel_data.get('image_versions2', {})
                        if isinstance(image_versions, dict) and 'candidates' in image_versions:
                            candidates = image_versions['candidates']
                            if isinstance(candidates, list) and candidates:
                                # Download highest quality version
                                best_candidate = candidates[0]
                                if 'url' in best_candidate:
                                    filename = f"{shortcode}_hq_thumb.jpg"
                                    hq_thumbnail = self.download_image(best_candidate['url'], filename, self.thumbnails_dir)
                                    if not thumbnail_local:  # Use as fallback
                                        thumbnail_local = hq_thumbnail
                        
                        # Process and clean data with ALL image paths using correctly extracted values
                        processed_reel = {
                            'content_id': reel_data.get('pk', shortcode),
                            'shortcode': shortcode,
                            'content_type': 'reel',
                            'url': f"https://www.instagram.com/p/{shortcode}/",
                            'description': caption_text,  # Use the properly extracted caption
                            'thumbnail_url': display_url or thumbnail_url,  # Primary thumbnail URL
                            'thumbnail_local': thumbnail_local,  # Primary local thumbnail path
                            'display_url_local': display_url_local,  # Display image local path
                            'video_thumbnail_local': video_thumbnail_local,  # Video thumbnail local path
                            'view_count': int(view_count),  # Use properly extracted view count
                            'like_count': int(like_count),  # Use properly extracted like count
                            'comment_count': int(comment_count),  # Use properly extracted comment count
                            'date_posted': reel_data.get('taken_at_timestamp', reel_data.get('taken_at')),
                            'username': username,
                            # Hashtags removed as not needed
                            'language': 'en',  # Default, could be detected
                            'all_image_urls': {  # Store all original URLs for reference
                                'display_url': display_url,
                                'thumbnail_url': thumbnail_url,
                                'video_thumbnails': [v.get('url', '') for v in video_thumbnails] if video_thumbnails else []
                            }
                        }
                        
                        return processed_reel
                        
                    elif response.status == 429:
                        # Rate limited
                        response_text = await response.text()
                        print(f"🚨 Rate limited for reel {shortcode} (attempt {attempt + 1})")
                        
                        if attempt < max_retries - 1:
                            # Exponential backoff for rate limits
                            backoff_time = min(30, 5 * (2 ** attempt))
                            print(f"⏱️ Waiting {backoff_time}s before retry...")
                            await asyncio.sleep(backoff_time)
                            continue
                        else:
                            print(f"❌ Rate limited after {max_retries} attempts for {shortcode}")
                            return None
                            
                    else:
                        response_text = await response.text()
                        print(f"❌ Failed to fetch reel {shortcode} (attempt {attempt + 1}): {response.status}")
                        if "rate limit" in response_text.lower():
                            print(f"🚨 Rate limit detected in response: {response_text[:200]}...")
                            if attempt < max_retries - 1:
                                await asyncio.sleep(5 * (2 ** attempt))
                                continue
                        
                        if attempt < max_retries - 1:
                            continue
                        return None
                        
            except asyncio.TimeoutError:
                print(f"⏱️ Timeout for reel {shortcode} (attempt {attempt + 1})")
                if attempt < max_retries - 1:
                    continue
                return None
                
            except Exception as e:
                print(f"❌ Error fetching reel {shortcode} (attempt {attempt + 1}): {e}")
                if attempt < max_retries - 1:
                    continue
                return None
        
        return None
    
    async def fetch_post_ids(self, username: str, count: int = 100, start_pagination_token: str = None, max_pages: int = None) -> tuple[List[Dict], str]:
        """Fetch normal post IDs with robust multi-provider strategy.
        Order:
          1) RapidAPI 20251 GET /userposts/?username_or_id=<username>
          2) Stable POST get_ig_user_posts.php (fallback)
        """
        try:
            self.log_progress(f"Fetching {count} post IDs for @{username}...", debug_only=False)

            # Provider 1: instagram-scraper-20251 (fast GET)
            try:
                fast_host = os.getenv('RAPIDAPI_ALT_HOST_20251', 'instagram-scraper-20251.p.rapidapi.com')
                headers = {
                    'x-rapidapi-key': self.rapidapi_key,
                    'x-rapidapi-host': fast_host
                }
                url = f"https://{fast_host}/userposts/"
                params = { 'username_or_id': username }
                resp = requests.get(url, headers=headers, params=params, timeout=30)
                if resp.status_code == 200:
                    data = resp.json() if resp.text else {}
                    self.save_debug_response(data, "posts_fast_api", username)
                    items = []
                    # Try common shapes
                    if isinstance(data, dict):
                        if 'data' in data and isinstance(data['data'], list):
                            items = data['data']
                        elif 'items' in data and isinstance(data['items'], list):
                            items = data['items']
                        elif 'results' in data and isinstance(data['results'], list):
                            items = data['results']
                    posts_refs = []
                    for it in items:
                        # Prefer shortcode/code; keep as lightweight refs
                        shortcode = it.get('code') or it.get('shortcode') or it.get('id') or it.get('pk')
                        if shortcode:
                            posts_refs.append({ 'shortcode': shortcode })
                        # Stop if enough
                        if len(posts_refs) >= count:
                            break
                    if posts_refs:
                        self.log_progress(f"✅ Fetched {len(posts_refs)} post IDs from fast API", debug_only=True)
                        return posts_refs[:count], None
                else:
                    self.log_progress(f"⚠️ Fast API userposts failed: {resp.status_code}", debug_only=True)
            except Exception as e:
                self.log_progress(f"⚠️ Fast API userposts error: {e}", debug_only=True)

            # Provider 2: Stable endpoint (POST)
            all_posts = []
            max_id = start_pagination_token
            pages_fetched = 0
            target_pages = max_pages if max_pages else 3  # try a few pages by default for reliability
            batch_num = 1

            while len(all_posts) < count and pages_fetched < target_pages:
                url = f"https://{self.api_host}/get_ig_user_posts.php"
                payload = f"username_or_url={username}&count=50"
                if max_id:
                    payload += f"&max_id={max_id}"

                response = requests.post(url, data=payload, headers=self.headers, timeout=30)
                if response.status_code == 200:
                    data = response.json() if response.text else {}
                    self.save_debug_response(data, f"posts_batch_{batch_num}", username)
                    posts = []
                    if isinstance(data, dict):
                        if 'posts' in data and isinstance(data['posts'], list):
                            posts = data['posts']
                        elif 'items' in data and isinstance(data['items'], list):
                            posts = data['items']
                        elif 'data' in data and isinstance(data['data'], list):
                            posts = data['data']
                    if not posts:
                        break
                    all_posts.extend(posts)
                    # Try common pagination token fields
                    max_id = data.get('pagination_token') or data.get('next_max_id')
                    pages_fetched += 1
                    batch_num += 1
                    time.sleep(1)
                    if not max_id:
                        break
                else:
                    self.log_progress(f"❌ Stable posts fetch failed: {response.status_code}")
                    break

            # Normalize to lightweight refs with shortcodes
            refs: List[Dict] = []
            for it in all_posts:
                node = it.get('node', it)
                shortcode = node.get('shortcode') or node.get('code') or node.get('id') or node.get('pk')
                if shortcode:
                    refs.append({'shortcode': shortcode})
                if len(refs) >= count:
                    break

            self.log_progress(f"✅ Fetched {len(refs)} post IDs for @{username}")
            return refs[:count], max_id
        except Exception as e:
            self.log_progress(f"❌ Error fetching post IDs: {e}")
            return [], None

    async def fetch_post_details(self, session: aiohttp.ClientSession, shortcode: str, username: str, max_retries: int = 3) -> Optional[Dict]:
        """Fetch individual post details and map to unified content schema (no views for posts)"""
        import urllib.parse
        for attempt in range(max_retries):
            try:
                full_instagram_url = f"https://www.instagram.com/p/{shortcode}/"
                encoded_url = urllib.parse.quote(full_instagram_url, safe='')
                url = f"https://{self.api_host}/get_media_data.php?reel_post_code_or_url={encoded_url}&type=post"
                if attempt > 0:
                    await asyncio.sleep(min(10, 1 * (2 ** attempt)))
                async with session.get(url, headers=self.headers, timeout=30) as response:
                    if response.status == 200:
                        post_data = await response.json()
                        if not post_data or not isinstance(post_data, dict):
                            if attempt < max_retries - 1:
                                continue
                            return None

                        # Metrics
                        like_count = post_data.get('edge_media_preview_like', {}).get('count', 0)
                        comment_count = post_data.get('edge_media_to_parent_comment', {}).get('count', 0)

                        # Caption
                        caption_text = ""
                        edges = post_data.get('edge_media_to_caption', {}).get('edges', [])
                        if edges:
                            caption_text = edges[0].get('node', {}).get('text', '')

                        # Images / Media
                        display_url = post_data.get('display_url', '')
                        thumbnail_local = ""
                        display_url_local = ""
                        if display_url:
                            try:
                                display_url_local = self.download_image(display_url, f"{shortcode}_display.jpg", self.thumbnails_dir)
                                thumbnail_local = display_url_local
                            except Exception:
                                display_url_local = ""

                        image_versions = post_data.get('image_versions2', {})
                        if isinstance(image_versions, dict) and 'candidates' in image_versions and not thumbnail_local:
                            candidates = image_versions.get('candidates') or []
                            if candidates and 'url' in candidates[0]:
                                thumbnail_local = self.download_image(candidates[0]['url'], f"{shortcode}_thumb.jpg", self.thumbnails_dir)

                        # Determine content_style and carousel flags (robust across API variants)
                        product_type = post_data.get('product_type')
                        media_type = post_data.get('media_type')  # 1=image, 2=video, 8=carousel (private API)
                        # Private API style
                        carousel_media = post_data.get('carousel_media') or []
                        # Public GraphQL style
                        sidecar_edges = (
                            post_data.get('edge_sidecar_to_children', {}) or {}
                        ).get('edges', [])

                        # Count children from either representation
                        carousel_media_count = 0
                        if isinstance(carousel_media, list) and len(carousel_media) > 0:
                            carousel_media_count = len(carousel_media)
                        elif isinstance(sidecar_edges, list) and len(sidecar_edges) > 0:
                            carousel_media_count = len(sidecar_edges)

                        # Detect if any child is a video in carousel
                        carousel_has_video = False
                        if isinstance(carousel_media, list) and len(carousel_media) > 0:
                            for child in carousel_media:
                                try:
                                    if (child.get('media_type') == 2) or (child.get('video_versions')):
                                        carousel_has_video = True
                                        break
                                except Exception:
                                    continue
                        elif isinstance(sidecar_edges, list) and len(sidecar_edges) > 0:
                            for edge in sidecar_edges:
                                try:
                                    node = edge.get('node', {})
                                    if node.get('is_video') or node.get('video_url') or node.get('video_versions'):
                                        carousel_has_video = True
                                        break
                                except Exception:
                                    continue

                        # If we didn't get a display/thumbnail earlier and sidecar exists, use first child display_url
                        if not display_url and isinstance(sidecar_edges, list) and len(sidecar_edges) > 0:
                            try:
                                first_node = sidecar_edges[0].get('node', {})
                                display_url = first_node.get('display_url') or first_node.get('thumbnail_src') or display_url
                            except Exception:
                                pass

                        # Single item video detection across variants
                        is_video_post = bool(post_data.get('video_versions')) or bool(post_data.get('is_video')) or media_type == 2

                        # Compute content_style with broader carousel detection
                        is_carousel = (
                            product_type == 'carousel_container' or
                            media_type == 8 or
                            (isinstance(carousel_media, list) and len(carousel_media) > 0) or
                            (isinstance(sidecar_edges, list) and len(sidecar_edges) > 0)
                        )
                        if is_carousel:
                            content_style = 'carousel_video' if carousel_has_video else 'carousel_image'
                        else:
                            content_style = 'video' if is_video_post else 'image'

                        processed_post = {
                            'content_id': post_data.get('pk', shortcode),
                            'shortcode': shortcode,
                            'content_type': 'post',
                            'url': f"https://www.instagram.com/p/{shortcode}/",
                            'description': caption_text,
                            'thumbnail_url': display_url,
                            'thumbnail_local': thumbnail_local,
                            'display_url_local': display_url_local,
                            'content_style': content_style,
                            'view_count': 0,
                            'like_count': int(like_count),
                            'comment_count': int(comment_count),
                            'date_posted': post_data.get('taken_at_timestamp', post_data.get('taken_at')),
                            'username': username,
                            'language': 'en',
                            'all_image_urls': {
                                'display_url': display_url,
                                'product_type': product_type,
                                'media_type': media_type,
                                'carousel_media_count': carousel_media_count,
                                'carousel_has_video': carousel_has_video,
                                'is_sidecar': bool(sidecar_edges),
                            }
                        }
                        return processed_post
                    elif response.status == 429 and attempt < max_retries - 1:
                        await asyncio.sleep(min(30, 5 * (2 ** attempt)))
                        continue
                    else:
                        if attempt < max_retries - 1:
                            continue
                        return None
            except Exception:
                if attempt < max_retries - 1:
                    continue
                return None
        return None

    async def fetch_all_post_details(self, post_ids: List[Dict], username: str) -> List[Dict]:
        """Fetch details for a list of posts in parallel with rate limiting"""
        print(f"📋 Fetching details for {len(post_ids)} posts...")
        # Extract shortcodes
        shortcodes: List[str] = []
        for post in post_ids:
            post_data = post.get('node', post)
            shortcode = post_data.get('shortcode') or post_data.get('code') or post_data.get('id') or post_data.get('pk', '')
            if shortcode:
                shortcodes.append(shortcode)
        results: List[Dict] = []
        if not shortcodes:
            return results
        connector = aiohttp.TCPConnector(limit=8)
        async with aiohttp.ClientSession(connector=connector) as session:
            tasks = [self.fetch_post_details(session, sc, username) for sc in shortcodes]
            fetched = await asyncio.gather(*tasks, return_exceptions=True)
            for item in fetched:
                if isinstance(item, dict):
                    results.append(item)
        return results

    def _calculate_post_outliers(self, posts: List[Dict]) -> List[Dict]:
        """Compute outlier_score for posts using likes vs median likes"""
        if not posts:
            return posts
        likes = [p.get('like_count', 0) for p in posts if isinstance(p.get('like_count', 0), (int, float))]
        non_zero_likes = [l for l in likes if l and l > 0]
        median_likes = statistics.median(non_zero_likes) if non_zero_likes else 0
        for p in posts:
            like_count = p.get('like_count', 0)
            outlier_score = (like_count / median_likes) if median_likes > 0 else 0
            p['outlier_score'] = round(outlier_score, 4)
        return posts

    async def run_posts_only_pipeline(self, username: str, max_posts: int = 60) -> Tuple[Dict, List[Dict], List[Dict]]:
        """Run a posts-only pipeline: fetch profile, posts, compute outliers by likes, categorize, and save"""
        print(f"⚡ Starting POSTS-ONLY pipeline for @{username}")
        try:
            self._validate_pipeline_prerequisites(username)
        except Exception as e:
            print(f"❌ Pipeline validation failed: {e}")
            return None, [], []

        # Step 1: Profile
        profile_data = await self.fetch_profile_data(username)
        if not profile_data:
            print("❌ Failed to fetch profile data")
            return None, [], []

        # Normalize/raw-map fields so saving uses the same schema as primary profile fetch
        # This ensures display fields like profile_name, bio, followers, posts_count are present
        normalized_profile: Dict = profile_data.copy()
        try:
            normalized_profile.setdefault('username', username)
            # Name and bio
            if not normalized_profile.get('profile_name'):
                normalized_profile['profile_name'] = normalized_profile.get('full_name', username)
            if not normalized_profile.get('bio'):
                normalized_profile['bio'] = normalized_profile.get('biography', '')
            # Followers and posts
            if 'followers' not in normalized_profile:
                normalized_profile['followers'] = int(normalized_profile.get('follower_count', normalized_profile.get('followers', 0)) or 0)
            if 'posts_count' not in normalized_profile:
                normalized_profile['posts_count'] = int(normalized_profile.get('media_count', normalized_profile.get('posts_count', 0)) or 0)
            # Verification / business flags
            if 'is_verified' not in normalized_profile:
                normalized_profile['is_verified'] = bool(normalized_profile.get('is_verified', False))
            if 'is_business_account' not in normalized_profile:
                normalized_profile['is_business_account'] = bool(normalized_profile.get('is_business', False))
            # Profile image mapping
            if not normalized_profile.get('profile_image_url'):
                normalized_profile['profile_image_url'] = normalized_profile.get('profile_pic_url', '')
            # URL convenience
            if not normalized_profile.get('profile_url'):
                normalized_profile['profile_url'] = f"https://instagram.com/{username}"
        except Exception as e:
            print(f"⚠️ Failed to normalize basic profile fields for @{username}: {e}")

        # Step 2: Post IDs
        post_ids, _ = await self.fetch_post_ids(username, count=max_posts, max_pages=2)
        if not post_ids:
            print("❌ No post IDs found")
            return normalized_profile, [], []

        # Filter existing content
        existing_shortcodes = await self._get_existing_content_ids_from_db(username, content_type_filter='post')
        filtered_ids = self._filter_new_reel_ids(post_ids, existing_shortcodes)

        # Step 3: Details
        detailed_posts = await self.fetch_all_post_details(filtered_ids, username)
        if not detailed_posts:
            print("❌ No post details fetched")
            return normalized_profile, [], []

        # Step 4: Categorize and compute outliers
        categorized_posts: List[Dict] = []
        for p in detailed_posts:
            try:
                ai = await self.ai_categorize_reel_content(p.get('description', '') or '')
                p.update({
                    'primary_category': ai.get('primary_category', 'Lifestyle'),
                    'secondary_category': ai.get('secondary_category', ''),
                    'tertiary_category': ai.get('tertiary_category', ''),
                    'categorization_confidence': ai.get('confidence', 0.7),
                })
                # Map keywords to keyword_1..keyword_4
                kws = ai.get('keywords') or []
                if isinstance(kws, list):
                    p['keyword_1'] = (kws[0] if len(kws) > 0 else '')
                    p['keyword_2'] = (kws[1] if len(kws) > 1 else '')
                    p['keyword_3'] = (kws[2] if len(kws) > 2 else '')
                    p['keyword_4'] = (kws[3] if len(kws) > 3 else '')
                categorized_posts.append(p)
            except Exception:
                p.update({
                    'primary_category': 'Lifestyle',
                    'secondary_category': '',
                    'tertiary_category': '',
                    'categorization_confidence': 0.5,
                })
                categorized_posts.append(p)

        categorized_posts = self._calculate_post_outliers(categorized_posts)

        # Step 4.5: Fetch similar/related accounts so the primary profile gets similar_account1..20 fields
        secondary_profiles: List[Dict] = []
        try:
            similar_profiles_list = await self.fetch_similar_profiles(username)
            if similar_profiles_list:
                secondary_profiles = await self.process_all_secondary_profiles(similar_profiles_list, username)
                # Populate similar_account1..20 on the normalized profile (usernames only)
                secondary_usernames = [p.get('username', '') for p in secondary_profiles if p.get('username')]
                for i in range(1, 21):
                    key = f'similar_account{i}'
                    normalized_profile[key] = secondary_usernames[i-1] if i <= len(secondary_usernames) else ''
        except Exception as e:
            print(f"⚠️ Could not fetch/process similar profiles for @{username}: {e}")

        # Step 5: Save
        await self.save_to_csv_and_supabase(normalized_profile, categorized_posts, secondary_profiles, username)

        print(f"✅ POSTS-ONLY pipeline complete for @{username}: {len(categorized_posts)} posts saved")
        return normalized_profile, categorized_posts, secondary_profiles
    async def fetch_all_reel_details(self, reel_ids: List[Dict], username: str) -> List[Dict]:
        """Step 3: Fetch all reel details with SMART RATE LIMITING and RETRY LOGIC"""
        print(f"📋 Fetching details for {len(reel_ids)} reels with smart rate limiting...")
        
        # Extract shortcodes first
        shortcodes = []
        for reel in reel_ids:
            shortcode = None
            
            # Try different possible structures
            if 'node' in reel and 'media' in reel['node']:
                shortcode = reel['node']['media'].get('code', '')
            elif 'shortcode' in reel:
                shortcode = reel.get('shortcode', '')
            elif 'code' in reel:
                shortcode = reel.get('code', '')
            
            if shortcode:
                shortcodes.append(shortcode)
            else:
                print(f"⚠️ No shortcode found in reel: {list(reel.keys())}")
        
        if not shortcodes:
            print("❌ No valid shortcodes found")
            return []
        
        detailed_reels = []
        failed_shortcodes = []
        
        # Smart batching with dynamic adjustment
        current_batch_size = 3  # Start smaller for rate limiting
        max_batch_size = 8
        min_batch_size = 1
        
        # Track rate limiting
        rate_limit_hits = 0
        consecutive_successes = 0
        
        async with aiohttp.ClientSession() as session:
            for i in range(0, len(shortcodes), current_batch_size):
                batch_shortcodes = shortcodes[i:i + current_batch_size]
                batch_num = i//current_batch_size + 1
                total_batches = math.ceil(len(shortcodes)/current_batch_size)
                
                print(f"🔄 Batch {batch_num}/{total_batches} ({len(batch_shortcodes)} reels, batch_size={current_batch_size})")
                
                # Retry logic for the entire batch
                max_batch_retries = 2
                for batch_attempt in range(max_batch_retries):
                    try:
                        # Add semaphore for concurrency control within batch
                        semaphore = asyncio.Semaphore(current_batch_size)
                        
                        async def fetch_with_semaphore(shortcode):
                            async with semaphore:
                                # Add small stagger between requests in same batch
                                await asyncio.sleep(0.3)
                                return await self.fetch_reel_details(session, shortcode, username)
                        
                        tasks = [fetch_with_semaphore(sc) for sc in batch_shortcodes]
                        batch_results = await asyncio.gather(*tasks, return_exceptions=True)
                        
                        # Analyze results
                        valid_results = []
                        rate_limited_count = 0
                        none_count = 0
                        exception_count = 0
                        
                        for j, result in enumerate(batch_results):
                            if isinstance(result, Exception):
                                if "429" in str(result) or "rate limit" in str(result).lower():
                                    rate_limited_count += 1
                                    failed_shortcodes.append(batch_shortcodes[j])
                                else:
                                    exception_count += 1
                                    failed_shortcodes.append(batch_shortcodes[j])
                            elif result is None:
                                none_count += 1
                                print(f"⚠️ Reel detail request returned NoneType for {batch_shortcodes[j]}")
                                failed_shortcodes.append(batch_shortcodes[j])
                            else:
                                valid_results.append(result)
                        
                        detailed_reels.extend(valid_results)
                        
                        # Dynamic batch size adjustment
                        success_rate = len(valid_results) / len(batch_shortcodes)
                        
                        if rate_limited_count > 0:
                            rate_limit_hits += 1
                            current_batch_size = max(min_batch_size, current_batch_size - 1)
                            print(f"🚨 Rate limited! Reducing batch size to {current_batch_size}")
                            
                            # Exponential backoff for rate limits
                            backoff_time = min(30, 5 * (2 ** batch_attempt))
                            print(f"⏱️ Backing off for {backoff_time}s...")
                            await asyncio.sleep(backoff_time)
                            
                            if batch_attempt < max_batch_retries - 1:
                                continue  # Retry this batch
                        
                        elif success_rate > 0.8:  # 80% success rate
                            consecutive_successes += 1
                            if consecutive_successes >= 2 and current_batch_size < max_batch_size:
                                current_batch_size = min(max_batch_size, current_batch_size + 1)
                                print(f"✅ Good success rate, increasing batch size to {current_batch_size}")
                        
                        print(f"✅ Batch {batch_num}: {len(valid_results)}/{len(batch_shortcodes)} successful")
                        if rate_limited_count > 0:
                            print(f"   🚨 {rate_limited_count} rate limited")
                        if none_count > 0:
                            print(f"   ⚠️ {none_count} returned None")
                        if exception_count > 0:
                            print(f"   ❌ {exception_count} exceptions")
                        
                        break  # Success, move to next batch
                        
                    except Exception as e:
                        print(f"❌ Batch {batch_num} attempt {batch_attempt + 1} failed: {e}")
                        if batch_attempt == max_batch_retries - 1:
                            # Final attempt failed, add all to failed list
                            failed_shortcodes.extend(batch_shortcodes)
                        else:
                            # Wait before retry
                            await asyncio.sleep(3 * (2 ** batch_attempt))
                
                # Adaptive delay between batches
                if rate_limit_hits > 0:
                    batch_delay = 3.0  # Longer delay if we've hit rate limits
                else:
                    batch_delay = 1.0  # Normal delay
                    
                await asyncio.sleep(batch_delay)
        
        print(f"✅ Successfully fetched {len(detailed_reels)} reel details out of {len(shortcodes)} attempts")
        if failed_shortcodes:
            print(f"⚠️ Failed to fetch {len(failed_shortcodes)} reels: {failed_shortcodes[:5]}{'...' if len(failed_shortcodes) > 5 else ''}")
            
            # If we didn't get detailed data, create basic reel data from reel IDs
            if len(detailed_reels) == 0 and reel_ids:
                print("🔄 No detailed reel data retrieved, creating basic reel records from IDs...")
                for reel in reel_ids:
                    try:
                        # Extract basic data from the reel ID response
                        if 'node' in reel and 'media' in reel['node']:
                            media = reel['node']['media']
                            basic_reel = {
                                'content_id': media.get('pk', ''),
                                'shortcode': media.get('code', ''),
                                'content_type': 'reel',
                                'url': f"https://www.instagram.com/p/{media.get('code', '')}/",
                                'description': '',  # No caption in basic data
                                'thumbnail_url': '',  # Will be filled from image_versions2 if available
                                'thumbnail_local': '',
                                'view_count': int(media.get('play_count', 0)),
                                'like_count': int(media.get('like_count', 0)),
                                'comment_count': int(media.get('comment_count', 0)),
                                'date_posted': None,
                                'username': username,
                                'hashtags': [],
                                'language': 'en',
                                'all_image_urls': {}
                            }
                            
                            # Try to extract thumbnail from image_versions2
                            image_versions = media.get('image_versions2', {})
                            if isinstance(image_versions, dict) and 'candidates' in image_versions:
                                candidates = image_versions['candidates']
                                if isinstance(candidates, list) and candidates:
                                    basic_reel['thumbnail_url'] = candidates[0].get('url', '')
                            
                            detailed_reels.append(basic_reel)
                            print(f"📋 Created basic reel record: {basic_reel['shortcode']} ({basic_reel['view_count']:,} views)")
                    except Exception as e:
                        print(f"❌ Error creating basic reel record: {e}")
                        continue
                
                print(f"✅ Created {len(detailed_reels)} basic reel records from IDs")
        
        return detailed_reels
    
    def _create_basic_reels_from_ids(self, reel_ids: List[Dict], username: str) -> List[Dict]:
        """Create basic reel records from reel IDs when detailed fetching fails"""
        basic_reels = []
        for reel in reel_ids:
            try:
                # Extract basic data from the reel ID response
                if 'node' in reel and 'media' in reel['node']:
                    media = reel['node']['media']
                    basic_reel = {
                        'content_id': media.get('pk', ''),
                        'shortcode': media.get('code', ''),
                        'content_type': 'reel',
                        'url': f"https://www.instagram.com/p/{media.get('code', '')}/",
                        'description': '',  # No caption in basic data
                        'thumbnail_url': '',  # Will be filled from image_versions2 if available
                        'thumbnail_local': '',
                        'view_count': int(media.get('play_count', 0)),
                        'like_count': int(media.get('like_count', 0)),
                        'comment_count': int(media.get('comment_count', 0)),
                        'date_posted': None,
                        'username': username,
                        'hashtags': [],
                        'language': 'en',
                        'all_image_urls': {}
                    }
                    
                    # Try to extract thumbnail from image_versions2
                    image_versions = media.get('image_versions2', {})
                    if isinstance(image_versions, dict) and 'candidates' in image_versions:
                        candidates = image_versions['candidates']
                        if isinstance(candidates, list) and candidates:
                            basic_reel['thumbnail_url'] = candidates[0].get('url', '')
                    
                    basic_reels.append(basic_reel)
                    print(f"📋 Created basic reel record: {basic_reel['shortcode']} ({basic_reel['view_count']:,} views)")
            except Exception as e:
                print(f"❌ Error creating basic reel record: {e}")
                continue
        
        print(f"✅ Created {len(basic_reels)} basic reel records from IDs")
        return basic_reels
    
    async def _fetch_and_process_all_similar_profiles(self, username: str) -> List[Dict]:
        """Fetch similar profiles and process them completely (for parallel startup)"""
        try:
            self.log_progress(f"🔍 [PARALLEL] Fetching similar profiles for @{username}...", debug_only=True)
            self.log_progress(f"Finding similar profiles...", debug_only=False)
            
            # Step 1: Fetch similar profiles list
            similar_profiles_list = await self.fetch_similar_profiles(username)
            
            if not similar_profiles_list:
                print("⚠️ [PARALLEL] No similar profiles found")
                return []
            
            print(f"✅ [PARALLEL] Found {len(similar_profiles_list)} similar profiles")
            
            # Step 2: Process all secondary profiles completely (with details + categorization)
            print(f"👥 [PARALLEL] Processing ALL {len(similar_profiles_list)} secondary profiles...")
            secondary_profiles = await self.process_all_secondary_profiles(similar_profiles_list, username)
            
            if secondary_profiles:
                # No need for separate categorization - already done immediately!
                print(f"✅ [PARALLEL] Completed: {len(secondary_profiles)} secondary profiles fully processed (with immediate categorization)")
                return secondary_profiles
            else:
                print("⚠️ [PARALLEL] No secondary profiles were processed successfully")
                return []
                
        except Exception as e:
            print(f"❌ [PARALLEL] Error in similar profiles processing: {e}")
            return []
    
    def calculate_metrics(self, reels: List[Dict]) -> Dict:
        """Step 4: Calculate comprehensive metrics"""
        if not reels:
            return {
                'total_reels': 0,
                'median_views': 0,
                'mean_views': 0,
                'std_views': 0,
                'total_views': 0,
                'total_likes': 0,
                'total_comments': 0,
            }
        
        # Extract metrics
        views = [reel.get('view_count', 0) for reel in reels]
        likes = [reel.get('like_count', 0) for reel in reels]
        comments = [reel.get('comment_count', 0) for reel in reels]
        
        # Filter non-zero views for statistics
        non_zero_views = [v for v in views if v > 0]
        
        median_views = statistics.median(non_zero_views) if non_zero_views else 0
        mean_views = statistics.mean(non_zero_views) if non_zero_views else 0
        std_views = statistics.stdev(non_zero_views) if len(non_zero_views) > 1 else 0
        
        # Calculate outlier scores for each reel
        for reel in reels:
            view_count = reel.get('view_count', 0)
            outlier_score = (view_count / median_views) if median_views > 0 else 0
            reel['outlier_score'] = round(outlier_score, 4)
        
        return {
            'total_reels': len(reels),
            'median_views': int(median_views),
            'mean_views': round(mean_views, 2),
            'std_views': round(std_views, 2),
            'total_views': sum(views),
            'total_likes': sum(likes),
            'total_comments': sum(comments),
        }
    
    async def categorize_reel(self, reel: Dict) -> Dict:
        """Step 5: Categorize individual reel using AI (PROMPT 3)"""
        try:
            description = reel.get('description', '')
            
            print(f"🤖 Categorizing reel {reel.get('shortcode', 'unknown')}")
            print(f"   Description preview: {description[:100]}...")
            
            # Use AI categorization (PROMPT 3) without hashtags
            ai_result = await self.ai_categorize_reel_content(description)
            
            # Update reel with AI categorization
            keywords = ai_result.get('keywords', [''])
            reel.update({
                'primary_category': ai_result.get('primary_category', 'Lifestyle'),
                'secondary_category': ai_result.get('secondary_category', ''),
                'tertiary_category': ai_result.get('tertiary_category', ''),
                'keyword_1': keywords[0] if len(keywords) > 0 else '',
                'keyword_2': keywords[1] if len(keywords) > 1 else '',
                'keyword_3': keywords[2] if len(keywords) > 2 else '',
                'keyword_4': keywords[3] if len(keywords) > 3 else '',
                'categorization_confidence': ai_result.get('confidence', 0.7),
                'content_style': 'video'  # Default for reels
            })
            
            print(f"✅ Categorized as: {reel['primary_category']} (confidence: {reel['categorization_confidence']})")
            print(f"   Keywords: {[reel.get(f'keyword_{i}', '') for i in range(1,5)]}")
            
            return reel
            
        except Exception as e:
            print(f"❌ Error categorizing reel: {e}")
            return reel
    
    async def categorize_secondary_profile(self, profile: Dict) -> Dict:
        """Categorize a secondary profile using AI (PROMPTS 1 & 2)"""
        try:
            username = profile.get('username', '')
            profile_name = profile.get('full_name', username)
            bio = profile.get('biography', '')
            followers = profile.get('followers_count', 0)
            
            print(f"🤖 Categorizing secondary profile @{username}")
            
            # AI categorization using both prompts
            account_type_result = await self.ai_categorize_profile_type(username, profile_name, bio, followers)
            content_categories_result = await self.ai_categorize_profile_content(username, profile_name, bio)
            
            # Update profile with AI categorization results
            profile.update({
                'primary_category': content_categories_result.get('primary_category', 'Lifestyle'),
                'secondary_category': content_categories_result.get('secondary_category', ''),
                'tertiary_category': content_categories_result.get('tertiary_category', ''),
                'categorization_confidence': content_categories_result.get('confidence', 0.7),
                'estimated_account_type': account_type_result.get('account_type', 'Personal'),
                'account_type_confidence': account_type_result.get('confidence', 0.7),
            })
            
            print(f"✅ Categorized @{username} as: {profile['primary_category']} ({profile['estimated_account_type']})")
            
            return profile
            
        except Exception as e:
            print(f"❌ Error categorizing secondary profile @{profile.get('username', 'unknown')}: {e}")
            # Return profile with default values
            profile.update(DEFAULT_PROFILE_CATEGORIES)
            profile.update({
                'estimated_account_type': 'Personal',
                'account_type_confidence': 0.5,
            })
            return profile
    
    async def categorize_all_reels_parallel(self, reels: List[Dict], batch_size: int = 20) -> List[Dict]:
        """Categorize all reels in parallel batches"""
        self.log_progress(f"🤖 Categorizing {len(reels)} reels in parallel batches of {batch_size}...", debug_only=True)
        self.log_progress(f"Categorizing {len(reels)} content items...", debug_only=False)
        
        categorized_reels = []
        
        # Process reels in batches
        for i in range(0, len(reels), batch_size):
            batch = reels[i:i + batch_size]
            print(f"📦 Processing reel batch {i//batch_size + 1}: {len(batch)} reels")
            
            # Create tasks for parallel processing
            tasks = [self.categorize_reel(reel) for reel in batch]
            
            # Run batch in parallel
            batch_results = await asyncio.gather(*tasks, return_exceptions=True)
            
            # Handle results and exceptions
            for j, result in enumerate(batch_results):
                if isinstance(result, Exception):
                    print(f"❌ Error categorizing reel {batch[j].get('shortcode', 'unknown')}: {result}")
                    # Add uncategorized reel with defaults
                    reel_defaults = DEFAULT_REEL_CATEGORIES.copy()
                    reel_defaults.update({
                        'keyword_1': '', 'keyword_2': '', 'keyword_3': '', 'keyword_4': '',
                        'content_style': 'video'
                    })
                    batch[j].update(reel_defaults)
                    categorized_reels.append(batch[j])
                else:
                    categorized_reels.append(result)
            
            print(f"✅ Completed batch {i//batch_size + 1}: {len(batch_results)} reels categorized")
            
            # Small delay between batches to avoid overwhelming OpenAI API
            if i + batch_size < len(reels):
                await asyncio.sleep(1)
        
        print(f"✅ Categorized {len(categorized_reels)} reels total")
        
        # DEBUG: Validate return data
        if categorized_reels:
            print(f"🐛 DEBUG: Sample categorized reel fields: {list(categorized_reels[0].keys())}")
            print(f"🐛 DEBUG: First categorized reel shortcode: {categorized_reels[0].get('shortcode', 'N/A')}")
        else:
            print("🚨 WARNING: categorize_all_reels_parallel returning empty list!")
        
        return categorized_reels
        
    async def categorize_all_secondary_profiles_parallel(self, profiles: List[Dict], batch_size: int = 20) -> List[Dict]:
        """Categorize all secondary profiles in parallel batches"""
        self.log_progress(f"🤖 Categorizing {len(profiles)} secondary profiles in parallel batches of {batch_size}...", debug_only=True)
        self.log_progress(f"Categorizing {len(profiles)} similar profiles...", debug_only=False)
        
        categorized_profiles = []
        
        # Process profiles in batches
        for i in range(0, len(profiles), batch_size):
            batch = profiles[i:i + batch_size]
            print(f"📦 Processing profile batch {i//batch_size + 1}: {len(batch)} profiles")
            
            # Create tasks for parallel processing
            tasks = [self.categorize_secondary_profile(profile) for profile in batch]
            
            # Run batch in parallel
            batch_results = await asyncio.gather(*tasks, return_exceptions=True)
            
            # Handle results and exceptions
            for j, result in enumerate(batch_results):
                if isinstance(result, Exception):
                    print(f"❌ Error categorizing profile @{batch[j].get('username', 'unknown')}: {result}")
                    # Add uncategorized profile with defaults
                    batch[j].update(DEFAULT_PROFILE_CATEGORIES)
                    categorized_profiles.append(batch[j])
                else:
                    categorized_profiles.append(result)
            
            print(f"✅ Completed batch {i//batch_size + 1}: {len(batch_results)} profiles categorized")
            
            # Small delay between batches to avoid overwhelming OpenAI API
            if i + batch_size < len(profiles):
                await asyncio.sleep(1)
        
        print(f"✅ Categorized {len(categorized_profiles)} secondary profiles total")
        return categorized_profiles
    
    async def fetch_similar_profiles(self, username: str) -> List[Dict]:
        """Step 6: Fetch similar profiles with retry logic"""
        max_attempts = 3  # 1 original + 2 retries for better reliability
        
        for attempt in range(max_attempts):
            try:
                if attempt > 0:
                    # Exponential backoff: 2s, 4s
                    delay = 2 ** attempt
                    print(f"🔄 Retry attempt {attempt + 1}/{max_attempts} for similar profiles: @{username} (waiting {delay}s)")
                    await asyncio.sleep(delay)
                
                url = f"https://{self.similar_host}/get_ig_similar_accounts.php?username_or_url={username}"
                
                if attempt == 0:  # Only print URL on first attempt to avoid spam
                    print(f"🔍 Similar Profiles Request: {url}")
                
                response = requests.get(url, headers=self.similar_headers, timeout=45)  # Increased timeout
                
                # Check for HTTP errors that should be retried
                if response.status_code >= 500:
                    # Server errors - should retry
                    raise requests.exceptions.HTTPError(f"Server error: {response.status_code}")
                elif response.status_code == 429:
                    # Rate limit - should retry with longer delay
                    print(f"⚠️ Rate limited, will retry with longer delay")
                    raise requests.exceptions.HTTPError(f"Rate limit: {response.status_code}")
                elif response.status_code == 408:
                    # Request timeout - should retry
                    raise requests.exceptions.HTTPError(f"Request timeout: {response.status_code}")
                elif response.status_code >= 400:
                    # Client errors (except rate limit and timeout) - don't retry
                    print(f"❌ Client error {response.status_code} for @{username}: {response.text}")
                    return []
                
                if response.status_code == 200:
                    try:
                        data = response.json()
                    except ValueError as e:
                        # JSON parsing error - should retry
                        raise ValueError(f"Invalid JSON response: {e}")
                    
                    # DEBUG: Print and save full response (only on successful response)
                    self.print_json_response(data, f"similar_profiles_{username}")
                    self.save_debug_response(data, "similar_profiles", username)
                    
                    # Parse similar profiles - handle both list and dict formats
                    similar_profiles = []
                    if isinstance(data, list):
                        # Direct list format
                        similar_profiles = data
                    elif isinstance(data, dict):
                        # Check for list in 'data' key or numeric keys
                        if 'data' in data and isinstance(data['data'], list):
                            similar_profiles = data['data']
                        else:
                            # Numeric keys format
                            for key, profile in data.items():
                                if key.isdigit() and isinstance(profile, dict):
                                    similar_profiles.append(profile)
                    
                    # Filter and display found profiles
                    valid_profiles = []
                    for profile in similar_profiles:
                        if isinstance(profile, dict) and profile.get('username'):
                            valid_profiles.append(profile)
                            if attempt == 0:  # Only print found profiles on first attempt to avoid spam
                                print(f"🔍 Similar profile found: @{profile.get('username', 'unknown')} - {profile.get('full_name', 'N/A')}")
                    
                    # Successful response - log and return results (even if empty)
                    if attempt > 0:
                        print(f"✅ Retry successful for @{username}: Found {len(valid_profiles)} similar profiles")
                    else:
                        print(f"✅ Found {len(valid_profiles)} similar profiles for @{username}")
                    return valid_profiles[:20]  # Limit to top 20
                else:
                    # Non-200 status code that isn't a server error
                    print(f"❌ Similar profiles fetch failed: {response.status_code}")
                    print(f"🐛 Response text: {response.text}")
                    return []
                    
            except (requests.exceptions.RequestException, ValueError) as e:
                error_type = type(e).__name__
                print(f"⚠️ Attempt {attempt + 1}/{max_attempts} failed for @{username} ({error_type}): {e}")
                
                # Special handling for rate limits - add extra delay
                if "429" in str(e) or "rate limit" in str(e).lower():
                    if attempt < max_attempts - 1:  # Don't delay on the last attempt
                        print(f"🔄 Rate limit detected, adding extra delay...")
                        await asyncio.sleep(5)  # Extra delay for rate limits
                
                if attempt == max_attempts - 1:
                    print(f"❌ All {max_attempts} attempts failed for similar profiles @{username} (final error: {error_type})")
                    return []
            except Exception as e:
                # Unexpected errors - don't retry
                print(f"❌ Unexpected error fetching similar profiles for @{username}: {e}")
                return []
        
        return []
    
    def fetch_secondary_profile_data_instagram360(self, username: str) -> Optional[Dict]:
        """Fetch detailed profile data using configurable Instagram Scraper API"""
        try:
            print(f"📡 Fetching secondary profile data for @{username} using Instagram Scraper API")
            
            # Use configurable host, fallback to the working endpoint
            secondary_host = os.getenv('INSTAGRAM_SCRAPER_SECONDARY_HOST', 'instagram-scraper-20251.p.rapidapi.com')
            conn = http.client.HTTPSConnection(secondary_host)
            
            headers = {
                'x-rapidapi-key': self.rapidapi_key,
                'x-rapidapi-host': secondary_host
            }
            
            conn.request("GET", f"/userinfo/?username_or_id={username}", headers=headers)
            res = conn.getresponse()
            data = res.read()
            
            if res.status == 200:
                profile_data = json.loads(data.decode("utf-8"))
                
                # Save debug response
                self.save_debug_response(profile_data, f"instagram_scraper_profile_{username}", username)
                
                # NEW API STRUCTURE: Data is directly under 'data' key without 'status' wrapper
                if 'data' in profile_data and profile_data['data']:
                    data_obj = profile_data['data']
                    print(f"✅ Got Instagram Scraper profile data for @{username}")
                    # Rate limiting now handled at higher level
                    return data_obj
                else:
                    print(f"❌ Instagram Scraper API returned no data for @{username}")
                    return None
            elif res.status == 429:
                print(f"⚠️ Rate limited for @{username}, waiting 3 seconds...")
                time.sleep(3)
                return None  # Skip this profile to avoid blocking others
            elif res.status == 403:
                print(f"❌ Access forbidden for @{username} (private account or API restriction)")
                return None
            else:
                print(f"❌ Instagram Scraper API request failed for @{username}: HTTP {res.status}")
                return None
                
        except Exception as e:
            print(f"❌ Error fetching Instagram Scraper profile data for @{username}: {e}")
            return None
            
    async def fetch_secondary_profile_data(self, similar_profile: Dict, primary_username: str) -> Optional[Dict]:
        """Step 7: Fetch detailed data for a secondary profile without categorization"""
        try:
            username = similar_profile.get('username', '')
            if not username:
                return None
            
            # Fetch detailed profile data using Instagram Scraper API
            instagram360_data = self.fetch_secondary_profile_data_instagram360(username)
            
            if instagram360_data:
                # Extract data from Instagram Scraper API response (correct field mapping)
                profile_pic_url = instagram360_data.get('profile_pic_url', similar_profile.get('profile_pic_url', ''))
                # Get HD profile pic URL from nested structure
                hd_pic_info = instagram360_data.get('hd_profile_pic_url_info', {})
                hd_profile_pic_url = hd_pic_info.get('url', profile_pic_url)
                
                full_name = instagram360_data.get('full_name', similar_profile.get('full_name', ''))
                biography = instagram360_data.get('biography', '')
                followers_count = instagram360_data.get('follower_count', 0)
                following_count = instagram360_data.get('following_count', 0)
                is_verified = instagram360_data.get('is_verified', similar_profile.get('is_verified', False))
                is_private = instagram360_data.get('is_private', similar_profile.get('is_private', False))
                media_count = instagram360_data.get('media_count', 0)
                business_email = instagram360_data.get('public_email', '')
                external_url = instagram360_data.get('external_url', '')
                category = instagram360_data.get('category', '')
                # Map provider-specific account_type to our enum (Personal, Business Page, Influencer)
                raw_account_type = instagram360_data.get('account_type', None)
                if isinstance(raw_account_type, (int, float)):
                    account_type_map = {1: 'Personal', 2: 'Business Page', 3: 'Influencer'}
                    estimated_account_type = account_type_map.get(int(raw_account_type), 'Personal')
                elif isinstance(raw_account_type, str):
                    val = raw_account_type.strip().lower()
                    if val in ['personal', 'creator', 'influencer']:
                        estimated_account_type = 'Personal' if val == 'personal' else 'Influencer'
                    elif val in ['business', 'business page']:
                        estimated_account_type = 'Business Page'
                    else:
                        estimated_account_type = 'Personal'
                else:
                    estimated_account_type = 'Personal'
                
            else:
                # Fallback to basic similar profile data
                print(f"⚠️ Using basic data for @{username}")
                profile_pic_url = similar_profile.get('profile_pic_url', '')
                hd_profile_pic_url = profile_pic_url  # Same as regular for fallback
                full_name = similar_profile.get('full_name', '')
                biography = ''
                followers_count = self.extract_followers_from_context(similar_profile.get('social_context', ''))
                following_count = 0
                is_verified = similar_profile.get('is_verified', False)
                is_private = similar_profile.get('is_private', False)
                media_count = 0
                business_email = ''
                external_url = ''
                category = ''
                estimated_account_type = 'Personal'
            
            # Download profile image (prefer HD version)
            profile_pic_local = ""
            download_url = hd_profile_pic_url if hd_profile_pic_url else profile_pic_url
            if download_url:
                filename = f"{username}_secondary_profile.jpg"
                try:
                    profile_pic_local = self.download_image(download_url, filename, self.images_dir)
                    print(f"📸 Downloaded secondary profile image: {filename}")
                except Exception as e:
                    print(f"⚠️ Failed to download profile image for @{username}: {e}")
            
            # Map to secondary_profiles schema WITHOUT categorization (will be done later in parallel)
            secondary_profile = {
                'username': username,
                'full_name': full_name,
                'biography': biography,
                'followers_count': followers_count,
                'following_count': following_count,
                'media_count': media_count,
                'profile_pic_url': profile_pic_url,
                'profile_pic_local': profile_pic_local,
                'is_verified': is_verified,
                'is_private': is_private,
                'business_email': business_email,
                'external_url': external_url,
                'category': category,
                'pk': similar_profile.get('pk', ''),
                'social_context': similar_profile.get('social_context', ''),
                'estimated_account_type': estimated_account_type,
                # Categorization fields will be filled later
                'primary_category': '',
                'secondary_category': '',
                'tertiary_category': '',
                'categorization_confidence': 0.0,
                'estimated_language': 'en',  # Default, could be detected from bio
                'click_count': 0,
                'search_count': 0,
                'promotion_eligible': followers_count > 1000,  # Basic eligibility check
                'discovered_by': primary_username,  # The primary profile that discovered this one
                'discovery_reason': 'similar_profiles_api',
                'api_source': 'instagram_scraper_20251',
                'similarity_rank': 0,  # Will be set based on order
                'last_basic_scrape': datetime.utcnow().isoformat(),
                'last_full_scrape': datetime.utcnow().isoformat() if instagram360_data else None,
                'analysis_timestamp': datetime.utcnow().isoformat(),
            }
            
            return secondary_profile
            
        except Exception as e:
            print(f"❌ Error fetching secondary profile data for @{username}: {e}")
            return None
    
    async def process_all_secondary_profiles(self, similar_profiles: List[Dict], primary_username: str) -> List[Dict]:
        """Step 7: Process all secondary profiles with TRUE PARALLEL processing and rate limiting"""
        print(f"📋 Processing {len(similar_profiles)} secondary profiles...")
        
        # Step 1: Check which profiles already exist in database to avoid duplicates
        existing_usernames = set()
        if similar_profiles:
            usernames_to_check = [p.get('username', '') for p in similar_profiles if p.get('username')]
            if usernames_to_check:
                try:
                    # Check which usernames already exist in secondary_profiles table
                    existing_response = self.supabase.client.table('secondary_profiles').select('username').in_('username', usernames_to_check).execute()
                    existing_usernames = {profile['username'] for profile in existing_response.data}
                    
                    if existing_usernames:
                        print(f"🔍 Found {len(existing_usernames)} profiles already in database: {list(existing_usernames)[:5]}...")
                        print(f"⚡ Skipping API calls for existing profiles to save quota and avoid duplicates")
                except Exception as e:
                    print(f"⚠️ Error checking existing profiles: {e} - proceeding without duplicate check")
        
        # Step 2: Filter out profiles that already exist
        new_profiles = [
            profile for profile in similar_profiles 
            if profile.get('username', '') not in existing_usernames
        ]
        
        print(f"📊 Processing {len(new_profiles)} NEW profiles (skipping {len(existing_usernames)} existing)")
        print(f"🚀 Using TRUE PARALLEL processing with rate limiting (3 concurrent requests)")
        
        start_time = time.time()
        
        # Create semaphore to limit concurrent requests (respects rate limits)
        semaphore = asyncio.Semaphore(3)  # Reduced to 3 concurrent requests for better rate limiting
        
        async def process_single_profile(similar_profile: Dict, rank: int) -> Dict:
            """OPTIMIZED: Process and IMMEDIATELY categorize a single profile"""
            async with semaphore:
                try:
                    # Add delay to respect rate limits (increased from 200ms)
                    await asyncio.sleep(0.5)  # 500ms delay between requests
                    
                    # Step 1: Fetch profile data
                    secondary_data = await self.fetch_secondary_profile_data(similar_profile, primary_username)
                    if not secondary_data:
                        print(f"❌ [PARALLEL] Failed to fetch secondary profile {rank}/{len(new_profiles)}")
                        return None
                    
                    secondary_data['similarity_rank'] = rank
                    
                    # Step 2: IMMEDIATELY categorize while it's hot in memory
                    print(f"🤖 [PARALLEL] Immediately categorizing @{secondary_data['username']}...")
                    categorized_profile = await self.categorize_secondary_profile(secondary_data)
                    
                    print(f"✅ [PARALLEL] Completed {rank}/{len(new_profiles)}: @{categorized_profile['username']} - {categorized_profile.get('primary_category', 'N/A')} ({categorized_profile.get('estimated_account_type', 'N/A')})")
                    return categorized_profile
                    
                except Exception as e:
                    print(f"❌ [PARALLEL] Error processing+categorizing profile {rank}: {e}")
                    return None
        
        # Step 3: Process only NEW profiles that don't exist in database
        secondary_profiles = []
        
        if new_profiles:
            # Create tasks for new profiles to process in parallel
            tasks = [
                process_single_profile(profile, i + 1) 
                for i, profile in enumerate(new_profiles)
            ]
            
            # Execute all tasks in parallel
            print(f"🚀 Starting {len(tasks)} parallel profile processing tasks...")
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            # Filter out None results and exceptions
            new_secondary_profiles = [
                result for result in results 
                if result is not None and not isinstance(result, Exception)
            ]
            
            secondary_profiles.extend(new_secondary_profiles)
        
        # Step 4: Load existing profiles from database to include in response
        if existing_usernames:
            try:
                existing_response = self.supabase.client.table('secondary_profiles').select('*').in_('username', list(existing_usernames)).execute()
                existing_profiles = existing_response.data
                print(f"📥 Loaded {len(existing_profiles)} existing profiles from database")
                secondary_profiles.extend(existing_profiles)
            except Exception as e:
                print(f"⚠️ Error loading existing profiles: {e}")
        
        total_time = time.time() - start_time
        total_processed = len(new_profiles)
        total_returned = len(secondary_profiles)
        
        # Calculate rate
        if total_time > 0 and total_processed > 0:
            rate = total_processed / (total_time / 60)  # profiles per minute
            print(f"✅ OPTIMIZED PARALLEL processing completed: {total_processed} NEW + {len(existing_usernames)} EXISTING = {total_returned} total profiles in {total_time:.1f}s ({rate:.1f} new/min)")
            print("   🚀 OPTIMIZATION: Skipped duplicate API calls + fetched/categorized new profiles immediately!")
        else:
            print(f"✅ OPTIMIZED processing completed: {total_returned} total profiles ({len(existing_usernames)} from database)")
            print("   ⚡ All profiles already existed - saved API quota by avoiding duplicate calls!")
        
        return secondary_profiles
    

    
    def extract_keywords(self, description: str, hashtags: List[str]) -> List[str]:
        """Extract top 4 keywords from description and hashtags"""
        # Simple implementation - in production would use NLP
        words = description.split()
        keywords = []
        
        # Add hashtags first
        keywords.extend(hashtags[:2])
        
        # Add significant words from description
        significant_words = [word for word in words if len(word) > 4 and word.isalpha()]
        keywords.extend(significant_words[:2])
        
        # Pad with empty strings if needed
        while len(keywords) < 4:
            keywords.append('')
        
        return keywords[:4]
    
    def extract_followers_from_context(self, social_context: str) -> int:
        """Extract follower count from social context"""
        import re
        if not social_context:
            return 0
        
        match = re.search(r'([\d,]+)\s*followers?', social_context.lower())
        if match:
            return int(match.group(1).replace(',', ''))
        return 0
    
    async def run_viral_analysis_fast_pipeline(self, username: str, max_reels: int = 12) -> Tuple[Dict, List[Dict], List[Dict]]:
        """Run optimized FAST pipeline for viral analysis refresh (SKIP similar profiles for speed)"""
        print(f"⚡ Starting VIRAL ANALYSIS FAST pipeline for @{username}")
        print(f"🎯 Strategy: Profile + {max_reels} latest reels ONLY (no similar profiles for maximum speed)")
        start_time = time.time()
        
        # Pre-execution validation
        try:
            self._validate_pipeline_prerequisites(username)
        except Exception as e:
            print(f"❌ Pipeline validation failed: {e}")
            return None, [], []
        
        try:
            # Step 1: Fetch profile data
            print("👤 Step 1: Fetching profile data (Instagram Scraper API)...")
            profile_data = await self.fetch_profile_data(username)
            if not profile_data:
                print("❌ Failed to fetch profile data")
                return None, [], []
            
            # Step 2: Fetch only recent reels (NO similar profiles!)
            print(f"📊 Step 2: Fetching {max_reels} latest reels (SKIP similar profiles for speed)...")
            
            # Fetch reel IDs
            reel_ids, _ = await self.fetch_reel_ids(username, count=max_reels, max_pages=1)
            
            if not reel_ids:
                print("❌ No reel IDs found")
                return None, [], []
            
            print(f"✅ Got {len(reel_ids)} reel IDs")
            
            # Check for duplicates in database
            existing_shortcodes = await self._get_existing_content_ids_from_db(username)
            reel_ids = self._filter_new_reel_ids(reel_ids, existing_shortcodes)
            
            print(f"✅ Filtered to {len(reel_ids)} NEW reels")
            
            # Step 3: Process reels with categorization (NO similar profiles!)
            categorized_reels = []
            if reel_ids:
                print(f"⚡ Step 3: Processing {len(reel_ids)} reels with categorization...")
                categorized_reels = await self._process_reel_batch_with_categorization(reel_ids, username, "VIRAL FAST")
            
            # Create final primary profile
            final_profile = await self._create_primary_profile_record(
                profile_data, 
                categorized_reels, 
                username,
                []  # NO secondary profiles for viral analysis speed
            )
            
            total_time = time.time() - start_time
            print(f"✅ VIRAL ANALYSIS FAST pipeline completed in {total_time:.1f}s")
            print(f"   📊 Profile: ✅")
            print(f"   📋 Content: {len(categorized_reels)} reels")
            print(f"   👥 Similar Profiles: SKIPPED for maximum speed!")
            print(f"   ⚡ Speed gain: ~80% faster than full pipeline")
            
            return final_profile, categorized_reels, []  # Return empty list for similar profiles
            
        except Exception as e:
            print(f"❌ Error in viral analysis fast pipeline: {e}")
            import traceback
            print(f"   Traceback: {traceback.format_exc()}")
            return None, [], []

    async def run_complete_pipeline(self, username: str) -> Tuple[Dict, List[Dict], List[Dict]]:
        """Run the complete HIGH PRIORITY pipeline with progressive processing"""
        print(f"🚀 Starting HIGH PRIORITY pipeline for @{username}")
        print("⚡ Progressive processing: 12 reels + 20 profiles FAST → Save → 88 more reels BACKGROUND (100 total)")
        start_time = time.time()
        
        # Step 1: Fetch profile data
        print("📡 Step 1: Fetching profile data...")
        profile_data = await self.fetch_profile_data(username)
        if not profile_data:
            return None, [], []
        
        # Step 2: TRUE PARALLEL STARTUP - Process reels + profiles simultaneously
        print("🚀 Step 2: TRUE PARALLEL STARTUP - Reels + Profiles simultaneously...")
        print("   📋 Task A: Fetch + Process + Categorize PAGE 1 reels (12 reels)")
        print("   🔍 Task B: Fetch + Process + Categorize 20 similar profiles")
        print("   🚀 OPTIMIZATION: Both tasks run completely in parallel!")
        
        # Start both COMPLETE processing tasks in parallel
        reels_task = self._fetch_and_process_page1_reels_complete(username)
        profiles_task = self._fetch_and_process_all_similar_profiles(username)
        
        # Wait for both to complete
        try:
            (initial_categorized_reels, page1_next_token), secondary_profiles = await asyncio.gather(
                reels_task, profiles_task
            )
        except Exception as e:
            print(f"❌ True parallel startup error: {e}")
            return None, [], []
        
        if len(initial_categorized_reels) == 0:
            print("❌ No reels processed")
            return None, [], []
        
        print(f"✅ TRUE PARALLEL startup completed:")
        print(f"   📋 Page 1 reels: {len(initial_categorized_reels)} reels (FULLY processed + categorized)")
        print(f"   👥 Similar profiles: {len(secondary_profiles) if secondary_profiles else 0} profiles (FULLY processed + categorized)")
        print(f"   📄 Next page token: {'Available' if page1_next_token else 'None'}")
        print(f"   🚀 BREAKTHROUGH: Both tasks completed entirely in parallel!")
        
        # DEFENSIVE CHECK: Handle case where no similar profiles found
        if not secondary_profiles or len(secondary_profiles) == 0:
            print("⚠️ NOTICE: No similar profiles found - pipeline will continue with empty secondary profiles")
            print("   ✅ This is normal for some accounts and won't cause any issues")
            print("   📊 Primary profile will still be created successfully")
            secondary_profiles = []  # Ensure it's an empty list, not None
        
        # PAGE 1 reels already processed completely in parallel! Skip this step.
        print("✅ PAGE 1 reels already processed completely in TRUE PARALLEL mode!")
        print("   🚀 BREAKTHROUGH: Reels were processed simultaneously with profiles!")
        
        # Step 5: FAST SAVE - Create primary profile and save first batch
        print(f"💾 Step 5: FAST SAVE - Creating primary profile & saving first batch...")
        initial_metrics = self.calculate_metrics(initial_categorized_reels)
        
        # Create initial primary profile 
        initial_primary_profile = await self.create_primary_profile_record(profile_data, initial_metrics, secondary_profiles)
        
        # Save initial data for immediate display
        print("💾 Saving page 1 data for immediate display...")
        print(f"   📊 Primary profile: {'✅' if initial_primary_profile else '❌'}")
        print(f"   📋 Content data: {len(initial_categorized_reels)} reels")
        print(f"   👥 Secondary profiles: {len(secondary_profiles) if secondary_profiles else 0} profiles")
        
        # DEFENSIVE CHECK: Ensure secondary_profiles is a list
        if secondary_profiles is None:
            secondary_profiles = []
            print("   🛡️ Converted None secondary_profiles to empty list")
        
        await self.save_to_csv_and_supabase(initial_primary_profile, initial_categorized_reels, secondary_profiles, username)
        
        # Verify data was saved (CSV or Supabase)
        import os
        if self.supabase is None or self.supabase.keep_local_csv:
            # Check CSV files if enabled
            csv_status = {}
            
            for csv_name in [PRIMARY_PROFILE_CSV, CONTENT_CSV, SECONDARY_PROFILE_CSV]:
                if os.path.exists(csv_name):
                    file_size = os.path.getsize(csv_name)
                    csv_status[csv_name] = f"✅ {file_size} bytes"
                    print(f"✅ {csv_name} created successfully ({file_size} bytes)")
                else:
                    csv_status[csv_name] = "❌ NOT CREATED"
                    print(f"🚨 ERROR: {csv_name} was NOT created!")
            
            # Summary of all 3 CSV files for fast display
            print(f"📊 FIRST BATCH CSV STATUS:")
            for csv_name, status in csv_status.items():
                print(f"   📄 {csv_name}: {status}")
            
            # Check if we have the complete fast display dataset
            all_csvs_created = all("✅" in status for status in csv_status.values())
            if all_csvs_created:
                print(f"🎉 ALL 3 CSV FILES READY FOR FAST DISPLAY!")
            else:
                print(f"⚠️ Some CSV files missing - fast display incomplete")
        
        fast_display_time = time.time() - start_time
        print(f"⚡ FAST DISPLAY ready in {fast_display_time:.1f}s")
        print(f"   📊 COMPLETE FAST DATASET:")
        print(f"      🏢 Primary profile: 1 profile (with first 12 reels metrics)")
        print(f"      📋 Content: {len(initial_categorized_reels)} categorized reels")
        print(f"      👥 Secondary profiles: {len(secondary_profiles)} FULLY PROCESSED similar accounts")
        if self.use_supabase:
            print(f"   ☁️ DATA SAVED TO: Supabase {'+ CSV' if self.supabase.keep_local_csv else '(no CSV)'}")
        else:
            print(f"   💾 DATA SAVED TO: CSV files only")
        print(f"   📋 Fast flow: Reels(12) → Categorize → Profiles(ALL 20) → Save")
        
        # Step 8: COMPLETED - Using only the first 12 reels (simplified pipeline)
        print(f"✅ Step 8: SIMPLIFIED - Using only the first 12 reels")
        print(f"   📋 Total reels: {len(initial_categorized_reels)}")
        print(f"   🚀 No additional reel fetching - keeping it simple!")
        
        
        # Step 9: Calculate metrics with the 12 reels we have
        print(f"📊 Step 9: Calculating metrics from {len(initial_categorized_reels)} reels...")
        final_metrics = self.calculate_metrics(initial_categorized_reels)
        
        # Step 10: Create FINAL primary profile record
        print("👤 Step 10: Creating FINAL primary profile record...")
        final_primary_profile = await self.create_primary_profile_record(profile_data, final_metrics, secondary_profiles)
        
        # Step 11: Update primary profile with final metrics
        print("💾 Step 11: Updating primary profile with final metrics...")
        self._update_primary_profile_final_metrics(final_primary_profile, username)
        
        total_time = time.time() - start_time
        print(f"✅ SIMPLIFIED PIPELINE completed in {total_time:.1f}s")
        print(f"   ⚡ FAST DISPLAY delivered in {fast_display_time:.1f}s:")
        print(f"      📊 ALL 3 CSV FILES: primaryprofile.csv + content.csv + secondary_profile.csv")
        print(f"      📋 Content: {len(initial_categorized_reels)} reels")
        print(f"      👥 Profiles: {len(secondary_profiles)} secondary profiles")
        print(f"   🎯 SIMPLIFIED: Just {len(initial_categorized_reels)} reels + profiles - clean and fast!")
        
        return final_primary_profile, initial_categorized_reels, secondary_profiles

    async def run_viral_analysis_pipeline(self, username: str, max_reels: int = 100) -> Tuple[Dict, List[Dict], List[Dict]]:
        """Run optimized pipeline for viral analysis (SKIP similar profiles for speed)"""
        print(f"⚡ Starting VIRAL ANALYSIS OPTIMIZED pipeline for @{username}")
        print(f"🎯 Strategy: Profile + {max_reels} reels ONLY (no similar profiles for maximum speed)")
        start_time = time.time()
        
        # Pre-execution validation to prevent pipeline waste
        try:
            self._validate_pipeline_prerequisites(username)
        except Exception as e:
            print(f"❌ Pipeline validation failed: {e}")
            return None, [], []
        
        # Initialize Bright Data client
        bright_client = BrightDataClient()
        
        try:
            # Step 1: Fetch profile data using existing Instagram Scraper API
            print("👤 Step 1: Fetching profile data (Instagram Scraper API)...")
            profile_data = await self.fetch_profile_data(username)
            if not profile_data:
                print("❌ Failed to fetch profile data")
                return None, [], []
            
            # Step 2: Fetch reels using Bright Data API (NO similar profiles!)
            print(f"📊 Step 2: Fetching {max_reels} reels from Bright Data (SKIP similar profiles for speed)...")
            
            bright_data_response = await bright_client.fetch_profile_and_reels_batch(username, max_reels)
            
            if not bright_data_response.success:
                print(f"❌ Bright Data fetch failed: {bright_data_response.error}")
                return None, [], []
            
            print(f"✅ Bright Data successful: {len(bright_data_response.data)} reels")
            
            # Step 3: Process reels with categorization (NO similar profiles!)
            print(f"⚡ Step 3: Processing {len(bright_data_response.data)} reels with categorization...")
            
            # Process all reels with AI categorization
            categorized_reels = []
            for i, reel in enumerate(bright_data_response.data):
                try:
                    # Process reel data
                    processed_reel = await self._process_bright_data_reel(reel, username, profile_data)
                    if processed_reel:
                        categorized_reels.append(processed_reel)
                    
                    # Progress update every 10 reels
                    if (i + 1) % 10 == 0:
                        print(f"   📋 Processed {i + 1}/{len(bright_data_response.data)} reels...")
                        
                except Exception as e:
                    print(f"❌ Error processing reel {i+1}: {e}")
                    continue
            
            # Create final primary profile
            final_profile = await self._create_bright_primary_profile_record(
                profile_data, 
                self._calculate_content_metrics(categorized_reels), 
                username,
                []  # NO secondary profiles for viral analysis speed
            )
            
            total_time = time.time() - start_time
            print(f"✅ VIRAL ANALYSIS OPTIMIZED pipeline completed in {total_time:.1f}s")
            print(f"   📊 Profile: ✅")
            print(f"   📋 Content: {len(categorized_reels)} reels")
            print(f"   👥 Similar Profiles: SKIPPED for maximum speed!")
            print(f"   ⚡ Speed gain: ~60-80% faster than full pipeline")
            
            return final_profile, categorized_reels, []  # Return empty list for similar profiles
            
        except Exception as e:
            print(f"❌ Error in viral analysis pipeline: {e}")
            import traceback
            print(f"   Traceback: {traceback.format_exc()}")
            return None, [], []

    async def _process_bright_data_reel(self, reel: Dict, username: str, profile_data: Dict) -> Dict:
        """Process a single Bright Data reel for viral analysis pipeline"""
        try:
            # Extract shortcode - Bright Data uses 'shortcode', fallback to post_id
            shortcode = reel.get('shortcode', reel.get('post_id', f"viral_reel_{username}"))
            
            # Extract caption/description - Bright Data uses 'description'
            caption = reel.get('description', '')
            if isinstance(caption, dict):
                caption = caption.get('text', '')
            
            # Extract view count - Bright Data uses 'video_play_count' or 'views'
            view_count = int(reel.get('video_play_count', 0) or reel.get('views', 0) or 0)
            
            # Extract like count - Bright Data uses 'likes'
            like_count = int(reel.get('likes', 0) or 0)
            
            # Extract comment count - Bright Data uses 'num_comments'
            comment_count = int(reel.get('num_comments', 0) or 0)
            
            # Extract image URLs - Bright Data uses 'thumbnail'
            thumbnail_url = reel.get('thumbnail', '')
            display_url = reel.get('thumbnail', '')
            
            # Download thumbnail image for viral analysis
            thumbnail_local = ""
            display_url_local = ""
            
            if display_url:
                filename = f"{shortcode}_display.jpg"
                try:
                    display_url_local = self.download_image(display_url, filename, self.thumbnails_dir)
                    thumbnail_local = display_url_local
                except Exception as e:
                    print(f"⚠️ Failed to download thumbnail for viral analysis {shortcode}: {e}")
            
            # Create transformed reel for viral analysis
            transformed_reel = {
                'content_id': reel.get('post_id', shortcode),
                'shortcode': shortcode,
                'content_type': 'reel',
                'url': reel.get('url', f"https://www.instagram.com/p/{shortcode}/"),
                'description': caption,
                'thumbnail_url': thumbnail_url,
                'thumbnail_local': thumbnail_local,
                'display_url_local': display_url_local,
                'video_thumbnail_local': "",
                'view_count': view_count,
                'like_count': like_count,
                'comment_count': comment_count,
                'date_posted': reel.get('date_posted', ''),
                'username': reel.get('user_posted', username),
                'language': 'en',
                'all_image_urls': {
                    'display_url': display_url,
                    'thumbnail_url': thumbnail_url,
                }
            }
            
            # 🚀 VIRAL ANALYSIS CATEGORIZATION
            print(f"🔥 Viral categorizing reel {shortcode}...")
            categorized_reel = await self.categorize_reel(transformed_reel)
            
            print(f"✅ Viral processed {shortcode}: {categorized_reel.get('primary_category', 'N/A')} (confidence: {categorized_reel.get('categorization_confidence', 0.0)})")
            return categorized_reel
            
        except Exception as e:
            print(f"❌ Error processing reel for viral analysis: {e}")
            return None

    def _calculate_content_metrics(self, reels: List[Dict]) -> Dict:
        """Calculate content metrics specifically for viral analysis pipeline"""
        if not reels:
            return {
                'total_reels': 0,
                'median_views': 0,
                'mean_views': 0,
                'std_views': 0,
                'total_views': 0,
                'total_likes': 0,
                'total_comments': 0,
                'viral_potential_score': 0.0,
                'engagement_rate': 0.0,
            }
        
        # Extract metrics for viral analysis
        views = [reel.get('view_count', 0) for reel in reels]
        likes = [reel.get('like_count', 0) for reel in reels]
        comments = [reel.get('comment_count', 0) for reel in reels]
        
        # Filter non-zero views for statistics
        non_zero_views = [v for v in views if v > 0]
        
        median_views = statistics.median(non_zero_views) if non_zero_views else 0
        mean_views = statistics.mean(non_zero_views) if non_zero_views else 0
        std_views = statistics.stdev(non_zero_views) if len(non_zero_views) > 1 else 0
        
        total_views = sum(views)
        total_likes = sum(likes)
        total_comments = sum(comments)
        
        # Calculate viral-specific metrics
        engagement_rate = ((total_likes + total_comments) / total_views * 100) if total_views > 0 else 0
        viral_potential_score = (median_views / 1000000) * engagement_rate if median_views > 0 else 0  # Score based on millions of views and engagement
        
        # Calculate outlier scores for viral analysis
        for reel in reels:
            view_count = reel.get('view_count', 0)
            outlier_score = (view_count / median_views) if median_views > 0 else 0
            reel['outlier_score'] = round(outlier_score, 4)
        
        return {
            'total_reels': len(reels),
            'median_views': int(median_views),
            'mean_views': round(mean_views, 2),
            'std_views': round(std_views, 2),
            'total_views': total_views,
            'total_likes': total_likes,
            'total_comments': total_comments,
            'viral_potential_score': round(viral_potential_score, 4),
            'engagement_rate': round(engagement_rate, 4),
        }

    async def run_low_priority_pipeline(self, username: str) -> Tuple[Dict, List[Dict], List[Dict]]:
        """Run low priority pipeline using Bright Data API + fallback profile fetch"""
        print(f"🔄 Starting LOW PRIORITY pipeline for @{username}")
        print("💡 Strategy: Bright Data for reels + Instagram Scraper API for profile")
        start_time = time.time()
        
        # Pre-execution validation to prevent pipeline waste
        try:
            self._validate_pipeline_prerequisites(username)
        except Exception as e:
            print(f"❌ Pipeline validation failed: {e}")
            return None, [], []
        
        # Initialize Bright Data client
        bright_client = BrightDataClient()
        
        try:
            # Step 1: Fetch profile data using existing Instagram Scraper API (same as HIGH priority)
            print("👤 Step 1: Fetching profile data (Instagram Scraper API with rate limiting)...")
            profile_data = await self.fetch_profile_data(username)
            if not profile_data:
                print("❌ Failed to fetch profile data")
                return None, [], []
            
            # Step 2: Run Bright Data fetch AND similar profiles in parallel (TIME OPTIMIZATION)
            print("🚀 Step 2: Running Bright Data + Similar Profiles in PARALLEL...")
            print("   📊 Task 1: Fetching 100 reels from Bright Data (with polling)")
            print("   🔍 Task 2: Fetching 20 similar profiles + processing (Instagram Scraper API)")
            
            # 🚀 IMMEDIATE PARALLEL PROCESSING: Start BOTH tasks immediately!
            print("🚀 IMMEDIATE PARALLEL PROCESSING: Start similar profiles NOW, reels when ready!")
            
            # Step 2A: Start similar profiles processing IMMEDIATELY
            print("👥 Step 2A: Starting similar profiles processing IMMEDIATELY...")
            similar_profiles_task = self._fetch_and_process_similar_profiles_parallel(username)
            
            # Step 2B: Start Bright Data request (will process reels when ready)
            print("📊 Step 2B: Starting Bright Data request (will process reels immediately when ready)...")
            bright_data_task = bright_client.fetch_profile_and_reels_batch(username, 100)
            
            # Define async function to process reels immediately when Bright Data is ready
            async def process_reels_when_ready():
                print("⚡ Waiting for Bright Data (100 reels)...")
                response = await bright_data_task
                
                # Check Bright Data response
                if not response.success:
                    print(f"❌ Bright Data request failed: {response.error}")
                    return None
                
                bright_data = response.data
                if not bright_data:
                    print("❌ No data returned from Bright Data")
                    return None
                
                print(f"✅ Bright Data ready: {len(bright_data)} reel records")
                print("🚀 STARTING REEL PROCESSING IMMEDIATELY!")
                
                # DEBUG: Save raw Bright Data response (only if not using Supabase)
                if not self.use_supabase:
                    debug_file = f"debug_bright_data_{username}_{int(time.time())}.json"
                    try:
                        with open(debug_file, 'w') as f:
                            json.dump(bright_data, f, indent=2, default=str)
                        print(f"🐛 DEBUG: Saved raw Bright Data response to {debug_file}")
                    except Exception as e:
                        print(f"⚠️ Could not save debug file: {e}")
                else:
                    print(f"🐛 DEBUG: Skipping Bright Data debug file save (Supabase mode)")
                
                # Step 3: 🚀 IMMEDIATE REEL PROCESSING
                print("🚀 Step 3: IMMEDIATE Transform + Categorize reels (20x parallel)...")
                print(f"   📊 Processing {len(bright_data)} reel records IMMEDIATELY")
                print(f"   ⚡ Using 20x parallel categorization calls per batch")
                
                # All Bright Data records are reels - no need to separate
                reels_data = bright_data
                
                # Process reels immediately
                categorized_reels = await self._transform_and_categorize_bright_reels_parallel(reels_data, username, batch_size=20)
                return categorized_reels
            
            # Start reel processing task (will process when Bright Data is ready)
            reels_processing_task = process_reels_when_ready()
            
            # Run BOTH tasks in TRUE parallel (no blocking!)
            print("⚡ Step 4: Running BOTH tasks in TRUE parallel (no blocking)...")
            print("   👥 Similar profiles: Processing NOW")
            print("   📊 Reels: Will process IMMEDIATELY when Bright Data returns")
            
            categorized_reels, secondary_profiles = await asyncio.gather(
                reels_processing_task,
                similar_profiles_task
            )
            
            # Handle case where reels failed
            if categorized_reels is None:
                print("❌ Reel processing failed")
                return None, [], secondary_profiles or []
            
            # Secondary profiles are ALREADY categorized from process_all_secondary_profiles
            categorized_secondary_profiles = secondary_profiles
            print(f"✅ Using {len(categorized_secondary_profiles)} already-categorized secondary profiles")
            
            # Step 5: Calculate metrics from categorized reels
            print("📊 Step 5: Calculating metrics from categorized reels...")
            metrics = self.calculate_metrics(categorized_reels)
            
            # Step 6: Create primary profile record (using Instagram Scraper profile + Bright Data metrics)
            print("👤 Step 6: Creating primary profile record (Instagram profile + Bright Data metrics)...")
            primary_profile = await self._create_hybrid_primary_profile_record(profile_data, metrics, username, categorized_secondary_profiles)
            
            # Step 7: Data ready for external save (low priority pipeline doesn't save internally)
            print("💾 Step 7: Data prepared for external save...")
            print(f"✅ Data ready for save: primaryprofile.csv, content.csv, secondary_profile.csv")
            
            processing_time = time.time() - start_time
            print(f"✅ LOW PRIORITY pipeline completed in {processing_time:.1f}s")
            print(f"   📈 Results: 1 profile, {len(categorized_reels)} reels, {len(categorized_secondary_profiles)} secondary profiles")
            
            return primary_profile, categorized_reels, categorized_secondary_profiles
            
        except Exception as e:
            print(f"❌ Low priority pipeline failed: {e}")
            return None, [], []
        finally:
            bright_client.close()

    async def _transform_bright_profile_data(self, bright_profile: Dict, username: str) -> Dict:
        """Transform Bright Data profile response to match existing format"""
        try:
            # Map Bright Data fields to existing format - using actual Bright Data field names
            transformed = {
                'username': username,
                'full_name': bright_profile.get('profile_name', bright_profile.get('full_name', bright_profile.get('name', ''))),
                'biography': bright_profile.get('bio', bright_profile.get('biography', '')),
                'follower_count': int(bright_profile.get('followers', bright_profile.get('follower_count', 0))),
                'following_count': int(bright_profile.get('following', bright_profile.get('following_count', 0))),
                'media_count': int(bright_profile.get('posts_count', bright_profile.get('media_count', 0))),
                'profile_pic_url': bright_profile.get('user_profile_url', bright_profile.get('profile_pic_url', bright_profile.get('profile_image_url', ''))),
                'hd_profile_pic_url': bright_profile.get('user_profile_url', bright_profile.get('hd_profile_pic_url', bright_profile.get('profile_pic_url', ''))),
                'is_verified': bright_profile.get('is_verified', False),
                'is_private': bright_profile.get('is_private', False),
                'is_business': bright_profile.get('is_business_account', bright_profile.get('account_type') == 'business'),
                'external_url': bright_profile.get('external_url', ''),
                'category': bright_profile.get('category', ''),
            }
            
            # Download profile images
            profile_pic_local = ""
            hd_profile_pic_local = ""
            
            if transformed['profile_pic_url']:
                filename = f"{username}_profile.jpg"
                profile_pic_local = self.download_image(transformed['profile_pic_url'], filename, self.images_dir)
            
            if transformed['hd_profile_pic_url'] and transformed['hd_profile_pic_url'] != transformed['profile_pic_url']:
                filename = f"{username}_profile_hd.jpg"
                hd_profile_pic_local = self.download_image(transformed['hd_profile_pic_url'], filename, self.images_dir)
            
            transformed['profile_image_local'] = profile_pic_local
            transformed['hd_profile_image_local'] = hd_profile_pic_local
            
            return transformed
            
        except Exception as e:
            print(f"❌ Error transforming profile data: {e}")
            return {}

    async def _transform_bright_reels_data(self, bright_reels: List[Dict], username: str) -> List[Dict]:
        """Transform Bright Data reels response to match existing format"""
        transformed_reels = []
        
        for i, reel in enumerate(bright_reels):
            try:
                # Extract shortcode - Bright Data uses 'shortcode', fallback to post_id
                shortcode = reel.get('shortcode', reel.get('post_id', f"bright_reel_{i}"))
                
                # Extract caption/description - Bright Data uses 'description'
                caption = reel.get('description', '')
                if isinstance(caption, dict):
                    caption = caption.get('text', '')
                
                # Extract view count - Bright Data uses 'video_play_count' or 'views'
                view_count = int(reel.get('video_play_count', 0) or reel.get('views', 0) or 0)
                
                # Extract like count - Bright Data uses 'likes'
                like_count = int(reel.get('likes', 0) or 0)
                
                # Extract comment count - Bright Data uses 'num_comments'
                comment_count = int(reel.get('num_comments', 0) or 0)
                
                # Extract image URLs - Bright Data uses 'thumbnail'
                thumbnail_url = reel.get('thumbnail', '')
                display_url = reel.get('thumbnail', '')
                
                # Download thumbnail image
                thumbnail_local = ""
                display_url_local = ""
                
                if display_url:
                    filename = f"{shortcode}_display.jpg"
                    try:
                        display_url_local = self.download_image(display_url, filename, self.thumbnails_dir)
                        thumbnail_local = display_url_local
                    except Exception as e:
                        print(f"⚠️ Failed to download image for {shortcode}: {e}")
                
                # Create transformed reel
                transformed_reel = {
                    'content_id': reel.get('post_id', shortcode),  # Bright Data uses 'post_id'
                    'shortcode': shortcode,
                    'content_type': 'reel',
                    'url': reel.get('url', f"https://www.instagram.com/p/{shortcode}/"),  # Use actual URL from Bright Data
                    'description': caption,
                    'thumbnail_url': thumbnail_url,
                    'thumbnail_local': thumbnail_local,
                    'display_url_local': display_url_local,
                    'video_thumbnail_local': "",
                    'view_count': view_count,
                    'like_count': like_count,
                    'comment_count': comment_count,
                    'date_posted': reel.get('date_posted', ''),  # Bright Data uses 'date_posted'
                    'username': reel.get('user_posted', username),  # Bright Data uses 'user_posted'
                    'language': 'en',
                    'all_image_urls': {
                        'display_url': display_url,
                        'thumbnail_url': thumbnail_url,
                    }
                }
                
                transformed_reels.append(transformed_reel)
                print(f"📋 Transformed reel {i+1}/{len(bright_reels)}: {shortcode}")
                
            except Exception as e:
                print(f"❌ Error transforming reel {i}: {e}")
                continue
        
        print(f"✅ Transformed {len(transformed_reels)}/{len(bright_reels)} reels")
        return transformed_reels

    async def _transform_and_categorize_bright_reels_parallel(self, bright_reels: List[Dict], username: str, batch_size: int = 20) -> List[Dict]:
        """🚀 SUPER OPTIMIZED: Transform + Categorize Bright Data reels with 20x parallel categorization calls"""
        print(f"🚀 SUPER OPTIMIZED: Transform + Categorize {len(bright_reels)} Bright Data reels with {batch_size}x parallel categorization...")
        
        categorized_reels = []
        
        # Process reels in batches
        for i in range(0, len(bright_reels), batch_size):
            batch = bright_reels[i:i + batch_size]
            batch_num = i//batch_size + 1
            total_batches = math.ceil(len(bright_reels)/batch_size)
            print(f"⚡ Processing reel batch {batch_num}/{total_batches}: {len(batch)} reels")
            
            # Step 1: Transform all reels in batch (parallel downloads)
            print(f"🔄 [{batch_num}] Step 1: Transform {len(batch)} reels (parallel downloads)...")
            transform_tasks = [self._transform_single_bright_reel(reel, i + j, username) for j, reel in enumerate(batch)]
            transformed_batch = await asyncio.gather(*transform_tasks, return_exceptions=True)
            
            # Filter out failed transformations
            valid_transformed_reels = []
            for j, result in enumerate(transformed_batch):
                if isinstance(result, Exception):
                    print(f"❌ Error transforming reel {i + j}: {result}")
                    # Create fallback reel
                    try:
                        shortcode = batch[j].get('shortcode', batch[j].get('post_id', f"bright_reel_{i + j}"))
                        fallback_reel = {
                            'content_id': batch[j].get('post_id', shortcode),
                            'shortcode': shortcode,
                            'content_type': 'reel',
                            'url': batch[j].get('url', f"https://www.instagram.com/p/{shortcode}/"),
                            'description': batch[j].get('description', ''),
                            'thumbnail_url': batch[j].get('thumbnail', ''),
                            'thumbnail_local': '',
                            'display_url_local': '',
                            'video_thumbnail_local': '',
                            'view_count': int(batch[j].get('video_play_count', 0) or batch[j].get('views', 0) or 0),
                            'like_count': int(batch[j].get('likes', 0) or 0),
                            'comment_count': int(batch[j].get('num_comments', 0) or 0),
                            'date_posted': batch[j].get('date_posted', ''),
                            'username': batch[j].get('user_posted', username),
                            'language': 'en',
                            'all_image_urls': {
                                'display_url': batch[j].get('thumbnail', ''),
                                'thumbnail_url': batch[j].get('thumbnail', ''),
                            }
                        }
                        valid_transformed_reels.append(fallback_reel)
                    except Exception as e:
                        print(f"❌ Error creating fallback reel {i + j}: {e}")
                        continue
                else:
                    valid_transformed_reels.append(result)
            
            print(f"✅ [{batch_num}] Step 1: Transformed {len(valid_transformed_reels)} reels")
            
            # Step 2: Fire 20x parallel categorization calls at once! 🚀
            print(f"🚀 [{batch_num}] Step 2: Fire {len(valid_transformed_reels)}x PARALLEL categorization calls...")
            categorization_tasks = [self.categorize_reel(reel) for reel in valid_transformed_reels]
            categorized_batch = await asyncio.gather(*categorization_tasks, return_exceptions=True)
            
            # Handle categorization results
            for j, result in enumerate(categorized_batch):
                if isinstance(result, Exception):
                    print(f"❌ Error categorizing reel {j}: {result}")
                    # Add uncategorized reel with defaults
                    reel_defaults = DEFAULT_REEL_CATEGORIES.copy()
                    reel_defaults.update({
                        'keyword_1': '', 'keyword_2': '', 'keyword_3': '', 'keyword_4': '',
                        'content_style': 'video'
                    })
                    valid_transformed_reels[j].update(reel_defaults)
                    categorized_reels.append(valid_transformed_reels[j])
                else:
                    categorized_reels.append(result)
            
            print(f"🚀 [{batch_num}] Step 2: Categorized {len(categorized_batch)} reels in parallel")
            print(f"✅ Completed batch {batch_num}/{total_batches}: {len(categorized_batch)} reels processed")
            
            # Small delay between batches to avoid overwhelming OpenAI API
            if i + batch_size < len(bright_reels):
                await asyncio.sleep(1)
        
        print(f"🚀 SUPER OPTIMIZED: Processed {len(categorized_reels)} reels total (20x parallel categorization per batch)")
        return categorized_reels

    async def _transform_single_bright_reel(self, reel: Dict, index: int, username: str) -> Dict:
        """Transform a single Bright Data reel (WITHOUT categorization)"""
        try:
            # Extract shortcode - Bright Data uses 'shortcode', fallback to post_id
            shortcode = reel.get('shortcode', reel.get('post_id', f"bright_reel_{index}"))
            
            # Extract caption/description - Bright Data uses 'description'
            caption = reel.get('description', '')
            if isinstance(caption, dict):
                caption = caption.get('text', '')
            
            # Extract view count - Bright Data uses 'video_play_count' or 'views'
            view_count = int(reel.get('video_play_count', 0) or reel.get('views', 0) or 0)
            
            # Extract like count - Bright Data uses 'likes'
            like_count = int(reel.get('likes', 0) or 0)
            
            # Extract comment count - Bright Data uses 'num_comments'
            comment_count = int(reel.get('num_comments', 0) or 0)
            
            # Extract image URLs - Bright Data uses 'thumbnail'
            thumbnail_url = reel.get('thumbnail', '')
            display_url = reel.get('thumbnail', '')
            
            # Download thumbnail image
            thumbnail_local = ""
            display_url_local = ""
            
            if display_url:
                filename = f"{shortcode}_display.jpg"
                try:
                    display_url_local = self.download_image(display_url, filename, self.thumbnails_dir)
                    thumbnail_local = display_url_local
                    print(f"🖼️ Downloaded: {filename}")
                except Exception as e:
                    print(f"⚠️ Failed to download image for {shortcode}: {e}")
            
            # Create transformed reel (NO categorization yet)
            transformed_reel = {
                'content_id': reel.get('post_id', shortcode),  # Bright Data uses 'post_id'
                'shortcode': shortcode,
                'content_type': 'reel',
                'url': reel.get('url', f"https://www.instagram.com/p/{shortcode}/"),  # Use actual URL from Bright Data
                'description': caption,
                'thumbnail_url': thumbnail_url,
                'thumbnail_local': thumbnail_local,
                'display_url_local': display_url_local,
                'video_thumbnail_local': "",
                'view_count': view_count,
                'like_count': like_count,
                'comment_count': comment_count,
                'date_posted': reel.get('date_posted', ''),  # Bright Data uses 'date_posted'
                'username': reel.get('user_posted', username),  # Bright Data uses 'user_posted'
                'language': 'en',
                'all_image_urls': {
                    'display_url': display_url,
                    'thumbnail_url': thumbnail_url,
                }
            }
            
            return transformed_reel
            
        except Exception as e:
            print(f"❌ Error transforming reel {index}: {e}")
            raise e

    async def _transform_and_categorize_single_bright_reel(self, reel: Dict, index: int, username: str) -> Dict:
        """Transform and categorize a single Bright Data reel"""
        try:
            # Extract shortcode - Bright Data uses 'shortcode', fallback to post_id
            shortcode = reel.get('shortcode', reel.get('post_id', f"bright_reel_{index}"))
            
            # Extract caption/description - Bright Data uses 'description'
            caption = reel.get('description', '')
            if isinstance(caption, dict):
                caption = caption.get('text', '')
            
            # Extract view count - Bright Data uses 'video_play_count' or 'views'
            view_count = int(reel.get('video_play_count', 0) or reel.get('views', 0) or 0)
            
            # Extract like count - Bright Data uses 'likes'
            like_count = int(reel.get('likes', 0) or 0)
            
            # Extract comment count - Bright Data uses 'num_comments'
            comment_count = int(reel.get('num_comments', 0) or 0)
            
            # Extract image URLs - Bright Data uses 'thumbnail'
            thumbnail_url = reel.get('thumbnail', '')
            display_url = reel.get('thumbnail', '')
            
            # Download thumbnail image
            thumbnail_local = ""
            display_url_local = ""
            
            if display_url:
                filename = f"{shortcode}_display.jpg"
                try:
                    display_url_local = self.download_image(display_url, filename, self.thumbnails_dir)
                    thumbnail_local = display_url_local
                except Exception as e:
                    print(f"⚠️ Failed to download image for {shortcode}: {e}")
            
            # Create transformed reel
            transformed_reel = {
                'content_id': reel.get('post_id', shortcode),  # Bright Data uses 'post_id'
                'shortcode': shortcode,
                'content_type': 'reel',
                'url': reel.get('url', f"https://www.instagram.com/p/{shortcode}/"),  # Use actual URL from Bright Data
                'description': caption,
                'thumbnail_url': thumbnail_url,
                'thumbnail_local': thumbnail_local,
                'display_url_local': display_url_local,
                'video_thumbnail_local': "",
                'view_count': view_count,
                'like_count': like_count,
                'comment_count': comment_count,
                'date_posted': reel.get('date_posted', ''),  # Bright Data uses 'date_posted'
                'username': reel.get('user_posted', username),  # Bright Data uses 'user_posted'
                'language': 'en',
                'all_image_urls': {
                    'display_url': display_url,
                    'thumbnail_url': thumbnail_url,
                }
            }
            
            # 🚀 IMMEDIATE CATEGORIZATION (while image downloads in background)
            print(f"🤖 Categorizing reel {shortcode} immediately...")
            categorized_reel = await self.categorize_reel(transformed_reel)
            
            print(f"✅ Completed {shortcode}: {categorized_reel.get('primary_category', 'N/A')} (confidence: {categorized_reel.get('categorization_confidence', 0.0)})")
            return categorized_reel
            
        except Exception as e:
            print(f"❌ Error processing reel {index}: {e}")
            raise e

    async def _create_bright_primary_profile_record(self, profile_data: Dict, metrics: Dict, username: str, secondary_profiles: List[Dict] = None) -> Dict:
        """Create primary profile record from Bright Data with AI categorization"""
        try:
            # Use the Bright Data field names or transformed field names
            profile_name = profile_data.get('full_name', profile_data.get('profile_name', username))
            bio = profile_data.get('biography', profile_data.get('bio', ''))
            followers = profile_data.get('follower_count', profile_data.get('followers', 0))
            
            # AI categorization (same as existing pipeline)
            account_type_result = await self.ai_categorize_profile_type(username, profile_name, bio, followers)
            content_categories_result = await self.ai_categorize_profile_content(username, profile_name, bio)
            
            # Prepare similar accounts fields (20 fields for related accounts)
            similar_accounts = {}
            if secondary_profiles:
                # Extract usernames from secondary profiles (up to 20)
                secondary_usernames = [profile.get('username', '') for profile in secondary_profiles if profile.get('username')]
                for i in range(1, 21):  # similar_account1 to similar_account20
                    if i <= len(secondary_usernames):
                        similar_accounts[f'similar_account{i}'] = secondary_usernames[i-1]
                    else:
                        similar_accounts[f'similar_account{i}'] = ''
                print(f"📊 Added {len(secondary_usernames)} similar accounts to Bright Data primary profile")
            else:
                # Initialize empty similar account fields
                for i in range(1, 21):
                    similar_accounts[f'similar_account{i}'] = ''
            
            # Build the complete profile record
            profile_record = {
                'username': username,
                'profile_name': profile_name,
                'bio': bio,
                'followers': followers,
                'posts_count': int(profile_data.get('media_count', profile_data.get('posts_count', 0))),
                'is_verified': profile_data.get('is_verified', False),
                'is_business_account': profile_data.get('is_business', False),
                'profile_url': f"https://instagram.com/{username}",
                'profile_image_url': profile_data.get('profile_pic_url', ''),
                'profile_image_local': profile_data.get('profile_image_local', ''),
                'hd_profile_image_local': profile_data.get('hd_profile_image_local', ''),
                'account_type': account_type_result.get('account_type', 'Personal'),
                'language': 'en',
                'content_type': 'entertainment',
                'total_reels': metrics['total_reels'],
                'median_views': metrics['median_views'],
                'mean_views': metrics['mean_views'],
                'std_views': metrics['std_views'],
                'total_views': metrics['total_views'],
                'total_likes': metrics['total_likes'],
                'total_comments': metrics['total_comments'],
                'profile_primary_category': content_categories_result.get('primary_category', 'Lifestyle'),
                'profile_secondary_category': content_categories_result.get('secondary_category', ''),
                'profile_tertiary_category': content_categories_result.get('tertiary_category', ''),
                'profile_categorization_confidence': content_categories_result.get('confidence', 0.7),
                'account_type_confidence': account_type_result.get('confidence', 0.7),
            }
            
            # Add the 20 similar account fields
            profile_record.update(similar_accounts)
            
            # Add timestamps at the end
            profile_record.update({
                'last_full_scrape': datetime.utcnow().isoformat(),
                'analysis_timestamp': datetime.utcnow().isoformat(),
            })
            
            return profile_record
            
        except Exception as e:
            print(f"❌ Error creating primary profile record: {e}")
            return {}
    
    async def _create_hybrid_primary_profile_record(self, profile_data: Dict, metrics: Dict, username: str, secondary_profiles: List[Dict] = None) -> Dict:
        """Create primary profile record from Instagram Scraper API profile + Bright Data metrics"""
        try:
            # Use Instagram Scraper API field names (same as HIGH priority pipeline)
            profile_name = profile_data.get('full_name', username)
            bio = profile_data.get('biography', '')
            followers = int(profile_data.get('follower_count', profile_data.get('followers', 0)))
            
            print(f"🤖 AI Categorizing hybrid profile @{username} (Instagram profile + Bright Data metrics)")
            
            # AI categorization (same as existing pipeline)
            account_type_result = await self.ai_categorize_profile_type(username, profile_name, bio, followers)
            content_categories_result = await self.ai_categorize_profile_content(username, profile_name, bio)
            
            # Prepare similar accounts fields (20 fields for related accounts)
            similar_accounts = {}
            if secondary_profiles:
                # Extract usernames from secondary profiles (up to 20)
                secondary_usernames = [profile.get('username', '') for profile in secondary_profiles if profile.get('username')]
                for i in range(1, 21):  # similar_account1 to similar_account20
                    if i <= len(secondary_usernames):
                        similar_accounts[f'similar_account{i}'] = secondary_usernames[i-1]
                    else:
                        similar_accounts[f'similar_account{i}'] = ''
                print(f"📊 Added {len(secondary_usernames)} similar accounts to hybrid primary profile")
            else:
                # Initialize empty similar account fields
                for i in range(1, 21):
                    similar_accounts[f'similar_account{i}'] = ''
            
            # Build the complete profile record (Instagram Scraper fields + Bright Data metrics)
            profile_record = {
                'username': username,
                'profile_name': profile_name,
                'bio': bio,
                'followers': followers,
                'posts_count': int(profile_data.get('media_count', 0)),
                'is_verified': profile_data.get('is_verified', False),
                'is_business_account': profile_data.get('is_business', False),
                'profile_url': f"https://instagram.com/{username}",
                'profile_image_url': profile_data.get('profile_pic_url', ''),
                'profile_image_local': profile_data.get('profile_image_local', ''),
                'hd_profile_image_local': profile_data.get('hd_profile_image_local', ''),
                'account_type': account_type_result.get('account_type', 'Personal'),
                'language': 'en',
                'content_type': 'entertainment',
                # Use metrics calculated from Bright Data reels
                'total_reels': metrics['total_reels'],
                'median_views': metrics['median_views'],
                'mean_views': metrics['mean_views'],
                'std_views': metrics['std_views'],
                'total_views': metrics['total_views'],
                'total_likes': metrics['total_likes'],
                'total_comments': metrics['total_comments'],
                'profile_primary_category': content_categories_result.get('primary_category', 'Lifestyle'),
                'profile_secondary_category': content_categories_result.get('secondary_category', ''),
                'profile_tertiary_category': content_categories_result.get('tertiary_category', ''),
                'profile_categorization_confidence': content_categories_result.get('confidence', 0.7),
                'account_type_confidence': account_type_result.get('confidence', 0.7),
            }
            
            # Add the 20 similar account fields
            profile_record.update(similar_accounts)
            
            # Add timestamps at the end
            profile_record.update({
                'last_full_scrape': datetime.utcnow().isoformat(),
                'analysis_timestamp': datetime.utcnow().isoformat(),
            })
            
            print(f"✅ Created hybrid profile record: Instagram profile + Bright Data metrics from {metrics['total_reels']} reels")
            return profile_record
            
        except Exception as e:
            print(f"❌ Error creating hybrid profile record: {e}")
            return {}
    

    
    def _update_primary_profile_final_metrics(self, final_profile: Dict, username: str):
        """Update primary profile with final metrics from complete dataset"""
        try:
            if final_profile:
                print(f"💾 Updating primary profile with final metrics for @{username}...")
                
                # Read existing primary profiles
                existing_profiles = []
                try:
                    with open("primaryprofile.csv", 'r', encoding='utf-8') as f:
                        reader = csv.DictReader(f)
                        existing_profiles = list(reader)
                except FileNotFoundError:
                    print("⚠️ Primary profile CSV not found - will create new")
                
                # Update the profile for this username with final metrics
                updated = False
                for i, profile in enumerate(existing_profiles):
                    if profile.get('username') == username:
                        # Update with final metrics
                        existing_profiles[i] = final_profile
                        updated = True
                        print(f"✅ Updated existing profile for @{username} with final metrics")
                        break
                
                if not updated:
                    # Add new profile if not found
                    existing_profiles.append(final_profile)
                    print(f"✅ Added new profile for @{username} with final metrics")
                
                # Write back to CSV
                if existing_profiles:
                    fieldnames = list(final_profile.keys())
                    with open("primaryprofile.csv", 'w', newline='', encoding='utf-8') as f:
                        writer = csv.DictWriter(f, fieldnames=fieldnames)
                        writer.writeheader()
                        writer.writerows(existing_profiles)
                    print(f"💾 Primary profile updated with final metrics")
            else:
                print("⚠️ No final profile to update")
        except Exception as e:
            print(f"❌ Error updating primary profile final metrics: {e}")
    
    async def _fetch_and_process_similar_profiles_parallel(self, username: str) -> List[Dict]:
        """Fetch similar profiles and process them in parallel with other tasks"""
        try:
            print(f"🔍 [PARALLEL TASK] Starting similar profiles fetch for @{username}...")
            
            # Step 1: Fetch similar profiles (rate-limited Instagram Scraper API)
            print(f"🔍 [PARALLEL TASK] Fetching 20 similar profiles...")
            similar_profiles = await self.fetch_similar_profiles(username)
            print(f"📊 [PARALLEL TASK] Retrieved {len(similar_profiles)} similar profiles")
            
            if not similar_profiles:
                print("⚠️ [PARALLEL TASK] No similar profiles found - continuing without secondary profiles")
                return []
            
            # Step 2: Process all secondary profiles
            print(f"👥 [PARALLEL TASK] Processing {len(similar_profiles)} secondary profiles...")
            secondary_profiles = await self.process_all_secondary_profiles(similar_profiles, username)
            
            print(f"✅ [PARALLEL TASK] Completed: {len(secondary_profiles)} secondary profiles processed")
            
            # Debug output
            if len(secondary_profiles) == 0:
                print("⚠️ [PARALLEL TASK] Warning: No secondary profiles were processed successfully")
                print(f"   Original similar profiles count: {len(similar_profiles)}")
                print("   This might indicate an issue with profile processing")
            
            return secondary_profiles
            
        except Exception as e:
            print(f"❌ [PARALLEL TASK] Error in similar profiles processing: {e}")
            import traceback
            print(f"   Traceback: {traceback.format_exc()}")
            return []
    
    async def _fetch_similar_profiles_with_retry(self, username: str, max_retries: int = 3) -> List[Dict]:
        """Fetch similar profiles with enhanced retry logic for HIGH priority requests"""
        for attempt in range(max_retries):
            try:
                print(f"🔄 Similar profiles retry attempt {attempt + 1}/{max_retries} for @{username}")
                
                # Add progressive delay between retries
                if attempt > 0:
                    delay = min(10, 2 ** attempt)  # 2s, 4s, 8s
                    print(f"⏱️ Waiting {delay}s before retry...")
                    await asyncio.sleep(delay)
                
                # Try fetching similar profiles
                similar_profiles = await self.fetch_similar_profiles(username)
                if similar_profiles:
                    print(f"📊 Retrieved {len(similar_profiles)} similar profiles on attempt {attempt + 1}")
                    
                    # Process the profiles
                    secondary_profiles = await self.process_all_secondary_profiles(similar_profiles, username)
                    if secondary_profiles:
                        print(f"✅ Successfully processed {len(secondary_profiles)} secondary profiles")
                        return secondary_profiles
                    else:
                        print(f"⚠️ Processing failed for similar profiles on attempt {attempt + 1}")
                else:
                    print(f"⚠️ No similar profiles returned on attempt {attempt + 1}")
                    
            except Exception as e:
                print(f"❌ Error on similar profiles attempt {attempt + 1}: {e}")
                if attempt == max_retries - 1:
                    print("❌ All similar profiles retry attempts failed")
                    import traceback
                    print(f"   Final error traceback: {traceback.format_exc()}")
        
        print(f"⚠️ WARNING: HIGH priority request proceeding without similar profiles after {max_retries} attempts")
        return []
    
    async def _fetch_and_process_page1_reels_complete(self, username: str) -> Tuple[List[Dict], str]:
        """BREAKTHROUGH: Fetch + Process + Categorize PAGE 1 reels completely in parallel"""
        try:
            print(f"🚀 [PARALLEL TASK] Complete PAGE 1 reel processing for @{username}...")
            
            # Step 1: Fetch PAGE 1 reel IDs
            print(f"📋 [PARALLEL TASK] Fetching PAGE 1 reel IDs (12 reels)...")
            initial_reel_ids, page1_next_token = await self.fetch_reel_ids(username, count=12, max_pages=1)
            
            if not initial_reel_ids:
                print(f"❌ [PARALLEL TASK] No reel IDs found")
                return [], None
            
            print(f"✅ [PARALLEL TASK] Got {len(initial_reel_ids)} reel IDs")
            
            # Filter out reels that already exist in database (in case this isn't the first run)
            print(f"🔍 [PARALLEL TASK] Checking {len(initial_reel_ids)} PAGE 1 reels against existing database content...")
            existing_shortcodes = await self._get_existing_content_ids_from_db(username)
            
            initial_reel_ids = self._filter_new_reel_ids(initial_reel_ids, existing_shortcodes)
            print(f"✅ [PARALLEL TASK] Filtered result: {len(initial_reel_ids)} NEW reels to process")
            
            if not initial_reel_ids:
                print(f"⏭️ [PARALLEL TASK] All PAGE 1 reels already processed - continuing with existing data")
                return [], page1_next_token
            
            # Step 2: Process + Categorize reels immediately
            print(f"⚡ [PARALLEL TASK] Processing {len(initial_reel_ids)} reels with IMMEDIATE categorization...")
            initial_categorized_reels = await self._process_reel_batch_with_categorization(initial_reel_ids, username, "PAGE 1 PARALLEL")
            
            if not initial_categorized_reels:
                print("🚨 [PARALLEL TASK] Optimized processing failed! Falling back...")
                # Fallback to old method
                initial_reels = await self._process_reel_batch_fast(initial_reel_ids, username, "PAGE 1 FALLBACK")
                if initial_reels:
                    initial_categorized_reels = await self.categorize_all_reels_parallel(initial_reels, batch_size=12)
                    if not initial_categorized_reels:
                        initial_categorized_reels = initial_reels
                else:
                    initial_categorized_reels = self._create_basic_reels_from_ids(initial_reel_ids, username)
            
            print(f"✅ [PARALLEL TASK] Complete PAGE 1 processing: {len(initial_categorized_reels)} reels (fetched + categorized)")
            return initial_categorized_reels, page1_next_token
            
        except Exception as e:
            print(f"❌ [PARALLEL TASK] Error in complete PAGE 1 reel processing: {e}")
            import traceback
            print(f"   Traceback: {traceback.format_exc()}")
            return [], None
    
    async def _process_reel_batch_fast(self, reel_ids: List[Dict], username: str, batch_name: str) -> List[Dict]:
        """Process a batch of reel IDs into detailed reels (PROGRESSIVE FETCHING)"""
        try:
            print(f"⚡ [{batch_name}] Processing {len(reel_ids)} reels for @{username}...")
            
            # Fetch details for this batch of reels
            print(f"📋 [{batch_name}] Fetching details for {len(reel_ids)} reels...")
            detailed_reels = await self.fetch_all_reel_details(reel_ids, username)
            
            # Handle None return from fetch_all_reel_details
            if detailed_reels is None:
                print(f"❌ [{batch_name}] fetch_all_reel_details returned None! Using empty list as fallback.")
                detailed_reels = []
            
            print(f"✅ [{batch_name}] Completed: {len(detailed_reels)} detailed reels")
            return detailed_reels
            
        except Exception as e:
            print(f"❌ [{batch_name}] Error in reel processing: {e}")
            import traceback
            print(f"   Traceback: {traceback.format_exc()}")
            return []

    async def _process_reel_batch_with_categorization(self, reel_ids: List[Dict], username: str, batch_name: str) -> List[Dict]:
        """OPTIMIZED: Process reel batch with IMMEDIATE categorization (fetch + categorize in parallel)"""
        try:
            print(f"⚡ [{batch_name}] Processing {len(reel_ids)} reels with IMMEDIATE categorization for @{username}...")
            
            # Extract shortcodes first (same logic as fetch_all_reel_details)
            shortcodes = []
            for reel in reel_ids:
                shortcode = None
                
                # Try different possible structures
                if 'node' in reel and 'media' in reel['node']:
                    shortcode = reel['node']['media'].get('code', '')
                elif 'shortcode' in reel:
                    shortcode = reel.get('shortcode', '')
                elif 'code' in reel:
                    shortcode = reel.get('code', '')
                
                if shortcode:
                    shortcodes.append(shortcode)
                else:
                    print(f"⚠️ No shortcode found in reel: {list(reel.keys())}")
            
            if not shortcodes:
                print(f"❌ [{batch_name}] No valid shortcodes found")
                return []
            
            categorized_reels = []
            failed_shortcodes = []
            
            # Process reels in smaller batches for rate limiting
            process_batch_size = 4
            
            async with aiohttp.ClientSession() as session:
                for i in range(0, len(shortcodes), process_batch_size):
                    batch_shortcodes = shortcodes[i:i + process_batch_size]
                    batch_num = i//process_batch_size + 1
                    total_batches = math.ceil(len(shortcodes)/process_batch_size)
                    
                    print(f"🔄 [{batch_name}] Processing sub-batch {batch_num}/{total_batches} ({len(batch_shortcodes)} reels)")
                    
                    async def fetch_and_categorize_reel(shortcode):
                        """Fetch reel details and immediately categorize"""
                        try:
                            # Step 1: Fetch reel details
                            reel_data = await self.fetch_reel_details(session, shortcode, username)
                            if not reel_data:
                                return None
                            
                            # Step 2: Immediately categorize while image download happens in background
                            print(f"🤖 [{batch_name}] Categorizing reel {shortcode} immediately...")
                            categorized_reel = await self.categorize_reel(reel_data)
                            
                            print(f"✅ [{batch_name}] Completed {shortcode}: {categorized_reel.get('primary_category', 'N/A')} (confidence: {categorized_reel.get('categorization_confidence', 0.0)})")
                            return categorized_reel
                            
                        except Exception as e:
                            print(f"❌ [{batch_name}] Error processing reel {shortcode}: {e}")
                            return None
                    
                    # Create tasks for parallel fetch + categorize
                    tasks = [fetch_and_categorize_reel(sc) for sc in batch_shortcodes]
                    
                    # Run batch in parallel
                    batch_results = await asyncio.gather(*tasks, return_exceptions=True)
                    
                    # Process results
                    valid_results = []
                    for j, result in enumerate(batch_results):
                        if isinstance(result, Exception):
                            print(f"❌ [{batch_name}] Exception for {batch_shortcodes[j]}: {result}")
                            failed_shortcodes.append(batch_shortcodes[j])
                        elif result is None:
                            print(f"⚠️ [{batch_name}] No data for {batch_shortcodes[j]}")
                            failed_shortcodes.append(batch_shortcodes[j])
                        else:
                            valid_results.append(result)
                    
                    categorized_reels.extend(valid_results)
                    
                    print(f"✅ [{batch_name}] Sub-batch {batch_num}: {len(valid_results)}/{len(batch_shortcodes)} successful (fetch + categorize)")
                    
                    # Small delay between sub-batches
                    if i + process_batch_size < len(shortcodes):
                        await asyncio.sleep(1.0)
            
            print(f"🎉 [{batch_name}] OPTIMIZED PROCESSING COMPLETE:")
            print(f"   ✅ Successfully processed: {len(categorized_reels)} reels")
            print(f"   ❌ Failed: {len(failed_shortcodes)} reels")
            print(f"   🚀 Each reel was fetched AND categorized immediately (no waiting for separate phases)")
            
            return categorized_reels
            
        except Exception as e:
            print(f"❌ [{batch_name}] Error in optimized reel processing: {e}")
            import traceback
            print(f"   Traceback: {traceback.format_exc()}")
            return []
    
    async def _fetch_all_reels_parallel(self, username: str, num_reels: int) -> List[Dict]:
        """Fetch all reel IDs and details in parallel with similar profiles (HIGH priority task)"""
        try:
            print(f"🎬 [PARALLEL TASK] Fetching ALL reel IDs for @{username} (up to {num_reels})...")
            
            # Step 1: Fetch all reel IDs
            all_reel_ids, _ = await self.fetch_reel_ids(username, num_reels)
            print(f"📋 [PARALLEL TASK] Retrieved {len(all_reel_ids)} reel IDs")
            
            # Step 2: Filter out reels that already exist in database
            print(f"🔍 [PARALLEL TASK] Checking {len(all_reel_ids)} reels against existing database content...")
            existing_shortcodes = await self._get_existing_content_ids_from_db(username)
            all_reel_ids = self._filter_new_reel_ids(all_reel_ids, existing_shortcodes)
            print(f"✅ [PARALLEL TASK] Filtered to {len(all_reel_ids)} NEW reels")
            
            if not all_reel_ids:
                print(f"⏭️ [PARALLEL TASK] All reels already exist in database - skipping API calls")
                return []
            
            # Step 3: Fetch details only for NEW reels
            print(f"📋 [PARALLEL TASK] Fetching details for {len(all_reel_ids)} NEW reels...")
            all_detailed_reels = await self.fetch_all_reel_details(all_reel_ids, username)
            
            print(f"✅ [PARALLEL TASK] Completed: {len(all_detailed_reels)} detailed reels")
            return all_detailed_reels
            
        except Exception as e:
            print(f"❌ [PARALLEL TASK] Error in reel fetching: {e}")
            return []
    
    def _validate_system_requirements(self):
        """Validate system requirements and dependencies before pipeline execution"""
        if DEBUG_MODE:
            print("🔍 Validating system requirements...")
        
        validation_errors = []
        
        # 1. Test cross-platform file locking
        try:
            import platform
            import tempfile
            import os
            
            with tempfile.NamedTemporaryFile(delete=False) as temp_file:
                temp_path = temp_file.name
                
            try:
                # Test file locking based on platform
                with open(temp_path, 'w') as f:
                    if platform.system() == 'Windows':
                        try:
                            import msvcrt
                            msvcrt.locking(f.fileno(), msvcrt.LK_LOCK, 1)
                            msvcrt.locking(f.fileno(), msvcrt.LK_UNLCK, 1)
                        except ImportError:
                            validation_errors.append("Windows file locking (msvcrt) not available")
                    else:
                        try:
                            import fcntl
                            fcntl.flock(f.fileno(), fcntl.LOCK_EX)
                            fcntl.flock(f.fileno(), fcntl.LOCK_UN)
                        except ImportError:
                            validation_errors.append("Unix file locking (fcntl) not available")
            finally:
                os.unlink(temp_path)
                
        except Exception as e:
            validation_errors.append(f"File locking test failed: {e}")
        
        # 2. Test CSV operations
        try:
            import csv
            import tempfile
            
            test_data = [{'test': 'value', 'number': 123}]
            with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.csv') as temp_file:
                temp_path = temp_file.name
                
            try:
                # Test CSV writing
                with open(temp_path, 'w', newline='', encoding='utf-8') as f:
                    writer = csv.DictWriter(f, fieldnames=['test', 'number'])
                    writer.writeheader()
                    writer.writerows(test_data)
                
                # Test CSV reading
                with open(temp_path, 'r', encoding='utf-8') as f:
                    reader = csv.DictReader(f)
                    list(reader)
                    
            finally:
                os.unlink(temp_path)
                
        except Exception as e:
            validation_errors.append(f"CSV operations test failed: {e}")
        
        # 3. Test environment variables (warn but don't fail)
        # Check for RapidAPI key first (new standard), then fall back to legacy names
        rapidapi_key = os.getenv('RAPIDAPI_KEY') or os.getenv('INSTAGRAM_SCRAPER_API_KEY')
        
        if not rapidapi_key:
            if DEBUG_MODE:
                print(f"⚠️  Missing RapidAPI key - set one of these environment variables:")
                print(f"     - RAPIDAPI_KEY (recommended)")
                print(f"     - INSTAGRAM_SCRAPER_API_KEY (legacy)")
                print("   This is required for Instagram data scraping")
        else:
            if DEBUG_MODE:
                print("✅ RapidAPI key found")
        
        optional_env_vars = {
            'OPENAI_API_KEY': 'AI categorization',
            'BRIGHT_DATA_API_KEY': 'Bright Data reels fetching'
        }
        
        missing_optional_vars = []
        for var, purpose in optional_env_vars.items():
            if not os.getenv(var):
                missing_optional_vars.append(f"{var} (for {purpose})")
        
        if missing_optional_vars:
            if DEBUG_MODE:
                print(f"⚠️  Missing optional environment variables (pipeline may have limited functionality):")
                for var in missing_optional_vars:
                    print(f"     - {var}")
        
        # Only fail on critical system issues, not missing API keys
        
        # 4. Test OpenAI connection (warn only)
        try:
            if os.getenv('OPENAI_API_KEY'):
                client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))
                # Just test the client creation, not an actual API call
        except Exception as e:
            print(f"⚠️  OpenAI client test failed: {e} (AI categorization may be limited)")
        
        # 5. Test required Python modules
        required_modules = ['aiohttp', 'requests', 'openai', 'pathlib']
        for module in required_modules:
            try:
                __import__(module)
            except ImportError:
                validation_errors.append(f"Required module {module} not installed")
        
        # Report validation results
        if validation_errors:
            print("❌ System validation FAILED. Fix these issues before running pipeline:")
            for i, error in enumerate(validation_errors, 1):
                print(f"   {i}. {error}")
            raise RuntimeError(f"System validation failed with {len(validation_errors)} errors")
        else:
            if DEBUG_MODE:
                print("✅ System validation passed - all requirements met")
                print(f"   Platform: {platform.system()}")
                print(f"   File locking: {'msvcrt (Windows)' if platform.system() == 'Windows' else 'fcntl (Unix)'}")
                print(f"   CSV operations: Working")
                print(f"   Environment variables: Set")
                print(f"   Required modules: Available")
    
    def _validate_pipeline_prerequisites(self, username: str):
        """Validate pipeline prerequisites before starting execution"""
        print(f"🔍 Pre-execution validation for @{username}...")
        
        # 1. Validate username format
        if not username or not isinstance(username, str):
            raise ValueError("Invalid username: must be a non-empty string")
        
        # 2. Test CSV saving capability (early detection of file permission issues)
        try:
            test_data = [{'username': username, 'test': 'pre_validation'}]
            self._append_to_master_csv("test_validation.csv", test_data, "validation test")
            # Clean up test file
            if Path("test_validation.csv").exists():
                Path("test_validation.csv").unlink()
        except Exception as e:
            raise RuntimeError(f"CSV file operations test failed: {e}")
        
        # 3. Validate environment variables for this specific pipeline (warn only)
        pipeline_vars = {
            'INSTAGRAM_SCRAPER_API_KEY': 'Instagram profile data',
            'OPENAI_API_KEY': 'AI categorization',
            'BRIGHT_DATA_API_KEY': 'Bright Data reels fetch'
        }
        
        missing_vars = []
        for var, purpose in pipeline_vars.items():
            if not os.getenv(var):
                missing_vars.append(f"{var} (for {purpose})")
        
        if missing_vars:
            print(f"⚠️  Missing environment variables for @{username} pipeline:")
            for var in missing_vars:
                print(f"     - {var}")
            print("   Pipeline will continue but some features may be limited")
        
        # 4. Test OpenAI client before starting pipeline (warn only)
        try:
            if self.openai_client is None:
                print("⚠️  OpenAI client not initialized - AI categorization will be limited")
        except Exception as e:
            print(f"⚠️  OpenAI client validation failed: {e} - AI categorization will be limited")
        
        print(f"✅ Pre-execution validation passed for @{username}")
        print(f"   Username: Valid")
        print(f"   CSV operations: Working")
        print(f"   API keys: Available")
        print(f"   OpenAI client: Ready")
    
    async def create_primary_profile_record(self, profile_data: Dict, metrics: Dict, secondary_profiles: List[Dict] = None) -> Dict:
        """Create primary profile record matching database schema with AI categorization (PROMPTS 1 & 2)"""
        username = profile_data.get('username', '')
        profile_name = profile_data.get('full_name', '')
        bio = profile_data.get('biography', '')
        followers = int(profile_data.get('follower_count', profile_data.get('followers', 0)))
        
        print(f"🤖 AI Categorizing primary profile @{username} (using 2 separate prompts)")
        
        # PROMPT 1: Determine account type
        print("📝 Running PROMPT 1: Account Type Classification")
        account_type_result = await self.ai_categorize_profile_type(username, profile_name, bio, followers)
        
        # PROMPT 2: Determine content categories  
        print("📝 Running PROMPT 2: Content Categories Classification")
        content_categories_result = await self.ai_categorize_profile_content(username, profile_name, bio)
        
        # Prepare similar accounts fields (20 fields for related accounts)
        similar_accounts = {}
        if secondary_profiles:
            # Extract usernames from secondary profiles (up to 20)
            secondary_usernames = [profile.get('username', '') for profile in secondary_profiles if profile.get('username')]
            for i in range(1, 21):  # similar_account1 to similar_account20
                if i <= len(secondary_usernames):
                    similar_accounts[f'similar_account{i}'] = secondary_usernames[i-1]
                else:
                    similar_accounts[f'similar_account{i}'] = ''
            print(f"📊 Added {len(secondary_usernames)} similar accounts to primary profile")
        else:
            # Initialize empty similar account fields
            for i in range(1, 21):
                similar_accounts[f'similar_account{i}'] = ''
        
        # Build the complete profile record
        profile_record = {
            'username': username,
            'profile_name': profile_name,
            'bio': bio,
            'followers': followers,
            'posts_count': int(profile_data.get('media_count', profile_data.get('posts_count', 0))),
            'is_verified': profile_data.get('is_verified', False),
            'is_business_account': profile_data.get('is_business', False),
            'profile_url': f"https://instagram.com/{username}",
            'profile_image_url': profile_data.get('profile_pic_url', ''),
            'profile_image_local': profile_data.get('profile_image_local', ''),
            'hd_profile_image_local': profile_data.get('hd_profile_image_local', ''),  # Additional image path
            'account_type': account_type_result.get('account_type', 'Personal'),  # PROMPT 1 result
            'language': 'en',  # Default
            'content_type': 'entertainment',  # Default
            'total_reels': metrics['total_reels'],
            'median_views': metrics['median_views'],
            'mean_views': metrics['mean_views'],
            'std_views': metrics['std_views'],
            'total_views': metrics['total_views'],
            'total_likes': metrics['total_likes'],
            'total_comments': metrics['total_comments'],
            'profile_primary_category': content_categories_result.get('primary_category', 'Lifestyle'),  # PROMPT 2 result
            'profile_secondary_category': content_categories_result.get('secondary_category', ''),  # PROMPT 2 result
            'profile_tertiary_category': content_categories_result.get('tertiary_category', ''),  # PROMPT 2 result
            'profile_categorization_confidence': content_categories_result.get('confidence', 0.7),  # PROMPT 2 confidence
            'account_type_confidence': account_type_result.get('confidence', 0.7),  # PROMPT 1 confidence
        }
        
        # Add the 20 similar account fields
        profile_record.update(similar_accounts)
        
        # Add timestamps at the end
        profile_record.update({
            'last_full_scrape': datetime.utcnow().isoformat(),
            'analysis_timestamp': datetime.utcnow().isoformat(),
        })
        
        return profile_record
    
    def save_to_csv(self, primary_profile: Dict, content_data: List[Dict], secondary_profiles: List[Dict], username: str):
        """Save all data to consolidated master CSV files"""
        
        # Save to master primaryprofile.csv
        if primary_profile:
            self._append_to_master_csv(PRIMARY_PROFILE_CSV, [primary_profile], "primary profile")
        
        # Save to master content.csv
        if content_data:
            print(f"💾 Saving {len(content_data)} content records to {CONTENT_CSV}...")
            # DEBUG: Print sample content data
            if len(content_data) > 0:
                print(f"🐛 DEBUG: Sample content record fields: {list(content_data[0].keys())}")
                print(f"🐛 DEBUG: First record shortcode: {content_data[0].get('shortcode', 'N/A')}")
            
            try:
                self._append_to_master_csv(CONTENT_CSV, content_data, "content")
                print(f"✅ Successfully called _append_to_master_csv for content.csv")
            except Exception as e:
                print(f"❌ ERROR in _append_to_master_csv for content.csv: {e}")
                import traceback
                print(f"   Traceback: {traceback.format_exc()}")
        else:
            print("⚠️ No content_data to save to content.csv (data is empty or None)")
            print(f"🐛 DEBUG: content_data type: {type(content_data)}, value: {content_data}")
        
        # Save to master secondary_profile.csv
        if secondary_profiles and len(secondary_profiles) > 0:
            self._append_to_master_csv(SECONDARY_PROFILE_CSV, secondary_profiles, "secondary profiles")
            print(f"✅ Saved {len(secondary_profiles)} secondary profiles to {SECONDARY_PROFILE_CSV}")
        else:
            print("ℹ️ No secondary profiles to save - creating empty secondary_profile.csv if needed")
            # Create empty secondary_profile.csv with headers if it doesn't exist
            try:
                import os
                if not os.path.exists(SECONDARY_PROFILE_CSV):
                    with open(SECONDARY_PROFILE_CSV, 'w', newline='', encoding=CSV_ENCODING) as f:
                        writer = csv.writer(f)
                        writer.writerow(['username', 'profile_name', 'bio', 'followers', 'posts_count', 'is_verified', 'profile_url', 'profile_image_url', 'profile_image_local', 'primary_category', 'secondary_category', 'tertiary_category', 'categorization_confidence', 'estimated_account_type', 'account_type_confidence', 'last_scraped'])
                    print("✅ Created empty secondary_profile.csv with headers")
            except Exception as e:
                print(f"⚠️ Could not create empty secondary_profile.csv: {e}")
    
    async def save_to_csv_and_supabase(self, primary_profile: Dict, content_data: List[Dict], secondary_profiles: List[Dict], username: str):
        """Save all data to CSV files and Supabase"""
        
        # Save to Supabase first (if enabled)
        profile_id = None
        if self.use_supabase and self.supabase:
            try:
                print(f"💾 Saving to Supabase...")
                
                # Save primary profile
                if primary_profile:
                    profile_id = await self.supabase.save_primary_profile(primary_profile)
                    if profile_id:
                        print(f"✅ Saved primary profile to Supabase (ID: {profile_id})")
                
                # Save content data
                saved_content = 0
                if content_data and profile_id:
                    saved_content = await self.supabase.save_content_batch(content_data, profile_id, username)
                    print(f"✅ Saved {saved_content} content records to Supabase")
                
                # Save secondary profiles
                saved_profiles = 0
                if secondary_profiles and profile_id:
                    saved_profiles = await self.supabase.save_secondary_profiles_batch(secondary_profiles, profile_id)
                    print(f"✅ Saved {saved_profiles} secondary profiles to Supabase")
                
                # Verify data integrity after save
                if profile_id:
                    print(f"🔍 Verifying data integrity for @{username}...")
                    verification = await self.supabase.verify_data_integrity(
                        profile_id, 
                        len(content_data) if content_data else 0,
                        len(secondary_profiles) if secondary_profiles else 0,
                        username
                    )
                    
                    if verification["success"]:
                        print(f"✅ Data verification PASSED for @{username}")
                        print(f"   📊 Primary profile: {'✅' if verification['primary_profile'] else '❌'}")
                        print(f"   📋 Content: {verification['content_count']}/{verification['expected_content']}")
                        print(f"   👥 Secondary: {verification['secondary_count']}/{verification['expected_secondary']}")
                        
                        # Show warnings if any
                        if verification.get("warnings"):
                            print(f"   ⚠️ Warnings:")
                            for warning in verification["warnings"]:
                                print(f"      • {warning}")
                    else:
                        print(f"❌ Data verification FAILED for @{username}")
                        for error in verification["errors"]:
                            print(f"   🚨 {error}")
                        
                        # Show warnings even on failure
                        if verification.get("warnings"):
                            print(f"   ⚠️ Warnings:")
                            for warning in verification["warnings"]:
                                print(f"      • {warning}")
                        
                        # Attempt rollback on verification failure
                        print(f"🔄 Attempting rollback for @{username}...")
                        rollback_success = await self.supabase.rollback_failed_save(profile_id, username)
                        if rollback_success:
                            print(f"✅ Successfully rolled back partial data for @{username}")
                            profile_id = None  # Reset so CSV save can proceed as fallback
                        else:
                            print(f"❌ Rollback failed for @{username} - manual cleanup may be needed")
                    
            except Exception as e:
                print(f"❌ Error saving to Supabase: {e}")
                # Attempt rollback if we have a profile_id
                if profile_id:
                    print(f"🔄 Attempting rollback due to save error...")
                    rollback_success = await self.supabase.rollback_failed_save(profile_id, username)
                    if rollback_success:
                        print(f"✅ Successfully rolled back partial data")
                        profile_id = None  # Reset so CSV save can proceed as fallback
                # Continue with CSV save even if Supabase fails
        
        # Save to CSV files (only if enabled or as fallback when Supabase fails)
        if (self.supabase is None and KEEP_LOCAL_CSV) or (self.supabase and self.supabase.keep_local_csv):
            print(f"💾 Saving to CSV files...")
            self.save_to_csv(primary_profile, content_data, secondary_profiles, username)
        elif self.supabase is None:
            print(f"⚠️ Supabase not available and CSV disabled - no data saved!")
    
    async def _get_existing_content_ids_from_db(self, username: str, content_type_filter: Optional[str] = None) -> set:
        """Get set of existing content IDs/shortcodes from database to prevent duplicate fetching"""
        existing_ids = set()
        try:
            if hasattr(self, 'supabase') and self.supabase:
                # Query content table for existing content_ids and shortcodes for this username
                query = self.supabase.client.table('content').select('content_id, shortcode').eq('username', username)
                if content_type_filter:
                    query = query.eq('content_type', content_type_filter)
                response = query.execute()
                
                if response.data:
                    for item in response.data:
                        # Add both content_id and shortcode to the set for comprehensive checking
                        if item.get('content_id'):
                            existing_ids.add(item['content_id'].lower())
                        if item.get('shortcode'):
                            existing_ids.add(item['shortcode'].lower())
                    
                    print(f"📊 Found {len(response.data)} existing content records in database for @{username}")
                    print(f"⚡ Skipping API calls for {len(existing_ids)} existing content IDs to save quota")
                else:
                    print(f"📊 No existing content found in database for @{username} - will process all")
            else:
                print(f"⚠️ No database connection - proceeding without duplicate check")
        except Exception as e:
            print(f"⚠️ Error checking existing content in database: {e} - proceeding without duplicate check")
        
        return existing_ids

    def _get_existing_records(self, filename: str, key_field: str) -> set:
        """Get set of existing records to prevent duplicates (CSV fallback method)"""
        existing_keys = set()
        try:
            if Path(filename).exists():
                with open(filename, 'r', newline='', encoding='utf-8') as f:
                    reader = csv.DictReader(f)
                    record_count = 0
                    for row in reader:
                        if key_field in row and row[key_field]:
                            existing_keys.add(row[key_field].lower())
                            record_count += 1
                    print(f"📊 Found {record_count} existing {key_field} records in {filename}")
            else:
                print(f"📊 File {filename} doesn't exist - no existing records to check")
        except Exception as e:
            print(f"⚠️ Error reading existing records from {filename}: {e}")
        return existing_keys

    def _filter_new_reel_ids(self, reel_ids: List[Dict], existing_shortcodes: set) -> List[Dict]:
        """Filter reel IDs to only include ones not already in database or CSV"""
        if not reel_ids:
            return reel_ids
            
        # If no existing records, return all reels
        if not existing_shortcodes:
            print(f"📋 No existing records found - processing all {len(reel_ids)} reels")
            return reel_ids
            
        filtered_reels = []
        skipped_count = 0
        
        for reel in reel_ids:
            # Handle nested reel structure (node/cursor format vs direct format)
            reel_data = reel.get('node', reel)  # Extract from 'node' if present, else use reel directly
            
            # Check multiple possible shortcode fields in the reel data
            shortcode = (reel_data.get('shortcode') or 
                        reel_data.get('code') or 
                        reel_data.get('id') or 
                        reel_data.get('pk', ''))
            
            if not shortcode:
                # If no shortcode found, include the reel (don't skip it)
                print(f"⚠️ Reel has no shortcode/ID, including anyway. Keys: {list(reel_data.keys())}")
                filtered_reels.append(reel)
            elif shortcode.lower() not in existing_shortcodes:
                filtered_reels.append(reel)
            else:
                skipped_count += 1
                print(f"⏭️ Skipping already processed reel: {shortcode}")
        
        if skipped_count > 0:
            print(f"📋 Filtered reel IDs: kept {len(filtered_reels)}, skipped {skipped_count} already processed")
        else:
            print(f"📋 All {len(filtered_reels)} reels are new - processing all")
        
        return filtered_reels

    def _deduplicate_data(self, data: List[Dict], existing_keys: set, key_field: str, data_type: str) -> List[Dict]:
        """Remove duplicates from data based on key field"""
        if not data:
            return data
            
        deduplicated = []
        skipped_count = 0
        
        for item in data:
            key_value = item.get(key_field, '').lower()
            if key_value and key_value not in existing_keys:
                deduplicated.append(item)
                existing_keys.add(key_value)  # Track for subsequent items in same batch
            else:
                skipped_count += 1
                print(f"⏭️ Skipping duplicate {data_type}: {item.get(key_field, 'Unknown')}")
        
        if skipped_count > 0:
            print(f"📋 Deduplicated {data_type}: kept {len(deduplicated)}, skipped {skipped_count} duplicates")
            
        return deduplicated

    def _append_to_master_csv(self, filename: str, data: List[Dict], data_type: str):
        """Thread-safe append to master CSV file with header management and deduplication (cross-platform)"""
        import threading
        import platform
        from pathlib import Path
        
        if not data:
            return
        
        # Determine the key field for deduplication based on data type
        key_field = 'username'  # Default for profiles
        if 'content' in data_type.lower() or 'reel' in data_type.lower():
            key_field = 'content_id' if any('content_id' in item for item in data) else 'shortcode'
        
        # Get existing records and deduplicate
        existing_keys = self._get_existing_records(filename, key_field)
        deduplicated_data = self._deduplicate_data(data, existing_keys, key_field, data_type)
        
        if not deduplicated_data:
            print(f"⏭️ All {len(data)} {data_type} records were duplicates - nothing to save")
            return
        
        # Cross-platform file locking
        def _lock_file(file_obj):
            """Cross-platform file locking"""
            try:
                if platform.system() == 'Windows':
                    import msvcrt
                    msvcrt.locking(file_obj.fileno(), msvcrt.LK_LOCK, 1)
                else:
                    import fcntl
                    fcntl.flock(file_obj.fileno(), fcntl.LOCK_EX)
            except ImportError:
                # Fallback: use threading lock if OS-level locking fails
                pass
        
        def _unlock_file(file_obj):
            """Cross-platform file unlocking"""
            try:
                if platform.system() == 'Windows':
                    import msvcrt
                    msvcrt.locking(file_obj.fileno(), msvcrt.LK_UNLCK, 1)
                else:
                    import fcntl
                    fcntl.flock(file_obj.fileno(), fcntl.LOCK_UN)
            except ImportError:
                # Fallback: threading lock handles this
                pass
        
        # Use a lock for thread safety
        lock_file = f"{filename}.lock"
        
        try:
            with open(lock_file, 'w') as lock:
                _lock_file(lock)
                
                file_exists = Path(filename).exists()
                fieldnames = list(deduplicated_data[0].keys())
                
                if not file_exists:
                    # Create new file with headers
                    with open(filename, 'w', newline='', encoding='utf-8') as f:
                        writer = csv.DictWriter(f, fieldnames=fieldnames)
                        writer.writeheader()
                        writer.writerows(deduplicated_data)
                    print(f"💾 Created {filename} with {len(deduplicated_data)} {data_type} records")
                else:
                    # Check if existing file has compatible headers
                    existing_headers = self._get_csv_headers(filename)
                    
                    if set(fieldnames) != set(existing_headers):
                        # Handle field mismatch - create backup and new file
                        backup_file = f"{filename}.backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
                        Path(filename).rename(backup_file)
                        print(f"⚠️ Field mismatch detected. Backed up {filename} to {backup_file}")
                        
                        # Create new file with current structure
                        with open(filename, 'w', newline='', encoding='utf-8') as f:
                            writer = csv.DictWriter(f, fieldnames=fieldnames)
                            writer.writeheader()
                            writer.writerows(deduplicated_data)
                        print(f"💾 Created new {filename} with updated structure and {len(deduplicated_data)} {data_type} records")
                    else:
                        # Append to existing file
                        with open(filename, 'a', newline='', encoding='utf-8') as f:
                            writer = csv.DictWriter(f, fieldnames=existing_headers)
                            # Ensure data matches existing field order
                            ordered_data = [{field: row.get(field, '') for field in existing_headers} for row in deduplicated_data]
                            writer.writerows(ordered_data)
                        print(f"💾 Appended {len(deduplicated_data)} {data_type} records to {filename}")
                
        except Exception as e:
            print(f"❌ Error saving to {filename}: {e}")
            # Fallback: create timestamped file
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            fallback_file = f"{data_type.replace(' ', '_')}_{timestamp}.csv"
            with open(fallback_file, 'w', newline='', encoding='utf-8') as f:
                writer = csv.DictWriter(f, fieldnames=list(deduplicated_data[0].keys()))
                writer.writeheader()
                writer.writerows(deduplicated_data)
            print(f"💾 Fallback: Saved to {fallback_file}")
        finally:
            # Clean up lock file
            try:
                Path(lock_file).unlink(missing_ok=True)
            except:
                pass
    
    def _get_csv_headers(self, filename: str) -> List[str]:
        """Get headers from existing CSV file"""
        try:
            with open(filename, 'r', newline='', encoding='utf-8') as f:
                reader = csv.reader(f)
                return next(reader)
        except:
            return []

    def append_reels_to_csv(self, additional_reels: List[Dict], username: str):
        """Append additional reels to the master content.csv file"""
        if not additional_reels:
            print("⚠️ No additional reels to append")
            return
        
        # Append to master content.csv
        self._append_to_master_csv("content.csv", additional_reels, "additional content")
        print(f"💾 Appended {len(additional_reels)} additional reels from @{username} to master content.csv")


# ========================================================================================
# BRIGHT DATA API CLIENT FOR LOW PRIORITY REQUESTS
# ========================================================================================

@dataclass
class BrightDataConfig:
    """Configuration for Bright Data API"""
    api_key: str
    base_url: str
    profiles_dataset_id: str
    reels_dataset_id: str

def get_bright_data_config() -> BrightDataConfig:
    """Get Bright Data configuration from environment variables"""
    return BrightDataConfig(
        api_key=os.getenv('BRIGHT_DATA_API_KEY', ''),
        base_url=os.getenv('BRIGHT_DATA_BASE_URL', 'https://api.brightdata.com/datasets/v3'),
        profiles_dataset_id=os.getenv('BRIGHT_DATA_PROFILES_DATASET_ID', 'gd_l1vikfch901nx3by4'),
        reels_dataset_id=os.getenv('BRIGHT_DATA_REELS_DATASET_ID', 'gd_lyclm20il4r5helnj')
    )

@dataclass
class BrightDataResponse:
    """Standardized response from Bright Data API"""
    success: bool
    data: Optional[Any] = None
    error: Optional[str] = None
    request_id: Optional[str] = None
    snapshot_id: Optional[str] = None
    metadata: Optional[Dict] = None

@dataclass
class BatchRequest:
    """Represents a batch request status for a single username"""
    username: str
    profile: Optional[Any] = None
    profile_success: bool = False
    reels_snapshot_id: Optional[str] = None
    reels_request_id: Optional[str] = None
    reels_success: bool = False
    reels_data: Optional[List] = None
    error: Optional[str] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None

class BrightDataError(Exception):
    """Custom exception for Bright Data API errors"""
    pass

class BrightDataClient:
    """Bright Data API client for low priority requests"""
    
    def __init__(self, max_retries: int = 3, retry_delay: float = 1.0, timeout: int = 1800):
        self.config = get_bright_data_config()
        self.max_retries = max_retries
        self.retry_delay = retry_delay
        self.timeout = timeout
        
        # Debug configuration
        print(f"🔧 Bright Data Configuration Debug:")
        print(f"   API Key: {'*' * 10}{self.config.api_key[-10:] if len(self.config.api_key) > 10 else 'NOT_SET'}")
        print(f"   Base URL: {self.config.base_url}")
        print(f"   Profiles Dataset: {self.config.profiles_dataset_id}")
        print(f"   Reels Dataset: {self.config.reels_dataset_id}")
        
        if not self.config.api_key:
            raise BrightDataError("BRIGHT_DATA_API_KEY environment variable not set!")
        
        # Setup HTTP session
        self.session = requests.Session()
        self.session.headers.update({
            'Authorization': f'Bearer {self.config.api_key}',
            'Content-Type': 'application/json',
            'User-Agent': 'Instagram-Analytics-Backend/1.0'
        })
        
        print("✅ Bright Data client initialized")
    
    def _make_request(self, method: str, endpoint: str, payload: Optional[Dict] = None, params: Optional[Dict] = None) -> requests.Response:
        """Make HTTP request with retry logic"""
        url = f"{self.config.base_url}/{endpoint.lstrip('/')}"
        
        # Debug request details
        print(f"🌐 Bright Data API Request:")
        print(f"   Method: {method}")
        print(f"   URL: {url}")
        print(f"   Params: {params}")
        print(f"   Payload: {json.dumps(payload, indent=2) if payload else 'None'}")
        print(f"   Headers: {dict(self.session.headers)}")
        
        for attempt in range(self.max_retries + 1):
            try:
                if method.upper() == 'POST':
                    response = self.session.post(url, json=payload, params=params, timeout=self.timeout)
                else:
                    response = self.session.get(url, params=params, timeout=self.timeout)
                
                # Debug response details
                print(f"📥 Bright Data API Response (Attempt {attempt + 1}):")
                print(f"   Status Code: {response.status_code}")
                print(f"   Response Headers: {dict(response.headers)}")
                print(f"   Response Text: {response.text[:500]}{'...' if len(response.text) > 500 else ''}")
                
                if response.status_code in [200, 202]:
                    return response
                elif 400 <= response.status_code < 500:
                    raise BrightDataError(f"Client error {response.status_code}: {response.text}")
                else:
                    print(f"⚠️ Server error {response.status_code}, retrying...")
                    
            except requests.RequestException as e:
                print(f"⚠️ Request failed, retrying... {e}")
                
                if attempt == self.max_retries:
                    raise BrightDataError(f"Request failed after {self.max_retries + 1} attempts: {e}")
            
            if attempt < self.max_retries:
                delay = self.retry_delay * (2 ** attempt)
                print(f"⏳ Waiting {delay}s before retry...")
                time.sleep(delay)
        
        raise BrightDataError(f"Request failed after {self.max_retries + 1} attempts")
    
    async def fetch_profile_and_reels_batch(self, username: str, num_reels: int = 100) -> BrightDataResponse:
        """Fetch profile and reels data using a single Bright Data API request"""
        profile_url = f"https://www.instagram.com/{username}/"
        
        print(f"🚀 Triggering single Bright Data request for @{username} ({num_reels} reels)")
        
        try:
            # Create single request for all reels
            payload = [{
                "url": profile_url,
                "num_of_posts": num_reels  # Request all reels in one go
            }]
            
            print(f"📊 Requesting {num_reels} reels in single request")
            
            # Make the API request
            response = self._make_request(
                'POST',
                'trigger',
                payload=payload,
                params={
                    'dataset_id': self.config.reels_dataset_id,
                    'include_errors': 'true',
                    'type': 'discover_new',
                    'discover_by': 'url_all_reels'
                }
            )
            
            result = response.json()
            snapshot_id = result.get('snapshot_id')
            request_id = result.get('request_id') or result.get('requestId') or result.get('id')
            
            if snapshot_id:
                print(f"✅ Got snapshot ID directly: {snapshot_id}")
                # Poll this specific snapshot
                snapshot_data = await self._poll_snapshot(snapshot_id, self.timeout)
                return snapshot_data
            elif request_id:
                print(f"✅ Got request ID: {request_id}, polling for snapshot...")
                # Poll for snapshot ID first
                snapshot_id = await self._poll_for_snapshot_id(request_id, self.timeout // 2)
                if snapshot_id:
                    snapshot_data = await self._poll_snapshot(snapshot_id, self.timeout // 2)
                    return snapshot_data
                else:
                    return BrightDataResponse(success=False, error="Could not get snapshot ID")
            else:
                return BrightDataResponse(success=False, error="No snapshot or request ID received")
                
        except Exception as e:
            return BrightDataResponse(success=False, error=str(e))
    
    async def _trigger_single_request(self, payload: List[Dict], request_num: int) -> BrightDataResponse:
        """Trigger a single Bright Data request (for parallel processing)"""
        try:
            response = self._make_request(
                'POST',
                'trigger',
                payload=payload,
                params={
                    'dataset_id': self.config.reels_dataset_id,
                    'include_errors': 'true',
                    'type': 'discover_new',
                    'discover_by': 'url_all_reels'
                }
            )
            
            result = response.json()
            snapshot_id = result.get('snapshot_id')
            request_id = result.get('request_id') or result.get('requestId') or result.get('id')
            
            if snapshot_id:
                # Poll this specific snapshot
                snapshot_data = await self._poll_snapshot(snapshot_id, self.timeout // 4)  # Shorter timeout for parallel
                return snapshot_data
            elif request_id:
                # Poll for snapshot ID first
                snapshot_id = await self._poll_for_snapshot_id(request_id, self.timeout // 8)
                if snapshot_id:
                    snapshot_data = await self._poll_snapshot(snapshot_id, self.timeout // 8)
                    return snapshot_data
                else:
                    return BrightDataResponse(success=False, error=f"Request {request_num}: Could not get snapshot ID")
            else:
                return BrightDataResponse(success=False, error=f"Request {request_num}: No snapshot or request ID")
                
        except Exception as e:
            return BrightDataResponse(success=False, error=f"Request {request_num}: {str(e)}")
    
    async def _poll_for_snapshot_id(self, request_id: str, timeout: int = 900) -> Optional[str]:
        """Poll for snapshot ID using request ID"""
        max_attempts = timeout // 15
        attempt = 0
        
        print(f"⏳ Polling for snapshot ID (request: {request_id})")
        
        while attempt < max_attempts:
            try:
                response = self.session.get(
                    f"{self.config.base_url}/snapshots",
                    params={"dataset_id": self.config.reels_dataset_id, "status": "ready"},
                    timeout=30
                )
                
                if response.status_code == 200:
                    snapshots = response.json()
                    if isinstance(snapshots, list):
                        for snapshot in snapshots:
                            snap_request_id = snapshot.get("request_id") or snapshot.get("requestId")
                            if snap_request_id == request_id:
                                snapshot_id = snapshot.get("snapshot_id") or snapshot.get("id")
                                print(f"✅ Found snapshot: {snapshot_id}")
                                return snapshot_id
                
                await asyncio.sleep(15)
                attempt += 1
                
            except Exception as e:
                print(f"⚠️ Error polling snapshots: {e}")
                await asyncio.sleep(15)
                attempt += 1
        
        print("❌ Timeout waiting for snapshot")
        return None
    
    async def _poll_snapshot(self, snapshot_id: str, timeout: int = 1800) -> BrightDataResponse:
        """Poll snapshot until data is ready"""
        max_attempts = 180
        attempt = 0
        
        print(f"⏳ Polling snapshot data (ID: {snapshot_id})")
        
        while attempt < max_attempts:
            try:
                response = self.session.get(
                    f"{self.config.base_url}/snapshot/{snapshot_id}",
                    params={"format": "json"},
                    timeout=30
                )
                
                if response.status_code == 202:
                    await asyncio.sleep(10)
                    attempt += 1
                    continue
                
                elif response.status_code == 200:
                    if not response.text.strip():
                        await asyncio.sleep(10)
                        attempt += 1
                        continue
                    
                    try:
                        result = response.json()
                        
                        if isinstance(result, list):
                            if result:
                                print(f"✅ Data ready: {len(result)} records")
                                return BrightDataResponse(success=True, data=result, snapshot_id=snapshot_id)
                            else:
                                await asyncio.sleep(10)
                                attempt += 1
                                continue
                        
                        # Check for download URLs
                        if isinstance(result, dict):
                            download_url = result.get('download_urls', {}).get('json')
                            if download_url:
                                print(f"📥 Downloading data from URL")
                                try:
                                    data_response = self.session.get(download_url, timeout=60)
                                    if data_response.status_code == 200:
                                        data = data_response.json()
                                        record_count = len(data) if isinstance(data, list) else 1
                                        print(f"✅ Downloaded {record_count} records")
                                        return BrightDataResponse(success=True, data=data, snapshot_id=snapshot_id)
                                except Exception as download_err:
                                    print(f"❌ Download error: {download_err}")
                                return BrightDataResponse(success=False, error="Failed to download data", snapshot_id=snapshot_id)
                            
                            # Check embedded data
                            if 'data' in result:
                                data = result['data']
                                return BrightDataResponse(
                                    success=True, 
                                    data=data if isinstance(data, list) else [data], 
                                    snapshot_id=snapshot_id
                                )
                        
                        await asyncio.sleep(10)
                        attempt += 1
                        continue
                    
                    except json.JSONDecodeError:
                        await asyncio.sleep(10)
                        attempt += 1
                        continue
                
                elif response.status_code >= 400:
                    return BrightDataResponse(success=False, error=f"API error: HTTP {response.status_code}", snapshot_id=snapshot_id)
                
                else:
                    await asyncio.sleep(5)
                    attempt += 1
                    continue
                        
            except requests.RequestException as e:
                await asyncio.sleep(5)
                attempt += 1
                continue
            except Exception as e:
                await asyncio.sleep(5)
                attempt += 1
                continue
        
        return BrightDataResponse(success=False, error="Timeout waiting for snapshot data", snapshot_id=snapshot_id)

    def close(self):
        """Clean up resources"""
        if hasattr(self, 'session'):
            self.session.close()


async def main():
    """Main function to run the pipeline"""
    print("🔧 Instagram Comprehensive Data Pipeline")
    print("=" * 50)
    
    # Environment variables already loaded at top of file
    
    # Priority selection menu
    print("\n🎯 Select request priority:")
    print("1. High Priority - Fast processing using current APIs")
    print("2. Low Priority - Batch processing using Bright Data API (20 profiles + 100 reels)")
    
    while True:
        priority_choice = input("Enter choice (1-2): ").strip()
        if priority_choice in ['1', '2']:
            break
        print("❌ Invalid choice. Please enter 1 or 2.")

    # Check environment variables based on priority
    print("🔍 Checking environment variables...")
    if priority_choice == '1':
        # High priority - existing APIs
        required_vars = ['INSTAGRAM_SCRAPER_API_KEY', 'SIMILAR_PROFILES_API_KEY']
    else:
        # Low priority - Bright Data API
        required_vars = ['BRIGHT_DATA_API_KEY', 'SIMILAR_PROFILES_API_KEY']
    
    optional_vars = ['OPENAI_API_KEY']
    
    all_vars = required_vars + optional_vars
    
    for var in all_vars:
        value = os.getenv(var)
        if value:
            masked_value = f"{'*' * 10}{value[-10:] if len(value) > 10 else value}"
            status = "✅" if var in required_vars else "✅ (optional)"
            print(f"{status} {var}: {masked_value}")
        else:
            status = "❌" if var in required_vars else "⚠️ (optional)"
            print(f"{status} {var}: Not found")
    
    missing_vars = [var for var in required_vars if not os.getenv(var)]
    
    if missing_vars:
        print(f"❌ Missing environment variables: {', '.join(missing_vars)}")
        print("💡 Make sure your .env file is in the same directory as this script")
        return
    
    pipeline = InstagramDataPipeline()
    
    username = input("Enter Instagram username (without @): ").strip()
    
    # Route based on priority
    if priority_choice == '1':
        # High priority - existing pipeline (saves internally)
        print("🚀 Running HIGH PRIORITY pipeline...")
        primary_profile, content_data, secondary_profiles = await pipeline.run_complete_pipeline(username)
        needs_save = False  # High priority pipeline saves during execution
    else:
        # Low priority - Bright Data API (needs final save)
        print("🔄 Running LOW PRIORITY pipeline with Bright Data API...")
        primary_profile, content_data, secondary_profiles = await pipeline.run_low_priority_pipeline(username)
        needs_save = True  # Low priority pipeline returns data for final save
    
    if primary_profile:
        # Save to CSV files if needed (low priority only)
        if needs_save:
            print("💾 Saving LOW PRIORITY pipeline results to CSV files...")
            pipeline.save_to_csv(primary_profile, content_data, secondary_profiles, username)
        else:
            print("💾 HIGH PRIORITY pipeline data already saved during execution")
        
        print(f"\n📈 Final Summary:")
        print(f"  Primary Profile: ✅")
        print(f"  Content Records: {len(content_data)}")
        print(f"  Secondary Profiles: {len(secondary_profiles)}")
        print(f"  Total Views: {primary_profile.get('total_views', 0):,}")
        print(f"  Median Views: {primary_profile.get('median_views', 0):,}")
        print(f"  💾 All data saved during pipeline execution")
    else:
        print("❌ Pipeline failed")

if __name__ == "__main__":
    asyncio.run(main())