# ShipStream — Master Prompt — Dokumentasi PDF UTS Pemrograman API
# Paste prompt ini ke Claude baru, lampirkan semua file .md, lalu jalankan.

---

```
## KONTEKS & IDENTITAS

Kamu adalah asisten yang bertugas membuat dokumentasi PDF UTS mata kuliah Pemrograman API.

### Identitas Mahasiswa
- Nama       : Yogi Prasetyo
- NIM        : 22081010297
- Mata Kuliah: Pemrograman API
- Dosen      : Muhammad Muharrom Al Haromainy, S.Kom., M.Kom.
- Universitas: UPN "Veteran" Jawa Timur
- Semester   : 6 (Genap TA. 2025/2026)

---

## SOAL UTS (REFERENSI)

1. Buatlah website yang menyediakan API sederhana menggunakan basis data lokal.
   - Agar dapat menggunakan API, harus menggunakan API KEY
   - Sediakan sistem login dan daftar akun untuk request/create API KEY
2. Implementasikan API + API KEY menggunakan POSTMAN
3. Sediakan landing page sebagai website penyedia API

Kumpulkan: arsip ZIP + dokumentasi PDF

---

## TUGASMU

Buat dokumentasi PDF profesional (~25-30 halaman) menggunakan bash_tool dan WeasyPrint/ReportLab.
Dokumentasi harus mencakup semua fitur project ShipStream — Logistics Rate & Tracking API.

---

## STRUKTUR DOKUMEN (WAJIB IKUTI URUTAN INI)

### HALAMAN COVER
- Judul: "Dokumentasi UTS — ShipStream Logistics API"
- Nama, NIM, Mata Kuliah, Dosen, Universitas, Tahun

### BAB 1 — PENDAHULUAN (2 halaman)
1.1 Latar Belakang  
→ Jelaskan kebutuhan sistem API logistik modern, referensi ke RajaOngkir sebagai inspirasi.

1.2 Tujuan  
→ Membangun platform API dengan sistem autentikasi, manajemen API Key, dan data logistik.

1.3 Ruang Lingkup  
→ Backend FastAPI, Database PostgreSQL, Frontend Vanilla JS, Testing Postman.

1.4 Teknologi yang Digunakan  
→ Tabel: Python 3.13, FastAPI, SQLAlchemy, PostgreSQL 18, Argon2, JWT, Vanilla JS, Postman.

---

### BAB 2 — ARSITEKTUR SISTEM (3 halaman)

2.1 Gambaran Umum Sistem  
→ Diagram alur: User → Landing Page → Register/Login → JWT Token → Generate API Key → 
   Request ke endpoint /v1/* dengan header X-API-Key → Response data logistik.

2.2 Struktur Folder Project  
→ Tampilkan struktur folder lengkap dalam format code block:
```
logistics-api/
├── app/
│   ├── main.py
│   ├── database.py
│   ├── models/base.py
│   ├── routers/ (auth, apikey, billing, logistics, profile, telegram_bot)
│   ├── schemas/schemas.py
│   └── utils/ (security, api_key_auth, crypto_validator, dependencies,
│               exchange_rate, security_utils, seed_data, sync_schema)
├── frontend/
│   ├── index.html
│   ├── dashboard.html
│   └── assets/ (style.css, hero.png)
├── postman/collection.json
├── backups/
├── requirements.txt
└── README.md
```

2.3 Skema Database  
→ Buat tabel dokumentasi untuk 5 tabel utama:

**Tabel: users**
| Kolom | Tipe | Keterangan |
|---|---|---|
| id | Integer PK | Auto-increment |
| username | String UNIQUE | Login identifier |
| email | String UNIQUE | Email verifikasi |
| hashed_password | String | Argon2 hash |
| is_verified | Boolean | Aktif setelah OTP |
| quota_limit | Integer | Total kuota prepaid |
| quota_used | Integer | Kuota terpakai |
| preferences | JSON | {lang, timezone, currency} |

**Tabel: api_keys**
| Kolom | Tipe | Keterangan |
|---|---|---|
| id | Integer PK | |
| key | String UNIQUE | UUID-based key value |
| label | String | Nama deskriptif |
| user_id | FK → users | Pemilik key |
| is_active | Boolean | Status aktif |
| total_requests | Integer | Counter penggunaan |
| ip_whitelist | String nullable | Comma-separated IPs |
| status | String | active/suspended/limited |

**Tabel: transactions**
| Kolom | Tipe | Keterangan |
|---|---|---|
| id | Integer PK | |
| user_id | FK → users | |
| order_id | String UNIQUE | Format: BILL-XXXXXXXX |
| amount | Integer | Nominal IDR |
| quota_added | Integer | Request yang dibeli |
| payment_method | String | midtrans / crypto |
| tx_hash | String nullable | Blockchain TXID |
| status | String | pending/success/failed/expired/cancelled |
| expires_at | DateTime | +1 jam dari created_at |

**Tabel: verification_codes** — OTP 6-digit untuk register & update keamanan  
**Tabel: user_sessions** — Tracking sesi aktif per device + IP address

2.4 Alur Autentikasi  
→ Jelaskan flow: Register → OTP Email → Login → JWT Token → Bearer Authorization

---

### BAB 3 — IMPLEMENTASI BACKEND (6 halaman)

3.1 Konfigurasi Utama (main.py)  
→ Tampilkan kode main.py lengkap dengan penjelasan:
- CORS middleware (allow_origins=["*"] untuk development)
- Static file serving untuk frontend
- Router registration (auth, apikey, billing, logistics, profile)
- Auto create tables on startup

```python
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from app.database import engine, Base
from app.routers import auth, apikey, billing, logistics, profile

Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="ShipStream — Logistics Rate & Tracking API",
    description="Platform API Logistik dengan sistem billing & kuota prepaid",
    version="2.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(apikey.router)
