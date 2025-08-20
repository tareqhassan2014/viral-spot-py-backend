# POST `/api/profile/{primary_username}/add-competitor/{target_username}` ⚡

**Manual Competitor Addition with Intelligent Profile Processing and Storage Management**

## Description

The Manual Competitor Addition endpoint provides a comprehensive system for strategically building and managing competitor lists through direct profile addition. This endpoint serves as a critical component of the competitive analysis infrastructure, enabling users to manually curate their competitor landscape by adding specific Instagram profiles to their similar profiles database.

### Key Features

-   **Direct Profile Integration**: Add any Instagram profile as a competitor with comprehensive profile data fetching
-   **Intelligent Duplicate Prevention**: Automatic detection and handling of existing competitor relationships
-   **Advanced Image Management**: Professional profile image downloading, optimization, and CDN-ready storage
-   **Fallback Profile Creation**: Robust handling of API failures with intelligent fallback profile generation
-   **High-Rank Manual Priority**: Manual additions receive priority ranking (999) for strategic competitor positioning
-   **Batch Processing Integration**: Seamless integration with existing profile batch processing workflows
-   **Real-time Storage Optimization**: Supabase bucket storage with automated CDN URL generation

### Primary Use Cases

-   **Strategic Competitor Tracking**: Manually add key competitors for focused analysis and monitoring
-   **Custom Competitor Lists**: Build curated competitor lists beyond algorithmic suggestions
-   **Profile Data Backup**: Ensure competitor profile data availability through local storage caching
-   **Competitive Intelligence**: Add emerging competitors or industry leaders for strategic insights
-   **Manual Profile Recovery**: Add profiles that failed automatic detection or processing
-   **Custom Analysis Workflows**: Support specialized competitor analysis and benchmarking processes

### Competitor Management Pipeline

-   **Profile Validation**: Verify target profile existence and accessibility through external Instagram APIs
-   **Data Acquisition**: Fetch comprehensive profile metadata including usernames, display names, and profile images
-   **Image Processing**: Download, optimize, and store profile images in Supabase storage buckets
-   **Database Integration**: Store competitor relationships in optimized similar_profiles table structure
-   **CDN Distribution**: Generate public URLs for fast profile image delivery through Supabase CDN
-   **Relationship Management**: Establish primary-competitor relationships with appropriate ranking and metadata
-   **Fallback Handling**: Create minimal competitor entries when external API access fails

### Intelligent Storage Management

-   **Bucket Organization**: Organized storage structure in Supabase 'profile-images' bucket with logical paths
-   **CDN Optimization**: Automatic public URL generation for fast profile image delivery
-   **Duplicate Handling**: Smart detection and reuse of existing competitor relationships
-   **Batch Coordination**: Integration with batch processing workflows using unique batch identifiers
-   **Storage Efficiency**: Optimized storage paths and cleanup processes for long-term scalability

## Path Parameters

| Parameter          | Type   | Required | Description                                         |
| :----------------- | :----- | :------- | :-------------------------------------------------- |
| `primary_username` | string | ✅       | The username of the user who is adding a competitor |
| `target_username`  | string | ✅       | The username of the profile to add as a competitor  |

## Execution Flow

1. **Request Validation**: Validate path parameters and ensure proper username formatting (lowercase, @ symbol removal)
2. **Service Availability Check**: Verify SimpleSimilarProfilesAPI service availability and external API connectivity
3. **Duplicate Detection**: Query existing similar_profiles table to identify existing competitor relationships
4. **External Profile Fetching**: Call Instagram API through SimpleSimilarProfilesAPI to retrieve target profile data
5. **Fallback Profile Generation**: Create minimal profile entry if external API fails (username-based display name generation)
6. **Batch ID Assignment**: Generate unique UUID for batch tracking and profile processing coordination
7. **Profile Processing**: Execute comprehensive profile processing including image download and storage management
8. **Database Storage**: Store competitor relationship in similar_profiles table with high manual ranking (999)

## Complete Implementation

### Python (FastAPI) Implementation

