import secrets
import string
from passlib.context import CryptContext
from datetime import datetime, timedelta
from jose import JWTError, jwt
import os
import uuid
from dotenv import load_dotenv

load_dotenv()

SECRET_KEY = os.getenv("SECRET_KEY")
if not SECRET_KEY:
    # Untuk keperluan EAS, kita berikan fallback namun dengan peringatan di log console
    print("WARNING: SECRET_KEY not found in .env. Using insecure default. Please configure local .env!")
    SECRET_KEY = "yogi_prasetyo_uts_insecure_fallback"

ALGORITHM = os.getenv("ALGORITHM", "HS256")
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", 1440))

pwd_context = CryptContext(schemes=["argon2"], deprecated="auto")

def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password):
    return pwd_context.hash(password)

def create_access_token(data: dict, expires_delta: timedelta = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    
    # Add unique ID (jti) for session tracking
    jti = str(uuid.uuid4())
    to_encode.update({
        "exp": expire,
        "jti": jti
    })
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt, jti

def generate_api_key(length: int = 32):
    """Generate a high-entropy string for API Key."""
    alphabet = string.ascii_letters + string.digits
    return "".join(secrets.choice(alphabet) for _ in range(length))

def get_current_user_from_token(token: str):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        jti: str = payload.get("jti")
        if username is None:
            return None
        return {"username": username, "jti": jti}
    except JWTError:
        return None
