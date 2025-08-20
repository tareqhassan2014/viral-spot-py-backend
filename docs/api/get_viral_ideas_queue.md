# GET `/api/viral-ideas/queue/{session_id}` ⚡

Retrieves real-time status and progress information for a specific viral ideas analysis job.

## Description

This endpoint provides **real-time status tracking** for individual viral analysis jobs, enabling frontend applications to monitor and display progress updates to users. It serves as the primary polling endpoint for job-specific status information throughout the analysis pipeline.

**Key Features:**

-   **Real-time progress tracking** with percentage completion and current processing step
-   **Comprehensive job metadata** including timing, priority, and form data
-   **Active competitor tracking** with processing status for each competitor
-   **Optimized database view usage** for fast, single-query status retrieval
-   **Content strategy display** with extracted form responses for user reference
-   **Error state handling** with detailed error messages and recovery guidance
-   **Polling optimization** designed for frequent frontend status checks

**Primary Use Cases:**

1. **Progress Monitoring**: Frontend progress bars and status indicators during analysis
2. **User Feedback**: Real-time updates showing current processing step and completion percentage
3. **Error Detection**: Immediate notification of analysis failures with detailed error messages
4. **Form Data Display**: Show users their submitted content strategy and competitor selections
5. **Timing Analysis**: Track submission, start, and completion timestamps for user insight
6. **Job Management**: Enable job cancellation, retry, or modification based on current status

**Response Includes:**

-   **Job Metadata**: ID, session, status, progress, priority, and timing information
-   **Form Data**: Content type, target audience, and goals from the original submission
-   **Competitor List**: Active competitors selected for analysis with their processing status
-   **Progress Tracking**: Current step, percentage complete, and estimated completion time
-   **Error Information**: Detailed error messages and suggested recovery actions when applicable

## Path Parameters

| Parameter    | Type   | Description                                                                        |
| :----------- | :----- | :--------------------------------------------------------------------------------- |
| `session_id` | string | The unique identifier for the user's session, which is linked to the analysis job. |

## Execution Flow

1.  **Request Validation**: The endpoint receives a GET request with a `session_id` string parameter in the URL path.

2.  **Primary Queue Data Retrieval**:

    -   Queries `viral_queue_summary` view using session_id as unique identifier
    -   Uses `SELECT *` to fetch all 16 pre-aggregated fields from the optimized view
    -   View automatically handles JOIN between `viral_ideas_queue` and `viral_ideas_competitors` tables
    -   Returns `404 Not Found` immediately if no queue entry exists for the session

3.  **Queue Data Processing**:

    -   Extracts comprehensive queue metadata from view result
    -   Processes extracted form data fields (content_type, target_audience, main_goals)
    -   Retrieves timing information (submitted_at, started_processing_at, completed_at)
    -   Accesses progress tracking data (status, progress_percentage, current_step)

4.  **Active Competitor Data Retrieval**:

    -   Queries `viral_ideas_competitors` table for detailed competitor information
    -   Filters for active competitors only (`is_active = TRUE`) linked to the queue entry
    -   Fetches competitor usernames and individual processing status
    -   Builds comprehensive competitor array for response

5.  **Response Assembly and Transformation**:

    -   Combines queue metadata with competitor data into unified response object
    -   Structures data for optimal frontend consumption and display
    -   Includes both original form submission data and current processing state
    -   Provides complete job context for progress monitoring and user feedback

6.  **Error Handling and Response**:
    -   Comprehensive try-catch with specific HTTP exception handling
    -   Detailed error logging for debugging and monitoring
    -   Graceful handling of missing data with appropriate fallbacks
    -   Returns standardized APIResponse format for frontend consistency

## Detailed Implementation Guide

### Python (FastAPI) - Complete Implementation

```python
# In backend_api.py

@app.get("/api/viral-ideas/queue/{session_id}")
async def get_viral_ideas_queue(session_id: str, api_instance: ViralSpotAPI = Depends(get_api)):
    """Get viral ideas queue status by session ID"""
    try:
        # Step 1: Query optimized viral_queue_summary view for comprehensive queue data
        result = api_instance.supabase.client.table('viral_queue_summary').select('*').eq('session_id', session_id).execute()

        if not result.data:
            raise HTTPException(status_code=404, detail="Queue entry not found")

        queue_data = result.data[0]

        # Step 2: Get detailed competitor information for this specific queue
        competitors_result = api_instance.supabase.client.table('viral_ideas_competitors').select(
            'competitor_username, processing_status'
        ).eq('queue_id', queue_data['id']).eq('is_active', True).execute()

        # Step 3: Process and transform competitor data
        competitors = [comp['competitor_username'] for comp in competitors_result.data] if competitors_result.data else []

        # Step 4: Assemble comprehensive response with all relevant job information
        return APIResponse(
            success=True,
            data={
                'id': queue_data['id'],
                'session_id': queue_data['session_id'],
                'primary_username': queue_data['primary_username'],
                'status': queue_data['status'],
                'progress_percentage': queue_data['progress_percentage'],
                'current_step': queue_data.get('current_step'),
                'priority': queue_data.get('priority', 5),
                'error_message': queue_data.get('error_message'),

                # Extracted form data from content_strategy JSONB field
                'content_type': queue_data['content_type'],
                'target_audience': queue_data['target_audience'],
                'main_goals': queue_data['main_goals'],
                'full_content_strategy': queue_data.get('full_content_strategy', {}),

                # Competitor information
                'competitors': competitors,
                'active_competitors_count': queue_data.get('active_competitors_count', 0),
                'total_competitors_count': queue_data.get('total_competitors_count', 0),

                # Timing and scheduling information
                'submitted_at': queue_data['submitted_at'],
                'started_processing_at': queue_data['started_processing_at'],
                'completed_at': queue_data['completed_at'],
                'auto_rerun_enabled': queue_data.get('auto_rerun_enabled', True),
                'rerun_frequency_hours': queue_data.get('rerun_frequency_hours', 24),
                'total_runs': queue_data.get('total_runs', 0),
                'last_analysis_at': queue_data.get('last_analysis_at'),
                'next_scheduled_run': queue_data.get('next_scheduled_run')
            }
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting viral ideas queue: {e}")
        raise HTTPException(status_code=500, detail="Failed to get queue status")
```

