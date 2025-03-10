from datetime import datetime
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from utils.chrome_options import chrome_options
from utils.logger import setup_logging
from utils.db_manager import store_economic_data
import time

logging = setup_logging("EconScraper")

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
    Initializes Chrome WebDriver and navigates to TradingView's USDCAD Economic Calendar.
    
    Returns:
        WebDriver: Initialized driver if successful
        None: If initialization fails
    """
    try:
        driver = chrome_options()
        driver.set_window_size(1920, 1080)
        logging.info("Initializing WebDriver and opening economic calendar page.")
        driver.get("https://www.tradingview.com/symbols/USDCAD/economic-calendar/?exchange=FX_IDC")
        
        # Wait for calendar items to load
        WebDriverWait(driver, 30).until(
            EC.presence_of_element_located((By.XPATH, "//div[contains(@data-name, 'economic-calendar-item')]"))
        )
        logging.info("Economic calendar page loaded successfully.")
        return driver
    
    except Exception as e:
        logging.error(f"Failed to open economic calendar: {e}")
        return None

def filter_option(driver):
    """
    Applies filters to the economic calendar:
    1. Clicks "High Importance" filter
    2. Selects "This Week" timeframe
    
    Note: Uses JavaScript click due to potential overlay issues
    """
    # Applies 'High Importance' filter
    try:
        logging.info("Finding the High Importance button.")
        importance_button = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.XPATH, 
                '//*[@id="js-category-content"]/div[2]/div/section/div/div[2]/div/div/div/div[1]/div[1]/button/span[2]/span[1]'
            ))
        )
        driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", importance_button)
        time.sleep(2)  # Allow page to settle after scroll
        driver.execute_script("arguments[0].click();", importance_button)
        logging.info("Importance button clicked successfully.")
    
    except Exception as e:
        logging.error(f"Failed to click Importance button: {e}")
    
    # Applies 'This Week' filter
    try:
        logging.info(f"Selecting 'This Week' option")
        time.sleep(2)  

        this_week_button = WebDriverWait(driver, 15).until(
            EC.element_to_be_clickable((By.XPATH, "//button[contains(., 'This week')]"))
        )
        driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", this_week_button)
        driver.execute_script("arguments[0].click();", this_week_button)
   
    except Exception as e:
        logging.error(f"Failed to select 'This Week': {e}")
        return 

# ---------------------------- DATA EXTRACTION ----------------------------

def scrape_economic_data(driver):
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
    logging.info("Waiting for the economic calendar to load.")
    
    # Verifies data is available
    try:
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.XPATH, "//div[contains(@data-name, 'economic-calendar-item')]"))
        )
    except Exception:
        logging.warning("No economic calendar data available. Skipping scrape.")
        return []

    # Get all event rows
    rows = driver.find_elements(By.XPATH, "//div[contains(@data-name, 'economic-calendar-item')]")

    if not rows:
        logging.warning("No economic calendar rows found. Skipping.")
        return []

    econ_data = []
    logging.info(f"Scraping Econ Events for {len(rows)} events.")

    # Process each event row
    for index, row in enumerate(rows):
        try:
            # Extract date
            date_element = row.find_elements(By.XPATH, ".//time")
            event_date = format_date(date_element[0].get_attribute("datetime")) if date_element else "N/A"

            # Extract time (requires JavaScript due to shadow DOM)
            event_time = driver.execute_script("""
                let shadow_host = arguments[0].shadowRoot;
                return shadow_host ? shadow_host.querySelector('time-format').textContent.trim() : 'N/A';
            """, row)

            # Extract country
            country_elements = row.find_elements(By.XPATH, ".//span[contains(@class, 'countryName')]")
            country = country_elements[0].text.strip() if country_elements else "N/A"

            # Extract event name
            event_elements = row.find_elements(By.XPATH, ".//span[contains(@class, 'titleText')]")
            event_name = event_elements[0].text.strip() if event_elements else "N/A"

            # Extract values
            value_elements = row.find_elements(By.XPATH, ".//span[contains(@class, 'valueWithUnit')]")
            actual_value = clean_text(value_elements[0].text) if len(value_elements) > 0 else "N/A"
            forecast_value = clean_text(value_elements[1].text) if len(value_elements) > 1 else "N/A"
            prior_value = clean_text(value_elements[2].text) if len(value_elements) > 2 else "N/A"

            # Stores event data
            econ_data.append({
                "date": event_date,
                "time": event_time,
                "country": country,
                "event": event_name,
                "actual": actual_value,
                "forecast": forecast_value,
                "prior": prior_value
            })

        except Exception as e:
            logging.error(f"Error processing row {index}: {e}")

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
    driver = open_economic_calendar()
    
    if not driver:
        logging.error("WebDriver initialization failed.")
        return []

    try:
        filter_option(driver)
        time.sleep(2)  
        economic_data = scrape_economic_data(driver)

        if economic_data:
            store_economic_data(economic_data) 
            return economic_data

    except Exception as e:
        logging.error(f"Error scraping economic data: {e}.")
        return []
    
    finally:
        driver.quit()
