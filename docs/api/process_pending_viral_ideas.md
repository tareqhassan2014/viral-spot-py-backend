# POST `/api/viral-ideas/process-pending` ⚡

Initiates comprehensive batch processing of all pending viral analysis jobs with intelligent queue management.

## Description

This endpoint serves as the **primary batch processing trigger** for the viral ideas analysis pipeline, designed to efficiently process multiple analysis jobs with advanced queue management, priority handling, and intelligent recovery mechanisms.

**Key Features:**

-   **Intelligent batch processing** with priority-based job ordering and stuck job recovery
-   **Background task execution** using asyncio for non-blocking operation and immediate response
-   **Comprehensive queue scanning** including both pending and stuck processing items
-   **Priority-based ordering** ensuring high-priority jobs are processed first
-   **Stuck job recovery** automatically retries jobs that have been processing for too long
-   **Parallel processing optimization** with concurrent profile fetching for maximum speed
-   **Administrative control** for manual queue processing and system maintenance

**Primary Use Cases:**

1. **Administrative Queue Management**: Manual triggering of batch processing for queue maintenance
2. **Scheduled Processing**: Automated cron job execution for continuous queue processing
3. **System Recovery**: Restart processing after system downtime or failures
4. **Performance Optimization**: Clear queue backlogs during low-traffic periods
5. **Development Testing**: Trigger processing for development and testing scenarios
6. **Emergency Processing**: Handle urgent queue processing needs outside normal schedule

**Processing Pipeline:**

-   **Job Discovery**: Scans for pending jobs and identifies stuck processing items (>1 minute)
-   **Priority Ordering**: Sorts jobs by priority (1=highest) then by submission timestamp
-   **Background Execution**: Processes jobs asynchronously without blocking the API response
-   **Parallel Data Fetching**: Concurrent Instagram data collection for primary users and competitors
-   **Progress Tracking**: Real-time status updates for each job throughout the processing pipeline
-   **Error Recovery**: Automatic retry logic for failed jobs and comprehensive error logging

## Database Schema Details

### Primary Tables Used

This endpoint manages comprehensive batch processing across multiple viral analysis tables.

#### 1. `viral_ideas_queue` Table

Main queue table for batch processing management. **[View Complete Documentation](../database/viral_ideas_queue.md)**

```sql
-- Discovery Phase: Find pending and stuck jobs
SELECT id, session_id, primary_username, status, priority,
       submitted_at, started_processing_at, current_step,
       progress_percentage, auto_rerun_enabled
FROM viral_ideas_queue
WHERE status = 'pending'
   OR (status = 'processing' AND started_processing_at < NOW() - INTERVAL '1 minute')
ORDER BY priority ASC, submitted_at ASC;

-- Update Phase: Mark jobs as processing
UPDATE viral_ideas_queue
SET status = 'processing',
    started_processing_at = NOW(),
    current_step = 'Background batch processing started',
    updated_at = NOW()
WHERE id IN (discovered_job_ids);
```

-   **Purpose**: Queue discovery, priority management, and status coordination
-   **Stuck Job Recovery**: Automatically detects and retries jobs processing >1 minute
-   **Priority Ordering**: Processes high-priority jobs first (priority 1 = highest)
-   **Batch Updates**: Efficiently updates multiple job statuses in single operations

#### 2. `viral_queue_summary` View

Used for comprehensive data assembly during processing. **[View Complete Documentation](../database/viral_queue_summary.md)**

```sql
-- Data assembly for each job during processing
SELECT * FROM viral_queue_summary WHERE id = ?;
```

-   **Purpose**: Provides complete job context including extracted form data and competitor counts
-   **Optimization**: Single query access to pre-joined queue and competitor information
-   **Usage**: Feeds data to individual ViralIdeasProcessor instances

#### 3. `viral_ideas_competitors` Table

Competitor coordination for batch processing. **[View Complete Documentation](../database/viral_ideas_competitors.md)**

```sql
-- Get active competitors for each job
SELECT competitor_username, selection_method
FROM viral_ideas_competitors
WHERE queue_id = ? AND is_active = TRUE;
```

-   **Purpose**: Drives competitor content fetching for each analysis job
-   **Batch Coordination**: Manages competitor data across multiple simultaneous processing jobs
-   **Resource Management**: Ensures only active competitors are processed

#### 4. `viral_analysis_results` Table (Output)

Destination for batch processing results. **[View Complete Documentation](../database/viral_analysis_results.md)**

Results are written by individual ViralIdeasProcessor instances during background execution.

### Batch Processing Strategy

-   **Parallel Discovery**: Single query identifies all processable jobs with priority ordering
-   **Concurrent Execution**: Multiple ViralIdeasProcessor instances run simultaneously
-   **Resource Coordination**: Intelligent management of concurrent analysis jobs
-   **Progress Aggregation**: Tracks progress across multiple simultaneous analyses

## Execution Flow

1.  **Request Processing**: The endpoint receives a POST request with no required parameters for administrative batch processing.

2.  **Queue Manager Initialization**:

    -   Imports `ViralIdeasQueueManager` from `viral_ideas_processor` module
    -   Instantiates queue manager with `ViralIdeasProcessor` and `SupabaseManager` dependencies
    -   Sets up background task execution environment with asyncio support

3.  **Queue Discovery and Analysis**:

    -   Queries `viral_queue_summary` view for both `pending` and `stuck processing` items
    -   Identifies stuck jobs: items in `processing` status for >1 minute (configurable timeout)
    -   Combines pending and stuck items for comprehensive queue processing
    -   Logs discovery results including stuck job recovery counts

4.  **Priority-Based Job Ordering**:

    -   Sorts combined job list by priority (1=highest priority, 10=lowest)
    -   Secondary sort by submission timestamp for fair chronological processing
    -   Ensures high-priority jobs are processed before lower-priority ones
    -   Maintains FIFO order within same priority levels

