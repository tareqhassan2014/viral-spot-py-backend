#!/usr/bin/env python3
"""
Enhanced Instagram Network Discovery Crawler
=============================================

Intelligent, multi-round crawler that discovers Instagram profiles through
smart network expansion and queues them for processing via CSV-based queue system.

Enhanced Features:
- No database dependencies - purely CSV-based
- Integrates with production queue_processor.py
- Built-in RapidAPI integration for similar profile discovery
- Smart seed selection from existing primary profiles
- Multi-round discovery with different seed profiles per round
- Configurable limits and filtering
- Thread-safe CSV operations
- Intelligent fallback to default seed (mindset.therapy)

Enhanced Algorithm:
1. Check for existing primary profiles in primaryprofile.csv
2. If available, randomly select unused primary profiles as seeds
3. If no primary profiles, fall back to mindset.therapy
4. Use RapidAPI to find similar profiles for each seed
5. Select best profiles (excluding existing ones)
6. Loop with new primary profiles until target limit reached
7. Add to CSV queue for processing by queue_processor.py
8. Profiles get processed with LOW priority by default

Smart Seed Selection Logic:
- First: Check primaryprofile.csv for existing profiles
- Random: Randomly select from available primary profiles
- Fallback: Use mindset.therapy if no primary profiles
- Loop: Continue with different seeds until limit reached

Usage:
    from network_crawler import NetworkCrawler
    
    crawler = NetworkCrawler()
    
    # Enhanced multi-round discovery (automatic seed selection)
    summary = await crawler.start_discovery()
    
    # Backward compatible with manual seeds
    summary = await crawler.start_discovery(['seed_username'])
    
    # Add single profile
    crawler.add_profile_to_queue('username', priority='LOW')
"""

import asyncio
import json
import csv
import time
import requests
import random
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Set, Tuple
import logging
from dataclasses import dataclass
from pathlib import Path
import os

# Import centralized configuration
import config

# Import Supabase integration
try:
    from supabase_integration import SupabaseManager
    SUPABASE_AVAILABLE = True
except ImportError:
    SUPABASE_AVAILABLE = False
    print("⚠️ Supabase integration not available for crawler")

# Load environment variables from .env file
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    print("Warning: python-dotenv not installed. Install with: pip install python-dotenv")

# Setup basic logging using config
logging.basicConfig(level=getattr(logging, config.LOG_LEVEL), format=config.LOG_FORMAT)
logger = logging.getLogger(__name__)

@dataclass
class DiscoveryResult:
    """Result of a discovery operation"""
    seed_usernames: List[str]  # All usernames used as seeds
    total_rounds: int  # Number of discovery rounds performed
    total_similar_found: int  # Total similar profiles found across all rounds
    total_selected: int  # Total profiles selected across all rounds
    total_queued: int  # Total profiles successfully queued
    total_skipped_duplicates: int  # Total duplicates skipped across all rounds
    completed_at: str
    discovery_strategy: str  # How the seed profiles were chosen
    
    # Aliases for backward compatibility
    @property
    def similar_found(self) -> int:
        return self.total_similar_found
    
    @property
    def selected(self) -> int:
        return self.total_selected
    
    @property
    def queued(self) -> int:
        return self.total_queued
    
    @property
    def skipped_duplicates(self) -> int:
        return self.total_skipped_duplicates

