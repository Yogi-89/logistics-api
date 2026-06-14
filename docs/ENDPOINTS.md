# API Endpoints – Logistics API

| Method | Endpoint | Deskripsi |
|--------|----------|-----------|
| `GET` | `/` | Root — status server & dokumentasi link |
| `GET` | `/docs` | Swagger UI (FastAPI otomatis) |
| `GET` | `/redoc` | ReDoc (FastAPI otomatis) |

---

## Auth

| Method | Endpoint | Deskripsi |
|--------|----------|-----------|
| `POST` | `/auth/register` | Registrasi user baru |
| `POST` | `/auth/login` | Login, mengembalikan JWT token |
| `POST` | `/auth/verify-otp` | Verifikasi kode OTP email |
| `POST` | `/auth/resend-otp` | Kirim ulang kode OTP |

---

## API Key

| Method | Endpoint | Deskripsi |
|--------|----------|-----------|
| `POST` | `/apikey/generate` | Generate API Key baru |
| `GET` | `/apikey/list` | Lihat semua API Key milik user |
| `PUT` | `/apikey/{key_id}/settings` | Update label, limit, whitelist IP, atau status API Key |
| `DELETE` | `/apikey/revoke/{key_id}` | Revoke / hapus API Key |

---

## Cities

| Method | Endpoint | Deskripsi |
|--------|----------|-----------|
| `GET` | `/v1/cities` | Daftar semua kota |
| `GET` | `/v1/cities/{city_id}` | Detail satu kota |

---

## Couriers

| Method | Endpoint | Deskripsi |
|--------|----------|-----------|
| `GET` | `/v1/couriers` | Daftar semua kurir |

---

## Shipments

| Method | Endpoint | Deskripsi |
|--------|----------|-----------|
| `POST` | `/v1/shipments` | Buat shipment baru (mengembalikan AWB) |
| `GET` | `/v1/label/{awb}` | Generate shipping label PDF berdasarkan AWB |

---

## Tracking

| Method | Endpoint | Deskripsi |
|--------|----------|-----------|
| `GET` | `/v1/tracking/{awb}` | Lacak status pengiriman |
| `PUT` | `/v1/tracking/{awb}/update` | Update status tracking (Auth required) |

---

> **Base URL:** `http://localhost:8000`  
> **Autentikasi:** JWT Bearer token (dari `/auth/login`) atau `X-API-Key` header
