# ShipStream — Logistics Rate & Tracking API — What Was Built

> Update terakhir: 2026-04-23

---

## 🔐 Sistem Autentikasi

| Fitur | Status | Endpoint |
|---|---|---|
| Register user baru | ✅ Done | `POST /auth/register` |
| Verifikasi OTP (email) | ✅ Done | `POST /auth/verify-code` |
| Kirim ulang OTP | ✅ Done | Lewat UI |
| Login → dapat JWT token | ✅ Done | `POST /auth/login` |
| Redirect ke dashboard jika sudah login | ✅ Done | Frontend |
| **Premium Auth Modal Container** | ✅ Done | `index.html` (Modal overlay) |
| Debug OTP endpoint (dev only) | ✅ Done | `GET /auth/debug/otp/{username}` |

---

## 🗝️ Manajemen API Key

| Fitur | Status | Endpoint |
|---|---|---|
| Generate API Key baru | ✅ Done | `POST /apikey/generate` |
| List semua API Key milik user | ✅ Done | `GET /apikey/list` |
| Revoke/hapus API Key | ✅ Done | `DELETE /apikey/revoke/{key_id}` |
| Update label, limit, IP whitelist | ✅ Done | `PUT /apikey/{key_id}/settings` |
| Custom dropdown premium (portal pattern) | ✅ Done | Frontend UI |
| Copy API Key ke clipboard | ✅ Done | Frontend UI |
| **Client-side Duplicate Label Check** | ✅ Done | `dashboard.html` |

---

## 📦 Layanan Logistik (Pakai API Key)

| Fitur | Status | Endpoint |
|---|---|---|
| Daftar kota | ✅ Done | `GET /v1/cities` |
| Daftar kurir | ✅ Done | `GET /v1/couriers` |
| Cek ongkos kirim | ✅ Done | `GET /v1/cost` |
| Tracking resi | ✅ Done | `GET /v1/tracking/{awb}` |
| Cek kuota user via API | ✅ Done | `GET /v1/quota` |
| Middleware auth X-API-Key | ✅ Done | `api_key_auth.py` |
| Cek IP whitelist | ✅ Done | `api_key_auth.py` |

---

## 💳 Sistem Billing & Top-up

| Fitur | Status | Endpoint/File |
|---|---|---|
| Buat invoice top-up (pending) | ✅ Done | `POST /v1/billing/topup` |
| Lihat riwayat transaksi | ✅ Done | `GET /v1/billing/history` |
| Auto-expire transaksi >1 jam | ✅ Done | `billing.py` → `_auto_expire_pending()` |
| Batalkan order (pending/expired) | ✅ Done | `DELETE /v1/billing/cancel/{order_id}` |
| Submit TX Hash (crypto) | ✅ Done | `POST /v1/billing/submit-proof/{order_id}` |
| Auto-verify on-chain via BaseScan | ✅ Done | `crypto_validator.py` |
| Exchange rate IDR/USD (CoinGecko) | ✅ Done | `GET /v1/billing/exchange-rate` |
| Konfirmasi pembayaran manual (admin) | ✅ Done | `POST /v1/billing/admin/confirm-payment/{order_id}` |
| Credit quota ke user setelah sukses | ✅ Done | `billing.py` |
| Cache transaksi global `window._billingCache` | ✅ Done | `dashboard.html` |

### Status Transaksi (badge di UI):
| Status DB | Label UI | Warna |
|---|---|---|
| `pending` | PENDING | Biru |
| `awaiting_verification` | AWAITING | Amber/Kuning |
| `success` | SUCCESS | Hijau |
| `expired` / `cancelled` / `failed` | INVALID | Merah (Ditambah keterangan "Kadaluarsa" / "Cancel by user") |

---

## 🖥️ Dashboard UI/UX

