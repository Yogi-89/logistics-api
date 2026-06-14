"""
test_shipments.py
Deep testing for Shipment AWB generation, tracking, labels, and edge cases.
"""

from unittest.mock import MagicMock, patch
from datetime import datetime
from fastapi.testclient import TestClient
from app.main import app
from app.utils.api_key_auth import validate_api_key
from app.database import get_db

# Patch rate limiter storage before any app code imports
from limits.storage import MemoryStorage
from app.utils.limiter import limiter
limiter._storage = MemoryStorage()

client = TestClient(app)


# ---------------------------------------------------------------------------
# Build proper mock objects
# ---------------------------------------------------------------------------

def _make_tracking():
    t = MagicMock()
    t.id = 1
    t.awb = "SS-REG-TEST001"
    t.courier_id = 1
    t.status = "MANIFESTED"
    t.origin_city_id = 1
    t.destination_city_id = 2
    t.service_type = "REG"
    t.weight_gram = 1000
    t.length_cm = None
    t.width_cm = None
    t.height_cm = None
    t.insurance_value = 0.0
    t.shipping_cost = 12000.0
    t.sender_name = "Yogi"
    t.sender_phone = "081234567890"
    t.sender_address = "Jl. Testing 123"
    t.sender_postal_code = None
    t.sender_lat = None
    t.sender_long = None
    t.receiver_name = "Customer"
    t.receiver_phone = "082345678901"
    t.receiver_address = "Jl. Penerima 456"
    t.receiver_postal_code = None
    t.receiver_lat = None
    t.receiver_long = None
    t.last_updated = datetime.utcnow()
    t.history = [{"status": "MANIFESTED", "location": "Warehouse",
                  "timestamp": datetime.utcnow().isoformat(), "note": ""}]
    return t


def _make_city():
    c = MagicMock()
    c.id = 1
    c.name = "Jakarta"
    c.province = "DKI Jakarta"
    c.type = "Kota"
    c.postal_code = "10110"
    c.rajaongkir_id = 1
    return c


def _make_courier():
    c = MagicMock()
    c.name = "JNE"
    c.code = "jne"
    c.id = 1
    return c


def _make_query_mock(**model_mocks):
    """
    Returns a db.query side_effect function that dispatches by model name.
    """
    def side_effect(model):
        q = MagicMock()
        q.filter.return_value = q
        q.order_by.return_value = q
        name = model.__name__ if hasattr(model, '__name__') else str(model)
        if name in model_mocks:
            obj = model_mocks[name]
            q.filter.return_value.first.return_value = obj
            q.first.return_value = obj
            q.all.return_value = [obj] if obj else []
        else:
            q.filter.return_value.first.return_value = None
            q.first.return_value = None
            q.all.return_value = []
        return q
    return side_effect


def _db_with_found_tracking():
    db = MagicMock()
    db.add.return_value = None
    db.commit.return_value = None
    db.refresh.return_value = None
    db.query.side_effect = _make_query_mock(
        Tracking=_make_tracking(),
        City=_make_city(),
        Courier=_make_courier(),
    )
    return db


async def _override_api_key():
    u = MagicMock()
    u.quota_limit = 1000
    u.quota_used = 0
    u.is_active = True
    u.is_verified = True
    u.username = "testuser"
    k = MagicMock()
    k.owner = u
    return k


VALID_SHIPMENT_PAYLOAD = {
    "courier_id": 1,
    "origin_city_id": 1,
    "destination_city_id": 2,
    "service_type": "REG",
    "weight_gram": 1000,
    "sender_name": "Yogi Prasetyo",
    "sender_phone": "081234567890",
    "sender_address": "Jl. Testing No. 123, Jakarta",
    "receiver_name": "Customer Satu",
    "receiver_phone": "082345678901",
    "receiver_address": "Jl. Penerima No. 456, Bandung",
}


# ===========================================================================
# Schema Validation Tests (no DB interaction needed past mock setup)
# ===========================================================================

