import os
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from dotenv import load_dotenv


load_dotenv()
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./test.db")
engine = create_async_engine(DATABASE_URL, echo=True)
async_session = async_sessionmaker(bind=engine,class_=AsyncSession, expire_on_commit=False)

async def get_db():
    async with async_session() as db:
        try:
            yield db
        finally:
            await db.close()