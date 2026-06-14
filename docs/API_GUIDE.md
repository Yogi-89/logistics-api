# API Guide — Logistics API

Dokumentasi lengkap endpoint API, contoh request/response, dan panduan integrasi.

- **Author:** Yogi Prasetyo (22081010297)
- **Base URL (local):** `http://localhost:8000`
- **Base URL (production):** disesuaikan dengan deployment
- **Swagger Docs:** `<base_url>/docs`
- **Redoc:** `<base_url>/redoc`

---

## 1. Autentikasi

API ini menggunakan **dua lapis autentikasi:**

| Lapis | Header | Digunakan Untuk |
|-------|--------|-----------------|
| **JWT Bearer Token** | `Authorization: Bearer <token>` | Manajemen akun, API Key, billing |
| **API Key** | `X-API-Key: <key>` | Endpoint logistik (v1/cost, v1/tracking, dll) |

> **Flow:** Daftar → Verifikasi OTP → Login (dapat JWT) → Generate API Key → Pakai API Key untuk akses data logistik.

---

## 2. Endpoint Publik

### 2.1 Root Info
```
GET /api/
```
**Auth:** Tidak perlu.

**Response:**
```json
{
  "message": "Welcome to Logistics API",
  "author": "Yogi Prasetyo",
  "nim": "22081010297",
  "docs": "/docs"
}
```

---

## 3. Autentikasi Akun (`/auth`)

### 3.1 Register
```
POST /auth/register
```
**Auth:** Tidak perlu.

**Request Body:**
| Field | Tipe | Required | Keterangan |
|-------|------|----------|------------|
| `username` | string | ✅ | Username unik |
| `email` | string (email) | ✅ | Email valid |
| `password` | string | ✅ | Password akun |
| `phone_number` | string | ❌ | Nomor HP (opsional) |
| `captcha_token` | string | ❌ | Turnstile captcha token |

**Contoh Request:**
```json
{
  "username": "johndoe",
  "email": "john@example.com",
  "password": "SecurePass123!",
  "phone_number": "081234567890"
}
```

**Response (201):**
```json
{
  "id": 1,
  "username": "johndoe",
  "email": "john@example.com",
  "phone_number": "081234567890",
  "is_active": true,
  "is_verified": false,
  "quota_limit": 100,
  "quota_used": 0,
  "preferences": {},
  "password_updated_at": null
}
```

**Error 400:**
```json
{ "detail": "Username already registered" }
```

---

### 3.2 Verifikasi OTP
```
POST /auth/verify-code
```
**Auth:** Tidak perlu.

**Request Body:**
```json
{
  "code": "123456",
  "channel": "email",
  "type": "registration"
}
```

**Response:**
```json
{
  "message": "Akun berhasil diverifikasi!",
  "status": "verified"
}
```

**Error 400:**
```json
{ "detail": "Kode verifikasi salah atau sudah kedaluwarsa" }
```

---

### 3.3 Login
```
POST /auth/login
```
**Auth:** Tidak perlu.  
**Header:** `X-Captcha-Token: <turnstile_token>` (opsional untuk development).

**Request Body:**
```json
{
  "username": "johndoe",
  "password": "SecurePass123!"
}
```

