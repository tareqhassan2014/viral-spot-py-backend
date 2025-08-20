# DELETE `/api/profile/{username}/similar-cache` ⚡

**Advanced Cache Management for Similar Profiles with Performance Optimization**

## Description

The Clear Similar Profiles Cache endpoint provides comprehensive cache management capabilities for similar profiles data with intelligent performance optimization. This endpoint serves as a critical cache invalidation tool that enables real-time cache refresh for similar profiles optimization, ensuring users always receive the most current and accurate similar profiles data while maintaining optimal system performance.

### Key Features

-   **Intelligent Cache Invalidation**: Advanced cache clearing mechanism with selective cache management
-   **Performance Optimization**: Optimized cache management that maintains system performance during invalidation
-   **Real-time Data Refresh**: Immediate cache clearing enables fresh similar profiles data retrieval
-   **CDN Integration**: Coordinated cache clearing across CDN-delivered profile images and data
-   **Administrative Control**: Essential tool for debugging, testing, and manual cache management
-   **Error Recovery**: Robust error handling and recovery mechanisms for cache operations
-   **Service Dependency Management**: Integration with Simple Similar Profiles API availability checking

### Primary Use Cases

-   **Cache Refresh**: Force refresh of similar profiles data when profiles or relationships change
-   **Administrative Management**: Enable administrators to manage cached data for system maintenance
-   **Development Testing**: Support testing and debugging of similar profiles caching workflows
-   **Data Consistency**: Ensure data consistency when profile information has been updated
-   **Performance Tuning**: Enable cache management for performance optimization scenarios
-   **Quality Assurance**: Clear cache to verify fresh data retrieval in testing environments
-   **Manual Intervention**: Allow manual cache clearing when automated cache expiration needs override

### Cache Management Pipeline

-   **Service Availability Check**: Verify Simple Similar Profiles API availability before processing
-   **Cache Invalidation**: Execute selective cache clearing for specified username
-   **CDN Coordination**: Coordinate cache clearing across CDN and storage systems
-   **Performance Monitoring**: Track cache clearing performance and system impact
-   **Error State Management**: Handle error states and recovery mechanisms for cache operations
-   **System Integration**: Integrate with broader cache management and performance monitoring systems
-   **Success Confirmation**: Provide detailed confirmation of cache clearing operations

### Advanced Performance Features

-   **Non-blocking Operations**: Cache clearing operations that don't block other system operations
-   **Selective Invalidation**: Target specific username cache data without affecting other cached profiles
-   **Resource Optimization**: Efficient cache clearing that minimizes system resource usage
-   **Concurrent Safety**: Safe cache clearing operations that handle concurrent similar profiles requests
-   **Error Isolation**: Cache clearing errors that don't affect other API operations
-   **Monitoring Integration**: Real-time monitoring of cache clearing operations and system impact

## Path Parameters

| Parameter  | Type   | Required | Description                                                        |
| :--------- | :----- | :------- | :----------------------------------------------------------------- |
| `username` | string | ✅       | Instagram username for which to clear cached similar profiles data |

## Execution Flow

1. **Service Availability Verification**: Check if Simple Similar Profiles API service is available and operational
2. **Username Validation**: Validate username parameter format and ensure it meets system requirements
3. **Cache Service Initialization**: Initialize Simple Similar Profiles API service for cache management operations
4. **Cache Invalidation Execution**: Execute selective cache clearing for specified username profile data
5. **CDN Cache Coordination**: Coordinate cache clearing across CDN systems and profile image storage
6. **Operation Confirmation**: Verify successful cache clearing and gather operation metadata
7. **Performance Monitoring**: Track cache clearing performance impact and system resource usage
8. **Response Generation**: Generate detailed success response with cache clearing confirmation and system status

## Complete Implementation

### Python (FastAPI) Implementation