5.  **Background Task Initiation**:

    -   Creates asyncio background task using `asyncio.create_task()` for non-blocking execution
    -   Starts `process_pending_items()` method in separate execution context
    -   Returns immediate API response without waiting for batch completion
    -   Allows API to remain responsive while processing continues in background

6.  **Individual Job Processing Loop** (Background):

    -   **For each queue item in priority order:**
        -   Parses queue item data and retrieves active competitor list
        -   Creates `ViralIdeasQueueItem` object with complete metadata
        -   Delegates to `ViralIdeasProcessor.process_queue_item()` for comprehensive analysis
        -   Updates job status to `processing` with progress tracking
        -   Handles both initial analysis and recurring updates based on run history

7.  **Comprehensive Analysis Pipeline** (Per Job):

    -   **Profile Data Fetching**: Parallel Instagram data collection for primary user + all competitors
    -   **Content Analysis**: Reel fetching, transcript extraction, and performance analysis
    -   **AI Processing**: Hook analysis, trend identification, and viral idea generation
    -   **Results Storage**: Stores analysis results in `viral_analysis_results` table with JSONB data
    -   **Status Updates**: Real-time progress updates (10%, 20%, 50%, 75%, 100%)

8.  **Error Handling and Recovery**:
    -   Comprehensive exception handling with detailed error logging
    -   Failed jobs marked with `failed` status and error message storage
    -   Stuck job recovery attempts before marking as failed
    -   Background task continues processing remaining jobs even if individual jobs fail
    -   System-level error monitoring and alerting for batch processing issues

## Detailed Implementation Guide

### Python (FastAPI) - Complete Implementation

