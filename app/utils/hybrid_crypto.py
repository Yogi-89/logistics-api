"""Application-layer hybrid encryption for API payloads.

Two schemes are supported, both wrapping an AES-256-GCM key:

``RSA-AES``
    The client generates a random 32-byte AES key, encrypts it with the server's RSA-2048
    public key using OAEP/SHA-256, and sends the AES-GCM nonce + ciphertext alongside it.

``ECC-AES`` (ECIES)
    The client generates an ephemeral P-256 key pair, performs ECDH with the server's
    public key, derives a 32-byte key with HKDF-SHA256 and encrypts the payload with
    AES-256-GCM. ``encrypted_key`` carries the ephemeral *public* key.

Wire format (JSON body, base64 values)::

    {
      "encrypted_key": "<base64>",
      "nonce": "<base64, 12 bytes>",
      "ciphertext": "<base64, AES-GCM ciphertext || tag>"
    }

Keys are read from ``RSA_PRIVATE_KEY_PEM`` / ``ECC_PRIVATE_KEY_PEM`` when set, otherwise
from ``KEYS_DIR`` (default ``<repo>/keys``). Missing keys are generated on first use so a
fresh checkout or a Render deploy works without manual provisioning.

This module is intentionally free of FastAPI imports; the ASGI middleware in
``app.middleware.encrypted_body`` is what applies it to HTTP requests.
"""

from __future__ import annotations

import base64
import binascii
import json
import os
import threading
from pathlib import Path
from typing import Any, Dict, Optional, Tuple

from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import ec, padding, rsa
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from cryptography.hazmat.primitives.kdf.hkdf import HKDF

RSA_KEY_SIZE = 2048
ECC_CURVE_NAME = "SECP256R1"
AES_KEY_BYTES = 32
GCM_NONCE_BYTES = 12
# Domain separation for the ECIES KDF; clients must use the same value.
HKDF_INFO = b"shipstream-ecc-aes-v1"

SUPPORTED_SCHEMES = ("NONE", "RSA-AES", "ECC-AES")
DECRYPTION_ERROR_DETAIL = "Payload decryption or integrity check failed"

_RSA_ENV = "RSA_PRIVATE_KEY_PEM"
_ECC_ENV = "ECC_PRIVATE_KEY_PEM"
_RSA_FILE = "rsa_private.pem"
_ECC_FILE = "ecc_private.pem"

_lock = threading.Lock()
_cache: Dict[str, Any] = {}


class PayloadDecryptionError(Exception):
    """Raised when an encrypted payload cannot be decoded, unwrapped or authenticated."""


# ---------------------------------------------------------------------------
# Key management
# ---------------------------------------------------------------------------

def keys_dir() -> Path:
    """Directory holding the generated PEM files (override with ``KEYS_DIR``)."""
    configured = os.getenv("KEYS_DIR")
    if configured:
        return Path(configured)
    return Path(__file__).resolve().parents[2] / "keys"


def _rsa_private_key() -> rsa.RSAPrivateKey:
    pem = os.getenv(_RSA_ENV)
    if pem:
        return serialization.load_pem_private_key(pem.encode("utf-8"), password=None)
    return _load_or_generate(_RSA_FILE, lambda: rsa.generate_private_key(public_exponent=65537, key_size=RSA_KEY_SIZE))


def _ecc_private_key() -> ec.EllipticCurvePrivateKey:
    pem = os.getenv(_ECC_ENV)
    if pem:
        return serialization.load_pem_private_key(pem.encode("utf-8"), password=None)
    return _load_or_generate(_ECC_FILE, lambda: ec.generate_private_key(ec.SECP256R1()))


def _load_or_generate(filename: str, factory) -> Any:
    directory = keys_dir()
    path = directory / filename
    if path.exists():
        return serialization.load_pem_private_key(path.read_bytes(), password=None)

    directory.mkdir(parents=True, exist_ok=True)
    key = factory()
    pem = key.private_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PrivateFormat.PKCS8,
        encryption_algorithm=serialization.NoEncryption(),
    )
    path.write_bytes(pem)
    try:  # best effort on POSIX; Windows ignores chmod
        path.chmod(0o600)
    except OSError:
        pass
    return key


