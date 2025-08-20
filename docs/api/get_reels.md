# GET `/api/reels`

Retrieves a list of reels, with extensive support for filtering, sorting, and pagination.

## Description

This is the main endpoint for browsing and discovering viral content in the ViralSpot platform. It provides a powerful set of filters to allow users to narrow down the content they are interested in. The results are paginated to ensure efficient loading and browsing.

## Query Parameters

This endpoint accepts a wide range of query parameters to customize the results.

### General

| Parameter | Type    | Description                                                                       | Default |
| :-------- | :------ | :-------------------------------------------------------------------------------- | :------ |
| `search`  | string  | A search term to match against reel captions, transcripts, and other text fields. | `null`  |
| `limit`   | integer | The maximum number of reels to return per page (1-100).                           | `24`    |
| `offset`  | integer | The number of reels to skip for pagination.                                       | `0`     |

### Filtering

| Parameter                     | Type    | Description                                                    | Default |
| :---------------------------- | :------ | :------------------------------------------------------------- | :------ |
| `primary_categories`          | string  | Comma-separated list of primary categories to filter by.       | `null`  |
| `secondary_categories`        | string  | Comma-separated list of secondary categories to filter by.     | `null`  |
| `tertiary_categories`         | string  | Comma-separated list of tertiary categories to filter by.      | `null`  |
| `keywords`                    | string  | Comma-separated list of keywords to filter by.                 | `null`  |
| `min_outlier_score`           | float   | Minimum outlier score.                                         | `null`  |
| `max_outlier_score`           | float   | Maximum outlier score.                                         | `null`  |
| `min_views`                   | integer | Minimum view count.                                            | `null`  |
| `max_views`                   | integer | Maximum view count.                                            | `null`  |
| `min_likes`                   | integer | Minimum like count.                                            | `null`  |
| `max_likes`                   | integer | Maximum like count.                                            | `null`  |
| `min_comments`                | integer | Minimum comment count.                                         | `null`  |
| `max_comments`                | integer | Maximum comment count.                                         | `null`  |
| `min_followers`               | integer | Minimum follower count for the reel's creator.                 | `null`  |
| `max_followers`               | integer | Maximum follower count for the reel's creator.                 | `null`  |
| `date_range`                  | string  | A predefined date range to filter by (e.g., `last_7_days`).    | `null`  |
| `is_verified`                 | boolean | Filter for content from verified or non-verified accounts.     | `null`  |
| `account_types`               | string  | Comma-separated list of account types to filter by.            | `null`  |
| `content_types`               | string  | Comma-separated list of content types to filter by.            | `null`  |
| `languages`                   | string  | Comma-separated list of languages to filter by.                | `null`  |
| `content_styles`              | string  | Comma-separated list of content styles to filter by.           | `null`  |
| `min_account_engagement_rate` | float   | Minimum account engagement rate (0-100).                       | `null`  |
| `max_account_engagement_rate` | float   | Maximum account engagement rate (0-100).                       | `null`  |
| `excluded_usernames`          | string  | Comma-separated list of usernames to exclude from the results. | `null`  |

### Sorting & Ordering

| Parameter      | Type    | Description                                                                                                                                       | Default |
| :------------- | :------ | :------------------------------------------------------------------------------------------------------------------------------------------------ | :------ |
| `sort_by`      | string  | The sorting order. Options: `popular`, `views`, `likes`, `comments`, `recent`, `oldest`, `followers`, `account_engagement`, `content_engagement`. | `null`  |
| `random_order` | boolean | If `true`, returns the results in a random order for the given `session_id`.                                                                      | `false` |
| `session_id`   | string  | A unique ID for the user's session, used for consistent random ordering.                                                                          | `null`  |

## Execution Flow

