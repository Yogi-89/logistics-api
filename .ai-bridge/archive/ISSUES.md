# ShipStream — Logistics Rate & Tracking API — Bug & Status

> Format: Bug → Root Cause → Fix → Status

---

## 🟢 RESOLVED (Sudah Diselesaikan)

### [RESOLVED] Tombol Trash API Key Rusak (ReferenceError)
- **Tanggal ditemukan**: 2026-04-23
- **Gejala**: Klik tombol hapus API key tidak memunculkan apa-apa; muncul error di console.
- **Root Cause**: Memanggil `showConfirmDialog` padahal fungsi yang ada bernama `showConfirmModal`.
- **Fix**: Rename pemanggilan fungsi di `revokeKey()`.
- **File**: `frontend/dashboard.html`

### [RESOLVED] Tampilan modal billing di mobile perlu review
- **Tanggal ditemukan**: 2026-04-19
- **Fix**: Melalui konsolidasi media query di `style.css` (PROMPT C), layout modal dan grid settings sudah dipaksa 1-kolom dan simetris.
- **File**: `frontend/assets/style.css`

### [RESOLVED] User session tracking tidak update `last_active` secara real-time
- **Tanggal ditemukan**: 2026-04-19
- **Fix**: Implementasi session health polling setiap 5 menit di frontend memastikan session dicheck secara berkala ke backend.
- **File**: `frontend/dashboard.html`

### [RESOLVED] Playground dropdown kembali ke default saat pindah tab
- **Tanggal ditemukan**: 2026-04-23
- **Gejala**: User memilih API Key di playground, pindah ke tab Keys, lalu kembali ke Docs. Dropdown playground reset ke index 0.
- **Root Cause**: Komponen playground di-render ulang setiap kali tab dibuka tanpa mekanisme penyimpanan state pilihan user.
- **Fix**: Menyimpan `_selectedPlaygroundKey` ke variabel global dan melakukan restorasi nilai setelah proses render selesai.
- **File**: `frontend/dashboard.html`

### [RESOLVED] Timer interval tidak dibersihkan saat navigasi/logout
- **Tanggal ditemukan**: 2026-04-23
- **Gejala**: Performa dashboard semakin lambat setelah beberapa jam penggunaan (memory leak) atau freeze saat logout.
- **Root Cause**: `setInterval` untuk countdown billing dan checkout terus berjalan di background meskipun user sudah pindah tab atau logout.
- **Fix**: Implementasi global array `window._intervals` untuk menampung semua ID interval dan melakukan `clearInterval` massal saat logout atau re-inisialisasi.
- **File**: `frontend/dashboard.html`

### [RESOLVED] Animasi tidak smooth di HP spesifikasi rendah
- **Tanggal ditemukan**: 2026-04-23
- **Gejala**: UI terasa patah-patah (laggy) saat scrolling atau membuka tab di perangkat mobile lama.
- **Root Cause**: Penggunaan filter blur yang berat dikombinasikan dengan `transform: translateY` pada efek hover kartu `.glass`.
- **Fix**: Menonaktifkan efek transform pada media query mobile dan menyederhanakan transisi box-shadow.
- **File**: `frontend/assets/style.css`

### [RESOLVED] Copy to clipboard gagal di browser mobile (iOS/WebView)
- **Tanggal ditemukan**: 2026-04-23
- **Gejala**: Menekan tombol copy pada API Key atau alamat crypto tidak memberikan respon (gagal).
- **Root Cause**: `navigator.clipboard` diblokir oleh browser mobile jika tidak berjalan di HTTPS atau jika tidak dipicu oleh gesture user yang "bersih".
- **Fix**: Menggunakan fallback `document.execCommand('copy')` dengan elemen textarea tersembunyi jika API modern gagal.
- **File**: `frontend/dashboard.html`

### [RESOLVED] Auto-kapitalisasi mengganggu input data sensitif
- **Tanggal ditemukan**: 2026-04-23
- **Gejala**: Huruf pertama pada API Key label atau Transaction Hash otomatis menjadi kapital di HP, menyebabkan data tidak valid.
- **Root Cause**: Fitur bawaan OS mobile (autocapitalize/autocorrect) aktif secara default pada elemen `<input type="text">`.
- **Fix**: Menambahkan atribut `autocapitalize="none"`, `autocorrect="off"`, dan `spellcheck="false"` pada semua input teknis.
- **File**: `frontend/index.html`, `frontend/dashboard.html`

### [RESOLVED] Toast position overlapping dengan elemen header mobile
- **Tanggal ditemukan**: 2026-04-23
- **Gejala**: Notifikasi toast muncul di bawah dan menutupi navigasi atau meluap ke luar layar.
- **Root Cause**: CSS positioning `bottom: 20px` bertabrakan dengan floating navigation bar di mobile.
- **Fix**: Memindahkan toast ke `top: 16px` dengan dukungan `safe-area-inset-top` agar kompatibel dengan Notch/Dynamic Island.
- **File**: `frontend/assets/style.css`

