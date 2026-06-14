import os
import subprocess
import sys

import uvicorn

from app.utils.env import get_database_url


def prepare_database() -> None:
    database_url = get_database_url()
    if not database_url.startswith("sqlite"):
        subprocess.run([sys.executable, "-m", "alembic", "upgrade", "head"], check=True)
        return

    from app.database import Base, engine
    import app.models.base  # noqa: F401 - register models before create_all

    Base.metadata.create_all(bind=engine)


if __name__ == "__main__":
    prepare_database()
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=int(os.getenv("PORT", "8000")),
    )
