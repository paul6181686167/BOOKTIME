"""
Tests pour l'authentification BOOKTIME
Tests des endpoints d'inscription, connexion, et gestion des tokens
"""
import pytest
from httpx import AsyncClient

class TestAuthentication:
    """Tests pour les endpoints d'authentification"""
    
    @pytest.mark.asyncio
    async def test_register_user_success(self, test_client: AsyncClient):
        """Test inscription utilisateur réussie"""
        user_data = {
            "first_name": "John",
            "last_name": "Doe"
        }
        
        response = await test_client.post("/api/auth/register", json=user_data)
        
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert "token_type" in data
        assert data["token_type"] == "bearer"
        assert "user" in data
        assert data["user"]["first_name"] == "John"
        assert data["user"]["last_name"] == "Doe"
    
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
    async def test_login_user_success(self, test_client: AsyncClient):
        """Test connexion utilisateur réussie"""
        # D'abord créer un utilisateur
        user_data = {
            "first_name": "Jane",
            "last_name": "Smith"
        }
        
        register_response = await test_client.post("/api/auth/register", json=user_data)
        assert register_response.status_code == 200
        
        # Ensuite se connecter
        login_response = await test_client.post("/api/auth/login", json=user_data)
        
        assert login_response.status_code == 200
        data = login_response.json()
        assert "access_token" in data
        assert "token_type" in data
        assert data["token_type"] == "bearer"
        assert "user" in data
        assert data["user"]["first_name"] == "Jane"
        assert data["user"]["last_name"] == "Smith"
    
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
    
    @pytest.mark.asyncio
    async def test_get_current_user(self, test_client: AsyncClient, auth_headers: dict):
        """Test récupération utilisateur connecté"""
        response = await test_client.get("/api/auth/me", headers=auth_headers)
        
        assert response.status_code == 200
        data = response.json()
        assert "id" in data
        assert "first_name" in data
        assert "last_name" in data
        assert data["first_name"] == "Test"
        assert data["last_name"] == "User"
    
    @pytest.mark.asyncio
    async def test_get_current_user_no_token(self, test_client: AsyncClient):
        """Test récupération utilisateur sans token"""
        response = await test_client.get("/api/auth/me")
        
        assert response.status_code == 401
    
    @pytest.mark.asyncio
    async def test_get_current_user_invalid_token(self, test_client: AsyncClient):
        """Test récupération utilisateur avec token invalide"""
        headers = {"Authorization": "Bearer invalid_token"}
        response = await test_client.get("/api/auth/me", headers=headers)
        
        assert response.status_code == 401
    
    @pytest.mark.asyncio
    async def test_register_duplicate_user(self, test_client: AsyncClient):
        """Test inscription utilisateur déjà existant"""
        user_data = {
            "first_name": "Duplicate",
            "last_name": "User"
        }
        
        # Première inscription
        response1 = await test_client.post("/api/auth/register", json=user_data)
        assert response1.status_code == 200
        
        # Seconde inscription (même utilisateur)
        response2 = await test_client.post("/api/auth/register", json=user_data)
        assert response2.status_code == 200  # Connexion automatique
        
        # Vérifier que c'est le même utilisateur
        data1 = response1.json()
        data2 = response2.json()
        assert data1["user"]["id"] == data2["user"]["id"]