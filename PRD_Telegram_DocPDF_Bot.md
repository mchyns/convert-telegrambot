# PRD — Telegram Document Converter Bot

## 1. Informasi Produk

**Nama Produk:** DocPDF Bot  
**Platform:** Telegram Bot  
**Fungsi Utama:** Konversi file DOCX ke PDF dan PDF ke DOCX melalui Telegram tanpa aplikasi desktop tambahan di sisi pengguna.

### 1.1 Tujuan

Membangun bot Telegram yang memungkinkan pengguna mengirim file dokumen, memilih jenis konversi, lalu menerima hasil konversi kembali langsung di dalam chat.

Konversi utama:

- DOCX → PDF
- PDF → DOCX

Produk harus berfokus pada proses yang sederhana, cepat, aman, dan minim interaksi. Pengguna tidak perlu membuat akun khusus karena identitas pengguna sudah berasal dari Telegram.

### 1.2 Prinsip Produk

- User cukup mengirim file ke bot.
- Bot mendeteksi format file secara otomatis.
- Bot memberikan pilihan konversi yang valid.
- File diproses di server.
- Hasil dikirim kembali sebagai dokumen Telegram.
- File sementara dihapus otomatis setelah proses selesai.
- Semua batas file, timeout, dan jumlah pekerjaan dibuat configurable.
- Tidak menyimpan file pengguna secara permanen.

---

# 2. Target Pengguna

## 2.1 Pengguna Utama

- Mahasiswa
- Pelajar
- Dosen dan tenaga pendidikan
- Karyawan
- Administrasi kantor
- Freelancer
- Pengguna umum yang membutuhkan konversi dokumen cepat

## 2.2 Use Case

### DOCX ke PDF

Pengguna memiliki tugas atau dokumen Word dan perlu mengubahnya menjadi PDF sebelum dikirim.

### PDF ke DOCX

Pengguna menerima dokumen PDF dan membutuhkan versi yang dapat diedit kembali menggunakan Microsoft Word atau aplikasi sejenis.

---

# 3. Scope Produk

## 3.1 Fitur MVP

### A. Start Bot

Command:

```text
/start
```

Bot menampilkan:

- Nama bot
- Penjelasan singkat
- Format yang didukung
- Cara menggunakan bot
- Tombol bantuan

Contoh:

```text
Halo, selamat datang di DocPDF Bot.

Kirim file DOCX atau PDF ke chat ini.
Bot akan membantu mengubah:
DOCX → PDF
PDF → DOCX

Kirim dokumen untuk memulai.
```

### B. Automatic File Detection

Bot harus dapat mendeteksi file berdasarkan:

1. Extension
2. MIME type
3. File signature jika diperlukan

Format yang diterima:

```text
.docx
.pdf
```

File lain ditolak dengan pesan yang jelas.

### C. DOCX → PDF

Flow:

```text
User mengirim DOCX
↓
Bot validasi file
↓
Bot mengunduh file
↓
File masuk processing queue
↓
Worker menjalankan LibreOffice headless
↓
PDF dibuat
↓
PDF divalidasi
↓
PDF dikirim ke Telegram
↓
Temporary files dihapus
```

### D. PDF → DOCX

Flow:

```text
User mengirim PDF
↓
Bot validasi file
↓
Bot mengunduh file
↓
File masuk processing queue
↓
Worker menjalankan PDF to DOCX converter
↓
DOCX dibuat
↓
DOCX divalidasi
↓
DOCX dikirim ke Telegram
↓
Temporary files dihapus
```

### E. Progress Status

Bot memberikan status sederhana:

```text
File diterima.
Sedang memproses dokumen...
```

Jika proses membutuhkan waktu:

```text
Konversi masih berjalan.
Mohon tunggu...
```

Setelah selesai:

```text
Konversi selesai.

File hasil:
namadokumen.pdf
```

### F. Error Handling

Bot harus menangani:

- File corrupt
- File kosong
- Format tidak didukung
- File terlalu besar
- Timeout
- Converter gagal
- File hasil tidak terbentuk
- Telegram API gagal
- Storage penuh
- Queue terlalu panjang
- Dependency converter bermasalah

