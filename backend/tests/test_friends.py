import pytest
from fastapi import HTTPException

from app.friends.helpers import (
    MAX_MESSAGE_CHARS,
    clean_book_ref,
    clean_message,
    display_label,
    pair_key,
    parse_iso,
    search_filter,
)


# ---------- fonctions pures ----------


def test_pair_key_is_symmetric():
    assert pair_key("b", "a") == pair_key("a", "b") == "a|b"


def test_display_label_prefers_name_then_email_prefix():
    assert display_label({"display_name": " Paul ", "email": "x@y.fr"}) == "Paul"
    assert display_label({"email": "lecteur@mail.fr"}) == "lecteur"
    assert display_label(None) == "Lecteur"


def test_search_filter_never_matches_email_fragments():
    exact = search_filter("Paul@Mail.fr", "me")
    assert exact["email"] == "paul@mail.fr"
    by_name = search_filter("pa", "me")
    assert "display_name" in by_name and "email" not in by_name
    assert search_filter("p", "me") is None
    assert search_filter("", "me") is None


def test_search_filter_escapes_regex():
    flt = search_filter("a.*", "me")
    assert flt["display_name"]["$regex"] == r"a\.\*"


def test_clean_message_requires_text_or_book():
    with pytest.raises(HTTPException):
        clean_message("  ", None)
    assert clean_message(" salut ", None) == {"text": "salut", "book": None}
    with pytest.raises(HTTPException):
        clean_message("a" * (MAX_MESSAGE_CHARS + 1), None)


def test_clean_book_ref_validates_and_trims():
    ref = clean_book_ref(
        {"title": "  Dune ", "author": "Frank Herbert", "cover_url": "https://x/y.jpg", "evil": "x"}
    )
    assert ref["title"] == "Dune"
    assert ref["cover_url"] == "https://x/y.jpg"
    assert "evil" not in ref
    assert clean_book_ref({"title": "Dune", "cover_url": "javascript:alert(1)"})["cover_url"] == ""
    with pytest.raises(HTTPException):
        clean_book_ref({"author": "Sans titre"})
    assert clean_book_ref(None) is None


def test_parse_iso_round_trip():
    parsed = parse_iso("2026-11-06T18:00:00.123456Z")
    assert parsed.year == 2026 and parsed.tzinfo is None
    assert parse_iso("n'importe quoi") is None


# ---------- parcours complet (base simulée, jamais la vraie base) ----------

mongomock = pytest.importorskip("mongomock")


@pytest.fixture
def api(monkeypatch):
    from fastapi import FastAPI
    from fastapi.testclient import TestClient

    from app.friends import routes
    from app.security.jwt import get_current_user

    mock_db = mongomock.MongoClient().db
    monkeypatch.setattr(routes, "friendships", mock_db["friendships"])
    monkeypatch.setattr(routes, "messages", mock_db["friend_messages"])
    monkeypatch.setattr(routes, "users_collection", mock_db["users"])
    monkeypatch.setattr(routes, "books_collection", mock_db["books"])
    monkeypatch.setattr(routes, "_indexes_ready", True)

    mock_db["users"].insert_many(
        [
            {"id": "u1", "email": "alice@mail.fr", "display_name": "Alice", "bio": "Lectrice de SF"},
            {"id": "u2", "email": "bob@mail.fr", "display_name": "Bob"},
            {"id": "u3", "email": "carl@mail.fr"},
        ]
    )
    mock_db["books"].insert_many(
        [
            {"id": "b1", "user_id": "u2", "title": "Dune", "author": "Frank Herbert",
             "is_favorite": True, "rating": 5, "review": "Un chef-d'oeuvre", "status": "completed"},
            {"id": "b2", "user_id": "u2", "title": "Hyperion", "author": "Dan Simmons",
             "rating": 4, "status": "completed"},
            {"id": "b3", "user_id": "u2", "title": "Neuromancien", "author": "William Gibson",
             "status": "to_read"},
        ]
    )

    app = FastAPI()
    app.include_router(routes.router)
    current = {"id": "u1"}
    app.dependency_overrides[get_current_user] = lambda: {"id": current["id"], "email": "x"}
    client = TestClient(app)

    def as_user(user_id):
        current["id"] = user_id
        return client

    return as_user


