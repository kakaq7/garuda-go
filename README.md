# Garuda Talenta — Sistem Informasi Pembinaan Sepak Bola

Aplikasi Flask berbahasa Indonesia untuk menghimpun profil dan informasi pemain sepak bola Indonesia dari usia dini hingga senior. Kontribusi masyarakat masuk sebagai **pending** dan hanya dapat tampil setelah admin menerbitkannya.

## Fitur

- Landing page modern, responsif, dan berbahasa Indonesia.
- Direktori pemain publik dengan pencarian dan filter fase, provinsi, dan posisi.
- Halaman detail pemain serta informasi sumber yang dapat dibuka.
- Form kontribusi dengan validasi, persetujuan, tautan sumber, dan honeypot anti-spam sederhana.
- Panel admin untuk menerbitkan, menunda, atau menolak kontribusi, dengan catatan review.
- Status privasi: email kontributor hanya terlihat di panel admin, tidak di halaman publik.
- Supabase sebagai database; halaman demo fallback bila Supabase belum dikonfigurasi.
- Endpoint `/health` untuk pemeriksaan sederhana.

## Struktur proyek

```text
app.py                 Aplikasi Flask dan rute
api/index.py           Entry point WSGI Vercel
templates/             Template Jinja HTML
static/css/style.css   Desain responsif
static/js/main.js      Navigasi mobile dan flash message
supabase/schema.sql    Skema tabel dan kebijakan RLS
vercel.json            Konfigurasi deploy Vercel
requirements.txt       Dependensi Python
.env.example           Contoh environment variable
```

## 1. Siapkan Supabase

1. Buat project di Supabase.
2. Buka **SQL Editor**, jalankan seluruh isi `supabase/schema.sql`.
3. Salin Project URL dan server-side key dari **Project Settings → API**.
4. Simpan key hanya sebagai environment variable server di Vercel. Jangan pernah menaruh `service_role` key di HTML, JavaScript, repositori publik, atau variabel berawalan `NEXT_PUBLIC_`.

**Penting tentang key:** aplikasi membutuhkan hak akses untuk membaca antrean pending dan mengubah status review. Karena itu, gunakan `SUPABASE_KEY` berupa **service_role/secret key hanya di lingkungan server** untuk pengalaman admin penuh. Key ini melewati RLS; jangan sampai terekspos ke browser. Jika hanya menggunakan anon/publishable key, kebijakan RLS membatasi akses publik dengan baik, tetapi panel admin tidak akan bisa membaca semua antrean atau memperbarui status tanpa rancangan autentikasi admin berbasis Supabase yang lebih lengkap.

## 2. Konfigurasi environment variable

Di Vercel, buka **Project → Settings → Environment Variables**, lalu tambahkan untuk Production (dan Preview bila diperlukan):

- `SUPABASE_URL` — URL project Supabase.
- `SUPABASE_KEY` — server-side secret/service role key.
- `FLASK_SECRET_KEY` — string acak panjang dan rahasia.
- `ADMIN_USERNAME` — nama pengguna panel admin.
- `ADMIN_PASSWORD_HASH` — hash kata sandi admin (disarankan).

Untuk membuat hash secara lokal:

```bash
python -c "from werkzeug.security import generate_password_hash; print(generate_password_hash('GANTI_DENGAN_PASSWORD_KUAT'))"
```

Salin hasilnya ke `ADMIN_PASSWORD_HASH`. Bila `ADMIN_PASSWORD_HASH` diisi, aplikasi akan menggunakannya. Alternatif setup cepat adalah `ADMIN_PASSWORD` dalam bentuk teks biasa, tetapi **tidak disarankan** untuk produksi. Ganti username dan password bawaan; jangan gunakan password contoh.

## 3. Deploy ke Vercel

1. Ekstrak ZIP ini, lalu push seluruh folder proyek ke repository Git.
2. Di Vercel, pilih **Add New → Project** dan impor repository tersebut.
3. Tambahkan environment variable di atas.
4. Deploy. Konfigurasi `vercel.json` memakai Python runtime Vercel dan entry point `api/index.py`.
5. Setelah deploy, uji `/health`, `/pemain`, `/kontribusi`, dan `/admin/masuk`.

Jika Anda sudah memiliki project Vercel yang mengatur `SUPABASE_URL` dan `SUPABASE_KEY`, pastikan kedua variabel tersedia pada environment deployment yang sedang diuji, lalu tambahkan variabel Flask/admin lainnya.

## 4. Jalankan lokal

Python 3.10+ direkomendasikan.

```bash
python -m venv .venv
# Windows: .venv\\Scripts\\activate
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env  # isi nilainya, lalu ekspor variabel ke shell atau gunakan dotenv runner
python app.py
```

Buka `http://127.0.0.1:5000`. Flask tidak membaca `.env` secara otomatis dalam konfigurasi ini; ekspor variabel ke shell, atau tambahkan `python-dotenv` dan pemanggilan `load_dotenv()` bila ingin memuat `.env` langsung.

## Catatan penting sebelum produksi

- Data contoh di mode fallback hanya untuk pratinjau dan **tidak persisten** pada serverless. Pastikan Supabase tersambung sebelum menerima kontribusi sungguhan.
- Gunakan `FLASK_SECRET_KEY` acak, HTTPS, password hash, backup database, rate limiting/CAPTCHA, log audit, dan prosedur respons insiden.
- Untuk mengurangi risiko spam, tambahkan rate limit di lapisan edge/server dan verifikasi sumber yang lebih kuat.
- Profil pemain muda membutuhkan kehati-hatian khusus. Jangan publikasikan kontak pribadi, alamat, dokumen identitas, data kesehatan, lokasi rutin, atau informasi sensitif anak. Dapatkan izin yang sesuai dari wali/pihak berwenang sebelum mengolah data anak dan siapkan kebijakan privasi serta proses koreksi/penghapusan.
- Sistem ini bukan sistem scouting resmi dan tidak menyatakan afiliasi dengan PSSI atau federasi mana pun. Data publik perlu ditinjau manusia dan dapat salah.
- Saat ini autentikasi admin menggunakan satu akun berbasis environment variable. Untuk penggunaan organisasi, tingkatkan menjadi multi-admin, MFA, role-based access, audit log, dan perlindungan CSRF.

## Routes

- `/` — Beranda
- `/pemain` — Direktori dan filter
- `/pemain/<id>` — Detail pemain terbit
- `/kontribusi` — Formulir kontribusi publik
- `/tentang` — Misi, verifikasi, dan privasi
- `/admin/masuk` — Login admin
- `/admin` — Antrean verifikasi (login diperlukan)
- `/health` — Status aplikasi dan konfigurasi database
