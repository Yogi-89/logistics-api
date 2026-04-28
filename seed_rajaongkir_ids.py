import os
import httpx
import psycopg2
from dotenv import load_dotenv

load_dotenv()

# 36 kota yang ada di seed_cities.py
CITIES = [
    "Banda Aceh", "Medan", "Padang", "Pekanbaru", "Palembang",
    "Bandar Lampung", "Batam", "Jakarta Pusat", "Jakarta Selatan",
    "Jakarta Barat", "Jakarta Timur", "Jakarta Utara", "Bandung",
    "Bekasi", "Depok", "Tangerang", "Semarang", "Surakarta",
    "Yogyakarta", "Surabaya", "Malang", "Sidoarjo", "Denpasar",
    "Mataram", "Kupang", "Pontianak", "Banjarmasin", "Samarinda",
    "Balikpapan", "Makassar", "Manado", "Palu", "Kendari",
    "Jayapura", "Sorong", "Ambon"
]

def seed():
    api_key = os.getenv("RAJA_ONGKIR_API_KEY")
    db_url = os.getenv("DATABASE_URL")

    if not api_key or api_key == "your_raja_ongkir_key_here":
        print("RAJA_ONGKIR_API_KEY not set in .env")
        return

    conn = psycopg2.connect(db_url)
    cur = conn.cursor()

    for city_name in CITIES:
        try:
            resp = httpx.get(
                "https://rajaongkir.komerce.id/api/v1/destination/domestic-destination",
                headers={"key": api_key},
                params={"search": city_name, "limit": 50, "offset": 0},
                timeout=10.0
            )
            data = resp.json()
            results = data.get("data", [])

            if not results:
                print(f"Not found: {city_name}")
                continue

            # Ambil ID dari hasil pertama yang city_name-nya cocok
            raja_id = None
            
            # Step 1: Try exact city_name match
            for r in results:
                ro_city = r.get("city_name", "").lower()
                if ro_city == city_name.lower():
                    raja_id = r.get("id")
                    break
            
            # Step 2: Try label match if still no exact city match
            if not raja_id:
                for r in results:
                    ro_label = r.get("label", "").lower()
                    if city_name.lower() in ro_label:
                        raja_id = r.get("id")
                        break

            if raja_id is None:
                # Fallback: pakai hasil pertama
                raja_id = results[0].get("id")
                print(f"Fallback to first result for: {city_name} -> id={raja_id} ({results[0].get('label')})")
            else:
                print(f"OK {city_name} -> rajaongkir_id={raja_id}")

            cur.execute(
                "UPDATE cities SET rajaongkir_id = %s WHERE name = %s",
                (raja_id, city_name)
            )
        except Exception as e:
            print(f"Error for {city_name}: {e}")

    conn.commit()
    cur.close()
    conn.close()
    print("\nSeeding rajaongkir_id finished!")

if __name__ == "__main__":
    seed()
