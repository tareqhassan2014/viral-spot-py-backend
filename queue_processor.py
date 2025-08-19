#!/usr/bin/env python3
"""
Production-Level Instagram Scraping Queue Processor
===================================================

Manages a CSV-based priority queue system for Instagram profile scraping requests.
Integrates with the existing PrimaryProfileFetch.py system and implements
intelligent priority handling.

Features:
- HIGH priority requests pause LOW priority processing
- Thread-safe CSV operations with file locking
- Robust error handling and recovery
- Real-time queue monitoring and statistics
- Graceful shutdown and resume capabilities
- Integration with existing PrimaryProfileFetch system

Queue CSV Schema:
- username: Instagram username to scrape
- source: Where request originated (crawler, manual, api, etc.)
- priority: HIGH or LOW
- timestamp: When request was added (ISO format)
- status: PENDING, PROCESSING, COMPLETED, FAILED, PAUSED
- attempts: Number of processing attempts
- last_attempt: Timestamp of last processing attempt
- error_message: Last error if failed
- request_id: Unique identifier for tracking
"""

import asyncio
import csv
import json
import time
import uuid
import threading
import signal
import sys
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Tuple, Set
from dataclasses import dataclass, asdict
from pathlib import Path
from enum import Enum
import logging
import platform
import os

# Import our existing profile fetcher
from PrimaryProfileFetch import InstagramDataPipeline
from config import (
    KEEP_LOCAL_CSV,
    MAX_CONCURRENT_LOW_PRIORITY,
    MAX_CONCURRENT_HIGH_PRIORITY
)

# Import Supabase integration
try:
    from supabase_integration import SupabaseManager
    SUPABASE_AVAILABLE = True
except ImportError as e:
    SUPABASE_AVAILABLE = False
    print(f"⚠️ Supabase integration not available: {e}")
    SupabaseManager = None

class Priority(Enum):
    HIGH = "HIGH"
    LOW = "LOW"

class Status(Enum):
    PENDING = "PENDING"
    PROCESSING = "PROCESSING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    PAUSED = "PAUSED"

@dataclass
class QueueItem:
    """Single queue item representation"""
    username: str
    source: str
    priority: Priority
    timestamp: str
    status: Status = Status.PENDING
    attempts: int = 0
    last_attempt: Optional[str] = None
    error_message: Optional[str] = None
    request_id: str = None
    
    def __post_init__(self):
        if self.request_id is None:
            self.request_id = str(uuid.uuid4())[:8]

