# ShipStream — Logistics Rate & Tracking API — Context & Guidelines

> **ATURAN WAJIB untuk IDE Antigravity:**
> Baca file ini, `WHAT_WAS_BUILT.md`, `PROGRESS.md`, dan `ISSUES.md` sebelum melakukan perubahan apapun ke project ini.

---

## Identitas Project

| Properti | Nilai |
|---|---|
| **Nama** | ShipStream — Logistics Rate & Tracking API |
| **Root Path** | `C:\Users\Developer\Documents\Semester 8\pemograman_api\logistics-api` |
| **Tujuan** | Platform API logistik dengan sistem billing & kuota prepaid |
| **Status** | ✅ FULLY STABILIZED — Final Polish (Resend.com & Security Limits) |
| **Server** | `uvicorn app.main:app --reload` di port `8000` |
| **Landing Page** | http://127.0.0.1:8000/ |
| **Dashboard** | http://127.0.0.1:8000/dashboard |

---

## Stack Teknologi

| Layer | Teknologi |
|---|---|
| **Backend** | FastAPI (Python 3.13) |
| **ORM** | SQLAlchemy |
| **Database** | PostgreSQL lokal (pgAdmin4), DB: `logistics_api`, port: `5432` |
| **Auth** | JWT Bearer Token |
| **Frontend** | Vanilla JS + HTML + CSS (single-file dashboard) |
| **Payment** | Midtrans (simulasi) + Crypto on-chain (Base USDC via BaseScan API) |
| **Notifikasi** | Telegram Bot webhook |

---

## Struktur Folder LENGKAP

```
logistics-api/
├── app/
│   ├── main.py                      ← Entry point, register semua router
│   ├── database.py                  ← Engine SQLAlchemy + Session
│   ├── models/
│   │   └── base.py                  ← Semua model SQLAlchemy (User, APIKey, Transaction, dll)
│   ├── routers/
│   │   ├── auth.py                  ← Register, Login, Verify OTP
│   │   ├── apikey.py                ← Generate, List, Revoke API Key
│   │   ├── billing.py               ← Topup, History, Cancel, Submit Proof, Exchange Rate
│   │   ├── logistics.py             ← Cities, Couriers, Cost, Tracking
│   │   ├── profile.py               ← Profile info, Sessions, Preferences, Security OTP
│   │   └── telegram_bot.py          ← Webhook Telegram (/cek_kuota command)
│   ├── schemas/
│   │   └── schemas.py               ← Semua Pydantic schema (request/response models)
│   └── utils/
│       ├── api_key_auth.py          ← Middleware autentikasi X-API-Key
│       ├── crypto_validator.py      ← Validasi tx_hash via BaseScan API
│       ├── dependencies.py          ← get_current_user (JWT decoder)
│       ├── exchange_rate.py         ← CoinGecko API untuk kurs IDR/USD
│       ├── mailer.py                ← Integrasi Resend.com API
│       ├── security.py              ← Hashing password (argon2)
│       ├── security_utils.py        ← OTP generation & validation
│       ├── seed_data.py             ← Seed data awal (cities, couriers)
│       ├── migrate_billing.py       ← Skrip migrasi kolom billing
│       ├── migrate_db.py            ← Skrip migrasi kolom umum
│       ├── recalculate_quotas.py    ← Recalculate quota_used dari transactions
│       ├── setup_triggers.py        ← Setup DB trigger (opsional)
│       └── sync_schema.py           ← Sinkronisasi schema DB
├── frontend/
│   ├── index.html                   ← Premium Landing Page + Auth Modal
│   ├── dashboard.html               ← Dashboard utama (3093 baris, single-file app)
│   └── assets/
│       ├── style.css                ← Global & Landing styles
│       ├── hero.png                 ← Legacy background
│       └── img/
│           ├── hero_bg.png          ← Premium Hero Background
│           └── payments/            ← Logo crypto (base_usdc.png, plasma_usdt.png)
├── backups/                         ← SQL backup snapshot
├── scratch/                         ← Script debugging & maintenance
├── postman/collection.json          ← Postman collection untuk testing API
├── requirements.txt                 ← Python dependencies
├── CONTEXT.md                       ← ← INI FILE INI
├── WHAT_WAS_BUILT.md                ← Daftar fitur yang sudah dibangun
├── PROGRESS.md                      ← Riwayat perubahan per sesi
└── ISSUES.md                        ← Bug yang ditemukan & statusnya
```

