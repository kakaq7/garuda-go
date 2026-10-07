# Supabase Vercel Health Check

Dashboard sederhana untuk mengetes Supabase dari Vercel:
- Environment variables
- PostgreSQL/database query
- Supabase Auth
- Supabase Storage

## 1. Siapkan database

Buka Supabase > SQL Editor, lalu jalankan isi `supabase-test.sql`.

## 2. Environment variables

Di Vercel > Project > Settings > Environment Variables tambahkan:

`SUPABASE_URL`
`SUPABASE_SERVICE_ROLE_KEY`

Jangan commit service role key ke GitHub dan jangan expose key ini di frontend.

## 3. Deploy

Hubungkan repository ke Vercel atau gunakan:

```bash
vercel
vercel --prod
```

Setelah deploy buka:

`https://PROJECT.vercel.app/`

Endpoint JSON:

`https://PROJECT.vercel.app/api/health`

## 4. Local test

Buat virtual environment, install dependency, lalu set environment variables.

Windows PowerShell:

```powershell
$env:SUPABASE_URL="https://YOUR_PROJECT.supabase.co"
$env:SUPABASE_SERVICE_ROLE_KEY="YOUR_SERVICE_ROLE_KEY"
python api/index.py
```

macOS/Linux:

```bash
export SUPABASE_URL="https://YOUR_PROJECT.supabase.co"
export SUPABASE_SERVICE_ROLE_KEY="YOUR_SERVICE_ROLE_KEY"
python api/index.py
```

Buka http://localhost:5000
