from pydantic_settings import BaseSettings
from typing import List

class Settings(BaseSettings):
    """
    Application settings loaded from environment variables.
    """
    # API Settings
    API_VERSION: str = "1.0.0"
    API_PREFIX: str = "/api/v1"
    
    # CORS Settings
    CORS_ORIGINS: List[str] = ["*"]
    
    # Database Settings
    DB_URL: str
    
    # Scheduler Settings
    ECONOMIC_DATA_HOUR: int = 12
    ECONOMIC_DATA_MINUTE: int = 35
    FEAR_INDEX_INTERVAL: str = "*"
    EARNINGS_HOUR: int = 4
    EARNINGS_MINUTE: int = 0
    NEXT_WEEK_EARNINGS_DAY: str = "mon"
    NEXT_WEEK_EARNINGS_HOUR: int = 12
    NEXT_WEEK_EARNINGS_MINUTE: int = 0
    MARKET_HOLIDAYS_DAY: str = "sun"
    MARKET_HOLIDAYS_HOUR: int = 18
    MARKET_HOLIDAYS_MINUTE: int = 0
    
    class Config:
        env_file = ".env" 