import subprocess
import argparse
from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from pathlib import Path
import uuid
from scrapers.econ_scraper import scrape_and_store_economic_data
from scrapers.fear_sentiment import fear_index
from scrapers.earnings_scraper import scrape_all_earnings

from utils.logger import setup_logger, get_request_logger

from utils.db_manager import (
    get_latest_economic_events,
    get_latest_earnings,
    get_latest_fear_greed,
)

logger = setup_logger("api")

app = FastAPI(title="Market Dashboard API")

# Allow CORS for local development
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

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

# ---------------------------- SCRAPER FUNCTIONS ----------------------------

def run_scrapers():
    """Run all our scrapers to get fresh data"""
    try:
        logger.info("Starting scrapers...")
        
        # Run each scraper
        scrape_and_store_economic_data()
        fear_index()
        scrape_all_earnings()
        
        logger.info("All scrapers finished!")
        
    except Exception as e:
        # Log any errors that happen
        logger.error(f"Scraper error: {str(e)}", extra={
            "extras": {
                "error_type": type(e).__name__
            }
        })

# ---------------------------- MAIN ----------------------------

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--mode", choices=["scraper", "api", "both"], default="both")
    args = parser.parse_args()
    
    try:
        if args.mode in ["scraper", "both"]:
            run_scrapers()
            
        if args.mode in ["api", "both"]:
            # Start the API server
            subprocess.run(
                ["uvicorn", "main:app", "--reload", "--port", "8000"],
                check=True
            )

    except KeyboardInterrupt:
        print("\nShutting down...")

    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    main() 