"""Tests de durcissement : limitation de débit, mots de passe, jetons, CORS, index, erreurs."""

import importlib
import logging
from datetime import datetime, timedelta

import pytest
from fastapi import HTTPException
from httpx import AsyncClient

from app.database.connection import users_collection
from app.security.rate_limit import RateLimiter, client_ip, ip_rate_limit
from app.security.jwt import token_revoked
from app.utils.timeutils import to_epoch, utcnow


# --------------------------------------------------------------------------- limiteur de débit
class TestRateLimiter:
    def test_blocks_after_limit_and_resets(self):
        limiter = RateLimiter(3, 60)
        for _ in range(3):
            limiter.check("k")
        with pytest.raises(HTTPException) as exc:
            limiter.check("k")
        assert exc.value.status_code == 429
        assert int(exc.value.headers["Retry-After"]) >= 1
        limiter.reset("k")
        limiter.check("k")  # de nouveau possible

    def test_keys_are_independent(self):
        limiter = RateLimiter(1, 60)
        limiter.check("a")
        limiter.check("b")
        assert limiter.blocked("a") and limiter.blocked("b")
        assert not limiter.blocked("c")

    def test_window_expires(self, monkeypatch):
        import app.security.rate_limit as rl

        now = [1000.0]
        monkeypatch.setattr(rl.time, "monotonic", lambda: now[0])
        limiter = RateLimiter(1, 10)
        limiter.hit("k")
        assert limiter.blocked("k")
        now[0] += 11
        assert not limiter.blocked("k")

    def test_client_ip_uses_first_forwarded_address(self):
        class Req:
            headers = {"x-forwarded-for": "1.2.3.4, 10.0.0.1"}
            client = None

        assert client_ip(Req()) == "1.2.3.4"

    def test_ip_dependency_can_be_disabled(self, monkeypatch):
        dep = ip_rate_limit("t-disabled", 1, 60)

        class Req:
            headers = {}
            client = None

        monkeypatch.setenv("RATE_LIMIT_ENABLED", "false")
        for _ in range(5):
            dep(Req())
        monkeypatch.setenv("RATE_LIMIT_ENABLED", "true")
        dep(Req())
        with pytest.raises(HTTPException):
            dep(Req())


# --------------------------------------------------------------------------- mots de passe
class TestPasswordRules:
    @pytest.mark.asyncio
    async def test_register_rejects_short_password(self, test_client: AsyncClient, unique_email: str):
        r = await test_client.post(
            "/api/auth/register",
            json={"email": unique_email, "password": "abc12", "accept_terms": True},
        )
        assert r.status_code in (400, 422)

    @pytest.mark.asyncio
    async def test_register_rejects_password_over_72_bytes(
        self, test_client: AsyncClient, unique_email: str
    ):
        r = await test_client.post(
            "/api/auth/register",
            json={"email": unique_email, "password": "é" * 40, "accept_terms": True},  # 80 octets
        )
        assert r.status_code == 400  # et non une erreur 500 de bcrypt

    @pytest.mark.asyncio
    async def test_login_with_overlong_password_is_a_clean_error(
        self, test_client: AsyncClient, registered_user: dict
    ):
        r = await test_client.post(
            "/api/auth/login",
            json={"email": registered_user["email"], "password": "x" * 200},
        )
        assert r.status_code == 400  # "Email ou mot de passe incorrect", pas une erreur 500


# --------------------------------------------------------------------------- sessions révoquées
class TestTokenRevocation:
    def test_token_revoked_logic(self):
        changed = datetime(2026, 1, 1, 12, 0, 0)
        epoch = to_epoch(changed)
        assert not token_revoked({"iat": epoch - 5}, {})  # jamais changé
        assert token_revoked({"iat": epoch - 5}, {"password_changed_at": changed})
        assert not token_revoked({"iat": epoch + 5}, {"password_changed_at": changed})
        assert token_revoked({}, {"password_changed_at": changed})  # ancien jeton sans iat

    @pytest.mark.asyncio
    async def test_old_token_rejected_after_password_change(
        self, test_client: AsyncClient, registered_user: dict, auth_headers: dict
    ):
        assert (await test_client.get("/api/auth/me", headers=auth_headers)).status_code == 200
        users_collection.update_one(
            {"email": registered_user["email"].lower()},
            {"$set": {"password_changed_at": utcnow() + timedelta(seconds=30)}},
        )
        r = await test_client.get("/api/auth/me", headers=auth_headers)
        assert r.status_code == 401

    @pytest.mark.asyncio
    async def test_change_password_returns_working_new_token(
        self, test_client: AsyncClient, registered_user: dict, auth_headers: dict
    ):
        r = await test_client.post(
            "/api/auth/change-password",
            json={"current_password": registered_user["password"], "new_password": "NouveauMdp#2026"},
            headers=auth_headers,
        )
        assert r.status_code == 200, r.text
        new_token = r.json()["access_token"]
        me = await test_client.get("/api/auth/me", headers={"Authorization": f"Bearer {new_token}"})
        assert me.status_code == 200


