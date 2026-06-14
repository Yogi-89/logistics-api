import os
from slowapi import Limiter
from slowapi.util import get_remote_address
from dotenv import load_dotenv
from app.utils.env import get_redis_url

load_dotenv()

# Redis-backed limiter if URL is provided, otherwise falls back to in-memory
redis_url = get_redis_url()

limiter = Limiter(
    key_func=get_remote_address,
    storage_uri=redis_url
)
