import os
from datetime import datetime
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger

from scrapers.econ_scraper import scrape_and_store_economic_data
from scrapers.fear_sentiment import fear_index
from scrapers.earnings_scraper import scrape_earnings_this_week, scrape_earnings_next_week
from scrapers.general_info import fetch_and_store_market_holidays
from utils.logger import setup_logger
from utils.db_manager import (
    get_latest_economic_events,
    get_latest_earnings,
    get_latest_fear_greed,
    clear_database_data
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

# Start the scheduler when the application starts
@app.on_event("startup")
async def startup_event():
    try:
        # Clear the database first
        logger.info("Clearing database on startup...")
        clear_database_data()
        
        # Setup scheduled tasks
        setup_scheduler()
        scheduler.start()
        
        # Run all scrapers to populate the fresh database
        logger.info("Running initial scrapers to populate database...")
        run_scrapers()
        
    except Exception as e:
        logger.error(f"Error during startup: {e}")
        raise

# Stop the scheduler when the application shuts down
@app.on_event("shutdown")
async def shutdown_event():
    scheduler.shutdown()

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
            ("earnings", scrape_earnings_this_week),
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

@app.get("/reset-and-scrape")
async def reset_and_scrape():
    """
    Manually triggers database cleanup and runs all scrapers.
    Useful for testing and manual resets.
    """
    try:
        # Clear the database
        logger.info("Manually clearing database...")
        clear_database_data()
        
        # Run all scrapers
        logger.info("Manually running all scrapers...")
        run_scrapers()
        
        return {
            "status": "success",
            "message": "Database cleared and scrapers executed successfully"
        }
        
    except Exception as e:
        logger.error(f"Error in reset-and-scrape: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# ---------------------------- SCRAPER FUNCTIONS ----------------------------

def run_scrapers():
    """
    Runs all scrapers sequentially.
    """
    try:
        logger.info("Starting scrapers...")

        # Scrape and store economic data
        logger.info("Starting economic data scraper...")
        economic_data = scrape_and_store_economic_data()
        logger.info(f"Economic data scraper completed. Retrieved {len(economic_data) if economic_data else 0} records")

        # Scrape fear index
        logger.info("Starting fear index scraper...")
        fear_data = fear_index()
        logger.info(f"Fear index scraper completed. Retrieved {len(fear_data) if fear_data else 0} records")

        # Scrape all earnings
        logger.info("Starting earnings scraper...")
        earnings_data = scrape_earnings_this_week()
        logger.info(f"Earnings scraper completed. Retrieved {len(earnings_data) if earnings_data else 0} records")

        # Fetch and store market holidays
        logger.info("Starting market holidays scraper...")
        holidays_data = fetch_and_store_market_holidays()
        logger.info(f"Market holidays scraper completed. Retrieved {len(holidays_data) if holidays_data else 0} records")

        logger.info("All scrapers finished successfully")

    except Exception as e:
        logger.error(f"Scraper error: {e}")
        # Re-raise the exception to ensure the startup process knows about the failure
        raise

# ---------------------------- SCHEDULER SETUP ----------------------------

def setup_scheduler():
    """
    Sets up scheduled scraper jobs.
    """
    # Economic data - Every Sunday at 4 PM
    scheduler.add_job(
        scrape_and_store_economic_data,
        CronTrigger(hour=12, minute=35),
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
        scrape_earnings_this_week,
        CronTrigger(hour=8, minute=0),
        id="earnings_this_week",
        name="Earnings This Week Scraper",
        replace_existing=True
    )
    
    # Next Week Earnings - Mondays and Fridays at 8:30 AM
    scheduler.add_job(
        scrape_earnings_next_week,
        CronTrigger(hour=8, minute=30, day_of_week='mon,fri'),
        id="earnings_next_week",
        name="Earnings Next Week Scraper",
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

    # Database cleanup - Every two weeks on Sunday at 1 AM
    scheduler.add_job(
        clear_database_data,
        CronTrigger(day_of_week='sun', hour=1, minute=0),
        id='database_cleanup',
        name="Database Cleanup",
        replace_existing=True
    )
    
    # Log all scheduled jobs
    jobs = scheduler.get_jobs()
    for job in jobs:
        logger.info(f"Scheduled job: {job.name}")

setup_scheduler()