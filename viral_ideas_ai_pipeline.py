"""
Viral Ideas AI Pipeline
======================

Python pipeline with EXACT prompts from N8N workflow that outputs
data in the format expected by our database schema.

Uses the same OpenAI pattern as the categorization system.
"""

import os
import json
import logging
import asyncio
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime
from openai import OpenAI
import re

# Import Supabase integration
try:
    from supabase_integration import SupabaseManager
    SUPABASE_AVAILABLE = True
except ImportError:
    SUPABASE_AVAILABLE = False

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ========================================================================================
# NEW HOOK-BASED WORKFLOW PROMPTS
# ========================================================================================

# STEP 1: PROFILE ANALYSIS PROMPT - Now imported from new_hook_workflow_prompts.py

# STEP 2: ENHANCED HOOK ANALYSIS PROMPT - Now imported from new_hook_workflow_prompts.py

AI_AGENT_ANALYSIS_PROMPT = """You are an Instagram Reels viral content analysis specialist. Analyze the reel data and generate viral insights.

Your task is to identify the most effective patterns, hooks, and strategies that make content go viral.

# Reel Data
{reel_data}

# Analysis Requirements
1. Identify the top 5 most effective hook patterns
2. Analyze engagement patterns and what drives high performance
3. Extract content themes that resonate with audiences
4. Provide actionable insights for creating viral content

# Output Format
Return a JSON object with this exact structure:

{{
    "analysis_summary": "Brief overview of key findings",
    "viral_score": 85,
    "top_hooks": [
        {{
            "pattern": "Hook pattern name",
            "effectiveness": 95,
            "examples": ["example 1", "example 2"],
            "why_it_works": "explanation"
        }}
    ],
    "engagement_patterns": {{
        "high_engagement_traits": ["trait1", "trait2", "trait3"],
        "optimal_length": "30-45 seconds",
        "best_posting_times": ["morning", "evening"],
        "content_structure": "hook-problem-solution-cta"
    }},
    "content_themes": [
        {{
            "theme": "Theme name",
            "popularity_score": 90,
            "target_audience": "audience description",
            "examples": ["example1", "example2"]
        }}
    ],
    "recommendations": [
        "Specific actionable recommendation 1",
        "Specific actionable recommendation 2"
    ]
}}"""

# STEP 3: HOOK GENERATION PROMPT
# Import the updated prompts from the dedicated prompts file
from new_hook_workflow_prompts import (
    PROFILE_ANALYSIS_PROMPT,
    ENHANCED_HOOK_ANALYSIS_PROMPT,
    HOOK_GENERATION_PROMPT,
    HOOK_SCRIPT_GENERATION_PROMPT
)

# Legacy prompt (to be removed)
OLD_HOOK_GENERATION_PROMPT = """# Viral Hook Replication Expert

You are a specialist at taking proven viral competitor hooks and adapting them for a specific creator while maintaining traceability.

## YOUR CRITICAL MISSION
You MUST generate exactly 5 hooks. No more, no less. Each hook must be based on a different competitor hook from the analysis provided.

## CRITICAL REQUIREMENTS
1. Generate EXACTLY 5 hooks - this is mandatory
2. Each hook MUST be directly inspired by a specific competitor hook
3. Each hook MUST reference the exact source reel ID it came from
4. Use different competitor hooks as sources (don't repeat the same source)
5. Show clear traceability from competitor → your adaptation

## Input Data

### Creator Profile Analysis
{profile_analysis}

### My Content Style (Learn from these transcripts)
{my_hook_analyses}

### Competitor Hook Analysis (SOURCE MATERIAL - adapt these)
{competitor_hook_analyses}

### My Speaking Style Reference
{my_reel_transcript}

## Generation Strategy
For each of the 5 hooks:
1. Pick ONE DIFFERENT competitor hook that performed well
2. Identify what made that hook effective 
3. Adapt it to match creator's content themes and speaking style
4. Maintain the psychological triggers and power words that worked
5. ALWAYS reference the source reel ID

## MANDATORY OUTPUT FORMAT
You MUST return exactly this structure with 5 hook objects:

[
    {{
        "hook_id": 1,
        "hook_text": "Your adapted version of the competitor hook",
        "original_competitor_hook": "Exact text of the competitor hook this is based on",
        "source_reel_id": "competitor_reel_database_id",
        "source_username": "competitor_username",
        "adaptation_strategy": "How you adapted their hook for this creator",
        "psychological_triggers": ["fear", "curiosity", "urgency"],
        "power_words_used": ["stop", "secret", "free", "thousands"],
        "estimated_effectiveness": 9.2,
        "why_it_works": "Why this competitor hook was successful + why your adaptation will work",
        "creator_voice_elements": ["specific elements that match creator's style"],
        "content_theme_alignment": "How this fits the creator's content themes",
        "hook_type": "question/statement/shocking_fact/problem/curiosity_gap"
    }},
    {{
        "hook_id": 2,
        "hook_text": "Second adapted hook based on different competitor",
        "original_competitor_hook": "Different competitor hook text",
        "source_reel_id": "different_competitor_reel_id",
        "source_username": "different_competitor_username",
        "adaptation_strategy": "Different adaptation approach",
        "psychological_triggers": ["different", "triggers"],
        "power_words_used": ["different", "power", "words"],
        "estimated_effectiveness": 8.8,
        "why_it_works": "Different explanation",
        "creator_voice_elements": ["different voice elements"],
        "content_theme_alignment": "Different theme alignment",
        "hook_type": "different_hook_type"
    }},
    {{
        "hook_id": 3,
        "hook_text": "Third adapted hook",
        "original_competitor_hook": "Third competitor hook",
        "source_reel_id": "third_reel_id",
        "source_username": "third_username",
        "adaptation_strategy": "Third strategy",
        "psychological_triggers": ["third", "triggers"],
        "power_words_used": ["third", "words"],
        "estimated_effectiveness": 9.0,
        "why_it_works": "Third explanation",
        "creator_voice_elements": ["third elements"],
        "content_theme_alignment": "Third alignment",
        "hook_type": "third_type"
    }},
    {{
        "hook_id": 4,
        "hook_text": "Fourth adapted hook",
        "original_competitor_hook": "Fourth competitor hook",
        "source_reel_id": "fourth_reel_id",
        "source_username": "fourth_username",
        "adaptation_strategy": "Fourth strategy",
        "psychological_triggers": ["fourth", "triggers"],
        "power_words_used": ["fourth", "words"],
        "estimated_effectiveness": 8.9,
        "why_it_works": "Fourth explanation",
        "creator_voice_elements": ["fourth elements"],
        "content_theme_alignment": "Fourth alignment",
        "hook_type": "fourth_type"
    }},
    {{
        "hook_id": 5,
        "hook_text": "Fifth adapted hook",
        "original_competitor_hook": "Fifth competitor hook",
        "source_reel_id": "fifth_reel_id",
        "source_username": "fifth_username",
        "adaptation_strategy": "Fifth strategy",
        "psychological_triggers": ["fifth", "triggers"],
        "power_words_used": ["fifth", "words"],
        "estimated_effectiveness": 9.1,
        "why_it_works": "Fifth explanation",
        "creator_voice_elements": ["fifth elements"],
        "content_theme_alignment": "Fifth alignment",
        "hook_type": "fifth_type"
    }}
]

## FINAL REMINDER
- You MUST generate exactly 5 hooks
- Each must use a different competitor hook as source
- Return only the JSON array, nothing else
- If you have fewer than 5 competitor hooks available, create variations or use similar patterns to reach exactly 5

ENSURE EVERY HOOK HAS CLEAR TRACEABILITY TO A SPECIFIC COMPETITOR REEL."""

