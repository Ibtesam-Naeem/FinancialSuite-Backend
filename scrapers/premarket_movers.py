from datetime import datetime
import requests
from utils.logger import setup_logging
from utils.db_manager import store_premarket_data
import os
from dotenv import load_dotenv

load_dotenv()
logging = setup_logging("PremarketLogger")

POLYGON_API_KEY = os.getenv("POLYGON_API_KEY")

def get_premarket_movers():
    """
    Fetches pre-market gainers and losers using Polygon.io API.
    Returns list of dictionaries containing ticker data.
    """
    try:
        # Get current date in YYYY-MM-DD format
        today = datetime.now().strftime('%Y-%m-%d')
        
        # Endpoint for pre-market data
        url = "https://api.polygon.io/v2/snapshot/locale/us/markets/stocks/gainers"
        
        params = {
            "apiKey": POLYGON_API_KEY,
            "include_otc": False,
            "session": "pre-market"
        }

        logging.info("Fetching pre-market gainers from Polygon.io")
        gainers_response = requests.get(url, params=params)
        gainers_response.raise_for_status()
        
        # Gets pre-market losers
        url = "https://api.polygon.io/v2/snapshot/locale/us/markets/stocks/losers"
        logging.info("Fetching pre-market losers from Polygon.io")
        losers_response = requests.get(url, params=params)
        losers_response.raise_for_status()

        gainers_data = gainers_response.json().get("tickers", [])
        losers_data = losers_response.json().get("tickers", [])
        
        def process_tickers(tickers):
            processed = []
            for ticker in tickers:
                try:
                    ticker_data = {
                        "symbol": ticker["ticker"],
                        "price": ticker["day"]["c"],
                        "change": ticker["todaysChange"],
                        "change_percent": ticker["todaysChangePerc"],
                        "volume": ticker["day"]["v"],
                        "timestamp": today
                    }
                    processed.append(ticker_data)

                except KeyError as e:
                    logging.warning(f"Missing data for ticker {ticker.get('ticker', 'unknown')}: {e}")
                    continue
            return processed

        # Process gainers and losers
        gainers = process_tickers(gainers_data)[:20]  
        losers = process_tickers(losers_data)[:20]   
        result = {
            "gainers": gainers,
            "losers": losers
        }

        # Store in database
        store_premarket_data(result)
        logging.info(f"Successfully processed {len(gainers)} gainers and {len(losers)} losers")
        return result

    except requests.exceptions.RequestException as e:
        logging.error(f"Error fetching data from Polygon.io: {e}")
        return {"gainers": [], "losers": []}
    
    except Exception as e:
        logging.error(f"Unexpected error processing pre-market data: {e}")
        return {"gainers": [], "losers": []}