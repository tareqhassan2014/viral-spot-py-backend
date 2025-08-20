# GET `/api/debug/profile/{username}` 🐛

Comprehensive debugging and testing interface for Instagram profile data fetching with direct external API access and raw response inspection.

## Description

This endpoint serves as the **primary debugging and testing interface** for Instagram profile data fetching, providing direct access to external Instagram scraper APIs with raw response inspection, performance monitoring, and comprehensive error diagnosis capabilities for development and troubleshooting workflows.

**Key Features:**

-   **Direct API Access**: Bypasses all application layers to test external Instagram scraper API connectivity
-   **Raw Data Inspection**: Returns unprocessed, untransformed API responses for detailed debugging analysis
-   **Performance Monitoring**: Tracks API response times, error rates, and service availability metrics
-   **Error Diagnosis**: Comprehensive error classification with specific troubleshooting guidance
-   **Service Validation**: Tests API key validity, endpoint availability, and response format consistency
-   **Development Testing**: Enables rapid testing of profile fetching without full application pipeline
-   **API Comparison**: Supports testing multiple Instagram scraper services for reliability comparison

**Primary Use Cases:**

1. **API Integration Testing**: Validating external Instagram scraper API connections and responses
2. **Error Diagnosis**: Troubleshooting profile fetching failures and API service issues
3. **Performance Analysis**: Monitoring API response times and identifying performance bottlenecks
4. **Service Reliability**: Testing backup APIs and failover mechanisms during service outages
5. **Development Workflow**: Rapid testing of profile data availability without queue processing
6. **Data Format Validation**: Inspecting raw API responses for schema changes and data quality
7. **Credential Verification**: Testing API key validity and service access permissions

**Debug Testing Pipeline:**

-   **API Authentication**: Validates RapidAPI credentials and service access permissions
-   **External Service Connection**: Tests Instagram scraper API availability and response consistency
-   **Data Format Inspection**: Returns raw, unprocessed API responses for schema validation
-   **Performance Metrics**: Measures API response times and identifies performance issues
-   **Error Classification**: Categorizes API failures with specific diagnostic information
-   **Service Monitoring**: Tracks external API health and availability for system monitoring
-   **Fallback Testing**: Validates backup API services and failover mechanisms

**Development Integration:**

-   **No Database Dependencies**: Operates independently of application database for isolated testing
-   **Bypass Application Logic**: Skips all data transformation and validation for pure API testing
-   **Raw Response Access**: Provides unmodified external API responses for debugging analysis
-   **Service Isolation**: Tests external API connectivity without affecting application state
-   **Development Safety**: Includes warnings and restrictions for production deployment safety

**Note**: This endpoint is **strictly for development and testing purposes** and should never be exposed in production environments due to direct external API access and raw data exposure.

## Path Parameters

| Parameter  | Type   | Description                          |
| :--------- | :----- | :----------------------------------- |
| `username` | string | The username of the profile to test. |

## Execution Flow

1.  **Request Processing and Validation**: The endpoint receives a GET request with a `username` path parameter and performs initial input validation to ensure the username is properly formatted.

2.  **API Service Availability Check**:

    -   Validates that `SimpleSimilarProfilesAPI` module is available and properly initialized
    -   Checks for required API credentials (RapidAPI key) and service configurations
    -   Returns HTTP 503 if external API services are unavailable or misconfigured
    -   Ensures safe testing environment with proper error handling for missing dependencies

3.  **External API Authentication and Configuration**:

    -   Retrieves Instagram scraper API credentials from environment variables (`RAPIDAPI_KEY`, `INSTAGRAM_SCRAPER_API_KEY`)
    -   Configures API host settings (`INSTAGRAM_SCRAPER_API_HOST`) with fallback to default service
    -   Prepares authentication headers with RapidAPI key and host configuration
    -   Sets up request timeout and retry parameters for reliable external API communication

4.  **Direct Instagram API Call**:

    -   Calls `_fetch_basic_profile_data()` method directly, bypassing all application transformation layers
    -   Makes HTTP POST request to Instagram scraper API (`ig_get_fb_profile.php`) with username parameter
    -   Uses 30-second timeout and proper Content-Type headers for reliable external API communication
    -   Captures raw API response including status codes, headers, and complete response body

5.  **Raw Response Processing and Validation**:

    -   Processes HTTP response status and validates successful external API communication
    -   Extracts raw profile data without any transformation, validation, or normalization
    -   Maintains original field names, data types, and response structure from external API
    -   Identifies missing or incomplete profile data for debugging analysis

6.  **Performance Metrics Collection**:

    -   Measures API response time from request initiation to response completion
    -   Tracks external API status codes and response sizes for performance monitoring
    -   Calculates network latency and processing overhead for optimization analysis
    -   Collects service availability metrics for reliability monitoring

7.  **Debug Response Assembly**:

    -   Assembles comprehensive debug response with raw profile data, API metadata, and performance metrics
    -   Includes service availability status, response validation results, and timing information
    -   Provides detailed diagnostic information for troubleshooting external API issues
    -   Maintains complete audit trail of external API interaction for debugging analysis

8.  **Error Classification and Reporting**:
    -   Categorizes external API errors with specific error types and diagnostic information
    -   Provides actionable troubleshooting guidance for common API integration issues
    -   Includes detailed error context for rapid issue resolution and service recovery
    -   Maintains comprehensive error logging for system monitoring and debugging workflows

## Detailed Implementation Guide

### Python (FastAPI) - Complete Implementation

```python
# In backend_api.py

@app.get("/api/debug/profile/{username}")
async def debug_profile_fetch(
    username: str = Path(..., description="Username to test profile fetching")
):
    """
    Debug endpoint to test profile fetching directly with comprehensive diagnostics

    Features:
    - Direct external Instagram API access bypassing application layers
    - Raw response inspection with detailed performance metrics
    - Comprehensive error diagnosis and troubleshooting guidance
    - API service availability validation and credential verification
    """
    # Step 1: Validate API service availability
    if not SIMPLE_SIMILAR_API_AVAILABLE:
        logger.warning(f"❌ SimpleSimilarProfilesAPI not available for debug fetch: {username}")
        raise HTTPException(
            status_code=503,
            detail="Simple similar profiles API not available"
        )

    # Step 2: Track performance metrics
    import time
    start_time = time.time()

    try:
        logger.info(f"🐛 DEBUG: Starting profile fetch for @{username}")

        # Step 3: Initialize API service and validate credentials
        similar_api = get_similar_api()

        # Validate API credentials before making request
        rapidapi_key = os.getenv('RAPIDAPI_KEY') or os.getenv('INSTAGRAM_SCRAPER_API_KEY')
        api_host = os.getenv('INSTAGRAM_SCRAPER_API_HOST', 'instagram-scraper-stable-api.p.rapidapi.com')

        if not rapidapi_key:
            logger.error(f"❌ No RapidAPI key available for debug fetch: {username}")
            raise HTTPException(
                status_code=503,
                detail="API credentials not configured"
            )

        # Step 4: Call internal method directly for debugging with timing
        api_call_start = time.time()
        profile_data = await similar_api._fetch_basic_profile_data(username)
        api_call_duration = time.time() - api_call_start

        # Step 5: Analyze raw response and collect diagnostics
        response_analysis = {
            'data_received': profile_data is not None,
            'response_size_bytes': len(str(profile_data)) if profile_data else 0,
            'api_call_duration_ms': round(api_call_duration * 1000, 2),
            'api_endpoint': f"https://{api_host}/ig_get_fb_profile.php",
            'api_host': api_host,
            'credentials_available': bool(rapidapi_key),
            'timeout_used': 30
        }

        # Step 6: Validate response structure and extract metadata
        profile_metadata = {}
        if profile_data:
            profile_metadata = {
                'has_username': 'username' in profile_data,
                'has_full_name': 'full_name' in profile_data,
                'has_profile_pic': 'profile_pic_url' in profile_data,
                'field_count': len(profile_data.keys()),
                'available_fields': list(profile_data.keys()),
                'data_type': type(profile_data).__name__
            }

        # Step 7: Calculate total processing time
        total_duration = time.time() - start_time

        logger.info(f"✅ DEBUG: Successfully fetched profile data for @{username} in {total_duration:.3f}s")

        return APIResponse(
            success=True,
            data={
                'username': username,
                'profile_data': profile_data,
                'api_available': profile_data is not None,
                'debug_info': {
                    'api_endpoint': response_analysis['api_endpoint'],
                    'api_call_duration_ms': response_analysis['api_call_duration_ms'],
                    'total_request_duration_ms': round(total_duration * 1000, 2),
                    'response_size_bytes': response_analysis['response_size_bytes'],
                    'credentials_configured': response_analysis['credentials_available'],
                    'service_host': response_analysis['api_host']
                },
                'response_analysis': response_analysis,
                'profile_metadata': profile_metadata,
                'timestamp': datetime.now().isoformat(),
                'environment': {
                    'api_host_configured': bool(api_host),
                    'timeout_seconds': 30,
                    'method': 'POST',
                    'content_type': 'application/x-www-form-urlencoded'
                }
            },
            message=f"Debug fetch for @{username}"
        )

    except HTTPException:
        # Re-raise HTTP exceptions
        raise

    except requests.exceptions.Timeout as e:
        total_duration = time.time() - start_time
        logger.error(f"⏰ DEBUG: Timeout fetching profile for @{username} after {total_duration:.3f}s")

        raise HTTPException(
            status_code=408,
            detail={
                "error": "Request timeout",
                "username": username,
                "timeout_duration": 30,
                "total_request_time": round(total_duration * 1000, 2),
                "troubleshooting": "Check network connectivity and API service status"
            }
        )

    except requests.exceptions.ConnectionError as e:
        total_duration = time.time() - start_time
        logger.error(f"🌐 DEBUG: Connection error fetching profile for @{username}: {e}")

        raise HTTPException(
            status_code=502,
            detail={
                "error": "API connection failed",
                "username": username,
                "api_host": api_host,
                "troubleshooting": "Verify API host configuration and network connectivity"
            }
        )

    except requests.exceptions.HTTPError as e:
        total_duration = time.time() - start_time
        logger.error(f"📡 DEBUG: HTTP error fetching profile for @{username}: {e}")

        raise HTTPException(
            status_code=502,
            detail={
                "error": "Instagram API error",
                "username": username,
                "http_status": getattr(e.response, 'status_code', 'unknown'),
                "api_response": getattr(e.response, 'text', 'no response body'),
                "troubleshooting": "Check Instagram API service status and rate limits"
            }
        )

    except Exception as e:
        total_duration = time.time() - start_time
        logger.error(f"❌ DEBUG: Unexpected error in profile fetch for @{username}: {e}")

        raise HTTPException(
            status_code=500,
            detail={
                "error": str(e),
                "username": username,
                "request_duration_ms": round(total_duration * 1000, 2),
                "error_type": type(e).__name__,
                "troubleshooting": "Check system logs for detailed error information"
            }
        )

```

