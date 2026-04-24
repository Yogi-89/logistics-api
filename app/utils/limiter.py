import os
from slowapi import Limiter
from slowapi.util import get_remote_address
from dotenv import load_dotenv

load_dotenv()

# Redis-backed limiter if URL is provided, otherwise falls back to in-memory
redis_url = os.getenv("REDIS_URL", "memory://")

limiter = Limiter(
    key_func=get_remote_address,
    storage_uri=redis_url
)
