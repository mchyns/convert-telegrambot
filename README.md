# DocPDF Bot — Telegram Document Converter Bot

Bot Telegram untuk konversi dua arah dokumen **DOCX ke PDF** dan **PDF ke DOCX** secara cepat, aman, dan tanpa aplikasi desktop tambahan di sisi pengguna.

---

## 🌟 Fitur Utama

- 🔄 **DOCX → PDF**: Mengonversi file Microsoft Word ke dokumen PDF siap cetak/kirim dengan LibreOffice Headless.
- 🔄 **PDF → DOCX**: Merekonstruksi file PDF teks menjadi dokumen Word yang dapat diedit menggunakan `pdf2docx`.
- ⚡ **Deteksi Format Otomatis**: Cukup kirim file, bot langsung mendeteksi format, ukuran, dan jenis konversi yang tepat.
- 🛡️ **Keamanan Tingkat Tinggi**:
  - Direktori kerja terisolasi berbasis UUID (`/tmp/docpdf/{job_uuid}/`).
  - Pencegahan *path traversal* (`../../`), karakter berbahaya, dan *command injection*.
  - Proteksi terhadap *decompression/zip bomb* dan file korup.
  - **Zero Permanent Storage**: File sementara langsung dihapus otomatis setelah dokumen dikirim ke Telegram.
  - TTL sweeper otomatis untuk membersihkan sisa direktori setiap interval waktu tertentu.
- 🚦 **Queue & Worker Architecture**: Didukung **Redis + RQ** untuk menangani antrian konversi berat tanpa memblokir respon bot Telegram.
- 🗄️ **Database Persistence**: Menyimpan status pekerjaan, riwayat kuota, dan statistik menggunakan **PostgreSQL** (atau SQLite otomatis untuk mode development lokal).
- ⏱️ **Rate Limiter & Quota**: Pembatasan ukuran file (default 25 MB) dan pembatasan konversi per jam untuk mencegah spam/abuse.

---

## 🏗️ Arsitektur Sistem

```text
               ┌─────────────────────┐
               │    Telegram User    │
               └──────────┬──────────┘
                          │ (Kirim Dokumen)
                          ▼
               ┌─────────────────────┐
               │  aiogram 3 Bot App  │
               └──────────┬──────────┘
                          │ (Validasi & UUID Sandbox)
                          ▼
               ┌─────────────────────┐
               │     Redis Queue     │
               └──────────┬──────────┘
                          │
                          ▼
               ┌─────────────────────┐
               │  Conversion Worker  │
               └────┬───────────┬─────┘
                    │           │
     ┌──────────────┘           └──────────────┐
     ▼                                         ▼
┌───────────────────────┐            ┌───────────────────────┐
│ DOCX → PDF Conversion │            │ PDF → DOCX Conversion │
│ (LibreOffice Headless)│            │      (pdf2docx)       │
└───────────┬───────────┘            └───────────┬───────────┘
            │                                    │
            └─────────────────┬──────────────────┘
                              │ (Validasi Output)
                              ▼
               ┌─────────────────────┐
               │  Telegram Delivery  │
               │   & Auto-Cleanup    │
               └─────────────────────┘
```

---

## 🚀 Panduan Memulai Cepat (Local Development)