**Response (200):**
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIs...",
  "token_type": "bearer"
}
```

**Error 401:**
```json
{ "detail": "Incorrect username or password" }
```

**Error 403 (Belum verifikasi):**
```json
{ "detail": "NEED_VERIFICATION" }
```

---

### 3.4 Kirim Ulang Kode Verifikasi
```
POST /auth/resend-registration-code
```
**Auth:** Tidak perlu.  
**Rate limit:** Maks 3x per 24 jam, delay 60s → 120s → 180s.

**Request Body:**
```json
{
  "email": "john@example.com",
  "type": "registration"
}
```

**Response:**
```json
{
  "message": "Kode baru telah dikirim!",
  "resend_count": 1,
  "next_delay": 120
}
```

**Error 429:**
```json
{ "detail": "Batas pengiriman ulang kode telah tercapai (Max 3x per 24 jam)." }
```

---

## 4. Manajemen API Key (`/apikey`)

> Semua endpoint di section ini memerlukan **JWT Bearer Token** dari hasil login.

### 4.1 Generate API Key
```
POST /apikey/generate
```
**Auth:** `Bearer <JWT>`

**Request Body:**
```json
{
  "label": "Dashboard App",
  "request_limit": 1000
}
```

| Field | Tipe | Required | Keterangan |
|-------|------|----------|------------|
| `label` | string | ✅ | Nama label untuk identifikasi |
| `request_limit` | int | ❌ | Batas request bulanan |

**Response (200):**
```json
{
  "id": 1,
  "key": "sk_example_generated_api_key",
  "label": "Dashboard App",
  "is_active": true,
  "created_at": "2026-06-12T18:00:00",
  "total_requests": 0,
  "request_limit": 1000,
  "ip_whitelist": null,
  "status": "active"
}
```

---

### 4.2 List Semua API Key
```
GET /apikey/list
```
**Auth:** `Bearer <JWT>`

**Response:**
```json
[
  {
    "id": 1,
    "key": "sk_example_generated_api_key",
    "label": "Dashboard App",
    "is_active": true,
    "created_at": "2026-06-12T18:00:00",
    "total_requests": 0,
    "request_limit": 1000,
    "ip_whitelist": null,
    "status": "active"
  }
]
```

---

### 4.3 Update Pengaturan API Key
```
PUT /apikey/{key_id}/settings
```
**Auth:** `Bearer <JWT>`

**Request Body (semua opsional):**
```json
{
  "label": "New Label Name",
  "request_limit": 2000,
  "ip_whitelist": "192.168.1.1,192.168.1.2",
  "is_active": true
}
```

**Response:** sama dengan response generate.

---

### 4.4 Revoke / Hapus API Key
```
DELETE /apikey/revoke/{key_id}
```
**Auth:** `Bearer <JWT>`

**Response:**
```json
{ "message": "API Key revoked successfully" }
```

---

## 5. Profil Pengguna (`/profile`)

> Semua endpoint di section ini memerlukan **JWT Bearer Token**.

### 5.1 Lihat Profil Saya
```
GET /profile/me
```
**Auth:** `Bearer <JWT>`

**Response:**
```json
{
  "id": 1,
  "username": "johndoe",
  "email": "john@example.com",
  "phone_number": "081234567890",
  "is_active": true,
  "is_verified": true,
  "quota_limit": 100,
  "quota_used": 0,
  "preferences": {},
  "password_updated_at": null
}
```

---

### 5.2 Request OTP untuk Perubahan Data Sensitif
```
POST /profile/request-otp?action=change_password&channel=email
```
**Auth:** `Bearer <JWT>`  
**Query params:** `action` (email/phone/password), `channel` (email)  
**Body:** `password` (string) — password saat ini untuk verifikasi.

**Contoh Request:**
```
POST /profile/request-otp?action=password&channel=email
Content-Type: application/json

