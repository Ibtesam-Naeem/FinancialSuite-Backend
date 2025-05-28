# Market Dashboard Backend for Stockpedia.ca and other projects of mine!

A simple API that collects and serves financial market data. It scrapes data from various sources and utilizes apis to provide it through REST endpoints.

## What it does

- Tracks upcoming earnings reports
- Monitors important economic events
- Checks the market fear & greed index
- Provides market holiday information

## API Endpoints

The API is live at: https://sea-turtle-app-hbqlx.ondigitalocean.app/

- `/earnings` - Get upcoming earnings reports
- `/economic-events` - Get economic calendar events
- `/fear-greed` - Get current market sentiment
- `/market-holidays` - Get upcoming market holidays
- `/trigger-scrapers` - Manually run all data scrapers

## Tech Stack

- FastAPI for the API
- Playwright for web scraping
- Selenium for fallback 
- PostgreSQL for data storage
- Deployed on Digital Ocean

That's it! Just a simple service that keeps track of market data.