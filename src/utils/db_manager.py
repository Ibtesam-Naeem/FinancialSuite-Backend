import os
import psycopg2
from psycopg2.extras import execute_values
from dotenv import load_dotenv
from utils.logger import setup_logger
import time

# Set up logger with consistent naming
logger = setup_logger("database")

load_dotenv()
DB_URL = os.getenv("DB_URL")


def get_db_connection():
    """Establishes a connection to the PostgreSQL database."""
    start_time = time.time()
    try:
        conn = psycopg2.connect(DB_URL)
        logger.debug(f"DB connection established in {(time.time() - start_time):.2f}s")
        return conn
    except Exception as e:
        logger.error(f"Failed to connect to DB after {(time.time() - start_time):.2f}s: {e}")
        raise

# --------------------- EARNINGS REPORT DATABASE FUNCTIONS ---------------------

def store_earnings_data(data):
    """
    Stores earnings data in the PostgreSQL database.
    Prevents duplicates and updates existing records.
    """
    if not data:
        logger.debug("No earnings data provided to store")
        return

    start_time = time.time()
    try:
        conn = get_db_connection()
        cur = conn.cursor()

        # Log table creation attempt
        logger.debug("Ensuring earnings_reports table exists")
        cur.execute("""
            CREATE TABLE IF NOT EXISTS earnings_reports (
                id SERIAL PRIMARY KEY,
                ticker TEXT NOT NULL,
                report_date DATE NOT NULL,
                eps_estimate TEXT,
                reported_eps TEXT,
                revenue_forecast TEXT,
                reported_revenue TEXT,
                time TEXT NOT NULL DEFAULT 'Unknown',
                market_cap TEXT,
                UNIQUE (ticker, report_date, time)
            )
        """)
        conn.commit()

        # Log the insert operation
        logger.debug(f"Attempting to store {len(data)} earnings records")
        
        insert_query = """
        INSERT INTO earnings_reports (ticker, report_date, eps_estimate, reported_eps, revenue_forecast, reported_revenue, time, market_cap)
        VALUES %s
        ON CONFLICT (ticker, report_date, time) DO UPDATE
        SET eps_estimate = EXCLUDED.eps_estimate,
            reported_eps = EXCLUDED.reported_eps,
            revenue_forecast = EXCLUDED.revenue_forecast,
            reported_revenue = EXCLUDED.reported_revenue,
            market_cap = EXCLUDED.market_cap;
        """

        data_values = [
            (
                record["Ticker"],
                record["Date Reporting"],
                record["EPS Estimate"],
                record["Reported EPS"],
                record["Revenue Forecast"],
                record["Reported Revenue"],
                "Unknown" if not record.get("Time") or str(record["Time"]).strip() == "" else record["Time"],
                record["Market Cap"]
            )
            for record in data
        ]

        execute_values(cur, insert_query, data_values)
        conn.commit()
        duration = time.time() - start_time
        logger.info(f"Successfully stored {len(data)} earnings reports in {duration:.2f}s")

    except Exception as e:
        duration = time.time() - start_time
        logger.error(f"Database error (Earnings Reports) after {duration:.2f}s: {e}")
    
    finally:
        cur.close()
        conn.close()


def get_latest_earnings(limit=10):
    """
    Fetches the latest earnings reports from the database.
    """
    conn = get_db_connection()
    cur = conn.cursor()

    cur.execute(f"""
        SELECT ticker, report_date, eps_estimate, reported_eps, revenue_forecast, reported_revenue, time, market_cap
        FROM earnings_reports
        ORDER BY report_date DESC
        LIMIT {limit};
    """)

    rows = cur.fetchall()
    earnings_data = [
        {
            "Ticker": row[0],
            "Date Reporting": row[1],
            "EPS Estimate": row[2],
            "Reported EPS": row[3],
            "Revenue Forecast": row[4],
            "Reported Revenue": row[5],
            "Time": row[6] if row[6] else "Unknown",
            "Market Cap": row[7]
        }
        for row in rows
    ]

    cur.close()
    conn.close()
    return earnings_data

# --------------------- ECONOMIC EVENTS DATABASE FUNCTIONS ---------------------

