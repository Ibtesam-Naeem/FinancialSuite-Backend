import os
import requests
from datetime import datetime
from dotenv import load_dotenv
from utils.logger import setup_logging
from utils.db_manager import store_market_holidays

load_dotenv()
logging = setup_logging("GeneralInfoLogger")

POLYGON_API_KEY = os.getenv("POLYGON_API_KEY")

def get_market_holidays():
    """
    Fetches stock market holidays from Polygon.io API.
    Returns list of dictionaries containing holiday data.
    """
    try:
        # Gets the current year
        current_year = datetime.now().year
        
        # Endpoint for market holidays
        url = f"https://api.polygon.io/v1/marketstatus/upcoming"
        
        params = {
            "apiKey": POLYGON_API_KEY,
        }

        logging.info("Fetching market holidays from Polygon.io")
        response = requests.get(url, params=params)
        response.raise_for_status()
        
        holidays_data = response.json()
        
        processed_holidays = []
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

            except KeyError as e:
                logging.warning(f"Missing data for holiday: {e}")
                continue

        # Stores the data in the database
        if processed_holidays:
            store_market_holidays(processed_holidays)
            logging.info(f"Successfully processed {len(processed_holidays)} market holidays")
        
        return processed_holidays

    except requests.exceptions.RequestException as e:
        logging.error(f"Error fetching holiday data from Polygon.io: {e}")
        return []
    
    except Exception as e:
        logging.error(f"Unexpected error processing market holidays: {e}")
        return []