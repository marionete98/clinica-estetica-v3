"""
Main FastAPI application entry point for Clínica Luana multi-agent system.
"""

import logging
import asyncio
import sys
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from apscheduler.triggers.interval import IntervalTrigger

from config.settings import settings
from config.telemetry import setup_telemetry
from config.chatwoot_client import chatwoot_client
from services.container import get_redis_client, get_supabase_client
from routes.webhooks import router as webhooks_router
from routes.api import router as api_router
from routes.metrics import router as metrics_router
from routes.dashboard import router as dashboard_router
from jobs.reminder_job import run_reminder_job
from jobs.feedback_job import run_feedback_job
from jobs.kb_sync_job import create_kb_sync_job
from services.alerts import run_alert_check
from services.agent_orchestrator import cleanup_orchestrator
from middleware.rate_limit import RateLimitMiddleware

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)],
)

logger = logging.getLogger(__name__)

# Global scheduler instance
scheduler = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Lifespan context manager for startup and shutdown events.

    Handles:
    - Connection initialization on startup
    - Scheduled jobs initialization
    - Connection cleanup on shutdown
    """
    global scheduler

    # Initialise telemetry lazily so we have the FastAPI app instance ready
    try:
        setup_telemetry(app, settings)
    except Exception as telemetry_error:
        logging.getLogger(__name__).warning(
            "Telemetry setup failed",
            extra={"error": str(telemetry_error)},
        )

    # Startup
    logger.info("Starting Clínica Luana Multi-Agent System...")

    try:
        # Initialize Redis connection (async)
        redis_client = get_redis_client()
        await redis_client.ensure_initialized()
        logger.info("Redis connection established")
    except Exception as e:
        logger.warning(
            f"Redis connection failed: {e}. System will operate without context."
        )

    try:
        # Initialize Supabase connection
        supabase_client = get_supabase_client()
        supabase = supabase_client.client
        # Test connection with a simple query (using knowledge_base which exists)
        supabase.table("knowledge_base").select("id").limit(1).execute()
        logger.info("Supabase connection established")
    except Exception as e:
        logger.error(f"Supabase connection failed: {e}")
        # Supabase is critical, but we'll let the app start

    try:
        # Check Chatwoot connection
        if chatwoot_client.health_check():
            logger.info("Chatwoot API connection verified")
        else:
            logger.warning("Chatwoot API health check failed")
    except Exception as e:
        logger.warning(f"Chatwoot connection check failed: {e}")

    # Initialize APScheduler
    try:
        scheduler = AsyncIOScheduler()

        # Add reminder job (runs every 30 minutes)
        scheduler.add_job(
            run_reminder_job,
            trigger=IntervalTrigger(minutes=30),
            id="reminder_job",
            name="Send appointment reminders (D-1 and H-2)",
            replace_existing=True,
            max_instances=1,
            misfire_grace_time=300,  # 5 minutes grace time
        )
        logger.info("Reminder job scheduled (every 30 minutes)")

        # Add feedback job (runs daily at 10:00)
        scheduler.add_job(
            run_feedback_job,
            trigger=CronTrigger(hour=10, minute=0),
            id="feedback_job",
            name="Send post-treatment feedback requests",
            replace_existing=True,
            max_instances=1,
            misfire_grace_time=600,  # 10 minutes grace time
        )
        logger.info("Feedback job scheduled (daily at 10:00)")

        # Add alert check job (runs every 5 minutes)
        scheduler.add_job(
            run_alert_check,
            trigger=IntervalTrigger(minutes=5),
            id="alert_check_job",
            name="Check metric thresholds and trigger alerts",
            replace_existing=True,
            max_instances=1,
            misfire_grace_time=120,  # 2 minutes grace time
        )
        logger.info("Alert check job scheduled (every 5 minutes)")

        # Initialize Knowledge Base cache sync job
        kb_sync_job = create_kb_sync_job(scheduler)
        kb_sync_job.start()
        logger.info("KB cache sync job scheduled (every 3 hours)")

        # Start the scheduler
        scheduler.start()
        logger.info("APScheduler started successfully")

        # Initialize KB cache on startup (non-blocking)
        async def init_cache_background():
            """Initialize cache in background to not block startup."""
            try:
                success = await kb_sync_job.initialize_cache_on_startup()
                if success:
                    logger.info("Knowledge base cache initialized on startup")
                else:
                    logger.error("Failed to initialize KB cache on startup")
            except Exception as e:
                logger.error(f"Failed to initialize KB cache on startup: {e}")
        
        # Run cache initialization in background
        asyncio.create_task(init_cache_background())
        logger.info("KB cache initialization started in background")

    except Exception as e:
        logger.error(f"Failed to start APScheduler: {e}")
        scheduler = None

    # Log configuration
    logger.info(f"LLM Provider: {settings.MODEL_PROVIDER}")
    logger.info(f"Environment: {settings.ENV}")

    logger.info("System startup complete")

    yield

    # Shutdown
    logger.info("Shutting down Clínica Luana Multi-Agent System...")

    # Cleanup agent orchestrator (close all model clients)
    try:
        await cleanup_orchestrator()
        logger.info("Agent orchestrator cleaned up")
    except Exception as e:
        logger.error(f"Error cleaning up agent orchestrator: {e}")

    # Shutdown scheduler
    if scheduler:
        try:
            scheduler.shutdown(wait=True)
            logger.info("APScheduler shut down")
        except Exception as e:
            logger.error(f"Error shutting down scheduler: {e}")

    try:
        # Close Chatwoot client
        chatwoot_client.close()
        logger.info("Chatwoot client closed")
    except Exception as e:
        logger.error(f"Error closing Chatwoot client: {e}")

    logger.info("System shutdown complete")


app = FastAPI(
    title="Clínica Luana Multi-Agent System",
    description="Sistema de atendimento automatizado multi-agente para WhatsApp",
    version=settings.app_version,
    lifespan=lifespan,
)

# CORS middleware
# Note: In production, restrict to specific domains
allowed_origins = ["*"] if settings.is_development else [
    "https://app.chatwoot.com",
    "https://clinicaluana.com.br",
    "https://www.clinicaluana.com.br"
]
app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Rate limiting middleware
app.add_middleware(RateLimitMiddleware, paths_to_limit=["/webhook/"])


# Global exception handler
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """
    Global exception handler for unhandled errors.

    Logs the error and returns a generic 500 response.
    """
    logger.error(
        f"Unhandled exception: {exc}",
        exc_info=True,
        extra={
            "path": request.url.path,
            "method": request.method,
        },
    )

    return JSONResponse(
        status_code=500,
        content={
            "error": "Internal server error",
            "message": "An unexpected error occurred. Please try again later.",
            "path": request.url.path,
        },
    )


# Include routers
app.include_router(webhooks_router)
app.include_router(api_router)
app.include_router(metrics_router)
app.include_router(dashboard_router)


@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "message": "Clínica Luana Multi-Agent System",
        "version": settings.app_version,
        "docs": "/docs",
        "health": "/health",
        "endpoints": {
            "webhooks": "/webhook/chatwoot",
            "chat": "/chat",
            "metrics": "/metrics",
            "dashboard": "/dashboard",
        },
    }


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)