**Critical Implementation Details:**

1. **Direct External API Access**: Bypasses all application layers to provide raw Instagram scraper API testing
2. **Comprehensive Error Handling**: Specific exception handling for timeout, connection, HTTP, and system errors
3. **Performance Monitoring**: Detailed timing measurements for API calls and total request processing
4. **Raw Response Preservation**: Maintains complete original API response for debugging analysis
5. **Credential Validation**: Checks API key availability and configuration before making requests
6. **Debug Metadata Collection**: Gathers detailed diagnostic information for troubleshooting workflows
7. **Development Safety**: Includes proper HTTP status codes and error context for safe development testing

### Nest.js (Mongoose) - Complete Implementation

```typescript
// debug.controller.ts
import {
    Controller,
    Get,
    Param,
    HttpException,
    HttpStatus,
} from "@nestjs/common";
import { ApiTags, ApiOperation, ApiParam, ApiResponse } from "@nestjs/swagger";

@ApiTags("debug")
@Controller("api/debug")
export class DebugController {
    constructor(private readonly debugService: DebugService) {}

    @Get("profile/:username")
    @ApiOperation({
        summary: "Debug Instagram profile fetching",
        description:
            "Direct testing of external Instagram API with raw response inspection",
    })
    async debugProfileFetch(@Param("username") username: string) {
        try {
            if (!username || username.trim().length === 0) {
                throw new HttpException(
                    "Username is required",
                    HttpStatus.BAD_REQUEST
                );
            }

            const cleanUsername = username.replace(/^@/, "");
            const startTime = Date.now();

            const result = await this.debugService.fetchProfileDebugData(
                cleanUsername
            );
            const totalDuration = Date.now() - startTime;

            return {
                success: true,
                data: {
                    ...result,
                    debug_info: {
                        ...result.debug_info,
                        total_request_duration_ms: totalDuration,
                    },
                },
                message: `Debug fetch for @${cleanUsername}`,
            };
        } catch (error) {
            throw new HttpException(
                `Debug fetch failed: ${error.message}`,
                HttpStatus.INTERNAL_SERVER_ERROR
            );
        }
    }
}

// debug.service.ts
import { Injectable, Logger } from "@nestjs/common";
import { ConfigService } from "@nestjs/config";
import { HttpService } from "@nestjs/axios";
import { firstValueFrom } from "rxjs";

@Injectable()
export class DebugService {
    private readonly logger = new Logger(DebugService.name);

    constructor(
        private readonly httpService: HttpService,
        private readonly configService: ConfigService
    ) {}

    async fetchProfileDebugData(username: string): Promise<any> {
        try {
            // Get API credentials
            const rapidApiKey = this.configService.get<string>("RAPIDAPI_KEY");
            const apiHost = this.configService.get<string>(
                "INSTAGRAM_SCRAPER_API_HOST",
                "instagram-scraper-stable-api.p.rapidapi.com"
            );

            if (!rapidApiKey) {
                throw new Error("API credentials not configured");
            }

            // Configure API request
            const url = `https://${apiHost}/ig_get_fb_profile.php`;
            const payload = `username_or_url=${username}`;

            const headers = {
                "x-rapidapi-key": rapidApiKey,
                "x-rapidapi-host": apiHost,
                "Content-Type": "application/x-www-form-urlencoded",
            };

            // Make API call with timing
            const apiCallStart = Date.now();
            const response = await firstValueFrom(
                this.httpService.post(url, payload, { headers, timeout: 30000 })
            );
            const apiCallDuration = Date.now() - apiCallStart;

            // Analyze response
            if (response.status === 200 && response.data) {
                const profileData = response.data;

                return {
                    username,
                    profile_data: profileData,
                    api_available: true,
                    debug_info: {
                        api_endpoint: url,
                        api_call_duration_ms: apiCallDuration,
                        response_status: response.status,
                        service_host: apiHost,
                    },
                    response_analysis: {
                        status_code: response.status,
                        response_size_bytes: JSON.stringify(response.data)
                            .length,
                        data_received: true,
                    },
                    profile_metadata: {
                        field_count: Object.keys(profileData).length,
                        available_fields: Object.keys(profileData),
                        has_username: "username" in profileData,
                        has_full_name: "full_name" in profileData,
                    },
                };
            } else {
                return {
                    username,
                    profile_data: null,
                    api_available: false,
                    error_details: {
                        http_status: response.status,
                        response_body: response.data,
                    },
                };
            }
        } catch (error) {
            throw new Error(`Profile fetch failed: ${error.message}`);
        }
    }
}
```

## Responses

### Success: 200 OK - Profile Data Retrieved

Returns comprehensive profile data with detailed debugging information:

```json
{
    "success": true,
    "data": {
        "username": "entrepreneur_mike",
        "profile_data": {
            "username": "entrepreneur_mike",
            "full_name": "Mike Johnson | Entrepreneur",
            "profile_pic_url": "https://scontent-lax3-1.cdninstagram.com/v/t51.2885-19/...",
            "follower_count": 125000,
            "following_count": 850,
            "media_count": 847,
            "biography": "🚀 Building the future | 💼 Startup Advisor | 📱 Tech Enthusiast",
            "is_verified": false,
            "is_private": false,
            "external_url": "https://mikejohnson.com",
            "category": "Entrepreneur",
            "_raw_response": {
                "username": "entrepreneur_mike",
                "full_name": "Mike Johnson | Entrepreneur",
                "biography": "🚀 Building the future | 💼 Startup Advisor | 📱 Tech Enthusiast",
                "follower_count": 125000,
                "following_count": 850,
                "media_count": 847,
                "profile_pic_url": "https://scontent-lax3-1.cdninstagram.com/v/t51.2885-19/...",
                "is_verified": false,
                "is_private": false,
                "external_url": "https://mikejohnson.com",
                "category": "Entrepreneur"
            },
            "_api_metadata": {
                "response_status": 200,
                "response_headers": {
                    "content-type": "application/json",
                    "x-ratelimit-remaining": "985",
                    "x-ratelimit-reset": "1705412400"
                },
                "response_size_bytes": 1247,
                "api_host": "instagram-scraper-stable-api.p.rapidapi.com",
                "request_method": "POST",
                "request_url": "https://instagram-scraper-stable-api.p.rapidapi.com/ig_get_fb_profile.php"
            }
        },
        "api_available": true,
        "debug_info": {
            "api_endpoint": "https://instagram-scraper-stable-api.p.rapidapi.com/ig_get_fb_profile.php",
            "api_call_duration_ms": 1247.3,
            "total_request_duration_ms": 1285.7,
            "response_size_bytes": 1247,
            "credentials_configured": true,
            "service_host": "instagram-scraper-stable-api.p.rapidapi.com"
        },
        "response_analysis": {
            "data_received": true,
            "response_size_bytes": 1247,
            "api_call_duration_ms": 1247.3,
            "api_endpoint": "https://instagram-scraper-stable-api.p.rapidapi.com/ig_get_fb_profile.php",
            "api_host": "instagram-scraper-stable-api.p.rapidapi.com",
            "credentials_available": true,
            "timeout_used": 30
        },
        "profile_metadata": {
            "has_username": true,
            "has_full_name": true,
            "has_profile_pic": true,
            "field_count": 10,
            "available_fields": [
                "username",
                "full_name",
                "profile_pic_url",
                "follower_count",
                "following_count",
                "media_count",
                "biography",
                "is_verified",
                "is_private",
                "external_url"
            ],
            "data_type": "object"
        },
        "timestamp": "2024-01-15T14:30:25.123Z",
        "environment": {
            "api_host_configured": true,
            "timeout_seconds": 30,
            "method": "POST",
            "content_type": "application/x-www-form-urlencoded"
        }
    },
    "message": "Debug fetch for @entrepreneur_mike"
}
```

### Success: 200 OK - Profile Not Found

Returns when the requested profile does not exist or is inaccessible:

```json
{
    "success": true,
    "data": {
        "username": "nonexistent_user",
        "profile_data": null,
        "api_available": false,
        "debug_info": {
            "api_endpoint": "https://instagram-scraper-stable-api.p.rapidapi.com/ig_get_fb_profile.php",
            "api_call_duration_ms": 842.1,
            "total_request_duration_ms": 867.4,
            "response_status": 404,
            "credentials_configured": true,
            "service_host": "instagram-scraper-stable-api.p.rapidapi.com"
        },
        "response_analysis": {
            "data_received": false,
            "response_size_bytes": 0,
            "api_call_duration_ms": 842.1,
            "status_code": 404,
            "error_reason": "profile_not_found"
        },
        "error_details": {
            "http_status": 404,
            "response_body": null,
            "possible_causes": [
                "Profile does not exist",
                "Username misspelled",
                "Profile deleted"
            ],
            "recommended_actions": [
                "Verify username spelling",
                "Check if profile exists on Instagram"
            ]
        },
        "timestamp": "2024-01-15T14:30:25.123Z"
    },
    "message": "Debug fetch for @nonexistent_user"
}
```

### Error: 400 Bad Request

Returned for invalid username parameters:

```json
{
    "success": false,
    "detail": "Username is required"
}
```

**Common Triggers:**

-   Empty or missing username parameter
-   Username exceeds 30 character limit
-   Invalid characters in username
-   Malformed path parameters

### Error: 403 Forbidden

Returned when debug endpoint is accessed in production environment:

```json
{
    "success": false,
    "detail": "Debug endpoint not available in production"
}
```

**Common Triggers:**

-   Debug endpoint accessed in production environment
-   Debug mode disabled in configuration
-   Security restrictions preventing debug access

### Error: 408 Request Timeout

Returned when external Instagram API calls timeout:

```json
{
    "success": false,
    "detail": {
        "error": "Request timeout",
        "username": "timeout_test_user",
        "timeout_duration": 30,
        "total_request_time": 30127.5,
        "troubleshooting": "Check network connectivity and API service status"
    }
}
```

**Common Triggers:**

-   Network connectivity issues during external API calls
-   Instagram scraper API service slowdown or overload
-   High network latency affecting request timing
-   External API service temporarily unresponsive

### Error: 502 Bad Gateway

Returned for external Instagram API connection failures:

```json
{
    "success": false,
    "detail": {
        "error": "API connection failed",
        "username": "connection_test_user",
        "api_host": "instagram-scraper-stable-api.p.rapidapi.com",
        "troubleshooting": "Verify API host configuration and network connectivity"
    }
}
```

**Common Triggers:**

-   External Instagram API service unavailable
-   Network connectivity issues preventing API access
-   Incorrect API host configuration in environment variables
-   DNS resolution failures for external API endpoints

### Error: 503 Service Unavailable

Returned when required API services or credentials are not available:

```json
{
    "success": false,
    "detail": "Simple similar profiles API not available"
}
```

**Common Triggers:**

-   `SimpleSimilarProfilesAPI` module not properly initialized
-   Missing required API credentials (`RAPIDAPI_KEY`, `INSTAGRAM_SCRAPER_API_KEY`)
-   External API service configuration not available
-   Development environment not properly configured

### Error: 500 Internal Server Error

Returned for unexpected server-side errors during processing:

```json
{
    "success": false,
    "detail": {
        "error": "Unexpected error: KeyError('profile_pic_url')",
        "username": "error_test_user",
        "request_duration_ms": 1524.8,
        "error_type": "KeyError",
        "troubleshooting": "Check system logs for detailed error information"
    }
}
```

**Common Triggers:**

-   Unexpected data format changes in external Instagram API responses
-   System resource exhaustion during API processing
-   Internal application errors during response processing
-   Configuration errors in API integration setup

**Comprehensive Response Field Reference:**

| Field                       | Type        | Description                         | When Present       | Purpose                  |
| :-------------------------- | :---------- | :---------------------------------- | :----------------- | :----------------------- |
| **Core Debug Fields**       |             |                                     |                    |                          |
| `username`                  | string      | Requested username for testing      | Always             | Request tracking         |
| `profile_data`              | object/null | Raw Instagram API response          | When successful    | Data inspection          |
| `api_available`             | boolean     | Whether external API returned data  | Always             | Service status           |
| `message`                   | string      | Debug operation description         | Always             | Operation tracking       |
| **Debug Information**       |             |                                     |                    |                          |
| `api_endpoint`              | string      | Full external API URL called        | Always             | Endpoint verification    |
| `api_call_duration_ms`      | number      | External API response time          | Always             | Performance monitoring   |
| `total_request_duration_ms` | number      | Complete request processing time    | Always             | Performance analysis     |
| `response_status`           | number      | HTTP status from external API       | Always             | Status tracking          |
| `credentials_configured`    | boolean     | Whether API credentials available   | Always             | Configuration validation |
| `service_host`              | string      | External API host being used        | Always             | Service identification   |
| **Response Analysis**       |             |                                     |                    |                          |
| `data_received`             | boolean     | Whether valid data was returned     | Always             | Success indicator        |
| `response_size_bytes`       | number      | Raw response payload size           | Always             | Performance metrics      |
| `status_code`               | number      | HTTP status code from API           | Always             | Status analysis          |
| `headers_count`             | number      | Number of response headers          | When successful    | Response completeness    |
| `content_type`              | string      | API response content type           | When available     | Format validation        |
| **Profile Metadata**        |             |                                     |                    |                          |
| `has_username`              | boolean     | Whether username field present      | When data received | Data validation          |
| `has_full_name`             | boolean     | Whether full name available         | When data received | Completeness check       |
| `has_profile_pic`           | boolean     | Whether profile picture available   | When data received | Media availability       |
| `field_count`               | number      | Total fields in profile response    | When data received | Data richness            |
| `available_fields`          | array       | List of all available data fields   | When data received | Schema inspection        |
| `data_completeness_score`   | number      | Percentage of expected data present | When data received | Quality metric           |
| **Environment Info**        |             |                                     |                    |                          |
| `api_host_configured`       | boolean     | Whether custom API host set         | Always             | Configuration status     |
| `timeout_seconds`           | number      | Request timeout used                | Always             | Configuration tracking   |
| `method`                    | string      | HTTP method used for API call       | Always             | Request method tracking  |
| `timestamp`                 | datetime    | When debug request was processed    | Always             | Request timing           |

## External API Configuration

### Instagram Scraper API Integration

The debug endpoint integrates with external Instagram scraper services for raw profile data access:

```python
# External API configuration details
EXTERNAL_API_CONFIG = {
    'primary_service': {
        'name': 'Instagram Scraper Stable API',
        'host': 'instagram-scraper-stable-api.p.rapidapi.com',
        'endpoint': '/ig_get_fb_profile.php',
        'method': 'POST',
        'timeout': 30,
        'auth_type': 'rapidapi_key'
    },
    'backup_service': {
        'name': 'Instagram Scraper Secondary',
        'host': 'instagram-scraper-20251.p.rapidapi.com',
        'endpoint': '/get_profile',
        'method': 'GET',
        'timeout': 30,
        'auth_type': 'rapidapi_key'
    },
    'authentication': {
        'required_headers': [
            'x-rapidapi-key',
            'x-rapidapi-host',
            'Content-Type'
        ],
        'env_variables': [
            'RAPIDAPI_KEY',
            'INSTAGRAM_SCRAPER_API_KEY',
            'INSTAGRAM_SCRAPER_API_HOST'
        ]
    },
    'rate_limits': {
        'requests_per_minute': 100,
        'requests_per_day': 10000,
        'burst_limit': 20
    }
}
```

### Environment Variable Configuration

```bash
# Required environment variables for debug endpoint
RAPIDAPI_KEY=your_rapidapi_key_here
INSTAGRAM_SCRAPER_API_KEY=backup_api_key_here
INSTAGRAM_SCRAPER_API_HOST=instagram-scraper-stable-api.p.rapidapi.com

