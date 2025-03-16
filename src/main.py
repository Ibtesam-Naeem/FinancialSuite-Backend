import subprocess
import argparse
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pathlib import Path
import uvicorn
import os
import sys

from utils.logger import setup_logging

from utils.db_manager import (
    get_latest_economic_events,
    get_latest_earnings,
    get_latest_fear_greed,
    get_latest_premarket_movers
)

# Initialize logging
logging = setup_logging("Main Script Logger")

# Initialize FastAPI
app = FastAPI(title="Market Dashboard API")

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---------------------------- API ENDPOINTS ----------------------------

@app.get("/")
async def root():
    return {"message": "Market Dashboard API"}

@app.get("/economic-events")
async def get_economic_events(limit: int = 10):
    try:
        events = get_latest_economic_events(limit)
        return {"status": "success", "data": events}
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/earnings")
async def get_earnings(limit: int = 10):
    try:
        earnings = get_latest_earnings(limit)
        return {"status": "success", "data": earnings}
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/fear-greed")
async def get_fear_greed(limit: int = 1):
    try:
        fear_data = get_latest_fear_greed(limit)
        return {"status": "success", "data": fear_data}
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/premarket")
async def get_premarket():
    try:
        premarket = get_latest_premarket_movers()
        return {"status": "success", "data": premarket}
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# ---------------------------- SCRAPER FUNCTIONS ----------------------------

def run_scrapers():
    """
    Runs all the scrapers to collect
    all the market data
    """
    try:
        # Import scraper modules only when needed
        from scrapers.econ_scraper import scrape_and_store_economic_data
        from scrapers.fear_sentiment import fear_index
        from scrapers.earnings_scraper import scrape_all_earnings
        from scrapers.premarket_movers import get_premarket_movers
        
        # Scrape and store economic events
        scrape_and_store_economic_data()
        
        # # Get fear index
        fear_index()
        
        # Get earnings data
        scrape_all_earnings()
        
        # Get pre-market movers
        # get_premarket_movers()
        
    except Exception as e:
        logging.error(f"Error running scrapers: {e}")

# ---------------------------- MAIN ----------------------------

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--mode", choices=["scraper", "api", "both"], default="both")
    args = parser.parse_args()
    
    try:
        if args.mode in ["scraper", "both"]:
            run_scrapers()
            
        if args.mode in ["api", "both"]:
            # Run FastAPI server directly using uvicorn
            print("Starting FastAPI server on http://127.0.0.1:8000")
            # Get the absolute path to the current file
            current_file = Path(__file__).resolve()
            # Get the directory containing the current file
            current_dir = current_file.parent
            # Change the working directory to the directory containing the current file
            os.chdir(current_dir)
            # Run uvicorn with the correct module path
            uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)
    except KeyboardInterrupt:
        print("\nShutting down...")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    main() 