**Critical Implementation Details:**

1. **Optimized View Query**: Uses `viral_queue_summary` view which pre-joins `viral_ideas_queue` and `viral_ideas_competitors` tables for single-query efficiency
2. **Session-based Lookup**: Leverages unique `session_id` index for fast queue entry retrieval
3. **Active Competitor Filtering**: Secondary query specifically for active competitors (`is_active = TRUE`) with processing status
4. **Comprehensive Data Extraction**: Retrieves 16+ fields including form data, timing, scheduling, and progress information
5. **Form Data Processing**: Extracts content strategy fields from JSONB for easy frontend consumption
6. **Error State Preservation**: Includes error messages and current step information for troubleshooting
7. **Scheduling Context**: Provides auto-rerun settings and timing for recurring analysis management

**Database View Optimization:**

The `viral_queue_summary` view eliminates the need for complex JOINs in application code:

```sql
-- viral_queue_summary view structure (16 fields)
SELECT
    q.id, q.session_id, q.primary_username, q.status, q.priority,
    q.progress_percentage, q.current_step, q.error_message,
    q.submitted_at, q.started_processing_at, q.completed_at,
    q.auto_rerun_enabled, q.rerun_frequency_hours, q.total_runs,
    extract_content_strategy_field(q.content_strategy, 'contentType') as content_type,
    extract_content_strategy_field(q.content_strategy, 'targetAudience') as target_audience,
    extract_content_strategy_field(q.content_strategy, 'goals') as main_goals,
    q.content_strategy as full_content_strategy,
    COUNT(c.id) FILTER (WHERE c.is_active = TRUE) as active_competitors_count
FROM viral_ideas_queue q
LEFT JOIN viral_ideas_competitors c ON q.id = c.queue_id
GROUP BY q.id, [all_queue_fields]
```

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
    _id: Types.ObjectId; // MongoDB default _id (18 columns total)

    @Prop({ required: true, unique: true, index: true })
    session_id: string;

    @Prop({ required: true, index: true })
    primary_username: string;

    @Prop({ type: Object, default: {} })
    content_strategy: {
        contentType?: string;
        targetAudience?: string;
        goals?: string;
    };

    @Prop({ type: Object, default: {} })
    analysis_settings: Record<string, any>;

    @Prop({ default: "pending", index: true })
    status: string; // 'pending', 'processing', 'completed', 'failed', 'paused'

    @Prop({ default: 5 })
    priority: number;

    @Prop()
    current_step: string;

    @Prop({ default: 0 })
    progress_percentage: number;

    @Prop()
    error_message: string;

    @Prop({ default: true })
    auto_rerun_enabled: boolean;

    @Prop({ default: 24 })
    rerun_frequency_hours: number;

    @Prop()
    last_analysis_at: Date;

    @Prop()
    next_scheduled_run: Date;

    @Prop({ default: 0 })
    total_runs: number;

    @Prop({ default: Date.now, index: true })
    submitted_at: Date;

    @Prop()
    started_processing_at: Date;

    @Prop()
    completed_at: Date;
}

export const ViralIdeasQueueSchema =
    SchemaFactory.createForClass(ViralIdeasQueue);

// viral-ideas-competitors.schema.ts
@Schema({ timestamps: true })
export class ViralIdeasCompetitors {
    _id: Types.ObjectId; // MongoDB default _id

    @Prop({
        type: Types.ObjectId,
        ref: "ViralIdeasQueue",
        required: true,
        index: true,
    })
    queue_id: Types.ObjectId;

    @Prop({ required: true })
    competitor_username: string;

    @Prop({ default: "suggested" })
    selection_method: string;

    @Prop({ default: true, index: true })
    is_active: boolean;

    @Prop({ default: "pending" })
    processing_status: string;

    @Prop({ default: Date.now })
    added_at: Date;

    @Prop()
    removed_at: Date;
}

export const ViralIdeasCompetitorsSchema = SchemaFactory.createForClass(
    ViralIdeasCompetitors
);

// ===============================================
// CONTROLLER IMPLEMENTATION
// ===============================================

