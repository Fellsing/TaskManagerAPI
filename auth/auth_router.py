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
from models.models import UserDB
from schemas.users import UserCreate

from auth.auth_utils import Token, authenticate_user, create_access_token, get_user


router = APIRouter()
load_dotenv()
SECRET_KEY = os.getenv("SECRET_KEY")
ALGORITHM = os.getenv("ALGORITHM")
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES"))


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