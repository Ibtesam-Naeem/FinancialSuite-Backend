import argparse
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pathlib import Path
import uvicorn
import os

from utils.logger import setup_logging

from utils.db_manager import (
    get_latest_economic_events,
    get_latest_earnings,
    get_latest_fear_greed,
    get_latest_premarket_movers,
    get_latest_premarket_gainers,
    get_latest_premarket_losers,
    get_latest_market_holidays,
    create_top_stocks_table,
    store_top_stocks,
    get_latest_top_stocks
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

@app.get("/premarket/gainers")
async def get_premarket_gainers_endpoint(limit: int = 20):
    try:
        gainers = get_latest_premarket_gainers(limit)
        return {"status": "success", "data": gainers}
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/premarket/losers")
async def get_premarket_losers_endpoint(limit: int = 20):
    try:
        losers = get_latest_premarket_losers(limit)
        return {"status": "success", "data": losers}
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/premarket")
async def get_premarket(limit: int = 20):
    try:
        premarket = get_latest_premarket_movers(limit)
        return {"status": "success", "data": premarket}
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    
@app.get("/market-holidays")
async def get_market_holidays():
    try:
        holidays = get_latest_market_holidays()
        return {
            "status": "success",
            "data": holidays
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    
@app.get("/top-stocks")
async def get_top_stocks(category: str = None, limit: int = 5):
    """
    Get the latest top stocks for after-hours or premarket.
    Args:
        category (str, optional): Filter by category ('after_hours' or 'premarket')
        limit (int): Number of records to return
    Returns:
        dict: Dictionary containing the top stocks data
    """
    try:
        if category and category not in ['after_hours', 'premarket']:
            raise HTTPException(
                status_code=400,
                detail="Category must be either 'after_hours' or 'premarket'"
            )
            
        stocks = get_latest_top_stocks(category, limit)
        return {"status": "success", "data": stocks}
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# ---------------------------- SCRAPER FUNCTIONS ----------------------------

def run_scrapers():
    """
    Runs all the scrapers to collect
    all the market data
    """
    try:
        from scrapers.econ_scraper import scrape_and_store_economic_data
        from scrapers.fear_sentiment import fear_index
        from scrapers.earnings_scraper import scrape_all_earnings
        from scrapers.premarket_movers import get_premarket_movers
        from scrapers.general_info import get_market_holidays
        
        # Create top_stocks table if it doesn't exist
        logging.info("Creating top_stocks table...")
        create_top_stocks_table()
        logging.info("Top stocks table created successfully")
        
        # Scrape and store economic events
        scrape_and_store_economic_data()
        
        # Get fear index
        fear_index()
        
        # Get earnings data
        logging.info("Fetching earnings data...")
        earnings = scrape_all_earnings()
        # Store top 5 earnings stocks
        if earnings:
            logging.info(f"Found {len(earnings)} earnings records")
            top_earnings = [{'ticker': stock['Ticker'], 'rank': i+1} 
                          for i, stock in enumerate(earnings[:5])]
            logging.info(f"Storing top earnings: {top_earnings}")
            store_top_stocks('after_hours', top_earnings)
        else:
            logging.warning("No earnings data found")

        # Get Market Holidays
        get_market_holidays()
        
        # Get pre-market movers
        logging.info("Fetching premarket movers...")
        premarket = get_premarket_movers()
        # Store top 5 premarket stocks
        if premarket and premarket.get('gainers'):
            logging.info(f"Found {len(premarket['gainers'])} premarket records")
            top_premarket = [{'ticker': stock['symbol'], 'rank': i+1} 
                           for i, stock in enumerate(premarket['gainers'][:5])]
            logging.info(f"Storing top premarket: {top_premarket}")
            store_top_stocks('premarket', top_premarket)
        else:
            logging.warning("No premarket data found")
        
    except Exception as e:
        logging.error(f"Error running scrapers: {e}")
        raise  

# ---------------------------- MAIN ----------------------------

def main():
    """
    Main function to run the scrapers and the API server.
    """
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