class QueueManager:
    """Thread-safe CSV queue manager with file locking"""
    
    def __init__(self, csv_file_path: str = "queue.csv"):
        self.csv_file_path = csv_file_path
        self.lock = threading.RLock()
        self._ensure_csv_exists()
        
    def _ensure_csv_exists(self):
        """Create CSV file with headers if it doesn't exist"""
        # Always create CSV for queue operations (queue needs to work)
        if not Path(self.csv_file_path).exists():
            try:
                with open(self.csv_file_path, 'w', newline='', encoding='utf-8') as f:
                    writer = csv.DictWriter(f, fieldnames=[
                        'username', 'source', 'priority', 'timestamp', 'status',
                        'attempts', 'last_attempt', 'error_message', 'request_id'
                    ])
                    writer.writeheader()
                logging.info(f"✅ Created queue CSV file: {self.csv_file_path}")
            except Exception as e:
                logging.error(f"❌ Failed to create queue CSV: {e}")
    
    def _safe_file_operation(self, operation_func, mode='r', **kwargs):
        """Simple file operation without complex locking - like PrimaryProfileFetch"""
        # For queue operations, always try to work with CSV as it's critical for functionality
        # Create the file if it doesn't exist
        if not Path(self.csv_file_path).exists():
            self._ensure_csv_exists()
            
        with self.lock:
            try:
                with open(self.csv_file_path, mode, newline='', encoding='utf-8') as f:
                    return operation_func(f, **kwargs)
            except Exception as e:
                logging.error(f"Queue file operation failed: {e}")
                return None
    
    def add_item(self, item: QueueItem) -> bool:
        """Add item to queue (thread-safe)"""
        def _write_operation(f):
            # Read existing data
            f.seek(0)
            reader = csv.DictReader(f)
            rows = list(reader)
            
            # Check for duplicates
            for row in rows:
                if row['username'].lower() == item.username.lower() and row['status'] in ['PENDING', 'PROCESSING']:
                    logging.info(f"⏭️ Skipping duplicate request for @{item.username}")
                    return False
            
            # Add new item - convert enums to strings for CSV serialization
            item_dict = asdict(item)
            item_dict['priority'] = item.priority.value if hasattr(item.priority, 'value') else str(item.priority)
            item_dict['status'] = item.status.value if hasattr(item.status, 'value') else str(item.status)
            rows.append(item_dict)
            
            # Write back to file
            with open(self.csv_file_path, 'w', newline='', encoding='utf-8') as write_f:
                if rows:
                    writer = csv.DictWriter(write_f, fieldnames=rows[0].keys())
                    writer.writeheader()
                    writer.writerows(rows)
            return True
        
        return self._safe_file_operation(_write_operation, mode='r+') or False
    
    def get_next_item(self) -> Optional[QueueItem]:
        """Get next item to process and IMMEDIATELY mark as PROCESSING to prevent race conditions"""
        def _atomic_get_and_mark_operation(f):
            reader = csv.DictReader(f)
            rows = list(reader)
            selected_item = None
            updated = False
            
            # Find HIGH priority pending items first
            for i, row in enumerate(rows):
                if row['priority'] == Priority.HIGH.value and row['status'] == Status.PENDING.value:
                    selected_item = self._create_queue_item_from_row(row)
                    # IMMEDIATELY mark as PROCESSING to prevent other calls from getting the same item
                    rows[i]['status'] = Status.PROCESSING.value
                    rows[i]['last_attempt'] = datetime.now().isoformat()
                    rows[i]['attempts'] = str(int(row.get('attempts', 0)) + 1)
                    updated = True
                    break
            
            # If no HIGH priority, find LOW priority pending items
            if not selected_item:
                for i, row in enumerate(rows):
                    if row['priority'] == Priority.LOW.value and row['status'] == Status.PENDING.value:
                        selected_item = self._create_queue_item_from_row(row)
                        # IMMEDIATELY mark as PROCESSING to prevent other calls from getting the same item
                        rows[i]['status'] = Status.PROCESSING.value
                        rows[i]['last_attempt'] = datetime.now().isoformat()
                        rows[i]['attempts'] = str(int(row.get('attempts', 0)) + 1)
                        updated = True
                        break
            
            # Write back updated rows if we found an item
            if updated and rows:
                with open(self.csv_file_path, 'w', newline='', encoding='utf-8') as write_f:
                    writer = csv.DictWriter(write_f, fieldnames=rows[0].keys())
                    writer.writeheader()
                    writer.writerows(rows)
            
            return selected_item
        
        return self._safe_file_operation(_atomic_get_and_mark_operation, mode='r+')
    
    def _create_queue_item_from_row(self, row: Dict) -> QueueItem:
        """Convert CSV row to QueueItem with proper type conversion"""
        return QueueItem(
            username=row.get('username', ''),
            source=row.get('source', ''),
            priority=Priority(row.get('priority', 'LOW')),
            timestamp=row.get('timestamp', ''),
            status=Status(row.get('status', 'PENDING')),
            attempts=int(row.get('attempts', 0)),
            last_attempt=row.get('last_attempt') if row.get('last_attempt') else None,
            error_message=row.get('error_message') if row.get('error_message') else None,
            request_id=row.get('request_id', '')
        )
    
    def update_item_status(self, request_id: str, status: Status, error_message: str = None, increment_attempts: bool = False) -> bool:
        """Update item status in queue"""
        def _update_operation(f):
            reader = csv.DictReader(f)
            rows = list(reader)
            updated = False
            
            for row in rows:
                if row['request_id'] == request_id:
                    row['status'] = status.value if hasattr(status, 'value') else str(status)
                    row['last_attempt'] = datetime.now().isoformat()
                    if error_message:
                        row['error_message'] = error_message
                    if increment_attempts:
                        row['attempts'] = str(int(row.get('attempts', 0)) + 1)
                    updated = True
                    break
            
            if updated:
                with open(self.csv_file_path, 'w', newline='', encoding='utf-8') as write_f:
                    if rows:
                        writer = csv.DictWriter(write_f, fieldnames=rows[0].keys())
                        writer.writeheader()
                        writer.writerows(rows)
            
            return updated
        
        return self._safe_file_operation(_update_operation, mode='r+') or False
    
    def pause_low_priority_items(self) -> int:
        """Pause all LOW priority items that are currently processing"""
        def _pause_operation(f):
            reader = csv.DictReader(f)
            rows = list(reader)
            paused_count = 0
            
            for row in rows:
                if (row['priority'] == Priority.LOW.value and 
                    row['status'] == Status.PROCESSING.value):
                    row['status'] = Status.PAUSED.value
                    paused_count += 1
            
            if paused_count > 0:
                with open(self.csv_file_path, 'w', newline='', encoding='utf-8') as write_f:
                    if rows:
                        writer = csv.DictWriter(write_f, fieldnames=rows[0].keys())
                        writer.writeheader()
                        writer.writerows(rows)
            
            return paused_count
        
        return self._safe_file_operation(_pause_operation, mode='r+') or 0
    
    def resume_paused_items(self) -> int:
        """Resume all paused items"""
        def _resume_operation(f):
            reader = csv.DictReader(f)
            rows = list(reader)
            resumed_count = 0
            
            for row in rows:
                if row['status'] == Status.PAUSED.value:
                    row['status'] = Status.PENDING.value
                    resumed_count += 1
            
            if resumed_count > 0:
                with open(self.csv_file_path, 'w', newline='', encoding='utf-8') as write_f:
                    if rows:
                        writer = csv.DictWriter(write_f, fieldnames=rows[0].keys())
                        writer.writeheader()
                        writer.writerows(rows)
            
            return resumed_count
        
        return self._safe_file_operation(_resume_operation, mode='r+') or 0
    
    def get_queue_stats(self) -> Dict:
        """Get current queue statistics"""
        def _stats_operation(f):
            reader = csv.DictReader(f)
            rows = list(reader)
            
            stats = {
                'total': len(rows),
                'pending': 0,
                'processing': 0,
                'completed': 0,
                'failed': 0,
                'paused': 0,
                'high_priority': 0,
                'low_priority': 0,
                'by_source': {}
            }
            
            for row in rows:
                status = row.get('status', 'PENDING')
                priority = row.get('priority', 'LOW')
                source = row.get('source', 'unknown')
                
                stats[status.lower()] = stats.get(status.lower(), 0) + 1
                stats[priority.lower() + '_priority'] = stats.get(priority.lower() + '_priority', 0) + 1
                stats['by_source'][source] = stats['by_source'].get(source, 0) + 1
            
            return stats
        
        return self._safe_file_operation(_stats_operation) or {}
    
    def has_high_priority_pending(self) -> bool:
        """Check if there are any HIGH priority pending items"""
        def _check_operation(f):
            reader = csv.DictReader(f)
            for row in reader:
                if (row.get('priority') == Priority.HIGH.value and 
                    row.get('status') == Status.PENDING.value):
                    return True
            return False
        
        return self._safe_file_operation(_check_operation) or False
    
    def get_all_items(self) -> List[QueueItem]:
        """Get all items from the queue"""
        def _get_all_operation(f):
            reader = csv.DictReader(f)
            items = []
            for row in reader:
                items.append(self._create_queue_item_from_row(row))
            return items
        
        return self._safe_file_operation(_get_all_operation) or []

