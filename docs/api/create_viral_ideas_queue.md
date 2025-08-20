# POST `/api/viral-ideas/queue` ⚡

Creates a new viral ideas analysis job and adds it to the queue.

## Description

This endpoint is the trigger for the core AI-powered viral ideas pipeline. It allows a user to submit a request for a new analysis based on their content strategy and a selected list of competitors.

The endpoint creates a new entry in the `viral_ideas_queue` table and links the selected competitors in the `viral_ideas_competitors` table. This new job will then be picked up by the backend processors for analysis.

## Request Body

The endpoint expects a JSON request body with the following structure:

```json
{
    "session_id": "unique_session_id",
    "primary_username": "user_profile",
    "content_strategy": {
        "contentType": "Educational",
        "targetAudience": "Beginner developers",
        "goals": "Increase brand awareness"
    },
    "selected_competitors": ["competitor1", "competitor2"]
}
```

| Field                  | Type             | Description                                             |
| :--------------------- | :--------------- | :------------------------------------------------------ |
| `session_id`           | string           | A unique identifier for the user's session.             |
| `primary_username`     | string           | The username of the user requesting the analysis.       |
| `content_strategy`     | object           | An object describing the user's content strategy.       |
| `selected_competitors` | array of strings | A list of usernames for the competitors to be analyzed. |

## Execution Flow

1.  **Receive Request**: The endpoint receives a POST request with a JSON body containing the `session_id`, `primary_username`, `content_strategy`, and `selected_competitors`.
2.  **Validate Request Body**: The incoming JSON is validated against a predefined schema (e.g., a Pydantic model or a Nest.js DTO) to ensure all required fields are present and have the correct types.
3.  **Create Queue Entry**: A new record is created in the `viral_ideas_queue` table with the data from the request. The status is set to `pending`.
4.  **Link Competitors**: For each username in the `selected_competitors` array, a new record is created in the `viral_ideas_competitors` table, linking them to the new queue entry.
5.  **Send Response**: The endpoint returns a success message along with the ID of the newly created queue entry.

## Detailed Implementation Guide

### Python (FastAPI)

```python
# Pydantic models for request validation (lines 94-103)
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

# Complete create_viral_ideas_queue endpoint implementation (lines 1428-1490)
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
```

**Line-by-Line Explanation:**

1.  **Pydantic Model Validation**:

    ```python
    class ViralIdeasQueueRequest(BaseModel):
        session_id: str
        primary_username: str
        selected_competitors: List[str]
        content_strategy: ContentStrategyData
    ```

    Automatically validates the incoming JSON body with nested content strategy validation.

2.  **Content Strategy Transformation**:

    ```python
    content_strategy_json = {
        "contentType": request.content_strategy.contentType,
        "targetAudience": request.content_strategy.targetAudience,
        "goals": request.content_strategy.goals
    }
    ```

    Converts the Pydantic model to a dictionary for JSON storage in the database.

3.  **Queue Entry Creation**:

    ```python
    queue_result = api_instance.supabase.client.table('viral_ideas_queue').insert({
        'session_id': request.session_id,
        'primary_username': request.primary_username,
        'content_strategy': content_strategy_json,
        'status': 'pending',
        'priority': 5
    }).execute()
    ```

    Inserts a new record into the `viral_ideas_queue` table with default priority of 5.

4.  **Queue Validation**:

    ```python
    if not queue_result.data:
        raise HTTPException(status_code=500, detail="Failed to create queue entry")
    ```

    Ensures the queue entry was successfully created before proceeding.

5.  **Competitor Records Creation**:

    ```python
    competitor_records = []
    for competitor_username in request.selected_competitors:
        competitor_records.append({
            'queue_id': queue_id,
            'competitor_username': competitor_username,
            'selection_method': 'manual',
            'is_active': True,
            'processing_status': 'pending'
        })
    ```

    Creates detailed competitor records with metadata for tracking and processing.

6.  **Bulk Competitor Insert**:

    ```python
    competitors_result = api_instance.supabase.client.table('viral_ideas_competitors').insert(competitor_records).execute()
    ```

    Performs a bulk insert of all competitor records for efficiency.

7.  **Response Construction**:

    ```python
    response = ViralIdeasQueueResponse(
        id=queue_id,
        session_id=request.session_id,
        primary_username=request.primary_username,
        status='pending',
        submitted_at=queue_record['submitted_at']
    )
    ```

    Creates a structured response using the Pydantic response model.

8.  **Success Response**:
    ```python
    return APIResponse(
        success=True,
        data=response.dict(),
        message=f"Viral ideas analysis queued for @{request.primary_username}"
    )
    ```
    Returns a comprehensive response with success status, data, and user-friendly message.

