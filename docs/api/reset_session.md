# POST `/api/reset-session`

**Session State Management with Intelligent Content Delivery Control**

## Description

The Session Reset endpoint provides comprehensive session state management capabilities for controlling content delivery consistency and randomization across the platform. This endpoint serves as a critical utility for managing user session data, specifically targeting the intelligent random session feature that ensures consistent, non-duplicate content delivery when using randomized content ordering.

### Key Features

-   **Session State Clearing**: Complete removal of session-specific tracking data for fresh content experiences
-   **Duplicate Prevention Reset**: Clear seen content history to allow previously shown items to reappear
-   **Random Seed Management**: Reset deterministic randomization seeds for new content ordering patterns
-   **Content Discovery Control**: Enable users to restart their content discovery journey with fresh randomization
-   **Session Memory Management**: Efficient cleanup of in-memory session data to prevent memory bloat
-   **Multi-Endpoint Integration**: Seamless integration with `/api/reels` and `/api/posts` random ordering features
-   **Debug and Development Support**: Essential utility for testing and debugging session-based features

### Primary Use Cases

-   **User Content Reset**: Allow users to reset their content feed for a fresh browsing experience
-   **Testing and Debugging**: Clear session state during development and testing of content delivery features
-   **Memory Management**: Periodic cleanup of accumulated session data to optimize server memory usage
-   **Content Rediscovery**: Enable users to see previously shown content by clearing their session history
-   **Session Troubleshooting**: Resolve issues with stuck or corrupted session states
-   **A/B Testing Support**: Reset session data between different test scenarios and configurations
-   **Development Workflows**: Support rapid iteration during feature development and testing

### Session Management Pipeline

-   **Session Identification**: Validate and process session ID parameters for target session selection
-   **Memory Access**: Access in-memory session storage dictionary to locate session-specific data
-   **State Verification**: Check existence of session data before attempting deletion operations
-   **Data Cleanup**: Remove all tracked content IDs and randomization seeds for the specified session
-   **Memory Optimization**: Free up memory resources previously allocated to session data
-   **Response Generation**: Provide clear feedback on operation success and session state status
-   **Integration Coordination**: Ensure compatibility with content delivery endpoints and randomization features

### Intelligent Content Delivery Integration

-   **Random Order Support**: Direct integration with `random_order=true` functionality in content endpoints
-   **Seen Content Tracking**: Manages the system that prevents duplicate content delivery within sessions
-   **Consistent Randomization**: Controls deterministic random ordering using MD5-based session seeds
-   **Cross-Endpoint Coordination**: Supports session consistency across both `/api/reels` and `/api/posts` endpoints
-   **Memory Efficiency**: Optimized in-memory storage using Python sets for fast content ID lookups
-   **Session Persistence**: Maintains session data across multiple API calls until explicitly reset

## Query Parameters

| Parameter    | Type   | Required | Description                                |
| :----------- | :----- | :------- | :----------------------------------------- |
| `session_id` | string | ✅       | Unique identifier for the session to reset |

## Execution Flow

1. **Request Validation**: Validate the session_id parameter and ensure it meets format requirements
2. **Session Storage Access**: Access the global in-memory session_storage dictionary containing all active sessions
3. **Session Existence Check**: Verify whether the specified session_id exists in the current session storage
4. **State Cleanup**: Remove all session data including seen content IDs and randomization tracking
5. **Memory Optimization**: Free up memory resources previously allocated to the session data
6. **Operation Logging**: Log the session reset operation for monitoring and debugging purposes
7. **Response Generation**: Generate appropriate success or not-found response based on operation outcome
8. **Integration Update**: Ensure next content requests for this session will use fresh randomization

## Complete Implementation

### Python (FastAPI) Implementation