app.include_router(billing.router)
app.include_router(logistics.router)
app.include_router(profile.router)
```

3.2 Sistem Autentikasi (auth.py)  
→ Tampilkan kode register + login endpoint dengan penjelasan:
- POST /auth/register — validasi username unik, hash password Argon2, kirim OTP
- POST /auth/verify-code — verifikasi OTP 6-digit
- POST /auth/login — OAuth2PasswordRequestForm, return JWT token 24 jam

3.3 Manajemen API Key (apikey.py)  
→ Tampilkan kode generate + list + revoke dengan penjelasan:
- POST /apikey/generate — generate UUID key, simpan ke DB
- GET /apikey/list — list semua key milik user yang login
- DELETE /apikey/revoke/{key_id} — hapus key, validasi ownership
- PUT /apikey/{key_id}/settings — update label, limit, IP whitelist

3.4 Middleware Validasi API Key (api_key_auth.py)  
→ Jelaskan flow validasi:
1. Baca header X-API-Key dari setiap request ke /v1/*
2. Query ke tabel api_keys
3. Cek is_active = True
4. Cek IP whitelist (jika ada)
5. Cek quota_used < quota_limit (global user quota)
6. Increment total_requests + quota_used
7. Return user object atau raise 401/403

3.5 Endpoint Logistik (logistics.py)  
→ Dokumentasikan 5 endpoint:

| Endpoint | Method | Auth | Deskripsi |
|---|---|---|---|
| /v1/cities | GET | X-API-Key | Daftar kota tujuan pengiriman |
| /v1/couriers | GET | X-API-Key | Daftar kurir tersedia |
| /v1/cost | GET | X-API-Key | Hitung ongkos kirim |
| /v1/tracking/{awb} | GET | X-API-Key | Tracking status paket |
| /v1/quota | GET | X-API-Key | Cek sisa kuota user |

→ Tampilkan contoh response JSON untuk masing-masing endpoint:

**/v1/couriers — Response:**
```json
[
  {"id": 1, "name": "JNE Express", "code": "jne"},
  {"id": 2, "name": "J&T Express", "code": "jnt"},
  {"id": 3, "name": "SiCepat", "code": "sicepat"}
]
```

**/v1/cost — Request params:** origin_id, destination_id, weight_gram, courier_code  
**/v1/cost — Response:**
```json
{
  "origin": 1,
  "destination": 3,
  "courier": "JNE Express",
  "weight": 1000,
  "total_cost": 10000,
  "currency": "IDR"
}
```

**/v1/tracking/{awb} — Response:**
```json
{
  "awb": "LGS-12345678",
  "courier": "SiCepat",
  "status": "IN_TRANSIT",
  "history": [
    {"timestamp": "2026-04-14 08:00", "status": "PICKED_UP", "location": "Surabaya"},
    {"timestamp": "2026-04-14 15:00", "status": "IN_TRANSIT", "location": "Jakarta Hub"}
  ]
}
```

3.6 Sistem Billing & Kuota (billing.py)  
→ Jelaskan arsitektur Global Prepaid Pool:
- User punya quota_limit (total dibeli) dan quota_used (terpakai)
- Semua API Key berbagi satu pool kuota yang sama
- POST /v1/billing/topup — buat invoice, pilih Midtrans atau Crypto
- POST /v1/billing/submit-proof/{order_id} — submit TX hash crypto
- Auto-verify via BaseScan API — jika valid → quota ditambah otomatis
- GET /v1/billing/history — list transaksi + auto-expire yang >1 jam
- DELETE /v1/billing/cancel/{order_id} — batalkan order pending

---

### BAB 4 — IMPLEMENTASI FRONTEND (3 halaman)

4.1 Landing Page (index.html)  
→ Jelaskan fitur:
- Hero section dengan CTA "Mulai Sekarang" dan "Get API Key"
- Form Register (username, email, password) + OTP verification
- Form Login → simpan JWT ke localStorage → redirect dashboard
- Dark premium theme dengan glassmorphism CSS

4.2 Dashboard (dashboard.html)  
→ Jelaskan 5 tab navigasi:

**Tab Keys** — Manajemen API Key
- List semua key aktif dengan label, nilai key, status
- Tombol Generate Key baru (input label)
- Tombol Copy key ke clipboard
- Tombol Revoke key dengan konfirmasi dialog

**Tab Docs** — Dokumentasi interaktif
- Referensi endpoint lengkap
- Playground untuk test endpoint langsung dari browser
- Contoh curl untuk setiap endpoint

**Tab Billing** — Riwayat transaksi
- List semua invoice dengan status badge (PENDING/SUCCESS/INVALID)
- Countdown timer real-time untuk invoice yang masih aktif
- Modal detail transaksi
- Tombol batalkan order
- Modal checkout Midtrans dan Crypto dengan panduan pembayaran

**Tab Profile** — Informasi akun
- Tampilkan username, email, nomor HP
- Update email/password dengan verifikasi OTP
- Daftar sesi aktif per device + IP address
- Revoke sesi yang tidak dikenal

**Tab Settings** — Preferensi
- Dropdown bahasa (Indonesia/English)
- Dropdown timezone (WIB/WITA/WIT)
- Dropdown format currency
- Alert threshold untuk notifikasi kuota
- Webhook Telegram untuk notifikasi

4.3 Sistem i18n (Internasionalisasi)  
→ Jelaskan implementasi multi-bahasa dengan objek `translations` di JavaScript:
- Bahasa Indonesia dan English
- Disimpan di `user.preferences.lang` di database
- Diterapkan ke semua teks UI saat halaman dimuat

---

### BAB 5 — TESTING DENGAN POSTMAN (5 halaman)

5.1 Setup Environment Postman  
→ Instruksi lengkap:
1. Import file `postman/collection.json`
2. Buat environment baru: `LogiRate Local`
3. Set variable: `baseUrl = http://localhost:8000`
4. Set variable: `token = (diisi setelah login)`
5. Set variable: `apiKey = (diisi setelah generate key)`

