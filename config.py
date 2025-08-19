"""
Configuration Settings for Instagram Data Pipeline

This module contains all configuration settings, prompts, and constants used throughout 
the Instagram data processing pipeline.

Configuration Categories:
1. Debug and Logging Settings
2. API Configuration 
3. File and Directory Settings
4. OpenAI Prompts and Settings
5. Default Values and Fallbacks
6. Rate Limiting and Performance Settings
"""

import os

# ========================================================================================
# DEBUG AND LOGGING SETTINGS
# ========================================================================================

# Master debug flag - controls all debug output throughout the pipeline
DEBUG_MODE = os.getenv('DEBUG_MODE', 'false').lower() in ('true', '1', 'yes', 'on')

# Logging levels
LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO').upper()  # DEBUG, INFO, WARNING, ERROR
LOG_FORMAT = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
SAVE_DEBUG_RESPONSES = os.getenv('SAVE_DEBUG_RESPONSES', 'true').lower() in ('true', '1', 'yes', 'on')
PRINT_JSON_RESPONSES = DEBUG_MODE  # Only print full JSON in debug mode

# Helper function to determine if debug responses should be saved
def should_save_debug_responses():
    """
    Determine if debug responses should be saved to files.
    Returns False when using Supabase to avoid unnecessary file generation.
    """
    if not DEBUG_MODE or not SAVE_DEBUG_RESPONSES:
        return False
    
    # Import USE_SUPABASE here to avoid circular imports
    use_supabase = os.getenv('USE_SUPABASE', 'true').lower() in ('true', '1', 'yes', 'on')
    return not use_supabase

# ========================================================================================
# API CONFIGURATION SETTINGS
# ========================================================================================

# Environment variable names for API keys
ENV_RAPIDAPI_KEY = 'RAPIDAPI_KEY'
ENV_INSTAGRAM_SCRAPER_API_KEY = 'INSTAGRAM_SCRAPER_API_KEY'
ENV_SIMILAR_PROFILES_HOST = 'SIMILAR_PROFILES_HOST'

# API Hosts and Endpoints
DEFAULT_INSTAGRAM_SCRAPER_HOST = 'instagram-scraper-stable-api.p.rapidapi.com'
DEFAULT_SIMILAR_PROFILES_HOST = 'instagram-scraper-stable-api.p.rapidapi.com'
DEFAULT_INSTAGRAM_SCRAPER_SECONDARY_HOST = 'instagram-scraper-20251.p.rapidapi.com'

# API Timeouts (in seconds)
DEFAULT_API_TIMEOUT = 30
LONG_API_TIMEOUT = 60
REEL_FETCH_TIMEOUT = 30
API_REQUEST_TIMEOUT = 30

# API Limits
SIMILAR_PROFILES_LIMIT = 20

# Rate Limiting Settings
DEFAULT_RATE_LIMIT_DELAY = 1.0  # seconds between requests
RATE_LIMIT_BACKOFF_DELAY = 5.0  # seconds to wait after rate limit hit
MAX_RETRY_ATTEMPTS = 3

# Batch Processing Settings
DEFAULT_REEL_BATCH_SIZE = 4
DEFAULT_CATEGORIZATION_BATCH_SIZE = 20
DEFAULT_PROFILE_BATCH_SIZE = 3
MAX_CONCURRENT_REQUESTS = 5

# ========================================================================================
# FILE AND DIRECTORY SETTINGS
# ========================================================================================

# Directory names
IMAGES_DIR_NAME = 'images'
THUMBNAILS_DIR_NAME = 'thumbnails'
DEBUG_DIR_NAME = 'debug_responses'

# CSV File names
PRIMARY_PROFILE_CSV = 'primaryprofile.csv'
CONTENT_CSV = 'content.csv'
SECONDARY_PROFILE_CSV = 'secondary_profile.csv'
QUEUE_CSV_PATH = 'queue.csv'
PRIMARY_PROFILE_CSV_PATH = 'primaryprofile.csv'

