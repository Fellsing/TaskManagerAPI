import asyncio
import logging
import os
import sys
from aiogram.filters import Command, CommandObject
from aiogram import Bot, Dispatcher, types
from dotenv import load_dotenv
from sqlalchemy import update

from core.redis_config import redis_client
from database import session
from models.models import UserDB


load_dotenv()
TG_TOKEN = os.getenv("TGBOT_TOKEN")

bot = Bot(token=TG_TOKEN)
dp = Dispatcher()

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout) 
    ]
)
logger = logging.getLogger(__name__)

def update_user_tg_id(user_id:int, tg_id:int):
    with session as db:
        db.execute(update(UserDB).where(UserDB.id==user_id).values(telegram_id=tg_id))
        db.commit()
        return True

@dp.message(Command("start"))
async def cmd_start(message: types.Message, command: CommandObject):
    token = command.args
    if token:
        user_id = int(redis_client.get(f"tg_auth:{token}"))
        if user_id:
            user_tg_id = message.from_user.id
            try: 
                update_user_tg_id(user_id, user_tg_id)
                await message.answer("✅ Аккаунт привязан! Теперь уведомления будут приходить в этот чат.")
                redis_client.delete(f"tg_auth:{token}")
                logger.info(f"User {user_id} linked Telegram account {user_tg_id}")
            except Exception as e:
                logger.error(f"Error linking account: {e}")
                await message.answer("❌ Произошла ошибка при сохранении. Попробуй позже.")
        else:
            await message.answer("❌ Ссылка недействительна или её срок действия (30 мин) истек.")
    else:
        await message.answer(
            f"""Привет! Я твой Task Manager бот. 🤖
            Чтобы я мог присылать тебе уведомления о дедлайнах, 
            нажми кнопку 'Привязать Telegram' в своем профиле на сайте."""
        )



async def main():
    logger.info("TGBot started correctly and working")
    await dp.start_polling(bot)



if __name__ == "__main__":
    asyncio.run(main())