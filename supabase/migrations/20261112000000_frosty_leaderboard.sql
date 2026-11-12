-- FROSTY worldwide leaderboard. Only the server-side Edge Function can read/write profiles.
create table if not exists public.frosty_players (
 id bigint generated always as identity primary key,
 token_hash text not null unique check (length(token_hash) = 64),
 name text not null check (char_length(name) between 2 and 18),
 best_score integer not null default 0 check (best_score >= 0),
 created_at timestamptz not null default now(),
 updated_at timestamptz not null default now(),
 last_score_at timestamptz
);
create unique index if not exists frosty_players_unique_name_ci on public.frosty_players (lower(name));
create index if not exists frosty_players_best_score_idx on public.frosty_players (best_score desc, updated_at asc);
alter table public.frosty_players enable row level security;
revoke all on table public.frosty_players from anon, authenticated;