# File operation settings
CSV_ENCODING = 'utf-8'
JSON_ENCODING = 'utf-8'
ENSURE_ASCII = False
JSON_INDENT = 2

# ========================================================================================
# PAGINATION AND LIMITS
# ========================================================================================

# Default counts for data fetching
DEFAULT_REEL_COUNT = 100
INITIAL_REEL_COUNT = 12  # For fast display
MAX_SIMILAR_PROFILES = 20
MAX_PAGINATION_PAGES = 20  # Safety limit

# Progressive fetching settings
PROGRESSIVE_FETCH_ENABLED = True
INITIAL_FETCH_PAGES = 1

# ========================================================================================
# IMAGE DOWNLOAD SETTINGS
# ========================================================================================

# Image download configuration
DOWNLOAD_IMAGES = True
DOWNLOAD_HD_IMAGES = True
IMAGE_DOWNLOAD_TIMEOUT = 30
MAX_IMAGE_SIZE_MB = 10

# User agent for image downloads
IMAGE_DOWNLOAD_USER_AGENT = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'

# ========================================================================================
# ERROR HANDLING AND VALIDATION SETTINGS
# ========================================================================================

# Error handling configuration
ENABLE_ERROR_RECOVERY = True
CONTINUE_ON_ERRORS = True
SAVE_ERROR_LOGS = True

# Validation settings
VALIDATE_SYSTEM_REQUIREMENTS = True
VALIDATE_PIPELINE_PREREQUISITES = True
STRICT_VALIDATION = False

# Fallback behavior
USE_FALLBACK_VALUES = True
CREATE_EMPTY_FILES_ON_ERROR = True

# ========================================================================================
# PIPELINE FLOW SETTINGS
# ========================================================================================

# Pipeline modes
HIGH_PRIORITY_MODE = 'high_priority'
LOW_PRIORITY_MODE = 'low_priority'
DEFAULT_PIPELINE_MODE = HIGH_PRIORITY_MODE

# Parallel processing settings
ENABLE_PARALLEL_PROCESSING = True
ENABLE_TRUE_PARALLEL_STARTUP = True
OPTIMIZE_FOR_SPEED = True

# Progress tracking
SHOW_PROGRESS_MESSAGES = True
DETAILED_PROGRESS_LOGGING = DEBUG_MODE

# ========================================================================================
# BRIGHT DATA API SETTINGS (for low priority mode)
# ========================================================================================

# Bright Data configuration
BRIGHT_DATA_BASE_URL = 'https://api.brightdata.com/datasets/v3'
BRIGHT_DATA_PROFILES_DATASET_ID = 'gd_l1vikfch901nx3by4'
BRIGHT_DATA_REELS_DATASET_ID = 'gd_lyclm20il4r5helnj'
BRIGHT_DATA_TIMEOUT = 1800  # 30 minutes
BRIGHT_DATA_MAX_RETRIES = 3
BRIGHT_DATA_RETRY_DELAY = 1.0

# ========================================================================================
# NETWORK CRAWLER CONFIGURATION
# ========================================================================================

# Discovery Settings
MAX_ACCOUNTS_TO_QUEUE = 4
MAX_DISCOVERY_ROUNDS = 5
PROFILES_PER_ROUND = 20
DISCOVERY_ROUND_DELAY = 2.0  # seconds between discovery rounds
RESET_USED_SEEDS_PER_SESSION = True

# Profile Selection Criteria
REQUIRE_MINIMUM_FOLLOWERS = True
MIN_FOLLOWERS = 1000
SELECTION_MULTIPLIER = 2.0

# Default Settings
DEFAULT_SEED_PROFILE = 'mindset.therapy'
DEFAULT_CRAWLER_PRIORITY = 'medium'

# Queue Processor Concurrency Settings
MAX_CONCURRENT_LOW_PRIORITY = 5
MAX_CONCURRENT_HIGH_PRIORITY = 3