---

# 4. Fitur Tambahan

## 4.1 Command `/help`

Menampilkan informasi:

```text
Cara menggunakan bot:

1. Kirim file DOCX untuk diubah menjadi PDF.
2. Kirim file PDF untuk diubah menjadi DOCX.
3. Tunggu proses selesai.
4. Download file hasil.

Format:
DOCX → PDF
PDF → DOCX
```

## 4.2 Command `/status`

Menampilkan status user:

```text
Status kamu:

Queue       : 1
Diproses    : 0
Selesai     : 12
Gagal       : 1
```

## 4.3 Command `/cancel`

Membatalkan pekerjaan user yang masih berada di queue.

Contoh:

```text
Pekerjaan berhasil dibatalkan.
```

## 4.4 Command `/about`

Informasi bot dan versi aplikasi.

---

# 5. User Flow

## 5.1 DOCX → PDF

```text
/start
    ↓
User mengirim file .docx
    ↓
Bot mendeteksi DOCX
    ↓
Bot melakukan validasi
    ↓
Bot memberi status "menunggu"
    ↓
Job masuk queue
    ↓
Worker mengambil job
    ↓
DOCX dikonversi menjadi PDF
    ↓
Output diperiksa
    ↓
PDF dikirim ke user
    ↓
Temporary data dihapus
```

## 5.2 PDF → DOCX

```text
/start
    ↓
User mengirim file .pdf
    ↓
Bot mendeteksi PDF
    ↓
Bot melakukan validasi
    ↓
Bot memberi status "menunggu"
    ↓
Job masuk queue
    ↓
Worker mengambil job
    ↓
PDF dikonversi menjadi DOCX
    ↓
Output diperiksa
    ↓
DOCX dikirim ke user
    ↓
Temporary data dihapus
```

---

# 6. Arsitektur Sistem

## 6.1 Rekomendasi Stack

### Backend

**Python 3.12+**

Alasan:

- Cocok untuk Telegram Bot
- Library Telegram matang
- Mudah menjalankan subprocess
- Banyak library PDF/DOCX
- Mudah dikembangkan menjadi worker-based architecture

### Telegram Framework

**aiogram 3.x**

Digunakan untuk:

- Telegram Bot API
- Handler command
- Handler document
- Callback query
- Middleware
- FSM jika diperlukan

### DOCX → PDF

**LibreOffice Headless**

LibreOffice dijalankan tanpa GUI.

Contoh konsep command:

```bash
libreoffice --headless --convert-to pdf --outdir /output input.docx
```

### PDF → DOCX

Rekomendasi awal:

**pdf2docx**

Alternatif:

- LibreOffice
- PyMuPDF + python-docx untuk pipeline custom
- layanan conversion pihak ketiga jika nantinya diperlukan

Untuk MVP, `pdf2docx` digunakan terlebih dahulu dan hasil konversi harus diberi catatan bahwa PDF kompleks dapat mengalami perubahan layout.

### Queue

Untuk MVP kecil:

```text
Redis + RQ
```

Alternatif:

- Celery + Redis
- Dramatiq + Redis

### Database

**PostgreSQL**

Digunakan untuk menyimpan:

- User Telegram ID
- Job
- Status job
- Waktu proses
- Statistik
- Error log

Database tidak digunakan untuk menyimpan file dokumen.

### Storage

Temporary local storage:

```text
/tmp/docpdf/
```

Production dengan banyak worker:

- S3 compatible storage
- MinIO
- Cloud object storage

Namun file harus memiliki TTL dan otomatis dihapus.

### Deployment

Rekomendasi:

```text
Docker
Docker Compose
Linux VPS
```

---

# 7. Arsitektur Komponen

