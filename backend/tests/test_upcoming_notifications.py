import pytest

from app.upcoming import scheduler

mongomock = pytest.importorskip("mongomock")


def test_notif_mode_defaults_to_in_app():
    assert scheduler.notif_mode({}) == "in_app"
    assert scheduler.notif_mode({"notif_upcoming": None}) == "in_app"
    assert scheduler.notif_mode({"notif_upcoming": "email"}) == "email"
    assert scheduler.notif_mode({"notif_upcoming": "none"}) == "none"


def test_eligible_users_include_default_but_not_opted_out(monkeypatch):
    users = mongomock.MongoClient().db.users
    users.insert_many(
        [
            {"id": "default"},  # jamais touché aux réglages
            {"id": "inapp", "notif_upcoming": "in_app"},
            {"id": "mail", "notif_upcoming": "email"},
            {"id": "off", "notif_upcoming": "none"},
        ]
    )
    ids = {u["id"] for u in users.find(scheduler.eligible_users_query())}
    assert ids == {"default", "inapp", "mail"}


def test_process_user_notifies_available_release_once(monkeypatch):
    created, emails = [], []
    item = {"id": "next_tome:x:3", "title": "X T3", "type": "next_tome", "series_name": "X"}

    async def fake_upcoming(user):
        return {"groups": {"available": [item]}}

    monkeypatch.setattr(scheduler, "get_upcoming_for_user", fake_upcoming)
    monkeypatch.setattr(scheduler, "create_notification", lambda uid, **kw: created.append((uid, kw)))
    monkeypatch.setattr(scheduler, "send_email", lambda *a: emails.append(a))
    notified = set()
    monkeypatch.setattr(scheduler.cache, "get_notified_ids", lambda uid: set(notified))
    monkeypatch.setattr(
        scheduler.cache, "set_cached", lambda uid, payload, notified_ids=(): notified.update(notified_ids)
    )

    user = {"id": "u1", "email": "a@b.fr"}  # sans réglage -> in_app
    scheduler._process_user(user)
    scheduler._process_user(user)  # second passage : déjà notifié

    assert len(created) == 1
    assert created[0][1]["title"] == "Disponible : X T3"
    assert created[0][1]["dedup_key"] == "next_tome:x:3"
    assert emails == []  # pas d'e-mail en mode in_app
