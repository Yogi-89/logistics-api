# Abstract

## English

**ShipStream — a metered logistics API platform for developers.**

Integrating shipping into an application usually means dealing with several courier APIs, each with its
own authentication, response format and commercial terms. ShipStream collapses that into a single REST
contract. A developer signs up, receives an API key, and can immediately quote shipping costs, list
cities and couriers, create shipments with a generated waybill, follow parcel tracking history and
download a printable shipping label. Usage is metered per request and paid for with prepaid quota, so
there is no monthly subscription and no per-courier contract to negotiate.

The platform is a full product rather than a thin proxy. It implements self-service onboarding with
email OTP verification, JWT sessions, multiple API keys per account, a shared quota pool, per-key IP
allow-listing and rate limiting with exponential backoff. Metering, key state and quota consumption are
enforced in the request path, and every billed action is traceable to an order.

Billing is deliberately independent of any single payment provider. Two flows are implemented: **static
QRIS**, where the payer scans the merchant's own QR code, confirms the transfer and an administrator
approves the order with a shared secret; and **USDC on Base**, where the submitted transaction hash is
verified against the chain — receipt status, transfer log, token contract, recipient wallet and expected
amount (with tolerance) must all match. Hashes unknown to the network are rejected rather than left in a
pending state, which keeps the ledger consistent with what the user is told.

The backend is a FastAPI application backed by PostgreSQL through SQLAlchemy, with Alembic migrations
and idempotent reference-data seeding executed at boot. The dashboard is served by the same process as
plain HTML/CSS/JS, keeping the deployment footprint to a single service. The reference deployment runs
on Render (Singapore) against Supabase Postgres, with Cloudflare for DNS and Resend for transactional
email; secrets are supplied entirely through environment variables so no credential is stored in the
repository.

The result is a compact but end-to-end example of API product engineering: a documented public contract,
authentication and abuse controls, usage metering, two independent payment verification paths, database
migrations, automated tests and a reproducible deployment.

## Bahasa Indonesia

**ShipStream — platform API logistik berbasis kuota untuk developer.**

Menambahkan fitur pengiriman ke sebuah aplikasi biasanya berarti harus berurusan dengan beberapa API
kurir, masing-masing dengan autentikasi, format respons, dan skema komersial yang berbeda. ShipStream
menyatukannya menjadi satu kontrak REST. Developer mendaftar, mendapatkan API key, lalu dapat langsung
menghitung ongkos kirim, melihat daftar kota dan kurir, membuat pengiriman beserta nomor resi (AWB),
melacak riwayat paket, dan mengunduh label pengiriman dalam format PDF. Pemakaian dihitung per request
dan dibayar di muka melalui kuota prabayar, sehingga tidak ada langganan bulanan maupun kontrak per
kurir.

Platform ini dibangun sebagai produk utuh, bukan sekadar proxy tipis. Tersedia pendaftaran mandiri
dengan verifikasi OTP email, sesi JWT, banyak API key dalam satu akun, kuota bersama, pembatasan IP per
key, serta rate limiting dengan exponential backoff. Penghitungan pemakaian, status key, dan sisa kuota
ditegakkan langsung pada jalur request, dan setiap transaksi yang dibebankan dapat ditelusuri ke order
terkait.

Sistem pembayaran sengaja tidak terikat pada satu penyedia. Ada dua alur: **QRIS statis**, di mana
pembayar memindai kode QR milik merchant, mengonfirmasi transfer, lalu admin menyetujui order dengan
token rahasia; dan **USDC di jaringan Base**, di mana hash transaksi diverifikasi langsung ke blockchain
— status receipt, log transfer, kontrak token, alamat penerima, dan nominal yang diharapkan (dengan
toleransi) harus cocok. Hash yang tidak dikenal jaringan akan ditolak, bukan dibiarkan menggantung,
sehingga status yang dilihat pengguna selalu konsisten dengan catatan sistem.

Backend berupa aplikasi FastAPI dengan basis data PostgreSQL melalui SQLAlchemy, migrasi Alembic, dan
seeding data referensi yang idempoten dan dijalankan saat boot. Dashboard disajikan oleh proses yang
sama dalam bentuk HTML/CSS/JS tanpa proses build, sehingga deployment hanya membutuhkan satu service.
Deployment referensi berjalan di Render (Singapura) dengan Supabase Postgres, Cloudflare untuk DNS, dan
Resend untuk email transaksional; seluruh kredensial disuplai lewat environment variable sehingga tidak
ada rahasia yang tersimpan di repositori.

Hasilnya adalah contoh ringkas namun menyeluruh dari rekayasa produk API: kontrak publik yang
terdokumentasi, autentikasi dan pengendalian penyalahgunaan, pengukuran pemakaian, dua jalur verifikasi
pembayaran yang independen, migrasi basis data, pengujian otomatis, serta deployment yang dapat direproduksi.

## Scope at a glance

| Aspect | Summary |
|---|---|
| Domain | Logistics: rates, courier directory, shipments, tracking, labels |
| Users | Developers/teams consuming the API, plus an administrator approving payments |
| Core entities | `users`, `api_keys`, `transactions`, `tracking`, `cities`, `subdistricts`, `couriers`, `user_sessions`, `verification_codes` |
| Monetisation | Prepaid quota packages paid via static QRIS or USDC (Base) |
| Auth | Email OTP → JWT session; `X-API-Key` for metered endpoints |
| Integrations | Resend (email), Etherscan v2 + Base RPC (chain), Komerce/RajaOngkir (rates, optional) |
| Deployment | One Render web service + managed PostgreSQL, documented in `docs/DEPLOYMENT.md` |
| Non-goals | Multi-tenant billing splits, webhook delivery, SDKs (all listed in the roadmap) |
