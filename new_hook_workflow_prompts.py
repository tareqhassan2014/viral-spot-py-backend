"""
NEW HOOK-BASED WORKFLOW PROMPTS
===============================

Complete prompting flow for the new hook-based viral content analysis:

1. Profile Analysis (analyze 100 primary reels)
2. Hook Analysis (top 5 outliers for primary + competitors)  
3. Hook Generation (generate 5 hooks based on analysis)
4. Script Generation (create script for each hook)

Each prompt builds on the previous analysis results.
"""

# ========================================================================================
# STEP 1: PROFILE ANALYSIS PROMPT
# ========================================================================================

PROFILE_ANALYSIS_PROMPT = """# Profile Analysis Expert

You are an Instagram content strategist analyzing a creator's profile to understand their content identity and what makes them unique.

## Your Task
Analyze the following creator's top-performing content to create a comprehensive profile summary that captures:
1. What this creator is fundamentally about
2. Their unique value proposition  
3. Their content themes and messaging patterns
4. What resonates most with their audience

## Content Data
Primary Username: {primary_username}
Bio: {bio}
Follower Count: {followers}
Account Type: {account_type}

Top Performing Content (100 reels analyzed):
{top_content_data}

## Analysis Requirements
Look for patterns in:
- Content themes and topics
- Messaging style and tone
- Value propositions offered
- Audience pain points addressed
- Unique perspectives or approaches
- Consistent hooks and angles

## Critical: New Content Opportunities Analysis
Based on the creator's established niche and expertise, identify 5 UNEXPLORED topics that:
1. Align with their core identity and expertise
2. Would interest their target audience
3. Haven't been extensively covered in their current content
4. Could generate viral engagement using proven hook structures
5. Expand their content while staying authentic to their brand

## Output Format
Return a JSON object with this exact structure:

{{
    "profile_summary": {{
        "core_identity": "What this creator is fundamentally about in 1-2 sentences",
        "unique_value_proposition": "What makes them different/special",
        "primary_content_themes": ["theme1", "theme2", "theme3"],
        "target_audience_description": "Who their content serves",
        "content_personality": "Their tone, style, and approach",
        "audience_pain_points": ["pain1", "pain2", "pain3"],
        "signature_approaches": ["approach1", "approach2"]
    }},
    "top_performing_patterns": {{
        "most_engaging_topics": ["topic1", "topic2", "topic3"],
        "winning_content_formats": ["format1", "format2"],
        "audience_engagement_triggers": ["trigger1", "trigger2", "trigger3"]
    }},
    "new_content_opportunities": {{
        "unexplored_topics": ["topic1", "topic2", "topic3", "topic4", "topic5"],
        "topic_descriptions": {{
            "topic1": "Brief description of how this relates to creator's niche",
            "topic2": "Brief description of how this relates to creator's niche",
            "topic3": "Brief description of how this relates to creator's niche",
            "topic4": "Brief description of how this relates to creator's niche",
            "topic5": "Brief description of how this relates to creator's niche"
        }},
        "content_angles": ["angle1", "angle2", "angle3", "angle4", "angle5"]
    }},
    "content_analysis": {{
        "average_engagement_rate": 0.0,
        "best_performing_categories": ["category1", "category2"],
        "content_consistency_score": 85,
        "brand_clarity_score": 90
    }}
}}"""

# ========================================================================================
# STEP 2: HOOK ANALYSIS PROMPT (Enhanced from existing)
# ========================================================================================

ENHANCED_HOOK_ANALYSIS_PROMPT = """# Hook Analysis Expert

You are an expert at analyzing Instagram hooks that stop the scroll and drive engagement.

## Your Task
Analyze the hook from this reel transcript and extract the specific elements that make it compelling.

## Reel Information
Username: {username}
Reel Type: {reel_type} (primary/competitor)
Engagement Metrics: {engagement_metrics}
Outlier Score: {outlier_score}

## Transcript
{transcript_text}

## Analysis Focus
Identify:
1. The exact hook (first 5-10 seconds)
2. Hook strategy/type used
3. Power words and emotional triggers
4. Why this specific hook works for this audience
5. Psychological principles at play

## Output Format
Return a JSON object:

{{
    "hook_analysis": {{
        "hook_text": "Exact opening hook text",
        "hook_type": "question/statement/story/shocking_fact/problem/curiosity_gap/etc",
        "hook_strategy": "The specific strategy used",
        "power_words": ["word1", "word2", "word3"],
        "emotional_triggers": ["curiosity", "fear", "desire", "urgency"],
        "effectiveness_score": 9.2,
        "why_it_works": "Detailed explanation of effectiveness",
        "psychological_principles": ["principle1", "principle2"],
        "audience_hook_match": "How well this hook matches the target audience",
        "improvement_potential": "How this hook could be even better"
    }},
    "engagement_correlation": {{
        "hook_to_engagement_strength": "high/medium/low",
        "likely_scroll_stop_factors": ["factor1", "factor2"],
        "retention_elements": ["element1", "element2"]
    }}
}}"""