# STEP 4: CREATOR-STYLE SCRIPT GENERATION PROMPT
HOOK_SCRIPT_GENERATION_PROMPT = """# Creator Voice Script Writer

You are a script writer who captures a creator's EXACT speaking style and tone from their transcripts.

## Your Mission
Write a script that sounds exactly like this creator would speak, using their vocabulary, phrasing, and delivery style.

## CRITICAL REQUIREMENTS
1. Study the creator's actual transcripts to match their speaking patterns
2. Use their typical words, phrases, and sentence structures
3. Match their energy level and presentation style
4. Maintain their authentic personality throughout
5. Apply the competitor's hook structure but in the creator's voice

## Input Data

### Hook to Develop (Competitor-inspired)
{hook_data}

### Creator's Actual Speaking Style (STUDY THESE CAREFULLY)
{creator_transcripts}

### Creator Profile & Themes
{profile_summary}

### Competitor Hook Pattern (Structure to follow)
{competitor_hook_pattern}

## Script Writing Strategy
1. **Voice Analysis**: Study how the creator speaks from their transcripts
   - What words do they use frequently?
   - How do they structure sentences?
   - What's their energy level and tone?
   - How do they transition between ideas?

2. **Hook Integration**: Take the competitor's hook strategy but rewrite it in the creator's voice

3. **Content Structure**: Use the viral pattern (Hook → Problem → Solution → CTA) but with creator's natural flow

## Output Format
{{
    "script": {{
        "title": "Script title matching creator's style",
        "hook_used": "The adapted hook in creator's voice",
        "full_script": "Complete script that sounds exactly like the creator would speak it",
        "structure_breakdown": {{
            "hook_section": "0-5 seconds: Hook in creator's style",
            "problem_section": "5-15 seconds: Problem using creator's language", 
            "solution_section": "15-45 seconds: Solution in creator's voice",
            "cta_section": "45-60 seconds: CTA matching creator's typical endings"
        }},
        "estimated_duration": 50,
        "creator_voice_elements": ["specific phrases/words from their transcripts used"],
        "speaking_pattern_match": "How this matches their natural speaking style",
        "energy_level": "matches creator's typical energy",
        "vocabulary_alignment": "uses creator's typical vocabulary"
    }},
    "voice_analysis": {{
        "typical_phrases": ["phrases the creator commonly uses"],
        "sentence_structure": "how they typically structure thoughts",
        "transition_words": ["how they move between ideas"],
        "energy_markers": ["words/phrases that show their personality"]
    }},
    "authenticity_score": {{
        "voice_match": 9.5,
        "vocabulary_accuracy": 9.2,
        "natural_flow": 9.0,
        "personality_capture": 9.3
    }}
}}

## Example Transformation
If creator typically says "Look, here's the thing..." and "But here's what's crazy..."
Don't write: "Today I want to share something amazing with you"
Do write: "Look, here's the thing that's absolutely crazy..."

MAKE IT SOUND LIKE THE CREATOR ACTUALLY WROTE AND WOULD SAY THIS."""

# ========================================================================================
# VIRAL IDEAS AI PROCESSOR
# ========================================================================================

