# GET `/api/viral-ideas/queue-status` ⚡

Gets comprehensive statistics and monitoring data for the viral ideas processing queue.

## Description

This endpoint serves as the primary **system monitoring and dashboard endpoint** for the viral ideas analysis pipeline. It provides real-time insights into queue health, processing performance, and recent activity patterns.

**Key Features:**

-   **Real-time queue statistics** across all status categories
-   **Recent activity monitoring** with the latest 10 submissions
-   **Performance metrics** including progress tracking and timing
-   **Content strategy insights** from form data aggregation
-   **Competitor analysis overview** with active competitor counts
-   **System health indicators** for operational monitoring

The endpoint provides essential data for:

1. **Administrative Dashboards**: System operators monitoring queue performance
2. **User Status Displays**: Frontend components showing overall system activity
3. **Performance Analytics**: Understanding processing bottlenecks and patterns
4. **Capacity Planning**: Monitoring workload trends and resource utilization
5. **Error Detection**: Quickly identifying failed analyses and system issues

**Response Sections:**

-   **Statistics**: Comprehensive counts across all status categories (pending, processing, completed, failed, total)
-   **Recent Items**: Latest 10 queue entries with full metadata, form data, and competitor counts
-   **Operational Metrics**: Processing timing, progress tracking, and system health indicators

## Execution Flow

1.  **Request Processing**: The endpoint receives a GET request with no parameters required.

2.  **Queue Statistics Collection** (4 parallel COUNT queries):

    -   **Pending Count**: `COUNT` query on `viral_ideas_queue` WHERE `status = 'pending'`
    -   **Processing Count**: `COUNT` query on `viral_ideas_queue` WHERE `status = 'processing'`
    -   **Completed Count**: `COUNT` query on `viral_ideas_queue` WHERE `status = 'completed'`
    -   **Failed Count**: `COUNT` query on `viral_ideas_queue` WHERE `status = 'failed'`
    -   **Total Calculation**: Sum of all status counts for system overview

3.  **Recent Activity Retrieval**:

    -   Queries `viral_queue_summary` view for enhanced data aggregation
    -   Fetches 8 essential fields: `id`, `primary_username`, `status`, `progress_percentage`, `current_step`, `submitted_at`, `content_type`, `target_audience`, `active_competitors_count`
    -   Orders by `submitted_at DESC` for chronological recent activity
    -   Limits to 10 most recent entries for performance optimization

4.  **Data Aggregation and Response Assembly**:

    -   Combines statistics object with totals and individual status counts
    -   Includes recent items array with processed form data and timing information
    -   Structures response for optimal dashboard consumption and frontend display

5.  **Error Handling and Logging**:
    -   Comprehensive try-catch with detailed error logging
    -   Returns `500 Internal Server Error` for any system failures
    -   Maintains system monitoring capabilities even during partial failures

## Detailed Implementation Guide

### Python (FastAPI) - Complete Implementation

```python
# In backend_api.py

@app.get("/api/viral-ideas/queue-status")
async def get_viral_ideas_queue_status(api_instance: ViralSpotAPI = Depends(get_api)):
    """Get overall viral ideas queue status and statistics"""
    try:
        # Step 1: Get queue statistics with parallel COUNT queries for performance
        pending_result = api_instance.supabase.client.table('viral_ideas_queue').select(
            'id', count='exact'
        ).eq('status', 'pending').execute()

        processing_result = api_instance.supabase.client.table('viral_ideas_queue').select(
            'id', count='exact'
        ).eq('status', 'processing').execute()

        completed_result = api_instance.supabase.client.table('viral_ideas_queue').select(
            'id', count='exact'
        ).eq('status', 'completed').execute()

        failed_result = api_instance.supabase.client.table('viral_ideas_queue').select(
            'id', count='exact'
        ).eq('status', 'failed').execute()

        # Step 2: Get recent items from optimized viral_queue_summary view
        recent_result = api_instance.supabase.client.table('viral_queue_summary').select(
            'id, primary_username, status, progress_percentage, current_step, submitted_at, '
            'content_type, target_audience, active_competitors_count'
        ).order('submitted_at', desc=True).limit(10).execute()

        # Step 3: Assemble comprehensive response with statistics and recent activity
        return APIResponse(
            success=True,
            data={
                'statistics': {
                    'pending': pending_result.count,
                    'processing': processing_result.count,
                    'completed': completed_result.count,
                    'failed': failed_result.count,
                    'total': (pending_result.count + processing_result.count +
                             completed_result.count + failed_result.count)
                },
                'recent_items': recent_result.data if recent_result.data else []
            }
        )

    except Exception as e:
        logger.error(f"Error getting viral ideas queue status: {e}")
        raise HTTPException(status_code=500, detail="Failed to get queue status")
```

