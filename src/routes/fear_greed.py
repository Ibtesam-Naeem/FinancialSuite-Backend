# ------------------------------ IMPORTS ------------------------------
from fastapi import APIRouter, HTTPException
from utils.logger import setup_logger
from utils.db_manager import get_latest_fear_greed

logger = setup_logger("api.fear_greed")
router = APIRouter()

# ------------------------------ ENDPOINTS ------------------------------
@router.get("/fear-greed")
async def get_fear_greed():
    """
    Gets all fear & greed index data.
    """
    try:
        fear_data = get_latest_fear_greed()
        return {"status": "success", "data": fear_data}

    except Exception as e:
        logger.error(f"Failed to get fear/greed index: {e}")
        raise HTTPException(status_code=500, detail=str(e)) 

# ------------------------------ END OF FILE ------------------------------