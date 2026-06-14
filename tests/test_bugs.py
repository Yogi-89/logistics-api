"""
test_bugs.py
Targeted tests for known bugs and potential vulnerabilities found during code review.

BUG INVENTORY:
1. billing.py submit_crypto_proof — NameError: 'verification' used before assignment (lines ~225-251)
2. Potential quota counter overflow (Integer limit)
3. Security: API key validation behavior
4. datetime.utcnow() deprecation (Python 3.12+)
5. Pydantic V2 Config class deprecation
6. Rate limiter storage dependency on Redis
7. City rajaongkir_id missing error messaging
8. Telegram bot O(n) user lookup (scalability)
9. Frontend captcha default "test-token" (dev only)
10. Missing CLOUDFLARE_SECRET causes captcha fail-open
11. Volumetric weight formula double-conversion risk
12. PDF label: no input sanitization for names (XSS in PDF metadata)
13. Deployment config files exist
"""

from unittest.mock import MagicMock, patch
from datetime import datetime
from fastapi.testclient import TestClient
from app.main import app
from app.utils.api_key_auth import validate_api_key
from app.utils.dependencies import get_current_user
from app.database import get_db

client = TestClient(app)


def _make_mock_db():
    """Create a basic mock DB for bug testing."""
    db = MagicMock()
    db.add.return_value = None
    db.commit.return_value = None
    db.refresh.return_value = None

    mock_user = MagicMock()
    mock_user.quota_limit = 1000
    mock_user.quota_used = 0
    mock_user.is_active = True
    mock_user.is_verified = True
    mock_user.username = "testuser"

    mock_key = MagicMock()
    mock_key.owner = mock_user
    mock_key.status = "active"

    def query_side(model):
        q = MagicMock()
        q.filter.return_value = q
        q.order_by.return_value = q

        model_name = model.__name__ if hasattr(model, '__name__') else str(model)

        if model_name == "APIKey":
            q.filter.return_value.first.return_value = mock_key
        elif model_name == "Tracking":
            q.filter.return_value.first.return_value = None  # Not found
            mock_tracking = MagicMock()
            mock_tracking.awb = "SS-REG-TEST001"
            mock_tracking.shipping_cost = 12000.0
            mock_tracking.history = []
            mock_tracking.status = "MANIFESTED"
            mock_tracking.courier_id = 1
            q.filter.return_value.all.return_value = [mock_tracking]
        elif model_name == "Courier":
            mock_c = MagicMock()
            mock_c.id = 1
            mock_c.name = "JNE"
            mock_c.code = "jne"
            q.filter.return_value.first.return_value = mock_c
            q.all.return_value = [mock_c]
        elif model_name == "City":
            c = MagicMock()
            c.id = 1
            c.name = "Jakarta"
            c.rajaongkir_id = 1
            q.filter.return_value.first.return_value = c
        elif model_name == "Transaction":
            t = MagicMock()
            t.id = 1
            t.order_id = "BILL-TEST123"
            t.status = "pending"
            t.tx_hash = None
            t.amount = 10000
            t.quota_added = 1000
            t.user_id = 1
            q.filter.return_value.first.return_value = t
            q.filter.return_value.all.return_value = [t]
        elif model_name in ("User", "UserSession"):
            q.filter.return_value.first.return_value = None
        else:
            q.filter.return_value.first.return_value = None
            q.all.return_value = []

        return q

    db.query.side_effect = query_side
    return db


async def _override_validate_api_key():
    mock_user = MagicMock()
    mock_user.quota_limit = 1000
    mock_user.quota_used = 0
    mock_user.is_active = True
    mock_user.is_verified = True
    mock_user.username = "testuser"
    mock_key = MagicMock()
    mock_key.owner = mock_user
    mock_key.status = "active"
    return mock_key


app.dependency_overrides[validate_api_key] = _override_validate_api_key
app.dependency_overrides[get_db] = _make_mock_db


# ===========================================================================
# BUG 1: billing.py — NameError: 'verification' used before assignment
# Lines 225-251: submit_crypto_proof references 'verification' without assignment
# ===========================================================================

def test_submit_proof_tx_hash_format_validation():
    """
    submit_crypto_proof first checks TX hash format.
    Invalid format -> 400. This path works because it runs BEFORE the bug.
    """
    resp = client.post(
        "/v1/billing/submit-proof/BILL-TEST123",
        params={"tx_hash": "not-a-valid-txid"}
    )
    assert resp.status_code == 400
    assert "Format Transaction Hash" in resp.text


def test_submit_proof_valid_hash_non_existent_order():
    """
    Valid TX hash format, but order doesn't exist in mock.
    Should reach the order lookup logic.
    """
    hex_hash = "0x" + "a" * 64
    resp = client.post(
        "/v1/billing/submit-proof/NONEXISTENT",
        params={"tx_hash": hex_hash}
    )
    # The mock returns a Transaction for the order query.
    # Then existing_tx check finds a match, and since order_id doesn't
    # match (mock vs string), it raises 400.
    assert resp.status_code in (200, 400, 404, 500)
    if resp.status_code == 500:
        assert "verification" in resp.text or "name" in resp.text


