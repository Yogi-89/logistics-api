"""Reference data seeding for cities, couriers and a demo shipment.

The seed is **idempotent**: rows are matched by ``City.name`` / ``Courier.code`` and updated
in place, so it can be re-run against a populated database (including production) without
deleting existing shipments or user data.

Run manually with::

    python -m app.utils.seed_data
"""

from app.database import SessionLocal
from app.models import base as models

# Logistics hubs, ports and industrial corridors used by domestic and export flows.
CITY_SEED = [
    {"name": "Jakarta Pusat", "province": "DKI Jakarta", "type": "Kota", "postal_code": "10110"},
    {"name": "Jakarta Utara", "province": "DKI Jakarta", "type": "Kota", "postal_code": "14110"},
    {"name": "Jakarta Barat", "province": "DKI Jakarta", "type": "Kota", "postal_code": "11110"},
    {"name": "Jakarta Timur", "province": "DKI Jakarta", "type": "Kota", "postal_code": "13110"},
    {"name": "Cikarang", "province": "Jawa Barat", "type": "Kabupaten", "postal_code": "17530"},
    {"name": "Karawang", "province": "Jawa Barat", "type": "Kabupaten", "postal_code": "41311"},
    {"name": "Bandung", "province": "Jawa Barat", "type": "Kota", "postal_code": "40111"},
    {"name": "Cirebon", "province": "Jawa Barat", "type": "Kota", "postal_code": "45111"},
    {"name": "Semarang", "province": "Jawa Tengah", "type": "Kota", "postal_code": "50111"},
    {"name": "Surabaya", "province": "Jawa Timur", "type": "Kota", "postal_code": "60111"},
    {"name": "Gresik", "province": "Jawa Timur", "type": "Kabupaten", "postal_code": "61111"},
    {"name": "Sidoarjo", "province": "Jawa Timur", "type": "Kabupaten", "postal_code": "61211"},
    {"name": "Pasuruan", "province": "Jawa Timur", "type": "Kota", "postal_code": "67111"},
    {"name": "Yogyakarta", "province": "DI Yogyakarta", "type": "Kota", "postal_code": "55111"},
    {"name": "Tangerang", "province": "Banten", "type": "Kota", "postal_code": "15111"},
    {"name": "Cilegon", "province": "Banten", "type": "Kota", "postal_code": "42411"},
    {"name": "Bandar Lampung", "province": "Lampung", "type": "Kota", "postal_code": "35111"},
    {"name": "Palembang", "province": "Sumatera Selatan", "type": "Kota", "postal_code": "30111"},
    {"name": "Jambi", "province": "Jambi", "type": "Kota", "postal_code": "36111"},
    {"name": "Pekanbaru", "province": "Riau", "type": "Kota", "postal_code": "28111"},
    {"name": "Batam", "province": "Kepulauan Riau", "type": "Kota", "postal_code": "29411"},
    {"name": "Tanjung Pinang", "province": "Kepulauan Riau", "type": "Kota", "postal_code": "29111"},
    {"name": "Medan", "province": "Sumatera Utara", "type": "Kota", "postal_code": "20111"},
    {"name": "Belawan", "province": "Sumatera Utara", "type": "Kota", "postal_code": "20411"},
    {"name": "Padang", "province": "Sumatera Barat", "type": "Kota", "postal_code": "25111"},
    {"name": "Banda Aceh", "province": "Aceh", "type": "Kota", "postal_code": "23111"},
    {"name": "Pontianak", "province": "Kalimantan Barat", "type": "Kota", "postal_code": "78111"},
    {"name": "Banjarmasin", "province": "Kalimantan Selatan", "type": "Kota", "postal_code": "70111"},
    {"name": "Balikpapan", "province": "Kalimantan Timur", "type": "Kota", "postal_code": "76111"},
    {"name": "Samarinda", "province": "Kalimantan Timur", "type": "Kota", "postal_code": "75111"},
    {"name": "Tarakan", "province": "Kalimantan Utara", "type": "Kota", "postal_code": "77111"},
    {"name": "Makassar", "province": "Sulawesi Selatan", "type": "Kota", "postal_code": "90111"},
    {"name": "Bitung", "province": "Sulawesi Utara", "type": "Kota", "postal_code": "95511"},
    {"name": "Manado", "province": "Sulawesi Utara", "type": "Kota", "postal_code": "95111"},
    {"name": "Kendari", "province": "Sulawesi Tenggara", "type": "Kota", "postal_code": "93111"},
    {"name": "Palu", "province": "Sulawesi Tengah", "type": "Kota", "postal_code": "94111"},
    {"name": "Denpasar", "province": "Bali", "type": "Kota", "postal_code": "80111"},
    {"name": "Mataram", "province": "Nusa Tenggara Barat", "type": "Kota", "postal_code": "83111"},
    {"name": "Kupang", "province": "Nusa Tenggara Timur", "type": "Kota", "postal_code": "85111"},
    {"name": "Ambon", "province": "Maluku", "type": "Kota", "postal_code": "97111"},
    {"name": "Ternate", "province": "Maluku Utara", "type": "Kota", "postal_code": "97711"},
    {"name": "Sorong", "province": "Papua Barat Daya", "type": "Kota", "postal_code": "98411"},
    {"name": "Jayapura", "province": "Papua", "type": "Kota", "postal_code": "99111"},
]