5.2 Testing Auth Endpoints  

**Test 1: Register User Baru**
- Method: POST
- URL: {{baseUrl}}/auth/register
- Body (JSON):
```json
{
  "username": "yogitest",
  "email": "yogi@test.com",
  "password": "password123"
}
```
- Expected response 200:
```json
{
  "id": 1,
  "username": "yogitest",
  "email": "yogi@test.com",
  "is_verified": false
}
```

**Test 2: Verifikasi OTP**
- Method: POST  
- URL: {{baseUrl}}/auth/verify-code
- Body (JSON):
```json
{
  "username": "yogitest",
  "code": "123456"
}
```
- Expected response 200: `{"message": "Account verified successfully"}`

**Test 3: Login**
- Method: POST
- URL: {{baseUrl}}/auth/login
- Body (form-data): username=yogitest, password=password123
- Expected response 200:
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer"
}
```
→ Salin access_token ke environment variable `token`

5.3 Testing API Key Management  

**Test 4: Generate API Key**
- Method: POST
- URL: {{baseUrl}}/apikey/generate
- Header: Authorization: Bearer {{token}}
- Body (JSON):
```json
{
  "label": "Production Key"
}
```
- Expected response 200:
```json
{
  "id": 1,
  "key": "aB3xK9mNpQ2rS7vW...",
  "label": "Production Key",
  "is_active": true,
  "total_requests": 0
}
```
→ Salin nilai `key` ke environment variable `apiKey`

**Test 5: List API Keys**
- Method: GET
- URL: {{baseUrl}}/apikey/list
- Header: Authorization: Bearer {{token}}
- Expected: Array berisi semua key milik user

**Test 6: Revoke API Key**
- Method: DELETE
- URL: {{baseUrl}}/apikey/revoke/1
- Header: Authorization: Bearer {{token}}
- Expected: `{"message": "API Key revoked successfully"}`

5.4 Testing Logistics Endpoints  

**Test 7: Get Couriers**
- Method: GET
- URL: {{baseUrl}}/v1/couriers
- Header: X-API-Key: {{apiKey}}
- Expected: Array daftar kurir

**Test 8: Get Cities**
- Method: GET
- URL: {{baseUrl}}/v1/cities
- Header: X-API-Key: {{apiKey}}
- Expected: Array daftar kota

**Test 9: Calculate Cost**
- Method: GET
- URL: {{baseUrl}}/v1/cost?origin_id=1&destination_id=3&weight_gram=1500&courier_code=jne
- Header: X-API-Key: {{apiKey}}
- Expected:
```json
{
  "origin": 1,
  "destination": 3,
  "courier": "JNE Express",
  "weight": 1500,
  "total_cost": 15000,
  "currency": "IDR"
}
```

**Test 10: Tracking Paket**
- Method: GET
- URL: {{baseUrl}}/v1/tracking/LGS-12345678
- Header: X-API-Key: {{apiKey}}
- Expected: Object tracking dengan history

**Test 11: Test Error — API Key Tidak Valid**
- Method: GET
- URL: {{baseUrl}}/v1/couriers
- Header: X-API-Key: INVALID_KEY_123
- Expected response 401:
```json
{
  "detail": "Invalid or inactive API Key"
}
```

**Test 12: Test Error — Tanpa API Key**
- Method: GET
- URL: {{baseUrl}}/v1/couriers
- (tanpa header X-API-Key)
- Expected response 422: Unprocessable Entity

5.5 Tabel Ringkasan Hasil Testing  

| No | Endpoint | Method | Auth | Expected | Status |
|---|---|---|---|---|---|
| 1 | /auth/register | POST | - | 200 | ✅ PASS |
| 2 | /auth/verify-code | POST | - | 200 | ✅ PASS |
| 3 | /auth/login | POST | - | 200 + Token | ✅ PASS |
| 4 | /apikey/generate | POST | Bearer JWT | 200 + Key | ✅ PASS |
| 5 | /apikey/list | GET | Bearer JWT | 200 + Array | ✅ PASS |
| 6 | /apikey/revoke/{id} | DELETE | Bearer JWT | 200 | ✅ PASS |
| 7 | /v1/couriers | GET | X-API-Key | 200 + Array | ✅ PASS |
| 8 | /v1/cities | GET | X-API-Key | 200 + Array | ✅ PASS |
| 9 | /v1/cost | GET | X-API-Key | 200 + Object | ✅ PASS |
| 10 | /v1/tracking/{awb} | GET | X-API-Key | 200 + Object | ✅ PASS |
| 11 | /v1/couriers (key invalid) | GET | X-API-Key salah | 401 | ✅ PASS |
| 12 | /v1/couriers (no key) | GET | - | 422 | ✅ PASS |

---

### BAB 6 — FITUR LANJUTAN (3 halaman)

6.1 Sistem Billing & Top-up  
→ Jelaskan dua metode pembayaran:
- **Midtrans**: Buat invoice → copy order ID → konfirmasi manual via admin endpoint
- **Crypto (Base USDC)**: Buat invoice → kirim USDC ke wallet admin → submit TX hash → 
  sistem auto-verify via BaseScan API → kuota otomatis bertambah

6.2 Global Prepaid Quota System  
→ Jelaskan arsitektur:
- Setiap akun punya saldo kuota terpusat (quota_limit - quota_used)
- Semua API Key milik akun yang sama berbagi satu pool
- Setiap request ke /v1/* mengurangi quota_used sebesar 1
- Dashboard menampilkan sisa kuota secara real-time di navbar

6.3 Keamanan Lanjutan  
→ Jelaskan fitur:
- OTP 6-digit untuk register, update email, update password
- IP Whitelist per API Key — tolak request dari IP yang tidak terdaftar
- Session tracking — monitor semua perangkat yang login
- JWT dengan expiry 24 jam + JTI unik per sesi

6.4 Integrasi Telegram Bot  
→ Jelaskan fitur /cek_kuota:
- User daftarkan Bot Token dan Chat ID di Settings dashboard
- Kirim /cek_kuota ke bot → sistem reply dengan sisa kuota saat ini

---

### BAB 7 — CARA MENJALANKAN PROJECT (2 halaman)

7.1 Prasyarat  
→ Daftar: Python 3.13, PostgreSQL 18, Postman, pgAdmin4

7.2 Langkah Setup  

**Step 1: Clone/extract project**
```
cd C:\Users\...\pemograman_api\logistics-api
```

**Step 2: Install dependencies**
```bash
pip install -r requirements.txt
```

**Step 3: Konfigurasi .env**
```env
DATABASE_URL=postgresql://postgres:postgres@localhost:5432/logistics_api
SECRET_KEY=your_secret_key_here
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=1440
DEBUG_MODE=True
```

**Step 4: Sinkronisasi schema database**
```bash
python -m app.utils.sync_schema
```

**Step 5: Seed data awal**
```bash
python -m app.utils.seed_data
```

**Step 6: Jalankan server**
```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

