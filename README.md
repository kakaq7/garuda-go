# CRUD Flask + Supabase Auth + Admin Approval + Vercel

Alur:
1. User register/login.
2. Hanya user login yang dapat CRUD.
3. Data baru berstatus `pending`.
4. Data pending/rejected tidak tampil di halaman umum.
5. Admin membuka `/admin` untuk approve/reject.
6. Hanya `approved` yang tampil.
7. Jika user mengedit data approved, status kembali `pending`.
8. Admin dapat mengedit tanpa mengubah status.

## Supabase
Jalankan `supabase/schema.sql` di SQL Editor.

Aktifkan Authentication > Providers > Email.

Setelah register akun yang akan menjadi admin, jalankan:
```sql
update public.profiles set role='admin'
where email='admin@example.com';
```

## Environment
```env
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_KEY=your-supabase-anon-key
SUPABASE_SERVICE_ROLE_KEY=your-supabase-service-role-key
FLASK_SECRET_KEY=long-random-secret
```

`SUPABASE_SERVICE_ROLE_KEY` hanya boleh berada di server/Vercel Environment Variables. Jangan masukkan ke frontend atau GitHub.

## Lokal
```bash
python -m venv .venv
# Windows: .venv\Scripts\activate
# macOS/Linux: source .venv/bin/activate
pip install -r requirements.txt
flask --app app run --debug
```

## Vercel
Import repository ke Vercel dan tambahkan ke Environment Variables:
- SUPABASE_URL
- SUPABASE_KEY
- SUPABASE_SERVICE_ROLE_KEY
- FLASK_SECRET_KEY

Kemudian deploy. `vercel.json` dan `api/index.py` sudah disiapkan.

Untuk production, pertimbangkan CSRF protection, rate limiting, audit log, pagination, email verification, password reset, dan RLS yang lebih granular.
