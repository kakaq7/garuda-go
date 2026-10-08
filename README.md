# CRUD Flask + Supabase + Vercel

Template CRUD sederhana menggunakan:

- Python Flask
- Supabase sebagai database PostgreSQL melalui Supabase Python client
- Vercel Python runtime
- HTML + CSS tanpa framework frontend

## 1. Buat database Supabase

1. Buat project di Supabase.
2. Buka **SQL Editor**.
3. Jalankan isi `supabase/schema.sql`.
4. Buka **Project Settings > API**.
5. Salin:
   - Project URL
   - anon/public key

> Jangan masukkan `service_role` key ke frontend. Untuk aplikasi production, gunakan arsitektur dan RLS yang sesuai kebutuhan keamanan Anda.

## 2. Jalankan lokal

Buat virtual environment:

```bash
python -m venv .venv
```

Aktifkan:

Windows:
```bash
.venv\Scripts\activate
```

macOS/Linux:
```bash
source .venv/bin/activate
```

Install dependency:

```bash
pip install -r requirements.txt
```

Salin `.env.example` menjadi `.env`, lalu isi:

```env
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_KEY=your-supabase-anon-key
FLASK_SECRET_KEY=ganti-dengan-secret-random
```

Jalankan:

```bash
flask --app app run --debug
```

Buka `http://127.0.0.1:5000`.

## 3. Deploy ke Vercel

### Opsi A — GitHub

1. Upload project ini ke repository GitHub.
2. Login ke Vercel.
3. Pilih **Add New > Project**.
4. Import repository.
5. Deploy.
6. Setelah project dibuat, buka **Settings > Environment Variables**.
7. Tambahkan:
   - `SUPABASE_URL`
   - `SUPABASE_KEY`
   - `FLASK_SECRET_KEY`
8. Redeploy.

`vercel.json` dan `api/index.py` sudah disiapkan untuk Flask.

### Opsi B — Vercel CLI

Install CLI:

```bash
npm i -g vercel
```

Login:

```bash
vercel login
```

Dari folder project:

```bash
vercel
```

Tambahkan environment variables melalui dashboard Vercel atau CLI, lalu deploy production:

```bash
vercel --prod
```

## 4. Struktur project

```text
flask-supabase-vercel-crud/
├── api/
│   └── index.py
├── static/
│   └── style.css
├── templates/
│   ├── base.html
│   ├── index.html
│   └── edit.html
├── supabase/
│   └── schema.sql
├── .env.example
├── .gitignore
├── app.py
├── requirements.txt
├── vercel.json
└── README.md
```

## 5. Fitur

- Create data
- Read/list data
- Update data
- Delete data
- Flash message
- Health check di `/health`
- Responsive sederhana
- Siap untuk deployment serverless Vercel

## Catatan keamanan

Contoh SQL mengaktifkan policy publik agar template mudah diuji. Untuk aplikasi production, jangan membuka operasi CRUD ke role `anon` tanpa autentikasi/otorisasi yang tepat. Gunakan Supabase Auth dan Row Level Security (RLS) sesuai kebutuhan aplikasi.