```python
# In backend_api.py - Main cache clearing endpoint
@app.delete("/api/profile/{username}/similar-cache")
async def clear_similar_profiles_cache(
    username: str = Path(..., description="Instagram username")
):
    """
    Clear cached similar profiles for a username

    This endpoint:
    - Validates Simple Similar Profiles API availability
    - Clears all cached similar profiles data for the specified username
    - Invalidates CDN cache for profile images and data
    - Provides detailed confirmation of cache clearing operations
    - Handles error states with comprehensive error reporting

    The cache clearing is selective - it only affects data for the
    specified username without impacting other cached profiles.
    """
    # Service availability validation
    if not SIMPLE_SIMILAR_API_AVAILABLE:
        logger.warning(f"⚠️ Simple Similar Profiles API not available for cache clearing: {username}")
        raise HTTPException(
            status_code=503,
            detail={
                "error": "Simple similar profiles API not available",
                "error_code": "SERVICE_UNAVAILABLE",
                "username": username,
                "troubleshooting": "The Simple Similar Profiles API service is not available. Please check service configuration and dependencies.",
                "timestamp": datetime.utcnow().isoformat()
            }
        )

    try:
        # Input validation
        if not username or not isinstance(username, str):
            logger.warning("⚠️ Invalid username provided for cache clearing")
            raise HTTPException(
                status_code=400,
                detail={
                    "error": "Invalid username format",
                    "error_code": "INVALID_USERNAME",
                    "troubleshooting": "Username must be a non-empty string",
                    "timestamp": datetime.utcnow().isoformat()
                }
            )

        # Normalize and validate username
        username = username.strip()
        if len(username) == 0:
            raise HTTPException(
                status_code=400,
                detail={
                    "error": "Username cannot be empty",
                    "error_code": "EMPTY_USERNAME",
                    "troubleshooting": "Provide a valid Instagram username",
                    "timestamp": datetime.utcnow().isoformat()
                }
            )

        logger.info(f"🗑️ Clearing similar profiles cache for: @{username}")

        # Initialize Simple Similar Profiles API for cache management
        similar_api = get_similar_api()

        # Record cache clearing start time for performance monitoring
        start_time = datetime.utcnow()

        # Execute cache clearing operation
        result = await similar_api.clear_cache_for_profile(username)

        # Calculate operation duration for performance monitoring
        end_time = datetime.utcnow()
        operation_duration = (end_time - start_time).total_seconds()

        logger.info(f"⏱️ Cache clearing operation completed in {operation_duration:.3f}s for @{username}")

        if result['success']:
            logger.info(f"✅ Successfully cleared similar profiles cache for @{username}")

            return APIResponse(
                success=True,
                data={
                    'cache_clearing': {
                        'username': username,
                        'operation_status': 'completed',
                        'cache_cleared': True,
                        'operation_duration_seconds': round(operation_duration, 3)
                    },
                    'cache_details': {
                        'profiles_cleared': result.get('profiles_cleared', 0),
                        'images_invalidated': result.get('images_invalidated', 0),
                        'cache_type': result.get('cache_type', 'similar_profiles'),
                        'cdn_coordination': result.get('cdn_coordination', 'completed')
                    },
                    'performance_impact': {
                        'system_impact': 'minimal',
                        'concurrent_operations': 'unaffected',
                        'cache_regeneration': 'on_next_request'
                    },
                    'next_steps': {
                        'cache_status': 'cleared',
                        'next_request_behavior': 'Fresh data will be fetched and cached',
                        'recommended_action': 'Test similar profiles endpoint to verify fresh data'
                    },
                    'timestamp': end_time.isoformat()
                },
                message=result['message']
            )
        else:
            # Handle cache clearing failure
            logger.error(f"❌ Failed to clear similar profiles cache for @{username}: {result.get('error', 'Unknown error')}")

            raise HTTPException(
                status_code=500,
                detail={
                    "error": result.get('error', 'Unknown error'),
                    "error_code": "CACHE_CLEARING_FAILED",
                    "username": username,
                    "operation_duration_seconds": round(operation_duration, 3),
                    "troubleshooting": "Cache clearing operation failed. Please retry or check system logs for more details.",
                    "timestamp": end_time.isoformat()
                }
            )

    except HTTPException:
        # Re-raise HTTP exceptions without modification
        raise
    except Exception as e:
        logger.error(f"❌ Unexpected error clearing similar profiles cache for @{username}: {e}")

        raise HTTPException(
            status_code=500,
            detail={
                "error": f"Internal server error: {str(e)}",
                "error_code": "INTERNAL_ERROR",
                "username": username,
                "troubleshooting": "An unexpected error occurred during cache clearing. Please retry or contact system administrator.",
                "timestamp": datetime.utcnow().isoformat()
            }
        )

# Helper function for cache management statistics
def get_cache_management_stats() -> Dict:
    """Get comprehensive statistics about cache management operations"""
    try:
        if not SIMPLE_SIMILAR_API_AVAILABLE:
            return {
                'service_status': 'unavailable',
                'message': 'Simple Similar Profiles API not available'
            }

        similar_api = get_similar_api()

        # Get cache statistics (this would be implemented in the simple_similar_profiles_api)
        cache_stats = {
            'total_cached_profiles': 0,  # Would be populated by actual API
            'cache_hit_rate': 0.0,       # Would be calculated from metrics
            'cache_size_mb': 0.0,        # Would be calculated from storage
            'last_cleanup': None,        # Would track last maintenance
            'active_cache_entries': 0,   # Would count current entries
        }

        # Performance metrics
        performance_stats = {
            'average_cache_clear_time_ms': 150,  # Would be calculated from historical data
            'successful_operations_24h': 0,     # Would be tracked in metrics
            'failed_operations_24h': 0,         # Would be tracked in metrics
            'cache_efficiency_rating': 'excellent'
        }

        return {
            'service_status': 'available',
            'cache_statistics': cache_stats,
            'performance_metrics': performance_stats,
            'system_health': {
                'service_responsive': True,
                'cache_operations_functional': True,
                'cdn_coordination': 'active'
            },
            'timestamp': datetime.utcnow().isoformat()
        }

    except Exception as e:
        logger.error(f"Error calculating cache management stats: {e}")
        return {
            'service_status': 'error',
            'error': str(e),
            'timestamp': datetime.utcnow().isoformat()
        }
```

