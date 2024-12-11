from datetime import date
import traceback
from services.routine import (
    create_routine,
    get_routine_by_id,
    get_routine_records,
    save_routine_record,
)
from services.routine_generate import get_routine
from fastapi import APIRouter, HTTPException, status
from schemas.routine import (
    Routine,
    RoutineCreateRequest,
    RoutineRecord,
    RoutineRecordRequest,
)
from services.user import get_user_by_id

router = APIRouter(
    prefix="/routine",
    tags=["Routines"],
    responses={404: {"description": "Not found"}},
)


@router.post("/record")
async def add_routine_record(record: RoutineRecordRequest):
    success = await save_routine_record(
        record.user_id, record.date, record.usage_time, record.routine_practice
    )
    if not success:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to save routine record",
        )
    return {"message": "Routine record added successfully"}


@router.get("/record/{user_id}", response_model=RoutineRecord)
async def read_routine_records(user_id: str):
    record = await get_routine_records(user_id)
    if not record:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No routine records found for the user",
        )
    return record


@router.post("/", response_model=Routine)
async def generate_routine(request: RoutineCreateRequest):
    try:
        time_minutes = request.time_minutes
        money_won = request.money_won
        owned_cosmetics = request.owned_cosmetics
        routine_create = await get_routine(time_minutes, money_won, owned_cosmetics)
        routine = await create_routine(routine_create)
        return routine
    except ValueError as e:
        traceback.print_exc()
        raise HTTPException(status_code=400, detail=str(e))
    except Exception:
        raise HTTPException(status_code=500, detail="Internal Server Error")


@router.get("/{routine_id}", response_model=Routine)
async def get_by_id(routine_id: str):
    routine = await get_routine_by_id(routine_id)
    if routine:
        return routine
    raise HTTPException(status_code=404, detail="Routine not found")


@router.get("/user/{user_id}", response_model=Routine)
async def get_routine_by_user_id(user_id: str):
    user = await get_user_by_id(user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    routine_id = user.routine_id
    if not routine_id:
        raise HTTPException(status_code=404, detail="Routine not exist for the user")
    routine = await get_routine_by_id(routine_id)
    if routine:
        return routine
    raise HTTPException(status_code=404, detail="Routine not found")