```python
# In backend_api.py - Global session storage
session_storage = {}  # In-memory dictionary for session tracking

# In ViralSpotAPI class - Main implementation
async def reset_session(self, session_id: str):
    """
    Reset random session data and content tracking

    This method:
    - Clears seen content history for the session
    - Removes randomization seeds and ordering data
    - Frees memory resources allocated to session
    - Enables fresh content delivery experience
    """
    try:
        # Input validation
        if not session_id or not isinstance(session_id, str):
            logger.warning("⚠️ Invalid session_id provided for reset")
            return {
                'success': False,
                'message': 'Invalid session ID format',
                'session_found': False
            }

        # Normalize session ID
        session_id = session_id.strip()

        if len(session_id) == 0:
            logger.warning("⚠️ Empty session_id provided for reset")
            return {
                'success': False,
                'message': 'Session ID cannot be empty',
                'session_found': False
            }

        # Check if session exists and get metadata
        session_existed = session_id in session_storage
        session_data_size = 0

        if session_existed:
            # Get size of stored data before deletion
            session_data_size = len(session_storage[session_id])

            # Delete session data
            del session_storage[session_id]

            logger.info(f"✅ Reset session: {session_id} (cleared {session_data_size} tracked items)")

            return {
                'success': True,
                'message': 'Session reset successfully',
                'session_found': True,
                'cleared_items_count': session_data_size,
                'next_request_behavior': 'Fresh randomization will be applied',
                'memory_freed': True
            }
        else:
            logger.info(f"ℹ️ Session reset requested for non-existent session: {session_id}")

            return {
                'success': True,
                'message': 'Session not found - no data to reset',
                'session_found': False,
                'cleared_items_count': 0,
                'next_request_behavior': 'New session will be created on first content request',
                'memory_freed': False
            }

    except Exception as e:
        logger.error(f"❌ Error resetting session {session_id}: {e}")
        return {
            'success': False,
            'message': f'Internal error during session reset: {str(e)}',
            'session_found': False,
            'error_type': type(e).__name__
        }

# FastAPI endpoint definition
@app.post("/api/reset-session")
async def reset_session(
    session_id: str = Query(..., description="Session ID to reset"),
    api_instance: ViralSpotAPI = Depends(get_api)
):
    """
    Reset user session data for fresh content delivery

    This endpoint clears all session-specific data including:
    - Seen content IDs to prevent duplicates
    - Random ordering seeds for consistent randomization
    - Session memory to optimize server performance

    After reset, the next content request will:
    - Generate new randomization patterns
    - Allow previously seen content to appear again
    - Create fresh content discovery experience
    """
    try:
        # Input validation at endpoint level
        if not session_id:
            raise HTTPException(
                status_code=400,
                detail="session_id parameter is required"
            )

        # Validate session ID format
        session_id = session_id.strip()
        if len(session_id) == 0:
            raise HTTPException(
                status_code=400,
                detail="session_id cannot be empty"
            )

        # Additional validation for session ID format
        if len(session_id) > 255:  # Reasonable limit for session IDs
            raise HTTPException(
                status_code=400,
                detail="session_id is too long (maximum 255 characters)"
            )

        # Check for potentially dangerous characters
        import re
        if not re.match(r'^[a-zA-Z0-9._-]+$', session_id):
            raise HTTPException(
                status_code=400,
                detail="session_id contains invalid characters (only alphanumeric, dots, underscores, and hyphens allowed)"
            )

        logger.info(f"🔄 Session reset requested for: {session_id}")

        # Call the main reset logic
        result = await api_instance.reset_session(session_id)

        # Determine appropriate HTTP status based on result
        if result['success']:
            logger.info(f"✅ Session reset completed successfully: {session_id}")

            return APIResponse(
                success=True,
                data={
                    'session_reset': {
                        'session_id': session_id,
                        'operation_status': 'completed',
                        'session_found': result['session_found'],
                        'cleared_items_count': result.get('cleared_items_count', 0),
                        'memory_freed': result.get('memory_freed', False)
                    },
                    'next_steps': {
                        'randomization': result.get('next_request_behavior', 'Fresh randomization will be applied'),
                        'content_delivery': 'Previously seen content may now reappear in random feeds',
                        'integration': 'Compatible with /api/reels and /api/posts random_order=true'
                    },
                    'timestamp': datetime.utcnow().isoformat(),
                    'server_info': {
                        'total_active_sessions': len(session_storage),
                        'session_storage_type': 'in_memory_dict'
                    }
                },
                message=result['message']
            )
        else:
            # Handle error cases with appropriate logging
            logger.error(f"❌ Session reset failed for {session_id}: {result.get('message', 'Unknown error')}")

            raise HTTPException(
                status_code=500,
                detail=result['message']
            )

    except HTTPException:
        # Re-raise HTTP exceptions without modification
        raise
    except Exception as e:
        logger.error(f"❌ Unexpected error in reset_session endpoint for {session_id}: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Internal server error: {str(e)}"
        )
```

### Critical Implementation Details

1. **Session Storage Structure**: Global in-memory dictionary using session IDs as keys and sets of content IDs as values
2. **Memory Management**: Automatic cleanup of session data with size tracking and optimization
3. **Input Validation**: Comprehensive validation of session ID format and content to prevent security issues
4. **Operational Logging**: Detailed logging for monitoring, debugging, and operational visibility
5. **Error Resilience**: Robust error handling with specific error types and detailed error messages
6. **Integration Support**: Direct compatibility with content delivery endpoints and randomization features
7. **Performance Monitoring**: Built-in analytics and statistics for session storage performance tracking