**Critical Implementation Details:**

1. **Parallel COUNT Queries**: Executes 4 separate COUNT queries for different status values to build comprehensive statistics
2. **Optimized View Usage**: Leverages `viral_queue_summary` view for recent items, which pre-joins and aggregates data from multiple tables
3. **Essential Field Selection**: Fetches 8 key fields for recent items to balance completeness with performance
4. **Chronological Ordering**: Uses `submitted_at DESC` to show most recent activity first
5. **Performance Limiting**: Caps recent items at 10 for consistent response times
6. **Total Calculation**: Computes total queue size by summing all status counts
7. **Robust Error Handling**: Comprehensive exception handling with detailed logging

### Nest.js (Mongoose) - Complete Implementation

**Schema Definitions:**

```typescript
// viral-ideas-queue.schema.ts
import { Prop, Schema, SchemaFactory } from "@nestjs/mongoose";
import { Document, Types } from "mongoose";

@Schema({ timestamps: true })
export class ViralIdeasQueue {
    _id: Types.ObjectId; // MongoDB default _id (18 columns total)

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

    @Prop({ default: 0 })
    total_runs: number;

    @Prop({ default: Date.now })
    submitted_at: Date;

    @Prop()
    started_processing_at: Date;

    @Prop()
    completed_at: Date;
}

export const ViralIdeasQueueSchema =
    SchemaFactory.createForClass(ViralIdeasQueue);
```

**Controller Implementation:**

```typescript
// viral-ideas.controller.ts
import { Controller, Get, InternalServerErrorException } from "@nestjs/common";
import { ApiTags, ApiOperation, ApiResponse } from "@nestjs/swagger";

@ApiTags("viral-ideas")
@Controller("api/viral-ideas")
export class ViralIdeasController {
    constructor(private readonly viralIdeasService: ViralIdeasService) {}

    @Get("queue-status")
    @ApiOperation({
        summary: "Get viral ideas queue status",
        description:
            "Retrieves comprehensive queue statistics and recent activity for system monitoring",
    })
    @ApiResponse({
        status: 200,
        description: "Queue status retrieved successfully",
    })
    async getQueueStatus() {
        try {
            const result = await this.viralIdeasService.getQueueStatus();
            return { success: true, data: result };
        } catch (error) {
            throw new InternalServerErrorException(
                "Failed to get queue status"
            );
        }
    }
}
```

**Service Implementation:**

