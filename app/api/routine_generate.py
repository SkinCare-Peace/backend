from services.routine_generate import get_routine
from fastapi import APIRouter, HTTPException
from schemas.routine_generate import Routine

router = APIRouter()


@router.get("/routine", response_model=Routine)
async def generate_routine(time_minutes: int, money_won: int):
    try:
        routine = get_routine(time_minutes, money_won)
        return routine
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception:
        raise HTTPException(status_code=500, detail="Internal Server Error")