# Optional configuration
DEBUG_MODE=true
NODE_ENV=development
API_TIMEOUT_SECONDS=30
DEBUG_ENDPOINT_ENABLED=true
```

### API Service Validation

```python
# Comprehensive API service validation
async def validate_external_api_services():
    """Validate all external API services for debugging reliability"""

    validation_results = {
        'primary_service': await test_primary_instagram_api(),
        'backup_service': await test_backup_instagram_api(),
        'credentials': validate_api_credentials(),
        'network': await test_network_connectivity(),
        'rate_limits': await check_rate_limit_status()
    }

    return {
        'overall_status': all(validation_results.values()),
        'service_details': validation_results,
        'recommendations': generate_debug_recommendations(validation_results)
    }

async def test_primary_instagram_api() -> Dict:
    """Test primary Instagram scraper API service"""
    try:
        # Test with Instagram's official account
        test_response = await fetch_profile_data('instagram')

        return {
            'available': test_response is not None,
            'response_time_ms': test_response.get('api_call_duration_ms', 0),
            'data_quality': test_response.get('profile_metadata', {}).get('data_completeness_score', 0),
            'last_tested': datetime.now().isoformat()
        }

    except Exception as e:
        return {
            'available': False,
            'error': str(e),
            'last_tested': datetime.now().isoformat()
        }