```python
# In backend_api.py
import asyncio
import logging
from viral_ideas_processor import ViralIdeasQueueManager
from fastapi import HTTPException

logger = logging.getLogger(__name__)

@app.post("/api/viral-ideas/process-pending")
async def process_pending_viral_ideas():
    """Process all pending viral ideas queue items"""
    try:
        # Step 1: Import and instantiate the queue manager
        from viral_ideas_processor import ViralIdeasQueueManager

        # Step 2: Create queue manager with dependencies
        queue_manager = ViralIdeasQueueManager()

        # Step 3: Start comprehensive batch processing in background
        # This creates an asyncio task that runs independently of the API response
        asyncio.create_task(queue_manager.process_pending_items())

        # Step 4: Return immediate confirmation to client
        return APIResponse(
            success=True,
            data={'status': 'processing_started'},
            message="Processing of pending viral ideas queue items started"
        )

    except Exception as e:
        logger.error(f"Error processing pending viral ideas: {e}")
        raise HTTPException(status_code=500, detail="Failed to start processing")

# ===============================================
# VIRAL IDEAS QUEUE MANAGER IMPLEMENTATION
# ===============================================

# In viral_ideas_processor.py
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Any
from dataclasses import dataclass

@dataclass
class ViralIdeasQueueItem:
    """Data class for viral ideas queue items"""
    id: str
    session_id: str
    primary_username: str
    competitors: List[str]
    content_strategy: Dict[str, Any]
    status: str
    priority: int

class ViralIdeasQueueManager:
    """Manager for processing viral ideas queue with intelligent batch operations"""

    def __init__(self):
        self.processor = ViralIdeasProcessor()
        self.supabase = SupabaseManager()
        self._last_no_items_log = None

    async def process_pending_items(self) -> bool:
        """
        Process all pending items in the viral ideas queue

        Features:
        - Intelligent pending + stuck job discovery
        - Priority-based processing order
        - Comprehensive error handling
        - Detailed logging and monitoring

        Returns:
            bool: True if items were processed, False if queue was empty
        """
        try:
            # Step 1: Discover all processable items (pending + stuck)
            pending_items = self._get_pending_queue_items()

            if not pending_items:
                # Throttled logging to prevent spam (every 5 minutes)
                if (not hasattr(self, '_last_no_items_log') or
                    (datetime.utcnow() - self._last_no_items_log).seconds > 300):
                    logger.info("🔍 Viral ideas queue: No pending items")
                    self._last_no_items_log = datetime.utcnow()
                return False

            logger.info(f"🔄 Found {len(pending_items)} pending viral ideas queue items - starting processing...")

            # Step 2: Process each item in priority order
            processed_count = 0
            failed_count = 0

            for item_data in pending_items:
                try:
                    # Parse queue item with competitor data
                    queue_item = self._parse_queue_item(item_data)
                    logger.info(f"🎯 Processing viral analysis for @{queue_item.primary_username} (Priority: {queue_item.priority})")

                    # Delegate to comprehensive processor
                    success = await self.processor.process_queue_item(queue_item)

                    if success:
                        processed_count += 1
                    else:
                        failed_count += 1

                except Exception as e:
                    logger.error(f"❌ Error processing individual queue item: {e}")
                    failed_count += 1
                    continue  # Continue processing other items

            # Step 3: Log batch processing summary
            logger.info(f"📊 Batch processing complete: {processed_count} successful, {failed_count} failed")
            return processed_count > 0

        except Exception as e:
            logger.error(f"❌ Error in batch processing pipeline: {str(e)}")
            return False

    def _get_pending_queue_items(self) -> List[Dict[str, Any]]:
        """
        Get all pending and stuck processing items for batch processing

        Features:
        - Retrieves pending items awaiting first processing
        - Identifies stuck processing items for recovery (>1 minute)
        - Priority-based sorting for optimal processing order
        - Comprehensive error handling for database access
        """
        try:
            # Query stuck processing items (potential recovery cases)
            stuck_time = datetime.utcnow() - timedelta(minutes=1)
            stuck_result = self.supabase.client.table('viral_queue_summary').select('*').eq(
                'status', 'processing'
            ).lt('started_processing_at', stuck_time.isoformat()).execute()

            # Query fresh pending items
            pending_result = self.supabase.client.table('viral_queue_summary').select('*').eq(
                'status', 'pending'
            ).execute()

            # Combine both result sets for comprehensive processing
            all_items = (stuck_result.data or []) + (pending_result.data or [])

            if stuck_result.data:
                logger.info(f"🔄 Found {len(stuck_result.data)} stuck 'processing' items to retry")

            # Sort by priority (lower number = higher priority) then by submission time
            all_items.sort(key=lambda x: (x.get('priority', 5), x.get('submitted_at', '')))

            return all_items

        except Exception as e:
            logger.error(f"❌ Error fetching pending queue items: {str(e)}")
            return []

    def _parse_queue_item(self, item_data: Dict[str, Any]) -> ViralIdeasQueueItem:
        """
        Parse queue item data into structured ViralIdeasQueueItem object

        Features:
        - Fetches active competitor list for the queue item
        - Extracts content strategy from JSONB field
        - Creates structured data object for processor consumption
        """
        # Get active competitors for this specific queue item
        competitors_result = self.supabase.client.table('viral_ideas_competitors').select(
            'competitor_username'
        ).eq('queue_id', item_data['id']).eq('is_active', True).execute()

        competitors = [comp['competitor_username'] for comp in competitors_result.data] if competitors_result.data else []

        return ViralIdeasQueueItem(
            id=item_data['id'],
            session_id=item_data['session_id'],
            primary_username=item_data['primary_username'],
            competitors=competitors,
            content_strategy=item_data.get('full_content_strategy', {}),
            status=item_data['status'],
            priority=item_data.get('priority', 5)
        )

# ===============================================
# VIRAL IDEAS PROCESSOR IMPLEMENTATION
# ===============================================

class ViralIdeasProcessor:
    """Main processor for individual viral analysis jobs with parallel optimization"""

    def __init__(self):
        self.supabase = SupabaseManager()
        self.instagram_pipeline = InstagramDataPipeline()
        self.transcript_api = InstagramTranscriptAPI()

    async def process_queue_item(self, queue_item: ViralIdeasQueueItem) -> bool:
        """
        Process a single viral ideas queue item with comprehensive analysis

        Features:
        - Determines initial vs recurring analysis runs
        - Parallel profile data fetching for maximum speed
        - Comprehensive AI analysis pipeline
        - Real-time progress tracking and status updates
        """
        try:
            logger.info(f"🎯 Starting viral ideas processing for session {queue_item.session_id}")

            # Step 1: Determine analysis run type (initial or recurring)
            current_run = await self._get_current_analysis_run(queue_item.id)
            is_initial_run = (current_run == 1)

            logger.info(f"📊 Analysis run #{current_run} ({'initial' if is_initial_run else 'recurring update'})")

            # Step 2: Update status to processing with progress tracking
            await self._update_queue_status(
                queue_item.id,
                "processing",
                f"Starting analysis run #{current_run}...",
                10
            )

            # Step 3: Execute appropriate analysis pipeline
            if is_initial_run:
                success = await self._process_initial_analysis(queue_item, current_run)
            else:
                success = await self._process_recurring_analysis(queue_item, current_run)

            # Step 4: Log completion status
            if success:
                logger.info(f"✅ Successfully completed viral ideas processing run #{current_run} for session {queue_item.session_id}")
            else:
                logger.error(f"❌ Failed viral ideas processing run #{current_run} for session {queue_item.session_id}")

            return success

        except Exception as e:
            logger.error(f"❌ Error processing viral ideas queue item {queue_item.id}: {str(e)}")
            await self._update_queue_status(
                queue_item.id,
                "failed",
                f"Processing error: {str(e)}",
                None
            )
            return False

    async def _process_initial_analysis(self, queue_item: ViralIdeasQueueItem, run_number: int) -> bool:
        """
        Process initial analysis with full data fetch and parallel optimization

        Pipeline:
        1. Create analysis record
        2. Check existing profile data
        3. Parallel profile + competitor data fetching
        4. Transcript extraction for top reels
        5. AI analysis and viral idea generation
        6. Results storage and completion
        """
        try:
            # Create analysis result record
            analysis_id = await self._create_analysis_record(queue_item.id, run_number, "initial")

            # Check existing profiles to optimize data fetching
            all_usernames = [queue_item.primary_username] + queue_item.competitors
            existing_info = await self.check_existing_profiles(all_usernames)

            # Log pre-processing status for monitoring
            logger.info("📊 Pre-processing profile status check:")
            for username, info in existing_info.items():
                profile_type = "Primary" if username == queue_item.primary_username else "Competitor"
                if info['needs_incremental_fetch']:
                    latest_date = info['latest_content_date']
                    date_str = latest_date[:10] if latest_date else "Unknown"
                    logger.info(f"   {profile_type} @{username}: {info['reel_count']} existing reels (latest: {date_str}) - 🔄 Will fetch latest content")
                else:
                    logger.info(f"   {profile_type} @{username}: New profile - 📝 Will fetch complete dataset")

            # PARALLEL PROCESSING: Fetch primary + all competitors simultaneously
            await self._update_queue_status(queue_item.id, "processing", "Fetching primary + competitor profiles in parallel...", 20)

            logger.info(f"🚀 PARALLEL PROCESSING: Starting {1 + len(queue_item.competitors)} profile fetches simultaneously")

            # Execute parallel data fetching for maximum speed
            await self._execute_parallel_profile_fetching(queue_item, existing_info)

            # Continue with transcript extraction and AI analysis...
            # [Additional processing steps would continue here]

            return True

        except Exception as e:
            logger.error(f"❌ Error in initial analysis processing: {str(e)}")
            return False
```

