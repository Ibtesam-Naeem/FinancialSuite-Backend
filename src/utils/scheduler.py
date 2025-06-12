# ------------------------------ IMPORTS ------------------------------
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from utils.logger import setup_logger
from utils.config import Settings
from scrapers.econ_scraper import scrape_and_store_economic_data
from scrapers.fear_sentiment import fear_index
from scrapers.earnings_scraper import scrape_all_earnings, scrape_next_week_earnings
from scrapers.general_info import fetch_and_store_market_holidays

logger = setup_logger("scheduler")
settings = Settings()

scheduler = BackgroundScheduler()

# ------------------------------ SETUP SCHEDULER ------------------------------
def setup_scheduler():
    """
    Sets up scheduled scraper jobs.
    """
    # Economic data
    scheduler.add_job(
        scrape_and_store_economic_data,
        CronTrigger(
            hour=settings.ECONOMIC_DATA_HOUR,
            minute=settings.ECONOMIC_DATA_MINUTE
        ),
        id="economic_data",
        name="Economic Data Scraper",
        replace_existing=True
    )
    
    # Fear index
    scheduler.add_job(
        fear_index,
        CronTrigger(hour=settings.FEAR_INDEX_INTERVAL, minute=0),
        id="fear_index",
        name="Fear Index Scraper",
        replace_existing=True
    )
    
    # Earnings
    scheduler.add_job(
        scrape_all_earnings,
        CronTrigger(
            hour=settings.EARNINGS_HOUR,
            minute=settings.EARNINGS_MINUTE
        ),
        id="earnings",
        name="Earnings Scraper",
        replace_existing=True
    )
    
    # Next Week Earnings
    scheduler.add_job(
        scrape_next_week_earnings,
        CronTrigger(
            day_of_week=settings.NEXT_WEEK_EARNINGS_DAY,
            hour=settings.NEXT_WEEK_EARNINGS_HOUR,
            minute=settings.NEXT_WEEK_EARNINGS_MINUTE
        ),
        id="next_week_earnings",
        name="Next Week Earnings Scraper",
        replace_existing=True
    )
    
    # Market holidays
    scheduler.add_job(
        fetch_and_store_market_holidays,
        CronTrigger(
            day_of_week=settings.MARKET_HOLIDAYS_DAY,
            hour=settings.MARKET_HOLIDAYS_HOUR,
            minute=settings.MARKET_HOLIDAYS_MINUTE
        ),
        id="market_holidays",
        name="Market Holidays Scraper",
        replace_existing=True
    )
    
    if not scheduler.running:
        scheduler.start()
        logger.info("Scheduler started successfully")
        
        # Log all scheduled jobs
        jobs = scheduler.get_jobs()
        for job in jobs:
            logger.info(f"Scheduled job: {job.name} - Next run: {job.next_run_time}")

# ------------------------------ RUN SCRAPERS ------------------------------
def run_scrapers():
    """
    Runs all scrapers sequentially.
    """
    try:
        logger.info("Starting scrapers...")

        # Scrape and store economic data
        scrape_and_store_economic_data()

        # Scrape fear index
        fear_index()

        # Scrape all earnings
        scrape_all_earnings()

        # Scrape next week earnings
        scrape_next_week_earnings()

        # Fetch and store market holidays
        fetch_and_store_market_holidays()
        
        logger.info("All scrapers finished successfully")

    except Exception as e:
        logger.error(f"Scraper error: {e}")
        raise 

# ------------------------------ END OF FILE ------------------------------