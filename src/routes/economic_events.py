# ------------------------------ IMPORTS ------------------------------
from fastapi import APIRouter, HTTPException
from utils.logger import setup_logger
from utils.db_manager import get_latest_economic_events

logger = setup_logger("api.economic_events")
router = APIRouter()

# ------------------------------ ENDPOINTS ------------------------------
@router.get("/economic-events")
async def get_economic_events():
    """
    Get all economic events.
    """
    try:
        events = get_latest_economic_events()
        return {"status": "success", "data": events}

    except Exception as e:
        logger.error(f"Failed to get economic events: {e}")
        raise HTTPException(status_code=500, detail=str(e)) 

# ------------------------------ END OF FILE ------------------------------