import requests
from datetime import datetime
from dotenv import load_dotenv
from utils.logger import setup_logger
from utils.db_manager import store_market_holidays
import os
import time

# ------------------------------ ENV & logger ------------------------------

load_dotenv()
POLYGON_API_KEY = os.getenv("POLYGON_API_KEY")

logger = setup_logger("scraper.holidays")

# ------------------------------ FETCH HOLIDAYS ------------------------------

def get_market_holidays():
    """
    Fetches stock market holidays from Polygon.io API.
    Returns list of dictionaries containing the holiday data.
    """
    start_time = time.time()
    try:
        current_year = datetime.now().year
        url = "https://api.polygon.io/v1/marketstatus/upcoming"
        params = { "apiKey": POLYGON_API_KEY }

        logger.debug("Making request to Polygon.io for market holidays")
        response = requests.get(url, params=params)
        response.raise_for_status()
        
        holidays_data = response.json()
        processed_holidays = []

        logger.debug(f"Processing {len(holidays_data)} holidays")
        for holiday in holidays_data:
            try:
                holiday_data = {
                    "name": holiday.get("name", "Unknown"),
                    "date": holiday.get("date"),
                    "status": holiday.get("status", "closed"),
                    "exchange": holiday.get("exchange", "NYSE"),
                    "year": current_year
                }
                processed_holidays.append(holiday_data)
                logger.debug(f"Processed holiday: {holiday_data['name']} on {holiday_data['date']}")

            except KeyError as e:
                logger.warning(f"Missing data for holiday: {e}")
        
        duration = time.time() - start_time
        logger.info(f"Fetched {len(processed_holidays)} market holidays in {duration:.2f}s")
        return processed_holidays

    except requests.exceptions.RequestException as e:
        duration = time.time() - start_time
        logger.error(f"Error fetching holiday data from Polygon.io after {duration:.2f}s: {e}")
        return []

    except Exception as e:
        duration = time.time() - start_time
        logger.error(f"Unexpected error processing market holidays after {duration:.2f}s: {e}")
        return []

# ------------------------------ STORE HOLIDAYS ------------------------------

def fetch_and_store_market_holidays():
    """
    Main function to fetch and store market holidays data.
    """
    start_time = time.time()
    holidays_data = get_market_holidays()
    
    if holidays_data:
        logger.debug(f"Attempting to store {len(holidays_data)} holidays")
        store_market_holidays(holidays_data)
        duration = time.time() - start_time
        logger.info(f"Market holidays fetch and store completed in {duration:.2f}s")
    else:
        duration = time.time() - start_time
        logger.warning(f"No market holidays found after {duration:.2f}s")

# ---------------------------- END OF FILE ----------------------------