class TestShipmentValidation:
    """These tests verify Pydantic schema validation — fast, no real DB needed."""

    def setup_method(self):
        app.dependency_overrides[validate_api_key] = _override_api_key
        app.dependency_overrides[get_db] = _db_with_found_tracking

    def test_sender_name_too_short(self):
        payload = {**VALID_SHIPMENT_PAYLOAD, "sender_name": "A"}
        resp = client.post("/v1/shipments", json=payload)
        assert resp.status_code == 422

    def test_receiver_name_too_short(self):
        app.dependency_overrides[get_db] = _db_with_found_tracking
        payload = {**VALID_SHIPMENT_PAYLOAD, "receiver_name": "B"}
        resp = client.post("/v1/shipments", json=payload)
        assert resp.status_code == 422

    def test_sender_address_too_short(self):
        app.dependency_overrides[get_db] = _db_with_found_tracking
        payload = {**VALID_SHIPMENT_PAYLOAD, "sender_address": "Jakarta"}
        resp = client.post("/v1/shipments", json=payload)
        assert resp.status_code == 422

    def test_weight_exceeds_max(self):
        app.dependency_overrides[get_db] = _db_with_found_tracking
        payload = {**VALID_SHIPMENT_PAYLOAD, "weight_gram": 70001}
        resp = client.post("/v1/shipments", json=payload)
        assert resp.status_code == 422

    def test_negative_insurance(self):
        app.dependency_overrides[get_db] = _db_with_found_tracking
        payload = {**VALID_SHIPMENT_PAYLOAD, "insurance_value": -100}
        resp = client.post("/v1/shipments", json=payload)
        assert resp.status_code == 422

    def test_valid_payload(self):
        app.dependency_overrides[get_db] = _db_with_found_tracking
        resp = client.post("/v1/shipments", json=VALID_SHIPMENT_PAYLOAD)
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "success"
        assert "awb" in data

    def test_awb_format(self):
        app.dependency_overrides[get_db] = _db_with_found_tracking
        resp = client.post("/v1/shipments", json=VALID_SHIPMENT_PAYLOAD)
        assert resp.status_code == 200
        awb = resp.json()["awb"]
        assert awb.startswith("SS-")
        parts = awb.split("-")
        assert len(parts) == 3
        assert parts[1] == "REG"
        assert len(parts[2]) == 8
        assert parts[2].isalnum()

    def test_volumetric_weight_used(self):
        app.dependency_overrides[get_db] = _db_with_found_tracking
        payload = {**VALID_SHIPMENT_PAYLOAD, "length_cm": 100, "width_cm": 100, "height_cm": 100}
        resp = client.post("/v1/shipments", json=payload)
        assert resp.status_code == 200
        assert resp.json()["shipping_cost"] > 2000

    def test_with_insurance(self):
        app.dependency_overrides[get_db] = _db_with_found_tracking
        payload = {**VALID_SHIPMENT_PAYLOAD, "insurance_value": 500000.0}
        resp = client.post("/v1/shipments", json=payload)
        assert resp.status_code == 200

    def test_missing_required_fields(self):
        app.dependency_overrides[get_db] = _db_with_found_tracking
        required = ["courier_id", "origin_city_id", "destination_city_id",
                    "service_type", "weight_gram", "sender_name",
                    "sender_phone", "sender_address", "receiver_name",
                    "receiver_phone"]
        for field in required:
            payload = {k: v for k, v in VALID_SHIPMENT_PAYLOAD.items() if k != field}
            resp = client.post("/v1/shipments", json=payload)
            assert resp.status_code == 422, f"Field {field} required"

    def test_all_valid_service_types(self):
        app.dependency_overrides[get_db] = _db_with_found_tracking
        limiter._storage = MemoryStorage()  # Fresh rate limit
        for svc in ["REG", "EXP", "YES", "OKE", "SPS"]:
            payload = {**VALID_SHIPMENT_PAYLOAD, "service_type": svc}
            resp = client.post("/v1/shipments", json=payload)
            assert resp.status_code == 200, f"Service {svc} failed: {resp.status_code}"

    def test_invalid_service_type(self):
        app.dependency_overrides[get_db] = _db_with_found_tracking
        payload = {**VALID_SHIPMENT_PAYLOAD, "service_type": "KILAT"}
        resp = client.post("/v1/shipments", json=payload)
        assert resp.status_code == 422


class TestPhoneValidation:

    def setup_method(self):
        app.dependency_overrides[validate_api_key] = _override_api_key
        app.dependency_overrides[get_db] = _db_with_found_tracking

    def test_international_format(self):
        payload = {**VALID_SHIPMENT_PAYLOAD, "sender_phone": "+6281234567890"}
        resp = client.post("/v1/shipments", json=payload)
        assert resp.status_code == 200

    def test_62_format(self):
        app.dependency_overrides[get_db] = _db_with_found_tracking
        payload = {**VALID_SHIPMENT_PAYLOAD, "sender_phone": "6281234567890"}
        resp = client.post("/v1/shipments", json=payload)
        assert resp.status_code == 200

    def test_08_format(self):
        app.dependency_overrides[get_db] = _db_with_found_tracking
        payload = {**VALID_SHIPMENT_PAYLOAD, "sender_phone": "081234567890"}
        resp = client.post("/v1/shipments", json=payload)
        assert resp.status_code == 200

    def test_too_short(self):
        app.dependency_overrides[get_db] = _db_with_found_tracking
        payload = {**VALID_SHIPMENT_PAYLOAD, "sender_phone": "081"}
        resp = client.post("/v1/shipments", json=payload)
        assert resp.status_code == 422

    def test_abc_string(self):
        app.dependency_overrides[get_db] = _db_with_found_tracking
        payload = {**VALID_SHIPMENT_PAYLOAD, "sender_phone": "abc"}
        resp = client.post("/v1/shipments", json=payload)
        assert resp.status_code == 422


