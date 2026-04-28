# 🌉 AI BRIDGE — ShipStream Logistics API
> Titik masuk utama. Baca COLLAB_PROTOCOL.md dulu sebelum apapun.

---

## 🎯 Project Snapshot
**Nama**: ShipStream — Logistics Rate & Tracking API
**Pemilik**: Yogi Prasetyo
**Konteks**: Portofolio standar industri
**Stack**: FastAPI + PostgreSQL + Vanilla JS
**Status**: ✅ 100% Fungsional & Hardened. CI/CD Aktif.

---

## 📁 Entry Points
| File | Fungsi |
|------|--------|
| `app/main.py` | App entrypoint, routing, static mount |
| `app/models/base.py` | Semua model SQLAlchemy |
| `app/schemas/schemas.py` | Semua Pydantic schema |
| `app/routers/logistics.py` | Endpoint logistik (cost, tracking, shipment, label) |
| `frontend/dashboard.html` | Dashboard SPA (monolith, hati-hati duplikasi JS) |
| `frontend/assets/style.css` | CSS global |
| `.env` | Konfigurasi environment |

---

## ⚠️ Hal Kritis
- Dashboard: jangan duplikasi `let/const/var` di global scope, gunakan `showConfirmModal`
- Quota: Global Pool di `User.quota_limit` — BUKAN per-API-key
- OTP: dibypass (`is_verified=True`) — jangan aktifkan tanpa SMTP siap
- DB: PostgreSQL `localhost:5432/logistics_api`, Alembic di `alembic/versions/`
- Redis: Gunakan `REDIS_URL=memory://` di `.env` lokal jika tidak ada Redis terinstall (Error 10061).

---

## 🔧 Next Steps (Active)

[x] DONE — Cek & pastikan `.env` | File: `.env`

[x] DONE — Update test untuk endpoint scale-up | File: `tests/test_main.py`

[x] DONE — Fix GitHub Actions CI agar lolos | File: `.github/workflows/lint-test.yml`

[x] DONE — Push ke GitHub & Aktivasi CI | File: `.git`
- Terhubung ke: `https://github.com/Yogi-89/logistics-api.git`
- Branch: `develop` (active)
- CI: `.github/workflows/lint-test.yml` (running)

---

## 🚀 Phase 2 — Scale Up & Deploy

[x] DONE — TODO-1 — Global Exception Handler | File: `app/main.py`
- Tambah handler SEBELUM route includes:
```python
from fastapi.responses import JSONResponse
@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    return JSONResponse(status_code=500, content={"detail": str(exc), "type": type(exc).__name__})
```
- Pastikan semua router sudah wrap DB calls dengan try/except HTTPException
- Test: hit endpoint dengan data invalid → harus return JSON bukan plain text

[x] DONE — TODO-2 — Endpoint Recommend Kurir | File: `app/routers/logistics.py`
- Tambah `POST /v1/cost/recommend` (taruh SEBELUM `/cost` agar tidak konflik routing)
- Logic: query semua kurir aktif dari DB → asyncio.gather hit Raja Ongkir per kurir secara paralel → sort by cost asc
- Fallback: jika Raja Ongkir gagal, gunakan internal_fallback formula yang sudah ada
- Schema baru di `app/schemas/schemas.py`: `CostRecommendRequest` (origin, destination, weight, optional: length, width, height)
- Response: list hasil semua kurir sorted by harga termurah
- Rate limit: 20/minute

[x] DONE — TODO-3 — Deploy ke Railway | File: `Procfile` + `railway.toml` (buat baru)
- Buat `Procfile`: `web: uvicorn app.main:app --host 0.0.0.0 --port $PORT`
- Buat `railway.toml`:
```toml
[build]
builder = "NIXPACKS"

[deploy]
startCommand = "alembic upgrade head && uvicorn app.main:app --host 0.0.0.0 --port $PORT"
healthcheckPath = "/api/"
healthcheckTimeout = 30
```
- Pastikan semua env vars sudah ada di Railway dashboard (DATABASE_URL auto-inject dari Railway PostgreSQL plugin)
- CORS `allow_origins`: ganti `["*"]` → `[os.getenv("ALLOWED_ORIGINS", "*")]` di `main.py`

