-- SIPPS Indonesia / Supabase schema
create extension if not exists pgcrypto;

create type public.player_status as enum ('pending', 'verified', 'rejected');

create table if not exists public.profiles (
  id uuid primary key references auth.users(id) on delete cascade,
  display_name text,
  is_admin boolean not null default false,
  created_at timestamptz not null default now()
);

create table if not exists public.players (
  id uuid primary key default gen_random_uuid(),
  full_name text not null,
  slug text unique,
  birth_year integer,
  age_group text not null,
  position text not null,
  city text,
  province text not null,
  club_name text,
  photo_url text,
  short_bio text,
  source_url text,
  evidence_notes text,
  submitted_by uuid not null references public.profiles(id) on delete restrict,
  verified_by uuid references public.profiles(id) on delete set null,
  status public.player_status not null default 'pending',
  rejection_reason text,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);

create index if not exists players_status_idx on public.players(status);
create index if not exists players_province_idx on public.players(province);
create index if not exists players_age_group_idx on public.players(age_group);
create index if not exists players_position_idx on public.players(position);

create or replace function public.make_player_slug()
returns trigger language plpgsql as $$
begin
  if new.slug is null or new.slug = '' then
    new.slug := lower(regexp_replace(
      regexp_replace(new.full_name, '[^a-zA-Z0-9 ]', '', 'g'),
      '\s+', '-', 'g'
    )) || '-' || substr(replace(new.id::text, '-', ''), 1, 8);
  end if;
  new.updated_at := now();
  return new;
end;
$$;

drop trigger if exists trg_players_slug on public.players;
create trigger trg_players_slug
before insert or update on public.players
for each row execute function public.make_player_slug();

-- Create profile automatically after Supabase Auth registration.
create or replace function public.handle_new_user()
returns trigger
language plpgsql
security definer set search_path = public
as $$
begin
  insert into public.profiles (id, display_name)
  values (new.id, coalesce(new.raw_user_meta_data->>'display_name', split_part(new.email, '@', 1)))
  on conflict (id) do nothing;
  return new;
end;
$$;

drop trigger if exists on_auth_user_created on auth.users;
create trigger on_auth_user_created
after insert on auth.users
for each row execute procedure public.handle_new_user();

alter table public.profiles enable row level security;
alter table public.players enable row level security;

-- Public can only read verified player data.
drop policy if exists "Public read verified players" on public.players;
create policy "Public read verified players"
on public.players for select
using (status = 'verified');

-- Logged-in users can create pending submissions.
drop policy if exists "Authenticated submit players" on public.players;
create policy "Authenticated submit players"
on public.players for insert to authenticated
with check (submitted_by = auth.uid() and status = 'pending');

-- Contributors can read their own submissions.
drop policy if exists "Users read own submissions" on public.players;
create policy "Users read own submissions"
on public.players for select to authenticated
using (submitted_by = auth.uid() or status = 'verified');

-- Users can update their own pending submissions if desired by future UI.
drop policy if exists "Users update own pending submissions" on public.players;
create policy "Users update own pending submissions"
on public.players for update to authenticated
using (submitted_by = auth.uid() and status = 'pending')
with check (submitted_by = auth.uid() and status = 'pending');

drop policy if exists "Users read own profile" on public.profiles;
create policy "Users read own profile"
on public.profiles for select to authenticated
using (id = auth.uid());

-- Admin mutations are intentionally performed server-side using SERVICE_ROLE_KEY.
-- IMPORTANT: protect SUPABASE_SERVICE_ROLE_KEY and never expose it in frontend JS.

-- After registering your first admin account, promote it:
-- update public.profiles set is_admin = true where id = 'YOUR-AUTH-USER-UUID';