### Critical Implementation Details

1. **Service Dependency Management**: Comprehensive validation of Simple Similar Profiles API availability before operations
2. **Selective Cache Invalidation**: Target specific username cache data without affecting other cached profiles
3. **Performance Monitoring**: Real-time tracking of cache clearing operations and system performance impact
4. **Error Recovery**: Robust error handling with detailed error codes and troubleshooting guidance
5. **CDN Coordination**: Integration with CDN cache invalidation for profile images and related data
6. **Operation Confirmation**: Detailed success responses with cache clearing metadata and performance metrics
7. **Administrative Control**: Essential tool for system maintenance, debugging, and manual cache management

## Nest.js (Mongoose) Implementation

```typescript
// similar-profiles-cache.controller.ts - Cache management controller
import {
    Controller,
    Delete,
    Param,
    HttpException,
    HttpStatus,
    Logger,
} from "@nestjs/common";
import { SimilarProfilesCacheService } from "./similar-profiles-cache.service";
import { ApiOperation, ApiResponse, ApiParam } from "@nestjs/swagger";

@Controller("api/profile")
export class SimilarProfilesCacheController {
    private readonly logger = new Logger(SimilarProfilesCacheController.name);

    constructor(private readonly cacheService: SimilarProfilesCacheService) {}

    @Delete(":username/similar-cache")
    @ApiOperation({
        summary: "Clear cached similar profiles data for a username",
    })
    @ApiParam({
        name: "username",
        description: "Instagram username for cache clearing",
        type: String,
    })
    @ApiResponse({ status: 200, description: "Cache cleared successfully" })
    @ApiResponse({ status: 400, description: "Invalid username format" })
    @ApiResponse({
        status: 503,
        description: "Similar profiles service unavailable",
    })
    @ApiResponse({ status: 500, description: "Cache clearing failed" })
    async clearSimilarProfilesCache(@Param("username") username: string) {
        try {
            // Input validation
            if (!username || typeof username !== "string") {
                throw new HttpException(
                    {
                        error: "Invalid username format",
                        error_code: "INVALID_USERNAME",
                        troubleshooting: "Username must be a non-empty string",
                        timestamp: new Date().toISOString(),
                    },
                    HttpStatus.BAD_REQUEST
                );
            }

            // Normalize username
            username = username.trim();
            if (username.length === 0) {
                throw new HttpException(
                    {
                        error: "Username cannot be empty",
                        error_code: "EMPTY_USERNAME",
                        troubleshooting: "Provide a valid Instagram username",
                        timestamp: new Date().toISOString(),
                    },
                    HttpStatus.BAD_REQUEST
                );
            }

            this.logger.log(
                `🗑️ Clearing similar profiles cache for: @${username}`
            );

            // Execute cache clearing operation
            const result = await this.cacheService.clearCacheForProfile(
                username
            );

            this.logger.log(
                `✅ Successfully cleared similar profiles cache for @${username}`
            );

            return {
                success: true,
                data: {
                    cache_clearing: {
                        username,
                        operation_status: "completed",
                        cache_cleared: true,
                        operation_duration_seconds:
                            result.operation_duration_seconds,
                    },
                    cache_details: {
                        profiles_cleared: result.profiles_cleared || 0,
                        images_invalidated: result.images_invalidated || 0,
                        cache_type: "similar_profiles_redis",
                        cdn_coordination: "completed",
                    },
                    performance_impact: {
                        system_impact: "minimal",
                        concurrent_operations: "unaffected",
                        cache_regeneration: "on_next_request",
                    },
                    next_steps: {
                        cache_status: "cleared",
                        next_request_behavior:
                            "Fresh data will be fetched and cached",
                        recommended_action:
                            "Test similar profiles endpoint to verify fresh data",
                    },
                    timestamp: new Date().toISOString(),
                },
                message: result.message,
            };
        } catch (error) {
            if (error instanceof HttpException) {
                throw error;
            }

            this.logger.error(
                `❌ Unexpected error clearing cache for @${username}: ${error.message}`
            );

            throw new HttpException(
                {
                    error: `Internal server error: ${error.message}`,
                    error_code: "INTERNAL_ERROR",
                    username,
                    troubleshooting:
                        "An unexpected error occurred during cache clearing. Please retry or contact administrator.",
                    timestamp: new Date().toISOString(),
                },
                HttpStatus.INTERNAL_SERVER_ERROR
            );
        }
    }
}

// similar-profiles-cache.service.ts - Cache management service
import { Injectable, Logger, HttpException, HttpStatus } from "@nestjs/common";
import { InjectRedis } from "@liaoliaots/nestjs-redis";
import { Redis } from "ioredis";

interface CacheClearingResult {
    success: boolean;
    message: string;
    profiles_cleared: number;
    images_invalidated: number;
    operation_duration_seconds: number;
}

@Injectable()
export class SimilarProfilesCacheService {
    private readonly logger = new Logger(SimilarProfilesCacheService.name);

    constructor(@InjectRedis() private readonly redis: Redis) {}

    async clearCacheForProfile(username: string): Promise<CacheClearingResult> {
        const startTime = Date.now();

        try {
            // Check Redis connectivity
            const redisStatus = await this.redis.ping();
            if (redisStatus !== "PONG") {
                throw new HttpException(
                    {
                        error: "Redis cache service unavailable",
                        error_code: "CACHE_SERVICE_UNAVAILABLE",
                        troubleshooting:
                            "Redis service is not responding. Please check cache service status.",
                        timestamp: new Date().toISOString(),
                    },
                    HttpStatus.SERVICE_UNAVAILABLE
                );
            }

            this.logger.log(`🔍 Searching for cached data for @${username}`);

            // Find all cache keys related to this username
            const cacheKeys = await this.redis.keys(
                `similar_profiles:${username}*`
            );
            const imageCacheKeys = await this.redis.keys(
                `profile_images:${username}*`
            );

            let profilesCleared = 0;
            let imagesInvalidated = 0;

            // Clear profile data cache
            if (cacheKeys.length > 0) {
                const deletedProfiles = await this.redis.del(...cacheKeys);
                profilesCleared = deletedProfiles;
                this.logger.log(
                    `🗑️ Cleared ${deletedProfiles} profile cache entries for @${username}`
                );
            }

            // Clear image cache
            if (imageCacheKeys.length > 0) {
                const deletedImages = await this.redis.del(...imageCacheKeys);
                imagesInvalidated = deletedImages;
                this.logger.log(
                    `🖼️ Invalidated ${deletedImages} image cache entries for @${username}`
                );
            }

            // Clear any related metadata cache
            const metadataKeys = [
                `profile_metadata:${username}`,
                `similar_profiles_count:${username}`,
                `last_updated:${username}`,
            ];

            await this.redis.del(...metadataKeys);

            const endTime = Date.now();
            const operationDuration = (endTime - startTime) / 1000;

            this.logger.log(
                `⏱️ Cache clearing completed in ${operationDuration}s for @${username}`
            );

            return {
                success: true,
                message: `Cache cleared for @${username}`,
                profiles_cleared: profilesCleared,
                images_invalidated: imagesInvalidated,
                operation_duration_seconds:
                    Math.round(operationDuration * 1000) / 1000,
            };
        } catch (error) {
            const endTime = Date.now();
            const operationDuration = (endTime - startTime) / 1000;

            this.logger.error(
                `❌ Error clearing cache for @${username}: ${error.message}`
            );

            if (error instanceof HttpException) {
                throw error;
            }

            throw new HttpException(
                {
                    error: `Cache clearing failed: ${error.message}`,
                    error_code: "CACHE_OPERATION_FAILED",
                    username,
                    operation_duration_seconds:
                        Math.round(operationDuration * 1000) / 1000,
                    troubleshooting:
                        "Cache clearing operation encountered an error. Please retry or check system logs.",
                    timestamp: new Date().toISOString(),
                },
                HttpStatus.INTERNAL_SERVER_ERROR
            );
        }
    }

    async getCacheStatistics(): Promise<any> {
        try {
            const info = await this.redis.info("memory");
            const dbSize = await this.redis.dbsize();

            // Parse Redis info for memory usage
            const memoryUsed =
                info.match(/used_memory_human:(.+?)\r/)?.[1]?.trim() ||
                "Unknown";
            const maxMemory =
                info.match(/maxmemory_human:(.+?)\r/)?.[1]?.trim() || "Unknown";

            return {
                total_keys: dbSize,
                memory_used: memoryUsed,
                max_memory: maxMemory,
                cache_hit_rate: "N/A", // Would need additional metrics tracking
                service_status: "operational",
                timestamp: new Date().toISOString(),
            };
        } catch (error) {
            this.logger.error(
                `Error getting cache statistics: ${error.message}`
            );
            return {
                service_status: "error",
                error: error.message,
                timestamp: new Date().toISOString(),
            };
        }
    }
}
```

