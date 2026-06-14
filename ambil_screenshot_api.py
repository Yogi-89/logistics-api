"""
=============================================================================
ambil_screenshot_api.py — Pengujian Otomatis Logistics API (EAS Semester 8)
=============================================================================
Metode   : requests (HTTP test endpoint) + Playwright (screenshot Swagger & Frontend)
Output   : bukti_pengujian/LAPORAN_PENGUJIAN.txt + 6 screenshot PNG + 11 JSON/response files
Target   : FastAPI Logistics Rate & Tracking API
Author   : Yogi Prasetyo / 22081010297
=============================================================================
"""

import os, sys, time, datetime, json, subprocess
from pathlib import Path

# ---------------------------------------------------------------------------
# 0. KONFIGURASI PATH & FOLDER OUTPUT
# ---------------------------------------------------------------------------
BASE_DIR = Path(__file__).resolve().parent
SCREENSHOT_DIR = BASE_DIR / "bukti_pengujian"
SCREENSHOT_DIR.mkdir(parents=True, exist_ok=True)

LOG_FILE = SCREENSHOT_DIR / "LAPORAN_PENGUJIAN.txt"
LOG_LINES = []

BASE_URL = "http://localhost:8000"

def log(msg: str):
    ts = datetime.datetime.now().strftime("%H:%M:%S")
    line = f"[{ts}] {msg}"
    LOG_LINES.append(line)
    print(line)