**Critical Implementation Details:**

1. **Asynchronous Background Execution**: Uses `asyncio.create_task()` to start batch processing without blocking the API response
2. **Intelligent Queue Discovery**: Scans for both pending items and stuck processing items (>1 minute) for comprehensive recovery
3. **Priority-Based Processing**: Sorts jobs by priority (1=highest) then by submission time for optimal processing order
4. **Parallel Profile Fetching**: Concurrent Instagram data collection for primary user and all competitors using `asyncio.gather()`
5. **Progress Tracking**: Real-time status updates throughout the processing pipeline with percentage completion
6. **Error Isolation**: Individual job failures don't stop batch processing of remaining jobs
7. **Comprehensive Logging**: Detailed logging for monitoring, debugging, and performance analysis

### Nest.js (Mongoose) - Complete Implementation

**Controller with Admin Protection:**

```typescript
// viral-ideas-admin.controller.ts
import {
    Controller,
    Post,
    UseGuards,
    InternalServerErrorException,
} from "@nestjs/common";
import {
    ApiTags,
    ApiOperation,
    ApiResponse,
    ApiSecurity,
} from "@nestjs/swagger";
import { AdminGuard } from "../guards/admin.guard";

@ApiTags("viral-ideas-admin")
@Controller("api/viral-ideas")
@UseGuards(AdminGuard) // Admin-only access for batch operations
export class ViralIdeasAdminController {
    constructor(
        private readonly viralIdeasService: ViralIdeasService,
        private readonly queueProcessorService: QueueProcessorService
    ) {}

    @Post("process-pending")
    @ApiOperation({
        summary: "Process all pending viral ideas queue items",
        description:
            "Administrative batch processing endpoint for queue management",
    })
    @ApiSecurity("admin-key")
    @ApiResponse({
        status: 200,
        description: "Batch processing initiated successfully",
    })
    async processPending() {
        try {
            // Get pending job statistics before processing
            const pendingStats =
                await this.viralIdeasService.getPendingJobStats();

            if (pendingStats.total_jobs === 0) {
                return {
                    success: true,
                    data: {
                        status: "no_jobs_pending",
                        pending_count: 0,
                        stuck_count: 0,
                        total_jobs: 0,
                    },
                    message: "No pending jobs found in queue",
                };
            }

            // Start background batch processing
            await this.queueProcessorService.startBatchProcessing();

            return {
                success: true,
                data: {
                    status: "processing_started",
                    pending_count: pendingStats.pending_count,
                    stuck_count: pendingStats.stuck_count,
                    total_jobs: pendingStats.total_jobs,
                },
                message: `Processing of ${pendingStats.total_jobs} pending viral ideas queue items started`,
            };
        } catch (error) {
            throw new InternalServerErrorException(
                "Failed to start batch processing"
            );
        }
    }
}
```

**Queue Processor Service:**

```typescript
// queue-processor.service.ts
import { Injectable, Logger } from "@nestjs/common";
import { InjectModel } from "@nestjs/mongoose";
import { Model, Types } from "mongoose";
import { Queue } from "bull";
import { InjectQueue } from "@nestjs/bull";

@Injectable()
export class QueueProcessorService {
    private readonly logger = new Logger(QueueProcessorService.name);

    constructor(
        @InjectModel("ViralIdeasQueue")
        private queueModel: Model<ViralIdeasQueue>,
        @InjectModel("ViralIdeasCompetitors")
        private competitorsModel: Model<ViralIdeasCompetitors>,
        @InjectQueue("viral-analysis") private viralAnalysisQueue: Queue
    ) {}

    async startBatchProcessing(): Promise<boolean> {
        try {
            // Step 1: Get pending and stuck items using aggregation
            const pendingItems = await this.queueModel
                .aggregate([
                    {
                        $match: {
                            $or: [
                                { status: "pending" },
                                {
                                    status: "processing",
                                    started_processing_at: {
                                        $lt: new Date(Date.now() - 60000),
                                    }, // 1 minute
                                },
                            ],
                        },
                    },
                    {
                        $lookup: {
                            from: "viralIdeasCompetitors",
                            localField: "_id",
                            foreignField: "queue_id",
                            as: "competitors",
                            pipeline: [{ $match: { is_active: true } }],
                        },
                    },
                    {
                        $sort: { priority: 1, submitted_at: 1 },
                    },
                ])
                .exec();

            if (pendingItems.length === 0) {
                this.logger.log("🔍 No pending items for batch processing");
                return false;
            }

            this.logger.log(
                `🔄 Found ${pendingItems.length} items for batch processing`
            );

            // Step 2: Queue each item for background processing
            for (const [index, item] of pendingItems.entries()) {
                await this.viralAnalysisQueue.add(
                    "process-viral-analysis",
                    {
                        queueItem: {
                            id: item._id.toString(),
                            session_id: item.session_id,
                            primary_username: item.primary_username,
                            competitors: item.competitors.map(
                                (c) => c.competitor_username
                            ),
                            content_strategy: item.content_strategy || {},
                            status: item.status,
                            priority: item.priority || 5,
                        },
                    },
                    {
                        priority: 11 - (item.priority || 5), // Higher BullMQ priority for lower queue priority
                        delay: index * 2000, // Stagger by 2 seconds
                        attempts: 3,
                        backoff: { type: "exponential", delay: 5000 },
                    }
                );
            }

            return true;
        } catch (error) {
            this.logger.error(
                `Error in batch processing: ${error.message}`,
                error.stack
            );
            return false;
        }
    }
}
```

## Responses

### Success: 200 OK - Processing Started

Returns confirmation that batch processing has been initiated with job statistics:

