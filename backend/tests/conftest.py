"""
Fixtures pytest : client HTTP async (httpx) + utilisateur JWT pour l’API réelle.
"""

from __future__ import annotations

import uuid

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient

from app.main import app


@pytest_asyncio.fixture
async def test_client():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac


@pytest.fixture
def unique_email() -> str:
    return f"pytest_{uuid.uuid4().hex[:16]}@example.com"


@pytest.fixture
def test_password() -> str:
    return "pytestSecret1!"


@pytest_asyncio.fixture
async def registered_user(test_client: AsyncClient, unique_email: str, test_password: str):
    r = await test_client.post(
        "/api/auth/register",
        json={"email": unique_email, "password": test_password},
    )
    assert r.status_code == 200, r.text
    data = r.json()
    assert "access_token" in data
    return {
        "email": unique_email,
        "password": test_password,
        "token": data["access_token"],
        "user": data.get("user") or {},
    }


@pytest_asyncio.fixture
async def auth_headers(registered_user: dict):
    return {"Authorization": f"Bearer {registered_user['token']}"}


@pytest.fixture
def test_book_payload() -> dict:
    return {
        "title": "Livre pytest",
        "author": "Auteur Pytest",
        "category": "roman",
        "description": "Desc",
        "status": "to_read",
        "cover_url": "",
        "saga": "",
        "genre": "",
        "publisher": "",
        "isbn": "",
    }


@pytest_asyncio.fixture
async def test_book(test_client: AsyncClient, auth_headers: dict, test_book_payload: dict):
    r = await test_client.post("/api/books", json=test_book_payload, headers=auth_headers)
    assert r.status_code == 200, r.text
    return r.json()


@pytest_asyncio.fixture
async def multiple_test_books(test_client: AsyncClient, auth_headers: dict):
    created = []
    for i in range(1, 4):
        payload = {
            "title": f"Test Book {i}",
            "author": "Auteur Multi",
            "category": "roman",
            "description": "",
            "status": "to_read",
            "cover_url": "",
            "saga": "",
            "genre": "",
            "publisher": "",
            "isbn": "",
        }
        r = await test_client.post("/api/books", json=payload, headers=auth_headers)
        assert r.status_code == 200, r.text
        created.append(r.json())
    return created
