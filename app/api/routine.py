from services.routine import get_routine, get_routine_by_id
from fastapi import APIRouter, HTTPException
from schemas.routine import Routine

router = APIRouter(
    prefix="/routine",
    tags=["Routines"],
    responses={404: {"description": "Not found"}},
)


@router.post("/", response_model=Routine)
async def generate_routine(time_minutes: int, money_won: int):
    try:
        routine = await get_routine(time_minutes, money_won)
        return routine
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception:
        raise HTTPException(status_code=500, detail="Internal Server Error")


@router.get("/{routine_id}", response_model=Routine)
async def get_by_id(routine_id: str):
    routine = await get_routine_by_id(routine_id)
    if routine:
        return routine
    raise HTTPException(status_code=404, detail="Routine not found")
