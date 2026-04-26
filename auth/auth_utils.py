from datetime import datetime, timedelta, timezone
import os
from typing import Annotated
import uuid
import jwt
from fastapi import Depends, HTTPException, Response, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from pwdlib import PasswordHash
from dotenv import load_dotenv
from pydantic import BaseModel, EmailStr

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from database import get_db
from models.models import UserDB
import logging

logger = logging.getLogger(__name__)
load_dotenv()

SECRET_KEY = os.getenv("SECRET_KEY", "insanely-giga-secre-key-monster")
ALGORITHM = os.getenv("ALGORITHM", "HS256")
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", 30))
REFRESH_TOKEN_EXPIRE_DAYS = int(os.getenv("REFRESH_TOKEN_EXPIRE_DAYS", 30))

class Token(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str



class TokenData(BaseModel):
    username: str | None = None


class User(BaseModel):
    username: str
    email: EmailStr | None = None


class UserInDb(User):
    hashed_password: str


password_hash = PasswordHash.recommended()
DUMMY_HASH = password_hash.hash("dummypassword")


def verify_password(plain_password, hashed_password):
    return password_hash.verify(plain_password, hashed_password)


def get_password_hash(password):
    return password_hash.hash(password)


async def authenticate_user(db: AsyncSession, username: str, password: str):
    user = await get_user(db=db, username=username)
    if not user:
        verify_password(password, DUMMY_HASH)
        return False
    if not verify_password(password, user.hashed_password):
        return False
    return user


async def get_user(db: AsyncSession, username: str):
    user = await db.execute(
        select(UserDB).where((UserDB.username == username) | (UserDB.email == username))
    )
    res = user.scalar_one_or_none()
    return res

async def get_user_by_id(db: AsyncSession, user_id: int):
    user = await db.execute(
        select(UserDB).where(UserDB.id == user_id)
    )
    res = user.scalar_one_or_none()
    return res

def create_access_token(data: dict, expires_delta: timedelta | None = None):
    data_copy = data.copy()
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=15)

    data_copy.update({"exp": expire})
    encoded_jwt = jwt.encode(data_copy, SECRET_KEY, ALGORITHM)
    return encoded_jwt

def create_refresh_token():
    return str(uuid.uuid4())

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/signin")


async def get_current_user(
        response: Response,
    token: Annotated[str, Depends(oauth2_scheme)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Couldnt validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, ALGORITHM)
        username = payload.get("sub")
        exp = payload.get("exp")
        if username is None:
            raise credentials_exception
        token_data = TokenData(username=username)
        if exp:
            cur_time = datetime.now(timezone.utc).timestamp()
            remaining_time = exp -cur_time
            if 0<remaining_time <=60:
                response.headers["X-Refresh_Suggested"] = "true"
                response.headers["Access-Control-Expose-Headers"] = "X-Refresh-Suggested"
                logger.info(f"Token for user {username} expires in {int(remaining_time)}s. Suggesting refresh.")
    except jwt.InvalidTokenError:
        raise credentials_exception
    user = await get_user(db, username)
    if user is None:
        raise credentials_exception
    return user


# спец функция для оптимизации запросов к БД. функция не обращается к БД, работает только с токеном, что является выгодным, но малоприменимым вариантом :)
async def get_current_user_id(token: Annotated[str, Depends(oauth2_scheme)]):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Couldnt validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, ALGORITHM)
        user_id = payload.get("user_id")
        if user_id is None:
            raise credentials_exception
    except jwt.InvalidTokenError:
        raise credentials_exception
    return user_id
