"""FastAPI main application."""

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .config import settings
from .database import init_database
from .scheduler import start_background_poller, stop_scheduler
from .api import router

# Configure logging
logging.basicConfig(
    level=settings.log_level,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
)

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager."""
    # Startup
    logger.info("🚀 Starting Twitter Signal Monitor...")
    
    # Initialize database
    init_database()
    logger.info("✅ Database initialized")
    
    # Start background poller
    start_background_poller()
    logger.info("✅ Background poller started")
    
    yield
    
    # Shutdown
    logger.info("Shutting down...")
    stop_scheduler()
    logger.info("✅ Shutdown complete")


# Create FastAPI app
app = FastAPI(
    title="Twitter Financial Signal Monitor",
    description="Monitor Twitter accounts for financial signals and send Telegram alerts",
    version="0.1.0",
    lifespan=lifespan
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API routes
app.include_router(router, prefix="/api/v1", tags=["tracks"])


@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "message": "Twitter Financial Signal Monitor API",
        "version": "0.1.0",
        "docs": "/docs"
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
