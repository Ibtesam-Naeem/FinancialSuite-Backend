import os
import psycopg2
from psycopg2.extras import execute_values
from dotenv import load_dotenv
from utils.logger import setup_logging

logging = setup_logging("DB Logger")

load_dotenv()
DB_URL = os.getenv("DB_URL")


def get_db_connection():
    """Establishes a connection to the PostgreSQL database."""
    return psycopg2.connect(DB_URL)

# --------------------- EARNINGS REPORT DATABASE FUNCTIONS ---------------------

def store_earnings_data(data):
    """
    Stores earnings data in the PostgreSQL database.
    Prevents duplicates and updates existing records.
    """
    if not data:
        logging.info("No earnings data to store.")
        return

    try:
        conn = get_db_connection()
        cur = conn.cursor()

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
        logging.info(f"Successfully stored {len(data)} earnings reports in the database.")

    except Exception as e:
        logging.error(f"Database error (Earnings Reports): {e}")
    
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
        logging.info("No economic data to store.")
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
        logging.info(f"Successfully stored {len(economic_data)} economic events in the database.")

    except Exception as e:
        logging.error(f"Database error (Economic Events): {e}")
    
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

def store_premarket_data(data):
    """
    Stores pre-market movers data in the PostgreSQL database.
    """
    if not data or not (data.get("gainers") or data.get("losers")):
        logging.info("No pre-market data to store.")
        return

    try:
        conn = get_db_connection()
        cur = conn.cursor()

        # Create table if it doesn't exist
        cur.execute("""
            CREATE TABLE IF NOT EXISTS premarket_movers (
                id SERIAL PRIMARY KEY,
                symbol TEXT NOT NULL,
                price NUMERIC,
                change NUMERIC,
                change_percent NUMERIC,
                volume BIGINT,
                is_gainer BOOLEAN,
                timestamp DATE NOT NULL,
                created_at TIMESTAMP DEFAULT NOW(),
                UNIQUE (symbol, timestamp)
            )
        """)
        conn.commit()

        # Prepare data for insertion
        insert_query = """
            INSERT INTO premarket_movers 
            (symbol, price, change, change_percent, volume, is_gainer, timestamp)
            VALUES %s
            ON CONFLICT (symbol, timestamp) DO UPDATE SET
                price = EXCLUDED.price,
                change = EXCLUDED.change,
                change_percent = EXCLUDED.change_percent,
                volume = EXCLUDED.volume,
                is_gainer = EXCLUDED.is_gainer;
        """

        # Process gainers and losers
        movers_data = []
        for gainer in data.get("gainers", []):
            movers_data.append((
                gainer["symbol"],
                gainer["price"],
                gainer["change"],
                gainer["change_percent"],
                gainer["volume"],
                True,
                gainer["timestamp"]
            ))
        
        for loser in data.get("losers", []):
            movers_data.append((
                loser["symbol"],
                loser["price"],
                loser["change"],
                loser["change_percent"],
                loser["volume"],
                False,
                loser["timestamp"]
            ))

        execute_values(cur, insert_query, movers_data)
        conn.commit()
        logging.info(f"Successfully stored {len(movers_data)} pre-market movers in the database.")

    except Exception as e:
        logging.error(f"Database error (Pre-market Movers): {e}")
    
    finally:
        cur.close()
        conn.close()

def get_latest_premarket_movers(limit=20):
    """
    Fetches the latest pre-market movers from the database.
    Returns gainers and losers for the most recent date.
    """
    conn = get_db_connection()
    cur = conn.cursor()

    cur.execute("""
        WITH latest_date AS (
            SELECT MAX(timestamp) as max_date 
            FROM premarket_movers
        )
        SELECT symbol, price, change, change_percent, volume, is_gainer, timestamp
        FROM premarket_movers, latest_date
        WHERE timestamp = latest_date.max_date
        ORDER BY change_percent DESC;
    """)

    rows = cur.fetchall()
    
    gainers = []
    losers = []
    
    for row in rows:
        mover_data = {
            "symbol": row[0],
            "price": float(row[1]),
            "change": float(row[2]),
            "change_percent": float(row[3]),
            "volume": row[4],
            "timestamp": row[6]
        }
        
        if row[5]:  # is_gainer
            gainers.append(mover_data)
        else:
            losers.append(mover_data)

    cur.close()
    conn.close()
    
    return {
        "gainers": gainers[:limit],
        "losers": losers[-limit:]
    }

