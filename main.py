#!/usr/bin/env python3
"""
ViralSpot Main Startup Script
============================

Starts both the queue processor and FastAPI backend server simultaneously.
This combines the functionality of queue_processor.py and start_backend.py.
"""

import os
import sys
import asyncio
import signal
import threading
import logging
from pathlib import Path
from contextlib import asynccontextmanager

# Disable noisy HTTP logs from httpx
logging.getLogger("httpx").setLevel(logging.WARNING)

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

class MainApplication:
    """Main application that manages both queue processor and API server"""
    
    def __init__(self):
        self.queue_processor = None
        self.viral_processor = None
        self.api_server_task = None
        self.shutdown_event = None  # Will be created in async context
        self.running = True
        self.shutting_down = False
        
    async def start_queue_processor(self):
        """Start the queue processor"""
        try:
            from queue_processor import QueueProcessor
            
            print("🔄 Starting Queue Processor...")
            self.queue_processor = QueueProcessor()
            # Disable signal handling since main.py manages signals
            await self.queue_processor.start_processing(setup_signals=False)
        except Exception as e:
            print(f"❌ Queue Processor failed: {e}")
            if self.shutdown_event:
                self.shutdown_event.set()
    
    async def start_viral_processor(self):
        """Start the viral ideas processor"""
        try:
            from viral_ideas_processor import ViralIdeasQueueManager
            
            print("🎯 Starting Viral Ideas Processor...")
            self.viral_processor = ViralIdeasQueueManager()
            
            # Adaptive processing loop - responsive when needed, efficient when idle
            empty_checks = 0
            while self.running:
                try:
                    # Process pending items
                    had_items = await self.viral_processor.process_pending_items()
                    
                    if had_items:
                        # Found items - reset counter and check again quickly
                        empty_checks = 0
                        await asyncio.sleep(0.5)  # Quick check for more items
                    else:
                        # No items found - implement adaptive backoff
                        empty_checks += 1
                        
                        if empty_checks <= 5:
                            # First 5 empty checks: fast polling (2 seconds)
                            await asyncio.sleep(2)
                        elif empty_checks <= 15:
                            # Next 10 empty checks: medium polling (5 seconds)
                            await asyncio.sleep(5)
                        else:
                            # After 15 empty checks: slower polling (10 seconds)
                            await asyncio.sleep(10)
                    
                except Exception as e:
                    print(f"⚠️ Error in viral processor loop: {e}")
                    # Wait longer on error to avoid spam
                    await asyncio.sleep(5)
                
        except Exception as e:
            print(f"❌ Viral Ideas Processor failed: {e}")
            if self.shutdown_event:
                self.shutdown_event.set()
    
    async def start_api_server(self):
        """Start the FastAPI server"""
        try:
            import uvicorn
            
            print("🌐 Starting FastAPI Server...")
            
            # Create uvicorn config
            config = uvicorn.Config(
                "backend_api:app",
                host="0.0.0.0",
                port=8000,
                reload=False,  # Disable reload since we're managing lifecycle
                access_log=True,
                log_level="info"
            )
            
            # Create and start server
            server = uvicorn.Server(config)
            await server.serve()
            
        except Exception as e:
            print(f"❌ API Server failed: {e}")
            if self.shutdown_event:
                self.shutdown_event.set()
    
    def setup_signal_handlers(self, loop):
        """Setup signal handlers for graceful shutdown"""
        def signal_handler(signum):
            if self.shutting_down:
                print(f"🛑 Already shutting down, ignoring signal {signum}")
                return
                
            print(f"\n🛑 Received shutdown signal {signum}")
            self.shutting_down = True
            self.running = False
            # Schedule shutdown in the event loop
            if self.shutdown_event:
                loop.call_soon_threadsafe(self.shutdown_event.set)
        
        # For Unix-like systems
        if hasattr(signal, 'SIGINT'):
            loop.add_signal_handler(signal.SIGINT, lambda: signal_handler(signal.SIGINT))
        if hasattr(signal, 'SIGTERM'):
            loop.add_signal_handler(signal.SIGTERM, lambda: signal_handler(signal.SIGTERM))
    
    def setup_windows_signal_handlers(self):
        """Setup signal handlers for Windows systems"""
        def signal_handler(signum, frame):
            if self.shutting_down:
                print(f"🛑 Already shutting down, ignoring signal {signum}")
                return
                
            print(f"\n🛑 Received shutdown signal {signum}")
            self.shutting_down = True
            self.running = False
            # Schedule shutdown
            if self.shutdown_event:
                asyncio.create_task(self._trigger_shutdown())
        
        signal.signal(signal.SIGINT, signal_handler)
        if hasattr(signal, 'SIGTERM'):
            signal.signal(signal.SIGTERM, signal_handler)
    
    async def _trigger_shutdown(self):
        """Helper to trigger shutdown event"""
        if self.shutdown_event:
            self.shutdown_event.set()
    
    async def run(self):
        """Run both services concurrently"""
        # Create shutdown event in async context
        self.shutdown_event = asyncio.Event()
        
        # Get current event loop and setup signal handlers
        loop = asyncio.get_running_loop()
        try:
            self.setup_signal_handlers(loop)
        except NotImplementedError:
            # Windows doesn't support add_signal_handler, use fallback
            self.setup_windows_signal_handlers()
        
        print("🚀 Starting ViralSpot Services...")
        print("=" * 50)
        
        try:
            # Start all three services concurrently
            queue_task = asyncio.create_task(self.start_queue_processor())
            viral_task = asyncio.create_task(self.start_viral_processor())
            api_task = asyncio.create_task(self.start_api_server())
            
            self.api_server_task = api_task
            
            print("✅ All services started successfully!")
            print("\n📍 Available API endpoints:")
            print("   GET  http://localhost:8000/api/reels")
            print("   GET  http://localhost:8000/api/filter-options")
            print("   GET  http://localhost:8000/api/profile/{username}")
            print("   GET  http://localhost:8000/api/profile/{username}/reels")
            print("   GET  http://localhost:8000/api/profile/{username}/similar")
            print("   POST http://localhost:8000/api/reset-session")
            print("   🎯 VIRAL IDEAS:")
            print("   POST http://localhost:8000/api/viral-ideas/queue")
            print("   GET  http://localhost:8000/api/viral-analysis/{queue_id}/results")
            print("   GET  http://localhost:8000/api/content/competitor/{username}")
            print("\n📚 API Documentation: http://localhost:8000/docs")
            print("🔧 Health Check: http://localhost:8000/health")
            print("\n🔄 Queue Processor: Active and monitoring queue")
            print("🎯 Viral Ideas Processor: Active and monitoring viral analysis queue")
            print("=" * 50)
            
            # Wait for shutdown signal or service failure
            await self.shutdown_event.wait()
            
        except Exception as e:
            print(f"❌ Fatal error: {e}")
        finally:
            await self.shutdown()
    
    async def shutdown(self):
        """Gracefully shutdown both services"""
        if self.shutting_down:
            return  # Already shutting down
            
        self.shutting_down = True
        print("\n🛑 Starting graceful shutdown...")
        
        # Stop processors first
        if self.queue_processor:
            print("🔄 Stopping queue processor...")
            try:
                # Set running to False to stop the processing loop
                self.queue_processor.running = False
                # Give it a moment to finish current operations
                await asyncio.sleep(1)
                print("✅ Queue processor stopped")
            except Exception as e:
                print(f"⚠️ Error stopping queue processor: {e}")
        
        if self.viral_processor:
            print("🎯 Stopping viral ideas processor...")
            try:
                # The viral processor uses the main app's running flag
                self.running = False
                # Give it a moment to finish current operations
                await asyncio.sleep(1)
                print("✅ Viral ideas processor stopped")
            except Exception as e:
                print(f"⚠️ Error stopping viral processor: {e}")
        
        # Cancel API server
        if self.api_server_task and not self.api_server_task.done():
            print("📍 Stopping API server...")
            self.api_server_task.cancel()
            try:
                await asyncio.wait_for(self.api_server_task, timeout=5.0)
            except (asyncio.CancelledError, asyncio.TimeoutError):
                print("✅ API server stopped")
            except Exception as e:
                print(f"⚠️ Error stopping API server: {e}")
        
        print("✅ All services stopped gracefully")

async def main():
    """Main startup function"""
    print("🚀 ViralSpot Main Application")
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
    
    # Start the application
    app = MainApplication()
    try:
        await app.run()
    except KeyboardInterrupt:
        print("\n👋 Application stopped by user")
    except Exception as e:
        print(f"❌ Application failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    # Fix Windows console encoding for emojis
    if sys.platform == 'win32':
        import os
        os.system('chcp 65001 >nul 2>&1')
    
    asyncio.run(main())