---

## 🎨 Phase 3 — Branding & UI Polish

[x] DONE — TODO-4 — Fix Splash Screen Video | File: `frontend/dashboard.html`

### Asset yang digunakan:
| Konteks | File |
|---|---|
| Navbar dark | `frontend/assets/navbar_footer_dark_modern_blue-removebg-preview.png` |
| Navbar light | `frontend/assets/navbar_footer_white_modern_blue-removebg-preview.png` |
| Favicon | `frontend/assets/logo_icon_dark_modern_blue-removebg-preview.png` |
| Splash video | `frontend/assets/fix backgound.mp4` (versi cepat, background putih) |
| Splash fallback | `frontend/assets/logo_dark_cut.png` |
| Shipping label PDF | sudah solved oleh Yogi, skip |

### Instruksi AI IDE:
1. **Splash screen** — Ganti implementasi splash yang ada dengan ini:
```html
<div id="splash" style="position:fixed;inset:0;background:#0b0d11;display:flex;align-items:center;justify-content:center;z-index:9999;transition:opacity 0.6s ease">
  <video id="splash-video" autoplay muted playsinline
    style="width:420px;height:420px;object-fit:contain;mix-blend-mode:screen;">
    <source src="assets/fix backgound.mp4" type="video/mp4">
  </video>
</div>
```
Tambah JS (letakkan di akhir `<body>` atau DOMContentLoaded):
```javascript
const splashVideo = document.getElementById('splash-video');
const splash = document.getElementById('splash');
if (splashVideo) {
  splashVideo.addEventListener('ended', () => {
    splash.style.opacity = '0';
    setTimeout(() => splash.remove(), 600);
  });
  // Fallback: jika video gagal load, hilangkan splash setelah 3 detik
  splashVideo.addEventListener('error', () => {
    splash.innerHTML = `<img src="assets/logo_dark_cut.png"
      style="width:200px;animation:splashFade 2.5s ease forwards">`;
    setTimeout(() => { splash.style.opacity='0'; setTimeout(()=>splash.remove(),600); }, 2500);
  });
}
```
Tambah CSS di `<style>` atau `style.css`:
```css
@keyframes splashFade {
  0%   { opacity:0; transform:scale(0.85); }
  30%  { opacity:1; transform:scale(1); }
  80%  { opacity:1; transform:scale(1); }
  100% { opacity:0; transform:scale(1.05); }
}
```
2. **Kenapa `mix-blend-mode:multiply`** — background putih video jadi transparan, logo dark navy tetap terlihat di atas `#0b0d11`. Tidak perlu edit file video.
3. **Navbar & Favicon** — jika belum diimplementasi, terapkan sekarang:
   - Navbar: `<img src="assets/navbar_footer_dark_modern_blue-removebg-preview.png" height="36">`
   - Favicon: `<link rel="icon" type="image/png" href="assets/logo_icon_dark_modern_blue-removebg-preview.png">`
4. **Test**: buka `localhost:8000` → splash muncul → logo S terlihat jelas di background gelap → fade out → dashboard normal. Pastikan tidak ada box/card putih di sekitar logo.

⚠️ JANGAN loop video. JANGAN pakai `animasi_white_logo_fix_cut.mp4` (terlalu lambat). JANGAN stretch video melebihi 500px. Background splash HARUS `#0b0d11` bukan `#0f172a`.

📌 Raja Ongkir logo upload → MANUAL oleh Yogi: `logo_icon_dark_modern_blue-removebg-preview.png`

