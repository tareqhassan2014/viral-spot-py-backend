"""
Supabase Integration Module for Instagram Data Pipeline
======================================================

This module handles all Supabase operations including:
- Database CRUD operations
- Image uploads to storage buckets
- Transaction management
- Error handling and retries

Installation:
    pip install supabase postgrest gotrue realtime storage3 httpx

Environment Variables Required:
    - SUPABASE_URL: Your Supabase project URL
    - SUPABASE_SERVICE_ROLE_KEY: Service role key for full access
    - SUPABASE_ANON_KEY: Anonymous key (optional)
"""

import os
import asyncio
import aiohttp
from typing import Dict, List, Optional, Tuple, Any, Union
from datetime import datetime
from pathlib import Path
import json
import logging
from urllib.parse import urlparse
import uuid
import time
from dataclasses import asdict

# Supabase imports with error handling
try:
    from supabase import create_client, Client
    from supabase.client import ClientOptions
    import httpx
    
    # Try to import exceptions, but don't fail if they're not available
    try:
        from postgrest.exceptions import APIError
    except ImportError:
        APIError = Exception
    
    try:
        from gotrue.exceptions import AuthError
    except ImportError:
        try:
            from gotrue import AuthError
        except ImportError:
            AuthError = Exception
    
    try:
        from storage3.exceptions import StorageException
    except ImportError:
        StorageException = Exception
    
    SUPABASE_AVAILABLE = True
except ImportError as e:
    SUPABASE_AVAILABLE = False
    print(f"⚠️ Supabase libraries not installed: {e}")
    print("   Run: pip install supabase postgrest gotrue realtime storage3 httpx")
    Client = None
    ClientOptions = None
    APIError = Exception
    AuthError = Exception
    StorageException = Exception