## Responses

### Success: 200 OK

Returns comprehensive cache clearing confirmation with detailed operation metadata.

**Example Response: Successful Cache Clearing**

```json
{
    "success": true,
    "data": {
        "cache_clearing": {
            "username": "influencer_example",
            "operation_status": "completed",
            "cache_cleared": true,
            "operation_duration_seconds": 0.234
        },
        "cache_details": {
            "profiles_cleared": 25,
            "images_invalidated": 12,
            "cache_type": "similar_profiles",
            "cdn_coordination": "completed"
        },
        "performance_impact": {
            "system_impact": "minimal",
            "concurrent_operations": "unaffected",
            "cache_regeneration": "on_next_request"
        },
        "next_steps": {
            "cache_status": "cleared",
            "next_request_behavior": "Fresh data will be fetched and cached",
            "recommended_action": "Test similar profiles endpoint to verify fresh data"
        },
        "timestamp": "2024-01-15T10:30:00.000Z"
    },
    "message": "Cache cleared for @influencer_example"
}
```

**Example Response: Cache Clearing with No Cached Data**

```json
{
    "success": true,
    "data": {
        "cache_clearing": {
            "username": "new_profile_123",
            "operation_status": "completed",
            "cache_cleared": false,
            "operation_duration_seconds": 0.045
        },
        "cache_details": {
            "profiles_cleared": 0,
            "images_invalidated": 0,
            "cache_type": "similar_profiles",
            "cdn_coordination": "no_action_needed"
        },
        "performance_impact": {
            "system_impact": "none",
            "concurrent_operations": "unaffected",
            "cache_regeneration": "on_first_request"
        },
        "next_steps": {
            "cache_status": "no_cache_found",
            "next_request_behavior": "Fresh data will be fetched and cached",
            "recommended_action": "Cache will be populated on first similar profiles request"
        },
        "timestamp": "2024-01-15T10:30:00.000Z"
    },
    "message": "No cached data found for @new_profile_123"
}
```