1.  **Receive Request**: The endpoint receives a GET request with a wide range of optional query parameters for filtering, sorting, and pagination.
2.  **Parse and Validate Filters**: The query parameters are parsed and validated, often using a Pydantic-like model (`ReelFilter`) to ensure data integrity.
3.  **Build Dynamic Query**: A flexible database query is constructed on the `content` table. Each filter parameter adds a `WHERE` clause to the query. This includes filtering by categories, keywords, performance metrics (views, likes), and account metrics (followers).
4.  **Apply Sorting**: The `sort_by` parameter determines the `ORDER BY` clause. If `random_order` is `true`, it uses a `session_id` to create a consistent random sort for that user's session.
5.  **Apply Pagination**: The `limit` and `offset` parameters are used to paginate the results.
6.  **Execute Query**: The complex, dynamically built query is executed against the database.
7.  **Transform Data**: The results are transformed into a frontend-friendly format.
8.  **Send Response**: The paginated and transformed list of reels is returned with a `200 OK` status.

## Detailed Implementation Guide

### Python (FastAPI)

```python
# ReelFilter Pydantic Model (lines 62-91 in backend_api.py)
class ReelFilter(BaseModel):
    search: Optional[str] = None
    primary_categories: Optional[str] = None
    secondary_categories: Optional[str] = None
    tertiary_categories: Optional[str] = None
    keywords: Optional[str] = None
    min_outlier_score: Optional[float] = None
    max_outlier_score: Optional[float] = None
    min_views: Optional[int] = None
    max_views: Optional[int] = None
    min_followers: Optional[int] = None
    max_followers: Optional[int] = None
    min_likes: Optional[int] = None
    max_likes: Optional[int] = None
    min_comments: Optional[int] = None
    max_comments: Optional[int] = None
    date_range: Optional[str] = None
    is_verified: Optional[bool] = None
    random_order: Optional[bool] = False
    session_id: Optional[str] = None
    sort_by: Optional[str] = None
    account_types: Optional[str] = None
    content_types: Optional[str] = None
    languages: Optional[str] = None
    content_styles: Optional[str] = None
    excluded_usernames: Optional[str] = None
    min_account_engagement_rate: Optional[float] = None
    max_account_engagement_rate: Optional[float] = None

# Main get_reels method in ViralSpotAPI class (lines 493-540)
async def get_reels(self, filters: ReelFilter, limit: int = 24, offset: int = 0):
    """Get reels with filtering and pagination"""
    try:
        logger.info(f"Getting reels: limit={limit}, offset={offset}")
        logger.info(f"Filters: min_followers={filters.min_followers}, max_followers={filters.max_followers}")

        # Build and execute query - request one extra to check if there's more data
        query = self._build_content_query(filters, limit + 1, offset)
        response = query.execute()

        # Handle empty or None response data properly
        if not response or not hasattr(response, 'data') or response.data is None or len(response.data) == 0:
            logger.info("📭 No reels found for the given filters")
            return {'reels': [], 'isLastPage': True}

        data = response.data
        logger.info(f"📦 Raw data received: {len(data)} items")

        # Check if there are more pages based on whether we got more than requested
        has_more_data = len(data) > limit

        # Apply random ordering if needed
        if filters.random_order and filters.session_id:
            data = self._apply_random_ordering(data, filters.session_id, limit)
        else:
            data = data[:limit] if data else []  # Trim to exact limit, handle None case

        # Transform for frontend - filter out None items first
        valid_data = [item for item in data if item is not None]
        transformed_reels = []
        for item in valid_data:
            try:
                transformed = self._transform_content_for_frontend(item)
                if transformed is not None:
                    transformed_reels.append(transformed)
            except Exception as e:
                logger.error(f"❌ Error transforming content item: {e}")
                continue

        # Check if this is the last page
        is_last_page = not has_more_data

        logger.info(f"✅ Returned {len(transformed_reels)} reels, isLastPage: {is_last_page}")

        return {
            'reels': transformed_reels,
            'isLastPage': is_last_page
        }

    except Exception as e:
        logger.error(f"❌ Error getting reels: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# FastAPI endpoint definition (lines 1099-1164)
@app.get("/api/reels")
async def get_reels(
    search: Optional[str] = Query(None),
    primary_categories: Optional[str] = Query(None),
    secondary_categories: Optional[str] = Query(None),
    tertiary_categories: Optional[str] = Query(None),
    keywords: Optional[str] = Query(None),
    min_outlier_score: Optional[float] = Query(None),
    max_outlier_score: Optional[float] = Query(None),
    min_views: Optional[int] = Query(None),
    max_views: Optional[int] = Query(None),
    min_followers: Optional[int] = Query(None),
    max_followers: Optional[int] = Query(None),
    min_likes: Optional[int] = Query(None),
    max_likes: Optional[int] = Query(None),
    min_comments: Optional[int] = Query(None),
    max_comments: Optional[int] = Query(None),
    date_range: Optional[str] = Query(None),
    is_verified: Optional[bool] = Query(None),
    random_order: Optional[bool] = Query(False),
    session_id: Optional[str] = Query(None),
    sort_by: Optional[str] = Query(None, regex="^(popular|views|likes|comments|recent|oldest|followers|account_engagement|content_engagement)$"),
    excluded_usernames: Optional[str] = Query(None),
    account_types: Optional[str] = Query(None),
    content_types: Optional[str] = Query(None),
    languages: Optional[str] = Query(None),
    content_styles: Optional[str] = Query(None),
    min_account_engagement_rate: Optional[float] = Query(None, ge=0.0, le=100.0),
    max_account_engagement_rate: Optional[float] = Query(None, ge=0.0, le=100.0),
    limit: int = Query(24, ge=1, le=100),
    offset: int = Query(0, ge=0),
    api_instance: ViralSpotAPI = Depends(get_api)
):
    """Get reels with filtering and pagination"""
    filters = ReelFilter(
        search=search,
        primary_categories=primary_categories,
        secondary_categories=secondary_categories,
        tertiary_categories=tertiary_categories,
        keywords=keywords,
        min_outlier_score=min_outlier_score,
        max_outlier_score=max_outlier_score,
        min_views=min_views,
        max_views=max_views,
        min_followers=min_followers,
        max_followers=max_followers,
        min_likes=min_likes,
        max_likes=max_likes,
        min_comments=min_comments,
        max_comments=max_comments,
        date_range=date_range,
        is_verified=is_verified,
        random_order=random_order,
        session_id=session_id,
        sort_by=sort_by,
        excluded_usernames=excluded_usernames,
        account_types=account_types,
        content_types=content_types,
        languages=languages,
        content_styles=content_styles,
        min_account_engagement_rate=min_account_engagement_rate,
        max_account_engagement_rate=max_account_engagement_rate
    )
    result = await api_instance.get_reels(filters, limit, offset)
    return APIResponse(success=True, data=result)
```

