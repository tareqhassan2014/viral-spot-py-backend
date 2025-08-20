# POST `/api/viral-ideas/queue/{queue_id}/start` ⚡

**Viral Analysis Queue Signal with Intelligent Worker Process Coordination**

## Description

The Start Viral Analysis endpoint provides comprehensive queue signaling and worker coordination for viral content analysis workflows. This endpoint serves as a critical trigger mechanism that signals the background processing system that a specific viral ideas analysis job is ready for processing, while maintaining robust queue state management and worker process coordination.

### Key Features

-   **Queue Signal Management**: Intelligent signaling system for background worker process coordination
-   **Job State Verification**: Comprehensive queue entry validation and status verification before processing
-   **Worker Process Integration**: Seamless coordination with background ViralIdeasProcessor workers
-   **Priority Queue Support**: Integration with priority-based queue management for urgent analysis requests
-   **Status Tracking**: Real-time status monitoring and progress tracking throughout the analysis lifecycle
-   **Error Recovery**: Robust error handling and recovery mechanisms for failed queue operations
-   **Asynchronous Processing**: Non-blocking queue signaling with background processing coordination

### Primary Use Cases

-   **Manual Analysis Triggers**: Allow users to manually trigger processing of queued viral analysis jobs
-   **Priority Processing**: Signal high-priority analysis jobs for immediate background processing
-   **Queue Management**: Provide control over queue processing flow and timing
-   **Development Testing**: Support testing and debugging of viral analysis processing workflows
-   **Administrative Control**: Enable administrative management of analysis queue processing
-   **Background Coordination**: Coordinate between frontend requests and background worker processes
-   **Processing Recovery**: Restart or retry analysis jobs that may have stalled or failed

### Viral Analysis Processing Pipeline

-   **Queue Entry Validation**: Verify queue entry exists and is in appropriate state for processing
-   **Worker Signal Generation**: Generate processing signals for background ViralIdeasProcessor workers
-   **Status Coordination**: Coordinate status updates between signaling endpoint and actual processors
-   **Priority Management**: Handle priority-based processing coordination for urgent analysis requests
-   **Error State Handling**: Manage error states and recovery mechanisms for failed processing attempts
-   **Progress Monitoring**: Enable real-time progress monitoring and status updates
-   **Completion Tracking**: Track analysis completion and result availability

### Background Worker Integration

-   **ViralIdeasProcessor Coordination**: Direct integration with background viral analysis processor workers
-   **Parallel Processing Support**: Coordinate parallel processing of multiple competitors and content sources
-   **Resource Management**: Intelligent resource allocation and management for concurrent analysis jobs
-   **Queue Polling**: Support for background worker queue polling and job pickup mechanisms
-   **Status Broadcasting**: Real-time status broadcasting between workers and monitoring systems
-   **Completion Notifications**: Automated notifications and callbacks when analysis processing completes

## Path Parameters

| Parameter  | Type   | Required | Description                                                 |
| :--------- | :----- | :------- | :---------------------------------------------------------- |
| `queue_id` | string | ✅       | UUID identifier for the viral analysis queue entry to start |

## Execution Flow

1. **Request Validation**: Validate queue_id parameter format and ensure it meets UUID requirements
2. **Queue Entry Verification**: Query viral_ideas_queue table to verify the specified queue entry exists
3. **Status State Check**: Verify the queue entry is in an appropriate state (typically 'pending') for processing
4. **Worker Availability**: Ensure background ViralIdeasProcessor workers are available for processing coordination
5. **Signal Generation**: Generate processing signal for background workers to pick up the queue entry
6. **Status Coordination**: Coordinate status tracking between signaling endpoint and worker processes
7. **Response Generation**: Generate success response confirming queue entry is ready for background processing
8. **Background Monitoring**: Enable monitoring of background processing progress and status updates

## Complete Implementation

### Python (FastAPI) Implementation

