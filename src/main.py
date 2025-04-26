import subprocess
import argparse
from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from pathlib import Path
import uuid
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from scrapers.econ_scraper import scrape_and_store_economic_data
from scrapers.fear_sentiment import fear_index
from scrapers.earnings_scraper import scrape_all_earnings
from scrapers.general_info import fetch_and_store_market_holidays
from utils.logger import setup_logger, get_request_logger
import os
from datetime import datetime

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

# Initialize the scheduler
scheduler = BackgroundScheduler()

@app.middleware("http")
async def log_requests(request: Request, call_next):
    req_id = str(uuid.uuid4())
    request.state.request_id = req_id
    
    log = get_request_logger(logger, req_id)
    request.state.logger = log
    
    # Logs basic request info
    log.info("Got request", extra={
        "extras": {
            "method": request.method,
            "url": str(request.url),
            "client": request.client.host if request.client else None,
            "user_agent": request.headers.get("user-agent")
        }
    })
    
    # Handles the request
    response = await call_next(request)
    
    # Logs the response
    log.info("Request finished", extra={
        "extras": {
            "status": response.status_code
        }
    })
    
    return response

# ---------------------------- API ENDPOINTS ----------------------------

@app.get("/")
async def root(request: Request):
    request.state.logger.info("Someone hit the root endpoint")
    return {"message": "Market Dashboard API"}

@app.get("/economic-events")
async def get_economic_events(limit: int = 10):
    try:
        events = get_latest_economic_events(limit)
        return {"status": "success", "data": events}
    
    except Exception as e:
        logger.error(f"Failed to get economic events: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/earnings")
async def get_earnings(limit: int = 10):
    try:
        earnings = get_latest_earnings(limit)
        return {"status": "success", "data": earnings}
    
    except Exception as e:
        logger.error(f"Failed to get earnings: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/market-holidays")
async def get_market_holidays(limit: int = 10):
    try:
        holidays = get_market_holidays(limit)
        return {"status": "success", "data": holidays}
    
    except Exception as e:
        logger.error(f"Failed to get market holidays: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
    
@app.get("/fear-greed")
async def get_fear_greed(limit: int = 1):
    try:
        fear_data = get_latest_fear_greed(limit)
        return {"status": "success", "data": fear_data}
    
    except Exception as e:
        logger.error(f"Failed to get fear/greed index: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/status")
async def get_status():
    """
    Returns the current status of the application and scheduler
    """
    try:
        # Get scheduler status
        scheduler_status = {
            "running": scheduler.running,
            "jobs": []
        }
        
        # Get all scheduled jobs
        for job in scheduler.get_jobs():
            scheduler_status["jobs"].append({
                "id": job.id,
                "name": job.name,
                "next_run_time": str(job.next_run_time) if job.next_run_time else None
            })
        
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
        logger.error(f"Status check error: {str(e)}")
        return {
            "status": "error",
            "message": str(e)
        }

# ---------------------------- SCRAPER FUNCTIONS ----------------------------

def run_scrapers():
    """
    Runs all of the  scrapers to get
    the latest data
    """
    try:
        logger.info("Starting scrapers...")
        
        # Runs each scraper
        scrape_and_store_economic_data()
        fear_index()
        scrape_all_earnings()
        fetch_and_store_market_holidays()

        logger.info("All scrapers finished!")
        
    except Exception as e:
        logger.error(f"Scraper error: {str(e)}", extra={
            "extras": {
                "error_type": type(e).__name__
            }
        })

# ---------------------------- SCHEDULER SETUP ----------------------------

def setup_scheduler():
    """
    Sets up a scheduler to run the scrapers at certain times
    """
    # Runs economic data scraper once per week (Sunday at 4 PM)
    scheduler.add_job(
        scrape_and_store_economic_data,
        CronTrigger(day_of_week='sun', hour='16', minute='0'),
        id='economic_data',
        name='Economic Data Scraper',
        replace_existing=True
    )
    
    # Runs fear index scraper every hour
    scheduler.add_job(
        fear_index,
        CronTrigger(hour='*', minute='0'),
        id='fear_index',
        name='Fear Index Scraper',
        replace_existing=True
    )
    
    # Runs earnings scraper once per day (at 8 AM)
    scheduler.add_job(
        scrape_all_earnings,
        CronTrigger(hour='8', minute='0'),
        id='earnings',
        name='Earnings Scraper',
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
        print("Starting application...")
        logger.info("Starting application...", extra={
            "extras": {
                "mode": args.mode,
                "environment": os.getenv("ENVIRONMENT", "dev")
            }
        })
        
        # Start the scheduler first
        print("Setting up scheduler...")
        setup_scheduler()
        
        # Verify scheduler started
        if not scheduler.running:
            raise Exception("Scheduler failed to start")
            
        print(f"Scheduler started successfully. Running: {scheduler.running}")
        logger.info(f"Scheduler started successfully. Running: {scheduler.running}")
        
        if args.mode in ["scraper", "both"]:
            print("Running initial scrapers...")
            logger.info("Running initial scrapers...")
            run_scrapers()
            
        if args.mode in ["api", "both"]:
            print("Starting API server...")
            logger.info("Starting API server...")
            # Start the API server
            subprocess.run(
                ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"],
                check=True
            )

    except KeyboardInterrupt:
        print("\nShutting down...")
        logger.info("Shutting down...")

    except Exception as e:
        print(f"Error: {e}")
        logger.error(f"Application error: {str(e)}", extra={
            "extras": {
                "error_type": type(e).__name__
            }
        })

if __name__ == "__main__":
    main() 