**Line-by-Line Explanation:**

1.  **`ReelFilter` Model**: A comprehensive Pydantic model that validates and structures all 29 possible filter parameters. This keeps the endpoint signature clean and provides automatic validation.

2.  **`logger.info(...)` statements**: Extensive logging throughout the method for debugging and monitoring performance.

3.  **`_build_content_query(filters, limit + 1, offset)`**: The core method that dynamically constructs a Supabase query. It requests one extra item (`limit + 1`) to efficiently determine if there are more pages without a separate count query.

4.  **Complex JOIN Query**: The query includes a sophisticated JOIN with the `primary_profiles` table to get profile information:

```sql
SELECT *, primary_profiles!profile_id (username, profile_name, bio, followers, profile_image_url, profile_image_path, is_verified, account_type)
```

5.  **Robust Error Handling**: Multiple layers of null checks and error handling to prevent crashes from malformed data.

6.  **`has_more_data = len(data) > limit`**: Pagination logic that checks if we received more items than requested, indicating there's another page.

7.  **`_apply_random_ordering(...)`**: Implements session-based consistent randomization using MD5 hashing and tracks seen items to avoid duplicates across pagination.

8.  **`_transform_content_for_frontend(...)`**: Complex transformation method that:

-   Handles CDN URLs for thumbnails and profile images
-   Provides multiple field aliases for frontend compatibility
-   Formats numbers (1.2M, 45K format)
-   Handles missing profile data with fallback lookups
-   Creates a comprehensive 40+ field response object

9.  **Individual Parameter Declaration**: Instead of using a dependency injection pattern, each query parameter is explicitly declared with validation rules (regex patterns, min/max values).

