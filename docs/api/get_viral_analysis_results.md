# GET `/api/viral-analysis/{queue_id}/results` ⚡

Retrieves the final results of a viral analysis job with comprehensive analysis data, reels, and insights.

## Description

This endpoint retrieves the complete, processed results of a viral ideas analysis job. It serves as the primary data source for displaying comprehensive analysis results to users, aggregating data from multiple database tables to provide a unified response.

**Key Features:**

-   **Multi-table data aggregation** from 7+ database tables
-   **Flexible JSONB analysis data** supporting multiple workflow versions
-   **Real-time CDN URL generation** for profile images
-   **Legacy compatibility** for backward-compatible frontend integrations
-   **Enhanced content transformation** using working endpoint patterns
-   **Performance-optimized queries** with proper indexing

The response includes:

-   **Analysis Metadata**: Process information, timing, and analysis run details
-   **Primary Profile**: Complete user profile data with computed CDN URLs
-   **Competitor Profiles**: Analyzed competitor profile information
-   **Content Collections**: Primary user reels, competitor reels, and analyzed reels
-   **Core Analysis Data**: AI-generated insights stored in flexible JSONB format
-   **Generated Scripts**: Full viral scripts and summaries from the analysis
-   **Legacy Compatibility**: Extracted hooks and sections for older frontend versions

## Path Parameters

| Parameter  | Type   | Description                                       |
| :--------- | :----- | :------------------------------------------------ |
| `queue_id` | string | The ID of the completed analysis job to retrieve. |

## Execution Flow

1.  **Request Validation**: The endpoint receives a GET request with a `queue_id` UUID parameter in the URL path.

2.  **Queue Verification**:

    -   Queries `viral_ideas_queue` table to verify the queue exists
    -   Extracts `primary_username` for subsequent profile queries
    -   Returns `404 Not Found` if queue doesn't exist

3.  **Primary Profile Data Retrieval**:

    -   Queries `primary_profiles` table with 13 essential fields
    -   Includes metrics: followers, total_reels, median_views, total_views, total_likes, total_comments
    -   Handles missing profile data gracefully with empty object fallback

4.  **Analysis Results Retrieval**:

    -   Queries `viral_analysis_results` table for latest analysis run (ORDER BY analysis_run DESC LIMIT 1)
    -   Fetches 8 metadata fields including timing, counts, and workflow version
    -   Extracts and parses the main `analysis_data` JSONB field with error handling
    -   Returns `404 Not Found` if no analysis results exist

5.  **Analyzed Reels Data**:

    -   Queries `viral_analysis_reels` table for reels used in the specific analysis
    -   Includes performance metrics captured at analysis time
    -   Fetches transcript status and hook analysis metadata
    -   Orders by reel_type and rank_in_selection for consistent presentation

6.  **Primary User Content**:

    -   Queries `content` table with JOIN to `primary_profiles` for enhanced data
    -   Applies `_transform_content_for_frontend()` transformation method
    -   Limits to top 50 reels ordered by view_count DESC
    -   Includes complete profile context within each reel

7.  **Competitor Data Aggregation**:

    -   Queries `viral_ideas_competitors` for active competitors only (`is_active = True`)
    -   Fetches competitor content from `content` table with profile JOINs
    -   Applies same content transformation as working endpoints
    -   Extracts and processes profile images with CDN URL generation
    -   Limits to top 100 competitor reels ordered by outlier_score DESC

8.  **Viral Scripts Integration**:

    -   Queries `viral_scripts` table for any additional generated scripts
    -   Orders by created_at DESC for latest scripts first
    -   Provides 10 comprehensive script fields including metadata

9.  **Response Assembly and Transformation**:

    -   Combines all data sources into structured response object
    -   Provides both complete `analysis_data` and extracted legacy sections
    -   Generates CDN URLs for all profile images using Supabase Storage
    -   Creates backward-compatible `viral_ideas` array for legacy frontend support
    -   Structures response for optimal frontend consumption

10. **Error Handling and Response**:
    -   Comprehensive try-catch with proper HTTP status codes
    -   Detailed error logging for debugging
    -   Graceful handling of missing data with sensible defaults

## Detailed Implementation Guide

### Python (FastAPI) - Complete Implementation

```python
# In backend_api.py

@app.get("/api/viral-analysis/{queue_id}/results")
async def get_viral_analysis_results(
    queue_id: str,
    api_instance: ViralSpotAPI = Depends(get_api)
):
    """Get viral analysis results for a queue entry"""
    try:
        # Step 1: Verify queue exists and get primary username
        queue_result = api_instance.supabase.client.table('viral_ideas_queue').select(
            'primary_username'
        ).eq('id', queue_id).execute()

        if not queue_result.data:
            raise HTTPException(status_code=404, detail="Queue not found")

        primary_username = queue_result.data[0]['primary_username']

        # Step 2: Get comprehensive primary profile data
        profile_result = api_instance.supabase.client.table('primary_profiles').select(
            'username, profile_name, bio, followers, posts_count, is_verified, '
            'profile_image_url, profile_image_path, account_type, total_reels, '
            'median_views, total_views, total_likes, total_comments'
        ).eq('username', primary_username).execute()

        profile_data = profile_result.data[0] if profile_result.data else {}

        # Step 3: Get latest analysis results with JSONB parsing
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

        # Step 4: Parse analysis_data JSONB with robust error handling
        analysis_data_json = analysis_record.get('analysis_data', '{}')
        if isinstance(analysis_data_json, str):
            try:
                analysis_data = json.loads(analysis_data_json)
            except (json.JSONDecodeError, TypeError):
                analysis_data = {}
        else:
            analysis_data = analysis_data_json or {}

        # Step 5: Get reels used in analysis with enhanced metadata
        reels_result = api_instance.supabase.client.table('viral_analysis_reels').select(
            'content_id, reel_type, username, rank_in_selection, '
            'view_count_at_analysis, like_count_at_analysis, comment_count_at_analysis, '
            'transcript_completed, hook_text, power_words, analysis_metadata'
        ).eq('analysis_id', analysis_id).order('reel_type, rank_in_selection').execute()

        # Step 6: Get primary user reels with JOIN and transformation
        primary_reels_result = api_instance.supabase.client.table('content').select('''
            *,
            primary_profiles!profile_id (
                username, profile_name, followers, profile_image_url,
                profile_image_path, is_verified, account_type
            )
        ''').eq('username', primary_username).order('view_count', desc=True).limit(50).execute()

        # Transform primary user reels using production method
        if primary_reels_result.data:
            for i, reel in enumerate(primary_reels_result.data):
                primary_reels_result.data[i] = api_instance._transform_content_for_frontend(reel)

        # Step 7: Get active competitors and their content
        competitors_result = api_instance.supabase.client.table('viral_ideas_competitors').select(
            'competitor_username'
        ).eq('queue_id', queue_id).eq('is_active', True).execute()

        competitor_usernames = [comp['competitor_username'] for comp in competitors_result.data or []]

        # Step 8: Fetch competitor reels and profiles in optimized single query
        competitor_reels_result = None
        competitor_profiles_data = []

        if competitor_usernames:
            competitor_reels_result = api_instance.supabase.client.table('content').select('''
                *,
                primary_profiles!profile_id (
                    username, profile_name, followers, profile_image_url,
                    profile_image_path, is_verified, account_type
                )
            ''').in_('username', competitor_usernames).order('outlier_score', desc=True).limit(100).execute()

            # Transform competitor data and extract profiles
            if competitor_reels_result.data:
                for i, reel in enumerate(competitor_reels_result.data):
                    competitor_reels_result.data[i] = api_instance._transform_content_for_frontend(reel)

                    # Extract unique profile data for separate profiles array
                    if reel.get('primary_profiles'):
                        profile = reel['primary_profiles']
                        if profile and profile.get('username'):
                            # Generate CDN URLs for profile images
                            if profile.get('profile_image_path'):
                                profile['profile_image_url'] = api_instance.supabase.client.storage.from_('profile-images').get_public_url(profile['profile_image_path'])
                            competitor_profiles_data.append(profile)

        # Step 9: Get additional viral scripts from dedicated table
        scripts_result = api_instance.supabase.client.table('viral_scripts').select(
            'id, script_title, script_content, script_type, estimated_duration, '
            'target_audience, primary_hook, call_to_action, source_reels, script_structure, status'
        ).eq('analysis_id', analysis_id).order('created_at', desc=True).execute()

        # Step 10: Assemble comprehensive response
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
                    'profile_image_url': api_instance.supabase.client.storage.from_('profile-images').get_public_url(
                        profile_data.get('profile_image_path', '')
                    ) if profile_data.get('profile_image_path') else profile_data.get('profile_image_url', ''),
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
                'viral_scripts_table': scripts_result.data or [],

                # Complete analysis data from JSONB field - contains all AI insights
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
```

