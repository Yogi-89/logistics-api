"""Tests for application-layer hybrid encryption (RSA-AES and ECC-AES).

Covers the plaintext baseline, both encrypted schemes, tamper detection and the batch
endpoint. The database and API-key lookup are mocked so the tests stay hermetic.
"""

import base64
import json
from unittest.mock import MagicMock

import pytest
from fastapi.testclient import TestClient

from app.database import get_db
from app.main import app
from app.utils import hybrid_crypto
from app.utils.api_key_auth import validate_api_key

client = TestClient(app)

API_KEY_HEADER = {"X-API-Key": "test-api-key"}

SHIPMENT = {
    "courier_id": 1,
    "origin_city_id": 1,
    "destination_city_id": 2,
    "service_type": "REG",
    "weight_gram": 1000,
    "insurance_value": 0,
    "sender_name": "Yogi",
    "sender_phone": "081234567890",
    "sender_address": "Jl. Pengirim No. 1, Sidoarjo",
    "receiver_name": "Budi",
    "receiver_phone": "081298765432",
    "receiver_address": "Jl. Penerima No. 2, Jakarta",
}


@pytest.fixture(autouse=True)
def mock_dependencies():
    # Preserve overrides other test modules install at import time (e.g. test_main.py);
    # clearing the dict outright would leak into their tests.
    original = dict(app.dependency_overrides)
    db = MagicMock()
    db.add.return_value = None
    db.commit.return_value = None
    db.refresh.return_value = None

    app.dependency_overrides[get_db] = lambda: db
    app.dependency_overrides[validate_api_key] = lambda: MagicMock()
    yield
    app.dependency_overrides.clear()
    app.dependency_overrides.update(original)


def _plain_post(payload):
    return client.post("/v1/shipments", json=payload, headers=API_KEY_HEADER)


def _encrypted_post(wrapper, scheme):
    headers = {**API_KEY_HEADER, "X-Encryption-Scheme": scheme}
    return client.post("/v1/shipments", json=wrapper, headers=headers)


def test_plaintext_shipment_still_works():
    response = _plain_post(SHIPMENT)
    assert response.status_code == 200, response.text
    assert response.json()["awb"].startswith("SS-REG-")
    # No decryption happened, so the metrics headers must be absent.
    assert "x-server-decrypt-ms" not in response.headers


def test_none_scheme_header_behaves_like_plaintext():
    response = client.post(
        "/v1/shipments",
        json=SHIPMENT,
        headers={**API_KEY_HEADER, "X-Encryption-Scheme": "NONE"},
    )
    assert response.status_code == 200, response.text


def test_rsa_aes_shipment_decrypts_and_creates_awb():
    wrapper = hybrid_crypto.encrypt_rsa_aes(json.dumps(SHIPMENT).encode())
    response = _encrypted_post(wrapper, "RSA-AES")

    assert response.status_code == 200, response.text
    assert response.json()["awb"].startswith("SS-REG-")
    assert float(response.headers["x-server-decrypt-ms"]) >= 0
    assert int(response.headers["x-decrypted-bytes"]) == len(json.dumps(SHIPMENT).encode())


def test_ecc_aes_shipment_decrypts_and_creates_awb():
    wrapper = hybrid_crypto.encrypt_ecc_aes(json.dumps(SHIPMENT).encode())
    response = _encrypted_post(wrapper, "ECC-AES")

    assert response.status_code == 200, response.text
    assert response.json()["awb"].startswith("SS-REG-")
    assert int(response.headers["x-decrypted-bytes"]) > 0


def test_tampered_ciphertext_is_rejected():
    wrapper = hybrid_crypto.encrypt_rsa_aes(json.dumps(SHIPMENT).encode())
    raw = bytearray(base64.b64decode(wrapper["ciphertext"]))
    raw[0] ^= 0xFF
    wrapper["ciphertext"] = base64.b64encode(bytes(raw)).decode()

    response = _encrypted_post(wrapper, "RSA-AES")
    assert response.status_code == 400
    assert response.json()["detail"] == hybrid_crypto.DECRYPTION_ERROR_DETAIL


def test_tampered_ecc_ciphertext_is_rejected():
    wrapper = hybrid_crypto.encrypt_ecc_aes(json.dumps(SHIPMENT).encode())
    raw = bytearray(base64.b64decode(wrapper["ciphertext"]))
    raw[-1] ^= 0x01  # corrupt the GCM tag
    wrapper["ciphertext"] = base64.b64encode(bytes(raw)).decode()

    response = _encrypted_post(wrapper, "ECC-AES")
    assert response.status_code == 400
    assert response.json()["detail"] == hybrid_crypto.DECRYPTION_ERROR_DETAIL


def test_unknown_scheme_is_rejected():
    response = _encrypted_post({"encrypted_key": "", "nonce": "", "ciphertext": ""}, "AES-ROT13")
    assert response.status_code == 400
    assert "Unsupported encryption scheme" in response.json()["detail"]


def test_batch_shipments_returns_all_awbs():
    payload = [{**SHIPMENT} for _ in range(3)]
    response = client.post("/v1/shipments/batch", json=payload, headers=API_KEY_HEADER)

    assert response.status_code == 200, response.text
    body = response.json()
    assert body["count"] == 3
    assert len(body["shipments"]) == 3
    assert all(item["awb"].startswith("SS-REG-") for item in body["shipments"])


def test_batch_is_also_decrypted():
    payload = [{**SHIPMENT} for _ in range(10)]
    wrapper = hybrid_crypto.encrypt_ecc_aes(json.dumps(payload).encode())
    headers = {**API_KEY_HEADER, "X-Encryption-Scheme": "ECC-AES"}

    response = client.post("/v1/shipments/batch", json=wrapper, headers=headers)
    assert response.status_code == 200, response.text
    assert response.json()["count"] == 10


def test_public_keys_endpoint_exposes_both_keys():
    response = client.get("/v1/security/public-keys", headers=API_KEY_HEADER)

    assert response.status_code == 200, response.text
    body = response.json()
    assert "BEGIN PUBLIC KEY" in body["rsa_public_key_pem"]
    assert "BEGIN PUBLIC KEY" in body["ecc_public_key_pem"]
    assert body["supported_schemes"] == ["NONE", "RSA-AES", "ECC-AES"]
    assert body["ecc_curve"] == "SECP256R1"
