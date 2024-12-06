from datetime import date
from services.routine import (
    get_routine,
    get_routine_by_id,
    get_routine_records,
    save_routine_record,
)
from fastapi import APIRouter, HTTPException, status
from schemas.routine import Routine, RoutineRecord

router = APIRouter(
    prefix="/routine",
    tags=["Routines"],
    responses={404: {"description": "Not found"}},
)


@router.post("/{user_id}")
async def add_routine_record(user_id: str, date: date):
    success = await save_routine_record(user_id, date)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to save routine record",
        )
    return {"message": "Routine record added successfully"}


@router.get("/{user_id}", response_model=RoutineRecord)
async def read_routine_records(user_id: str):
    record = await get_routine_records(user_id)
    if not record:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No routine records found for the user",
        )
    return record


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
