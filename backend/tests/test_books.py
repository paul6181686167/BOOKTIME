"""Tests API livres (`app/books/routes.py`) — pagination + CRUD."""

import pytest
from httpx import AsyncClient


class TestBooks:
    @pytest.mark.asyncio
    async def test_get_books_empty(self, test_client: AsyncClient, auth_headers: dict):
        response = await test_client.get("/api/books", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert "items" in data
        assert "total" in data
        assert isinstance(data["items"], list)

    @pytest.mark.asyncio
    async def test_add_book_success(
        self, test_client: AsyncClient, auth_headers: dict, test_book_payload: dict
    ):
        response = await test_client.post(
            "/api/books", json=test_book_payload, headers=auth_headers
        )
        assert response.status_code == 200
        data = response.json()
        assert data["title"] == test_book_payload["title"]
        assert data["author"] == test_book_payload["author"]
        assert "id" in data

    @pytest.mark.asyncio
    async def test_add_book_invalid_data(self, test_client: AsyncClient, auth_headers: dict):
        invalid_data = {
            "title": "",
            "author": "Test Author",
            "category": "invalid_category",
        }
        response = await test_client.post(
            "/api/books", json=invalid_data, headers=auth_headers
        )
        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_get_books_with_data(
        self, test_client: AsyncClient, auth_headers: dict, multiple_test_books: list
    ):
        response = await test_client.get("/api/books", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert data["total"] >= 3

    @pytest.mark.asyncio
    async def test_get_books_by_category(
        self, test_client: AsyncClient, auth_headers: dict, multiple_test_books: list
    ):
        response = await test_client.get(
            "/api/books?category=roman", headers=auth_headers
        )
        assert response.status_code == 200
        data = response.json()
        for item in data.get("items", []):
            assert item.get("category") == "roman"

    @pytest.mark.asyncio
    async def test_get_books_by_status(
        self, test_client: AsyncClient, auth_headers: dict, multiple_test_books: list
    ):
        response = await test_client.get(
            "/api/books?status=to_read", headers=auth_headers
        )
        assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_get_book_by_id(
        self, test_client: AsyncClient, auth_headers: dict, test_book: dict
    ):
        book_id = test_book["id"]
        response = await test_client.get(f"/api/books/{book_id}", headers=auth_headers)
        assert response.status_code == 200
        assert response.json()["id"] == book_id

    @pytest.mark.asyncio
    async def test_get_book_not_found(self, test_client: AsyncClient, auth_headers: dict):
        response = await test_client.get(
            "/api/books/nonexistent-id-xyz", headers=auth_headers
        )
        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_update_book_success(
        self, test_client: AsyncClient, auth_headers: dict, test_book: dict
    ):
        book_id = test_book["id"]
        update_data = {"status": "reading"}
        response = await test_client.put(
            f"/api/books/{book_id}", json=update_data, headers=auth_headers
        )
        assert response.status_code == 200
        assert response.json().get("status") == "reading"

    @pytest.mark.asyncio
    async def test_update_book_not_found(self, test_client: AsyncClient, auth_headers: dict):
        response = await test_client.put(
            "/api/books/nonexistent-id-xyz",
            json={"status": "reading"},
            headers=auth_headers,
        )
        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_delete_book_success(
        self, test_client: AsyncClient, auth_headers: dict, test_book: dict
    ):
        book_id = test_book["id"]
        response = await test_client.delete(f"/api/books/{book_id}", headers=auth_headers)
        assert response.status_code == 200
        get_response = await test_client.get(f"/api/books/{book_id}", headers=auth_headers)
        assert get_response.status_code == 404

    @pytest.mark.asyncio
    async def test_delete_book_not_found(self, test_client: AsyncClient, auth_headers: dict):
        response = await test_client.delete(
            "/api/books/nonexistent-id-xyz", headers=auth_headers
        )
        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_search_grouped(
        self, test_client: AsyncClient, auth_headers: dict, multiple_test_books: list
    ):
        response = await test_client.get(
            "/api/books/search-grouped?q=Test+Book+1", headers=auth_headers
        )
        assert response.status_code == 200
        data = response.json()
        assert data.get("total_books", 0) >= 1

    @pytest.mark.asyncio
    async def test_books_without_auth(self, test_client: AsyncClient):
        response = await test_client.get("/api/books")
        assert response.status_code in (401, 403)