def save_log():
    with open(LOG_FILE, "w", encoding="utf-8") as f:
        f.write("=" * 72 + "\n")
        f.write("LAPORAN PENGUJIAN OTOMATIS — LOGISTICS API EAS\n")
        f.write(f"Tanggal : {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write(f"NPM     : 22081010297\n")
        f.write(f"Base URL: {BASE_URL}\n")
        f.write(f"Swagger : {BASE_URL}/docs\n")
        f.write("=" * 72 + "\n\n")
        for line in LOG_LINES:
            f.write(line + "\n")
    log(f"\n📄 Laporan disimpan → {LOG_FILE}")

# ---------------------------------------------------------------------------
# 1. PLAYWRIGHT — SCREENSHOT
# ---------------------------------------------------------------------------
from playwright.sync_api import sync_playwright

class BrowserManager:
    def __init__(self):
        self.playwright = None
        self.browser = None
        self.page = None
    
    def start(self):
        self.playwright = sync_playwright().start()
        chromium_path = "/app/data/.cache/ms-playwright/chromium-1223/chrome-linux64/chrome"
        self.browser = self.playwright.chromium.launch(
            headless=True,
            executable_path=chromium_path,
            args=["--no-sandbox", "--disable-dev-shm-usage"]
        )
        self.page = self.browser.new_page(viewport={"width": 1920, "height": 1080})
        return self.page
    
    def screenshot(self, nama_file: str, label: str):
        path = SCREENSHOT_DIR / nama_file
        self.page.screenshot(path=str(path), full_page=False)
        log(f"   📸 {label} → {nama_file}")
    
    def stop(self):
        if self.browser:
            self.browser.close()
        if self.playwright:
            self.playwright.stop()

# ---------------------------------------------------------------------------
# 2. HTTP TESTING — REQUESTS
# ---------------------------------------------------------------------------
import requests

session = requests.Session()
TEST_USERNAME = "test_screenshot"
TEST_PASSWORD = "password123"
access_token = None
api_key = None

def api_get(path: str, use_auth: bool = True):
    headers = {}
    if use_auth and access_token:
        headers["Authorization"] = f"Bearer {access_token}"
    if api_key:
        headers["X-API-Key"] = api_key
    return session.get(f"{BASE_URL}{path}", headers=headers)

def api_post(path: str, data: dict, use_auth: bool = True):
    headers = {}
    if use_auth and access_token:
        headers["Authorization"] = f"Bearer {access_token}"
    if api_key:
        headers["X-API-Key"] = api_key
    return session.post(f"{BASE_URL}{path}", json=data, headers=headers)

def save_json_response(nama_file: str, response, label: str = ""):
    path = SCREENSHOT_DIR / nama_file
    with open(path, "w", encoding="utf-8") as f:
        try:
            body = response.json()
        except:
            body = response.text[:500]
        json.dump({
            "status_code": response.status_code,
            "url": response.url,
            "body": body
        }, f, indent=2, ensure_ascii=False)
    log(f"   💾 {label or nama_file} (status={response.status_code})")

# ---------------------------------------------------------------------------
# 3. SERVER MANAGEMENT
# ---------------------------------------------------------------------------

server_process = None

def start_server():
    log("🚀 Memulai server FastAPI...")
    global server_process
    server_process = subprocess.Popen(
        ["python", "-m", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"],
        cwd=str(BASE_DIR),
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    for i in range(20):
        try:
            r = requests.get(f"{BASE_URL}/api/", timeout=2)
            if r.status_code == 200:
                log(f"✅ Server siap! → {r.json()['message']}")
                return True
        except:
            pass
        time.sleep(1)
    log("❌ Server gagal start setelah 20 detik")
    return False

def stop_server():
    global server_process
    if server_process:
        server_process.terminate()
        server_process.wait(timeout=5)
        log("🛑 Server dihentikan")
    os.system("fuser -k 8000/tcp 2>/dev/null")

# ---------------------------------------------------------------------------
# 4. TEST CASES
# ---------------------------------------------------------------------------

def test_s01_swagger(bm: BrowserManager):
    """Screenshot Swagger UI /docs"""
    log("=" * 60)
    log("[TEST S01] SCREENSHOT SWAGGER UI — /docs")
    log("=" * 60)
    
    page = bm.page
    page.goto(f"{BASE_URL}/docs", wait_until="networkidle")
    time.sleep(2)
    bm.screenshot("S01_Swagger_UI.png", "Swagger UI — Semua Endpoint")
    
    # Scroll ke bawah
    page.evaluate("window.scrollTo(0, 600)")
    time.sleep(1)
    bm.screenshot("S02_Swagger_UI_Scroll.png", "Swagger UI — Endpoint Lanjutan")
    log("   ✅ Swagger UI ter-capture\n")

def test_s02_redoc(bm: BrowserManager):
    """Screenshot ReDoc"""
    log("=" * 60)
    log("[TEST S02] SCREENSHOT REDOC — /redoc")
    log("=" * 60)
    
    page = bm.page
    page.goto(f"{BASE_URL}/redoc", wait_until="networkidle")
    time.sleep(2)
    bm.screenshot("S03_ReDoc.png", "ReDoc — Dokumentasi Alternatif")
    log("   ✅ ReDoc ter-capture\n")

def test_s03_frontend_index(bm: BrowserManager):
    """Screenshot landing page"""
    log("=" * 60)
    log("[TEST S03] SCREENSHOT FRONTEND — Landing Page (/)")
    log("=" * 60)
    
    page = bm.page
    page.goto(f"{BASE_URL}/", wait_until="networkidle")
    time.sleep(2)
    bm.screenshot("S04_Frontend_Index.png", "Frontend — Landing Page")
    log("   ✅ Landing page ter-capture\n")

def test_s04_frontend_dashboard(bm: BrowserManager):
    """Screenshot dashboard"""
    log("=" * 60)
    log("[TEST S04] SCREENSHOT FRONTEND — Dashboard (/dashboard)")
    log("=" * 60)
    
    page = bm.page
    page.goto(f"{BASE_URL}/dashboard", wait_until="networkidle")
    time.sleep(2)
    bm.screenshot("S05_Frontend_Dashboard.png", "Frontend — Dashboard")
    
    # Scroll dashboard
    page.evaluate("window.scrollTo(0, 500)")
    time.sleep(1)
    bm.screenshot("S06_Frontend_Dashboard_Scroll.png", "Frontend — Dashboard (Scroll)")
    log("   ✅ Dashboard ter-capture\n")

def test_a01_register():
    """Register user"""
    log("=" * 60)
    log("[TEST A01] REGISTER USER")
    log("=" * 60)
    
    payload = {
        "username": TEST_USERNAME,
        "email": f"{TEST_USERNAME}@test.com",
        "password": TEST_PASSWORD,
        "full_name": "Test Screenshot User"
    }
    
    r = api_post("/auth/register", payload, use_auth=False)
    save_json_response("R01_Register.json", r)
    
    if r.status_code in [200, 201]:
        log(f"   ✅ Register berhasil: {r.json().get('username', '?')}")
    elif r.status_code == 409:
        log(f"   ⚠️  User sudah ada (409)")
    else:
        log(f"   ⚠️  status={r.status_code}")

def test_a02_login():
    """Login"""
    global access_token
    log("=" * 60)
    log("[TEST A02] LOGIN")
    log("=" * 60)
    
    payload = {"username": TEST_USERNAME, "password": TEST_PASSWORD}
    r = api_post("/auth/login", payload, use_auth=False)
    save_json_response("R02_Login.json", r)
    
    if r.status_code == 200:
        data = r.json()
        access_token = data.get("access_token")
        log(f"   ✅ Login OK! Token: {access_token[:20] if access_token else 'N/A'}...")
    else:
        log(f"   ⚠️  status={r.status_code}")

def test_a03_otp():
    """Verify OTP"""
    log("=" * 60)
    log("[TEST A03] DEBUG OTP & VERIFY")
    log("=" * 60)
    
    if not access_token:
        log("   ⚠️  Skip — tidak ada token")
        return
    
    r = api_get(f"/auth/debug/otp/{TEST_USERNAME}")
    save_json_response("R03_Debug_OTP.json", r)
    
    if r.status_code == 200:
        code = r.json().get("code")
        log(f"   ✅ OTP code: {code}")
        
        vr = api_post("/auth/verify-code", {"username": TEST_USERNAME, "code": str(code)})
        save_json_response("R04_Verify_OTP.json", vr)
        log(f"   {'✅' if vr.status_code == 200 else '⚠️'} Verify: {vr.status_code}")
    else:
        log(f"   ⚠️  Debug OTP: {r.status_code} (mungkin sudah verified)")

def test_a04_apikey():
    """Generate API key"""
    global api_key
    log("=" * 60)
    log("[TEST A04] GENERATE API KEY")
    log("=" * 60)
    
    if not access_token:
        log("   ⚠️  Skip — tidak ada token")
        return
    
    r = api_post("/apikey/generate", {"name": "Key_Screenshot_Test"})
    save_json_response("R05_Generate_APIKey.json", r)
    
    if r.status_code in [200, 201]:
        data = r.json()
        api_key = data.get("key") or data.get("api_key")
        log(f"   ✅ API Key: {api_key[:16] if api_key else 'N/A'}...")

def test_a05_couriers():
    """List couriers"""
    log("=" * 60)
    log("[TEST A05] LIST COURIERS")
    log("=" * 60)
    
    r = api_get("/logistics/couriers")
    save_json_response("R06_Couriers.json", r)
    if r.status_code == 200:
        log(f"   ✅ {len(r.json())} kurir")

def test_a06_cities():
    """List cities"""
    log("=" * 60)
    log("[TEST A06] LIST CITIES")
    log("=" * 60)
    
    r = api_get("/logistics/cities")
    save_json_response("R07_Cities.json", r)
    if r.status_code == 200:
        log(f"   ✅ {len(r.json())} kota")

def test_a07_cost():
    """Cost recommendation"""
    log("=" * 60)
    log("[TEST A07] COST RECOMMENDATION")
    log("=" * 60)
    
    r = api_post("/logistics/cost/recommend", {"origin_city_id": "1", "destination_city_id": "2", "weight": 1000})
    save_json_response("R08_Cost_Recommend.json", r)
    if r.status_code == 200:
        log(f"   ✅ {len(r.json())} rekomendasi")

def test_a08_tracking():
    """Tracking"""
    log("=" * 60)
    log("[TEST A08] TRACKING")
    log("=" * 60)
    
    r = api_get("/logistics/tracking/TEST-AWB-001")
    save_json_response("R09_Tracking.json", r)
    log(f"   ✅ status={r.status_code}")

def test_a09_profile():
    """Profile"""
    log("=" * 60)
    log("[TEST A09] PROFILE /me")
    log("=" * 60)
    
    if not access_token:
        log("   ⚠️  Skip — tidak ada token")
        return
    
    r = api_get("/profile/me")
    save_json_response("R10_Profile.json", r)
    if r.status_code == 200:
        log(f"   ✅ {r.json().get('username')} / {r.json().get('email')}")

def test_a10_exchange_rate():
    """Exchange rate (public endpoint)"""
    log("=" * 60)
    log("[TEST A10] EXCHANGE RATE")
    log("=" * 60)
    
    r = api_get("/billing/exchange-rate")
    save_json_response("R11_ExchangeRate.json", r)
    if r.status_code == 200:
        log(f"   ✅ Rate: {r.json()}")

def test_a11_pytest():
    """Run pytest suite"""
    log("=" * 60)
    log("[TEST A11] PYTEST SUITE")
    log("=" * 60)
    
    try:
        result = subprocess.run(
            ["python", "-m", "pytest", "tests/", "-v", "--tb=short"],
            cwd=str(BASE_DIR),
            capture_output=True,
            text=True,
            timeout=120
        )
        
        out_path = SCREENSHOT_DIR / "R12_Pytest_Output.txt"
        with open(out_path, "w", encoding="utf-8") as f:
            f.write(result.stdout)
            f.write("\n\n=== STDERR ===\n")
            f.write(result.stderr)
        
        for line in result.stdout.splitlines():
            if any(w in line.lower() for w in ["passed", "failed", "error"]):
                log(f"   📊 {line.strip()}")
        log(f"   📄 Full output → R12_Pytest_Output.txt")
    except subprocess.TimeoutExpired:
        log("   ❌ Timeout (>120s)")
    except Exception as e:
        log(f"   ❌ Error: {e}")

# ---------------------------------------------------------------------------
# 5. MAIN EXECUTION
# ---------------------------------------------------------------------------

def main():
    global server_process
    server_process = None
    
    log("=" * 72)
    log("PENGUJIAN OTOMATIS — LOGISTICS API (EAS Semester 8)")
    log(f"NPM: 22081010297 | {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    log("=" * 72)
    log("")
    
    # Step 1: Start server
    if not start_server():
        log("❌ Server gagal start. Exit.")
        save_log()
        return
    
    bm = BrowserManager()
    try:
        # Phase 1: Screenshots (Playwright)
        log("\n📸 PHASE 1: SCREENSHOT (Playwright headless)\n")
        bm.start()
        
        test_s01_swagger(bm)            # S01, S02
        test_s02_redoc(bm)              # S03
        test_s03_frontend_index(bm)     # S04
        test_s04_frontend_dashboard(bm) # S05, S06
        
        # Phase 2: API endpoint testing
        log("\n🌐 PHASE 2: API ENDPOINT TESTING (requests)\n")
        
        test_a01_register()       # R01
        test_a02_login()          # R02
        test_a03_otp()            # R03, R04
        test_a04_apikey()         # R05
        test_a05_couriers()       # R06
        test_a06_cities()         # R07
        test_a07_cost()           # R08
        test_a08_tracking()       # R09
        test_a09_profile()        # R10
        test_a10_exchange_rate()  # R11
        
        # Phase 3: Pytest
        log("\n🧪 PHASE 3: PYTEST\n")
        test_a11_pytest()         # R12
        
    except Exception as e:
        log(f"\n❌ FATAL ERROR: {e}")
        import traceback
        log(traceback.format_exc())
    finally:
        bm.stop()
        stop_server()
    
    log("\n" + "=" * 72)
    log("✅ PENGUJIAN SELESAI")
    log("=" * 72)
    save_log()
    
    log("\n📦 FILE OUTPUT:")
    for f in sorted(SCREENSHOT_DIR.glob("*")):
        size_kb = f.stat().st_size / 1024
        log(f"   {f.name} ({size_kb:.1f} KB)")

if __name__ == "__main__":
    main()
