#!/usr/bin/env python3
"""
ViralSpot Backend Startup Script
===============================

Starts the FastAPI backend server with proper environment validation.
"""

import os
import sys
from pathlib import Path

def check_environment():
    """Check if all required environment variables are set"""
    required_vars = [
        'SUPABASE_URL',
        'SUPABASE_SERVICE_ROLE_KEY'
    ]
    
    missing_vars = []
    for var in required_vars:
        if not os.getenv(var):
            missing_vars.append(var)
    
    if missing_vars:
        print("❌ Missing required environment variables:")
        for var in missing_vars:
            print(f"   - {var}")
        print("\nPlease set these environment variables in your .env file or system environment.")
        print("Example .env file:")
        print("SUPABASE_URL=https://your-project.supabase.co")
        print("SUPABASE_SERVICE_ROLE_KEY=your-service-role-key")
        return False
    
    return True

def check_dependencies():
    """Check if required packages are installed"""
    try:
        import fastapi
        import uvicorn
        import supabase
        print("✅ All required packages are installed")
        return True
    except ImportError as e:
        print(f"❌ Missing required package: {e}")
        print("\nPlease install requirements:")
        print("pip install -r requirements_backend.txt")
        return False

def main():
    """Main startup function"""
    print("🚀 ViralSpot Backend Server Startup")
    print("=" * 40)
    
    # Load environment variables first
    try:
        from dotenv import load_dotenv
        load_dotenv()
        print("✅ Environment variables loaded")
    except ImportError:
        print("⚠️ python-dotenv not installed, using system environment")
    
    # Check environment
    if not check_environment():
        sys.exit(1)
    
    # Check dependencies
    if not check_dependencies():
        sys.exit(1)
    
    # Start the server
    print("\n🌐 Starting FastAPI server...")
    print("📍 Available endpoints:")
    print("   GET  http://localhost:8000/api/reels")
    print("   GET  http://localhost:8000/api/filter-options")
    print("   GET  http://localhost:8000/api/profile/{username}")
    print("   GET  http://localhost:8000/api/profile/{username}/reels")
    print("   GET  http://localhost:8000/api/profile/{username}/similar")
    print("   POST http://localhost:8000/api/reset-session")
    print("\n📚 API Documentation: http://localhost:8000/docs")
    print("🔧 Health Check: http://localhost:8000/health")
    print("\n" + "=" * 40)
    
    try:
        # Import uvicorn
        import uvicorn
        
        uvicorn.run(
            "backend_api:app",  # Use import string instead of importing directly
            host="0.0.0.0", 
            port=8000,
            reload=True,  # Enable auto-reload during development
            access_log=True
        )
    except KeyboardInterrupt:
        print("\n👋 Server stopped by user")
    except Exception as e:
        print(f"❌ Server failed to start: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()