**Critical Implementation Details:**

1. **Multi-table Data Aggregation**: This endpoint performs 7+ database queries to assemble comprehensive results
2. **Robust JSONB Handling**: Safely parses the `analysis_data` JSONB field with fallback to empty object
3. **Content Transformation**: Uses the same `_transform_content_for_frontend()` method as production endpoints
4. **CDN URL Generation**: Dynamically generates Supabase Storage URLs for all profile images
5. **Active Competitor Filtering**: Only includes competitors marked as `is_active = True`
6. **Latest Analysis Selection**: Uses `ORDER BY analysis_run DESC LIMIT 1` to get most recent analysis
7. **Performance Optimization**: Limits content queries (50 primary, 100 competitor reels)
8. **Legacy Support**: Provides both new `analysis_data` format and extracted legacy sections

### Nest.js (Mongoose) - Complete Implementation

```typescript
// ===============================================
// SCHEMAS (with MongoDB _id identifiers)
// ===============================================

// viral-ideas-queue.schema.ts
import { Prop, Schema, SchemaFactory } from "@nestjs/mongoose";
import { Document, Types } from "mongoose";

@Schema({ timestamps: true })
export class ViralIdeasQueue {
    _id: Types.ObjectId; // MongoDB default _id

    @Prop({ required: true, unique: true })
    session_id: string;

    @Prop({ required: true })
    primary_username: string;

    @Prop({ type: Object, default: {} })
    content_strategy: {
        contentType?: string;
        targetAudience?: string;
        goals?: string;
    };

    @Prop({ default: "pending" })
    status: string;

    @Prop({ default: 5 })
    priority: number;
}

export const ViralIdeasQueueSchema =
    SchemaFactory.createForClass(ViralIdeasQueue);

// viral-analysis-results.schema.ts
@Schema({ timestamps: true })
export class ViralAnalysisResults {
    _id: Types.ObjectId; // MongoDB default _id

    @Prop({ type: Types.ObjectId, ref: "ViralIdeasQueue", required: true })
    queue_id: Types.ObjectId;

    @Prop({ default: 1 })
    analysis_run: number;

    @Prop({ default: "initial" })
    analysis_type: string;

    @Prop({ default: 0 })
    total_reels_analyzed: number;

    @Prop({ default: 0 })
    primary_reels_count: number;

    @Prop({ default: 0 })
    competitor_reels_count: number;

    @Prop({ default: 0 })
    transcripts_fetched: number;

    @Prop({ type: Object, default: {} })
    analysis_data: {
        workflow_version?: string;
        analysis_timestamp?: string;
        profile_analysis?: any;
        individual_reel_analyses?: any[];
        generated_hooks?: any[];
        complete_scripts?: any[];
        scripts_summary?: any[];
        analysis_summary?: any;
    };

    @Prop({ default: "v2_json" })
    workflow_version: string;

    @Prop({ default: "pending" })
    status: string;

    @Prop()
    started_at: Date;

    @Prop()
    analysis_completed_at: Date;
}

export const ViralAnalysisResultsSchema =
    SchemaFactory.createForClass(ViralAnalysisResults);

// primary-profile.schema.ts
@Schema({ timestamps: true })
export class PrimaryProfile {
    _id: Types.ObjectId; // MongoDB default _id (13 columns total)

    @Prop({ required: true, unique: true })
    username: string;

    @Prop()
    profile_name: string;

    @Prop()
    bio: string;

    @Prop({ default: 0 })
    followers: number;

    @Prop({ default: 0 })
    posts_count: number;

    @Prop({ default: false })
    is_verified: boolean;

    @Prop()
    profile_image_url: string;

    @Prop()
    profile_image_path: string;

    @Prop({ default: "Personal" })
    account_type: string;

    @Prop({ default: 0 })
    total_reels: number;

    @Prop({ default: 0 })
    median_views: number;

    @Prop({ default: 0 })
    total_views: number;

    @Prop({ default: 0 })
    total_likes: number;

    @Prop({ default: 0 })
    total_comments: number;
}

export const PrimaryProfileSchema =
    SchemaFactory.createForClass(PrimaryProfile);

// ===============================================
// CONTROLLER IMPLEMENTATION
// ===============================================

// viral-ideas.controller.ts
import {
    Controller,
    Get,
    Param,
    NotFoundException,
    InternalServerErrorException,
} from "@nestjs/common";
import {
    ApiTags,
    ApiOperation,
    ApiParam,
    ApiResponse,
    ApiNotFoundResponse,
    ApiInternalServerErrorResponse,
} from "@nestjs/swagger";

@ApiTags("viral-analysis")
@Controller("api/viral-analysis")
export class ViralIdeasController {
    constructor(private readonly viralIdeasService: ViralIdeasService) {}

    @Get(":queueId/results")
    @ApiOperation({
        summary: "Get viral analysis results",
        description:
            "Retrieves comprehensive viral analysis results for a completed queue entry",
    })
    @ApiParam({
        name: "queueId",
        description: "MongoDB ObjectId of the completed analysis queue entry",
        type: "string",
    })
    @ApiResponse({
        status: 200,
        description: "Analysis results retrieved successfully",
        schema: {
            type: "object",
            properties: {
                success: { type: "boolean", example: true },
                data: {
                    type: "object",
                    description: "Complete analysis results with all sections",
                },
            },
        },
    })
    @ApiNotFoundResponse({
        description: "Queue not found or analysis results not available",
    })
    @ApiInternalServerErrorResponse({
        description: "Server error during results retrieval",
    })
    async getAnalysisResults(@Param("queueId") queueId: string) {
        try {
            const result = await this.viralIdeasService.getAnalysisResults(
                queueId
            );

            if (!result) {
                throw new NotFoundException("Analysis results not found");
            }

            return { success: true, data: result };
        } catch (error) {
            if (error instanceof NotFoundException) {
                throw error;
            }
            throw new InternalServerErrorException(
                "Failed to get analysis results"
            );
        }
    }
}

// ===============================================
// SERVICE IMPLEMENTATION
// ===============================================

// viral-ideas.service.ts
import { Injectable, NotFoundException } from "@nestjs/common";
import { InjectModel } from "@nestjs/mongoose";
import { Model, Types } from "mongoose";

@Injectable()
export class ViralIdeasService {
    constructor(
        @InjectModel("ViralIdeasQueue")
        private queueModel: Model<ViralIdeasQueue>,
        @InjectModel("ViralAnalysisResults")
        private analysisResultsModel: Model<ViralAnalysisResults>,
        @InjectModel("PrimaryProfile")
        private profileModel: Model<PrimaryProfile>,
        @InjectModel("Content") private contentModel: Model<Content>,
        @InjectModel("ViralIdeasCompetitors")
        private competitorsModel: Model<ViralIdeasCompetitors>,
        @InjectModel("ViralAnalysisReels")
        private analysisReelsModel: Model<ViralAnalysisReels>,
        @InjectModel("ViralScripts") private scriptsModel: Model<ViralScripts>,
        private storageService: StorageService // For CDN URL generation
    ) {}

    async getAnalysisResults(queueId: string): Promise<any> {
        // Step 1: Validate queueId and get primary username
        if (!Types.ObjectId.isValid(queueId)) {
            throw new NotFoundException("Invalid queue ID format");
        }

        const queue = await this.queueModel
            .findById(queueId)
            .select("primary_username")
            .exec();

        if (!queue) {
            throw new NotFoundException("Queue not found");
        }

        // Step 2: Get primary profile data (13 essential fields)
        const profileData = await this.profileModel
            .findOne({ username: queue.primary_username })
            .select(
                "username profile_name bio followers posts_count is_verified profile_image_url profile_image_path account_type total_reels median_views total_views total_likes total_comments"
            )
            .exec();

        // Step 3: Get latest analysis results with JSONB analysis_data
        const analysisResult = await this.analysisResultsModel
            .findOne({ queue_id: new Types.ObjectId(queueId) })
            .sort({ analysis_run: -1 })
            .select(
                "_id analysis_run analysis_type status total_reels_analyzed primary_reels_count competitor_reels_count transcripts_fetched analysis_data workflow_version started_at analysis_completed_at"
            )
            .exec();

        if (!analysisResult) {
            throw new NotFoundException("Analysis results not found");
        }

        // Step 4: Parse analysis_data with robust error handling
        let analysisData = {};
        try {
            analysisData =
                typeof analysisResult.analysis_data === "string"
                    ? JSON.parse(analysisResult.analysis_data)
                    : analysisResult.analysis_data || {};
        } catch (error) {
            console.warn("Failed to parse analysis_data JSONB:", error);
            analysisData = {};
        }

        // Step 5: Get reels used in analysis with enhanced metadata
        const analyzedReels = await this.analysisReelsModel
            .find({ analysis_id: analysisResult._id })
            .select(
                "content_id reel_type username rank_in_selection view_count_at_analysis like_count_at_analysis comment_count_at_analysis transcript_completed hook_text power_words analysis_metadata"
            )
            .sort({ reel_type: 1, rank_in_selection: 1 })
            .exec();

        // Step 6: Get primary user reels with profile population
        const primaryReels = await this.contentModel
            .find({ username: queue.primary_username })
            .populate({
                path: "profile_id",
                model: "PrimaryProfile",
                select: "username profile_name followers profile_image_url profile_image_path is_verified account_type",
            })
            .sort({ view_count: -1 })
            .limit(50)
            .exec();

        // Transform primary reels for frontend
        const transformedPrimaryReels = await Promise.all(
            primaryReels.map((reel) => this.transformContentForFrontend(reel))
        );

        // Step 7: Get active competitors
        const competitors = await this.competitorsModel
            .find({ queue_id: new Types.ObjectId(queueId), is_active: true })
            .select("competitor_username")
            .exec();

        const competitorUsernames = competitors.map(
            (comp) => comp.competitor_username
        );

        // Step 8: Get competitor reels and extract profiles
        let competitorReels = [];
        let competitorProfilesData = [];

        if (competitorUsernames.length > 0) {
            const competitorReelsData = await this.contentModel
                .find({ username: { $in: competitorUsernames } })
                .populate({
                    path: "profile_id",
                    model: "PrimaryProfile",
                    select: "username profile_name followers profile_image_url profile_image_path is_verified account_type",
                })
                .sort({ outlier_score: -1 })
                .limit(100)
                .exec();

            // Transform competitor reels and extract unique profiles
            const profilesMap = new Map();
            competitorReels = await Promise.all(
                competitorReelsData.map(async (reel) => {
                    const transformed = await this.transformContentForFrontend(
                        reel
                    );

                    // Extract unique profile data
                    if (
                        reel.profile_id &&
                        !profilesMap.has(reel.profile_id.username)
                    ) {
                        const profile = reel.profile_id;
                        // Generate CDN URL for profile image
                        if (profile.profile_image_path) {
                            profile.profile_image_url =
                                await this.storageService.getPublicUrl(
                                    "profile-images",
                                    profile.profile_image_path
                                );
                        }
                        profilesMap.set(profile.username, profile);
                        competitorProfilesData.push(profile);
                    }

                    return transformed;
                })
            );
        }

        // Step 9: Get viral scripts from dedicated collection
        const viralScripts = await this.scriptsModel
            .find({ analysis_id: analysisResult._id })
            .select(
                "_id script_title script_content script_type estimated_duration target_audience primary_hook call_to_action source_reels script_structure status"
            )
            .sort({ createdAt: -1 })
            .exec();

        // Step 10: Assemble comprehensive response
        return {
            analysis: {
                id: analysisResult._id.toString(),
                status: analysisResult.status,
                workflow_version: analysisResult.workflow_version,
                started_at: analysisResult.started_at,
                analysis_completed_at: analysisResult.analysis_completed_at,
                total_reels_analyzed: analysisResult.total_reels_analyzed || 0,
                primary_reels_count: analysisResult.primary_reels_count || 0,
                competitor_reels_count:
                    analysisResult.competitor_reels_count || 0,
                transcripts_fetched: analysisResult.transcripts_fetched || 0,
            },
            primary_profile: {
                username: profileData?.username || queue.primary_username,
                profile_name: profileData?.profile_name || "",
                bio: profileData?.bio || "",
                followers: profileData?.followers || 0,
                posts_count: profileData?.posts_count || 0,
                is_verified: profileData?.is_verified || false,
                profile_image_url: profileData?.profile_image_path
                    ? await this.storageService.getPublicUrl(
                          "profile-images",
                          profileData.profile_image_path
                      )
                    : profileData?.profile_image_url || "",
                profile_image_path: profileData?.profile_image_path || "",
                account_type: profileData?.account_type || "Personal",
                total_reels: profileData?.total_reels || 0,
                median_views: profileData?.median_views || 0,
                total_views: profileData?.total_views || 0,
                total_likes: profileData?.total_likes || 0,
                total_comments: profileData?.total_comments || 0,
            },
            analyzed_reels: analyzedReels || [],
            primary_user_reels: transformedPrimaryReels || [],
            competitor_reels: competitorReels || [],
            competitor_profiles: competitorProfilesData,
            viral_scripts_table: viralScripts || [],

            // Complete analysis data from JSONB field - contains all AI insights
            analysis_data: analysisData,

            // Legacy compatibility - extract hooks for backward compatibility
            viral_ideas: this.extractLegacyHooks(analysisData),

            // Extract key sections for easier frontend access
            profile_analysis: analysisData.profile_analysis || {},
            generated_hooks: analysisData.generated_hooks || [],
            individual_reel_analyses:
                analysisData.individual_reel_analyses || [],
            complete_scripts: analysisData.complete_scripts || [],
            scripts_summary: analysisData.scripts_summary || [],
            analysis_summary: analysisData.analysis_summary || {},
        };
    }

    // ===============================================
    // HELPER METHODS
    // ===============================================

    private extractLegacyHooks(analysisData: any): any[] {
        if (!analysisData.generated_hooks) return [];

        return analysisData.generated_hooks.map((hook: any, index: number) => ({
            id: `hook_${index}`,
            idea_text: hook.hook_text || "",
            explanation: hook.adaptation_strategy || "",
            confidence_score: hook.effectiveness_score || 0,
            power_words: hook.psychological_triggers || [],
        }));
    }

    private async transformContentForFrontend(content: any): Promise<any> {
        // Apply the same transformation logic as working endpoints
        const transformed = {
            ...content.toObject(),
            // Add any necessary transformations
            profile_data: content.profile_id
                ? {
                      username: content.profile_id.username,
                      profile_name: content.profile_id.profile_name,
                      followers: content.profile_id.followers,
                      is_verified: content.profile_id.is_verified,
                      profile_image_url: content.profile_id.profile_image_path
                          ? await this.storageService.getPublicUrl(
                                "profile-images",
                                content.profile_id.profile_image_path
                            )
                          : content.profile_id.profile_image_url,
                  }
                : null,
        };

        return transformed;
    }
}

// ===============================================
// STORAGE SERVICE FOR CDN URLs
// ===============================================

// storage.service.ts
@Injectable()
export class StorageService {
    constructor(private configService: ConfigService) {}

    async getPublicUrl(bucket: string, path: string): Promise<string> {
        const supabaseUrl = this.configService.get("SUPABASE_URL");
        return `${supabaseUrl}/storage/v1/object/public/${bucket}/${path}`;
    }
}

// ===============================================
// DTO FOR REQUEST/RESPONSE VALIDATION
// ===============================================

// get-viral-analysis-results.dto.ts
import { IsUUID, IsNotEmpty } from "class-validator";
import { ApiProperty } from "@nestjs/swagger";

export class GetAnalysisResultsParamsDto {
    @ApiProperty({
        description: "MongoDB ObjectId of the analysis queue entry",
        example: "507f1f77bcf86cd799439011",
    })
    @IsNotEmpty()
    queueId: string; // MongoDB _id as string
}

export class AnalysisResultsResponseDto {
    @ApiProperty({ example: true })
    success: boolean;

    @ApiProperty({
        description: "Complete analysis results data",
        type: "object",
    })
    data: {
        analysis: {
            id: string;
            status: string;
            workflow_version: string;
            started_at: Date;
            analysis_completed_at: Date;
            total_reels_analyzed: number;
            primary_reels_count: number;
            competitor_reels_count: number;
            transcripts_fetched: number;
        };
        primary_profile: any;
        analyzed_reels: any[];
        primary_user_reels: any[];
        competitor_reels: any[];
        competitor_profiles: any[];
        viral_scripts_table: any[];
        analysis_data: any; // Main JSONB analysis insights
        viral_ideas: any[]; // Legacy compatibility
        profile_analysis: any;
        generated_hooks: any[];
        individual_reel_analyses: any[];
        complete_scripts: any[];
        scripts_summary: any[];
        analysis_summary: any;
    };
}
```

