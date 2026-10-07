# Flask + Supabase + Vercel

Website Flask sederhana untuk menambahkan data nama dan email ke tabel `users` di Supabase.

## Struktur

- `api/index.py` - aplikasi Flask
- `templates/index.html` - form HTML
- `requirements.txt` - dependency Python
- `vercel.json` - konfigurasi Vercel
- `supabase.sql` - SQL untuk membuat tabel
- `.env.example` - contoh environment variable

## Setup Supabase

1. Buka Supabase.
2. Masuk ke SQL Editor.
3. Jalankan isi `supabase.sql`.

## Lokal

Buat virtual environment:

```bash
python -m venv venv
```

Aktifkan:

Windows:
```bash
venv\Scripts\activate
```

Linux/macOS:
```bash
source venv/bin/activate
```

Install dependency:

```bash
pip install -r requirements.txt
```

Salin `.env.example` menjadi `.env`, lalu isi:

```env
SUPABASE_URL=https://YOUR_PROJECT.supabase.co
SUPABASE_KEY=YOUR_SUPABASE_KEY
```

Jalankan:

```bash
python api/index.py
```

Buka `http://127.0.0.1:5000`.

## Deploy ke Vercel

Push project ke GitHub lalu import repository tersebut ke Vercel.

Di Vercel, tambahkan Environment Variables:

- `SUPABASE_URL`
- `SUPABASE_KEY`

Jangan commit file `.env` atau membagikan key rahasia.

Untuk backend, gunakan key Supabase yang sesuai untuk server-side access dan jangan menaruh secret key di HTML/JavaScript browser.