# Queue Management Settings
PRESERVE_QUEUE_HISTORY = True  # Keep completed/failed items in queue.csv for history
CLEAR_QUEUE_ON_RESTART = False  # Don't clear the queue when adding new items

# ========================================================================================
# PERFORMANCE AND OPTIMIZATION SETTINGS
# ========================================================================================

# Memory management
ENABLE_GARBAGE_COLLECTION = True
BATCH_MEMORY_OPTIMIZATION = True

# Threading and concurrency
USE_SEMAPHORES = True
ENABLE_RATE_LIMITING = True
ADAPTIVE_BATCH_SIZING = True

# Cache settings
ENABLE_RESPONSE_CACHING = False
CACHE_DURATION_MINUTES = 60

# ========================================================================================
# OUTPUT AND REPORTING SETTINGS
# ========================================================================================

# Console output
SHOW_EMOJIS = True
COLORED_OUTPUT = True
PROGRESS_INDICATORS = True

# Summary reporting
SHOW_FINAL_SUMMARY = True
DETAILED_METRICS_REPORT = DEBUG_MODE
SHOW_CSV_STATUS = True

# Time tracking
TRACK_EXECUTION_TIME = True
SHOW_TIMING_BREAKDOWNS = DEBUG_MODE

# ========================================================================================
# PROFILE TYPE CLASSIFICATION (PROMPT 1)
# ========================================================================================

PROFILE_TYPE_CLASSIFICATION_PROMPT = """
Analyze this Instagram profile and determine the ACCOUNT TYPE ONLY.

Username: @{username}
Profile Name: {profile_name}
Bio: {bio}
Followers: {followers:,}

Determine if this is:
- "Influencer": Personal brand, individual creator, celebrity, public figure
- "Theme Page": Meme pages, quote pages, content aggregators, anonymous pages
- "Business Page": Companies, brands, services, organizations, official business accounts

Consider:
- Follower count and engagement patterns
- Bio language and branding
- Whether it's a personal brand vs company vs content aggregator
- Business indicators (contact info, services, products)

Return ONLY a JSON object:
{{
    "account_type": "Influencer|Theme Page|Business Page",
    "confidence": 0.95
}}
"""

# ========================================================================================
# PROFILE CONTENT CATEGORIZATION (PROMPT 2)
# ========================================================================================

PROFILE_CONTENT_CATEGORIZATION_PROMPT = """
Analyze this Instagram profile and categorize the CONTENT CATEGORIES ONLY.

Username: @{username}
Profile Name: {profile_name}
Bio: {bio}

Categorize the main content themes from these options:
Memes, Fails, Pranks, Challenges, Transformations, Reactions, ASMR, Satisfying, Talents, Stunts, Pets, Animals, Interviews, Compilations, Surveillance, Karma, Coincidences, Freakouts, Confrontations, Fights, Glitches, Flashbacks, Edits, Montages, Highlights, Motivation, Mindset, Fitness, Vlogging, Routines, Aesthetics, LipSync, Covers, Freestyles, Instruments, Skits, Impersonations, Comedy, Podcasting, Acting, Storytelling, Spokenword, Cinematics, Performing, Magic, Dance, Flashmobs, Busking, Beatboxing, Duets, Psychology, Therapy, Advice, Dating, Masculinity, Femininity, Careers, Finance, Entrepreneurship, Startups, Crypto, Economics, Documentaries, History, Science, Space, Technology, Language, Facts, Infographics, Conspiracies, News, Politics, Commentary, Debates, Luxury, Wealth, Interiors, Minimalism, Productivity, Proposals, Weddings, Parenting, Babies, Adoption, Kindness, Tearjerkers, Family, Relationships, Faith, Christianity, Islam, Spirituality, Horoscopes, Manifestation, Meditation, Mindfulness, Gratitude, Journaling, Resilience, Booktok, Anime, Kpop, Cosplay, Fandoms, Watches, Sneakers, Skateboarding, Parkour, Wrestling, JiuJitsu, Chess, Debating, Military, Bodycams, Firefighting, Prisons, Tattoos, Barbershop

IMPORTANT: You must provide exactly 3 different categories in order of relevance. If the content seems to only fit 1-2 categories, choose the most logical third category that could still apply to this profile, even if loosely related.

Provide 3 categories in order of relevance:
- Primary: Most dominant content theme
- Secondary: Second most common theme  
- Tertiary: Third theme (REQUIRED - choose the best fit even if less obvious)

Return ONLY a JSON object:
{{
    "primary_category": "main category",
    "secondary_category": "secondary category", 
    "tertiary_category": "tertiary category (REQUIRED)",
    "confidence": 0.95
}}
"""

