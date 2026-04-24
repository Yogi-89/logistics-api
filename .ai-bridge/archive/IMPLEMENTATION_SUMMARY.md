# ShipStream � Logistics Rate & Tracking API � Implementation Summary

**Project Status**: ✅ ADVANCED (PHASE 6)  
**Last Updated**: 2026-04-16  
**Backend**: FastAPI (Python)  
**Database**: PostgreSQL 18  
**Frontend**: HTML5 + Vanilla JavaScript

---

## 🎯 Phase 1: Database Setup

### PostgreSQL Configuration
- **Server**: PostgreSQL 18 (port 5432)
- **User**: `postgres`
- **Password**: `postgres`
- **Database**: `logistics_api`

### Database Creation Process
1. Created database `logistics_api` via pgAdmin 4 v9.11
2. Tables auto-created from SQLAlchemy models on first app startup
3. Backed up all databases to: `backups/` folder

### Database Tables
```
✅ users         - Data User, Quota Balance (Limit & Used)
✅ api_keys      - API key management (Centralized tracking)
✅ cities        - Shipping destinations (10 cities seeded)
✅ couriers      - Courier services (5 couriers seeded)
✅ tracking      - Package tracking info (LGS sample)
✅ transactions  - Crypto payment history & status
✅ verification_codes - OTP Storage (Email/SMS)
```

### Seeded Data
```bash
python -m app.utils.seed_data
```
- **Cities**: Surabaya, Jakarta, Bandung, Yogyakarta, Semarang
- **Couriers**: JNE Express, J&T Express, SiCepat
- **Tracking**: 1 sample AWB (LGS-12345678) with history

---

## 🛠️ Phase 2: Backend Issues & Fixes

### Issue 1: Password Hashing Error (FIXED ✅)
**Problem**: `passlib[bcrypt]` incompatible with Python 3.13
```
ValueError: password cannot be longer than 72 bytes
```

**Solution**:
- Replaced `passlib[bcrypt]` with `passlib[argon2]`
- Updated `requirements.txt`:
  ```
  passlib[argon2]  # Changed from bcrypt
  argon2-cffi
  email-validator
  ```
- Updated `app/utils/security.py`:
  ```python
  pwd_context = CryptContext(schemes=["argon2"], deprecated="auto")
  ```

### Issue 2: Database Connection Error (FIXED ✅)
**Problem**: Password authentication failed for user "postgres"
```
FATAL: password authentication failed for user "postgres"
```

**Solution**:
- Reset PostgreSQL password using psql command:
  ```powershell
  $env:PGPASSWORD=''; & "C:\Program Files\PostgreSQL\18\bin\psql.exe" -U postgres -d postgres -c "ALTER USER postgres WITH PASSWORD 'postgres';"
  ```
- Verified connection works with argon2 fix

### Issue 3: API Response 500 Error (FIXED ✅)
**Problem**: Register endpoint returned Internal Server Error
- Root cause: bcrypt compatibility issue (see Issue 1)

**Solution**: Applied argon2 fix from Issue 1

---

## 🌐 Phase 3: Frontend & Backend Integration

### Environment Configuration
**File**: `.env`
```
DATABASE_URL=postgresql://postgres:postgres@localhost:5432/logistics_api
SECRET_KEY=yogi_prasetyo_secret_key_2024_uts
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=1440
```

### Frontend-Backend Communication
**API Base URL**: `http://localhost:8000`

**Key Endpoints**:
- `POST /auth/register` - User registration
- `POST /auth/login` - User login (returns JWT token)
- `POST /apikey/generate` - Create API key
- `GET /apikey/list` - List user's API keys
- `DELETE /apikey/revoke/{id}` - Revoke API key
- `GET /logistics/cities` - List cities
- `GET /logistics/couriers` - List couriers
- `POST /logistics/rate` - Calculate shipping rate
- `GET /logistics/tracking/{awb}` - Track package

---

## 📱 Phase 4: Routing & Static Files Setup

### Main Application Routes
**File**: `app/main.py`

```python
# Frontend Routes
@app.get("/")                    # Homepage (index.html)
@app.get("/dashboard")          # Dashboard (dashboard.html)
@app.get("/index.html")         # Direct HTML access
@app.get("/dashboard.html")     # Direct HTML access

# API Routes (routed via include_router)
@app.include_router(auth.router)        # /auth/* endpoints
@app.include_router(apikey.router)      # /apikey/* endpoints
@app.include_router(logistics.router)   # /logistics/* endpoints

# Static Files
app.mount("/static", StaticFiles(...))  # CSS, JS, assets
```

### CORS Configuration
```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins (dev mode)
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

### Frontend Files Structure
```
frontend/
├── index.html          # Login/Register page
├── dashboard.html      # User dashboard (after login)
└── assets/
    └── style.css       # Global styling