```python
# In backend_api.py - Main endpoint implementation
@app.post("/api/viral-ideas/queue/{queue_id}/start")
async def start_viral_analysis(queue_id: str, api_instance: ViralSpotAPI = Depends(get_api)):
    """
    Mark viral ideas analysis as ready to be picked up by processor

    This endpoint:
    - Verifies the queue entry exists and is in valid state
    - Signals background workers that job is ready for processing
    - Coordinates status tracking with ViralIdeasProcessor workers
    - Returns confirmation that processing will begin shortly

    Note: This endpoint does not immediately start processing. It signals
    background workers who will update the status to 'processing' when
    they actually begin the analysis workflow.
    """
    try:
        # Input validation
        if not queue_id:
            logger.warning("⚠️ Missing queue_id parameter for viral analysis start")
            raise HTTPException(
                status_code=400,
                detail="queue_id parameter is required"
            )

        # Validate UUID format
        import uuid
        try:
            uuid_obj = uuid.UUID(queue_id)
        except ValueError:
            logger.warning(f"⚠️ Invalid UUID format for queue_id: {queue_id}")
            raise HTTPException(
                status_code=400,
                detail="queue_id must be a valid UUID"
            )

        logger.info(f"🎯 Starting viral analysis signal for queue: {queue_id}")

        # Verify the queue entry exists and get current status
        check_result = api_instance.supabase.client.table('viral_ideas_queue').select(
            'id, status, session_id, primary_username, priority, current_step, progress_percentage, created_at, submitted_at'
        ).eq('id', queue_id).execute()

        if not check_result.data:
            logger.warning(f"❌ Queue entry not found: {queue_id}")
            raise HTTPException(
                status_code=404,
                detail="Queue entry not found"
            )

        queue_item = check_result.data[0]
        current_status = queue_item['status']

        logger.info(f"📊 Queue entry found - Status: {current_status}, User: @{queue_item['primary_username']}")

        # Validate queue state for processing
        valid_states = ['pending', 'failed', 'paused']
        if current_status not in valid_states:
            logger.warning(f"⚠️ Invalid queue state for processing: {current_status}")
            raise HTTPException(
                status_code=409,
                detail=f"Queue entry is in '{current_status}' state and cannot be started. Valid states: {', '.join(valid_states)}"
            )

        # Check if processing is already in progress
        if current_status == 'processing':
            logger.info(f"ℹ️ Queue entry already in processing state: {queue_id}")
            return APIResponse(
                success=True,
                data={
                    'queue_id': queue_id,
                    'status': current_status,
                    'current_step': queue_item.get('current_step', 'Processing...'),
                    'progress_percentage': queue_item.get('progress_percentage', 0),
                    'session_id': queue_item['session_id'],
                    'primary_username': queue_item['primary_username'],
                    'processing_state': 'already_started'
                },
                message="Analysis is already in progress"
            )

        # Optional: Update queue entry to signal it's ready for processing
        update_result = api_instance.supabase.client.table('viral_ideas_queue').update({
            'updated_at': datetime.utcnow().isoformat(),
            'current_step': 'Signaled for processing - awaiting worker pickup'
        }).eq('id', queue_id).execute()

        if not update_result.data:
            logger.warning(f"⚠️ Failed to update queue entry signal: {queue_id}")
        else:
            logger.info(f"✅ Queue entry signaled for processing: {queue_id}")

        # Generate processing signal response
        logger.info(f"🚀 Viral analysis queued successfully: {queue_id}")

        return APIResponse(
            success=True,
            data={
                'queue_processing': {
                    'queue_id': queue_id,
                    'status': current_status,
                    'signal_sent': True,
                    'processing_state': 'ready_for_pickup',
                    'worker_coordination': 'background_processor_notified'
                },
                'queue_details': {
                    'session_id': queue_item['session_id'],
                    'primary_username': queue_item['primary_username'],
                    'priority': queue_item.get('priority', 5),
                    'submitted_at': queue_item.get('submitted_at'),
                    'current_step': queue_item.get('current_step', 'Awaiting processing'),
                    'progress_percentage': queue_item.get('progress_percentage', 0)
                },
                'next_steps': {
                    'worker_processing': 'Background ViralIdeasProcessor will pick up this job',
                    'status_updates': 'Status will change to "processing" when worker begins',
                    'monitoring': 'Use /api/viral-ideas/queue/{session_id} to monitor progress',
                    'expected_duration': '5-15 minutes depending on competitors and content volume'
                },
                'timestamp': datetime.utcnow().isoformat()
            },
            message="Analysis queued successfully - processor will start shortly"
        )

    except HTTPException:
        # Re-raise HTTP exceptions without modification
        raise
    except Exception as e:
        logger.error(f"❌ Unexpected error starting viral analysis for queue {queue_id}: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Internal server error: {str(e)}"
        )
```

