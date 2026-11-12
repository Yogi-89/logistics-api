"""Print a few seeded cities together with their RajaOngkir IDs.

Run from the repository root:  python scripts/verify_cities.py
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.database import SessionLocal  # noqa: E402
from app.models.base import City  # noqa: E402

db = SessionLocal()
cities = db.query(City).limit(10).all()
for c in cities:
    print(f"ID: {c.id}, Name: {c.name}, RajaOngkir ID: {c.rajaongkir_id}")
db.close()