def validate_api_credentials() -> Dict:
    """Validate API credentials and configuration"""
    rapidapi_key = os.getenv('RAPIDAPI_KEY')
    backup_key = os.getenv('INSTAGRAM_SCRAPER_API_KEY')
    api_host = os.getenv('INSTAGRAM_SCRAPER_API_HOST')

    return {
        'primary_key_available': bool(rapidapi_key),
        'backup_key_available': bool(backup_key),
        'custom_host_configured': bool(api_host),
        'key_format_valid': rapidapi_key and len(rapidapi_key) > 20 if rapidapi_key else False,
        'configuration_complete': bool(rapidapi_key) and bool(api_host)
    }
```

## Performance Monitoring and Analysis

### API Response Time Tracking

```typescript
// Advanced performance monitoring for debug endpoint
@Injectable()
export class DebugPerformanceMonitor {
    private performanceHistory: Map<string, PerformanceMetric[]> = new Map();

    recordApiCall(
        username: string,
        metrics: {
            api_duration_ms: number;
            response_size_bytes: number;
            status_code: number;
            success: boolean;
        }
    ) {
        const metric: PerformanceMetric = {
            timestamp: new Date(),
            username,
            ...metrics,
        };

        if (!this.performanceHistory.has(username)) {
            this.performanceHistory.set(username, []);
        }

        const history = this.performanceHistory.get(username);
        history.push(metric);

        // Keep only last 100 records per username
        if (history.length > 100) {
            history.splice(0, history.length - 100);
        }
    }

    getPerformanceStats(username?: string): {
        avg_response_time_ms: number;
        success_rate: number;
        total_requests: number;
        recent_performance: PerformanceMetric[];
        performance_trend: string;
    } {
        let allMetrics: PerformanceMetric[] = [];

        if (username) {
            allMetrics = this.performanceHistory.get(username) || [];
        } else {
            // Aggregate all metrics
            for (const metrics of this.performanceHistory.values()) {
                allMetrics.push(...metrics);
            }
        }

        if (allMetrics.length === 0) {
            return {
                avg_response_time_ms: 0,
                success_rate: 0,
                total_requests: 0,
                recent_performance: [],
                performance_trend: "no_data",
            };
        }

        const avgResponseTime =
            allMetrics.reduce((sum, m) => sum + m.api_duration_ms, 0) /
            allMetrics.length;
        const successCount = allMetrics.filter((m) => m.success).length;
        const successRate = (successCount / allMetrics.length) * 100;

        // Calculate performance trend (last 10 vs previous 10)
        const recent = allMetrics.slice(-10);
        const previous = allMetrics.slice(-20, -10);

        let trend = "stable";
        if (recent.length >= 5 && previous.length >= 5) {
            const recentAvg =
                recent.reduce((sum, m) => sum + m.api_duration_ms, 0) /
                recent.length;
            const previousAvg =
                previous.reduce((sum, m) => sum + m.api_duration_ms, 0) /
                previous.length;

            if (recentAvg < previousAvg * 0.9) trend = "improving";
            else if (recentAvg > previousAvg * 1.1) trend = "degrading";
        }

        return {
            avg_response_time_ms: Math.round(avgResponseTime * 100) / 100,
            success_rate: Math.round(successRate * 100) / 100,
            total_requests: allMetrics.length,
            recent_performance: allMetrics.slice(-10),
            performance_trend: trend,
        };
    }
}

interface PerformanceMetric {
    timestamp: Date;
    username: string;
    api_duration_ms: number;
    response_size_bytes: number;
    status_code: number;
    success: boolean;
}
```

### Rate Limit Monitoring

```python
# Rate limit tracking for debug endpoint usage
class DebugRateLimitMonitor:
    def __init__(self):
        self.request_history = []
        self.rate_limit_warnings = []

    def track_request(self, username: str, response_headers: Dict):
        """Track debug endpoint usage and rate limit consumption"""
        request_record = {
            'timestamp': datetime.now(),
            'username': username,
            'rate_limit_remaining': response_headers.get('x-ratelimit-remaining'),
            'rate_limit_reset': response_headers.get('x-ratelimit-reset'),
            'request_id': str(uuid.uuid4())[:8]
        }

        self.request_history.append(request_record)

        # Keep only last 1000 requests
        if len(self.request_history) > 1000:
            self.request_history = self.request_history[-1000:]

        # Check for rate limit warnings
        remaining = int(response_headers.get('x-ratelimit-remaining', 999))
        if remaining < 50:
            self.rate_limit_warnings.append({
                'timestamp': datetime.now(),
                'remaining_requests': remaining,
                'reset_time': response_headers.get('x-ratelimit-reset'),
                'warning_level': 'high' if remaining < 10 else 'medium'
            })

    def get_rate_limit_status(self) -> Dict:
        """Get current rate limit status and usage patterns"""
        if not self.request_history:
            return {'status': 'no_usage_data'}

        recent_requests = [
            r for r in self.request_history
            if (datetime.now() - r['timestamp']).total_seconds() < 3600
        ]

        last_request = self.request_history[-1]

        return {
            'requests_last_hour': len(recent_requests),
            'total_requests_tracked': len(self.request_history),
            'last_rate_limit_remaining': last_request.get('rate_limit_remaining'),
            'last_rate_limit_reset': last_request.get('rate_limit_reset'),
            'recent_warnings': self.rate_limit_warnings[-5:],
            'usage_pattern': self._analyze_usage_pattern(recent_requests),
            'recommended_throttling': self._calculate_recommended_throttling()
        }

    def _analyze_usage_pattern(self, requests: List[Dict]) -> str:
        """Analyze recent usage pattern for optimization recommendations"""
        if len(requests) < 5:
            return 'low_usage'

        # Calculate request frequency
        time_span = (requests[-1]['timestamp'] - requests[0]['timestamp']).total_seconds()
        frequency = len(requests) / (time_span / 60)  # requests per minute

        if frequency > 50:
            return 'high_frequency'
        elif frequency > 20:
            return 'moderate_frequency'
        elif frequency > 5:
            return 'standard_frequency'
        else:
            return 'low_frequency'

    def _calculate_recommended_throttling(self) -> Dict:
        """Calculate recommended throttling based on usage patterns"""
        if not self.request_history:
            return {'delay_ms': 0, 'batch_size': 1}

        recent_failures = [
            r for r in self.rate_limit_warnings
            if (datetime.now() - r['timestamp']).total_seconds() < 3600
        ]

        if len(recent_failures) > 3:
            return {'delay_ms': 2000, 'batch_size': 1, 'reason': 'frequent_rate_limits'}
        elif len(recent_failures) > 0:
            return {'delay_ms': 1000, 'batch_size': 2, 'reason': 'some_rate_limits'}
        else:
            return {'delay_ms': 500, 'batch_size': 5, 'reason': 'normal_operation'}