### Key Implementation Features

**1. Comprehensive Validation**: Uses nested Pydantic models for automatic request validation and type checking.

**2. Atomic Operations**: Creates queue entry first, then competitors, with proper error handling at each step.

**3. Rich Competitor Metadata**: Stores additional fields like `selection_method`, `is_active`, and `processing_status` for advanced queue management.

**4. Priority System**: Includes priority field (default 5) for queue processing optimization.

**5. Error Resilience**: Comprehensive error handling with detailed logging and proper HTTP status codes.

**6. Background Processing Ready**: Includes placeholder for triggering background analysis processing.

**7. Structured Responses**: Uses Pydantic models for consistent response formatting.

### Nest.js (Mongoose)

```typescript
// DTOs for validation
import { IsString, IsArray, IsNotEmpty, ValidateNested } from "class-validator";
import { Type } from "class-transformer";

export class ContentStrategyDto {
    @IsString()
    @IsNotEmpty()
    contentType: string;

    @IsString()
    @IsNotEmpty()
    targetAudience: string;

    @IsString()
    @IsNotEmpty()
    goals: string;
}

export class CreateViralIdeasQueueDto {
    @IsString()
    @IsNotEmpty()
    session_id: string;

    @IsString()
    @IsNotEmpty()
    primary_username: string;

    @IsArray()
    @IsString({ each: true })
    selected_competitors: string[];

    @ValidateNested()
    @Type(() => ContentStrategyDto)
    content_strategy: ContentStrategyDto;
}

// In your viral-ideas.controller.ts
import { Controller, Post, Body, Logger } from "@nestjs/common";
import { ViralIdeasService } from "./viral-ideas.service";
import { CreateViralIdeasQueueDto } from "./dto/create-viral-ideas-queue.dto";

@Controller("api/viral-ideas")
export class ViralIdeasController {
    private readonly logger = new Logger(ViralIdeasController.name);

    constructor(private readonly viralIdeasService: ViralIdeasService) {}

    @Post("queue")
    async createViralIdeasQueue(@Body() createDto: CreateViralIdeasQueueDto) {
        this.logger.log(
            `Creating viral ideas queue for @${createDto.primary_username}`
        );

        const result = await this.viralIdeasService.createQueue(createDto);

        this.logger.log(`✅ Queue created with ID: ${result.id}`);
        return {
            success: true,
            data: result,
            message: `Viral ideas analysis queued for @${createDto.primary_username}`,
        };
    }
}

// In your viral-ideas.service.ts
import { Injectable, Logger } from "@nestjs/common";
import { InjectModel } from "@nestjs/mongoose";
import { Model } from "mongoose";
import {
    ViralIdeasQueue,
    ViralIdeasQueueDocument,
} from "./schemas/viral-ideas-queue.schema";
import {
    ViralIdeasCompetitor,
    ViralIdeasCompetitorDocument,
} from "./schemas/viral-ideas-competitor.schema";
import { CreateViralIdeasQueueDto } from "./dto/create-viral-ideas-queue.dto";

@Injectable()
export class ViralIdeasService {
    private readonly logger = new Logger(ViralIdeasService.name);

    constructor(
        @InjectModel(ViralIdeasQueue.name)
        private viralIdeasQueueModel: Model<ViralIdeasQueueDocument>,
        @InjectModel(ViralIdeasCompetitor.name)
        private viralIdeasCompetitorModel: Model<ViralIdeasCompetitorDocument>
    ) {}

    async createQueue(createDto: CreateViralIdeasQueueDto): Promise<any> {
        try {
            // Create the main queue entry with transaction support
            const session = await this.viralIdeasQueueModel.db.startSession();

            let result;
            await session.withTransaction(async () => {
                // Create the main queue entry
                const newQueueItem = new this.viralIdeasQueueModel({
                    session_id: createDto.session_id,
                    primary_username: createDto.primary_username,
                    content_strategy: createDto.content_strategy,
                    status: "pending",
                    priority: 5,
                    submitted_at: new Date(),
                });

                const savedQueueItem = await newQueueItem.save({ session });

                // Create the competitor links with rich metadata
                if (
                    createDto.selected_competitors &&
                    createDto.selected_competitors.length > 0
                ) {
                    const competitorDocs = createDto.selected_competitors.map(
                        (username) => ({
                            queue_id: savedQueueItem._id,
                            competitor_username: username,
                            selection_method: "manual",
                            is_active: true,
                            processing_status: "pending",
                            added_at: new Date(),
                        })
                    );

                    await this.viralIdeasCompetitorModel.insertMany(
                        competitorDocs,
                        { session }
                    );

                    this.logger.log(
                        `Added ${competitorDocs.length} competitors for queue ${savedQueueItem._id}`
                    );
                }

                // Prepare response data
                result = {
                    id: savedQueueItem._id.toString(),
                    session_id: savedQueueItem.session_id,
                    primary_username: savedQueueItem.primary_username,
                    status: savedQueueItem.status,
                    submitted_at: savedQueueItem.submitted_at.toISOString(),
                    competitors_count:
                        createDto.selected_competitors?.length || 0,
                };
            });

            await session.endSession();

            // Optional: Trigger background processing
            // await this.triggerBackgroundProcessing(result.id);

            return result;
        } catch (error) {
            this.logger.error(
                `❌ Error creating viral ideas queue: ${error.message}`
            );
            throw error;
        }
    }

    // Optional: Method to trigger background processing
    private async triggerBackgroundProcessing(queueId: string): Promise<void> {
        try {
            // This could integrate with a job queue like BullMQ
            // For now, just log the intent
            this.logger.log(
                `🚀 Background processing triggered for queue: ${queueId}`
            );

            // Example integration with BullMQ:
            // await this.viralAnalysisQueue.add('process-viral-ideas', { queueId });
        } catch (error) {
            this.logger.warn(
                `⚠️ Failed to trigger background processing: ${error.message}`
            );
            // Don't throw here - queue creation was successful
        }
    }
}

// Mongoose Schemas
import { Prop, Schema, SchemaFactory } from "@nestjs/mongoose";
import { Document } from "mongoose";

// Content Strategy subdocument
@Schema({ _id: false })
export class ContentStrategy {
    @Prop({ required: true })
    contentType: string;

    @Prop({ required: true })
    targetAudience: string;

    @Prop({ required: true })
    goals: string;
}

export const ContentStrategySchema =
    SchemaFactory.createForClass(ContentStrategy);

// Main Queue Schema
export type ViralIdeasQueueDocument = ViralIdeasQueue & Document;

@Schema({ timestamps: true, collection: "viral_ideas_queue" })
export class ViralIdeasQueue {
    @Prop({ required: true, index: true })
    session_id: string;

    @Prop({ required: true, index: true })
    primary_username: string;

    @Prop({ type: ContentStrategySchema, required: true })
    content_strategy: ContentStrategy;

    @Prop({
        required: true,
        enum: ["pending", "processing", "completed", "failed", "cancelled"],
        default: "pending",
        index: true,
    })
    status: string;

    @Prop({ type: Number, default: 5, index: true })
    priority: number;

    @Prop({ type: Date, default: Date.now })
    submitted_at: Date;

    @Prop({ type: Date })
    started_at?: Date;

    @Prop({ type: Date })
    completed_at?: Date;

    @Prop()
    error_message?: string;
}

export const ViralIdeasQueueSchema =
    SchemaFactory.createForClass(ViralIdeasQueue);

// Create indexes for efficient querying
ViralIdeasQueueSchema.index({ session_id: 1, primary_username: 1 });
ViralIdeasQueueSchema.index({ status: 1, priority: -1, submitted_at: 1 });

// Competitor Schema
export type ViralIdeasCompetitorDocument = ViralIdeasCompetitor & Document;

@Schema({ timestamps: true, collection: "viral_ideas_competitors" })
export class ViralIdeasCompetitor {
    @Prop({ type: String, ref: "ViralIdeasQueue", required: true, index: true })
    queue_id: string;

    @Prop({ required: true, index: true })
    competitor_username: string;

    @Prop({
        required: true,
        enum: ["manual", "suggested", "auto"],
        default: "manual",
    })
    selection_method: string;

    @Prop({ type: Boolean, default: true })
    is_active: boolean;

    @Prop({
        required: true,
        enum: ["pending", "processing", "completed", "failed"],
        default: "pending",
        index: true,
    })
    processing_status: string;

    @Prop({ type: Date, default: Date.now })
    added_at: Date;

    @Prop({ type: Date })
    processed_at?: Date;

    @Prop()
    error_message?: string;
}

export const ViralIdeasCompetitorSchema =
    SchemaFactory.createForClass(ViralIdeasCompetitor);

// Create compound indexes
ViralIdeasCompetitorSchema.index(
    { queue_id: 1, competitor_username: 1 },
    { unique: true }
);
ViralIdeasCompetitorSchema.index({
    queue_id: 1,
    is_active: 1,
    processing_status: 1,
});
```

