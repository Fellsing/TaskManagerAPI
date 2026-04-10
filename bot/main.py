import asyncio
import logging
import os
import sys
from aiogram.filters import Command, CommandObject
from aiogram import Bot, Dispatcher, types
import aiohttp
from dotenv import load_dotenv
from sqlalchemy import select, update

from core.redis_config import redis_client
from core.http_client import HttpClient
from database import session
from models.models import UserDB


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


def update_user_tg_id(user_id: int, tg_id: int):
    with session as db:
        db.execute(update(UserDB).where(UserDB.id == user_id).values(telegram_id=tg_id))
        db.commit()
        return True


def get_user_by_tg_id(tg_id: int):
    with session as db:
        user = db.execute(select(UserDB).where(UserDB.telegram_id == tg_id))
        return user


@dp.message(Command("start"))
async def cmd_start(message: types.Message, command: CommandObject):
    user_tg_id = message.from_user.id
    token = command.args
    if get_user_by_tg_id(user_tg_id):
        await message.answer(
            f"С возвращением, {message.from_user.first_name}! 👋\n"
            "Твой аккаунт уже привязан. Я пришлю уведомление, когда дедлайн будет близко."
        )
        return

    if token:
        user_id = int(redis_client.get(f"tg_auth:{token}"))
        if user_id:
            try:
                update_user_tg_id(user_id, user_tg_id)
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
    c_session = HttpClient.get_session()
    async with session.get("https://api.thecatapi.com/v1/images/search") as catpic:
        if catpic.status == 200:
            data = await catpic.json()
            pic_url = data[0]["url"]
            await message.answer_photo(photo=pic_url, caption="Твой китэк! 🐈")
        else:
            await message.answer("Нет китека :с (ошибка внешнего АПИ)")


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
