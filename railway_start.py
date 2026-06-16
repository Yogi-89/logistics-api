import os
import subprocess
import sys

import uvicorn

from app.utils.env import get_database_url


def seed_reference_data_if_empty() -> None:
    from app.database import SessionLocal
    from app.models import base as models

    db = SessionLocal()
    try:
        city_count = db.query(models.City).count()
        courier_count = db.query(models.Courier).count()
    finally:
        db.close()

    if city_count == 0 and courier_count == 0:
        from app.utils.seed_data import seed

        seed()


def prepare_database() -> None:
    database_url = get_database_url()
    if not database_url.startswith("sqlite"):
        subprocess.run([sys.executable, "-m", "alembic", "upgrade", "head"], check=True)
        seed_reference_data_if_empty()
        return

    from app.database import Base, engine
    import app.models.base  # noqa: F401 - register models before create_all

    Base.metadata.create_all(bind=engine)
    seed_reference_data_if_empty()


if __name__ == "__main__":
    prepare_database()
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=int(os.getenv("PORT", "8000")),
    )