def get_rsa_private_key() -> rsa.RSAPrivateKey:
    with _lock:
        if "rsa_private" not in _cache:
            _cache["rsa_private"] = _rsa_private_key()
        return _cache["rsa_private"]


def get_ecc_private_key() -> ec.EllipticCurvePrivateKey:
    with _lock:
        if "ecc_private" not in _cache:
            _cache["ecc_private"] = _ecc_private_key()
        return _cache["ecc_private"]


def public_pem(key) -> str:
    """Serialise a public key as PEM (SubjectPublicKeyInfo)."""
    return key.public_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PublicFormat.SubjectPublicKeyInfo,
    ).decode("utf-8")


def get_public_keys() -> Dict[str, str]:
    """PEM-encoded public keys handed to API clients."""
    return {
        "rsa_public_key_pem": public_pem(get_rsa_private_key().public_key()),
        "ecc_public_key_pem": public_pem(get_ecc_private_key().public_key()),
        "rsa_key_size": str(RSA_KEY_SIZE),
        "ecc_curve": ECC_CURVE_NAME,
    }


# ---------------------------------------------------------------------------
# Decryption
# ---------------------------------------------------------------------------

def _b64decode(value: str, field: str) -> bytes:
    try:
        return base64.b64decode(value, validate=False)
    except (binascii.Error, ValueError, TypeError) as exc:
        raise PayloadDecryptionError(f"invalid base64 in {field}") from exc