```text
                ┌───────────────────┐
                │      Telegram     │
                └─────────┬─────────┘
                          │
                          ▼
                ┌───────────────────┐
                │   Telegram Bot    │
                │     aiogram       │
                └─────────┬─────────┘
                          │
                          ▼
                ┌───────────────────┐
                │     Validator     │
                └─────────┬─────────┘
                          │
                          ▼
                ┌───────────────────┐
                │       Queue       │
                │   Redis + RQ      │
                └─────────┬─────────┘
                          │
                          ▼
                ┌───────────────────┐
                │      Worker       │
                └───────┬─────┬─────┘
                        │     │
             ┌──────────┘     └──────────┐
             ▼                           ▼
    ┌────────────────┐          ┌────────────────┐
    │  DOCX → PDF    │          │  PDF → DOCX    │
    │  LibreOffice   │          │   pdf2docx     │
    └───────┬────────┘          └───────┬────────┘
            │                           │
            └────────────┬──────────────┘
                         ▼
                ┌───────────────────┐
                │ Output Validator  │
                └─────────┬─────────┘
                          ▼
                ┌───────────────────┐
                │ Telegram Delivery │
                └─────────┬─────────┘
                          ▼
                     User receives
```

---

# 8. Modul Sistem

## 8.1 Telegram Bot Module

Tanggung jawab:

- menerima update Telegram
- membaca command
- menerima dokumen
- mengirim status
- mengirim hasil

File contoh:

```text
app/bot/
├── handlers/
│   ├── start.py
│   ├── help.py
│   ├── document.py
│   └── status.py
├── keyboards/
│   └── main.py
└── middleware/
    └── rate_limit.py
```

## 8.2 File Validator

Validasi:

- extension
- MIME type
- signature
- ukuran
- filename
- karakter berbahaya
- file kosong

Rules:

```text
Allowed:
application/pdf
application/vnd.openxmlformats-officedocument.wordprocessingml.document
```

Extension yang diterima:

```text
.pdf
.docx
```

File dengan extension palsu tidak boleh langsung dipercaya.

---

# 9. File Naming

File hasil harus mempertahankan nama file asli.

Contoh:

```text
laporan-akhir.docx
```

menjadi:

```text
laporan-akhir.pdf
```

Dan:

```text
laporan-akhir.pdf
```

menjadi:

```text
laporan-akhir.docx
```

Jika nama file tidak tersedia:

```text
converted_document.pdf
```

Untuk file temporary gunakan UUID.

Contoh:

```text
/tmp/docpdf/8fd2e7d4/input.docx
/tmp/docpdf/8fd2e7d4/output.pdf
```

---

# 10. Database Design

## 10.1 Table `users`

```sql
CREATE TABLE users (
    id BIGSERIAL PRIMARY KEY,
    telegram_id BIGINT UNIQUE NOT NULL,
    username VARCHAR(255),
    first_name VARCHAR(255),
    last_name VARCHAR(255),
    total_jobs INTEGER DEFAULT 0,
    successful_jobs INTEGER DEFAULT 0,
    failed_jobs INTEGER DEFAULT 0,
    created_at TIMESTAMP NOT NULL,
    updated_at TIMESTAMP NOT NULL
);
```

## 10.2 Table `jobs`

```sql
CREATE TABLE jobs (
    id BIGSERIAL PRIMARY KEY,
    job_uuid UUID UNIQUE NOT NULL,
    user_id BIGINT NOT NULL,
    input_filename VARCHAR(512) NOT NULL,
    output_filename VARCHAR(512),
    input_format VARCHAR(20) NOT NULL,
    output_format VARCHAR(20) NOT NULL,
    input_size BIGINT NOT NULL,
    status VARCHAR(30) NOT NULL,
    error_message TEXT,
    processing_started_at TIMESTAMP,
    processing_finished_at TIMESTAMP,
    created_at TIMESTAMP NOT NULL,
    updated_at TIMESTAMP NOT NULL,

    CONSTRAINT fk_jobs_user
        FOREIGN KEY (user_id)
        REFERENCES users(id)
);
```

## 10.3 Status Job

Status yang diperbolehkan:

```text
queued
processing
completed
failed
cancelled
```

---

# 11. API Internal

Bot dapat menggunakan internal service layer agar business logic tidak bercampur dengan Telegram handler.

Contoh:

```text
POST /internal/jobs
GET  /internal/jobs/{job_uuid}
POST /internal/jobs/{job_uuid}/cancel
```

Endpoint internal tidak boleh terbuka ke internet tanpa authentication.