---

## Database Schema (Tabel PostgreSQL)

### `users`
| Kolom | Tipe | Keterangan |
|---|---|---|
| id | Integer PK | Auto-increment |
| username | String UNIQUE | Login identifier |
| email | String UNIQUE | Email verifikasi |
| phone_number | String UNIQUE nullable | Nomor HP |
| hashed_password | String | bcrypt hash |
| is_active | Boolean | Default True |
| is_verified | Boolean | Default False, aktif setelah OTP |
| quota_limit | Integer | Total kuota prepaid yang dimiliki |
| quota_used | Integer | Kuota yang sudah terpakai |
| preferences | JSON | `{lang, timezone, currency, alert_threshold, webhooks}` |
| password_updated_at | DateTime | Waktu terakhir update password |
| security_resend_count | Integer | Counter pengiriman OTP keamanan |
| security_last_resend_at | DateTime | Waktu terakhir kirim OTP keamanan |

### `api_keys`
| Kolom | Tipe | Keterangan |
|---|---|---|
| id | Integer PK | |
| key | String UNIQUE | Key value (UUID-based) |
| label | String | Nama deskriptif key |
| user_id | FK → users | Pemilik key |
| is_active | Boolean | |
| total_requests | Integer | Counter penggunaan key ini |
| request_limit | Integer nullable | Per-key spending limit |
| ip_whitelist | String nullable | Comma-separated IPs |
| status | String | `active`, `suspended`, `limited` |

### `transactions`
| Kolom | Tipe | Keterangan |
|---|---|---|
| id | Integer PK | |
| user_id | FK → users | |
| api_key_id | FK → api_keys nullable | Key target (opsional) |
| order_id | String UNIQUE | Format: `BILL-XXXXXXXX` |
| amount | Integer | Nominal IDR |
| quota_added | Integer | Jumlah request yang dibeli |
| payment_method | String | `midtrans` / `crypto` |
| tx_metadata | JSON nullable | Crypto: `{address, chain, symbol, expected_usd}` |
| tx_hash | String nullable | Blockchain TXID |
| status | String | `pending`, `awaiting_verification`, `success`, `failed`, `expired`, `cancelled` |
| created_at | DateTime | |
| expires_at | DateTime nullable | Batas waktu 1 jam dari created_at |

### `verification_codes`
| Kolom | Tipe | Keterangan |
|---|---|---|
| id | Integer PK | |
| user_id | FK → users | |
| code | String | 6-digit OTP |
| channel | String | `email` / `phone` |
| type | String | `registration`, `password_reset`, `security_update` |
| is_used | Boolean | |
| expires_at | DateTime | |

### `user_sessions`
| Kolom | Tipe | Keterangan |
|---|---|---|
| id | Integer PK | |
| user_id | FK → users | |
| jti | String UNIQUE | JWT ID unik per sesi |
| device_info | String | User-Agent summary |
| ip_address | String | |
| is_active | Boolean | |
| created_at / last_active | DateTime | |

---

## Alur Data (Data Flow)

