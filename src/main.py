import os
import uuid
import argparse
from datetime import datetime
from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger

from scrapers.econ_scraper import scrape_and_store_economic_data
from scrapers.fear_sentiment import fear_index
from scrapers.earnings_scraper import scrape_all_earnings
from scrapers.general_info import fetch_and_store_market_holidays
from utils.logger import setup_logger, get_request_logger
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

scheduler = BackgroundScheduler()

# ---------------------------- MIDDLEWARE ----------------------------

@app.middleware("http")
async def log_requests(request: Request, call_next):
    """
    Middleware to log incoming requests and responses.
    """
    req_id = str(uuid.uuid4())
    request.state.request_id = req_id
    log = get_request_logger(logger, req_id)
    request.state.logger = log

    log.info("Got request", extra={
        "extras": {
            "method": request.method,
            "url": str(request.url),
            "client": request.client.host if request.client else None,
            "user_agent": request.headers.get("user-agent")
        }
    })

    response = await call_next(request)

    log.info("Request finished", extra={
        "extras": {
            "status": response.status_code
        }
    })

    return response

# ---------------------------- API ENDPOINTS ----------------------------

@app.get("/")
async def root(request: Request):
    """
    Root endpoint.
    """
    request.state.logger.info("Root endpoint hit")
    return {"message": "Market Dashboard API"}

@app.get("/economic-events")
async def get_economic_events(limit: int = 10):
    """
    Get latest economic events.
    """
    try:
        events = get_latest_economic_events(limit)
        return {"status": "success", "data": events}

    except Exception as e:
        logger.error(f"Failed to get economic events: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/earnings")
async def get_earnings(limit: int = 10):
    """
    Get latest earnings data.
    """
    try:
        earnings = get_latest_earnings(limit)
        return {"status": "success", "data": earnings}

    except Exception as e:
        logger.error(f"Failed to get earnings: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/market-holidays")
async def get_market_holidays(limit: int = 10):
    """
    Gets upcoming market holidays.
    """
    try:
        holidays = fetch_and_store_market_holidays(limit)
        return {"status": "success", "data": holidays}

    except Exception as e:
        logger.error(f"Failed to get market holidays: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/fear-greed")
async def get_fear_greed(limit: int = 1):
    """
    Gets latest fear & greed index.
    """
    try:
        fear_data = get_latest_fear_greed(limit)
        return {"status": "success", "data": fear_data}

    except Exception as e:
        logger.error(f"Failed to get fear/greed index: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/status")
async def get_status():
    """
    Returns the current status of the application and scheduler.
    """
    try:
        scheduler_status = {
            "running": scheduler.running,
            "jobs": [
                {
                    "id": job.id,
                    "name": job.name,
                    "next_run_time": str(job.next_run_time) if job.next_run_time else None
                }
                for job in scheduler.get_jobs()
            ]
        }
        return {
            "status": "success",
            "data": {
                "application": "running",
                "scheduler": scheduler_status,
                "environment": os.getenv("ENVIRONMENT", "dev"),
                "current_time": datetime.now().isoformat()
            }
        }
    except Exception as e:
        logger.error(f"Status check error: {e}")
        return {"status": "error", "message": str(e)}

@app.get("/trigger-scrapers")
async def trigger_scrapers():
    """
    Manually triggers all scrapers immediately.
    """
    try:
        if not scheduler.running:
            scheduler.start()
        run_scrapers()
        return {"status": "success", "message": "Scrapers triggered successfully"}
    except Exception as e:
        logger.error(f"Error triggering scrapers: {e}")
        return {"status": "error", "message": str(e)}

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
    scheduler.add_job(
        scrape_and_store_economic_data,
        CronTrigger(day_of_week="sun", hour="16", minute="0"),
        id="economic_data",
        name="Economic Data Scraper",
        replace_existing=True
    )
    scheduler.add_job(
        fear_index,
        CronTrigger(hour="*", minute="0"),
        id="fear_index",
        name="Fear Index Scraper",
        replace_existing=True
    )
    scheduler.add_job(
        scrape_all_earnings,
        CronTrigger(hour="8", minute="0"),
        id="earnings",
        name="Earnings Scraper",
        replace_existing=True
    )
    scheduler.start()
    logger.info("Scheduler started successfully")

# ---------------------------- MAIN ----------------------------

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--mode", choices=["scraper", "api", "both"], default="both")
    args = parser.parse_args()

    try:
        logger.info("Starting application...", extra={
            "extras": {
                "mode": args.mode,
                "environment": os.getenv("ENVIRONMENT", "dev")
            }
        })

        setup_scheduler()

        if args.mode in ["scraper", "both"]:
            run_scrapers()

        if args.mode in ["api", "both"]:
            import uvicorn
            uvicorn.run(app, host="0.0.0.0", port=8000)

    except KeyboardInterrupt:
        logger.info("Shutting down...")
        if scheduler.running:
            scheduler.shutdown()

    except Exception as e:
        logger.error(f"Application error: {e}")

if __name__ == "__main__":
    main()