## Responses

### Success: 200 OK

Returns a comprehensive JSON object with complete analysis results, aggregated from multiple database tables.

**Complete Response Structure:**

```json
{
    "success": true,
    "data": {
        "analysis": {
            "id": "507f1f77bcf86cd799439011",
            "status": "completed",
            "workflow_version": "hook_based_v2",
            "started_at": "2024-01-15T10:30:00Z",
            "analysis_completed_at": "2024-01-15T10:45:23Z",
            "total_reels_analyzed": 58,
            "primary_reels_count": 8,
            "competitor_reels_count": 50,
            "transcripts_fetched": 47
        },
        "primary_profile": {
            "username": "user_profile",
            "profile_name": "Content Creator",
            "bio": "Creating viral content daily 🚀",
            "followers": 125000,
            "posts_count": 342,
            "is_verified": true,
            "profile_image_url": "https://your-supabase.storage.supabase.co/storage/v1/object/public/profile-images/user_profile.jpg",
            "profile_image_path": "user_profile.jpg",
            "account_type": "Influencer",
            "total_reels": 156,
            "median_views": 45000,
            "total_views": 2850000,
            "total_likes": 185000,
            "total_comments": 12400
        },
        "analyzed_reels": [
            {
                "content_id": "reel_abc123",
                "reel_type": "primary",
                "username": "user_profile",
                "rank_in_selection": 1,
                "view_count_at_analysis": 125000,
                "like_count_at_analysis": 8500,
                "comment_count_at_analysis": 420,
                "transcript_completed": true,
                "hook_text": "The one mistake that's killing your growth...",
                "power_words": ["mistake", "killing", "growth"],
                "analysis_metadata": {
                    "outlier_score": 0.95,
                    "engagement_rate": 0.078,
                    "transcript_quality": "high"
                }
            }
        ],
        "primary_user_reels": [
            {
                "content_id": "reel_def456",
                "username": "user_profile",
                "description": "5 tips to grow your business...",
                "view_count": 98000,
                "like_count": 7200,
                "comment_count": 385,
                "outlier_score": 0.88,
                "profile_data": {
                    "username": "user_profile",
                    "profile_name": "Content Creator",
                    "followers": 125000,
                    "is_verified": true,
                    "profile_image_url": "https://cdn-url..."
                }
            }
        ],
        "competitor_reels": [
            {
                "content_id": "comp_reel_789",
                "username": "competitor1",
                "description": "The secret they don't want you to know...",
                "view_count": 2500000,
                "like_count": 125000,
                "comment_count": 8900,
                "outlier_score": 0.97,
                "profile_data": {
                    "username": "competitor1",
                    "profile_name": "Viral Creator",
                    "followers": 850000,
                    "is_verified": true
                }
            }
        ],
        "competitor_profiles": [
            {
                "username": "competitor1",
                "profile_name": "Viral Creator",
                "followers": 850000,
                "profile_image_url": "https://cdn-url...",
                "is_verified": true,
                "account_type": "Influencer"
            }
        ],
        "viral_scripts_table": [
            {
                "_id": "507f1f77bcf86cd799439022",
                "script_title": "Growth Hack Script #1",
                "script_content": "Hook: The one mistake...\nSetup: Most creators think...\nPunch: But here's what actually works...",
                "script_type": "educational",
                "estimated_duration": 45,
                "target_audience": "aspiring creators",
                "primary_hook": "The one mistake that's killing your growth",
                "call_to_action": "Save this post for later!",
                "source_reels": ["reel_abc123", "comp_reel_789"],
                "script_structure": {
                    "hook_duration": 3,
                    "setup_duration": 15,
                    "content_duration": 22,
                    "cta_duration": 5
                },
                "status": "approved"
            }
        ],
        "analysis_data": {
            "workflow_version": "hook_based_v2",
            "analysis_timestamp": "2024-01-15T10:45:23.456Z",
            "profile_analysis": {
                "content_identity": {
                    "primary_themes": [
                        "business growth",
                        "productivity",
                        "entrepreneurship"
                    ],
                    "content_style": "educational with personal stories",
                    "target_demographic": "aspiring entrepreneurs 25-35",
                    "engagement_patterns": {
                        "best_posting_times": ["6pm-8pm EST"],
                        "high_engagement_topics": [
                            "productivity hacks",
                            "business mistakes"
                        ],
                        "content_format_preferences": "quick tips with personal anecdotes"
                    }
                },
                "audience_analysis": {
                    "primary_interests": [
                        "business",
                        "self-improvement",
                        "productivity"
                    ],
                    "pain_points": [
                        "time management",
                        "scaling business",
                        "work-life balance"
                    ],
                    "aspirations": [
                        "financial freedom",
                        "successful business",
                        "personal growth"
                    ]
                },
                "competitive_positioning": {
                    "unique_angle": "practical business advice with vulnerability",
                    "differentiation_factors": [
                        "authentic storytelling",
                        "actionable insights"
                    ],
                    "content_gaps": [
                        "advanced strategy content",
                        "team management tips"
                    ]
                }
            },
            "individual_reel_analyses": [
                {
                    "content_id": "reel_abc123",
                    "reel_type": "primary",
                    "username": "user_profile",
                    "hook_analysis": {
                        "hook_text": "The one mistake that's killing your growth...",
                        "hook_effectiveness": 0.92,
                        "psychological_triggers": [
                            "fear of loss",
                            "curiosity gap",
                            "authority"
                        ],
                        "structure_analysis": "problem identification + promise of solution",
                        "word_choice_impact": {
                            "power_words": ["mistake", "killing", "growth"],
                            "emotional_impact": "high urgency + personal relevance"
                        }
                    },
                    "content_analysis": {
                        "main_theme": "common business growth mistake",
                        "teaching_method": "problem + solution framework",
                        "credibility_indicators": [
                            "personal experience",
                            "specific examples"
                        ],
                        "engagement_drivers": [
                            "relatable problem",
                            "actionable solution"
                        ]
                    },
                    "performance_context": {
                        "view_count": 125000,
                        "engagement_rate": 0.078,
                        "outlier_score": 0.95,
                        "performance_tier": "top 5% of profile"
                    }
                }
            ],
            "generated_hooks": [
                {
                    "hook_id": 1,
                    "hook_text": "I lost $50k because I ignored this one rule...",
                    "adaptation_strategy": "Personal vulnerability + specific loss amount + curiosity gap",
                    "based_on_competitors": ["competitor1", "competitor2"],
                    "psychological_triggers": [
                        "loss aversion",
                        "curiosity",
                        "social proof"
                    ],
                    "effectiveness_score": 0.89,
                    "target_content_type": "business mistake story",
                    "estimated_performance": "high engagement expected",
                    "personalization_notes": "Adapted for user's business niche and authentic storytelling style"
                },
                {
                    "hook_id": 2,
                    "hook_text": "The productivity hack that 99% of entrepreneurs miss...",
                    "adaptation_strategy": "Exclusivity + high percentage + knowledge gap",
                    "based_on_competitors": ["competitor3"],
                    "psychological_triggers": [
                        "exclusivity",
                        "fear of missing out",
                        "authority"
                    ],
                    "effectiveness_score": 0.85,
                    "target_content_type": "productivity tip",
                    "estimated_performance": "viral potential in productivity niche"
                }
            ],
            "complete_scripts": [
                {
                    "hook_id": 1,
                    "script": {
                        "title": "The $50k Business Mistake",
                        "estimated_duration": 45,
                        "structure": "hook + story + lesson + CTA",
                        "hook": "I lost $50k because I ignored this one rule...",
                        "setup": "When I started my business, I thought I knew everything about scaling...",
                        "main_content": "But I made the classic mistake of hiring too fast without systems...",
                        "lesson": "Always build your systems before you build your team",
                        "call_to_action": "Save this if you're planning to hire soon!",
                        "visual_suggestions": "Split screen showing chaos vs organized systems"
                    },
                    "based_on_competitor": "competitor1",
                    "original_competitor_hook": "Why I fired my entire team and started over...",
                    "competitor_reel_id": "comp_reel_789",
                    "adaptation_notes": "Personalized with user's business experience and storytelling style"
                }
            ],
            "scripts_summary": [
                {
                    "script_id": 1,
                    "hook_id": 1,
                    "title": "The $50k Business Mistake",
                    "estimated_duration": 45,
                    "based_on_competitor": "competitor1",
                    "original_competitor_hook": "Why I fired my entire team...",
                    "competitor_reel_id": "comp_reel_789"
                }
            ],
            "analysis_summary": {
                "total_hooks_analyzed": 58,
                "primary_hooks": 8,
                "competitor_hooks": 50,
                "hooks_generated": 5,
                "scripts_created": 5,
                "unique_competitors_analyzed": 12,
                "analysis_quality_score": 0.87,
                "dominant_themes": [
                    "business growth",
                    "productivity",
                    "entrepreneurship"
                ],
                "recommended_content_frequency": "3-4 posts per week",
                "optimal_content_mix": {
                    "educational": 60,
                    "personal_stories": 30,
                    "behind_scenes": 10
                }
            }
        },

        // Legacy compatibility sections (extracted from analysis_data)
        "viral_ideas": [
            {
                "id": "hook_0",
                "idea_text": "I lost $50k because I ignored this one rule...",
                "explanation": "Personal vulnerability + specific loss amount + curiosity gap",
                "confidence_score": 0.89,
                "power_words": ["loss aversion", "curiosity", "social proof"]
            }
        ],
        "profile_analysis": {
            // Extracted from analysis_data.profile_analysis
        },
        "generated_hooks": [
            // Extracted from analysis_data.generated_hooks
        ],
        "individual_reel_analyses": [
            // Extracted from analysis_data.individual_reel_analyses
        ],
        "complete_scripts": [
            // Extracted from analysis_data.complete_scripts
        ],
        "scripts_summary": [
            // Extracted from analysis_data.scripts_summary
        ],
        "analysis_summary": {
            // Extracted from analysis_data.analysis_summary
        }
    }
}
```

