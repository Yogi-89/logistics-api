# 📊 PROGRESS — ShipStream Logistics API
> Status per: 2026-04-23 | Dikompilasi dari PROGRESS.md + ISSUES.md

---

## Status Keseluruhan
**[████████████] 100%** — Final Polish Selesai

---

## ✅ Fitur Yang Sudah Selesai

### Backend (FastAPI)
- [x] Auth: Register, Login (JWT + Session Tracking), Verify Code, Resend OTP
- [x] Auth: Debug endpoint OTP (`DEBUG_MODE` protected)
- [x] API Key: Generate, List, Update Settings (label, limit, IP whitelist), Revoke
- [x] Logistics: List Couriers, List Cities, Hitung Ongkir, Track AWB, Generate PDF Label
- [x] Logistics: Rate-limit headers (`X-RateLimit-*`) di semua endpoint
- [x] Billing: Create Topup (pending invoice), History, Cancel Order
- [x] Billing: Crypto Auto-Verify via BaseScan API (Base chain + Plasma chain)
- [x] Billing: Toleransi ±0.05 USD, fallback RPC jika explorer API gagal
- [x] Billing: Auto-expire pending (1 jam) & awaiting_verification (2 jam)
- [x] Billing: Admin manual confirm endpoint
- [x] Billing: Exchange rate live via CoinGecko
- [x] Profile: Get Me, Update Email/Phone/Password (semua perlu OTP)
- [x] Profile: Request OTP dengan rate-limit & exponential backoff
- [x] Profile: Preferences (lang, timezone, currency, alert_threshold, webhooks)
- [x] Profile: Test Webhook (HTTP + Telegram), Auto setWebhook Telegram
- [x] Profile: Session Management (List, Revoke per session)
- [x] Telegram Bot: Webhook handler `/cek_kuota`, `/start`
- [x] Static Frontend: Serve dari FastAPI langsung

### Frontend
- [x] Landing Page (index.html): Hero section, fitur highlight, pricing, auth modal
- [x] Auth Modal: Login & Register form, captcha-ready (dibypass)
- [x] Dashboard (dashboard.html): Tab-based SPA
  - [x] Tab Docs: API Playground (cek ongkir, tracking, daftar kurir/kota)
  - [x] Tab Keys: Kelola API Key (create, settings, revoke)
  - [x] Tab Billing: Topup (Midtrans + Crypto), history transaksi, countdown
  - [x] Tab Profile: Info user, ganti email/phone/password + OTP flow
  - [x] Tab Settings: Preferensi, Webhook setup (HTTP + Telegram), Session management
- [x] Internasionalisasi (i18n): EN & ID, toggle bahasa real-time
- [x] Dark/Light mode toggle
- [x] Mobile Responsive: Semua tab sudah 1-kolom di mobile
- [x] Copy to clipboard fallback (iOS/WebView compat)
- [x] Global interval cleanup saat logout (mencegah memory leak)
- [x] Playground state persistence antar tab

### DevOps / Tooling
- [x] Postman Collection tersedia di `postman/collection.json`
- [x] Backup DB tersedia di `backups/`
- [x] Seed scripts: `seed_cities.py`, `app/utils/seed_data.py`
- [x] Migration scripts di `app/utils/` dan root

---

## 🟡 Known Limitations (Bukan Bug, By Design)

| Item | Detail |
|------|--------|
| Midtrans | Simulasi saja, tidak terhubung ke gateway asli |
| Email OTP | Menggunakan Resend.com (`re_Zckt2kfw...`) — perlu verifikasi domain untuk produksi |
| Exchange Rate | CoinGecko free tier, bisa rate-limited; fallback hardcoded 16000 |
| Shipping Cost | Kalkulasi ongkir adalah simulasi berbasis formula arbitrary (bukan API Raja Ongkir) |
| Tracking | Data tracking adalah seed/dummy, bukan real-time dari kurir |

---

## 📋 Bug Terakhir yang Diselesaikan (Terbaru Dulu)

| Tanggal | Bug | File |
|---------|-----|------|
| 2026-04-23 | Settings tab mobile masih 2 kolom | style.css |
| 2026-04-23 | Security Health card tidak simetris | dashboard.html, style.css |
| 2026-04-23 | Playground dropdown reset saat pindah tab | dashboard.html |
| 2026-04-23 | Memory leak dari timer/interval tidak dibersihkan | dashboard.html |
| 2026-04-23 | Copy clipboard gagal di iOS/WebView | dashboard.html |
| 2026-04-23 | Toast overlap dengan navigasi mobile | style.css |
| 2026-04-22 | Hapus IP Whitelist tidak tersimpan (Pydantic field_set) | apikey.py |
| 2026-04-22 | Duplicate email register → HTTP 500 | auth.py |
| 2026-04-21 | NameError timedelta di profile.py | profile.py |
| 2026-04-20 | Dashboard tidak bisa diklik (duplicate `let currentTab`) | dashboard.html |
| 2026-04-20 | SyntaxError: await outside async function | billing.py |
| 2026-04-20 | Countdown & format jam tidak sesuai WIB | dashboard.html |
| 2026-04-19 | Billing modal detail crash (btoa encoding) | dashboard.html |

---

## 🔮 Hal Yang Mungkin Dikerjakan Selanjutnya (Jika Ada)
- [ ] Dokumentasi PDF resmi untuk submission UAS
- [ ] Unit test (pytest) untuk endpoint kritis
- [ ] Rate limiting middleware berbasis Redis (saat ini hanya DB-based)
- [ ] Integrasi Raja Ongkir API untuk data ongkir real
- [ ] SMS OTP via Twilio/Fonnte
