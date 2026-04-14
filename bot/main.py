import asyncio
import logging
import os
import sys
from aiogram.filters import Command, CommandObject
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram import Bot, Dispatcher, types, F
from aiogram.fsm.state import StatesGroup, State
from aiogram.fsm.context import FSMContext
from aiogram_calendar import SimpleCalendar,SimpleCalendarCallback
import aiohttp
from dotenv import load_dotenv
from sqlalchemy import delete, desc, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from core.redis_config import redis_client
from core.http_client import HttpClient
from database import async_session
from models.models import TaskDB, UserDB
from crud import add_new_task


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

class TaskStates(StatesGroup):
    waiting_for_title = State()
    waiting_for_description = State()
    waiting_for_deadline = State()

@dp.callback_query(F.data=="add_task")
async def start_add_task(callback: types.CallbackQuery, state:FSMContext):
    await state.set_state(TaskStates.waiting_for_title)
    await callback.answer()
    await callback.message.answer("Введите заголовок задачи:")

@dp.message(TaskStates.waiting_for_title)
async def process_title(message:types.Message, state: FSMContext):
    await state.update_data(title=message.text)
    await state.set_state(TaskStates.waiting_for_description)
    await message.answer("Теперь введите описание (или отправьте '-' чтобы пропустить):")

@dp.message(TaskStates.waiting_for_description)
async def process_description(message: types.Message, state: FSMContext):
    await state.update_data(description=None if message.text=="-" else message.text)
    await state.set_state(TaskStates.waiting_for_deadline)
    await message.answer("Выберите дату дедлайна:",
        reply_markup=await SimpleCalendar().start_calendar())
    


@dp.callback_query(SimpleCalendarCallback.filter(),TaskStates.waiting_for_deadline)
async def process_deadline(callback: types.CallbackQuery, callback_data: SimpleCalendarCallback, state:FSMContext):
    selected, date = await SimpleCalendar().process_selection(callback, callback_data)
    if selected:
        user_data = await state.get_data()

        async with async_session() as db:
            user = await get_user_by_tg_id(db, callback.from_user.id)
            await add_new_task(db,user_data["title"], user_data["description"], user.id, date)
        await state.clear()
        await callback.message.answer(f"✅ Задача добавлена! Дедлайн: {date.strftime('%d.%m.%Y')}")
        await callback.answer()
        


async def update_user_tg_id(db: AsyncSession, user_id: int, tg_id: int):
    await db.execute(
        update(UserDB).where(UserDB.id == user_id).values(telegram_id=tg_id)
    )
    await db.commit()
    return True


async def get_user_by_tg_id(db: AsyncSession, tg_id: int):
    user = await db.execute(select(UserDB).where(UserDB.telegram_id == tg_id))
    return user.scalar()


async def get_tasks_by_user_id(db: AsyncSession, user_id: int):
    tasks = await db.execute(
        select(TaskDB)
        .where(TaskDB.owner_id == user_id)
        .order_by(desc(TaskDB.creation_date))
    )
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

    async with async_session() as db:
        user = await get_user_by_tg_id(db, message.from_user.id)
        if not user:
            await message.answer(
                "Вначале привяжите телеграм-аккаунт к учетной записи в приложении."
            )
            return
        tasks = await get_tasks_by_user_id(db, user.id)
        if not tasks:
            builder = InlineKeyboardBuilder()
            builder.add(
                types.InlineKeyboardButton(
                    text="➕ Добавить задачу", callback_data="add_task"
                )
            )
            await message.answer("У вас нет задач.", reply_markup=builder.as_markup())
            return

    for task in tasks:
        builder = InlineKeyboardBuilder()
        builder.row(
            types.InlineKeyboardButton(
                text="✅ Готово", callback_data=f"done_{task.id}"
            ),
            types.InlineKeyboardButton(
                text="📝 Изменить", callback_data=f"edit_{task.id}"
            ),
        )
        builder.row(
            types.InlineKeyboardButton(text="🗑 Удалить", callback_data=f"del_{task.id}")
        )

        status = "✅" if task.status else "⏳"
        await message.answer(
            f"{status} **{task.title}**\n{task.description or 'Без описания'}",
            reply_markup=builder.as_markup(),
            parse_mode="Markdown",
        )
    ab_builder = InlineKeyboardBuilder()
    ab_builder.row(
        types.InlineKeyboardButton(text="➕ Добавить задачу", callback_data="add_task")
    )
    await message.answer(
        "Вы можете добавить еще одну задачу:",
        reply_markup=ab_builder.as_markup(),
        parse_mode="Markdown",
    )


@dp.callback_query(F.data.startswith("del_"))
async def delete_task_handler(callback: types.CallbackQuery):
    task_id = int(callback.data.split("_")[1])

    async with async_session() as db:
        await db.execute(delete(TaskDB).where(TaskDB.id == task_id))
        await db.commit()

    await callback.answer("Задача удалена")


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
