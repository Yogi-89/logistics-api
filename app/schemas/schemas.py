from pydantic import BaseModel, EmailStr, Field, field_validator
import re
from typing import Optional, List
from datetime import datetime

# --- User Schemas ---
class UserBase(BaseModel):
    username: str
    email: EmailStr
    phone_number: Optional[str] = None

class UserCreate(UserBase):
    password: str
    captcha_token: Optional[str] = None

class User(UserBase):
    id: int
    is_active: bool
    is_verified: bool
    quota_limit: int
    quota_used: int
    preferences: Optional[dict] = {}
    password_updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True

class PreferencesUpdate(BaseModel):
    lang: Optional[str] = None
    timezone: Optional[str] = None
    currency: Optional[str] = None
    alert_threshold: Optional[int] = None
    webhooks: Optional[dict] = None

class WebhookTest(BaseModel):
    channel: str
    url: Optional[str] = None
    bot_token: Optional[str] = None
    chat_id: Optional[str] = None

# --- API Key Schemas ---
class APIKeyCreate(BaseModel):
    label: str
    request_limit: Optional[int] = None

class APIKeyUpdate(BaseModel):
    label: Optional[str] = None
    request_limit: Optional[int] = None
    ip_whitelist: Optional[str] = None
    is_active: Optional[bool] = None

class APIKey(BaseModel):
    id: int
    key: str
    label: str
    is_active: bool
    created_at: datetime
    total_requests: int
    request_limit: Optional[int]
    ip_whitelist: Optional[str] = None
    status: str

    class Config:
        from_attributes = True

# --- Token Schemas ---
class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    username: Optional[str] = None

# --- Logistics Schemas ---
class City(BaseModel):
    id: int
    name: str
    province: str
    type: Optional[str] = None
    postal_code: Optional[str] = None

    class Config:
        from_attributes = True

class Courier(BaseModel):
    id: int
    name: str
    code: str
    logo_url: Optional[str] = None
    description: Optional[str] = None

    class Config:
        from_attributes = True

class CostRequest(BaseModel):
    origin: int
    destination: int
    weight: int = Field(..., gt=0, le=70000)
    courier: str
    length: Optional[int] = Field(None, gt=0, le=300)
    width: Optional[int] = Field(None, gt=0, le=300)
    height: Optional[int] = Field(None, gt=0, le=300)

class TrackingHistory(BaseModel):
    status: str
    location: str
    timestamp: datetime

class TrackingInfo(BaseModel):
    awb: str
    courier: str
    status: str
    service_type: Optional[str] = None
    weight_gram: Optional[int] = None
    shipping_cost: Optional[float] = None
    sender_name: Optional[str] = None
    receiver_name: Optional[str] = None
    receiver_address: Optional[str] = None
    history: List[dict]

    class Config:
        from_attributes = True

class ShipmentCreate(BaseModel):
    courier_id: int
    origin_city_id: int
    destination_city_id: int
    service_type: str = Field(..., pattern=r"^(REG|EXP|YES|OKE|SPS)$")
    weight_gram: int = Field(..., gt=0, le=70000)
    length_cm: Optional[int] = Field(None, gt=0, le=300)
    width_cm: Optional[int] = Field(None, gt=0, le=300)
    height_cm: Optional[int] = Field(None, gt=0, le=300)
    insurance_value: Optional[float] = Field(0.0, ge=0.0)
    sender_name: str = Field(..., min_length=2)
    sender_phone: str
    sender_address: str = Field(..., min_length=10)
    sender_postal_code: Optional[str] = None
    receiver_name: str = Field(..., min_length=2)
    receiver_phone: str
    receiver_address: str = Field(..., min_length=10)
    receiver_postal_code: Optional[str] = None

    @field_validator("sender_phone", "receiver_phone")
    @classmethod
    def validate_phone(cls, v):
        if not re.match(r"^(\+62|62|0)8[1-9][0-9]{6,11}$", v):
            raise ValueError("Invalid Indonesian phone number format")
        return v

    @field_validator("sender_postal_code", "receiver_postal_code")
    @classmethod
    def validate_postal(cls, v):
        if v is not None and not re.match(r"^\d{5}$", v):
            raise ValueError("Postal code must be exactly 5 digits")
        return v

# --- Billing Schemas ---
class TopupRequest(BaseModel):
    api_key_id: Optional[int] = None
    amount: int
    quota_added: int
    payment_method: Optional[str] = "midtrans" # midtrans, crypto
    chain: Optional[str] = None # For crypto: polygon, arbitrum
    symbol: Optional[str] = None # USDT, USDC
    tx_metadata: Optional[dict] = None

class Transaction(BaseModel):
    id: int
    order_id: str
    api_key_id: Optional[int] = None
    amount: int
    quota_added: int
    payment_method: str
    tx_metadata: Optional[dict] = None
    tx_hash: Optional[str] = None
    actual_crypto_amount: Optional[float] = None
    actual_saldo: Optional[int] = None
    status: str
    status_reason: Optional[str] = None
    created_at: datetime
    expires_at: Optional[datetime] = None

    class Config:
        from_attributes = True

# --- Verification Schemas ---
class VerificationCode(BaseModel):
    code: str
    channel: str # email, phone
    type: str # registration, password_reset, security_update

class ResendCodeRequest(BaseModel):
    email: EmailStr
    type: str = "registration"

# --- Profile Update Request Schemas ---
class UpdatePasswordRequest(BaseModel):
    password: str
    new_password: str
    otp_email: str = ""
    otp_phone: str = ""

class UpdateEmailRequest(BaseModel):
    password: str
    new_email: str
    otp_email: str = ""
    otp_phone: str = ""

class UpdatePhoneRequest(BaseModel):
    password: str
    new_phone: str
    otp_email: str = ""
    otp_phone: str = ""