### 1. Kebutuhan Sistem
- Python 3.12 atau 3.13
- Token bot dari [@BotFather](https://t.me/BotFather) di Telegram
- *(Opsional untuk DOCX → PDF di lokal)*: [LibreOffice](https://www.libreoffice.org/) terinstal di komputer. (Untuk PDF → DOCX sudah otomatis berjalan mandiri).

### 2. Setup Virtual Environment
```bash
# Buat virtual environment
python -m venv .venv

# Aktivasi di Windows (PowerShell):
.venv\Scripts\Activate.ps1
# Atau di Linux/macOS:
source .venv/bin/activate

# Install dependensi
pip install -r requirements.txt
```

### 3. Konfigurasi Environment (`.env`)
Salin template `.env.example` ke `.env`:
```bash
cp .env.example .env
```
Buka `.env` dan masukkan token bot Anda:
```env
BOT_TOKEN=123456789:ABCDefGhIJKlmNoPQRsTUVwxyZ
DATABASE_URL=sqlite+aiosqlite:///./docpdf.db
USE_REDIS_QUEUE=false
```
> *Catatan*: Dalam mode `USE_REDIS_QUEUE=false`, bot menggunakan antrian asynchronous internal otomatis sehingga Anda **tidak wajib** menjalankan Redis atau PostgreSQL saat pengembangan lokal di Windows.

### 4. Menjalankan Bot
```bash
python -m app.main
```

---

## 🐳 Deployment Produksi (Docker & Docker Compose)

Untuk lingkungan produksi (Linux VPS / Server), disarankan menjalankan seluruh stack menggunakan Docker Compose:

```bash
# 1. Pastikan file .env sudah terisi BOT_TOKEN yang valid
nano .env

# 2. Build dan jalankan seluruh container
docker compose up -d --build

# 3. Pantau log sistem
docker compose logs -f
```

Stack produksi terdiri dari:
1. **`telegram-bot`**: Menangani webhook/polling Telegram, validasi awal, dan penerimaan file.
2. **`worker`**: Worker terisolasi dilengkapi **LibreOffice headless** dan `pdf2docx` untuk pemrosesan file berat.
3. **`redis`**: Antrian pesan RQ yang persisten.
4. **`postgres`**: Database relasional untuk penyimpanan metadata dan statistik pekerjaan.

---

## 📖 Perintah Bot (Commands)

### Perintah Pengguna
| Perintah | Deskripsi |
|---|---|
| `/start` | Membuka pesan selamat datang, tombol navigasi, dan petunjuk utama |
| `/help` | Menampilkan panduan penggunaan dan rincian format dokumen yang didukung |
| `/status` | Melihat statistik dokumen pengguna (dalam antrian, diproses, sukses, gagal) |
| `/cancel` | Membatalkan dokumen milik pengguna yang masih menunggu di antrian |
| `/about` | Menampilkan informasi versi aplikasi dan kebijakan privasi dokumen |

### Perintah Administrator
*(Hanya dapat diakses oleh Telegram ID yang didaftarkan pada `ADMIN_TELEGRAM_IDS`)*
| Perintah | Deskripsi |
|---|---|
| `/admin` | Menampilkan menu dan bantuan perintah administrator |
| `/stats` | Melihat metrik performa: total pengguna, total konversi, tingkat keberhasilan, dan rasio format |
| `/queue` | Memeriksa beban antrian server dan jumlah worker yang sedang aktif |

---

## 🧪 Menjalankan Pengujian (Testing)

Proyek ini telah dilengkapi dengan suite unit test lengkap yang mencakup validasi dokumen, keamanan isolasi, konversi PDF ke DOCX, dan repository database:

```bash
# Jalankan seluruh unit test
pytest -v
```

---

## 📂 Struktur Direktori Proyek

```text
docpdf-bot/
├── app/
│   ├── bot/
│   │   ├── handlers/         # Router perintah & penerimaan file (.docx & .pdf)
│   │   ├── keyboards/        # Inline keyboard & menu interaktif
│   │   └── middleware/       # Anti-spam & user persistence middleware
│   ├── config/               # Pengaturan pydantic-settings & .env
│   ├── conversion/
│   │   ├── docx_to_pdf.py    # Subprocess runner LibreOffice headless
│   │   ├── pdf_to_docx.py    # Pipeline konversi berbasis pdf2docx
│   │   ├── validator.py      # Sanitasi filename, magic bytes & zip-bomb check
│   │   └── cleanup.py        # Pembersihan berkala direktori sementara (TTL)
│   ├── database/
│   │   ├── models.py         # Model SQLAlchemy (User & Job)
│   │   ├── repository.py     # Layer query database & metrik admin
│   │   └── session.py        # Engine database asynchronous (Postgres / SQLite)
│   ├── queue/
│   │   ├── jobs.py           # Eksekutor job konversi & integrasi RQ
│   │   └── worker.py         # Entrypoint runner worker independen
│   ├── services/
│   │   ├── telegram.py       # Helper pengiriman dokumen & pesan status
│   │   └── job_service.py    # Orkestrasi alur kerja persiapan job
│   └── main.py               # Entrypoint utama bot Telegram
├── docker/
│   ├── bot.Dockerfile        # Dockerfile untuk bot Telegram
│   └── worker.Dockerfile     # Dockerfile untuk worker dengan LibreOffice
├── tests/                    # Unit & integration test suite
├── docker-compose.yml        # Konfigurasi container produksi (Bot, Worker, Redis, DB)
├── requirements.txt          # Dependensi Python
├── .env.example              # Template konfigurasi environment
├── .gitignore
└── README.md
```

---

## 📄 Lisensi & Privasi

Aplikasi ini mengutamakan kerahasiaan data pengguna:
- Tidak ada dokumen yang disimpan permanen di server maupun database.
- Direktori pemrosesan segera dihapus begitu dokumen dikirim kembali ke pengguna Telegram.
