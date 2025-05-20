import time
from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeout
from utils.logger import setup_logger
from utils.db_manager import store_fear_greed_index, get_latest_fear_greed

logger = setup_logger("scraper.sentiment")

# ---------------------------- HELPER FUNCTION ----------------------------

def get_fear_category(fear_value):
    """
    Returns the Fear & Greed category based on the given value (0-100).
    """
    try:
        fear_value = int(fear_value)
        logger.debug(f"Categorizing fear value: {fear_value}")

        if 0 <= fear_value <= 25:
            return "Extreme Fear"
        elif 26 <= fear_value <= 44:
            return "Fear"
        elif 45 <= fear_value <= 55:
            return "Neutral"
        elif 56 <= fear_value <= 74:
            return "Greed"
        elif 75 <= fear_value <= 100:
            return "Extreme Greed"
        else:
            logger.warning(f"Fear value {fear_value} outside expected range 0-100")
            return "Unknown"
    except ValueError:
        logger.error(f"Invalid fear value provided: {fear_value}")
        return "Unknown"

# ---------------------------- MAIN FUNCTION ----------------------------

def fear_index():
    """
    Scrapes CNN's Fear & Greed Index, stores it in the database, and returns the current data.
    Returns a list containing the fear value, category, and stored date, or empty list if failed.
    """
    start_time = time.time()
    try:
        logger.debug("Starting Playwright for fear index scrape")
        p = sync_playwright().start()
        browser = p.chromium.launch(headless=True)
        context = browser.new_context()
        page = context.new_page()

        logger.debug("Navigating to CNN Fear & Greed page")
        page.goto("https://www.cnn.com/markets/fear-and-greed", timeout=30000)

        logger.debug("Waiting for fear value to load")
        page.wait_for_selector("span.dial-number-value", timeout=15000)

        fear_value_text = page.locator("span.dial-number-value").first.text_content()
        fear_value = int(fear_value_text.strip())
        category = get_fear_category(fear_value)

        duration = time.time() - start_time
        logger.info(f"Fear & Greed value: {fear_value} ({category}) - scraped in {duration:.2f}s")

        store_fear_greed_index(fear_value, category)
        latest_entry = get_latest_fear_greed(1)

        return [{
            "Fear Value": fear_value,
            "Category": category,
            "Stored Date": latest_entry[0]["Date"] if latest_entry else "N/A"
        }]

    except PlaywrightTimeout as e:
        duration = time.time() - start_time
        logger.error(f"Timeout scraping Fear & Greed index after {duration:.2f}s: {e}")
        return []

    except Exception as e:
        duration = time.time() - start_time
        logger.error(f"Error scraping Fear & Greed index after {duration:.2f}s: {e}")
        return []

    finally:
        try:
            browser.close()
            p.stop()
        except Exception:
            pass