[x] DONE — TODO-5 — Fix Splash: Ganti ke animasi_dark_logo_fix_cut.mp4 | File: `frontend/dashboard.html`
- Ganti source video dari `fix backgound.mp4` → `animasi_dark_logo_fix_cut.mp4`
- HAPUS `mix-blend-mode` dari style video (tidak diperlukan, background video sudah gelap)
- Ganti listener `ended` → `timeupdate` agar stop di detik ke-3:
```javascript
const splashVideo = document.getElementById('splash-video');
const splash = document.getElementById('splash');
if (splashVideo) {
  splashVideo.addEventListener('timeupdate', () => {
    if (splashVideo.currentTime >= 3) {
      splash.style.opacity = '0';
      setTimeout(() => splash.remove(), 600);
    }
  });
  splashVideo.addEventListener('error', () => {
    splash.innerHTML = `<img src="assets/logo_dark_cut.png" style="width:200px;animation:splashFade 2.5s ease forwards">`;
    setTimeout(() => { splash.style.opacity='0'; setTimeout(()=>splash.remove(),600); }, 2500);
  });
  setTimeout(() => {
    if (document.getElementById('splash')) {
      splash.style.opacity = '0';
      setTimeout(() => splash.remove(), 600);
    }
  }, 5000);
}
```
- TAMBAH `mix-blend-mode: screen` pada style video agar box background video menyatu dengan `#0b0d11`:
```html
<video id="splash-video" autoplay muted playsinline
  style="width:420px;height:420px;object-fit:contain;mix-blend-mode:screen;">
```
- Test: box biru gelap di belakang logo S harus hilang, logo cyan tetap terlihat jelas
⚠️ JANGAN loop video. JANGAN loop video.
[x] DONE — TODO-6 — Final Splash Screen | File: `frontend/dashboard.html` + `frontend/index.html`
- Ganti source video splash → `assets/fix_backgound_clear.mp4` (4.2MB, background clear, no watermark)
- Style video:
```html
<video id="splash-video" autoplay muted playsinline
  style="width:420px;height:420px;object-fit:contain;mix-blend-mode:screen;filter:brightness(1.3) contrast(1.1);">
  <source src="assets/fix_backgound_clear.mp4" type="video/mp4">
</video>
```
- JS tetap pakai `timeupdate` stop di detik ke-3 + safety timeout 5 detik
- Test: logo S muncul jelas, tidak ada box, tidak ada watermark, fade out detik ke-3
⚠️ File final: `fix_backgound_clear.mp4`. Jangan pakai file splash lain.

---

## 🎨 Phase 3 — Branding (Active)

[x] DONE — TODO-7 — Final Splash: PNG + CSS Animation | File: `frontend/dashboard.html` + `frontend/index.html`
- HAPUS semua `<video>` splash yang ada di kedua file
- Ganti dengan:
```html
<div id="splash" style="position:fixed;inset:0;background:#0b0d11;display:flex;align-items:center;justify-content:center;z-index:9999;transition:opacity 0.6s ease">
  <img src="assets/logo_icon_white_modern_blue-removebg-preview.png"
    style="width:280px;height:280px;object-fit:contain;animation:splashAnim 3s ease forwards;">
</div>
```
- Tambah CSS (Neon Glow):
```css
@keyframes splashAnim {
  0%   { opacity: 0; filter: drop-shadow(0 0 0px #00d2ff); transform: scale(0.9); }
  40%  { opacity: 1; filter: drop-shadow(0 0 20px #00d2ff); transform: scale(1); }
  80%  { opacity: 1; filter: drop-shadow(0 0 10px #00d2ff); transform: scale(1); }
  100% { opacity: 0; filter: drop-shadow(0 0 0px #00d2ff); transform: scale(1.1); }
}
```
- Test: logo S putih muncul dengan pendar biru neon di atas background `#0b0d11`, sangat bersih & premium. Fade out 3 detik.
⚠️ PENTING: Gunakan `logo_icon_white_modern_blue-removebg-preview.png` untuk kontras terbaik.