# ========================================================================================
# REEL CONTENT CATEGORIZATION (PROMPT 3)
# ========================================================================================

REEL_CONTENT_CATEGORIZATION_PROMPT = """Analyze this Instagram reel caption and categorize the content with keywords.

Caption: {description}

Categorize from these options:
Memes, Fails, Pranks, Challenges, Transformations, Reactions, ASMR, Satisfying, Talents, Stunts, Pets, Animals, Interviews, Compilations, Surveillance, Karma, Coincidences, Freakouts, Confrontations, Fights, Glitches, Flashbacks, Edits, Montages, Highlights, Motivation, Mindset, Fitness, Vlogging, Routines, Aesthetics, LipSync, Covers, Freestyles, Instruments, Skits, Impersonations, Comedy, Podcasting, Acting, Storytelling, Spokenword, Cinematics, Performing, Magic, Dance, Flashmobs, Busking, Beatboxing, Duets, Psychology, Therapy, Advice, Dating, Masculinity, Femininity, Careers, Finance, Entrepreneurship, Startups, Crypto, Economics, Documentaries, History, Science, Space, Technology, Language, Facts, Infographics, Conspiracies, News, Politics, Commentary, Debates, Luxury, Wealth, Interiors, Minimalism, Productivity, Proposals, Weddings, Parenting, Babies, Adoption, Kindness, Tearjerkers, Family, Relationships, Faith, Christianity, Islam, Spirituality, Horoscopes, Manifestation, Meditation, Mindfulness, Gratitude, Journaling, Resilience, Booktok, Anime, Kpop, Cosplay, Fandoms, Watches, Sneakers, Skateboarding, Parkour, Wrestling, JiuJitsu, Chess, Debating, Military, Bodycams, Firefighting, Prisons, Tattoos, Barbershop

IMPORTANT: You must provide exactly 3 different categories in order of relevance. If the content seems to only fit 1-2 categories, choose the most logical third category that could still apply, even if loosely related.

Extract the 4 most relevant keywords from the caption that best describe this specific piece of content.

Provide:
- Primary: The most dominant category for this content
- Secondary: Second most relevant category 
- Tertiary: Third category (REQUIRED - choose the best fit even if less obvious)
- 4 specific keywords that describe THIS content (not generic terms)

Return ONLY a valid JSON object with this exact structure:
{{
    "primary_category": "main category",
    "secondary_category": "secondary category", 
    "tertiary_category": "tertiary category (REQUIRED)",
    "keywords": ["specific_keyword1", "specific_keyword2", "specific_keyword3", "specific_keyword4"],
    "confidence": 0.95
}}"""

# ========================================================================================
# CATEGORY FALLBACK MAPPINGS
# ========================================================================================

