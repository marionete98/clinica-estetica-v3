"""
Knowledge Base Synchronization Job - Automatic Redis cache sync every 3 hours.
"""

import logging
from datetime import datetime
from typing import Optional
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.interval import IntervalTrigger

from services.container import get_kb_cache_service
from services.kb_cache_service import KnowledgeBaseCacheService
from utils.logger import logger as structured_logger

logger = logging.getLogger(__name__)


class KnowledgeBaseSyncJob:
    """Scheduled job for automatic knowledge base cache synchronization."""
    
    def __init__(
        self,
        scheduler: AsyncIOScheduler,
        kb_cache_service: Optional[KnowledgeBaseCacheService] = None,
    ):
        """Initialize the KB sync job."""
        self.scheduler = scheduler
        self.job_id = "kb_cache_sync"
        self.sync_interval_hours = 3
        self._cache_service = kb_cache_service or get_kb_cache_service()
        
        logger.info("Knowledge Base Sync Job initialized")
    
    def start(self) -> None:
        """Start the scheduled sync job."""
        try:
            # Add job to scheduler
            self.scheduler.add_job(
                func=self._sync_cache_job,
                trigger=IntervalTrigger(hours=self.sync_interval_hours),
                id=self.job_id,
                name="Knowledge Base Cache Sync",
                replace_existing=True,
                max_instances=1,
                coalesce=True,
                misfire_grace_time=300
            )
            
            logger.info(f"KB sync job scheduled to run every {self.sync_interval_hours} hours")
            
        except Exception as e:
            logger.error(f"Error starting KB sync job: {e}")
    
    def stop(self) -> None:
        """Stop the scheduled sync job."""
        try:
            if self.scheduler.get_job(self.job_id):
                self.scheduler.remove_job(self.job_id)
                logger.info("KB sync job stopped")
            
        except Exception as e:
            logger.error(f"Error stopping KB sync job: {e}")
    
    async def _sync_cache_job(self) -> None:
        """Execute the cache synchronization job."""
        job_start = datetime.now()
        
        try:
            logger.info("Starting scheduled KB cache synchronization...")
            
            # Perform cache synchronization
            success = await self._cache_service.sync_cache()
            
            # Calculate execution time
            execution_time = (datetime.now() - job_start).total_seconds()
            
            if success:
                # Get cache statistics
                stats = await self._cache_service.get_cache_stats()
                
                logger.info(
                    f"KB cache sync completed successfully in {execution_time:.2f}s. "
                    f"Entries: {stats.total_entries}, Templates: {stats.total_templates}, "
                    f"Hit rate: {stats.hit_rate:.1%}"
                )
                
                # Log success to Supabase for monitoring
                await structured_logger.log_to_supabase(
                    level="INFO",
                    message="KB cache sync completed successfully",
                    context={
                        "job": "kb_cache_sync",
                        "execution_time_seconds": execution_time,
                        "total_entries": stats.total_entries,
                        "total_templates": stats.total_templates,
                        "hit_rate": stats.hit_rate,
                        "cache_size_mb": stats.cache_size_mb
                    }
                )
                
            else:
                logger.error(f"KB cache sync failed after {execution_time:.2f}s")
                
                # Log failure to Supabase
                await structured_logger.log_to_supabase(
                    level="ERROR",
                    message="KB cache sync failed",
                    context={
                        "job": "kb_cache_sync",
                        "execution_time_seconds": execution_time,
                        "error": "Sync operation returned False"
                    }
                )
            
        except Exception as e:
            execution_time = (datetime.now() - job_start).total_seconds()
            
            logger.error(f"KB cache sync job failed with exception: {e}")
            
            # Log exception to Supabase
            await structured_logger.log_to_supabase(
                level="ERROR",
                message="KB cache sync job failed with exception",
                context={
                    "job": "kb_cache_sync",
                    "execution_time_seconds": execution_time,
                    "error": str(e),
                    "error_type": type(e).__name__
                }
            )
    
    async def initialize_cache_on_startup(self) -> bool:
        """Initialize cache on application startup."""
        try:
            logger.info("Initializing KB cache on startup...")
            
            # Check if cache already exists and is recent
            stats = await self._cache_service.get_cache_stats()

            if stats.total_entries > 0 and stats.last_sync:
                # Cache exists and has data
                time_since_sync = datetime.now() - stats.last_sync

                if time_since_sync.total_seconds() < self._cache_service.SYNC_INTERVAL:
                    logger.info(
                        f"KB cache already initialized with {stats.total_entries} entries. "
                        f"Last sync: {time_since_sync.total_seconds():.0f}s ago"
                    )
                    return True

            # Initialize cache
            success = await self._cache_service.initialize_cache()

            if success:
                stats = await self._cache_service.get_cache_stats()
                logger.info(
                    f"KB cache initialized successfully. "
                    f"Entries: {stats.total_entries}, Templates: {stats.total_templates}"
                )
                
            return success
            
        except Exception as e:
            logger.error(f"KB cache initialization failed with exception: {e}")
            return False


# Global job instance
kb_sync_job: Optional[KnowledgeBaseSyncJob] = None


def create_kb_sync_job(scheduler: AsyncIOScheduler) -> KnowledgeBaseSyncJob:
    """Factory function to create and configure the KB sync job."""
    global kb_sync_job
    
    kb_sync_job = KnowledgeBaseSyncJob(
        scheduler,
        kb_cache_service=get_kb_cache_service(),
    )
    
    return kb_sync_job


def get_kb_sync_job() -> Optional[KnowledgeBaseSyncJob]:
    """Get the global KB sync job instance."""
    return kb_sync_job
