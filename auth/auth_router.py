from typing import Annotated
import uuid
from fastapi import APIRouter, Depends, FastAPI
from fastapi.security import OAuth2PasswordRequestForm
from datetime import datetime, timedelta, timezone
from typing import Annotated
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from pwdlib import PasswordHash
from pydantic import BaseModel, EmailStr

from sqlalchemy.ext.asyncio import AsyncSession
from database import get_db
from models.models import UserDB
from schemas.users import UserCreate

from core.redis_config import redis_client, get_redis_client

from auth.auth_utils import (
    Token,
    authenticate_user,
    create_access_token,
    get_current_user,
    get_user,
    get_user_by_id,
    SECRET_KEY,
    ALGORITHM,
    ACCESS_TOKEN_EXPIRE_MINUTES,
    REFRESH_TOKEN_EXPIRE_DAYS,
    create_refresh_token,
)


router = APIRouter()

async def get_redis():
    client = get_redis_client()
    try:
        yield client
    finally:
        await client.aclose()

class RefreshTokenRequest(BaseModel):
    refresh_token: str

@router.post("/auth/signin")
async def login_user(
    form_data: Annotated[OAuth2PasswordRequestForm, Depends()],
    db: Annotated[AsyncSession, Depends(get_db)],
    redis = Depends(get_redis)
) -> Token:
    user = await authenticate_user(db, form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Неверное имя пользователя или пароль",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        {"sub": user.username, "user_id": user.id}, access_token_expires
    )
    refresh_token = create_refresh_token()
    await redis.set(
        f"refresh_token:{refresh_token}",
        user.id,
        ex=REFRESH_TOKEN_EXPIRE_DAYS * 24 * 3600,
    )
    return Token(
        access_token=access_token, refresh_token=refresh_token, token_type="bearer"
    )


@router.post("/auth/signup")
async def create_user(
    user_data: UserCreate, db: Annotated[AsyncSession, Depends(get_db)]
):
    user = await get_user(db, user_data.username)
    if user:
        raise HTTPException(status_code=400, detail="Пользователь уже существует")
    new_user = UserDB(
        username=user_data.username,
        email=user_data.email,
        hashed_password=PasswordHash.recommended().hash(user_data.password),
    )
    db.add(new_user)
    await db.commit()
    await db.refresh(new_user)
    return {"status": f"Пользователь {new_user.username} успешно зарегистрирован!"}


@router.post("/auth/refresh")
async def refresh_tokens(request_data:RefreshTokenRequest, db: Annotated[AsyncSession, Depends(get_db)]):
    refresh_token = request_data.refresh_token
    user_id = await redis_client.get(f"refresh_token:{refresh_token}")
    if not user_id:
        raise HTTPException(status_code=401, detail="Invalid or expired refresh token")
    await redis_client.delete(f"refresh_token:{refresh_token}")

    user = await get_user_by_id(db,int(user_id))
    new_access_token = create_access_token(data={"sub":user.username})
    new_refresh_token = create_refresh_token()
    await redis_client.set(f"refresh_token:{new_refresh_token}", user_id, ex=REFRESH_TOKEN_EXPIRE_DAYS*24*3600)

    return Token(access_token=new_access_token, refresh_token=new_refresh_token, token_type="bearer")

@router.get("/auth/telegram-link")
async def get_tg_link(user: Annotated[UserDB, Depends(get_current_user)]):
    token = str(uuid.uuid4())

    redis_client.set(f"tg_auth:{token}", user.id, ex=1800)

    bot_username = "FellsingTasksBot"
    link = f"https://t.me/{bot_username}?start={token}"

    return {"link": link}
