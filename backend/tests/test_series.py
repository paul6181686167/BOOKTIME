"""
Tests pour la gestion des séries BOOKTIME
Tests des endpoints de séries intelligentes
"""
import pytest
from httpx import AsyncClient

class TestSeries:
    """Tests pour les endpoints de gestion des séries"""
    
    @pytest.mark.asyncio
    async def test_get_popular_series(self, test_client: AsyncClient):
        """Test récupération séries populaires"""
        response = await test_client.get("/api/series/popular")
        
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) > 0
        
        # Vérifier structure d'une série
        series = data[0]
        assert "name" in series
        assert "category" in series
        assert "total_volumes" in series
        assert "description" in series
    
    @pytest.mark.asyncio
    async def test_get_popular_series_by_category(self, test_client: AsyncClient):
        """Test récupération séries populaires par catégorie"""
        response = await test_client.get("/api/series/popular?category=manga")
        
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        
        # Toutes les séries devraient être des mangas
        for series in data:
            assert series["category"] == "manga"
    
    @pytest.mark.asyncio
    async def test_search_series(self, test_client: AsyncClient):
        """Test recherche de séries"""
        response = await test_client.get("/api/series/search?q=Harry Potter")
        
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        
        # Vérifier que les résultats contiennent "Harry Potter"
        for series in data:
            assert "Harry Potter" in series["name"] or "Harry Potter" in series.get("description", "")
    
    @pytest.mark.asyncio
    async def test_detect_series_from_book(self, test_client: AsyncClient, auth_headers: dict):
        """Test détection de série à partir d'un livre"""
        book_data = {
            "title": "Harry Potter and the Philosopher's Stone",
            "author": "J.K. Rowling",
            "category": "roman"
        }
        
        response = await test_client.post("/api/series/detect", json=book_data, headers=auth_headers)
        
        assert response.status_code == 200
        data = response.json()
        assert "detected_series" in data
        assert len(data["detected_series"]) > 0
        
        # Vérifier structure de la série détectée
        series = data["detected_series"][0]
        assert "name" in series
        assert "confidence_score" in series
        assert series["confidence_score"] >= 0.0
    
    @pytest.mark.asyncio
    async def test_complete_series_auto_add(self, test_client: AsyncClient, auth_headers: dict, test_book: dict):
        """Test ajout automatique de tous les volumes d'une série"""
        complete_data = {
            "series_name": "Test Series",
            "target_volumes": 5,
            "template_book_id": test_book["id"]
        }
        
        response = await test_client.post("/api/series/complete", json=complete_data, headers=auth_headers)
        
        assert response.status_code == 200
        data = response.json()
        assert "books_added" in data
        assert "series_info" in data
        assert data["books_added"] == 5
        assert data["series_info"]["name"] == "Test Series"
    
    @pytest.mark.asyncio
    async def test_get_user_series_library(self, test_client: AsyncClient, auth_headers: dict, multiple_test_books: list):
        """Test récupération bibliothèque de séries utilisateur"""
        response = await test_client.get("/api/series/library", headers=auth_headers)
        
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        
        # Vérifier structure d'une série de bibliothèque
        if len(data) > 0:
            series = data[0]
            assert "name" in series
            assert "books" in series
            assert "progress" in series
            assert "completion_percentage" in series
    
    @pytest.mark.asyncio
    async def test_get_series_recommendations(self, test_client: AsyncClient, auth_headers: dict):
        """Test récupération recommandations de séries"""
        response = await test_client.get("/api/series/recommendations", headers=auth_headers)
        
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        
        # Vérifier structure des recommandations
        for recommendation in data:
            assert "name" in recommendation
            assert "reason" in recommendation
            assert "confidence_score" in recommendation
    
    @pytest.mark.asyncio
    async def test_update_series_preferences(self, test_client: AsyncClient, auth_headers: dict):
        """Test mise à jour préférences de séries"""
        preferences = {
            "preferred_categories": ["roman", "manga"],
            "max_volumes_per_series": 10,
            "auto_add_enabled": True
        }
        
        response = await test_client.put("/api/series/preferences", json=preferences, headers=auth_headers)
        
        assert response.status_code == 200
        data = response.json()
        assert data["preferred_categories"] == preferences["preferred_categories"]
        assert data["max_volumes_per_series"] == preferences["max_volumes_per_series"]
        assert data["auto_add_enabled"] == preferences["auto_add_enabled"]
    
    @pytest.mark.asyncio
    async def test_series_analytics(self, test_client: AsyncClient, auth_headers: dict):
        """Test analytics des séries"""
        response = await test_client.get("/api/series/analytics", headers=auth_headers)
        
        assert response.status_code == 200
        data = response.json()
        assert "total_series" in data
        assert "completed_series" in data
        assert "in_progress_series" in data
        assert "favorite_categories" in data
        assert "completion_stats" in data
    
    @pytest.mark.asyncio
    async def test_series_without_auth(self, test_client: AsyncClient):
        """Test accès aux séries sans authentification"""
        response = await test_client.get("/api/series/library")
        
        assert response.status_code == 401
    
    @pytest.mark.asyncio
    async def test_invalid_series_complete_request(self, test_client: AsyncClient, auth_headers: dict):
        """Test requête de complétion de série invalide"""
        invalid_data = {
            "series_name": "",  # Nom vide
            "target_volumes": 0,  # Nombre invalide
            "template_book_id": "nonexistent-id"
        }
        
        response = await test_client.post("/api/series/complete", json=invalid_data, headers=auth_headers)
        
        assert response.status_code == 422