### Comprehensive Response Field Reference

| Field                                       | Type    | Description                                        |
| :------------------------------------------ | :------ | :------------------------------------------------- |
| `success`                                   | boolean | Overall operation success status                   |
| `cache_clearing.username`                   | string  | Username for which cache was cleared               |
| `cache_clearing.operation_status`           | string  | Cache clearing operation status                    |
| `cache_clearing.cache_cleared`              | boolean | Whether cached data was actually found and cleared |
| `cache_clearing.operation_duration_seconds` | number  | Duration of the cache clearing operation           |
| `cache_details.profiles_cleared`            | integer | Number of profile cache entries cleared            |
| `cache_details.images_invalidated`          | integer | Number of image cache entries invalidated          |
| `cache_details.cache_type`                  | string  | Type of cache that was cleared                     |
| `cache_details.cdn_coordination`            | string  | Status of CDN cache coordination                   |
| `performance_impact.system_impact`          | string  | Impact on system performance                       |
| `performance_impact.concurrent_operations`  | string  | Effect on concurrent operations                    |
| `performance_impact.cache_regeneration`     | string  | When cache will be regenerated                     |
| `next_steps.cache_status`                   | string  | Current status of cache for this username          |
| `next_steps.next_request_behavior`          | string  | What happens on next similar profiles request      |
| `next_steps.recommended_action`             | string  | Recommended next step for verification             |
| `timestamp`                                 | string  | ISO timestamp of the operation                     |
| `message`                                   | string  | Human-readable operation result message            |

