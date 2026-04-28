from app.database import SessionLocal
from app.models.base import City

db = SessionLocal()
cities = db.query(City).limit(10).all()
for c in cities:
    print(f"ID: {c.id}, Name: {c.name}, RajaOngkir ID: {c.rajaongkir_id}")
db.close()
