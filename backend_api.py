#!/usr/bin/env python3
"""
ViralSpot Backend API Server
============================

FastAPI server that connects the existing Supabase database to the frontend.
Serves endpoints for reels, profiles, similar profiles, and filtering.

Endpoints:
- GET /api/reels - Get reels with filtering and pagination
- GET /api/filter-options - Get available filter options
- GET /api/profile/{username} - Get profile data
- GET /api/profile/{username}/reels - Get profile's reels
- GET /api/profile/{username}/similar - Get similar profiles
- POST /api/reset-session - Reset random session
"""

import os
import json
import logging
from typing import List, Dict, Optional, Any, Union
from datetime import datetime, timedelta
import asyncio
from dataclasses import dataclass
import random
import hashlib

# FastAPI imports
from fastapi import FastAPI, HTTPException, Query, Path, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel
import uvicorn

# Import existing Supabase integration
try:
    from supabase_integration import SupabaseManager
    SUPABASE_AVAILABLE = True
except ImportError as e:
    SUPABASE_AVAILABLE = False
    print(f"⚠️ Supabase integration not available: {e}")
    SupabaseManager = None

# Import simple similar profiles API
try:
    from simple_similar_profiles_api import get_similar_api
    SIMPLE_SIMILAR_API_AVAILABLE = True
except ImportError as e:
    SIMPLE_SIMILAR_API_AVAILABLE = False
    print(f"⚠️ Simple similar profiles API not available: {e}")
    get_similar_api = None

# Load environment variables
from dotenv import load_dotenv
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Pydantic models for request/response
class ReelFilter(BaseModel):
    search: Optional[str] = None
    primary_categories: Optional[str] = None
    secondary_categories: Optional[str] = None
    tertiary_categories: Optional[str] = None
    keywords: Optional[str] = None
    min_outlier_score: Optional[float] = None
    max_outlier_score: Optional[float] = None
    min_views: Optional[int] = None
    max_views: Optional[int] = None
    min_followers: Optional[int] = None
    max_followers: Optional[int] = None
    min_likes: Optional[int] = None
    max_likes: Optional[int] = None
    min_comments: Optional[int] = None
    max_comments: Optional[int] = None
    date_range: Optional[str] = None
    is_verified: Optional[bool] = None
    random_order: Optional[bool] = False
    session_id: Optional[str] = None
    sort_by: Optional[str] = None  # Sort option: 'popular', 'views', 'likes', 'comments', 'recent', 'oldest', 'followers', 'engagement_rate'
    # New filter fields
    account_types: Optional[str] = None  # Comma-separated: Influencer, Theme Page, Business Page, Personal
    content_types: Optional[str] = None  # Comma-separated: reel, post, story
    languages: Optional[str] = None  # Comma-separated: en, es, fr, etc.
    content_styles: Optional[str] = None  # Comma-separated: video, image, etc.
    excluded_usernames: Optional[str] = None  # Comma-separated usernames to exclude
    # Account engagement rate filters (percentage): (likes + comments) / followers * 100
    min_account_engagement_rate: Optional[float] = None
    max_account_engagement_rate: Optional[float] = None

# Viral Ideas Queue Models
class ContentStrategyData(BaseModel):
    contentType: str
    targetAudience: str 
    goals: str

class ViralIdeasQueueRequest(BaseModel):
    session_id: str
    primary_username: str
    selected_competitors: List[str]
    content_strategy: ContentStrategyData

class ViralIdeasQueueResponse(BaseModel):
    id: str
    session_id: str
    primary_username: str
    status: str
    submitted_at: str

class APIResponse(BaseModel):
    success: bool
    data: Any
    message: Optional[str] = None
    error: Optional[str] = None

# Global session storage for random mode
session_storage = {}