10. **Manual Filter Object Construction**: The endpoint manually constructs the `ReelFilter` object from all the individual parameters, providing full control over the validation process.

### Key Helper Methods

#### `_build_content_query()` Method (lines 135-330)

This is the most complex part of the implementation. It dynamically builds a Supabase query with:

```python
def _build_content_query(self, filters: ReelFilter, limit: int, offset: int):
    """Build Supabase query for content with filters"""
    # Base query with JOIN to get profile data
    query = self.supabase.client.table('content').select('''
        *,
        primary_profiles!profile_id (
            username, profile_name, bio, followers, profile_image_url,
            profile_image_path, is_verified, account_type
        )
    ''')

    # Dynamic filter building:
    # 1. Search filter (searches description and username)
    if filters.search:
        search_term = f"%{filters.search}%"
        query = query.or_(f"description.ilike.{search_term},username.ilike.{search_term}")

    # 2. Category filters (comma-separated lists)
    if filters.primary_categories:
        categories = [cat.strip() for cat in filters.primary_categories.split(',')]
        query = query.in_('primary_category', categories)

    # 3. Keyword search across multiple fields
    if filters.keywords:
        keywords = [kw.strip() for kw in filters.keywords.split(',')]
        keyword_filters = []
        for keyword in keywords:
            keyword_pattern = f"%{keyword}%"
            keyword_filters.extend([
                f"keyword_1.ilike.{keyword_pattern}",
                f"keyword_2.ilike.{keyword_pattern}",
                f"keyword_3.ilike.{keyword_pattern}",
                f"keyword_4.ilike.{keyword_pattern}",
                f"description.ilike.{keyword_pattern}"
            ])
        if keyword_filters:
            query = query.or_(','.join(keyword_filters))

    # 4. Numeric range filters
    if filters.min_views is not None:
        query = query.gte('view_count', filters.min_views)
    if filters.max_views is not None:
        query = query.lte('view_count', filters.max_views)

    # 5. Profile-based filters (requires JOIN data)
    if filters.min_followers is not None:
        query = query.gte('primary_profiles.followers', filters.min_followers)

    # 6. Exclusion filters
    if filters.excluded_usernames:
        excluded_users = [u.strip() for u in filters.excluded_usernames.split(',')]
        query = query.not_.in_('username', excluded_users)

    # 7. Sorting logic
    if filters.sort_by == "views":
        query = query.order('view_count', desc=True)
    elif filters.sort_by == "recent":
        query = query.order('date_posted', desc=True)
    else:  # Default: "popular"
        query = query.order('outlier_score', desc=True).order('view_count', desc=True)

    # 8. Pagination
    return query.range(offset, offset + limit - 1)
```

#### `_apply_random_ordering()` Method (lines 334-360)

Implements consistent session-based randomization:

```python
def _apply_random_ordering(self, data: List[Dict], session_id: str, limit: int) -> List[Dict]:
    """Apply consistent random ordering for a session"""
    if not session_id:
        return data

    # Create a hash-based seed for consistent randomization
    seed = hashlib.md5(session_id.encode()).hexdigest()
    random.seed(seed)

    # If we have seen data for this session, exclude it
    if session_id in session_storage:
        seen_ids = session_storage[session_id]
        data = [item for item in data if item['content_id'] not in seen_ids]
    else:
        session_storage[session_id] = set()

    # Randomize the remaining data
    random.shuffle(data)

    # Take only what we need
    result = data[:limit]

    # Track seen items to avoid duplicates in future requests
    for item in result:
        session_storage[session_id].add(item['content_id'])

    return result
```

#### `_transform_content_for_frontend()` Method (lines 362-457)

Comprehensive data transformation with 40+ output fields:

