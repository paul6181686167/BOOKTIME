from datetime import datetime, timedelta

import pytest
from fastapi import HTTPException

from app.admin.helpers import (
    admin_emails,
    bucket_by_day,
    clean_reason,
    is_admin,
    is_online,
)
from app.security.jwt import should_touch_last_seen


# ---------- fonctions pures ----------


def test_admin_emails_parsing_is_case_insensitive_and_trimmed():
    assert admin_emails(" Paul@Mail.fr , ,autre@mail.fr ") == {"paul@mail.fr", "autre@mail.fr"}
    assert admin_emails("") == set()


def test_nobody_is_admin_without_configuration():
    assert is_admin({"email": "paul@mail.fr"}, set()) is False
    assert is_admin(None, {"paul@mail.fr"}) is False
    assert is_admin({"email": "PAUL@mail.fr"}, {"paul@mail.fr"}) is True
    assert is_admin({"email": "x@y.fr", "is_admin": True}, set()) is True
    # Une valeur truthy qui n'est pas exactement True ne suffit pas
    assert is_admin({"email": "x@y.fr", "is_admin": "yes"}, set()) is False


def test_bucket_by_day_covers_every_day_even_empty():
    today = datetime(2026, 11, 6, 15, 0)
    dates = [
        datetime(2026, 11, 6, 1),
        datetime(2026, 11, 6, 23),
        datetime(2026, 11, 4),
        datetime(2026, 10, 1),  # hors fenêtre
        None,
        "pas une date",
    ]
    out = bucket_by_day(dates, 3, today)
    assert out == [
        {"date": "2026-11-04", "count": 1},
        {"date": "2026-11-05", "count": 0},
        {"date": "2026-11-06", "count": 2},
    ]


def test_is_online_window():
    now = datetime(2026, 11, 6, 12, 0)
    assert is_online(now - timedelta(minutes=5), now) is True
    assert is_online(now - timedelta(minutes=30), now) is False
    assert is_online(None, now) is False


def test_clean_reason_trims_and_limits():
    assert clean_reason("  spam   répété ") == "spam répété"
    assert len(clean_reason("a" * 500)) == 200
    assert clean_reason(None) == ""


def test_last_seen_is_rewritten_only_when_old():
    now = datetime(2026, 11, 6, 12, 0)
    assert should_touch_last_seen(None, now) is True
    assert should_touch_last_seen(now - timedelta(seconds=60), now) is False
    assert should_touch_last_seen(now - timedelta(seconds=600), now) is True


# ---------- parcours complet (base simulée) ----------

mongomock = pytest.importorskip("mongomock")


@pytest.fixture
def world(monkeypatch):
    from fastapi import FastAPI
    from fastapi.testclient import TestClient

    from app.admin import routes
    from app.security.jwt import get_current_user

    monkeypatch.setenv("ADMIN_EMAILS", "admin@mail.fr")
    mock_db = mongomock.MongoClient().db
    monkeypatch.setattr(routes, "db", mock_db)
    monkeypatch.setattr(routes, "users_collection", mock_db["users"])
    monkeypatch.setattr(routes, "books_collection", mock_db["books"])
    monkeypatch.setattr(routes, "series_library_collection", mock_db["series_library"])

    now = datetime.utcnow()
    mock_db["users"].insert_many(
        [
            {"id": "admin", "email": "admin@mail.fr", "created_at": now - timedelta(days=30),
             "last_seen": now},
            {"id": "u1", "email": "alice@mail.fr", "display_name": "Alice",
             "created_at": now, "last_seen": now - timedelta(minutes=3)},
            {"id": "u2", "email": "bob@mail.fr", "created_at": now - timedelta(days=3),
             "last_seen": now - timedelta(days=2)},
            {"id": "u3", "email": "troll@mail.fr", "created_at": now - timedelta(days=10),
             "banned": True, "banned_reason": "spam"},
        ]
    )
    mock_db["books"].insert_many(
        [
            {"id": "b1", "user_id": "u1", "title": "A", "category": "roman", "status": "completed",
             "review": "Super", "rating": 5, "date_added": now, "is_favorite": True},
            {"id": "b2", "user_id": "u1", "title": "B", "category": "manga", "status": "reading",
             "review": "", "rating": 0, "date_added": now - timedelta(days=2)},
            {"id": "b3", "user_id": "u2", "title": "C", "category": "poesie", "status": "to_read",
             "date_added": now - timedelta(days=40)},
        ]
    )
    mock_db["friend_messages"].insert_many(
        [
            {"id": "m1", "text": "salut", "book": None, "created_at": now},
            {"id": "m2", "text": "", "book": {"title": "Dune"}, "created_at": now - timedelta(days=3)},
        ]
    )
    mock_db["friendships"].insert_many(
        [{"id": "f1", "status": "accepted"}, {"id": "f2", "status": "pending"}]
    )

    app = FastAPI()
    app.include_router(routes.router)
    current = {"id": "admin"}

    def fake_user():
        return mock_db["users"].find_one({"id": current["id"]}, {"_id": 0})

    app.dependency_overrides[get_current_user] = fake_user
    client = TestClient(app)

    def as_user(user_id):
        current["id"] = user_id
        return client

    return as_user, mock_db


