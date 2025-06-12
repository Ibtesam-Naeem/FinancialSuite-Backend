# ------------------------------ IMPORTS ------------------------------
from fastapi import APIRouter, HTTPException
from utils.logger import setup_logger
from utils.db_manager import get_latest_earnings, get_latest_next_week_earnings

logger = setup_logger("api.earnings")
router = APIRouter()

# ------------------------------ ENDPOINTS ------------------------------
@router.get("/earnings")
async def get_earnings():
    """
    Get all earnings data for this week.
    """
    try:
        earnings = get_latest_earnings()
        return {"status": "success", "data": earnings}

    except Exception as e:
        logger.error(f"Failed to get earnings: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/next-week-earnings")
async def get_next_week_earnings():
    """
    Get all earnings data for next week.
    """
    try:
        earnings = get_latest_next_week_earnings()
        return {"status": "success", "data": earnings}

    except Exception as e:
        logger.error(f"Failed to get next week earnings: {e}")
        raise HTTPException(status_code=500, detail=str(e)) 

# ------------------------------ END OF FILE ------------------------------