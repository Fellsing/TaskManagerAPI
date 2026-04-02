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
from sqlalchemy import desc, select

from database import get_db
from models.models import TaskDB, UserDB
from schemas.tasks import TaskCreate, TaskUpdate
from schemas.users import UserCreate

from auth.auth_utils import Token, TokenData, authenticate_user, create_access_token, get_current_user, get_current_user_id, get_user


router = APIRouter(tags=["Tasks"], prefix="/task")


@router.post("/add", summary='Добавить задачу')
async def create_task(current_user: Annotated[UserDB,Depends(get_current_user)], task:TaskCreate, db:Annotated[Session,Depends(get_db)]):
    db_note = TaskDB(**task.model_dump(), status = False, owner_id=current_user.id, creation_date=datetime.now(timezone.utc))
    db.add(db_note)
    db.commit()
    db.refresh(db_note)
    return db_note


@router.get("/me")
async def get_tasks(db: Annotated[Session, Depends(get_db)], cur_user: Annotated[UserDB, Depends(get_current_user)]):
    query = select(TaskDB).where(TaskDB.owner_id==cur_user.id).order_by(desc(TaskDB.deadline))
    res = db.execute(query).scalars().all()
    return res

@router.post("/delete/{task_id}")
async def delete_task(db: Annotated[Session, Depends(get_db)], cur_user: Annotated[UserDB, Depends(get_current_user)], task_id:int):
    query = select(TaskDB).where(TaskDB.owner_id==cur_user.id, TaskDB.id==task_id)
    task = db.execute(query).scalar_one_or_none()
    if task is None:
        raise HTTPException(status_code=400, detail="Данной записи не существует")
    db.delete(task)
    db.commit()
    return {"status":f"Запись с ИД {task_id} успешно удалена"}


@router.patch("/update/{task_id}")
async def update_task(task_id:int,db: Annotated[Session, Depends(get_db)], cur_user: Annotated[UserDB, Depends(get_current_user)], task_data:TaskUpdate ):
    query = select(TaskDB).where(TaskDB.owner_id==cur_user.id, TaskDB.id==task_id)
    task = db.execute(query).scalar_one_or_none()
    if task is None:
        raise HTTPException(status_code=400, detail="Данной записи не существует")
    updated_task_attrs = task_data.model_dump(exclude_unset=True)
    for key,value in updated_task_attrs.items():
        setattr(task, key, value)
    db.commit()
    db.refresh(task)
    return task