def test_non_admin_is_refused_everywhere(world):
    as_user, _ = world
    client = as_user("u1")
    assert client.get("/api/admin/stats").status_code == 403
    assert client.get("/api/admin/users").status_code == 403
    assert client.post("/api/admin/users/u2/ban", json={}).status_code == 403
    assert client.post("/api/admin/users/u3/unban").status_code == 403


def test_stats_are_computed_live(world):
    as_user, _ = world
    stats = as_user("admin").get("/api/admin/stats").json()

    assert stats["users"]["total"] == 4
    assert stats["users"]["banned"] == 1
    assert stats["users"]["online"] == 2  # admin et Alice
    assert stats["users"]["active_24h"] == 2
    assert stats["users"]["new_today"] == 1
    assert len(stats["users"]["signups_per_day"]) == 14
    assert sum(d["count"] for d in stats["users"]["signups_per_day"]) == 3  # u3 a plus de 14 jours

    books = stats["books"]
    assert books["total"] == 3 and books["completed"] == 1 and books["reading"] == 1
    assert books["to_read"] == 1 and books["added_today"] == 1 and books["added_7d"] == 2
    assert books["by_category"] == {"roman": 1, "bd": 0, "manga": 1, "autre": 1}

    eng = stats["engagement"]
    assert eng["reviews"] == 1 and eng["ratings"] == 1 and eng["favorites"] == 1
    assert eng["messages"] == 2 and eng["messages_24h"] == 1 and eng["book_recommendations"] == 1
    assert eng["friendships"] == 1 and eng["friend_requests_pending"] == 1


def test_user_list_search_and_counts(world):
    as_user, _ = world
    client = as_user("admin")

    data = client.get("/api/admin/users").json()
    assert data["total"] == 4
    assert [u["id"] for u in data["users"]] == ["u1", "u2", "u3", "admin"]  # plus récent d'abord
    alice = data["users"][0]
    assert alice["books_count"] == 2 and alice["reviews_count"] == 1 and alice["online"] is True
    assert "password_hash" not in alice and "avatar_url" not in alice
    assert data["users"][3]["is_admin"] is True

    assert [u["id"] for u in client.get("/api/admin/users", params={"q": "ali"}).json()["users"]] == ["u1"]
    banned = client.get("/api/admin/users", params={"status": "banned"}).json()
    assert [u["id"] for u in banned["users"]] == ["u3"] and banned["users"][0]["banned_reason"] == "spam"
    assert client.get("/api/admin/users", params={"limit": 2}).json()["users"].__len__() == 2
    assert client.get("/api/admin/users", params={"status": "x"}).status_code == 422


def test_ban_and_unban_rules(world):
    as_user, mock_db = world
    client = as_user("admin")

    assert client.post("/api/admin/users/u2/ban", json={"reason": "  insultes  "}).json()["success"] is True
    stored = mock_db["users"].find_one({"id": "u2"})
    assert stored["banned"] is True and stored["banned_reason"] == "insultes" and stored["banned_at"]

    assert client.post("/api/admin/users/admin/ban", json={}).status_code == 400  # soi-même
    assert client.post("/api/admin/users/inconnu/ban", json={}).status_code == 404

    mock_db["users"].update_one({"id": "u1"}, {"$set": {"is_admin": True}})
    assert client.post("/api/admin/users/u1/ban", json={}).status_code == 400  # autre administrateur

    assert client.post("/api/admin/users/u2/unban").json()["success"] is True
    stored = mock_db["users"].find_one({"id": "u2"})
    assert stored["banned"] is False and "banned_reason" not in stored
    assert client.post("/api/admin/users/inconnu/unban").status_code == 404


# ---------- contrôle du bannissement à l'authentification ----------


def test_banned_account_is_rejected_by_authentication(monkeypatch):
    from fastapi.security import HTTPAuthorizationCredentials

    from app.security import jwt as security

    mock_db = mongomock.MongoClient().db
    monkeypatch.setattr(security, "users_collection", mock_db["users"])
    mock_db["users"].insert_many(
        [
            {"id": "ok", "email": "ok@mail.fr"},
            {"id": "bad", "email": "bad@mail.fr", "banned": True},
        ]
    )

    def creds(user_id):
        token = security.create_access_token({"sub": user_id}, timedelta(minutes=5))
        return HTTPAuthorizationCredentials(scheme="Bearer", credentials=token)

    with pytest.raises(HTTPException) as banned:
        security.get_current_user(creds("bad"))
    assert banned.value.status_code == 403 and "suspendu" in banned.value.detail

    user = security.get_current_user(creds("ok"))
    assert user["id"] == "ok"
    # La dernière activité est enregistrée au passage
    assert isinstance(mock_db["users"].find_one({"id": "ok"})["last_seen"], datetime)
