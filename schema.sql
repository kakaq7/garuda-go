-- Jalankan di Supabase Dashboard > SQL Editor.
-- Backend Flask mengakses Supabase dari server, bukan dari browser.
create extension if not exists pgcrypto;

create table if not exists public.players (
  id uuid primary key default gen_random_uuid(),
  name text not null check (char_length(name) between 1 and 120),
  age integer not null check (age between 8 and 45),
  birth_year integer,
  position text,
  club text,
  province text,
  stage text,
  summary text not null check (char_length(summary) between 30 and 3000),
  source_name text,
  source_url text,
  submitter_email text,
  consent boolean not null default false,
  status text not null default 'pending' check (status in ('pending','published','rejected')),
  review_note text,
  reviewed_at timestamptz,
  created_at timestamptz not null default now()
);

create index if not exists players_status_created_idx on public.players(status, created_at desc);
create index if not exists players_province_idx on public.players(province);
create index if not exists players_stage_idx on public.players(stage);

alter table public.players enable row level security;
-- Pengunjung hanya dapat membaca profil yang sudah dipublikasikan.
drop policy if exists "Public can read published players" on public.players;
create policy "Public can read published players" on public.players
  for select to anon, authenticated using (status = 'published');
-- Opsi untuk server yang memakai anon key: publik hanya boleh mengirim kontribusi pending.
-- Jika backend memakai service_role key, key tersebut melewati RLS dan tidak boleh bocor ke browser.
drop policy if exists "Public can submit pending players" on public.players;
create policy "Public can submit pending players" on public.players
  for insert to anon, authenticated with check (status = 'pending' and consent = true);
-- Tidak ada policy update/delete untuk publik. Admin server harus memakai service_role key.
