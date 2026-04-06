from fastapi import FastAPI
from sqlalchemy import engine, MetaData
from auth.auth_router import router as auth_router
from routers.task import router as task_router
from routers.notifications import router as notify_router
from database import engine
from models.models import UserDB

app = FastAPI()
app.include_router(auth_router)
app.include_router(task_router)
app.include_router(notify_router)

@app.get("/")
async def root():
    return {"status":"hello world"}