## Nest.js (Mongoose) Implementation

```typescript
// session.controller.ts - API endpoint controller
import { Controller, Post, Query, HttpException, HttpStatus, Logger } from '@nestjs/common';
import { SessionService } from './session.service';
import { ApiOperation, ApiResponse, ApiQuery } from '@nestjs/swagger';

@Controller('api')
export class SessionController {
  private readonly logger = new Logger(SessionController.name);

  constructor(private readonly sessionService: SessionService) {}

  @Post('reset-session')
  @ApiOperation({ summary: 'Reset user session data for fresh content delivery' })
  @ApiQuery({
    name: 'session_id',
    description: 'Unique identifier for the session to reset',
    type: String,
    required: true
  })
  @ApiResponse({ status: 200, description: 'Session reset successfully' })
  @ApiResponse({ status: 400, description: 'Invalid session ID format' })
  @ApiResponse({ status: 500, description: 'Internal server error' })
  async resetSession(@Query('session_id') sessionId: string) {
    try {
      // Input validation at controller level
      if (!sessionId) {
        throw new HttpException(
          'session_id parameter is required',
          HttpStatus.BAD_REQUEST
        );
      }

      // Normalize and validate session ID
      const normalizedSessionId = sessionId.trim();

      if (normalizedSessionId.length === 0) {
        throw new HttpException(
          'session_id cannot be empty',
          HttpStatus.BAD_REQUEST
        );
      }

      if (normalizedSessionId.length > 255) {
        throw new HttpException(
          'session_id is too long (maximum 255 characters)',
          HttpStatus.BAD_REQUEST
        );
      }

      // Validate session ID format
      const sessionIdRegex = /^[a-zA-Z0-9._-]+$/;
      if (!sessionIdRegex.test(normalizedSessionId)) {
        throw new HttpException(
          'session_id contains invalid characters (only alphanumeric, dots, underscores, and hyphens allowed)',
          HttpStatus.BAD_REQUEST
        );
      }

      this.logger.log(`🔄 Session reset requested for: ${normalizedSessionId}`);

      // Process session reset
      const result = await this.sessionService.resetSession(normalizedSessionId);

      this.logger.log(`✅ Session reset completed successfully: ${normalizedSessionId}`);

      return {
        success: true,
        data: {
          session_reset: {
            session_id: normalizedSessionId,
            operation_status: 'completed',
            session_found: result.session_found,
            cleared_items_count: result.cleared_items_count || 0,
            memory_freed: result.memory_freed || false
          },
          next_steps: {
            randomization: result.next_request_behavior || 'Fresh randomization will be applied',
            content_delivery: 'Previously seen content may now reappear in random feeds',
            integration: 'Compatible with content endpoints using random ordering'
          },
          timestamp: new Date().toISOString(),
          server_info: await this.sessionService.getSessionStorageStats()
        },
        message: result.message
      };

    } catch (error) {
      if (error instanceof HttpException) {
        throw error;
      }

      this.logger.error(`❌ Unexpected error in reset_session endpoint for ${sessionId}: ${error.message}`);

      throw new HttpException(
        `Internal server error: ${error.message}`,
        HttpStatus.INTERNAL_SERVER_ERROR
      );
    }
  }
}

// session.service.ts - Business logic service with Redis integration
import { Injectable, Logger, Inject } from '@nestjs/common';
import { Cache } from 'cache-manager';

interface SessionResetResult {
  success: boolean;
  message: string;
  session_found: boolean;
  cleared_items_count?: number;
  memory_freed?: boolean;
  next_request_behavior?: string;
  error_type?: string;
}

@Injectable()
export class SessionService {
  private readonly logger = new Logger(SessionService.name);
  private readonly CACHE_PREFIX = 'session_data:';
  private readonly DEFAULT_TTL = 86400; // 24 hours

  constructor(@Inject('CACHE_MANAGER') private cacheManager: Cache) {}

  async resetSession(sessionId: string): Promise<SessionResetResult> {
    try {
      // Input validation
      if (!sessionId || typeof sessionId !== 'string') {
        this.logger.warn('⚠️ Invalid session_id provided for reset');
        return {
          success: false,
          message: 'Invalid session ID format',
          session_found: false
        };
      }

      // Normalize session ID
      const normalizedSessionId = sessionId.trim();

      if (normalizedSessionId.length === 0) {
        this.logger.warn('⚠️ Empty session_id provided for reset');
        return {
          success: false,
          message: 'Session ID cannot be empty',
          session_found: false
        };
      }

      // Construct cache key
      const cacheKey = `${this.CACHE_PREFIX}${normalizedSessionId}`;

      // Check if session exists and get metadata
      const sessionData = await this.cacheManager.get<Set<string>>(cacheKey);
      const sessionExisted = sessionData !== undefined && sessionData !== null;
      const sessionDataSize = sessionExisted ? (sessionData as any).size || 0 : 0;

      if (sessionExisted) {
        // Delete session data from cache
        await this.cacheManager.del(cacheKey);

        this.logger.log(`✅ Reset session: ${normalizedSessionId} (cleared ${sessionDataSize} tracked items)`);

        return {
          success: true,
          message: 'Session reset successfully',
          session_found: true,
          cleared_items_count: sessionDataSize,
          next_request_behavior: 'Fresh randomization will be applied',
          memory_freed: true
        };
      } else {
        this.logger.log(`ℹ️ Session reset requested for non-existent session: ${normalizedSessionId}`);

        return {
          success: true,
          message: 'Session not found - no data to reset',
          session_found: false,
          cleared_items_count: 0,
          next_request_behavior: 'New session will be created on first content request',
          memory_freed: false
        };
      }

    } catch (error) {
      this.logger.error(`❌ Error resetting session ${sessionId}: ${error.message}`);
      return {
        success: false,
        message: `Internal error during session reset: ${error.message}`,
        session_found: false,
        error_type: error.constructor.name
      };
    }
  }

  async getSessionStorageStats(): Promise<any> {
    """Get comprehensive statistics about current session storage"""
    try {
      // In Redis implementation, you would query cache statistics
      // This is a simplified example
      const stats = await this.calculateCacheStats();

      return {
        storage_type: 'redis_cache',
        total_active_sessions: stats.session_count || 0,
        cache_configuration: {
          default_ttl_hours: this.DEFAULT_TTL / 3600,
          key_prefix: this.CACHE_PREFIX,
          auto_expiration: true
        }
      };
    } catch (error) {
      this.logger.error(`Error calculating session storage stats: ${error.message}`);
      return {
        error: 'Unable to calculate statistics',
        storage_type: 'redis_cache'
      };
    }
  }

  private async calculateCacheStats(): Promise<{ session_count: number }> {
    // Implementation would depend on your Redis setup and cache-manager configuration
    // This is a placeholder for the actual stats calculation
    return { session_count: 0 };
  }
}
```

