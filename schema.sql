-- Garuda Talenta - Supabase schema
create extension if not exists pgcrypto;

create table if not exists public.players (
  id uuid primary key default gen_random_uuid(),
  name text not null,
  birth_date date,
  age_group text,
  position text,
  club text,
  province text,
  city text,
  photo_url text,
  bio text,
  source_name text,
  source_url text,
  status text not null default 'pending'
    check (status in ('pending','published','rejected')),
  verification_note text,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);

create index if not exists players_status_idx on public.players(status);
create index if not exists players_name_idx on public.players using gin (to_tsvector('simple', name));

alter table public.players enable row level security;

-- Public can only read published players.
drop policy if exists "public_read_published_players" on public.players;
create policy "public_read_published_players"
on public.players for select
to anon, authenticated
using (status = 'published');

-- Public contribution insert: only pending records.
drop policy if exists "public_submit_player" on public.players;
create policy "public_submit_player"
on public.players for insert
to anon, authenticated
with check (status = 'pending');

-- Updates/deletes should be performed by the server using the secret/service key,
-- not directly from the browser.
