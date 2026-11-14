"""Fallback pricing tests: unknown couriers and cities without RajaOngkir IDs must not fail."""

from unittest.mock import MagicMock

import pytest
from fastapi.testclient import TestClient

from app.database import get_db
from app.main import app
from app.utils.api_key_auth import validate_api_key

client = TestClient(app)

API_KEY_HEADER = {"X-API-Key": "test-api-key"}


def _city(city_id, name, rajaongkir_id=None):
    city = MagicMock()
    city.id = city_id
    city.name = name
    city.province = "Jawa Timur"
    city.type = "Kota"
    city.postal_code = "60111"
    city.rajaongkir_id = rajaongkir_id
    return city


def _courier(name, code):
    courier = MagicMock()
    courier.id = 1
    courier.name = name
    courier.code = code
    return courier


@pytest.fixture()
def mock_db():
    """DB stub where cities exist but no courier row matches the requested code."""
    origin = _city(1, "Surabaya")
    destination = _city(2, "Jakarta Utara")

    db = MagicMock()

    city_query = MagicMock()
    city_query.filter.return_value.first.side_effect = [origin, destination]
    courier_query = MagicMock()
    courier_query.filter.return_value.first.return_value = None  # not seeded

    def dispatch(model):
        name = getattr(model, "__name__", str(model))
        return city_query if name == "City" else courier_query

    db.query.side_effect = dispatch

    original = dict(app.dependency_overrides)
    app.dependency_overrides[get_db] = lambda: db
    app.dependency_overrides[validate_api_key] = lambda: MagicMock()
    yield db
    app.dependency_overrides.clear()
    app.dependency_overrides.update(original)


def test_unknown_international_courier_uses_estimate(mock_db):
    response = client.post(
        "/v1/cost",
        json={"origin": 1, "destination": 2, "weight": 1000, "courier": "dhl"},
        headers=API_KEY_HEADER,
    )
    assert response.status_code == 200, response.text
    body = response.json()
    assert body["results"], "expected fallback services"
    assert body["results"][0]["service"].startswith("INTL")
    assert body["results"][0]["source"] == "internal_fallback"


def test_unknown_domestic_courier_falls_back_instead_of_404(mock_db):
    response = client.post(
        "/v1/cost",
        json={"origin": 1, "destination": 2, "weight": 1000, "courier": "ninja"},
        headers=API_KEY_HEADER,
    )
    assert response.status_code == 200, response.text
    services = [item["service"] for item in response.json()["results"]]
    assert "REG" in services


def test_missing_rajaongkir_id_returns_notice_not_error(mock_db):
    response = client.post(
        "/v1/cost",
        json={"origin": 1, "destination": 2, "weight": 1000, "courier": "jne"},
        headers=API_KEY_HEADER,
    )
    assert response.status_code == 200, response.text
    assert "notice" in response.json()
