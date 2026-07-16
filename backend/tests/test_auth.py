"""Tests authentification JWT (email + mot de passe)."""

import pytest
from httpx import AsyncClient


class TestAuthentication:
    @pytest.mark.asyncio
    async def test_health_endpoint(self, test_client: AsyncClient):
        response = await test_client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data.get("status") == "ok"

    @pytest.mark.asyncio
    async def test_register_user_success(
        self, test_client: AsyncClient, unique_email: str, test_password: str
    ):
        response = await test_client.post(
            "/api/auth/register",
            json={"email": unique_email, "password": test_password},
        )
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert data.get("token_type") == "bearer"
        assert data["user"]["email"] == unique_email.lower()

    @pytest.mark.asyncio
    async def test_register_user_missing_fields(self, test_client: AsyncClient):
        response = await test_client.post(
            "/api/auth/register",
            json={"email": "incomplet@example.com"},
        )
        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_login_user_success(
        self, test_client: AsyncClient, unique_email: str, test_password: str
    ):
        await test_client.post(
            "/api/auth/register",
            json={"email": unique_email, "password": test_password},
        )
        login_response = await test_client.post(
            "/api/auth/login",
            json={"email": unique_email, "password": test_password},
        )
        assert login_response.status_code == 200
        data = login_response.json()
        assert "access_token" in data
        assert data["user"]["email"] == unique_email.lower()

    @pytest.mark.asyncio
    async def test_login_user_not_found(self, test_client: AsyncClient):
        response = await test_client.post(
            "/api/auth/login",
            json={"email": "absent_xyz@example.com", "password": "secretpass1"},
        )
        assert response.status_code == 400