```typescript
// viral-ideas.service.ts
import { Injectable, Logger } from "@nestjs/common";
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

    async getQueueStatus(): Promise<any> {
        try {
            // Step 1: Get statistics using parallel countDocuments for performance
            const [pending, processing, completed, failed] = await Promise.all([
                this.queueModel.countDocuments({ status: "pending" }).exec(),
                this.queueModel.countDocuments({ status: "processing" }).exec(),
                this.queueModel.countDocuments({ status: "completed" }).exec(),
                this.queueModel.countDocuments({ status: "failed" }).exec(),
            ]);

            const total = pending + processing + completed + failed;

            // Step 2: Get recent items with comprehensive field selection
            const recentItemsRaw = await this.queueModel
                .find()
                .select(
                    "_id session_id primary_username status priority progress_percentage current_step error_message submitted_at started_processing_at completed_at content_strategy auto_rerun_enabled total_runs"
                )
                .sort({ submitted_at: -1 })
                .limit(10)
                .exec();

            // Step 3: Enhance recent items with competitor counts and computed metrics
            const recentItems = await Promise.all(
                recentItemsRaw.map(async (item) => {
                    // Get active competitor count for this queue item
                    const competitorCount = await this.competitorsModel
                        .countDocuments({ queue_id: item._id, is_active: true })
                        .exec();

                    // Extract and process form data from content_strategy
                    const contentStrategy = item.content_strategy || {};

                    // Calculate processing duration if completed
                    const processingDuration =
                        item.started_processing_at && item.completed_at
                            ? Math.round(
                                  (item.completed_at.getTime() -
                                      item.started_processing_at.getTime()) /
                                      (1000 * 60)
                              )
                            : null;

                    // Check if processing job is overdue (> 30 minutes)
                    const isOverdue =
                        item.status === "processing" &&
                        item.started_processing_at
                            ? Date.now() -
                                  item.started_processing_at.getTime() >
                              30 * 60 * 1000
                            : false;

                    return {
                        id: item._id.toString(),
                        session_id: item.session_id,
                        primary_username: item.primary_username,
                        status: item.status,
                        priority: item.priority,
                        progress_percentage: item.progress_percentage || 0,
                        current_step: item.current_step || null,
                        error_message: item.error_message || null,
                        submitted_at: item.submitted_at,
                        started_processing_at:
                            item.started_processing_at || null,
                        completed_at: item.completed_at || null,

                        // Extracted form data for dashboard insights
                        content_type: contentStrategy.contentType || "",
                        target_audience: contentStrategy.targetAudience || "",
                        main_goals: contentStrategy.goals || "",

                        // Operational metadata
                        active_competitors_count: competitorCount,
                        auto_rerun_enabled: item.auto_rerun_enabled,
                        total_runs: item.total_runs || 0,
                        processing_duration: processingDuration,
                        is_overdue: isOverdue,
                    };
                })
            );

            // Step 4: Calculate enhanced system metrics
            const systemMetrics = this.calculateSystemHealth(
                pending,
                processing,
                completed,
                failed,
                recentItems
            );

            return {
                statistics: {
                    pending,
                    processing,
                    completed,
                    failed,
                    total,
                    ...systemMetrics,
                },
                recent_items: recentItems,
            };
        } catch (error) {
            this.logger.error(
                `Error getting queue status: ${error.message}`,
                error.stack
            );
            throw error;
        }
    }

    private calculateSystemHealth(
        pending: number,
        processing: number,
        completed: number,
        failed: number,
        recentItems: any[]
    ): any {
        // Calculate success rate from recent activity
        const recentCompleted = recentItems.filter(
            (item) => item.status === "completed"
        ).length;
        const recentFailed = recentItems.filter(
            (item) => item.status === "failed"
        ).length;
        const recentTotal = recentCompleted + recentFailed;
        const successRate =
            recentTotal > 0 ? (recentCompleted / recentTotal) * 100 : 100;

        // Calculate average processing time
        const completedWithDuration = recentItems.filter(
            (item) => item.processing_duration !== null
        );
        const avgProcessingTime =
            completedWithDuration.length > 0
                ? completedWithDuration.reduce(
                      (sum, item) => sum + item.processing_duration,
                      0
                  ) / completedWithDuration.length
                : null;

        // System health indicators
        const total = pending + processing + completed + failed;
        const activeJobs = pending + processing;
        const capacityUsage =
            total > 0 ? (activeJobs / Math.max(total, 100)) * 100 : 0;
        const overdueJobs = recentItems.filter(
            (item) => item.is_overdue
        ).length;

        return {
            queue_capacity_usage: Math.round(capacityUsage * 100) / 100,
            processing_efficiency: Math.round(successRate * 100) / 100,
            average_processing_time_minutes: avgProcessingTime
                ? Math.round(avgProcessingTime * 100) / 100
                : null,
            overdue_jobs: overdueJobs,
            last_activity:
                recentItems.length > 0 ? recentItems[0].submitted_at : null,
            system_health_score: this.calculateHealthScore(
                successRate,
                avgProcessingTime,
                overdueJobs
            ),
        };
    }

    private calculateHealthScore(
        successRate: number,
        avgTime: number | null,
        overdueJobs: number
    ): number {
        let score = 100;
        if (successRate < 95) score -= 95 - successRate;
        if (avgTime && avgTime > 20) score -= Math.min(20, avgTime - 20);
        score -= overdueJobs * 10;
        return Math.max(0, Math.round(score));
    }
}
```