### [RESOLVED] Hapus IP Whitelist di Settings API Key tidak tersimpan
- **Tanggal ditemukan**: 2026-04-22
- **Gejala**: User menghapus IP whitelist, klik save, tapi data lama tetap ada di DB.
- **Root Cause**: Backend menggunakan `if val is not None` check, sehingga mengabaikan nilai `null/""` yang dikirim frontend untuk mengosongkan field.
- **Fix**: Menggunakan `model_fields_set` di Pydantic untuk membedakan field yang tidak dikirim vs field yang dikirim sebagai null.
- **File**: `app/routers/apikey.py`, `frontend/dashboard.html`

### [RESOLVED] Duplicate Email Register menyebabkan HTTP 500
- **Tanggal ditemukan**: 2026-04-22
- **Gejala**: Register dengan email yang sudah terdaftar menghasilkan Error 500.
- **Root Cause**: Database IntegrityError tidak ditangani secara eksplisit di level router.
- **Fix**: Tambahkan `db.query(User).filter(...)` check sebelum proses registrasi.
- **File**: `app/routers/auth.py`

### [RESOLVED] Dashboard tidak bisa diklik sama sekali
- **Tanggal ditemukan**: 2026-04-20
- **Gejala**: Semua tab navbar (Keys, Billing, Profile, dll) tidak merespons klik
- **Root Cause**: `let currentTab = 'keys'` dideklarasi dua kali di `dashboard.html` (line 781 dan 1344). Browser mem-parse ini sebagai `SyntaxError` yang membuat seluruh script block gagal dieksekusi.
- **Fix**: Hapus deklarasi duplikat di line 1344
- **File**: `frontend/dashboard.html`

### [RESOLVED] "Unable to load transaction details" alert saat klik status badge
- **Tanggal ditemukan**: 2026-04-19
- **Gejala**: Klik badge PENDING/SUCCESS/INVALID di billing history menghasilkan alert error
- **Root Cause 1**: Data transaksi di-encode ke attribute HTML via `btoa()` (Base64). Karakter JSON yang kompleks (seperti blockchain hash) merusak encoding.
- **Root Cause 2**: Setelah migrasi cache, `formatAmount()` masih didefinisikan sebagai `const` lokal di dalam `loadBillingHistory()`, tidak bisa diakses dari `showTxInfoModal()`.
- **Fix 1**: Ganti Base64 encoding dengan `window._billingCache` global array + `data-tx-idx` index
- **Fix 2**: Promosikan `formatAmount()` dan `safeFormatDateGlobal()` ke global scope
- **File**: `frontend/dashboard.html`

### [RESOLVED] NameError: `timedelta` is not defined di `profile.py`
- **Tanggal ditemukan**: 2026-04-21
- **Gejala**: HTTP 500 saat meminta OTP keamanan.
- **Root Cause**: Lupa mengimpor `timedelta` pada module `profile.py`.
- **Fix**: Tambahkan `from datetime import datetime, timedelta`.
- **File**: `app/routers/profile.py`

### [RESOLVED] SyntaxError backend: `await` outside async function
- **Tanggal ditemukan**: 2026-04-20
- **Gejala**: Server crash saat startup dengan error: `SyntaxError: 'await' outside async function` di `billing.py` line 48
- **Root Cause**: Redundant import `from app.utils.exchange_rate import exchange_rate_provider` di dalam fungsi `create_topup()` menyebabkan masalah scope di beberapa versi Python
- **Fix**: Hapus import duplikat di dalam fungsi; gunakan top-level import yang sudah ada
- **File**: `app/routers/billing.py`

### [RESOLVED] Inkonsistensi Countdown & Format Jam (GMT+7)
- **Tanggal ditemukan**: 2026-04-20
- **Gejala**: Countdown expired prematur dan jam tidak sesuai WIB.
- **Root Cause**: `new Date(string)` menganggap string tanpa 'Z' sebagai local time, padahal DB menyimpan UTC.
- **Fix**: Paksa UTC parsing lewat `safeParseDate` dan standardisasi `safeFormatDateGlobal`.
- **Status**: [RESOLVED]

### [RESOLVED] Auth UI Monolith & Basic Aesthetic
- **Tanggal ditemukan**: 2026-04-19
- **Gejala**: Halaman utama terlihat seperti prototype internal, bukan produk SaaS profesional. Forms login/register langsung tampil di body.
- **Fix**: Redesign menjadi Premium Landing Page dengan sistem **Auth Modal**.
- **Status**: [RESOLVED]
- **File**: `frontend/index.html`, `frontend/assets/style.css`