```

## Security Considerations and Production Safety

### Access Control and Security

```typescript
// Security middleware for debug endpoint
@Injectable()
export class DebugSecurityGuard implements CanActivate {
    constructor(private configService: ConfigService) {}

    canActivate(context: ExecutionContext): boolean {
        const request = context.switchToHttp().getRequest();

        // Block access in production environment
        const isProduction =
            this.configService.get<string>("NODE_ENV") === "production";
        const debugEnabled = this.configService.get<boolean>(
            "DEBUG_ENDPOINT_ENABLED",
            false
        );

        if (isProduction && !debugEnabled) {
            throw new HttpException(
                "Debug endpoints not available in production",
                HttpStatus.FORBIDDEN
            );
        }

        // Check for development IP restrictions
        const allowedIPs = this.configService.get<string[]>(
            "DEBUG_ALLOWED_IPS",
            []
        );
        const clientIP = request.ip || request.connection.remoteAddress;

        if (allowedIPs.length > 0 && !allowedIPs.includes(clientIP)) {
            throw new HttpException(
                "Debug access restricted to authorized IPs",
                HttpStatus.FORBIDDEN
            );
        }

        // Log debug endpoint usage for security monitoring
        const logger = new Logger("DebugSecurity");
        logger.warn(
            `Debug endpoint accessed: ${request.url} from IP: ${clientIP}`
        );

        return true;
    }
}

// Apply security guard to debug routes
@Controller("api/debug")
@UseGuards(DebugSecurityGuard)
export class DebugController {
    // ... controller implementation
}
```

### Credential Protection

```python
# Secure credential handling for debug operations
class SecureDebugCredentials:

    @staticmethod
    def validate_and_mask_credentials() -> Dict:
        """Validate credentials and return masked versions for debug output"""
        rapidapi_key = os.getenv('RAPIDAPI_KEY')
        backup_key = os.getenv('INSTAGRAM_SCRAPER_API_KEY')

        def mask_key(key: str) -> str:
            """Mask API key for safe logging"""
            if not key or len(key) < 8:
                return 'invalid_key'
            return f"{key[:4]}...{key[-4:]}"

        return {
            'primary_key_status': 'configured' if rapidapi_key else 'missing',
            'primary_key_masked': mask_key(rapidapi_key) if rapidapi_key else None,
            'backup_key_status': 'configured' if backup_key else 'missing',
            'backup_key_masked': mask_key(backup_key) if backup_key else None,
            'credentials_valid': bool(rapidapi_key or backup_key)
        }

    @staticmethod
    def sanitize_debug_response(response_data: Dict) -> Dict:
        """Remove sensitive information from debug responses"""
        sanitized = response_data.copy()

        # Remove potentially sensitive fields
        sensitive_fields = [
            '_raw_response.api_key',
            'debug_info.credentials',
            'environment.api_keys'
        ]

        for field_path in sensitive_fields:
            keys = field_path.split('.')
            current = sanitized

            try:
                for key in keys[:-1]:
                    current = current[key]
                if keys[-1] in current:
                    del current[keys[-1]]
            except (KeyError, TypeError):
                pass  # Field doesn't exist, skip

        return sanitized
```

## Development Testing and Validation

### Debug Testing Suite

```python
# test_debug_profile_fetch.py
import pytest
import asyncio
from fastapi.testclient import TestClient
from unittest.mock import Mock, patch, AsyncMock
import time

class TestDebugProfileFetch:

    def test_debug_fetch_successful_profile(self, client: TestClient):
        """Test successful profile data retrieval with debug information"""
        mock_profile_data = {
            'username': 'test_user',
            'full_name': 'Test User',
            'profile_pic_url': 'https://example.com/pic.jpg',
            'follower_count': 1000,
            'following_count': 500,
            'biography': 'Test account for debugging'
        }

        with patch('simple_similar_profiles_api.SimpleSimilarProfilesAPI._fetch_basic_profile_data') as mock_fetch:
            mock_fetch.return_value = mock_profile_data

            response = client.get("/api/debug/profile/test_user")

            assert response.status_code == 200
            data = response.json()

            assert data["success"] is True
            assert data["data"]["username"] == "test_user"
            assert data["data"]["api_available"] is True
            assert "debug_info" in data["data"]
            assert "response_analysis" in data["data"]
            assert "profile_metadata" in data["data"]

    def test_debug_fetch_api_unavailable(self, client: TestClient):
        """Test behavior when external API is unavailable"""
        with patch('backend_api.SIMPLE_SIMILAR_API_AVAILABLE', False):
            response = client.get("/api/debug/profile/test_user")

            assert response.status_code == 503
            assert "not available" in response.json()["detail"]

    def test_debug_fetch_profile_not_found(self, client: TestClient):
        """Test handling of non-existent profiles"""
        with patch('simple_similar_profiles_api.SimpleSimilarProfilesAPI._fetch_basic_profile_data') as mock_fetch:
            mock_fetch.return_value = None

            response = client.get("/api/debug/profile/nonexistent_user")

            assert response.status_code == 200
            data = response.json()

            assert data["data"]["profile_data"] is None
            assert data["data"]["api_available"] is False

    def test_debug_fetch_api_timeout(self, client: TestClient):
        """Test handling of API timeout scenarios"""
        with patch('simple_similar_profiles_api.SimpleSimilarProfilesAPI._fetch_basic_profile_data') as mock_fetch:
            mock_fetch.side_effect = asyncio.TimeoutError("Request timeout")

            response = client.get("/api/debug/profile/timeout_user")

            assert response.status_code == 408
            assert "timeout" in response.json()["detail"]["error"].lower()

    def test_debug_fetch_performance(self, client: TestClient):
        """Test debug endpoint response time performance"""
        start_time = time.time()
        response = client.get("/api/debug/profile/performance_test")
        end_time = time.time()

        response_time = end_time - start_time

        # Debug endpoint should respond quickly even for external API calls
        assert response_time < 35.0  # Allow for 30s API timeout + processing
        assert response.status_code in [200, 503]  # Either success or service unavailable

    def test_debug_fetch_concurrent_requests(self, client: TestClient):
        """Test behavior with concurrent debug requests"""
        import threading

        responses = []

        def make_debug_request():
            response = client.get("/api/debug/profile/concurrent_test")
            responses.append(response)

        # Make 3 concurrent debug requests
        threads = []
        for i in range(3):
            thread = threading.Thread(target=make_debug_request)
            threads.append(thread)
            thread.start()

        for thread in threads:
            thread.join()

        # All requests should complete without interference
        assert len(responses) == 3

        # Check that all requests succeeded or failed consistently
        status_codes = [r.status_code for r in responses]
        assert len(set(status_codes)) <= 2  # Should be consistent (all 200 or all error)

    def test_debug_fetch_input_validation(self, client: TestClient):
        """Test input validation and error handling"""
        test_cases = [
            ("", 422),  # Empty username
            ("a" * 50, 422),  # Too long username
            ("valid_user", 200),  # Valid username
            ("@valid_user", 200),  # Username with @ symbol
        ]

        for username, expected_status in test_cases:
            response = client.get(f"/api/debug/profile/{username}")

            # Allow for service unavailable as well
            assert response.status_code in [expected_status, 503]

    def test_debug_fetch_credential_validation(self, client: TestClient):
        """Test handling of missing or invalid credentials"""
        with patch.dict(os.environ, {}, clear=True):
            # Remove all API credentials
            with patch('simple_similar_profiles_api.SimpleSimilarProfilesAPI._fetch_basic_profile_data') as mock_fetch:
                mock_fetch.return_value = None

                response = client.get("/api/debug/profile/cred_test")

                # Should handle missing credentials gracefully
                assert response.status_code in [200, 503]