def store_economic_data(economic_data):
    """
    Stores economic event data in the PostgreSQL database.
    Prevents duplicates and updates existing records.
    """
    if not economic_data:
        logger.info("No economic data to store.")
        return

    try:
        conn = get_db_connection()
        cur = conn.cursor()

        cur.execute("""
            CREATE TABLE IF NOT EXISTS economic_events (
                id SERIAL PRIMARY KEY,
                event_date TIMESTAMP NOT NULL,
                event_time TEXT DEFAULT NULL,
                country TEXT NOT NULL,
                event TEXT NOT NULL,
                actual_value TEXT,
                forecast_value TEXT,
                prior_value TEXT,
                created_at TIMESTAMP DEFAULT NOW(),
                UNIQUE (event_date, event, country)
            )
        """)
        conn.commit()

        insert_query = """
        INSERT INTO economic_events (event_date, event_time, country, event, actual_value, forecast_value, prior_value)
        VALUES %s
        ON CONFLICT (event_date, event, country) 
        DO UPDATE SET
            actual_value = EXCLUDED.actual_value,
            forecast_value = EXCLUDED.forecast_value,
            prior_value = EXCLUDED.prior_value;
        """

        data_values = [
            (
                record["date"],
                record["time"],
                record["country"],
                record["event"],
                record["actual"],
                record["forecast"],
                record["prior"]
            )
            for record in economic_data
        ]

        execute_values(cur, insert_query, data_values) 
        conn.commit()
        logger.info(f"Successfully stored {len(economic_data)} economic events in the database.")

    except Exception as e:
        logger.error(f"Database error (Economic Events): {e}")
    
    finally:
        cur.close()
        conn.close()

def get_latest_economic_events(limit=10):
    """
    Fetches the latest stored economic events from the database.
    """
    conn = get_db_connection()
    cur = conn.cursor()

    cur.execute(f"""
        SELECT event_date, event_time, country, event, actual_value, forecast_value, prior_value
        FROM economic_events
        ORDER BY event_date DESC
        LIMIT {limit};
    """)

    rows = cur.fetchall()
    econ_data = [
        {
            "Date": row[0],
            "Time": row[1] if row[1] else "Unknown",
            "Country": row[2],
            "Event": row[3],
            "Actual": row[4],
            "Forecast": row[5],
            "Prior": row[6],
        }
        for row in rows
    ]

    cur.close()
    conn.close()
    return econ_data

# --------------------- FEAR SENTIMENT DATABASE FUNCTIONS ---------------------

def store_fear_greed_index(fear_value, category):
    """
    Stores the Fear & Greed Index value in PostgreSQL.
    Prevents duplicate entries for the same date.
    """
    conn = get_db_connection()
    cur = conn.cursor()

    cur.execute("""
        CREATE TABLE IF NOT EXISTS fear_greed_index (
            id SERIAL PRIMARY KEY,
            date TIMESTAMP DEFAULT NOW() UNIQUE,
            fear_value INTEGER NOT NULL,
            category TEXT NOT NULL
        )
    """)
    conn.commit()  

    cur.execute("""
        INSERT INTO fear_greed_index (date, fear_value, category)
        VALUES (NOW(), %s, %s)
        ON CONFLICT (date) DO UPDATE
        SET fear_value = EXCLUDED.fear_value,
            category = EXCLUDED.category;
    """, (fear_value, category))

    conn.commit()
    cur.close()
    conn.close()

def get_latest_fear_greed(limit=10):
    """
    Fetches the latest stored Fear & Greed Index data.
    """
    conn = get_db_connection()
    cur = conn.cursor()

    cur.execute(f"""
        SELECT date, fear_value, category
        FROM fear_greed_index
        ORDER BY date DESC
        LIMIT {limit};
    """)

    rows = cur.fetchall()
    fear_greed_data = [
        {
            "Date": row[0],
            "Fear Value": row[1],
            "Category": row[2],
        }
        for row in rows
    ]

    cur.close()
    conn.close()
    return fear_greed_data

# --------------------- MARKET HOLIDAYS DATABASE FUNCTIONS ---------------------

def store_market_holidays(holidays_data):
    """
    Stores market holidays data in the PostgreSQL database.
    
    :param holidays_data: List of dictionaries containing holiday information
    :return: True if successful, False otherwise
    """
    if not holidays_data:
        logger.info("No market holidays data to store.")
        return False

    try:
        conn = get_db_connection()
        cur = conn.cursor()

        # Create the table if it doesn't exist
        cur.execute("""
            CREATE TABLE IF NOT EXISTS market_holidays (
                id SERIAL PRIMARY KEY,
                name TEXT NOT NULL,
                date DATE NOT NULL,
                status TEXT NOT NULL,
                exchange TEXT NOT NULL,
                year INTEGER NOT NULL,
                created_at TIMESTAMP DEFAULT NOW(),
                UNIQUE (name, date, exchange)
            )
        """)
        conn.commit()

        # Insert or update the holiday data
        for holiday in holidays_data:
            try:
                # Parse date string to proper format
                from datetime import datetime
                holiday_date = datetime.strptime(holiday["date"], "%Y-%m-%d").date()
                
                cur.execute("""
                    INSERT INTO market_holidays (name, date, status, exchange, year)
                    VALUES (%s, %s, %s, %s, %s)
                    ON CONFLICT (name, date, exchange) 
                    DO UPDATE SET
                        status = EXCLUDED.status,
                        year = EXCLUDED.year
                """, (
                    holiday["name"],
                    holiday_date,
                    holiday["status"],
                    holiday["exchange"],
                    holiday["year"]
                ))
                conn.commit()
            except Exception as e:
                logger.error(f"Error storing holiday {holiday['name']}: {e}")
                conn.rollback()

        logger.info(f"Successfully stored {len(holidays_data)} market holidays in the database.")
        cur.close()
        conn.close()
        return True

    except Exception as e:
        logger.error(f"Database error (Market Holidays): {e}")
        return False