---

## 🔧 Phase 4 — Raja Ongkir V2 Migration (Active)

[x] DONE — TODO-8 — Fix 405 Error + Migrasi Raja Ongkir V2 | File: `app/routers/logistics.py` + `frontend/dashboard.html`

### ❌ Root Cause Error yang Terjadi:
Server log menunjukkan:
```
GET /v1/cost?origin_id=42&destination_id=44&courier_code=jne&weight_gram=1000 → 405 Method Not Allowed
```
Ada **3 masalah sekaligus** yang harus difix:
1. **Method salah**: frontend memanggil `GET`, endpoint hanya terima `POST`
2. **Nama field salah**: frontend kirim `origin_id`, `destination_id`, `courier_code`, `weight_gram` — tapi schema backend (`CostRequest`) mengharapkan `origin`, `destination`, `courier`, `weight`
3. **Base URL Raja Ongkir lama**: kode masih pakai `api.rajaongkir.com/starter/cost` yang deprecated

---

### ✏️ FIX A — Frontend: Perbaiki cara memanggil `/v1/cost` | File: `frontend/dashboard.html`

Cari di `dashboard.html` bagian JavaScript yang fetch ke `/v1/cost` atau `/cost`.
Ganti seluruh fetch call itu menjadi:

```javascript
// ✅ BENAR — POST dengan JSON body, nama field sesuai CostRequest schema
const response = await fetch('/v1/cost', {
  method: 'POST',                          // wajib POST, bukan GET
  headers: {
    'Content-Type': 'application/json',
    'X-API-Key': userApiKey                // ambil dari variabel yang sudah ada di dashboard
  },
  body: JSON.stringify({
    origin: parseInt(originId),            // ← nama field: origin (bukan origin_id)
    destination: parseInt(destinationId),  // ← nama field: destination (bukan destination_id)
    weight: parseInt(weightGram),          // ← nama field: weight (bukan weight_gram), satuan: gram
    courier: courierCode,                  // ← nama field: courier (bukan courier_code), contoh: "jne"
    length: parseInt(length) || null,      // opsional
    width: parseInt(width) || null,        // opsional
    height: parseInt(height) || null       // opsional
  })
});
const data = await response.json();
// data.results berisi array hasil kurir
// data.origin, data.destination, data.courier, data.effective_weight, dll
```

⚠️ Aturan field:
- `origin` dan `destination` = **integer ID kota dari DB lokal** (ambil dari endpoint `/v1/cities`)
- `weight` = **integer dalam gram** (1 kg = 1000, bukan 1)
- `courier` = **string kode kurir lowercase**: `"jne"`, `"jnt"`, `"sicepat"`, `"pos"`, dll
- Jangan kirim `null` sebagai string `"null"` — kirim `null` JavaScript atau hapus key dari object

---

### ✏️ FIX B — Backend: Migrasi Raja Ongkir V2 | File: `app/routers/logistics.py`

**B1. Ganti BASE URL** — ada di **2 tempat**:
- Di fungsi `calculate_cost` (endpoint `POST /v1/cost`)
- Di fungsi `get_single_courier_cost` yang ada di dalam fungsi `calculate_recommendations`

Cari baris:
```python
"https://api.rajaongkir.com/starter/cost"
```
Ganti **keduanya** menjadi:
```python
"https://rajaongkir.komerce.id/api/v1/calculate/domestic-cost"
```

**B2. Ganti parsing response** — ada di **2 tempat** yang sama:

