import os
import subprocess
import sys

import uvicorn


def prepare_database() -> None:
    database_url = os.getenv("DATABASE_URL")
    if database_url:
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