CATEGORY_FALLBACK_MAP = {
    # Viral & Visual Formats
    'Memes': ['Comedy', 'Entertainment', 'Viral'],
    'Fails': ['Comedy', 'Entertainment', 'Reactions'],
    'Pranks': ['Comedy', 'Entertainment', 'Challenges'],
    'Challenges': ['Entertainment', 'Pranks', 'Viral'],
    'Transformations': ['Motivation', 'Lifestyle', 'Fitness'],
    'Reactions': ['Entertainment', 'Comedy', 'Commentary'],
    'ASMR': ['Satisfying', 'Lifestyle', 'Wellness'],
    'Satisfying': ['ASMR', 'Lifestyle', 'Entertainment'],
    'Talents': ['Performing', 'Entertainment', 'Skills'],
    'Stunts': ['Entertainment', 'Challenges', 'Sports'],
    'Pets': ['Animals', 'Entertainment', 'Lifestyle'],
    'Animals': ['Pets', 'Nature', 'Entertainment'],
    'Interviews': ['Commentary', 'Educational', 'Podcasting'],
    'Compilations': ['Entertainment', 'Highlights', 'Montages'],
    'Surveillance': ['News', 'Documentary', 'Reality'],
    'Karma': ['Justice', 'Reactions', 'Entertainment'],
    'Coincidences': ['Entertainment', 'Reactions', 'Viral'],
    'Freakouts': ['Reactions', 'Entertainment', 'Drama'],
    'Confrontations': ['Drama', 'Reactions', 'News'],
    'Fights': ['Sports', 'Drama', 'Reality'],
    'Glitches': ['Technology', 'Comedy', 'Fails'],
    'Flashbacks': ['Nostalgia', 'Entertainment', 'History'],
    'Edits': ['Cinematics', 'Art', 'Entertainment'],
    'Montages': ['Edits', 'Cinematics', 'Entertainment'],
    'Highlights': ['Sports', 'Entertainment', 'Compilations'],
    
    # Creator-Led & Performance
    'Motivation': ['Mindset', 'Lifestyle', 'Psychology'],
    'Mindset': ['Motivation', 'Psychology', 'Lifestyle'],
    'Fitness': ['Health', 'Lifestyle', 'Motivation'],
    'Vlogging': ['Lifestyle', 'Entertainment', 'Storytelling'],
    'Routines': ['Lifestyle', 'Productivity', 'Wellness'],
    'Aesthetics': ['Art', 'Fashion', 'Lifestyle'],
    'LipSync': ['Music', 'Entertainment', 'Performance'],
    'Covers': ['Music', 'Performing', 'Entertainment'],
    'Freestyles': ['Music', 'Performing', 'Creativity'],
    'Instruments': ['Music', 'Performing', 'Art'],
    'Skits': ['Comedy', 'Acting', 'Entertainment'],
    'Impersonations': ['Comedy', 'Acting', 'Entertainment'],
    'Comedy': ['Entertainment', 'Skits', 'Humor'],
    'Podcasting': ['Educational', 'Commentary', 'Storytelling'],
    'Acting': ['Performing', 'Entertainment', 'Art'],
    'Storytelling': ['Entertainment', 'Educational', 'Art'],
    'Spokenword': ['Poetry', 'Art', 'Performance'],
    'Cinematics': ['Art', 'Entertainment', 'Technology'],
    'Performing': ['Entertainment', 'Art', 'Music'],
    'Magic': ['Entertainment', 'Performance', 'Mystery'],
    'Dance': ['Performing', 'Entertainment', 'Music'],
    'Flashmobs': ['Dance', 'Entertainment', 'Performance'],
    'Busking': ['Music', 'Performance', 'Art'],
    'Beatboxing': ['Music', 'Performance', 'Talent'],
    'Duets': ['Music', 'Collaboration', 'Entertainment'],
    
    # Educational & Commentary
    'Psychology': ['Educational', 'Therapy', 'Science'],
    'Therapy': ['Psychology', 'Health', 'Wellness'],
    'Advice': ['Educational', 'Lifestyle', 'Relationships'],
    'Dating': ['Relationships', 'Advice', 'Lifestyle'],
    'Masculinity': ['Psychology', 'Lifestyle', 'Identity'],
    'Femininity': ['Psychology', 'Lifestyle', 'Identity'],
    'Careers': ['Business', 'Educational', 'Finance'],
    'Finance': ['Business', 'Educational', 'Economics'],
    'Entrepreneurship': ['Business', 'Finance', 'Motivation'],
    'Startups': ['Business', 'Entrepreneurship', 'Technology'],
    'Crypto': ['Finance', 'Technology', 'Investment'],
    'Economics': ['Finance', 'Educational', 'Business'],
    'Documentaries': ['Educational', 'News', 'History'],
    'History': ['Educational', 'Documentary', 'Culture'],
    'Science': ['Educational', 'Technology', 'Facts'],
    'Space': ['Science', 'Educational', 'Technology'],
    'Technology': ['Science', 'Educational', 'Innovation'],
    'Language': ['Educational', 'Culture', 'Communication'],
    'Facts': ['Educational', 'Science', 'Trivia'],
    'Infographics': ['Educational', 'Visual', 'Data'],
    'Conspiracies': ['Mystery', 'Commentary', 'Investigation'],
    'News': ['Current Events', 'Information', 'Politics'],
    'Politics': ['News', 'Commentary', 'Society'],
    'Commentary': ['Opinion', 'Analysis', 'Discussion'],
    'Debates': ['Discussion', 'Politics', 'Education'],
    
    # Lifestyle & Emotion
    'Luxury': ['Wealth', 'Lifestyle', 'Fashion'],
    'Wealth': ['Luxury', 'Finance', 'Success'],
    'Interiors': ['Design', 'Lifestyle', 'Aesthetics'],
    'Minimalism': ['Lifestyle', 'Design', 'Philosophy'],
    'Productivity': ['Lifestyle', 'Business', 'Self-Improvement'],
    'Proposals': ['Romance', 'Relationships', 'Weddings'],
    'Weddings': ['Romance', 'Lifestyle', 'Celebration'],
    'Parenting': ['Family', 'Lifestyle', 'Educational'],
    'Babies': ['Parenting', 'Family', 'Lifestyle'],
    'Adoption': ['Family', 'Parenting', 'Love'],
    'Kindness': ['Inspiration', 'Humanity', 'Positivity'],
    'Tearjerkers': ['Emotion', 'Inspiration', 'Drama'],
    'Family': ['Relationships', 'Lifestyle', 'Love'],
    'Relationships': ['Love', 'Advice', 'Psychology'],
    'Faith': ['Spirituality', 'Religion', 'Philosophy'],
    'Christianity': ['Faith', 'Religion', 'Spirituality'],
    'Islam': ['Faith', 'Religion', 'Spirituality'],
    'Spirituality': ['Faith', 'Philosophy', 'Wellness'],
    'Horoscopes': ['Spirituality', 'Mysticism', 'Prediction'],
    'Manifestation': ['Spirituality', 'Motivation', 'Philosophy'],
    'Meditation': ['Spirituality', 'Wellness', 'Mindfulness'],
    'Mindfulness': ['Meditation', 'Wellness', 'Psychology'],
    'Gratitude': ['Positivity', 'Spirituality', 'Wellness'],
    'Journaling': ['Self-Reflection', 'Wellness', 'Writing'],
    'Resilience': ['Motivation', 'Psychology', 'Strength'],
    
    # Niche Communities & Interests
    'Booktok': ['Reading', 'Literature', 'Community'],
    'Anime': ['Entertainment', 'Animation', 'Culture'],
    'Kpop': ['Music', 'Culture', 'Entertainment'],
    'Cosplay': ['Art', 'Entertainment', 'Creativity'],
    'Fandoms': ['Community', 'Entertainment', 'Culture'],
    'Watches': ['Fashion', 'Luxury', 'Collecting'],
    'Sneakers': ['Fashion', 'Culture', 'Collecting'],
    'Skateboarding': ['Sports', 'Culture', 'Lifestyle'],
    'Parkour': ['Sports', 'Fitness', 'Urban'],
    'Wrestling': ['Sports', 'Entertainment', 'Competition'],
    'JiuJitsu': ['Martial Arts', 'Sports', 'Discipline'],
    'Chess': ['Strategy', 'Competition', 'Intelligence'],
    'Debating': ['Education', 'Communication', 'Logic'],
    'Military': ['Service', 'Discipline', 'Honor'],
    'Bodycams': ['Reality', 'Law Enforcement', 'Documentation'],
    'Firefighting': ['Service', 'Heroes', 'Emergency'],
    'Prisons': ['Justice', 'Reality', 'System'],
    'Tattoos': ['Art', 'Expression', 'Culture'],
    'Barbershop': ['Grooming', 'Culture', 'Community'],
}

