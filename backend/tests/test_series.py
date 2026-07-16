"""Tests API séries (`app/series/routes.py`)."""

import pytest
from httpx import AsyncClient


class TestSeries:
    @pytest.mark.asyncio
    async def test_get_popular_series(self, test_client: AsyncClient, auth_headers: dict):
        response = await test_client.get("/api/series/popular", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert "series" in data
        assert isinstance(data["series"], list)
        assert len(data["series"]) > 0
        s0 = data["series"][0]
        assert "name" in s0
        assert "category" in s0
        assert "volumes" in s0
        assert "description" in s0

    @pytest.mark.asyncio
    async def test_get_popular_series_by_category(
        self, test_client: AsyncClient, auth_headers: dict
    ):
        response = await test_client.get(
            "/api/series/popular?category=manga", headers=auth_headers
        )
        assert response.status_code == 200
        data = response.json()
        for series in data.get("series", []):
            assert series["category"] == "manga"

    @pytest.mark.asyncio
    async def test_search_series(self, test_client: AsyncClient, auth_headers: dict):
        response = await test_client.get(
            "/api/series/search?q=Harry+Potter", headers=auth_headers
        )
        assert response.status_code == 200
        data = response.json()
        assert "series" in data
        for series in data.get("series", []):
            blob = f"{series.get('name','')} {series.get('description','')}"
            assert "Harry" in blob or "Potter" in blob

    @pytest.mark.asyncio
    async def test_detect_series(self, test_client: AsyncClient, auth_headers: dict):
        response = await test_client.get(
            "/api/series/detect",
            params={"title": "Harry Potter and the Philosopher's Stone", "author": "J.K. Rowling"},
            headers=auth_headers,
        )
        assert response.status_code == 200
        data = response.json()
        assert "detected_series" in data
        assert isinstance(data["detected_series"], list)

    @pytest.mark.asyncio
    async def test_complete_series_auto_add(
        self, test_client: AsyncClient, auth_headers: dict, test_book: dict
    ):
        complete_data = {
            "series_name": "Harry Potter",
            "target_volumes": 2,
            "template_book_id": test_book["id"],
        }
        response = await test_client.post(
            "/api/series/complete", json=complete_data, headers=auth_headers
        )
        assert response.status_code == 200
        data = response.json()
        assert data.get("success") is True
        assert "created_books" in data

    @pytest.mark.asyncio
    async def test_get_user_series_library(
        self, test_client: AsyncClient, auth_headers: dict
    ):
        response = await test_client.get("/api/series/library", headers=auth_headers)
        assert response.status_code == 200
        assert isinstance(response.json(), list)

    @pytest.mark.asyncio
    async def test_reading_preferences_get(
        self, test_client: AsyncClient, auth_headers: dict
    ):
        response = await test_client.get(
            "/api/series/reading-preferences", headers=auth_headers
        )
        assert response.status_code == 200
        data = response.json()
        assert "preferences" in data

    @pytest.mark.asyncio
    async def test_series_without_auth(self, test_client: AsyncClient):
        response = await test_client.get("/api/series/library")
        assert response.status_code in (401, 403)

    @pytest.mark.asyncio
    async def test_invalid_series_complete_request(
        self, test_client: AsyncClient, auth_headers: dict
    ):
        invalid_data = {
            "series_name": "",
            "target_volumes": 0,
            "template_book_id": "nonexistent-id",
        }
        response = await test_client.post(
            "/api/series/complete", json=invalid_data, headers=auth_headers
        )
        assert response.status_code in (400, 422)