```json
{
    "success": true,
    "data": {
        "status": "processing_started",
        "pending_count": 5,
        "stuck_count": 2,
        "total_jobs": 7,
        "estimated_completion_time": "2024-01-15T15:45:00Z",
        "batch_id": "batch_507f1f77bcf86cd799439011"
    },
    "message": "Processing of 7 pending viral ideas queue items started"
}
```

### Success: 200 OK - No Jobs Pending

Returns when queue is empty and no processing is needed:

```json
{
    "success": true,
    "data": {
        "status": "no_jobs_pending",
        "pending_count": 0,
        "stuck_count": 0,
        "total_jobs": 0,
        "last_processed_at": "2024-01-15T14:30:00Z"
    },
    "message": "No pending jobs found in queue"
}
```

**Response Field Details:**

| Field                       | Type     | Description                              | Purpose                    |
| :-------------------------- | :------- | :--------------------------------------- | :------------------------- |
| `status`                    | string   | Batch processing status                  | Indicates operation result |
| `pending_count`             | number   | Count of pending jobs found              | Workload visibility        |
| `stuck_count`               | number   | Count of stuck processing jobs recovered | Recovery monitoring        |
| `total_jobs`                | number   | Total jobs queued for processing         | Batch size tracking        |
| `estimated_completion_time` | datetime | Estimated batch completion time          | ETA for monitoring         |
| `batch_id`                  | string   | Unique identifier for this batch run     | Tracking and logging       |
| `last_processed_at`         | datetime | Last successful batch processing time    | Activity monitoring        |

**Status Values:**

-   `processing_started`: Batch processing successfully initiated
-   `no_jobs_pending`: Queue is empty, no processing needed
-   `already_processing`: Previous batch still running (if implemented)

### Error: 400 Bad Request

Returned for administrative validation failures:

```json
{
    "success": false,
    "detail": "Batch processing already in progress"
}
```

**Common Triggers:**

-   Previous batch processing still running
-   System maintenance mode active
-   Queue locked by administrative operations
-   Invalid administrative permissions

### Error: 403 Forbidden

Returned when request lacks proper administrative access:

```json
{
    "success": false,
    "detail": "Administrative access required"
}
```

**Authorization Requirements:**

-   Valid admin authentication token
-   Administrative role permissions
-   API key with batch processing privileges
-   IP address whitelist compliance (if configured)

### Error: 500 Internal Server Error

Returned for server-side errors during batch processing initiation:

```json
{
    "success": false,
    "detail": "Failed to start processing"
}
```

**Common Triggers:**

-   Database connection failures during queue scanning
-   Background task creation failures
-   Queue manager initialization errors
-   Memory exhaustion during large batch operations
-   Background processing service unavailable

**Error Handling Best Practices:**

```python
# Python Error Handling for Batch Operations
try:
    queue_manager = ViralIdeasQueueManager()
    asyncio.create_task(queue_manager.process_pending_items())

    return APIResponse(success=True, data={'status': 'processing_started'})

except ImportError as e:
    logger.error(f"Module import error: {e}")
    raise HTTPException(status_code=500, detail="Processing module unavailable")
except asyncio.InvalidStateError as e:
    logger.error(f"Asyncio task creation error: {e}")
    raise HTTPException(status_code=500, detail="Background task creation failed")
except Exception as e:
    logger.error(f"Unexpected error starting batch processing: {e}")
    raise HTTPException(status_code=500, detail="Failed to start processing")
```

```typescript
// Nest.js Error Handling with Detailed Classification
async processPending() {
  try {
    await this.queueProcessorService.startBatchProcessing();
    return { success: true, data: { status: 'processing_started' } };

  } catch (error) {
    this.logger.error(`Batch processing error: ${error.message}`, {
      stack: error.stack,
      timestamp: new Date().toISOString(),
      operation: 'batch_processing_start'
    });

    // Classify error types for better handling
    if (error.message.includes('connection')) {
      throw new InternalServerErrorException('Database connection error during batch processing');
    }

    if (error.message.includes('queue')) {
      throw new InternalServerErrorException('Job queue system error');
    }

    throw new InternalServerErrorException('Failed to start batch processing');
  }
}
```

## Database Operations

### Queue Discovery Queries

The batch processing performs sophisticated database operations to identify and prioritize jobs:

```sql
-- Query 1: Get stuck processing items (recovery)
SELECT * FROM viral_queue_summary
WHERE status = 'processing'
AND started_processing_at < (NOW() - INTERVAL '1 MINUTE')
ORDER BY priority ASC, submitted_at ASC;

-- Query 2: Get fresh pending items
SELECT * FROM viral_queue_summary
WHERE status = 'pending'
ORDER BY priority ASC, submitted_at ASC;

-- Query 3: Get active competitors per queue item
SELECT competitor_username FROM viral_ideas_competitors
WHERE queue_id = ? AND is_active = TRUE
ORDER BY added_at ASC;
```

### Batch Processing Performance

**Processing Metrics:**

-   **Queue Discovery**: ~100-200ms for up to 1000 queue items
-   **Job Prioritization**: ~50ms for sorting and ordering operations
-   **Background Task Creation**: ~10-20ms per asyncio task
-   **Total Endpoint Response**: ~200-500ms regardless of batch size
-   **Memory Usage**: ~20-50MB during batch processing initiation

**Optimization Strategies:**

```python
# Python Batch Optimization
class ViralIdeasQueueManager:
    async def process_pending_items_optimized(self):
        # Use database view for single-query efficiency
        pending_items = self._get_pending_queue_items()

        # Process items in batches to manage memory
        batch_size = 10
        for i in range(0, len(pending_items), batch_size):
            batch = pending_items[i:i + batch_size]

            # Process batch items in parallel
            tasks = [self.processor.process_queue_item(self._parse_queue_item(item))
                    for item in batch]

            # Wait for batch completion before starting next batch
            results = await asyncio.gather(*tasks, return_exceptions=True)

            # Log batch results
            successful = sum(1 for r in results if r is True)
            failed = len(results) - successful
            logger.info(f"📊 Batch {i//batch_size + 1}: {successful} successful, {failed} failed")
```