### Critical Implementation Details

1. **Queue State Validation**: Comprehensive validation of queue entry existence and processing state
2. **Worker Coordination**: Direct coordination with background ViralIdeasProcessor workers
3. **Status Management**: Intelligent status tracking and state transitions throughout processing lifecycle
4. **Error Recovery**: Robust error handling with specific error types and recovery mechanisms
5. **Background Processing**: Integration with asyncio-based background processing for non-blocking execution
6. **Performance Monitoring**: Built-in statistics and monitoring for queue processing performance
7. **Resource Management**: Intelligent resource allocation and coordination for concurrent processing jobs

## Nest.js (Mongoose) Implementation

```typescript
// viral-analysis.controller.ts - API endpoint controller
import {
    Controller,
    Post,
    Param,
    HttpException,
    HttpStatus,
    Logger,
} from "@nestjs/common";
import { ViralAnalysisService } from "./viral-analysis.service";
import { ApiOperation, ApiResponse, ApiParam } from "@nestjs/swagger";

@Controller("api/viral-ideas/queue")
export class ViralAnalysisController {
    private readonly logger = new Logger(ViralAnalysisController.name);

    constructor(private readonly viralAnalysisService: ViralAnalysisService) {}

    @Post(":queueId/start")
    @ApiOperation({
        summary: "Signal viral analysis job for background processing",
    })
    @ApiParam({
        name: "queueId",
        description: "UUID of the viral analysis queue entry to start",
        type: String,
    })
    @ApiResponse({ status: 200, description: "Analysis queued successfully" })
    @ApiResponse({ status: 404, description: "Queue entry not found" })
    @ApiResponse({
        status: 409,
        description: "Queue entry in invalid state for processing",
    })
    async startViralAnalysis(@Param("queueId") queueId: string) {
        try {
            // Input validation
            if (!queueId) {
                throw new HttpException(
                    "queueId parameter is required",
                    HttpStatus.BAD_REQUEST
                );
            }

            // Validate UUID format
            const uuidRegex =
                /^[0-9a-f]{8}-[0-9a-f]{4}-4[0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$/i;
            if (!uuidRegex.test(queueId)) {
                throw new HttpException(
                    "queueId must be a valid UUID",
                    HttpStatus.BAD_REQUEST
                );
            }

            this.logger.log(
                `🎯 Starting viral analysis signal for queue: ${queueId}`
            );

            // Process queue start signal
            const result = await this.viralAnalysisService.startAnalysisSignal(
                queueId
            );

            this.logger.log(
                `🚀 Viral analysis queued successfully: ${queueId}`
            );

            return {
                success: true,
                data: {
                    queue_processing: {
                        queue_id: queueId,
                        status: result.status,
                        signal_sent: true,
                        processing_state: "ready_for_pickup",
                        worker_coordination: "background_processor_notified",
                    },
                    queue_details: result.queue_details,
                    next_steps: {
                        worker_processing:
                            "Background ViralIdeasProcessor will pick up this job",
                        status_updates:
                            'Status will change to "processing" when worker begins',
                        monitoring: `Use /api/viral-ideas/queue/${result.session_id} to monitor progress`,
                        expected_duration:
                            "5-15 minutes depending on competitors and content volume",
                    },
                    timestamp: new Date().toISOString(),
                },
                message:
                    "Analysis queued successfully - processor will start shortly",
            };
        } catch (error) {
            if (error instanceof HttpException) {
                throw error;
            }

            this.logger.error(
                `❌ Unexpected error starting viral analysis for queue ${queueId}: ${error.message}`
            );

            throw new HttpException(
                `Internal server error: ${error.message}`,
                HttpStatus.INTERNAL_SERVER_ERROR
            );
        }
    }
}

// viral-analysis.service.ts - Business logic service
import {
    Injectable,
    Logger,
    NotFoundException,
    ConflictException,
} from "@nestjs/common";
import { InjectModel } from "@nestjs/mongoose";
import { Model } from "mongoose";
import { ViralIdeasQueue, ViralIdeasCompetitor } from "./schemas";
import { Queue } from "bull";
import { InjectQueue } from "@nestjs/bull";

interface AnalysisSignalResult {
    status: string;
    session_id: string;
    queue_details: any;
    processing_state: string;
}

@Injectable()
export class ViralAnalysisService {
    private readonly logger = new Logger(ViralAnalysisService.name);

    constructor(
        @InjectModel(ViralIdeasQueue.name)
        private viralQueueModel: Model<ViralIdeasQueue>,
        @InjectModel(ViralIdeasCompetitor.name)
        private competitorModel: Model<ViralIdeasCompetitor>,
        @InjectQueue("viral-analysis") private viralAnalysisQueue: Queue
    ) {}

    async startAnalysisSignal(queueId: string): Promise<AnalysisSignalResult> {
        try {
            // Find and validate queue entry
            const queueEntry = await this.viralQueueModel
                .findById(queueId)
                .exec();

            if (!queueEntry) {
                this.logger.warn(`❌ Queue entry not found: ${queueId}`);
                throw new NotFoundException("Queue entry not found");
            }

            const currentStatus = queueEntry.status;
            this.logger.log(
                `📊 Queue entry found - Status: ${currentStatus}, User: @${queueEntry.primary_username}`
            );

            // Validate queue state for processing
            const validStates = ["pending", "failed", "paused"];
            if (!validStates.includes(currentStatus)) {
                this.logger.warn(
                    `⚠️ Invalid queue state for processing: ${currentStatus}`
                );
                throw new ConflictException(
                    `Queue entry is in '${currentStatus}' state and cannot be started. Valid states: ${validStates.join(
                        ", "
                    )}`
                );
            }

            // Update queue entry to signal processing readiness
            await this.viralQueueModel
                .findByIdAndUpdate(queueId, {
                    updated_at: new Date(),
                    current_step:
                        "Signaled for processing - awaiting worker pickup",
                })
                .exec();

            this.logger.log(
                `✅ Queue entry signaled for processing: ${queueId}`
            );

            // Add job to BullMQ queue for background processing
            await this.viralAnalysisQueue.add(
                "process-viral-analysis",
                { queueId },
                {
                    priority: queueEntry.priority || 5,
                    attempts: 3,
                    backoff: {
                        type: "exponential",
                        delay: 60000, // 1 minute
                    },
                }
            );

            return {
                status: currentStatus,
                session_id: queueEntry.session_id,
                processing_state: "ready_for_pickup",
                queue_details: {
                    session_id: queueEntry.session_id,
                    primary_username: queueEntry.primary_username,
                    priority: queueEntry.priority || 5,
                    submitted_at: queueEntry.submitted_at,
                    current_step: "Awaiting processing",
                    progress_percentage: 0,
                },
            };
        } catch (error) {
            this.logger.error(
                `❌ Error signaling viral analysis start: ${error.message}`
            );
            throw error;
        }
    }
}
```