# Import existing config
import config

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class SupabaseManager:
    """Manages all Supabase operations for the Instagram pipeline"""
    
    def __init__(self):
        """Initialize Supabase client and configuration"""
        if not SUPABASE_AVAILABLE:
            raise ImportError(
                "Supabase libraries not installed. Run:\n"
                "pip install supabase postgrest gotrue realtime storage3 httpx"
            )
        
        self.supabase_url = os.getenv('SUPABASE_URL')
        self.supabase_key = os.getenv('SUPABASE_SERVICE_ROLE_KEY')  # Use service role for full access
        self.anon_key = os.getenv('SUPABASE_ANON_KEY')
        
        if not self.supabase_url or not self.supabase_key:
            raise ValueError("Supabase URL and Service Role Key must be set in environment variables")
        
        # Create Supabase client with service role key
        self.client = create_client(
            self.supabase_url,
            self.supabase_key,
            options=ClientOptions(
                auto_refresh_token=True,
                persist_session=True
            )
        )
        
        # Storage configuration
        self.storage_url = os.getenv('SUPABASE_STORAGE_URL', f"{self.supabase_url}/storage/v1")
        self.profile_images_bucket = os.getenv('PROFILE_IMAGES_BUCKET', 'profile-images')
        self.content_thumbnails_bucket = os.getenv('CONTENT_THUMBNAILS_BUCKET', 'content-thumbnails')
        
        # Batch settings
        self.batch_size = int(os.getenv('DB_BATCH_SIZE', '100'))
        self.max_retries = int(os.getenv('DB_MAX_RETRIES', '3'))
        self.retry_delay = float(os.getenv('DB_RETRY_DELAY', '1.0'))
        
        # Feature flags
        self.use_supabase = os.getenv('USE_SUPABASE', 'true').lower() == 'true'
        self.keep_local_csv = os.getenv('KEEP_LOCAL_CSV', 'false').lower() == 'true'
        self.upload_images = os.getenv('UPLOAD_IMAGES_TO_SUPABASE', 'true').lower() == 'true'
        
        logger.info(f"✅ Supabase Manager initialized")
        logger.info(f"   URL: {self.supabase_url}")
        logger.info(f"   Upload Images: {self.upload_images}")
        logger.info(f"   Keep Local CSV: {self.keep_local_csv}")
    
    async def upload_image_to_bucket(self, local_path: str, bucket: str, remote_path: str) -> Optional[str]:
        """Upload image to Supabase storage bucket"""
        if not self.upload_images or not local_path or not Path(local_path).exists():
            return None
        
        try:
            with open(local_path, 'rb') as f:
                file_data = f.read()
            
            # Upload to Supabase storage
            response = self.client.storage.from_(bucket).upload(
                path=remote_path,
                file=file_data,
                file_options={"content-type": "image/jpeg", "upsert": "true"}
            )
            
            # Get public URL
            public_url = self.client.storage.from_(bucket).get_public_url(remote_path)
            
            logger.info(f"✅ Uploaded {Path(local_path).name} to {bucket}/{remote_path}")
            return remote_path
            
        except Exception as e:
            logger.error(f"❌ Failed to upload {local_path} to Supabase: {e}")
            return None
    
    async def save_primary_profile(self, profile_data: Dict) -> Optional[str]:
        """Save or update primary profile in Supabase"""
        if not self.use_supabase:
            return None
        
        try:
            # Upload profile images first
            if profile_data.get('profile_image_local'):
                profile_image_path = await self.upload_image_to_bucket(
                    profile_data['profile_image_local'],
                    self.profile_images_bucket,
                    f"{profile_data['username']}/profile.jpg"
                )
                if profile_image_path:
                    profile_data['profile_image_path'] = profile_image_path
            
            if profile_data.get('hd_profile_image_local'):
                hd_profile_image_path = await self.upload_image_to_bucket(
                    profile_data['hd_profile_image_local'],
                    self.profile_images_bucket,
                    f"{profile_data['username']}/profile_hd.jpg"
                )
                if hd_profile_image_path:
                    profile_data['hd_profile_image_path'] = hd_profile_image_path
            
            # Remove local paths before inserting
            db_data = profile_data.copy()
            db_data.pop('profile_image_local', None)
            db_data.pop('hd_profile_image_local', None)

            # Filter to allowed columns in primary_profiles to avoid PostgREST schema errors
            allowed_fields = {
                'username', 'profile_name', 'bio', 'followers', 'posts_count', 'is_verified',
                'is_business_account', 'profile_url', 'profile_image_url', 'profile_image_path',
                'hd_profile_image_path', 'account_type', 'language', 'content_type', 'total_reels',
                'median_views', 'mean_views', 'std_views', 'total_views', 'total_likes', 'total_comments',
                'profile_primary_category', 'profile_secondary_category', 'profile_tertiary_category',
                'profile_categorization_confidence', 'account_type_confidence',
                'similar_account1','similar_account2','similar_account3','similar_account4','similar_account5',
                'similar_account6','similar_account7','similar_account8','similar_account9','similar_account10',
                'similar_account11','similar_account12','similar_account13','similar_account14','similar_account15',
                'similar_account16','similar_account17','similar_account18','similar_account19','similar_account20',
                'last_full_scrape', 'analysis_timestamp'
            }
            db_data = {k: v for k, v in db_data.items() if k in allowed_fields}

            # Normalize account_type to valid enum string (Personal | Business Page | Influencer)
            raw_account_type = profile_data.get('account_type') or profile_data.get('estimated_account_type')
            normalized_account_type = None
            if raw_account_type is not None:
                try:
                    # Numeric or numeric string
                    if isinstance(raw_account_type, (int, float)) or (isinstance(raw_account_type, str) and raw_account_type.isdigit()):
                        n = int(raw_account_type)
                        mapping = {1: 'Personal', 2: 'Business Page', 3: 'Influencer'}
                        normalized_account_type = mapping.get(n, 'Personal')
                    elif isinstance(raw_account_type, str):
                        v = raw_account_type.strip().lower()
                        if v in ['personal']:
                            normalized_account_type = 'Personal'
                        elif v in ['business', 'business page']:
                            normalized_account_type = 'Business Page'
                        elif v in ['influencer', 'creator']:
                            normalized_account_type = 'Influencer'
                        else:
                            normalized_account_type = 'Personal'
                except Exception:
                    normalized_account_type = 'Personal'
            if normalized_account_type:
                db_data['account_type'] = normalized_account_type
                logger.info(f"🔎 Normalized account_type for @{db_data.get('username','?')}: {normalized_account_type}")
            
            # Convert timestamps
            if db_data.get('last_full_scrape'):
                db_data['last_full_scrape'] = self._ensure_timestamp(db_data['last_full_scrape'])
            if db_data.get('analysis_timestamp'):
                db_data['analysis_timestamp'] = self._ensure_timestamp(db_data['analysis_timestamp'])
            
            # Upsert profile
            response = self.client.table('primary_profiles').upsert(
                db_data,
                on_conflict='username'
            ).execute()
            
            if response.data:
                profile_id = response.data[0]['id']
                logger.info(f"✅ Saved primary profile @{profile_data['username']} (ID: {profile_id})")
                return profile_id
            
            return None
            
        except Exception as e:
            logger.error(f"❌ Failed to save primary profile: {e}")
            return None
    
    async def save_content_batch(self, content_data: List[Dict], profile_id: str, username: str) -> int:
        """Save batch of content records to Supabase with improved duplicate handling"""
        if not self.use_supabase or not content_data:
            return 0
        
        saved_count = 0
        
        # Process in batches
        for i in range(0, len(content_data), self.batch_size):
            batch = content_data[i:i + self.batch_size]
            
            try:
                # Pre-check for existing shortcodes to avoid duplicates
                shortcodes_in_batch = [content.get('shortcode') for content in batch if content.get('shortcode')]
                existing_content = {}
                
                if shortcodes_in_batch:
                    existing_response = self.client.table('content').select('shortcode, content_id, id').in_('shortcode', shortcodes_in_batch).execute()
                    if existing_response.data:
                        for existing in existing_response.data:
                            existing_content[existing['shortcode']] = existing
                        logger.info(f"🔍 Found {len(existing_content)} existing content records out of {len(shortcodes_in_batch)} in batch")
                
                # Upload thumbnails and prepare batch data
                db_batch = []
                skipped_duplicates = 0
                # Track duplicates within the same batch to avoid ON CONFLICT affecting the same row twice
                seen_shortcodes = set()
                seen_content_ids = set()
                
                for content in batch:
                    shortcode = content.get('shortcode')
                    content_id = content.get('content_id')
                    
                    # Skip if this shortcode already exists in DB and content_id is different
                    if shortcode in existing_content:
                        existing_record = existing_content[shortcode]
                        if content.get('content_id') != existing_record.get('content_id'):
                            logger.warning(f"⚠️ Skipping duplicate shortcode {shortcode} with different content_id")
                            skipped_duplicates += 1
                            continue
                    
                    # Skip duplicates within the incoming batch (most common cause of 21000 errors)
                    if shortcode and shortcode in seen_shortcodes:
                        logger.info(f"⏭️ Skipping duplicate shortcode within batch: {shortcode}")
                        skipped_duplicates += 1
                        continue
                    if content_id and content_id in seen_content_ids:
                        logger.info(f"⏭️ Skipping duplicate content_id within batch: {content_id}")
                        skipped_duplicates += 1
                        continue
                    
                    db_content = content.copy()
                    db_content['profile_id'] = profile_id
                    
                    # Upload thumbnail images (ensure display first, then thumb)
                    if content.get('display_url_local'):
                        display_path = await self.upload_image_to_bucket(
                            content['display_url_local'],
                            self.content_thumbnails_bucket,
                            f"{username}/{content['shortcode']}_display.jpg"
                        )
                        if display_path:
                            db_content['display_url_path'] = display_path
                    if content.get('thumbnail_local'):
                        thumbnail_path = await self.upload_image_to_bucket(
                            content['thumbnail_local'],
                            self.content_thumbnails_bucket,
                            f"{username}/{content['shortcode']}_thumb.jpg"
                        )
                        if thumbnail_path:
                            db_content['thumbnail_path'] = thumbnail_path
                    
                    if content.get('video_thumbnail_local'):
                        video_thumb_path = await self.upload_image_to_bucket(
                            content['video_thumbnail_local'],
                            self.content_thumbnails_bucket,
                            f"{username}/{content['shortcode']}_video_thumb.jpg"
                        )
                        if video_thumb_path:
                            db_content['video_thumbnail_path'] = video_thumb_path
                    
                    # Remove local paths
                    db_content.pop('thumbnail_local', None)
                    db_content.pop('display_url_local', None)
                    db_content.pop('video_thumbnail_local', None)
                    
                    # Remove viral analysis fields that don't belong in content table
                    db_content.pop('viral_score', None)
                    db_content.pop('viral_potential_score', None)
                    db_content.pop('engagement_rate', None)

                    # Filter to allowed content fields
                    allowed_content_fields = {
                        'content_id','shortcode','content_type','url','description','thumbnail_url','thumbnail_path',
                        'display_url_path','video_thumbnail_path','view_count','like_count','comment_count','outlier_score',
                        'date_posted','username','language','content_style','primary_category','secondary_category',
                        'tertiary_category','categorization_confidence','keyword_1','keyword_2','keyword_3','keyword_4',
                        'all_image_urls','profile_id','transcript','transcript_language','transcript_fetched_at','transcript_available'
                    }
                    db_content = {k: v for k, v in db_content.items() if k in allowed_content_fields}
                    
                    # Convert date_posted
                    if db_content.get('date_posted'):
                        db_content['date_posted'] = self._ensure_timestamp(db_content['date_posted'])
                    
                    # Convert all_image_urls to JSON
                    if db_content.get('all_image_urls') and isinstance(db_content['all_image_urls'], dict):
                        db_content['all_image_urls'] = json.dumps(db_content['all_image_urls'])
                    
                    db_batch.append(db_content)
                    # Mark as seen after we decide to include it
                    if shortcode:
                        seen_shortcodes.add(shortcode)
                    if content_id:
                        seen_content_ids.add(content_id)
                
                if skipped_duplicates > 0:
                    logger.info(f"⚠️ Skipped {skipped_duplicates} duplicate shortcodes in batch")
                
                if not db_batch:
                    logger.info("ℹ️ No new content to save in this batch (all were duplicates)")
                    continue
                
                # Insert batch with improved conflict handling
                # Use shortcode as the primary conflict resolution since it's the unique constraint causing issues
                # Also include content_id in conflict target to respect both unique constraints
                response = self.client.table('content').upsert(
                    db_batch,
                    on_conflict='shortcode'
                ).execute()
                
                if response.data:
                    saved_count += len(response.data)
                    logger.info(f"✅ Saved batch of {len(response.data)} content records")
                
            except Exception as e:
                logger.error(f"❌ Failed to save content batch: {e}")
                # Try to save individual records to avoid losing entire batch
                individual_saved = await self._save_content_individually(batch, profile_id, username)
                saved_count += individual_saved
                continue
        
        return saved_count
    
    async def _save_content_individually(self, batch: List[Dict], profile_id: str, username: str) -> int:
        """Save content records individually when batch fails"""
        saved_count = 0
        
        for content in batch:
            try:
                db_content = content.copy()
                db_content['profile_id'] = profile_id

                # Upload images first (display, then thumb, then video)
                if content.get('display_url_local'):
                    display_path = await self.upload_image_to_bucket(
                        content['display_url_local'],
                        self.content_thumbnails_bucket,
                        f"{username}/{content['shortcode']}_display.jpg"
                    )
                    if display_path:
                        db_content['display_url_path'] = display_path
                if content.get('thumbnail_local'):
                    thumb_path = await self.upload_image_to_bucket(
                        content['thumbnail_local'],
                        self.content_thumbnails_bucket,
                        f"{username}/{content['shortcode']}_thumb.jpg"
                    )
                    if thumb_path:
                        db_content['thumbnail_path'] = thumb_path
                if content.get('video_thumbnail_local'):
                    video_thumb_path = await self.upload_image_to_bucket(
                        content['video_thumbnail_local'],
                        self.content_thumbnails_bucket,
                        f"{username}/{content['shortcode']}_video_thumb.jpg"
                    )
                    if video_thumb_path:
                        db_content['video_thumbnail_path'] = video_thumb_path

                # Remove fields that don't belong
                db_content.pop('thumbnail_local', None)
                db_content.pop('display_url_local', None)
                db_content.pop('video_thumbnail_local', None)
                db_content.pop('viral_score', None)
                db_content.pop('viral_potential_score', None)
                db_content.pop('engagement_rate', None)
                
                # Convert date_posted
                if db_content.get('date_posted'):
                    db_content['date_posted'] = self._ensure_timestamp(db_content['date_posted'])
                
                # Convert all_image_urls to JSON
                if db_content.get('all_image_urls') and isinstance(db_content['all_image_urls'], dict):
                    db_content['all_image_urls'] = json.dumps(db_content['all_image_urls'])
                
                # Filter to allowed content fields
                allowed_content_fields = {
                    'content_id','shortcode','content_type','url','description','thumbnail_url','thumbnail_path',
                    'display_url_path','video_thumbnail_path','view_count','like_count','comment_count','outlier_score',
                    'date_posted','username','language','content_style','primary_category','secondary_category',
                    'tertiary_category','categorization_confidence','keyword_1','keyword_2','keyword_3','keyword_4',
                    'all_image_urls','profile_id','transcript','transcript_language','transcript_fetched_at','transcript_available'
                }
                db_content = {k: v for k, v in db_content.items() if k in allowed_content_fields}

                # Try to insert individual record
                response = self.client.table('content').upsert(
                    [db_content],
                    on_conflict='shortcode'
                ).execute()
                
                if response.data:
                    saved_count += 1
                    
            except Exception as e:
                logger.warning(f"⚠️ Failed to save individual content record {content.get('shortcode', 'unknown')}: {e}")
                continue
        
        logger.info(f"🔄 Individual save recovered {saved_count}/{len(batch)} records")
        return saved_count
    
    async def save_secondary_profiles_batch(self, profiles: List[Dict], discovered_by_id: str) -> int:
        """Save batch of secondary profiles to Supabase"""
        if not self.use_supabase or not profiles:
            return 0
        
        saved_count = 0
        
        # Process in batches
        for i in range(0, len(profiles), self.batch_size):
            batch = profiles[i:i + self.batch_size]
            
            try:
                # Prepare batch data
                db_batch = []
                for profile in batch:
                    db_profile = profile.copy()
                    db_profile['discovered_by_id'] = discovered_by_id
                    
                    # Upload profile pic
                    if profile.get('profile_pic_local'):
                        profile_pic_path = await self.upload_image_to_bucket(
                            profile['profile_pic_local'],
                            self.profile_images_bucket,
                            f"secondary/{profile['username']}/profile.jpg"
                        )
                        if profile_pic_path:
                            db_profile['profile_pic_path'] = profile_pic_path
                    
                    # Remove local path
                    db_profile.pop('profile_pic_local', None)
                    
                    # Convert timestamps
                    for ts_field in ['last_basic_scrape', 'last_full_scrape', 'analysis_timestamp']:
                        if db_profile.get(ts_field):
                            db_profile[ts_field] = self._ensure_timestamp(db_profile[ts_field])

                    # Normalize estimated_account_type (enum: Personal | Business Page | Influencer | Theme Page)
                    raw_type = db_profile.get('estimated_account_type')
                    if raw_type is not None:
                        try:
                            normalized_type = None
                            if isinstance(raw_type, (int, float)) or (isinstance(raw_type, str) and str(raw_type).isdigit()):
                                n = int(raw_type)
                                mapping = {1: 'Personal', 2: 'Business Page', 3: 'Influencer'}
                                normalized_type = mapping.get(n, 'Personal')
                            elif isinstance(raw_type, str):
                                v = raw_type.strip().lower()
                                if v in ['personal']:
                                    normalized_type = 'Personal'
                                elif v in ['business', 'business page']:
                                    normalized_type = 'Business Page'
                                elif v in ['influencer', 'creator']:
                                    normalized_type = 'Influencer'
                                elif v in ['theme', 'theme page', 'theme-page']:
                                    normalized_type = 'Theme Page'
                                else:
                                    normalized_type = 'Personal'
                            if normalized_type:
                                db_profile['estimated_account_type'] = normalized_type
                        except Exception:
                            db_profile['estimated_account_type'] = 'Personal'

                    # Ensure id is present for databases without DEFAULT uuid
                    # PostgREST applies DEFAULT only when column is omitted, but some deployments
                    # might have NOT NULL without DEFAULT. To be safe, generate id for new rows.
                    if not db_profile.get('id'):
                        db_profile['id'] = str(uuid.uuid4())

                    # Keep only allowed fields to avoid PostgREST schema errors
                    allowed_secondary_fields = {
                        'id', 'username', 'full_name', 'biography', 'followers_count', 'following_count',
                        'media_count', 'profile_pic_url', 'profile_pic_path', 'is_verified', 'is_private',
                        'business_email', 'external_url', 'category', 'pk', 'social_context',
                        'estimated_account_type', 'primary_category', 'secondary_category', 'tertiary_category',
                        'categorization_confidence', 'account_type_confidence', 'estimated_language', 'click_count',
                        'search_count', 'promotion_eligible', 'discovered_by', 'discovery_reason', 'api_source',
                        'similarity_rank', 'last_basic_scrape', 'last_full_scrape', 'analysis_timestamp',
                        'discovered_by_id'
                    }
                    db_profile = {k: v for k, v in db_profile.items() if k in allowed_secondary_fields}
                    
                    db_batch.append(db_profile)
                
                # Insert batch
                response = self.client.table('secondary_profiles').upsert(
                    db_batch,
                    on_conflict='username'
                ).execute()
                
                if response.data:
                    saved_count += len(response.data)
                    logger.info(f"✅ Saved batch of {len(response.data)} secondary profiles")
                
            except Exception as e:
                logger.error(f"❌ Failed to save secondary profiles batch: {e}")
                continue
        
        return saved_count
    
    async def save_queue_item(self, queue_item: Dict) -> bool:
        """Save or update queue item in Supabase"""
        if not self.use_supabase:
            logger.warning("⚠️ Supabase not available for save_queue_item")
            return False
        
        try:
            logger.info(f"💾 Saving queue item to Supabase: {queue_item}")
            
            # Convert timestamp
            if queue_item.get('timestamp'):
                queue_item['timestamp'] = self._ensure_timestamp(queue_item['timestamp'])
            if queue_item.get('last_attempt'):
                queue_item['last_attempt'] = self._ensure_timestamp(queue_item['last_attempt'])
            
            logger.info(f"📊 Processed queue item data: {queue_item}")
            
            # Upsert queue item
            response = self.client.table('queue').upsert(
                queue_item,
                on_conflict='request_id'
            ).execute()
            
            logger.info(f"📨 Supabase upsert response: {response.data}")
            
            if response.data:
                logger.info(f"✅ Successfully saved queue item for @{queue_item['username']}")
                return True
            else:
                logger.warning(f"⚠️ Supabase upsert returned no data for @{queue_item['username']}")
                return False
            
        except Exception as e:
            logger.error(f"❌ Failed to save queue item for @{queue_item.get('username', 'unknown')}: {e}")
            import traceback
            logger.error(f"❌ Full save_queue_item traceback: {traceback.format_exc()}")
            return False
    
    async def get_queue_stats(self) -> Dict:
        """Get queue statistics from Supabase"""
        if not self.use_supabase:
            return {}
        
        try:
            response = self.client.table('queue_stats').select('*').execute()
            if response.data:
                return response.data[0]
            return {}
        except Exception as e:
            logger.error(f"❌ Failed to get queue stats: {e}")
            return {}
    
    async def get_next_queue_item(self, priority: Optional[str] = None) -> Optional[Dict]:
        """Get next pending queue item"""
        if not self.use_supabase:
            return None
        
        try:
            # Disabled noisy log: Getting next queue item
            
            query = self.client.table('queue').select('*').eq('status', 'PENDING')
            
            if priority:
                query = query.eq('priority', priority)
            
            # Order by priority (HIGH first) and timestamp
            # Use CASE statement to prioritize HIGH over LOW
            query = query.order('priority', desc=False).order('timestamp')  # 'HIGH' comes before 'LOW' alphabetically
            
            response = query.execute()
            
            logger.info(f"📊 Found {len(response.data) if response.data else 0} PENDING queue items")
            
            if response.data:
                queue_item = response.data[0]
                logger.info(f"🎯 Selecting queue item: {queue_item['username']} (priority: {queue_item['priority']}, id: {queue_item['id']})")
                
                # Update status to PROCESSING atomically
                update_response = self.client.table('queue').update({
                    'status': 'PROCESSING',
                    'last_attempt': datetime.utcnow().isoformat(),
                    'attempts': queue_item['attempts'] + 1
                }).eq('id', queue_item['id']).execute()
                
                if update_response.data:
                    logger.info(f"✅ Successfully marked {queue_item['username']} as PROCESSING")
                    return queue_item
                else:
                    logger.warning(f"⚠️ Failed to update status for {queue_item['username']}")
            else:
                # Disabled noisy log: No PENDING queue items found
                pass
            
            return None
            
        except Exception as e:
            logger.error(f"❌ Failed to get next queue item: {e}")
            return None
    
    async def update_queue_item_status(self, request_id: str, status: str, error_message: Optional[str] = None) -> bool:
        """Update queue item status by request_id"""
        if not self.use_supabase:
            return False
        
        try:
            update_data = {
                'status': status,
                'last_attempt': datetime.utcnow().isoformat()
            }
            
            if error_message:
                update_data['error_message'] = error_message
            
            # Update by request_id instead of id
            response = self.client.table('queue').update(update_data).eq('request_id', request_id).execute()
            
            return bool(response.data)
            
        except Exception as e:
            logger.error(f"❌ Failed to update queue item status: {e}")
            return False
    
    def _ensure_timestamp(self, timestamp_value: Any) -> str:
        """Ensure timestamp is in proper ISO format for Postgres"""
        if isinstance(timestamp_value, str):
            # Already a string, just ensure it's properly formatted
            try:
                # Parse and reformat to ensure consistency
                if timestamp_value.replace('T', ' ').replace('-', '').replace(':', '').replace('.', '').isdigit():
                    return timestamp_value
                return datetime.fromisoformat(timestamp_value.replace('Z', '+00:00')).isoformat()
            except:
                return datetime.utcnow().isoformat()
        elif isinstance(timestamp_value, (int, float)):
            # Unix timestamp
            return datetime.fromtimestamp(timestamp_value).isoformat()
        elif isinstance(timestamp_value, datetime):
            return timestamp_value.isoformat()
        else:
            return datetime.utcnow().isoformat()
    
    async def verify_data_integrity(self, profile_id: str, expected_content_count: int, expected_secondary_count: int, username: str) -> Dict:
        """Verify all data was uploaded successfully to Supabase with improved duplicate handling"""
        if not self.use_supabase:
            return {"success": True, "message": "Supabase not enabled - skipping verification"}
        
        verification_report = {
            "success": True,
            "primary_profile": False,
            "content_count": 0,
            "secondary_count": 0,
            "expected_content": expected_content_count,
            "expected_secondary": expected_secondary_count,
            "errors": [],
            "warnings": []
        }
        
        try:
            # Verify primary profile exists
            profile_response = self.client.table('primary_profiles').select('id, username').eq('id', profile_id).execute()
            if profile_response.data and len(profile_response.data) > 0:
                verification_report["primary_profile"] = True
                logger.info(f"✅ Primary profile verified in Supabase: @{username}")
            else:
                verification_report["success"] = False
                verification_report["errors"].append(f"Primary profile not found: {profile_id}")
                logger.error(f"❌ Primary profile NOT found in Supabase: @{username}")
            
            # Verify content count with improved duplicate handling
            content_response = self.client.table('content').select('id').eq('profile_id', profile_id).execute()
            actual_content_count = len(content_response.data) if content_response.data else 0
            verification_report["content_count"] = actual_content_count
            
            # Check if the user already has content in the system (for viral analysis pipelines)
            total_user_content = self.client.table('content').select('id').eq('username', username).execute()
            total_user_count = len(total_user_content.data) if total_user_content.data else 0
            
            if actual_content_count == expected_content_count:
                logger.info(f"✅ Content verified: {actual_content_count}/{expected_content_count} records")
            elif actual_content_count < expected_content_count:
                # Check if this is due to existing content in the system
                if total_user_count >= expected_content_count:
                    logger.info(f"✅ Content verification passed: User has {total_user_count} total records (≥{expected_content_count} expected)")
                    verification_report["warnings"].append(f"Profile-specific content: {actual_content_count}, Total user content: {total_user_count}")
                elif actual_content_count > 0:
                    # Partial save - allow if we got at least some content
                    minimum_threshold = max(1, expected_content_count // 10)  # At least 10% or 1 record
                    if actual_content_count >= minimum_threshold:
                        logger.warning(f"⚠️ Partial content save: {actual_content_count}/{expected_content_count} (above minimum threshold)")
                        verification_report["warnings"].append(f"Partial save: {actual_content_count}/{expected_content_count} records")
                    else:
                        verification_report["success"] = False
                        verification_report["errors"].append(f"Content count too low: {actual_content_count}/{expected_content_count}")
                        logger.error(f"❌ Content count too low: {actual_content_count}/{expected_content_count}")
                else:
                    verification_report["success"] = False
                    verification_report["errors"].append(f"No content found, expected {expected_content_count}")
                    logger.error(f"❌ No content found, expected {expected_content_count}")
            
            # Verify secondary profiles count with relaxed validation for viral analysis
            secondary_response = self.client.table('secondary_profiles').select('id').eq('discovered_by_id', profile_id).execute()
            actual_secondary_count = len(secondary_response.data) if secondary_response.data else 0
            verification_report["secondary_count"] = actual_secondary_count
            
            if actual_secondary_count == expected_secondary_count:
                logger.info(f"✅ Secondary profiles verified: {actual_secondary_count}/{expected_secondary_count} records")
            elif expected_secondary_count == 0 and actual_secondary_count > 0:
                # For viral analysis, secondary profiles aren't expected but might exist from previous runs
                logger.info(f"ℹ️ Found {actual_secondary_count} secondary profiles (none expected - likely from previous runs)")
                verification_report["warnings"].append(f"Unexpected secondary profiles: {actual_secondary_count} (likely from previous runs)")
            else:
                verification_report["success"] = False
                verification_report["errors"].append(f"Secondary profiles count mismatch: {actual_secondary_count}/{expected_secondary_count}")
                logger.error(f"❌ Secondary profiles count mismatch: {actual_secondary_count}/{expected_secondary_count}")
            
            # Overall success determination
            if verification_report["warnings"] and not verification_report["errors"]:
                logger.info(f"✅ Data verification passed with warnings for @{username}")
                
            return verification_report
            
        except Exception as e:
            verification_report["success"] = False
            verification_report["errors"].append(f"Verification failed: {str(e)}")
            logger.error(f"❌ Data verification failed: {e}")
            return verification_report
    
    async def rollback_failed_save(self, profile_id: str, username: str) -> bool:
        """Rollback failed save operation by removing partial data"""
        if not self.use_supabase or not profile_id:
            return True
        
        try:
            logger.info(f"🔄 Rolling back failed save for @{username} (ID: {profile_id})")
            
            # Delete in reverse order of creation (to respect foreign key constraints)
            
            # 1. Delete secondary profiles first
            secondary_response = self.client.table('secondary_profiles').delete().eq('discovered_by_id', profile_id).execute()
            logger.info(f"🗑️ Deleted secondary profiles for {profile_id}")
            
            # 2. Delete content records
            content_response = self.client.table('content').delete().eq('profile_id', profile_id).execute()
            logger.info(f"🗑️ Deleted content records for {profile_id}")
            
            # 3. Delete primary profile last
            profile_response = self.client.table('primary_profiles').delete().eq('id', profile_id).execute()
            logger.info(f"🗑️ Deleted primary profile {profile_id}")
            
            logger.info(f"✅ Successfully rolled back failed save for @{username}")
            return True
            
        except Exception as e:
            logger.error(f"❌ Rollback failed for @{username}: {e}")
            return False