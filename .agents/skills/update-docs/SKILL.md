# ATURAN WAJIB UPDATE FILE DOKUMENTASI

## KAPAN HARUS UPDATE
Wajib update file .md yang relevan setiap kali:
- Ada file baru dibuat atau dihapus
- Ada fungsi/komponen baru ditambahkan
- Ada bug yang berhasil diperbaiki
- Ada perubahan logic/alur utama
- Ada teknologi/library baru dipakai
- Ada fitur selesai atau dimulai

Jangan skip update meskipun perubahannya kecil.

## CARA UPDATE (RINGKAS & TERSTRUKTUR)

### Jika file .md sudah ada:
- Baca isi file tersebut terlebih dahulu
- Update HANYA bagian yang berubah
- Jangan tulis ulang seluruh file
- Jangan hapus informasi yang masih relevan

### Format penulisan WAJIB:
- Gunakan bullet point, BUKAN paragraf
- Maksimal 1-2 baris per item
- Gunakan status tag: [DONE] [WIP] [TODO] [FIXED] [REMOVED]
- Sertakan nama file/fungsi yang terdampak

### Contoh format yang BENAR:
[DONE] tambah validasi input form login → auth/validate.js
[FIXED] bug JWT expired tidak tertangkap → auth/token.js:42
[WIP] integrasi payment gateway → payment/midtrans.js

### Contoh format yang SALAH (jangan lakukan):
"Saya telah berhasil menyelesaikan implementasi validasi 
input pada form login dengan menambahkan fungsi baru..."

## PENAMAAN FILE .MD
- Baca nama file .md untuk pahami isinya sebelum update
- Update file yang namanya paling relevan dengan perubahan
- Jangan update file .md yang tidak berkaitan

## PRIORITAS UPDATE
1. File .md yang namanya paling sesuai perubahan → update duluan
2. progress.md atau sejenisnya → selalu update setiap selesai task
3. bridge.md → update hasil eksekusi dengan 1-2 baris ringkas

## LARANGAN
- DILARANG menulis penjelasan panjang di file .md
- DILARANG duplikasi informasi di beberapa file sekaligus
- DILARANG update file .md yang tidak relevan dengan perubahan
- DILARANG hapus informasi lama kecuali sudah tidak relevan
