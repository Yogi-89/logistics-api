# 🤝 COLLAB PROTOCOL — Dual AI Collaboration
> Dokumen ini adalah kontrak kerja antara 2 AI di project ShipStream.
> Wajib dibaca oleh AI IDE di setiap sesi sebelum menyentuh kode apapun.

---

## 👥 Peran Masing-Masing AI

| AI | Peran | Tools |
|----|-------|-------|
| **Claude Desktop** | Architect — analisis, keputusan teknis, menulis instruksi ke bridge.md | Filesystem MCP (read/write .ai-bridge) |
| **AI IDE (Antigravity)** | Executor — eksekusi kode, hapus/buat file, jalankan test | Full akses codebase |

**Yogi** = owner yang memvalidasi dan mengarahkan keduanya.

---

## 📋 Protokol Status Tag (WAJIB konsisten)

Semua task di `bridge.md` section `Next Steps` menggunakan tag berikut:

| Tag | Arti | Siapa yang tulis |
|-----|------|-----------------|
| `[ ] TODO` | Belum dikerjakan, instruksi dari Claude | Claude Desktop |
| `[~] WIP` | Sedang dikerjakan | AI IDE |
| `[x] DONE` | Selesai & terverifikasi Claude | AI IDE (Claude verifikasi) |
| `[!] BLOCKED` | Ada masalah, butuh keputusan Yogi/Claude | AI IDE |
| `[?] VERIFY` | Selesai dikerjakan AI IDE, menunggu verifikasi Claude | AI IDE |

---

## 🔄 Alur Kerja Standar

```
Claude tulis [ ] TODO di bridge.md
        ↓
Yogi attach bridge.md ke AI IDE
        ↓
AI IDE baca bridge.md → eksekusi kode
        ↓
AI IDE ubah tag → [?] VERIFY + update progress.md
        ↓
Yogi ping Claude → Claude baca bridge.md + verifikasi kode
        ↓
Claude ubah tag → [x] DONE atau tulis [!] BLOCKED jika ada masalah
        ↓
Lanjut ke TODO berikutnya
```

---

## 📐 Aturan Penulisan di `bridge.md`

### Format TODO (ditulis Claude):
```
[ ] TODO — <judul singkat> | File: <nama file>
- <instruksi spesifik baris 1>
- <instruksi spesifik baris 2>
```

### Format setelah AI IDE selesai:
```
[?] VERIFY — <judul singkat> | File: <nama file>
- [x] <instruksi 1 yang sudah dikerjakan>
- [x] <instruksi 2 yang sudah dikerjakan>
```

### Format setelah Claude verifikasi:
```
[x] DONE — <judul singkat> | File: <nama file>
```
(detail dipindah ke progress.md, baris ini jadi ringkas)

---

## 📁 Aturan File di `.ai-bridge/`

| File | Penulis | Isi |
|------|---------|-----|
| `bridge.md` | Claude + AI IDE | Current state + active TODO list |
| `progress.md` | AI IDE | Log semua yang sudah DONE |
| `struktur.md` | AI IDE | Update jika ada perubahan struktur folder |
| `tech_used.md` | AI IDE | Update jika ada library/tool baru |
| `COLLAB_PROTOCOL.md` | Claude | Dokumen ini — jangan diubah tanpa konfirmasi Yogi |
| `archive/` | — | Gudang sejarah, tidak dibaca rutin |

**Larangan:**
- AI IDE DILARANG buat file baru di `.ai-bridge/` selain yang terdaftar di atas
- Claude DILARANG buat file task terpisah (semua instruksi masuk `bridge.md`)

---

## 🤖 Panduan untuk AI IDE (Antigravity)

### Di awal setiap sesi:
1. Baca `bridge.md` → cari semua item `[ ] TODO`
2. Kerjakan dari atas ke bawah, satu per satu
3. Ubah tag ke `[~] WIP` saat mulai, `[?] VERIFY` saat selesai

### Saat selesai task:
1. Update tag di `bridge.md` → `[?] VERIFY`
2. Catat di `progress.md` dengan format SKILL.md
3. Jangan hapus section TODO dari `bridge.md` — biarkan Claude yang ubah ke `[x] DONE`

### Saat ada masalah:
- Ubah tag ke `[!] BLOCKED`
- Tambahkan 1 baris keterangan masalahnya di bawah tag
- Jangan tebak-tebak sendiri jika menyangkut keputusan arsitektur

### Model yang digunakan AI IDE:
- **Claude Sonnet 4.6 (thinking)** → untuk task analisis/arsitektur yang kompleks
- **Gemini 2.5 Flash** → untuk eksekusi rutin (edit file, fix bug, update docs)
- **Gemini 2.5 Pro** → untuk task yang butuh reasoning lebih dalam

---

## 🤖 Panduan untuk Claude Desktop

### Di awal setiap sesi baru:
1. Baca `bridge.md` saja → sudah cukup untuk sync konteks (token-efisien)
2. Cek apakah ada item `[?] VERIFY` → verifikasi kode aktual via Filesystem
3. Tulis TODO baru di `bridge.md` jika ada task selanjutnya

> Baca `progress.md` hanya jika perlu detail history. Baca `COLLAB_PROTOCOL.md` hanya jika ada kebingungan protokol.

### Saat menulis TODO:
- Spesifik: sebutkan nama file, nama fungsi, atau baris yang relevan
- Jangan tulis penjelasan panjang — AI IDE butuh instruksi, bukan narasi
- Maksimal 5 instruksi per TODO item agar tidak overload konteks AI IDE
