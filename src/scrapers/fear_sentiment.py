import time
from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeout
from utils.logger import setup_logger
from utils.db_manager import store_fear_greed_index, get_latest_fear_greed

logger = setup_logger("SentimentLogger")

# ---------------------------- HELPER FUNCTION ----------------------------

def get_fear_category(fear_value):
    """
    Returns the Fear & Greed category based on the given value (0-100).
    """
    fear_value = int(fear_value)

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
        return "Unknown"

# ---------------------------- MAIN FUNCTION ----------------------------

def fear_index():
    """
    Scrapes CNN's Fear & Greed Index, stores it in the database, and returns the current data.
    Returns a list containing the fear value, category, and stored date, or empty list if failed.
    """
    try:
        p = sync_playwright().start()
        browser = p.chromium.launch(headless=True)
        context = browser.new_context()
        page = context.new_page()

        page.goto("https://www.cnn.com/markets/fear-and-greed", timeout=30000)
        logger.info("Navigated to Fear & Greed Index")

        page.wait_for_selector("span.dial-number-value", timeout=15000)

        fear_value_text = page.locator("span.dial-number-value").first.text_content()
        fear_value = int(fear_value_text.strip())
        category = get_fear_category(fear_value)

        logger.info(f"Fear Value: {fear_value} - Category: {category}")

        store_fear_greed_index(fear_value, category)
        latest_entry = get_latest_fear_greed(1)

        return [{
            "Fear Value": fear_value,
            "Category": category,
            "Stored Date": latest_entry[0]["Date"] if latest_entry else "N/A"
        }]

    except PlaywrightTimeout as e:
        logger.error(f"Timeout while loading Fear & Greed index: {e}")
        return []

    except Exception as e:
        logger.error(f"Unable to locate fear value: {e}")
        return []

    finally:
        try:
            browser.close()
            p.stop()
        except Exception:
            pass
