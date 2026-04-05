import pytest
import pytest_asyncio
import jwt
from auth.auth_utils import SECRET_KEY, ALGORITHM
from httpx import AsyncClient

@pytest_asyncio.fixture
async def auth_headers(ac: AsyncClient):
    user_response = await ac.post("/auth/signup", json={"username":"Fell", "email":"fellsing13@gmail.com", "password":"Password123!"})

    user_login_response = await ac.post("/auth/signin", data={"username":"fellsing13@gmail.com", "password":"Password123!"})

    token = user_login_response.json()["access_token"]
    return {"Authorization":f"Bearer {token}"}

@pytest_asyncio.fixture
async def add_task(ac: AsyncClient, auth_headers):
    adding_task = await ac.post("/task/add", json={"title":"strr", "description":"strr descr", "deadline":"2036-04-10T15:00:00"}, headers=auth_headers)
    task_id = adding_task.json()["id"]
    owner_id = adding_task.json()["owner_id"]
    return {"task_id":task_id, "owner_id": owner_id}

@pytest.mark.asyncio
async def test_create_task(ac: AsyncClient):
    user_response = await ac.post("/auth/signup", json={"username":"Fell", "email":"fellsing13@gmail.com", "password":"Password123!"})

    user_login_response = await ac.post("/auth/signin", data={"username":"fellsing13@gmail.com", "password":"Password123!"})
    assert user_login_response.status_code==200

    token = user_login_response.json()["access_token"]
    headers = {"Authorization":f"Bearer {token}"}
    payload = jwt.decode(token, SECRET_KEY, algorithms=ALGORITHM)
    user_id = payload.get("user_id")
    response = await ac.post("/task/add", json={"title":"strr", "description":"strr descr", "deadline":"2036-04-10T15:00:00"}, headers=headers)
    assert response.status_code==200
    assert response.json()["title"]=="strr"
    assert response.json()["owner_id"]==user_id #Данная проверка и в целом декодирование в тесте излишне, применено только в целях демонстрации



@pytest.mark.asyncio
async def test_delete_task(ac: AsyncClient, auth_headers):
    adding_task = await ac.post("/task/add", json={"title":"strr", "description":"strr descr", "deadline":"2036-04-10T15:00:00"}, headers=auth_headers)
    assert adding_task.status_code==200
    assert adding_task.json()["title"]=="strr"

    task_id = adding_task.json()["id"]
    res = await ac.delete(f"/task/delete/{task_id}", headers=auth_headers)

    assert res.status_code==200


@pytest.mark.asyncio
async def test_patch_update_task(ac: AsyncClient, auth_headers):
    adding_task = await ac.post("/task/add", json={"title":"strr", "description":"strr descr", "deadline":"2036-04-10T15:00:00"}, headers=auth_headers)
    assert adding_task.status_code==200
    assert adding_task.json()["title"]=="strr"
    task_id = adding_task.json()["id"]

    response = await ac.patch(f"/task/update/{task_id}", headers=auth_headers, json={"title":"successfully done","description":"strr super insane descr", "deadline":"2056-04-10T15:00:00"})
    assert response.status_code==200
    assert response.json()["title"]=="successfully done"
    assert response.json()["description"]=="strr super insane descr"
    assert response.json()["deadline"]=="2056-04-10T15:00:00"
    


@pytest.mark.asyncio
async def test_get_task_by_id(ac: AsyncClient, auth_headers):
    adding_task = await ac.post("/task/add", json={"title":"strr", "description":"strr descr", "deadline":"2036-04-10T15:00:00"}, headers=auth_headers)
    assert adding_task.status_code==200
    assert adding_task.json()["title"]=="strr"
    task_id = adding_task.json()["id"]
    owner_ID = adding_task.json()["owner_id"]

    response = await ac.get(f"/task/me/{task_id}", headers=auth_headers)
    assert response.status_code==200
    assert response.json()["owner_id"] == owner_ID




@pytest.mark.asyncio
async def test_access_denied (ac: AsyncClient, auth_headers, add_task):
    task_id = add_task["task_id"]
    await ac.post("/auth/signup", json={"username":"hacker", "email":"hacker@gmail.com", "password":"Password123!"})

    user_login_response = await ac.post("/auth/signin", data={"username":"hacker@gmail.com", "password":"Password123!"})

    token = user_login_response.json()["access_token"]
    headers = {"Authorization":f"Bearer {token}"}


    response = await ac.get(f"/task/me/{task_id}", headers=headers)
    assert response.status_code==404