# --------------------------------------------------------------------------- réinitialisation
class TestPasswordReset:
    @pytest.fixture
    def captured_mail(self, monkeypatch):
        from app.auth import routes as auth_routes

        sent = []
        monkeypatch.setattr(auth_routes, "_email_configured", lambda: True)
        monkeypatch.setattr(
            auth_routes, "_send_reset_email", lambda to, token, url: sent.append((to, token))
        )
        return sent

    @pytest.mark.asyncio
    async def test_response_is_identical_for_unknown_and_known_accounts(
        self, test_client: AsyncClient, registered_user: dict, captured_mail
    ):
        known = await test_client.post(
            "/api/auth/forgot-password", json={"email": registered_user["email"]}
        )
        unknown = await test_client.post(
            "/api/auth/forgot-password", json={"email": "personne-ici@example.com"}
        )
        assert known.status_code == unknown.status_code == 200
        assert known.json() == unknown.json()
        assert len(captured_mail) == 1  # seul le compte existant reçoit un e-mail

    @pytest.mark.asyncio
    async def test_reset_token_is_stored_hashed_and_single_use(
        self, test_client: AsyncClient, registered_user: dict, captured_mail
    ):
        await test_client.post("/api/auth/forgot-password", json={"email": registered_user["email"]})
        _, token = captured_mail[0]

        stored = users_collection.find_one({"email": registered_user["email"].lower()}, {"_id": 0})
        assert stored["reset_token"] != token  # jamais en clair en base

        ok = await test_client.post(
            "/api/auth/reset-password", json={"token": token, "new_password": "ApresReset#2026"}
        )
        assert ok.status_code == 200, ok.text
        again = await test_client.post(
            "/api/auth/reset-password", json={"token": token, "new_password": "EncoreUn#2026"}
        )
        assert again.status_code == 400

        login = await test_client.post(
            "/api/auth/login",
            json={"email": registered_user["email"], "password": "ApresReset#2026"},
        )
        assert login.status_code == 200

    @pytest.mark.asyncio
    async def test_reset_rejects_weak_password(
        self, test_client: AsyncClient, registered_user: dict, captured_mail
    ):
        await test_client.post("/api/auth/forgot-password", json={"email": registered_user["email"]})
        _, token = captured_mail[0]
        r = await test_client.post(
            "/api/auth/reset-password", json={"token": token, "new_password": "court"}
        )
        assert r.status_code in (400, 422)


# --------------------------------------------------------------------------- CORS
class TestCors:
    def test_known_and_preview_origins_allowed(self):
        from app.security.cors import is_origin_allowed

        assert is_origin_allowed("https://booktime-fawn.vercel.app")
        assert is_origin_allowed("capacitor://localhost")
        assert is_origin_allowed("https://booktime-git-feature-paul6181686167s-projects.vercel.app")

    def test_foreign_vercel_origins_rejected(self):
        from app.security.cors import is_origin_allowed

        assert not is_origin_allowed("https://evil.vercel.app")
        assert not is_origin_allowed("https://x-paul6181686167s-projects.vercel.app.evil.com")
        assert not is_origin_allowed(None)

    @pytest.mark.asyncio
    async def test_preflight_from_evil_origin_has_no_allow_header(self, test_client: AsyncClient):
        r = await test_client.options(
            "/api/auth/login",
            headers={"Origin": "https://evil.vercel.app", "Access-Control-Request-Method": "POST"},
        )
        assert "access-control-allow-origin" not in {k.lower() for k in r.headers}

    @pytest.mark.asyncio
    async def test_error_responses_keep_cors_for_allowed_origin(self, test_client: AsyncClient):
        r = await test_client.get(
            "/api/auth/me", headers={"Origin": "https://booktime-fawn.vercel.app"}
        )
        assert r.status_code in (401, 403)
        assert r.headers.get("access-control-allow-origin") == "https://booktime-fawn.vercel.app"


