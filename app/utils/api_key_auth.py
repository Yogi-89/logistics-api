from fastapi import Security, HTTPException, status, Depends, Request
from fastapi.security.api_key import APIKeyHeader
from sqlalchemy.orm import Session
from sqlalchemy import update
from app.database import get_db
from app.models import base as models
import httpx
import asyncio
from datetime import datetime

API_KEY_NAME = "X-API-Key"
api_key_header = APIKeyHeader(name=API_KEY_NAME, auto_error=False)

def validate_api_key(request: Request, api_key: str = Security(api_key_header), db: Session = Depends(get_db)):
    if not api_key:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="API Key missing in header (X-API-Key)"
        )
    
    db_key = db.query(models.APIKey).filter(models.APIKey.key == api_key, models.APIKey.is_active == True).first()
    if not db_key:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or inactive API Key"
        )
    
    # 0. Check Owner Verification Status
    if not db_key.owner.is_verified:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Akun pemilik API Key belum diverifikasi. Silakan hubungi admin atau verifikasi di Dashboard."
        )
    
    # 1. Check IP Whitelist
    client_ip = request.client.host
    if db_key.ip_whitelist:
        allowed_ips = [ip.strip() for ip in db_key.ip_whitelist.split(",")]
        # Note: In some setups (proxies), you might need X-Forwarded-For
        if client_ip not in allowed_ips:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"IP address {client_ip} is not whitelisted for this API Key"
            )

    # 2. Check Quota (Prepaid logic - GLOBAL POOL)
    user = db_key.owner
    if user.quota_used >= user.quota_limit:
        db_key.status = "limited"
        db.commit()
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Account quota exceeded (Global prepaid limit reached). Please top up."
        )

    # 3. Check Per-Key Spending Cap (Optional)
    if db_key.request_limit and db_key.total_requests >= db_key.request_limit:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="API Key specific limit reached (Spending cap)"
        )

    # 4. Increment usage (Atomic update to API Key)
    # The DB Trigger 'trg_sync_user_quota' will automatically update user.quota_used
    db_key.total_requests = models.APIKey.total_requests + 1
    db.commit()

    # 5. Check Low Quota Alert (Otomasi)
    check_quota_alert(user, db)
    
    return db_key

def check_quota_alert(user: models.User, db: Session):
    prefs = user.preferences or {}
    threshold = prefs.get("alert_threshold", 0)
    remaining = user.quota_limit - user.quota_used

    # Only alert if remaining is at or below threshold and hasn't alerted for this level yet
    if threshold > 0 and remaining <= threshold:
        last_alert = prefs.get("last_alert_at")
        # Simple cooldown: Once per 24h OR if top-up happened (reset by checking if last_alert_quota < remaining)
        # For simplicity in EAS: if not alerted for this specific session/threshold state
        last_alert_quota = prefs.get("last_alert_quota", 0)
        
        if not last_alert or last_alert_quota < remaining:
             # Trigger alert!
             # Non-blocking fire and forget for the alert
             asyncio.create_task(send_notification(user))
             
             # Save alert state
             new_prefs = user.preferences.copy()
             new_prefs["last_alert_at"] = datetime.utcnow().isoformat()
             new_prefs["last_alert_quota"] = remaining
             user.preferences = new_prefs
             db.commit()

async def send_notification(user: models.User):
    webhooks = (user.preferences or {}).get("webhooks", {})
    channel = webhooks.get("channel")
    if not channel or channel == "none":
        return

    msg = f"⚠️ [ShipStream Alert] Sisa kuota Anda tinggal {user.quota_limit - user.quota_used}. Segera lakukan Top-up!"
    
    try:
        async with httpx.AsyncClient() as client:
            if channel == "telegram":
                token = webhooks.get("telegram_token")
                chat_id = webhooks.get("telegram_chat_id")
                if token and chat_id:
                    await client.post(f"https://api.telegram.org/bot{token}/sendMessage", json={"chat_id": chat_id, "text": msg})
            elif channel == "webhook":
                url = webhooks.get("url")
                if url:
                    await client.post(url, json={"message": msg, "type": "low_quota"})
    except Exception as e:
        print(f"Failed to send automated alert: {e}")
