from fastapi import APIRouter, HTTPException, status
from schemas.statistics import StatisticsRequest, StatisticsRespond
from services.statistics import save_statistics, get_statistics

router = APIRouter(
    prefix="/statistics",
    tags=["Statistics"],
    responses={404: {"description": "Not found"}},
)


@router.post("/", status_code=status.HTTP_201_CREATED)
async def create_statistics(statistics_entry: StatisticsRequest):
    success = await save_statistics(statistics_entry)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to save statistics",
        )
    return {"message": "Statistics saved successfully"}


@router.get("/{user_id}", response_model=StatisticsRespond)
async def read_statistics(user_id: str):
    stats = await get_statistics(user_id)
    if not stats:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No statistics found for the user",
        )
    return stats