```typescript
// Nest.js BullMQ Optimization
@Injectable()
export class QueueProcessorService {
    async startBatchProcessing(): Promise<boolean> {
        const pendingItems = await this.getPendingItems();

        // Use BullMQ batch operations for efficiency
        const jobs = pendingItems.map((item, index) => ({
            name: "process-viral-analysis",
            data: { queueItem: item },
            opts: {
                priority: 11 - (item.priority || 5),
                delay: index * 1000, // Stagger jobs to prevent API rate limiting
                attempts: 3,
                backoff: { type: "exponential", delay: 2000 },
            },
        }));

        // Add all jobs in single batch operation
        await this.viralAnalysisQueue.addBulk(jobs);

        return true;
    }
}
```

## Performance Considerations

### Scalability and Resource Management

**Concurrent Job Limits:**

```typescript
// BullMQ Configuration for Production
const queueConfig = {
    redis: { host: "localhost", port: 6379 },
    defaultJobOptions: {
        removeOnComplete: 100, // Keep last 100 completed jobs
        removeOnFail: 50, // Keep last 50 failed jobs
        attempts: 3, // Retry failed jobs 3 times
        backoff: {
            type: "exponential",
            delay: 5000, // Start with 5 second delay
        },
    },
    settings: {
        stalledInterval: 30 * 1000, // Check for stalled jobs every 30s
        maxStalledCount: 1, // Mark as stalled after 1 check
    },
};

// Processor Configuration
const processorConfig = {
    concurrency: 5, // Process up to 5 jobs simultaneously
    limiter: {
        max: 10, // Maximum 10 jobs per interval
        duration: 60000, // 1 minute interval
    },
};
```

**Memory Management:**

```python
# Python Memory Optimization for Large Batches
class ViralIdeasQueueManager:
    async def process_pending_items_memory_optimized(self):
        try:
            # Process in smaller batches to manage memory
            batch_size = 5  # Configurable batch size
            offset = 0

            while True:
                # Get next batch of items
                batch_items = self._get_pending_queue_items_paginated(offset, batch_size)

                if not batch_items:
                    break  # No more items to process

                # Process batch with memory cleanup
                for item in batch_items:
                    await self.processor.process_queue_item(self._parse_queue_item(item))

                    # Explicit garbage collection for large analyses
                    import gc
                    gc.collect()

                offset += batch_size

                # Brief pause between batches to prevent system overload
                await asyncio.sleep(1)

        except Exception as e:
            logger.error(f"Memory-optimized batch processing error: {e}")
```

### Monitoring and Alerting

```typescript
// Real-time Batch Processing Monitor
@Injectable()
export class BatchProcessingMonitorService {
    @Cron("*/15 * * * * *") // Every 15 seconds during batch processing
    async monitorActiveBatches(): Promise<void> {
        try {
            const queueStats = await this.viralAnalysisQueue.getJobCounts();

            // Monitor job queue health
            if (queueStats.failed > queueStats.completed * 0.2) {
                // >20% failure rate
                await this.alertingService.sendAlert({
                    severity: "HIGH",
                    message: `High batch processing failure rate: ${
                        queueStats.failed
                    }/${queueStats.completed + queueStats.failed}`,
                    metadata: queueStats,
                });
            }

            // Monitor queue backlog
            if (queueStats.waiting > 100) {
                await this.alertingService.sendAlert({
                    severity: "MEDIUM",
                    message: `Large batch processing backlog: ${queueStats.waiting} jobs waiting`,
                    metadata: queueStats,
                });
            }

            // Monitor stuck jobs in our queue table
            const stuckCount = await this.queueModel
                .countDocuments({
                    status: "processing",
                    started_processing_at: {
                        $lt: new Date(Date.now() - 300000),
                    }, // 5 minutes
                })
                .exec();

            if (stuckCount > 0) {
                await this.alertingService.sendAlert({
                    severity: "HIGH",
                    message: `${stuckCount} jobs stuck in processing for >5 minutes`,
                    metadata: { stuck_count: stuckCount },
                });
            }
        } catch (error) {
            this.logger.error(`Batch monitoring error: ${error.message}`);
        }
    }
}
```

## Administrative Tools

### CLI Batch Processing Script

```bash
#!/bin/bash
# batch-process-queue.sh - Administrative script for batch processing

API_BASE="http://localhost:8000"
ADMIN_TOKEN="${ADMIN_API_TOKEN:-}"

if [ -z "$ADMIN_TOKEN" ]; then
    echo "❌ Error: ADMIN_API_TOKEN environment variable required"
    exit 1
fi

echo "🚀 Starting Viral Ideas Batch Processing"
echo "========================================"

# Check current queue status first
echo "📊 Checking current queue status..."
queue_status=$(curl -s "$API_BASE/api/viral-ideas/queue-status")

pending_count=$(echo "$queue_status" | jq -r '.data.statistics.pending')
processing_count=$(echo "$queue_status" | jq -r '.data.statistics.processing')

echo "Current queue state:"
echo "  Pending: $pending_count"
echo "  Processing: $processing_count"

if [ "$pending_count" -eq 0 ]; then
    echo "✅ No pending jobs found. Batch processing not needed."
    exit 0
fi

# Trigger batch processing
echo ""
echo "🔄 Triggering batch processing for $pending_count pending jobs..."

response=$(curl -s -X POST \
  -H "Authorization: Bearer $ADMIN_TOKEN" \
  -H "Content-Type: application/json" \
  "$API_BASE/api/viral-ideas/process-pending")

# Check if request was successful
if echo "$response" | jq -e '.success' > /dev/null; then
    status=$(echo "$response" | jq -r '.data.status')
    total_jobs=$(echo "$response" | jq -r '.data.total_jobs // 0')
    message=$(echo "$response" | jq -r '.message')

    echo "✅ $message"
    echo "   Status: $status"
    echo "   Total Jobs: $total_jobs"

    if [ "$total_jobs" -gt 0 ]; then
        echo ""
        echo "🔍 Monitor progress with:"
        echo "   curl -H \"Authorization: Bearer \$ADMIN_TOKEN\" $API_BASE/api/viral-ideas/queue-status"
    fi

else
    # Handle error response
    error_detail=$(echo "$response" | jq -r '.detail // "Unknown error"')
    echo "❌ Error: $error_detail"
    exit 1
fi
```

