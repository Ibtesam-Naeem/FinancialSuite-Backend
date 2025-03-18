from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from utils.chrome_options import chrome_options 
from utils.logger import setup_logging
from utils.db_manager import store_earnings_data
import time

# Initialize logger
logging = setup_logging("EarningsScraper")

# ---------------------------- BROWSER FUNCTIONS ----------------------------

def open_earnings_calendar():
    """
    Initializes Chrome WebDriver and navigates to TradingView's Earnings Calendar.
    
    Returns:
        WebDriver: Initialized driver if successful
        None: If initialization fails
    """
    try:
        driver = chrome_options()
        logging.info("Initializing WebDriver and opening earnings calendar page.")
        driver.get("https://www.tradingview.com/markets/stocks-usa/earnings/")
        
        # Wait for data table to load
        WebDriverWait(driver, 30).until(
            EC.presence_of_element_located((By.CLASS_NAME, "tv-data-table"))
        )
        logging.info("Earnings calendar page loaded successfully.")
        return driver
    
    except Exception as e:
        logging.error(f"Failed to open earnings calendar: {e}")
        return None

# ---------------------------- DATA EXTRACTION ----------------------------

def scrape_earnings_data(driver):
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
    
    Returns:
        list: List of dictionaries containing earnings data
    """
    # Applies the "This Week" filter
    try:
        WebDriverWait(driver, 10).until(
            EC.presence_of_all_elements_located((By.XPATH, "//div[contains(@class, 'itemContent-LeZwGiB6') and contains(text(), 'This Week')]"))
        )
        this_week_button = driver.find_element(By.XPATH, "//div[contains(@class, 'itemContent-LeZwGiB6') and contains(text(), 'This Week')]")
        this_week_button.click()
        logging.info("Clicked on 'This Week' button.")
    
    except Exception as e:
        logging.error(f"Failed to click on 'This Week' button: {e}")

    # Waits for data table to refresh
    WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.CLASS_NAME, "tv-data-table"))
    )

    time.sleep(2)  
    while True:
        try:
            load_more_button = WebDriverWait(driver, 2).until(
                EC.presence_of_element_located((By.CLASS_NAME, "tv-load-more__btn"))
            )
            load_more_button.click()
            logging.info("Clicked 'Load More' button. Loading more data.")
            time.sleep(1)  # Prevent rate limiting

        except Exception:
            logging.info("No more data to load.")
            break

    # Extracts earnings data from table
    earnings_data = []
    rows = driver.find_elements(By.CLASS_NAME, "tv-data-table__row")
    logging.info(f"Scraping earnings for {len(rows)} stocks.")

    for index, row in enumerate(rows):
        try:
            # Extract ticker symbol
            ticker_element = WebDriverWait(row, 3).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "[data-field-key='name']"))
            )
            ticker_full = ticker_element.text.strip()
            ticker_d = ticker_full.split("\n")[0]

            # If it ends with 'D', remove it as tradingview has a "D" in some tickers
            if ticker_d.endswith("D"):
                ticker = ticker_d[:-1]
            else:
                ticker = ticker_d

            # Extract market cap
            mkt_cap_element = row.find_element(By.CSS_SELECTOR, "[data-field-key='market_cap_basic']")
            mtk_cap = mkt_cap_element.text.strip("USD") if mkt_cap_element else "N/A"

            # Extract EPS data
            eps_estimate_element = row.find_element(By.CSS_SELECTOR, "[data-field-key='earnings_per_share_forecast_next_fq']")
            eps_estimate = eps_estimate_element.text.strip("USD") if eps_estimate_element else "N/A"

            reported_eps_element = row.find_element(By.CSS_SELECTOR, '[data-field-key="earnings_per_share_fq"]')
            reported_eps = reported_eps_element.text.strip("USD") if reported_eps_element else "N/A"

            # Extract revenue data
            revenue_forecast_element = row.find_element(By.CSS_SELECTOR, "[data-field-key='revenue_forecast_next_fq']")
            revenue_forecast = revenue_forecast_element.text.strip("USD") if revenue_forecast_element else "N/A"
            
            reported_revenue_forecast = row.find_element(By.CSS_SELECTOR, '[data-field-key="revenue_fq"]')
            reported_revenue = reported_revenue_forecast.text.strip("USD") if reported_revenue_forecast else "N/A"

            # Extract timing information
            time_element = row.find_element(By.CSS_SELECTOR, "[data-field-key='earnings_release_next_time']")
            time_reporting = time_element.get_attribute("title").strip() or "Unknown"
            
            # Extract the date reporting information
            date_reporting_element = row.find_element(By.CSS_SELECTOR, "[data-field-key='earnings_release_next_date']")
            date_reporting = date_reporting_element.text.strip() if date_reporting_element else "N/A"

            # Store extracted data
            earnings_data.append({
                "Ticker": ticker,
                "Date Reporting": date_reporting,
                "EPS Estimate": eps_estimate,
                "Reported EPS": reported_eps,
                "Reported Revenue": reported_revenue,
                "Revenue Forecast": revenue_forecast,
                "Time": time_reporting,
                "Market Cap": mtk_cap,
            })

        except Exception as e:
            logging.error(f"Error processing row {index}: {e}")

    return earnings_data

# ---------------------------- MAIN FUNCTION ----------------------------

def scrape_all_earnings():
    """
    Main function that:
    1. Opens the earnings calendar
    2. Scrapes the earnings data
    3. Stores it in the database
    
    Returns:
        list: Scraped earnings data if successful
        empty list: If any step fails
    """
    driver = open_earnings_calendar()
    if not driver:
        logging.error("WebDriver initialization failed.")
        return []

    try:
        earnings_data = scrape_earnings_data(driver)
        if earnings_data:
            store_earnings_data(earnings_data) 
            logging.info(f"Successfully stored {len(earnings_data)} earnings records in the database.")
        return earnings_data

    except Exception as e:
        logging.error(f"Error scraping earnings: {e}")
        return []
    
    finally:
        driver.quit()