def _parse_wrapper(body: bytes) -> Tuple[bytes, bytes, bytes]:
    try:
        wrapper = json.loads(body.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise PayloadDecryptionError("encrypted body is not valid JSON") from exc

    if not isinstance(wrapper, dict):
        raise PayloadDecryptionError("encrypted body must be a JSON object")

    try:
        encrypted_key = _b64decode(wrapper["encrypted_key"], "encrypted_key")
        nonce = _b64decode(wrapper["nonce"], "nonce")
        ciphertext = _b64decode(wrapper["ciphertext"], "ciphertext")
    except KeyError as exc:
        raise PayloadDecryptionError(f"missing field {exc}") from exc

    if len(nonce) != GCM_NONCE_BYTES:
        raise PayloadDecryptionError("nonce must be 12 bytes")
    if not ciphertext:
        raise PayloadDecryptionError("ciphertext is empty")
    return encrypted_key, nonce, ciphertext


def _load_ephemeral_public_key(raw: bytes) -> ec.EllipticCurvePublicKey:
    """Accept an uncompressed point (65 bytes), DER SPKI, or a PEM string."""
    if len(raw) == 65 and raw[0] == 0x04:
        return ec.EllipticCurvePublicKey.from_encoded_point(ec.SECP256R1(), raw)
    if raw.startswith(b"-----BEGIN"):
        return serialization.load_pem_public_key(raw)
    try:
        return serialization.load_der_public_key(raw)
    except ValueError as exc:
        raise PayloadDecryptionError("unsupported ephemeral public key encoding") from exc


def _unwrap_aes_key(scheme: str, encrypted_key: bytes) -> bytes:
    if scheme == "RSA-AES":
        try:
            return get_rsa_private_key().decrypt(
                encrypted_key,
                padding.OAEP(
                    mgf=padding.MGF1(algorithm=hashes.SHA256()),
                    algorithm=hashes.SHA256(),
                    label=None,
                ),
            )
        except ValueError as exc:
            raise PayloadDecryptionError("RSA key unwrap failed") from exc

    peer = _load_ephemeral_public_key(encrypted_key)
    try:
        shared_secret = get_ecc_private_key().exchange(ec.ECDH(), peer)
    except ValueError as exc:
        raise PayloadDecryptionError("ECDH exchange failed") from exc

    return HKDF(
        algorithm=hashes.SHA256(),
        length=AES_KEY_BYTES,
        salt=None,
        info=HKDF_INFO,
    ).derive(shared_secret)


def decrypt_payload(scheme: str, body: bytes) -> bytes:
    """Decrypt ``body`` for ``scheme`` (``RSA-AES`` or ``ECC-AES``)."""
    normalized = (scheme or "").strip().upper()
    if normalized not in ("RSA-AES", "ECC-AES"):
        raise PayloadDecryptionError(f"unsupported scheme: {scheme}")

    encrypted_key, nonce, ciphertext = _parse_wrapper(body)
    aes_key = _unwrap_aes_key(normalized, encrypted_key)
    if len(aes_key) != AES_KEY_BYTES:
        raise PayloadDecryptionError("unwrapped key must be 32 bytes")

    try:
        return AESGCM(aes_key).decrypt(nonce, ciphertext, None)
    except Exception as exc:  # InvalidTag, ValueError
        raise PayloadDecryptionError("AES-GCM authentication failed") from exc


# ---------------------------------------------------------------------------
# Encryption helpers (clients, tests and integration examples)
# ---------------------------------------------------------------------------

def _transport(encrypted_key: bytes, nonce: bytes, ciphertext: bytes) -> Dict[str, str]:
    return {
        "encrypted_key": base64.b64encode(encrypted_key).decode("ascii"),
        "nonce": base64.b64encode(nonce).decode("ascii"),
        "ciphertext": base64.b64encode(ciphertext).decode("ascii"),
    }


def encrypt_rsa_aes(plaintext: bytes, rsa_public_key_pem: Optional[str] = None) -> Dict[str, str]:
    """Client-side helper: wrap ``plaintext`` for the server's RSA public key."""
    if rsa_public_key_pem is None:
        rsa_public_key_pem = public_pem(get_rsa_private_key().public_key())
    public_key = serialization.load_pem_public_key(rsa_public_key_pem.encode("utf-8"))

    aes_key = AESGCM.generate_key(bit_length=AES_KEY_BYTES * 8)
    nonce = os.urandom(GCM_NONCE_BYTES)
    ciphertext = AESGCM(aes_key).encrypt(nonce, plaintext, None)
    encrypted_key = public_key.encrypt(
        aes_key,
        padding.OAEP(
            mgf=padding.MGF1(algorithm=hashes.SHA256()),
            algorithm=hashes.SHA256(),
            label=None,
        ),
    )
    return _transport(encrypted_key, nonce, ciphertext)


def encrypt_ecc_aes(plaintext: bytes, ecc_public_key_pem: Optional[str] = None) -> Dict[str, str]:
    """Client-side helper: ECIES-wrap ``plaintext`` for the server's P-256 public key."""
    if ecc_public_key_pem is None:
        ecc_public_key_pem = public_pem(get_ecc_private_key().public_key())
    server_public = serialization.load_pem_public_key(ecc_public_key_pem.encode("utf-8"))

    ephemeral_private = ec.generate_private_key(ec.SECP256R1())
    shared_secret = ephemeral_private.exchange(ec.ECDH(), server_public)
    aes_key = HKDF(
        algorithm=hashes.SHA256(),
        length=AES_KEY_BYTES,
        salt=None,
        info=HKDF_INFO,
    ).derive(shared_secret)

    nonce = os.urandom(GCM_NONCE_BYTES)
    ciphertext = AESGCM(aes_key).encrypt(nonce, plaintext, None)
    ephemeral_public = ephemeral_private.public_key().public_bytes(
        encoding=serialization.Encoding.X962,
        format=serialization.PublicFormat.UncompressedPoint,
    )
    return _transport(ephemeral_public, nonce, ciphertext)


def encrypt_request(payload: Dict[str, Any], scheme: str) -> Dict[str, str]:
    """Convenience wrapper: JSON-encode ``payload`` then encrypt it."""
    normalized = scheme.strip().upper()
    raw = json.dumps(payload).encode("utf-8")
    if normalized == "RSA-AES":
        return encrypt_rsa_aes(raw)
    if normalized == "ECC-AES":
        return encrypt_ecc_aes(raw)
    raise ValueError(f"unsupported scheme: {scheme}")