class HybridQueueManager:
    """Hybrid queue manager that works with both CSV and Supabase"""
    
    def __init__(self, csv_file_path: str = "queue.csv"):
        self.csv_manager = QueueManager(csv_file_path)
        
        # Initialize Supabase manager
        try:
            if SUPABASE_AVAILABLE:
                self.supabase = SupabaseManager()
                self.use_supabase = self.supabase.use_supabase
                print(f"✅ Queue using: {'Supabase + CSV' if self.use_supabase else 'CSV only'}")
            else:
                self.supabase = None
                self.use_supabase = False
        except Exception as e:
            print(f"⚠️ Supabase not available for queue: {e}")
            self.supabase = None
            self.use_supabase = False
    
    async def add_item(self, item: QueueItem) -> bool:
        """Add item to both CSV and Supabase"""
        # Add to CSV first (as backup)
        csv_result = self.csv_manager.add_item(item)
        
        # Add to Supabase
        if self.use_supabase and self.supabase:
            try:
                # Convert enums to strings for JSON serialization
                item_dict = asdict(item)
                item_dict['priority'] = item.priority.value if hasattr(item.priority, 'value') else str(item.priority)
                item_dict['status'] = item.status.value if hasattr(item.status, 'value') else str(item.status)
                
                supabase_result = await self.supabase.save_queue_item(item_dict)
                return csv_result and supabase_result
            except Exception as e:
                logging.error(f"Failed to add to Supabase queue: {e}")
        
        return csv_result
    
    async def get_next_item(self) -> Optional[QueueItem]:
        """Get next item from Supabase or CSV"""
        if self.use_supabase and self.supabase:
            try:
                # Try Supabase first
                queue_data = await self.supabase.get_next_queue_item()
                if queue_data:
                    return QueueItem(
                        username=queue_data['username'],
                        source=queue_data['source'],
                        priority=Priority(queue_data['priority']),
                        timestamp=queue_data['timestamp'],
                        status=Status(queue_data['status']),
                        attempts=queue_data['attempts'],
                        last_attempt=queue_data.get('last_attempt'),
                        error_message=queue_data.get('error_message'),
                        request_id=queue_data['request_id']
                    )
            except Exception as e:
                logging.error(f"Failed to get from Supabase queue: {e}")
        
        # Fallback to CSV
        return self.csv_manager.get_next_item()
    
    async def update_item_status(self, request_id: str, status: Status, error_message: str = None) -> bool:
        """Update item status in both systems"""
        # Update CSV
        csv_result = self.csv_manager.update_item_status(request_id, status, error_message)
        
        # Update Supabase
        if self.use_supabase and self.supabase:
            try:
                # Need to get the queue ID first
                # For now, we'll rely on CSV as source of truth
                pass
            except Exception as e:
                logging.error(f"Failed to update Supabase queue: {e}")
        
        return csv_result
    
    async def get_queue_stats(self) -> Dict:
        """Get queue statistics"""
        if self.use_supabase and self.supabase:
            try:
                stats = await self.supabase.get_queue_stats()
                if stats:
                    return stats
            except Exception as e:
                logging.error(f"Failed to get Supabase queue stats: {e}")
        
        # Fallback to CSV stats
        return self.csv_manager.get_queue_stats()
    
    # Delegate other methods to CSV manager for compatibility
    def get_all_items(self) -> List[QueueItem]:
        return self.csv_manager.get_all_items()
    
    def has_high_priority_pending(self) -> bool:
        return self.csv_manager.has_high_priority_pending()
    
    def pause_low_priority_items(self) -> int:
        """Pause all LOW priority items that are currently processing"""
        return self.csv_manager.pause_low_priority_items()
    
    def resume_paused_items(self) -> int:
        """Resume all paused items"""
        return self.csv_manager.resume_paused_items()