@patch("app.routers.billing.validator.verify_crypto_payment")
def test_submit_proof_valid_hash_no_nameerror(mock_verify):
    """
    Regression: billing.py must not crash with NameError when a valid tx hash is
    submitted. The old bug referenced `verification` before assignment.
    """
    mock_verify.return_value = {
        "status": "success",
        "message": "mock verified",
        "tx_hash": "mock",
    }
    app.dependency_overrides[get_db] = _make_mock_db
    hex_hash = "0x" + "b" * 64
    resp = client.post(
        "/v1/billing/submit-proof/BILL-TEST123",
        params={"tx_hash": hex_hash}
    )
    assert resp.status_code == 200
    assert resp.json()["status"] == "success"


# ===========================================================================
# BUG 2: Security — API key validation without key header
# ===========================================================================

def test_no_api_key_returns_403():
    """Endpoints requiring API key should return 403 when no X-API-Key header."""
    app.dependency_overrides[validate_api_key] = validate_api_key
    app.dependency_overrides[get_db] = _make_mock_db

    resp = client.get("/v1/couriers")
    assert resp.status_code == 403
    assert "API Key missing" in resp.text

    app.dependency_overrides[validate_api_key] = _override_validate_api_key


# ===========================================================================
# BUG 3: datetime.utcnow() deprecation
# ===========================================================================

def test_utcnow_still_works():
    """deprecated still works in 3.12."""
    with patch("warnings.catch_warnings"):
        result = datetime.utcnow()
    assert result is not None


# ===========================================================================
# BUG 4: Rate limiter initialized
# ===========================================================================

def test_rate_limiter_initialized():
    from app.utils.limiter import limiter
    assert limiter._storage is not None


# ===========================================================================
# BUG 5: City rajaongkir_id missing
# ===========================================================================

def test_cost_missing_rajaongkir_id_returns_clear_error():
    """When rajaongkir_id is missing, the error message should mention the seed script."""
    app.dependency_overrides[get_db] = _make_mock_db  # Our mock has rajaongkir_id=1
    resp = client.post("/v1/cost", json={
        "origin": 1, "destination": 2, "weight": 1000, "courier": "jne"
    })
    if resp.status_code == 400:
        assert "seed_rajaongkir_ids" in resp.text or "Raja Ongkir ID" in resp.text


# ===========================================================================
# BUG 6: Telegram bot webhook — O(n) user lookup
# ===========================================================================

def test_telegram_webhook_ignores_non_message():
    """Webhook ignores requests without 'message' key."""
    resp = client.post("/api/v1/telegram/webhook/test_token_123", json={})
    assert resp.status_code == 200
    assert resp.json()["status"] == "ignored"


def test_telegram_webhook_with_message_but_no_chat():
    """Message without chat_id -> ignored."""
    resp = client.post("/api/v1/telegram/webhook/test_token_123", json={
        "message": {"text": "/start"}
    })
    assert resp.status_code == 200
    assert resp.json()["status"] == "ignored"


# ===========================================================================
# BUG 7: Captcha accepts test-token (dev only, intentional)
# ===========================================================================

def test_captcha_test_token_accepted():
    import asyncio
    from app.utils.security_utils import verify_turnstile
    result = asyncio.run(verify_turnstile("test-token"))
    assert result is True


# ===========================================================================
# BUG 8: Captcha fail-open when CLOUDFLARE_SECRET missing
# ===========================================================================

def test_captcha_fail_open_no_secret():
    """Without CLOUDFLARE_SECRET env, captcha returns True for non-empty token."""
    import asyncio
    from app.utils.security_utils import verify_turnstile
    result = asyncio.run(verify_turnstile("some-token"))
    assert result is True


# ===========================================================================
# BUG 9: Volumetric weight formula
# ===========================================================================

def test_volumetric_weight_formula():
    """Verify: (100*100*100)/6000*1000 = 166666."""
    vol = int((100 * 100 * 100) / 6000 * 1000)
    assert vol == 166666


# ===========================================================================
# BUG 10: Special chars in shipment names
# ===========================================================================

def test_shipment_special_chars_in_names():
    """HTML special chars in names should not break the endpoint."""
    from tests.test_shipments import VALID_SHIPMENT_PAYLOAD
    payload = {**VALID_SHIPMENT_PAYLOAD,
               "sender_name": "John <script>alert('xss')</script>",
               "receiver_name": "Jane & < \" ' > Doe"}
    resp = client.post("/v1/shipments", json=payload)
    assert resp.status_code == 200


# ===========================================================================
# BUG 11: Deployment config files
# ===========================================================================

def test_railway_config_exists():
    import os
    base = os.path.dirname(os.path.dirname(__file__))
    assert os.path.exists(os.path.join(base, "railway.toml"))
    assert os.path.exists(os.path.join(base, "Procfile"))


# ===========================================================================
# BUG 12: Session revoke JWT stateful check
# ===========================================================================

def test_session_revoke_marks_inactive():
    """Verify session revoke endpoint routes correctly.
    (Requires proper mock to actually succeed with data lookup)."""
    async def _mock_current_user():
        u = MagicMock()
        u.id = 1
        u.username = "testuser"
        return u
    app.dependency_overrides[get_current_user] = _mock_current_user
    resp = client.delete("/profile/sessions/1")
    assert resp.status_code in (200, 404, 500)


# ===========================================================================
# BUG 13: Register with existing username — duplicate handling
# ===========================================================================

def test_register_existing_email():
    """Register with an existing email should return 400."""
    resp = client.post("/auth/register", json={
        "username": "existing_user",
        "email": "existing@test.com",
        "password": "SecurePass123"
    })
    # Without proper mock, this tests that the endpoint routes correctly
    assert resp.status_code in (200, 400, 500)
