# Endpoint index

Complete, always-current reference: `/docs` (Swagger) or `/redoc` on any running instance.
This page is a compact map of what exists.

Legend: **key** = requires `X-API-Key`, **jwt** = requires `Authorization: Bearer <token>`, — = public.

## Service

| Method | Path | Auth | Purpose |
|---|---|---|---|
| GET | `/api/` | — | Health/identity payload |
| GET | `/` | — | Landing page / dashboard entry |
| GET | `/docs`, `/redoc`, `/openapi.json` | — | Interactive API reference |

## Authentication

| Method | Path | Auth | Purpose |
|---|---|---|---|
| POST | `/auth/register` | — | Create an account, emits an email OTP |
| POST | `/auth/verify-code` | — | Activate the account with the OTP |
| POST | `/auth/login` | captcha header | Exchange credentials for a JWT |
| POST | `/auth/resend-registration-code` | — | Re-send the OTP (rate limited) |
| GET | `/auth/debug/otp/{username}` | — | Debug only; disabled when `DEBUG_MODE=false` |

## API keys

| Method | Path | Auth | Purpose |
|---|---|---|---|
| POST | `/apikey/generate` | jwt | Create a key (label, optional limits/allow-list) |
| GET | `/apikey/list` | jwt | List keys with usage counters |
| PUT | `/apikey/{key_id}/settings` | jwt | Update label, limit, IP allow-list |
| DELETE | `/apikey/revoke/{key_id}` | jwt | Revoke a key |

## Logistics (metered)

| Method | Path | Auth | Purpose |
|---|---|---|---|
| POST | `/v1/cost` | key | Shipping cost for one courier |
| POST | `/v1/cost/recommend` | key | Cheapest courier recommendation |
| GET | `/v1/couriers` | key | Courier catalogue |
| GET | `/v1/cities` | key | City directory |
| GET | `/v1/cities/{city_id}/subdistricts` | key | Subdistricts for a city |
| POST | `/v1/shipments` | key | Create a shipment, returns an AWB |
| GET | `/v1/tracking/{awb}` | key | Tracking status and history |
| POST | `/v1/tracking/{awb}/update` | key | Append a tracking event |
| GET | `/v1/label/{awb}` | key | Printable label (PDF, `?lang=id|en`) |
| GET | `/v1/quota` | key | Remaining quota for the account |

## Billing

| Method | Path | Auth | Purpose |
|---|---|---|---|
| POST | `/v1/billing/topup` | jwt | Create an order (`crypto` or `qris`) |
| GET | `/v1/billing/history` | jwt | Orders, auto-expiring stale ones |
| DELETE | `/v1/billing/cancel/{order_id}` | jwt | Cancel a pending order |
| POST | `/v1/billing/submit-proof/{order_id}` | jwt | Submit a crypto TXID for verification |
| POST | `/v1/billing/submit-qris-proof/{order_id}` | jwt | Declare a QRIS transfer, optional note |
| POST | `/v1/billing/admin/confirm-payment/{order_id}` | admin token | Approve an order and credit quota |
| GET | `/v1/billing/qris-config` | — | QRIS image path + merchant label |
| GET | `/v1/billing/exchange-rate` | — | Current IDR/USD rate |
| GET | `/v1/billing/contact` | — | Public support contact |

## Profile

| Method | Path | Auth | Purpose |
|---|---|---|---|
| GET | `/profile/me` | jwt | Current account and quota |
| POST | `/profile/request-otp` | jwt | OTP for a sensitive change |
| PUT | `/profile/update-email` | jwt | Change email (OTP protected) |
| PUT | `/profile/update-phone` | jwt | Change phone number |
| PUT | `/profile/update-password` | jwt | Rotate the password |
| PATCH | `/profile/preferences` | jwt | Language, currency, alert threshold, webhook |
| GET | `/profile/sessions` | jwt | Active sessions |
| DELETE | `/profile/sessions/{session_id}` | jwt | Revoke a session |
| POST | `/profile/test-webhook` | jwt | Send a test event to the configured webhook |

## Integrations

| Method | Path | Auth | Purpose |
|---|---|---|---|
| POST | `/api/v1/telegram/webhook/{bot_token}` | bot token | Telegram update receiver |

All metered endpoints return `401` for a missing/invalid key and a quota error when the account is
exhausted; failures never consume a unit of quota.