class ViralIdeasAI:
    """AI Pipeline for viral ideas analysis using exact N8N workflow prompts"""
    
    def __init__(self):
        self.openai_client = self._init_openai()
        self.supabase = SupabaseManager() if SUPABASE_AVAILABLE else None
        
    def _init_openai(self) -> Optional[OpenAI]:
        """Initialize OpenAI client"""
        try:
            api_key = os.getenv('OPENAI_API_KEY')
            if not api_key:
                logger.error("OPENAI_API_KEY not found in environment variables")
                return None
            return OpenAI(api_key=api_key)
        except Exception as e:
            logger.error(f"Failed to initialize OpenAI client: {e}")
            return None
    
    async def process_analysis(self, analysis_id: str) -> bool:
        """NEW HOOK-BASED WORKFLOW - Main entry point"""
        try:
            logger.info(f"🤖 Starting NEW HOOK-BASED AI analysis for analysis_id: {analysis_id}")
            
            # Step 1: Get reel data and profile data
            reel_data = await self._get_analysis_reels(analysis_id)
            if not reel_data:
                logger.error("No reel data found for analysis")
                return False
            
            primary_username = await self._get_primary_username(analysis_id)
            profile_data = await self._get_profile_data(primary_username)
            
            # Step 2: Profile Analysis (100 primary reels)
            logger.info("📊 Step 2: Analyzing profile and content identity...")
            profile_analysis = await self._analyze_profile(primary_username, profile_data, reel_data)
            if not profile_analysis:
                logger.error("Profile analysis failed")
                return False
            
            # Step 3: Hook Analysis (Top 5 outliers from primary + competitors)
            logger.info("🎣 Step 3: Analyzing hooks from top outlier reels...")
            hook_analyses = await self._analyze_outlier_hooks(reel_data)
            if not hook_analyses:
                logger.error("Hook analysis failed")
                return False
            
            # Step 4: Generate 5 Hooks based on analysis
            logger.info("🚀 Step 4: Generating 5 custom hooks...")
            generated_hooks = await self._generate_hooks(profile_analysis, hook_analyses, reel_data)
            if not generated_hooks or len(generated_hooks) < 1:
                logger.error("Hook generation failed - expected at least 1 hook")
                return False
            logger.info(f"✅ Generated {len(generated_hooks)} hooks successfully")
            
            # Step 5: Generate Scripts for each hook (one script per hook based on competitor patterns)
            logger.info("📝 Step 5: Creating scripts for each hook...")
            hook_scripts = await self._generate_hook_scripts(generated_hooks, profile_analysis, hook_analyses, reel_data)
            if not hook_scripts or len(hook_scripts) < 1:
                logger.error("Script generation failed - expected at least 1 script")
                return False
            logger.info(f"✅ Generated {len(hook_scripts)} scripts successfully")
            
            # Step 6: Store all results in new flexible JSONB format
            logger.info("💾 Step 6: Storing analysis results in database...")
            await self._store_hook_analysis_results(analysis_id, profile_analysis, hook_analyses, generated_hooks, hook_scripts)
            
            logger.info(f"✅ NEW HOOK-BASED analysis completed for {analysis_id}")
            logger.info(f"   📊 Profile analyzed and stored")
            logger.info(f"   🎣 {len(hook_analyses)} hooks analyzed and stored") 
            logger.info(f"   🚀 {len(generated_hooks)} hooks generated and stored")
            logger.info(f"   📝 {len(hook_scripts)} scripts created and stored")
            logger.info(f"   💾 All data saved to flexible JSONB schema")
            return True
            
        except Exception as e:
            logger.error(f"Error in hook-based AI analysis: {e}")
            return False
    
    async def _get_analysis_reels(self, analysis_id: str) -> List[Dict[str, Any]]:
        """Get comprehensive reel data for analysis - enhanced for new flexible schema"""
        try:
            if not self.supabase:
                logger.error("Supabase not available")
                return []
            
            # Get reels selected for this analysis with analysis_metadata
            result = self.supabase.client.table('viral_analysis_reels').select('*').eq('analysis_id', analysis_id).execute()
            
            if not result.data:
                logger.error(f"No reels found for analysis_id: {analysis_id}")
                return []
            
            # Get comprehensive reel data with transcripts and metadata
            reels_with_transcripts = []
            for reel in result.data:
                content_id = reel.get('content_id')
                if content_id and reel.get('transcript_completed') == True:
                    # Get full content data including transcript and metadata
                    content_result = self.supabase.client.table('content').select(
                        'id, content_id, shortcode, url, description, view_count, like_count, comment_count, outlier_score, username, transcript, transcript_available, date_posted'
                    ).eq('content_id', content_id).execute()
                    
                    if content_result.data and content_result.data[0].get('transcript'):
                        content = content_result.data[0]
                        transcript_data = content['transcript']
                        
                        # Extract text from the transcript structure (robust parsing)
                        transcript_text = ""
                        if isinstance(transcript_data, dict):
                            if 'content' in transcript_data:
                                # Handle {'content': [...]} format
                                text_segments = []
                                for segment in transcript_data['content']:
                                    if isinstance(segment, dict) and 'text' in segment:
                                        text_segments.append(segment['text'])
                                transcript_text = ' '.join(text_segments)
                            elif 'text' in transcript_data:
                                # Handle {'text': '...'} format
                                transcript_text = transcript_data['text']
                            else:
                                # Handle other dict formats
                                transcript_text = str(transcript_data)
                        else:
                            # Handle string format
                            transcript_text = str(transcript_data)
                        
                        # Parse existing analysis_metadata if available
                        existing_analysis = {}
                        if reel.get('analysis_metadata'):
                            try:
                                if isinstance(reel['analysis_metadata'], str):
                                    existing_analysis = json.loads(reel['analysis_metadata'])
                                else:
                                    existing_analysis = reel['analysis_metadata']
                            except:
                                existing_analysis = {}
                        
                        # Create comprehensive reel object
                        enhanced_reel = {
                            # Core identifiers
                            'id': content['id'],
                            'content_id': content['content_id'],
                            'reel_type': reel.get('reel_type', 'unknown'),
                            'username': content['username'],
                            
                            # Content metadata
                            'shortcode': content['shortcode'],
                            'url': content['url'],
                            'description': content['description'],
                            'date_posted': content['date_posted'],
                            
                            # Engagement metrics
                            'view_count': content['view_count'],
                            'like_count': content['like_count'],
                            'comment_count': content['comment_count'],
                            'outlier_score': content['outlier_score'],
                            
                            # Analysis data
                            'transcript_text': transcript_text.strip(),
                            'selection_reason': reel.get('selection_reason'),
                            'rank_in_selection': reel.get('rank_in_selection'),
                            'existing_analysis': existing_analysis,
                            
                            # Raw analysis reel data (for backward compatibility)
                            'analysis_reel_data': reel
                        }
                        
                        reels_with_transcripts.append(enhanced_reel)
            
            logger.info(f"Found {len(reels_with_transcripts)} reels with completed transcripts")
            return reels_with_transcripts
            
        except Exception as e:
            logger.error(f"Error getting reel data: {e}")
            import traceback
            logger.error(f"Traceback: {traceback.format_exc()}")
            return []

    # ========================================================================================
    # NEW HOOK-BASED WORKFLOW METHODS
    # ========================================================================================
    
    async def _get_primary_username(self, analysis_id: str) -> str:
        """Get primary username from analysis"""
        try:
            if not self.supabase:
                return ""
            
            result = self.supabase.client.table('viral_analysis_results').select(
                'queue_id'
            ).eq('id', analysis_id).execute()
            
            if result.data:
                queue_id = result.data[0]['queue_id']
                queue_result = self.supabase.client.table('viral_ideas_queue').select(
                    'primary_username'
                ).eq('id', queue_id).execute()
                
                if queue_result.data:
                    return queue_result.data[0]['primary_username']
            
            return ""
        except Exception as e:
            logger.error(f"Error getting primary username: {e}")
            return ""
    
    async def _get_profile_data(self, username: str) -> Dict[str, Any]:
        """Get profile data from database"""
        try:
            if not self.supabase:
                return {}
            
            result = self.supabase.client.table('primary_profiles').select(
                'username, profile_name, bio, followers, account_type, profile_primary_category'
            ).eq('username', username).execute()
            
            return result.data[0] if result.data else {}
        except Exception as e:
            logger.error(f"Error getting profile data: {e}")
            return {}
    
    async def _analyze_profile(self, username: str, profile_data: Dict[str, Any], reel_data: List[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
        """STEP 2: Analyze profile and create content identity summary"""
        try:
            if not self.openai_client:
                return None
            
            # Filter to primary reels only and format for analysis
            primary_reels = [reel for reel in reel_data if reel.get('reel_type') == 'primary']
            
            # Format content data for prompt
            top_content_data = []
            for reel in primary_reels[:100]:  # Top 100 reels
                content_item = {
                    'description': reel.get('description', '')[:200],
                    'transcript': reel.get('transcript_text', '')[:300],
                    'view_count': reel.get('view_count', 0),
                    'like_count': reel.get('like_count', 0),
                    'comment_count': reel.get('comment_count', 0),
                    'categories': [reel.get('primary_category', ''), reel.get('secondary_category', '')]
                }
                top_content_data.append(content_item)
            
            # Create prompt
            prompt = PROFILE_ANALYSIS_PROMPT.format(
                primary_username=username,
                bio=profile_data.get('bio', ''),
                followers=profile_data.get('followers', 0),
                account_type=profile_data.get('account_type', 'Personal'),
                top_content_data=json.dumps(top_content_data[:50], indent=2)  # Limit for prompt size
            )
            
            logger.info(f"🔄 PROFILE ANALYSIS INPUT for @{username}")
            logger.info(f"   Analyzing {len(primary_reels)} primary reels")
            
            response = self.openai_client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.3
            )
            
            response_text = response.choices[0].message.content
            logger.info(f"📤 PROFILE ANALYSIS OUTPUT:")
            logger.info(f"   Full response length: {len(response_text)} characters")
            logger.info(f"=== FULL PROFILE ANALYSIS AI RESPONSE ===")
            logger.info(response_text)
            logger.info(f"=== END PROFILE ANALYSIS AI RESPONSE ===")
            
            profile_analysis = self._parse_json_response(response_text)
            
            if profile_analysis:
                logger.info("✅ Profile analysis completed")
                return profile_analysis
            else:
                logger.error("Failed to parse profile analysis")
                return None
                
        except Exception as e:
            logger.error(f"Error in profile analysis: {e}")
            return None
    
    async def _analyze_outlier_hooks(self, reel_data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """STEP 3: Analyze hooks from top 3 primary + 5 competitor outlier reels"""
        try:
            if not self.openai_client:
                return []
            
            # Get top 3 primary outliers
            primary_reels = [reel for reel in reel_data if reel.get('reel_type') == 'primary']
            primary_outliers = sorted(primary_reels, key=lambda x: float(x.get('outlier_score', 0)), reverse=True)[:3]
            
            # Get top 5 competitor outliers
            competitor_reels = [reel for reel in reel_data if reel.get('reel_type') == 'competitor']
            competitor_outliers = sorted(competitor_reels, key=lambda x: float(x.get('outlier_score', 0)), reverse=True)[:5]
            
            # Analyze all hooks
            hook_analyses = []
            all_outliers = primary_outliers + competitor_outliers
            
            logger.info(f"🔄 HOOK ANALYSIS: Analyzing {len(all_outliers)} outlier reels")
            
            for reel in all_outliers:
                if not reel.get('transcript_text'):
                    continue
                
                # Create hook analysis prompt
                engagement_metrics = {
                    'views': reel.get('view_count', 0),
                    'likes': reel.get('like_count', 0),
                    'comments': reel.get('comment_count', 0)
                }
                
                prompt = ENHANCED_HOOK_ANALYSIS_PROMPT.format(
                    username=reel.get('username', ''),
                    reel_type=reel.get('reel_type', ''),
                    engagement_metrics=json.dumps(engagement_metrics),
                    outlier_score=reel.get('outlier_score', 0),
                    transcript_text=reel.get('transcript_text', '')
                )
                
                try:
                    response = self.openai_client.chat.completions.create(
                        model="gpt-4o-mini",
                        messages=[{"role": "user", "content": prompt}],
                        temperature=0.3
                    )
                    
                    response_text = response.choices[0].message.content
                    logger.info(f"📤 HOOK ANALYSIS OUTPUT for reel {reel.get('id', 'unknown')}:")
                    logger.info(f"   Full response length: {len(response_text)} characters")
                    logger.info(f"=== FULL HOOK ANALYSIS AI RESPONSE ===")
                    logger.info(response_text)
                    logger.info(f"=== END HOOK ANALYSIS AI RESPONSE ===")
                    
                    hook_analysis = self._parse_json_response(response_text)
                    
                    if hook_analysis:
                        hook_analysis['reel_id'] = reel.get('id', '')
                        hook_analysis['reel_type'] = reel.get('reel_type', '')
                        hook_analysis['username'] = reel.get('username', '')
                        hook_analyses.append(hook_analysis)
                        logger.info(f"✅ Hook analyzed for {reel.get('username', '')}: {hook_analysis.get('hook_analysis', {}).get('hook_text', '')[:50]}...")
                        
                except Exception as e:
                    logger.error(f"Error analyzing hook for reel {reel.get('id', '')}: {e}")
                    continue
            
            logger.info(f"✅ Hook analysis completed: {len(hook_analyses)} hooks analyzed")
            return hook_analyses
            
        except Exception as e:
            logger.error(f"Error in hook analysis: {e}")
            return []
    
    async def _generate_hooks(self, profile_analysis: Dict[str, Any], hook_analyses: List[Dict[str, Any]], reel_data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """STEP 4: Generate 5 hooks based on competitor analysis with full traceability"""
        try:
            if not self.openai_client:
                return []
            
            # Separate my hooks from competitor hooks
            my_hook_analyses = [h for h in hook_analyses if h.get('reel_type') == 'primary']
            competitor_hook_analyses = [h for h in hook_analyses if h.get('reel_type') == 'competitor']
            
            # Get all primary reel transcripts for style analysis
            primary_reels = [reel for reel in reel_data if reel.get('reel_type') == 'primary']
            my_reel_transcripts = [reel.get('transcript_text', '') for reel in primary_reels if reel.get('transcript_text')]
            
            # Enhanced competitor data with reel metadata for traceability
            enhanced_competitor_analyses = []
            for analysis in competitor_hook_analyses:
                reel_id = analysis.get('reel_id', '')
                # Find the corresponding reel data for metadata
                reel_metadata = next((r for r in reel_data if r.get('id') == reel_id), {})
                
                enhanced_analysis = {
                    **analysis,
                    'reel_metadata': {
                        'reel_id': reel_id,
                        'content_id': reel_metadata.get('content_id', ''),
                        'shortcode': reel_metadata.get('shortcode', ''),
                        'url': reel_metadata.get('url', ''),
                        'view_count': reel_metadata.get('view_count', 0),
                        'like_count': reel_metadata.get('like_count', 0),
                        'username': analysis.get('username', ''),
                        'description': reel_metadata.get('description', '')[:100]  # First 100 chars
                    }
                }
                enhanced_competitor_analyses.append(enhanced_analysis)
            
            # Create hook generation prompt with enhanced data
            prompt = HOOK_GENERATION_PROMPT.format(
                profile_analysis=json.dumps(profile_analysis, indent=2),
                my_hook_analyses=json.dumps(my_hook_analyses, indent=2),
                competitor_hook_analyses=json.dumps(enhanced_competitor_analyses, indent=2),
                my_reel_transcript='\n\n'.join(my_reel_transcripts[:3])  # Multiple transcripts for better style analysis
            )
            
            logger.info(f"🔄 HOOK GENERATION INPUT:")
            logger.info(f"   My hooks: {len(my_hook_analyses)}, Competitor hooks: {len(competitor_hook_analyses)}")
            
            response = self.openai_client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": "You are a hook generation expert. You MUST generate exactly 5 hooks in valid JSON array format. Do not generate fewer than 5 hooks under any circumstances."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.8
            )
            
            response_text = response.choices[0].message.content
            logger.info(f"📤 HOOK GENERATION OUTPUT:")
            logger.info(f"   Full response length: {len(response_text)} characters")
            logger.info(f"=== FULL AI RESPONSE ===")
            logger.info(response_text)
            logger.info(f"=== END AI RESPONSE ===")
            
            # Enhanced hook parsing with better error handling
            hooks_list = []
            
            # First try: Use specialized array parsing method
            try:
                logger.info("🔍 Attempting array parsing method...")
                hooks_list = self._parse_json_array_response(response_text)
                if hooks_list:
                    logger.info(f"✅ Extracted {len(hooks_list)} hooks using array parser")
                    for i, hook in enumerate(hooks_list):
                        logger.info(f"   Hook {i+1}: {hook.get('hook_text', 'N/A')[:50]}...")
                else:
                    logger.warning("❌ Array parser returned None/empty")
            except Exception as e:
                logger.warning(f"❌ Array JSON parsing failed: {e}")
                import traceback
                logger.warning(f"Traceback: {traceback.format_exc()}")
            
            # Second try: Extract JSON array from response using regex
            if not hooks_list:
                try:
                    import re
                    # Look for complete JSON array
                    array_match = re.search(r'\[[\s\S]*\]', response_text)
                    if array_match:
                        json_str = array_match.group()
                        hooks_list = json.loads(json_str)
                        logger.info(f"✅ Extracted {len(hooks_list)} hooks using regex")
                except Exception as e:
                    logger.warning(f"Regex JSON extraction failed: {e}")
            
            # Third try: Look for individual hook objects and combine them
            if not hooks_list:
                try:
                    import re
                    # Find all complete hook objects with better pattern
                    hook_pattern = r'\{\s*"hook_id"[^}]*(?:\{[^}]*\}[^}]*)*\}'
                    hook_matches = re.findall(hook_pattern, response_text, re.DOTALL)
                    
                    parsed_hooks = []
                    for match in hook_matches:
                        try:
                            # Clean up the match to ensure it's a complete JSON object
                            cleaned_match = match
                            brace_count = 0
                            for i, char in enumerate(match):
                                if char == '{':
                                    brace_count += 1
                                elif char == '}':
                                    brace_count -= 1
                                    if brace_count == 0:
                                        cleaned_match = match[:i+1]
                                        break
                            
                            hook_obj = json.loads(cleaned_match)
                            if 'hook_id' in hook_obj and 'hook_text' in hook_obj:
                                parsed_hooks.append(hook_obj)
                        except Exception as parse_error:
                            logger.warning(f"Failed to parse individual hook: {parse_error}")
                            continue
                    
                    if parsed_hooks:
                        hooks_list = parsed_hooks
                        logger.info(f"✅ Extracted {len(hooks_list)} hooks using pattern matching")
                        
                except Exception as e:
                    logger.warning(f"Pattern matching failed: {e}")
            
            # Fourth try: Force generate 5 hooks if we have competitor data but failed parsing
            if not hooks_list and len(enhanced_competitor_analyses) >= 1:
                logger.warning("Failed to parse AI response, creating fallback hooks based on competitor analysis")
                fallback_hooks = []
                for i, comp_analysis in enumerate(enhanced_competitor_analyses[:5]):
                    fallback_hook = {
                        "hook_id": i + 1,
                        "hook_text": f"Here's what I learned from {comp_analysis.get('username', 'competitor')}: {comp_analysis.get('hook_analysis', {}).get('hook_text', 'Amazing insight')}",
                        "original_competitor_hook": comp_analysis.get('hook_analysis', {}).get('hook_text', ''),
                        "source_reel_id": comp_analysis.get('reel_id', ''),
                        "source_username": comp_analysis.get('username', ''),
                        "adaptation_strategy": "Direct adaptation with creator context",
                        "psychological_triggers": comp_analysis.get('hook_analysis', {}).get('emotional_triggers', []),
                        "power_words_used": comp_analysis.get('hook_analysis', {}).get('power_words', []),
                        "estimated_effectiveness": 8.5,
                        "why_it_works": "Based on proven competitor pattern",
                        "creator_voice_elements": ["authentic", "practical"],
                        "content_theme_alignment": "Matches creator themes",
                        "hook_type": comp_analysis.get('hook_analysis', {}).get('hook_type', 'statement')
                    }
                    fallback_hooks.append(fallback_hook)
                hooks_list = fallback_hooks
                logger.info(f"✅ Generated {len(hooks_list)} fallback hooks")
            
            # Validate and return
            if isinstance(hooks_list, list) and len(hooks_list) >= 1:
                logger.info(f"✅ Generated {len(hooks_list)} hooks successfully")
                return hooks_list[:5]  # Take first 5 if we got more
            else:
                logger.error(f"Hook generation failed - got {type(hooks_list)}: {hooks_list}")
                logger.error(f"Raw response (first 500 chars): {response_text[:500]}")
                return []
                
        except Exception as e:
            logger.error(f"Error generating hooks: {e}")
            return []
    
    async def _generate_hook_scripts(self, hooks: List[Dict[str, Any]], profile_analysis: Dict[str, Any], hook_analyses: List[Dict[str, Any]], reel_data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """STEP 5: Generate a unique script for each hook based on the specific competitor reel it was inspired by"""
        try:
            if not self.openai_client:
                return []
            
            # Get creator's actual transcripts for voice analysis
            primary_reels = [reel for reel in reel_data if reel.get('reel_type') == 'primary']
            creator_transcripts = []
            for reel in primary_reels:
                if reel.get('transcript_text'):
                    creator_transcripts.append({
                        'reel_id': reel.get('id', ''),
                        'transcript': reel.get('transcript_text', '')[:800],  # Limit size but get substantial content
                        'description': reel.get('description', '')[:100]
                    })
            
            scripts = []
            
            for i, hook in enumerate(hooks):
                try:
                    # Find the specific competitor hook pattern this was based on
                    source_reel_id = hook.get('source_reel_id', '')
                    source_username = hook.get('source_username', '')
                    competitor_hook_pattern = {}
                    competitor_reel_context = {}
                    
                    if source_reel_id:
                        # Find the original competitor analysis with full context
                        competitor_analysis = next((h for h in hook_analyses if h.get('reel_id') == source_reel_id), {})
                        if competitor_analysis:
                            # Get the full competitor reel data for context
                            competitor_reel = next((r for r in reel_data if r.get('id') == source_reel_id), {})
                            
                            competitor_hook_pattern = {
                                'original_hook': hook.get('original_competitor_hook', ''),
                                'hook_type': competitor_analysis.get('hook_analysis', {}).get('hook_type', ''),
                                'hook_strategy': competitor_analysis.get('hook_analysis', {}).get('hook_strategy', ''),
                                'power_words': competitor_analysis.get('hook_analysis', {}).get('power_words', []),
                                'psychological_triggers': competitor_analysis.get('hook_analysis', {}).get('emotional_triggers', []),
                                'why_it_works': competitor_analysis.get('hook_analysis', {}).get('why_it_works', ''),
                                'structure_pattern': f"Follow {source_username}'s pattern but in creator's voice"
                            }
                            
                            competitor_reel_context = {
                                'username': source_username,
                                'description': competitor_reel.get('description', '')[:200],
                                'transcript_excerpt': competitor_reel.get('transcript_text', '')[:300],
                                'engagement_metrics': {
                                    'view_count': competitor_reel.get('view_count', 0),
                                    'like_count': competitor_reel.get('like_count', 0),
                                    'outlier_score': competitor_reel.get('outlier_score', 0)
                                }
                            }
                    
                    # Enhanced prompt with more specific context about the competitor reel
                    enhanced_prompt = HOOK_SCRIPT_GENERATION_PROMPT.format(
                        hook_data=json.dumps(hook, indent=2),
                        creator_transcripts=json.dumps(creator_transcripts, indent=2),
                        profile_summary=json.dumps(profile_analysis.get('profile_summary', {}), indent=2),
                        competitor_hook_pattern=json.dumps(competitor_hook_pattern, indent=2)
                    )
                    
                    # Add specific context about the competitor reel this script is based on
                    enhanced_prompt += f"\n\n## COMPETITOR REEL CONTEXT (Base your script structure on this):\n"
                    enhanced_prompt += f"Original Competitor: @{source_username}\n"
                    enhanced_prompt += f"Their Hook: {hook.get('original_competitor_hook', '')}\n"
                    enhanced_prompt += f"Your Adapted Hook: {hook.get('hook_text', '')}\n"
                    enhanced_prompt += f"Competitor Context: {json.dumps(competitor_reel_context, indent=2)}\n"
                    enhanced_prompt += f"\n## UNIQUE SCRIPT REQUIREMENT:\n"
                    enhanced_prompt += f"Create a UNIQUE script for Hook #{i+1} that is distinctly different from other scripts you might generate. "
                    enhanced_prompt += f"Base the content structure and style on the specific competitor reel context above. "
                    enhanced_prompt += f"Ensure this script has a unique value proposition and approach compared to other hooks."
                    
                    logger.info(f"🔄 SCRIPT GENERATION {i+1}/{len(hooks)}:")
                    logger.info(f"   Hook: {hook.get('hook_text', '')[:50]}...")
                    logger.info(f"   Based on: @{source_username} - {hook.get('original_competitor_hook', '')[:50]}...")
                    
                    response = self.openai_client.chat.completions.create(
                        model="gpt-4o-mini",
                        messages=[{"role": "user", "content": enhanced_prompt}],
                        temperature=0.8  # Slightly higher temperature for more variation
                    )
                    
                    response_text = response.choices[0].message.content
                    logger.info(f"📤 SCRIPT GENERATION OUTPUT {i+1}:")
                    logger.info(f"   Full response length: {len(response_text)} characters")
                    logger.info(f"=== FULL SCRIPT AI RESPONSE {i+1} ===")
                    logger.info(response_text)
                    logger.info(f"=== END SCRIPT AI RESPONSE {i+1} ===")
                    
                    script_data = self._parse_json_response(response_text)
                    
                    if script_data:
                        # Enhanced script metadata for better traceability
                        enhanced_script = {
                            **script_data,
                            'hook_id': hook.get('hook_id', i+1),
                            'source_hook': hook.get('hook_text', ''),
                            'based_on_competitor': source_username,
                            'original_competitor_hook': hook.get('original_competitor_hook', ''),
                            'competitor_reel_id': source_reel_id,
                            'adaptation_context': {
                                'hook_strategy': competitor_hook_pattern.get('hook_strategy', ''),
                                'psychological_triggers': competitor_hook_pattern.get('psychological_triggers', []),
                                'unique_angle': f"Script #{i+1} - {hook.get('adaptation_strategy', '')}"
                            }
                        }
                        
                        scripts.append(enhanced_script)
                        script_title = script_data.get('script', {}).get('title', f'Script {i+1}')
                        logger.info(f"✅ Script {i+1} generated: {script_title}")
                    else:
                        logger.error(f"Failed to parse script response for hook {i+1}")
                    
                except Exception as e:
                    logger.error(f"Error generating script for hook {i+1}: {e}")
                    continue
            
            logger.info(f"✅ Script generation completed: {len(scripts)} unique scripts created")
            return scripts
            
        except Exception as e:
            logger.error(f"Error in script generation: {e}")
            return []
    
    def _parse_json_response(self, response_text: str) -> Optional[Dict[str, Any]]:
        """Parse JSON response with cleaning"""
        try:
            cleaned_text = self._clean_json_response(response_text)
            if cleaned_text:
                return json.loads(cleaned_text)
            return None
        except Exception as e:
            logger.error(f"Error parsing JSON response: {e}")
            return None
    
    def _parse_json_array_response(self, response_text: str) -> Optional[List[Dict[str, Any]]]:
        """Parse JSON array response with cleaning - specifically for hook generation"""
        try:
            logger.info("🔍 Starting JSON array parsing...")
            cleaned_text = self._clean_json_response(response_text)
            logger.info(f"📝 Cleaned text length: {len(cleaned_text) if cleaned_text else 0}")
            logger.info(f"📝 Cleaned text preview: {cleaned_text[:200] if cleaned_text else 'None'}...")
            
            if cleaned_text:
                parsed = json.loads(cleaned_text)
                logger.info(f"✅ JSON parsed successfully, type: {type(parsed)}")
                
                if isinstance(parsed, list):
                    logger.info(f"✅ Found list with {len(parsed)} items")
                    return parsed
                elif isinstance(parsed, dict):
                    logger.info(f"📦 Found dict with keys: {list(parsed.keys())}")
                    # Sometimes AI wraps the array in an object
                    if 'hooks' in parsed:
                        logger.info("✅ Found 'hooks' key in dict")
                        return parsed['hooks']
                    elif 'generated_hooks' in parsed:
                        logger.info("✅ Found 'generated_hooks' key in dict")
                        return parsed['generated_hooks']
                    elif 'data' in parsed:
                        logger.info("✅ Found 'data' key in dict")
                        return parsed['data']
                    else:
                        logger.info("📦 Single hook object, wrapping in array")
                        # Single hook object, wrap in array
                        return [parsed]
                else:
                    logger.warning(f"❌ Unexpected parsed type: {type(parsed)}")
                    return None
            else:
                logger.warning("❌ Cleaned text is empty")
                return None
        except Exception as e:
            logger.error(f"❌ Error parsing JSON array response: {e}")
            import traceback
            logger.error(f"Traceback: {traceback.format_exc()}")
            return None
    
    async def _get_reel_metadata_for_frontend(self, reel_id: str) -> Dict[str, Any]:
        """Get reel metadata for frontend display"""
        try:
            if not self.supabase:
                return {}
            
            # Get reel metadata from content table
            result = self.supabase.client.table('content').select(
                'content_id, shortcode, url, description, view_count, like_count, comment_count, username, date_posted'
            ).eq('id', reel_id).execute()
            
            if result.data:
                reel = result.data[0]
                return {
                    'reel_id': reel_id,
                    'content_id': reel.get('content_id', ''),
                    'shortcode': reel.get('shortcode', ''),
                    'url': reel.get('url', f"https://www.instagram.com/p/{reel.get('shortcode', '')}/"),
                    'description': reel.get('description', '')[:100],
                    'view_count': reel.get('view_count', 0),
                    'like_count': reel.get('like_count', 0),
                    'comment_count': reel.get('comment_count', 0),
                    'username': reel.get('username', ''),
                    'date_posted': reel.get('date_posted', ''),
                    'instagram_url': f"https://www.instagram.com/p/{reel.get('shortcode', '')}/"
                }
            return {}
            
        except Exception as e:
            logger.error(f"Error getting reel metadata: {e}")
            return {}

    async def _store_hook_analysis_results(self, analysis_id: str, profile_analysis: Dict[str, Any], hook_analyses: List[Dict[str, Any]], generated_hooks: List[Dict[str, Any]], hook_scripts: List[Dict[str, Any]]):
        """Store all results in new flexible JSONB schema"""
        try:
            if not self.supabase:
                return
            
            # Enhance hooks with reel metadata for frontend traceability
            enhanced_hooks = []
            for hook in generated_hooks:
                enhanced_hook = {**hook}
                source_reel_id = hook.get('source_reel_id', '')
                if source_reel_id:
                    reel_metadata = await self._get_reel_metadata_for_frontend(source_reel_id)
                    enhanced_hook['source_reel_metadata'] = reel_metadata
                enhanced_hooks.append(enhanced_hook)
            
            # Create comprehensive analysis data for new JSONB field
            analysis_data = {
                "workflow_version": "hook_based_v2",
                "analysis_timestamp": datetime.now().isoformat(),
                "profile_analysis": profile_analysis,
                "individual_reel_analyses": hook_analyses,
                "generated_hooks": enhanced_hooks,
                "complete_scripts": hook_scripts,  # Full script data for frontend display
                "scripts_summary": [
                    {
                        "script_id": i+1,
                        "hook_id": script.get('hook_id', i+1),
                        "title": script.get('script', {}).get('title', f'Hook Script {i+1}'),
                        "estimated_duration": script.get('script', {}).get('estimated_duration', 60),
                        "based_on_competitor": script.get('based_on_competitor', ''),
                        "original_competitor_hook": script.get('original_competitor_hook', ''),
                        "competitor_reel_id": script.get('competitor_reel_id', '')
                    }
                    for i, script in enumerate(hook_scripts)
                ],
                "analysis_summary": {
                    "total_hooks_analyzed": len(hook_analyses),
                    "primary_hooks": len([h for h in hook_analyses if h.get('reel_type') == 'primary']),
                    "competitor_hooks": len([h for h in hook_analyses if h.get('reel_type') == 'competitor']),
                    "hooks_generated": len(enhanced_hooks),
                    "scripts_created": len(hook_scripts),
                    "unique_competitors_analyzed": len(set(h.get('username', '') for h in hook_analyses if h.get('reel_type') == 'competitor'))
                }
            }
            
            # Update viral_analysis_results with new JSONB structure
            update_data = {
                "analysis_data": json.dumps(analysis_data),
                "workflow_version": "hook_based_v2",
                "status": "completed",
                "analysis_completed_at": datetime.now().isoformat()
            }
            
            self.supabase.client.table('viral_analysis_results').update(
                update_data
            ).eq('id', analysis_id).execute()
            
            # Store individual reel analyses in viral_analysis_reels.analysis_metadata
            for hook_analysis in hook_analyses:
                reel_id = hook_analysis.get('reel_id', '')
                if reel_id:
                    # Find existing reel record
                    reel_result = self.supabase.client.table('viral_analysis_reels').select('id').eq(
                        'analysis_id', analysis_id
                    ).eq('content_id', reel_id).execute()
                    
                    if reel_result.data:
                        # Update existing record with analysis metadata
                        analysis_metadata = {
                            "hook_analysis": hook_analysis.get('hook_analysis', {}),
                            "analysis_timestamp": datetime.now().isoformat(),
                            "workflow_version": "hook_based_v2"
                        }
                        
                        self.supabase.client.table('viral_analysis_reels').update({
                            "analysis_metadata": json.dumps(analysis_metadata),
                            "hook_text": hook_analysis.get('hook_analysis', {}).get('hook_text', ''),
                            "power_words": json.dumps(hook_analysis.get('hook_analysis', {}).get('power_words', []))
                        }).eq('id', reel_result.data[0]['id']).execute()
            
            # Store scripts in viral_scripts table with enhanced metadata and traceability
            for i, script in enumerate(hook_scripts):
                corresponding_hook = enhanced_hooks[i] if i < len(enhanced_hooks) else {}
                
                # Script data aligned with actual database schema
                script_data = {
                    "analysis_id": analysis_id,
                    "script_title": script.get('script', {}).get('title', f'Hook Script {i+1}'),
                    "script_content": script.get('script', {}).get('full_script', ''),
                    "script_type": "reel",  # Default to reel type
                    "estimated_duration": script.get('script', {}).get('estimated_duration', 60),
                    "target_audience": script.get('script', {}).get('target_audience', ''),
                    "primary_hook": script.get('source_hook', corresponding_hook.get('hook_text', '')),
                    "call_to_action": script.get('script', {}).get('call_to_action', ''),
                    "source_reels": json.dumps({
                        'competitor_hook_source': corresponding_hook.get('source_reel_metadata', {}),
                        'hook_id': script.get('hook_id', i+1),
                        'adaptation_strategy': corresponding_hook.get('adaptation_strategy', ''),
                        'source_reel_id': corresponding_hook.get('source_reel_id', ''),
                        'based_on_competitor': script.get('based_on_competitor', ''),
                        'original_competitor_hook': script.get('original_competitor_hook', ''),
                        'competitor_reel_id': script.get('competitor_reel_id', ''),
                        'adaptation_context': script.get('adaptation_context', {}),
                        # Include all hook metadata in source_reels JSONB field
                        'hook_metadata': {
                            'hook_strategy': corresponding_hook.get('hook_strategy', ''),
                            'psychological_triggers': corresponding_hook.get('psychological_triggers', []),
                            'power_words_used': corresponding_hook.get('power_words_used', []),
                            'estimated_effectiveness': corresponding_hook.get('estimated_effectiveness', 0),
                            'content_theme_alignment': corresponding_hook.get('content_theme_alignment', ''),
                            'hook_type': corresponding_hook.get('hook_type', '')
                        },
                        'voice_analysis': script.get('voice_analysis', {})
                    }),
                    "script_structure": json.dumps(script.get('script', {}).get('structure_breakdown', {})),
                    "generation_prompt": "HOOK_SCRIPT_GENERATION_PROMPT",
                    "ai_model": "gpt-4o-mini",
                    "generation_temperature": 0.8,
                    "status": "completed"
                }
                
                self.supabase.client.table('viral_scripts').insert(script_data).execute()
            
            logger.info(f"✅ Stored analysis results in new JSONB format for {analysis_id}")
            logger.info(f"   📊 Analysis data: {len(json.dumps(analysis_data))} characters")
            logger.info(f"   🎯 Generated hooks: {len(enhanced_hooks)}")
            logger.info(f"   📝 Scripts created: {len(hook_scripts)}")
            
        except Exception as e:
            logger.error(f"Error storing hook analysis results: {e}")
            import traceback
            logger.error(f"Traceback: {traceback.format_exc()}")
    
    async def _process_hook_analysis(self, reel_data: List[Dict[str, Any]]):
        """Process each reel for hook analysis using exact N8N prompt"""
        try:
            if not self.openai_client:
                logger.error("OpenAI client not available")
                return
            
            for reel in reel_data:
                transcript_text = reel.get('transcript_text', '')
                if not transcript_text:
                    continue
                
                # Use exact N8N prompt
                prompt = HOOK_ANALYZER_PROMPT.format(transcript_text=transcript_text)
                
                # Log the input
                logger.info(f"🔄 HOOK ANALYSIS INPUT for reel {reel['content_id']}:")
                logger.info(f"   Transcript (first 150 chars): {transcript_text[:150]}...")
                
                try:
                    response = self.openai_client.chat.completions.create(
                        model="gpt-4o-mini",
                        messages=[{"role": "user", "content": prompt}],
                        temperature=0.7
                    )
                    
                    # Log the output
                    response_text = response.choices[0].message.content
                    logger.info(f"📤 HOOK ANALYSIS OUTPUT for reel {reel['content_id']}:")
                    logger.info(f"   Raw response: {response_text}")
                    
                    hook_analysis = self._parse_hook_response(response_text)
                    
                    if hook_analysis:
                        # Store hook analysis in viral_analysis_reels table
                        await self._store_hook_analysis(reel['id'], hook_analysis)
                        logger.info(f"✅ Hook analysis completed for reel {reel['id']}")
                    
                except Exception as e:
                    logger.error(f"Error analyzing hook for reel {reel['id']}: {e}")
                    continue
                    
        except Exception as e:
            logger.error(f"Error in hook analysis processing: {e}")
    
    def _parse_hook_response(self, response_text: str) -> Optional[Dict[str, Any]]:
        """Parse hook analyzer response into structured data"""
        try:
            # Clean the response text
            cleaned_text = self._clean_json_response(response_text)
            if cleaned_text:
                return json.loads(cleaned_text)
            
            # If that fails, try to extract just the JSON part with better parsing
            try:
                # Find JSON-like structure in the response
                import re
                json_match = re.search(r'\{.*\}', response_text, re.DOTALL)
                if json_match:
                    json_text = json_match.group()
                    
                    # Try various JSON fixes
                    import ast
                    try:
                        # First try standard JSON
                        return json.loads(json_text)
                    except:
                        # Try using ast.literal_eval for simple cases
                        try:
                            return ast.literal_eval(json_text)
                        except:
                            # Try fixing quotes manually
                            import re
                            # Simple quote escape fix
                            fixed_text = re.sub(r'(?<!\\)"(?=.*")', '\\"', json_text)
                            return json.loads(fixed_text)
            except:
                pass
                
            # Return a basic fallback
            return {
                "hook_type": "unknown",
                "hook_text": response_text[:100] if response_text else "No response",
                "effectiveness_score": 5,
                "why_it_works": "Analysis incomplete",
                "attention_grabbers": [],
                "improvement_suggestions": "Retry analysis"
            }
        except Exception as e:
            logger.error(f"Error parsing hook response: {e}")
            # Return fallback on any error
            return {
                "hook_type": "error",
                "hook_text": "Parsing failed",
                "effectiveness_score": 1,
                "why_it_works": "Error in analysis",
                "attention_grabbers": [],
                "improvement_suggestions": "Retry with different prompt"
            }
    
    async def _store_hook_analysis(self, reel_id: str, hook_analysis: Dict[str, Any]):
        """Store hook analysis in viral_analysis_reels table"""
        try:
            if not self.supabase:
                return
            
            # Extract hook text and power words for the schema fields that exist
            hook_text = ""
            power_words = []
            
            if isinstance(hook_analysis, dict):
                hook_text = hook_analysis.get('hook_text', '') or str(hook_analysis.get('why_it_works', ''))[:200]
                power_words = hook_analysis.get('attention_grabbers', [])
            
            self.supabase.client.table('viral_analysis_reels').update({
                'hook_text': hook_text[:500] if hook_text else '',  # Limit length
                'power_words': power_words
            }).eq('id', reel_id).execute()
            
        except Exception as e:
            logger.error(f"Error storing hook analysis: {e}")
    
    async def _process_overall_analysis(self, reel_data: List[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
        """Process overall analysis using exact N8N AI Agent prompt"""
        try:
            if not self.openai_client:
                logger.error("OpenAI client not available")
                return None
            
            # Format reel data for the prompt
            formatted_reels = []
            for reel in reel_data:
                formatted_reel = {
                    'id': reel.get('id', ''),
                    'transcript': reel.get('transcript_text', ''),
                    'like_count': reel.get('like_count', 0),
                    'view_count': reel.get('view_count', 0),
                    'comment_count': reel.get('comment_count', 0),
                    'hook_analysis': reel.get('hook_analysis', {}),
                    'url': reel.get('media_url', '')
                }
                formatted_reels.append(formatted_reel)
            
            # Use exact N8N AI Agent prompt
            prompt = AI_AGENT_ANALYSIS_PROMPT.format(
                reel_data=json.dumps(formatted_reels, indent=2)
            )
            
            # Log the input
            logger.info(f"🔄 OVERALL ANALYSIS INPUT:")
            logger.info(f"   Analyzing {len(formatted_reels)} reels")
            logger.info(f"   Prompt length: {len(prompt)} chars")
            
            response = self.openai_client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.7
            )
            
            # Log the output
            response_text = response.choices[0].message.content
            logger.info(f"📤 OVERALL ANALYSIS OUTPUT:")
            logger.info(f"   Raw response: {response_text}")
            
            analysis_results = self._parse_analysis_response(response.choices[0].message.content)
            
            if analysis_results:
                logger.info("✅ Overall analysis completed")
                return analysis_results
            else:
                logger.error("Failed to parse analysis results")
                return self._create_fallback_analysis()
                
        except Exception as e:
            logger.error(f"Error in overall analysis: {e}")
            return self._create_fallback_analysis()
    
    def _parse_analysis_response(self, response_text: str) -> Optional[Dict[str, Any]]:
        """Parse the overall analysis response"""
        try:
            cleaned_text = self._clean_json_response(response_text)
            if cleaned_text:
                return json.loads(cleaned_text)
            return None
        except Exception as e:
            logger.error(f"Error parsing analysis response: {e}")
            return None
    
    def _create_fallback_analysis(self) -> Dict[str, Any]:
        """Create fallback analysis when AI fails - matches expected format"""
        return {
            "analysis_summary": "Analysis completed with basic insights",
            "viral_score": 75,
            "top_hooks": [
                {
                    "pattern": "Question Hook",
                    "effectiveness": 80,
                    "examples": ["What if I told you?", "Did you know?"],
                    "why_it_works": "Creates curiosity and engagement"
                }
            ],
            "engagement_patterns": {
                "high_engagement_traits": ["strong_hook", "clear_value", "call_to_action"],
                "optimal_length": "30-45 seconds",
                "best_posting_times": ["morning", "evening"],
                "content_structure": "hook-problem-solution-cta"
            },
            "content_themes": [
                {
                    "theme": "Educational Content",
                    "popularity_score": 85,
                    "target_audience": "Learning-focused users",
                    "examples": ["How-to content", "Tips and tricks"]
                }
            ],
            "recommendations": [
                "Use strong hooks in first 3 seconds",
                "Provide clear value proposition",
                "Include clear call-to-action"
            ]
        }
    
    def _format_reel_data(self, reel_data: List[Dict[str, Any]]) -> str:
        """Format reel data for AI prompt"""
        formatted = []
        for reel in reel_data[:10]:  # Limit to top 10 for prompt size
            formatted.append({
                'transcript': reel.get('transcript_text', '')[:500],
                'engagement': {
                    'likes': reel.get('like_count', 0),
                    'views': reel.get('view_count', 0),
                    'comments': reel.get('comment_count', 0)
                },
                'hook_analysis': reel.get('hook_analysis', {})
            })
        return json.dumps(formatted, indent=2)
    
    async def _generate_viral_ideas(self, analysis_results: Dict[str, Any], reel_data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Generate individual viral ideas using dedicated prompt"""
        try:
            if not self.openai_client:
                return []
            
            # Extract winning patterns from analysis
            winning_patterns = analysis_results.get('top_hooks', [])
            top_reels = reel_data[:5]  # Top 5 reels
            source_reels = [reel.get('id', '') for reel in top_reels]
            
            prompt = IDEA_GENERATOR_PROMPT.format(
                winning_patterns=json.dumps(winning_patterns),
                top_reels=json.dumps([{
                    'id': reel.get('id', ''),
                    'transcript': reel.get('transcript_text', '')[:200]
                } for reel in top_reels]),
                source_reels=json.dumps(source_reels)
            )
            
            # Log the input
            logger.info(f"🔄 VIRAL IDEAS INPUT:")
            logger.info(f"   Top reels: {len(top_reels)}")
            logger.info(f"   Prompt length: {len(prompt)} chars")
            
            response = self.openai_client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.8
            )
            
            # Log the output
            response_text = response.choices[0].message.content
            logger.info(f"📤 VIRAL IDEAS OUTPUT:")
            logger.info(f"   Raw response: {response_text}")
            
            ideas = self._parse_ideas_response(response_text)
            logger.info(f"✅ Generated {len(ideas)} viral ideas")
            return ideas
            
        except Exception as e:
            logger.error(f"Error generating viral ideas: {e}")
            return []
    
    def _parse_ideas_response(self, response_text: str) -> List[Dict[str, Any]]:
        """Parse the viral ideas response"""
        try:
            cleaned_text = self._clean_json_response(response_text)
            logger.info(f"🧹 Cleaned ideas text: {cleaned_text[:200]}...")
            
            if cleaned_text:
                parsed = json.loads(cleaned_text)
                logger.info(f"📊 Parsed ideas type: {type(parsed)}")
                
                if isinstance(parsed, list):
                    logger.info(f"✅ Found {len(parsed)} ideas in list")
                    return parsed
                elif isinstance(parsed, dict) and 'ideas' in parsed:
                    logger.info(f"✅ Found {len(parsed['ideas'])} ideas in dict")
                    return parsed['ideas']
                else:
                    logger.warning(f"❌ Unexpected parsed structure: {list(parsed.keys()) if isinstance(parsed, dict) else type(parsed)}")
                    
            # Fallback: try to extract JSON array directly
            import re
            array_match = re.search(r'\[.*\]', response_text, re.DOTALL)
            if array_match:
                try:
                    fallback_parsed = json.loads(array_match.group())
                    if isinstance(fallback_parsed, list):
                        logger.info(f"✅ Fallback parsing found {len(fallback_parsed)} ideas")
                        return fallback_parsed
                except:
                    pass
                    
            logger.warning("❌ No valid ideas array found")
            return []
        except Exception as e:
            logger.error(f"Error parsing ideas response: {e}")
            return []
    
    async def _generate_scripts(self, reel_data: List[Dict[str, Any]], analysis_results: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Generate scripts based on user reels and winning patterns"""
        if not self.openai_client:
            return []
        
        try:
            # Get user's reels (primary reels)
            user_reels = [reel for reel in reel_data if reel.get('is_primary_profile', False)]
            if not user_reels:
                user_reels = reel_data[:3]  # Fallback to first 3 reels
            
            user_transcripts = [reel.get('transcript_text', '') for reel in user_reels[:3]]
            winning_patterns = analysis_results.get('top_hooks', [])
            target_topic = "viral content creation"  # Default topic
            
            prompt = SCRIPT_GENERATOR_PROMPT.format(
                user_transcripts=json.dumps(user_transcripts),
                winning_patterns=json.dumps(winning_patterns),
                target_topic=target_topic
            )
            
            # Log the input
            logger.info(f"🔄 SCRIPT GENERATION INPUT:")
            logger.info(f"   User reels: {len(user_reels)}")
            logger.info(f"   Prompt length: {len(prompt)} chars")
            
            response = self.openai_client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.8
            )
            
            # Log the output
            response_text = response.choices[0].message.content
            logger.info(f"📤 SCRIPT GENERATION OUTPUT:")
            logger.info(f"   Raw response: {response_text}")
            
            script_data = self._parse_script_response(response_text)
            if script_data:
                logger.info("✅ Generated script")
                return [script_data]
            
            return []
            
        except Exception as e:
            logger.error(f"Error generating scripts: {e}")
            return []
    
    def _parse_script_response(self, response_text: str) -> Optional[Dict[str, Any]]:
        """Parse the script generation response"""
        try:
            cleaned_text = self._clean_json_response(response_text)
            if cleaned_text:
                return json.loads(cleaned_text)
            return None
        except Exception as e:
            logger.error(f"Error parsing script response: {e}")
            return None
    
    def _clean_json_response(self, response_text: str) -> Optional[str]:
        """Clean JSON response text to handle common AI response issues"""
        try:
            logger.info(f"🧹 Starting JSON cleaning on {len(response_text)} characters")
            
            # Remove markdown code blocks
            text = response_text.strip()
            logger.info(f"🧹 After strip: {len(text)} characters")
            
            if text.startswith('```json'):
                text = text[7:]
                logger.info("🧹 Removed ```json prefix")
            elif text.startswith('```'):
                text = text[3:]
                logger.info("🧹 Removed ``` prefix")
            
            if text.endswith('```'):
                text = text[:-3]
                logger.info("🧹 Removed ``` suffix")
            
            # Fix common JSON issues
            text = self._fix_json_quotes(text)
            logger.info(f"🧹 After quote fixes: {len(text)} characters")
            
            # Fix trailing commas - enhanced version
            import re
            # Remove trailing commas before closing brackets/braces
            text = re.sub(r',(\s*[}\]])', r'\1', text)
            # Remove trailing commas at end of lines (more aggressive)
            text = re.sub(r',(\s*\n\s*[}\]])', r'\1', text)
            logger.info(f"🧹 After comma fixes: {len(text)} characters")
            
            # Find JSON boundaries - prioritize arrays for hook generation
            start_array = text.find('[')
            start_object = text.find('{')
            
            # Choose array first if both exist and array comes first or is very close
            if start_array != -1 and (start_object == -1 or start_array <= start_object + 5):
                start = start_array
                logger.info(f"🧹 Looking for JSON array, start at: {start}")
            elif start_object != -1:
                start = start_object 
                logger.info(f"🧹 Looking for JSON object, start at: {start}")
            else:
                start = -1
                logger.info("🧹 No JSON found")
            
            if start != -1:
                # Find matching closing bracket
                bracket_count = 0
                end_char = '}' if text[start] == '{' else ']'
                start_char = text[start]
                logger.info(f"🧹 JSON starts with '{start_char}', looking for closing '{end_char}'")
                
                for i in range(start, len(text)):
                    if text[i] == start_char:
                        bracket_count += 1
                    elif text[i] == end_char:
                        bracket_count -= 1
                        if bracket_count == 0:
                            cleaned_json = text[start:i+1]
                            # Final pass to remove any remaining trailing commas
                            cleaned_json = re.sub(r',(\s*[}\]])', r'\1', cleaned_json)
                            logger.info(f"✅ Extracted JSON: {len(cleaned_json)} characters")
                            logger.info(f"🔍 JSON preview: {cleaned_json[:100]}...")
                            return cleaned_json
            
            # If no brackets found, clean the whole text
            text = re.sub(r',(\s*[}\]])', r'\1', text)
            return text.strip()
            
        except Exception as e:
            logger.error(f"Error cleaning JSON response: {e}")
            return response_text
    
    def _fix_json_quotes(self, text: str) -> str:
        """Fix unescaped quotes in JSON strings"""
        try:
            import re
            
            # Replace curly quotes with straight quotes
            text = text.replace('"', '"').replace('"', '"')
            text = text.replace(''', "'").replace(''', "'")
            
            # Fix unescaped quotes inside JSON string values
            # This regex finds quotes that are inside string values and escapes them
            def escape_inner_quotes(match):
                full_match = match.group(0)
                # If it already has escaped quotes, don't change it
                if '\\"' in full_match:
                    return full_match
                # Escape quotes inside the string value
                key_part = match.group(1)
                value_part = match.group(2)
                # Escape quotes in the value part only
                escaped_value = value_part.replace('"', '\\"')
                return f'"{key_part}": "{escaped_value}"'
            
            # Pattern to find "key": "value with quotes" patterns
            pattern = r'"([^"]+)":\s*"([^"]*\'[^"]*)"'
            text = re.sub(pattern, escape_inner_quotes, text)
            
            return text
        except Exception as e:
            logger.error(f"Error fixing JSON quotes: {e}")
            return text
    
    async def _store_analysis_results(self, analysis_id: str, analysis_results: Dict[str, Any], ideas: List[Dict[str, Any]], scripts: List[Dict[str, Any]]):
        """Store all analysis results in database"""
        try:
            if not self.supabase:
                logger.warning("Supabase not available - results not stored")
                return
            
            # Store analysis results
            await self._store_viral_analysis_results(analysis_id, analysis_results)
            
            # Store viral ideas
            await self._store_viral_ideas(analysis_id, ideas)
            
            # Store generated scripts
            await self._store_generated_scripts(analysis_id, scripts)
            
            logger.info("✅ All analysis results stored successfully")
            
        except Exception as e:
            logger.error(f"Error storing analysis results: {e}")
    
    async def _store_viral_analysis_results(self, analysis_id: str, analysis_results: Dict[str, Any]):
        """Update viral_analysis_results table with correct schema"""
        try:
            self.supabase.client.table('viral_analysis_results').update({
                'viral_ideas': analysis_results.get('viral_ideas', []),
                'trending_patterns': analysis_results.get('winning_patterns', {}),
                'hook_analysis': analysis_results.get('top_competitor_analysis', []),
                'raw_ai_output': json.dumps(analysis_results),
                'status': 'ai_completed',
                'analysis_completed_at': datetime.utcnow().isoformat()
            }).eq('id', analysis_id).execute()
            
        except Exception as e:
            logger.error(f"Error storing viral analysis results: {e}")
    
    async def _store_viral_ideas(self, analysis_id: str, ideas: List[Dict[str, Any]]):
        """Store individual viral ideas with correct schema"""
        try:
            for idx, idea in enumerate(ideas):
                self.supabase.client.table('viral_ideas').insert({
                    'analysis_id': analysis_id,
                    'idea_text': idea.get('idea_title', '') + ': ' + idea.get('idea_description', ''),
                    'idea_rank': idx + 1,
                    'explanation': idea.get('why_it_will_work', '') or idea.get('explanation', ''),
                    'category': idea.get('category', 'general'),
                    'confidence_score': idea.get('confidence_score', 50),
                    'power_words': idea.get('power_words', [])
                }).execute()
                
        except Exception as e:
            logger.error(f"Error storing viral ideas: {e}")
    
    async def _store_generated_scripts(self, analysis_id: str, scripts: List[Dict[str, Any]]):
        """Store generated scripts with correct schema"""
        try:
            for script in scripts:
                self.supabase.client.table('viral_scripts').insert({
                    'analysis_id': analysis_id,
                    'script_title': script.get('script_title', ''),
                    'script_content': script.get('script_content', ''),
                    'script_type': script.get('script_type', 'reel'),
                    'estimated_duration': script.get('estimated_duration', 60),
                    'target_audience': script.get('target_audience', ''),
                    'primary_hook': script.get('primary_hook', ''),
                    'call_to_action': script.get('call_to_action', ''),
                    'source_reels': script.get('source_reels', []),
                    'script_structure': script.get('script_structure', {}),
                    'generation_prompt': "SCRIPT_GENERATOR_PROMPT",
                    'ai_model': "gpt-4o-mini",
                    'generation_temperature': 0.8,
                    'status': 'draft'
                }).execute()
                
        except Exception as e:
            logger.error(f"Error storing viral scripts: {e}")

# ========================================================================================
# MAIN ENTRY POINT
# ========================================================================================

async def process_viral_analysis(analysis_id: str) -> bool:
    """Main entry point for processing viral ideas analysis"""
    ai_processor = ViralIdeasAI()
    return await ai_processor.process_analysis(analysis_id)

if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1:
        analysis_id = sys.argv[1]
        result = asyncio.run(process_viral_analysis(analysis_id))
        print("Analysis completed" if result else "Analysis failed")
    else:
        print("Usage: python viral_ideas_ai_pipeline.py <analysis_id>")