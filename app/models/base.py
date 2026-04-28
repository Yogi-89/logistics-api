from sqlalchemy import Column, Integer, String, Boolean, ForeignKey, JSON, DateTime, Float, Numeric
from sqlalchemy.orm import relationship
from datetime import datetime
from app.database import Base

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True)
    email = Column(String, unique=True, index=True)
    phone_number = Column(String, unique=True, index=True, nullable=True)
    hashed_password = Column(String)
    is_active = Column(Boolean, default=True)
    is_verified = Column(Boolean, default=False)

    # Global Quota Pool
    quota_limit = Column(Integer, default=1000) # Default free initial quota or 0
    quota_used = Column(Integer, default=0)

    # Preferences & Security Metadata
    preferences = Column(JSON, default={}) # Stores: lang, timezone, currency, alert_threshold, webhooks
    password_updated_at = Column(DateTime, default=datetime.utcnow)
    
    # OTP Tracking (Registration)
    resend_count = Column(Integer, default=0)
    last_resend_at = Column(DateTime, nullable=True)

    # OTP Tracking (Security Core)
    security_resend_count = Column(Integer, default=0)
    security_last_resend_at = Column(DateTime, nullable=True)

    api_keys = relationship("APIKey", back_populates="owner", cascade="all, delete-orphan")
    verification_codes = relationship("VerificationCode", back_populates="user", cascade="all, delete-orphan")
    sessions = relationship("UserSession", back_populates="user", cascade="all, delete-orphan")

class APIKey(Base):
    __tablename__ = "api_keys"

    id = Column(Integer, primary_key=True, index=True)
    key = Column(String, unique=True, index=True)
    label = Column(String)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"))
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Analytics & Usage (Per-Key)
    total_requests = Column(Integer, default=0)
    request_limit = Column(Integer, nullable=True) # Optional per-key limit (Spending limit)
    ip_whitelist = Column(String, nullable=True) # Comma separated list
    status = Column(String, default="active") # active, suspended, limited

    owner = relationship("User", back_populates="api_keys")

class City(Base):
    __tablename__ = "cities"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True)
    province = Column(String)
    type = Column(String) # Kota, Kabupaten
    postal_code = Column(String)
    rajaongkir_id = Column(Integer, nullable=True)

    subdistricts = relationship("Subdistrict", back_populates="city")

class Subdistrict(Base):
    __tablename__ = "subdistricts"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String)
    city_id = Column(Integer, ForeignKey("cities.id", ondelete="CASCADE"))
    
    city = relationship("City", back_populates="subdistricts")

class Courier(Base):
    __tablename__ = "couriers"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String)
    code = Column(String, unique=True)
    logo_url = Column(String, nullable=True)
    description = Column(String, nullable=True)

class Tracking(Base):
    __tablename__ = "tracking"

    id = Column(Integer, primary_key=True, index=True)
    awb = Column(String, unique=True, index=True)
    courier_id = Column(Integer, ForeignKey("couriers.id"))
    status = Column(String)
    origin_city_id = Column(Integer, ForeignKey("cities.id"))
    destination_city_id = Column(Integer, ForeignKey("cities.id"))
    
    # Scale-up: Detailed Logistics Data
    service_type = Column(String, nullable=True) # REG, YES, OKE
    weight_gram = Column(Integer, default=1000)
    length_cm = Column(Integer, nullable=True)
    width_cm = Column(Integer, nullable=True)
    height_cm = Column(Integer, nullable=True)
    insurance_value = Column(Float, default=0.0)
    shipping_cost = Column(Float, default=0.0)
    
    # Origin & Destination Detail
    sender_name = Column(String, nullable=True)
    sender_phone = Column(String, nullable=True)
    sender_address = Column(String, nullable=True)
    sender_postal_code = Column(String, nullable=True)
    sender_lat = Column(Float, nullable=True)
    sender_long = Column(Float, nullable=True)

    receiver_name = Column(String, nullable=True)
    receiver_phone = Column(String, nullable=True)
    receiver_address = Column(String, nullable=True)
    receiver_postal_code = Column(String, nullable=True)
    receiver_lat = Column(Float, nullable=True)
    receiver_long = Column(Float, nullable=True)

    last_updated = Column(DateTime, default=datetime.utcnow)
    history = Column(JSON) # List of status updates

class Transaction(Base):
    __tablename__ = "transactions"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"))
    api_key_id = Column(Integer, ForeignKey("api_keys.id", ondelete="SET NULL"), nullable=True)
    order_id = Column(String, unique=True, index=True)
    amount = Column(Integer)
    quota_added = Column(Integer)
    payment_method = Column(String, default="midtrans") # midtrans, crypto
    tx_metadata = Column(JSON, nullable=True) # For crypto: {address, chain, symbol}
    tx_hash = Column(String, nullable=True, index=True) # Blockchain Transaction ID
    actual_crypto_amount = Column(Float, nullable=True) # Real crypto value (e.g. 0.29 USDC)
    actual_saldo = Column(Numeric(15, 2), nullable=True) # Real IDR value for QRIS (Industry Standard)
    status = Column(String, default="pending") # pending, awaiting_verification, success, failed, expired
    status_reason = Column(String, nullable=True) # e.g., "Cancel by user", "Kadaluarsa"
    created_at = Column(DateTime, default=datetime.utcnow)
    expires_at = Column(DateTime, nullable=True)  # 1-hour payment window

    # Relationships
    owner = relationship("User")
    api_key = relationship("APIKey")

class VerificationCode(Base):
    __tablename__ = "verification_codes"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"))
    code = Column(String)
    channel = Column(String) # email, phone
    type = Column(String) # registration, password_reset, security_update
    is_used = Column(Boolean, default=False)
    expires_at = Column(DateTime)
    created_at = Column(DateTime, default=datetime.utcnow)

    user = relationship("User", back_populates="verification_codes")

class UserSession(Base):
    __tablename__ = "user_sessions"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"))
    jti = Column(String, unique=True, index=True) # JWT Unique ID for revocation
    device_info = Column(String) # User-Agent summary
    ip_address = Column(String)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    last_active = Column(DateTime, default=datetime.utcnow)

    user = relationship("User", back_populates="sessions")