**Response Field Details:**

| Field Section          | Purpose                             | Data Source                            | Count                     |
| :--------------------- | :---------------------------------- | :------------------------------------- | :------------------------ |
| `analysis`             | Process metadata and timing         | `viral_analysis_results` table         | 8 fields                  |
| `primary_profile`      | User's complete profile data        | `primary_profiles` table               | 13 fields                 |
| `analyzed_reels`       | Reels specifically used in analysis | `viral_analysis_reels` table           | Variable (5-15 typically) |
| `primary_user_reels`   | User's top content collection       | `content` table (filtered)             | 50 reels max              |
| `competitor_reels`     | Competitor content used             | `content` table (filtered)             | 100 reels max             |
| `competitor_profiles`  | Unique competitor profile data      | Extracted from reel joins              | Variable (3-12 typically) |
| `viral_scripts_table`  | Additional generated scripts        | `viral_scripts` table                  | Variable (0-10 typically) |
| `analysis_data`        | **Main AI insights (JSONB)**        | `viral_analysis_results.analysis_data` | Complete analysis         |
| `viral_ideas`          | Legacy hook format                  | Extracted from `analysis_data`         | 5 hooks typically         |
| _6 extracted sections_ | Easy frontend access                | Extracted from `analysis_data`         | Varies by section         |

