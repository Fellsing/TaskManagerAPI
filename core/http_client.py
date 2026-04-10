import aiohttp
from typing import Optional

class HttpClient:
    session: Optional[aiohttp.ClientSession] = None

    @classmethod
    async def close_session(cls):
        if cls.session:
            await cls.session.close()
            cls.session=None

    @classmethod
    async def get_session(cls):
        if cls.session is None or cls.session.closed:
            cls.session = aiohttp.ClientSession()
        return cls.session