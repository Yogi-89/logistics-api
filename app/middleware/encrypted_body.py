"""Decrypt application-layer encrypted request bodies before routing.

Encryption has to happen *before* Pydantic validation, so this is an ASGI middleware rather
than a per-route dependency: it reads the raw body, replaces it with the plaintext and lets
FastAPI parse it normally. That keeps the OpenAPI schema, request models and existing
validators untouched, and it lets every protected route report the same decryption metrics.

Protection is opt-in per request: no ``X-Encryption-Scheme`` header (or ``NONE``) means the
body is forwarded unchanged, preserving the plaintext baseline.
"""

from __future__ import annotations

import time
from typing import Iterable

from fastapi.responses import JSONResponse

from app.utils.hybrid_crypto import (
    DECRYPTION_ERROR_DETAIL,
    SUPPORTED_SCHEMES,
    PayloadDecryptionError,
    decrypt_payload,
)

SCHEME_HEADER = b"x-encryption-scheme"
DECRYPT_MS_HEADER = b"x-server-decrypt-ms"
DECRYPTED_BYTES_HEADER = b"x-decrypted-bytes"


class EncryptedBodyMiddleware:
    """Decrypt ``{encrypted_key, nonce, ciphertext}`` bodies for the configured paths."""

    def __init__(self, app, protected_paths: Iterable[str] = ()) -> None:
        self.app = app
        self.protected_paths = frozenset(protected_paths)

    async def __call__(self, scope, receive, send):
        if not self._is_protected(scope):
            await self.app(scope, receive, send)
            return

        headers = {key.lower(): value for key, value in scope.get("headers", [])}
        scheme = (headers.get(SCHEME_HEADER) or b"NONE").decode("latin-1").strip().upper()

        if scheme in ("", "NONE"):
            await self.app(scope, receive, send)
            return

        if scheme not in SUPPORTED_SCHEMES:
            await self._fail(scope, receive, send, f"Unsupported encryption scheme: {scheme}")
            return

        body = await self._read_body(receive)
        started = time.perf_counter()
        try:
            plaintext = decrypt_payload(scheme, body)
        except PayloadDecryptionError:
            await self._fail(scope, receive, send, DECRYPTION_ERROR_DETAIL)
            return
        elapsed_ms = (time.perf_counter() - started) * 1000.0

        scope["headers"] = [
            (b"content-length", str(len(plaintext)).encode("latin-1"))
            if key.lower() == b"content-length"
            else (key, value)
            for key, value in scope.get("headers", [])
        ]

        replayed = False

        async def replay_receive():
            nonlocal replayed
            if replayed:
                return {"type": "http.disconnect"}
            replayed = True
            return {"type": "http.request", "body": plaintext, "more_body": False}

        async def send_with_metrics(message):
            if message["type"] == "http.response.start":
                message.setdefault("headers", [])
                message["headers"] = list(message["headers"]) + [
                    (DECRYPT_MS_HEADER, f"{elapsed_ms:.3f}".encode("latin-1")),
                    (DECRYPTED_BYTES_HEADER, str(len(plaintext)).encode("latin-1")),
                ]
            await send(message)

        await self.app(scope, replay_receive, send_with_metrics)

    def _is_protected(self, scope) -> bool:
        return (
            scope.get("type") == "http"
            and scope.get("method") == "POST"
            and scope.get("path") in self.protected_paths
        )

    @staticmethod
    async def _read_body(receive) -> bytes:
        chunks = []
        more_body = True
        while more_body:
            message = await receive()
            if message["type"] == "http.disconnect":
                break
            chunks.append(message.get("body", b""))
            more_body = message.get("more_body", False)
        return b"".join(chunks)

    @staticmethod
    async def _fail(scope, receive, send, detail: str) -> None:
        response = JSONResponse({"detail": detail}, status_code=400)
        await response(scope, receive, send)
