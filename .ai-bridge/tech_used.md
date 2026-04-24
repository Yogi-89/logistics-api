# 🛠️ TECH USED — ShipStream Logistics API
> Stack teknologi yang digunakan dalam project ini

---

## Backend

| Teknologi | Versi / Detail | Fungsi |
|-----------|---------------|--------|
| **Python** | 3.x | Bahasa utama backend |
| **FastAPI** | Latest | Web framework async, auto-docs Swagger |
| **Uvicorn** | Latest | ASGI server untuk menjalankan FastAPI |
| **SQLAlchemy** | Latest | ORM untuk database access |
| **Pydantic v2** | Latest | Validasi data, schema request/response |
| **pydantic-settings** | Latest | Load konfigurasi dari .env |
| **psycopg2-binary** | Latest | Driver PostgreSQL |
| **passlib[argon2]** | Latest | Hashing password (algoritma Argon2) |
| **python-jose[cryptography]** | Latest | JWT token (create + verify) |
| **python-dotenv** | Latest | Load .env ke environment |
| **python-multipart** | Latest | Support form data upload |
| **email-validator** | Latest | Validasi format email di Pydantic |
| **fpdf2** | Latest | Generate PDF (Shipping Label) |
| **httpx** | Latest | Async HTTP client (Telegram, CoinGecko, BaseScan) |
| **resend** | Latest | Email OTP via Resend.com API |
| **pytest** | Latest | Framework testing Python |
| **flake8** | Latest | Linter untuk konsistensi gaya kode |

---

## Database

| Teknologi | Detail |
|-----------|--------|
| **PostgreSQL** | Primary database (`localhost:5432/logistics_api`) |
| **SQLite** | `logistics.db` ada di root, kemungkinan dev fallback awal |

---

## External APIs & Services

| Service | Digunakan Untuk | Config Key |
|---------|----------------|------------|
| **Resend.com** | Kirim OTP via email | `RESEND_API_KEY` |
| **CoinGecko API** | Kurs IDR/USD real-time | Public (no key) |
| **BaseScan / Etherscan V2** | Verifikasi transaksi crypto Base chain | `ETHERSCAN_API_KEY` |
| **PlasmasScan** | Verifikasi transaksi crypto Plasma chain | Public |
| **Telegram Bot API** | Bot notifikasi + webhook | Token dari user |
| **Cloudflare Turnstile** | CAPTCHA (dibypass, kode ada tapi dikomentari) | — |

---

## Blockchain / Crypto

| Item | Detail |
|------|--------|
| **Chain 1** | Base Mainnet (Ethereum L2) — USDC |
| **Chain 2** | Plasma — USDT |
| **Token USDC** | Contract: `0x833589fcd6edb6e08f4c7c32d4f71b54bda02913` (Base) |
| **Token USDT** | Contract: `0xc2132D05D31c914a87C6611C10748AEb04B58e8F` (Plasma) |
| **Wallet** | `0x47443cef765320f815c651fab1196c7ad55789a5` |
| **Verifikasi** | EVM `eth_getTransactionReceipt` + Transfer event log parsing |

---

## Frontend

| Teknologi | Detail |
|-----------|--------|
| **HTML5** | Struktur halaman |
| **CSS3** | Custom properties (CSS vars), Grid, Flexbox, glassmorphism |
| **Vanilla JavaScript** | ES6+, async/await, fetch API — tanpa framework |
| **i18n Custom** | Sistem translasi EN/ID buatan sendiri (objek JS) |
| **Fetch API** | Komunikasi ke backend |

---

## Tooling & Dev

| Tool | Fungsi |
|------|--------|
| **Postman** | Testing API (collection ada di `postman/collection.json`) |
| **Git** | Version control (`.git` folder ada) |
| **pg_dump** | Backup database (file `.sql` di folder `backups/`) |

---

## Security Implementation

| Mekanisme | Detail |
|-----------|--------|
| **Argon2** | Hashing password (via passlib) |
| **JWT HS256** | Auth token, expire 1440 menit (24 jam) |
| **JTI (JWT ID)** | Unik per session, tersimpan di DB untuk revocation |
| **OTP** | 6 digit, expire per channel, rate-limited (3x/24jam + backoff) |
| **IP Whitelist** | Opsional per API Key |
| **API Key** | 32 char hex, header `X-API-Key` |
| **Quota System** | Global pool per user, per-key sub-limit opsional |

---

## Environment Variables (.env)

```env
DATABASE_URL          # PostgreSQL connection string
SECRET_KEY            # JWT signing key
ALGORITHM             # JWT algorithm (HS256)
ACCESS_TOKEN_EXPIRE_MINUTES  # Token lifetime (1440 = 24h)
RESEND_API_KEY        # Resend.com email API
RESEND_FROM_EMAIL     # Sender email
ETHERSCAN_API_KEY     # BaseScan/Etherscan V2
MY_CRYPTO_WALLET      # Alamat wallet penerima
USDC_CONTRACT_BASE    # Contract USDC di Base chain
USDT_CONTRACT_PLASMA  # Contract USDT di Plasma
USD_PRICE_IDR         # Fallback hardcode kurs (17000)
DEBUG_MODE            # Aktifkan debug endpoints (True/False)
ADMIN_NAME            # Nama admin untuk support display
ADMIN_EMAIL           # Email admin
ADMIN_WHATSAPP        # Nomor WhatsApp admin
```