---

# 12. Conversion Service

## 12.1 DOCX → PDF

Pipeline:

```text
Input DOCX
    ↓
Basic validation
    ↓
LibreOffice headless
    ↓
Output PDF
    ↓
PDF validation
    ↓
Return file path
```

Pengecekan hasil:

- file exists
- ukuran file > 0
- magic bytes PDF
- dapat dibuka parser PDF
- jumlah halaman valid

## 12.2 PDF → DOCX

Pipeline:

```text
Input PDF
    ↓
PDF validation
    ↓
pdf2docx
    ↓
Output DOCX
    ↓
DOCX ZIP/container validation
    ↓
Return file path
```

Pengecekan hasil:

- file exists
- ukuran file > 0
- DOCX merupakan ZIP container valid
- `[Content_Types].xml` tersedia
- document relationship valid

---

# 13. PDF → DOCX Limitasi

Konversi PDF ke DOCX bukan sekadar rename extension.

PDF menyimpan layout halaman, sedangkan DOCX menyimpan struktur dokumen yang berbeda.

Untuk itu:

- teks harus diekstrak
- posisi elemen dipetakan
- gambar diproses
- tabel direkonstruksi
- paragraf direkonstruksi
- font dan spacing diperkirakan

Dokumen sederhana harus menjadi target utama MVP.

Dokumen yang kemungkinan memiliki perubahan layout:

- scan
- PDF hasil foto
- PDF dengan banyak kolom
- tabel kompleks
- formulir
- dokumen dengan banyak gambar
- font khusus
- PDF dengan handwriting

Bot harus memberi informasi bahwa hasil PDF → DOCX dapat berbeda dari dokumen asli, terutama pada layout yang kompleks.

---

# 14. OCR

OCR tidak wajib untuk MVP.

Namun sistem harus disiapkan agar nantinya dapat mendukung:

```text
Scanned PDF
    ↓
OCR
    ↓
Text reconstruction
    ↓
DOCX
```

Pilihan teknologi:

- Tesseract OCR
- PaddleOCR
- OCR service

Fitur ini dapat diaktifkan sebagai mode terpisah.

Contoh:

```text
PDF biasa → DOCX
PDF scan → DOCX + OCR
```

---

# 15. Security

## 15.1 Temporary File Isolation

Setiap job memiliki folder sendiri.

```text
/tmp/docpdf/{job_uuid}/
```

Contoh:

```text
input/
output/
logs/
```

Setelah job selesai:

```text
delete folder
```

## 15.2 File Sanitization

Nama file dari user tidak boleh digunakan langsung sebagai command argument atau path.

Gunakan:

```text
UUID + extension
```

Nama asli hanya digunakan sebagai metadata/output filename.

## 15.3 Command Injection Prevention

Jangan menggunakan shell string yang dibangun dari input user.

Hindari:

```python
os.system(f"libreoffice {filename}")
```

Gunakan subprocess argument list:

```python
subprocess.run([
    "libreoffice",
    "--headless",
    "--convert-to",
    "pdf",
    input_file
])
```

## 15.4 Resource Limit

Setiap conversion harus mempunyai:

- maximum execution time
- memory limit
- CPU limit
- maximum file size
- queue limit
- per-user rate limit

## 15.5 Malicious File Protection

Sistem harus memvalidasi dokumen dan mempertimbangkan:

- zip bomb
- decompression bomb
- malformed PDF
- oversized embedded image
- recursive archive content
- suspicious OOXML content

Untuk production, worker sebaiknya berjalan di container terisolasi.

---

# 16. Rate Limit

Contoh konfigurasi awal:

```env
MAX_FILE_SIZE_MB=25
MAX_JOBS_PER_USER_PER_HOUR=30
MAX_CONCURRENT_JOBS=3
JOB_TIMEOUT_SECONDS=120
MAX_QUEUE_SIZE=100
```

Semua nilai harus dapat diubah melalui environment variable.

---

# 17. Queue System

Queue digunakan supaya banyak user tidak membuat server overload.

Contoh:

```text
User A → Job 001
User B → Job 002
User C → Job 003
User D → Job 004
```