## Responses

### Success: 200 OK

Returns a comprehensive dashboard object with detailed queue statistics, recent activity, and system health metrics.

**Complete Response Structure:**

```json
{
    "success": true,
    "data": {
        "statistics": {
            "pending": 5,
            "processing": 2,
            "completed": 150,
            "failed": 1,
            "total": 158,
            "queue_capacity_usage": 4.43,
            "processing_efficiency": 98.68,
            "average_processing_time_minutes": 14.5,
            "overdue_jobs": 0,
            "last_activity": "2024-01-15T14:30:00Z",
            "system_health_score": 95
        },
        "recent_items": [
            {
                "id": "507f1f77bcf86cd799439011",
                "session_id": "session_12345",
                "primary_username": "entrepreneur_mike",
                "status": "completed",
                "priority": 5,
                "progress_percentage": 100,
                "current_step": "Analysis Complete",
                "error_message": null,
                "submitted_at": "2024-01-15T14:30:00Z",
                "started_processing_at": "2024-01-15T14:32:00Z",
                "completed_at": "2024-01-15T14:47:00Z",
                "content_type": "Business Tips, Productivity Hacks",
                "target_audience": "Entrepreneurs, Small Business Owners",
                "main_goals": "Increase followers, Build brand awareness",
                "active_competitors_count": 4,
                "auto_rerun_enabled": true,
                "total_runs": 1,
                "processing_duration": 15,
                "is_overdue": false
            },
            {
                "id": "507f1f77bcf86cd799439012",
                "session_id": "session_67890",
                "primary_username": "fitness_coach_sarah",
                "status": "processing",
                "priority": 3,
                "progress_percentage": 75,
                "current_step": "Generating Viral Scripts",
                "error_message": null,
                "submitted_at": "2024-01-15T14:25:00Z",
                "started_processing_at": "2024-01-15T14:27:00Z",
                "completed_at": null,
                "content_type": "Fitness Tips, Workout Routines",
                "target_audience": "Fitness Enthusiasts, Beginners",
                "main_goals": "Build community, Share expertise",
                "active_competitors_count": 6,
                "auto_rerun_enabled": true,
                "total_runs": 0,
                "processing_duration": null,
                "is_overdue": false
            },
            {
                "id": "507f1f77bcf86cd799439013",
                "session_id": "session_54321",
                "primary_username": "tech_reviewer_alex",
                "status": "pending",
                "priority": 7,
                "progress_percentage": 0,
                "current_step": null,
                "error_message": null,
                "submitted_at": "2024-01-15T14:20:00Z",
                "started_processing_at": null,
                "completed_at": null,
                "content_type": "Tech Reviews, Product Comparisons",
                "target_audience": "Tech Enthusiasts, Consumers",
                "main_goals": "Educate audience, Drive affiliate sales",
                "active_competitors_count": 3,
                "auto_rerun_enabled": false,
                "total_runs": 0,
                "processing_duration": null,
                "is_overdue": false
            },
            {
                "id": "507f1f77bcf86cd799439014",
                "session_id": "session_98765",
                "primary_username": "food_blogger_jenny",
                "status": "failed",
                "priority": 5,
                "progress_percentage": 25,
                "current_step": "Fetching Competitor Data",
                "error_message": "Failed to fetch reels: Instagram rate limit exceeded",
                "submitted_at": "2024-01-15T13:45:00Z",
                "started_processing_at": "2024-01-15T13:47:00Z",
                "completed_at": null,
                "content_type": "Food Recipes, Cooking Tips",
                "target_audience": "Home Cooks, Food Lovers",
                "main_goals": "Share recipes, Build cooking community",
                "active_competitors_count": 5,
                "auto_rerun_enabled": true,
                "total_runs": 2,
                "processing_duration": null,
                "is_overdue": false
            }
        ]
    }
}
```

**Response Field Details:**

