"""« Découvrir » ne doit jamais tourner dans le vide ni rester vide (`recommendations/resilience.py`)."""

import asyncio

import pytest
from httpx import AsyncClient

from app.recommendations import resilience
from app.recommendations.routes import recommendation_service


def _rec(title: str) -> dict:
    return {
        "book_id": f"/works/{title}",
        "title": title,
        "author": "Auteur",
        "category": "roman",
        "source": "algorithm_author",
        "reasons": ["test"],
    }


@pytest.fixture(autouse=True)
def _reset_cache():
    resilience.clear_cache()
    yield
    resilience.clear_cache()


async def _add_book(client: AsyncClient, headers: dict, title: str, category: str = "roman"):
    r = await client.post(
        "/api/books", headers=headers, json={"title": title, "author": "A", "category": category, "status": "completed"}
    )
    assert r.status_code in (200, 201), r.text


class TestRecommendationsResilience:
    @pytest.mark.asyncio
    async def test_service_trop_lent_repli_sur_le_catalogue_local(
        self, test_client: AsyncClient, auth_headers: dict, monkeypatch
    ):
        async def very_slow(*args, **kwargs):
            await asyncio.sleep(30)

        monkeypatch.setattr(recommendation_service, "get_personalized_recommendations", very_slow)
        monkeypatch.setenv("RECO_PERSONALIZED_TIMEOUT", "0.2")

        r = await test_client.get("/api/recommendations/personalized?limit=12&refresh=true", headers=auth_headers)
        assert r.status_code == 200
        data = r.json()["data"]
        assert data["fallback"] is True
        assert len(data["recommendations"]) == 12
        first = data["recommendations"][0]
        assert first["title"] and first["cover_url"]

    @pytest.mark.asyncio
    async def test_service_en_echec_ne_renvoie_pas_une_liste_vide(
        self, test_client: AsyncClient, auth_headers: dict, monkeypatch
    ):
        async def empty(*args, **kwargs):
            return {"recommendations": [], "error": "Open Library indisponible"}

        monkeypatch.setattr(recommendation_service, "get_personalized_recommendations", empty)
        r = await test_client.get("/api/recommendations/personalized?limit=10", headers=auth_headers)
        assert r.status_code == 200
        assert len(r.json()["data"]["recommendations"]) == 10

    @pytest.mark.asyncio
    async def test_populaires_en_panne_repli_local(self, test_client: AsyncClient, monkeypatch):
        async def boom(*args, **kwargs):
            raise RuntimeError("panne")

        monkeypatch.setattr(recommendation_service, "_get_popular_recommendations", boom)
        r = await test_client.get("/api/recommendations/popular?limit=8")
        assert r.status_code == 200
        assert len(r.json()["data"]["recommendations"]) == 8

    @pytest.mark.asyncio
    async def test_cache_puis_rafraichir_regenere(
        self, test_client: AsyncClient, auth_headers: dict, monkeypatch
    ):
        calls = {"n": 0}

        async def fake(user_id, limit):
            calls["n"] += 1
            return {"recommendations": [_rec(f"Livre {calls['n']}")]}

        monkeypatch.setattr(recommendation_service, "get_personalized_recommendations", fake)
        await test_client.get("/api/recommendations/personalized?limit=5", headers=auth_headers)
        r2 = await test_client.get("/api/recommendations/personalized?limit=5", headers=auth_headers)
        assert calls["n"] == 1  # deuxième appel servi par le cache
        assert r2.json()["data"]["recommendations"][0]["title"] == "Livre 1"

        r3 = await test_client.get("/api/recommendations/personalized?limit=5&refresh=true", headers=auth_headers)
        assert calls["n"] == 2
        assert r3.json()["data"]["recommendations"][0]["title"] == "Livre 2"

    @pytest.mark.asyncio
    async def test_rafraichir_en_echec_ressert_la_derniere_liste(
        self, test_client: AsyncClient, auth_headers: dict, monkeypatch
    ):
        state = {"ok": True}

        async def flaky(user_id, limit):
            if state["ok"]:
                return {"recommendations": [_rec("Dernière liste connue")]}
            raise RuntimeError("Open Library en panne")

        monkeypatch.setattr(recommendation_service, "get_personalized_recommendations", flaky)
        await test_client.get("/api/recommendations/personalized?limit=5", headers=auth_headers)
        state["ok"] = False
        r = await test_client.get("/api/recommendations/personalized?limit=5&refresh=true", headers=auth_headers)
        data = r.json()["data"]
        assert data["stale"] is True
        assert data["recommendations"][0]["title"] == "Dernière liste connue"

    @pytest.mark.asyncio
    async def test_le_repli_exclut_les_livres_deja_possedes_et_privilegie_les_categories_lues(
        self, test_client: AsyncClient, auth_headers: dict, monkeypatch
    ):
        async def empty(*args, **kwargs):
            return {"recommendations": []}

        monkeypatch.setattr(recommendation_service, "get_personalized_recommendations", empty)
        owned = resilience._local_pool()
        titles = [w["title"] for w in owned if w["category"] == "manga"][:3]
        for t in titles:
            await _add_book(test_client, auth_headers, t, "manga")

        r = await test_client.get("/api/recommendations/personalized?limit=20", headers=auth_headers)
        recs = r.json()["data"]["recommendations"]
        got = {x["title"] for x in recs}
        assert not got & set(titles)
        mangas = [x for x in recs if x["category"] == "manga"]
        assert len(mangas) >= 10  # ~70 % dans la catégorie lue

    @pytest.mark.asyncio
    async def test_filtre_categorie_ne_pollue_pas_le_cache(
        self, test_client: AsyncClient, auth_headers: dict, monkeypatch
    ):
        async def fake(user_id, limit):
            return {"recommendations": [_rec("Roman A"), {**_rec("BD B"), "category": "bd"}]}

        monkeypatch.setattr(recommendation_service, "get_personalized_recommendations", fake)
        only_bd = await test_client.get("/api/recommendations/personalized?limit=5&category=bd", headers=auth_headers)
        assert [x["title"] for x in only_bd.json()["data"]["recommendations"]] == ["BD B"]
        everything = await test_client.get("/api/recommendations/personalized?limit=5", headers=auth_headers)
        assert len(everything.json()["data"]["recommendations"]) == 2