**Step 7: Akses aplikasi**
- Landing Page : http://127.0.0.1:8000
- Dashboard    : http://127.0.0.1:8000/dashboard
- Swagger UI   : http://127.0.0.1:8000/docs

7.3 Kredensial Testing
```
Username : yogiuser
Password : yogi123456
```

---

### BAB 8 — PENUTUP (1 halaman)

8.1 Kesimpulan  
→ Ringkasan: Berhasil membangun platform API logistik lengkap dengan sistem autentikasi JWT, 
manajemen API Key, endpoint data logistik, sistem billing prepaid, dan dashboard interaktif. 
Semua requirement soal UTS terpenuhi dan project diperluas dengan fitur advanced.

8.2 Saran Pengembangan  
→ 3 poin: (1) Migrasi ke Alembic untuk database migration, 
(2) Implementasi rate limiting per endpoint, 
(3) Deploy ke cloud dengan domain publik.

---

### DAFTAR PUSTAKA (1 halaman)
- FastAPI Documentation — https://fastapi.tiangolo.com
- SQLAlchemy Documentation — https://docs.sqlalchemy.org
- PostgreSQL Documentation — https://www.postgresql.org/docs
- JWT Introduction — https://jwt.io/introduction
- Postman Learning Center — https://learning.postman.com
- BaseScan API Docs — https://basescan.org/apis