```python
# In backend_api.py - Main endpoint handler
@app.post("/api/profile/{primary_username}/add-competitor/{target_username}")
async def add_manual_competitor(
    primary_username: str = Path(..., description="Primary username (the user adding competitors)"),
    target_username: str = Path(..., description="Target username to add as competitor")
):
    """
    Add a specific profile manually to competitors list

    This endpoint:
    - Fetches the target profile's basic info (name, image)
    - Downloads and stores profile image in Supabase bucket
    - Stores profile in similar_profiles table
    - Returns formatted profile data for frontend
    """
    if not SIMPLE_SIMILAR_API_AVAILABLE:
        raise HTTPException(
            status_code=503,
            detail="Simple similar profiles API not available"
        )

    try:
        # Input validation and sanitization
        primary_username = primary_username.lower().strip().replace('@', '')
        target_username = target_username.lower().strip().replace('@', '')

        # Validate username format
        if not primary_username or not target_username:
            raise HTTPException(
                status_code=400,
                detail="Both primary_username and target_username are required"
            )

        if primary_username == target_username:
            raise HTTPException(
                status_code=400,
                detail="Cannot add self as competitor"
            )

        # Username format validation
        if not all(c.isalnum() or c in '._-' for c in primary_username):
            raise HTTPException(
                status_code=400,
                detail="Primary username contains invalid characters"
            )

        if not all(c.isalnum() or c in '._-' for c in target_username):
            raise HTTPException(
                status_code=400,
                detail="Target username contains invalid characters"
            )

        logger.info(f"📝 Manual competitor addition: @{primary_username} adding @{target_username}")

        # Get SimpleSimilarProfilesAPI instance
        similar_api = get_similar_api()

        # Call the comprehensive profile addition method
        result = await similar_api.add_manual_profile(primary_username, target_username)

        # Process successful result
        if result['success']:
            logger.info(f"✅ Successfully added @{target_username} as competitor for @{primary_username}")

            return APIResponse(
                success=True,
                data={
                    'competitor_profile': result['data'],
                    'primary_username': primary_username,
                    'target_username': target_username,
                    'cached': result.get('cached', False),
                    'processing_time': result.get('processing_time', 0),
                    'image_available': bool(result['data'].get('profile_image_url')),
                    'rank': result['data'].get('rank', 999),
                    'batch_id': result.get('batch_id'),
                    'created_at': datetime.utcnow().isoformat()
                },
                message=f"Successfully added @{target_username} as competitor"
            )
        else:
            # Handle specific error cases
            error_message = result.get('error', 'Profile not found or unavailable')

            if 'not found' in error_message.lower():
                logger.warning(f"⚠️ Target profile @{target_username} not found")
                raise HTTPException(
                    status_code=404,
                    detail=f"Profile @{target_username} not found on Instagram"
                )
            elif 'api' in error_message.lower():
                logger.error(f"❌ External API error for @{target_username}: {error_message}")
                raise HTTPException(
                    status_code=502,
                    detail="External Instagram API temporarily unavailable"
                )
            else:
                logger.error(f"❌ Unknown error adding @{target_username}: {error_message}")
                raise HTTPException(
                    status_code=500,
                    detail=f"Failed to add competitor: {error_message}"
                )

    except HTTPException:
        # Re-raise HTTP exceptions without modification
        raise
    except Exception as e:
        logger.error(f"❌ Unexpected error adding manual competitor @{target_username} for @{primary_username}: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Internal server error: {str(e)}"
        )
```

### Critical Implementation Details

1. **Username Normalization**: All usernames are converted to lowercase and @ symbols are removed for consistency
2. **Duplicate Prevention**: Existing competitor relationships are detected and returned without reprocessing
3. **Fallback Profile Creation**: When external APIs fail, intelligent display names are generated from usernames
4. **High Manual Ranking**: Manual additions receive rank 999 for priority positioning in competitor lists
5. **Comprehensive Error Handling**: Specific error types (404, 502, 500) with detailed logging and user feedback
6. **Batch Tracking**: Unique batch IDs enable processing coordination and cache management
7. **CDN Integration**: Profile images are stored in Supabase buckets with automatic public URL generation

## Nest.js (Mongoose) Implementation

