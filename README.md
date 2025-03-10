```python:marketdashboard/README.md
# Market Dashboard Data Service

A Python-based market data service that scrapes and serves financial market data including earnings reports, economic events, market sentiment, and pre-market movers.

## Features

- **Earnings Calendar**: Scrapes upcoming earnings reports from TradingView

- **Economic Events**: Collects high-importance economic events from TradingView's USDCAD calendar

- **Fear & Greed Index**: Tracks market sentiment from CNN's Fear & Greed Index

- **Pre-market Movers**: Fetches pre-market gainers and losers 
from Polygon.io

- **REST API**: Serves collected data through FastAPI endpoints

## Installation

1. Clone the repository:
```bash
git clone [your-repo-url]
cd market-data-service
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Set up environment variables:
```bash
# Create .env file
touch .env

# Add required variables
POLYGON_API_KEY=your_polygon_api_key
DB_URL=your_postgres_database_url
CHROME_BINARY_PATH=/path/to/chrome  
CHROMEDRIVER_PATH=/path/to/chromedriver  
```

## Usage

### Running the Service

Run both scrapers and API:
```bash
python -m marketdashboard.main --mode both
```

Run only scrapers:
```bash
python -m marketdashboard.main --mode scraper
```

Run only API:
```bash
python -m marketdashboard.main --mode api
```

### API Endpoints

- `GET /earnings`: Latest earnings reports
- `GET /economic-events`: High-importance economic events
- `GET /fear-greed`: Current Fear & Greed Index
- `GET /premarket`: Pre-market gainers and losers

Access API documentation at: `http://localhost:8000/docs`

## Project Structure

```
marketdashboard/
├── api/
│   └── main.py
├── scrapers/
│   ├── earnings_scraper.py
│   ├── econ_scraper.py
│   ├── fear_sentiment.py
│   └── premarket_movers.py
├── utils/
│   ├── chrome_options.py
│   ├── db_manager.py
│   └── logger.py
└── main.py
```

## Dependencies

- FastAPI: Web framework for API
- Selenium: Web scraping
- psycopg2: PostgreSQL database connection
- requests: HTTP requests for APIs
- python-dotenv: Environment variable management

## Database Schema

The service uses PostgreSQL with the following tables:
- `earnings_reports`: Upcoming company earnings
- `economic_events`: Economic calendar events
- `fear_greed_index`: Market sentiment data
- `premarket_movers`: Pre-market trading activity

## Notes

- Pre-market data is only available during market pre-market hours (4:00 AM - 9:30 AM ET)
- Requires Chrome and ChromeDriver for web scraping
- Designed to run as a data service for other applications
```

You can create this file by running:
```bash
touch marketdashboard/README.md
```