# ========================================================================================
# SUPABASE CONFIGURATION
# ========================================================================================

# Supabase Integration Settings
USE_SUPABASE = os.getenv('USE_SUPABASE', 'true').lower() in ('true', '1', 'yes', 'on')
KEEP_LOCAL_CSV = os.getenv('KEEP_LOCAL_CSV', 'false').lower() in ('true', '1', 'yes', 'on')  # Default to false
UPLOAD_IMAGES_TO_SUPABASE = os.getenv('UPLOAD_IMAGES_TO_SUPABASE', 'true').lower() in ('true', '1', 'yes', 'on')

# Supabase Storage Settings
PROFILE_IMAGES_BUCKET = os.getenv('PROFILE_IMAGES_BUCKET', 'profile-images')
CONTENT_THUMBNAILS_BUCKET = os.getenv('CONTENT_THUMBNAILS_BUCKET', 'content-thumbnails')

# Database Settings
DB_BATCH_SIZE = int(os.getenv('DB_BATCH_SIZE', '100'))
DB_MAX_RETRIES = int(os.getenv('DB_MAX_RETRIES', '3'))
DB_RETRY_DELAY = float(os.getenv('DB_RETRY_DELAY', '1.0'))

# ========================================================================================
# APPLICATION CONFIGURATION
# ========================================================================================

