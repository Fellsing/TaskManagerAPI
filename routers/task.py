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


from sqlalchemy import desc, select
from sqlalchemy.ext.asyncio import AsyncSession
from database import get_db
from models.models import TaskDB, UserDB
from schemas.tasks import TaskCreate, TaskUpdate
from schemas.users import UserCreate
from crud import add_new_task, update_task_crud, delete_task_crud, get_tasks_crud

from auth.auth_utils import (
    Token,
    TokenData,
    authenticate_user,
    create_access_token,
    get_current_user,
    get_current_user_id,
    get_user,
)


router = APIRouter(tags=["Tasks"], prefix="/task")


@router.post("/add", summary="Добавить задачу")
async def create_task(
    current_user: Annotated[UserDB, Depends(get_current_user)],
    task: TaskCreate,
    db: Annotated[AsyncSession, Depends(get_db)],
):
    db_note = await add_new_task(db=db, owner_id=current_user.id, **task.model_dump())
    return db_note


@router.get("/me")
async def get_tasks(
    db: Annotated[AsyncSession, Depends(get_db)],
    cur_user: Annotated[UserDB, Depends(get_current_user)],
    skip: int = 0,
    limit: int = 10,
):
    res = await get_tasks_crud(db, cur_user.id, skip, limit)
    return res.scalars().all()


@router.get("/me/{task_id}")
async def get_task_by_id(
    db: Annotated[AsyncSession, Depends(get_db)],
    cur_user: Annotated[UserDB, Depends(get_current_user)],
    task_id: int,
):
    query = select(TaskDB).where(TaskDB.owner_id == cur_user.id, TaskDB.id == task_id)
    task = await db.execute(query)
    task_obj = task.scalar_one_or_none()
    if task_obj is None:
        raise HTTPException(status_code=404, detail="Данной записи не существует")
    return task_obj


@router.delete("/delete/{task_id}")
async def delete_task(
    db: Annotated[AsyncSession, Depends(get_db)],
    cur_user: Annotated[UserDB, Depends(get_current_user)],
    task_id: int,
):
    await delete_task_crud(db, task_id, cur_user.id)
    return {"status": f"Запись с ИД {task_id} успешно удалена"}


@router.patch("/update/{task_id}")
async def update_task(
    task_id: int,
    db: Annotated[AsyncSession, Depends(get_db)],
    cur_user: Annotated[UserDB, Depends(get_current_user)],
    task_data: TaskUpdate,
):
    task = await update_task_crud(
        db=db, task_id=task_id, user_id=cur_user.id, **task_data.model_dump()
    )
    return task