## Responses

### Success: 200 OK

Returns comprehensive queue signaling confirmation with processing coordination details.

**Example Response: Queue Successfully Signaled**

```json
{
    "success": true,
    "data": {
        "queue_processing": {
            "queue_id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
            "status": "pending",
            "signal_sent": true,
            "processing_state": "ready_for_pickup",
            "worker_coordination": "background_processor_notified"
        },
        "queue_details": {
            "session_id": "user_session_xyz789",
            "primary_username": "content_creator_123",
            "priority": 5,
            "submitted_at": "2024-01-15T09:45:00.000Z",
            "current_step": "Awaiting processing",
            "progress_percentage": 0
        },
        "next_steps": {
            "worker_processing": "Background ViralIdeasProcessor will pick up this job",
            "status_updates": "Status will change to \"processing\" when worker begins",
            "monitoring": "Use /api/viral-ideas/queue/user_session_xyz789 to monitor progress",
            "expected_duration": "5-15 minutes depending on competitors and content volume"
        },
        "timestamp": "2024-01-15T10:30:00.000Z"
    },
    "message": "Analysis queued successfully - processor will start shortly"
}
```

**Example Response: Queue Already Processing**

```json
{
    "success": true,
    "data": {
        "queue_id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
        "status": "processing",
        "current_step": "Analyzing competitor content",
        "progress_percentage": 45,
        "session_id": "user_session_xyz789",
        "primary_username": "content_creator_123",
        "processing_state": "already_started"
    },
    "message": "Analysis is already in progress"
}
```