class RapidAPIClient:
    """Self-contained RapidAPI client for similar profiles"""
    
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.getenv(config.ENV_RAPIDAPI_KEY) or os.getenv(config.ENV_INSTAGRAM_SCRAPER_API_KEY)
        if not self.api_key:
            logger.warning(f"⚠️ No RapidAPI key found. Set {config.ENV_RAPIDAPI_KEY} or {config.ENV_INSTAGRAM_SCRAPER_API_KEY} environment variable.")
        
        # Use the correct endpoint from environment or config
        self.api_host = os.getenv(config.ENV_SIMILAR_PROFILES_HOST, config.DEFAULT_SIMILAR_PROFILES_HOST)
        self.base_url = f"https://{self.api_host}"
        self.headers = {
            "X-RapidAPI-Key": self.api_key,
            "X-RapidAPI-Host": self.api_host
        }
    
    def get_similar_profiles(self, username: str, limit: int = None) -> List[Dict]:
        """Get similar profiles for a username with retry logic"""
        if not self.api_key:
            logger.error("❌ No RapidAPI key available")
            return []
        
        # Use config limit if not specified
        if limit is None:
            limit = config.SIMILAR_PROFILES_LIMIT
        
        max_attempts = 3  # 1 original + 2 retries for enhanced reliability
        
        for attempt in range(max_attempts):
            try:
                if attempt > 0:
                    logger.info(f"🔄 Retry attempt {attempt + 1}/{max_attempts} for similar profiles: @{username}")
                    # Progressive delay before retry: 2s, 4s, 6s
                    import time
                    delay = min(6, 2 * attempt + 2)
                    logger.info(f"⏱️ Waiting {delay}s before retry...")
                    time.sleep(delay)
                
                url = f"{self.base_url}/get_ig_similar_accounts.php?username_or_url={username}"
                
                response = requests.get(url, headers=self.headers, timeout=config.API_REQUEST_TIMEOUT)
                
                # Check for HTTP errors that should be retried
                if response.status_code >= 500:
                    # Server errors - should retry
                    raise requests.exceptions.HTTPError(f"Server error: {response.status_code}")
                elif response.status_code == 429:
                    # Rate limit - should retry
                    raise requests.exceptions.HTTPError(f"Rate limit: {response.status_code}")
                elif response.status_code >= 400:
                    # Client errors (except rate limit) - don't retry
                    logger.error(f"❌ Client error {response.status_code} for @{username}: {response.text}")
                    return []
                
                response.raise_for_status()
                
                try:
                    data = response.json()
                except ValueError as e:
                    # JSON parsing error - should retry
                    raise ValueError(f"Invalid JSON response: {e}")
                
                # Parse similar profiles - handle both list and dict formats (same logic as PrimaryProfileFetch.py)
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
                
                # Filter and return valid profiles only
                valid_profiles = []
                for profile in similar_profiles:
                    if isinstance(profile, dict) and profile.get('username'):
                        valid_profiles.append(profile)
                
                # Successful response - log results
                if attempt > 0:
                    logger.info(f"✅ Retry successful for @{username}: Found {len(valid_profiles)} similar profiles")
                else:
                    logger.info(f"🔍 Found {len(valid_profiles)} similar profiles for @{username}")
                
                # If we got profiles OR we're on the last attempt, return results
                if len(valid_profiles) > 0 or attempt == max_attempts - 1:
                    if len(valid_profiles) == 0 and attempt == max_attempts - 1:
                        logger.warning(f"⚠️ No similar profiles found for @{username} after {max_attempts} attempts")
                    return valid_profiles[:limit]
                else:
                    # Got 0 profiles but we can still retry
                    logger.warning(f"⚠️ Got 0 profiles for @{username} on attempt {attempt + 1}, will retry...")
                    continue
                
            except (requests.exceptions.RequestException, ValueError) as e:
                logger.warning(f"⚠️ Attempt {attempt + 1}/{max_attempts} failed for @{username}: {e}")
                if attempt == max_attempts - 1:
                    logger.error(f"❌ All {max_attempts} attempts failed for similar profiles @{username}")
                    return []
            except Exception as e:
                # Unexpected errors - don't retry
                logger.error(f"❌ Unexpected error getting similar profiles for @{username}: {e}")
                return []
        
        return []

