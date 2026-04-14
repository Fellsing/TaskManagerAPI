from sqlalchemy.ext.asyncio import AsyncSession
from models.models import TaskDB
from datetime import datetime, timezone


async def add_new_task(
    db: AsyncSession,
    title: str,
    description: str,
    user_id: int,
    deadline: datetime = None,
):
    db_note = TaskDB(
        title=title,
        description=description,
        deadline=deadline,
        status=False,
        owner_id=user_id,
        creation_date=datetime.now(timezone.utc).replace(tzinfo=None),
        notification_sent=False,
    )
    db.add(db_note)
    await db.commit()
    await db.refresh(db_note)
    return db_note
