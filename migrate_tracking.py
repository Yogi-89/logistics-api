import os
from dotenv import load_dotenv
import psycopg2

load_dotenv()

def migrate():
    try:
        conn = psycopg2.connect(os.getenv('DATABASE_URL'))
        cur = conn.cursor()
        
        print("Migrating tracking table...")
        
        # Add columns if not exist
        columns = [
            ("sender_name", "VARCHAR"),
            ("sender_phone", "VARCHAR"),
            ("receiver_name", "VARCHAR"),
            ("receiver_phone", "VARCHAR"),
            ("receiver_address", "VARCHAR")
        ]
        
        for col, col_type in columns:
            try:
                cur.execute(f"ALTER TABLE tracking ADD COLUMN {col} {col_type}")
                print(f"Added column: {col}")
            except Exception as e:
                print(f"Column {col} might already exist: {e}")
                conn.rollback()
                continue
        
        # Seed a sample record for the demo
        print("Seeding sample tracking record for PDF demo...")
        
        # First, ensure we have a courier and cities (Audit showed we have them)
        # We'll just update any existing tracking or insert a new one
        cur.execute("SELECT id FROM couriers LIMIT 1")
        courier_id = cur.fetchone()[0]
        
        cur.execute("SELECT id FROM cities LIMIT 2")
        cities = cur.fetchall()
        origin_id = cities[0][0]
        dest_id = cities[1][0]
        
        cur.execute("""
            INSERT INTO tracking (awb, courier_id, status, origin_city_id, destination_city_id, sender_name, sender_phone, receiver_name, receiver_phone, receiver_address, history)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            ON CONFLICT (awb) DO UPDATE SET
                sender_name = EXCLUDED.sender_name,
                sender_phone = EXCLUDED.sender_phone,
                receiver_name = EXCLUDED.receiver_name,
                receiver_phone = EXCLUDED.receiver_phone,
                receiver_address = EXCLUDED.receiver_address
        """, (
            "SHIP-ELITE-999", courier_id, "ON_PROCESS", origin_id, dest_id,
            "Yogi Logistics Center", "08123456789",
            "Bapak Budi Santoso", "08556677889",
            "Jl. Mawar Indah No. 45, Surabaya, Jawa Timur",
            '[{"status": "PICKED_UP", "time": "2024-04-20 10:00:00", "location": "Jakarta"}]'
        ))
        
        conn.commit()
        print("Migration and seeding complete!")
        cur.close()
        conn.close()
    except Exception as e:
        print(f"Migration failed: {e}")

if __name__ == "__main__":
    migrate()