Jika worker hanya 2:

```text
Worker 1 → Job 001
Worker 2 → Job 002

Queue:
Job 003
Job 004
```

Setelah selesai:

```text
Worker 1 → Job 003
Worker 2 → Job 004
```

---

# 18. UX Telegram

## 18.1 Saat User Mengirim DOCX

Bot:

```text
File diterima.

Nama:
laporan.docx

Ukuran:
2.4 MB

Konversi:
DOCX → PDF

Status:
Masuk antrian.
```

## 18.2 Saat Processing

```text
Sedang mengonversi laporan.docx...
```

## 18.3 Saat Berhasil

```text
Konversi selesai.

File PDF sudah siap.
```

Bot kemudian mengirim dokumen:

```text
laporan.pdf
```

## 18.4 Saat Gagal

```text
Konversi gagal.

Dokumen kemungkinan rusak atau memiliki struktur yang tidak didukung.

Silakan coba file lain.
```

Jangan menampilkan stack trace kepada user.

---

# 19. Inline Keyboard

Keyboard utama:

```text
[ Cara Menggunakan ]
[ Format Didukung ]
[ Status ]
```

Setelah file diterima:

```text
[ Convert ]
[ Batal ]
```

Jika format sudah dapat ditentukan otomatis, tombol Convert dapat langsung diproses tanpa meminta pilihan user.

---

# 20. Admin Panel

Admin panel bersifat optional untuk MVP, tetapi disarankan untuk production.

Fitur:

- Dashboard
- Total users
- Total jobs
- Conversion success rate
- Queue status
- Failed jobs
- Job history
- Per-user statistics
- Block/unblock user
- Maintenance mode
- Rate limit configuration
- Maximum file size configuration

Admin panel dapat dibuat menggunakan:

```text
FastAPI + Jinja
```

atau

```text
Laravel/React
```

Namun untuk MVP bot, admin panel tidak wajib.

---

# 21. Logging

Gunakan structured logging.

Informasi:

```text
timestamp
level
job_uuid
telegram_id
input_format
output_format
processing_time
file_size
status
error_code
```

Jangan log:

- isi dokumen
- token bot
- password database
- file content
- sensitive document metadata yang tidak diperlukan

Contoh:

```text
INFO job=8fd2... format=docx_to_pdf size=2481932 status=completed duration=4.21s
```

---

# 22. Monitoring

Monitoring production minimal:

- CPU
- RAM
- disk usage
- queue depth
- worker status
- conversion duration
- failed jobs
- Telegram API error
- database connection
- Redis connection

Health check:

```text
GET /health
```

Output:

```json
{
  "status": "ok",
  "database": "ok",
  "redis": "ok",
  "converter": "ok"
}
```

---

# 23. Configuration

Gunakan `.env`.

Contoh:

```env
APP_ENV=production
APP_NAME=DocPDF Bot

BOT_TOKEN=YOUR_TELEGRAM_BOT_TOKEN

DATABASE_URL=postgresql://docpdf:password@postgres:5432/docpdf

REDIS_URL=redis://redis:6379/0

MAX_FILE_SIZE_MB=25
MAX_CONCURRENT_JOBS=3
JOB_TIMEOUT_SECONDS=120
MAX_QUEUE_SIZE=100

TEMP_DIR=/tmp/docpdf

LOG_LEVEL=INFO
```

Jangan commit `.env` ke repository.

---

# 24. Project Structure

Rekomendasi:

```text
docpdf-bot/
├── app/
│   ├── bot/
│   │   ├── handlers/
│   │   │   ├── start.py
│   │   │   ├── help.py
│   │   │   ├── document.py
│   │   │   ├── status.py
│   │   │   └── cancel.py
│   │   ├── keyboards/
│   │   └── middleware/
│   │
│   ├── conversion/
│   │   ├── docx_to_pdf.py
│   │   ├── pdf_to_docx.py
│   │   ├── validator.py
│   │   └── cleanup.py
│   │
│   ├── queue/
│   │   ├── jobs.py
│   │   └── worker.py
│   │
│   ├── database/
│   │   ├── models.py
│   │   ├── repository.py
│   │   └── migrations/
│   │
│   ├── config/
│   │   └── settings.py
│   │
│   ├── services/
│   │   ├── telegram.py
│   │   └── job_service.py
│   │
│   └── main.py
│
├── tests/
│   ├── test_validator.py
│   ├── test_docx_to_pdf.py
│   ├── test_pdf_to_docx.py
│   └── test_jobs.py
│
├── docker/
│   ├── bot.Dockerfile
│   └── worker.Dockerfile
│
├── docker-compose.yml
├── requirements.txt
├── .env.example
├── .gitignore
└── README.md
```

