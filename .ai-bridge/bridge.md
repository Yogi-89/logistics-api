# 🌉 AI BRIDGE — ShipStream Logistics API
> File ini adalah titik masuk utama bagi AI assistant di sesi baru.
> Baca file ini + struktur.md + progress.md sebelum mengerjakan apapun.

---

## 🎯 Tentang Project
**Nama**: ShipStream — Logistics Rate & Tracking API  
**Pemilik**: Yogi Prasetyo (NIM: 22081010297)  
**Konteks**: Tugas UTS/UAS Semester 8 — Mata Kuliah Pemrograman API  
**Stack**: FastAPI (Python) + PostgreSQL + Vanilla JS Frontend  
**Status saat ini**: ✅ Fungsional penuh, final polish selesai (per 2026-04-23)

---

## 📁 Entry Points Penting
| File | Fungsi |
|------|--------|
| `app/main.py` | App entrypoint, routing utama, static mount |
| `app/models/base.py` | Semua model database SQLAlchemy |
| `app/schemas/schemas.py` | Semua Pydantic schema (validasi request/response) |
| `app/routers/` | Semua endpoint API (auth, billing, logistics, dll) |
| `frontend/dashboard.html` | Dashboard SPA utama (Vanilla JS, sangat besar) |
| `frontend/index.html` | Landing page + modal auth (login/register) |
| `frontend/assets/style.css` | CSS global untuk seluruh frontend |
| `.env` | Konfigurasi environment (DB, JWT, API keys) |

---

## ⚠️ Hal Kritis yang Harus Diketahui AI

### 1. Dashboard HTML adalah monolith besar
`dashboard.html` berisi semua JS inline dalam satu file besar. Saat mengedit, **SELALU** cek:
- Tidak ada duplikasi deklarasi `let/const/var` di scope global
- Fungsi yang dipanggil via `onclick=""` harus di global scope (indent 8 spasi di root)
- Fungsi `showConfirmModal` (BUKAN `showConfirmDialog`) untuk dialog konfirmasi

### 2. Sistem Quota (Global Pool)
- Quota disimpan di `User.quota_limit` dan `User.quota_used` (BUKAN di per-API-key)
- API Key hanya punya `request_limit` sebagai sub-limit opsional
- Saat topup sukses → `user.quota_limit += quota_added`

### 3. Crypto Payment Flow
- Order dibuat → user kirim crypto → submit TXID → auto-verify via BaseScan API → quota ditambah
- Toleransi ±0.05 USD
- Fallback: admin manual confirm via `/v1/billing/admin/confirm-payment/{order_id}`

### 4. Auth
- JWT dengan session tracking di tabel `user_sessions`
- Verifikasi OTP dibypass (`is_verified=True` otomatis) — **jangan aktifkan di produksi tanpa setup SMTP**
- Debug endpoint aktif: `GET /auth/debug/otp/{username}` (hanya saat `DEBUG_MODE=True`)

### 5. Database
- PostgreSQL di `localhost:5432/logistics_api`
- Ada backup di folder `backups/` (tanggal 2026-04-15)
- Migration scripts ada di `app/utils/migrate_*.py` dan root

---

## 🚫 Jangan Lakukan
- Jangan aktifkan verifikasi OTP tanpa setup SMTP/Resend yang benar
- Jangan expose `DEBUG_MODE=True` di produksi
- Jangan edit `dashboard.html` tanpa membaca ISSUES.md pola bug dulu
- Jangan ganti struktur quota dari Global Pool ke per-key tanpa refactor billing

---

## 📞 Kontak Admin (dari .env)
- **Nama**: Yogi Prasetyo
- **Email**: tumbalairdrop3@gmail.com
- **WhatsApp**: 6285817698693

---

## ?? Scale-up Roadmap
1. **Alembic Migration**: Transisi dari Base.metadata.create_all() ke manajemen skema industri standard.
2. **Logistics Engine Upgrade**: Kalkulasi ongkir realistis dengan metrik Volumetrik vs Aktual, dan integrasi data Subdistrict.
3. **Rate Limiting**: Migrasi dari quota sederhana ke *Redis/SlowAPI Rate Limit* yang robust untuk mencegah API Abuse.
4. **Shipment (AWB) API**: Endpoint khusus untuk Generate Nomor Resi dan track tahapan pengiriman (Manifested, Transit, Delivered).

---

## ?? Staging Strategy & Branching
- **main**: Source of truth produksi. Wajib stabil, protected branch, no direct commit.
- **staging**: Pre-production environment. Untuk testing keseluruhan sebelum dirilis ke main.
- **develop**: Branch kerja aktif tempat integrasi fitur-fitur baru (Alembic, Rate Limit, Endpoint Logistik).
- **GitHub Actions**: Wajib lolos CI Pipeline (Linting, Test) saat Pull Request ke staging/main.
