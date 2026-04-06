from datetime import datetime, timedelta, timezone
import smtplib
from email.message import EmailMessage
from typing import Annotated
from celery import Celery
from dotenv import load_dotenv
import os
from fastapi import Depends
import redis
from sqlalchemy import func, select, update
from sqlalchemy.orm import Session

from database import get_db, session
from models.models import TaskDB, UserDB


load_dotenv()
REDIS_URL = os.getenv("REDIS_URL", "redis://redis:6379/0")

celery_app = Celery("tasks", broker=REDIS_URL, backend=REDIS_URL)
redis_broker = redis.Redis(host='redis', port=6379, decode_responses=True)

celery_app.conf.update(
    task_serializer="json",
    result_serializer="json",
    timezone="Asia/Almaty",
    enable_utc=True,
    task_annotations={"tasks.send_uvedomlenie": "100/m"},
)


celery_app.conf.beat_schedule = {"check_every_three_minutes":{"task":"check_deadlines", "schedule": 180.0}}

@celery_app.task(name="send_uvedomlenie")
def send_uved_email(receiver_email: str, title: str):
    SMTP_SERVER = os.getenv("SMTP_SERVER")
    SMTP_PORT = int(os.getenv("SMTP_PORT"))
    SENDER_EMAIL = os.getenv("SENDER_EMAIL")
    SENDER_PASSWORD = os.getenv("SENDER_PASSWORD")

    message = EmailMessage()
    message["Subject"] = title
    message["From"] = SENDER_EMAIL
    message["To"] = receiver_email
    message.set_content(
        f"Привет! Дедлайн у задачи '{title}' наступит уже через час. Поспеши выполнить задачу :)"
    )

    try:
        with smtplib.SMTP_SSL(SMTP_SERVER, SMTP_PORT) as server:
            server.login(SENDER_EMAIL, SENDER_PASSWORD)
            server.send_message(message)
            return f"Емейл успешно отправлен "
    except Exception as e:
        return f"Ошибка при отправке: {e}"


@celery_app.task(name="check_deadlines")
def check_deadlines():

    with session as db:
        cur_time = datetime.now(timezone.utc)
        one_hour_from_ccur = cur_time + timedelta(hours=1)
        query = (
            select(UserDB.id, UserDB.email, TaskDB.title, TaskDB.id)
            .join(UserDB, UserDB.id == TaskDB.owner_id)
            .where(
                TaskDB.notification_sent == False,
                TaskDB.deadline <= one_hour_from_ccur,
                TaskDB.deadline > cur_time,
            )
        )
        
        results = db.execute(query).all()
        for user_id, email, title, task_id in results:
            redis_broker.publish(f"user_{user_id}_notifications", f"Дедлайн по задаче: {title} наступит уже через час!")
            send_uved_email.delay(email, title)
            db.execute(update(TaskDB).where(TaskDB.id==task_id).values(notification_sent=True))
        db.commit()