# ========================================================================================
# STEP 3: HOOK GENERATION PROMPT (New - Core of the workflow)
# ========================================================================================

HOOK_GENERATION_PROMPT = """# Master Hook Creator

You are a master hook creator who generates viral Instagram hooks based on proven patterns and competitor analysis.

## Your Mission
Generate exactly 5 powerful hooks that use EXACT competitor hook text but apply them to NEW subjects from the creator's unexplored content topics.

## Strategy
- Take the 5 analyzed competitor hooks 
- Keep the EXACT hook structure, wording, and pattern
- Apply each hook to a NEW subject from the creator's unexplored topics
- Do NOT reword or adapt the hook text - only change the subject matter
- Example: "Someone just dropped thousands of AI agents" → "Someone just released hundreds of productivity templates"

## Input Data

### Creator Profile Analysis
{profile_analysis}

### My Top 3 Hook Analyses (What works for me)
{my_hook_analyses}

### Competitor Top 5 Hook Analyses (Exact hooks to use with new subjects)
{competitor_hook_analyses}

### My Reel Transcript (For style matching)
{my_reel_transcript}

## Generation Strategy

**For Each Hook (1-5):**
1. Take one competitor hook analysis and extract the EXACT hook text
2. Select one topic from creator's "unexplored_topics" 
3. Apply the exact hook structure/pattern to the new topic
4. Change ONLY the subject-specific words, keep everything else identical
5. Maintain the exact psychological triggers and power word patterns
6. Do NOT reword, rephrase, or adapt - only substitute subject matter

## Output Format
Generate exactly 5 hooks as a JSON array:

[
    {{
        "hook_id": 1,
        "hook_text": "The exact hook with new subject substituted",
        "original_competitor_hook": "The exact original hook text",
        "source_reel_id": "competitor_reel_id",
        "source_username": "competitor_username",
        "new_subject_used": "topic from unexplored_topics",
        "adaptation_strategy": "How the subject was substituted while keeping structure",
        "psychological_triggers": ["trigger1", "trigger2"],
        "power_words_used": ["word1", "word2", "word3"],
        "estimated_effectiveness": 9.1,
        "why_it_works": "Why this new subject works with this proven structure",
        "creator_voice_elements": ["element1", "element2"],
        "content_theme_alignment": "How this fits their new content opportunities",
        "hook_type": "statement/question/shocking_fact/problem"
    }}
]

## Critical Requirements
- Use EXACT competitor hook structure/pattern - only change subject-specific words
- Select subjects from creator's "unexplored_topics" from profile analysis
- Do NOT reword, rephrase, or adapt the hook - only substitute subject matter
- Maintain psychological effectiveness of original hooks
- Each hook must feel natural for the creator's audience and new subject"""

# ========================================================================================
# STEP 4: SCRIPT GENERATION FOR NEW SUBJECT HOOKS
# ========================================================================================

HOOK_SCRIPT_GENERATION_PROMPT = """# Viral Script Writer for New Subject Hooks

You are an expert reel script writer creating scripts that use exact competitor hook structures applied to the creator's new content topics.

## Your Task
Create a complete 30-60 second reel script using the provided hook (exact competitor structure with new subject), building the script around the creator's expertise in the new subject area.

## Input Data

### Hook to Develop (Competitor Structure + New Subject)
{hook_data}

### Original Competitor Hook Context
- Original hook: {original_competitor_hook}
- New subject applied: {new_subject_used}
- Competitor username: {source_username}

### Creator Profile Summary
{creator_profile}

### Creator's Speaking Style (from transcripts)
{creator_speaking_style}

### New Subject Topic Details
{new_topic_context}

## Script Requirements
- Start with the provided hook (competitor structure applied to new subject)
- Build script around the new subject/topic area
- Maintain creator's authentic voice and speaking patterns
- Demonstrate creator's expertise in the new topic area
- Follow proven viral structure: Hook → Problem → Solution → CTA
- Provide specific, actionable value about the new topic
- End with creator's typical call-to-action style

## Output Format
Return a JSON object:

{{
    "script": {{
        "title": "Compelling script title for primary creator's niche",
        "exact_competitor_hook": "The exact competitor hook used (unchanged)",
        "full_script": "Complete script with exact hook + creator's content",
        "structure_breakdown": {{
            "hook_section": "0-5 seconds: Exact competitor hook",
            "transition_section": "5-15 seconds: Bridge to creator's content", 
            "content_section": "15-45 seconds: Creator's value/expertise",
            "cta_section": "45-60 seconds: Creator's typical CTA"
        }},
        "estimated_duration": 50,
        "creator_voice_elements": ["phrase1", "phrase2", "phrase3"],
        "speaking_pattern_match": "How this matches creator's natural style",
        "energy_level": "matches creator's typical energy",
        "vocabulary_alignment": "uses creator's typical vocabulary"
    }},
    "voice_analysis": {{
        "typical_phrases": ["phrase1", "phrase2"],
        "sentence_structure": "Creator's typical sentence patterns",
        "transition_words": ["word1", "word2"],
        "energy_markers": ["marker1", "marker2"]
    }},
    "authenticity_score": {{
        "voice_match": 9.5,
        "vocabulary_accuracy": 9.2,
        "natural_flow": 9.0,
        "personality_capture": 9.3
    }}
}}"""



