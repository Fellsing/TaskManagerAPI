import asyncio
import os
import redis.asyncio as redis
from sse_starlette import ServerSentEvent, EventSourceResponse


REDIS_URL = os.getenv("REDIS_URL", "redis://redis:6379/0")
redis_client = redis.from_url(REDIS_URL, decode_responses=True)

async def notification_generator(user_id: int):
    # объект подписки
    pubsub = redis_client.pubsub()
    
    # подписка на канал этого конкретного пользователя
    channel_name = f"user_{user_id}_notifications"
    await pubsub.subscribe(channel_name)
    
    try:
        # прослушка сообщения из Redis в бесконечном цикле
        async for message in pubsub.listen():
            if message["type"] == "message":
                # отправка данных  клиенту
                yield {
                    "event": "new_notification",
                    "data": message["data"]
                }
    except asyncio.CancelledError:
        # отписка, в случае закрытия вкладки
        await pubsub.unsubscribe(channel_name)
        raise