```python
def _transform_content_for_frontend(self, content_item: Dict) -> Dict:
    """Transform Supabase content to frontend format"""
    # Handle CDN URLs for thumbnails
    thumbnail_url = None
    if content_item.get('thumbnail_path'):
        thumbnail_url = self.supabase.client.storage.from_('content-thumbnails').get_public_url(content_item['thumbnail_path'])

    # Handle profile data from JOIN
    profile = content_item.get('primary_profiles', {}) or {}

    # Fallback profile lookup if JOIN failed
    if not profile.get('profile_name'):
        username = content_item.get('username')
        if username:
            lookup = self.supabase.client.table('primary_profiles').select('*').eq('username', username).limit(1).execute()
            if lookup.data:
                profile = lookup.data[0]

    # Build comprehensive response object
    return {
        'id': content_item.get('content_id', ''),
        'content_id': content_item.get('content_id', ''),
        'shortcode': content_item.get('shortcode', ''),
        'url': content_item.get('url', ''),
        'description': content_item.get('description', ''),
        'thumbnail_url': thumbnail_url,
        'view_count': content_item.get('view_count', 0),
        'like_count': content_item.get('like_count', 0),
        'comment_count': content_item.get('comment_count', 0),
        'outlier_score': content_item.get('outlier_score', 0),
        'outlierScore': f"{content_item.get('outlier_score', 0):.1f}x",  # Formatted
        'date_posted': content_item.get('date_posted'),
        'username': content_item.get('username'),
        'profile_name': profile.get('profile_name', ''),
        'followers': profile.get('followers', 0),
        'is_verified': profile.get('is_verified', False),
        # Formatted numbers for display
        'views': self._format_number(content_item.get('view_count', 0)),
        'likes': self._format_number(content_item.get('like_count', 0)),
        'comments': self._format_number(content_item.get('comment_count', 0)),
        # ... 20+ more fields for frontend compatibility
    }
```

### Performance Optimizations

1. **Single Query with JOIN**: Instead of separate queries for content and profiles, uses a single query with JOIN for better performance.

2. **Efficient Pagination**: Uses `limit + 1` technique to check for more pages without expensive COUNT queries.

3. **CDN Integration**: Handles Supabase Storage CDN URLs for images and thumbnails.

4. **Session-based Randomization**: Implements consistent random ordering that remembers what users have seen.

5. **Comprehensive Error Handling**: Multiple layers of null checks and fallback mechanisms.

### Nest.js (Mongoose)

