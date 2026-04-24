# 🗂️ STRUKTUR — ShipStream Logistics API
> Peta lengkap seluruh folder dan file project

---

## Root Directory
```
logistics-api/
├── .ai-bridge/          ← [BARU] File konteks untuk AI assistant
├── .agents/skills/      ← Skill definitions untuk agent workflow
├── app/                 ← 🔑 Core aplikasi FastAPI
├── backups/             ← SQL dump backup DB (2026-04-15)
├── docs/                ← Kosong (placeholder docs)
├── frontend/            ← 🔑 Seluruh UI (HTML/CSS/JS)
├── postman/             ← Collection Postman untuk testing
├── tests/               ← [BARU] Unit & Integration Tests (pytest)
├── .env                 ← Konfigurasi environment
├── .flake8              ← [BARU] Konfigurasi linting
├── logistics.db         ← SQLite (dev fallback, tidak dipakai aktif)
├── requirements.txt     ← Dependency Python
└── *.md                 ← Berbagai file dokumentasi
```

---

## app/ — Core Backend
```
app/
├── main.py              ← App init, CORS, router include, static mount, endpoint /
├── database.py          ← SQLAlchemy engine, SessionLocal, Base
│
├── models/
│   └── base.py          ← Semua model DB (User, APIKey, City, Courier, Tracking,
│                           Transaction, VerificationCode, UserSession)
│
├── schemas/
│   └── schemas.py       ← Semua Pydantic schema (validasi in/out per endpoint)
│
├── routers/
│   ├── auth.py          ← /auth/* (register, login, verify-code, resend, debug OTP)
│   ├── apikey.py        ← /apikey/* (generate, list, settings, revoke)
│   ├── logistics.py     ← /v1/* (couriers, cities, cost, tracking/{awb}, label/{awb}, quota)
│   ├── billing.py       ← /v1/billing/* (topup, history, cancel, submit-proof, confirm)
│   ├── profile.py       ← /profile/* (me, request-otp, update-*, preferences, sessions)
│   └── telegram_bot.py  ← /api/v1/telegram/webhook/{bot_token}
│
└── utils/
    ├── api_key_auth.py      ← Middleware validasi API Key + quota deduction
    ├── crypto_validator.py  ← Verifikasi TXID via BaseScan API + RPC fallback
    ├── dependencies.py      ← get_current_user (JWT decode + session check)
    ├── exchange_rate.py     ← CoinGecko rate provider (IDR per USD)
    ├── mailer.py            ← Pengiriman email OTP via Resend.com
    ├── security.py          ← Password hash (argon2), JWT create/decode, API key gen
    ├── security_utils.py    ← verify_turnstile (captcha), create_verification_code
    ├── migrate_billing.py   ← Migration: tambah kolom billing
    ├── migrate_db.py        ← Migration: skema awal
    ├── recalculate_quotas.py← Utilitas hitung ulang quota
    ├── seed_data.py         ← Seed kurir & data awal
    ├── setup_triggers.py    ← DB trigger setup
    └── sync_schema.py       ← Sinkronisasi schema DB
```

---

## frontend/ — UI Layer
```
frontend/
├── index.html           ← Landing page + Auth Modal (login/register)
├── dashboard.html       ← 🔑 Dashboard SPA utama (tab-based, JS monolith)
├── dashboard_v2.html    ← Draft versi 2 (tidak aktif dipakai)
│
└── assets/
    ├── style.css        ← 🔑 CSS global semua halaman
    ├── style_temp.txt   ← Backup/draft CSS sementara
    └── img/
        ├── gmail.png, sms.png, whatsapp.jpg  ← Ikon notifikasi
        ├── logistics/   ← Logo kurir (JNE, J&T, SiCepat, Pos, Anteraja)
        ├── payments/    ← Gambar crypto (USDC, USDT)
        ├── qrcodes/     ← QR Code wallet crypto
        └── system/      ← hero_bg.png
```

---

## Database Schema (dari models/base.py)

| Tabel | Kolom Penting |
|-------|--------------|
| `users` | id, username, email, phone_number, hashed_password, is_verified, quota_limit, quota_used, preferences (JSON), resend_count |
| `api_keys` | id, key, label, user_id (FK), is_active, total_requests, request_limit, ip_whitelist, status |
| `cities` | id, name, province, type, postal_code |
| `couriers` | id, name, code, logo_url, description |
| `tracking` | id, awb, courier_id (FK), status, origin_city_id, destination_city_id, sender/receiver info, history (JSON) |
| `transactions` | id, user_id (FK), order_id, amount, quota_added, payment_method, tx_hash, status, expires_at |
| `verification_codes` | id, user_id (FK), code, channel, type, is_used, expires_at |
| `user_sessions` | id, user_id (FK), jti, device_info, ip_address, is_active, last_active |

---

## API Routes Summary

| Prefix | Router | Auth |
|--------|--------|------|
| `/auth/*` | auth.py | Public |
| `/apikey/*` | apikey.py | JWT Bearer |
| `/v1/*` | logistics.py | API Key Header |
| `/v1/billing/*` | billing.py | JWT Bearer |
| `/profile/*` | profile.py | JWT Bearer |
| `/api/v1/telegram/*` | telegram_bot.py | Token in URL |
| `/` `/dashboard` | main.py | Public (static) |

---

## File Dokumentasi di Root

| File | Isi |
|------|-----|
| `README.md` | Overview project |
| `PROGRESS.md` | Log progress per sesi |
| `ISSUES.md` | Bug tracker + pola bug preventif |
| `CONTEXT.md` | Konteks proyek untuk AI |
| `TECH_USED.md` | Teknologi yang digunakan |
| `CRITICAL_FIXES.md` | Fix kritis yang pernah dilakukan |
| `IMPLEMENTATION_SUMMARY.md` | Ringkasan implementasi |
| `WHAT_WAS_BUILT.md` | Deskripsi fitur yang dibangun |
| `DETAILED_ANALYSIS.md` | Analisis mendalam sistem |
| `IMPROVEMENTS_SUMMARY.md` | Daftar perbaikan yang sudah dilakukan |
| `UI-UX_IMPROVEMENTS.md` | Catatan perbaikan UI/UX |
