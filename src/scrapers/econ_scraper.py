from datetime import datetime
from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeout
from utils.logger import setup_logger
from utils.db_manager import store_economic_data
import time

logger = setup_logger("scraper.economic")

# ---------------------------- HELPER FUNCTIONS ----------------------------

def clean_text(value):
    """
    Removes newline characters and trims spaces from text values.
    Returns 'N/A' if value is None.
    """
    cleaned = value.replace("\n", "").strip() if value else "N/A"
    logger.debug(f"Cleaned text value: {value} -> {cleaned}")
    return cleaned

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
    Initializes Playwright and navigates to TradingView's 
    USDCAD Economic Calendar.
    """
    start_time = time.time()
    try:
        logger.debug("Starting Playwright browser")
        p = sync_playwright().start()
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(viewport={"width": 1920, "height": 1080})
        page = context.new_page()

        logger.debug("Navigating to economic calendar")
        page.goto("https://www.tradingview.com/symbols/USDCAD/economic-calendar/?exchange=FX_IDC", timeout=60000)
        
        logger.debug("Waiting for calendar items to load")
        page.wait_for_selector("div[data-name*='economic-calendar-item']", timeout=30000)
        
        duration = time.time() - start_time
        logger.info(f"Economic calendar loaded in {duration:.2f}s")
        return p, browser, page
        
    except Exception as e:
        duration = time.time() - start_time
        logger.error(f"Failed to open economic calendar after {duration:.2f}s: {e}")
        return None, None, None

def filter_option(page):
    """
    Applies filters to the economic calendar:
    1. Clicks "High Importance" filter
    2. Selects "This Week" timeframe
    """
    start_time = time.time()
    try:
        logger.debug("Looking for importance filter button")
        importance_button = page.locator('button:has-text("Importance")')
        importance_button.scroll_into_view_if_needed()
        time.sleep(1)
        importance_button.click()
        logger.debug("Clicked importance filter")
        
        logger.debug("Looking for 'This Week' button")
        this_week_button = page.locator('button:has-text("This week")')
        this_week_button.scroll_into_view_if_needed()
        time.sleep(1)
        this_week_button.click()
        
        duration = time.time() - start_time
        logger.debug(f"Applied calendar filters in {duration:.2f}s")
        
    except Exception as e:
        duration = time.time() - start_time
        logger.error(f"Failed to apply filters after {duration:.2f}s: {e}")

# ---------------------------- DATA EXTRACTION ----------------------------

def scrape_economic_data(page):
    """
    Extracts economic event data from the filtered calendar.

    Collects for each event:
    - Date and time
    - Country
    - Event name
    - Actual, forecast, and prior values
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

            # Time
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
    """
    start_time = time.time()
    
    p, browser, page = open_economic_calendar()
    if not page:
        logger.error("Browser initialization failed")
        return []

    try:
        logger.debug("Applying calendar filters")
        filter_option(page)
        time.sleep(2)
        
        logger.debug("Starting economic data scrape")
        economic_data = scrape_economic_data(page)

        if economic_data:
            logger.debug(f"Found {len(economic_data)} economic events")
            store_economic_data(economic_data)
            duration = time.time() - start_time
            logger.info(f"Complete economic scrape finished in {duration:.2f}s")
            return economic_data
        else:
            logger.warning("No economic data found to store")
            return []

    except Exception as e:
        duration = time.time() - start_time
        logger.error(f"Error scraping economic data after {duration:.2f}s: {e}")
        return []

    finally:
        browser.close()
        p.stop()