```typescript
// DTO for validation (equivalent to ReelFilter)
export class GetReelsDto {
    @IsOptional()
    @IsString()
    search?: string;

    @IsOptional()
    @IsString()
    primary_categories?: string;

    @IsOptional()
    @IsString()
    secondary_categories?: string;

    @IsOptional()
    @IsString()
    tertiary_categories?: string;

    @IsOptional()
    @IsString()
    keywords?: string;

    @IsOptional()
    @IsNumber()
    @Min(0)
    min_outlier_score?: number;

    @IsOptional()
    @IsNumber()
    @Min(0)
    max_outlier_score?: number;

    @IsOptional()
    @IsInt()
    @Min(0)
    min_views?: number;

    @IsOptional()
    @IsInt()
    @Min(0)
    max_views?: number;

    @IsOptional()
    @IsInt()
    @Min(0)
    min_followers?: number;

    @IsOptional()
    @IsInt()
    @Min(0)
    max_followers?: number;

    @IsOptional()
    @IsInt()
    @Min(0)
    min_likes?: number;

    @IsOptional()
    @IsInt()
    @Min(0)
    max_likes?: number;

    @IsOptional()
    @IsInt()
    @Min(0)
    min_comments?: number;

    @IsOptional()
    @IsInt()
    @Min(0)
    max_comments?: number;

    @IsOptional()
    @IsString()
    date_range?: string;

    @IsOptional()
    @IsBoolean()
    @Transform(({ value }) => value === "true")
    is_verified?: boolean;

    @IsOptional()
    @IsBoolean()
    @Transform(({ value }) => value === "true")
    random_order?: boolean;

    @IsOptional()
    @IsString()
    session_id?: string;

    @IsOptional()
    @IsIn([
        "popular",
        "views",
        "likes",
        "comments",
        "recent",
        "oldest",
        "followers",
        "account_engagement",
        "content_engagement",
    ])
    sort_by?: string;

    @IsOptional()
    @IsString()
    excluded_usernames?: string;

    @IsOptional()
    @IsString()
    account_types?: string;

    @IsOptional()
    @IsString()
    content_types?: string;

    @IsOptional()
    @IsString()
    languages?: string;

    @IsOptional()
    @IsString()
    content_styles?: string;

    @IsOptional()
    @IsNumber()
    @Min(0)
    @Max(100)
    min_account_engagement_rate?: number;

    @IsOptional()
    @IsNumber()
    @Min(0)
    @Max(100)
    max_account_engagement_rate?: number;

    @IsOptional()
    @IsInt()
    @Min(1)
    @Max(100)
    limit?: number = 24;

    @IsOptional()
    @IsInt()
    @Min(0)
    offset?: number = 0;
}

// In your content.controller.ts
@Controller("api")
export class ContentController {
    constructor(private readonly contentService: ContentService) {}

    @Get("/reels")
    async getReels(@Query() queryParams: GetReelsDto) {
        const result = await this.contentService.getReels(queryParams);
        return { success: true, data: result };
    }
}

// In your content.service.ts
@Injectable()
export class ContentService {
    constructor(
        @InjectModel(Content.name) private contentModel: Model<ContentDocument>,
        @InjectModel(PrimaryProfile.name)
        private profileModel: Model<PrimaryProfileDocument>,
        @Inject("CACHE_MANAGER") private cacheManager: Cache // For session storage
    ) {}

    async getReels(filters: GetReelsDto): Promise<any> {
        const { limit = 24, offset = 0 } = filters;

        // 1. Build MongoDB aggregation pipeline for complex filtering
        const pipeline: any[] = [];

        // Match stage - build query conditions
        const matchConditions: any = {};

        // Search filter (equivalent to PostgreSQL ilike)
        if (filters.search) {
            matchConditions.$or = [
                { description: { $regex: filters.search, $options: "i" } },
                { username: { $regex: filters.search, $options: "i" } },
            ];
        }

        // Category filters
        if (filters.primary_categories) {
            const categories = filters.primary_categories
                .split(",")
                .map((c) => c.trim());
            matchConditions.primary_category = { $in: categories };
        }

        if (filters.secondary_categories) {
            const categories = filters.secondary_categories
                .split(",")
                .map((c) => c.trim());
            matchConditions.secondary_category = { $in: categories };
        }

        // Keyword search across multiple fields
        if (filters.keywords) {
            const keywords = filters.keywords.split(",").map((k) => k.trim());
            const keywordConditions = [];

            keywords.forEach((keyword) => {
                const regex = { $regex: keyword, $options: "i" };
                keywordConditions.push(
                    { keyword_1: regex },
                    { keyword_2: regex },
                    { keyword_3: regex },
                    { keyword_4: regex },
                    { description: regex }
                );
            });

            if (keywordConditions.length > 0) {
                matchConditions.$or = matchConditions.$or
                    ? [...matchConditions.$or, ...keywordConditions]
                    : keywordConditions;
            }
        }

        // Numeric range filters
        if (filters.min_views !== undefined) {
            matchConditions.view_count = {
                ...matchConditions.view_count,
                $gte: filters.min_views,
            };
        }
        if (filters.max_views !== undefined) {
            matchConditions.view_count = {
                ...matchConditions.view_count,
                $lte: filters.max_views,
            };
        }

        if (filters.min_likes !== undefined) {
            matchConditions.like_count = {
                ...matchConditions.like_count,
                $gte: filters.min_likes,
            };
        }
        if (filters.max_likes !== undefined) {
            matchConditions.like_count = {
                ...matchConditions.like_count,
                $lte: filters.max_likes,
            };
        }

        // Exclusion filters
        if (filters.excluded_usernames) {
            const excludedUsers = filters.excluded_usernames
                .split(",")
                .map((u) => u.trim());
            matchConditions.username = { $nin: excludedUsers };
        }

        // Content type filter
        if (filters.content_types) {
            const types = filters.content_types.split(",").map((t) => t.trim());
            matchConditions.content_type = { $in: types };
        }

        // Language filter
        if (filters.languages) {
            const languages = filters.languages.split(",").map((l) => l.trim());
            matchConditions.language = { $in: languages };
        }

        // Add match stage if we have conditions
        if (Object.keys(matchConditions).length > 0) {
            pipeline.push({ $match: matchConditions });
        }

        // 2. Lookup stage (equivalent to JOIN with primary_profiles)
        pipeline.push({
            $lookup: {
                from: "primary_profiles",
                localField: "profile_id",
                foreignField: "_id",
                as: "profile",
            },
        });

        // Unwind the profile array (since it's a 1:1 relationship)
        pipeline.push({
            $unwind: {
                path: "$profile",
                preserveNullAndEmptyArrays: true,
            },
        });

        // 3. Additional filtering based on profile data
        const profileMatchConditions: any = {};

        if (filters.min_followers !== undefined) {
            profileMatchConditions["profile.followers"] = {
                ...profileMatchConditions["profile.followers"],
                $gte: filters.min_followers,
            };
        }
        if (filters.max_followers !== undefined) {
            profileMatchConditions["profile.followers"] = {
                ...profileMatchConditions["profile.followers"],
                $lte: filters.max_followers,
            };
        }

        if (filters.is_verified !== undefined) {
            profileMatchConditions["profile.is_verified"] = filters.is_verified;
        }

        if (filters.account_types) {
            const types = filters.account_types.split(",").map((t) => t.trim());
            profileMatchConditions["profile.account_type"] = { $in: types };
        }

        // Add profile-based filtering
        if (Object.keys(profileMatchConditions).length > 0) {
            pipeline.push({ $match: profileMatchConditions });
        }

        // 4. Sorting
        let sortStage: any = {};

        switch (filters.sort_by) {
            case "views":
                sortStage = { view_count: -1 };
                break;
            case "likes":
                sortStage = { like_count: -1 };
                break;
            case "comments":
                sortStage = { comment_count: -1 };
                break;
            case "recent":
                sortStage = { date_posted: -1 };
                break;
            case "oldest":
                sortStage = { date_posted: 1 };
                break;
            case "followers":
                sortStage = { "profile.followers": -1 };
                break;
            default: // 'popular'
                sortStage = { outlier_score: -1, view_count: -1 };
        }

        pipeline.push({ $sort: sortStage });

        // 5. Pagination
        pipeline.push({ $skip: offset });
        pipeline.push({ $limit: limit + 1 }); // Get one extra to check for more pages

        // 6. Execute aggregation
        const results = await this.contentModel.aggregate(pipeline).exec();

        // 7. Handle random ordering if requested
        let processedResults = results;
        if (filters.random_order && filters.session_id) {
            processedResults = await this.applyRandomOrdering(
                results,
                filters.session_id,
                limit
            );
        } else {
            processedResults = results.slice(0, limit);
        }

        // 8. Check for more pages
        const hasMore = results.length > limit;

        // 9. Transform results for frontend
        const transformedReels = processedResults.map((item) =>
            this.transformContentForFrontend(item)
        );

        return {
            reels: transformedReels,
            isLastPage: !hasMore,
        };
    }

    private async applyRandomOrdering(
        data: any[],
        sessionId: string,
        limit: number
    ): Promise<any[]> {
        // Create consistent seed from session ID
        const seed = this.createHashSeed(sessionId);

        // Get seen items from cache
        const cacheKey = `random_session:${sessionId}`;
        const seenIds = (await this.cacheManager.get<string[]>(cacheKey)) || [];

        // Filter out seen items
        const unseenData = data.filter(
            (item) => !seenIds.includes(item.content_id)
        );

        // Shuffle with consistent seed
        const shuffled = this.shuffleWithSeed(unseenData, seed);

        // Take only what we need
        const result = shuffled.slice(0, limit);

        // Update seen items in cache
        const newSeenIds = [
            ...seenIds,
            ...result.map((item) => item.content_id),
        ];
        await this.cacheManager.set(cacheKey, newSeenIds, { ttl: 3600 }); // 1 hour TTL

        return result;
    }

    private createHashSeed(sessionId: string): number {
        // Simple hash function to create consistent seed
        let hash = 0;
        for (let i = 0; i < sessionId.length; i++) {
            const char = sessionId.charCodeAt(i);
            hash = (hash << 5) - hash + char;
            hash = hash & hash; // Convert to 32-bit integer
        }
        return Math.abs(hash);
    }

    private shuffleWithSeed(array: any[], seed: number): any[] {
        const shuffled = [...array];
        let currentIndex = shuffled.length;

        // Use seed to create predictable randomness
        let random = seed;

        while (currentIndex !== 0) {
            // Generate pseudo-random number
            random = (random * 9301 + 49297) % 233280;
            const randomIndex = Math.floor((random / 233280) * currentIndex);
            currentIndex--;

            // Swap elements
            [shuffled[currentIndex], shuffled[randomIndex]] = [
                shuffled[randomIndex],
                shuffled[currentIndex],
            ];
        }

        return shuffled;
    }

    private transformContentForFrontend(item: any): any {
        const profile = item.profile || {};

        return {
            id: item.content_id,
            content_id: item.content_id,
            shortcode: item.shortcode,
            url: item.url,
            description: item.description,
            title: item.description, // Alias
            thumbnail_url: item.thumbnail_url,
            view_count: item.view_count || 0,
            like_count: item.like_count || 0,
            comment_count: item.comment_count || 0,
            outlier_score: item.outlier_score || 0,
            outlierScore: `${(item.outlier_score || 0).toFixed(1)}x`,
            date_posted: item.date_posted,
            username: item.username,
            profile: `@${item.username}`,
            profile_name: profile.profile_name || "",
            bio: profile.bio || "",
            followers: profile.followers || 0,
            profile_followers: profile.followers || 0,
            profile_image_url: profile.profile_image_url,
            profileImage: profile.profile_image_url,
            is_verified: profile.is_verified || false,
            primary_category: item.primary_category,
            secondary_category: item.secondary_category,
            tertiary_category: item.tertiary_category,
            keyword_1: item.keyword_1,
            keyword_2: item.keyword_2,
            keyword_3: item.keyword_3,
            keyword_4: item.keyword_4,
            content_style: item.content_style,
            // Formatted numbers
            views: this.formatNumber(item.view_count || 0),
            likes: this.formatNumber(item.like_count || 0),
            comments: this.formatNumber(item.comment_count || 0),
        };
    }

    private formatNumber(num: number): string {
        if (num >= 1000000) {
            return `${(num / 1000000).toFixed(1)}M`;
        } else if (num >= 1000) {
            return `${(num / 1000).toFixed(1)}K`;
        }
        return num.toString();
    }
}
```

