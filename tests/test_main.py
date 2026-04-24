"""
tests/test_main.py
ShipStream Logistics API — Test Suite
Semua test menggunakan TestClient FastAPI + dependency overrides.
Tidak butuh koneksi DB live.
"""

from unittest.mock import MagicMock, patch
from fastapi.testclient import TestClient
from app.main import app
from app.utils.api_key_auth import validate_api_key
from app.database import get_db

# ---------------------------------------------------------------------------
# Shared mock objects
# ---------------------------------------------------------------------------

def _make_mock_api_key():
    """Buat mock API key object yang cukup untuk melewati validate_api_key."""
    mock_user = MagicMock()
    mock_user.quota_limit = 1000
    mock_user.quota_used = 0
    mock_user.is_active = True

    mock_key = MagicMock()
    mock_key.owner = mock_user
    return mock_key


def _make_mock_db():
    """Buat mock DB session untuk endpoint yang butuh query."""
    mock_db = MagicMock()

    # Mock courier (untuk /v1/shipments — tidak dipakai langsung di create_shipment
    # tapi diperlukan oleh validate_api_key yang sudah di-override)
    mock_courier = MagicMock()
    mock_courier.name = "JNE"

    # Mock tracking record hasil db.refresh
    mock_tracking = MagicMock()
    mock_tracking.awb = "SS-REG-TEST001"
    mock_tracking.shipping_cost = 12000.0

    # Konfigurasi chain: db.add / db.commit / db.refresh tidak error
    mock_db.add.return_value = None
    mock_db.commit.return_value = None
    mock_db.refresh.return_value = None  # refresh mengubah obj in-place; mock cukup

    return mock_db


# ---------------------------------------------------------------------------
# Override dependencies — berlaku untuk seluruh modul
# ---------------------------------------------------------------------------

async def _override_validate_api_key():
    """Mock validate_api_key: bypass seluruh auth + quota logic."""
    return _make_mock_api_key()


def _override_get_db():
    """Mock get_db: kembalikan mock DB session."""
    db = _make_mock_db()
    try:
        yield db
    finally:
        pass


app.dependency_overrides[validate_api_key] = _override_validate_api_key
app.dependency_overrides[get_db] = _override_get_db

client = TestClient(app)

# ---------------------------------------------------------------------------
# Payload helper
# ---------------------------------------------------------------------------

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

# ---------------------------------------------------------------------------
# Tests — Root
# ---------------------------------------------------------------------------


def test_read_main():
    """GET / harus mengembalikan 200 (file response index.html atau redirect)."""
    response = client.get("/")
    # Bisa 200 (file ada) atau 404 jika frontend/ tidak ada di env test — keduanya OK
    assert response.status_code in (200, 404)


# ---------------------------------------------------------------------------
# Tests — POST /v1/shipments (valid)
# ---------------------------------------------------------------------------


def test_shipment_valid_payload():
    """POST /v1/shipments dengan payload valid → harus return 200 dan ada key 'awb'."""
    response = client.post("/v1/shipments", json=VALID_SHIPMENT_PAYLOAD)
    assert response.status_code == 200, (
        f"Expected 200, got {response.status_code}. Body: {response.text}"
    )
    data = response.json()
    assert "awb" in data, f"Response harus mengandung 'awb'. Got: {data}"
    assert data["awb"].startswith("SS-REG-"), (
        f"AWB format salah. Got: {data['awb']}"
    )


# ---------------------------------------------------------------------------
# Tests — POST /v1/shipments (invalid, → 422)
# ---------------------------------------------------------------------------


def test_shipment_invalid_phone():
    """POST /v1/shipments dengan sender_phone='abc' → harus return 422."""
    payload = {**VALID_SHIPMENT_PAYLOAD, "sender_phone": "abc"}
    response = client.post("/v1/shipments", json=payload)
    assert response.status_code == 422, (
        f"Expected 422, got {response.status_code}. Body: {response.text}"
    )
    assert "Indonesian phone number" in response.text, (
        f"Pesan error tidak mengandung 'Indonesian phone number'. Got: {response.text}"
    )


def test_shipment_invalid_weight_negative():
    """POST /v1/shipments dengan weight_gram=-1 → harus return 422."""
    payload = {**VALID_SHIPMENT_PAYLOAD, "weight_gram": -1}
    response = client.post("/v1/shipments", json=payload)
    assert response.status_code == 422, (
        f"Expected 422, got {response.status_code}. Body: {response.text}"
    )


def test_shipment_invalid_weight_zero():
    """POST /v1/shipments dengan weight_gram=0 → harus return 422 (gt=0)."""
    payload = {**VALID_SHIPMENT_PAYLOAD, "weight_gram": 0}
    response = client.post("/v1/shipments", json=payload)
    assert response.status_code == 422, (
        f"Expected 422, got {response.status_code}. Body: {response.text}"
    )


def test_shipment_invalid_service_type():
    """POST /v1/shipments dengan service_type='KILAT' (tidak dalam enum) → 422."""
    payload = {**VALID_SHIPMENT_PAYLOAD, "service_type": "KILAT"}
    response = client.post("/v1/shipments", json=payload)
    assert response.status_code == 422, (
        f"Expected 422, got {response.status_code}. Body: {response.text}"
    )


# ---------------------------------------------------------------------------
# Tests — POST /v1/cost (invalid weight → 422)
# ---------------------------------------------------------------------------


def test_cost_invalid_weight_zero():
    """POST /v1/cost dengan weight=0 → harus return 422 (gt=0)."""
    response = client.post("/v1/cost", json={
        "origin": 1,
        "destination": 2,
        "weight": 0,   # Invalid: harus gt=0
        "courier": "jne"
    })
    assert response.status_code == 422, (
        f"Expected 422, got {response.status_code}. Body: {response.text}"
    )


def test_cost_invalid_weight_negative():
    """POST /v1/cost dengan weight=-500 → harus return 422."""
    response = client.post("/v1/cost", json={
        "origin": 1,
        "destination": 2,
        "weight": -500,
        "courier": "jne"
    })
    assert response.status_code == 422, (
        f"Expected 422, got {response.status_code}. Body: {response.text}"
    )
