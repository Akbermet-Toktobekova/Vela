from fastapi import APIRouter
from typing import List
from models.schemas import MicroLesson
from services.mock_db import db

router = APIRouter(prefix="/api/learning", tags=["Micro-Learning"])

@router.get("/today", response_model=MicroLesson)
async def get_daily_lesson():
    return db.get_daily_lesson()

@router.get("/all", response_model=List[MicroLesson])
async def get_all_lessons():
    return db.get_all_lessons()