### [RESOLVED] Modal "Batalkan Order" tidak aman (menggunakan native confirm())
- **Tanggal ditemukan**: 2026-04-19
- **Fix**: Ganti `window.confirm()` dengan `showConfirmDialog()` custom branded dialog
- **File**: `frontend/dashboard.html`

### [RESOLVED] Offset/Padding Tidak Simetris di Mobile (Profile & Settings)
- **Tanggal ditemukan**: 2026-04-22
- **Fix**: (Update 2026-04-23) Melakukan audit mendalam (Audit 1) dan memastikan `max-width: 100% !important` pada kartu di tab settings serta menonaktifkan transform hover di mobile.
- **File**: `frontend/assets/style.css`

### [RESOLVED] Inkonsistensi Label Alignment di Playground
- **Tanggal ditemukan**: 2026-04-23
- **Fix**: Menambahkan `min-height` dan `flex-end` alignment pada label di dalam `grid-2-col`.
- **File**: `frontend/assets/style.css`

---

## 🟡 KNOWN LIMITATIONS (Diketahui, Bukan Bug)

### Midtrans hanya simulasi
- Pembayaran Midtrans tidak terhubung ke gateway asli — hanya membuat invoice pending
- Konfirmasi manual diperlukan via `/v1/billing/admin/confirm-payment/{order_id}`
- **Status**: By design untuk UTS environment

### Telegram OTP bergantung pada internet
- Jika OTP melalui Telegram, user harus sudah setup bot token dan chat ID
- OTP fallback via email memerlukan konfigurasi SMTP (belum diimplementasi — langsung tampil di console/debug endpoint)
- **Status**: [RESOLVED] Menggunakan Resend.com

### Exchange rate menggunakan CoinGecko free tier
- Rate-limited ke beberapa request per menit
- Jika gagal, fallback ke `window._lastExchangeRate = 16000` (hardcoded)
- **Status**: Acceptable untuk demo

---

### [RESOLVED] Telegram setup wizard UI
- **Tanggal ditemukan**: 2026-04-19
- **Fix**: Sudah diimplementasikan box informasi "Cara Setup Bot" yang muncul otomatis saat channel Telegram dipilih.
- **File**: `frontend/dashboard.html`

### [RESOLVED] Settings tab mobile masih 2 kolom
- Tanggal ditemukan: 2026-04-23
- Gejala: Card berjejer 2 kolom di mobile padahal tab lain sudah 1 kolom
- Root cause: minmax(300px) tidak bisa collapse di viewport 360px
- Fix: minmax(min(280px, 100%), 1fr) di base rule
- File: frontend/assets/style.css

---

### [RESOLVED] Docs tab input misalign saat bahasa EN
- Tanggal ditemukan: 2026-04-23
- Gejala: Label EN lebih panjang menggeser alignment input
- Root cause: label height tidak seragam antar kolom
- Fix: min-height + flex align-end pada label
- File: frontend/assets/style.css

---

### [RESOLVED] Konten card overflow di mobile
- Tanggal ditemukan: 2026-04-23
- Fix: overflow hidden + flex-wrap control
- File: frontend/assets/style.css

---

## 📋 Template — Cara Menambah Issue Baru

```markdown
### [STATUS] Judul singkat masalah
- **Tanggal ditemukan**: YYYY-MM-DD
- **Gejala**: Apa yang terlihat dari sisi user
- **Root Cause**: Mengapa ini terjadi secara teknis
- **Fix**: (isi jika sudah resolved) langkah yang dilakukan
- **File**: file yang terlibat
- **Prioritas**: High / Medium / Low
```

Status options: `[OPEN]` `[IN PROGRESS]` `[RESOLVED]` `[WONT FIX]`

---

## ⚠️ Pola Bug yang Sering Terjadi — PANDUAN PREVENTIF

### 1. Duplicate variable declaration di dashboard.html
**Tanda**: Seluruh dashboard tidak bisa diklik, tidak ada error yang jelas di UI  
**Check**: Jalankan `Select-String -Path "frontend/dashboard.html" -Pattern "^        (let|var|const) " | Group-Object {$_.Line.Split("=")[0].Trim()} | Where-Object Count -gt 1`  

### 2. Fungsi JS yang tidak bisa diakses dari onclick
**Tanda**: `ReferenceError: xxx is not defined` di console  
**Cek**: Apakah fungsi itu didefinisikan di dalam fungsi lain? Jika ya, pindah ke global scope (indent 8 spasi di root script block)  

### 3. Schema Pydantic tidak sinkron dengan model SQLAlchemy
**Tanda**: `422 Unprocessable Entity` di endpoint  
**Cek**: Field di `schemas.py` harus ada di `models/base.py`  

### 4. Frontend fetch ke endpoint yang salah/berubah
**Tanda**: `404 Not Found` di network tab browser  
**Cek**: Bandingkan URL di `fetch()` di `dashboard.html` dengan route di router Python  

---

*File ini terakhir diupdate: 2026-04-23 oleh Antigravity*
