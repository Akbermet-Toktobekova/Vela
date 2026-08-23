from fastapi import APIRouter
from models.schemas import UserFinancialProfile
from services.mock_db import db

router = APIRouter(prefix="/api/profile", tags=["User Profile"])

@router.get("/{user_id}", response_model=UserFinancialProfile)
async def get_user_profile(user_id: str = "user_default"):
    return db.get_profile(user_id)

@router.post("", response_model=UserFinancialProfile)
async def update_user_profile(profile: UserFinancialProfile):
    return db.update_profile(profile)
