"""Les statistiques du profil doivent prendre en compte tous les livres (`stats/routes.py`)."""

from datetime import datetime, timezone

import pytest
from httpx import AsyncClient

from app.database.connection import books_collection


def _insert(user_id: str, **fields):
    doc = {
        "id": f"t-{fields['title']}",
        "user_id": user_id,
        "author": "A",
        "category": "roman",
        "date_added": datetime.now(timezone.utc),
        **fields,
    }
    books_collection.insert_one(doc)


class TestStatsAllBooks:
    @pytest.mark.asyncio
    async def test_la_somme_des_cases_est_egale_au_total(
        self, test_client: AsyncClient, auth_headers: dict, registered_user: dict
    ):
        uid = registered_user["user"]["id"]
        for title, status in [("a", "completed"), ("b", "reading"), ("c", "to_read"), ("d", "to_reread")]:
            _insert(uid, title=title, status=status)
        stats = (await test_client.get("/api/stats", headers=auth_headers)).json()
        assert stats["total_books"] == 4
        assert stats["to_reread_books"] == 1
        assert (
            stats["completed_books"] + stats["reading_books"] + stats["to_read_books"] + stats["to_reread_books"]
            == stats["total_books"]
        )

    @pytest.mark.asyncio
    async def test_pages_lues_comptent_termines_a_relire_et_en_cours(
        self, test_client: AsyncClient, auth_headers: dict, registered_user: dict
    ):
        uid = registered_user["user"]["id"]
        _insert(uid, title="fini", status="completed", total_pages=300)
        _insert(uid, title="relire", status="to_reread", total_pages=200, date_completed=datetime(2020, 5, 1))
        _insert(uid, title="encours", status="reading", total_pages=400, current_page=120)
        _insert(uid, title="depasse", status="reading", total_pages=100, current_page=500)
        _insert(uid, title="alire", status="to_read", total_pages=999)
        stats = (await test_client.get("/api/stats", headers=auth_headers)).json()
        assert stats["total_pages_read"] == 300 + 200 + 120 + 100

    @pytest.mark.asyncio
    async def test_un_livre_a_relire_garde_sa_date_de_lecture_sans_la_remplacer_par_aujourd_hui(
        self, test_client: AsyncClient, auth_headers: dict, registered_user: dict
    ):
        uid = registered_user["user"]["id"]
        _insert(uid, title="vieux", status="to_reread", date_completed=datetime(2020, 5, 1))
        # remis à relire sans date de lecture connue : pas de date inventée
        _insert(uid, title="sans-date", status="to_reread", updated_at=datetime.now(timezone.utc))
        stats = (await test_client.get("/api/stats", headers=auth_headers)).json()
        assert stats["completion_dates"] == {"2020-05-01": 1}
        assert stats["completed_this_year"] == 0
