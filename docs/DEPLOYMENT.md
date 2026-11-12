# Deployment runbook

Reference topology: **Render** (Singapore) for the app, **Supabase** for PostgreSQL, **Cloudflare** for
DNS, **Resend** for transactional email. Every step below is reproducible from this repository.

```
User ──► Cloudflare DNS ──► Render web service ──► Supabase Postgres
                                     │
                                     ├──► Resend (OTP email)
                                     └──► Etherscan v2 / Base RPC (crypto)
```

## 1. Database (Supabase)

1. Create a project and pick the region closest to your Render region.
2. Copy the connection string from **Project Settings → Database → Connection string → URI**.
   Use the **Session pooler** variant: the direct connection is IPv6-only, and the pooler works from
   IPv4-only hosts.
3. Keep the `postgres.<project-ref>` user name intact; it is required by the pooler.
4. Force the psycopg2 dialect, because SQLAlchemy 2.1 otherwise looks for `psycopg` (v3):

   ```
   postgresql+psycopg2://postgres.<ref>:<password>@aws-0-<region>.pooler.supabase.com:5432/postgres
   ```

5. URL-encode special characters in the password (`@` → `%40`, `:` → `%3A`, `#` → `%23`).

Schema creation is automatic: `start.py` runs `alembic upgrade head` and seeds reference data when the
tables are empty. No manual SQL is required.

### Row Level Security

The app connects as the table owner, which bypasses RLS. Enabling RLS therefore hardens the public API
surface without affecting the application. If Supabase Advisor reports `RLS Enabled No Policy`, add an
explicit deny policy per table:

```sql
alter table public.users enable row level security;
create policy deny_all_public on public.users
  as restrictive for all to anon, authenticated
  using (false) with check (false);
```

## 2. Application (Render)

Create a **Web Service** from the repository:

| Setting | Value |
|---|---|
| Runtime | Python 3.12 |
| Build command | `pip install -r requirements.txt` |
| Start command | `python start.py` |
| Health check path | `/api/` |
| Region | Singapore (or nearest to your database) |

`render.yaml` describes the same service for Blueprint-based deploys. Region cannot be changed after
creation — pick it correctly the first time.

### Environment variables

| Variable | Required | Notes |
|---|---|---|
| `DATABASE_URL` | yes | Session-pooler URI with `postgresql+psycopg2://` |
| `SECRET_KEY` | yes | 32+ random bytes; `render.yaml` can generate it |
| `ALGORITHM` | no | Default `HS256` |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | no | Default `1440` |
| `ALLOWED_ORIGINS` | recommended | e.g. `https://apilogistik.my.id,https://www.apilogistik.my.id` |
| `DEBUG_MODE` | yes | `False` in production (debug OTP endpoint) |
| `RESEND_API_KEY` / `RESEND_FROM_EMAIL` | for email | Sending-only key is enough |
| `RAJA_ONGKIR_API_KEY` | optional | Komerce "Shipping Cost" key |
| `ETHERSCAN_API_KEY` | for crypto | Etherscan v2 key covers Base via `chainid=8453` |
| `MY_CRYPTO_WALLET` | for crypto | **Set this** — otherwise the hard-coded default receives funds |
| `QRIS_IMAGE_URL` / `QRIS_MERCHANT_NAME` | for QRIS | Path or absolute URL to the merchant QR |
| `ADMIN_CONFIRM_TOKEN` | for QRIS | Shared secret required by the admin confirmation endpoint |
| `PYTHON_VERSION` | recommended | `3.12.7` |
| `REDIS_URL` | no | `memory://` unless running multiple instances |

## 3. Custom domain (Cloudflare)

1. Add the site to Cloudflare (free plan) and copy the two assigned nameservers into your registrar.
2. Create the records — **proxy must be off (grey cloud)** so Render can issue its certificate:

   | Type | Name | Content |
   |---|---|---|
   | A | `@` | `216.24.57.1` |
   | CNAME | `www` | `<service-name>.onrender.com` |

3. In Render: **Settings → Custom Domains → Add**, then wait for `verified`.
4. Switch `ALLOWED_ORIGINS` to the custom domain and redeploy.

DNS caching is the most common false alarm: after moving nameservers, an ISP/router may still answer
`SERVFAIL`/`NXDOMAIN` from a stale negative cache for up to a few hours. Confirm with a public resolver
(`1.1.1.1`, `8.8.8.8`) before debugging the application.

## 4. Email (Resend)

1. Add the domain in Resend and let it configure DNS (Cloudflare integration) or copy the SPF/DKIM
   records manually.
2. Wait for the domain status to become **Verified**.
3. Create an API key with **Sending access**.
4. Set `RESEND_API_KEY` and `RESEND_FROM_EMAIL` (e.g. `noreply@apilogistik.my.id`), then redeploy.
5. Test with a real registration; without a verified domain, sending is limited to your own address.

## 5. QRIS merchant code

The QR must be a real EMVCo QRIS payload (starts with `000201`, ends with a CRC tag `63`). A GoPay
"pay" QR or an app-internal link will be rejected by other banking apps.

Validate a candidate image before deploying it:

```bash
python scripts/decode_qris.py frontend/assets/img/qrcodes/<file>
# expects: CRC VALID, type: static (nominal diisi pembayar)
```

Then point `QRIS_IMAGE_URL` at the file (or an absolute URL) and redeploy. Static mode (tag `01 = 11`)
lets the payer type the amount, which is what the checkout screen assumes.

## 6. Confirming a QRIS payment

When the transfer arrives, approve the order with the shared secret:

```bash
curl -X POST "https://apilogistik.my.id/v1/billing/admin/confirm-payment/BILL-XXXXXXXX" \
  -H "X-Admin-Token: $ADMIN_CONFIRM_TOKEN"
```

The response includes the user's new global quota limit. The same action is available from the
dashboard's transaction list.

## 7. Post-deploy checklist

```bash
curl -s https://<domain>/api/ | jq          # health payload
curl -s https://<domain>/v1/billing/qris-config | jq   # QR image + merchant
curl -s -o /dev/null -w "%{http_code}\n" https://<domain>/docs
```

- [ ] `/api/` returns `{"service": "ShipStream Logistics API", ...}`
- [ ] `/docs` renders Swagger
- [ ] Registration delivers an OTP email (or the debug endpoint returns one when `DEBUG_MODE=true`)
- [ ] QRIS image loads in the top-up modal and scans in a banking app
- [ ] Admin confirmation returns 401 without `X-Admin-Token`
- [ ] `DEBUG_MODE=false` before opening the service to real users

## 8. Troubleshooting

| Symptom | Cause | Fix |
|---|---|---|
| `ModuleNotFoundError: No module named 'psycopg'` | SQLAlchemy 2.1 defaults to psycopg v3 | Use `postgresql+psycopg2://` in `DATABASE_URL` |
| `Port scan timeout reached` | Wrong start command | Use `python start.py` (binds `$PORT`) |
| `tenant/user not found` | Pooler user missing project ref | Username must be `postgres.<project-ref>` |
| `NXDOMAIN` only on one network | Stale negative DNS cache | Wait, flush DNS, or test via `1.1.1.1` |
| OTP email never arrives | Domain not verified in Resend | Verify the domain, check `RESEND_FROM_EMAIL` |
| QRIS rejected by bank apps | Not an EMVCo payload | Validate with `scripts/decode_qris.py`, replace the image |
| Deploy stays `unverified` | Custom domain not added/verified in Render | Add the domain, then trigger verification |