Untuk fungsi `calculate_cost`, cari blok ini dan ganti:
```python
# HAPUS (V1 lama):
raja_results = data.get("rajaongkir", {}).get("results", [])
for r in raja_results:
    for s in r.get("costs", []):
        results.append({
            "service": s.get("service"),
            "description": s.get("description"),
            "cost": s.get("cost", [{}])[0].get("value", 0),
            "etd": s.get("cost", [{}])[0].get("etd", "N/A"),
            "source": "rajaongkir"
        })

# GANTI JADI (V2 baru) — untuk fungsi calculate_cost:
raja_results = data.get("data", [])
for r in raja_results:
    results.append({
        "service": r.get("service", ""),
        "description": r.get("description", ""),
        "cost": r.get("cost", 0),
        "etd": r.get("etd", "N/A"),
        "source": "rajaongkir"
    })
```

Untuk fungsi `get_single_courier_cost` (dalam `calculate_recommendations`), ganti menjadi:
```python
# GANTI JADI (V2 baru) — untuk fungsi get_single_courier_cost:
raja_results = data.get("data", [])
for r in raja_results:
    results.append({
        "courier_name": r.get("name", courier.name),
        "courier_code": courier.code,
        "service": r.get("service", ""),
        "description": r.get("description", ""),
        "cost": r.get("cost", 0),
        "etd": r.get("etd", "N/A"),
        "source": "rajaongkir"
    })
```

**B3. Yang TIDAK perlu diubah di backend:**
- Header auth: `headers={"key": rajaongkir_key}` ✅
- HTTP method ke Raja Ongkir: tetap `POST` ✅
- Body fields ke Raja Ongkir: `origin`, `destination`, `weight`, `courier` ✅
- Kondisi pengecekan key: `if rajaongkir_key and rajaongkir_key != "your_raja_ongkir_key_here"` ✅
- Fallback internal jika API gagal ✅

---

### ✏️ FIX C — Pastikan `.env` sudah diisi | File: `.env`

Cek baris ini:
```
RAJA_ONGKIR_API_KEY=your_raja_ongkir_key_here
```
Jika masih placeholder, API key belum diisi oleh Yogi. Jangan ganti dari kode — biarkan, Yogi yang isi manual.

---

### ✅ TEST setelah semua fix selesai:

```bash
# 1. Restart server
uvicorn app.main:app --reload

# 2. Test dengan curl (ganti SK-xxx dengan API key user yang valid dari DB)
curl -X POST http://localhost:8000/v1/cost \
  -H "X-API-Key: SK-xxx" \
  -H "Content-Type: application/json" \
  -d '{"origin": 42, "destination": 44, "weight": 1000, "courier": "jne"}'
```

Diagnosis response:
- `200` + `"source": "rajaongkir"` → ✅ semua fix berhasil, Raja Ongkir V2 aktif
- `200` + `"source": "internal_fallback"` → backend ok, tapi API key belum diisi di `.env`
- `405 Method Not Allowed` → FIX A belum diterapkan, frontend masih kirim GET
- `422 Unprocessable Entity` → FIX A nama field masih salah (`origin_id` dll)
- `404 city not found` → origin/destination ID tidak ada di DB lokal

Setelah test berhasil, tandai TODO ini sebagai `[x] DONE`.

---

## 🔧 Phase 4 — Fix Origin/Destination ID Raja Ongkir (Active)

[ ] TODO-9 — Tambah kolom `rajaongkir_id` di tabel cities + update logic cost | File: `app/models/base.py` + `alembic/versions/` + `seed_cities.py` + `app/routers/logistics.py`

### ❌ Root Cause Bug Saat Ini:
Endpoint `/v1/cost` mengirim ID kota dari DB lokal (misal: `42`) ke Raja Ongkir sebagai `origin`/`destination`.
Padahal Raja Ongkir V2 punya sistem ID sendiri yang **berbeda total** dengan ID DB lokal.
Akibatnya Raja Ongkir tidak mengenali kota dengan benar → mengembalikan hasil yang sama untuk semua rute.

### ✅ Solusi: Simpan `rajaongkir_id` di tabel cities

