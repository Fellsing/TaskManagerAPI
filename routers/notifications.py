from fastapi import APIRouter, Depends
from sse_starlette.sse import EventSourceResponse
from auth.auth_utils import get_current_user 
from models.models import UserDB
from services.sse_notifications import notification_generator

router = APIRouter(prefix="/notifications", tags=["Notifications"])

@router.get("/stream")
async def stream_notifications(current_user: UserDB = Depends(get_current_user)):
    
    return EventSourceResponse(notification_generator(current_user.id))