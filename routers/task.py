import fastapi
from typing import Annotated
from fastapi import APIRouter, Depends, FastAPI
from fastapi.security import OAuth2PasswordRequestForm
from datetime import datetime, timedelta, timezone
import os
from typing import Annotated
import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from pwdlib import PasswordHash
from dotenv import load_dotenv
from pydantic import BaseModel, EmailStr

from sqlalchemy.orm import Session

from database import get_db
from models.models import TaskDB, UserDB
from schemas.tasks import TaskCreate
from schemas.users import UserCreate

from auth.auth_utils import Token, authenticate_user, create_access_token, get_current_user, get_user


router = APIRouter()


@router.post("/task/add")
async def create_task(current_user: Annotated[UserDB,Depends(get_current_user)], task:TaskCreate, db:Annotated[Session,Depends(get_db)]):
    if not current_user:
        raise HTTPException(status_code=401, detail="Вы не авторизованы")
    db_note = TaskDB(title = task.title, description = task.description, deadline=task.deadline, status = False, owner_id=current_user.id)
    db.add(db_note)
    db.commit()
    db.refresh(db_note)
    return db_note