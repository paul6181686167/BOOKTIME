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
from app.database import get_database
from app.security.auth import create_access_token

# Configuration base de données de test
TEST_DATABASE_URL = "mongodb://localhost:27017/booktime_test"

@pytest.fixture(scope="session")
def event_loop():
    """Créer un event loop pour les tests async"""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()

@pytest.fixture(scope="session")
async def test_database():
    """Fixture pour la base de données de test"""
    client = AsyncIOMotorClient(TEST_DATABASE_URL)
    database = client.booktime_test
    
    # Nettoyer avant les tests
    await database.drop_collection("users")
    await database.drop_collection("books")
    await database.drop_collection("user_profiles")
    await database.drop_collection("social_activities")
    await database.drop_collection("follows")
    await database.drop_collection("social_notifications")
    
    yield database
    
    # Nettoyer après les tests
    await database.drop_collection("users")
    await database.drop_collection("books")
    await database.drop_collection("user_profiles")
    await database.drop_collection("social_activities")
    await database.drop_collection("follows")
    await database.drop_collection("social_notifications")
    
    client.close()

@pytest.fixture
async def test_client(test_database):
    """Client HTTP pour les tests"""
    # Override de la base de données pour les tests
    def override_get_database():
        return test_database
    
    app.dependency_overrides[get_database] = override_get_database
    
    async with AsyncClient(app=app, base_url="http://test") as client:
        yield client
    
    # Nettoyer les overrides
    app.dependency_overrides.clear()

@pytest.fixture
async def test_user(test_database):
    """Créer un utilisateur de test"""
    user_data = {
        "id": "test-user-123",
        "first_name": "Test",
        "last_name": "User",
        "created_at": "2024-01-01T00:00:00Z"
    }
    
    await test_database.users.insert_one(user_data)
    return user_data

@pytest.fixture
async def test_token(test_user):
    """Token d'authentification pour les tests"""
    token = create_access_token(data={"sub": test_user["id"]})
    return token

@pytest.fixture
async def auth_headers(test_token):
    """Headers d'authentification pour les tests"""
    return {"Authorization": f"Bearer {test_token}"}

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

@pytest.fixture
async def test_book(test_database, test_user, test_book_data):
    """Créer un livre de test dans la base"""
    book_data = {
        **test_book_data,
        "id": "test-book-123",
        "user_id": test_user["id"],
        "current_page": 0,
        "rating": 0,
        "review": "",
        "cover_url": "",
        "auto_added": False,
        "date_added": "2024-01-01T00:00:00Z",
        "updated_at": "2024-01-01T00:00:00Z"
    }
    
    await test_database.books.insert_one(book_data)
    return book_data

@pytest.fixture
async def multiple_test_books(test_database, test_user):
    """Créer plusieurs livres de test"""
    books_data = [
        {
            "id": f"test-book-{i}",
            "user_id": test_user["id"],
            "title": f"Test Book {i}",
            "author": f"Author {i}",
            "category": ["roman", "bd", "manga"][i % 3],
            "status": ["to_read", "reading", "completed"][i % 3],
            "description": f"Description {i}",
            "total_pages": 200 + i * 50,
            "current_page": 0,
            "rating": 0,
            "review": "",
            "cover_url": "",
            "saga": f"Saga {i}" if i % 2 == 0 else "",
            "volume_number": i + 1 if i % 2 == 0 else None,
            "genre": "Fiction",
            "publication_year": 2020 + i,
            "publisher": f"Publisher {i}",
            "isbn": f"123456789012{i}",
            "auto_added": False,
            "date_added": "2024-01-01T00:00:00Z",
            "updated_at": "2024-01-01T00:00:00Z"
        }
        for i in range(5)
    ]
    
    await test_database.books.insert_many(books_data)
    return books_data