| Field Section                                  | Description                            | Source                     | Purpose                  |
| :--------------------------------------------- | :------------------------------------- | :------------------------- | :----------------------- |
| **statistics.pending**                         | Jobs waiting to be processed           | COUNT query                | Workload monitoring      |
| **statistics.processing**                      | Jobs currently being processed         | COUNT query                | Active capacity tracking |
| **statistics.completed**                       | Successfully finished jobs             | COUNT query                | Success metrics          |
| **statistics.failed**                          | Jobs that encountered errors           | COUNT query                | Error rate monitoring    |
| **statistics.total**                           | Sum of all jobs in system              | Calculated                 | Overall system scale     |
| **statistics.queue_capacity_usage**            | Percentage of active vs total jobs     | Calculated                 | Resource utilization     |
| **statistics.processing_efficiency**           | Success rate from recent activity      | Calculated                 | System reliability       |
| **statistics.average_processing_time_minutes** | Mean duration for completed jobs       | Calculated                 | Performance benchmarking |
| **statistics.overdue_jobs**                    | Jobs processing longer than 30 minutes | Calculated                 | System health alert      |
| **statistics.last_activity**                   | Timestamp of most recent submission    | Recent items               | Activity monitoring      |
| **statistics.system_health_score**             | Overall system health (0-100)          | Calculated                 | Quick health assessment  |
| **recent_items[]**                             | Latest 10 submissions with metadata    | `viral_queue_summary` view | Activity timeline        |

**Enhanced Metrics Explanation:**

-   **Queue Capacity Usage**: `(pending + processing) / max(total, 100) * 100` - Shows how much of the system capacity is actively in use
-   **Processing Efficiency**: `(recent_completed / (recent_completed + recent_failed)) * 100` - Success rate from the last 10 processed jobs
-   **System Health Score**: Composite score factoring in success rate, processing speed, and overdue jobs
-   **Overdue Detection**: Jobs in 'processing' status for more than 30 minutes are flagged as potentially stuck

### Error: 500 Internal Server Error

Returned for server-side errors during queue status retrieval:

```json
{
    "success": false,
    "detail": "Failed to get queue status"
}
```

**Common Triggers:**

-   Database connection failures or timeouts
-   COUNT query performance issues on large tables
-   `viral_queue_summary` view access problems
-   Memory exhaustion during competitor count aggregation
-   Network issues with database cluster

**Error Handling Best Practices:**

```python
# Python Error Handling
try:
    # Execute all COUNT queries and recent items fetch
    return APIResponse(success=True, data=result)
except Exception as e:
    logger.error(f"Error getting viral ideas queue status: {e}")
    raise HTTPException(status_code=500, detail="Failed to get queue status")
```

## Database Schema Details

### Core Tables and Views

#### 1. `viral_ideas_queue` (Primary Table) [[memory:6676026]]

-   **Purpose**: Main queue table tracking all analysis job requests
-   **Key Fields**: 18 columns including status, progress, form data, scheduling
-   **Queries**: 4 separate COUNT queries for status statistics
-   **Performance**: Indexed on `status` field for efficient counting

#### 2. `viral_queue_summary` (Optimized View)

-   **Purpose**: Pre-aggregated view combining queue and competitor data
-   **Performance**: Eliminates need for JOINs in endpoint logic
-   **Fields**: 16 essential fields including extracted form data and competitor counts

```sql
-- Key indexes for performance
CREATE INDEX idx_viral_queue_status ON viral_ideas_queue(status);
CREATE INDEX idx_viral_queue_submitted_at ON viral_ideas_queue(submitted_at DESC);
CREATE INDEX idx_viral_competitors_queue_active ON viral_ideas_competitors(queue_id, is_active) WHERE is_active = TRUE;
```

## Performance Considerations

### Response Time Optimization

-   **Total Queries**: 5 database queries (4 COUNT + 1 SELECT)
-   **Estimated Response Time**: 200-500ms typical, up to 1s for large queues
-   **Memory Usage**: ~10MB for typical response with 10 recent items
-   **Caching Recommended**: 30-60 second TTL for monitoring use cases

### Monitoring Integration

