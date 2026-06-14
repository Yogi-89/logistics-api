import random
import string
import httpx
import os
from datetime import datetime, timedelta
from app.models import base as models
from app.utils.mailer import send_otp_email
from sqlalchemy.orm import Session
import sys

CLOUDFLARE_SECRET = os.getenv("CLOUDFLARE_SECRET")

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
        return True
        
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                "https://challenges.cloudflare.com/turnstile/v0/siteverify",
                data={
                    "secret": CLOUDFLARE_SECRET,
                    "response": token,
                    "remoteip": remote_ip
                }
            )
            result = response.json()
            return result.get("success", False)
    except Exception as e:
        print(f"Captcha Verification Error: {e}")
        return False

def generate_otp(length: int = 6):
    """Generate a numeric OTP code."""
    return "".join(random.choices(string.digits, k=length))

def create_verification_code(db: Session, user_id: int, channel: str, code_type: str = "registration"):
    """
    Creates a new verification code in the database and 'sends' it.
    (Simulated delivery to console for local EAS testing).
    """
    code = generate_otp()
    expires_at = datetime.utcnow() + timedelta(minutes=15)
    
    db_code = models.VerificationCode(
        user_id=user_id,
        code=code,
        channel=channel,
        type=code_type,
        expires_at=expires_at
    )
    db.add(db_code)
    db.commit()
    
    # Professional Gateway Simulation (Local Development)
    gateway = "SMS-GATEWAY" if channel != "email" else "MAIL-GATEWAY"
    provider = "Twilio-Sim" if channel != "email" else "SendGrid-Sim"
    
    print(f"\n[{gateway}] ---------------------------", flush=True)
    print(f" Provider: {provider}", flush=True)
    print(f" To      : {channel}", flush=True)
    print(f" Code    : {code}", flush=True)
    print(f" Type    : {code_type}", flush=True)
    print(f"---------------------------------------\n", flush=True)
    
    # Real Delivery via Resend (Only for Email)
    if channel == "email":
        # Get user email
        user = db.query(models.User).filter(models.User.id == user_id).first()
        if user and user.email:
            send_otp_email(user.email, code)
    
    return code