### Error: 404 Not Found

Returned in the following scenarios:

```json
{
    "success": false,
    "detail": "Queue not found"
}
```

**Triggers:**

-   `queue_id` doesn't exist in `viral_ideas_queue` table
-   Analysis results don't exist for the given `queue_id`
-   Analysis is still in progress (status != 'completed')

### Error: 400 Bad Request

Returned for invalid request parameters:

```json
{
    "success": false,
    "detail": "Invalid queue ID format"
}
```

**Triggers:**

-   `queue_id` is not a valid UUID (Python) or ObjectId (MongoDB)
-   `queue_id` parameter is missing or empty

### Error: 500 Internal Server Error

Returned for server-side errors:

```json
{
    "success": false,
    "detail": "Failed to get analysis results"
}
```

**Common Triggers:**

-   Database connection failures
-   JSONB parsing errors in `analysis_data` field
-   CDN URL generation failures
-   Content transformation method failures
-   Memory/timeout issues with large result sets

**Error Handling Best Practices:**

```python
# Python Error Handling
try:
    # ... main logic
    return APIResponse(success=True, data=result)
except HTTPException:
    raise  # Re-raise HTTP exceptions as-is
except json.JSONDecodeError as e:
    logger.error(f"JSONB parsing error: {e}")
    raise HTTPException(status_code=500, detail="Invalid analysis data format")
except Exception as e:
    logger.error(f"Unexpected error in get_viral_analysis_results: {e}")
    raise HTTPException(status_code=500, detail="Failed to get analysis results")
```

