# ShipStream Logistics API — CRITICAL FIXES & CODE CHANGES

**Priority**: HIGH - Segera lakukan sebelum production  
**Estimated Time**: ~2-3 jam untuk semua fixes

---

## 🔴 CRITICAL FIX #1: Secure Admin Payment Confirmation Endpoint

**File**: [app/routers/billing.py](app/routers/billing.py#L130)  
**Severity**: CRITICAL - Security Vulnerability  
**Issue**: Siapa saja bisa confirm pembayaran dan credit unlimited quota

### Current Code (VULNERABLE):
```python
@router.post("/admin/confirm-payment/{order_id}")
def confirm_payment(order_id: str, db: Session = Depends(get_db)):
    """
    Step 3 (Admin): Admin confirms the payment is valid.
    Only after this, the Quota is added to the API Key.
    """
    # Find transaction
    tx = db.query(models.Transaction).filter(models.Transaction.order_id == order_id).first()
    if not tx:
        raise HTTPException(status_code=404, detail="Transaction not found")
    
    if tx.status == "success":
        return {"message": "Transaction already processed"}

    # Update status to success
    tx.status = "success"
    
    # Global Quota Credit ← ANYONE CAN EXECUTE THIS!
    user = db.query(models.User).filter(models.User.id == tx.user_id).first()
    if user:
        user.quota_limit += tx.quota_added
        
    api_key = db.query(models.APIKey).filter(models.APIKey.id == tx.api_key_id).first()
    if api_key and api_key.status == "limited":
        api_key.status = "active"
    
    db.commit()
    return {
        "message": "Pembayaran berhasil dikonfirmasi. Kuota telah ditambahkan.", 
        "order_id": order_id,
        "new_global_limit": user.quota_limit if user else None,
        "status": "success"
    }
```

### Fixed Code:
```python
@router.post("/admin/confirm-payment/{order_id}")
def confirm_payment(
    order_id: str, 
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)  # ← ADD THIS
):
    """
    Step 3 (Admin): Admin confirms the payment is valid.
    Only after this, the Quota is added to the API Key.
    
    SECURITY: Requires authentication + admin role
    """
    # ← ADD THIS AUTHORIZATION CHECK
    if not current_user or current_user.username not in ["admin", "yogiuser"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access only"
        )
    
    # Find transaction
    tx = db.query(models.Transaction).filter(models.Transaction.order_id == order_id).first()
    if not tx:
        raise HTTPException(status_code=404, detail="Transaction not found")
    
    # Log admin action for audit
    audit_log = f"[ADMIN_CONFIRM] User: {current_user.username}, TX: {order_id}, At: {datetime.utcnow().isoformat()}"
    print(audit_log, flush=True)  # TODO: Setup proper audit logging
    
    if tx.status == "success":
        return {"message": "Transaction already processed"}

    # Update status to success
    tx.status = "success"
    
    # Global Quota Credit (Now protected)
    user = db.query(models.User).filter(models.User.id == tx.user_id).first()
    if user:
        user.quota_limit += tx.quota_added
        
    api_key = db.query(models.APIKey).filter(models.APIKey.id == tx.api_key_id).first()
    if api_key and api_key.status == "limited":
        api_key.status = "active"
    
    db.commit()
    return {
        "message": "Pembayaran berhasil dikonfirmasi. Kuota telah ditambahkan.", 
        "order_id": order_id,
        "new_global_limit": user.quota_limit if user else None,
        "status": "success",
        "confirmed_by": current_user.username,
        "confirmed_at": datetime.utcnow().isoformat()
    }
```

### What Changed:
1. ✅ Added `current_user: models.User = Depends(get_current_user)` parameter
2. ✅ Added authorization check untuk admin only
3. ✅ Added audit logging
4. ✅ Return confirmed_by + timestamp untuk tracking

---

## 🔴 CRITICAL FIX #2: Setup Database Trigger untuk Quota Sync

**File**: Database (PostgreSQL) atau setup script  
**Severity**: CRITICAL - Quota tracking accuracy  
**Issue**: `quota_used` tidak ter-sync otomatis dengan total API calls

### Current Issue:
```python
# Di app/utils/api_key_auth.py line 45:
db_key.total_requests = models.APIKey.total_requests + 1
db.commit()

# Tapi tidak ada trigger untuk update user.quota_used!
# Ini bisa menyebabkan quota check tidak akurat
```

### Solution: Create SQL Migration

**File to Create**: `app/utils/setup_triggers.py`

```python
def setup_quota_sync_trigger(engine):
    """
    Sets up PostgreSQL trigger untuk otomatis sync quota_used
    setiap kali ada update di api_keys table.
    
    Run ini sekali saat first-time setup atau di seed_data.py
    """
    
    with engine.connect() as connection:
        # Create function
        create_function = """
        CREATE OR REPLACE FUNCTION sync_user_quota()
        RETURNS TRIGGER AS $$
        BEGIN
            UPDATE users
            SET quota_used = (
                SELECT COALESCE(SUM(total_requests), 0) 
                FROM api_keys 
                WHERE user_id = NEW.user_id
            )
            WHERE id = NEW.user_id;
            RETURN NEW;
        END;
        $$ LANGUAGE plpgsql;
        """
        
        # Drop trigger jika sudah ada (untuk idempotency)
        drop_trigger = """
        DROP TRIGGER IF EXISTS trg_sync_user_quota ON api_keys;
        """
        
        # Create trigger
        create_trigger = """
        CREATE TRIGGER trg_sync_user_quota
            AFTER UPDATE OF total_requests ON api_keys
            FOR EACH ROW
            EXECUTE FUNCTION sync_user_quota();
        """
        
        try:
            connection.execute(drop_trigger)
            print("[✓] Dropped existing trigger (if any)")
            
            connection.execute(create_function)
            print("[✓] Created sync_user_quota() function")
            
            connection.execute(create_trigger)
            print("[✓] Created trg_sync_user_quota trigger")
            
            connection.commit()
            print("[✓] Database trigger setup COMPLETE")
            
        except Exception as e:
            print(f"[✗] Error setting up trigger: {e}")
            connection.rollback()
            raise
```

### Usage in app/main.py or seed_data.py:

```python
from app.utils.setup_triggers import setup_quota_sync_trigger

# Jalankan saat startup (sekali saja)
Base.metadata.create_all(bind=engine)

# ADD THIS:
try:
    setup_quota_sync_trigger(engine)
except Exception as e:
    print(f"Warning: Trigger setup failed (might already exist): {e}")
```

### Alternative: Manual SQL Setup

Jalankan di pgAdmin atau psql console:

```sql
-- Create function
CREATE OR REPLACE FUNCTION sync_user_quota()
RETURNS TRIGGER AS $$
BEGIN
    UPDATE users
    SET quota_used = (
        SELECT COALESCE(SUM(total_requests), 0) 
        FROM api_keys 
        WHERE user_id = NEW.user_id
    )
    WHERE id = NEW.user_id;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Create trigger
DROP TRIGGER IF EXISTS trg_sync_user_quota ON api_keys;
CREATE TRIGGER trg_sync_user_quota
    AFTER UPDATE OF total_requests ON api_keys
    FOR EACH ROW
    EXECUTE FUNCTION sync_user_quota();

-- Test: INSERT dummy data dan verify hasil
SELECT * FROM users WHERE id = 1;  -- Check quota_used before
UPDATE api_keys SET total_requests = total_requests + 100 WHERE user_id = 1;
SELECT * FROM users WHERE id = 1;  -- Check quota_used after (should increase)
```

---

## 🟡 HIGH PRIORITY FIX #3: Restrict Turnstile Fail-Open

**File**: [app/utils/security_utils.py](app/utils/security_utils.py#L10)  
**Severity**: HIGH - Registration validation  
**Issue**: Siapa saja bisa register tanpa captcha validation

### Current Code:
```python
async def verify_turnstile(token: str, remote_ip: str = None):
    """
    Validates Cloudflare Turnstile captcha token.
    For local development, we allow 'test-token'.
    """
    if not token:
        return False
    if token == "test-token":
        return True
    
    if not CLOUDFLARE_SECRET:
        # If secret is missing, we fail-open for development convenience
        # but in production, this should be mandatory.
        return True  # ← FAIL-OPEN! RISKY!
```

### Fixed Code:
```python
import os
from dotenv import load_dotenv

load_dotenv()

async def verify_turnstile(token: str, remote_ip: str = None):
    """
    Validates Cloudflare Turnstile captcha token.
    
    Security Policy:
    - Development: Allow test-token OR accept any token if no secret
    - Production: REQUIRE valid secret + token validation
    """
    if not token:
        return False
    
    # Dev convenience: allow test-token
    if token == "test-token":
        return (os.getenv("ENVIRONMENT") != "production")
    
    CLOUDFLARE_SECRET = os.getenv("CLOUDFLARE_SECRET")
    
    if not CLOUDFLARE_SECRET:
        # Production: Reject jika tidak ada secret
        if os.getenv("ENVIRONMENT") == "production":
            print("[ERROR] CLOUDFLARE_SECRET missing in production! Rejecting registration.")
            return False
        
        # Development: Allow untuk convenience (dengan warning)
        print("[WARN] CLOUDFLARE_SECRET not configured. Allowing registration (dev mode only)")
        return True
    
    # Validate token dengan Turnstile API
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                "https://challenges.cloudflare.com/turnstile/v0/siteverify",
                data={
                    "secret": CLOUDFLARE_SECRET,
                    "response": token,
                    "remoteip": remote_ip
                },
                timeout=10.0
            )
            result = response.json()
            success = result.get("success", False)
            
            if not success:
                print(f"[WARN] Turnstile validation failed: {result.get('error-codes', 'unknown')}")
            
            return success
            
    except Exception as e:
        print(f"[ERROR] Turnstile verification error: {e}")
        # Fail-closed untuk production
        if os.getenv("ENVIRONMENT") == "production":
            return False
        # Fail-open untuk dev (dengan warning)
        print("[WARN] Using fail-open in development mode")
        return True
```

### Update .env:
```env
# Production flag
ENVIRONMENT=development  # Change to "production" in deployment

# Cloudflare Turnstile
CLOUDFLARE_SECRET=your_turnstile_secret_key_here
TURNSTILE_SITE_KEY=your_turnstile_site_key

---

## 🟢 FRONTEND FIXES APPLIED (UI Logic)

During the interactive debugging session I also applied two frontend fixes to address buttons that were stuck/not submitting correctly:

- **Fix A — Change Email / Change Password form submission:** The profile security modal was submitting data via query-string on a `PUT` request which caused backend endpoints to not receive JSON payloads. I updated the client to send a JSON body with `Content-Type: application/json` when calling `/profile/update-email` and `/profile/update-password`.
    - File changed: `frontend/dashboard.html` — updated form submit to use `fetch(..., { method: 'PUT', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(body) })`.
    - Effect: `Ubah Email` and `Ubah Password` actions now send proper JSON and should invoke the server logic.

- **Fix B — "Soon" badge replaced with "loading...":** The small badge next to phone number in the Profile card showed `Soon` (misleading). I replaced it with `loading...` to match the current loading state in the UI while profile data is fetched.
    - File changed: `frontend/dashboard.html` — replaced the inline badge text.
    - Effect: Visual clarity for users while data loads.

These frontend fixes are client-side only and documented here so they are tracked with the critical fixes.
```

---

## 🟡 HIGH PRIORITY FIX #4: Complete Test-Webhook Endpoint

**File**: [app/routers/profile.py](app/routers/profile.py#L133)  
**Severity**: HIGH - Feature incomplete  
**Issue**: Test webhook implementation tidak selesai

### Current Code (Incomplete):
```python
@router.post("/profile/test-webhook")
async def test_webhook(
    payload: schemas.WebhookTest,
    current_user: models.User = Depends(get_current_user),
    request: Request = None
):
    """
    Test a webhook or telegram integration before saving.
    """
    test_msg = f"🚀 [ShipStream] Test Notification for {current_user.username}. Your integration is working perfectly!"
    # INCOMPLETE! Tidak ada after ini
```

### Fixed Code:
```python
@router.post("/profile/test-webhook")
async def test_webhook(
    payload: schemas.WebhookTest,
    current_user: models.User = Depends(get_current_user),
):
    """
    Test a webhook or telegram integration before saving.
    
    Supported channels:
    - telegram: Requires bot_token and chat_id
    - webhook: Requires URL (for custom HTTP webhooks)
    """
    
    test_msg = f"🚀 [ShipStream] Test Notification\n\nUser: {current_user.username}\nMessage: Your integration is working perfectly!"
    
    if payload.channel == "telegram":
        if not payload.bot_token or not payload.chat_id:
            raise HTTPException(
                status_code=400,
                detail="Telegram requires bot_token and chat_id"
            )
        
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"https://api.telegram.org/bot{payload.bot_token}/sendMessage",
                    json={
                        "chat_id": payload.chat_id,
                        "text": test_msg,
                        "parse_mode": "HTML"
                    },
                    timeout=10.0
                )
                
                if response.status_code == 200:
                    return {
                        "status": "success",
                        "message": "Pesan test berhasil dikirim ke Telegram!",
                        "channel": "telegram",
                        "chat_id": payload.chat_id
                    }
                else:
                    error = response.json()
                    raise HTTPException(
                        status_code=400,
                        detail=f"Telegram API error: {error.get('description', 'unknown')}"
                    )
        
        except httpx.TimeoutException:
            raise HTTPException(
                status_code=504,
                detail="Telegram API timeout. Check bot_token dan internet connection."
            )
        except Exception as e:
            raise HTTPException(
                status_code=500,
                detail=f"Failed to send test message: {str(e)}"
            )
    
    elif payload.channel == "webhook":
        if not payload.url:
            raise HTTPException(
                status_code=400,
                detail="Webhook requires URL"
            )
        
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    payload.url,
                    json={
                        "event": "test",
                        "username": current_user.username,
                        "message": test_msg,
                        "timestamp": datetime.utcnow().isoformat()
                    },
                    timeout=10.0
                )
                
                if response.status_code in [200, 201, 204]:
                    return {
                        "status": "success",
                        "message": "Webhook test berhasil dikirim!",
                        "channel": "webhook",
                        "url": payload.url,
                        "status_code": response.status_code
                    }
                else:
                    return {
                        "status": "warning",
                        "message": f"Webhook returned status {response.status_code}",
                        "channel": "webhook",
                        "url": payload.url,
                        "status_code": response.status_code,
                        "response": response.text[:200]
                    }
        
        except httpx.TimeoutException:
            raise HTTPException(
                status_code=504,
                detail="Webhook URL timeout. Check URL dan server responsiveness."
            )
        except Exception as e:
            raise HTTPException(
                status_code=500,
                detail=f"Failed to send webhook: {str(e)}"
            )
    
    else:
        raise HTTPException(
            status_code=400,
            detail=f"Unknown channel: {payload.channel}. Supported: telegram, webhook"
        )
```

---

## 🟡 MEDIUM PRIORITY FIX #5: Add Session Last-Active Middleware

**File**: [app/main.py](app/main.py) atau file baru: `app/middleware/session_tracking.py`  
**Severity**: MEDIUM - Session accuracy  
**Issue**: `last_active` hanya update di login, bukan setiap request

### New File: app/middleware/session_tracking.py

```python
from fastapi import Request
from datetime import datetime
from app.database import SessionLocal, get_db
from app.models import base as models
from app.utils import security
import logging

logger = logging.getLogger(__name__)

class SessionTrackingMiddleware:
    def __init__(self, app):
        self.app = app
    
    async def __call__(self, request: Request, call_next):
        response = await call_next(request)
        
        # Only track authenticated requests
        auth_header = request.headers.get("Authorization", "")
        if not auth_header.startswith("Bearer "):
            return response
        
        try:
            token = auth_header.split(" ")[1]
            token_data = security.get_current_user_from_token(token)
            
            if token_data:
                # Update session last_active asynchronously
                import asyncio
                asyncio.create_task(
                    self._update_session_async(token_data.get("jti"))
                )
        
        except Exception as e:
            logger.warning(f"Failed to update session: {e}")
        
        return response
    
    @staticmethod
    async def _update_session_async(jti: str):
        """Update session last_active without blocking response"""
        if not jti:
            return
        
        db = SessionLocal()
        try:
            session = db.query(models.UserSession).filter(
                models.UserSession.jti == jti,
                models.UserSession.is_active == True
            ).first()
            
            if session:
                session.last_active = datetime.utcnow()
                db.commit()
        
        except Exception as e:
            logger.error(f"Error updating session: {e}")
            db.rollback()
        
        finally:
            db.close()
```

### Update app/main.py:

```python
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from app.middleware.session_tracking import SessionTrackingMiddleware

app = FastAPI(...)

# Add session tracking middleware BEFORE other middleware
app.add_middleware(SessionTrackingMiddleware)

# Other middleware...
app.add_middleware(CORSMiddleware, ...)
```

---

## 🟡 MEDIUM PRIORITY FIX #6: Mobile Responsiveness Improvements

**File**: [frontend/assets/style.css](frontend/assets/style.css)  
**Severity**: MEDIUM - UX  
**Issue**: Modal dan tabs mungkin overflow di mobile kecil

### CSS Additions:

```css
/* Modal responsiveness */
.modal-content {
    max-height: 90vh;
    overflow-y: auto;
    overflow-x: hidden;
    -webkit-overflow-scrolling: touch;  /* Smooth scroll pada iOS */
}

/* Tablet breakpoint */
@media (max-width: 1024px) {
    .modal-content {
        max-height: 85vh;
        padding: 15px;
    }
    
    .modal-header h2 {
        font-size: 18px;
    }
}

/* Mobile breakpoint */
@media (max-width: 768px) {
    .modal-overlay {
        padding: 0;
    }
    
    .modal-content {
        border-radius: 8px 8px 0 0;
        max-height: 92vh;
        min-height: 100px;
    }
    
    .modal-header {
        padding: 12px 15px;
    }
    
    .modal-body {
        padding: 15px;
        max-height: calc(92vh - 100px);
        overflow-y: auto;
    }
    
    /* Tab styling untuk mobile */
    .tab {
        padding: 10px 12px;
        font-size: 13px;
    }
    
    /* Transaction detail card */
    .tx-card {
        flex-direction: column;
        gap: 10px;
    }
    
    .tx-card-value {
        font-size: 14px;
    }
}

/* Small mobile */
@media (max-width: 480px) {
    .modal-content {
        max-height: 95vh;
    }
    
    .tab {
        padding: 8px 10px;
        font-size: 12px;
    }
    
    .modal-header h2 {
        font-size: 16px;
    }
    
    /* Stack button vertically */
    .modal-footer {
        flex-direction: column;
        gap: 8px;
    }
    
    .modal-footer button {
        width: 100%;
    }
}
```

---

## 📋 IMPLEMENTATION CHECKLIST

### Before Production:

- [ ] Fix #1: Secure admin confirm-payment endpoint
- [ ] Fix #2: Setup database trigger untuk quota sync
- [ ] Fix #3: Restrict Turnstile fail-open
- [ ] Fix #4: Complete test-webhook endpoint
- [ ] Fix #5: Add session tracking middleware
- [ ] Fix #6: Update CSS untuk mobile responsiveness

### Testing Checklist:

- [ ] Test admin confirm-payment dengan auth
- [ ] Test quota_used auto-sync via trigger
- [ ] Test Turnstile in production mode
- [ ] Test webhook (Telegram + HTTP custom)
- [ ] Test session last_active updates
- [ ] Test mobile responsiveness

### Deployment Checklist:

- [ ] Update .env untuk production
- [ ] Set ENVIRONMENT=production
- [ ] Configure CLOUDFLARE_SECRET
- [ ] Setup database trigger before first deploy
- [ ] Run full end-to-end tests
- [ ] Backup database sebelum deploy

---

**Total Estimated Time**: 2-3 hours untuk semua fixes  
**Priority**: CRITICAL (Fixes #1, #2) DANGEROUS untuk production tanpa ini!
