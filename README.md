# ShipStream — Logistics API Platform

**One integration for shipping rates, courier data and parcel tracking — metered per API key.**

ShipStream is a production-shaped logistics API platform: developers sign up, generate an API key,
call a single set of endpoints for rates/tracking/labels, and pay for usage with prepaid quota
(QRIS or USDC on Base). It ships with a self-service dashboard, automated on-chain payment
verification and a documented REST surface.

[![Live](https://img.shields.io/badge/live-apilogistik.my.id-4f46e5?style=flat-square)](https://apilogistik.my.id)
[![API Docs](https://img.shields.io/badge/docs-Swagger-85ea2d?style=flat-square)](https://apilogistik.my.id/docs)
[![Python](https://img.shields.io/badge/python-3.12-3776ab?style=flat-square&logo=python&logoColor=white)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.137-009688?style=flat-square&logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com/)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-17-4169e1?style=flat-square&logo=postgresql&logoColor=white)](https://www.postgresql.org/)
[![License](https://img.shields.io/badge/license-MIT-black?style=flat-square)](LICENSE)

---

## Why it exists

Adding shipping to an application normally means integrating several courier APIs, each with its own
auth scheme, error format and pricing. ShipStream exposes one contract instead:

```
your app ──► ShipStream API ──► courier / rate providers
                  │
                  └─ API key, quota, rate limits, audit trail
```

Every key belongs to a user account with a shared prepaid quota pool, so a team can issue several
keys without juggling separate subscriptions.

## Features

**Developer API**
- Shipping-cost quotes across couriers, plus a cheapest-courier recommendation endpoint
- City / subdistrict directory and courier catalogue
- Shipment creation with generated AWB (waybill)
- Real-time tracking history and status updates
- Printable shipping label (PDF)
- Per-key quota endpoint and OpenAPI/Swagger schema

**Accounts & access**
- Email + OTP registration, JWT sessions, argon2 password hashing
- Multiple API keys per account with revoke and per-key settings
- Shared prepaid quota pool, request counting, IP allow-listing
- Rate limiting with exponential backoff on repeated failures

**Billing**
- Prepaid top-up packages, order lifecycle (`pending → awaiting_verification → success`)
- **Static QRIS**: payer scans the merchant QR, confirms, admin approves with a shared token
- **USDC on Base**: automatic verification against the chain via Etherscan v2 + RPC fallback

**Operations**
- Alembic migrations executed on boot, idempotent reference-data seeding
- Health endpoint, structured startup logs, GitHub Actions lint + tests
- Stateless app tier (safe to scale) against a managed PostgreSQL database

## Architecture

```mermaid
flowchart LR
    subgraph Client
        B[Browser dashboard<br/>vanilla HTML/CSS/JS]
        D[Developer app]
    end

    subgraph Render
        A[FastAPI app<br/>uvicorn]
        L[(Rate limiter)]
    end

    subgraph Managed
        P[(PostgreSQL<br/>Supabase)]
        R[Resend<br/>transactional email]
        E[Etherscan v2 + Base RPC]
        Q[Static QRIS<br/>merchant code]
    end

    B -->|JWT| A
    D -->|X-API-Key| A
    A --- L
    A --> P
    A --> R
    A --> E
    A -.->|shows QR| Q
```

Request flow for a metered API call:

1. `X-API-Key` is resolved to its owner; inactive/revoked keys are rejected.
2. The shared quota pool is checked and the request counter incremented.
3. The courier/rate provider is called (with a local dataset fallback when no provider key is set).
4. The response is returned and the call is recorded for analytics.

See [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) for the data model, module map and payment state machines.

## Tech stack

| Layer | Choice |
|---|---|
| API | FastAPI, Pydantic v2, Uvicorn |
| Data | PostgreSQL 17, SQLAlchemy 2, Alembic |
| Auth | JWT (python-jose), argon2 (passlib), OTP via Resend |
| Payments | Etherscan v2 / Base RPC, static QRIS + admin approval |
| Frontend | Server-served vanilla HTML/CSS/JS dashboard (no build step) |
| Infra | Render (Singapore), Supabase Postgres, Cloudflare DNS, GitHub Actions |

## Quick start

```bash
git clone https://github.com/Yogi-89/logistics-api.git
cd logistics-api

python -m venv .venv
# Windows: .venv\Scripts\activate
source .venv/bin/activate
pip install -r requirements.txt

cp .env.example .env          # then fill DATABASE_URL + SECRET_KEY
alembic upgrade head          # create the schema
python -m app.utils.seed_data # optional reference data (cities, couriers)
python start.py               # http://localhost:8000
```

Open <http://localhost:8000> for the dashboard, `/docs` for Swagger, `/redoc` for ReDoc.

Minimal environment for a first run:

```env
DATABASE_URL=postgresql+psycopg2://postgres:postgres@localhost:5432/logistics_api
SECRET_KEY=dev-only-change-me
DEBUG_MODE=True
```

Everything else (email, crypto, QRIS, courier provider) is optional and degrades gracefully.

## API at a glance

Authentication is a header on every metered call:

```bash
curl https://apilogistik.my.id/v1/cost \
  -H "X-API-Key: YOUR_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"origin": 1, "destination": 2, "weight": 1000, "courier": "jne"}'
```

| Group | Endpoints |
|---|---|
| Auth | `POST /auth/register`, `/auth/verify-code`, `/auth/login`, `/auth/resend-registration-code` |
| API keys | `POST /apikey/generate`, `GET /apikey/list`, `POST /apikey/{id}/settings`, `POST /apikey/revoke/{id}` |
| Logistics | `POST /v1/cost`, `/v1/cost/recommend`, `/v1/shipments`, `GET /v1/cities`, `/v1/couriers`, `/v1/cities/{id}/subdistricts`, `/v1/tracking/{awb}`, `/v1/label/{awb}` |
| Account | `GET /profile/me`, `POST /profile/request-otp`, `/profile/update-email`, `GET /v1/quota` |
| Billing | `POST /v1/billing/topup`, `GET /v1/billing/history`, `POST /v1/billing/submit-proof/{order}`, `POST /v1/billing/submit-qris-proof/{order}`, `POST /v1/billing/admin/confirm-payment/{order}` |

Full reference: [docs/API_GUIDE.md](docs/API_GUIDE.md) and [docs/ENDPOINTS.md](docs/ENDPOINTS.md).

## Payments

**QRIS (static).** The dashboard renders the merchant QR, the payer transfers the exact amount and
confirms, and an admin approves the order with `X-Admin-Token`. No gateway, no per-transaction fee.

**USDC on Base.** The transaction hash is verified against the chain: the receipt status, the transfer
log to the merchant wallet, the token contract and the expected amount (with tolerance) must all
match. Unknown hashes are rejected instead of being left pending.

Environment variables and the admin confirmation flow are documented in [docs/DEPLOYMENT.md](docs/DEPLOYMENT.md).

## Project structure

```
app/
  main.py              FastAPI app, routers, static dashboard mount
  database.py          engine/session factory
  models/              SQLAlchemy models
  routers/             auth, apikey, logistics, billing, profile, telegram_bot
  schemas/             Pydantic request/response models
  utils/               security, OTP, crypto validator, rate limiting, seeding
alembic/               migration environment and versions
frontend/              dashboard, landing page, assets (no build step)
scripts/               operational helpers (seed, verify, audit)
tests/                 pytest suite
docs/                  abstract, architecture, API guide, deployment runbook
start.py               boot: migrations → seed → uvicorn
render.yaml            infrastructure-as-code for the Render service
```

## Testing

```bash
pytest tests/ -v
flake8 app/ --config=.flake8
```

CI runs both on every push to `develop`/`main`/`staging`.

## Documentation

| Document | Contents |
|---|---|
| [docs/ABSTRACT.md](docs/ABSTRACT.md) | Project abstract / executive summary (EN + ID) |
| [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) | Module map, data model, request and payment flows |
| [docs/API_GUIDE.md](docs/API_GUIDE.md) | Step-by-step API usage with examples |
| [docs/ENDPOINTS.md](docs/ENDPOINTS.md) | Endpoint index |
| [docs/DEPLOYMENT.md](docs/DEPLOYMENT.md) | Render + Supabase + Resend + Cloudflare runbook |

## Roadmap

- [ ] Webhook subscriptions for tracking status changes
- [ ] Redis-backed quota counters for horizontal scaling
- [ ] Usage analytics charts in the dashboard
- [ ] Sandbox keys with synthetic tracking data
- [ ] OpenAPI-generated SDKs (TypeScript, Python)

## License

Released under the [MIT License](LICENSE).

## Author

**Yogi Prasetyo** — [github.com/Yogi-89](https://github.com/Yogi-89)