```

### Development Workflow Integration

```bash
#!/bin/bash
# debug-profile-test.sh - Comprehensive debug testing script

API_BASE="${API_BASE:-http://localhost:8000}"

function test_debug_endpoint() {
    local username="$1"
    local verbose="${2:-false}"

    echo "🧪 Testing debug endpoint for @$username"
    echo "=============================================="

    # Test basic connectivity
    echo "📡 Testing API connectivity..."
    start_time=$(date +%s%N)

    response=$(curl -s -w "HTTPSTATUS:%{http_code};TIME:%{time_total}" \
                    "$API_BASE/api/debug/profile/$username")

    end_time=$(date +%s%N)

    # Parse response
    http_status=$(echo "$response" | grep -o "HTTPSTATUS:[0-9]*" | cut -d: -f2)
    response_time=$(echo "$response" | grep -o "TIME:[0-9.]*" | cut -d: -f2)
    response_body=$(echo "$response" | sed -E 's/HTTPSTATUS:[0-9]*;TIME:[0-9.]*$//')

    echo "HTTP Status: $http_status"
    echo "Response Time: ${response_time}s"

    # Analyze response based on status
    if [ "$http_status" = "200" ]; then
        echo "✅ Debug endpoint accessible"

        # Parse JSON response
        if echo "$response_body" | jq -e '.success' > /dev/null 2>&1; then
            api_available=$(echo "$response_body" | jq -r '.data.api_available')

            if [ "$api_available" = "true" ]; then
                echo "✅ External Instagram API working"

                # Extract debug information
                if [ "$verbose" = "true" ]; then
                    echo ""
                    echo "📊 Debug Information:"
                    echo "   API Endpoint: $(echo "$response_body" | jq -r '.data.debug_info.api_endpoint')"
                    echo "   API Duration: $(echo "$response_body" | jq -r '.data.debug_info.api_call_duration_ms')ms"
                    echo "   Response Size: $(echo "$response_body" | jq -r '.data.response_analysis.response_size_bytes') bytes"
                    echo "   Service Host: $(echo "$response_body" | jq -r '.data.debug_info.service_host')"

                    echo ""
                    echo "📋 Profile Metadata:"
                    echo "   Field Count: $(echo "$response_body" | jq -r '.data.profile_metadata.field_count')"
                    echo "   Has Username: $(echo "$response_body" | jq -r '.data.profile_metadata.has_username')"
                    echo "   Has Full Name: $(echo "$response_body" | jq -r '.data.profile_metadata.has_full_name')"
                    echo "   Has Profile Pic: $(echo "$response_body" | jq -r '.data.profile_metadata.has_profile_pic')"

                    echo ""
                    echo "🔍 Available Fields:"
                    echo "$response_body" | jq -r '.data.profile_metadata.available_fields[]' | sed 's/^/   - /'
                fi

            else
                echo "❌ External Instagram API not working"

                # Show error details if available
                error_details=$(echo "$response_body" | jq -r '.data.error_details // empty')
                if [ -n "$error_details" ]; then
                    echo "Error Details: $error_details"
                fi
            fi
        else
            echo "❌ Invalid JSON response from debug endpoint"
        fi

    elif [ "$http_status" = "503" ]; then
        echo "❌ Debug service unavailable"
        detail=$(echo "$response_body" | jq -r '.detail // "Unknown error"')
        echo "Reason: $detail"

    elif [ "$http_status" = "403" ]; then
        echo "❌ Debug endpoint access forbidden"
        echo "Note: Debug endpoints may be disabled in production"

    elif [ "$http_status" = "408" ]; then
        echo "⏰ Request timeout"
        echo "External Instagram API may be slow or unresponsive"

    else
        echo "❌ Unexpected error (HTTP $http_status)"
        echo "Response: $response_body"
    fi

    echo ""
    echo "🔧 Troubleshooting Guide:"

    case "$http_status" in
        "200")
            if [ "$api_available" = "false" ]; then
                echo "   1. Check API credentials (RAPIDAPI_KEY)"
                echo "   2. Verify Instagram API service status"
                echo "   3. Test with a known public profile"
            else
                echo "   ✅ All systems working correctly"
            fi
            ;;
        "503")
            echo "   1. Check if SimpleSimilarProfilesAPI module is available"
            echo "   2. Verify API credentials in environment variables"
            echo "   3. Restart the application if needed"
            ;;
        "403")
            echo "   1. Set DEBUG_ENDPOINT_ENABLED=true if needed"
            echo "   2. Check NODE_ENV is not set to 'production'"
            echo "   3. Verify IP restrictions if configured"
            ;;
        "408")
            echo "   1. Check network connectivity"
            echo "   2. Verify Instagram API service status"
            echo "   3. Consider increasing timeout if needed"
            ;;
        *)
            echo "   1. Check application logs for detailed error information"
            echo "   2. Verify environment configuration"
            echo "   3. Test with different username"
            ;;
    esac
}

