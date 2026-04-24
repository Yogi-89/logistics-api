from app.database import SessionLocal
from app.models import base as models
from sqlalchemy import text

def seed():
    db = SessionLocal()
    
    # Clear existing data to ensure new columns are populated
    try:
        db.query(models.Tracking).delete()
        db.query(models.Courier).delete()
        db.query(models.City).delete()
        # Normalize existing users: sync quota_used with sum of keys instead of just 0
        users_res = db.execute(text("SELECT id FROM users")).fetchall()
        for u in users_res:
            u_id = u[0]
            sum_requests = db.execute(text("SELECT SUM(total_requests) FROM api_keys WHERE user_id = :uid"), {"uid": u_id}).scalar() or 0
            db.execute(text("UPDATE users SET quota_used = :val WHERE id = :uid"), {"val": sum_requests, "uid": u_id})
        
        db.execute(text("UPDATE users SET quota_limit = 1000 WHERE quota_limit IS NULL"))
        db.commit()
        print("Existing users normalized and usage synced from keys.")
    except Exception as e:
        print(f"Warning during clear: {e}")
        db.rollback()

    # Rich Cities Data
    cities = [
        models.City(name="Surabaya", province="Jawa Timur", type="Kota", postal_code="60111-60299"),
        models.City(name="Jakarta Pusat", province="DKI Jakarta", type="Kota", postal_code="10110-10750"),
        models.City(name="Bandung", province="Jawa Barat", type="Kota", postal_code="40111-40294"),
        models.City(name="Yogyakarta", province="DIY", type="Kota", postal_code="55111-55283"),
        models.City(name="Semarang", province="Jawa Tengah", type="Kota", postal_code="50111-50277"),
        models.City(name="Sidoarjo", province="Jawa Timur", type="Kabupaten", postal_code="61211-61276"),
        models.City(name="Medan", province="Sumatera Utara", type="Kota", postal_code="20111-20259"),
        models.City(name="Makassar", province="Sulawesi Selatan", type="Kota", postal_code="90111-90245"),
        models.City(name="Denpasar", province="Bali", type="Kota", postal_code="80111-80239"),
        models.City(name="Tangerang", province="Banten", type="Kota", postal_code="15111-15159"),
    ]
    
    # Rich Couriers Data with Logos & Descriptions
    couriers = [
        models.Courier(
            name="JNE Express", 
            code="jne", 
            logo_url="https://images.unsplash.com/photo-1531403009284-440f080d1e12?q=80&w=100&auto=format&fit=crop",
            description="Jalur Nugraha Ekakurir (JNE) adalah salah satu kurir terbesar di Indonesia."
        ),
        models.Courier(
            name="J&T Express", 
            code="jnt", 
            logo_url="https://images.unsplash.com/photo-1566241440091-ec10de8db2e1?q=80&w=100",
            description="Fokus pada pengiriman e-commerce yang cepat dan efisien."
        ),
        models.Courier(
            name="SiCepat", 
            code="sicepat", 
            logo_url="https://images.unsplash.com/photo-1590086782792-42dd2350140d?q=80&w=100",
            description="SiCepat Ekspres menawarkan layanan jemput paket di tempat."
        ),
        models.Courier(
            name="POS Indonesia", 
            code="pos", 
            logo_url="https://images.unsplash.com/photo-1506784983877-45594efa4cbe?q=80&w=100",
            description="Badan Usaha Milik Negara yang menangani layanan pos nasional."
        ),
        models.Courier(
            name="AnterAja", 
            code="anteraja", 
            logo_url="https://images.unsplash.com/photo-1586769852836-bc069f19e1b6?q=80&w=100",
            description="Layanan pengiriman berbasis teknologi dengan kurir Satria."
        ),
    ]

    try:
        db.add_all(cities)
        db.add_all(couriers)
        db.commit()
        print("Cities and Couriers seeded with rich metadata!")
        
        # Add dummy tracking
        jne = db.query(models.Courier).filter(models.Courier.code == "jne").first()
        track = models.Tracking(
            awb="LGS-12345678",
            courier_id=jne.id if jne else 1,
            status="DELIVERED",
            history=[
                {"status": "PICKED_UP", "location": "Surabaya Hub", "timestamp": "2024-05-01T10:00:00"},
                {"status": "IN_TRANSIT", "location": "Jakarta Gateway", "timestamp": "2024-05-02T08:00:00"},
                {"status": "OUT_FOR_DELIVERY", "location": "Jakarta Pusat DC", "timestamp": "2024-05-03T09:30:00"},
                {"status": "DELIVERED", "location": "Alamat Penerima", "timestamp": "2024-05-03T11:45:00"}
            ]
        )
        db.add(track)
        db.commit()
        print("Tracking dummy seeded!")

    except Exception as e:
        print(f"Error seeding: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    seed()