```typescript
// competitor.controller.ts - API endpoint controller
import {
    Controller,
    Post,
    Param,
    HttpException,
    HttpStatus,
    Logger,
} from "@nestjs/common";
import { CompetitorService } from "./competitor.service";

@Controller("api/profile")
export class CompetitorController {
    private readonly logger = new Logger(CompetitorController.name);

    constructor(private readonly competitorService: CompetitorService) {}

    @Post(":primary_username/add-competitor/:target_username")
    async addManualCompetitor(
        @Param("primary_username") primaryUsername: string,
        @Param("target_username") targetUsername: string
    ) {
        try {
            // Input validation and sanitization
            const sanitizedPrimary = primaryUsername
                .toLowerCase()
                .replace(/^@/, "")
                .trim();
            const sanitizedTarget = targetUsername
                .toLowerCase()
                .replace(/^@/, "")
                .trim();

            // Validate input parameters
            if (!sanitizedPrimary || !sanitizedTarget) {
                throw new HttpException(
                    "Both primary_username and target_username are required",
                    HttpStatus.BAD_REQUEST
                );
            }

            if (sanitizedPrimary === sanitizedTarget) {
                throw new HttpException(
                    "Cannot add self as competitor",
                    HttpStatus.BAD_REQUEST
                );
            }

            this.logger.log(
                `📝 Manual competitor addition: @${sanitizedPrimary} adding @${sanitizedTarget}`
            );

            // Process competitor addition
            const result = await this.competitorService.addManualCompetitor(
                sanitizedPrimary,
                sanitizedTarget
            );

            this.logger.log(
                `✅ Successfully added @${sanitizedTarget} as competitor for @${sanitizedPrimary}`
            );

            return {
                success: true,
                data: {
                    competitor_profile: result.data,
                    primary_username: sanitizedPrimary,
                    target_username: sanitizedTarget,
                    cached: result.cached,
                    processing_time: result.processing_time,
                    image_available: Boolean(result.data?.profile_image_url),
                    rank: result.data?.rank || 999,
                    batch_id: result.batch_id,
                    created_at: new Date().toISOString(),
                },
                message: `Successfully added @${sanitizedTarget} as competitor`,
            };
        } catch (error) {
            if (error instanceof HttpException) {
                throw error;
            }

            this.logger.error(
                `❌ Error adding manual competitor: ${error.message}`
            );

            // Handle specific error types
            if (error.message.includes("not found")) {
                throw new HttpException(
                    `Profile @${targetUsername} not found on Instagram`,
                    HttpStatus.NOT_FOUND
                );
            } else if (
                error.message.includes("api") ||
                error.message.includes("external")
            ) {
                throw new HttpException(
                    "External Instagram API temporarily unavailable",
                    HttpStatus.BAD_GATEWAY
                );
            }

            throw new HttpException(
                "Internal server error occurred while adding competitor",
                HttpStatus.INTERNAL_SERVER_ERROR
            );
        }
    }
}
```

## Responses

### Success: 200 OK

Returns comprehensive competitor profile data with processing metadata.

**Example Response: Successful Addition**

```json
{
    "success": true,
    "data": {
        "competitor_profile": {
            "username": "competitor_account",
            "name": "Competitor Account",
            "profile_image_url": "https://your-cdn.com/similar/primary_user/competitor_account_profile.jpg",
            "rank": 999,
            "image_available": true,
            "image_downloaded": true,
            "batch_id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
            "created_at": "2024-01-15T10:30:00.000Z"
        },
        "primary_username": "primary_user",
        "target_username": "competitor_account",
        "cached": false,
        "processing_time": 2847.3,
        "image_available": true,
        "rank": 999,
        "batch_id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
        "created_at": "2024-01-15T10:30:00.000Z"
    },
    "message": "Successfully added @competitor_account as competitor"
}
```

**Example Response: Cached Competitor (Already Exists)**

```json
{
    "success": true,
    "data": {
        "competitor_profile": {
            "username": "existing_competitor",
            "name": "Existing Competitor",
            "profile_image_url": "https://your-cdn.com/similar/primary_user/existing_competitor_profile.jpg",
            "rank": 999,
            "image_available": true,
            "image_downloaded": true,
            "batch_id": "b2c3d4e5-f6g7-8901-bcde-f23456789012",
            "created_at": "2024-01-10T14:20:00.000Z"
        },
        "primary_username": "primary_user",
        "target_username": "existing_competitor",
        "cached": true,
        "processing_time": 45.2,
        "image_available": true,
        "rank": 999,
        "batch_id": "b2c3d4e5-f6g7-8901-bcde-f23456789012",
        "created_at": "2024-01-15T10:30:00.000Z"
    },
    "message": "Successfully added @existing_competitor as competitor"
}
```