def get_latest_market_holidays():
    """
    Fetches the latest market holidays from the database.
    """
    try:
        conn = get_db_connection()
        cur = conn.cursor()

        cur.execute("""
            SELECT name, date, status, exchange, year
            FROM market_holidays
            WHERE date >= CURRENT_DATE
            ORDER BY date ASC
            LIMIT 10;
        """)

        rows = cur.fetchall()
        holidays_data = [
            {
                "name": row[0],
                "date": row[1].strftime("%Y-%m-%d"),
                "status": row[2],
                "exchange": row[3],
                "year": row[4]
            }
            for row in rows
        ]

        cur.close()
        conn.close()
        return holidays_data
    
    except Exception as e:
        logger.error(f"Error fetching market holidays: {e}")
        return []

# --------------------- TOP STOCKS DATABASE FUNCTIONS ---------------------

def create_top_stocks_table():
    """
    Creates the top_stocks table if it doesn't exist.
    """
    try:
        conn = get_db_connection()
        cur = conn.cursor()

        cur.execute("""
            CREATE TABLE IF NOT EXISTS top_stocks (
                id SERIAL PRIMARY KEY,
                category VARCHAR(50),  -- 'after_hours' or 'premarket'
                ticker VARCHAR(10),
                rank INTEGER,  -- Rank of the stock (1-5)
                date DATE,     -- Date of the data
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        conn.commit()
        logger.info("Top stocks table created or already exists.")
    except Exception as e:
        logger.error(f"Error creating top_stocks table: {e}")
    finally:
        if 'conn' in locals():
            conn.close()

def execute_query(query, params=None):
    """
    Helper function to execute a database query.
    Args:
        query (str): SQL query to execute
        params (tuple, optional): Query parameters
    """
    conn = get_db_connection()
    cur = conn.cursor()
    try:
        if params:
            cur.execute(query, params)
        else:
            cur.execute(query)
        conn.commit()
    except Exception as e:
        conn.rollback()
        raise e
    finally:
        cur.close()
        conn.close()

def store_top_stocks(category, stocks_data):
    """
    Stores top stocks data in the database.
    Args:
        category (str): Category of stocks ('after_hours' or 'premarket')
        stocks_data (list): List of dictionaries containing ticker and rank
    """
    try:
        conn = get_db_connection()
        cur = conn.cursor()

        cur.execute("""
            DELETE FROM top_stocks 
            WHERE category = %s AND date = CURRENT_DATE
        """, (category,))
        
        for stock in stocks_data:
            cur.execute("""
                INSERT INTO top_stocks (category, ticker, rank, date)
                VALUES (%s, %s, %s, CURRENT_DATE)
            """, (category, stock['ticker'], stock['rank']))
            
        conn.commit()
        logger.info(f"Successfully stored {len(stocks_data)} top stocks for {category}")
        
    except Exception as e:
        logger.error(f"Error storing top stocks: {e}")
        raise
    finally:
        if 'conn' in locals():
            conn.close()

def get_latest_top_stocks(category=None, limit=5):
    """
    Retrieves the latest top stocks from the database.
    """
    try:
        conn = get_db_connection()
        cur = conn.cursor()

        query = """
            SELECT category, ticker, rank, date, created_at
            FROM top_stocks
            WHERE date = CURRENT_DATE
        """
        params = []
        
        if category:
            query += " AND category = %s"
            params.append(category)
            
        query += " ORDER BY rank LIMIT %s"
        params.append(limit)

        cur.execute(query, params)
        results = cur.fetchall()

        return [{
            'category': row[0],
            'ticker': row[1],
            'rank': row[2],
            'date': row[3],
            'created_at': row[4]
        } for row in results]
    
    except Exception as e:
        logger.error(f"Error fetching top stocks: {e}")
        return []
    
    finally:
        if 'conn' in locals():
            conn.close()

