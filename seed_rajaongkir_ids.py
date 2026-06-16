import httpx

from app.database import SessionLocal
from app.models import base as models
from app.utils.env import clean_env


def _pick_destination_id(city_name: str, results: list[dict]) -> int | None:
    normalized_city = city_name.lower()

    for row in results:
        if row.get("city_name", "").lower() == normalized_city:
            return row.get("id")

    for row in results:
        if normalized_city in row.get("label", "").lower():
            return row.get("id")

    if results:
        return results[0].get("id")

    return None


def seed() -> None:
    api_key = clean_env("RAJA_ONGKIR_API_KEY")
    if not api_key:
        print("RAJA_ONGKIR_API_KEY not set; skipping RajaOngkir ID seed.")
        return

    db = SessionLocal()
    try:
        cities = db.query(models.City).filter(models.City.rajaongkir_id.is_(None)).all()
        if not cities:
            print("RajaOngkir IDs already seeded.")
            return

        print(f"Seeding RajaOngkir IDs for {len(cities)} cities...")

        with httpx.Client(timeout=10.0) as client:
            for city in cities:
                try:
                    resp = client.get(
                        "https://rajaongkir.komerce.id/api/v1/destination/domestic-destination",
                        headers={"key": api_key},
                        params={"search": city.name, "limit": 50, "offset": 0},
                    )
                    resp.raise_for_status()
                    destination_id = _pick_destination_id(city.name, resp.json().get("data", []))
                    if destination_id is None:
                        print(f"RajaOngkir destination not found: {city.name}")
                        continue

                    city.rajaongkir_id = destination_id
                    print(f"OK {city.name} -> rajaongkir_id={destination_id}")
                except Exception as exc:
                    print(f"Error seeding RajaOngkir ID for {city.name}: {exc}")

        db.commit()
        print("RajaOngkir ID seeding finished.")
    except Exception as exc:
        db.rollback()
        print(f"RajaOngkir ID seeding failed: {exc}")
    finally:
        db.close()


if __name__ == "__main__":
    seed()
