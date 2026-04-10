"""
Configuration pytest pour les tests BOOKTIME
Setup fixtures, client de test, base de données de test
"""
import pytest
import asyncio
import os
from httpx import AsyncClient
from motor.motor_asyncio import AsyncIOMotorClient
from app.main import app

# Configuration base de données de test
TEST_DATABASE_URL = "mongodb://localhost:27017/booktime_test"

@pytest.fixture(scope="session")
def event_loop():
    """Créer un event loop pour les tests async"""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()

@pytest.fixture
async def test_client():
    """Client HTTP pour les tests"""
    async with AsyncClient(app=app, base_url="http://test") as ac:
        yield ac

@pytest.fixture
async def test_user_data():
    """Données d'utilisateur de test"""
    return {
        "first_name": "Test",
        "last_name": "User"
    }

@pytest.fixture
async def test_book_data():
    """Données de livre de test"""
    return {
        "title": "Test Book",
        "author": "Test Author",
        "category": "roman",
        "description": "Description du livre de test",
        "total_pages": 300,
        "status": "to_read",
        "saga": "Test Saga",
        "volume_number": 1,
        "genre": "Fiction",
        "publication_year": 2023,
        "publisher": "Test Publisher",
        "isbn": "1234567890123"
    }