#!/usr/bin/env python3
"""
Viral Ideas Processor Starter

This script starts the viral ideas queue processor either as a one-time run
or as a continuous background service.

Usage:
    python start_viral_processor.py --once    # Process queue once and exit
    python start_viral_processor.py --daemon  # Run continuously as daemon
    python start_viral_processor.py --help    # Show help

Author: AI Assistant
Date: 2024
"""

import asyncio
import argparse
import logging
import signal
import sys
import time
from datetime import datetime
from viral_ideas_processor import ViralIdeasQueueManager

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('viral_processor.log'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

class ViralProcessorService:
    """Service wrapper for viral ideas processor"""
    
    def __init__(self, interval_minutes: int = 5):
        self.queue_manager = ViralIdeasQueueManager()
        self.interval_minutes = interval_minutes
        self.running = False
        self.setup_signal_handlers()
    
    def setup_signal_handlers(self):
        """Setup signal handlers for graceful shutdown"""
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)
    
    def _signal_handler(self, signum, frame):
        """Handle shutdown signals"""
        logger.info(f"Received signal {signum}, shutting down gracefully...")
        self.running = False
    
    async def run_once(self):
        """Process queue once and exit"""
        logger.info("🚀 Starting viral ideas processor (one-time run)")
        start_time = datetime.utcnow()
        
        try:
            await self.queue_manager.process_pending_items()
            
            end_time = datetime.utcnow()
            duration = (end_time - start_time).total_seconds()
            logger.info(f"✅ Viral ideas processing completed in {duration:.2f} seconds")
            
        except Exception as e:
            logger.error(f"❌ Error during viral ideas processing: {str(e)}")
            sys.exit(1)
    
    async def run_daemon(self):
        """Run continuously as a daemon service with adaptive polling"""
        logger.info(f"🚀 Starting viral ideas processor daemon (adaptive polling: {self.interval_minutes} min base interval)")
        self.running = True
        empty_checks = 0
        
        while self.running:
            try:
                start_time = datetime.utcnow()
                
                # Process pending items and check if any were found
                had_items = await self.queue_manager.process_pending_items()
                
                end_time = datetime.utcnow()
                duration = (end_time - start_time).total_seconds()
                
                if had_items:
                    # Found items - reset counter and check again quickly
                    empty_checks = 0
                    logger.info(f"✅ Processed items in {duration:.2f}s - checking again in 10 seconds")
                    await asyncio.sleep(10)  # Quick recheck for more items
                else:
                    # No items found - implement adaptive backoff
                    empty_checks += 1
                    
                    if empty_checks <= 3:
                        # First 3 empty checks: fast polling (30 seconds)
                        sleep_time = 30
                    elif empty_checks <= 10:
                        # Next 7 empty checks: medium polling (2 minutes)
                        sleep_time = 120
                    else:
                        # After 10 empty checks: use base interval
                        sleep_time = self.interval_minutes * 60
                    
                    if empty_checks <= 1:  # Only log for first few checks to avoid spam
                        logger.info(f"✅ Queue check completed in {duration:.2f}s - no items found")
                        logger.info(f"⏰ Waiting {sleep_time} seconds until next check...")
                    
                    await asyncio.sleep(sleep_time)
                
            except Exception as e:
                logger.error(f"❌ Error during daemon processing: {str(e)}")
                if self.running:
                    logger.info("⏰ Waiting 1 minute before retry...")
                    await asyncio.sleep(60)
        
        logger.info("🛑 Viral ideas processor daemon stopped")
    
    async def check_status(self):
        """Check the status of pending queue items"""
        try:
            from supabase_integration import SupabaseManager
            supabase = SupabaseManager()
            
            # Get queue statistics
            pending_count = supabase.client.table('viral_ideas_queue').select('id', count='exact').eq('status', 'pending').execute()
            processing_count = supabase.client.table('viral_ideas_queue').select('id', count='exact').eq('status', 'processing').execute()
            completed_count = supabase.client.table('viral_ideas_queue').select('id', count='exact').eq('status', 'completed').execute()
            failed_count = supabase.client.table('viral_ideas_queue').select('id', count='exact').eq('status', 'failed').execute()
            
            print("📊 Viral Ideas Queue Status:")
            print(f"   ⏳ Pending:    {pending_count.count}")
            print(f"   🔄 Processing: {processing_count.count}")
            print(f"   ✅ Completed:  {completed_count.count}")
            print(f"   ❌ Failed:     {failed_count.count}")
            
            # Show recent items
            recent_items = supabase.client.table('viral_queue_summary').select(
                'primary_username, status, progress_percentage, current_step, submitted_at'
            ).order('submitted_at', desc=True).limit(5).execute()
            
            if recent_items.data:
                print("\n🕒 Recent Queue Items:")
                for item in recent_items.data:
                    status_emoji = {"pending": "⏳", "processing": "🔄", "completed": "✅", "failed": "❌"}.get(item['status'], "❓")
                    progress = f" ({item['progress_percentage']}%)" if item['progress_percentage'] else ""
                    current_step = f" - {item['current_step']}" if item['current_step'] else ""
                    print(f"   {status_emoji} @{item['primary_username']}{progress}{current_step}")
            
        except Exception as e:
            logger.error(f"Error checking status: {str(e)}")

def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(description='Viral Ideas Queue Processor')
    parser.add_argument('--once', action='store_true', help='Process queue once and exit')
    parser.add_argument('--daemon', action='store_true', help='Run continuously as daemon')
    parser.add_argument('--status', action='store_true', help='Check queue status and exit')
    parser.add_argument('--interval', type=float, default=0.1, help='Check interval in minutes (daemon mode only) - use 0.1 for 6 seconds')
    
    args = parser.parse_args()
    
    if not any([args.once, args.daemon, args.status]):
        parser.print_help()
        sys.exit(1)
    
    # Create service instance
    service = ViralProcessorService(interval_minutes=args.interval)
    
    try:
        if args.status:
            # Check status
            asyncio.run(service.check_status())
        elif args.once:
            # Run once
            asyncio.run(service.run_once())
        elif args.daemon:
            # Run as daemon
            asyncio.run(service.run_daemon())
            
    except KeyboardInterrupt:
        logger.info("👋 Interrupted by user")
        sys.exit(0)
    except Exception as e:
        logger.error(f"💥 Fatal error: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main()