class ViralSpotAPI:
    """Main API class that handles all endpoints"""
    
    def __init__(self):
        """Initialize API with Supabase connection"""
        if not SUPABASE_AVAILABLE:
            raise RuntimeError("Supabase integration not available. Please install required packages.")
        
        self.supabase = SupabaseManager()
        if not self.supabase.use_supabase:
            raise RuntimeError("Supabase not configured. Please set SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY")
        
        logger.info("✅ ViralSpot API initialized with Supabase")
    
    def _build_content_query(self, filters: ReelFilter, limit: int, offset: int):
        """Build Supabase query for content with filters"""
        query = self.supabase.client.table('content').select('''
            *,
            primary_profiles!profile_id (
                username,
                profile_name,
                bio,
                followers,
                profile_image_url,
                profile_image_path,
                is_verified,
                account_type
            )
        ''')
        
        # Search filter
        if filters.search:
            # Search in description and username from content table
            # Profile name search is handled separately due to PostgREST limitations with joined table OR queries
            search_term = f"%{filters.search}%"
            query = query.or_(
                f"description.ilike.{search_term},"
                f"username.ilike.{search_term}"
            )
        
        # Category filters
        if filters.primary_categories:
            categories = [cat.strip() for cat in filters.primary_categories.split(',')]
            query = query.in_('primary_category', categories)
        
        if filters.secondary_categories:
            categories = [cat.strip() for cat in filters.secondary_categories.split(',')]
            query = query.in_('secondary_category', categories)
        
        if filters.tertiary_categories:
            categories = [cat.strip() for cat in filters.tertiary_categories.split(',')]
            query = query.in_('tertiary_category', categories)
        
        # New filter fields - use proper filter syntax for joined table
        if filters.account_types:
            account_types = [t.strip() for t in filters.account_types.split(',')]
            query = query.filter('primary_profiles.account_type', 'in', f"({','.join(account_types)})")
        
        if filters.content_types:
            # Normalize requested content types to the valid enum values in DB
            requested_types = [t.strip() for t in filters.content_types.split(',') if t and t.strip()]
            valid_types = set()
            for t in requested_types:
                tl = t.lower()
                if tl in {'post', 'image', 'photo', 'carousel', 'carousel_album', 'graphimage', 'graphsidecar'}:
                    valid_types.add('post')
                elif tl in {'reel', 'video'}:
                    valid_types.add('reel')
                elif tl in {'story', 'stories'}:
                    valid_types.add('story')
                # Ignore unknown values silently
            content_types = sorted(valid_types)
            if content_types:
                query = query.in_('content_type', content_types)
            else:
                # If after normalization nothing valid remains, force no results
                query = query.eq('content_type', '___none___')
        else:
            content_types = []
        
        if filters.languages:
            languages = [lang.strip() for lang in filters.languages.split(',')]
            query = query.in_('language', languages)
        
        if filters.content_styles:
            styles = [style.strip() for style in filters.content_styles.split(',')]
            query = query.in_('content_style', styles)
        
        # Excluded usernames filter (for viral ideas niche outliers)
        if filters.excluded_usernames:
            excluded_users = [username.strip() for username in filters.excluded_usernames.split(',') if username.strip()]
            if excluded_users:
                # Use not_.in_ to exclude these usernames
                query = query.not_.in_('username', excluded_users)
                logger.info(f"🚫 Excluding {len(excluded_users)} usernames from results")
        
        # Keyword filter
        if filters.keywords:
            keywords = [kw.strip() for kw in filters.keywords.split(',')]
            # Search in any of the keyword fields
            keyword_filters = []
            for keyword in keywords:
                keyword_pattern = f"%{keyword}%"
                keyword_filters.extend([
                    f"keyword_1.ilike.{keyword_pattern}",
                    f"keyword_2.ilike.{keyword_pattern}",
                    f"keyword_3.ilike.{keyword_pattern}",
                    f"keyword_4.ilike.{keyword_pattern}",
                    f"description.ilike.{keyword_pattern}"
                ])
            if keyword_filters:
                query = query.or_(','.join(keyword_filters))
        
        # Numeric filters
        if filters.min_outlier_score is not None:
            query = query.gte('outlier_score', filters.min_outlier_score)
        if filters.max_outlier_score is not None:
            query = query.lte('outlier_score', filters.max_outlier_score)
        
        # For posts, ignore view_count filters (posts don't have views)
        is_post_mode = any((ct or '').lower() == 'post' for ct in content_types)
        if not is_post_mode:
            if filters.min_views is not None:
                query = query.gte('view_count', filters.min_views)
            if filters.max_views is not None:
                query = query.lte('view_count', filters.max_views)
        
        if filters.min_likes is not None:
            query = query.gte('like_count', filters.min_likes)
        if filters.max_likes is not None:
            query = query.lte('like_count', filters.max_likes)
        
        if filters.min_comments is not None:
            query = query.gte('comment_count', filters.min_comments)
        if filters.max_comments is not None:
            query = query.lte('comment_count', filters.max_comments)
        
        # Follower filter (from profile) - use simpler approach for joined table filtering
        if filters.min_followers is not None:
            query = query.filter('primary_profiles.followers', 'gte', filters.min_followers)
        if filters.max_followers is not None:
            query = query.filter('primary_profiles.followers', 'lte', filters.max_followers)
        
        # Verified filter - use proper filter syntax for joined table
        if filters.is_verified is not None:
            query = query.filter('primary_profiles.is_verified', 'eq', filters.is_verified)
        
        # Date range filter
        if filters.date_range and filters.date_range != 'all':
            now = datetime.utcnow()
            if filters.date_range == 'day':
                cutoff = now - timedelta(days=1)
            elif filters.date_range == 'week':
                cutoff = now - timedelta(weeks=1)
            elif filters.date_range == 'month':
                cutoff = now - timedelta(days=30)
            elif filters.date_range == 'year':
                cutoff = now - timedelta(days=365)
            else:
                cutoff = None
            
            if cutoff:
                query = query.gte('date_posted', cutoff.isoformat())
        
        # Apply sorting
        if filters.random_order and filters.session_id:
            # For random mode, we'll handle ordering after the query
            pass
        elif filters.sort_by:
            # Apply specific sorting
            if filters.sort_by == 'views':
                query = query.order('view_count', desc=True)
            elif filters.sort_by == 'likes':
                query = query.order('like_count', desc=True)
            elif filters.sort_by == 'comments':
                query = query.order('comment_count', desc=True)
            elif filters.sort_by == 'followers':
                query = query.order('primary_profiles.followers', desc=True)
            elif filters.sort_by == 'account_engagement':
                # Approximate by high interactions; client refines by interactions per followers
                query = query.order('like_count', desc=True).order('comment_count', desc=True)
            elif filters.sort_by == 'content_engagement':
                # Content engagement proxy: interactions per views ~ (like+comment)/views (server can't compute ratio here)
                # Approximate by interaction volume; client can refine if needed
                query = query.order('like_count', desc=True).order('comment_count', desc=True)
            elif filters.sort_by == 'recent':
                query = query.order('date_posted', desc=True)
            elif filters.sort_by == 'oldest':
                query = query.order('date_posted', desc=False)
            elif filters.sort_by == 'popular':
                # For posts, prioritize likes as secondary; for reels, views
                if is_post_mode:
                    query = query.order('outlier_score', desc=True).order('like_count', desc=True)
                else:
                    query = query.order('outlier_score', desc=True).order('view_count', desc=True)
            else:
                # Default fallback
                if is_post_mode:
                    query = query.order('outlier_score', desc=True).order('like_count', desc=True)
                else:
                    query = query.order('outlier_score', desc=True).order('view_count', desc=True)
        else:
            # Default ordering by outlier score desc, then view count desc
            if is_post_mode:
                query = query.order('outlier_score', desc=True).order('like_count', desc=True)
            else:
                query = query.order('outlier_score', desc=True).order('view_count', desc=True)
        
        # Pagination
        query = query.range(offset, offset + limit - 1)
        
        return query
    
    def _apply_random_ordering(self, data: List[Dict], session_id: str, limit: int) -> List[Dict]:
        """Apply consistent random ordering for a session"""
        if not session_id:
            return data
        
        # Create a hash-based seed for consistent randomization
        seed = hashlib.md5(session_id.encode()).hexdigest()
        random.seed(seed)
        
        # If we have seen data for this session, exclude it
        if session_id in session_storage:
            seen_ids = session_storage[session_id]
            data = [item for item in data if item['content_id'] not in seen_ids]
        else:
            session_storage[session_id] = set()
        
        # Randomize the remaining data
        random.shuffle(data)
        
        # Take only what we need
        result = data[:limit]
        
        # Track seen items
        for item in result:
            session_storage[session_id].add(item['content_id'])
        
        return result
    
    def _transform_content_for_frontend(self, content_item: Dict) -> Dict:
        """Transform Supabase content to frontend format"""
        if content_item is None or not isinstance(content_item, dict):
            logger.error("❌ Content item is None in transformation")
            return None
            
        profile = content_item.get('primary_profiles') if content_item else {}
        # Ensure profile is always a dict to avoid NoneType .get errors
        if profile is None or not isinstance(profile, dict):
            profile = {}
        
        # Get the best available thumbnail URL
        thumbnail_url = None
        if content_item and content_item.get('thumbnail_path'):
            # Use Supabase storage URL
            thumbnail_url = self.supabase.client.storage.from_('content-thumbnails').get_public_url(content_item['thumbnail_path'])
        elif content_item and content_item.get('display_url_path'):
            thumbnail_url = self.supabase.client.storage.from_('content-thumbnails').get_public_url(content_item['display_url_path'])
        elif content_item and content_item.get('thumbnail_url'):
            thumbnail_url = content_item['thumbnail_url']
        
        # Get profile image URL
        profile_image_url = None
        if profile and profile.get('profile_image_path'):
            profile_image_url = self.supabase.client.storage.from_('profile-images').get_public_url(profile['profile_image_path'])
        elif profile and profile.get('profile_image_url'):
            profile_image_url = profile['profile_image_url']
        
        # If no joined profile data, try a fallback lookup by username
        try:
            if not profile or not profile.get('profile_name'):
                username = content_item.get('username')
                if username:
                    lookup = self.supabase.client.table('primary_profiles').select(
                        'username, profile_name, bio, followers, profile_image_url, profile_image_path, is_verified, account_type'
                    ).eq('username', username).limit(1).execute()
                    if lookup.data:
                        profile = lookup.data[0]
                        # Recompute profile image URL from stored path if available
                        if profile.get('profile_image_path'):
                            profile_image_url = self.supabase.client.storage.from_('profile-images').get_public_url(profile['profile_image_path'])
                        elif profile.get('profile_image_url'):
                            profile_image_url = profile.get('profile_image_url')
        except Exception:
            pass
        
        transformed = {
            'id': content_item.get('content_id', ''),
            'reel_id': content_item.get('content_id', ''),
            'content_id': content_item.get('content_id', ''),
            'content_type': content_item.get('content_type', 'reel'),
            'shortcode': content_item.get('shortcode', ''),
            'url': content_item.get('url', ''),
            'description': content_item.get('description', ''),
            'title': content_item.get('description', ''),  # Alias for frontend
            'thumbnail_url': thumbnail_url,
            'thumbnail_local': thumbnail_url,  # For compatibility
            'thumbnail': thumbnail_url,  # For compatibility
            'view_count': content_item.get('view_count', 0),
            'like_count': content_item.get('like_count', 0),
            'comment_count': content_item.get('comment_count', 0),
            'outlier_score': content_item.get('outlier_score', 0),
            'outlierScore': f"{content_item.get('outlier_score', 0):.1f}x",  # Formatted for frontend
            'date_posted': content_item.get('date_posted'),
            'username': content_item.get('username'),
            'profile': f"@{content_item.get('username', '')}",
            'profile_name': profile.get('profile_name', ''),
            'bio': profile.get('bio', ''),
            'profile_followers': profile.get('followers', 0),
            'followers': profile.get('followers', 0),  # For compatibility
            'profile_image_url': profile_image_url,
            'profileImage': profile_image_url,  # For compatibility
            'is_verified': profile.get('is_verified', False),
            'primary_category': content_item.get('primary_category'),
            'secondary_category': content_item.get('secondary_category'),
            'tertiary_category': content_item.get('tertiary_category'),
            'keyword_1': content_item.get('keyword_1'),
            'keyword_2': content_item.get('keyword_2'),
            'keyword_3': content_item.get('keyword_3'),
            'keyword_4': content_item.get('keyword_4'),
            'categorization_confidence': content_item.get('categorization_confidence', 0),
            'content_style': content_item.get('content_style', None),
            # Frontend expects these as formatted strings
            'views': self._format_number(content_item.get('view_count', 0)),
            'likes': self._format_number(content_item.get('like_count', 0)),
            'comments': self._format_number(content_item.get('comment_count', 0)),
        }

        # Fallbacks when join didn't return a profile row
        if not transformed['profile_name']:
            transformed['profile_name'] = content_item.get('username', '') or ''
        if transformed['profile_image_url'] is None and profile.get('profile_pic_url'):
            transformed['profile_image_url'] = profile.get('profile_pic_url')
            transformed['profileImage'] = transformed['profile_image_url']
        
        return transformed
    
    def _format_number(self, num: int) -> str:
        """Format number for display (e.g., 1.2M, 45K)"""
        if num >= 1000000:
            return f"{num / 1000000:.1f}M"
        elif num >= 1000:
            return f"{num / 1000:.0f}K"
        else:
            return str(num)
    
    def _transform_profile_for_frontend(self, profile_item: Dict) -> Dict:
        """Transform Supabase profile to frontend format"""
        # Get profile image URL
        profile_image_url = None
        if profile_item.get('profile_image_path'):
            profile_image_url = self.supabase.client.storage.from_('profile-images').get_public_url(profile_item['profile_image_path'])
        elif profile_item.get('profile_image_url'):
            profile_image_url = profile_item['profile_image_url']
        
        return {
            'username': profile_item['username'],
            'profile_name': profile_item.get('profile_name', ''),
            'followers': profile_item.get('followers', 0),
            'profile_image_url': profile_image_url,
            'profile_image_local': profile_image_url,
            'bio': profile_item.get('bio', ''),
            'is_verified': profile_item.get('is_verified', False),
            'is_business_account': profile_item.get('is_business_account', False),
            'reels_count': profile_item.get('total_reels', 0),
            'average_views': profile_item.get('mean_views', 0),
            'primary_category': profile_item.get('profile_primary_category'),
            'profile_type': 'primary',
            'url': f"https://www.instagram.com/{profile_item['username']}/"
        }
    
    async def get_reels(self, filters: ReelFilter, limit: int = 24, offset: int = 0):
        """Get reels with filtering and pagination"""
        try:
            logger.info(f"Getting reels: limit={limit}, offset={offset}")
            logger.info(f"Filters: min_followers={filters.min_followers}, max_followers={filters.max_followers}")
            
            # Build and execute query - request one extra to check if there's more data
            query = self._build_content_query(filters, limit + 1, offset)
            response = query.execute()
            
            # Handle empty or None response data properly
            if not response or not hasattr(response, 'data') or response.data is None or len(response.data) == 0:
                logger.info("📭 No reels found for the given filters")
                return {'reels': [], 'isLastPage': True}
            
            data = response.data
            logger.info(f"📦 Raw data received: {len(data)} items")
            
            # Check if there are more pages based on whether we got more than requested
            has_more_data = len(data) > limit
            
            # Apply random ordering if needed
            if filters.random_order and filters.session_id:
                data = self._apply_random_ordering(data, filters.session_id, limit)
            else:
                data = data[:limit] if data else []  # Trim to exact limit, handle None case
            
            # Transform for frontend - filter out None items first
            valid_data = [item for item in data if item is not None]
            transformed_reels = []
            for item in valid_data:
                try:
                    transformed = self._transform_content_for_frontend(item)
                    if transformed is not None:
                        transformed_reels.append(transformed)
                except Exception as e:
                    logger.error(f"❌ Error transforming content item: {e}")
                    continue
            
            # Check if this is the last page
            is_last_page = not has_more_data
            
            logger.info(f"✅ Returned {len(transformed_reels)} reels, isLastPage: {is_last_page}")
            
            return {
                'reels': transformed_reels,
                'isLastPage': is_last_page
            }
            
        except Exception as e:
            logger.error(f"❌ Error getting reels: {e}")
            raise HTTPException(status_code=500, detail=str(e))

    async def get_reels_mode(self, mode: str, filters: ReelFilter, limit: int = 24, offset: int = 0):
        """Get content filtered by content_type mode: 'reels' or 'posts'"""
        if mode not in ['reels', 'posts']:
            raise HTTPException(status_code=400, detail="Invalid mode")
        # Clone filters and set content_types
        mode_filters = filters.copy()
        mode_filters.content_types = 'reel' if mode == 'reels' else 'post'
        return await self.get_reels(mode_filters, limit, offset)
    
    async def get_filter_options(self):
        """Get available filter options from database"""
        try:
            logger.info("Getting filter options")
            
            # Get distinct categories and content metadata
            categories_response = self.supabase.client.table('content').select(
                'primary_category, secondary_category, tertiary_category, content_type, language, content_style'
            ).execute()
            
            # Get distinct keywords
            keywords_response = self.supabase.client.table('content').select(
                'keyword_1, keyword_2, keyword_3, keyword_4'
            ).execute()
            
            # Get distinct usernames and account types
            usernames_response = self.supabase.client.table('primary_profiles').select(
                'username, profile_name, account_type'
            ).execute()
            
            # Process categories and metadata
            primary_categories = set()
            secondary_categories = set()
            tertiary_categories = set()
            content_types = set()
            languages = set()
            content_styles = set()
            
            for item in categories_response.data:
                if item.get('primary_category'):
                    primary_categories.add(item['primary_category'])
                if item.get('secondary_category'):
                    secondary_categories.add(item['secondary_category'])
                if item.get('tertiary_category'):
                    tertiary_categories.add(item['tertiary_category'])
                if item.get('content_type'):
                    content_types.add(item['content_type'])
                if item.get('language'):
                    languages.add(item['language'])
                if item.get('content_style'):
                    content_styles.add(item['content_style'])
            
            # Process keywords
            keywords = set()
            for item in keywords_response.data:
                for i in range(1, 5):
                    keyword = item.get(f'keyword_{i}')
                    if keyword and keyword.strip():
                        keywords.add(keyword.strip())
            
            # Process usernames and account types
            usernames = []
            account_types = set()
            for item in usernames_response.data:
                usernames.append({
                    'username': item['username'],
                    'profile_name': item.get('profile_name', '')
                })
                if item.get('account_type'):
                    account_types.add(item['account_type'])
            
            result = {
                'primary_categories': sorted(list(primary_categories)),
                'secondary_categories': sorted(list(secondary_categories)),
                'tertiary_categories': sorted(list(tertiary_categories)),
                'keywords': sorted(list(keywords)),
                'usernames': usernames,
                # New filter options
                'account_types': sorted(list(account_types)),
                'content_types': sorted(list(content_types)),
                'languages': sorted(list(languages)),
                'content_styles': sorted(list(content_styles))
            }
            
            logger.info(f"✅ Filter options: {len(result['primary_categories'])} primary categories, {len(result['keywords'])} keywords")
            
            return result
            
        except Exception as e:
            logger.error(f"❌ Error getting filter options: {e}")
            raise HTTPException(status_code=500, detail=str(e))
    
    async def get_profile(self, username: str):
        """Get profile data"""
        try:
            logger.info(f"Getting profile: {username}")
            
            response = self.supabase.client.table('primary_profiles').select('*').eq('username', username).execute()
            
            if not response.data:
                raise HTTPException(status_code=404, detail="Profile not found")
            
            profile = response.data[0]
            transformed_profile = self._transform_profile_for_frontend(profile)
            
            logger.info(f"✅ Found profile: {username}")
            
            return transformed_profile
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"❌ Error getting profile {username}: {e}")
            raise HTTPException(status_code=500, detail=str(e))
    
    async def get_secondary_profile(self, username: str):
        """Get secondary profile data for loading state"""
        try:
            logger.info(f"Getting secondary profile: {username}")
            
            response = self.supabase.client.table('secondary_profiles').select('''
                username,
                full_name,
                biography,
                followers_count,
                profile_pic_url,
                profile_pic_path,
                is_verified,
                primary_category,
                secondary_category,
                tertiary_category,
                estimated_account_type,
                created_at
            ''').eq('username', username).execute()
            
            if not response.data:
                return None
            
            profile = response.data[0]
            
            # Get the best available profile image URL
            profile_image_url = None
            profile_image_local = None
            
            if profile.get('profile_pic_path'):
                # Convert Supabase storage path to public URL
                profile_image_url = self.supabase.client.storage.from_('profile-images').get_public_url(profile['profile_pic_path'])
                profile_image_local = profile_image_url  # Use the same URL for both fields
            elif profile.get('profile_pic_url'):
                # Fallback to original Instagram URL
                profile_image_url = profile['profile_pic_url']
                profile_image_local = profile_image_url
            
            # Transform to match frontend interface
            transformed_profile = {
                'username': profile.get('username', username),
                'profile_name': profile.get('full_name', username),
                'bio': profile.get('biography', ''),
                'followers': profile.get('followers_count', 0),
                'profile_image_url': profile_image_url,
                'profile_image_local': profile_image_local,
                'is_verified': profile.get('is_verified', False),
                'primary_category': profile.get('primary_category'),
                'account_type': profile.get('estimated_account_type', 'Personal'),
                'url': f"https://instagram.com/{username}",
                'reels_count': 0,  # Unknown for secondary profiles
                'average_views': 0,  # Unknown for secondary profiles
                'is_secondary': True,  # Flag to indicate this is secondary data
                'created_at': profile.get('created_at')
            }
            
            logger.info(f"✅ Found secondary profile: {username} with image URL: {profile_image_url}")
            
            return transformed_profile
            
        except Exception as e:
            logger.error(f"❌ Error getting secondary profile {username}: {e}")
            return None
    
    async def request_profile_processing(self, username: str, source: str = "frontend"):
        """Request high priority processing for a profile"""
        try:
            logger.info(f"Requesting high priority processing for: {username}")
            
            # Import here to avoid circular imports
            from queue_processor import Priority
            
            # CRITICAL: First check if PRIMARY profile already exists
            # If primary profile exists, no need to queue
            primary_response = self.supabase.client.table('primary_profiles').select('username').eq('username', username).execute()
            
            if primary_response.data:
                logger.info(f"✅ PRIMARY profile {username} already exists - no queueing needed")
                return {
                    'queued': False,
                    'message': f'Profile {username} is already fully processed',
                    'estimated_time': 'complete'
                }
            
            # Check if already in queue for processing using Supabase directly
            try:
                logger.info(f"🔍 Checking Supabase queue for existing {username} entries...")
                
                # Check for any active queue items (PENDING, PROCESSING, or recent)
                queue_response = self.supabase.client.table('queue').select('*').eq('username', username).in_('status', ['PENDING', 'PROCESSING']).execute()
                
                logger.info(f"📊 Supabase queue check result for {username}: {len(queue_response.data) if queue_response.data else 0} active items found")
                
                if queue_response.data:
                    queue_item = queue_response.data[0]  # Get the first match
                    status = queue_item.get('status', 'UNKNOWN')
                    logger.info(f"✅ {username} already in Supabase queue with status: {status}")
                    return {
                        'queued': True,
                        'message': f'Profile {username} is already in queue (status: {status})',
                        'estimated_time': '2-5 minutes'
                    }
                
                # Also check for recently completed items (last 10 minutes) to avoid re-queueing
                from datetime import datetime, timedelta
                ten_minutes_ago = (datetime.now() - timedelta(minutes=10)).isoformat()
                
                recent_response = self.supabase.client.table('queue').select('*').eq('username', username).eq('status', 'COMPLETED').gte('timestamp', ten_minutes_ago).execute()
                
                if recent_response.data:
                    logger.info(f"✅ {username} was recently completed in queue - checking if primary profile exists")
                    # Double-check if primary profile was actually created
                    primary_check = self.supabase.client.table('primary_profiles').select('username').eq('username', username).execute()
                    if primary_check.data:
                        logger.info(f"✅ {username} primary profile confirmed to exist")
                        return {
                            'queued': False,
                            'message': f'Profile {username} was recently processed and is now available',
                            'estimated_time': 'complete'
                        }
                
                logger.info(f"📝 No active queue entries found for {username} - proceeding with queue addition")
                
            except Exception as e:
                logger.error(f"❌ Error checking Supabase queue for {username}: {e}")
                logger.info(f"🔄 Continuing with queue addition despite check error")
            
            # If we get here, we have a secondary profile that needs upgrading to primary
            logger.info(f"🔄 Secondary profile {username} needs upgrade to primary - adding to Supabase queue")
            
            # Add directly to Supabase queue
            import uuid
            from datetime import datetime
            
            try:
                queue_data = {
                    'username': username,
                    'source': source,
                    'priority': 'HIGH',
                    'timestamp': datetime.now().isoformat(),
                    'status': 'PENDING',
                    'attempts': 0,
                    'request_id': str(uuid.uuid4())[:8]
                }
                
                logger.info(f"📝 Adding {username} to Supabase queue with data: {queue_data}")
                
                supabase_success = await self.supabase.save_queue_item(queue_data)
                
                if supabase_success:
                    logger.info(f"✅ Successfully added {username} to Supabase queue for secondary→primary upgrade")
                    
                    # Verify the item was added by checking the queue
                    verify_response = self.supabase.client.table('queue').select('*').eq('username', username).eq('status', 'PENDING').execute()
                    if verify_response.data:
                        logger.info(f"🔍 Verification: {username} confirmed in Supabase queue")
                    else:
                        logger.warning(f"⚠️ Verification failed: {username} not found in queue after addition")
                    
                    return {
                        'queued': True,
                        'message': f'Profile {username} added to high priority processing queue',
                        'estimated_time': '2-5 minutes'
                    }
                else:
                    logger.error(f"❌ Failed to add {username} to Supabase queue (save_queue_item returned False)")
                    
            except Exception as queue_error:
                logger.error(f"❌ Supabase queue addition error for {username}: {queue_error}")
                import traceback
                logger.error(f"❌ Full traceback: {traceback.format_exc()}")
            
            # Final fallback - optimistically return success to show loading state
            logger.info(f"ℹ️ Using optimistic response for {username} - showing loading state")
            return {
                'queued': True,  # Always show loading state for secondary profiles
                'message': f'Profile {username} is being processed (upgrade in progress)',
                'estimated_time': '2-5 minutes'
            }
                
        except Exception as e:
            logger.error(f"❌ Error requesting processing for {username}: {e}")
            return {
                'queued': False,
                'message': f'Error requesting processing: {str(e)}',
                'estimated_time': 'unknown'
            }
    
    async def check_profile_status(self, username: str):
        """Check if profile processing is complete"""
        try:
            logger.info(f"Checking profile status: {username}")
            
            # Check if profile exists in primary_profiles now
            response = self.supabase.client.table('primary_profiles').select('username, created_at').eq('username', username).execute()
            
            if response.data:
                return {
                    'completed': True,
                    'message': 'Profile processing completed',
                    'created_at': response.data[0].get('created_at')
                }
            else:
                # Check queue status using Supabase directly
                try:
                    queue_response = self.supabase.client.table('queue').select('*').eq('username', username).order('timestamp', desc=True).limit(1).execute()
                    
                    if queue_response.data:
                        queue_item = queue_response.data[0]
                        return {
                            'completed': False,
                            'status': queue_item['status'],
                            'message': f'Profile is {queue_item["status"].lower()}',
                            'attempts': queue_item.get('attempts', 0)
                        }
                
                except Exception as e:
                    logger.warning(f"⚠️ Error checking Supabase queue for status: {e}")
                
                return {
                    'completed': False,
                    'status': 'NOT_FOUND',
                    'message': 'Profile not found in queue or database'
                }
                
        except Exception as e:
            logger.error(f"❌ Error checking profile status {username}: {e}")
            return {
                'completed': False,
                'status': 'ERROR',
                'message': f'Error checking status: {str(e)}'
            }
    
    async def get_profile_reels(self, username: str, sort_by: str = 'popular', limit: int = 24, offset: int = 0):
        """Get reels for a specific profile"""
        try:
            logger.info(f"Getting reels for profile: {username}, sort_by: {sort_by}")
            
            # Use the same profile join as the main query to get real profile data
            query = self.supabase.client.table('content').select('''
                *,
                primary_profiles!profile_id (
                    username,
                    profile_name,
                    followers,
                    profile_image_url,
                    profile_image_path,
                    is_verified,
                    account_type
                )
            ''').eq('username', username)
            
            # Apply sorting
            if sort_by == 'popular':
                query = query.order('outlier_score', desc=True).order('view_count', desc=True)
            elif sort_by == 'recent':
                query = query.order('date_posted', desc=True)
            elif sort_by == 'oldest':
                query = query.order('date_posted', desc=False)
            
            # Apply pagination - request one extra to check for more data
            query = query.range(offset, offset + limit)
            
            response = query.execute()
            
            if not response.data:
                return {'reels': [], 'isLastPage': True}
            
            # Check if there are more pages
            has_more_data = len(response.data) > limit
            
            # Trim to exact limit
            data_to_return = response.data[:limit]
            
            # Transform for frontend with real profile data from the join
            transformed_reels = []
            for item in data_to_return:
                transformed_reels.append(self._transform_content_for_frontend(item))
            
            is_last_page = not has_more_data
            
            logger.info(f"✅ Returned {len(transformed_reels)} reels for {username}")
            
            return {
                'reels': transformed_reels,
                'isLastPage': is_last_page
            }
            
        except Exception as e:
            logger.error(f"❌ Error getting profile reels for {username}: {e}")
            raise HTTPException(status_code=500, detail=str(e))
    
    async def get_similar_profiles(self, username: str, limit: int = 20):
        """Get similar profiles for a username"""
        try:
            logger.info(f"Getting similar profiles for: {username}")
            
            # First, get the primary profile to get discovered_by_id
            primary_response = self.supabase.client.table('primary_profiles').select('id, username, profile_name, followers, mean_views, profile_primary_category').eq('username', username).execute()
            
            if not primary_response.data:
                raise HTTPException(status_code=404, detail="Profile not found")
            
            primary_profile = primary_response.data[0]
            primary_id = primary_profile['id']
            
            # Get similar profiles from secondary_profiles table
            similar_response = self.supabase.client.table('secondary_profiles').select('''
                username,
                full_name,
                biography,
                followers_count,
                profile_pic_url,
                profile_pic_path,
                is_verified,
                estimated_account_type,
                primary_category,
                secondary_category,
                tertiary_category,
                similarity_rank,
                discovered_by,
                external_url
            ''').eq('discovered_by_id', primary_id).order('similarity_rank').limit(limit).execute()
            
            similar_profiles = []
            for i, profile in enumerate(similar_response.data):
                # Get profile image URL
                profile_image_url = None
                if profile.get('profile_pic_path'):
                    profile_image_url = self.supabase.client.storage.from_('profile-images').get_public_url(profile['profile_pic_path'])
                elif profile.get('profile_pic_url'):
                    profile_image_url = profile['profile_pic_url']
                
                # Calculate similarity score (mock for now, since it's not stored directly)
                similarity_score = max(0.1, 1.0 - (i * 0.05))  # Decreasing similarity
                
                similar_profiles.append({
                    'username': profile['username'],
                    'profile_name': profile.get('full_name', profile['username']),
                    'followers': profile.get('followers_count', 0),
                    'average_views': 0,  # Not available in secondary profiles
                    'primary_category': profile.get('primary_category'),
                    'secondary_category': profile.get('secondary_category'),
                    'tertiary_category': profile.get('tertiary_category'),
                    'profile_image_url': profile_image_url,
                    'profile_image_local': profile_image_url,
                    'profile_pic_url': profile_image_url,  # For compatibility
                    'profile_pic_local': profile_image_url,  # For compatibility
                    'bio': profile.get('biography', ''),
                    'is_verified': profile.get('is_verified', False),
                    'total_reels': 0,  # Not available
                    'similarity_score': similarity_score,
                    'rank': i + 1,
                    'url': f"https://www.instagram.com/{profile['username']}/"
                })
            
            # Create response similar to what frontend expects
            result = {
                'success': True,
                'data': similar_profiles,
                'count': len(similar_profiles),
                'target_username': username,
                'target_profile': {
                    'username': primary_profile['username'],
                    'profile_name': primary_profile.get('profile_name', ''),
                    'followers': primary_profile.get('followers', 0),
                    'average_views': primary_profile.get('mean_views', 0),
                    'primary_category': primary_profile.get('profile_primary_category'),
                    'keywords_analyzed': 0  # Not available
                },
                'analysis_summary': {
                    'total_profiles_compared': len(similar_profiles),
                    'profiles_with_similarity': len(similar_profiles),
                    'target_keywords_count': 0,  # Not available
                    'top_score': similar_profiles[0]['similarity_score'] if similar_profiles else 0
                }
            }
            
            logger.info(f"✅ Found {len(similar_profiles)} similar profiles for {username}")
            
            return result
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"❌ Error getting similar profiles for {username}: {e}")
            raise HTTPException(status_code=500, detail=str(e))
    
    async def reset_session(self, session_id: str):
        """Reset random session"""
        try:
            if session_id in session_storage:
                del session_storage[session_id]
                logger.info(f"✅ Reset session: {session_id}")
                return {'message': 'Session reset successfully'}
            else:
                return {'message': 'Session not found'}
        except Exception as e:
            logger.error(f"❌ Error resetting session {session_id}: {e}")
            raise HTTPException(status_code=500, detail=str(e))

