# SIPPS Indonesia

**Sistem Informasi Pembinaan Pemain Sepakbola dari Usia Dini hingga Senior di Indonesia.**

Aplikasi Flask + Supabase yang dirancang sebagai platform kolaboratif: masyarakat dapat mengusulkan data pemain, sementara admin melakukan verifikasi sebelum data tampil secara publik.

## Fitur utama

- Landing page modern dan responsif.
- Direktori pemain terverifikasi.
- Pencarian berdasarkan nama/kota/klub.
- Filter provinsi, posisi, dan kelompok usia.
- Halaman profil pemain.
- Register/login melalui Supabase Auth.
- Form kontribusi masyarakat.
- Riwayat status kontribusi pengguna.
- Moderasi admin: verifikasi / tolak + alasan.
- API health check.
- Supabase Row Level Security (RLS).
- Vercel-ready dengan Python serverless function.
- Service-role key hanya dipakai server-side untuk operasi admin.

## 1. Supabase

Buat project di Supabase, lalu buka **SQL Editor** dan jalankan isi `schema.sql`.

Setelah akun admin pertama dibuat melalui `/register`, ambil UUID user dari Supabase Dashboard > Authentication > Users, lalu jalankan:

```sql
update public.profiles
set is_admin = true
where id = 'UUID-USER-ADMIN';
```

### Auth email

Jika ingin pengguna melakukan verifikasi email, aktifkan Email provider dan pengaturan email confirmation di Supabase Auth. URL redirect produksi sebaiknya diarahkan ke domain Vercel Anda.

## 2. Environment Variables

Di Vercel > Project > Settings > Environment Variables, tambahkan:

- `SUPABASE_URL`
- `SUPABASE_KEY`
- `SUPABASE_SERVICE_ROLE_KEY`
- `FLASK_SECRET_KEY`

Semua variabel ini dapat diset untuk Production/Preview/Development sesuai kebutuhan.

**Jangan pernah menaruh `SUPABASE_SERVICE_ROLE_KEY` di JavaScript frontend, HTML, atau repository publik.**

## 3. Local development

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
```

Isi `.env`, kemudian jalankan:

```bash
flask --app app run --debug
```

Windows:

```powershell
.venv\Scripts\activate
flask --app app run --debug
```

## 4. Deploy ke Vercel

Push project ke GitHub/GitLab, import repository ke Vercel, lalu pastikan environment variables sudah diisi.

Vercel akan menggunakan:

```text
api/index.py
```

sebagai entry point Python.

## Catatan arsitektur

- Browser -> Flask/Vercel -> Supabase.
- Supabase Auth menangani akun pengguna.
- Data publik hanya `status = verified`.
- Kontribusi masyarakat masuk sebagai `pending`.
- Admin menggunakan `SUPABASE_SERVICE_ROLE_KEY` dari server untuk moderasi.
- RLS tetap diaktifkan untuk tabel Supabase.

## Pengembangan lanjutan yang direkomendasikan

1. Upload foto melalui Supabase Storage, bukan URL manual.
2. Sistem audit log untuk setiap tindakan admin.
3. Role `moderator` selain `admin`.
4. Dashboard statistik pembinaan nasional.
5. Peta sebaran pemain per provinsi.
6. Import data massal CSV oleh admin.
7. Sistem laporan/koreksi data oleh masyarakat.
8. Notifikasi email ketika kontribusi diverifikasi/ditolak.
9. Verifikasi sumber berlapis untuk data sensitif.
10. Pagination server-side untuk direktori besar.
