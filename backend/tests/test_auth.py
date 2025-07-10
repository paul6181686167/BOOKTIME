"""
Tests pour l'authentification BOOKTIME
Tests des endpoints d'inscription, connexion, et gestion des tokens
"""
import pytest
from httpx import AsyncClient

class TestAuthentication:
    """Tests pour les endpoints d'authentification"""
    
    @pytest.mark.asyncio
    async def test_health_endpoint(self, test_client: AsyncClient):
        """Test endpoint de santé de l'API"""
        response = await test_client.get("/health")
        
        assert response.status_code == 200
        data = response.json()
        assert "status" in data
        assert data["status"] == "ok"
    
    @pytest.mark.asyncio
    async def test_register_user_success(self, test_client: AsyncClient, test_user_data: dict):
        """Test inscription utilisateur réussie"""
        response = await test_client.post("/api/auth/register", json=test_user_data)
        
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert "token_type" in data
        assert data["token_type"] == "bearer"
        assert "user" in data
        assert data["user"]["first_name"] == test_user_data["first_name"]
        assert data["user"]["last_name"] == test_user_data["last_name"]
    
    @pytest.mark.asyncio
    async def test_register_user_missing_fields(self, test_client: AsyncClient):
        """Test inscription avec champs manquants"""
        user_data = {
            "first_name": "John"
            # last_name manquant
        }
        
        response = await test_client.post("/api/auth/register", json=user_data)
        
        assert response.status_code == 422
    
    @pytest.mark.asyncio
    async def test_login_user_success(self, test_client: AsyncClient, test_user_data: dict):
        """Test connexion utilisateur réussie"""
        # D'abord créer un utilisateur
        register_response = await test_client.post("/api/auth/register", json=test_user_data)
        assert register_response.status_code == 200
        
        # Ensuite se connecter
        login_response = await test_client.post("/api/auth/login", json=test_user_data)
        
        assert login_response.status_code == 200
        data = login_response.json()
        assert "access_token" in data
        assert "token_type" in data
        assert data["token_type"] == "bearer"
        assert "user" in data
        assert data["user"]["first_name"] == test_user_data["first_name"]
        assert data["user"]["last_name"] == test_user_data["last_name"]
    
    @pytest.mark.asyncio
    async def test_login_user_not_found(self, test_client: AsyncClient):
        """Test connexion utilisateur inexistant"""
        user_data = {
            "first_name": "Unknown",
            "last_name": "User"
        }
        
        response = await test_client.post("/api/auth/login", json=user_data)
        
        assert response.status_code == 401
        data = response.json()
        assert "detail" in data