```typescript
// Nest.js Error Handling
async getAnalysisResults(queueId: string): Promise<any> {
  try {
    // Validate ObjectId format first
    if (!Types.ObjectId.isValid(queueId)) {
      throw new BadRequestException('Invalid queue ID format');
    }

    // ... main logic

  } catch (error) {
    if (error instanceof NotFoundException || error instanceof BadRequestException) {
      throw error; // Re-throw known exceptions
    }

    // Log unexpected errors
    this.logger.error(`Unexpected error in getAnalysisResults: ${error.message}`, error.stack);
    throw new InternalServerErrorException('Failed to get analysis results');
  }
}
```

## Database Schema Details

### Core Tables (7 tables queried total)

#### 1. `viral_ideas_queue` (Entry Point)

-   **Purpose**: Tracks analysis job requests and status
-   **Key Fields**: `id`, `primary_username`, `status`, `content_strategy`
-   **Query**: Simple lookup to verify queue exists and get primary username

#### 2. `viral_analysis_results` (Primary Results)

-   **Purpose**: Stores analysis metadata and main JSONB insights
-   **Key Fields**: `analysis_data` (JSONB), `workflow_version`, timing fields
-   **Query**: Latest analysis run (`ORDER BY analysis_run DESC LIMIT 1`)
-   **Critical**: Contains the main `analysis_data` JSONB field with all AI insights

#### 3. `primary_profiles` (User Profile)

-   **Purpose**: Complete profile data for the analyzed user
-   **Fields**: 13 essential fields including metrics and image paths
-   **Query**: Single profile lookup by username with comprehensive field selection

#### 4. `viral_analysis_reels` (Analysis-Specific Reels)

-   **Purpose**: Tracks exactly which reels were used in this specific analysis
-   **Fields**: Performance at analysis time, transcript status, hook analysis
-   **Query**: All reels for analysis ID, ordered by type and rank

#### 5. `content` (Source Content)

-   **Purpose**: Full reel/post content data
-   **Query Strategy**:
    -   **Primary**: Top 50 by view_count DESC
    -   **Competitor**: Top 100 by outlier_score DESC
-   **JOIN**: Uses PostgreSQL foreign key to `primary_profiles` for enhanced data

#### 6. `viral_ideas_competitors` (Active Competitors)

-   **Purpose**: Tracks which competitors are active for this analysis
-   **Filter**: Only `is_active = TRUE` competitors included
-   **Query**: Simple list of competitor usernames for filtering

#### 7. `viral_scripts` (Generated Scripts)

-   **Purpose**: Additional generated scripts from AI pipeline
-   **Fields**: 10 comprehensive script fields including metadata
-   **Query**: All scripts for analysis ID, ordered by creation date DESC

### Database Performance Optimizations

**Indexes Used:**

```sql
-- JSONB performance indexes
CREATE INDEX idx_viral_analysis_results_analysis_data_gin
ON viral_analysis_results USING gin (analysis_data);

CREATE INDEX idx_analysis_data_hooks
ON viral_analysis_results USING gin ((analysis_data->'generated_hooks'));

-- Query performance indexes
CREATE INDEX idx_viral_analysis_results_workflow_version
ON viral_analysis_results (workflow_version);

CREATE INDEX idx_viral_queue_primary_username
ON viral_ideas_queue(primary_username);

CREATE INDEX idx_viral_competitors_active
ON viral_ideas_competitors(is_active) WHERE is_active = TRUE;
```

**Query Optimization Strategies:**

1. **Field Selection**: Only SELECT needed fields to reduce data transfer
2. **Result Limiting**: Caps at 50 primary reels, 100 competitor reels
3. **ORDER BY Optimization**: Uses indexed fields for sorting
4. **JOIN Strategy**: Single-query JOINs for content + profile data
5. **JSONB Indexing**: GIN indexes for fast JSONB field access

## Performance Considerations

### Response Size Management

-   **Typical Response Size**: 2-8MB for complete analysis results
-   **Large Analysis**: Can reach 15MB+ with extensive competitor data
-   **Optimization**: Frontend should implement progressive loading for large datasets

### Database Query Performance

-   **Total Queries**: 7 database queries executed sequentially
-   **Estimated Response Time**: 500ms - 2s depending on data size
-   **Bottlenecks**:
    -   JSONB parsing for large `analysis_data` fields
    -   Content transformation for 100+ reels
    -   CDN URL generation for profile images

### Memory and Scalability