class QueueProcessor:
    """Main queue processor with priority logic and Instagram integration"""
    
    def __init__(self, max_concurrent_low: int = None, max_concurrent_high: int = None):
        # Use Supabase-only queue manager instead of hybrid
        try:
            if SUPABASE_AVAILABLE:
                from supabase_integration import SupabaseManager
                self.supabase = SupabaseManager()
                self.use_supabase = self.supabase.use_supabase
                print(f"✅ Queue Processor using: {'Supabase only' if self.use_supabase else 'No database'}")
            else:
                self.supabase = None
                self.use_supabase = False
                print("⚠️ No Supabase available for queue processor")
        except Exception as e:
            print(f"⚠️ Supabase not available for queue processor: {e}")
            self.supabase = None
            self.use_supabase = False
        self.instagram_pipeline = InstagramDataPipeline()
        
        # Concurrency limits
        self.max_concurrent_low = max_concurrent_low or MAX_CONCURRENT_LOW_PRIORITY
        self.max_concurrent_high = max_concurrent_high or MAX_CONCURRENT_HIGH_PRIORITY
        
        # Processing state
        self.running = False
        self.low_priority_tasks: Set[asyncio.Task] = set()
        self.high_priority_tasks: Set[asyncio.Task] = set()
        self.shutdown_event = asyncio.Event()
        
        # Statistics
        self.stats = {
            'processed_count': 0,
            'error_count': 0,
            'start_time': None,
            'high_priority_processed': 0,
            'low_priority_processed': 0
        }
        
        # Setup logging with UTF-8 encoding for Windows
        import sys
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler('queue_processor.log', encoding='utf-8'),
                logging.StreamHandler(sys.stdout)
            ]
        )
        
        # Fix Windows console encoding for emojis
        if sys.platform == 'win32':
            import os
            os.system('chcp 65001 >nul 2>&1')
        self.logger = logging.getLogger(__name__)
    
    async def start_processing(self, setup_signals=True):
        """Start the queue processor
        
        Args:
            setup_signals: Whether to setup signal handlers. Set to False when
                          managed by another application (like main.py)
        """
        self.running = True
        self.stats['start_time'] = datetime.now()
        self.logger.info("🚀 Queue Processor started")
        
        # Setup signal handlers for graceful shutdown (only if not managed externally)
        if setup_signals:
            signal.signal(signal.SIGINT, self._signal_handler)
            signal.signal(signal.SIGTERM, self._signal_handler)
        
        try:
            await self._main_processing_loop()
        except Exception as e:
            self.logger.error(f"Fatal error in processing loop: {e}")
        finally:
            await self._graceful_shutdown()
    
    def _signal_handler(self, signum, frame):
        """Handle shutdown signals"""
        self.logger.info(f"🛑 Received shutdown signal {signum}")
        self.running = False
        asyncio.create_task(self._set_shutdown_event())
    
    async def _set_shutdown_event(self):
        """Set shutdown event in async context"""
        self.shutdown_event.set()
    
    async def _has_high_priority_pending(self) -> bool:
        """Check if there are HIGH priority items pending in Supabase"""
        if not self.use_supabase or not self.supabase:
            return False
        
        try:
            response = self.supabase.client.table('queue').select('id, username').eq('priority', 'HIGH').eq('status', 'PENDING').limit(1).execute()
            has_high = bool(response.data)
            if has_high and response.data:
                self.logger.info(f"🔴 HIGH priority item found: {response.data[0].get('username', 'unknown')}")
            return has_high
        except Exception as e:
            self.logger.error(f"Error checking high priority items: {e}")
            return False
    
    async def _get_next_supabase_item(self) -> Optional[Dict]:
        """Get next item from Supabase queue"""
        if not self.use_supabase or not self.supabase:
            self.logger.warning("⚠️ Supabase not available for queue operations")
            return None
        
        try:
            # Disabled noisy log: Queue processor requesting next item
            item = await self.supabase.get_next_queue_item()
            if item:
                self.logger.info(f"✅ Queue processor got item: {item['username']} (priority: {item['priority']})")
            else:
                # Disabled noisy log: No items available
                pass
            return item
        except Exception as e:
            self.logger.error(f"❌ Queue processor error getting next Supabase item: {e}")
            return None
    
    async def _main_processing_loop(self):
        """Main processing loop with priority logic"""
        while self.running:
            try:
                # Check for HIGH priority items first using Supabase
                if await self._has_high_priority_pending():
                    await self._handle_high_priority_processing()
                else:
                    await self._handle_low_priority_processing()
                
                # Brief pause to prevent busy waiting
                await asyncio.sleep(1)
                
                # Cleanup completed tasks
                await self._cleanup_completed_tasks()
                
                # Log stats periodically
                if self.stats['processed_count'] % 10 == 0:
                    await self._log_stats()
                
            except Exception as e:
                self.logger.error(f"Error in main processing loop: {e}")
                await asyncio.sleep(5)
    
    async def _handle_high_priority_processing(self):
        """Handle HIGH priority items (pause LOW priority)"""
        # Pause all LOW priority processing
        if self.low_priority_tasks:
            self.logger.info("⏸️ HIGH priority item detected - pausing LOW priority processing")
            # Cancel LOW priority tasks
            for task in self.low_priority_tasks:
                if not task.done():
                    task.cancel()
            await asyncio.gather(*self.low_priority_tasks, return_exceptions=True)
            self.low_priority_tasks.clear()
        
        # Process HIGH priority items from Supabase
        while (len(self.high_priority_tasks) < self.max_concurrent_high and 
               await self._has_high_priority_pending()):
            
            item_data = await self._get_next_supabase_item()
            if item_data and item_data.get('priority') == 'HIGH':
                # Convert to QueueItem format for compatibility
                queue_item = QueueItem(
                    username=item_data['username'],
                    source=item_data['source'],
                    priority=Priority.HIGH,
                    timestamp=item_data['timestamp'],
                    status=Status.PROCESSING,
                    attempts=item_data.get('attempts', 0),
                    last_attempt=item_data.get('last_attempt'),
                    error_message=item_data.get('error_message'),
                    request_id=item_data['request_id']
                )
                task = asyncio.create_task(self._process_item(queue_item))
                self.high_priority_tasks.add(task)
                self.logger.info(f"🔴 Started HIGH priority processing: @{queue_item.username}")
    
    async def _handle_low_priority_processing(self):
        """Handle LOW priority items (when no HIGH priority)"""
        # Process LOW priority items from Supabase
        while (len(self.low_priority_tasks) < self.max_concurrent_low and 
               not await self._has_high_priority_pending()):
            
            item_data = await self._get_next_supabase_item()
            if item_data and item_data.get('priority') == 'LOW':
                # Convert to QueueItem format for compatibility
                queue_item = QueueItem(
                    username=item_data['username'],
                    source=item_data['source'],
                    priority=Priority.LOW,
                    timestamp=item_data['timestamp'],
                    status=Status.PROCESSING,
                    attempts=item_data.get('attempts', 0),
                    last_attempt=item_data.get('last_attempt'),
                    error_message=item_data.get('error_message'),
                    request_id=item_data['request_id']
                )
                task = asyncio.create_task(self._process_item(queue_item))
                self.low_priority_tasks.add(task)
                self.logger.info(f"🔵 Started LOW priority processing: @{queue_item.username}")
            else:
                break
    
    async def _process_item(self, item: QueueItem) -> bool:
        """Process a single queue item"""
        start_time = time.time()
        
        # Item already marked as PROCESSING by get_next_item() to prevent race conditions
        
        try:
            self.logger.info(f"🔄 Processing @{item.username} (attempt {item.attempts + 1})")
            
            # Use existing Instagram pipeline (add posts-only mode for robustness)
            if item.source == 'posts-only':
                primary_profile, content_data, secondary_profiles = await self.instagram_pipeline.run_posts_only_pipeline(item.username)
            elif item.priority == Priority.HIGH:
                # High priority gets full pipeline (saves internally to Supabase)
                primary_profile, content_data, secondary_profiles = await self.instagram_pipeline.run_complete_pipeline(item.username)
            else:
                # Low priority gets low priority pipeline
                primary_profile, content_data, secondary_profiles = await self.instagram_pipeline.run_low_priority_pipeline(item.username)
                
                # Save the data for low priority items (to Supabase and/or CSV)
                if primary_profile:
                    self.logger.info(f"💾 Saving LOW PRIORITY pipeline results for @{item.username}...")
                    await self.instagram_pipeline.save_to_csv_and_supabase(
                        primary_profile, content_data, secondary_profiles, item.username
                    )
                    self.logger.info(f"✅ Data saved for @{item.username}")
                else:
                    self.logger.warning(f"⚠️ No data to save for @{item.username}")
            
            # Mark as completed in Supabase
            if self.use_supabase and self.supabase:
                try:
                    await self.supabase.update_queue_item_status(item.request_id, 'COMPLETED')
                except Exception as e:
                    self.logger.warning(f"Failed to update Supabase queue status: {e}")
            
            # Update stats
            self.stats['processed_count'] += 1
            if item.priority == Priority.HIGH:
                self.stats['high_priority_processed'] += 1
            else:
                self.stats['low_priority_processed'] += 1
            
            processing_time = time.time() - start_time
            self.logger.info(f"✅ Completed @{item.username} in {processing_time:.2f}s")
            
            return True
            
        except Exception as e:
            error_msg = str(e)
            self.logger.error(f"❌ Failed processing @{item.username}: {error_msg}")
            
            # Mark as failed in Supabase
            if self.use_supabase and self.supabase:
                try:
                    await self.supabase.update_queue_item_status(item.request_id, 'FAILED', error_msg)
                except Exception as e:
                    self.logger.warning(f"Failed to update Supabase queue status for failure: {e}")
            
            self.stats['error_count'] += 1
            return False
    
    async def _cleanup_completed_tasks(self):
        """Remove completed tasks from tracking sets"""
        for task_set in [self.high_priority_tasks, self.low_priority_tasks]:
            completed = {task for task in task_set if task.done()}
            task_set -= completed
    
    async def _graceful_shutdown(self):
        """Gracefully shutdown the processor"""
        self.logger.info("🛑 Starting graceful shutdown...")
        
        # Cancel all running tasks
        all_tasks = self.high_priority_tasks | self.low_priority_tasks
        for task in all_tasks:
            if not task.done():
                task.cancel()
        
        if all_tasks:
            await asyncio.gather(*all_tasks, return_exceptions=True)
        
        # Note: No need to resume items with Supabase - they remain in PENDING status automatically
        
        await self._log_final_stats()
        self.logger.info("✅ Queue Processor shutdown complete")
    
    async def _log_stats(self):
        """Log current processing statistics"""
        try:
            if self.use_supabase and self.supabase:
                queue_stats = await self.supabase.get_queue_stats()
            else:
                queue_stats = {}
        except:
            queue_stats = {}
            
        uptime = datetime.now() - self.stats['start_time'] if self.stats['start_time'] else timedelta(0)
        
        # Only log stats every 5 minutes instead of every few seconds
        if not hasattr(self, '_last_stats_log') or (datetime.utcnow() - self._last_stats_log).seconds > 300:
            self.logger.info(f"📊 Stats - Processed: {self.stats['processed_count']}, "
                        f"Errors: {self.stats['error_count']}, "
                        f"Queue: {queue_stats.get('pending', 0)} pending, "
                        f"Active: {len(self.high_priority_tasks) + len(self.low_priority_tasks)}, "
                        f"Uptime: {str(uptime).split('.')[0]}")
            self._last_stats_log = datetime.utcnow()
    
    async def _log_final_stats(self):
        """Log final statistics on shutdown"""
        uptime = datetime.now() - self.stats['start_time'] if self.stats['start_time'] else timedelta(0)
        
        try:
            if self.use_supabase and self.supabase:
                queue_stats = await self.supabase.get_queue_stats()
            else:
                queue_stats = {}
        except Exception as e:
            queue_stats = f"Error getting stats - {e}"
        
        self.logger.info("📈 Final Statistics:")
        self.logger.info(f"   Total Processed: {self.stats['processed_count']}")
        self.logger.info(f"   HIGH Priority: {self.stats['high_priority_processed']}")
        self.logger.info(f"   LOW Priority: {self.stats['low_priority_processed']}")
        self.logger.info(f"   Errors: {self.stats['error_count']}")
        self.logger.info(f"   Uptime: {str(uptime).split('.')[0]}")
        self.logger.info(f"   Queue Status: {queue_stats}")

