"""Tests de l'écran d'accueil « Qu'as-tu déjà lu ? » (`app/catalog/routes.py`)."""

import pytest
from httpx import AsyncClient


class TestOnboardingCatalog:
    @pytest.mark.asyncio
    async def test_romans_proposes_une_grande_selection_groupee_par_genre(
        self, test_client: AsyncClient, auth_headers: dict
    ):
        r = await test_client.get("/api/catalog/onboarding?group=roman", headers=auth_headers)
        assert r.status_code == 200
        data = r.json()
        assert data["total"] >= 150
        assert len(data["genres"]) >= 5
        w = data["works"][0]
        assert {"id", "title", "author", "genre", "category", "cover_url"} <= set(w)
        assert all(x["category"] == "roman" for x in data["works"])
        assert {x["genre"] for x in data["works"]} == set(data["genres"])

    @pytest.mark.asyncio
    async def test_romans_graphiques_melangent_mangas_et_bd(
        self, test_client: AsyncClient, auth_headers: dict
    ):
        r = await test_client.get("/api/catalog/onboarding?group=graphic_novel", headers=auth_headers)
        assert r.status_code == 200
        data = r.json()
        assert data["total"] >= 100
        assert {x["category"] for x in data["works"]} == {"manga", "bd"}

    @pytest.mark.asyncio
    async def test_les_identifiants_sont_uniques(self, test_client: AsyncClient, auth_headers: dict):
        ids = []
        for group in ("roman", "graphic_novel"):
            r = await test_client.get(f"/api/catalog/onboarding?group={group}", headers=auth_headers)
            ids += [w["id"] for w in r.json()["works"]]
        assert len(ids) == len(set(ids))

    @pytest.mark.asyncio
    async def test_groupe_invalide_refuse(self, test_client: AsyncClient, auth_headers: dict):
        r = await test_client.get("/api/catalog/onboarding?group=autre", headers=auth_headers)
        assert r.status_code == 400

    @pytest.mark.asyncio
    async def test_exige_une_connexion(self, test_client: AsyncClient):
        r = await test_client.get("/api/catalog/onboarding?group=roman")
        assert r.status_code in (401, 403)

    @pytest.mark.asyncio
    async def test_ajout_cree_des_livres_termines_sans_date_de_fin(
        self, test_client: AsyncClient, auth_headers: dict
    ):
        catalog = (
            await test_client.get("/api/catalog/onboarding?group=roman", headers=auth_headers)
        ).json()["works"]
        picked = catalog[:3]

        r = await test_client.post(
            "/api/catalog/onboarding",
            json={"ids": [w["id"] for w in picked] + ["inconnu-xyz"]},
            headers=auth_headers,
        )
        assert r.status_code == 200
        assert r.json() == {"added": 3, "skipped": 0}

        books = (await test_client.get("/api/books?limit=100", headers=auth_headers)).json()["items"]
        by_title = {b["title"]: b for b in books}
        for w in picked:
            b = by_title[w["title"]]
            assert b["status"] == "completed"
            assert b["author"] == w["author"]
            assert b["category"] == "roman"
            assert b.get("date_completed") is None
            assert b.get("category_verified") is True

    @pytest.mark.asyncio
    async def test_ajout_ignore_les_doublons(self, test_client: AsyncClient, auth_headers: dict):
        catalog = (
            await test_client.get("/api/catalog/onboarding?group=roman", headers=auth_headers)
        ).json()["works"]
        ids = [catalog[5]["id"], catalog[5]["id"]]

        first = await test_client.post("/api/catalog/onboarding", json={"ids": ids}, headers=auth_headers)
        assert first.json() == {"added": 1, "skipped": 0}
        again = await test_client.post("/api/catalog/onboarding", json={"ids": ids}, headers=auth_headers)
        assert again.json() == {"added": 0, "skipped": 1}

    @pytest.mark.asyncio
    async def test_ajout_ne_prend_que_les_identifiants_du_catalogue(
        self, test_client: AsyncClient, auth_headers: dict
    ):
        r = await test_client.post(
            "/api/catalog/onboarding",
            json={"ids": ["x"] * 3, "title": "Livre piégé"},
            headers=auth_headers,
        )
        assert r.status_code == 200
        assert r.json() == {"added": 0, "skipped": 0}

    @pytest.mark.asyncio
    async def test_les_categories_du_catalogue_survivent_a_la_reclassification(
        self, test_client: AsyncClient, auth_headers: dict
    ):
        works = (
            await test_client.get("/api/catalog/onboarding?group=graphic_novel", headers=auth_headers)
        ).json()["works"]
        manga = next(w for w in works if w["category"] == "manga" and w.get("kind") != "series")
        bd = next(w for w in works if w["category"] == "bd" and w.get("kind") != "series")
        await test_client.post(
            "/api/catalog/onboarding", json={"ids": [manga["id"], bd["id"]]}, headers=auth_headers
        )

        books = (await test_client.get("/api/books?limit=100", headers=auth_headers)).json()["items"]
        cats = {b["title"]: b["category"] for b in books}
        assert cats[manga["title"]] == "manga"
        assert cats[bd["title"]] == "bd"

    @pytest.mark.asyncio
    async def test_les_livres_coches_ne_gonflent_ni_l_objectif_ni_le_calendrier(
        self, test_client: AsyncClient, auth_headers: dict
    ):
        works = (
            await test_client.get("/api/catalog/onboarding?group=roman", headers=auth_headers)
        ).json()["works"]
        await test_client.post(
            "/api/catalog/onboarding", json={"ids": [w["id"] for w in works[:4]]}, headers=auth_headers
        )

        stats = (await test_client.get("/api/stats", headers=auth_headers)).json()
        assert stats["completed_books"] == 4
        assert stats["completed_this_year"] == 0
        assert stats["completion_dates"] == {}

    @pytest.mark.asyncio
    async def test_tintin_asterix_one_piece_sont_ajoutes_comme_series(
        self, test_client: AsyncClient, auth_headers: dict
    ):
        works = (
            await test_client.get("/api/catalog/onboarding?group=graphic_novel", headers=auth_headers)
        ).json()["works"]
        wanted = [w for w in works if w["title"] in ("One Piece", "Astérix", "Tintin")]
        assert len(wanted) == 3
        assert all(w.get("kind") == "series" for w in wanted)

        r = await test_client.post(
            "/api/catalog/onboarding",
            json={"ids": [w["id"] for w in wanted]},
            headers=auth_headers,
        )
        assert r.status_code == 200
        assert r.json()["added"] == 3

        series = (await test_client.get("/api/series/library", headers=auth_headers)).json()
        items = series if isinstance(series, list) else series.get("series") or []
        names = {(s.get("series_name") or s.get("name") or "").lower() for s in items}
        assert "one piece" in names
        assert "astérix" in names or "asterix" in names
        assert "tintin" in names
        books = (await test_client.get("/api/books?limit=100", headers=auth_headers)).json()["items"]
        book_titles = {b["title"] for b in books}
        assert "One Piece" not in book_titles
        assert "Tintin" not in book_titles