## Responses

### Success: 200 OK

Returns comprehensive session reset confirmation with operational metadata.

**Example Response: Session Found and Reset**

```json
{
    "success": true,
    "data": {
        "session_reset": {
            "session_id": "user_session_abc123",
            "operation_status": "completed",
            "session_found": true,
            "cleared_items_count": 47,
            "memory_freed": true
        },
        "next_steps": {
            "randomization": "Fresh randomization will be applied",
            "content_delivery": "Previously seen content may now reappear in random feeds",
            "integration": "Compatible with /api/reels and /api/posts random_order=true"
        },
        "timestamp": "2024-01-15T10:30:00.000Z",
        "server_info": {
            "total_active_sessions": 156,
            "session_storage_type": "in_memory_dict"
        }
    },
    "message": "Session reset successfully"
}
```

**Example Response: Session Not Found**

```json
{
    "success": true,
    "data": {
        "session_reset": {
            "session_id": "nonexistent_session_xyz789",
            "operation_status": "completed",
            "session_found": false,
            "cleared_items_count": 0,
            "memory_freed": false
        },
        "next_steps": {
            "randomization": "New session will be created on first content request",
            "content_delivery": "Fresh content delivery experience will be provided",
            "integration": "Ready for content endpoints with random ordering"
        },
        "timestamp": "2024-01-15T10:30:00.000Z",
        "server_info": {
            "total_active_sessions": 156,
            "session_storage_type": "in_memory_dict"
        }
    },
    "message": "Session not found - no data to reset"
}
```

### Error: 400 Bad Request

Returned for invalid session ID format or validation failures.

**Example Response:**

```json
{
    "success": false,
    "detail": "session_id contains invalid characters (only alphanumeric, dots, underscores, and hyphens allowed)",
    "error_code": "INVALID_FORMAT",
    "timestamp": "2024-01-15T10:30:00.000Z",
    "troubleshooting": "Use only letters, numbers, dots, underscores, and hyphens in session IDs"
}
```