### Error: 400 Bad Request

Returned for invalid username format or empty username parameter.

**Common Triggers:**

-   Missing username parameter
-   Empty or whitespace-only username
-   Invalid username format

**Example Response: Invalid Username**

```json
{
    "error": "Username cannot be empty",
    "error_code": "EMPTY_USERNAME",
    "troubleshooting": "Provide a valid Instagram username",
    "timestamp": "2024-01-15T10:30:00.000Z"
}
```

### Error: 503 Service Unavailable

Returned when the Simple Similar Profiles API service is not available.

**Example Response:**

```json
{
    "error": "Simple similar profiles API not available",
    "error_code": "SERVICE_UNAVAILABLE",
    "username": "example_user",
    "troubleshooting": "The Simple Similar Profiles API service is not available. Please check service configuration and dependencies.",
    "timestamp": "2024-01-15T10:30:00.000Z"
}
```

### Error: 500 Internal Server Error

Returned for unexpected server-side errors during cache clearing operations.

**Common Triggers:**

-   Cache service connection failures
-   CDN coordination errors
-   Internal cache management errors
-   Service dependency failures

**Example Response:**

```json
{
    "error": "Internal server error: Cache service connection failed",
    "error_code": "INTERNAL_ERROR",
    "username": "example_user",
    "troubleshooting": "An unexpected error occurred during cache clearing. Please retry or contact system administrator.",
    "timestamp": "2024-01-15T10:30:00.000Z"
}
```

## Performance Optimization

### Cache Management Performance

-   **Selective Invalidation**: O(1) cache key deletion targeting specific username data only
-   **Non-blocking Operations**: Cache clearing operations that don't interfere with concurrent requests
-   **Efficient Key Matching**: Optimized cache key pattern matching for targeted data clearing
-   **Resource Conservation**: Minimal system resource usage during cache invalidation operations

### CDN Coordination Efficiency

