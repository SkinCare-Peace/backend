# api/user.py
from typing import List
from fastapi import APIRouter, HTTPException, status, Depends
from schemas.user import UserCreate, UserUpdate, User
from services.user import (
    add_owned_cosmetic,
    create_user,
    get_user_by_id,
    get_user_by_email,
    remove_owned_cosmetic,
    update_user,
    delete_user,
)

router = APIRouter(
    prefix="/users",
    tags=["Users"],
    responses={404: {"description": "Not found"}},
)


@router.post("/", response_model=User, status_code=status.HTTP_201_CREATED)
async def register_user(user_create: UserCreate):
    existing_user = await get_user_by_email(user_create.email)
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered",
        )
    try:
        user = await create_user(user_create)
        return user
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e),
        )


@router.get("/{user_id}", response_model=User)
async def read_user(user_id: str):
    user = await get_user_by_id(user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )
    return user


@router.put("/{user_id}", response_model=User)
async def update_user_info(user_id: str, user_update: UserUpdate):
    user = await update_user(user_id, user_update)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found or no fields updated",
        )
    return user


@router.delete("/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_user_account(user_id: str):
    success = await delete_user(user_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )
    return


@router.get("/email/{email}", response_model=User)
async def read_user_by_email(email: str):
    user = await get_user_by_email(email)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )
    return user


@router.post("/{user_id}/cosmetics/{cosmetic_id}", response_model=User)
async def add_cosmetic_to_user(user_id: str, cosmetic_id: str):
    """
    사용자에게 화장품을 추가합니다.
    """
    user = await add_owned_cosmetic(user_id, cosmetic_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )
    return user


@router.delete("/{user_id}/cosmetics/{cosmetic_id}", response_model=User)
async def remove_cosmetic_from_user(user_id: str, cosmetic_id: str):
    """
    사용자에게서 화장품을 제거합니다.
    """
    user = await remove_owned_cosmetic(user_id, cosmetic_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )
    return user


@router.get("/{user_id}/cosmetics", response_model=List[str])
async def get_user_cosmetics(user_id: str):
    """
    사용자가 보유한 화장품 목록을 가져옵니다.
    """
    user = await get_user_by_id(user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )
    # 사용자 보유 화장품 목록 중복 제거
    if user.owned_cosmetics:
        all_cosmetics = []
        for cosmetics_list in user.owned_cosmetics.values():
            all_cosmetics.extend(cosmetics_list)

        # 중복 제거 후 반환
        result = list(set(all_cosmetics))
    else:
        result = []

    return result


@router.get("/{user_id}/cosmetics/by_type", response_model=dict)
async def get_user_cosmetics_by_type(user_id: str):
    """
    사용자가 보유한 화장품을 종류별로 그룹화하여 가져옵니다.
    """
    user = await get_user_by_id(user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )
    return user.owned_cosmetics
