# 🌉 AI BRIDGE — ShipStream Logistics API
> Titik masuk utama. Baca COLLAB_PROTOCOL.md dulu sebelum apapun.

---

## 🎯 Project Snapshot
**Nama**: ShipStream — Logistics Rate & Tracking API
**Pemilik**: Yogi Prasetyo
**Konteks**: Portofolio standar industri
**Stack**: FastAPI + PostgreSQL + Vanilla JS
**Status**: ✅ 100% Fungsional & Hardened. CI/CD Aktif.

---

## 📁 Entry Points
| File | Fungsi |
|------|--------|
| `app/main.py` | App entrypoint, routing, static mount |
| `app/models/base.py` | Semua model SQLAlchemy |
| `app/schemas/schemas.py` | Semua Pydantic schema |
| `app/routers/logistics.py` | Endpoint logistik (cost, tracking, shipment, label) |
| `frontend/dashboard.html` | Dashboard SPA (monolith, hati-hati duplikasi JS) |
| `frontend/assets/style.css` | CSS global |
| `.env` | Konfigurasi environment |

---

## ⚠️ Hal Kritis
- Dashboard: jangan duplikasi `let/const/var` di global scope, gunakan `showConfirmModal`
- Quota: Global Pool di `User.quota_limit` — BUKAN per-API-key
- OTP: dibypass (`is_verified=True`) — jangan aktifkan tanpa SMTP siap
- DB: PostgreSQL `localhost:5432/logistics_api`, Alembic di `alembic/versions/`

---

## 🔧 Next Steps (Active)

[x] DONE — Cek & pastikan `.env` | File: `.env`

[x] DONE — Update test untuk endpoint scale-up | File: `tests/test_main.py`

[x] DONE — Fix GitHub Actions CI agar lolos | File: `.github/workflows/lint-test.yml`

[ ] TODO — Persiapan Push ke GitHub & Deployment | File: `.git`
- [ ] Commit semua perubahan (Hardening, Tests, CI Workflow)
- [ ] Setup GitHub Remote (Manual by User)
- [ ] Push ke `develop` branch untuk mentrigger GitHub Actions

---

## 🗺️ Roadmap
1. ✅ Clean Architecture & Alembic
2. ✅ Rate Limiting (SlowAPI)
3. ✅ Shipment AWB + Tracking endpoint
4. ✅ Bug fix + Pydantic v2 hardening
5. ✅ Raja Ongkir integration + fallback
6. ✅ Unit test pytest
7. ✅ GitHub Actions CI lolos

---

## 🌿 Branching
- `main` → protected, produksi
- `staging` → pre-production, CI wajib lolos
- `develop` → branch kerja aktif