```typescript
// Health check integration
@Injectable()
export class SystemHealthService {
    async checkQueueHealth(): Promise<boolean> {
        const status = await this.viralIdeasService.getQueueStatus();
        const { overdue_jobs, processing_efficiency, system_health_score } =
            status.statistics;

        // Alert conditions
        if (
            overdue_jobs > 3 ||
            processing_efficiency < 85 ||
            system_health_score < 70
        ) {
            await this.alertService.sendAlert("Queue health degraded");
            return false;
        }
        return true;
    }
}
```

## Implementation Details

### File Locations and Functions

-   **Primary File:** `backend_api.py` (lines 1717-1749)
-   **Function:** `get_viral_ideas_queue_status(api_instance: ViralSpotAPI)`
-   **Database View:** `viral_queue_summary` (defined in `schema/viral_ideas_queue.sql`)
-   **Dependencies:** `ViralSpotAPI`, `SupabaseManager`, database views

### Database Queries Executed (in order)

1. **Pending Count**: `viral_ideas_queue.select('id', count='exact').eq('status', 'pending')`
2. **Processing Count**: `viral_ideas_queue.select('id', count='exact').eq('status', 'processing')`
3. **Completed Count**: `viral_ideas_queue.select('id', count='exact').eq('status', 'completed')`
4. **Failed Count**: `viral_ideas_queue.select('id', count='exact').eq('status', 'failed')`
5. **Recent Items**: `viral_queue_summary.select(8_fields).order('submitted_at', desc=True).limit(10)`

## Usage Examples

### Dashboard Integration

```typescript
// Real-time queue dashboard component
const QueueStatusDashboard: React.FC = () => {
    const [queueData, setQueueData] = useState(null);

    useEffect(() => {
        const fetchStatus = async () => {
            const response = await fetch("/api/viral-ideas/queue-status");
            const result = await response.json();
            if (result.success) setQueueData(result.data);
        };

        fetchStatus();
        const interval = setInterval(fetchStatus, 30000); // Poll every 30 seconds
        return () => clearInterval(interval);
    }, []);

    return (
        <div className="queue-dashboard">
            <StatCard
                title="Queue Health"
                value={`${queueData?.statistics.system_health_score}/100`}
            />
            <StatCard
                title="Processing"
                value={queueData?.statistics.processing}
            />
            <StatCard title="Pending" value={queueData?.statistics.pending} />

            {queueData?.statistics.overdue_jobs > 0 && (
                <Alert type="warning">
                    {queueData.statistics.overdue_jobs} jobs are overdue
                </Alert>
            )}
        </div>
    );
};
```

### CLI Monitoring

```bash
# Simple queue status check
curl -s http://localhost:8000/api/viral-ideas/queue-status | jq '.data.statistics'

# Monitor for overdue jobs
curl -s http://localhost:8000/api/viral-ideas/queue-status | jq '.data.statistics.overdue_jobs'

# Get recent failed jobs
curl -s http://localhost:8000/api/viral-ideas/queue-status | jq '.data.recent_items[] | select(.status == "failed")'
```

## Testing Examples

```typescript
// Unit test for queue status
describe("QueueStatus", () => {
    it("should return comprehensive statistics", async () => {
        const result = await service.getQueueStatus();

        expect(result.statistics).toMatchObject({
            pending: expect.any(Number),
            processing: expect.any(Number),
            completed: expect.any(Number),
            failed: expect.any(Number),
            total: expect.any(Number),
            system_health_score: expect.any(Number),
        });

        expect(result.recent_items).toBeInstanceOf(Array);
        expect(result.recent_items.length).toBeLessThanOrEqual(10);
    });
});
```

## Related Endpoints

### Queue Management Workflow

1. **Create Job**: `POST /api/viral-ideas/queue` - Adds new analysis request
2. **Monitor Status**: `GET /api/viral-ideas/queue-status` - **This endpoint** - System overview
3. **Individual Status**: `GET /api/viral-ideas/queue/{session_id}` - Specific job tracking
4. **Process Jobs**: Background processors handle queue processing
5. **Get Results**: `GET /api/viral-analysis/{queue_id}/results` - Final analysis results

---

**Note**: This endpoint is designed for frequent polling (every 15-30 seconds) and should be optimized for performance with caching and efficient indexing.