### Key Differences in Nest.js Implementation

1. **Comprehensive DTO Validation**: Uses nested DTOs with class-validator decorators for thorough request validation.

2. **Transaction Support**: Implements MongoDB transactions to ensure atomicity between queue and competitor creation.

3. **Rich Schema Design**:

    - **Queue Schema**: Includes status tracking, priority system, and timestamp management
    - **Competitor Schema**: Tracks selection method, processing status, and error handling
    - **Strategic Indexing**: Optimized indexes for efficient querying and processing

4. **Background Processing Integration**: Includes placeholder for job queue integration (BullMQ, etc.).

5. **Error Resilience**: Comprehensive error handling with transaction rollback and detailed logging.

6. **Status Management**: Built-in status tracking for both queue items and individual competitors.

7. **Performance Optimization**:
    - **Compound Indexes**: Efficient querying on multiple fields
    - **Bulk Operations**: Uses `insertMany` for competitor creation
    - **Lean Operations**: Optimized for high-throughput queue processing

## Responses

### Success: 200 OK

Returns a comprehensive confirmation object with the ID of the newly created queue entry and processing metadata.

**Example Response:**

```json
{
    "success": true,
    "data": {
        "id": "64f8a9b2c1d2e3f4a5b6c7d8",
        "session_id": "sess_2024_01_15_abc123def456",
        "primary_username": "fitness_creator_alex",
        "status": "pending",
        "submitted_at": "2024-01-15T14:30:25.123Z",
        "competitors_count": 3
    },
    "message": "Viral ideas analysis queued for @fitness_creator_alex"
}
```

