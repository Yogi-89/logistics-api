"""
tests/conftest.py
Konfigurasi pytest session-wide.

Masalah: SlowAPI membaca REDIS_URL dari env saat modul limiter.py diimport.
Solusi: Patch env var DAN patch limiter object agar pakai memory storage.
"""

import os
import pytest

# 1. Set env SEBELUM import apapun dari app
os.environ["REDIS_URL"] = "memory://"
os.environ.setdefault("DATABASE_URL", "sqlite:///:memory:")
os.environ.setdefault("SECRET_KEY", "test_secret_key")
os.environ.setdefault("RAJA_ONGKIR_API_KEY", "your_raja_ongkir_key_here")


@pytest.fixture(autouse=True, scope="session")
def patch_limiter_storage():
    """
    Patch storage limiter SlowAPI ke in-memory agar tidak butuh Redis.
    """
    from limits.storage import MemoryStorage
    from app.utils.limiter import limiter

    limiter._storage = MemoryStorage()
    limiter.enabled = False
    yield
    limiter.enabled = True


@pytest.fixture(autouse=True)
def reset_limiter_storage():
    """
    Reset the in-memory storage before each test to avoid rate-limit
    state leaking between tests.
    """
    from limits.storage import MemoryStorage
    from app.utils.limiter import limiter

    limiter._storage = MemoryStorage()
    limiter.reset()
    yield