| Fitur | Status | File |
|---|---|---|
| Tab Keys — API Key management | ✅ Done | `dashboard.html` |
| Tab Docs — Dokumentasi + Playground | ✅ Done | `dashboard.html` |
| Tab Billing — Riwayat transaksi | ✅ Done | `dashboard.html` |
| Tab Profile — Info akun + sessions | ✅ Done | `dashboard.html` |
| Tab Settings — Preferensi + webhook | ✅ Done | `dashboard.html` |
| Modal checkout Midtrans | ✅ Done | `dashboard.html` |
| Modal checkout Crypto (dengan countdown 1 jam) | ✅ Done | `dashboard.html` |
| Modal detail transaksi (SUCCESS, AWAITING, INVALID) | ✅ Done | `dashboard.html` |
| Modal konfirmasi (custom, menggantikan `confirm()`) | ✅ Done | `showConfirmModal()` |
| Countdown timer di billing list (untuk PENDING) | ✅ Done | `startBillingCountdown()` |
| Floating dock navigation (mobile) | ✅ Done | `dashboard.html` |
| i18n (Indonesia/English) | ✅ Done | `translations` object |
| Preferensi timezone, currency | ✅ Done | `preferences` JSON di DB |
| Banner verifikasi akun | ✅ Done | `dashboard.html` |
| Global quota display di navbar | ✅ Done | `dashboard.html` |
| Toast notification system | ✅ Done | `showToast()` |
| Ikon Koin Crypto (USDC/USDT) di Billing & Checkout | ✅ Done | `dashboard.html` |
| Sinkronisasi Waktu UTC & Format 24h (WIB) | ✅ Done | `dashboard.html` |
| Dropdown Pilih API Key di Playground (Premium UI) | ✅ Done | `dashboard.html` |
| **Global Session Interceptor (401)** | ✅ Done | `dashboard.html` |
| **Session Health Polling** | ✅ Done | `dashboard.html` |
| **Optimized Settings Mobile Grid** | ✅ Done | `style.css` |
| **Grid Form Label Alignment** | ✅ Done | `style.css` |

---

## 👤 Profil & Keamanan

| Fitur | Status | Endpoint |
|---|---|---|
| Lihat profil + quota global | ✅ Done | `GET /profile/me` |
| Update email (dengan OTP) | ✅ Done | `PUT /profile/update-email` |
| Update nomor HP | ✅ Done | `PUT /profile/update-phone` |
| Update password (dengan OTP) | ✅ Done | `PUT /profile/update-password` |
| Simpan preferensi (lang, timezone, currency, webhook) | ✅ Done | `PATCH /profile/preferences` |
| Lihat semua sesi aktif | ✅ Done | `GET /profile/sessions` |
| Hapus/revoke sesi | ✅ Done | `DELETE /profile/sessions/{session_id}` |
| Test webhook Telegram | ✅ Done | `POST /profile/test-webhook` |
| Request OTP keamanan | ✅ Done | `POST /profile/request-otp` |
| **Advanced Security Limit (3x/24h)** | ✅ Done | `profile.py` & `auth.py` |
| **Exponential Backoff (60-180s)** | ✅ Done | Backend logic |
| **Premium Email Delivery (Resend)** | ✅ Done | `mailer.py` |
| **Indonesian Label Standardization** | ✅ Done | Clean "diubah" responses |
| **"Soon" Badge UI Markers** | ✅ Done | Phone/SMS features |

---

## 🤖 Telegram Bot

| Fitur | Status | Endpoint |
|---|---|---|
| Webhook handler | ✅ Done | `POST /api/v1/telegram/webhook/{bot_token}` |
| Command `/cek_kuota` | ✅ Done | `telegram_bot.py` |

---

## 🔧 Infrastruktur & DevOps

| Fitur | Status | File |
|---|---|---|
| CORS middleware (allow all origins) | ✅ Done | `main.py` |
| Static file serving (frontend) | ✅ Done | `main.py` |
| Auto create tables on startup | ✅ Done | `Base.metadata.create_all()` |
| Postman collection | ✅ Done | `postman/collection.json` |
| DB backups (SQL dump) | ✅ Done | `backups/` |

---

---
 
 ## 🌐 Landing Page (Industrial Upgrade)
 
 | Fitur | Status | Detail |
 |---|---|---|
 | **Futuristic Hero Section** | ✅ Done | High-impact visuals + Value props |
 | **Feature Grid showcase** | ✅ Done | Unified stack, Security, Webhooks |
 | **Pricing Tiers (Prepaid)** | ✅ Done | Starter, Growth, Enterprise plans |
 | **Sticky Glassmorphism Nav** | ✅ Done | Navigation with quick access |
 | **Auth Integration** | ✅ Done | One-click Modal Login/Register |
 | **Asset Optimization** | ✅ Done | `hero_bg.png` generated & integrated |
 | **Session Termination Alert** | ✅ Done | landing notification handler |
 
 ---
 
 *File ini terakhir diupdate: 2026-04-23 oleh Antigravity*