# ======================================================================
# QUEUE MANAGEMENT UTILITIES
# ======================================================================

def add_to_queue(username: str, source: str = "manual", priority: Priority = Priority.LOW) -> bool:
    """Utility function to add item to queue (Supabase first, CSV as backup).
    Returns True if the item was inserted OR already exists as active (PENDING/PROCESSING)."""
    # Try Supabase directly so the processor can see it
    try:
        if SUPABASE_AVAILABLE:
            supabase = SupabaseManager()
            # Check if an active item already exists for this username
            existing = supabase.client.table('queue').select('*').eq('username', username).in_('status', ['PENDING', 'PROCESSING']).limit(1).execute()
            if existing.data:
                logging.info(f"⏭️ Skipping duplicate request for @{username} (already active in Supabase)")
                return True
            # Insert new item
            import uuid as _uuid
            request_id = str(_uuid.uuid4())[:8]
            insert_data = {
                'username': username,
                'source': source,
                'priority': priority.value if hasattr(priority, 'value') else str(priority),
                'timestamp': datetime.now().isoformat(),
                'status': 'PENDING',
                'attempts': 0,
                'request_id': request_id
            }
            response = supabase.client.table('queue').insert(insert_data).execute()
            if response.data:
                logging.info(f"✅ Added @{username} to Supabase queue ({source}, {priority})")
                return True
            # If insert returned no data, treat as failure and try CSV
    except Exception as e:
        logging.error(f"Failed to add to Supabase queue: {e}")

    # Fallback to CSV (best-effort)
    try:
        queue_manager = QueueManager()
        item = QueueItem(
            username=username,
            source=source,
            priority=priority,
            timestamp=datetime.now().isoformat()
        )
        # If already present in CSV as active, treat as success
        all_items = queue_manager.get_all_items()
        for it in all_items:
            if it.username.lower() == username.lower() and it.status in [Status.PENDING, Status.PROCESSING]:
                logging.info(f"⏭️ Skipping duplicate request for @{username} (already active in CSV)")
                return True
        return queue_manager.add_item(item)
    except Exception as e:
        logging.error(f"Failed to add to CSV queue: {e}")
        return False

