import os
import sys
import time
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from auth.auth_router import router as auth_router
from routers.task import router as task_router
from routers.notifications import router as notify_router
from database import engine
from models.models import UserDB
from exceptions import TaskNotFoundException, PostAppException, NotEnoughPermission
import logging

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)

logger = logging.getLogger(__name__)

app = FastAPI()
app.include_router(auth_router)
app.include_router(task_router)
app.include_router(notify_router)


@app.exception_handler(TaskNotFoundException)
async def task_not_fount_exception_handler(
    request: Request, exc: TaskNotFoundException
):
    return JSONResponse(status_code=404, content={"detail": "Задача не найдена"})


@app.exception_handler(PostAppException)
async def task_not_fount_exception_handler(request: Request, exc: PostAppException):
    return JSONResponse(
        status_code=404,
        content={"detail": "Задача не найдена или у вас нет прав на её удаление"},
    )


@app.exception_handler(NotEnoughPermission)
async def task_not_fount_exception_handler(request: Request, exc: NotEnoughPermission):
    return JSONResponse(
        status_code=404, content={"detail": "У вас нет прав на её удаление"}
    )


# @app.middleware("http")
# async def process_time_header(request: Request, call_next):
#     if os.getenv("TESTING"): 
#         return await call_next(request)
#     start_time = time.perf_counter()
#     response = await call_next(request)
#     process_time = time.perf_counter() - start_time
#     logger.info(f"Path: {request.url.path} | Process time: {process_time:.4f} sec")
#     response.headers["X-Process-Time"] = str(process_time)
#     return response


@app.get("/")
async def root():
    return {"status": "hello world"}
