# ShipStream — Logistics Rate & Tracking API

Sistem API Logistik sederhana untuk cek tarif dan tracking paket sebagai syarat EAS Pemrograman API.

## 🌟 Fitur Utama (Advanced Version)
- **Global Quota Pool**: Sistem prepaid terpusat. Kuota digunakan bersama oleh semua API Key dalam satu akun.
- **Crypto Payment Automation**: Verifikasi pembayaran otomatis menggunakan **BaseScan API** (Ethereum/Base network).
- **Advanced API Dashboard**: Monitoring penggunaan kuota global dan manajemen API Key real-time.
- **Security**: OTP Verification via **Resend.com**, 3x/24h Daily Limits, and Exponential Backoff for premium protection.

## 🚀 Instalasi & Setup

### 1. Persiapan Database
Pastikan PostgreSQL lokal Anda sudah berjalan. Buat database baru bernama `logistics_api`.

### 2. Environment Variables
Buat file `.env` di root folder dengan konfigurasi berikut:
```env
DATABASE_URL=postgresql://user:password@localhost:5432/logistics_api
SECRET_KEY=isi_dengan_string_acak_panjang
ALGORITHM=HS256
BASESCAN_API_KEY=your_basescan_api_key
MY_CRYPTO_WALLET=your_wallet_address
USDC_CONTRACT_BASE=0x833589fcd6edb6e08f4c7c32d4f71b54bda02913
USD_PRICE_IDR=17000
RESEND_API_KEY=re_your_api_key
DEBUG_MODE=True
```

### 3. Install Dependencies
```bash
pip install -r requirements.txt
```

### 4. Database Schema Sync (Wajib)
Jalankan script ini untuk menyinkronkan tabel PostgreSQL dengan model Global Quota terbaru:
```bash
python -m app.utils.sync_schema
```

### 5. Seed Data (Opsional)
Jalankan script berikut untuk mengisi data dummy (kota/kurir/tracking):
```bash
python -m app.utils.seed_data
```

### 6. Jalankan Aplikasi
```bash
uvicorn app.main:app --reload
```
Buka `http://localhost:8000` untuk API Docs (Swagger) atau dashboard UI.

## 🔒 Catatan Keamanan (Review Internal)

> [!WARNING]
> Proyek ini saat ini menggunakan `allow_origins=["*"]` pada middleware CORS di `main.py`. Pengaturan ini hanya ditujukan untuk **lingkungan pengembangan/testing (Dev Mode)** agar mempermudah testing dari berbagai port.
> **PADA PRODUKSI**: Harus diganti dengan daftar domain yang spesifik.

> [!CAUTION]
> Logic `SECRET_KEY` memiliki fallback jika tidak diisi guna mencegah crash, namun akan mencetak peringatan di console. Pastikan `.env` selalu terkonfigurasi dengan benar di server deployment.

## 📁 Struktur Folder
- `app/`: Logika backend (FastAPI).
    - `routers/`: `auth`, `apikey`, `billing`, `profile`, `logistics`, `telegram_bot`.
    - `utils/`: `crypto_validator`, `exchange_rate`, `security_utils`, `sync_schema`, `migrate_db`.
- `frontend/`: UI Dashboard (HTML/CSS/JS).
- `postman/`: Koleksi testing API Postman.
- `backups/`: SQL backup snapshot berkala.
- `docs/`: Dokumentasi pendukung.

---
**Dibuat Oleh**: Yogi Prasetyo (22081010297)
**Mata Kuliah**: Pemrograman API
**Dosen**: Muhammad Muharrom Al Haromainy, S.Kom., M.Kom.