Raja Ongkir V2 menggunakan `id` dari endpoint `/destination/domestic-destination` sebagai parameter origin/destination.
ID ini adalah integer unik dari sistem Raja Ongkir, bukan dari DB kita.

---

### STEP 1 — Tambah kolom `rajaongkir_id` ke model City | File: `app/models/base.py`

Cari class `City` dan tambah satu kolom:
```python
class City(Base):
    __tablename__ = "cities"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True)
    province = Column(String)
    type = Column(String)
    postal_code = Column(String)
    rajaongkir_id = Column(Integer, nullable=True)  # ← TAMBAH INI

    subdistricts = relationship("Subdistrict", back_populates="city")
```

---

### STEP 2 — Buat Alembic migration baru | Jalankan di terminal:
```bash
alembic revision --autogenerate -m "add rajaongkir_id to cities"
alembic upgrade head
```
Ini akan membuat file baru di `alembic/versions/` dan menambah kolom ke DB.

---

### STEP 3 — Buat script seed `seed_rajaongkir_ids.py` di root project

Buat file baru `seed_rajaongkir_ids.py` dengan isi berikut.
Script ini melakukan GET ke Raja Ongkir per kota, ambil ID pertama yang match, simpan ke DB.

```python
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
        print("❌ RAJA_ONGKIR_API_KEY belum diisi di .env")
        return

    conn = psycopg2.connect(db_url)
    cur = conn.cursor()

    for city_name in CITIES:
        try:
            resp = httpx.get(
                "https://rajaongkir.komerce.id/api/v1/destination/domestic-destination",
                headers={"key": api_key},
                params={"search": city_name, "limit": 5, "offset": 0},
                timeout=10.0
            )
            data = resp.json()
            results = data.get("data", [])

            if not results:
                print(f"⚠️  Tidak ditemukan: {city_name}")
                continue

            # Ambil ID dari hasil pertama yang city_name-nya cocok
            raja_id = None
            for r in results:
                label = r.get("label", "").lower()
                city_match = r.get("city_name", "").lower()
                if city_name.lower() in city_match or city_name.lower() in label:
                    raja_id = r.get("id")
                    break

            if raja_id is None:
                # Fallback: pakai hasil pertama
                raja_id = results[0].get("id")
                print(f"⚡ Fallback ke hasil pertama untuk: {city_name} → id={raja_id} ({results[0].get('label')})")
            else:
                print(f"✅ {city_name} → rajaongkir_id={raja_id}")

            cur.execute(
                "UPDATE cities SET rajaongkir_id = %s WHERE name = %s",
                (raja_id, city_name)
            )
        except Exception as e:
            print(f"❌ Error untuk {city_name}: {e}")

    conn.commit()
    cur.close()
    conn.close()
    print("\n🎉 Seeding rajaongkir_id selesai!")

if __name__ == "__main__":
    seed()
```

Jalankan script ini setelah migration selesai:
```bash
python seed_rajaongkir_ids.py
```
Verifikasi hasilnya di output terminal — pastikan semua 36 kota dapat `rajaongkir_id` (bukan `⚠️`).

---

### STEP 4 — Update logic di `app/routers/logistics.py`

Ada 2 fungsi yang perlu diupdate: `calculate_cost` dan `get_single_courier_cost`.

**Di fungsi `calculate_cost`** — ubah bagian pengambilan origin/destination dan pengiriman ke Raja Ongkir:

```python
# HAPUS bagian ini:
origin = db.query(models.City).filter(models.City.id == payload.origin).first()
destination = db.query(models.City).filter(models.City.id == payload.destination).first()

if not origin or not destination:
    raise HTTPException(status_code=404, detail="Origin or Destination city not found")

# ... lalu saat hit Raja Ongkir:
data={
    "origin": str(payload.origin),      # ← INI YANG SALAH (ID lokal)
    "destination": str(payload.destination),
    ...
}

# GANTI JADI:
origin = db.query(models.City).filter(models.City.id == payload.origin).first()
destination = db.query(models.City).filter(models.City.id == payload.destination).first()

if not origin or not destination:
    raise HTTPException(status_code=404, detail="Origin or Destination city not found")

# Validasi rajaongkir_id tersedia
if not origin.rajaongkir_id or not destination.rajaongkir_id:
    raise HTTPException(
        status_code=400,
        detail=f"Raja Ongkir ID belum tersedia untuk kota {origin.name if not origin.rajaongkir_id else destination.name}. Jalankan seed_rajaongkir_ids.py"
    )

# ... lalu saat hit Raja Ongkir:
data={
    "origin": str(origin.rajaongkir_id),        # ← PAKAI rajaongkir_id
    "destination": str(destination.rajaongkir_id),  # ← PAKAI rajaongkir_id
    "weight": int(effective_weight),
    "courier": payload.courier.lower()
}
```

**Di fungsi `get_single_courier_cost`** (dalam `calculate_recommendations`) — perlu akses origin/destination city dari DB dulu.
Karena fungsi ini nested, tambahkan lookup di luar sebelum `asyncio.gather`:

```python
# Di awal fungsi calculate_recommendations, setelah baris couriers = db.query(...):
origin_city = db.query(models.City).filter(models.City.id == payload.origin).first()
destination_city = db.query(models.City).filter(models.City.id == payload.destination).first()

if not origin_city or not destination_city:
    raise HTTPException(status_code=404, detail="Origin or Destination city not found")

if not origin_city.rajaongkir_id or not destination_city.rajaongkir_id:
    raise HTTPException(
        status_code=400,
        detail="Raja Ongkir ID belum tersedia. Jalankan seed_rajaongkir_ids.py"
    )

# Lalu di dalam get_single_courier_cost, ganti:
data={
    "origin": str(payload.origin),          # ← HAPUS
    "destination": str(payload.destination), # ← HAPUS
    ...
}

# JADI:
data={
    "origin": str(origin_city.rajaongkir_id),
    "destination": str(destination_city.rajaongkir_id),
    "weight": int(effective_weight),
    "courier": courier.code.lower()
}
```

---

### STEP 5 — TEST akhir setelah semua selesai:
```bash
# Cek apakah rajaongkir_id sudah terisi di DB
psql -U postgres -d logistics_api -c "SELECT id, name, rajaongkir_id FROM cities LIMIT 10;"

# Test endpoint (Surabaya→Jakarta Pusat, JNE)
curl -X POST http://localhost:8000/v1/cost \
  -H "X-API-Key: SK-xxx" \
  -H "Content-Type: application/json" \
  -d '{"origin": 20, "destination": 8, "weight": 1000, "courier": "jne"}'

# Ulangi dengan kota berbeda (Bandung→Medan)
curl -X POST http://localhost:8000/v1/cost \
  -H "X-API-Key: SK-xxx" \
  -H "Content-Type: application/json" \
  -d '{"origin": 13, "destination": 2, "weight": 1000, "courier": "jne"}'
```

✅ Sukses jika: kedua response punya `cost` yang **berbeda** (Surabaya→Jakarta vs Bandung→Medan harganya tidak sama)
❌ Masih sama → `rajaongkir_id` belum ter-seed atau masih pakai ID lama di kode

Setelah test berhasil, tandai TODO ini sebagai `[x] DONE`.

---

## 🗺️ Roadmap
2. ✅ Rate Limiting (SlowAPI)
3. ✅ Shipment AWB + Tracking endpoint
4. ✅ Bug fix + Pydantic v2 hardening
5. ✅ Raja Ongkir integration + fallback
6. ✅ Unit test pytest
7. ✅ GitHub Actions CI lolos

---

## 🌿 Branching
- `main` → protected, produksi
- `staging` → pre-production, CI wajib lolos
- `develop` → branch kerja aktif