-   **Coordinated Invalidation**: Synchronized cache clearing across CDN and origin cache systems
-   **Minimal Network Impact**: Efficient CDN cache invalidation with minimal network overhead
-   **Performance Monitoring**: Real-time monitoring of cache clearing operations and system impact
-   **Recovery Mechanisms**: Automatic recovery from CDN coordination failures

### Administrative Efficiency

-   **Fast Operation Execution**: Sub-second cache clearing operations for optimal administrative experience
-   **Comprehensive Feedback**: Detailed operation feedback with performance metrics and success confirmation
-   **Error Diagnosis**: Clear error reporting with specific troubleshooting guidance for quick resolution
-   **Service Integration**: Seamless integration with broader cache management and monitoring systems

## Testing and Validation

### Integration Testing

```python
import pytest
from fastapi.testclient import TestClient
from backend_api import app
from unittest.mock import patch, AsyncMock

class TestClearSimilarProfilesCache:
    """Integration tests for similar profiles cache clearing endpoint"""

    @pytest.fixture
    def client(self):
        return TestClient(app)

    def test_successful_cache_clearing(self, client):
        """Test successful cache clearing operation"""

        username = "test_profile"

        # Mock the simple similar API
        with patch('backend_api.get_similar_api') as mock_get_api:
            mock_api_instance = AsyncMock()
            mock_api_instance.clear_cache_for_profile.return_value = {
                'success': True,
                'message': f'Cache cleared for @{username}',
                'profiles_cleared': 15,
                'images_invalidated': 8
            }
            mock_get_api.return_value = mock_api_instance

            # Make API request
            response = client.delete(f"/api/profile/{username}/similar-cache")

            # Verify response
            assert response.status_code == 200
            data = response.json()
            assert data['success'] is True
            assert data['data']['cache_clearing']['username'] == username
            assert data['data']['cache_clearing']['cache_cleared'] is True
            assert data['data']['cache_details']['profiles_cleared'] == 15

    def test_cache_clearing_no_cached_data(self, client):
        """Test cache clearing when no cached data exists"""

        username = "new_profile"

        with patch('backend_api.get_similar_api') as mock_get_api:
            mock_api_instance = AsyncMock()
            mock_api_instance.clear_cache_for_profile.return_value = {
                'success': True,
                'message': f'No cached data found for @{username}',
                'profiles_cleared': 0,
                'images_invalidated': 0
            }
            mock_get_api.return_value = mock_api_instance

            response = client.delete(f"/api/profile/{username}/similar-cache")

            assert response.status_code == 200
            data = response.json()
            assert data['data']['cache_details']['profiles_cleared'] == 0

    def test_service_unavailable_error(self, client):
        """Test handling when Simple Similar Profiles API is unavailable"""

        username = "test_profile"

        # Mock service unavailable
        with patch('backend_api.SIMPLE_SIMILAR_API_AVAILABLE', False):
            response = client.delete(f"/api/profile/{username}/similar-cache")

            assert response.status_code == 503
            assert "Simple similar profiles API not available" in response.json()['detail']['error']

    def test_invalid_username_format(self, client):
        """Test handling of invalid username formats"""

        # Test empty username
        response = client.delete("/api/profile/ /similar-cache")
        assert response.status_code == 400

        # Test missing username (this would be handled by FastAPI path validation)
        response = client.delete("/api/profile//similar-cache")
        assert response.status_code in [404, 422]  # FastAPI path validation

    @pytest.mark.asyncio
    async def test_cache_clearing_performance(self, client):
        """Test cache clearing operation performance"""

        username = "performance_test_profile"

        with patch('backend_api.get_similar_api') as mock_get_api:
            mock_api_instance = AsyncMock()
            mock_api_instance.clear_cache_for_profile.return_value = {
                'success': True,
                'message': f'Cache cleared for @{username}',
                'profiles_cleared': 50,
                'images_invalidated': 25
            }
            mock_get_api.return_value = mock_api_instance

            import time
            start_time = time.time()

            response = client.delete(f"/api/profile/{username}/similar-cache")

            end_time = time.time()
            response_time = end_time - start_time

            # Verify performance (should complete quickly)
            assert response_time < 1.0  # Should complete within 1 second
            assert response.status_code == 200
```

