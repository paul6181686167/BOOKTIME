"""
Tests pour la gestion des livres BOOKTIME
Tests CRUD complets pour les livres
"""
import pytest
from httpx import AsyncClient

class TestBooks:
    """Tests pour les endpoints de gestion des livres"""
    
    @pytest.mark.asyncio
    async def test_get_books_empty(self, test_client: AsyncClient, auth_headers: dict):
        """Test récupération livres vides"""
        response = await test_client.get("/api/books", headers=auth_headers)
        
        assert response.status_code == 200
        data = response.json()
        assert data == []
    
    @pytest.mark.asyncio
    async def test_add_book_success(self, test_client: AsyncClient, auth_headers: dict, test_book_data: dict):
        """Test ajout livre réussi"""
        response = await test_client.post("/api/books", json=test_book_data, headers=auth_headers)
        
        assert response.status_code == 201
        data = response.json()
        assert data["title"] == test_book_data["title"]
        assert data["author"] == test_book_data["author"]
        assert data["category"] == test_book_data["category"]
        assert "id" in data
        assert "date_added" in data
    
    @pytest.mark.asyncio
    async def test_add_book_invalid_data(self, test_client: AsyncClient, auth_headers: dict):
        """Test ajout livre avec données invalides"""
        invalid_data = {
            "title": "",  # Titre vide
            "author": "Test Author",
            "category": "invalid_category"  # Catégorie invalide
        }
        
        response = await test_client.post("/api/books", json=invalid_data, headers=auth_headers)
        
        assert response.status_code == 422
    
    @pytest.mark.asyncio
    async def test_get_books_with_data(self, test_client: AsyncClient, auth_headers: dict, multiple_test_books: list):
        """Test récupération livres avec données"""
        response = await test_client.get("/api/books", headers=auth_headers)
        
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 5
        assert all("id" in book for book in data)
        assert all("title" in book for book in data)
    
    @pytest.mark.asyncio
    async def test_get_books_by_category(self, test_client: AsyncClient, auth_headers: dict, multiple_test_books: list):
        """Test récupération livres par catégorie"""
        response = await test_client.get("/api/books?category=roman", headers=auth_headers)
        
        assert response.status_code == 200
        data = response.json()
        assert all(book["category"] == "roman" for book in data)
    
    @pytest.mark.asyncio
    async def test_get_books_by_status(self, test_client: AsyncClient, auth_headers: dict, multiple_test_books: list):
        """Test récupération livres par statut"""
        response = await test_client.get("/api/books?status=reading", headers=auth_headers)
        
        assert response.status_code == 200
        data = response.json()
        assert all(book["status"] == "reading" for book in data)
    
    @pytest.mark.asyncio
    async def test_get_book_by_id(self, test_client: AsyncClient, auth_headers: dict, test_book: dict):
        """Test récupération livre par ID"""
        book_id = test_book["id"]
        response = await test_client.get(f"/api/books/{book_id}", headers=auth_headers)
        
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == book_id
        assert data["title"] == test_book["title"]
    
    @pytest.mark.asyncio
    async def test_get_book_not_found(self, test_client: AsyncClient, auth_headers: dict):
        """Test récupération livre inexistant"""
        response = await test_client.get("/api/books/nonexistent-id", headers=auth_headers)
        
        assert response.status_code == 404
    
    @pytest.mark.asyncio
    async def test_update_book_success(self, test_client: AsyncClient, auth_headers: dict, test_book: dict):
        """Test mise à jour livre réussie"""
        book_id = test_book["id"]
        update_data = {
            "status": "completed",
            "current_page": 300,
            "rating": 5,
            "review": "Excellent livre!"
        }
        
        response = await test_client.put(f"/api/books/{book_id}", json=update_data, headers=auth_headers)
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "completed"
        assert data["current_page"] == 300
        assert data["rating"] == 5
        assert data["review"] == "Excellent livre!"
    
    @pytest.mark.asyncio
    async def test_update_book_not_found(self, test_client: AsyncClient, auth_headers: dict):
        """Test mise à jour livre inexistant"""
        update_data = {"status": "completed"}
        
        response = await test_client.put("/api/books/nonexistent-id", json=update_data, headers=auth_headers)
        
        assert response.status_code == 404
    
    @pytest.mark.asyncio
    async def test_delete_book_success(self, test_client: AsyncClient, auth_headers: dict, test_book: dict):
        """Test suppression livre réussie"""
        book_id = test_book["id"]
        
        response = await test_client.delete(f"/api/books/{book_id}", headers=auth_headers)
        
        assert response.status_code == 200
        
        # Vérifier que le livre n'existe plus
        get_response = await test_client.get(f"/api/books/{book_id}", headers=auth_headers)
        assert get_response.status_code == 404
    
    @pytest.mark.asyncio
    async def test_delete_book_not_found(self, test_client: AsyncClient, auth_headers: dict):
        """Test suppression livre inexistant"""
        response = await test_client.delete("/api/books/nonexistent-id", headers=auth_headers)
        
        assert response.status_code == 404
    
    @pytest.mark.asyncio
    async def test_search_books(self, test_client: AsyncClient, auth_headers: dict, multiple_test_books: list):
        """Test recherche dans les livres"""
        response = await test_client.get("/api/books/search?q=Test Book 1", headers=auth_headers)
        
        assert response.status_code == 200
        data = response.json()
        assert len(data) > 0
        assert any("Test Book 1" in book["title"] for book in data)
    
    @pytest.mark.asyncio
    async def test_books_without_auth(self, test_client: AsyncClient):
        """Test accès aux livres sans authentification"""
        response = await test_client.get("/api/books")
        
        assert response.status_code == 401