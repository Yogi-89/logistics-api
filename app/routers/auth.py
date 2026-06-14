from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.orm import Session
from fastapi.security import OAuth2PasswordRequestForm
from app.database import get_db
from app.models import base as models
from app.schemas import schemas
from app.utils import security
from app.utils.security_utils import verify_turnstile, create_verification_code
from datetime import datetime, timedelta
import os
from pydantic import BaseModel
from app.utils.env import get_bool_env

class LoginJSON(BaseModel):
    username: str
    password: str

router = APIRouter(prefix="/auth", tags=["Authentication"])

@router.post("/register", response_model=schemas.User)
async def register(user: schemas.UserCreate, db: Session = Depends(get_db)):
    # 1. Verify Captcha
    if not await verify_turnstile(user.captcha_token):
        raise HTTPException(status_code=400, detail="Captcha verification failed")

    # 2. Check existing user
    db_user = db.query(models.User).filter(models.User.username == user.username).first()
    if db_user:
        raise HTTPException(status_code=400, detail="Username already registered")
    
    db_email = db.query(models.User).filter(models.User.email == user.email).first()
    if db_email:
        raise HTTPException(status_code=400, detail="Email already registered")
    
    hashed_password = security.get_password_hash(user.password)
    new_user = models.User(
        username=user.username,
        email=user.email,
        phone_number=user.phone_number,
        hashed_password=hashed_password,
        is_verified=False
    )
    try:
        db.add(new_user)
        db.commit()
        db.refresh(new_user)
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Gagal menyimpan user: {str(e)}")

    # 3. Create & 'Send' Verification Code
    create_verification_code(db, new_user.id, "email", "registration")
    
    return new_user

@router.post("/verify-code")
def verify_code(req: schemas.VerificationCode, db: Session = Depends(get_db)):
    """Validates the OTP and activates the user account."""
    db_code = db.query(models.VerificationCode).filter(
        models.VerificationCode.code == req.code,
        models.VerificationCode.channel == req.channel,
        models.VerificationCode.is_used == False,
        models.VerificationCode.expires_at > datetime.utcnow()
    ).first()

    if not db_code:
        raise HTTPException(status_code=400, detail="Kode verifikasi salah atau sudah kedaluwarsa")

    # Activate User
    user = db.query(models.User).filter(models.User.id == db_code.user_id).first()
    if user:
        user.is_verified = True
    
    try:
        db_code.is_used = True
        db.commit()
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail="Gagal memperbarui status verifikasi")
    
    return {"message": "Akun berhasil diverifikasi!", "status": "verified"}

@router.post("/login", response_model=schemas.Token)
async def login(request: Request, login_data: LoginJSON, db: Session = Depends(get_db)):
    # 1. Verify Turnstile
    captcha_token = request.headers.get("X-Captcha-Token")
    if not await verify_turnstile(captcha_token):
        raise HTTPException(status_code=400, detail="Security validation failed")

    user = db.query(models.User).filter(
        (models.User.username == login_data.username) | 
        (models.User.email == login_data.username)
    ).first()
    
    if not user or not security.verify_password(login_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    if not user.is_verified:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="NEED_VERIFICATION", # Specific code for Frontend detection
        )
    
    access_token_expires = timedelta(minutes=security.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token, jti = security.create_access_token(
        data={"sub": user.username}, expires_delta=access_token_expires
    )

    # Track session in DB
    user_agent = request.headers.get("user-agent", "Unknown Device")
    client_ip = request.client.host
    
    new_session = models.UserSession(
        user_id=user.id,
        jti=jti,
        device_info=user_agent,
        ip_address=client_ip
    )
    try:
        db.add(new_session)
        db.commit()
    except Exception as e:
        db.rollback()
        # Non-critical: Login tetap berhasil meskipun session tracking gagal
        pass

    return {"access_token": access_token, "token_type": "bearer"}

@router.post("/resend-registration-code")
async def resend_registration_code(req: schemas.ResendCodeRequest, db: Session = Depends(get_db)):
    """Resends the registration OTP with rate limiting and exponential backoff."""
    user = db.query(models.User).filter(models.User.email == req.email).first()
    if not user:
        raise HTTPException(status_code=404, detail="Email tidak terdaftar")
    
    if user.is_verified:
        raise HTTPException(status_code=400, detail="Akun sudah terverifikasi, silakan login")
        
    # 1. Scale Up Protection & Reset (3x limit per 24 hours)
    now = datetime.utcnow()
    if user.last_resend_at:
        hours_passed = (now - user.last_resend_at).total_seconds() / 3600
        if hours_passed >= 24:
            user.resend_count = 0
            db.commit()

    if user.resend_count >= 3:
        raise HTTPException(status_code=429, detail="Batas pengiriman ulang kode telah tercapai (Max 3x per 24 jam). Silakan coba lagi besok.")
        
    # Rate Limiting & Backoff check
    now = datetime.utcnow()
    if user.last_resend_at:
        # Initial wait: 60s, then 120s, then 180s
        delay_seconds = 60 * (user.resend_count + 1)
        next_allowed = user.last_resend_at + timedelta(seconds=delay_seconds)
        
        if now < next_allowed:
            wait_time = int((next_allowed - now).total_seconds())
            raise HTTPException(status_code=429, detail=f"Silakan tunggu {wait_time} detik sebelum mengirim ulang")

    # Generate & Send Code
    create_verification_code(db, user.id, "email", "registration")
    
    # Update Tracking
    try:
        user.resend_count += 1
        user.last_resend_at = now
        db.commit()
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail="Gagal memperbarui data resend")
    
    return {
        "message": "Kode baru telah dikirim!",
        "resend_count": user.resend_count,
        "next_delay": 60 * (user.resend_count + 1)
    }
 
@router.get("/debug/otp/test-ping")
def debug_test_ping():
    """
    Utility endpoint for the frontend to check if debug mode is active/accessible.
    """
    if not get_bool_env("DEBUG_MODE"):
        raise HTTPException(status_code=403, detail="Debug features disabled")
    return {"status": "ok", "mode": "debug"}

@router.get("/debug/otp/{username}")
def get_debug_otp(username: str, db: Session = Depends(get_db)):
    """
    DEBUG ONLY: Get the latest active OTP for a user.
    Disabled in production (requires DEBUG_MODE=True in .env).
    """
    if not get_bool_env("DEBUG_MODE"):
        raise HTTPException(status_code=403, detail="Debug endpoint is disabled in production")
    
    user = db.query(models.User).filter(models.User.username == username).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
        
    code = db.query(models.VerificationCode).filter(
        models.VerificationCode.user_id == user.id,
        models.VerificationCode.is_used == False
    ).order_by(models.VerificationCode.created_at.desc()).first()
    
    if not code:
        raise HTTPException(status_code=404, detail="No active OTP found for this user")
        
    return {
        "username": username,
        "code": code.code,
        "type": code.type,
        "channel": code.channel,
        "expires_at": code.expires_at,
        "debug_note": "This endpoint should be disabled in production by setting DEBUG_MODE=False"
    }