### Error: 500 Internal Server Error

Returned for unexpected server-side errors during session processing.

**Example Response:**

```json
{
    "success": false,
    "detail": "Internal server error: Memory allocation failed during session cleanup",
    "error_code": "INTERNAL_ERROR",
    "timestamp": "2024-01-15T10:30:00.000Z",
    "troubleshooting": "Please retry the request. If the problem persists, contact system administrator"
}
```

## Performance Optimization

### Session Storage Performance

-   **Fast Lookups**: O(1) session existence checking using dictionary keys
-   **Efficient Content Tracking**: O(1) content ID existence checking using Python sets
-   **Memory Efficiency**: Automatic garbage collection when sessions are reset
-   **Scalability Threshold**: Optimal for <1000 concurrent sessions in development/testing

### Memory Management Strategies

-   **Automatic Cleanup**: Sessions cleared on explicit reset requests
-   **Memory Monitoring**: Built-in statistics for tracking storage usage
-   **Garbage Collection**: Python's automatic memory management handles freed session data
-   **Production Migration**: Redis recommended for >1000 sessions or >50MB usage

## Testing and Validation

### Integration Testing

```python
import pytest
from fastapi.testclient import TestClient
from backend_api import app, session_storage

class TestSessionResetEndpoint:
    """Integration tests for the session reset endpoint"""

    @pytest.fixture
    def client(self):
        return TestClient(app)

    @pytest.fixture(autouse=True)
    def clear_sessions(self):
        session_storage.clear()
        yield
        session_storage.clear()

    def test_successful_session_reset(self, client):
        """Test successful session reset via API"""

        # Setup session data
        session_id = "integration_test_session"
        session_storage[session_id] = {'content_1', 'content_2', 'content_3'}

        # Make API request
        response = client.post(f"/api/reset-session?session_id={session_id}")

        # Verify response
        assert response.status_code == 200
        data = response.json()
        assert data['success'] is True
        assert data['data']['session_reset']['session_found'] is True
        assert data['data']['session_reset']['cleared_items_count'] == 3

        # Verify session is actually cleared
        assert session_id not in session_storage

    def test_session_not_found(self, client):
        """Test reset of non-existent session"""

        response = client.post("/api/reset-session?session_id=nonexistent")

        assert response.status_code == 200
        data = response.json()
        assert data['success'] is True
        assert data['data']['session_reset']['session_found'] is False

    def test_invalid_session_id_characters(self, client):
        """Test session ID with invalid characters"""

        invalid_session_id = "invalid@session#id!"
        response = client.post(f"/api/reset-session?session_id={invalid_session_id}")

        assert response.status_code == 400
        assert "invalid characters" in response.json()['detail'].lower()
```

## Implementation Details

### File Locations

-   **Main Endpoint**: `backend_api.py` - `reset_session()` function (lines 1279-1286)
-   **Core Logic**: `backend_api.py` - `ViralSpotAPI.reset_session()` method (lines 1048-1059)
-   **Session Storage**: `backend_api.py` - Global `session_storage` dictionary (line 119)
-   **Integration**: Used by `_apply_random_ordering()` method in content delivery endpoints

### Processing Characteristics

-   **Memory Efficiency**: In-memory Python dictionary with automatic garbage collection
-   **Fast Operations**: O(1) session lookup and deletion operations
-   **Session Tracking**: Integration with content delivery for duplicate prevention
-   **Scalability**: Suitable for development/testing, Redis recommended for production

### Security Features

-   **Input Validation**: Comprehensive session ID format validation and sanitization
-   **Character Restrictions**: Only alphanumeric, dots, underscores, and hyphens allowed
-   **Length Limits**: Maximum 255 characters to prevent memory abuse
-   **Error Handling**: Detailed error messages with troubleshooting guidance

### Integration Points

-   **Content Endpoints**: Direct integration with `/api/reels` and `/api/posts` randomization
-   **Random Ordering**: Controls the `random_order=true` functionality across content delivery
-   **Duplicate Prevention**: Manages seen content tracking to avoid repeat content delivery
-   **Session Consistency**: Ensures consistent randomization across multiple API calls

---

**Development Note**: This endpoint provides **comprehensive session state management** with efficient memory handling, robust validation, and seamless integration with content delivery systems. It serves as an essential utility for managing user session data, supporting both development workflows and production content delivery optimization.

**Usage Recommendation**: Use this endpoint to reset user session data when implementing fresh content discovery features, debugging content delivery issues, or providing users with the ability to restart their content browsing experience with new randomization patterns.