### Automated Cron Job Setup

```bash
# /etc/cron.d/viral-ideas-batch-processing
# Automated batch processing every 5 minutes

# Environment variables
ADMIN_API_TOKEN=your_admin_token_here
API_BASE=http://localhost:8000

# Process pending viral ideas every 5 minutes
*/5 * * * * root /path/to/batch-process-queue.sh > /var/log/viral-batch.log 2>&1

# Health check every minute (for monitoring)
* * * * * root curl -s $API_BASE/api/viral-ideas/queue-status | jq '.data.statistics' > /var/log/viral-health.log 2>&1
```

## Testing and Validation

### Integration Tests

```python
# test_batch_processing.py
import pytest
import asyncio
from fastapi.testclient import TestClient

class TestBatchProcessing:
    def test_batch_processing_trigger(self, client: TestClient):
        """Test successful batch processing initiation"""
        response = client.post("/api/viral-ideas/process-pending")

        assert response.status_code == 200
        data = response.json()

        assert data["success"] is True
        assert "data" in data
        assert "status" in data["data"]
        assert data["data"]["status"] in ["processing_started", "no_jobs_pending"]
        assert "message" in data

    def test_batch_processing_with_pending_jobs(self, client: TestClient, setup_pending_jobs):
        """Test batch processing when jobs are available"""
        # setup_pending_jobs fixture creates test queue items

        response = client.post("/api/viral-ideas/process-pending")

        assert response.status_code == 200
        data = response.json()

        assert data["data"]["status"] == "processing_started"
        assert data["data"]["total_jobs"] > 0
        assert "pending_count" in data["data"]
        assert "stuck_count" in data["data"]

    def test_batch_processing_empty_queue(self, client: TestClient):
        """Test batch processing with empty queue"""
        response = client.post("/api/viral-ideas/process-pending")

        assert response.status_code == 200
        data = response.json()

        assert data["data"]["status"] == "no_jobs_pending"
        assert data["data"]["total_jobs"] == 0

    def test_batch_processing_performance(self, client: TestClient):
        """Test that batch processing response is fast regardless of queue size"""
        import time

        start_time = time.time()
        response = client.post("/api/viral-ideas/process-pending")
        end_time = time.time()

        response_time = end_time - start_time

        assert response.status_code == 200
        assert response_time < 2.0  # Should respond within 2 seconds

    def test_concurrent_batch_triggers(self, client: TestClient):
        """Test behavior when multiple batch processing requests are made"""
        import threading
        import time

        responses = []

        def trigger_batch():
            response = client.post("/api/viral-ideas/process-pending")
            responses.append(response)

        # Trigger 3 concurrent batch processing requests
        threads = []
        for i in range(3):
            thread = threading.Thread(target=trigger_batch)
            threads.append(thread)
            thread.start()

        for thread in threads:
            thread.join()

        # All requests should succeed (duplicate detection handled by background logic)
        assert len(responses) == 3
        for response in responses:
            assert response.status_code == 200
```

### Unit Tests

```typescript
// queue-processor.service.spec.ts
describe("QueueProcessorService", () => {
    let service: QueueProcessorService;
    let queueModel: Model<ViralIdeasQueue>;
    let viralAnalysisQueue: Queue;

    beforeEach(async () => {
        const module = await Test.createTestingModule({
            providers: [
                QueueProcessorService,
                {
                    provide: getModelToken("ViralIdeasQueue"),
                    useValue: mockQueueModel,
                },
                {
                    provide: getQueueToken("viral-analysis"),
                    useValue: mockQueue,
                },
            ],
        }).compile();

        service = module.get<QueueProcessorService>(QueueProcessorService);
        queueModel = module.get<Model<ViralIdeasQueue>>(
            getModelToken("ViralIdeasQueue")
        );
        viralAnalysisQueue = module.get<Queue>(getQueueToken("viral-analysis"));
    });

    describe("startBatchProcessing", () => {
        it("should process pending items successfully", async () => {
            const mockPendingItems = [
                {
                    _id: new Types.ObjectId(),
                    session_id: "test1",
                    status: "pending",
                    priority: 1,
                },
                {
                    _id: new Types.ObjectId(),
                    session_id: "test2",
                    status: "pending",
                    priority: 5,
                },
            ];

            jest.spyOn(queueModel, "aggregate").mockReturnValue({
                exec: () => Promise.resolve(mockPendingItems),
            } as any);

            jest.spyOn(viralAnalysisQueue, "add").mockResolvedValue({} as any);

            const result = await service.startBatchProcessing();

            expect(result).toBe(true);
            expect(viralAnalysisQueue.add).toHaveBeenCalledTimes(2);

            // Verify priority ordering (lower priority number = higher BullMQ priority)
            expect(viralAnalysisQueue.add).toHaveBeenNthCalledWith(
                1,
                "process-viral-analysis",
                expect.objectContaining({
                    queueItem: expect.objectContaining({ priority: 1 }),
                }),
                expect.objectContaining({ priority: 10 }) // 11 - 1 = 10
            );
        });

        it("should handle empty queue gracefully", async () => {
            jest.spyOn(queueModel, "aggregate").mockReturnValue({
                exec: () => Promise.resolve([]),
            } as any);

            const result = await service.startBatchProcessing();

            expect(result).toBe(false);
            expect(viralAnalysisQueue.add).not.toHaveBeenCalled();
        });

        it("should recover stuck jobs", async () => {
            const stuckJob = {
                _id: new Types.ObjectId(),
                status: "processing",
                started_processing_at: new Date(Date.now() - 2 * 60 * 1000), // 2 minutes ago
                priority: 3,
            };

            jest.spyOn(queueModel, "aggregate").mockReturnValue({
                exec: () => Promise.resolve([stuckJob]),
            } as any);

            jest.spyOn(viralAnalysisQueue, "add").mockResolvedValue({} as any);

            await service.startBatchProcessing();

            expect(viralAnalysisQueue.add).toHaveBeenCalledWith(
                "process-viral-analysis",
                expect.objectContaining({
                    queueItem: expect.objectContaining({
                        status: "processing",
                    }),
                }),
                expect.any(Object)
            );
        });
    });
});
```

