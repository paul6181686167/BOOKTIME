"""Limitation de débit en mémoire (fenêtre glissante), sans dépendance externe.

Suffisant pour une instance unique (Render, un seul processus). Avec plusieurs instances, chaque
processus compte de son côté : il faudrait alors un stockage partagé (Redis).

Usage :
    limiter = RateLimiter(max_events=10, window_seconds=900)
    limiter.check("login:ip:1.2.3.4")          # lève 429 si la limite est atteinte (compte l'appel)
    limiter.hit("login:email:a@b.c")            # enregistre un événement (ex. un échec)
    limiter.blocked("login:email:a@b.c")        # vrai si la limite est atteinte (ne compte pas)
    limiter.reset("login:email:a@b.c")          # efface (ex. connexion réussie)
"""
from __future__ import annotations

import os
import threading
import time
from collections import deque
from typing import Deque, Dict, Optional

from fastapi import HTTPException, Request, status

_MAX_KEYS = 20000  # garde-fou mémoire


class RateLimiter:
    def __init__(self, max_events: int, window_seconds: int, message: Optional[str] = None):
        self.max_events = max_events
        self.window = window_seconds
        self.message = message or "Trop de tentatives. Réessaie dans quelques minutes."
        self._events: Dict[str, Deque[float]] = {}
        self._lock = threading.Lock()

    def _prune(self, key: str, now: float) -> Deque[float]:
        queue = self._events.get(key)
        if queue is None:
            queue = deque()
            self._events[key] = queue
        cutoff = now - self.window
        while queue and queue[0] <= cutoff:
            queue.popleft()
        return queue

    def _gc(self, now: float) -> None:
        if len(self._events) <= _MAX_KEYS:
            return
        cutoff = now - self.window
        for key in [k for k, q in self._events.items() if not q or q[-1] <= cutoff]:
            self._events.pop(key, None)

    def blocked(self, key: str) -> bool:
        now = time.monotonic()
        with self._lock:
            return len(self._prune(key, now)) >= self.max_events

    def retry_after(self, key: str) -> int:
        now = time.monotonic()
        with self._lock:
            queue = self._prune(key, now)
            if len(queue) < self.max_events:
                return 0
            return max(1, int(queue[0] + self.window - now) + 1)

    def hit(self, key: str) -> None:
        now = time.monotonic()
        with self._lock:
            self._prune(key, now).append(now)
            self._gc(now)

    def reset(self, key: str) -> None:
        with self._lock:
            self._events.pop(key, None)

    def check(self, key: str) -> None:
        """Compte l'appel ; lève une erreur 429 si la limite est déjà atteinte."""
        now = time.monotonic()
        with self._lock:
            queue = self._prune(key, now)
            if len(queue) >= self.max_events:
                retry = max(1, int(queue[0] + self.window - now) + 1)
                raise HTTPException(
                    status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                    detail=self.message,
                    headers={"Retry-After": str(retry)},
                )
            queue.append(now)
            self._gc(now)

    def raise_if_blocked(self, key: str) -> None:
        if self.blocked(key):
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail=self.message,
                headers={"Retry-After": str(self.retry_after(key))},
            )


def rate_limiting_enabled() -> bool:
    """Désactivable pour les tests (RATE_LIMIT_ENABLED=false) ; actif par défaut."""
    return os.getenv("RATE_LIMIT_ENABLED", "true").strip().lower() != "false"


def client_ip(request: Optional[Request]) -> str:
    """Adresse du client : première entrée de X-Forwarded-For (proxy Render), sinon le socket."""
    if request is None:
        return "unknown"
    forwarded = request.headers.get("x-forwarded-for", "")
    if forwarded:
        first = forwarded.split(",")[0].strip()
        if first:
            return first[:64]
    return request.client.host if request.client else "unknown"


def ip_rate_limit(name: str, max_events: int, window_seconds: int, message: Optional[str] = None):
    """Dépendance FastAPI : limite par adresse IP pour une famille de routes."""
    limiter = RateLimiter(max_events, window_seconds, message)

    def dependency(request: Request) -> None:
        if not rate_limiting_enabled():
            return
        limiter.check(f"{name}:{client_ip(request)}")

    dependency.limiter = limiter  # type: ignore[attr-defined]
    return dependency
