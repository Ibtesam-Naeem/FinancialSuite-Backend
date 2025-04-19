from datetime import datetime
from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeout
from utils.logger import setup_logger
from utils.db_manager import store_economic_data
import time

logger = setup_logger("EconScraper")

# ---------------------------- HELPER FUNCTIONS ----------------------------

def clean_text(value):
    """
    Removes newline characters and trims spaces from text values.
    Returns 'N/A' if value is None.
    """
    return value.replace("\n", "").strip() if value else "N/A"

def format_date(date_string):
    """
    Formats TradingView date string to standard datetime format.
    Example: '2024-03-20T13:30:00.000Z' -> '2024-03-20 13:30:00'
    Returns original string if parsing fails.
    """
    try:
        return datetime.strptime(date_string, "%Y-%m-%dT%H:%M:%S.%fZ").strftime("%Y-%m-%d %H:%M:%S")
    except ValueError:
        return date_string 

# ---------------------------- BROWSER FUNCTIONS ----------------------------

def open_economic_calendar():
    """
    Initializes Playwright and navigates to TradingView's USDCAD Economic Calendar.
    
    Returns:
        tuple: (playwright, browser, page) if successful
        tuple: (None, None, None) if initialization fails
    """
    try:
        p = sync_playwright().start()
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(viewport={"width": 1920, "height": 1080})
        page = context.new_page()

        logger.info("Initializing Playwright and opening economic calendar page.")
        page.goto("https://www.tradingview.com/symbols/USDCAD/economic-calendar/?exchange=FX_IDC", timeout=60000)
        page.wait_for_selector("div[data-name*='economic-calendar-item']", timeout=30000)
        logger.info("Economic calendar page loaded successfully.")

        return p, browser, page
    except Exception as e:
        logger.error(f"Failed to open economic calendar: {e}")
        return None, None, None

def filter_option(page):
    """
    Applies filters to the economic calendar:
    1. Clicks "High Importance" filter
    2. Selects "This Week" timeframe
    """
    try:
        logger.info("Finding the High Importance button.")
        importance_button = page.locator('button:has-text("Importance")')
        importance_button.scroll_into_view_if_needed()
        time.sleep(1)
        importance_button.click()
        logger.info("Importance button clicked successfully.")
    except Exception as e:
        logger.error(f"Failed to click Importance button: {e}")

    try:
        logger.info("Selecting 'This Week' option")
        this_week_button = page.locator('button:has-text("This week")')
        this_week_button.scroll_into_view_if_needed()
        time.sleep(1)
        this_week_button.click()
    except Exception as e:
        logger.error(f"Failed to select 'This Week': {e}")

# ---------------------------- DATA EXTRACTION ----------------------------

def scrape_economic_data(page):
    """
    Extracts economic event data from the filtered calendar.

    Collects for each event:
    - Date and time
    - Country
    - Event name
    - Actual, forecast, and prior values

    Returns:
        list: List of dictionaries containing event data
    """
    logger.info("Waiting for the economic calendar to load.")

    try:
        page.wait_for_selector("div[data-name*='economic-calendar-item']", timeout=10000)
    except PlaywrightTimeout:
        logger.warning("No economic calendar data available. Skipping scrape.")
        return []

    rows = page.locator("div[data-name*='economic-calendar-item']")
    count = rows.count()

    if count == 0:
        logger.warning("No economic calendar rows found. Skipping.")
        return []

    econ_data = []
    logger.info(f"Scraping Econ Events for {count} events.")

    for index in range(count):
        try:
            row = rows.nth(index)

            # Date
            date_element = row.locator("time")
            event_date = format_date(date_element.get_attribute("datetime")) if date_element.count() > 0 else "N/A"

            # Time (visible directly)
            event_time = row.locator("span[class*=eventTime]").text_content(timeout=2000).strip() if row.locator("span[class*=eventTime]").count() > 0 else "N/A"

            # Country
            country = row.locator("span[class*='countryName']").first.text_content().strip() if row.locator("span[class*='countryName']").count() > 0 else "N/A"

            # Event name
            event_name = row.locator("span[class*='titleText']").first.text_content().strip() if row.locator("span[class*='titleText']").count() > 0 else "N/A"

            # Actual, Forecast, Prior
            values = row.locator("span[class*='valueWithUnit']")
            actual = clean_text(values.nth(0).text_content() or "") if values.count() > 0 else "N/A"
            forecast = clean_text(values.nth(1).text_content() or "") if values.count() > 1 else "N/A"
            prior = clean_text(values.nth(2).text_content() or "") if values.count() > 2 else "N/A"

            econ_data.append({
                "date": event_date,
                "time": event_time,
                "country": country,
                "event": event_name,
                "actual": actual,
                "forecast": forecast,
                "prior": prior
            })

        except Exception as e:
            logger.error(f"Error processing row {index}: {e}")

    return econ_data

# ---------------------------- MAIN FUNCTION ----------------------------

def scrape_and_store_economic_data():
    """
    Main function that:
    1. Opens the economic calendar
    2. Applies filters
    3. Scrapes the data
    4. Stores it in the database

    Returns:
        list: Scraped economic data if successful
        empty list: If any step fails
    """
    p, browser, page = open_economic_calendar()
    if not page:
        logger.error("Browser initialization failed.")
        return []

    try:
        filter_option(page)
        time.sleep(2)
        economic_data = scrape_economic_data(page)

        if economic_data:
            store_economic_data(economic_data)
            logger.info(f"Stored {len(economic_data)} economic events in the database.")
            return economic_data

    except Exception as e:
        logger.error(f"Error scraping economic data: {e}")
        return []

    finally:
        browser.close()
        p.stop()
