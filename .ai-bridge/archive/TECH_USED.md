# ShipStream — Tech Stack & Dependencies

## Backend
- Python 3.13
- FastAPI (Web Framework)
- SQLAlchemy (ORM)
- psycopg2-binary (PostgreSQL Driver)
- **Pydantic v2** (Data Validation)
- **python-dotenv** (Env Management)
- **httpx** (Async HTTP Client)
- **python-jose** (JWT Tokens)
- **passlib[argon2]** (Security/Hashing)
- **argon2-cffi** (Modern Password Hashing)
- **email-validator** (Email format validation)
- **python-multipart** (Form Data)
- **resend** (Email Marketing & Transactional API)

## Routers & modules
- `billing.py`: Topup, Verification, Exchange Rate
- `profile.py`: Profile, Sessions, Preferences
- `telegram_bot.py`: Webhook & Command handler

## Database
- PostgreSQL (Lokal via Laragon/Native)
- Database name: `logistics_api`

## Frontend
- Vanilla HTML/CSS/JS
- CSS: Custom Modern Glass-morphism
- Fonts: Inter, Roboto, Outfit

## External APIs & Integrations
- **BaseScan API**: Crypto Transaction Verification (Base Network)
- **CoinGecko API**: Real-time IDR/USD Exchange Rate
- **Telegram Bot API**: Notifications & Chat Commands
- **Resend Messaging**: Transactional OTP & Verification Delivery
- **USDC/USDT Contracts**: Multi-chain verification

## Tools
- Postman (Testing)
- Uvicorn (ASGI Server)
- OS: Windows