class NetworkCrawler:
    """
    Enhanced Instagram network discovery crawler with config.py integration
    
    Features:
    1. RapidAPI integration for similar profile discovery
    2. CSV-based queue management  
    3. Smart seed selection from primary profiles
    4. Multi-round discovery with different seeds
    5. Deduplication against existing queue
    6. Integration with queue_processor.py
    7. Centralized configuration via config.py
    """
    
    def __init__(self, api_key: Optional[str] = None):
        # Initialize RapidAPI client with optional override
        self.rapid_api = RapidAPIClient(api_key)
        
        # Initialize Supabase if available
        self.supabase = None
        self.use_supabase = False
        if SUPABASE_AVAILABLE:
            try:
                self.supabase = SupabaseManager()
                self.use_supabase = self.supabase.use_supabase
                logger.info(f"✅ Crawler using: {'Supabase + CSV' if self.use_supabase else 'CSV only'}")
            except Exception as e:
                logger.warning(f"⚠️ Supabase not available for crawler: {e}")
                self.use_supabase = False
        
        # Only create queue CSV if Supabase is disabled or explicitly enabled
        if not self.use_supabase or (self.supabase and self.supabase.keep_local_csv):
            self._ensure_queue_csv_exists()
        
        # Track processed usernames to avoid duplicates
        self.existing_usernames: Set[str] = set()
        
        # Load existing usernames from queue and primary profiles
        if not self.use_supabase or (self.supabase and self.supabase.keep_local_csv):
            self._load_existing_usernames_from_queue()
        
        # Load existing primary profiles to avoid re-processing
        self._load_existing_usernames_from_primary_profiles()
        
        # Load existing secondary profiles to avoid re-processing
        self._load_existing_usernames_from_secondary_profiles()
        
        # Note: Supabase usernames will be loaded separately in create_crawler()
        
        # Track used seed profiles to avoid infinite loops
        self.used_seed_profiles: Set[str] = set()
        
        logger.info(f"🚀 NetworkCrawler initialized with config:")
        logger.info(f"   📋 Max accounts per discovery: {config.MAX_ACCOUNTS_TO_QUEUE}")
        logger.info(f"   🔄 Max rounds: {config.MAX_DISCOVERY_ROUNDS}")
        logger.info(f"   🌱 Default seed: @{config.DEFAULT_SEED_PROFILE}")
        logger.info(f"   📁 Primary profiles CSV: {config.PRIMARY_PROFILE_CSV_PATH}")
        logger.info(f"   ☁️ Supabase integration: {'ENABLED' if self.use_supabase else 'DISABLED'}")
    
    async def _load_existing_usernames_from_supabase(self):
        """Load existing usernames from Supabase queue"""
        if not self.use_supabase or not self.supabase:
            return
        
        try:
            # Get all usernames from queue table
            response = self.supabase.client.table('queue').select('username').execute()
            if response.data:
                for item in response.data:
                    username = item.get('username', '').strip().lower()
                    if username:
                        self.existing_usernames.add(username)
                logger.info(f"📊 Loaded {len(response.data)} usernames from Supabase queue")
        except Exception as e:
            logger.warning(f"Could not load usernames from Supabase: {e}")
    
    async def _load_existing_usernames_from_supabase_primary_profiles(self):
        """Load existing usernames from Supabase primary profiles to prevent re-processing"""
        if not self.use_supabase or not self.supabase:
            return
        
        initial_count = len(self.existing_usernames)
        
        try:
            # Get all usernames from primary_profiles table
            response = self.supabase.client.table('primary_profiles').select('username').execute()
            if response.data:
                for item in response.data:
                    username = item.get('username', '').strip().lower()
                    if username:
                        self.existing_usernames.add(username)
                
                new_count = len(self.existing_usernames) - initial_count
                logger.info(f"📊 Loaded {new_count} primary profile usernames from Supabase for deduplication")
        except Exception as e:
            logger.warning(f"Could not load primary profile usernames from Supabase: {e}")
    
    async def _load_existing_usernames_from_supabase_secondary_profiles(self):
        """Load existing usernames from Supabase secondary profiles to prevent re-processing"""
        if not self.use_supabase or not self.supabase:
            return
        
        initial_count = len(self.existing_usernames)
        
        try:
            # Get all usernames from secondary_profiles table
            response = self.supabase.client.table('secondary_profiles').select('username').execute()
            if response.data:
                for item in response.data:
                    username = item.get('username', '').strip().lower()
                    if username:
                        self.existing_usernames.add(username)
                
                new_count = len(self.existing_usernames) - initial_count
                logger.info(f"📊 Loaded {new_count} secondary profile usernames from Supabase for deduplication")
        except Exception as e:
            logger.warning(f"Could not load secondary profile usernames from Supabase: {e}")
    
    def _load_primary_profiles(self) -> List[Dict]:
        """Load existing primary profiles from CSV or Supabase"""
        primary_profiles = []
        
        # Try Supabase first if available
        if self.use_supabase and self.supabase:
            try:
                response = self.supabase.client.table('primary_profiles').select('username').execute()
                if response.data:
                    primary_profiles = response.data
                    logger.info(f"📊 Loaded {len(primary_profiles)} primary profiles from Supabase")
                    return primary_profiles
            except Exception as e:
                logger.warning(f"⚠️ Could not load from Supabase, falling back to CSV: {e}")
        
        # Fall back to CSV
        if not Path(config.PRIMARY_PROFILE_CSV_PATH).exists():
            logger.info(f"📄 No primary profiles CSV found at {config.PRIMARY_PROFILE_CSV_PATH}")
            return primary_profiles
        
        try:
            with open(config.PRIMARY_PROFILE_CSV_PATH, 'r', newline='', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    username = row.get('username', '').strip()
                    if username:
                        primary_profiles.append(row)
            
            logger.info(f"📊 Loaded {len(primary_profiles)} existing primary profiles from CSV")
            return primary_profiles
            
        except Exception as e:
            logger.warning(f"⚠️ Could not load primary profiles: {e}")
            return primary_profiles
    
    async def add_profile_to_queue_async(self, username: str, source: str = "crawler", priority: str = None) -> bool:
        """Async version of add_profile_to_queue for Supabase integration"""
        if self.is_duplicate_profile(username):
            logger.info(f"⏭️ Skipping @{username}: already in queue or processed")
            return False
        
        # Use config default priority if not specified
        if priority is None:
            priority = config.DEFAULT_CRAWLER_PRIORITY
        
        # Create queue item
        queue_item = {
            'username': username,
            'source': source,
            'priority': priority,
            'timestamp': datetime.now().isoformat(),
            'status': 'PENDING',
            'attempts': 0,
            'last_attempt': None,
            'error_message': None,
            'request_id': str(time.time_ns())[-8:]  # Simple ID
        }
        
        # Add to Supabase if available
        if self.use_supabase and self.supabase:
            try:
                success = await self.supabase.save_queue_item(queue_item)
                if success:
                    logger.info(f"☁️ Added @{username} to Supabase queue ({priority} priority)")
                    # Update tracking
                    self.existing_usernames.add(username.lower())
            except Exception as e:
                logger.error(f"❌ Failed to add @{username} to Supabase queue: {e}")
        
        # Add to CSV only if enabled or as fallback when Supabase fails
        if not self.use_supabase or (self.supabase and self.supabase.keep_local_csv):
            return self.add_profile_to_queue(username, source, priority)
        else:
            # Update tracking even when not saving to CSV
            self.existing_usernames.add(username.lower())
            return True
    
    # ======================================================================
    # CSV QUEUE MANAGEMENT
    # ======================================================================
    
    def _ensure_queue_csv_exists(self):
        """Create queue CSV with headers if it doesn't exist"""
        if not Path(config.QUEUE_CSV_PATH).exists():
            with open(config.QUEUE_CSV_PATH, 'w', newline='', encoding='utf-8') as f:
                writer = csv.DictWriter(f, fieldnames=[
                    'username', 'source', 'priority', 'timestamp', 'status',
                    'attempts', 'last_attempt', 'error_message', 'request_id'
                ])
                writer.writeheader()
            logger.info(f"📁 Created queue CSV: {config.QUEUE_CSV_PATH}")
    
    def _load_existing_usernames_from_queue(self):
        """Load existing usernames from queue CSV to prevent duplicates"""
        try:
            with open(config.QUEUE_CSV_PATH, 'r', newline='', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    username = row.get('username', '').strip().lower()
                    if username:
                        self.existing_usernames.add(username)
            
            logger.info(f"📊 Loaded {len(self.existing_usernames)} existing usernames from queue")
        except Exception as e:
            logger.warning(f"Could not load existing usernames: {e}")
    
    def _load_existing_usernames_from_primary_profiles(self):
        """Load existing usernames from primary profiles to prevent re-processing"""
        initial_count = len(self.existing_usernames)
        
        # Try Supabase first if available
        if self.use_supabase and self.supabase:
            try:
                response = self.supabase.client.table('primary_profiles').select('username').execute()
                if response.data:
                    for item in response.data:
                        username = item.get('username', '').strip().lower()
                        if username:
                            self.existing_usernames.add(username)
                    logger.info(f"📊 Loaded {len(response.data)} primary profile usernames from Supabase")
                    return
            except Exception as e:
                logger.warning(f"⚠️ Could not load primary profiles from Supabase: {e}")
        
        # Fall back to CSV
        try:
            if Path(config.PRIMARY_PROFILE_CSV_PATH).exists():
                with open(config.PRIMARY_PROFILE_CSV_PATH, 'r', newline='', encoding='utf-8') as f:
                    reader = csv.DictReader(f)
                    for row in reader:
                        username = row.get('username', '').strip().lower()
                        if username:
                            self.existing_usernames.add(username)
                
                new_count = len(self.existing_usernames) - initial_count
                logger.info(f"📊 Loaded {new_count} primary profile usernames from CSV")
            else:
                logger.info(f"📄 No primary profiles CSV found - no existing profiles to exclude")
        except Exception as e:
            logger.warning(f"Could not load primary profile usernames: {e}")
    
    def _load_existing_usernames_from_secondary_profiles(self):
        """Load existing usernames from secondary profiles to prevent re-processing"""
        initial_count = len(self.existing_usernames)
        
        # Try Supabase first if available
        if self.use_supabase and self.supabase:
            try:
                response = self.supabase.client.table('secondary_profiles').select('username').execute()
                if response.data:
                    for item in response.data:
                        username = item.get('username', '').strip().lower()
                        if username:
                            self.existing_usernames.add(username)
                    
                    new_count = len(self.existing_usernames) - initial_count
                    logger.info(f"📊 Loaded {new_count} secondary profile usernames from Supabase for deduplication")
                    return
            except Exception as e:
                logger.warning(f"⚠️ Could not load secondary profiles from Supabase: {e}")
        
        # Fall back to CSV
        try:
            if Path(config.SECONDARY_PROFILE_CSV).exists():
                with open(config.SECONDARY_PROFILE_CSV, 'r', newline='', encoding='utf-8') as f:
                    reader = csv.DictReader(f)
                    for row in reader:
                        username = row.get('username', '').strip().lower()
                        if username:
                            self.existing_usernames.add(username)
                
                new_count = len(self.existing_usernames) - initial_count
                logger.info(f"📊 Loaded {new_count} secondary profile usernames from CSV")
            else:
                logger.info(f"📄 No secondary profiles CSV found - no existing secondary profiles to exclude")
        except Exception as e:
            logger.warning(f"Could not load secondary profile usernames: {e}")
    
    # ======================================================================
    # PRIMARY PROFILE MANAGEMENT
    # ======================================================================
    
    def _load_primary_profiles(self) -> List[Dict]:
        """Load existing primary profiles from CSV"""
        primary_profiles = []
        
        if not Path(config.PRIMARY_PROFILE_CSV_PATH).exists():
            logger.info(f"📄 No primary profiles CSV found at {config.PRIMARY_PROFILE_CSV_PATH}")
            return primary_profiles
        
        try:
            with open(config.PRIMARY_PROFILE_CSV_PATH, 'r', newline='', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    username = row.get('username', '').strip()
                    if username:
                        primary_profiles.append(row)
            
            logger.info(f"📊 Loaded {len(primary_profiles)} existing primary profiles")
            return primary_profiles
            
        except Exception as e:
            logger.warning(f"⚠️ Could not load primary profiles: {e}")
            return primary_profiles
    
    def _get_available_seed_profiles(self) -> List[str]:
        """Get list of available primary profiles that haven't been used as seeds yet"""
        primary_profiles = self._load_primary_profiles()
        
        if not primary_profiles:
            return []
        
        # Filter out profiles we've already used as seeds
        available_profiles = []
        for profile in primary_profiles:
            username = profile.get('username', '').strip()
            if username and username.lower() not in self.used_seed_profiles:
                available_profiles.append(username)
        
        return available_profiles
    
    def get_resume_profile(self) -> str:
        """
        Get a profile to start discovery from using the enhanced logic:
        1. Check if primaryprofile.csv exists and has data
        2. If yes, randomly select an unused primary profile
        3. If no primary profiles or all used, fall back to default seed
        """
        # Get available primary profiles
        available_profiles = self._get_available_seed_profiles()
        
        if available_profiles:
            # Randomly select from available primary profiles
            selected_profile = random.choice(available_profiles)
            self.used_seed_profiles.add(selected_profile.lower())
            logger.info(f"🎲 Randomly selected primary profile: @{selected_profile} (from {len(available_profiles)} available)")
            return selected_profile
        else:
            # No primary profiles available, use default seed
            primary_profiles_count = len(self._load_primary_profiles())
            if primary_profiles_count > 0:
                logger.info(f"🔄 All {primary_profiles_count} primary profiles used as seeds, using default: @{config.DEFAULT_SEED_PROFILE}")
            else:
                logger.info(f"🌱 No primary profiles found, using default seed: @{config.DEFAULT_SEED_PROFILE}")
            
            self.used_seed_profiles.add(config.DEFAULT_SEED_PROFILE.lower())
            return config.DEFAULT_SEED_PROFILE
    
    def is_duplicate_profile(self, username: str) -> bool:
        """Check if profile already exists in queue OR has already been processed as a primary profile"""
        return username.lower() in self.existing_usernames
    
    def add_profile_to_queue(self, username: str, source: str = "crawler", priority: str = None) -> bool:
        """Add a profile to the CSV queue"""
        if self.is_duplicate_profile(username):
            logger.info(f"⏭️ Skipping @{username}: already in queue or processed")
            return False
        
        # Use config default priority if not specified
        if priority is None:
            priority = config.DEFAULT_CRAWLER_PRIORITY
        
        try:
            # Create new row data
            row_data = {
                'username': username,
                'source': source,
                'priority': priority,
                'timestamp': datetime.now().isoformat(),
                'status': 'PENDING',
                'attempts': '0',
                'last_attempt': '',
                'error_message': '',
                'request_id': str(time.time_ns())[-8:]  # Simple ID
            }
            
            # Check if file needs headers (empty or doesn't exist)
            file_needs_headers = False
            if not Path(config.QUEUE_CSV_PATH).exists():
                file_needs_headers = True
            else:
                # Check if file is empty or has no proper headers
                try:
                    with open(config.QUEUE_CSV_PATH, 'r', newline='', encoding='utf-8') as f:
                        content = f.read().strip()
                        if not content or not content.startswith('username'):
                            file_needs_headers = True
                        elif config.CLEAR_QUEUE_ON_RESTART:
                            # Only clear if explicitly configured to do so
                            file_needs_headers = True
                except:
                    file_needs_headers = True
            
            # Write headers if needed, preserving existing data
            if file_needs_headers:
                # Read existing data first (if any)
                existing_data = []
                try:
                    with open(config.QUEUE_CSV_PATH, 'r', newline='', encoding='utf-8') as f:
                        reader = csv.DictReader(f)
                        existing_data = [row for row in reader if row.get('username')]  # Filter out empty rows
                except:
                    existing_data = []
                
                # Write headers + existing data + new data
                with open(config.QUEUE_CSV_PATH, 'w', newline='', encoding='utf-8') as f:
                    writer = csv.DictWriter(f, fieldnames=row_data.keys())
                    writer.writeheader()
                    # Write existing data first
                    for row in existing_data:
                        writer.writerow(row)
                    # Write new data
                    writer.writerow(row_data)
            else:
                with open(config.QUEUE_CSV_PATH, 'a', newline='', encoding='utf-8') as f:
                    writer = csv.DictWriter(f, fieldnames=row_data.keys())
                    writer.writerow(row_data)
            
            # Update our tracking set
            self.existing_usernames.add(username.lower())
            
            logger.info(f"📋 Added @{username} to queue ({priority} priority)")
            return True
            
        except Exception as e:
            logger.error(f"❌ Failed to add @{username} to queue: {e}")
            return False
    

    
    # ======================================================================
    # MAIN DISCOVERY OPERATIONS
    # ======================================================================
    
    async def start_discovery(self, seed_usernames: List[str] = None) -> DiscoveryResult:
        """
        Enhanced multi-round discovery with intelligent seed selection:
        1. Check for existing primary profiles, randomly select if available
        2. Use mindset.therapy as fallback if no primary profiles
        3. Loop through multiple rounds using different primary profiles
        4. Continue until max_accounts_to_queue limit is reached
        
        Args:
            seed_usernames: Optional initial profiles (for backward compatibility)
            
        Returns:
            Discovery summary statistics across all rounds
        """
        logger.info(f"🚀 Starting ENHANCED multi-round discovery")
        logger.info(f"🎯 Target: queue max {config.MAX_ACCOUNTS_TO_QUEUE} profiles")
        logger.info(f"🔄 Max rounds: {config.MAX_DISCOVERY_ROUNDS}")
        
        # Initialize tracking variables
        all_seed_usernames = []
        total_rounds = 0
        total_similar_found = 0
        total_selected = 0
        total_queued = 0
        total_skipped_duplicates = 0
        discovery_strategy = ""
        
        # Clear used seeds for this discovery session (if configured)
        if config.RESET_USED_SEEDS_PER_SESSION:
            self.used_seed_profiles.clear()
        
        # Determine discovery strategy
        primary_profiles = self._load_primary_profiles()
        if primary_profiles:
            discovery_strategy = f"random_from_{len(primary_profiles)}_primary_profiles"
            logger.info(f"🎲 Strategy: Random selection from {len(primary_profiles)} existing primary profiles")
        else:
            discovery_strategy = "default_seed_fallback"
            logger.info(f"🌱 Strategy: No primary profiles found, using default seed")
        
        try:
            # Multi-round discovery loop
            while total_queued < config.MAX_ACCOUNTS_TO_QUEUE and total_rounds < config.MAX_DISCOVERY_ROUNDS:
                total_rounds += 1
                
                # Get next seed profile using enhanced logic
                if seed_usernames and total_rounds == 1:
                    # Use provided seed for first round (backward compatibility)
                    seed_username = seed_usernames[0]
                    self.used_seed_profiles.add(seed_username.lower())
                    logger.info(f"🔄 Round {total_rounds}: Using provided seed @{seed_username}")
                else:
                    # Use intelligent seed selection
                    seed_username = self.get_resume_profile()
                    logger.info(f"🔄 Round {total_rounds}: Intelligent seed selection → @{seed_username}")
                
                all_seed_usernames.append(seed_username)
                
                # Calculate remaining slots
                remaining_slots = config.MAX_ACCOUNTS_TO_QUEUE - total_queued
                round_target = min(remaining_slots, config.PROFILES_PER_ROUND)
                
                logger.info(f"📊 Round {total_rounds}: @{seed_username} → targeting {round_target} profiles ({total_queued}/{config.MAX_ACCOUNTS_TO_QUEUE} queued)")
                
                # Get similar profiles from RapidAPI
                logger.info(f"🔎 Round {total_rounds}: Discovering similar profiles for @{seed_username}")
                similar_profiles = self.rapid_api.get_similar_profiles(seed_username)
                
                if not similar_profiles:
                    logger.warning(f"🔄 Round {total_rounds}: No similar profiles found for @{seed_username}")
                    
                    # If we have no other seeds to try, break
                    if not self._get_available_seed_profiles() and seed_username == config.DEFAULT_SEED_PROFILE:
                        logger.warning(f"🛑 No more seed options available, ending discovery")
                        break
                    continue
                
                total_similar_found += len(similar_profiles)
                logger.info(f"✅ Round {total_rounds}: Found {len(similar_profiles)} similar profiles")
                
                # Filter and select best profiles for this round
                selected_profiles, round_skipped_duplicates = self._filter_and_select_profiles(similar_profiles, max_select=round_target)
                total_selected += len(selected_profiles)
                total_skipped_duplicates += round_skipped_duplicates
                
                logger.info(f"🎯 Round {total_rounds}: @{seed_username}: {len(similar_profiles)} → {len(selected_profiles)} selected, {round_skipped_duplicates} duplicates skipped")
                
                # Queue selected profiles for this round (use async if Supabase is enabled)
                round_queued = 0
                for profile_data in selected_profiles[:round_target]:
                    username = profile_data.get('username')
                    if username:
                        # Use async method if Supabase is available
                        if self.use_supabase:
                            success = await self.add_profile_to_queue_async(username, source="crawler", priority="LOW")
                        else:
                            success = self.add_profile_to_queue(username, source="crawler", priority="LOW")
                        
                        if success:
                            round_queued += 1
                            total_queued += 1
                            logger.info(f"📋 Round {total_rounds}: Queued @{username} ({round_queued}/{round_target} this round, {total_queued}/{config.MAX_ACCOUNTS_TO_QUEUE} total)")
                        
                        # Stop if we've reached the overall limit
                        if total_queued >= config.MAX_ACCOUNTS_TO_QUEUE:
                            break
                
                logger.info(f"✅ Round {total_rounds}: Completed - queued {round_queued} profiles")
                
                # Break if we've reached the target
                if total_queued >= config.MAX_ACCOUNTS_TO_QUEUE:
                    logger.info(f"🎯 TARGET REACHED: {total_queued}/{config.MAX_ACCOUNTS_TO_QUEUE} profiles queued")
                    break
                
                # Check if we have more seed options
                available_seeds = self._get_available_seed_profiles()
                if not available_seeds and total_rounds >= 1:
                    logger.info(f"🔄 No more seed profiles available, ending discovery at {total_queued} profiles")
                    break
                
                # Small delay between rounds to be API-friendly
                if total_rounds < config.MAX_DISCOVERY_ROUNDS:
                    await asyncio.sleep(config.DISCOVERY_ROUND_DELAY)
            
            # Create comprehensive result
            result = DiscoveryResult(
                seed_usernames=all_seed_usernames,
                total_rounds=total_rounds,
                total_similar_found=total_similar_found,
                total_selected=total_selected,
                total_queued=total_queued,
                total_skipped_duplicates=total_skipped_duplicates,
                completed_at=datetime.now().isoformat(),
                discovery_strategy=discovery_strategy
            )
            
            logger.info(f"🎉 ENHANCED DISCOVERY COMPLETE:")
            logger.info(f"   🔄 Rounds: {total_rounds}")
            logger.info(f"   🌱 Seeds used: {len(all_seed_usernames)} ({', '.join(['@' + u for u in all_seed_usernames])})")
            logger.info(f"   📊 Total found: {total_similar_found} similar profiles")
            logger.info(f"   🎯 Total queued: {total_queued}/{config.MAX_ACCOUNTS_TO_QUEUE} profiles")
            logger.info(f"   🚀 Strategy: {discovery_strategy}")
            logger.info(f"   ☁️ Storage: {'Supabase + CSV' if self.use_supabase else 'CSV only'}")
            
            return result
            
        except Exception as e:
            logger.error(f"❌ Error in enhanced discovery: {e}")
            return DiscoveryResult(
                seed_usernames=all_seed_usernames,
                total_rounds=total_rounds,
                total_similar_found=total_similar_found,
                total_selected=total_selected,
                total_queued=total_queued,
                total_skipped_duplicates=total_skipped_duplicates,
                completed_at=datetime.now().isoformat(),
                discovery_strategy=f"failed_{discovery_strategy}"
            )
    

    

    def _filter_and_select_profiles(self, similar_profiles: List[Dict], max_select: int = None) -> Tuple[List[Dict], int]:
        """Filter and select the best profiles for queuing"""
        if max_select is None:
            max_select = config.MAX_ACCOUNTS_TO_QUEUE
            
        logger.info(f"🎯 Filtering {len(similar_profiles)} profiles (max select: {max_select})")
        
        selected = []
        skipped_duplicates = 0
        
        for profile in similar_profiles:
            username = profile.get('username')
            followers = profile.get('followers', 0)
            
            # Skip if no username
            if not username:
                continue
            
            # Skip duplicates (queue + already processed)
            if self.is_duplicate_profile(username):
                logger.debug(f"⏭️ Skipping @{username}: already in queue or processed")
                skipped_duplicates += 1
                continue
            
            # Basic filtering - minimum followers (only if we have follower data and filtering is enabled)
            if config.REQUIRE_MINIMUM_FOLLOWERS and 'followers' in profile and followers < config.MIN_FOLLOWERS:
                logger.debug(f"⏭️ Skipping @{username}: only {followers} followers (min: {config.MIN_FOLLOWERS})")
                continue
            
            # Add to selected list
            selected.append(profile)
            if 'followers' in profile:
                logger.debug(f"✅ Selected @{username} ({followers:,} followers)")
            else:
                logger.debug(f"✅ Selected @{username}")
            
            # Stop when we have enough candidates (get extra to choose from)
            if len(selected) >= max_select * config.SELECTION_MULTIPLIER:
                break
        
        # Sort by followers count and take the best ones
        selected.sort(key=lambda x: x.get('followers', 0), reverse=True)
        selected = selected[:max_select]
        
        logger.info(f"🎯 Selected {len(selected)} profiles, skipped {skipped_duplicates} duplicates (queue + processed)")
        return selected, skipped_duplicates
    
    # ======================================================================
    # UTILITY METHODS
    # ======================================================================
    
    async def get_queue_stats(self) -> Dict:
        """Get statistics about the current queue from Supabase or CSV"""
        stats = {'total': 0, 'pending': 0, 'by_priority': {'HIGH': 0, 'LOW': 0}}
        
        # Try Supabase first
        if self.use_supabase and self.supabase:
            try:
                supabase_stats = await self.supabase.get_queue_stats()
                if supabase_stats:
                    return {
                        'total': supabase_stats.get('total_count', 0),
                        'pending': supabase_stats.get('pending_count', 0),
                        'by_priority': {
                            'HIGH': supabase_stats.get('high_priority_count', 0),
                            'LOW': supabase_stats.get('low_priority_count', 0)
                        },
                        'source': 'supabase'
                    }
            except Exception as e:
                logger.error(f"Error getting Supabase queue stats: {e}")
        
        # Fall back to CSV
        csv_stats = self.get_queue_stats_csv()
        csv_stats['source'] = 'csv'
        return csv_stats
    
    def get_queue_stats_csv(self) -> Dict:
        """Get statistics about the current queue from CSV only"""
        return self._get_queue_stats_from_csv()
    
    def _get_queue_stats_from_csv(self) -> Dict:
        """Get statistics about the current queue from CSV"""
        try:
            stats = {'total': 0, 'pending': 0, 'by_priority': {'HIGH': 0, 'LOW': 0}}
            
            with open(config.QUEUE_CSV_PATH, 'r', newline='', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    stats['total'] += 1
                    if row.get('status') == 'PENDING':
                        stats['pending'] += 1
                    priority = row.get('priority', 'LOW')
                    stats['by_priority'][priority] = stats['by_priority'].get(priority, 0) + 1
            
            return stats
        except Exception as e:
            logger.error(f"Error getting queue stats: {e}")
            return {}


# ======================================================================
# UTILITY FUNCTIONS
# ======================================================================

async def create_crawler(api_key: str = None) -> NetworkCrawler:
    """Factory function to create a configured crawler with config.py settings"""
    crawler = NetworkCrawler(api_key)
    # Load Supabase usernames if available (queue + primary + secondary profiles)
    if crawler.use_supabase:
        await crawler._load_existing_usernames_from_supabase()
        # Also load primary and secondary profiles from Supabase for complete deduplication
        await crawler._load_existing_usernames_from_supabase_primary_profiles()
        await crawler._load_existing_usernames_from_supabase_secondary_profiles()
    return crawler

async def add_profile_to_queue_async(username: str, source: str = "manual", priority: str = None) -> bool:
    """Async utility function to add a single profile to queue"""
    crawler = await create_crawler()
    return await crawler.add_profile_to_queue_async(username, source, priority)

# Keep sync version for backward compatibility
def add_profile_to_queue(username: str, source: str = "manual", priority: str = None) -> bool:
    """Utility function to add a single profile to queue"""
    crawler = NetworkCrawler()
    return crawler.add_profile_to_queue(username, source, priority)

# ======================================================================
# CLI INTERFACE
# ======================================================================

async def main():
    """CLI interface for enhanced network crawler with config.py"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Enhanced Instagram Network Crawler with config.py")
    parser.add_argument("--discover", nargs="*", help="Start discovery (optionally from specific seed usernames)")
    parser.add_argument("--add", type=str, help="Add single username to queue")
    parser.add_argument("--source", type=str, default="manual", help="Source of request")
    parser.add_argument("--priority", choices=["HIGH", "LOW"], default=None, help="Request priority (uses config default if not specified)")
    parser.add_argument("--stats", action="store_true", help="Show queue statistics")
    parser.add_argument("--api-key", type=str, help="RapidAPI key (or set RAPIDAPI_KEY env var)")
    parser.add_argument("--config", action="store_true", help="Show current configuration")
    
    args = parser.parse_args()
    
    if args.config:
        print("🔧 Current Configuration:")
        print(f"   📋 Max accounts per discovery: {config.MAX_ACCOUNTS_TO_QUEUE}")
        print(f"   🔄 Max discovery rounds: {config.MAX_DISCOVERY_ROUNDS}")
        print(f"   👥 Min followers: {config.MIN_FOLLOWERS}")
        print(f"   🌱 Default seed: @{config.DEFAULT_SEED_PROFILE}")
        print(f"   📁 Primary profiles CSV: {config.PRIMARY_PROFILE_CSV_PATH}")
        print(f"   📁 Queue CSV: {config.QUEUE_CSV_PATH}")
        print(f"   🎯 Default priority: {config.DEFAULT_CRAWLER_PRIORITY}")
        print(f"   🔄 Profiles per round: {config.PROFILES_PER_ROUND}")
        print(f"   ⏱️ Round delay: {config.DISCOVERY_ROUND_DELAY}s")
        print(f"   ☁️ Supabase: {'AVAILABLE' if SUPABASE_AVAILABLE else 'NOT AVAILABLE'}")
    
    elif args.add:
        success = await add_profile_to_queue_async(args.add, args.source, args.priority)
        priority_used = args.priority or config.DEFAULT_CRAWLER_PRIORITY
        if success:
            print(f"✅ Added @{args.add} to queue ({priority_used} priority)")
        else:
            print(f"❌ Failed to add @{args.add} to queue")
    
    elif args.stats:
        crawler = await create_crawler(args.api_key)
        stats = await crawler.get_queue_stats()
        print("📊 Queue Statistics:")
        print(json.dumps(stats, indent=2))
    
    elif args.discover is not None:  # Check for None to allow empty list
        crawler = await create_crawler(args.api_key)
        # Convert empty list to None for automatic seed selection
        seed_usernames = args.discover if args.discover else None
        result = await crawler.start_discovery(seed_usernames)
        print("🎉 Enhanced Discovery Summary:")
        print(f"   🌱 Seeds used: {len(result.seed_usernames)} ({', '.join(['@' + u for u in result.seed_usernames])})")
        print(f"   🔄 Rounds: {result.total_rounds}")
        print(f"   📊 Similar found: {result.total_similar_found}")
        print(f"   🎯 Selected: {result.total_selected}")
        print(f"   📋 Queued: {result.total_queued}")
        print(f"   ⏭️ Duplicates skipped: {result.total_skipped_duplicates}")
        print(f"   🚀 Strategy: {result.discovery_strategy}")
        print(f"   ⚙️ Target: {config.MAX_ACCOUNTS_TO_QUEUE} profiles, {config.MAX_DISCOVERY_ROUNDS} max rounds")
        print(f"   ☁️ Storage: Supabase + CSV" if crawler.use_supabase else "   💾 Storage: CSV only")
    
    else:
        print("Enhanced Instagram Network Crawler with Supabase")
        print("=" * 50)
        print("Usage:")
        print("  python network_crawler.py --discover                    # Auto seed selection")
        print("  python network_crawler.py --discover username1 username2 # Manual seeds")
        print("  python network_crawler.py --add username --priority HIGH")
        print("  python network_crawler.py --stats")
        print("  python network_crawler.py --config                      # Show configuration")
        print("")
        print("Configuration is managed via config.py")
        print(f"Current settings: {config.MAX_ACCOUNTS_TO_QUEUE} profiles, {config.MAX_DISCOVERY_ROUNDS} rounds max")
        print(f"Storage: {'Supabase + CSV' if SUPABASE_AVAILABLE else 'CSV only'}")

if __name__ == "__main__":
    asyncio.run(main())