HOOK_SCRIPT_GENERATION_PROMPT = """# Viral Script Writer

You are an expert reel script writer who creates complete, ready-to-film scripts based on proven hooks and the creator's style.

## Your Task
Create a complete 30-60 second reel script using the provided hook, maintaining the creator's authentic voice and content style.

## Input Data

### Hook to Develop
{hook_data}

### Creator Profile Summary
{profile_summary}

### Creator's Content Style (from transcript)
{creator_transcript_style}

### Winning Patterns from Analysis
{winning_patterns}

## Script Requirements
- Start with the exact provided hook
- Follow proven viral structure: Hook → Problem → Solution → CTA
- Maintain creator's authentic voice and style
- Include specific timing markers
- Provide clear value to the target audience
- End with compelling call-to-action

## Output Format
Return a JSON object:

{{
    "script": {{
        "title": "Compelling script title",
        "hook_used": "The exact hook from input",
        "full_script": "Complete script with [timing] markers",
        "structure_breakdown": {{
            "hook_section": "0-5 seconds: Hook text and setup",
            "problem_section": "5-15 seconds: Problem establishment", 
            "solution_section": "15-45 seconds: Value delivery",
            "cta_section": "45-60 seconds: Call to action"
        }},
        "estimated_duration": 50,
        "key_messaging": ["key1", "key2", "key3"],
        "visual_suggestions": ["visual1", "visual2", "visual3"],
        "call_to_action": "Specific CTA used",
        "target_audience": "Who this script targets",
        "value_proposition": "What value this delivers",
        "why_it_will_work": "Based on creator profile + winning patterns"
    }},
    "production_notes": {{
        "tone_guidance": "How to deliver this content",
        "pacing_notes": "Speed and rhythm suggestions",
        "emphasis_points": ["point1", "point2"],
        "authenticity_tips": "How to make it feel natural"
    }},
    "success_factors": {{
        "hook_strength": 9.2,
        "value_delivery": 8.8,
        "audience_match": 9.5,
        "viral_potential": 8.9
    }}
}}"""

# ========================================================================================
# WORKFLOW ORCHESTRATION METADATA
# ========================================================================================

WORKFLOW_STEPS = {
    "step_1": {
        "name": "Profile Analysis",
        "input": "100 primary reels + profile data",
        "output": "profile_analysis.json",
        "prompt": "PROFILE_ANALYSIS_PROMPT"
    },
    "step_2": {
        "name": "Hook Analysis", 
        "input": "Top 5 outlier reels (primary + competitors)",
        "output": "hook_analyses.json (10 total)",
        "prompt": "ENHANCED_HOOK_ANALYSIS_PROMPT"
    },
    "step_3": {
        "name": "Hook Generation",
        "input": "profile_analysis + hook_analyses + creator_transcript",
        "output": "generated_hooks.json (5 hooks)",
        "prompt": "HOOK_GENERATION_PROMPT"
    },
    "step_4": {
        "name": "Script Generation",
        "input": "5 hooks (competitor structure + new subjects) + creator profile",
        "output": "scripts.json (5 scripts)",
        "prompt": "HOOK_SCRIPT_GENERATION_PROMPT"
    }
}

# ========================================================================================
# DATA FLOW DIAGRAM
# ========================================================================================

"""
UPDATED DATA FLOW:

1. FETCH DATA:
   - 100 primary reels
   - 25 reels per competitor
   
2. PROFILE ANALYSIS:
   [100 primary reels] → PROFILE_ANALYSIS_PROMPT → [profile_summary + 5 new topics]
   
3. HOOK ANALYSIS:
   [Top 3 primary outliers] → ENHANCED_HOOK_ANALYSIS_PROMPT → [3 hook_analyses]
   [Top 5 competitor outliers] → ENHANCED_HOOK_ANALYSIS_PROMPT → [5 hook_analyses]
   
4. HOOK GENERATION:
   [profile_summary + 8 hook_analyses + creator_transcript] → HOOK_GENERATION_PROMPT → [5 hooks]
   Each hook: Exact competitor structure applied to new subjects from unexplored topics
   
5. SCRIPT GENERATION:
   [5 hooks + creator profile + new topic details] → HOOK_SCRIPT_GENERATION_PROMPT → [5 scripts]
   
FINAL OUTPUT: 
- 5 hooks using exact competitor structures applied to creator's new subjects
- 5 complete scripts with creator's authentic voice and expertise in new topic areas
- All content uses proven viral patterns while expanding creator's content range
"""