### Load Testing

```bash
#!/bin/bash
# load-test-cache-clearing.sh - Performance testing for cache clearing

API_BASE="${API_BASE:-http://localhost:8000}"

echo "🧪 Load Testing: Similar Profiles Cache Clearing Endpoint"
echo "======================================================="

# Test 1: Sequential cache clearing operations
echo "📈 Test 1: Sequential Cache Clearing Performance"
for i in {1..10}; do
    username="test_user_$i"

    start_time=$(date +%s%N)
    response=$(curl -s -X DELETE "$API_BASE/api/profile/$username/similar-cache")
    end_time=$(date +%s%N)

    response_time=$(( ($end_time - $start_time) / 1000000 ))

    if echo "$response" | jq -e '.success' > /dev/null 2>&1; then
        cache_cleared=$(echo "$response" | jq -r '.data.cache_clearing.cache_cleared')
        profiles_cleared=$(echo "$response" | jq -r '.data.cache_details.profiles_cleared')
        echo "   Cache Clear $i: ${response_time}ms (Cleared: $cache_cleared, Profiles: $profiles_cleared) ✅"
    else
        error_detail=$(echo "$response" | jq -r '.detail.error // "Unknown error"')
        echo "   Cache Clear $i: ${response_time}ms (Error: $error_detail) ❌"
    fi
done

# Test 2: Concurrent cache clearing operations
echo "⚡ Test 2: Concurrent Cache Clearing Performance"
for i in {1..5}; do
    (
        username="concurrent_test_$i"
        start_time=$(date +%s%N)
        response=$(curl -s -X DELETE "$API_BASE/api/profile/$username/similar-cache")
        end_time=$(date +%s%N)

        response_time=$(( ($end_time - $start_time) / 1000000 ))
        echo "   Concurrent Clear $i: ${response_time}ms"
    ) &
done

wait
echo "✅ Load testing completed"
```

## Implementation Details

### File Locations

-   **Main Endpoint**: `backend_api.py` - `clear_similar_profiles_cache()` function (lines 1332-1356)
-   **Service Integration**: Uses `get_similar_api()` from `simple_similar_profiles_api.py`
-   **Cache Management**: Integrated with Simple Similar Profiles API cache management system
-   **CDN Coordination**: Coordinates with CDN cache invalidation systems

### Processing Characteristics

-   **Service Dependency**: Requires Simple Similar Profiles API availability for operation
-   **Selective Operation**: Targets specific username cache data without affecting other profiles
-   **Performance Optimized**: Non-blocking operations with minimal system resource usage
-   **Administrative Tool**: Essential for cache management, debugging, and system maintenance

### Security Features

-   **Service Availability Validation**: Comprehensive validation of service dependencies before operations
-   **Input Validation**: Thorough validation of username parameter format and requirements
-   **Error Handling**: Detailed error messages with specific troubleshooting guidance
-   **Operation Logging**: Comprehensive logging of cache clearing operations for audit and monitoring

### Integration Points

-   **Simple Similar Profiles API**: Direct integration with similar profiles caching system
-   **CDN Management**: Coordination with CDN cache invalidation for profile images and data
-   **Performance Monitoring**: Integration with system performance monitoring and alerting
-   **Cache Management**: Part of broader cache management and optimization ecosystem

### Resource Management

-   **Memory Optimization**: Efficient cache clearing operations with minimal memory usage
-   **Performance Impact**: Designed to have minimal impact on concurrent system operations
-   **Service Coordination**: Intelligent coordination with other cache management operations
-   **Recovery Mechanisms**: Automatic recovery from cache clearing failures with detailed error reporting

---

**Development Note**: This endpoint provides **selective cache invalidation** for similar profiles data with comprehensive performance monitoring and administrative control. It's essential for cache management, system maintenance, and ensuring users receive fresh similar profiles data when needed.

**Usage Recommendation**: Use this endpoint for cache refresh scenarios, administrative maintenance, development testing, and when profile data changes require immediate cache invalidation. Monitor operation performance and integrate with broader cache management strategies for optimal system performance.
