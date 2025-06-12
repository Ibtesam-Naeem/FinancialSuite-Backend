# ------------------------------ IMPORTS ------------------------------
from fastapi import APIRouter, HTTPException
from utils.logger import setup_logger
from utils.scheduler import scheduler
from scrapers.econ_scraper import scrape_and_store_economic_data
from scrapers.fear_sentiment import fear_index
from scrapers.earnings_scraper import scrape_all_earnings
from scrapers.general_info import fetch_and_store_market_holidays

logger = setup_logger("api.scrapers")
router = APIRouter()

# ------------------------------ ENDPOINTS ------------------------------
@router.get("/trigger-scrapers")
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
        logger.error(f"Error triggering scrapers: {e}")
        return {"status": "error", "message": str(e), "results": results} 