---

# 25. Docker Architecture

Rekomendasi service:

```text
telegram-bot
worker
redis
postgres
```

Contoh:

```text
docker-compose
│
├── bot
├── worker
├── redis
└── postgres
```

Worker harus memiliki LibreOffice dan seluruh dependency conversion.

Bot container tidak perlu menjalankan converter secara langsung.

---

# 26. Deployment

## 26.1 Development

Environment:

```text
Windows/Linux/macOS
Python
Docker Desktop
Telegram Bot
```

Development dapat menggunakan:

```text
long polling
```

## 26.2 Production

Rekomendasi:

```text
Linux VPS
Docker
Docker Compose
Reverse Proxy
HTTPS
```

Webhook dapat digunakan untuk production.

Arsitektur:

```text
Telegram
   ↓
HTTPS
   ↓
Reverse Proxy
   ↓
Bot API
   ↓
Redis Queue
   ↓
Worker
   ↓
Converter
```

---

# 27. Database Persistence

Database hanya menyimpan metadata.

Contoh:

```text
User:
Telegram ID
Username
Statistics

Job:
Filename
Format
Size
Status
Duration
Error
Timestamp
```

File dokumen tidak disimpan permanen ke PostgreSQL.

---

# 28. Automatic Cleanup

Setiap job wajib melakukan cleanup.

Contoh:

```python
try:
    process_conversion()
    send_output()
finally:
    cleanup_temp_directory()
```

Background cleanup juga dapat berjalan setiap beberapa menit untuk menangani orphaned files.

Contoh policy:

```text
Temporary file TTL = 30 minutes
```

---

# 29. Failure Recovery

Jika worker mati ketika job sedang diproses:

```text
processing
↓
worker crash
↓
job timeout detected
↓
job marked failed/requeued
```

Job yang aman untuk diulang dapat memiliki retry.

Contoh:

```env
MAX_RETRIES=2
```

Retry tidak boleh dilakukan terus-menerus untuk dokumen yang memang invalid.

---

# 30. Idempotency

Setiap job mempunyai UUID unik.

Contoh:

```text
9fc0ec9a-4d5a-4f7e-b3d5-4b9d1c3b2f10
```

Job yang sama tidak boleh menghasilkan duplicate processing karena retry.

Worker harus mengecek status job sebelum menjalankan conversion.

---

# 31. Performance Target

Target awal:

### DOCX → PDF

Dokumen normal:

```text
< 10 detik
```

### PDF → DOCX

Dokumen normal:

```text
< 20 detik
```

Nilai tersebut bukan jaminan dan sangat bergantung pada:

- jumlah halaman
- gambar
- tabel
- kompleksitas layout
- performa VPS
- jumlah worker

---

# 32. Acceptance Criteria

## A. DOCX → PDF

- User dapat mengirim DOCX.
- Bot menerima file valid.
- Bot menolak file unsupported.
- File DOCX berhasil diproses.
- PDF output dapat dibuka.
- PDF dikirim ke user.
- Nama file output benar.
- Temporary file dihapus.

## B. PDF → DOCX

- User dapat mengirim PDF.
- Bot menerima PDF valid.
- PDF berhasil dikonversi.
- DOCX output merupakan file valid.
- DOCX dapat dibuka di Microsoft Word/LibreOffice.
- File dikirim ke user.
- Temporary file dihapus.

## C. Security

- Input filename tidak dapat melakukan path traversal.
- Command injection tidak terjadi.
- File temporary tidak dapat diakses langsung oleh publik.
- Bot token tidak masuk source control.
- Dokumen user tidak disimpan permanen.