# Domestic last-mile, domestic cargo and international freight forwarders.
COURIER_SEED = [
    {
        "name": "JNE Express",
        "code": "jne",
        "logo_url": "/assets/img/logistics/JNE.png",
        "description": "Jalur Nugraha Ekakurir (JNE), jaringan last-mile terbesar di Indonesia.",
    },
    {
        "name": "J&T Express",
        "code": "jnt",
        "logo_url": "/assets/img/logistics/JNT.png",
        "description": "Kurir e-commerce dengan jangkauan pickup dan delivery harian.",
    },
    {
        "name": "SiCepat",
        "code": "sicepat",
        "logo_url": "/assets/img/logistics/SiCepat.png",
        "description": "SiCepat Ekspres, layanan jemput paket dan pengiriman reguler.",
    },
    {
        "name": "POS Indonesia",
        "code": "pos",
        "logo_url": "/assets/img/logistics/Pos-Indonesia.png",
        "description": "BUMN pos nasional dengan jangkauan hingga daerah terpencil.",
    },
    {
        "name": "AnterAja",
        "code": "anteraja",
        "logo_url": "/assets/img/logistics/anteraja.png",
        "description": "Layanan pengiriman berbasis teknologi dengan kurir Satria.",
    },
    {
        "name": "TIKI",
        "code": "tiki",
        "logo_url": None,
        "description": "Titipan Kilat, kurir domestik dengan layanan reguler dan kargo.",
    },
    {
        "name": "Ninja Xpress",
        "code": "ninja",
        "logo_url": None,
        "description": "Kurir regional Asia Tenggara dengan fokus e-commerce.",
    },
    {
        "name": "Lion Parcel",
        "code": "lion",
        "logo_url": None,
        "description": "Layanan kargo udara dan darat dari Lion Group.",
    },
    {
        "name": "DHL Express",
        "code": "dhl",
        "logo_url": None,
        "description": "Kargo internasional ekspres, dokumen dan paket lintas negara.",
    },
    {
        "name": "FedEx",
        "code": "fedex",
        "logo_url": None,
        "description": "Forwarding internasional dengan layanan express dan economy.",
    },
    {
        "name": "UPS",
        "code": "ups",
        "logo_url": None,
        "description": "Kargo internasional, termasuk solusi supply chain B2B.",
    },
    {
        "name": "Maersk",
        "code": "maersk",
        "logo_url": None,
        "description": "Pengapalan kontainer dan logistik laut untuk ekspor-impor.",
    },
]

DEMO_SHIPMENTS = [
    {
        "awb": "LGS-12345678",
        "courier_code": "jne",
        "status": "DELIVERED",
        "history": [
            {"status": "PICKED_UP", "location": "Surabaya Hub", "timestamp": "2024-05-01T10:00:00"},
            {"status": "IN_TRANSIT", "location": "Jakarta Gateway", "timestamp": "2024-05-02T08:00:00"},
            {"status": "OUT_FOR_DELIVERY", "location": "Jakarta Pusat DC", "timestamp": "2024-05-03T09:30:00"},
            {"status": "DELIVERED", "location": "Alamat Penerima", "timestamp": "2024-05-03T11:45:00"},
        ],
    }
]


def _upsert(db, model, match: dict, values: dict):
    """Return (created, updated) for one reference row."""
    row = db.query(model).filter_by(**match).first()
    if row is None:
        db.add(model(**match, **values))
        return True, False

    changed = False
    for key, value in values.items():
        if getattr(row, key, None) != value:
            setattr(row, key, value)
            changed = True
    return False, changed


def seed():
    db = SessionLocal()
    cities_created = cities_updated = 0
    couriers_created = couriers_updated = 0
    try:
        for city in CITY_SEED:
            created, updated = _upsert(
                db,
                models.City,
                {"name": city["name"]},
                {k: v for k, v in city.items() if k != "name"},
            )
            cities_created += int(created)
            cities_updated += int(updated)

        for courier in COURIER_SEED:
            created, updated = _upsert(
                db,
                models.Courier,
                {"code": courier["code"]},
                {k: v for k, v in courier.items() if k != "code"},
            )
            couriers_created += int(created)
            couriers_updated += int(updated)

        db.commit()

        for demo in DEMO_SHIPMENTS:
            if db.query(models.Tracking).filter(models.Tracking.awb == demo["awb"]).first():
                continue
            courier = db.query(models.Courier).filter(models.Courier.code == demo["courier_code"]).first()
            db.add(models.Tracking(
                awb=demo["awb"],
                courier_id=courier.id if courier else None,
                status=demo["status"],
                history=demo["history"],
            ))
        db.commit()

        print(
            "Seed complete: "
            f"{cities_created} cities created, {cities_updated} updated; "
            f"{couriers_created} couriers created, {couriers_updated} updated."
        )
    except Exception as exc:
        db.rollback()
        print(f"Seed failed, rolled back: {exc}")
        raise
    finally:
        db.close()


if __name__ == "__main__":
    seed()