```python
# Memory optimization techniques used
def optimize_memory_usage():
    # 1. Stream large results instead of loading all into memory
    # 2. Use select() to limit fields instead of SELECT *
    # 3. Transform content in batches rather than all at once
    # 4. Clean up intermediate variables after use
    pass
```

### Caching Strategies

```typescript
// Recommended caching for Nest.js
@Injectable()
export class ViralIdeasService {
    @Cacheable({ ttl: 300 }) // 5 minute cache
    async getAnalysisResults(queueId: string): Promise<any> {
        // Implementation...
    }

    @CacheEvict({ cacheKey: `analysis_results_${queueId}` })
    async invalidateAnalysisCache(queueId: string): Promise<void> {
        // Called when analysis is updated
    }
}
```

## Testing and Validation

### Unit Tests

```typescript
// viral-ideas.service.spec.ts
describe("ViralIdeasService", () => {
    describe("getAnalysisResults", () => {
        it("should return complete analysis results for valid queue", async () => {
            const mockQueueId = "507f1f77bcf86cd799439011";
            const result = await service.getAnalysisResults(mockQueueId);

            expect(result).toBeDefined();
            expect(result.analysis).toBeDefined();
            expect(result.analysis_data).toBeDefined();
            expect(result.primary_profile).toBeDefined();
            expect(Array.isArray(result.generated_hooks)).toBe(true);
        });

        it("should handle missing profile data gracefully", async () => {
            // Mock queue without profile data
            const result = await service.getAnalysisResults(mockQueueId);

            expect(result.primary_profile.username).toBe(mockUsername);
            expect(result.primary_profile.followers).toBe(0); // Default value
        });

        it("should throw NotFoundException for invalid queue", async () => {
            await expect(
                service.getAnalysisResults("invalid_id")
            ).rejects.toThrow(NotFoundException);
        });

        it("should parse JSONB analysis_data correctly", async () => {
            const result = await service.getAnalysisResults(mockQueueId);

            expect(typeof result.analysis_data).toBe("object");
            expect(result.analysis_data.workflow_version).toBeDefined();
            expect(Array.isArray(result.analysis_data.generated_hooks)).toBe(
                true
            );
        });

        it("should transform content using production method", async () => {
            const result = await service.getAnalysisResults(mockQueueId);

            expect(result.primary_user_reels[0]).toHaveProperty("profile_data");
            expect(result.competitor_reels[0]).toHaveProperty("profile_data");
        });
    });
});
```

### Integration Tests

```python
# test_viral_analysis_results.py
import pytest
from fastapi.testclient import TestClient

class TestViralAnalysisResults:
    def test_complete_analysis_flow(self, client: TestClient):
        # 1. Create analysis queue
        queue_response = client.post("/api/viral-ideas/queue", json={
            "session_id": "test_session",
            "primary_username": "test_user",
            "content_strategy": {
                "contentType": "Business Tips",
                "targetAudience": "Entrepreneurs",
                "goals": "Increase followers"
            },
            "selected_competitors": ["competitor1", "competitor2"]
        })
        queue_id = queue_response.json()["data"]["queue_id"]

        # 2. Mock analysis completion
        # ... complete analysis processing ...

        # 3. Test results retrieval
        response = client.get(f"/api/viral-analysis/{queue_id}/results")

        assert response.status_code == 200
        data = response.json()["data"]

        # Verify response structure
        assert "analysis" in data
        assert "primary_profile" in data
        assert "analysis_data" in data
        assert len(data["generated_hooks"]) > 0

    def test_error_handling(self, client: TestClient):
        # Test invalid queue ID
        response = client.get("/api/viral-analysis/invalid_id/results")
        assert response.status_code == 404

        # Test non-existent queue
        response = client.get("/api/viral-analysis/00000000-0000-0000-0000-000000000000/results")
        assert response.status_code == 404

    def test_large_response_handling(self, client: TestClient):
        # Test with queue that has many competitors and reels
        response = client.get(f"/api/viral-analysis/{large_queue_id}/results")

        assert response.status_code == 200
        data = response.json()["data"]

        # Verify limits are respected
        assert len(data["primary_user_reels"]) <= 50
        assert len(data["competitor_reels"]) <= 100
```

### Load Testing

```bash
# Performance test with Artillery
# artillery-load-test.yml
config:
  target: 'http://localhost:8000'
  phases:
    - duration: 60
      arrivalRate: 10
scenarios:
  - name: "Get analysis results"
    requests:
      - get:
          url: "/api/viral-analysis/{{ queue_id }}/results"
          headers:
            Authorization: "Bearer {{ auth_token }}"
```

## Edge Cases and Handling

### Common Edge Cases

1. **Empty Analysis Data**:

    ```python
    # Gracefully handle empty JSONB
    analysis_data = analysis_data_json or {}
    return APIResponse(success=True, data={
        "analysis_data": analysis_data,
        "generated_hooks": [],  # Empty array fallback
        "profile_analysis": {}  # Empty object fallback
    })
    ```

2. **Missing Profile Images**:

    ```typescript
    // Handle missing profile image paths
    profile_image_url: profileData?.profile_image_path
      ? await this.storageService.getPublicUrl('profile-images', profileData.profile_image_path)
      : (profileData?.profile_image_url || ''), // Fallback to existing URL or empty
    ```

3. **No Competitors Selected**:

    ```python
    # Handle analysis with no competitors
    competitor_usernames = [comp['competitor_username'] for comp in competitors_result.data or []]

    if not competitor_usernames:
        competitor_reels_result = None
        competitor_profiles_data = []
    ```

4. **Large JSONB Fields**:
    ```python
    # Handle large analysis_data with memory management
    if len(str(analysis_data_json)) > 10_000_000:  # 10MB limit
        logger.warning(f"Large analysis_data detected: {len(str(analysis_data_json))} bytes")
        # Consider pagination or streaming for very large responses
    ```

### Data Consistency Validation

```python
def validate_response_consistency(response_data):
    """Validate internal consistency of response data"""
    analysis = response_data['analysis']
    analysis_data = response_data['analysis_data']

    # Verify hook counts match
    generated_hooks_count = len(analysis_data.get('generated_hooks', []))
    extracted_hooks_count = len(response_data.get('generated_hooks', []))
    assert generated_hooks_count == extracted_hooks_count

    # Verify reel counts match analysis metadata
    actual_primary_count = len([r for r in response_data['analyzed_reels'] if r['reel_type'] == 'primary'])
    assert actual_primary_count == analysis['primary_reels_count']
```

## Implementation Details

### File Locations and Functions

-   **Primary File:** `backend_api.py` (lines 1752-1944)
-   **Function:** `get_viral_analysis_results(queue_id: str, api_instance: ViralSpotAPI)`
-   **Dependencies:** `ViralSpotAPI`, `SupabaseManager`, content transformation methods
-   **AI Pipeline Integration:** Uses results from `ViralIdeasAI` class in `viral_ideas_ai_pipeline.py`

### Database Queries Executed (in order)