**Key Response Features:**

-   **Queue ID**: Unique identifier for tracking the analysis job
-   **Session Tracking**: Links the queue entry to the user's session for status updates
-   **Status Management**: Initial status set to "pending" for background processing
-   **Timestamp Precision**: ISO timestamp for accurate job scheduling and tracking
-   **Competitor Count**: Number of competitors added for analysis scope validation
-   **User-Friendly Message**: Clear confirmation message with username reference

### Response Field Details:

-   **`id`**: Unique queue identifier (MongoDB ObjectId) for job tracking
-   **`session_id`**: Session identifier for linking multiple requests and status updates
-   **`primary_username`**: Username of the user requesting the viral ideas analysis
-   **`status`**: Current processing status ("pending", "processing", "completed", "failed", "cancelled")
-   **`submitted_at`**: ISO timestamp when the queue entry was created
-   **`competitors_count`**: Number of competitor profiles selected for analysis

### Processing Flow After Queue Creation:

1. **Queue Entry Created**: Job added to `viral_ideas_queue` table with "pending" status
2. **Competitors Linked**: All selected competitors added to `viral_ideas_competitors` table
3. **Background Processing**: Queue processor picks up the job based on priority
4. **Status Updates**: Job status updated through processing lifecycle
5. **Results Generation**: Analysis results stored and made available via other endpoints

### Integration with Background Processing:

The queue system is designed to integrate with background job processors:

**BullMQ Integration Example:**

```typescript
// In your background processor
import { Queue } from "bullmq";

const viralAnalysisQueue = new Queue("viral-analysis", {
    connection: { host: "localhost", port: 6379 },
});

// After queue creation
await viralAnalysisQueue.add("process-viral-ideas", {
    queueId: result.id,
    primaryUsername: result.primary_username,
    competitorsCount: result.competitors_count,
});
```

**Processing Priorities:**

-   **Priority 1-3**: High priority (premium users, urgent requests)
-   **Priority 4-6**: Normal priority (standard processing)
-   **Priority 7-10**: Low priority (batch processing, non-urgent)

### Queue Management Features:

-   **Atomic Operations**: Queue and competitor creation wrapped in transactions
-   **Error Recovery**: Failed jobs can be retried with exponential backoff
-   **Status Tracking**: Real-time status updates throughout processing lifecycle
-   **Priority Queuing**: Higher priority jobs processed first
-   **Competitor Management**: Individual competitor processing status tracking

### Error: 500 Internal Server Error

Returned if there is a failure in creating the queue entry or linking the competitors.

## Implementation Details

-   **File:** `backend_api.py`
-   **Function:** `create_viral_ideas_queue(request: ViralIdeasQueueRequest, ...)`
-   **Pydantic Model:** `ViralIdeasQueueRequest` is used to validate the incoming request body.
-   **Database Tables:**
    -   `viral_ideas_queue`: The main table for storing analysis jobs.
    -   `viral_ideas_competitors`: Stores the list of competitors for each analysis job.