### Key Differences in Nest.js Implementation

1. **MongoDB Aggregation Pipeline**: Uses MongoDB's powerful aggregation framework instead of SQL-like queries, providing more flexibility for complex filtering.

2. **DTO Validation**: Uses class-validator decorators for comprehensive input validation, replacing Pydantic models.

3. **Cache Manager**: Uses Nest.js cache manager (Redis/Memory) instead of in-memory dictionary for session storage.

4. **Aggregation with $lookup**: Replaces SQL JOINs with MongoDB's `$lookup` stage for profile data.

5. **Consistent Randomization**: Implements a deterministic shuffle algorithm using session-based seeds.

6. **Type Safety**: Full TypeScript support with proper typing throughout the implementation.

## Responses

### Success: 200 OK

Returns a paginated list of reel objects.

**Example Response:**

```json
{
    "success": true,
    "data": {
        "reels": [
            {
                "id": "reel_xyz",
                "caption": "Check out this amazing reel!",
                "view_count": 987654,
                "like_count": 98765
                // ... other reel data
            }
        ],
        "isLastPage": false
    }
}
```

## Implementation Details

-   **File:** `backend_api.py`
-   **Function:** `get_reels(filters: ReelFilter, limit: int, offset: int)`
-   **Pydantic Model:** `ReelFilter` is used to manage the large number of filter parameters.
-   **Database Table:** `content`, with joins to `primary_profiles`.