1. **Queue Verification**: `viral_ideas_queue.select('primary_username').eq('id', queue_id)`
2. **Profile Data**: `primary_profiles.select(13_fields).eq('username', primary_username)`
3. **Analysis Results**: `viral_analysis_results.select(8_fields).eq('queue_id', queue_id).order('analysis_run', desc=True).limit(1)`
4. **Analyzed Reels**: `viral_analysis_reels.select(8_fields).eq('analysis_id', analysis_id).order('reel_type, rank_in_selection')`
5. **Primary Content**: `content.select(*).eq('username', primary_username).order('view_count', desc=True).limit(50)` (with JOIN)
6. **Active Competitors**: `viral_ideas_competitors.select('competitor_username').eq('queue_id', queue_id).eq('is_active', True)`
7. **Competitor Content**: `content.select(*).in_('username', competitor_usernames).order('outlier_score', desc=True).limit(100)` (with JOIN)
8. **Viral Scripts**: `viral_scripts.select(10_fields).eq('analysis_id', analysis_id).order('created_at', desc=True)`

### Core Data Transformations

**1. JSONB Analysis Data Parsing:**

```python
# Robust parsing with fallback
analysis_data_json = analysis_record.get('analysis_data', '{}')
if isinstance(analysis_data_json, str):
    try:
        analysis_data = json.loads(analysis_data_json)
    except (json.JSONDecodeError, TypeError):
        analysis_data = {}
else:
    analysis_data = analysis_data_json or {}
```

**2. Content Frontend Transformation:**

```python
# Uses production _transform_content_for_frontend method
if primary_reels_result.data:
    for i, reel in enumerate(primary_reels_result.data):
        primary_reels_result.data[i] = api_instance._transform_content_for_frontend(reel)
```

**3. CDN URL Generation:**

```python
# Dynamic Supabase Storage URL generation
profile['profile_image_url'] = api_instance.supabase.client.storage.from_('profile-images').get_public_url(profile['profile_image_path'])
```

**4. Legacy Hook Extraction:**

```python
# Backward compatibility transformation
'viral_ideas': [
    {
        'id': f"hook_{i}",
        'idea_text': hook.get('hook_text', ''),
        'explanation': hook.get('adaptation_strategy', ''),
        'confidence_score': hook.get('effectiveness_score', 0),
        'power_words': hook.get('psychological_triggers', [])
    }
    for i, hook in enumerate(analysis_data.get('generated_hooks', []))
] if analysis_data.get('generated_hooks') else []
```

## Security Considerations

### Input Validation

```typescript
// Nest.js validation pipeline
@Get(':queueId/results')
async getAnalysisResults(
  @Param('queueId', ParseUUIDPipe) queueId: string // Built-in UUID validation
) {
  // Additional validation
  if (!Types.ObjectId.isValid(queueId)) {
    throw new BadRequestException('Invalid queue ID format');
  }
}
```

### Data Access Control

```python
# Current implementation - add authentication as needed
@app.get("/api/viral-analysis/{queue_id}/results")
async def get_viral_analysis_results(
    queue_id: str,
    api_instance: ViralSpotAPI = Depends(get_api)
    # TODO: Add authentication dependency
    # current_user: User = Depends(get_current_user)
):
    # TODO: Verify user has access to this queue_id
    # if not user_has_access(current_user, queue_id):
    #     raise HTTPException(status_code=403, detail="Access denied")
```

### JSONB Field Security

```python
# Sanitize JSONB content before parsing
def sanitize_jsonb_field(jsonb_data):
    """Remove potentially harmful content from JSONB"""
    if isinstance(jsonb_data, str):
        # Remove any script tags or potentially harmful content
        sanitized = re.sub(r'<script.*?</script>', '', jsonb_data, flags=re.IGNORECASE | re.DOTALL)
        return sanitized
    return jsonb_data
```

## Usage Examples

### Frontend Integration

```typescript
// React/Next.js usage example
const fetchAnalysisResults = async (queueId: string) => {
    try {
        const response = await fetch(`/api/viral-analysis/${queueId}/results`);

        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }

        const result = await response.json();

        if (!result.success) {
            throw new Error(
                result.detail || "Failed to fetch analysis results"
            );
        }

        return result.data;
    } catch (error) {
        console.error("Error fetching analysis results:", error);
        throw error;
    }
};

// Usage in component
const AnalysisResultsPage = ({ queueId }: { queueId: string }) => {
    const [results, setResults] = useState(null);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(null);

    useEffect(() => {
        fetchAnalysisResults(queueId)
            .then(setResults)
            .catch(setError)
            .finally(() => setLoading(false));
    }, [queueId]);

    if (loading) return <LoadingSpinner />;
    if (error) return <ErrorMessage error={error} />;
    if (!results) return <NoDataMessage />;

    return (
        <div>
            <AnalysisOverview analysis={results.analysis} />
            <ProfileSummary profile={results.primary_profile} />
            <GeneratedHooks hooks={results.generated_hooks} />
            <CompetitorInsights
                profiles={results.competitor_profiles}
                reels={results.competitor_reels}
            />
            <ViralScripts scripts={results.complete_scripts} />
        </div>
    );
};
```

### cURL Testing Examples

```bash
# Test successful results retrieval
curl -X GET "http://localhost:8000/api/viral-analysis/507f1f77bcf86cd799439011/results" \
  -H "Content-Type: application/json" \
  | jq '.'

# Test error handling - invalid queue ID
curl -X GET "http://localhost:8000/api/viral-analysis/invalid-id/results" \
  -H "Content-Type: application/json" \
  -w "HTTP Status: %{http_code}\n"

# Test non-existent queue
curl -X GET "http://localhost:8000/api/viral-analysis/00000000-0000-0000-0000-000000000000/results" \
  -H "Content-Type: application/json" \
  -w "HTTP Status: %{http_code}\n"
```

### Response Processing Examples

```javascript
// Extract specific insights from response
const processAnalysisResults = (resultsData) => {
    const { analysis_data, generated_hooks, competitor_profiles } = resultsData;

    // Get top performing hooks
    const topHooks = generated_hooks
        .sort((a, b) => b.effectiveness_score - a.effectiveness_score)
        .slice(0, 3);

    // Analyze competitor performance
    const topCompetitors = competitor_profiles
        .sort((a, b) => b.followers - a.followers)
        .slice(0, 5);

    // Extract content themes
    const contentThemes =
        analysis_data.profile_analysis?.content_identity?.primary_themes || [];

    return {
        topHooks,
        topCompetitors,
        contentThemes,
        analysisQuality:
            analysis_data.analysis_summary?.analysis_quality_score || 0,
    };
};
```

## Related Endpoints

### Workflow Integration

1. **Create Analysis**: `POST /api/viral-ideas/queue` - Creates the analysis job
2. **Check Status**: `GET /api/viral-ideas/queue-status` - Monitor analysis progress
3. **Get Content**: `GET /api/viral-analysis/{queue_id}/content` - Fetch source content used
4. **Process Queue**: Background processors handle the AI analysis pipeline

### Data Dependencies

-   **Requires**: Completed analysis job (status = 'completed')
-   **Provides**: Complete results for frontend display
-   **Caching**: Consider 5-minute cache due to large response size
-   **Rate Limiting**: Recommend 60 requests/minute per user due to computational cost

---

**Note**: This endpoint represents the culmination of the viral analysis pipeline, aggregating insights from AI processing, content analysis, and competitor research into a single comprehensive response optimized for frontend consumption.