## D. Reliability

- Worker crash tidak menyebabkan queue rusak.
- Job memiliki timeout.
- Conversion error dicatat.
- User menerima pesan error yang aman.
- System dapat melakukan cleanup orphan files.

---

# 33. Testing

## 33.1 Unit Test

Test:

```text
validator
filename sanitization
format detection
job status
cleanup
conversion service
```

## 33.2 Integration Test

Test:

```text
Telegram → Bot → Queue → Worker → Converter → Telegram
```

## 33.3 File Test Dataset

Sediakan:

```text
simple.docx
table.docx
image.docx
long-document.docx
simple.pdf
table.pdf
multi-column.pdf
image-heavy.pdf
scanned.pdf
corrupt.pdf
empty.pdf
```

## 33.4 Security Test

Test:

```text
../../etc/passwd
file.pdf.exe
file.docx.sh
malformed PDF
malformed DOCX
oversized file
zip bomb
repeated requests
spam upload
```

---

# 34. UX Edge Cases

### User mengirim file unsupported

```text
Format file belum didukung.

Format yang tersedia:
DOCX
PDF
```

### File terlalu besar

```text
Ukuran file melebihi batas yang diperbolehkan.
```

### User mengirim beberapa file

Bot membuat job terpisah untuk setiap file.

Contoh:

```text
3 file diterima.

Job #001
Job #002
Job #003
```

### Queue penuh

```text
Server sedang penuh.

Silakan coba lagi beberapa saat.
```

### Conversion gagal

```text
Dokumen tidak dapat dikonversi.

Kemungkinan penyebab:
- file rusak
- struktur dokumen tidak didukung
- proses conversion timeout
```

---

# 35. Future Features

## Batch Conversion

User dapat mengirim beberapa file sekaligus.

Contoh:

```text
10 DOCX
↓
10 PDF
```

## ZIP Result

Jika user mengirim banyak file:

```text
multiple files
↓
convert
↓
ZIP
```

## PDF Merge

```text
PDF A
PDF B
PDF C
↓
Merge
↓
combined.pdf
```

## PDF Split

```text
document.pdf
↓
page 1-3
page 4-8
page 9-12
```

## Compress PDF

```text
PDF
↓
Compression
↓
smaller PDF
```

## Convert Image to PDF

```text
JPG/PNG
↓
PDF
```

## OCR

```text
Scanned PDF
↓
OCR
↓
Editable DOCX
```

## Password-Protected File

Dapat ditambahkan dengan alur:

```text
User mengirim PDF
↓
PDF membutuhkan password
↓
Bot meminta password
↓
Password digunakan hanya selama processing
↓
Password tidak disimpan
```

## User Quota

Contoh:

```text
Free:
20 conversion/day

Premium:
Unlimited / higher quota
```

Fitur premium dapat ditambahkan jika produk nantinya dikomersialkan.

---

# 36. Admin Commands

Command yang dapat tersedia khusus admin:

```text
/admin
/stats
/queue
/jobs
/ban
/unban
/broadcast
/maintenance
```

Semua command admin wajib mengecek Telegram ID berdasarkan `ADMIN_TELEGRAM_IDS`.

Contoh:

```env
ADMIN_TELEGRAM_IDS=123456789,987654321
```

---

# 37. Environment Security

Secret wajib berada di environment:

```text
BOT_TOKEN
DATABASE_URL
REDIS_URL
```

Tidak diperbolehkan:

```python
BOT_TOKEN = "123456:ABC..."
```

di source code production.

Tambahkan `.env` ke:

```text
.gitignore
```

---

# 38. Product Metrics

Metric yang perlu dicatat:

```text
Total users
Daily active users
Total conversions
DOCX → PDF count
PDF → DOCX count
Success rate
Failure rate
Average processing time
Average file size
Peak queue
```

Metric tersebut membantu mengetahui bottleneck sistem dan kebutuhan scale-up.

---

# 39. Scalability

Versi pertama:

```text
1 bot
1 worker
1 Redis
1 PostgreSQL
```

Ketika traffic meningkat:

