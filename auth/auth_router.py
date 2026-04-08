from typing import Annotated
import uuid
from fastapi import APIRouter, Depends, FastAPI
from fastapi.security import OAuth2PasswordRequestForm
from datetime import datetime, timedelta, timezone
import os
from typing import Annotated
import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from pwdlib import PasswordHash
from pydantic import BaseModel, EmailStr

from sqlalchemy.orm import Session

from database import get_db
from models.models import UserDB
from schemas.users import UserCreate

from core.redis_config import redis_client

from auth.auth_utils import Token, authenticate_user, create_access_token, get_current_user, get_user, SECRET_KEY, ALGORITHM, ACCESS_TOKEN_EXPIRE_MINUTES


router = APIRouter()

@router.post("/auth/signin")
async def login_user(form_data: Annotated[OAuth2PasswordRequestForm, Depends()], db:Annotated[Session, Depends(get_db)])-> Token:
    user = authenticate_user(db,form_data.username, form_data.password)
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Неверное имя пользователя или пароль", headers={"WWW-Authenticate": "Bearer"})
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token({"sub":user.username, "user_id":user.id},access_token_expires)
    return Token(access_token=access_token, token_type="bearer")


@router.post("/auth/signup")
async def create_user(user_data:UserCreate, db: Annotated[Session, Depends(get_db)]):
    user = get_user(db, user_data.username)
    if user:
        raise HTTPException(status_code=400, detail="Пользователь уже существует")
    new_user = UserDB(username = user_data.username, email = user_data.email, hashed_password = PasswordHash.recommended().hash(user_data.password))
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return {"status":f"Пользователь {new_user.username} успешно зарегистрирован!"}



@router.get("/auth/telegram-link")
async def get_tg_link(user: Annotated[UserDB, Depends(get_current_user)]):
    token = str(uuid.uuid4())

    redis_client.set(f"tg_auth:{token}", user.id, ex=1800)

    bot_username = "FellsingTasksBot"
    link = f"https://t.me/{bot_username}?start={token}"

    return {"link":link}