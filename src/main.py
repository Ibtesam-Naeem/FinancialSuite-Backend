import os
from datetime import datetime
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from utils.logger import setup_logger
from utils.config import Settings
from utils.scheduler import setup_scheduler, run_scrapers, scheduler
from routes import (
    economic_events,
    earnings,
    market_holidays,
    fear_greed,
    scrapers
)

# Initialize logger and settings
logger = setup_logger("api")
settings = Settings()

# Initialize FastAPI app
app = FastAPI(
    title="Market Dashboard API",
    description="API for financial market data including economic events, earnings, and market sentiment",
    version="1.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(economic_events.router, prefix="/api/v1", tags=["Economic Events"])
app.include_router(earnings.router, prefix="/api/v1", tags=["Earnings"])
app.include_router(market_holidays.router, prefix="/api/v1", tags=["Market Holidays"])
app.include_router(fear_greed.router, prefix="/api/v1", tags=["Fear & Greed"])
app.include_router(scrapers.router, prefix="/api/v1", tags=["Scrapers"])

@app.on_event("startup")
async def startup_event():
    """
    Initialize services on application startup.
    """
    try:
        # Setup scheduler
        setup_scheduler()
        
        # Run initial scrapers
        logger.info("Running initial scraper execution...")
        run_scrapers()
        logger.info("Initial scraper execution completed")
        
    except Exception as e:
        logger.error(f"Error during startup: {e}")
        raise

@app.on_event("shutdown")
async def shutdown_event():
    """
    Cleanup services on application shutdown.
    """
    try:
        if scheduler.running:
            scheduler.shutdown()
            logger.info("Scheduler shutdown complete")
        logger.info("Application shutdown complete")
    except Exception as e:
        logger.error(f"Error during shutdown: {e}")
        raise