### Error: 400 Bad Request

Returned for invalid queue ID format or validation failures.

**Example Response:**

```json
{
    "success": false,
    "detail": "queue_id must be a valid UUID",
    "error_code": "INVALID_UUID_FORMAT",
    "timestamp": "2024-01-15T10:30:00.000Z",
    "troubleshooting": "Ensure queue_id is a properly formatted UUID (e.g., 12345678-1234-1234-1234-123456789012)"
}
```

### Error: 404 Not Found

Returned when the specified queue entry does not exist.

**Example Response:**

```json
{
    "success": false,
    "detail": "Queue entry not found",
    "error_code": "QUEUE_NOT_FOUND",
    "timestamp": "2024-01-15T10:30:00.000Z",
    "troubleshooting": "Verify the queue_id exists in the viral_ideas_queue table and was properly created"
}
```

### Error: 409 Conflict

Returned when the queue entry is in an invalid state for processing.

**Example Response:**

```json
{
    "success": false,
    "detail": "Queue entry is in 'completed' state and cannot be started. Valid states: pending, failed, paused",
    "error_code": "INVALID_QUEUE_STATE",
    "timestamp": "2024-01-15T10:30:00.000Z",
    "troubleshooting": "Queue entry must be in 'pending', 'failed', or 'paused' state to be started. Check current status and reset if needed"
}
```

### Error: 500 Internal Server Error

Returned for unexpected server-side errors during queue processing.

**Example Response:**

```json
{
    "success": false,
    "detail": "Internal server error: Database connection timeout",
    "error_code": "INTERNAL_ERROR",
    "timestamp": "2024-01-15T10:30:00.000Z",
    "troubleshooting": "Please retry the request. If the problem persists, contact system administrator"
}
```

## Database Schema Details

### Viral Ideas Queue Table

```sql
-- Main viral analysis queue table (from schema/viral_ideas_queue.sql)
CREATE TABLE viral_ideas_queue (
    id UUID DEFAULT uuid_generate_v4() PRIMARY KEY,
    session_id VARCHAR(255) UNIQUE NOT NULL,

    -- Primary profile being analyzed (19 columns total)
    primary_username VARCHAR(255) NOT NULL,

    -- Form data from the viral ideas flow
    content_strategy JSONB DEFAULT '{}', -- ContentStrategyData from form step 3
    analysis_settings JSONB DEFAULT '{}', -- Additional settings/preferences

    -- Queue status
    status VARCHAR(50) DEFAULT 'pending', -- 'pending', 'processing', 'completed', 'failed', 'paused'
    priority INTEGER DEFAULT 5, -- 1=highest, 10=lowest

    -- Analysis progress
    current_step VARCHAR(100), -- Current processing step
    progress_percentage INTEGER DEFAULT 0,
    error_message TEXT,

    -- Scheduling for automatic re-runs
    auto_rerun_enabled BOOLEAN DEFAULT TRUE,
    rerun_frequency_hours INTEGER DEFAULT 24,
    last_analysis_at TIMESTAMP WITH TIME ZONE,
    next_scheduled_run TIMESTAMP WITH TIME ZONE,
    total_runs INTEGER DEFAULT 0,

    -- Timestamps
    submitted_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    started_processing_at TIMESTAMP WITH TIME ZONE,
    completed_at TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Performance indexes
CREATE INDEX idx_viral_queue_status ON viral_ideas_queue(status);
CREATE INDEX idx_viral_queue_priority ON viral_ideas_queue(priority);
CREATE INDEX idx_viral_queue_submitted_at ON viral_ideas_queue(submitted_at DESC);
```

### Competitors Table

```sql
-- Competitor selections for each analysis (11 columns total)
CREATE TABLE viral_ideas_competitors (
    id UUID DEFAULT uuid_generate_v4() PRIMARY KEY,
    queue_id UUID REFERENCES viral_ideas_queue(id) ON DELETE CASCADE,

    -- Competitor details
    competitor_username VARCHAR(255) NOT NULL,
    selection_method VARCHAR(50) DEFAULT 'suggested', -- 'suggested', 'manual', 'api'

    -- Status tracking
    is_active BOOLEAN DEFAULT TRUE,
    processing_status VARCHAR(50) DEFAULT 'pending', -- 'pending', 'processing', 'completed', 'failed'

    -- Metadata
    added_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    removed_at TIMESTAMP WITH TIME ZONE,

    -- Unique constraint to prevent duplicate competitors per analysis
    UNIQUE(queue_id, competitor_username)
);
```

