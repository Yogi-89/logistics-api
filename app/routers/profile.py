from fastapi import APIRouter, Depends, HTTPException, status, Request, Body
from sqlalchemy.orm import Session
from sqlalchemy.orm.attributes import flag_modified
from app.database import get_db
from app.models import base as models
from app.schemas import schemas
from app.utils import security
from app.utils.dependencies import get_current_user
from app.utils.security_utils import create_verification_code
from datetime import datetime, timedelta
import httpx

router = APIRouter(prefix="/profile", tags=["User Profile"])

@router.get("/me", response_model=schemas.User)
def get_profile(current_user: models.User = Depends(get_current_user)):
    return current_user

@router.post("/request-otp")
def request_security_otp(
    action: str, 
    password: str = None,
    channel: str = None, 
    current_user: models.User = Depends(get_current_user), 
    db: Session = Depends(get_db)
):
    """
    Generates an OTP for security-sensitive actions with Scale Up protection.
    Actions: 'change_email', 'change_phone', 'change_password'
    """
    # 0. Verify Password first
    if not password or not security.verify_password(password, current_user.hashed_password):
        raise HTTPException(status_code=400, detail="Password salah")

    # 1. Scale Up Protection (3x limit per 24 hours)
    now = datetime.utcnow()
    # Reset counter if last resend was more than 24 hours ago
    if current_user.security_last_resend_at:
        hours_passed = (now - current_user.security_last_resend_at).total_seconds() / 3600
        if hours_passed >= 24:
            try:
                current_user.security_resend_count = 0
                db.commit()
            except Exception:
                db.rollback()

    if current_user.security_resend_count >= 3:
        raise HTTPException(
            status_code=429, 
            detail="Batas limit pengiriman OTP tercapai (Maks 3x per 24 jam). Silakan coba lagi besok."
        )

    # 2. Rate Limiting (Exponential Backoff for consecutive requests)
    if current_user.security_last_resend_at:
        # 60s, 120s, 180s logic
        delay_seconds = 60 * (current_user.security_resend_count + 1)
        next_allowed = current_user.security_last_resend_at + timedelta(seconds=delay_seconds)
        
        if now < next_allowed:
            wait_time = int((next_allowed - now).total_seconds())
            raise HTTPException(status_code=429, detail=f"Silakan tunggu {wait_time} detik sebelum mengirim ulang")

    # Normalize action names
    action_map = {
        "email": "change_email",
        "phone": "change_phone",
        "password": "change_password"
    }
    target_action = action_map.get(action, action)
    
    # Force EMAIL channel only for now (SMS is "Soon")
    # All security codes will go to the current user's email
    create_verification_code(db, current_user.id, "email", f"security_{target_action}")
    
    # Update Tracking
    try:
        current_user.security_resend_count += 1
        current_user.security_last_resend_at = now
        db.commit()
    except Exception:
        db.rollback()
        raise HTTPException(status_code=500, detail="Gagal memperbarui status keamanan")

    return {
        "message": "Kode OTP telah dikirim ke Email Anda.",
        "requires_dual_otp": False,
        "channels": ["email"],
        "resend_count": current_user.security_resend_count,
        "next_delay": 60 * (current_user.security_resend_count + 1)
    }

@router.put("/update-email")
def update_email(
    data: schemas.UpdateEmailRequest = Body(...), 
    current_user: models.User = Depends(get_current_user), 
    db: Session = Depends(get_db)
):
    # 1. Verify Password
    if not security.verify_password(data.password, current_user.hashed_password):
        raise HTTPException(status_code=400, detail="Password salah")
    
    # 2. Verify OTP (sent to phone for email change per user request)
    db_code = db.query(models.VerificationCode).filter(
        models.VerificationCode.user_id == current_user.id,
        models.VerificationCode.code == data.otp_email,
        models.VerificationCode.type == "security_change_email",
        models.VerificationCode.is_used == False,
        models.VerificationCode.expires_at > datetime.utcnow()
    ).first()

    if not db_code:
        raise HTTPException(status_code=400, detail="OTP salah atau kedaluwarsa")

    # 3. Update Email
    try:
        current_user.email = data.new_email
        db_code.is_used = True
        db.commit()
    except Exception:
        db.rollback()
        raise HTTPException(status_code=500, detail="Gagal memperbarui email")
    return {"message": "Email berhasil diubah"}

@router.put("/update-phone")
def update_phone(
    data: schemas.UpdatePhoneRequest = Body(...), 
    current_user: models.User = Depends(get_current_user), 
    db: Session = Depends(get_db)
):
    # 1. Verify Password
    if not security.verify_password(data.password, current_user.hashed_password):
        raise HTTPException(status_code=400, detail="Password salah")
    
    # 2. Verify OTP Email
    email_code = db.query(models.VerificationCode).filter(
        models.VerificationCode.user_id == current_user.id,
        models.VerificationCode.code == data.otp_email,
        models.VerificationCode.channel == "email",
        models.VerificationCode.type == "security_change_phone",
        models.VerificationCode.is_used == False,
        models.VerificationCode.expires_at > datetime.utcnow()
    ).first()

    if not email_code:
        raise HTTPException(status_code=400, detail="OTP Email salah atau kedaluwarsa")

    # 3. Update Phone
    try:
        current_user.phone_number = data.new_phone
        email_code.is_used = True
        db.commit()
    except Exception:
        db.rollback()
        raise HTTPException(status_code=500, detail="Gagal memperbarui nomor HP")
    return {"message": "Nomor HP berhasil diubah"}