# Initialize API
try:
    api = ViralSpotAPI()
    API_AVAILABLE = True
except Exception as e:
    print(f"❌ Failed to initialize API: {e}")
    api = None
    API_AVAILABLE = False

# FastAPI app
app = FastAPI(
    title="ViralSpot API",
    description="Backend API for ViralSpot Instagram Analytics Platform",
    version="1.0.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify your frontend domain
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Dependency to check API availability
def get_api():
    if not API_AVAILABLE or not api:
        raise HTTPException(status_code=503, detail="API not available. Check Supabase configuration.")
    return api

# API Routes

@app.get("/")
async def root():
    """Root endpoint"""
    return {"message": "ViralSpot API", "status": "running", "supabase_available": API_AVAILABLE}

@app.get("/api/reels")
async def get_reels(
    search: Optional[str] = Query(None),
    primary_categories: Optional[str] = Query(None),
    secondary_categories: Optional[str] = Query(None),
    tertiary_categories: Optional[str] = Query(None),
    keywords: Optional[str] = Query(None),
    min_outlier_score: Optional[float] = Query(None),
    max_outlier_score: Optional[float] = Query(None),
    min_views: Optional[int] = Query(None),
    max_views: Optional[int] = Query(None),
    min_followers: Optional[int] = Query(None),
    max_followers: Optional[int] = Query(None),
    min_likes: Optional[int] = Query(None),
    max_likes: Optional[int] = Query(None),
    min_comments: Optional[int] = Query(None),
    max_comments: Optional[int] = Query(None),
    date_range: Optional[str] = Query(None),
    is_verified: Optional[bool] = Query(None),
    random_order: Optional[bool] = Query(False),
    session_id: Optional[str] = Query(None),
    sort_by: Optional[str] = Query(None, regex="^(popular|views|likes|comments|recent|oldest|followers|account_engagement|content_engagement)$"),
    excluded_usernames: Optional[str] = Query(None),
    # New filter fields
    account_types: Optional[str] = Query(None),
    content_types: Optional[str] = Query(None),
    languages: Optional[str] = Query(None),
    content_styles: Optional[str] = Query(None),
    min_account_engagement_rate: Optional[float] = Query(None, ge=0.0, le=100.0),
    max_account_engagement_rate: Optional[float] = Query(None, ge=0.0, le=100.0),
    limit: int = Query(24, ge=1, le=100),
    offset: int = Query(0, ge=0),
    api_instance: ViralSpotAPI = Depends(get_api)
):
    """Get reels with filtering and pagination"""
    filters = ReelFilter(
        search=search,
        primary_categories=primary_categories,
        secondary_categories=secondary_categories,
        tertiary_categories=tertiary_categories,
        keywords=keywords,
        min_outlier_score=min_outlier_score,
        max_outlier_score=max_outlier_score,
        min_views=min_views,
        max_views=max_views,
        min_followers=min_followers,
        max_followers=max_followers,
        min_likes=min_likes,
        max_likes=max_likes,
        min_comments=min_comments,
        max_comments=max_comments,
        date_range=date_range,
        is_verified=is_verified,
        random_order=random_order,
        session_id=session_id,
        sort_by=sort_by,
        excluded_usernames=excluded_usernames,
        account_types=account_types,
        content_types=content_types,
        languages=languages,
        content_styles=content_styles,
        min_account_engagement_rate=min_account_engagement_rate,
        max_account_engagement_rate=max_account_engagement_rate
    )
    result = await api_instance.get_reels(filters, limit, offset)
    return APIResponse(success=True, data=result)

@app.get("/api/posts")
async def get_posts(
    search: Optional[str] = Query(None),
    primary_categories: Optional[str] = Query(None),
    secondary_categories: Optional[str] = Query(None),
    keywords: Optional[str] = Query(None),
    min_outlier_score: Optional[float] = Query(None),
    max_outlier_score: Optional[float] = Query(None),
    min_likes: Optional[int] = Query(None),
    max_likes: Optional[int] = Query(None),
    min_comments: Optional[int] = Query(None),
    max_comments: Optional[int] = Query(None),
    date_range: Optional[str] = Query(None),
    is_verified: Optional[bool] = Query(None),
    random_order: Optional[bool] = Query(False),
    session_id: Optional[str] = Query(None),
    sort_by: Optional[str] = Query(None, regex="^(popular|likes|comments|recent|oldest)$"),
    excluded_usernames: Optional[str] = Query(None),
    limit: int = Query(24, ge=1, le=100),
    offset: int = Query(0, ge=0),
    api_instance: ViralSpotAPI = Depends(get_api)
):
    """Get posts with filtering and pagination (likes-based)"""
    filters = ReelFilter(
        search=search,
        primary_categories=primary_categories,
        secondary_categories=secondary_categories,
        keywords=keywords,
        min_outlier_score=min_outlier_score,
        max_outlier_score=max_outlier_score,
        min_likes=min_likes,
        max_likes=max_likes,
        min_comments=min_comments,
        max_comments=max_comments,
        date_range=date_range,
        is_verified=is_verified,
        random_order=random_order,
        session_id=session_id,
        sort_by=sort_by,
        excluded_usernames=excluded_usernames,
        content_types='post'
    )
    result = await api_instance.get_reels(filters, limit, offset)
    return APIResponse(success=True, data=result)

@app.get("/api/filter-options")
async def get_filter_options(api_instance: ViralSpotAPI = Depends(get_api)):
    """Get available filter options"""
    result = await api_instance.get_filter_options()
    return APIResponse(success=True, data=result)

@app.get("/api/profile/{username}")
async def get_profile(
    username: str = Path(..., description="Instagram username"),
    api_instance: ViralSpotAPI = Depends(get_api)
):
    """Get profile data"""
    result = await api_instance.get_profile(username)
    return APIResponse(success=True, data=result)

@app.get("/api/profile/{username}/reels")
async def get_profile_reels(
    username: str = Path(..., description="Instagram username"),
    sort_by: str = Query("popular", regex="^(popular|recent|oldest)$"),
    limit: int = Query(24, ge=1, le=100),
    offset: int = Query(0, ge=0),
    api_instance: ViralSpotAPI = Depends(get_api)
):
    """Get reels for a specific profile"""
    result = await api_instance.get_profile_reels(username, sort_by, limit, offset)
    return APIResponse(success=True, data=result)

@app.get("/api/profile/{username}/similar")
async def get_similar_profiles(
    username: str = Path(..., description="Instagram username"),
    limit: int = Query(20, ge=1, le=100),
    api_instance: ViralSpotAPI = Depends(get_api)
):
    """Get similar profiles for a username"""
    result = await api_instance.get_similar_profiles(username, limit)
    return result  # Already formatted with success/data structure

@app.get("/api/profile/{username}/secondary")
async def get_secondary_profile(
    username: str = Path(..., description="Instagram username"),
    api_instance: ViralSpotAPI = Depends(get_api)
):
    """Get secondary profile data for loading state"""
    result = await api_instance.get_secondary_profile(username)
    if result:
        return APIResponse(success=True, data=result)
    else:
        raise HTTPException(status_code=404, detail="Secondary profile not found")

@app.post("/api/profile/{username}/request")
async def request_profile_processing(
    username: str = Path(..., description="Instagram username"),
    source: str = Query("frontend", description="Source of the request"),
    api_instance: ViralSpotAPI = Depends(get_api)
):
    """Request high priority processing for a profile"""
    result = await api_instance.request_profile_processing(username, source)
    return APIResponse(success=True, data=result)

@app.get("/api/profile/{username}/status")
async def check_profile_status(
    username: str = Path(..., description="Instagram username"),
    api_instance: ViralSpotAPI = Depends(get_api)
):
    """Check profile processing status"""
    result = await api_instance.check_profile_status(username)
    return APIResponse(success=True, data=result)

@app.post("/api/reset-session")
async def reset_session(
    session_id: str = Query(..., description="Session ID to reset"),
    api_instance: ViralSpotAPI = Depends(get_api)
):
    """Reset random session"""
    result = await api_instance.reset_session(session_id)
    return APIResponse(success=True, data=result)

# Simple Similar Profiles endpoints
@app.get("/api/profile/{username}/similar-fast")
async def get_similar_profiles_fast(
    username: str = Path(..., description="Instagram username"),
    limit: int = Query(20, description="Number of similar profiles to return", ge=1, le=80),
    force_refresh: bool = Query(False, description="Force refresh from API")
):
    """
    Get similar profiles with fast caching (new optimized endpoint)
    
    This endpoint uses the new similar_profiles table for lightning-fast loading.
    Images are stored in Supabase bucket and served via CDN.
    
    Features:
    - Returns cached results instantly (24hr cache)
    - Supports 20-80 similar profiles per request
    - Optimized for batch operations
    - CDN-delivered profile images
    """
    if not SIMPLE_SIMILAR_API_AVAILABLE:
        raise HTTPException(
            status_code=503, 
            detail="Simple similar profiles API not available"
        )
    
    try:
        similar_api = get_similar_api()
        result = await similar_api.get_similar_profiles(username, limit, force_refresh)
        
        if result['success']:
            return APIResponse(
                success=True, 
                data=result['data'],
                message=f"Found {result['total']} similar profiles ({'cached' if result.get('cached') else 'fresh'})"
            )
        else:
            raise HTTPException(status_code=500, detail=result.get('error', 'Unknown error'))
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error in similar profiles fast endpoint: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.delete("/api/profile/{username}/similar-cache")
async def clear_similar_profiles_cache(
    username: str = Path(..., description="Instagram username")
):
    """Clear cached similar profiles for a username"""
    if not SIMPLE_SIMILAR_API_AVAILABLE:
        raise HTTPException(
            status_code=503, 
            detail="Simple similar profiles API not available"
        )
    
    try:
        similar_api = get_similar_api()
        result = await similar_api.clear_cache_for_profile(username)
        
        if result['success']:
            return APIResponse(success=True, data=result, message=result['message'])
        else:
            raise HTTPException(status_code=500, detail=result.get('error', 'Unknown error'))
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error clearing similar profiles cache: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/debug/profile/{username}")
async def debug_profile_fetch(
    username: str = Path(..., description="Username to test profile fetching")
):
    """Debug endpoint to test profile fetching directly"""
    if not SIMPLE_SIMILAR_API_AVAILABLE:
        raise HTTPException(
            status_code=503, 
            detail="Simple similar profiles API not available"
        )
    
    try:
        similar_api = get_similar_api()
        # Call the internal method directly for debugging
        profile_data = await similar_api._fetch_basic_profile_data(username)
        
        return APIResponse(
            success=True, 
            data={
                'username': username,
                'profile_data': profile_data,
                'api_available': profile_data is not None
            },
            message=f"Debug fetch for @{username}"
        )
            
    except Exception as e:
        logger.error(f"❌ Error in debug profile fetch: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/profile/{primary_username}/add-competitor/{target_username}")
async def add_manual_competitor(
    primary_username: str = Path(..., description="Primary username (the user adding competitors)"),
    target_username: str = Path(..., description="Target username to add as competitor")
):
    """
    Add a specific profile manually to competitors list
    
    This endpoint:
    - Fetches the target profile's basic info (name, image)
    - Downloads and stores profile image in Supabase bucket
    - Stores profile in similar_profiles table
    - Returns formatted profile data for frontend
    """
    if not SIMPLE_SIMILAR_API_AVAILABLE:
        raise HTTPException(
            status_code=503, 
            detail="Simple similar profiles API not available"
        )
    
    try:
        similar_api = get_similar_api()
        result = await similar_api.add_manual_profile(primary_username, target_username)
        
        if result['success']:
            return APIResponse(
                success=True, 
                data=result['data'],
                message=result['message']
            )
        else:
            raise HTTPException(status_code=404, detail=result.get('error', 'Profile not found'))
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error adding manual competitor: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# Health check endpoint
@app.post("/api/viral-ideas/queue")
async def create_viral_ideas_queue(request: ViralIdeasQueueRequest, api_instance: ViralSpotAPI = Depends(get_api)):
    """Create a new viral ideas analysis queue entry"""
    try:
        # Convert Pydantic model to dict for JSON storage
        content_strategy_json = {
            "contentType": request.content_strategy.contentType,
            "targetAudience": request.content_strategy.targetAudience,
            "goals": request.content_strategy.goals
        }
        
        # Insert into viral_ideas_queue table
        queue_result = api_instance.supabase.client.table('viral_ideas_queue').insert({
            'session_id': request.session_id,
            'primary_username': request.primary_username,
            'content_strategy': content_strategy_json,
            'status': 'pending',
            'priority': 5
        }).execute()
        
        if not queue_result.data:
            raise HTTPException(status_code=500, detail="Failed to create queue entry")
        
        queue_record = queue_result.data[0]
        queue_id = queue_record['id']
        
        # Insert competitors into viral_ideas_competitors table
        if request.selected_competitors:
            competitor_records = []
            for competitor_username in request.selected_competitors:
                competitor_records.append({
                    'queue_id': queue_id,
                    'competitor_username': competitor_username,
                    'selection_method': 'manual',
                    'is_active': True,
                    'processing_status': 'pending'
                })
            
            competitors_result = api_instance.supabase.client.table('viral_ideas_competitors').insert(competitor_records).execute()
            
            if not competitors_result.data:
                logger.warning(f"Failed to insert some competitors for queue {queue_id}")
        
        # Start analysis processing (you can implement this later)
        # await start_viral_analysis(queue_id)
        
        response = ViralIdeasQueueResponse(
            id=queue_id,
            session_id=request.session_id,
            primary_username=request.primary_username,
            status='pending',
            submitted_at=queue_record['submitted_at']
        )
        
        return APIResponse(
            success=True,
            data=response.dict(),
            message=f"Viral ideas analysis queued for @{request.primary_username}"
        )
        
    except Exception as e:
        logger.error(f"Error creating viral ideas queue: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to create queue: {str(e)}")

@app.get("/api/viral-ideas/queue/{session_id}")
async def get_viral_ideas_queue(session_id: str, api_instance: ViralSpotAPI = Depends(get_api)):
    """Get viral ideas queue status by session ID"""
    try:
        # Get queue record with competitors
        result = api_instance.supabase.client.table('viral_queue_summary').select('*').eq('session_id', session_id).execute()
        
        if not result.data:
            raise HTTPException(status_code=404, detail="Queue entry not found")
        
        queue_data = result.data[0]
        
        # Get competitors for this queue
        competitors_result = api_instance.supabase.client.table('viral_ideas_competitors').select('competitor_username, processing_status').eq('queue_id', queue_data['id']).eq('is_active', True).execute()
        
        competitors = [comp['competitor_username'] for comp in competitors_result.data] if competitors_result.data else []
        
        return APIResponse(
            success=True,
            data={
                'id': queue_data['id'],
                'session_id': queue_data['session_id'],
                'primary_username': queue_data['primary_username'],
                'status': queue_data['status'],
                'progress_percentage': queue_data['progress_percentage'],
                'content_type': queue_data['content_type'],
                'target_audience': queue_data['target_audience'],
                'main_goals': queue_data['main_goals'],
                'competitors': competitors,
                'submitted_at': queue_data['submitted_at'],
                'started_processing_at': queue_data['started_processing_at'],
                'completed_at': queue_data['completed_at']
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting viral ideas queue: {e}")
        raise HTTPException(status_code=500, detail="Failed to get queue status")

@app.get("/api/viral-ideas/check-existing/{username}")
async def check_existing_analysis(username: str, api_instance: ViralSpotAPI = Depends(get_api)):
    """Check if there's already an existing analysis (completed or active) for a profile"""
    try:
        # First check for completed analyses (most recent)
        completed_result = api_instance.supabase.client.table('viral_ideas_queue').select('''
            id,
            session_id,
            primary_username,
            status,
            progress_percentage,
            submitted_at,
            started_processing_at,
            completed_at,
            error_message
        ''').eq('primary_username', username).eq('status', 'completed').order('completed_at', desc=True).limit(1).execute()
        
        if completed_result.data and len(completed_result.data) > 0:
            # Found a completed analysis - return it for immediate loading
            queue_item = completed_result.data[0]
            
            logger.info(f"✅ Found existing COMPLETED analysis for @{username}: queue_id={queue_item['id']}")
            
            return APIResponse(
                success=True,
                data={
                    'id': queue_item['id'],
                    'session_id': queue_item['session_id'],
                    'primary_username': queue_item['primary_username'],
                    'status': queue_item['status'],
                    'progress_percentage': queue_item.get('progress_percentage', 100),
                    'submitted_at': queue_item['submitted_at'],
                    'started_at': queue_item.get('started_processing_at'),
                    'completed_at': queue_item.get('completed_at'),
                    'error_message': queue_item.get('error_message'),
                    'analysis_type': 'completed'  # Flag to indicate this is completed
                },
                message=f"Found existing completed analysis for @{username}"
            )
        
        # If no completed analysis, check for active analyses (pending/processing)
        active_result = api_instance.supabase.client.table('viral_ideas_queue').select('''
            id,
            session_id,
            primary_username,
            status,
            progress_percentage,
            submitted_at,
            started_processing_at,
            completed_at,
            error_message
        ''').eq('primary_username', username).in_('status', ['pending', 'processing']).order('submitted_at', desc=True).limit(1).execute()
        
        if active_result.data and len(active_result.data) > 0:
            # Found an active analysis
            queue_item = active_result.data[0]
            
            logger.info(f"✅ Found existing ACTIVE analysis for @{username}: queue_id={queue_item['id']}, status={queue_item['status']}")
            
            return APIResponse(
                success=True,
                data={
                    'id': queue_item['id'],
                    'session_id': queue_item['session_id'],
                    'primary_username': queue_item['primary_username'],
                    'status': queue_item['status'],
                    'progress_percentage': queue_item.get('progress_percentage', 0),
                    'submitted_at': queue_item['submitted_at'],
                    'started_at': queue_item.get('started_processing_at'),
                    'completed_at': queue_item.get('completed_at'),
                    'error_message': queue_item.get('error_message'),
                    'analysis_type': 'active'  # Flag to indicate this is active
                },
                message=f"Found existing active analysis for @{username}"
            )
        else:
            # No analysis found (completed or active)
            logger.info(f"🔍 No existing analysis found for @{username}")
            raise HTTPException(status_code=404, detail="No existing analysis found")
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error checking existing analysis for @{username}: {e}")
        raise HTTPException(status_code=500, detail="Failed to check existing analysis")

@app.post("/api/viral-ideas/queue/{queue_id}/start")
async def start_viral_analysis(queue_id: str, api_instance: ViralSpotAPI = Depends(get_api)):
    """Mark viral ideas analysis as ready to be picked up by processor"""
    try:
        # Verify the queue entry exists but don't change status yet
        # The viral processor will change it to 'processing' when it actually starts
        check_result = api_instance.supabase.client.table('viral_ideas_queue').select('*').eq('id', queue_id).execute()
        
        if not check_result.data:
            raise HTTPException(status_code=404, detail="Queue entry not found")
        
        queue_item = check_result.data[0]
        
        # Just return success - the processor will pick up the 'pending' item
        return APIResponse(
            success=True,
            data={'queue_id': queue_id, 'status': queue_item['status']},
            message="Analysis queued successfully - processor will start shortly"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error starting viral analysis: {e}")
        raise HTTPException(status_code=500, detail="Failed to start analysis")

@app.post("/api/viral-ideas/queue/{queue_id}/process")
async def trigger_viral_analysis_processing(queue_id: str, api_instance: ViralSpotAPI = Depends(get_api)):
    """Trigger the actual viral ideas processing for a queue entry"""
    try:
        from viral_ideas_processor import ViralIdeasProcessor, ViralIdeasQueueItem
        
        # Get queue item details
        queue_result = api_instance.supabase.client.table('viral_queue_summary').select('*').eq('id', queue_id).execute()
        
        if not queue_result.data:
            raise HTTPException(status_code=404, detail="Queue entry not found")
        
        queue_data = queue_result.data[0]
        
        # Get competitors for this queue
        competitors_result = api_instance.supabase.client.table('viral_ideas_competitors').select('competitor_username').eq('queue_id', queue_id).eq('is_active', True).execute()
        
        competitors = [comp['competitor_username'] for comp in competitors_result.data] if competitors_result.data else []
        
        # Create queue item object
        queue_item = ViralIdeasQueueItem(
            id=queue_data['id'],
            session_id=queue_data['session_id'],
            primary_username=queue_data['primary_username'],
            competitors=competitors,
            content_strategy=queue_data.get('full_content_strategy', {}),
            status=queue_data['status'],
            priority=queue_data['priority']
        )
        
        # Start processing in background
        processor = ViralIdeasProcessor()
        
        # Use asyncio to run the processor in the background
        import asyncio
        asyncio.create_task(processor.process_queue_item(queue_item))
        
        return APIResponse(
            success=True,
            data={'queue_id': queue_id, 'status': 'processing_started'},
            message="Viral ideas processing started in background"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error triggering viral analysis processing: {e}")
        raise HTTPException(status_code=500, detail="Failed to start processing")

@app.post("/api/viral-ideas/process-pending")
async def process_pending_viral_ideas():
    """Process all pending viral ideas queue items"""
    try:
        from viral_ideas_processor import ViralIdeasQueueManager
        
        # Start processing in background
        queue_manager = ViralIdeasQueueManager()
        
        # Use asyncio to run the queue manager in the background
        import asyncio
        asyncio.create_task(queue_manager.process_pending_items())
        
        return APIResponse(
            success=True,
            data={'status': 'processing_started'},
            message="Processing of pending viral ideas queue items started"
        )
        
    except Exception as e:
        logger.error(f"Error processing pending viral ideas: {e}")
        raise HTTPException(status_code=500, detail="Failed to start processing")

@app.get("/api/viral-ideas/queue-status")
async def get_viral_ideas_queue_status(api_instance: ViralSpotAPI = Depends(get_api)):
    """Get overall viral ideas queue status and statistics"""
    try:
        # Get queue statistics
        pending_result = api_instance.supabase.client.table('viral_ideas_queue').select('id', count='exact').eq('status', 'pending').execute()
        processing_result = api_instance.supabase.client.table('viral_ideas_queue').select('id', count='exact').eq('status', 'processing').execute()
        completed_result = api_instance.supabase.client.table('viral_ideas_queue').select('id', count='exact').eq('status', 'completed').execute()
        failed_result = api_instance.supabase.client.table('viral_ideas_queue').select('id', count='exact').eq('status', 'failed').execute()
        
        # Get recent items
        recent_result = api_instance.supabase.client.table('viral_queue_summary').select(
            'id, primary_username, status, progress_percentage, current_step, submitted_at, '
            'content_type, target_audience, active_competitors_count'
        ).order('submitted_at', desc=True).limit(10).execute()
        
        return APIResponse(
            success=True,
            data={
                'statistics': {
                    'pending': pending_result.count,
                    'processing': processing_result.count,
                    'completed': completed_result.count,
                    'failed': failed_result.count,
                    'total': pending_result.count + processing_result.count + completed_result.count + failed_result.count
                },
                'recent_items': recent_result.data if recent_result.data else []
            }
        )
        
    except Exception as e:
        logger.error(f"Error getting viral ideas queue status: {e}")
        raise HTTPException(status_code=500, detail="Failed to get queue status")

# New endpoints for viral analysis results and content
@app.get("/api/viral-analysis/{queue_id}/results")
async def get_viral_analysis_results(
    queue_id: str,
    api_instance: ViralSpotAPI = Depends(get_api)
):
    """Get viral analysis results for a queue entry"""
    try:
        # Get the queue info first to get primary username
        queue_result = api_instance.supabase.client.table('viral_ideas_queue').select(
            'primary_username'
        ).eq('id', queue_id).execute()
        
        if not queue_result.data:
            raise HTTPException(status_code=404, detail="Queue not found")
        
        primary_username = queue_result.data[0]['primary_username']
        
        # Get primary profile data
        profile_result = api_instance.supabase.client.table('primary_profiles').select(
            'username, profile_name, bio, followers, posts_count, is_verified, '
            'profile_image_url, profile_image_path, account_type, total_reels, '
            'median_views, total_views, total_likes, total_comments'
        ).eq('username', primary_username).execute()
        
        profile_data = profile_result.data[0] if profile_result.data else {}
        
        # Get the latest analysis results for this queue
        analysis_result = api_instance.supabase.client.table('viral_analysis_results').select(
            'id, analysis_run, analysis_type, status, total_reels_analyzed, '
            'primary_reels_count, competitor_reels_count, transcripts_fetched, '
            'analysis_data, workflow_version, '
            'started_at, analysis_completed_at'
        ).eq('queue_id', queue_id).order('analysis_run', desc=True).limit(1).execute()
        
        if not analysis_result.data:
            raise HTTPException(status_code=404, detail="Analysis results not found")
        
        analysis_record = analysis_result.data[0]
        analysis_id = analysis_record['id']
        
        # Parse analysis_data from JSONB field
        analysis_data_json = analysis_record.get('analysis_data', '{}')
        if isinstance(analysis_data_json, str):
            try:
                analysis_data = json.loads(analysis_data_json)
            except (json.JSONDecodeError, TypeError):
                analysis_data = {}
        else:
            analysis_data = analysis_data_json or {}
        
        # Get reels used in analysis (with enhanced metadata from analysis_metadata)
        reels_result = api_instance.supabase.client.table('viral_analysis_reels').select(
            'content_id, reel_type, username, rank_in_selection, '
            'view_count_at_analysis, like_count_at_analysis, comment_count_at_analysis, '
            'transcript_completed, hook_text, power_words, analysis_metadata'
        ).eq('analysis_id', analysis_id).order('reel_type, rank_in_selection').execute()
        
        # Get primary user reels using the same JOIN approach as working endpoints
        primary_reels_result = api_instance.supabase.client.table('content').select('''
            *,
            primary_profiles!profile_id (
                username,
                profile_name,
                followers,
                profile_image_url,
                profile_image_path,
                is_verified,
                account_type
            )
        ''').eq('username', primary_username).order('view_count', desc=True).limit(50).execute()
        
        # Transform primary user reels using the same method as working endpoints
        if primary_reels_result.data:
            for i, reel in enumerate(primary_reels_result.data):
                primary_reels_result.data[i] = api_instance._transform_content_for_frontend(reel)
        
        # Get competitor usernames from the queue
        competitors_result = api_instance.supabase.client.table('viral_ideas_competitors').select(
            'competitor_username'
        ).eq('queue_id', queue_id).eq('is_active', True).execute()
        
        competitor_usernames = [comp['competitor_username'] for comp in competitors_result.data or []]
        
        # Get competitor reels from content table
        competitor_reels_result = None
        competitor_profiles_data = []
        
        if competitor_usernames:
            # Get competitor reels using the same JOIN approach as working /api/reels endpoint
            competitor_reels_result = api_instance.supabase.client.table('content').select('''
                *,
                primary_profiles!profile_id (
                    username,
                    profile_name,
                    followers,
                    profile_image_url,
                    profile_image_path,
                    is_verified,
                    account_type
                )
            ''').in_('username', competitor_usernames).order('outlier_score', desc=True).limit(100).execute()
            
            # Transform competitor reels using the same method as working endpoints
            competitor_profiles_data = []
            if competitor_reels_result.data:
                # Transform each reel using the working transformation method
                for i, reel in enumerate(competitor_reels_result.data):
                    competitor_reels_result.data[i] = api_instance._transform_content_for_frontend(reel)
                    
                    # Extract profile data for legacy compatibility (frontend expects separate profiles array)
                    if reel.get('primary_profiles'):
                        profile = reel['primary_profiles']
                        if profile and profile.get('username'):
                            # Add CDN URL for profile image
                            if profile.get('profile_image_path'):
                                profile['profile_image_url'] = api_instance.supabase.client.storage.from_('profile-images').get_public_url(profile['profile_image_path'])
                            competitor_profiles_data.append(profile)
        
        # Get scripts from viral_scripts table (if any exist there)
        scripts_result = api_instance.supabase.client.table('viral_scripts').select(
            'id, script_title, script_content, script_type, estimated_duration, '
            'target_audience, primary_hook, call_to_action, source_reels, script_structure, status'
        ).eq('analysis_id', analysis_id).order('created_at', desc=True).execute()
        
        # The analysis_data JSONB field contains the complete analysis results
        # Don't extract individual fields - the frontend should use the complete analysis_data object
        
        return APIResponse(
            success=True,
            data={
                'analysis': {
                    'id': analysis_id,
                    'status': analysis_record.get('status'),
                    'workflow_version': analysis_record.get('workflow_version'),
                    'started_at': analysis_record.get('started_at'),
                    'analysis_completed_at': analysis_record.get('analysis_completed_at'),
                    'total_reels_analyzed': analysis_record.get('total_reels_analyzed', 0),
                    'primary_reels_count': analysis_record.get('primary_reels_count', 0),
                    'competitor_reels_count': analysis_record.get('competitor_reels_count', 0),
                    'transcripts_fetched': analysis_record.get('transcripts_fetched', 0),
                },
                'primary_profile': {
                    'username': profile_data.get('username', primary_username),
                    'profile_name': profile_data.get('profile_name', ''),
                    'bio': profile_data.get('bio', ''),
                    'followers': profile_data.get('followers', 0),
                    'posts_count': profile_data.get('posts_count', 0),
                    'is_verified': profile_data.get('is_verified', False),
                    'profile_image_url': api_instance.supabase.client.storage.from_('profile-images').get_public_url(profile_data.get('profile_image_path', '')) if profile_data.get('profile_image_path') else profile_data.get('profile_image_url', ''),
                    'profile_image_path': profile_data.get('profile_image_path', ''),
                    'account_type': profile_data.get('account_type', 'Personal'),
                    'total_reels': profile_data.get('total_reels', 0),
                    'median_views': profile_data.get('median_views', 0),
                    'total_views': profile_data.get('total_views', 0),
                    'total_likes': profile_data.get('total_likes', 0),
                    'total_comments': profile_data.get('total_comments', 0)
                },
                'analyzed_reels': reels_result.data or [],
                'primary_user_reels': primary_reels_result.data or [],
                'competitor_reels': competitor_reels_result.data if competitor_reels_result else [],
                'competitor_profiles': competitor_profiles_data,
                'viral_scripts_table': scripts_result.data or [],  # Scripts from viral_scripts table
                
                # The complete analysis data from the JSONB field - this contains everything!
                'analysis_data': analysis_data,
                
                # Legacy compatibility - extract hooks for backward compatibility
                'viral_ideas': [
                    {
                        'id': f"hook_{i}",
                        'idea_text': hook.get('hook_text', ''),
                        'explanation': hook.get('adaptation_strategy', ''),
                        'confidence_score': hook.get('effectiveness_score', 0),
                        'power_words': hook.get('psychological_triggers', [])
                    }
                    for i, hook in enumerate(analysis_data.get('generated_hooks', []))
                ] if analysis_data.get('generated_hooks') else [],
                
                # Extract key sections for easier frontend access
                'profile_analysis': analysis_data.get('profile_analysis', {}),
                'generated_hooks': analysis_data.get('generated_hooks', []),
                'individual_reel_analyses': analysis_data.get('individual_reel_analyses', []),
                'complete_scripts': analysis_data.get('complete_scripts', []),
                'scripts_summary': analysis_data.get('scripts_summary', []),
                'analysis_summary': analysis_data.get('analysis_summary', {})
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting viral analysis results: {e}")
        raise HTTPException(status_code=500, detail="Failed to get analysis results")

@app.get("/api/viral-analysis/{queue_id}/content")
async def get_viral_analysis_content(
    queue_id: str,
    content_type: str = Query("all", regex="^(all|primary|competitor)$"),
    limit: int = Query(100, ge=1, le=200),
    offset: int = Query(0, ge=0),
    api_instance: ViralSpotAPI = Depends(get_api)
):
    """Get content/reels from viral analysis for grid display"""
    try:
        # Get the queue and analysis info
        queue_result = api_instance.supabase.client.table('viral_ideas_queue').select(
            'primary_username'
        ).eq('id', queue_id).execute()
        
        if not queue_result.data:
            raise HTTPException(status_code=404, detail="Queue not found")
        
        primary_username = queue_result.data[0]['primary_username']
        
        # Get the latest analysis for this queue
        analysis_result = api_instance.supabase.client.table('viral_analysis_results').select(
            'id'
        ).eq('queue_id', queue_id).order('analysis_run', desc=True).limit(1).execute()
        
        if not analysis_result.data:
            raise HTTPException(status_code=404, detail="Analysis not found")
        
        analysis_id = analysis_result.data[0]['id']
        
        if content_type == "primary":
            # Get all reels from the primary user
            query = api_instance.supabase.client.table('content').select(
                'content_id, shortcode, url, description, view_count, like_count, comment_count, '
                'date_posted, username, outlier_score, transcript, transcript_language, transcript_available'
            ).eq('username', primary_username)
            
            # Order by view count descending to show best performing first
            result = query.order('view_count', desc=True).range(offset, offset + limit - 1).execute()
            
            # Add reel_type for consistency
            reels = []
            for reel in result.data or []:
                reel['reel_type'] = 'primary'
                reels.append(reel)
            
        elif content_type == "competitor":
            # Get competitor usernames for this analysis
            competitors_result = api_instance.supabase.client.table('viral_ideas_competitors').select(
                'competitor_username'
            ).eq('queue_id', queue_id).eq('is_active', True).execute()
            
            if not competitors_result.data:
                return APIResponse(
                    success=True,
                    data={
                        'reels': [],
                        'total_count': 0,
                        'has_more': False
                    }
                )
            
            competitor_usernames = [comp['competitor_username'] for comp in competitors_result.data]
            
            # Get reels from all competitor users
            query = api_instance.supabase.client.table('content').select(
                'content_id, shortcode, url, description, view_count, like_count, comment_count, '
                'date_posted, username, outlier_score, transcript, transcript_language, transcript_available'
            ).in_('username', competitor_usernames)
            
            # Order by outlier score descending to show viral content first
            result = query.order('outlier_score', desc=True).range(offset, offset + limit - 1).execute()
            
            # Add reel_type for consistency
            reels = []
            for reel in result.data or []:
                reel['reel_type'] = 'competitor'
                reels.append(reel)
            
        else:  # "all"
            # Get both primary and competitor reels
            competitors_result = api_instance.supabase.client.table('viral_ideas_competitors').select(
                'competitor_username'
            ).eq('queue_id', queue_id).eq('is_active', True).execute()
            
            competitor_usernames = [comp['competitor_username'] for comp in competitors_result.data or []]
            all_usernames = [primary_username] + competitor_usernames
            
            query = api_instance.supabase.client.table('content').select(
                'content_id, shortcode, url, description, view_count, like_count, comment_count, '
                'date_posted, username, outlier_score, transcript, transcript_language, transcript_available'
            ).in_('username', all_usernames)
            
            result = query.order('outlier_score', desc=True).range(offset, offset + limit - 1).execute()
            
            # Add reel_type based on username
            reels = []
            for reel in result.data or []:
                reel['reel_type'] = 'primary' if reel['username'] == primary_username else 'competitor'
                reels.append(reel)
        
        return APIResponse(
            success=True,
            data={
                'reels': reels,
                'total_count': len(reels),
                'has_more': len(reels) == limit,
                'primary_username': primary_username
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting viral analysis content: {e}")
        raise HTTPException(status_code=500, detail="Failed to get analysis content")

@app.get("/api/content/competitor/{username}")
async def get_competitor_content(
    username: str,
    limit: int = Query(24, ge=1, le=100),
    offset: int = Query(0, ge=0),
    sort_by: str = Query("popular", regex="^(popular|recent|views|likes)$"),
    api_instance: ViralSpotAPI = Depends(get_api)
):
    """Get competitor content for grid display"""
    try:
        # Use the same JOIN as main reels endpoint to provide full profile data
        query = api_instance.supabase.client.table('content').select('''
            *,
            primary_profiles!profile_id (
                username,
                profile_name,
                bio,
                followers,
                profile_image_url,
                profile_image_path,
                is_verified,
                account_type
            )
        ''').eq('username', username)
        
        # Apply sorting
        if sort_by == "recent":
            query = query.order('date_posted', desc=True)
        elif sort_by == "views":
            query = query.order('view_count', desc=True)
        elif sort_by == "likes":
            query = query.order('like_count', desc=True)
        else:  # popular (default)
            query = query.order('outlier_score', desc=True)
        
        # Execute query with pagination
        result = query.range(offset, offset + limit - 1).execute()

        # Transform using the same method as working endpoints
        processed_reels = []
        for item in (result.data or []):
            transformed = api_instance._transform_content_for_frontend(item)
            if transformed:
                processed_reels.append(transformed)
        
        return APIResponse(
            success=True,
            data={
                'reels': processed_reels,
                'total_count': len(processed_reels),
                'has_more': len(result.data) == limit if result.data else False,
                'username': username,
                'sort_by': sort_by
            }
        )
        
    except Exception as e:
        logger.error(f"Error getting competitor content: {e}")
        raise HTTPException(status_code=500, detail="Failed to get competitor content")

@app.get("/api/content/user/{username}")
async def get_user_content(
    username: str,
    limit: int = Query(24, ge=1, le=100),
    offset: int = Query(0, ge=0),
    sort_by: str = Query("recent", regex="^(recent|popular|views|likes)$"),
    api_instance: ViralSpotAPI = Depends(get_api)
):
    """Get user's own content for grid display"""
    try:
        # Build query for user content with profile join for consistent profile data
        query = api_instance.supabase.client.table('content').select('''
            *,
            primary_profiles!profile_id (
                username,
                profile_name,
                bio,
                followers,
                profile_image_url,
                profile_image_path,
                is_verified,
                account_type
            )
        ''').eq('username', username)
        
        # Apply sorting  
        if sort_by == "popular":
            query = query.order('outlier_score', desc=True)
        elif sort_by == "views":
            query = query.order('view_count', desc=True)
        elif sort_by == "likes":
            query = query.order('like_count', desc=True)
        else:  # recent (default)
            query = query.order('date_posted', desc=True)
        
        # Execute query with pagination
        result = query.range(offset, offset + limit - 1).execute()

        # Transform using the same method as working endpoints
        processed_reels = []
        for item in (result.data or []):
            transformed = api_instance._transform_content_for_frontend(item)
            if transformed:
                processed_reels.append(transformed)
        
        return APIResponse(
            success=True,
            data={
                'reels': processed_reels,
                'total_count': len(processed_reels),
                'has_more': len(result.data) == limit if result.data else False,
                'username': username,
                'sort_by': sort_by
            }
        )
        
    except Exception as e:
        logger.error(f"Error getting user content: {e}")
        raise HTTPException(status_code=500, detail="Failed to get user content")

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "api_available": API_AVAILABLE,
        "simple_similar_api_available": SIMPLE_SIMILAR_API_AVAILABLE,
        "timestamp": datetime.utcnow().isoformat()
    }

if __name__ == "__main__":
    if not API_AVAILABLE:
        print("❌ Cannot start server: API not available")
        print("   Please check your Supabase configuration")
        exit(1)
    
    print("🚀 Starting ViralSpot API server...")
    print("📍 Endpoints available:")
    print("   GET  /api/reels")
    print("   GET  /api/posts")
    print("   GET  /api/filter-options")
    print("   GET  /api/profile/{username}")
    print("   GET  /api/profile/{username}/reels")
    print("   GET  /api/profile/{username}/similar")
    print("   GET  /api/profile/{username}/similar-fast ⚡ NEW FAST ENDPOINT")
    print("   POST /api/profile/{primary_username}/add-competitor/{target_username} ⚡ NEW")
    print("   GET  /api/debug/profile/{username} 🐛 DEBUG")
    print("   DELETE /api/profile/{username}/similar-cache")
    print("   GET  /api/profile/{username}/secondary")
    print("   POST /api/profile/{username}/request")
    print("   GET  /api/profile/{username}/status")
    print("   POST /api/reset-session")
    print("   🎯 VIRAL IDEAS QUEUE:")
    print("   POST /api/viral-ideas/queue ⚡ NEW - Create viral ideas analysis")
    print("   GET  /api/viral-ideas/queue/{session_id} ⚡ NEW - Get queue status")
    print("   POST /api/viral-ideas/queue/{queue_id}/start ⚡ NEW - Start analysis")
    print("   POST /api/viral-ideas/queue/{queue_id}/process ⚡ NEW - Trigger processing")
    print("   POST /api/viral-ideas/process-pending ⚡ NEW - Process all pending")
    print("   GET  /api/viral-ideas/queue-status ⚡ NEW - Get queue statistics")
    print("   🎯 VIRAL ANALYSIS RESULTS:")
    print("   GET  /api/viral-analysis/{queue_id}/results ⚡ NEW - Get analysis results")
    print("   GET  /api/viral-analysis/{queue_id}/content ⚡ NEW - Get analyzed content")
    print("   🎯 CONTENT GRID:")
    print("   GET  /api/content/competitor/{username} ⚡ NEW - Get competitor content")
    print("   GET  /api/content/user/{username} ⚡ NEW - Get user content")
    print(f"🌐 Server will be available at: http://localhost:8000")
    
    uvicorn.run(app, host="0.0.0.0", port=8000)