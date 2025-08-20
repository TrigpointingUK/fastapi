"""
TLog endpoints for public access.
"""
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.crud.tlog import get_trig_count
from app.db.database import get_db
from app.schemas.user import TrigCountResponse

router = APIRouter()


@router.get("/trig-count/{trig_id}", response_model=TrigCountResponse)
def get_trig_count_endpoint(
    trig_id: int,
    db: Session = Depends(get_db)
):
    """
    Public endpoint to get count of rows matching trig_id in tlog table.
    
    Args:
        trig_id: The trigger ID to count
        
    Returns:
        TrigCountResponse: Object containing trig_id and count
    """
    count = get_trig_count(db, trig_id=trig_id)
    return TrigCountResponse(trig_id=trig_id, count=count)
