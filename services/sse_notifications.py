import asyncio
import os
import redis.asyncio as redis
from sse_starlette import ServerSentEvent, EventSourceResponse


REDIS_URL = os.getenv("REDIS_URL", "redis://redis:6379/0")
redis_client = redis.from_url(REDIS_URL, decode_responses=True)

async def notification_generator(user_id: int):
    # установка статуса онлайна
    online_key = f"user_online: {user_id}"
    await redis_client.set(online_key, "1", ex=180)
    # объект подписки
    pubsub = redis_client.pubsub()
    
    # подписка на канал этого конкретного пользователя
    channel_name = f"user_{user_id}_notifications"
    await pubsub.subscribe(channel_name)
    
    try:
        # прослушка сообщения из Redis в бесконечном цикле
        async for message in pubsub.listen():
            # обновление статуса онлайна
            await redis_client.set(online_key, "1", ex=180)
            if message["type"] == "message":
                # отправка данных  клиенту
                yield {
                    "event": "new_notification",
                    "data": message["data"]
                }
    except asyncio.CancelledError:
        # отписка, в случае закрытия вкладки
        await redis_client.delete(online_key)
        await pubsub.unsubscribe(channel_name)
        raise