import redis.asyncio as redis
import os

# REDIS_URL = os.getenv("REDIS_URL", "redis")


# if REDIS_URL.startswith("redis://"):
#     redis_client= redis.from_url(REDIS_URL, decode_responses=True, socket_connect_timeout=2)
# else: 
#     redis_client = redis.Redis(host=REDIS_URL, port=6379, db=0, decode_responses=True, socket_connect_timeout=2)
    
# REDIS_URL = os.getenv("REDIS_URL", "localhost") # Для Windows лучше localhost

# # Создаем объект без автоматического открытия соединения
# redis_client = redis.from_url(
#     f"redis://{REDIS_URL}:6379" if not REDIS_URL.startswith("redis://") else REDIS_URL,
#     decode_responses=True,
#     auto_close_connection_pool=False # Важно для тестов
# )


def get_redis_client():
    REDIS_URL = os.getenv("REDIS_URL", "localhost")
    return redis.from_url(
        f"redis://{REDIS_URL}:6379" if not REDIS_URL.startswith("redis://") else REDIS_URL,
        decode_responses=True,socket_timeout=5,
        socket_connect_timeout=5
    )

# Оставляем переменную для совместимости, но не инициализируем её сразу активным соединением
redis_client = get_redis_client()

# def get_redis():
#     return redis_client