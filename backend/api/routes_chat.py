from fastapi import APIRouter
from models.schemas import ChatRequest, ChatResponse
from agents.coordinator import coordinator
from services.mock_db import db

router = APIRouter(prefix="/api/chat", tags=["Chat"])

@router.post("", response_model=ChatResponse)
async def send_chat_message(request: ChatRequest):
    profile = db.get_profile(request.user_id)
    response = coordinator.route_and_respond(request, profile)
    return response