# Debug Mode Configuration
# Set to True for detailed logging and JSON debug files
# Set to False for minimal professional progress updates only
DEBUG_MODE = False

# ========================================================================================
# OPENAI API CONFIGURATION
# ========================================================================================

OPENAI_MODEL = "gpt-4.1"
OPENAI_TEMPERATURE = 0.2
OPENAI_MAX_TOKENS_PROFILE_TYPE = 100
OPENAI_MAX_TOKENS_PROFILE_CONTENT = 150
OPENAI_MAX_TOKENS_REEL_CONTENT = 200

# ========================================================================================
# HELPER FUNCTIONS
# ========================================================================================

def get_fallback_category(primary_category: str, secondary_category: str) -> str:
    """
    Get a fallback tertiary category based on primary and secondary categories.
    
    Args:
        primary_category: The primary category
        secondary_category: The secondary category
        
    Returns:
        A suitable tertiary category that's different from primary and secondary
    """
    fallback_options = CATEGORY_FALLBACK_MAP.get(primary_category, ['Lifestyle', 'Entertainment', 'Motivation'])
    
    for option in fallback_options:
        if option != primary_category and option != secondary_category:
            return option
    
    # Final fallback if no suitable option found
    return 'Entertainment'

def clean_json_response(response_text: str) -> str:
    """
    Clean OpenAI response text to ensure valid JSON.
    
    Args:
        response_text: Raw response text from OpenAI
        
    Returns:
        Cleaned response text ready for JSON parsing
    """
    if response_text.startswith('```json'):
        response_text = response_text.replace('```json', '').replace('```', '').strip()
    
    return response_text

# ========================================================================================
# DEFAULT VALUES
# ========================================================================================

DEFAULT_PROFILE_TYPE = {
    'account_type': 'Personal',
    'confidence': 0.5
}

DEFAULT_PROFILE_CATEGORIES = {
    'primary_category': 'Lifestyle',
    'secondary_category': 'Entertainment', 
    'tertiary_category': 'Motivation',
    'confidence': 0.5
}

DEFAULT_REEL_CATEGORIES = {
    'primary_category': 'Lifestyle',
    'secondary_category': 'Entertainment',
    'tertiary_category': 'Motivation',
    'keywords': ['content', 'social', 'media', 'post'],
    'confidence': 0.5
}