```

---

## 🎨 Phase 5: Dashboard Implementation

### Dashboard Features (Tab System)

#### Tab 1: API Keys Management
- ✅ List user's API keys
- ✅ Generate new API key
- ✅ Revoke (delete) API key
- ✅ Copy key to clipboard
- ✅ Show creation date

**Endpoints Used**:
- `GET /apikey/list` - Fetch all keys for user
- `POST /apikey/generate` - Create new key
- `DELETE /apikey/revoke/{id}` - Delete key

#### Tab 2: Documentation
- ✅ API authentication methods (JWT, API Key)
- ✅ Available endpoints reference table
- ✅ Curl example usage
- ✅ Link to Swagger UI (`/docs`)

**Content**:
- Authentication overview
- Endpoint list with HTTP methods
- Quick usage examples
- Link to live API documentation

#### Tab 3: Settings
- ✅ Account information display
- ✅ Username & email display
- ✅ Logout functionality
- ✅ Danger zone (logout)

**Fields**:
- Username (read-only)
- Email (read-only)
- Logout button

---

## 🔐 Authentication Flow

### Registration Flow
```
1. User fills form (username, email, password)
2. Frontend POST to /auth/register
3. Backend hashes password with argon2
4. User stored in database
5. Success message shown
6. Redirect to login
```

### Login Flow
```
1. User enters username & password
2. Frontend POST to /auth/login (form data)
3. Backend verifies credentials
4. JWT token generated (valid for 24 hours)
5. Token stored in localStorage
6. Redirect to /dashboard
```

### API Access Flow
```
1. Frontend sends Authorization: Bearer {token}
2. Backend validates token via get_current_user()
3. User extracted from token
4. Request processed with user context
5. Response returned
```

---

## 📊 Database Model Relationships

```
User (1) ──────── (Many) APIKey
  │ username           │ key
  │ email              │ label
  │ hashed_password    │ user_id (FK)
  │ is_active          │ created_at
  │
  └──── (Many) Tracking (future enhancement)

City
  │ name
  │ province

Courier
  │ name
  │ code

Tracking
  │ awb
  │ courier_id (FK)
  │ status
  │ history (JSON)
```

---

## 🚀 How to Run

### 1. Start Backend
```powershell
cd "C:\Users\Developer\Documents\Semester 8\pemograman_api\logistics-api"
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### 2. Access in Browser
- **Frontend**: http://127.0.0.1:8000
- **API Docs**: http://127.0.0.1:8000/docs
- **Dashboard**: http://127.0.0.1:8000/dashboard

### 3. Test Credentials
```
Username: yogiuser
Password: yogi123456
Email: yogi@test.com
```

---

## 📦 Requirements Installed

```
fastapi           # Web framework
uvicorn           # ASGI server
sqlalchemy        # ORM
psycopg2-binary   # PostgreSQL driver
pydantic          # Data validation
python-multipart  # Form data handling
passlib[argon2]   # Password hashing (FIXED)
argon2-cffi       # Argon2 implementation
python-jose       # JWT tokens
python-dotenv     # Environment variables
email-validator   # Email validation
```

---

## 🐛 Known Issues Fixed

| Issue | Status | Solution |
|-------|--------|----------|
| api_key 404 error | ✅ FIXED | Added verification check in auth.py |
| Quota column missing | ✅ FIXED | Ran sync_schema.py utility |
| Admin redirect broken | ✅ FIXED | Updated dashboard.html paths |

---

## 📝 File Modifications Summary

### Modified Files
1. **requirements.txt** - Added argon2, email-validator
2. **app/utils/security.py** - Changed bcrypt to argon2
3. **app/main.py** - Added dashboard routing, static files
4. **frontend/index.html** - Fixed login redirect to `/dashboard`
5. **frontend/dashboard.html** - Complete rewrite with 3 tabs system

### New Features Added
- ✅ Argon2 password hashing
- ✅ Dashboard tab system
- ✅ API key management UI
- ✅ Documentation tab
- ✅ Settings tab with account info
- ✅ Proper routing for all frontend pages
- ✅ CORS configuration for frontend-backend communication

---

## ✨ What's Working

- ✅ User registration with email validation
- ✅ User login with JWT authentication
- ✅ Database integration & auto-create tables
- ✅ API key generation & management
- ✅ Frontend dashboard with tabs
- ✅ Static file serving
- ✅ CORS enabled for development
- ✅ Password hashing with argon2
- ✅ Token-based authentication
- ✅ Responsive UI with glass-morphism design

---

## 💎 Phase 6: Global Quota & Financial Integration

### Architecture: Global Prepaid Pool
Transisi dari sistem kuota per-key ke sistem **User-Level Prepaid Pool**.
- **Model**: `User` memiliki `quota_limit` dan `quota_used`.
- **Enforcement**: Middleware `api_key_auth.py` memeriksa saldo global sebelum memproses request.
- **Benefit**: User bisa membuat banyak key tanpa menambah biaya, semua key berbagi saldo yang sama.

### Crypto Payment Verification (Auto)
- **Engine**: `httpx` + **BaseScan API**.
- **Logic**: Backend memverifikasi `tx_hash` secara otomatis untuk memastikan dana (0.29 ETH/USDC) benar-benar masuk ke wallet admin sebelum menambah kuota.

### Database Synchronization
- **Utility**: `app/utils/sync_schema.py`
- **Purpose**: Menambah kolom baru ke tabel PostgreSQL yang sudah ada tanpa perlu menghapus database (migrations).

---

## 📞 Support
**Dibuat Oleh**: Yogi Prasetyo (UTS Pemrograman API)
**Database Sync Command**: `python -m app.utils.sync_schema`

For issues or questions:
1. Check backend logs in terminal
2. Check browser console (F12)
3. Test API directly via Swagger UI (/docs)
4. Verify PostgreSQL connection in pgAdmin

**Database Backup Location**: 
`C:\Users\Developer\Documents\Semester 8\pemograman_api\logistics-api\backups\`
```
