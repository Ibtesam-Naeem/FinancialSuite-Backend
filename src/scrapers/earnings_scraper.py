from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeout
from utils.logger import setup_logger
from utils.db_manager import store_earnings_data
import time

# Set up logger with consistent naming
logger = setup_logger("scraper.earnings")

# ---------------------------- BROWSER FUNCTIONS ----------------------------

def open_earnings_calendar():
    """
    Initializes Playwright Chromium and navigates
    to TradingView's Earnings Calendar.
    """
    start_time = time.time()
    try:
        logger.debug("Starting Playwright browser")
        p = sync_playwright().start()
        browser = p.chromium.launch(headless=True)
        context = browser.new_context()
        page = context.new_page()
        
        logger.debug("Navigating to earnings calendar")
        page.goto("https://www.tradingview.com/markets/stocks-usa/earnings/", timeout=60000)

        logger.debug("Waiting for data table to load")
        page.wait_for_selector(".tv-data-table", timeout=30000)
        
        duration = time.time() - start_time
        logger.info(f"Earnings calendar loaded in {duration:.2f}s")
        return p, browser, page

    except Exception as e:
        duration = time.time() - start_time
        logger.error(f"Failed to open earnings calendar after {duration:.2f}s: {e}")
        return None, None, None

# ---------------------------- DATA EXTRACTION ----------------------------

def scrape_earnings_data(page):
    """
    Extracts earnings data from TradingView for all stocks.

    Process:
    1. Clicks 'This Week' filter
    2. Loads all available data by clicking 'Load More'
    3. Extracts data for each stock:
       - Ticker symbol
       - Market cap
       - EPS (estimated and reported)
       - Revenue (estimated and reported)
       - Earnings date and time
    """
    # Applies the "This Week" filter
    try:
        this_week_button = page.locator("//div[contains(@class, 'itemContent-LeZwGiB6') and contains(text(), 'This Week')]")
        this_week_button.wait_for(timeout=10000)
        this_week_button.click()
        logger.info("Clicked on 'This Week' button.")
    except PlaywrightTimeout as e:
        logger.error(f"Failed to click on 'This Week' button: {e}")

    page.wait_for_selector(".tv-data-table", timeout=10000)
    time.sleep(2)

    # Click all 'Load More' buttons
    while True:
        try:
            load_more_button = page.locator(".tv-load-more__btn")
            if load_more_button.is_visible():
                load_more_button.click()
                logger.info("Clicked 'Load More' button. Loading more data.")
                time.sleep(1)
            else:
                break
        except Exception:
            logger.info("No more data to load.")
            break

    # Extracts earnings data from table
    earnings_data = []
    rows = page.locator(".tv-data-table__row")
    row_count = rows.count()
    logger.info(f"Scraping earnings for {row_count} stocks.")
    time.sleep(5)

    for index in range(row_count):
        try:
            row = rows.nth(index)

            # Extract ticker symbol
            ticker_element = row.locator("[data-field-key='name']")
            ticker_full = ticker_element.inner_text(timeout=3000).strip()
            ticker_d = ticker_full.split("\n")[0]
            ticker = ticker_d[:-1] if ticker_d.endswith("D") else ticker_d

            # Market cap
            mtk_cap = row.locator("[data-field-key='market_cap_basic']").inner_text().strip("USD")

            # EPS
            eps_estimate = row.locator("[data-field-key='earnings_per_share_forecast_next_fq']").inner_text().strip("USD")
            reported_eps = row.locator("[data-field-key='earnings_per_share_fq']").inner_text().strip("USD")

            # Revenue
            revenue_forecast = row.locator("[data-field-key='revenue_forecast_next_fq']").inner_text().strip("USD")
            reported_revenue = row.locator("[data-field-key='revenue_fq']").inner_text().strip("USD")

            # Time & date
            time_reporting = row.locator("[data-field-key='earnings_release_next_time']").get_attribute("title") or "Unknown"
            date_reporting = row.locator("[data-field-key='earnings_release_next_date']").inner_text().strip()

            earnings_data.append({
                "Ticker": ticker,
                "Date Reporting": date_reporting,
                "EPS Estimate": eps_estimate,
                "Reported EPS": reported_eps,
                "Reported Revenue": reported_revenue,
                "Revenue Forecast": revenue_forecast,
                "Time": time_reporting.strip() if time_reporting else "Unknown",
                "Market Cap": mtk_cap,
            })

        except Exception as e:
            logger.error(f"Error processing row {index}: {e}")

    return earnings_data

# ---------------------------- MAIN FUNCTION ----------------------------

def scrape_all_earnings():
    """
    Main function that:
    1. Opens the earnings calendar
    2. Scrapes the earnings data
    3. Stores it in the database
    """
    start_time = time.time()
    
    p, browser, page = open_earnings_calendar()
    if not page:
        logger.error("Browser initialization failed")
        return []

    try:
        logger.debug("Starting earnings data scrape")
        earnings_data = scrape_earnings_data(page)
        
        if earnings_data:
            logger.debug(f"Found {len(earnings_data)} earnings records")
            store_earnings_data(earnings_data)
            duration = time.time() - start_time
            logger.info(f"Complete earnings scrape finished in {duration:.2f}s")
        else:
            logger.warning("No earnings data found to store")
            
        return earnings_data

    except Exception as e:
        duration = time.time() - start_time
        logger.error(f"Error scraping earnings after {duration:.2f}s: {e}")
        return []

    finally:
        browser.close()
        p.stop()
