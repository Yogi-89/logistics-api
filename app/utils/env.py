import os


PLACEHOLDER_MARKERS = (
    "your_",
    "xxxxx",
    "user:password",
    "@host",
    ":port",
    "database_name",
)


def clean_env(name: str) -> str | None:
    value = os.getenv(name)
    if value is None:
        return None

    value = value.strip()
    if not value:
        return None

    lowered = value.lower()
    if any(marker in lowered for marker in PLACEHOLDER_MARKERS):
        print(f"[Config] WARNING: ignoring placeholder value for {name}.")
        return None

    return value


def get_database_url() -> str:
    return clean_env("DATABASE_URL") or "sqlite:///./test_logistics.db"


def get_redis_url() -> str:
    return clean_env("REDIS_URL") or "memory://"


def get_int_env(name: str, default: int) -> int:
    value = clean_env(name)
    if value is None:
        return default

    try:
        return int(value)
    except ValueError:
        print(f"[Config] WARNING: invalid integer for {name}; using {default}.")
        return default
