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

def fear_index(headless=True):
    """
    Scrapes CNN's Fear & Greed Index, stores it in the database, and returns the current data.
    Returns a list containing the fear value, category, and stored date, or empty list if failed.
    """
    start_time = time.time()
    try:
        logger.debug("Starting Playwright for fear index scrape")
        p = sync_playwright().start()
        browser = p.chromium.launch(headless=headless)
        context = browser.new_context(
            viewport={'width': 1920, 'height': 1080},
            user_agent='Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36'
        )
        page = context.new_page()

        logger.debug("Navigating to CNN Fear & Greed page")
        page.goto("https://www.cnn.com/markets/fear-and-greed", timeout=60000)
        
        # Wait for the page to be fully loaded
        page.wait_for_load_state('networkidle')
        time.sleep(5)  

        selectors = [
            "span.dial-number-value",
            "div[class*='dial-number'] span",
            "div[class*='fear-greed'] span[class*='value']",
            "div[class*='fear-greed'] span[class*='number']"
        ]

        fear_value = None

        for selector in selectors:
            try:
                logger.debug(f"Trying selector: {selector}")
                element = page.wait_for_selector(selector, timeout=5000)
                if element:
                    fear_value_text = element.text_content()
                    if fear_value_text and fear_value_text.strip().isdigit():
                        fear_value = int(fear_value_text.strip())
                        logger.debug(f"Found fear value: {fear_value} using selector: {selector}")
                        break

            except Exception as e:
                logger.debug(f"Selector {selector} failed: {e}")
                continue

        if not fear_value:
            raise Exception("Unable to find fear value on the page")

        category = get_fear_category(fear_value)

        duration = time.time() - start_time
        logger.info(f"Fear & Greed value: {fear_value} ({category}) - scraped in {duration:.2f}s")

        store_fear_greed_index(fear_value, category)
        latest_entry = get_latest_fear_greed()

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

# ---------------------------- END OF FILE ----------------------------