"SecurePass123!"
```

> **Catatan:** Body dikirim sebagai raw string (password saja).

**Response:**
```json
{
  "message": "Kode OTP telah dikirim ke Email Anda.",
  "requires_dual_otp": false,
  "channels": ["email"],
  "resend_count": 1,
  "next_delay": 60
}
```

---

### 5.3 Update Email
```
PUT /profile/update-email
```
**Auth:** `Bearer <JWT>`

```json
{
  "password": "SecurePass123!",
  "new_email": "newemail@example.com",
  "otp_email": "654321"
}
```

**Response:**
```json
{ "message": "Email berhasil diubah" }
```

---

### 5.4 Update Nomor HP
```
PUT /profile/update-phone
```
**Auth:** `Bearer <JWT>`

```json
{
  "password": "SecurePass123!",
  "new_phone": "087654321098",
  "otp_email": "654321"
}
```

**Response:**
```json
{ "message": "Nomor HP berhasil diubah" }
```

---

### 5.5 Update Password
```
PUT /profile/update-password
```
**Auth:** `Bearer <JWT>`

```json
{
  "password": "SecurePass123!",
  "new_password": "NewSecurePass456!",
  "otp_email": "654321"
}
```

**Response:**
```json
{ "message": "Password berhasil diperbarui" }
```

**Error (password sama):**
```json
{ "detail": "Password baru tidak boleh sama dengan password lama" }
```

---

### 5.6 Update Preferensi
```
PATCH /profile/preferences
```
**Auth:** `Bearer <JWT>`

```json
{
  "lang": "id",
  "timezone": "Asia/Jakarta",
  "currency": "IDR",
  "alert_threshold": 80,
  "webhooks": {
    "telegram_bot_token": "123:abc",
    "telegram_chat_id": "987654321"
  }
}
```

---

### 5.7 Test Webhook / Telegram
```
POST /profile/test-webhook
```
**Auth:** `Bearer <JWT>`

```json
{
  "channel": "telegram",
  "bot_token": "123:abc",
  "chat_id": "987654321"
}
```

```json
{ "status": "success", "message": "Test notification sent successfully!" }
```

---

### 5.8 List Session Aktif
```
GET /profile/sessions
```
**Auth:** `Bearer <JWT>`

---

### 5.9 Cabut / Logout Session
```
DELETE /profile/sessions/{session_id}
```
**Auth:** `Bearer <JWT>`

---

## 6. Logistik Data (`/v1`)

> Semua endpoint di section ini memerlukan **API Key** via header `X-API-Key`.

### 6.1 Rekomendasi Kurir Termurah
```
POST /v1/cost/recommend
```
**Auth:** `X-API-Key: <api_key>`  
**Rate limit:** 20 req/menit

**Request Body:**
```json
{
  "origin": 1,
  "destination": 2,
  "weight": 1000,
  "length": 10,
  "width": 10,
  "height": 5
}
```

**Response:**
```json
[
  {
    "courier_name": "JNE",
    "courier_code": "jne",
    "service": "REG",
    "cost": 12000,
    "etd": "2-3 Days",
    "source": "rajaongkir"
  },
  {
    "courier_name": "J&T",
    "courier_code": "jnt",
    "service": "EZ",
    "cost": 12500,
    "etd": "2-3 Days",
    "source": "rajaongkir"
  }
]
```

---

### 6.2 Daftar Kurir
```
GET /v1/couriers
```
**Auth:** `X-API-Key: <api_key>`

**Response:**
```json
[
  {
    "id": 1,
    "name": "JNE",
    "code": "jne",
    "logo_url": null,
    "description": "Jalur Nugraha Ekakurir"
  }
]
```

---

### 6.3 Daftar Kota
```
GET /v1/cities
```
**Auth:** `X-API-Key: <api_key>`

**Response:**
```json
[
  {
    "id": 1,
    "name": "Surabaya",
    "province": "Jawa Timur",
    "type": "Kota",
    "postal_code": "60111"
  }
]
```

---

### 6.4 Daftar Kecamatan
```
GET /v1/cities/{city_id}/subdistricts
```
**Auth:** `X-API-Key: <api_key>`

---

### 6.5 Kalkulasi Ongkos Kirim (Satu Kurir)
```
POST /v1/cost
```
**Auth:** `X-API-Key: <api_key>`  
**Rate limit:** 30 req/menit

**Request Body:**
```json
{
  "origin": 1,
  "destination": 2,
  "weight": 1000,
  "courier": "jne",
  "length": 10,
  "width": 10,
  "height": 5
}
```

**Response:**
```json
{
  "origin": "Surabaya",
  "destination": "Jakarta Pusat",
  "courier": "JNE",
  "actual_weight": 1000,
  "volumetric_weight": 83,
  "effective_weight": 1000,
  "results": [
    {
      "service": "REG",
      "description": "Reguler Service",
      "cost": 12000,
      "etd": "2-3 Days",
      "source": "rajaongkir"
    },
    {
      "service": "YES",
      "description": "Yakin Esok Sampai",
      "cost": 28000,
      "etd": "1 Day",
      "source": "rajaongkir"
    }
  ],
  "currency": "IDR"
}
```

---

### 6.6 Buat Shipment / Generate AWB
```
POST /v1/shipments
```
**Auth:** `X-API-Key: <api_key>`  
**Rate limit:** 10 req/menit

**Request Body:**
```json
{
  "courier_id": 1,
  "origin_city_id": 1,
  "destination_city_id": 2,
  "service_type": "REG",
  "weight_gram": 1000,
  "length_cm": 10,
  "width_cm": 10,
  "height_cm": 5,
  "insurance_value": 0.0,
  "sender_name": "John Doe",
  "sender_phone": "081234567890",
  "sender_address": "Jl. Merdeka No. 10, Surabaya",
  "sender_postal_code": "60111",
  "receiver_name": "Jane Smith",
  "receiver_phone": "087654321098",
  "receiver_address": "Jl. Thamrin No. 5, Jakarta Pusat",
  "receiver_postal_code": "10340"
}
```

| Field | Tipe | Required | Validasi |
|-------|------|----------|----------|
| `courier_id` | int | ✅ | ID kurir dari `/v1/couriers` |
| `origin_city_id` | int | ✅ | ID kota asal |
| `destination_city_id` | int | ✅ | ID kota tujuan |
| `service_type` | string | ✅ | REG, EXP, YES, OKE, SPS |
| `weight_gram` | int | ✅ | 1–70000 gram |
| `length_cm` | int | ❌ | 1–300 cm |
| `width_cm` | int | ❌ | 1–300 cm |
| `height_cm` | int | ❌ | 1–300 cm |
| `insurance_value` | float | ❌ | ≥ 0 |
| `sender_name` | string | ✅ | Min 2 karakter |
| `sender_phone` | string | ✅ | Format HP Indonesia |
| `sender_address` | string | ✅ | Min 10 karakter |
| `sender_postal_code` | string | ❌ | 5 digit |
| `receiver_name` | string | ✅ | Min 2 karakter |
| `receiver_phone` | string | ✅ | Format HP Indonesia |
| `receiver_address` | string | ✅ | Min 10 karakter |
| `receiver_postal_code` | string | ❌ | 5 digit |

**Response:**
```json
{
  "status": "success",
  "awb": "SS-REG-A1B2C3D4",
  "shipping_cost": 12000,
  "etd": "2-3 Days"
}
```

---

### 6.7 Lacak Paket (Tracking)
```
GET /v1/tracking/{awb}
```
**Auth:** `X-API-Key: <api_key>`

**Response:**
```json
{
  "awb": "SS-REG-A1B2C3D4",
  "courier": "JNE",
  "status": "IN_TRANSIT",
  "service_type": "REG",
  "weight_gram": 1000,
  "shipping_cost": 12000,
  "sender_name": "John Doe",
  "receiver_name": "Jane Smith",
  "receiver_address": "Jl. Thamrin No. 5, Jakarta Pusat",
  "history": [
    {
      "status": "MANIFESTED",
      "location": "Origin Warehouse",
      "timestamp": "2026-06-12T10:00:00",
      "note": "Package is being prepared for shipment"
    },
    {
      "status": "IN_TRANSIT",
      "location": "Jakarta Hub",
      "timestamp": "2026-06-12T16:00:00",
      "note": "Package arrived at transit hub"
    }
  ]
}
```

---

### 6.8 Update Status Tracking
```
POST /v1/tracking/{awb}/update?status=DELIVERED&location=Jakarta&note=Diterima+oleh+penerima
```
**Auth:** `X-API-Key: <api_key>`  
**Rate limit:** 20 req/menit

**Query params:**
| Param | Tipe | Required |
|-------|------|----------|
| `status` | string | ✅ |
| `location` | string | ✅ |
| `note` | string | ❌ |

**Response:**
```json
{
  "status": "success",
  "current_status": "DELIVERED"
}
```

---

### 6.9 Download Label Pengiriman (PDF)
```
GET /v1/label/{awb}?lang=id
```
**Auth:** `X-API-Key: <api_key>`

**Params:** `lang` = `id` (Indonesia) atau `en` (English)

**Response:** File PDF (Shipping Label A6).

---

### 6.10 Cek Kuota API
```
GET /v1/quota
```
**Auth:** `X-API-Key: <api_key>`

**Response:**
```json
{
  "status": "success",
  "username": "johndoe",
  "quota_limit": 100,
  "quota_used": 12,
  "quota_remaining": 88,
  "is_active": true
}
```

---

## 7. Billing & Transaksi (`/v1/billing`)

> Endpoint billing memerlukan **JWT Bearer Token**, kecuali `/contact` dan `/exchange-rate` yang publik.

### 7.1 Kurs Crypto (Publik)
```
GET /v1/billing/exchange-rate
```

**Response:**
```json
{
  "rate": 16250.50,
  "currency": "IDR",
  "provider": "CoinGecko"
}
```

---

### 7.2 Kontak Admin (Publik)
```
GET /v1/billing/contact
```

**Response:**
```json
{
  "name": "Admin ShipStream",
  "email": "admin@shipstream.dev",
  "whatsapp": "08123456789",
  "whatsapp_url": "https://wa.me/08123456789"
}
```

---

### 7.3 Topup Kuota
```
POST /v1/billing/topup
```
**Auth:** `Bearer <JWT>`  
**Syarat:** Akun harus terverifikasi.

**Request Body:**
```json
{
  "api_key_id": 1,
  "amount": 50000,
  "quota_added": 500,
  "payment_method": "crypto",
  "chain": "base",
  "symbol": "USDC"
}
```

| Field | Tipe | Required | Keterangan |
|-------|------|----------|------------|
| `api_key_id` | int | ❌ | ID API Key yang ingin di-topup |
| `amount` | int | ✅ | Nominal IDR |
| `quota_added` | int | ✅ | Jumlah kuota ditambahkan |
| `payment_method` | string | ❌ | `midtrans` atau `crypto` |
| `chain` | string | ❌ | `base`, `polygon`, `arbitrum` |
| `symbol` | string | ❌ | `USDC`, `USDT` |

**Response:**
```json
{
  "id": 1,
  "order_id": "BILL-A1B2C3D4",
  "api_key_id": 1,
  "amount": 50000,
  "quota_added": 500,
  "payment_method": "crypto",
  "tx_metadata": {
    "address": "0x0000000000000000000000000000000000000000",
    "chain": "base",
    "symbol": "USDC",
    "expected_usd": 3.08,
    "network": "Mainnet"
  },
  "tx_hash": null,
  "actual_crypto_amount": null,
  "actual_saldo": null,
  "status": "pending",
  "status_reason": null,
  "created_at": "2026-06-12T18:00:00",
  "expires_at": "2026-06-12T19:00:00"
}
```

---

### 7.4 Riwayat Transaksi
```
GET /v1/billing/history
```
**Auth:** `Bearer <JWT>`

---

### 7.5 Batalkan Pesanan
```
DELETE /v1/billing/cancel/{order_id}
```
**Auth:** `Bearer <JWT>`

**Response:**
```json
{
  "message": "Order BILL-A1B2C3D4 telah dibatalkan.",
  "order_id": "BILL-A1B2C3D4",
  "status": "cancelled"
}
```

---

### 7.6 Submit Bukti Pembayaran Crypto
```
POST /v1/billing/submit-proof/{order_id}?tx_hash=0x...
```
**Auth:** Tidak perlu (submit by anyone with TXID).

**Query params:** `tx_hash` — Transaction hash (0x + 64 hex chars).

**Response (sukses):**
```json
{
  "message": "Pembayaran BERHASIL diverifikasi secara otomatis! Kuota telah ditambahkan.",
  "status": "success"
}
```

---

### 7.7 Konfirmasi Pembayaran (Admin)
```
POST /v1/billing/admin/confirm-payment/{order_id}
```
**Auth:** Admin only.

---

## 8. Status Code Umum

| Kode | Arti |
|------|------|
| 200 | Sukses |
| 201 | Berhasil dibuat |
| 400 | Bad Request — validasi gagal |
| 401 | Unauthorized — auth gagal |
| 403 | Forbidden — belum verifikasi / tidak punya akses |
| 404 | Not Found — data tidak ditemukan |
| 429 | Too Many Requests — rate limit |
| 500 | Internal Server Error |

---

## 9. Rate Limiting

| Endpoint | Limit |
|----------|-------|
| `/v1/cost/recommend` | 20/menit |
| `/v1/couriers` | 60/menit |
| `/v1/cities` | 60/menit |
| `/v1/cities/{id}/subdistricts` | 60/menit |
| `/v1/cost` | 30/menit |
| `/v1/shipments` | 10/menit |
| `/v1/tracking/{awb}/update` | 20/menit |
| `/auth/resend-registration-code` | 3x/24jam |

---

## 10. Format AWB

Format nomor resi: `SS-{SERVICE_TYPE}-{RANDOM_8}`  
Contoh: `SS-REG-A1B2C3D4`, `SS-EXP-XY9Z8W7V`

---

## 11. Integrasi RajaOngkir

API mendukung integrasi **real-time** dengan RajaOngkir via environment variable `RAJA_ONGKIR_API_KEY`. Jika key tidak diset, sistem otomatis fallback ke kalkulasi internal.

---

_Dokumentasi ini dibuat untuk keperluan EAS Semester 6 — Mata Kuliah Pemograman API._