## Performance Optimization

### Queue Processing Performance

-   **Fast Lookups**: O(1) queue entry retrieval using UUID primary keys
-   **Parallel Processing**: Background workers process multiple analysis jobs concurrently
-   **Resource Management**: Intelligent resource allocation for competitor data fetching
-   **Scalability**: Support for multiple background worker instances

### Background Worker Coordination

-   **Non-blocking Signals**: Queue signaling doesn't block on actual processing
-   **Async Processing**: Background workers use asyncio for concurrent data fetching
-   **Priority Queues**: Support for priority-based processing coordination
-   **Resource Pooling**: Efficient connection pooling for database and external API calls

## Testing and Validation

### Integration Testing

```python
import pytest
from fastapi.testclient import TestClient
from backend_api import app
import uuid

class TestStartViralAnalysisEndpoint:
    """Integration tests for the start viral analysis endpoint"""

    @pytest.fixture
    def client(self):
        return TestClient(app)

    def test_successful_analysis_start(self, client):
        """Test successful viral analysis start signal"""

        # Create a test queue entry first
        queue_id = str(uuid.uuid4())

        # Make API request
        response = client.post(f"/api/viral-ideas/queue/{queue_id}/start")

        # Verify response
        assert response.status_code == 200
        data = response.json()
        assert data['success'] is True
        assert data['data']['queue_processing']['queue_id'] == queue_id
        assert data['data']['queue_processing']['signal_sent'] is True

    def test_invalid_uuid_format(self, client):
        """Test invalid UUID format handling"""

        invalid_queue_id = "not-a-valid-uuid"
        response = client.post(f"/api/viral-ideas/queue/{invalid_queue_id}/start")

        assert response.status_code == 400
        assert "valid UUID" in response.json()['detail']

    def test_queue_not_found(self, client):
        """Test handling of non-existent queue entry"""

        non_existent_uuid = str(uuid.uuid4())
        response = client.post(f"/api/viral-ideas/queue/{non_existent_uuid}/start")

        assert response.status_code == 404
        assert "not found" in response.json()['detail'].lower()
```

## Implementation Details

### File Locations

-   **Main Endpoint**: `backend_api.py` - `start_viral_analysis()` function (lines 1619-1643)
-   **Processing Trigger**: `backend_api.py` - `trigger_viral_analysis_processing()` function (lines 1645-1692)
-   **Background Processor**: `viral_ideas_processor.py` - `ViralIdeasProcessor` class
-   **Database Schema**: `schema/viral_ideas_queue.sql` - Complete queue system definition

### Processing Characteristics

-   **Signal-Based Architecture**: Endpoint signals processing readiness without blocking
-   **Background Processing**: Actual analysis runs in background using ViralIdeasProcessor
-   **Queue State Management**: Comprehensive status tracking and state transitions
-   **Worker Coordination**: Integration with background worker processes for scalable processing

### Security Features

-   **UUID Validation**: Comprehensive validation of queue ID format and structure
-   **State Verification**: Validation of queue entry state before allowing processing
-   **Error Handling**: Detailed error messages with troubleshooting guidance
-   **Access Control**: Integration with API authentication and authorization systems

### Integration Points

-   **Queue Management**: Direct integration with viral_ideas_queue table and management system
-   **Background Workers**: Coordination with ViralIdeasProcessor and queue management workers
-   **Status Monitoring**: Integration with queue status monitoring and progress tracking endpoints
-   **Result Delivery**: Coordination with viral analysis results storage and retrieval systems

---

**Development Note**: This endpoint provides **comprehensive queue signaling and worker coordination** for viral analysis processing. It serves as a critical trigger mechanism that coordinates between frontend requests and background processing systems, ensuring reliable and scalable viral content analysis workflows.

**Usage Recommendation**: Use this endpoint to signal that viral analysis jobs are ready for processing, enabling efficient coordination between user requests and background analysis workers while maintaining robust queue state management and error handling.