# --------------------------------------------------------------------------- production
class TestProductionGuards:
    def test_missing_secret_key_refused_in_production(self, monkeypatch):
        import app.config as config

        monkeypatch.setattr("dotenv.load_dotenv", lambda *a, **k: False)  # ignorer backend/.env
        monkeypatch.setenv("ENVIRONMENT", "production")
        monkeypatch.delenv("SECRET_KEY", raising=False)
        try:
            with pytest.raises(RuntimeError):
                importlib.reload(config)
        finally:
            monkeypatch.undo()
            importlib.reload(config)

    def test_public_error_hides_details_outside_development(self, monkeypatch, caplog):
        from app.utils.errors import public_error

        monkeypatch.setenv("ENVIRONMENT", "production")
        with caplog.at_level(logging.ERROR, logger="booktime.errors"):
            text = public_error(ValueError("mongodb://user:secret@host"), "Erreur de test")
        assert text == "Erreur de test"
        assert "secret" not in text
        assert "secret" in caplog.text  # le détail reste dans les journaux serveur

    def test_public_error_shows_details_in_development(self, monkeypatch):
        from app.utils.errors import public_error

        monkeypatch.setenv("ENVIRONMENT", "development")
        assert "boom" in public_error(ValueError("boom"), "Erreur")


# --------------------------------------------------------------------------- index
class TestIndexes:
    def test_ensure_indexes_creates_every_index_and_survives_errors(self):
        from app.database.indexes import INDEXES, ensure_indexes

        calls = []

        class Coll:
            def __init__(self, name):
                self.name = name

            def create_index(self, keys, **options):
                calls.append((self.name, keys, options))
                if self.name == "notifications":
                    raise RuntimeError("index conflict")

        class Db:
            db = {}

            def is_mock_mode(self):
                return False

        db = Db()
        db.db = {name: Coll(name) for name, _, _ in INDEXES}
        result = ensure_indexes(db)

        assert len(calls) == len(INDEXES)
        assert result["failed"] == 1
        assert result["created_or_present"] == len(INDEXES) - 1
        assert ("users", "email", {"unique": True, "sparse": True}) in calls

    def test_ensure_indexes_skipped_in_mock_mode(self):
        from app.database.indexes import ensure_indexes

        class Db:
            def is_mock_mode(self):
                return True

        assert ensure_indexes(Db()) == {"created_or_present": 0, "failed": 0}


# --------------------------------------------------------------------------- routes sensibles
class TestSensitiveRoutes:
    @pytest.mark.asyncio
    async def test_monitoring_requires_valid_payload_and_truncates(self, test_client: AsyncClient):
        ok = await test_client.post(
            "/api/monitoring/errors", json={"message": "Boom", "stack": "x" * 100}
        )
        assert ok.status_code in (200, 202, 204)
        too_big = await test_client.post("/api/monitoring/errors", json={"message": "m" * 100000})
        assert too_big.status_code == 422

    @pytest.mark.asyncio
    async def test_enrich_series_needs_admin(
        self, test_client: AsyncClient, auth_headers: dict
    ):
        anonymous = await test_client.post("/api/wikipedia/enrich-series")
        assert anonymous.status_code in (401, 403)
        normal_user = await test_client.post("/api/wikipedia/enrich-series", headers=auth_headers)
        assert normal_user.status_code == 403
        status = await test_client.get("/api/wikipedia/enrich-series/status", headers=auth_headers)
        assert status.status_code == 403

    @pytest.mark.asyncio
    async def test_debug_routes_removed(self, test_client: AsyncClient):
        for path in ("/api/wikidata/test/rowling", "/api/wikipedia/test/rowling"):
            assert (await test_client.get(path)).status_code == 404


# --------------------------------------------------------------------------- recherche
class TestRegexEscaping:
    @pytest.mark.asyncio
    async def test_special_characters_in_search_do_not_crash(
        self, test_client: AsyncClient, auth_headers: dict
    ):
        for q in ("(", "[a-", ".*", "a{2,1}", "\\"):
            r = await test_client.get("/api/books", params={"search": q}, headers=auth_headers)
            assert r.status_code != 500, (q, r.text)
