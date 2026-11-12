import os
from dotenv import load_dotenv
import psycopg2

load_dotenv()

def seed_cities():
    cities_data = [
        # Sumatra
        ("Banda Aceh", "Aceh", "Kota", "23231"),
        ("Medan", "Sumatera Utara", "Kota", "20111"),
        ("Padang", "Sumatera Barat", "Kota", "25111"),
        ("Pekanbaru", "Riau", "Kota", "28111"),
        ("Palembang", "Sumatera Selatan", "Kota", "30111"),
        ("Bandar Lampung", "Lampung", "Kota", "35111"),
        ("Batam", "Kepulauan Riau", "Kota", "29432"),
        
        # Jawa
        ("Jakarta Pusat", "DKI Jakarta", "Kota", "10110"),
        ("Jakarta Selatan", "DKI Jakarta", "Kota", "12110"),
        ("Jakarta Barat", "DKI Jakarta", "Kota", "11110"),
        ("Jakarta Timur", "DKI Jakarta", "Kota", "13110"),
        ("Jakarta Utara", "DKI Jakarta", "Kota", "14110"),
        ("Bandung", "Jawa Barat", "Kota", "40111"),
        ("Bekasi", "Jawa Barat", "Kota", "17111"),
        ("Depok", "Jawa Barat", "Kota", "16411"),
        ("Tangerang", "Banten", "Kota", "15111"),
        ("Semarang", "Jawa Tengah", "Kota", "50111"),
        ("Surakarta", "Jawa Tengah", "Kota", "57111"),
        ("Yogyakarta", "DI Yogyakarta", "Kota", "55111"),
        ("Surabaya", "Jawa Timur", "Kota", "60111"),
        ("Malang", "Jawa Timur", "Kota", "65111"),
        ("Sidoarjo", "Jawa Timur", "Kabupaten", "61211"),
        
        # Bali & Nusa Tenggara
        ("Denpasar", "Bali", "Kota", "80111"),
        ("Mataram", "Nusa Tenggara Barat", "Kota", "83111"),
        ("Kupang", "Nusa Tenggara Timur", "Kota", "85111"),
        
        # Kalimantan
        ("Pontianak", "Kalimantan Barat", "Kota", "78111"),
        ("Banjarmasin", "Kalimantan Selatan", "Kota", "70111"),
        ("Samarinda", "Kalimantan Timur", "Kota", "75111"),
        ("Balikpapan", "Kalimantan Timur", "Kota", "76111"),
        
        # Sulawesi
        ("Makassar", "Sulawesi Selatan", "Kota", "90111"),
        ("Manado", "Sulawesi Utara", "Kota", "95111"),
        ("Palu", "Sulawesi Tengah", "Kota", "94111"),
        ("Kendari", "Sulawesi Tenggara", "Kota", "93111"),
        
        # Papua
        ("Jayapura", "Papua", "Kota", "99111"),
        ("Sorong", "Papua Barat", "Kota", "98411"),
        ("Ambon", "Maluku", "Kota", "97111")
    ]

    try:
        conn = psycopg2.connect(os.getenv('DATABASE_URL'))
        cur = conn.cursor()
        
        print(f"Seeding {len(cities_data)} cities...")
        
        for city in cities_data:
            # Check if exists
            cur.execute("SELECT id FROM cities WHERE name = %s", (city[0],))
            if not cur.fetchone():
                cur.execute(
                    "INSERT INTO cities (name, province, type, postal_code) VALUES (%s, %s, %s, %s)",
                    city
                )
        
        conn.commit()
        print("Seeding complete!")
        cur.close()
        conn.close()
    except Exception as e:
        print(f"Seeding failed: {e}")

if __name__ == "__main__":
    seed_cities()