```
[Frontend JS] 
    → fetch('/auth/login') → dapat JWT token
    → token disimpan di localStorage

[Dashboard Load]
    → /profile/me         → ambil data user + preferences + quota
    → /apikey/list        → tampilkan daftar API Key
    → /v1/billing/exchange-rate → kurs IDR saat ini

[Billing Flow]
    → POST /v1/billing/topup          → buat transaction status=pending
    → POST /v1/billing/submit-proof   → user kirim tx_hash → auto-verify via BaseScan
    → GET  /v1/billing/history        → list semua transaksi, auto-expire yang lewat 1 jam
    → DELETE /v1/billing/cancel/{id}  → batalkan order pending atau expired

[API Key Usage]
    Setiap request ke /v1/* harus include header: X-API-Key: <key>
    Middleware api_key_auth.py akan:
    1. Validasi key aktif
    2. Cek IP whitelist (jika ada)
    3. Cek global quota user (quota_limit - quota_used > 0)
    4. Increment: api_key.total_requests + user.quota_used
```

---

## ATURAN WAJIB untuk IDE (Checklist Sebelum Edit)

### ✅ SEBELUM mengubah file apapun:
1. **Baca file target secara penuh** — jangan asumsi isinya
2. **Identifikasi semua file yang terafektar:**
   - Ubah `models/base.py` → cek `schemas/schemas.py` → cek semua router yang pakai model itu
   - Ubah endpoint di router → cek JS di `dashboard.html` yang memanggil endpoint itu
   - Ubah nama field/kolom → search seluruh project untuk referensinya
3. **Sebutkan sebelum implement:** file mana yang akan diubah + risiko konflik

### ✅ SETELAH mengubah file:
1. Verifikasi tidak ada import rusak
2. Verifikasi schema Pydantic masih cocok dengan model SQLAlchemy
3. Jika ubah DB schema → tulis SQL ALTER yang perlu dijalankan di pgAdmin4
4. **Update PROGRESS.md** dengan ringkasan perubahan yang baru dilakukan
5. **Update ISSUES.md** jika ditemukan bug baru atau bug diselesaikan
6. **Update file .md di akhir setiap sesi** — setelah semua perubahan selesai:
   - PROGRESS.md → tambah entry sesi baru (tanggal + ringkasan perubahan + file diubah)
   - ISSUES.md → update status bug yang diselesaikan (OPEN → RESOLVED) atau tambah bug baru
   - WHAT_WAS_BUILT.md → tambah fitur baru yang diimplementasi
   - QUICK_REFERENCE.md → update persentase komponen jika ada perubahan signifikan
   - CONTEXT.md → update tanggal "terakhir diupdate"
   Lakukan ini SEBELUM mengakhiri sesi, bukan sebagai afterthought.

### ❌ JANGAN PERNAH:
- Menghapus kolom/field tanpa konfirmasi eksplisit dari user
- Mengubah nama endpoint yang sudah ada tanpa update frontend JS
- Membuat file baru tanpa memberitahu posisinya dalam struktur folder
- Menambahkan deklarasi variabel JS (`let`, `const`, `var`) tanpa cek duplikat di `dashboard.html`
- Mendefinisikan fungsi JS di dalam scope fungsi lain jika fungsi itu dipanggil dari luar

### ⚠️ PANTAU SELALU di dashboard.html:
- Semua variabel `let/const/var` di top-level script (line 777–810) harus UNIK
- Fungsi yang dipanggil dari `onclick=` di HTML harus berada di **global scope** (indent 8 spasi, bukan di dalam fungsi lain)
- `formatAmount()` dan `safeFormatDateGlobal()` adalah global function — jangan redefinisi lokal di dalam fungsi lain

---

## Cara Mulai Sesi Baru

Paste prompt ini di awal sesi baru:
```
Baca file CONTEXT.md, WHAT_WAS_BUILT.md, PROGRESS.md, dan ISSUES.md 
di C:\Users\Developer\Documents\Semester 8\pemograman_api\logistics-api 
sebelum melakukan apapun.
```

---

*File ini terakhir diupdate: 2026-04-23 (Sesi Mobile Layout Fix & Visual Stabilization)*