### Error: 400 Bad Request

Returned for invalid input parameters or validation failures.

**Example Response:**

```json
{
    "success": false,
    "detail": "Cannot add self as competitor",
    "error_code": "SELF_ADDITION_PROHIBITED",
    "timestamp": "2024-01-15T10:30:00.000Z",
    "troubleshooting": "Ensure primary_username and target_username are different valid Instagram usernames"
}
```

### Error: 404 Not Found

Returned when the target profile cannot be found on Instagram.

**Example Response:**

```json
{
    "success": false,
    "detail": "Profile @nonexistent_user not found on Instagram",
    "error_code": "PROFILE_NOT_FOUND",
    "timestamp": "2024-01-15T10:30:00.000Z",
    "troubleshooting": "Verify the username exists on Instagram and is publicly accessible"
}
```

### Error: 502 Bad Gateway

Returned when external Instagram APIs are temporarily unavailable.

**Example Response:**

```json
{
    "success": false,
    "detail": "External Instagram API temporarily unavailable",
    "error_code": "EXTERNAL_API_UNAVAILABLE",
    "timestamp": "2024-01-15T10:30:00.000Z",
    "troubleshooting": "Please retry in a few minutes. The system will use fallback data if available"
}
```

### Error: 503 Service Unavailable

Returned when the SimpleSimilarProfilesAPI service is not available.

**Example Response:**

```json
{
    "success": false,
    "detail": "Simple similar profiles API not available",
    "error_code": "SERVICE_UNAVAILABLE",
    "timestamp": "2024-01-15T10:30:00.000Z",
    "troubleshooting": "Contact system administrator - competitor management service is currently unavailable"
}
```

### Error: 500 Internal Server Error

Returned for unexpected server-side errors during processing.

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

### similar_profiles Table Structure

```sql
-- Similar Profiles Table (optimized for competitor management)
CREATE TABLE similar_profiles (
    id UUID DEFAULT uuid_generate_v4() PRIMARY KEY,
    primary_username VARCHAR(255) NOT NULL, -- The main profile these are similar to
    similar_username VARCHAR(255) NOT NULL, -- The competitor profile's username
    similar_name VARCHAR(255), -- Display name of the competitor profile
    profile_image_path TEXT, -- Storage path in Supabase 'profile-images' bucket
    profile_image_url TEXT, -- CDN URL for the stored image (cached for performance)
    similarity_rank INTEGER DEFAULT 0, -- Order of similarity (999 = manual additions)
    batch_id UUID, -- Groups profiles processed together for cache management

    -- Processing status flags
    image_downloaded BOOLEAN DEFAULT FALSE, -- Track if image is successfully stored locally
    fetch_failed BOOLEAN DEFAULT FALSE, -- Mark profiles that failed to process

    -- Audit timestamps
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),

    -- Prevent duplicate competitor relationships
    UNIQUE(primary_username, similar_username)
);

-- Performance-optimized indexes for competitor operations
CREATE INDEX idx_similar_profiles_primary_username ON similar_profiles(primary_username);
CREATE INDEX idx_similar_profiles_batch_lookup ON similar_profiles(primary_username, similarity_rank, image_downloaded);
CREATE INDEX idx_similar_profiles_batch_id ON similar_profiles(batch_id);
CREATE INDEX idx_similar_profiles_ready_display ON similar_profiles(primary_username, image_downloaded, similarity_rank) WHERE image_downloaded = TRUE;
CREATE INDEX idx_similar_profiles_created_at ON similar_profiles(created_at);
```

## Performance Optimization

### Query Performance

-   **Primary Username Index**: Fast retrieval of all competitors for a specific user
-   **Composite Indexes**: Optimized queries for display-ready profiles with downloaded images
-   **Batch Lookup Index**: Efficient batch operation queries combining multiple criteria
-   **Selective Queries**: Query only necessary fields to minimize data transfer

### Storage Management

-   **Organized Bucket Structure**: Logical folder hierarchy in Supabase storage (`similar/{primary}/{target}_profile.jpg`)
-   **Image Optimization**: Standardized JPEG format with compression for faster loading
-   **CDN Caching**: Public URLs through Supabase CDN for global image delivery
-   **Cleanup Processes**: Temporary file cleanup after successful image processing

