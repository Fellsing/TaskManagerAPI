import sys
from sqlalchemy import delete, desc, select
from sqlalchemy.ext.asyncio import AsyncSession
from models.models import TaskDB
from datetime import datetime, timezone
import logging
from exceptions import TaskNotFoundException, NotEnoughPermission


logger = logging.getLogger(__name__)


def normalize_datetime(dt: datetime) -> datetime:
    if dt.tzinfo is not None:
        dt = dt.astimezone(timezone.utc).replace(tzinfo=None)
    return dt


async def add_new_task(
    db: AsyncSession,
    owner_id: int,
    title: str,
    description: str,
    deadline: datetime = None,
):
    db_note = TaskDB(
        title=title,
        description=description,
        deadline=normalize_datetime(deadline),
        status=False,
        owner_id=owner_id,
        creation_date=datetime.now(timezone.utc).replace(tzinfo=None),
        notification_sent=False,
    )
    logger.info(f"User {owner_id} is adding task {db_note.id}.")
    db.add(db_note)
    await db.commit()
    await db.refresh(db_note)
    return db_note


async def update_task_crud(db: AsyncSession, task_id: int, user_id: int, **kwargs):
    res = await db.execute(
        select(TaskDB).where(TaskDB.id == task_id, TaskDB.owner_id == user_id)
    )
    task = res.scalar_one_or_none()
    logger.info(
        f"User {user_id} is updating task {task_id} with fields {list(kwargs.keys())}."
    )
    if task:
        for key, value in kwargs.items():
            if value is not None:
                if isinstance(value, datetime):
                    value = normalize_datetime(value)
                setattr(task, key, value)
        await db.commit()
        await db.refresh(task)
    return task


async def delete_task_crud(db: AsyncSession, task_id: int, user_id: int):
    logger.info(f"User {user_id} is deleting task {task_id}.")
    res = await db.execute(
        delete(TaskDB).where(TaskDB.id == task_id, TaskDB.owner_id == user_id)
    )
    await db.commit()
    if res.rowcount == 0:
        raise TaskNotFoundException
    return True


async def get_tasks_crud(db: AsyncSession, user_id: int, skip:int, limit:int):
    logger.info(f"User {user_id} is checking own tasks with offset {skip} and limit {limit}.")
    res = await db.execute(
        select(TaskDB).where(TaskDB.owner_id == user_id).order_by(desc(TaskDB.deadline)).offset(skip).limit(limit)
    )
    return res
