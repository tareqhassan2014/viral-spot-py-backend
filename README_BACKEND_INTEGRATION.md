# ViralSpot Backend Integration

This document explains how to set up and run the new backend API server that connects your existing Supabase database to the frontend.

## Overview

The backend integration consists of:
- **FastAPI Server** (`backend_api.py`) - Serves all frontend API endpoints
- **Existing Data Pipeline** - Your current Instagram data collection system
- **Supabase Database** - Already set up with your schema

## Quick Start

### 1. Install Backend Dependencies

```bash
pip install -r requirements_backend.txt
```

### 2. Set Environment Variables

Create a `.env` file or set these environment variables:

```bash
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_SERVICE_ROLE_KEY=your-service-role-key
```

### 3. Start the Backend Server

```bash
python start_backend.py
```

Or run directly:

```bash
python backend_api.py
```

The server will start on `http://localhost:8000`

### 4. Start Your Frontend

Your frontend should now connect to the backend automatically (it's already configured to use `localhost:8000`).

## API Endpoints

The backend provides all the endpoints your frontend expects:

### Content & Filtering
- `GET /api/reels` - Get reels with advanced filtering
- `GET /api/filter-options` - Get available categories, keywords, usernames

### Profile Management  
- `GET /api/profile/{username}` - Get profile data
- `GET /api/profile/{username}/reels` - Get profile's reels
- `GET /api/profile/{username}/similar` - **Get 20 similar profiles** ⭐

### Utilities
- `POST /api/reset-session` - Reset random mode session
- `GET /health` - Health check
- `GET /docs` - Interactive API documentation

## Similar Profiles Integration

The backend properly integrates your similar profiles data:

### Data Source
- Uses `secondary_profiles` table
- Connected via `discovered_by_id` foreign key
- Shows up to 20 similar profiles per primary profile

### Frontend Display
- **Profile page "Similar" tab** - Shows similar profiles with analytics
- **Similarity scoring** - Ranks profiles by relevance
- **Profile linking** - Click to view similar profile details

## Features

### Advanced Filtering
- Search by content, username, profile name
- Filter by categories (primary, secondary, tertiary)
- Filter by keywords (searches all keyword fields)
- Numeric filters (views, likes, comments, followers, outlier score)
- Date range filtering
- Verified account filtering

### Random Mode
- Session-based randomization (consistent per session)
- Excludes previously seen content
- Perfect for discovery

### Image Handling
- Automatically serves images from Supabase storage
- Falls back to original URLs if storage unavailable
- Handles both profile images and content thumbnails

### Performance
- Efficient database queries with proper joins
- Pagination support
- Caching for filter options

## Architecture

```
Frontend (React/Next.js)
    ↓ HTTP requests
Backend API (FastAPI)
    ↓ Database queries  
Supabase Database
    ↑ Data populated by
Data Pipeline (Python)
```

## Data Flow

1. **Data Collection**: Your existing Python pipeline collects Instagram data
2. **Database Storage**: Data is stored in Supabase (primary_profiles, secondary_profiles, content)
3. **API Layer**: FastAPI server queries database and formats for frontend
4. **Frontend Display**: React app displays data with filtering, similar profiles, etc.

## Testing the Integration

### 1. Check API Health
```bash
curl http://localhost:8000/health
```

### 2. Test Reels Endpoint
```bash
curl http://localhost:8000/api/reels?limit=5
```

### 3. Test Similar Profiles
```bash
curl http://localhost:8000/api/profile/mindset.therapy/similar
```

## Troubleshooting

### "API not available" Error
- Check environment variables are set correctly
- Verify Supabase URL and service role key
- Ensure Supabase integration works: `python -c "from supabase_integration import SupabaseManager; SupabaseManager()"`

### No Data Returned
- Check if your database has data: Look at your Supabase dashboard
- Verify table names match the schema
- Check database permissions

### CORS Issues
- Backend has CORS enabled for all origins
- In production, update CORS settings in `backend_api.py`

### Images Not Loading
- Check Supabase storage bucket permissions
- Verify bucket names in environment variables
- Ensure images were uploaded during data collection

## Production Deployment

### Environment Variables
```bash
SUPABASE_URL=your-production-supabase-url
SUPABASE_SERVICE_ROLE_KEY=your-production-key
```

### CORS Configuration
Update the CORS middleware in `backend_api.py`:
```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://your-frontend-domain.com"],
    allow_credentials=True,
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)
```

### Server Deployment
- Use a production ASGI server like `gunicorn`
- Set up proper logging and monitoring
- Configure environment variables securely

## Similar Profiles Features

Your similar profiles are now fully integrated:

### Profile Page Similar Tab
- Shows similar profiles with similarity scores
- Displays follower counts, categories, bios
- Links to view each similar profile
- Shows analysis summary (profiles compared, keywords analyzed, etc.)

### Data Accuracy
- Uses actual similar profiles from your database
- Maintains discovery relationships (`discovered_by`)
- Preserves similarity rankings

### Performance
- Efficient queries with proper indexes
- Limited to 20 profiles per request (configurable)
- Fast loading with optimized data transformations

The backend is now ready to serve your frontend with all the Instagram data you've collected! 🚀