```text
1 bot
N workers
1 Redis
1 PostgreSQL
```

Jika diperlukan:

```text
Load Balancer
    ↓
Bot instance 1
Bot instance 2
Bot instance 3
    ↓
Redis
    ↓
Worker cluster
```

Conversion worker harus dibuat stateless sehingga dapat diperbanyak.

---

# 40. Definition of Done

Project dianggap selesai apabila:

- Bot Telegram berhasil dijalankan.
- `/start` berfungsi.
- Bot dapat menerima DOCX.
- Bot dapat mengubah DOCX menjadi PDF.
- Bot dapat menerima PDF.
- Bot dapat mengubah PDF menjadi DOCX.
- Hasil conversion dapat dikirim kembali melalui Telegram.
- Queue berjalan.
- Worker berjalan terpisah dari bot.
- File temporary dibersihkan.
- Rate limit aktif.
- Timeout aktif.
- Error handling aktif.
- Logging aktif.
- Database menyimpan metadata job.
- Docker deployment berhasil.
- `.env.example` tersedia.
- README berisi instalasi dan deployment.
- Unit test utama tersedia.
- Integration test conversion tersedia.
- Security test dasar lulus.

---

# 41. Rekomendasi MVP Final

Gunakan stack:

```text
Python 3.12+
aiogram 3.x
Redis
RQ
PostgreSQL
LibreOffice Headless
pdf2docx
Docker
Docker Compose
Linux VPS
```

Pipeline utama:

```text
Telegram
    ↓
aiogram
    ↓
Validator
    ↓
Redis Queue
    ↓
Worker
    ↓
LibreOffice / pdf2docx
    ↓
Output Validator
    ↓
Telegram
    ↓
Cleanup
```

Fokus MVP hanya pada:

```text
DOCX → PDF
PDF → DOCX
```

Setelah pipeline tersebut stabil, fitur seperti batch conversion, merge PDF, split PDF, OCR, compress PDF, dan premium quota dapat ditambahkan tanpa mengubah konsep inti arsitektur.

---

# 42. Catatan Implementasi Penting

Konversi DOCX → PDF sebaiknya tidak dilakukan langsung di proses handler Telegram karena proses conversion dapat memakan CPU/RAM dan menghambat bot ketika banyak pengguna mengirim file bersamaan.

Gunakan worker terpisah agar:

```text
Telegram Bot
```

tetap responsif sementara:

```text
Conversion Worker
```

menangani pekerjaan berat.

Untuk keamanan, setiap conversion harus dijalankan dalam environment terisolasi. File user diperlakukan sebagai untrusted input dan harus dihapus otomatis setelah job selesai.

Untuk PDF → DOCX, kualitas hasil sangat bergantung pada struktur PDF. MVP sebaiknya mengutamakan PDF digital berbasis teks dan menyediakan pesan bahwa layout kompleks atau hasil scan mungkin tidak identik dengan dokumen asli.

---

# 43. Roadmap

## Phase 1 — Core

```text
Bot setup
DOCX detection
PDF detection
DOCX → PDF
PDF → DOCX
Result delivery
```

## Phase 2 — Reliability

```text
Redis queue
Worker
Timeout
Retry
Cleanup
Logging
Rate limit
```

## Phase 3 — Production

```text
PostgreSQL
Docker
Monitoring
Admin tools
Metrics
Security hardening
```

## Phase 4 — Advanced

```text
Batch conversion
ZIP
Merge PDF
Split PDF
Compress PDF
OCR
Image → PDF
Premium quota
```

---

# 44. Final Product Vision

DocPDF Bot menjadi layanan konversi dokumen berbasis Telegram yang memungkinkan pengguna mengubah DOCX dan PDF secara praktis hanya dengan mengirim file ke bot.

Pengalaman yang dituju:

```text
Kirim file
     ↓
Bot validasi
     ↓
Bot memproses
     ↓
Hasil dikirim
     ↓
Temporary file dihapus
```

Tidak diperlukan aplikasi desktop di sisi pengguna, tidak diperlukan akun tambahan, dan seluruh proses dikendalikan melalui percakapan Telegram.
