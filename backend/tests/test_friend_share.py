import pytest
from fastapi import HTTPException

from app.friends.helpers import search_filter, search_rank
from app.friends.identity import (
    FRIEND_CODE_ALPHABET,
    clean_username,
    new_friend_code,
    normalize_friend_code,
    safe_label,
)


# ---------- fonctions pures ----------


def test_new_friend_code_uses_unambiguous_alphabet():
    for _ in range(50):
        code = new_friend_code()
        assert len(code) == 8
        assert all(c in FRIEND_CODE_ALPHABET for c in code)
    assert not set("01OIL") & set(FRIEND_CODE_ALPHABET)


def test_normalize_friend_code():
    assert normalize_friend_code("abcd-2345") == "ABCD2345"
    assert normalize_friend_code(" abcd 2345 ") == "ABCD2345"
    assert normalize_friend_code("ABCD234") == ""
    assert normalize_friend_code("ABCD2340") == ""  # 0 n'existe pas dans l'alphabet
    assert normalize_friend_code(None) == ""


def test_clean_username():
    assert clean_username("  @Paul.Lit_9 ") == "paul.lit_9"
    assert clean_username("") == ""
    assert clean_username(None) == ""
    for bad in ("ab", "x" * 21, "éric", "pa ul", "_paul", "paul!", "admin"):
        with pytest.raises(HTTPException) as err:
            clean_username(bad)
        assert err.value.status_code == 400


def test_safe_label_never_leaks_email():
    assert safe_label({"display_name": "Alice", "email": "alice@mail.fr"}) == "Alice"
    assert safe_label({"username": "alice", "email": "alice@mail.fr"}) == "@alice"
    assert safe_label({"email": "alice@mail.fr"}) == "Lecteur"


def test_search_filter_handle_and_name():
    handle = search_filter("@Alice", "me")
    assert handle["username"]["$regex"] == "^alice"
    assert "$or" not in handle
    assert search_filter("@a", "me") is None
    by_text = search_filter("Ali", "me")
    assert by_text["$or"][0]["username"]["$regex"] == "^ali"
    assert search_filter("a@b.fr", "me")["email"] == "a@b.fr"


def test_search_rank_puts_exact_handle_first():
    assert search_rank({"username": "alice"}, "@alice") == 0
    assert search_rank({"username": "alice2"}, "alice") == 1
    assert search_rank({"display_name": "Alice"}, "alice") == 2


# ---------- parcours avec base simulée ----------

mongomock = pytest.importorskip("mongomock")


@pytest.fixture
def env(monkeypatch):
    from fastapi import FastAPI
    from fastapi.testclient import TestClient

    from app.auth import routes as auth_routes
    from app.friends import routes
    from app.security.jwt import get_current_user

    mock_db = mongomock.MongoClient().db
    for name in ("friendships", "messages"):
        monkeypatch.setattr(routes, name, mock_db[name])
    monkeypatch.setattr(routes, "users_collection", mock_db["users"])
    monkeypatch.setattr(routes, "books_collection", mock_db["books"])
    monkeypatch.setattr(routes, "_indexes_ready", True)
    monkeypatch.setattr(auth_routes, "users_collection", mock_db["users"])

    mock_db["users"].insert_many(
        [
            {"id": "u1", "email": "alice@mail.fr", "display_name": "Alice", "username": "alice"},
            {"id": "u2", "email": "bob@mail.fr", "display_name": "Bob"},
            {"id": "u3", "email": "carl@mail.fr", "friend_code": "ZZZZ2222"},
            {"id": "u4", "email": "dan@mail.fr", "username": "dan", "banned": True,
             "friend_code": "BBBB3333"},
            {"id": "u5", "email": "eve@mail.fr", "display_name": "Alicia", "username": "alicia",
             "settings": {"discoverable": False}, "friend_code": "HHHH4444"},
        ]
    )

    app = FastAPI()
    app.include_router(routes.router)
    app.include_router(auth_routes.router)
    current = {"id": "u1"}
    app.dependency_overrides[get_current_user] = lambda: {"id": current["id"], "email": "x"}
    client = TestClient(app)

    def as_user(user_id):
        current["id"] = user_id
        return client

    as_user.users = mock_db["users"]
    return as_user


def test_my_code_is_created_once_and_stable(env):
    first = env("u2").get("/api/friends/me/code").json()
    assert len(first["code"]) == 8
    assert env("u2").get("/api/friends/me/code").json()["code"] == first["code"]
    assert env("u1").get("/api/friends/me/code").json()["username"] == "alice"


def test_by_code_returns_card_without_email(env):
    res = env("u1").get("/api/friends/by-code/zzzz-2222")
    assert res.status_code == 200
    body = res.json()
    assert body["user"]["id"] == "u3"
    assert body["user"]["display_name"] == "Lecteur"
    assert body["user"]["state"] == "none"
    assert "email" not in body["user"]
    assert body["is_me"] is False


def test_by_code_works_for_non_discoverable_but_not_banned(env):
    assert env("u1").get("/api/friends/by-code/HHHH4444").status_code == 200
    assert env("u1").get("/api/friends/by-code/BBBB3333").status_code == 404
    assert env("u1").get("/api/friends/by-code/AAAA9999").status_code == 404
    assert env("u1").get("/api/friends/by-code/court").status_code == 400


def test_by_code_state_follows_friend_request(env):
    assert env("u1").post("/api/friends/requests", json={"user_id": "u3"}).status_code == 200
    assert env("u1").get("/api/friends/by-code/ZZZZ2222").json()["user"]["state"] == "pending_out"
    assert env("u3").get("/api/friends/by-code/ZZZZ2222").json()["is_me"] is True
    assert env("u3").get("/api/friends/by-code/ZZZZ2222").json()["user"]["state"] == "me"


def test_search_by_handle_ranks_exact_first_and_hides_hidden_users(env):
    users = env("u2").get("/api/friends/search", params={"q": "@ali"}).json()["users"]
    assert [u["username"] for u in users] == ["alice"]  # alicia n'est pas découvrable
    users = env("u2").get("/api/friends/search", params={"q": "alice"}).json()["users"]
    assert users[0]["username"] == "alice"


def test_set_username_unique_and_removable(env):
    res = env("u2").put("/api/auth/me/profile", json={"username": "@Bobby"})
    assert res.status_code == 200
    assert res.json()["profile"]["username"] == "bobby"
    taken = env("u3").put("/api/auth/me/profile", json={"username": "bobby"})
    assert taken.status_code == 409
    own = env("u2").put("/api/auth/me/profile", json={"username": "bobby"})
    assert own.status_code == 200
    assert env("u2").put("/api/auth/me/profile", json={"username": "x"}).status_code == 400
    removed = env("u2").put("/api/auth/me/profile", json={"username": ""})
    assert removed.json()["profile"]["username"] == ""
    assert "username" not in env.users.find_one({"id": "u2"})