# Execute test
if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    if [ $# -eq 0 ]; then
        echo "Usage: $0 <username> [verbose]"
        echo "Examples:"
        echo "  $0 instagram              # Test with Instagram official account"
        echo "  $0 entrepreneur_mike true # Verbose output with debug details"
        exit 1
    fi

    test_debug_endpoint "$@"
fi
```

## Implementation Details

### File Locations and Functions

-   **Primary File:** `backend_api.py` (lines 1358-1386)
-   **Method:** `debug_profile_fetch(username: str)` FastAPI route handler
-   **Internal Service:** `simple_similar_profiles_api.py` (lines 447-496)
-   **Core Method:** `SimpleSimilarProfilesAPI._fetch_basic_profile_data(username: str)`
-   **Dependencies:** `requests`, environment configuration, logging utilities

### External API Integration

1. **Primary Service**: Instagram Scraper Stable API via RapidAPI
2. **Endpoint**: `https://instagram-scraper-stable-api.p.rapidapi.com/ig_get_fb_profile.php`
3. **Authentication**: RapidAPI key-based authentication with custom headers
4. **Request Method**: HTTP POST with form-encoded username parameter
5. **Timeout**: 30-second request timeout with proper error handling
6. **Response Format**: JSON with Instagram profile metadata and engagement data

### Processing Characteristics

-   **Direct API Access**: Bypasses all application layers for pure external API testing
-   **Raw Response Preservation**: Maintains complete original API response structure
-   **No Database Operations**: Operates independently without any database dependencies
-   **Performance Tracking**: Detailed timing measurements for API calls and processing
-   **Error Classification**: Comprehensive error handling with specific diagnostic information
-   **Development Safety**: Includes production restrictions and access controls

### Security and Safety Features

-   **Production Restrictions**: Automatically disabled in production environments
-   **Credential Protection**: API keys are validated but never exposed in responses
-   **Access Logging**: All debug endpoint usage is logged for security monitoring
-   **IP Restrictions**: Configurable IP-based access control for additional security
-   **Raw Data Sanitization**: Removes sensitive information from debug responses

## Usage Examples and Development Workflows

### Frontend Debug Integration

```typescript
// React Debug Component for API Testing
import React, { useState } from "react";

interface DebugProfileTestProps {
    onResult: (result: any) => void;
}

export const DebugProfileTester: React.FC<DebugProfileTestProps> = ({
    onResult,
}) => {
    const [username, setUsername] = useState("");
    const [testing, setTesting] = useState(false);
    const [result, setResult] = useState<any>(null);

    const testProfile = async () => {
        if (!username.trim()) return;

        setTesting(true);
        setResult(null);

        try {
            const response = await fetch(
                `/api/debug/profile/${username.replace(/^@/, "")}`
            );
            const data = await response.json();

            setResult(data);
            onResult(data);
        } catch (error) {
            setResult({
                success: false,
                error: error.message,
                timestamp: new Date().toISOString(),
            });
        } finally {
            setTesting(false);
        }
    };

    return (
        <div className="debug-profile-tester">
            <h3>🐛 Profile Debug Tester</h3>

            <div className="input-group">
                <input
                    type="text"
                    value={username}
                    onChange={(e) => setUsername(e.target.value)}
                    placeholder="Enter Instagram username"
                    disabled={testing}
                />
                <button
                    onClick={testProfile}
                    disabled={testing || !username.trim()}
                >
                    {testing ? "🔄 Testing..." : "🧪 Test Profile"}
                </button>
            </div>

            {result && (
                <div className="debug-results">
                    {result.success ? (
                        <div className="success-result">
                            <h4>✅ Debug Test Results</h4>

                            <div className="api-status">
                                <strong>API Status:</strong>{" "}
                                {result.data?.api_available
                                    ? "✅ Available"
                                    : "❌ Unavailable"}
                            </div>

                            {result.data?.debug_info && (
                                <div className="debug-info">
                                    <strong>Performance:</strong>
                                    <ul>
                                        <li>
                                            API Call:{" "}
                                            {
                                                result.data.debug_info
                                                    .api_call_duration_ms
                                            }
                                            ms
                                        </li>
                                        <li>
                                            Total Time:{" "}
                                            {
                                                result.data.debug_info
                                                    .total_request_duration_ms
                                            }
                                            ms
                                        </li>
                                        <li>
                                            Response Size:{" "}
                                            {
                                                result.data.response_analysis
                                                    ?.response_size_bytes
                                            }{" "}
                                            bytes
                                        </li>
                                    </ul>
                                </div>
                            )}

                            {result.data?.profile_metadata && (
                                <div className="profile-metadata">
                                    <strong>Profile Data:</strong>
                                    <ul>
                                        <li>
                                            Fields:{" "}
                                            {
                                                result.data.profile_metadata
                                                    .field_count
                                            }
                                        </li>
                                        <li>
                                            Username:{" "}
                                            {result.data.profile_metadata
                                                .has_username
                                                ? "✅"
                                                : "❌"}
                                        </li>
                                        <li>
                                            Full Name:{" "}
                                            {result.data.profile_metadata
                                                .has_full_name
                                                ? "✅"
                                                : "❌"}
                                        </li>
                                        <li>
                                            Profile Pic:{" "}
                                            {result.data.profile_metadata
                                                .has_profile_pic
                                                ? "✅"
                                                : "❌"}
                                        </li>
                                    </ul>
                                </div>
                            )}

                            {result.data?.profile_data && (
                                <details className="raw-data">
                                    <summary>📄 Raw Profile Data</summary>
                                    <pre>
                                        {JSON.stringify(
                                            result.data.profile_data,
                                            null,
                                            2
                                        )}
                                    </pre>
                                </details>
                            )}
                        </div>
                    ) : (
                        <div className="error-result">
                            <h4>❌ Debug Test Failed</h4>
                            <p>
                                <strong>Error:</strong>{" "}
                                {result.error || result.detail}
                            </p>

                            {result.detail?.troubleshooting && (
                                <div className="troubleshooting">
                                    <strong>Troubleshooting:</strong>
                                    <p>{result.detail.troubleshooting}</p>
                                </div>
                            )}
                        </div>
                    )}
                </div>
            )}
        </div>
    );
};
```

### CLI Debug Testing Tool

```bash
#!/bin/bash
# comprehensive-debug-test.sh - Complete debug testing suite

API_BASE="${API_BASE:-http://localhost:8000}"

function run_comprehensive_debug_test() {
    local test_type="${1:-basic}"

    echo "🧪 Running Comprehensive Debug Test Suite"
    echo "=========================================="
    echo "Test Type: $test_type"
    echo "API Base: $API_BASE"
    echo ""

    # Test 1: Basic connectivity
    echo "📡 Test 1: Basic Connectivity"
    test_basic_connectivity
    echo ""

    # Test 2: Valid profile
    echo "👤 Test 2: Valid Public Profile"
    test_profile "instagram" "Known public profile"
    echo ""

    # Test 3: Invalid profile
    echo "❓ Test 3: Non-existent Profile"
    test_profile "nonexistent_debug_user_12345" "Non-existent profile"
    echo ""

    # Test 4: Performance test
    if [ "$test_type" = "performance" ] || [ "$test_type" = "full" ]; then
        echo "⚡ Test 4: Performance Analysis"
        test_performance
        echo ""
    fi

    # Test 5: Concurrent requests
    if [ "$test_type" = "concurrent" ] || [ "$test_type" = "full" ]; then
        echo "🔄 Test 5: Concurrent Request Handling"
        test_concurrent_requests
        echo ""
    fi

    # Test 6: Error scenarios
    if [ "$test_type" = "error" ] || [ "$test_type" = "full" ]; then
        echo "❌ Test 6: Error Scenario Testing"
        test_error_scenarios
        echo ""
    fi

    echo "✅ Debug Test Suite Completed"
}

function test_basic_connectivity() {
    response=$(curl -s -o /dev/null -w "%{http_code}" "$API_BASE/api/debug/profile/instagram")

    if [ "$response" = "200" ]; then
        echo "✅ Debug endpoint accessible"
    elif [ "$response" = "503" ]; then
        echo "❌ Debug service unavailable (503)"
    elif [ "$response" = "403" ]; then
        echo "❌ Debug access forbidden (403) - may be production environment"
    else
        echo "❌ Unexpected response: HTTP $response"
    fi
}

function test_profile() {
    local username="$1"
    local description="$2"

    echo "Testing: $description (@$username)"

    start_time=$(date +%s%N)
    response=$(curl -s "$API_BASE/api/debug/profile/$username")
    end_time=$(date +%s%N)

    # Calculate response time in milliseconds
    response_time=$(( ($end_time - $start_time) / 1000000 ))

    if echo "$response" | jq -e '.success' > /dev/null 2>&1; then
        api_available=$(echo "$response" | jq -r '.data.api_available')
        api_duration=$(echo "$response" | jq -r '.data.debug_info.api_call_duration_ms // "N/A"')

        echo "   Success: $([ "$api_available" = "true" ] && echo "✅" || echo "❌")"
        echo "   API Available: $api_available"
        echo "   Response Time: ${response_time}ms"
        echo "   API Duration: ${api_duration}ms"

        if [ "$api_available" = "true" ]; then
            field_count=$(echo "$response" | jq -r '.data.profile_metadata.field_count // "N/A"')
            echo "   Profile Fields: $field_count"
        fi
    else
        echo "   ❌ Request failed"
        echo "   Response: $response"
    fi
}

function test_performance() {
    echo "Running 5 consecutive requests to measure performance..."

    local total_time=0
    local success_count=0

    for i in {1..5}; do
        start_time=$(date +%s%N)
        response=$(curl -s "$API_BASE/api/debug/profile/instagram")
        end_time=$(date +%s%N)

        request_time=$(( ($end_time - $start_time) / 1000000 ))
        total_time=$((total_time + request_time))

        if echo "$response" | jq -e '.success' > /dev/null 2>&1; then
            success_count=$((success_count + 1))
            echo "   Request $i: ${request_time}ms ✅"
        else
            echo "   Request $i: ${request_time}ms ❌"
        fi
    done

    avg_time=$((total_time / 5))
    success_rate=$((success_count * 100 / 5))

    echo "Performance Summary:"
    echo "   Average Response Time: ${avg_time}ms"
    echo "   Success Rate: $success_rate%"
    echo "   Total Requests: 5"
}

function test_concurrent_requests() {
    echo "Testing 3 concurrent requests..."

    # Start 3 background requests
    for i in {1..3}; do
        (
            start_time=$(date +%s%N)
            response=$(curl -s "$API_BASE/api/debug/profile/instagram")
            end_time=$(date +%s%N)

            request_time=$(( ($end_time - $start_time) / 1000000 ))

            if echo "$response" | jq -e '.success' > /dev/null 2>&1; then
                echo "   Concurrent Request $i: ${request_time}ms ✅"
            else
                echo "   Concurrent Request $i: ${request_time}ms ❌"
            fi
        ) &
    done

    # Wait for all background requests to complete
    wait
    echo "   All concurrent requests completed"
}

function test_error_scenarios() {
    echo "Testing various error scenarios..."

    # Test 1: Empty username
    echo "   Testing empty username..."
    response=$(curl -s -o /dev/null -w "%{http_code}" "$API_BASE/api/debug/profile/")
    echo "   Empty username: HTTP $response"

    # Test 2: Very long username
    echo "   Testing very long username..."
    long_username="a_very_long_username_that_exceeds_normal_limits_and_should_cause_validation_error"
    response=$(curl -s -o /dev/null -w "%{http_code}" "$API_BASE/api/debug/profile/$long_username")
    echo "   Long username: HTTP $response"

    # Test 3: Special characters
    echo "   Testing special characters..."
    response=$(curl -s -o /dev/null -w "%{http_code}" "$API_BASE/api/debug/profile/@test.user!")
    echo "   Special chars: HTTP $response"
}

# Execute if called directly
if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    test_type="${1:-basic}"

    echo "Available test types:"
    echo "  basic       - Basic connectivity and profile tests"
    echo "  performance - Include performance analysis"
    echo "  concurrent  - Include concurrent request testing"
    echo "  error       - Include error scenario testing"
    echo "  full        - Run all tests"
    echo ""

    run_comprehensive_debug_test "$test_type"
fi
```

## Advanced Debugging Features

### API Response Comparison

```python
# Compare responses across different API services
class APIResponseComparator:

    def __init__(self):
        self.api_services = {
            'primary': 'instagram-scraper-stable-api.p.rapidapi.com',
            'secondary': 'instagram-scraper-20251.p.rapidapi.com',
            'backup': 'instagram-lookup-api.p.rapidapi.com'
        }

    async def compare_api_responses(self, username: str) -> Dict:
        """Compare profile data across multiple Instagram APIs for debugging"""
        results = {}

        for service_name, api_host in self.api_services.items():
            try:
                start_time = time.time()

                # Configure API request for each service
                profile_data = await self._fetch_from_service(username, api_host)

                response_time = (time.time() - start_time) * 1000

                results[service_name] = {
                    'success': profile_data is not None,
                    'response_time_ms': round(response_time, 2),
                    'data': profile_data,
                    'api_host': api_host,
                    'field_count': len(profile_data.keys()) if profile_data else 0,
                    'has_core_fields': self._validate_core_fields(profile_data) if profile_data else False
                }

            except Exception as e:
                results[service_name] = {
                    'success': False,
                    'error': str(e),
                    'api_host': api_host,
                    'response_time_ms': -1
                }

        # Generate comparison analysis
        successful_services = [name for name, result in results.items() if result['success']]
        fastest_service = min(
            [name for name in successful_services],
            key=lambda name: results[name]['response_time_ms']
        ) if successful_services else None

        return {
            'comparison_results': results,
            'successful_services': successful_services,
            'fastest_service': fastest_service,
            'reliability_score': len(successful_services) / len(self.api_services) * 100,
            'recommendation': self._generate_service_recommendation(results)
        }

    def _validate_core_fields(self, profile_data: Dict) -> bool:
        """Validate that core profile fields are present"""
        required_fields = ['username', 'full_name', 'profile_pic_url']
        return all(field in profile_data and profile_data[field] for field in required_fields)

    def _generate_service_recommendation(self, results: Dict) -> str:
        """Generate service recommendation based on comparison results"""
        successful_count = sum(1 for result in results.values() if result['success'])

        if successful_count == 0:
            return "All services unavailable - check network connectivity and credentials"
        elif successful_count == len(results):
            return "All services working - use primary service for optimal performance"
        else:
            working_services = [name for name, result in results.items() if result['success']]
            return f"Use available services: {', '.join(working_services)}"

```

### Debug Dashboard Integration

```typescript
// Debug dashboard for monitoring API health
@Controller('api/debug/dashboard')
export class DebugDashboardController {
  constructor(
    private readonly debugService: DebugService,
    private readonly performanceMonitor: DebugPerformanceMonitor
  ) {}

  @Get('api-health')
  async getApiHealthStatus() {
    """Get comprehensive API health status for debugging dashboard"""
    try {
      const [connectivityTest, performanceStats, rateLimitStatus] = await Promise.all([
        this.debugService.testApiConnectivity(),
        this.performanceMonitor.getPerformanceStats(),
        this.debugService.getRateLimitStatus()
      ]);

      return {
        success: true,
        data: {
          overall_health: this.calculateOverallHealth([connectivityTest, performanceStats, rateLimitStatus]),
          api_connectivity: connectivityTest,
          performance_metrics: performanceStats,
          rate_limit_status: rateLimitStatus,
          last_updated: new Date().toISOString(),
          recommendations: this.generateHealthRecommendations({
            connectivity: connectivityTest,
            performance: performanceStats,
            rate_limits: rateLimitStatus
          })
        }
      };

    } catch (error) {
      return {
        success: false,
        error: error.message,
        timestamp: new Date().toISOString()
      };
    }
  }

  @Get('recent-tests')
  async getRecentDebugTests(@Query('limit') limit: number = 50) {
    """Get recent debug test results for monitoring"""
    const recentTests = await this.performanceMonitor.getRecentTests(limit);

    return {
      success: true,
      data: {
        recent_tests: recentTests,
        summary: {
          total_tests: recentTests.length,
          success_rate: this.calculateSuccessRate(recentTests),
          avg_response_time: this.calculateAverageResponseTime(recentTests),
          most_tested_profiles: this.getMostTestedProfiles(recentTests)
        }
      }
    };
  }

  private calculateOverallHealth(healthMetrics: any[]): string {
    """Calculate overall API health score"""
    let healthScore = 0;
    let maxScore = 0;

    healthMetrics.forEach(metric => {
      if (metric.service_available) healthScore += 1;
      if (metric.response_time_ms > 0 && metric.response_time_ms < 5000) healthScore += 1;
      maxScore += 2;
    });

    const healthPercentage = (healthScore / maxScore) * 100;

    if (healthPercentage >= 90) return 'excellent';
    if (healthPercentage >= 70) return 'good';
    if (healthPercentage >= 50) return 'fair';
    return 'poor';
  }
}
```

## Related Endpoints and Integration

### Debug Workflow Integration

1. **Profile Debug**: `GET /api/debug/profile/{username}` - **This endpoint** - Test raw profile fetching
2. **Status Check**: `GET /api/profile/{username}/status` - Monitor processing status after debug validation
3. **Request Processing**: `POST /api/profile/{username}/request` - Submit profile for full processing after debug confirmation
4. **Get Profile**: `GET /api/profile/{username}` - Access processed profile data after successful debug validation

### Development Testing Workflow

-   **API Validation**: `GET /api/debug/profile/{username}` - **This endpoint** - Validate external API connectivity
-   **Service Health**: `GET /api/debug/dashboard/api-health` - Monitor overall API service health
-   **Performance Analysis**: `GET /api/debug/dashboard/recent-tests` - Track debug endpoint performance
-   **Error Diagnosis**: Debug endpoint error responses provide detailed troubleshooting guidance

### Production Deployment Safety

-   **Environment Protection**: Debug endpoints automatically disabled in production environments
-   **Access Control**: IP-based restrictions and authentication for debug endpoint access
-   **Credential Security**: API keys validated but never exposed in debug responses
-   **Monitoring Integration**: Debug usage tracked for security and operational monitoring

---

**Development Note**: This debug endpoint provides **comprehensive Instagram API testing capabilities** with detailed response analysis, performance monitoring, and error diagnosis. It serves as an essential tool for validating external API integrations, troubleshooting connectivity issues, and ensuring reliable profile data fetching across different Instagram scraper services. The endpoint includes extensive safety measures to prevent production exposure while enabling thorough development testing and debugging workflows.

**Usage Recommendation**: Use this endpoint during development to validate API configurations, test profile data availability, and diagnose integration issues before deploying profile processing workflows to production environments.