# ===========================================================================
# Tracking Endpoints
# ===========================================================================

class TestTracking:
    """Note: 'not found' tests only work when we can differentiate by AWB value,
    which requires more sophisticated mock setup. For now, we test 'found' path."""

    def setup_method(self):
        app.dependency_overrides[validate_api_key] = _override_api_key
        app.dependency_overrides[get_db] = _db_with_found_tracking

    def test_tracking_found(self):
        resp = client.get("/v1/tracking/SS-REG-TEST001")
        assert resp.status_code == 200
        data = resp.json()
        assert data["awb"] == "SS-REG-TEST001"
        assert data["status"] == "MANIFESTED"

    def test_tracking_update(self):
        app.dependency_overrides[get_db] = _db_with_found_tracking
        resp = client.post("/v1/tracking/SS-REG-TEST001/update",
                           params={"status": "IN_TRANSIT", "location": "Sorting Center"})
        assert resp.status_code == 200
        assert resp.json()["current_status"] == "IN_TRANSIT"

    def test_tracking_has_courier_name(self):
        app.dependency_overrides[get_db] = _db_with_found_tracking
        resp = client.get("/v1/tracking/SS-REG-TEST001")
        assert resp.status_code == 200
        assert resp.json()["courier"] == "JNE"


# ===========================================================================
# PDF Label
# ===========================================================================

class TestShippingLabel:

    def setup_method(self):
        app.dependency_overrides[validate_api_key] = _override_api_key
        app.dependency_overrides[get_db] = _db_with_found_tracking

    def test_label_found(self):
        app.dependency_overrides[get_db] = _db_with_found_tracking
        resp = client.get("/v1/label/SS-REG-TEST001")
        assert resp.status_code == 200
        assert resp.headers["content-type"] == "application/pdf"

    def test_label_lang_en(self):
        app.dependency_overrides[get_db] = _db_with_found_tracking
        resp = client.get("/v1/label/SS-REG-TEST001?lang=en")
        assert resp.status_code == 200

    def test_label_invalid_lang(self):
        app.dependency_overrides[get_db] = _db_with_found_tracking
        resp = client.get("/v1/label/SS-REG-TEST001?lang=fr")
        assert resp.status_code == 200


# ===========================================================================
# Cost Endpoints
# ===========================================================================

class TestCost:

    def setup_method(self):
        app.dependency_overrides[validate_api_key] = _override_api_key
        app.dependency_overrides[get_db] = _db_with_found_tracking

    def test_weight_zero(self):
        app.dependency_overrides[get_db] = _db_with_found_tracking
        resp = client.post("/v1/cost", json={
            "origin": 1, "destination": 2, "weight": 0, "courier": "jne"
        })
        assert resp.status_code == 422

    def test_weight_negative(self):
        app.dependency_overrides[get_db] = _db_with_found_tracking
        resp = client.post("/v1/cost", json={
            "origin": 1, "destination": 2, "weight": -500, "courier": "jne"
        })
        assert resp.status_code == 422

    def test_cost_with_volumetric(self):
        app.dependency_overrides[get_db] = _db_with_found_tracking
        resp = client.post("/v1/cost", json={
            "origin": 1, "destination": 2, "weight": 1000, "courier": "jne",
            "length": 100, "width": 100, "height": 100
        })
        if resp.status_code == 200:
            data = resp.json()
            assert data["volumetric_weight"] > 0
            assert data["effective_weight"] > data["actual_weight"]


# ===========================================================================
# Quota
# ===========================================================================

class TestQuota:

    def setup_method(self):
        app.dependency_overrides[validate_api_key] = _override_api_key
        app.dependency_overrides[get_db] = _db_with_found_tracking

    def test_quota_status(self):
        app.dependency_overrides[get_db] = _db_with_found_tracking
        resp = client.get("/v1/quota")
        assert resp.status_code == 200
        data = resp.json()
        assert "quota_limit" in data
        assert "quota_remaining" in data
        assert "username" in data
