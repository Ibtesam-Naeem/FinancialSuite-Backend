# ------------------------------ IMPORTS ------------------------------
from fastapi import APIRouter, HTTPException
from utils.logger import setup_logger
from utils.db_manager import get_latest_market_holidays

logger = setup_logger("api.market_holidays")
router = APIRouter()

# ------------------------------ ENDPOINTS ------------------------------
@router.get("/market-holidays")
async def get_market_holidays():
    """
    Gets all market holidays.
    """
    try:
        holidays = get_latest_market_holidays()
        return {"status": "success", "data": holidays}

    except Exception as e:
        logger.error(f"Failed to get market holidays: {e}")
        raise HTTPException(status_code=500, detail=str(e)) 

# ------------------------------ END OF FILE ------------------------------