---

## INSTRUKSI TEKNIS UNTUK CLAUDE (EKSEKUTOR)

1. Baca semua file .md yang dilampirkan sebelum membuat PDF
2. Gunakan bash_tool untuk membuat PDF menggunakan WeasyPrint atau ReportLab
3. Styling PDF:
   - Font: Times New Roman atau DejaVu Serif untuk body, ukuran 12pt
   - Heading BAB: Bold, 16pt, uppercase
   - Sub-heading: Bold, 13pt
   - Code block: background #f5f5f5, font monospace 10pt, border kiri 3px solid #333
   - Tabel: border solid, header background #333 warna putih, baris alternating #f9f9f9
   - Margin halaman: 2.5cm semua sisi
   - Nomor halaman di footer tengah
   - Header: "Dokumentasi UTS — ShipStream Logistics API | Yogi Prasetyo — 22081010297"
4. Cover page: full background gelap (#1a1a2e), teks putih, logo/ikon sederhana
5. Setiap BAB mulai di halaman baru
6. Output file: `dokumentasi_UTS_Yogi_22081010297.pdf`
7. Simpan ke /mnt/user-data/outputs/

## CATATAN PENTING
- Semua kode yang ditampilkan harus ada syntax highlighting (bold untuk keywords)
- Response JSON harus diformat dengan indentasi yang rapi
- Tabel harus fit dalam satu halaman (jangan sampai terpotong)
- Jika screenshot tidak tersedia, buat placeholder bertuliskan "[Screenshot: nama_endpoint]"
- Total halaman target: 25-30 halaman
```