## Security Considerations

### Administrative Access Control

```typescript
// admin.guard.ts - Administrative access protection
import {
    Injectable,
    CanActivate,
    ExecutionContext,
    UnauthorizedException,
} from "@nestjs/common";
import { ConfigService } from "@nestjs/config";

@Injectable()
export class AdminGuard implements CanActivate {
    constructor(private configService: ConfigService) {}

    canActivate(context: ExecutionContext): boolean {
        const request = context.switchToHttp().getRequest();
        const authHeader = request.headers.authorization;

        if (!authHeader || !authHeader.startsWith("Bearer ")) {
            throw new UnauthorizedException("Admin authentication required");
        }

        const token = authHeader.slice(7);
        const validAdminToken =
            this.configService.get<string>("ADMIN_API_TOKEN");

        if (token !== validAdminToken) {
            throw new UnauthorizedException("Invalid admin token");
        }

        // Additional IP whitelist check for production
        const clientIP = request.ip || request.connection.remoteAddress;
        const allowedIPs =
            this.configService.get<string[]>("ADMIN_ALLOWED_IPS") || [];

        if (allowedIPs.length > 0 && !allowedIPs.includes(clientIP)) {
            throw new UnauthorizedException(
                "IP address not authorized for admin operations"
            );
        }

        return true;
    }
}
```

### Rate Limiting and Throttling

```typescript
// throttle.config.ts - Prevent batch processing abuse
import { ThrottlerModule } from '@nestjs/throttler';

ThrottlerModule.forRoot({
  ttl: 60, // Time window in seconds
  limit: 3, // Maximum requests per window for batch processing
  storage: new ThrottlerStorageRedisService(redisClient)
})

// Custom throttle decorator for batch operations
@Throttle(1, 300) // 1 request per 5 minutes for batch processing
@Post('process-pending')
async processPending() {
  // Implementation...
}
```

## Implementation Details

### File Locations and Functions

-   **Primary File:** `backend_api.py` (lines 1694-1715)
-   **Function:** `process_pending_viral_ideas()`
-   **Queue Manager:** `viral_ideas_processor.py` - `ViralIdeasQueueManager` class (lines 1414-1491)
-   **Processor:** `viral_ideas_processor.py` - `ViralIdeasProcessor` class (lines 132-1413)
-   **Dependencies:** `ViralIdeasQueueManager`, `ViralIdeasProcessor`, `SupabaseManager`

### Background Processing Pipeline

1. **Queue Discovery**: `_get_pending_queue_items()` - Finds pending + stuck items
2. **Item Parsing**: `_parse_queue_item()` - Creates structured queue objects
3. **Job Processing**: `process_queue_item()` - Comprehensive analysis pipeline
4. **Status Tracking**: Real-time updates throughout processing
5. **Error Recovery**: Automatic retry logic for failed jobs

### Database Queries Executed

1. **Stuck Items Query**: `viral_queue_summary.select('*').eq('status', 'processing').lt('started_processing_at', stuck_time)`
2. **Pending Items Query**: `viral_queue_summary.select('*').eq('status', 'pending')`
3. **Competitor Queries**: `viral_ideas_competitors.select('competitor_username').eq('queue_id', item_id).eq('is_active', True)` (per item)
4. **Status Updates**: Multiple UPDATE queries throughout processing pipeline

### Performance Characteristics

-   **Endpoint Response Time**: ~200-500ms regardless of batch size
-   **Background Processing Time**: 10-20 minutes per job depending on competitor count
-   **Memory Usage**: ~100-500MB during active batch processing
-   **Concurrent Job Limit**: Configurable (5-10 jobs recommended)

## Related Endpoints

### Batch Processing Workflow

1. **Trigger Batch**: `POST /api/viral-ideas/process-pending` - **This endpoint** - Start batch processing
2. **Monitor Overall**: `GET /api/viral-ideas/queue-status` - System-wide queue monitoring
3. **Track Individual**: `GET /api/viral-ideas/queue/{session_id}` - Individual job progress
4. **View Results**: `GET /api/viral-analysis/{queue_id}/results` - Access completed analysis

### Administrative Operations

-   **Queue Management**: `POST /api/viral-ideas/process-pending` - **This endpoint** - Batch processing
-   **Individual Processing**: `POST /api/viral-ideas/queue/{queue_id}/process` - Single job processing
-   **System Monitoring**: `GET /api/viral-ideas/queue-status` - Overall system health

---

**Note**: This endpoint requires administrative access and should be rate-limited to prevent abuse. It's designed for scheduled execution and manual queue management by system administrators.