### Memory Usage

-   **Streaming Downloads**: Process large profile images without loading entirely into memory
-   **Batch Processing**: Coordinate multiple profile additions efficiently
-   **Connection Pooling**: Reuse database connections for multiple operations
-   **Async Processing**: Non-blocking operations for improved concurrent handling

## Testing and Validation

### Integration Testing

```python
import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch
from backend_api import app

class TestAddManualCompetitor:
    """Comprehensive integration tests for manual competitor addition"""

    @pytest.fixture
    def client(self):
        return TestClient(app)

    def test_successful_competitor_addition(self, client):
        """Test successful addition of new competitor"""

        with patch('simple_similar_profiles_api.SimpleSimilarProfilesAPI.add_manual_profile') as mock_add:
            mock_add.return_value = {
                'success': True,
                'data': {
                    'username': 'test_competitor',
                    'name': 'Test Competitor',
                    'profile_image_url': 'https://cdn.example.com/test_competitor.jpg',
                    'rank': 999,
                    'image_available': True,
                    'image_downloaded': True
                },
                'cached': False,
                'processing_time': 1500.5
            }

            response = client.post("/api/profile/primary_user/add-competitor/test_competitor")

            assert response.status_code == 200
            data = response.json()
            assert data['success'] is True
            assert data['data']['competitor_profile']['username'] == 'test_competitor'
            assert data['data']['cached'] is False

    def test_cached_competitor_response(self, client):
        """Test response when competitor already exists"""

        with patch('simple_similar_profiles_api.SimpleSimilarProfilesAPI.add_manual_profile') as mock_add:
            mock_add.return_value = {
                'success': True,
                'data': {'username': 'existing_competitor'},
                'cached': True,
                'processing_time': 45.2
            }

            response = client.post("/api/profile/primary_user/add-competitor/existing_competitor")

            assert response.status_code == 200
            assert response.json()['data']['cached'] is True

    def test_profile_not_found_error(self, client):
        """Test handling of non-existent profile"""

        with patch('simple_similar_profiles_api.SimpleSimilarProfilesAPI.add_manual_profile') as mock_add:
            mock_add.return_value = {
                'success': False,
                'error': 'Profile not found'
            }

            response = client.post("/api/profile/primary_user/add-competitor/nonexistent_user")

            assert response.status_code == 404
            assert "not found" in response.json()['detail'].lower()

    def test_self_addition_validation(self, client):
        """Test prevention of self-addition as competitor"""

        response = client.post("/api/profile/test_user/add-competitor/test_user")

        assert response.status_code == 400
        assert "cannot add self" in response.json()['detail'].lower()
```

## Implementation Details

### File Locations

-   **Main Endpoint**: `backend_api.py` - `add_manual_competitor()` function (lines 1388-1425)
-   **Core Logic**: `simple_similar_profiles_api.py` - `SimpleSimilarProfilesAPI.add_manual_profile()` method (lines 370-445)
-   **Profile Processing**: `simple_similar_profiles_api.py` - `_process_single_similar_profile()` method (lines 271-329)
-   **Database Schema**: `schema/similar_profiles_table.sql` - Complete table definition and indexes

### Processing Characteristics

-   **Manual Priority**: Rank 999 ensures manual additions appear before algorithmic suggestions
-   **Batch Processing**: UUID-based batch coordination enables efficient processing workflows
-   **Fallback Support**: Intelligent display name generation when external APIs are unavailable
-   **CDN Integration**: Automatic public URL generation for globally distributed profile image delivery

### Security Features

-   **Input Validation**: Comprehensive username format validation and sanitization
-   **Duplicate Prevention**: Database constraints prevent duplicate competitor relationships
-   **Service Availability**: Graceful handling of service dependencies and external API failures
-   **Error Handling**: Specific error types with appropriate HTTP status codes and troubleshooting guidance

---

**Development Note**: This endpoint provides **comprehensive competitor management capabilities** with intelligent profile processing, robust error handling, and optimized storage management. It serves as a critical component for building strategic competitor lists through direct profile addition, supporting both immediate competitor tracking and long-term competitive intelligence workflows.

**Usage Recommendation**: Use this endpoint to strategically build curated competitor lists by adding specific Instagram profiles that are important for competitive analysis, brand monitoring, and market intelligence activities.
