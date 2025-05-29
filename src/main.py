import os
from datetime import datetime
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger

from scrapers.econ_scraper import scrape_and_store_economic_data
from scrapers.fear_sentiment import fear_index
from scrapers.earnings_scraper import scrape_all_earnings
from scrapers.general_info import fetch_and_store_market_holidays
from utils.logger import setup_logger
from utils.db_manager import (
    get_latest_economic_events,
    get_latest_earnings,
    get_latest_fear_greed,
)

logger = setup_logger("api")

app = FastAPI(title="Market Dashboard API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize scheduler as a global variable
scheduler = BackgroundScheduler()

# ---------------------------- API ENDPOINTS ----------------------------

@app.get("/economic-events")
async def get_economic_events():
    """
    Get all economic events.
    """
    try:
        events = get_latest_economic_events()
        return {"status": "success", "data": events}

    except Exception as e:
        logger.error(f"Failed to get economic events: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/earnings")
async def get_earnings():
    """
    Get all earnings data.
    """
    try:
        earnings = get_latest_earnings()
        return {"status": "success", "data": earnings}

    except Exception as e:
        logger.error(f"Failed to get earnings: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/market-holidays")
async def get_market_holidays():
    """
    Gets all market holidays.
    """
    try:
        holidays = fetch_and_store_market_holidays()
        return {"status": "success", "data": holidays}

    except Exception as e:
        logger.error(f"Failed to get market holidays: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/fear-greed")
async def get_fear_greed():
    """
    Gets all fear & greed index data.
    """
    try:
        fear_data = get_latest_fear_greed()
        return {"status": "success", "data": fear_data}

    except Exception as e:
        logger.error(f"Failed to get fear/greed index: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/trigger-scrapers")
async def trigger_scrapers():
    """
    Manually triggers all scrapers immediately.
    """
    results = {}
    try:
        if not scheduler.running:
            scheduler.start()
            
        scrapers = [
            ("economic_data", scrape_and_store_economic_data),
            ("fear_index", fear_index),
            ("earnings", scrape_all_earnings),
            ("market_holidays", fetch_and_store_market_holidays)
        ]
        
        for name, scraper_func in scrapers:
            try:
                scraper_func()
                results[name] = "success"
            except Exception as e:
                results[name] = f"failed: {str(e)}"
                
        return {"status": "completed", "results": results}
    
    except Exception as e:
        return {"status": "error", "message": str(e), "results": results}

# ---------------------------- SCRAPER FUNCTIONS ----------------------------

def run_scrapers():
    """
    Runs all scrapers sequentially.
    """
    try:
        logger.info("Starting scrapers...")

        # Scrape and store economic data
        scrape_and_store_economic_data()

        # Scrape fear index
        fear_index()

        # Scrape all earnings
        scrape_all_earnings()

        # Fetch and store market holidays
        fetch_and_store_market_holidays()
        logger.info("All scrapers finished successfully")

    except Exception as e:
        logger.error(f"Scraper error: {e}")

# ---------------------------- SCHEDULER SETUP ----------------------------

def setup_scheduler():
    """
    Sets up scheduled scraper jobs.
    """
    # Economic data - Every Sunday at 4 PM
    scheduler.add_job(
        scrape_and_store_economic_data,
        CronTrigger(hour=4, minute=0),
        id="economic_data",
        name="Economic Data Scraper",
        replace_existing=True
    )
    
    # Fear index - Every hour
    scheduler.add_job(
        fear_index,
        CronTrigger(hour="*", minute=0),
        id="fear_index",
        name="Fear Index Scraper",
        replace_existing=True
    )
    
    # Earnings - Every day at 8 AM
    scheduler.add_job(
        scrape_all_earnings,
        CronTrigger(hour=8, minute=0),
        id="earnings",
        name="Earnings Scraper",
        replace_existing=True
    )
    
    # Market holidays - Every Sunday at 6 PM
    scheduler.add_job(
        fetch_and_store_market_holidays,
        CronTrigger(day_of_week="sun", hour=18, minute=0),
        id="market_holidays",
        name="Market Holidays Scraper",
        replace_existing=True
    )
    
    if not scheduler.running:
        scheduler.start()
        logger.info("Scheduler started successfully")
        
        # Log all scheduled jobs
        jobs = scheduler.get_jobs()
        for job in jobs:
            logger.info(f"Scheduled job: {job.name} - Next run: {job.next_run_time}")

def run_initial_scrape():
    """
    Runs all scrapers once when the application starts.
    """
    try:
        logger.info("Running initial scrape on startup...")
        run_scrapers()
        logger.info("Initial scrape completed successfully")
        
    except Exception as e:
        logger.error(f"Error during initial scrape: {e}")

setup_scheduler()
run_initial_scrape()