def test_full_friend_flow(api):
    alice = api("u1")

    # Recherche : par nom, et par email exact ; jamais par fragment d'email
    names = alice.get("/api/friends/search", params={"q": "bo"}).json()["users"]
    assert [u["id"] for u in names] == ["u2"] and names[0]["state"] == "none"
    assert alice.get("/api/friends/search", params={"q": "carl@mail.fr"}).json()["users"][0]["id"] == "u3"
    assert alice.get("/api/friends/search", params={"q": "carl"}).json()["users"] == []

    # Pas amis : profil et messages interdits
    assert alice.get("/api/friends/u2/profile").status_code == 403
    assert alice.post("/api/friends/u2/messages", json={"text": "salut"}).status_code == 403

    # Demande, puis acceptation par Bob
    assert alice.post("/api/friends/requests", json={"user_id": "u2"}).json()["state"] == "pending_out"
    assert alice.post("/api/friends/requests", json={"user_id": "u1"}).status_code == 400
    bob = api("u2")
    incoming = bob.get("/api/friends/requests").json()["incoming"]
    assert len(incoming) == 1 and incoming[0]["user"]["id"] == "u1"
    assert bob.get("/api/friends/unread").json()["pending_requests"] == 1
    assert bob.post(f"/api/friends/requests/{incoming[0]['request_id']}/accept").json()["state"] == "friends"

    # Alice voit le profil de Bob : favoris, avis, statistiques
    profile = api("u1").get("/api/friends/u2/profile").json()
    assert [b["title"] for b in profile["favorites"]] == ["Dune"]
    assert {b["title"] for b in profile["reviews"]} == {"Dune", "Hyperion"}
    assert profile["stats"] == {"total_books": 3, "completed_books": 2}

    # Messagerie avec recommandation de livre
    sent = api("u1").post(
        "/api/friends/u2/messages",
        json={"text": "Lis celui-ci !", "book": {"title": "Fondation", "author": "Isaac Asimov"}},
    ).json()["message"]
    assert sent["mine"] is True and sent["book"]["title"] == "Fondation"

    friends = api("u2").get("/api/friends").json()["friends"]
    assert friends[0]["id"] == "u1" and friends[0]["unread"] == 1
    assert friends[0]["last_message"]["book_title"] == "Fondation"
    assert api("u2").get("/api/friends/unread").json()["unread_messages"] == 1

    thread = api("u2").get("/api/friends/u1/messages").json()["messages"]
    assert len(thread) == 1 and thread[0]["mine"] is False
    assert api("u2").get("/api/friends/unread").json()["unread_messages"] == 0

    # Récupération incrémentale
    after = {"after": thread[0]["created_at"]}
    assert api("u2").get("/api/friends/u1/messages", params=after).json()["messages"] == []
    api("u2").post("/api/friends/u1/messages", json={"text": "Merci !"})
    newer = api("u1").get("/api/friends/u2/messages", params=after).json()["messages"]
    assert [m["text"] for m in newer] == ["Merci !"]

    # Rupture d'amitié : l'accès est refermé
    assert api("u1").delete("/api/friends/u2").json()["success"] is True
    assert api("u1").get("/api/friends/u2/messages").status_code == 403


def test_mutual_requests_become_friends_and_decline_works(api):
    api("u1").post("/api/friends/requests", json={"user_id": "u2"})
    # Bob envoie aussi une demande : l'amitié est acceptée directement
    assert api("u2").post("/api/friends/requests", json={"user_id": "u1"}).json()["state"] == "friends"

    api("u3").post("/api/friends/requests", json={"user_id": "u1"})
    request_id = api("u1").get("/api/friends/requests").json()["incoming"][0]["request_id"]
    assert api("u1").delete(f"/api/friends/requests/{request_id}").json()["success"] is True
    assert api("u1").get("/api/friends/requests").json()["incoming"] == []
