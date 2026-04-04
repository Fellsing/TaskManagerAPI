import pytest
import pytest_asyncio
import jwt
from auth.auth_utils import SECRET_KEY, ALGORITHM
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_create_task(ac: AsyncClient):
    user_response = await ac.post("/auth/signup", json={"username":"Fell", "email":"fellsing13@gmail.com", "password":"Password123!"})
    assert user_response.status_code==200

    user_login_response = await ac.post("/auth/signin", data={"username":"fellsing13@gmail.com", "password":"Password123!"})
    assert user_login_response.status_code==200

    token = user_login_response.json()["access_token"]
    headers = {"Authorization":f"Bearer {token}"}
    payload = jwt.decode(token, SECRET_KEY, algorithms=ALGORITHM)
    user_id = payload.get("user_id")
    response = await ac.post("/task/add", json={"title":"strr", "description":"strr descr", "deadline":"2036-04-10T15:00:00"}, headers=headers)
    assert response.status_code==200
    assert response.json()["title"]=="strr"
    assert response.json()["owner_id"]==user_id
