import asyncio
import logging
import os
import sys
from aiogram.filters import Command, CommandObject
from aiogram import Bot, Dispatcher, types
import aiohttp
from dotenv import load_dotenv
from sqlalchemy import desc, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from core.redis_config import redis_client
from core.http_client import HttpClient
from database import async_session
from models.models import TaskDB, UserDB


load_dotenv()
TG_TOKEN = os.getenv("TGBOT_TOKEN")

bot = Bot(token=TG_TOKEN)
dp = Dispatcher()

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)],
)
logger = logging.getLogger(__name__)


async def update_user_tg_id(db:AsyncSession, user_id: int, tg_id: int):
    await db.execute(
        update(UserDB).where(UserDB.id == user_id).values(telegram_id=tg_id)
    )
    await db.commit()
    return True


async def get_user_by_tg_id(db:AsyncSession, tg_id: int):
    user = await db.execute(select(UserDB).where(UserDB.telegram_id == tg_id))
    return user.scalar()


async def get_tasks_by_user_id(db:AsyncSession,user_id: int):
    tasks = await db.execute(select(TaskDB).where(TaskDB.owner_id == user_id).order_by(desc(TaskDB.creation_date)))
    return tasks.scalars().all()


@dp.message(Command("start"))
async def cmd_start(message: types.Message, command: CommandObject):
    user_tg_id = message.from_user.id
    token = command.args
    if await get_user_by_tg_id(user_tg_id):
        await message.answer(
            f"С возвращением, {message.from_user.first_name}! 👋\n"
            "Твой аккаунт уже привязан. Я пришлю уведомление, когда дедлайн будет близко."
        )
        return

    if token:
        user_id = int(redis_client.get(f"tg_auth:{token}"))
        if user_id:
            try:
                await update_user_tg_id(user_id, user_tg_id)
                await message.answer(
                    "✅ Аккаунт привязан! Теперь уведомления будут приходить в этот чат."
                )
                redis_client.delete(f"tg_auth:{token}")
                logger.info(f"User {user_id} linked Telegram account {user_tg_id}")
            except Exception as e:
                logger.error(f"Error linking account: {e}")
                await message.answer(
                    "❌ Произошла ошибка при сохранении. Попробуй позже."
                )
        else:
            await message.answer(
                "❌ Ссылка недействительна или её срок действия (30 мин) истек."
            )
    else:
        await message.answer(
            f"""Привет! Я твой Task Manager бот. 🤖
            Чтобы я мог присылать тебе уведомления о дедлайнах, 
            нажми кнопку 'Привязать Telegram' в своем профиле на сайте."""
        )


@dp.message(Command("cat"))
async def get_random_cat_picture(message: types.Message):
    c_session = await HttpClient.get_session()
    async with c_session.get("https://api.thecatapi.com/v1/images/search") as catpic:
        if catpic.status == 200:
            data = await catpic.json()
            pic_url = data[0]["url"]
            await message.answer_photo(photo=pic_url, caption="Твой китэк! 🐈")
        else:
            await message.answer("Нет китека :с (ошибка внешнего АПИ)")


@dp.message(Command("tasks"))
async def get_user_tasks(message: types.Message):
    c_session = HttpClient.get_session()
    async with async_session() as db:
        user = await get_user_by_tg_id(db,message.from_user.id)
        if not user:
            await message.answer(
                "Вначале привяжите телеграм-аккаунт к учетной записи в приложении."
            )
            return
        tasks = await get_tasks_by_user_id(db, user.id)
        if not tasks:
            await message.answer("У тебя нет задач. Отдыхай :з")
            return

    text = "📋 **Твои задачи:**\n\n"
    for task in tasks:
        status = "✅" if task.status else "⏳"
        text += f"{status}{task.title}. Дедлайн: {task.deadline}\n"
    await message.answer(text, parse_mode="Markdown")


async def on_startup():
    logger.info("HTTP session started correctly.")
    await HttpClient.get_session()


async def on_shutdown():
    logger.info("HTTP session closed correctly.")
    await HttpClient.close_session()


async def main():
    logger.info("TGBot started correctly and working")
    dp.startup.register(on_startup)
    dp.shutdown.register(on_shutdown)
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