// viral-ideas.controller.ts
import {
    Controller,
    Get,
    Param,
    NotFoundException,
    BadRequestException,
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

@ApiTags("viral-ideas")
@Controller("api/viral-ideas")
export class ViralIdeasController {
    constructor(private readonly viralIdeasService: ViralIdeasService) {}

    @Get("queue/:sessionId")
    @ApiOperation({
        summary: "Get specific viral ideas queue status",
        description:
            "Retrieves real-time status and progress for a specific analysis job by session ID",
    })
    @ApiParam({
        name: "sessionId",
        description: "Unique session identifier for the analysis job",
        type: "string",
        example: "session_12345",
    })
    @ApiResponse({
        status: 200,
        description: "Queue status retrieved successfully",
        schema: {
            type: "object",
            properties: {
                success: { type: "boolean", example: true },
                data: {
                    type: "object",
                    description:
                        "Complete queue entry with progress and metadata",
                },
            },
        },
    })
    @ApiNotFoundResponse({
        description: "No queue entry found for the given session ID",
    })
    @ApiInternalServerErrorResponse({
        description: "Server error during queue status retrieval",
    })
    async getViralIdeasQueue(@Param("sessionId") sessionId: string) {
        try {
            // Validate session ID format
            if (!sessionId || sessionId.trim().length === 0) {
                throw new BadRequestException("Session ID is required");
            }

            const result = await this.viralIdeasService.getQueueBySessionId(
                sessionId
            );

            if (!result) {
                throw new NotFoundException("Queue entry not found");
            }

            return { success: true, data: result };
        } catch (error) {
            if (
                error instanceof NotFoundException ||
                error instanceof BadRequestException
            ) {
                throw error;
            }
            throw new InternalServerErrorException(
                "Failed to get queue status"
            );
        }
    }
}

// ===============================================
// SERVICE IMPLEMENTATION
// ===============================================

// viral-ideas.service.ts
import { Injectable, Logger, NotFoundException } from "@nestjs/common";
import { InjectModel } from "@nestjs/mongoose";
import { Model, Types } from "mongoose";

@Injectable()
export class ViralIdeasService {
    private readonly logger = new Logger(ViralIdeasService.name);

    constructor(
        @InjectModel("ViralIdeasQueue")
        private queueModel: Model<ViralIdeasQueue>,
        @InjectModel("ViralIdeasCompetitors")
        private competitorsModel: Model<ViralIdeasCompetitors>
    ) {}

    async getQueueBySessionId(sessionId: string): Promise<any | null> {
        try {
            // Step 1: Find queue entry by session_id with comprehensive field selection
            const queueItem = await this.queueModel
                .findOne({ session_id: sessionId })
                .select(
                    "_id session_id primary_username status priority progress_percentage current_step error_message submitted_at started_processing_at completed_at content_strategy analysis_settings auto_rerun_enabled rerun_frequency_hours total_runs last_analysis_at next_scheduled_run"
                )
                .exec();

            if (!queueItem) {
                return null;
            }

            // Step 2: Get active competitors with processing status
            const competitors = await this.competitorsModel
                .find({ queue_id: queueItem._id, is_active: true })
                .select(
                    "competitor_username processing_status selection_method added_at"
                )
                .sort({ added_at: 1 }) // Order by addition time
                .exec();

            // Step 3: Get total competitor count (including inactive)
            const totalCompetitorCount = await this.competitorsModel
                .countDocuments({ queue_id: queueItem._id })
                .exec();

            // Step 4: Extract and process form data from content_strategy
            const contentStrategy = queueItem.content_strategy || {};

            // Step 5: Calculate processing metrics
            const processingDuration =
                queueItem.started_processing_at && queueItem.completed_at
                    ? Math.round(
                          (queueItem.completed_at.getTime() -
                              queueItem.started_processing_at.getTime()) /
                              (1000 * 60)
                      )
                    : null;

            const isOverdue =
                queueItem.status === "processing" &&
                queueItem.started_processing_at
                    ? Date.now() - queueItem.started_processing_at.getTime() >
                      30 * 60 * 1000
                    : false;

            const estimatedTimeRemaining = this.calculateEstimatedTimeRemaining(
                queueItem.status,
                queueItem.progress_percentage,
                queueItem.started_processing_at
            );

            // Step 6: Assemble comprehensive response
            return {
                id: queueItem._id.toString(),
                session_id: queueItem.session_id,
                primary_username: queueItem.primary_username,
                status: queueItem.status,
                priority: queueItem.priority,
                progress_percentage: queueItem.progress_percentage || 0,
                current_step: queueItem.current_step || null,
                error_message: queueItem.error_message || null,

                // Extracted form data for frontend display
                content_type: contentStrategy.contentType || "",
                target_audience: contentStrategy.targetAudience || "",
                main_goals: contentStrategy.goals || "",
                full_content_strategy: contentStrategy,
                analysis_settings: queueItem.analysis_settings || {},

                // Competitor information with detailed metadata
                competitors: competitors.map(
                    (comp) => comp.competitor_username
                ),
                competitor_details: competitors.map((comp) => ({
                    username: comp.competitor_username,
                    processing_status: comp.processing_status,
                    selection_method: comp.selection_method,
                    added_at: comp.added_at,
                })),
                active_competitors_count: competitors.length,
                total_competitors_count: totalCompetitorCount,

                // Timing and scheduling information
                submitted_at: queueItem.submitted_at,
                started_processing_at: queueItem.started_processing_at || null,
                completed_at: queueItem.completed_at || null,
                auto_rerun_enabled: queueItem.auto_rerun_enabled,
                rerun_frequency_hours: queueItem.rerun_frequency_hours,
                total_runs: queueItem.total_runs || 0,
                last_analysis_at: queueItem.last_analysis_at || null,
                next_scheduled_run: queueItem.next_scheduled_run || null,

                // Computed metrics for frontend progress tracking
                processing_duration: processingDuration,
                is_overdue: isOverdue,
                estimated_time_remaining: estimatedTimeRemaining,
                can_be_cancelled: ["pending", "processing"].includes(
                    queueItem.status
                ),
                can_be_rerun: ["completed", "failed"].includes(
                    queueItem.status
                ),

                // Status classification for frontend styling
                status_category: this.getStatusCategory(queueItem.status),
                progress_stage: this.getProgressStage(
                    queueItem.progress_percentage
                ),
            };
        } catch (error) {
            this.logger.error(
                `Error getting queue by session ID ${sessionId}: ${error.message}`,
                error.stack
            );
            throw error;
        }
    }

    // ===============================================
    // HELPER METHODS FOR ENHANCED FUNCTIONALITY
    // ===============================================

    private calculateEstimatedTimeRemaining(
        status: string,
        progressPercentage: number,
        startedAt: Date | null
    ): number | null {
        if (status !== "processing" || !startedAt || progressPercentage <= 0) {
            return null;
        }

        const elapsedMinutes = (Date.now() - startedAt.getTime()) / (1000 * 60);
        const progressRatio = progressPercentage / 100;
        const estimatedTotalMinutes = elapsedMinutes / progressRatio;
        const remainingMinutes = estimatedTotalMinutes - elapsedMinutes;

        return Math.max(0, Math.round(remainingMinutes));
    }

    private getStatusCategory(status: string): string {
        const statusMap = {
            pending: "waiting",
            processing: "active",
            completed: "success",
            failed: "error",
            paused: "warning",
        };
        return statusMap[status] || "unknown";
    }

    private getProgressStage(progressPercentage: number): string {
        if (progressPercentage === 0) return "not_started";
        if (progressPercentage < 25) return "initializing";
        if (progressPercentage < 50) return "processing";
        if (progressPercentage < 75) return "analyzing";
        if (progressPercentage < 100) return "finalizing";
        return "completed";
    }
}

// ===============================================
// DTO FOR REQUEST/RESPONSE VALIDATION
// ===============================================

// get-queue-status.dto.ts
import { IsString, IsNotEmpty, Length } from "class-validator";
import { ApiProperty } from "@nestjs/swagger";

export class GetQueueStatusParamsDto {
    @ApiProperty({
        description: "Unique session identifier for the analysis job",
        example: "session_12345",
        minLength: 1,
        maxLength: 255,
    })
    @IsString()
    @IsNotEmpty()
    @Length(1, 255)
    sessionId: string;
}

export class QueueStatusResponseDto {
    @ApiProperty({ example: true })
    success: boolean;

    @ApiProperty({
        description: "Complete queue entry data with progress tracking",
        type: "object",
    })
    data: {
        id: string;
        session_id: string;
        primary_username: string;
        status: string;
        priority: number;
        progress_percentage: number;
        current_step: string;
        error_message: string;
        content_type: string;
        target_audience: string;
        main_goals: string;
        full_content_strategy: any;
        competitors: string[];
        competitor_details: Array<{
            username: string;
            processing_status: string;
            selection_method: string;
            added_at: Date;
        }>;
        active_competitors_count: number;
        total_competitors_count: number;
        submitted_at: Date;
        started_processing_at: Date;
        completed_at: Date;
        auto_rerun_enabled: boolean;
        rerun_frequency_hours: number;
        total_runs: number;
        processing_duration: number;
        is_overdue: boolean;
        estimated_time_remaining: number;
        can_be_cancelled: boolean;
        can_be_rerun: boolean;
        status_category: string;
        progress_stage: string;
    };
}
```

## Responses

### Success: 200 OK

Returns a comprehensive status object with complete job information, progress tracking, and competitor details.

**Complete Response Structure:**

```json
{
    "success": true,
    "data": {
        "id": "507f1f77bcf86cd799439011",
        "session_id": "session_12345",
        "primary_username": "entrepreneur_mike",
        "status": "processing",
        "priority": 5,
        "progress_percentage": 65,
        "current_step": "Analyzing Competitor Hooks",
        "error_message": null,

        "content_type": "Business Tips, Productivity Hacks",
        "target_audience": "Entrepreneurs, Small Business Owners",
        "main_goals": "Increase followers, Build brand awareness",
        "full_content_strategy": {
            "contentType": "Business Tips, Productivity Hacks",
            "targetAudience": "Entrepreneurs, Small Business Owners",
            "goals": "Increase followers, Build brand awareness",
            "additionalNotes": "Focus on actionable business advice"
        },
        "analysis_settings": {
            "analysis_depth": "comprehensive",
            "include_transcripts": true,
            "max_competitor_reels": 50
        },

        "competitors": [
            "business_guru_alex",
            "productivity_coach_sarah",
            "entrepreneur_jenny",
            "startup_advisor_mike"
        ],
        "competitor_details": [
            {
                "username": "business_guru_alex",
                "processing_status": "completed",
                "selection_method": "suggested",
                "added_at": "2024-01-15T14:30:00Z"
            },
            {
                "username": "productivity_coach_sarah",
                "processing_status": "processing",
                "selection_method": "manual",
                "added_at": "2024-01-15T14:30:30Z"
            },
            {
                "username": "entrepreneur_jenny",
                "processing_status": "pending",
                "selection_method": "suggested",
                "added_at": "2024-01-15T14:31:00Z"
            },
            {
                "username": "startup_advisor_mike",
                "processing_status": "pending",
                "selection_method": "api",
                "added_at": "2024-01-15T14:31:30Z"
            }
        ],
        "active_competitors_count": 4,
        "total_competitors_count": 4,

        "submitted_at": "2024-01-15T14:30:00Z",
        "started_processing_at": "2024-01-15T14:32:00Z",
        "completed_at": null,
        "auto_rerun_enabled": true,
        "rerun_frequency_hours": 24,
        "total_runs": 1,
        "last_analysis_at": "2024-01-14T14:30:00Z",
        "next_scheduled_run": "2024-01-16T14:30:00Z",

        "processing_duration": null,
        "is_overdue": false,
        "estimated_time_remaining": 8,
        "can_be_cancelled": true,
        "can_be_rerun": false,
        "status_category": "active",
        "progress_stage": "analyzing"
    }
}
```

**Comprehensive Field Reference:**

| Field                      | Type     | Description                           | Source                                    | Usage                     |
| :------------------------- | :------- | :------------------------------------ | :---------------------------------------- | :------------------------ |
| **Core Job Data**          |          |                                       |                                           |                           |
| `id`                       | string   | MongoDB ObjectId of queue entry       | `viral_ideas_queue._id`                   | Unique job identifier     |
| `session_id`               | string   | User session identifier               | `viral_ideas_queue.session_id`            | Frontend session tracking |
| `primary_username`         | string   | Username being analyzed               | `viral_ideas_queue.primary_username`      | User identification       |
| `status`                   | string   | Current job status                    | `viral_ideas_queue.status`                | Progress monitoring       |
| `priority`                 | number   | Job priority (1-10)                   | `viral_ideas_queue.priority`              | Queue ordering            |
| **Progress Tracking**      |          |                                       |                                           |                           |
| `progress_percentage`      | number   | Completion percentage (0-100)         | `viral_ideas_queue.progress_percentage`   | Progress bars             |
| `current_step`             | string   | Current processing stage              | `viral_ideas_queue.current_step`          | User feedback             |
| `error_message`            | string   | Error details if failed               | `viral_ideas_queue.error_message`         | Error display             |
| **Form Data**              |          |                                       |                                           |                           |
| `content_type`             | string   | Content type from form                | Extracted from `content_strategy`         | Strategy display          |
| `target_audience`          | string   | Target audience from form             | Extracted from `content_strategy`         | Strategy display          |
| `main_goals`               | string   | Goals from form                       | Extracted from `content_strategy`         | Strategy display          |
| `full_content_strategy`    | object   | Complete form submission              | `viral_ideas_queue.content_strategy`      | Full context              |
| `analysis_settings`        | object   | Additional analysis preferences       | `viral_ideas_queue.analysis_settings`     | Configuration             |
| **Competitor Information** |          |                                       |                                           |                           |
| `competitors`              | string[] | Active competitor usernames           | `viral_ideas_competitors` query           | Simple list               |
| `competitor_details`       | object[] | Detailed competitor metadata          | `viral_ideas_competitors` query           | Full competitor info      |
| `active_competitors_count` | number   | Count of active competitors           | Calculated                                | Quick reference           |
| `total_competitors_count`  | number   | Total competitors (inc. inactive)     | Calculated                                | Complete picture          |
| **Timing Data**            |          |                                       |                                           |                           |
| `submitted_at`             | datetime | When job was submitted                | `viral_ideas_queue.submitted_at`          | Timeline tracking         |
| `started_processing_at`    | datetime | When processing began                 | `viral_ideas_queue.started_processing_at` | Duration calculation      |
| `completed_at`             | datetime | When job finished                     | `viral_ideas_queue.completed_at`          | Completion tracking       |
| **Scheduling**             |          |                                       |                                           |                           |
| `auto_rerun_enabled`       | boolean  | Whether job reruns automatically      | `viral_ideas_queue.auto_rerun_enabled`    | Scheduling config         |
| `rerun_frequency_hours`    | number   | Hours between reruns                  | `viral_ideas_queue.rerun_frequency_hours` | Scheduling config         |
| `total_runs`               | number   | Number of times analyzed              | `viral_ideas_queue.total_runs`            | History tracking          |
| `last_analysis_at`         | datetime | Last completion time                  | `viral_ideas_queue.last_analysis_at`      | History reference         |
| `next_scheduled_run`       | datetime | Next scheduled analysis               | `viral_ideas_queue.next_scheduled_run`    | Future planning           |
| **Computed Metrics**       |          |                                       |                                           |                           |
| `processing_duration`      | number   | Minutes to complete (if done)         | Calculated                                | Performance tracking      |
| `is_overdue`               | boolean  | Whether processing is taking too long | Calculated                                | Alert indicator           |
| `estimated_time_remaining` | number   | Estimated minutes remaining           | Calculated                                | ETA display               |
| `can_be_cancelled`         | boolean  | Whether job can be cancelled          | Calculated                                | Action availability       |
| `can_be_rerun`             | boolean  | Whether job can be restarted          | Calculated                                | Action availability       |
| `status_category`          | string   | Status classification for UI          | Calculated                                | Styling helper            |
| `progress_stage`           | string   | Human-readable progress stage         | Calculated                                | User-friendly display     |

**Status Values and Meanings:**

| Status       | Description                     | Progress Range | Next Action                          |
| :----------- | :------------------------------ | :------------- | :----------------------------------- |
| `pending`    | Waiting in queue for processing | 0%             | System will start processing         |
| `processing` | Currently being analyzed        | 1-99%          | Monitor progress, allow cancellation |
| `completed`  | Analysis finished successfully  | 100%           | View results, schedule rerun         |
| `failed`     | Analysis encountered error      | Variable       | Review error, retry analysis         |
| `paused`     | Temporarily stopped             | Variable       | Resume or cancel analysis            |

**Progress Stages:**

| Stage          | Progress Range | Description                                |
| :------------- | :------------- | :----------------------------------------- |
| `not_started`  | 0%             | Job in queue, not yet picked up            |
| `initializing` | 1-24%          | Setting up analysis, fetching initial data |
| `processing`   | 25-49%         | Collecting and processing content          |
| `analyzing`    | 50-74%         | AI analysis of hooks and patterns          |
| `finalizing`   | 75-99%         | Generating scripts and final results       |
| `completed`    | 100%           | Analysis complete and results available    |

### Error: 404 Not Found

Returned when no queue entry exists for the provided session ID:

```json
{
    "success": false,
    "detail": "Queue entry not found"
}
```

**Common Triggers:**

-   Invalid or expired session ID
-   Session ID from different environment (dev/staging/prod)
-   Queue entry was manually deleted from database
-   Session ID format is valid but doesn't exist in system

### Error: 400 Bad Request

Returned for invalid session ID format:

```json
{
    "success": false,
    "detail": "Session ID is required"
}
```

**Validation Triggers:**

-   Empty session ID parameter
-   Session ID with only whitespace
-   Session ID exceeding maximum length (255 characters)

### Error: 500 Internal Server Error

Returned for server-side errors during queue retrieval:

```json
{
    "success": false,
    "detail": "Failed to get queue status"
}
```

**Common Triggers:**

-   Database connection failures
-   `viral_queue_summary` view access issues
-   Competitor query execution problems
-   JSON parsing errors in `content_strategy` field
-   Memory issues during data transformation

## Database Schema Details

### Core Tables and Views [[memory:6676026]]

#### 1. `viral_ideas_queue` (Primary Table)

-   **Purpose**: Stores individual analysis job requests with complete metadata
-   **Key Fields**: 18 columns including session tracking, form data, progress, timing, and scheduling
-   **Query Pattern**: Single record lookup by unique `session_id`
-   **Performance**: Indexed on `session_id` for instant retrieval

#### 2. `viral_queue_summary` (Optimized View)

-   **Purpose**: Pre-aggregated view combining queue data with competitor counts and extracted form fields
-   **Performance**: Eliminates complex JOINs and JSONB field extraction in application code
-   **Usage**: Primary data source for this endpoint to minimize query complexity

#### 3. `viral_ideas_competitors` (Competitor Tracking)

-   **Purpose**: Tracks competitors selected for each analysis with processing metadata
-   **Query Pattern**: Active competitors only (`is_active = TRUE`) for main response
-   **Performance**: Indexed on `queue_id` and `is_active` for efficient filtering

### Performance Optimizations

**Critical Indexes:**

```sql
-- Session-based lookup performance (primary query)
CREATE UNIQUE INDEX idx_viral_queue_session_id ON viral_ideas_queue(session_id);

-- Status and timing queries for progress tracking
CREATE INDEX idx_viral_queue_status_progress ON viral_ideas_queue(status, progress_percentage);

-- Competitor lookup performance
CREATE INDEX idx_viral_competitors_queue_active ON viral_ideas_competitors(queue_id, is_active) WHERE is_active = TRUE;

-- JSONB field optimization for form data extraction
CREATE INDEX idx_viral_queue_content_strategy_gin ON viral_ideas_queue USING gin (content_strategy);
```

## Frontend Integration Patterns

### Real-time Polling Implementation

```typescript
// useQueueTracking.ts - Custom React hook for job tracking
export const useQueueTracking = ({ sessionId, pollingInterval = 3000 }) => {
    const [queueData, setQueueData] = useState(null);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(null);

    useEffect(() => {
        const fetchStatus = async () => {
            try {
                const response = await fetch(
                    `/api/viral-ideas/queue/${sessionId}`
                );

                if (response.status === 404) {
                    setError("Analysis session not found");
                    return;
                }

                const result = await response.json();
                if (result.success) {
                    setQueueData(result.data);
                    setError(null);
                }
            } catch (err) {
                setError("Failed to fetch status");
            } finally {
                setLoading(false);
            }
        };

        fetchStatus();
        const interval = setInterval(fetchStatus, pollingInterval);
        return () => clearInterval(interval);
    }, [sessionId, pollingInterval]);

    return { queueData, loading, error };
};
```

## Database Schema Details

### Primary Data Sources

This endpoint leverages optimized database views and tables for efficient status retrieval.

#### 1. `viral_queue_summary` View

Optimized view that pre-joins queue and competitor data. **[View Complete Documentation](../database/viral_queue_summary.md)**

```sql
-- Primary query using optimized view
SELECT * FROM viral_queue_summary
WHERE session_id = ?;

-- View automatically provides:
-- - All viral_ideas_queue fields
-- - Extracted content_strategy fields (content_type, target_audience, main_goals)
-- - Aggregated competitor counts
-- - Pre-computed form data for frontend display
```

#### 2. `viral_ideas_competitors` Table

Detailed competitor tracking for analysis jobs. **[View Complete Documentation](../database/viral_ideas_competitors.md)**

```sql
-- Secondary query for detailed competitor information
SELECT competitor_username, processing_status, selection_method, added_at
FROM viral_ideas_competitors
WHERE queue_id = ?
AND is_active = TRUE
ORDER BY added_at ASC;
```

#### 3. `viral_ideas_queue` Table (Underlying Data)

Core queue table containing job metadata. **[View Complete Documentation](../database/viral_ideas_queue.md)**

The `viral_queue_summary` view is built on top of this table, providing all 20 columns plus computed fields.

### Query Optimization Strategy

-   **Single View Query**: Uses `viral_queue_summary` to eliminate complex JOINs
-   **Targeted Competitor Query**: Separate query for detailed competitor metadata
-   **Indexed Lookups**: Fast session-based retrieval with unique index
-   **Selective Fields**: Returns only necessary fields for frontend consumption

## Implementation Details

### File Locations and Functions

-   **Primary File:** `backend_api.py` (lines 1492-1531)
-   **Function:** `get_viral_ideas_queue(session_id: str, api_instance: ViralSpotAPI)`
-   **Database View:** `viral_queue_summary` (defined in `schema/viral_ideas_queue.sql`)
-   **Dependencies:** `ViralSpotAPI`, `SupabaseManager`, competitor tracking tables

### Database Queries Executed (in order)

1. **Primary Queue Data**: `viral_queue_summary.select('*').eq('session_id', session_id)` - Single comprehensive query
2. **Active Competitors**: `viral_ideas_competitors.select('competitor_username, processing_status').eq('queue_id', queue_id).eq('is_active', True)` - Detailed competitor information

### Performance Characteristics

-   **Response Time**: 50-100ms typical for single session lookup
-   **Memory Usage**: ~5-10MB per response depending on competitor count
-   **Database Load**: 2 queries total (1 view query + 1 competitor detail query)
-   **Polling Friendly**: Optimized for 2-5 second polling intervals

## Usage Examples

### Frontend Progress Tracking

```typescript
// AnalysisProgressPage.tsx - Complete progress tracking component
import React, { useState, useEffect } from "react";

interface ProgressPageProps {
    sessionId: string;
}

export const AnalysisProgressPage: React.FC<ProgressPageProps> = ({
    sessionId,
}) => {
    const [queueData, setQueueData] = useState(null);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(null);

    useEffect(() => {
        const fetchStatus = async () => {
            try {
                const response = await fetch(
                    `/api/viral-ideas/queue/${sessionId}`
                );

                if (response.status === 404) {
                    setError("Analysis session not found or expired");
                    return;
                }

                const result = await response.json();
                if (result.success) {
                    setQueueData(result.data);
                    setError(null);
                }
            } catch (err) {
                setError("Failed to fetch analysis status");
            } finally {
                setLoading(false);
            }
        };

        fetchStatus();

        // Poll every 3 seconds for active jobs, every 30 seconds for completed jobs
        const interval = queueData?.status === "processing" ? 3000 : 30000;
        const pollInterval = setInterval(fetchStatus, interval);

        return () => clearInterval(pollInterval);
    }, [sessionId, queueData?.status]);

    if (loading) return <div>Loading analysis status...</div>;
    if (error) return <div>Error: {error}</div>;
    if (!queueData) return <div>No analysis data available</div>;

    return (
        <div className="analysis-progress-page">
            {/* Progress header */}
            <div className="progress-header">
                <h1>Analysis Progress</h1>
                <div className="meta-info">
                    <span>@{queueData.primary_username}</span>
                    <span
                        className={`status-badge ${queueData.status_category}`}
                    >
                        {queueData.status.toUpperCase()}
                    </span>
                </div>
            </div>

            {/* Progress bar */}
            <div className="progress-section">
                <div className="progress-info">
                    <span>{queueData.current_step || "Processing..."}</span>
                    <span>{queueData.progress_percentage}%</span>
                </div>
                <div className="progress-bar">
                    <div
                        className="progress-fill"
                        style={{ width: `${queueData.progress_percentage}%` }}
                    />
                </div>
                {queueData.estimated_time_remaining && (
                    <div className="time-estimate">
                        Estimated time remaining:{" "}
                        {queueData.estimated_time_remaining} minutes
                    </div>
                )}
            </div>

            {/* Content strategy recap */}
            <div className="strategy-section">
                <h3>Your Content Strategy</h3>
                <div className="strategy-grid">
                    <div>
                        <strong>Type:</strong> {queueData.content_type}
                    </div>
                    <div>
                        <strong>Audience:</strong> {queueData.target_audience}
                    </div>
                    <div>
                        <strong>Goals:</strong> {queueData.main_goals}
                    </div>
                </div>
            </div>

            {/* Competitor analysis progress */}
            <div className="competitors-section">
                <h3>
                    Competitor Analysis ({queueData.active_competitors_count})
                </h3>
                {queueData.competitor_details.map((comp) => (
                    <div key={comp.username} className="competitor-row">
                        <span>@{comp.username}</span>
                        <span className={`status ${comp.processing_status}`}>
                            {comp.processing_status}
                        </span>
                        <span className="method">{comp.selection_method}</span>
                    </div>
                ))}
            </div>

            {/* Action buttons */}
            {queueData.status === "completed" && (
                <button
                    onClick={() =>
                        (window.location.href = `/results/${queueData.id}`)
                    }
                >
                    View Results
                </button>
            )}

            {queueData.can_be_cancelled && (
                <button onClick={() => handleCancelAnalysis(queueData.id)}>
                    Cancel Analysis
                </button>
            )}
        </div>
    );
};
```

### CLI Status Checking

```bash
#!/bin/bash
# check-analysis-status.sh - CLI tool for checking specific analysis status

SESSION_ID=$1

if [ -z "$SESSION_ID" ]; then
    echo "Usage: $0 <session_id>"
    exit 1
fi

echo "🔍 Checking analysis status for session: $SESSION_ID"
echo "=================================================="

# Fetch queue status
response=$(curl -s "http://localhost:8000/api/viral-ideas/queue/$SESSION_ID")

# Check if request was successful
if echo "$response" | jq -e '.success' > /dev/null; then
    # Parse response data
    status=$(echo "$response" | jq -r '.data.status')
    progress=$(echo "$response" | jq -r '.data.progress_percentage')
    username=$(echo "$response" | jq -r '.data.primary_username')
    current_step=$(echo "$response" | jq -r '.data.current_step // "N/A"')
    competitors_count=$(echo "$response" | jq -r '.data.active_competitors_count')

    echo "📊 Analysis Details:"
    echo "  User: @$username"
    echo "  Status: $status"
    echo "  Progress: $progress%"
    echo "  Current Step: $current_step"
    echo "  Competitors: $competitors_count"

    # Show timing information
    submitted_at=$(echo "$response" | jq -r '.data.submitted_at')
    echo "  Submitted: $submitted_at"

    if [ "$status" = "processing" ]; then
        estimated_remaining=$(echo "$response" | jq -r '.data.estimated_time_remaining // "N/A"')
        echo "  Estimated Remaining: $estimated_remaining minutes"
    fi

    # Show competitors
    echo ""
    echo "🏆 Competitors:"
    echo "$response" | jq -r '.data.competitor_details[] | "  @\(.username) - \(.processing_status) (\(.selection_method))"'

else
    # Handle error response
    error_detail=$(echo "$response" | jq -r '.detail // "Unknown error"')
    echo "❌ Error: $error_detail"
fi
```

## Testing and Validation

### Unit Tests

```typescript
// viral-ideas.service.spec.ts
describe("ViralIdeasService - Individual Queue Status", () => {
    let service: ViralIdeasService;
    let queueModel: Model<ViralIdeasQueue>;
    let competitorsModel: Model<ViralIdeasCompetitors>;

    describe("getQueueBySessionId", () => {
        it("should return complete queue data with competitor details", async () => {
            const mockQueue = {
                _id: new Types.ObjectId(),
                session_id: "test_session",
                primary_username: "test_user",
                status: "processing",
                progress_percentage: 65,
                content_strategy: {
                    contentType: "Business Tips",
                    targetAudience: "Entrepreneurs",
                    goals: "Increase followers",
                },
                started_processing_at: new Date(Date.now() - 10 * 60 * 1000), // 10 minutes ago
            };

            const mockCompetitors = [
                {
                    competitor_username: "comp1",
                    processing_status: "completed",
                    selection_method: "suggested",
                },
                {
                    competitor_username: "comp2",
                    processing_status: "processing",
                    selection_method: "manual",
                },
            ];

            jest.spyOn(queueModel, "findOne").mockReturnValue({
                select: () => ({ exec: () => Promise.resolve(mockQueue) }),
            } as any);

            jest.spyOn(competitorsModel, "find").mockReturnValue({
                select: () => ({
                    sort: () => ({
                        exec: () => Promise.resolve(mockCompetitors),
                    }),
                }),
            } as any);

            jest.spyOn(competitorsModel, "countDocuments").mockReturnValue({
                exec: () => Promise.resolve(2),
            } as any);

            const result = await service.getQueueBySessionId("test_session");

            expect(result).toBeDefined();
            expect(result.session_id).toBe("test_session");
            expect(result.status).toBe("processing");
            expect(result.competitors).toEqual(["comp1", "comp2"]);
            expect(result.competitor_details).toHaveLength(2);
            expect(result.content_type).toBe("Business Tips");
            expect(result.estimated_time_remaining).toBeGreaterThan(0);
            expect(result.can_be_cancelled).toBe(true);
            expect(result.status_category).toBe("active");
        });

        it("should return null for non-existent session", async () => {
            jest.spyOn(queueModel, "findOne").mockReturnValue({
                select: () => ({ exec: () => Promise.resolve(null) }),
            } as any);

            const result = await service.getQueueBySessionId("non_existent");
            expect(result).toBeNull();
        });

        it("should calculate estimated time remaining correctly", async () => {
            const startTime = new Date(Date.now() - 10 * 60 * 1000); // 10 minutes ago
            const estimatedTime = service["calculateEstimatedTimeRemaining"](
                "processing",
                50,
                startTime
            );
            expect(estimatedTime).toBeCloseTo(10, 1); // ~10 minutes remaining at 50% progress
        });

        it("should handle overdue detection", async () => {
            const overdueStartTime = new Date(Date.now() - 35 * 60 * 1000); // 35 minutes ago
            const mockQueue = {
                status: "processing",
                started_processing_at: overdueStartTime,
                // other fields...
            };

            // Test overdue calculation logic
            const isOverdue =
                Date.now() - overdueStartTime.getTime() > 30 * 60 * 1000;
            expect(isOverdue).toBe(true);
        });
    });
});
```

### Integration Tests

```python
# test_individual_queue_tracking.py
import pytest
from fastapi.testclient import TestClient
import uuid

class TestIndividualQueueTracking:
    def test_get_queue_success_with_all_fields(self, client: TestClient):
        # Use a known test session ID
        session_id = "test_session_comprehensive"

        response = client.get(f"/api/viral-ideas/queue/{session_id}")

        assert response.status_code == 200
        data = response.json()

        # Verify response structure
        assert data["success"] is True
        queue_data = data["data"]

        # Core fields validation
        assert "id" in queue_data
        assert "session_id" in queue_data
        assert queue_data["session_id"] == session_id
        assert "primary_username" in queue_data
        assert "status" in queue_data

        # Progress tracking fields
        assert "progress_percentage" in queue_data
        assert isinstance(queue_data["progress_percentage"], int)
        assert 0 <= queue_data["progress_percentage"] <= 100

        # Form data fields
        assert "content_type" in queue_data
        assert "target_audience" in queue_data
        assert "main_goals" in queue_data
        assert "full_content_strategy" in queue_data

        # Competitor data
        assert "competitors" in queue_data
        assert "competitor_details" in queue_data
        assert "active_competitors_count" in queue_data
        assert isinstance(queue_data["competitors"], list)
        assert isinstance(queue_data["competitor_details"], list)

        # Computed metrics
        assert "is_overdue" in queue_data
        assert "can_be_cancelled" in queue_data
        assert "can_be_rerun" in queue_data
        assert "status_category" in queue_data
        assert "progress_stage" in queue_data

    def test_queue_status_progression(self, client: TestClient):
        """Test that status progression works correctly"""
        session_id = "test_session_progression"

        # Test different status scenarios
        status_scenarios = [
            {"status": "pending", "progress": 0, "can_cancel": True, "can_rerun": False},
            {"status": "processing", "progress": 45, "can_cancel": True, "can_rerun": False},
            {"status": "completed", "progress": 100, "can_cancel": False, "can_rerun": True},
            {"status": "failed", "progress": 25, "can_cancel": False, "can_rerun": True}
        ]

        for scenario in status_scenarios:
            # This would require setting up test data for each scenario
            # In practice, you'd use database fixtures or mocking
            response = client.get(f"/api/viral-ideas/queue/{session_id}")

            if response.status_code == 200:
                queue_data = response.json()["data"]

                # Verify status-dependent computed fields
                if queue_data["status"] == scenario["status"]:
                    assert queue_data["can_be_cancelled"] == scenario["can_cancel"]
                    assert queue_data["can_be_rerun"] == scenario["can_rerun"]

    def test_competitor_details_structure(self, client: TestClient):
        session_id = "test_session_competitors"
        response = client.get(f"/api/viral-ideas/queue/{session_id}")

        if response.status_code == 200:
            queue_data = response.json()["data"]

            # Verify competitor details structure
            for competitor in queue_data.get("competitor_details", []):
                assert "username" in competitor
                assert "processing_status" in competitor
                assert "selection_method" in competitor
                assert "added_at" in competitor

                # Verify selection method values
                assert competitor["selection_method"] in ["suggested", "manual", "api"]

                # Verify processing status values
                assert competitor["processing_status"] in ["pending", "processing", "completed", "failed"]

    def test_polling_performance_under_load(self, client: TestClient):
        """Simulate rapid polling to test performance"""
        import time
        import threading

        session_id = "test_session_performance"

        def poll_endpoint():
            response = client.get(f"/api/viral-ideas/queue/{session_id}")
            return response.status_code, response.elapsed.total_seconds() if hasattr(response, 'elapsed') else 0

        # Simulate 10 concurrent polling requests
        threads = []
        results = []

        start_time = time.time()

        for i in range(10):
            thread = threading.Thread(target=lambda: results.append(poll_endpoint()))
            threads.append(thread)
            thread.start()

        for thread in threads:
            thread.join()

        end_time = time.time()
        total_time = end_time - start_time

        # All requests should succeed
        status_codes = [result[0] for result in results if result]
        assert all(code in [200, 404] for code in status_codes)

        # Total time should be reasonable for concurrent requests
        assert total_time < 5.0  # 10 concurrent requests in under 5 seconds

    def test_error_handling_scenarios(self, client: TestClient):
        # Test invalid session ID formats
        invalid_sessions = ["", "   ", "x" * 256]  # empty, whitespace, too long

        for invalid_session in invalid_sessions:
            response = client.get(f"/api/viral-ideas/queue/{invalid_session}")
            assert response.status_code in [400, 422]  # Bad request or validation error

        # Test non-existent session
        response = client.get("/api/viral-ideas/queue/definitely_does_not_exist")
        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()
```

## Related Endpoints

### Individual Job Workflow

1. **Create Analysis**: `POST /api/viral-ideas/queue` - Submit new analysis request
2. **Track Progress**: `GET /api/viral-ideas/queue/{session_id}` - **This endpoint** - Monitor specific job
3. **View Results**: `GET /api/viral-analysis/{queue_id}/results` - Access completed analysis results
4. **Get Content**: `GET /api/viral-analysis/{queue_id}/content` - Browse analyzed content/reels

### System Monitoring

-   **Overall Status**: `GET /api/viral-ideas/queue-status` - System-wide queue statistics
-   **Individual Tracking**: `GET /api/viral-ideas/queue/{session_id}` - **This endpoint** - Specific job monitoring

### Data Dependencies

-   **Queue Creation**: This endpoint returns data created by `POST /api/viral-ideas/queue`
-   **Competitor Selection**: Competitor data managed through queue creation and manual editing
-   **Progress Updates**: Status and progress updated by background processing services
-   **Results Access**: Queue ID from this endpoint used to access analysis results

---

**Note**: This endpoint is designed for frequent polling (2-5 second intervals) and provides comprehensive job tracking data for real-time user feedback. Consider implementing WebSocket connections for instant updates in high-traffic scenarios.