def get_queue_status() -> Dict:
    """Utility function to get queue status"""
    queue_manager = QueueManager()
    return queue_manager.get_queue_stats()

# ======================================================================
# CLI INTERFACE
# ======================================================================

async def main():
    """CLI interface for queue processor"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Instagram Queue Processor")
    parser.add_argument("--start", action="store_true", help="Start queue processing")
    parser.add_argument("--add", type=str, help="Add username to queue")
    parser.add_argument("--source", type=str, default="manual", help="Source of request")
    parser.add_argument("--priority", choices=["HIGH", "LOW"], default="LOW", help="Request priority")
    parser.add_argument("--status", action="store_true", help="Show queue status")

    parser.add_argument("--max-low", type=int, default=MAX_CONCURRENT_LOW_PRIORITY, help="Max concurrent LOW priority")
    parser.add_argument("--max-high", type=int, default=MAX_CONCURRENT_HIGH_PRIORITY, help="Max concurrent HIGH priority")
    
    args = parser.parse_args()
    
    if args.add:
        priority = Priority.HIGH if args.priority == "HIGH" else Priority.LOW
        success = add_to_queue(args.add, args.source, priority)
        if success:
            print(f"✅ Added @{args.add} to queue ({args.priority} priority)")
        else:
            print(f"❌ Failed to add @{args.add} to queue")
    
    elif args.status:
        stats = get_queue_status()
        print("📊 Queue Status:")
        print(json.dumps(stats, indent=2))
    
    elif args.start:
        processor = QueueProcessor(args.max_low, args.max_high)
        await processor.start_processing()
    
    else:
        parser.print_help()

if __name__ == "__main__":
    asyncio.run(main())