@router.put("/update-password")
def update_password(
    data: schemas.UpdatePasswordRequest = Body(...), 
    current_user: models.User = Depends(get_current_user), 
    db: Session = Depends(get_db)
):
    # 1. Verify Current Password
    if not security.verify_password(data.password, current_user.hashed_password):
        raise HTTPException(status_code=400, detail="Password lama salah")

    # 1.1 Prevent Password Reuse
    if security.verify_password(data.new_password, current_user.hashed_password):
        raise HTTPException(
            status_code=400, 
            detail="Password baru tidak boleh sama dengan password lama"
        )

    # 2. Verify OTP Email
    email_code = db.query(models.VerificationCode).filter(
        models.VerificationCode.user_id == current_user.id,
        models.VerificationCode.code == data.otp_email,
        models.VerificationCode.channel == "email",
        models.VerificationCode.type == "security_change_password",
        models.VerificationCode.is_used == False,
        models.VerificationCode.expires_at > datetime.utcnow()
    ).first()

    if not email_code:
        raise HTTPException(status_code=400, detail="OTP Email salah atau kedaluwarsa")

    # 3. Update Password
    try:
        current_user.hashed_password = security.get_password_hash(data.new_password)
        current_user.password_updated_at = datetime.utcnow()
        email_code.is_used = True
        db.commit()
    except Exception:
        db.rollback()
        raise HTTPException(status_code=500, detail="Gagal memperbarui password")
    return {"message": "Password berhasil diperbarui"}

@router.patch("/preferences", response_model=schemas.User)
def update_preferences(
    prefs: schemas.PreferencesUpdate,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Updates user preferences (lang, timezone, alert_threshold, etc)
    Stored in a JSON column for maximum flexibility.
    """
    if current_user.preferences is None:
        current_user.preferences = {}
        
    new_prefs = current_user.preferences.copy()
    
    # Merge updates
    if prefs.lang: new_prefs["lang"] = prefs.lang
    if prefs.timezone: new_prefs["timezone"] = prefs.timezone
    if prefs.currency: new_prefs["currency"] = prefs.currency
    if prefs.alert_threshold is not None: new_prefs["alert_threshold"] = prefs.alert_threshold
    
    if prefs.webhooks:
        if "webhooks" not in new_prefs: new_prefs["webhooks"] = {}
        new_prefs["webhooks"].update(prefs.webhooks)

    try:
        current_user.preferences = new_prefs
        flag_modified(current_user, "preferences")
        db.commit()
        db.refresh(current_user)
    except Exception:
        db.rollback()
        raise HTTPException(status_code=500, detail="Gagal menyimpan preferensi")
    return current_user

@router.post("/test-webhook")
async def test_webhook(
    payload: schemas.WebhookTest,
    current_user: models.User = Depends(get_current_user),
    request: Request = None
):
    """
    Test a webhook or telegram integration before saving.
    """
    test_msg = f"🚀 [ShipStream] Test Notification for {current_user.username}. Your integration is working perfectly!"
    
    try:
        async with httpx.AsyncClient() as client:
            if payload.channel == "telegram" and payload.bot_token and payload.chat_id:
                tg_url = f"https://api.telegram.org/bot{payload.bot_token}/sendMessage"
                res = await client.post(tg_url, json={"chat_id": payload.chat_id, "text": test_msg})
                if not res.is_success:
                    return {"status": "error", "detail": f"Telegram Error: {res.text}"}
                
                # --- AUTO SET WEBHOOK ---
                host = request.base_url.netloc
                scheme = "https" # Telegram requires HTTPS
                webhook_url = f"{scheme}://{host}/api/v1/telegram/webhook/{payload.bot_token}"
                
                # Call setWebhook API
                set_webhook_url = f"https://api.telegram.org/bot{payload.bot_token}/setWebhook?url={webhook_url}"
                await client.get(set_webhook_url)
                # ------------------------
            elif payload.channel == "webhook" and payload.url:
                res = await client.post(payload.url, json={"message": test_msg, "type": "test_alert"})
                if not res.is_success:
                    return {"status": "error", "detail": f"Webhook Error: {res.status_code}"}
            else:
                return {"status": "error", "detail": "Missing configuration for selected channel"}
                
        return {"status": "success", "message": "Test notification sent successfully!"}
    except Exception as e:
        return {"status": "error", "detail": str(e)}

@router.get("/sessions")
def list_sessions(
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    List all active and inactive sessions for the current user.
    """
    return db.query(models.UserSession).filter(
        models.UserSession.user_id == current_user.id
    ).order_by(models.UserSession.last_active.desc()).all()

@router.delete("/sessions/{session_id}")
def revoke_session(
    session_id: int,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Revokes a specific session.
    """
    session = db.query(models.UserSession).filter(
        models.UserSession.id == session_id,
        models.UserSession.user_id == current_user.id
    ).first()
    
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    
    try:
        session.is_active = False
        db.commit()
    except Exception:
        db.rollback()
        raise HTTPException(status_code=500, detail="Gagal mencabut sesi")
    return {"message": "Session revoked successfully"}
