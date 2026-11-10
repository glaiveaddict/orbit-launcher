create extension if not exists pgcrypto with schema extensions;

create table if not exists public.profiles (
  id uuid primary key references auth.users (id) on delete cascade,
  username text not null check (username ~ '^[A-Za-z0-9_]{3,20}$'),
  is_owner boolean not null default false,
  created_at timestamptz not null default now(),
  last_seen timestamptz not null default now()
);
create unique index if not exists profiles_username_key on public.profiles (lower(username));

create table if not exists public.redemptions (
  key_id text primary key check (key_id ~ '^[0-9a-f]{6,32}$'),
  user_id uuid not null references auth.users (id) on delete cascade,
  username text not null,
  key_for text,
  expires_at timestamptz,
  redeemed_at timestamptz not null default now(),
  disabled boolean not null default false,
  carried_over boolean not null default false
);
create index if not exists redemptions_user on public.redemptions (user_id);

create table if not exists public.key_log (
  id bigint generated always as identity primary key,
  at timestamptz not null default now(),
  event text not null,
  key_id text,
  username text,
  key_for text,
  detail text
);
create index if not exists key_log_at on public.key_log (at desc);

alter table public.profiles enable row level security;
alter table public.redemptions enable row level security;
alter table public.key_log enable row level security;

create or replace function public.is_owner() returns boolean
language sql stable security definer set search_path = public as $$
  select coalesce((select p.is_owner from public.profiles p where p.id = auth.uid()), false)
$$;

drop policy if exists profiles_read on public.profiles;
create policy profiles_read on public.profiles for select to authenticated using (id = auth.uid() or public.is_owner());
drop policy if exists redemptions_read on public.redemptions;
create policy redemptions_read on public.redemptions for select to authenticated using (user_id = auth.uid() or public.is_owner());
drop policy if exists key_log_read on public.key_log;
create policy key_log_read on public.key_log for select to authenticated using (public.is_owner());

revoke insert, update, delete, truncate on public.profiles, public.redemptions, public.key_log from anon, authenticated;
revoke all on public.profiles, public.redemptions, public.key_log from anon;

create or replace function public.handle_new_user() returns trigger
language plpgsql security definer set search_path = public as $$
declare
  uname text := new.raw_user_meta_data ->> 'username';
begin
  if uname is null or uname !~ '^[A-Za-z0-9_]{3,20}$' then
    raise exception 'bad username';
  end if;
  insert into public.profiles (id, username) values (new.id, uname);
  return new;
end
$$;
drop trigger if exists on_auth_user_created on auth.users;
create trigger on_auth_user_created after insert on auth.users for each row execute function public.handle_new_user();

create or replace function public.me() returns json
language plpgsql security definer set search_path = public as $$
declare
  p public.profiles;
begin
  update public.profiles set last_seen = now() where id = auth.uid() returning * into p;
  if not found then
    raise exception 'no account';
  end if;
  return json_build_object('id', p.id, 'username', p.username, 'owner', p.is_owner);
end
$$;

create or replace function public.key_status(p_key_id text) returns json
language plpgsql stable security definer set search_path = public as $$
declare
  r public.redemptions;
begin
  if auth.uid() is null then
    raise exception 'log in first';
  end if;
  select * into r from public.redemptions where key_id = p_key_id;
  if not found then
    return json_build_object('state', 'none');
  end if;
  if r.user_id <> auth.uid() then
    return json_build_object('state', 'taken');
  end if;
  return json_build_object('state', 'mine', 'disabled', r.disabled);
end
$$;

create or replace function public.redeem_key(p_key_id text, p_key_for text default null, p_expires_at timestamptz default null,
                                             p_carried boolean default false) returns json
language plpgsql security definer set search_path = public as $$
declare
  me uuid := auth.uid();
  uname text;
  r public.redemptions;
begin
  if me is null then
    raise exception 'log in first';
  end if;
  if p_key_id is null or p_key_id !~ '^[0-9a-f]{6,32}$' then
    raise exception 'bad key';
  end if;
  select username into uname from public.profiles where id = me;
  select * into r from public.redemptions where key_id = p_key_id for update;
  if found then
    if r.user_id = me then
      return json_build_object('ok', true, 'disabled', r.disabled, 'already', true);
    end if;
    insert into public.key_log (event, key_id, username, key_for, detail)
    values ('blocked', p_key_id, uname, coalesce(r.key_for, left(p_key_for, 40)), 'already used by ' || r.username);
    return json_build_object('ok', false, 'taken', true);
  end if;
  insert into public.redemptions (key_id, user_id, username, key_for, expires_at, carried_over)
  values (p_key_id, me, uname, left(p_key_for, 40), p_expires_at, coalesce(p_carried, false));
  insert into public.key_log (event, key_id, username, key_for, detail)
  values (case when p_carried then 'carried_over' else 'redeemed' end, p_key_id, uname, left(p_key_for, 40), null);
  return json_build_object('ok', true, 'disabled', false);
end
$$;

create or replace function public.owner_log(p_search text default '', p_limit int default 300) returns setof public.key_log
language plpgsql stable security definer set search_path = public as $$
begin
  if not public.is_owner() then
    raise exception 'owner only';
  end if;
  return query
    select * from public.key_log l
    where coalesce(p_search, '') = ''
       or l.username ilike '%' || p_search || '%'
       or l.key_for ilike '%' || p_search || '%'
       or l.key_id ilike p_search || '%'
    order by l.at desc
    limit least(greatest(coalesce(p_limit, 300), 1), 1000);
end
$$;

create or replace function public.owner_users(p_search text default '') returns json
language plpgsql stable security definer set search_path = public as $$
begin
  if not public.is_owner() then
    raise exception 'owner only';
  end if;
  return coalesce((
    select json_agg(u order by u.last_seen desc)
    from (
      select p.username, p.created_at, p.last_seen, p.is_owner,
             coalesce((select json_agg(json_build_object('key_id', r.key_id, 'key_for', r.key_for, 'disabled', r.disabled,
                                                         'redeemed_at', r.redeemed_at, 'expires_at', r.expires_at,
                                                         'carried_over', r.carried_over) order by r.redeemed_at desc)
                       from public.redemptions r where r.user_id = p.id), '[]'::json) as keys
      from public.profiles p
      where coalesce(p_search, '') = '' or p.username ilike '%' || p_search || '%'
         or exists (select 1 from public.redemptions r where r.user_id = p.id and (r.key_for ilike '%' || p_search || '%' or r.key_id ilike p_search || '%'))
      order by p.last_seen desc
      limit 100
    ) u
  ), '[]'::json);
end
$$;

create or replace function public.owner_set_key(p_key_id text, p_disabled boolean) returns json
language plpgsql security definer set search_path = public as $$
declare
  r public.redemptions;
begin
  if not public.is_owner() then
    raise exception 'owner only';
  end if;
  update public.redemptions set disabled = p_disabled where key_id = p_key_id returning * into r;
  if not found then
    raise exception 'no such key';
  end if;
  insert into public.key_log (event, key_id, username, key_for, detail)
  values (case when p_disabled then 'disabled' else 'enabled' end, r.key_id, r.username, r.key_for, null);
  return json_build_object('key_id', r.key_id, 'disabled', r.disabled);
end
$$;

create or replace function public.owner_clear_log() returns int
language plpgsql security definer set search_path = public as $$
declare
  n int;
begin
  if not public.is_owner() then
    raise exception 'owner only';
  end if;
  delete from public.key_log where true;
  get diagnostics n = row_count;
  return n;
end
$$;

create or replace function public.owner_reset_password(p_username text, p_password text) returns boolean
language plpgsql security definer set search_path = public, extensions as $$
declare
  uid uuid;
begin
  if not public.is_owner() then
    raise exception 'owner only';
  end if;
  if length(coalesce(p_password, '')) < 6 then
    raise exception 'password too short';
  end if;
  select id into uid from public.profiles where lower(username) = lower(p_username);
  if uid is null then
    raise exception 'no such user';
  end if;
  update auth.users set encrypted_password = extensions.crypt(p_password, extensions.gen_salt('bf')), updated_at = now() where id = uid;
  return true;
end
$$;

revoke execute on function public.is_owner(), public.me(), public.key_status(text), public.redeem_key(text, text, timestamptz, boolean),
  public.owner_log(text, int), public.owner_users(text), public.owner_set_key(text, boolean), public.owner_clear_log(),
  public.owner_reset_password(text, text), public.handle_new_user() from public, anon;
grant execute on function public.is_owner(), public.me(), public.key_status(text), public.redeem_key(text, text, timestamptz, boolean),
  public.owner_log(text, int), public.owner_users(text), public.owner_set_key(text, boolean), public.owner_clear_log(),
  public.owner_reset_password(text, text) to authenticated;

-- ============================================================================
-- v2.16: Orbit profiles, Friends on Orbit and the playtime leaderboard.
-- Safe to run again: it only adds what's missing.
-- ============================================================================
alter table public.profiles add column if not exists roblox_id bigint;
alter table public.profiles add column if not exists roblox_name text;
alter table public.profiles add column if not exists bio text;
alter table public.profiles add column if not exists badges text[] not null default '{}';
alter table public.profiles add column if not exists total_seconds bigint not null default 0;
alter table public.profiles add column if not exists week_seconds int not null default 0;
alter table public.profiles add column if not exists week_start date;
alter table public.profiles add column if not exists level int not null default 1;
alter table public.profiles add column if not exists level_title text;
alter table public.profiles add column if not exists top_games jsonb not null default '[]';
alter table public.profiles add column if not exists now_playing jsonb;
alter table public.profiles add column if not exists playing_at timestamptz;
alter table public.profiles add column if not exists public_profile boolean not null default true;
alter table public.profiles add column if not exists on_leaderboard boolean not null default true;
alter table public.profiles add column if not exists share_activity boolean not null default true;
create index if not exists profiles_roblox on public.profiles (roblox_id);
create index if not exists profiles_total on public.profiles (total_seconds desc);

create or replace function public._has_premium(p_uid uuid) returns boolean
language sql stable security definer set search_path = public as $$
  select exists (select 1 from public.redemptions r where r.user_id = p_uid and not r.disabled
                 and (r.expires_at is null or r.expires_at > now()))
$$;

create or replace function public._badges(p_uid uuid, p_owner boolean, p_extra text[]) returns text[]
language sql stable security definer set search_path = public as $$
  select array_remove(array[case when p_owner then 'founder' end,
                            case when public._has_premium(p_uid) then 'premium' end], null) || coalesce(p_extra, '{}')
$$;

create or replace function public._this_week() returns date
language sql stable as $$ select (date_trunc('week', now()))::date $$;

create or replace function public.sync_profile(p jsonb) returns json
language plpgsql security definer set search_path = public as $$
declare
  me uuid := auth.uid();
  games jsonb := '[]'::jsonb;
  g jsonb;
  ws date;
  playing jsonb;
begin
  if me is null then
    raise exception 'log in first';
  end if;
  for g in select value from jsonb_array_elements(case when jsonb_typeof(p -> 'top_games') = 'array' then p -> 'top_games' else '[]'::jsonb end) limit 5 loop
    if (g ->> 'pid') ~ '^[0-9]{1,15}$' then
      games := games || jsonb_build_array(jsonb_build_object('pid', g ->> 'pid', 'name', left(coalesce(g ->> 'name', 'Game'), 60),
                                                             'seconds', least(greatest(coalesce((g ->> 'seconds')::numeric, 0), 0), 315360000)::bigint));
    end if;
  end loop;
  ws := case when (p ->> 'week_start') ~ '^\d{4}-\d{2}-\d{2}$' then (p ->> 'week_start')::date end;
  if ws is not null and (ws > current_date + 1 or ws < current_date - 8) then
    ws := null;
  end if;
  if jsonb_typeof(p -> 'now_playing') = 'object' and (p -> 'now_playing' ->> 'place_id') ~ '^[0-9]{1,15}$' then
    playing := jsonb_build_object('place_id', p -> 'now_playing' ->> 'place_id', 'name', left(coalesce(p -> 'now_playing' ->> 'name', 'a game'), 60));
  end if;
  update public.profiles set
    roblox_id = case when (p ->> 'roblox_id') ~ '^[0-9]{1,15}$' then (p ->> 'roblox_id')::bigint else roblox_id end,
    roblox_name = case when (p ->> 'roblox_name') ~ '^[A-Za-z0-9_]{3,20}$' then p ->> 'roblox_name' else roblox_name end,
    bio = case when p ? 'bio' then nullif(left(regexp_replace(coalesce(p ->> 'bio', ''), '[\r\n\t]+', ' ', 'g'), 120), '') else bio end,
    total_seconds = least(greatest(coalesce((p ->> 'total_seconds')::numeric, total_seconds), 0), 315360000)::bigint,
    week_seconds = case when ws is null then week_seconds else least(greatest(coalesce((p ->> 'week_seconds')::numeric, 0), 0), 604800)::int end,
    week_start = coalesce(ws, week_start),
    level = least(greatest(coalesce((p ->> 'level')::int, level), 1), 999),
    level_title = coalesce(left(p ->> 'level_title', 24), level_title),
    top_games = games,
    now_playing = case when coalesce((p ->> 'share_activity')::boolean, share_activity) then playing end,
    playing_at = case when playing is not null then now() else playing_at end,
    public_profile = coalesce((p ->> 'public_profile')::boolean, public_profile),
    on_leaderboard = coalesce((p ->> 'on_leaderboard')::boolean, on_leaderboard),
    share_activity = coalesce((p ->> 'share_activity')::boolean, share_activity),
    last_seen = now()
  where id = me;
  return json_build_object('ok', true);
end
$$;

create or replace function public.get_profile(p_username text) returns json
language plpgsql stable security definer set search_path = public as $$
declare
  p public.profiles;
  mine boolean;
  rank_all int;
begin
  if auth.uid() is null then
    raise exception 'log in first';
  end if;
  select * into p from public.profiles where lower(username) = lower(p_username);
  if not found then
    return json_build_object('found', false);
  end if;
  mine := p.id = auth.uid();
  if not (p.public_profile or mine or public.is_owner()) then
    return json_build_object('found', true, 'private', true, 'username', p.username);
  end if;
  select count(*) + 1 into rank_all from public.profiles q
   where q.on_leaderboard and q.total_seconds > p.total_seconds;
  return json_build_object(
    'found', true, 'private', false, 'mine', mine, 'username', p.username, 'created_at', p.created_at,
    'last_seen', p.last_seen, 'online', p.last_seen > now() - interval '5 minutes',
    'roblox_id', p.roblox_id, 'roblox_name', p.roblox_name, 'bio', p.bio, 'badges', public._badges(p.id, p.is_owner, p.badges),
    'total_seconds', p.total_seconds,
    'week_seconds', case when p.week_start = public._this_week() then p.week_seconds else 0 end,
    'level', p.level, 'level_title', p.level_title, 'top_games', p.top_games,
    'rank', case when p.on_leaderboard and p.total_seconds > 0 then rank_all end,
    'now_playing', case when p.share_activity and p.playing_at > now() - interval '5 minutes' then p.now_playing end,
    'public_profile', p.public_profile, 'on_leaderboard', p.on_leaderboard, 'share_activity', p.share_activity);
end
$$;

create or replace function public.leaderboard(p_period text default 'all', p_limit int default 50) returns json
language plpgsql stable security definer set search_path = public as $$
declare
  wk date := public._this_week();
  rows json;
  mine json;
begin
  if auth.uid() is null then
    raise exception 'log in first';
  end if;
  with board as (
    select p.*, case when p_period = 'week' then (case when p.week_start = wk then p.week_seconds else 0 end)::bigint
                     else p.total_seconds end as secs
    from public.profiles p where p.on_leaderboard
  ), ranked as (
    select b.*, rank() over (order by b.secs desc) as pos from board b where b.secs > 0
  )
  select coalesce(json_agg(json_build_object('rank', r.pos, 'username', r.username, 'roblox_id', r.roblox_id, 'level', r.level,
                                             'seconds', r.secs, 'badges', public._badges(r.id, r.is_owner, r.badges), 'me', r.id = auth.uid()) order by r.pos, r.username), '[]'::json)
    into rows
    from (select * from ranked order by pos, username limit least(greatest(coalesce(p_limit, 50), 1), 100)) r;
  with board as (
    select p.*, case when p_period = 'week' then (case when p.week_start = wk then p.week_seconds else 0 end)::bigint
                     else p.total_seconds end as secs
    from public.profiles p where p.on_leaderboard
  )
  select json_build_object('rank', (select count(*) + 1 from board b2 where b2.secs > b.secs), 'username', b.username,
                           'roblox_id', b.roblox_id, 'level', b.level, 'seconds', b.secs, 'badges', public._badges(b.id, b.is_owner, b.badges), 'me', true)
    into mine from board b where b.id = auth.uid() and b.secs > 0;
  return json_build_object('period', p_period, 'rows', rows, 'me', mine,
                           'players', (select count(*) from public.profiles where on_leaderboard and total_seconds > 0));
end
$$;

create or replace function public.friends_on_orbit(p_roblox_ids bigint[]) returns json
language plpgsql stable security definer set search_path = public as $$
begin
  if auth.uid() is null then
    raise exception 'log in first';
  end if;
  return coalesce((
    select json_agg(json_build_object(
      'username', p.username, 'roblox_id', p.roblox_id, 'level', p.level, 'badges', public._badges(p.id, p.is_owner, p.badges),
      'last_seen', p.last_seen, 'online', p.last_seen > now() - interval '5 minutes',
      'now_playing', case when p.share_activity and p.playing_at > now() - interval '5 minutes' then p.now_playing end)
      order by p.playing_at desc nulls last, p.last_seen desc)
    from public.profiles p
    where p.roblox_id = any (p_roblox_ids[1:300]) and p.id <> auth.uid() and p.public_profile
  ), '[]'::json);
end
$$;

create or replace function public.owner_set_badges(p_username text, p_badges text[]) returns json
language plpgsql security definer set search_path = public as $$
declare
  clean text[];
begin
  if not public.is_owner() then
    raise exception 'owner only';
  end if;
  select coalesce(array_agg(distinct b), '{}') into clean from unnest(p_badges) b
   where b in ('beta', 'og', 'staff', 'creator', 'bug_hunter', 'verified', 'supporter');
  update public.profiles set badges = clean where lower(username) = lower(p_username);
  if not found then
    raise exception 'no such user';
  end if;
  return json_build_object('username', p_username, 'badges', clean);
end
$$;

revoke execute on function public._has_premium(uuid), public._badges(uuid, boolean, text[]), public.sync_profile(jsonb),
  public.get_profile(text), public.leaderboard(text, int), public.friends_on_orbit(bigint[]),
  public.owner_set_badges(text, text[]) from public, anon;
grant execute on function public.sync_profile(jsonb), public.get_profile(text), public.leaderboard(text, int),
  public.friends_on_orbit(bigint[]), public.owner_set_badges(text, text[]) to authenticated;

-- ============================================================================
-- v2.16.1: change your Orbit username. Your login follows the new name.
-- Safe to run again.
-- ============================================================================
alter table public.profiles add column if not exists username_changed_at timestamptz;

create or replace function public.username_available(p_username text) returns json
language plpgsql stable security definer set search_path = public as $$
declare
  me uuid := auth.uid();
  owner_id uuid;
begin
  if me is null then
    raise exception 'log in first';
  end if;
  if p_username is null or p_username !~ '^[A-Za-z0-9_]{3,20}$' then
    return json_build_object('ok', false, 'reason', 'invalid');
  end if;
  select id into owner_id from public.profiles where lower(username) = lower(p_username);
  if owner_id is null then
    return json_build_object('ok', true);
  end if;
  if owner_id = me then
    if exists (select 1 from public.profiles where id = me and username = p_username) then
      return json_build_object('ok', false, 'reason', 'yours');
    end if;
    return json_build_object('ok', true, 'case_only', true);
  end if;
  return json_build_object('ok', false, 'reason', 'taken');
end
$$;

create or replace function public.change_username(p_username text) returns json
language plpgsql security definer set search_path = public, auth as $$
declare
  me uuid := auth.uid();
  avail json;
  old_name text;
  domain text;
  new_email text;
begin
  if me is null then
    raise exception 'log in first';
  end if;
  avail := public.username_available(p_username);
  if not (avail ->> 'ok')::boolean then
    return avail;
  end if;
  select username into old_name from public.profiles where id = me for update;
  select coalesce(nullif(split_part(email, '@', 2), ''), 'players.orbit.invalid') into domain from auth.users where id = me;
  new_email := lower(p_username) || '@' || domain;
  begin
    update public.profiles set username = p_username, username_changed_at = now() where id = me;
    update auth.users set email = new_email, updated_at = now(),
           raw_user_meta_data = coalesce(raw_user_meta_data, '{}'::jsonb) || jsonb_build_object('username', p_username)
     where id = me;
    update auth.identities set identity_data = coalesce(identity_data, '{}'::jsonb) || jsonb_build_object('email', new_email), updated_at = now()
     where user_id = me and provider = 'email';
  exception when unique_violation then
    return json_build_object('ok', false, 'reason', 'taken');
  end;
  update public.redemptions set username = p_username where user_id = me;
  insert into public.key_log (event, username, detail) values ('renamed', p_username, 'was ' || old_name);
  return json_build_object('ok', true, 'username', p_username, 'old', old_name);
end
$$;

revoke execute on function public.username_available(text), public.change_username(text) from public, anon;
grant execute on function public.username_available(text), public.change_username(text) to authenticated;

-- ============================================================================
-- v2.16.2: username automod. Blocks bad words and names that pretend to be staff
-- (owner, admin, mod...). Checked here on the server, so a modded Orbit can't skip it.
-- Safe to run again. The owner can add or remove words from the Owner panel.
-- ============================================================================
create table if not exists public.blocked_words (
  word text primary key check (word ~ '^[a-z]{2,24}$'),
  kind text not null check (kind in ('bad', 'reserved')),
  match text not null default 'anywhere' check (match in ('anywhere', 'word', 'whole')),
  added_at timestamptz not null default now()
);
alter table public.blocked_words enable row level security;
revoke all on public.blocked_words from anon, authenticated;

-- anywhere = inside any name ("xXfuckXx"); word = as its own piece of the name ("Mod_Jake", "TheMod", "mod123")
-- so normal names like "Modern" or "Classic" stay fine; whole = only the entire name ("Orbit").
insert into public.blocked_words (word, kind, match) values
  ('fuck','bad','anywhere'), ('fuk','bad','anywhere'), ('fvck','bad','anywhere'), ('shit','bad','anywhere'),
  ('bitch','bad','anywhere'), ('cunt','bad','anywhere'), ('nigger','bad','anywhere'), ('nigga','bad','anywhere'),
  ('faggot','bad','anywhere'), ('fagot','bad','anywhere'), ('retard','bad','anywhere'), ('whore','bad','anywhere'),
  ('slut','bad','anywhere'), ('rape','bad','anywhere'), ('rapist','bad','anywhere'), ('porn','bad','anywhere'),
  ('penis','bad','anywhere'), ('vagina','bad','anywhere'), ('pussy','bad','anywhere'), ('dildo','bad','anywhere'),
  ('hitler','bad','anywhere'), ('nazi','bad','anywhere'), ('kkk','bad','anywhere'), ('molest','bad','anywhere'),
  ('tranny','bad','anywhere'), ('jizz','bad','anywhere'), ('hentai','bad','anywhere'), ('horny','bad','anywhere'),
  ('milf','bad','anywhere'), ('bastard','bad','anywhere'), ('twat','bad','anywhere'), ('boob','bad','anywhere'),
  ('cock','bad','word'), ('dick','bad','word'), ('ass','bad','word'), ('asshole','bad','anywhere'), ('sex','bad','word'),
  ('cum','bad','word'), ('tits','bad','word'), ('hoe','bad','word'), ('fag','bad','word'), ('pedo','bad','word'),
  ('kys','bad','word'), ('chink','bad','word'), ('spic','bad','word'), ('wank','bad','word'), ('anal','bad','word'),
  ('prick','bad','word'), ('negro','bad','word'),
  ('admin','reserved','anywhere'), ('administrator','reserved','anywhere'), ('owner','reserved','anywhere'),
  ('moderator','reserved','anywhere'), ('official','reserved','anywhere'), ('developer','reserved','anywhere'),
  ('founder','reserved','anywhere'), ('staff','reserved','anywhere'), ('helpdesk','reserved','anywhere'),
  ('stabzane','reserved','anywhere'),
  ('mod','reserved','word'), ('mods','reserved','word'), ('dev','reserved','word'), ('support','reserved','word'),
  ('ceo','reserved','word'), ('orbitteam','reserved','anywhere'),
  ('orbit','reserved','whole'), ('roblox','reserved','whole'), ('system','reserved','whole'), ('orbitlauncher','reserved','whole')
on conflict (word) do nothing;

create or replace function public._leet(t text) returns text
language sql immutable as $$ select translate(lower(coalesce(t, '')), '013457@$8!|', 'oieastasbii') $$;

-- Returns {"word": ..., "kind": "bad"|"reserved"} for the first rule a name breaks, or null.
create or replace function public._name_rule(p_name text, p_kinds text[] default array['bad', 'reserved']) returns json
language plpgsql stable security definer set search_path = public as $$
declare
  spaced text := regexp_replace(regexp_replace(coalesce(p_name, ''), '([a-z])([A-Z])', '\1_\2', 'g'), '([A-Za-z])([0-9])|([0-9])([A-Za-z])', '\1\3_\2\4', 'g');
  flat text := replace(public._leet(p_name), '_', '');
  squashed text;
  bare text := regexp_replace(lower(coalesce(p_name, '')), '[^a-z]', '', 'g');
  parts text[];
  r record;
begin
  squashed := regexp_replace(flat, '(.)\1+', '\1', 'g');
  parts := regexp_split_to_array(lower(spaced), '[^a-z0-9]+') || regexp_split_to_array(lower(spaced), '[^a-z]+')
        || regexp_split_to_array(public._leet(spaced), '[^a-z]+')
        || regexp_split_to_array(public._leet(regexp_replace(coalesce(p_name, ''), '([a-z])([A-Z])', '\1_\2', 'g')), '[^a-z]+');
  for r in select w.word, w.kind, w.match from public.blocked_words w where w.kind = any (p_kinds) order by length(w.word) desc loop
    if (r.match = 'anywhere' and (position(r.word in flat) > 0 or position(r.word in squashed) > 0 or position(r.word in bare) > 0))
       or (r.match = 'word' and r.word = any (parts))
       or (r.match = 'whole' and (r.word = flat or r.word = bare or r.word = squashed)) then
      return json_build_object('word', r.word, 'kind', r.kind);
    end if;
  end loop;
  return null;
end
$$;

create or replace function public._bio_rule(p_bio text) returns json
language plpgsql stable security definer set search_path = public as $$
declare
  words text[] := regexp_split_to_array(public._leet(p_bio), '[^a-z]+');
  flat text := regexp_replace(public._leet(p_bio), '[^a-z]', '', 'g');
  r record;
begin
  for r in select w.word, w.match from public.blocked_words w where w.kind = 'bad' loop
    if (r.match = 'anywhere' and position(r.word in flat) > 0) or (r.match <> 'anywhere' and r.word = any (words)) then
      return json_build_object('word', r.word);
    end if;
  end loop;
  return null;
end
$$;

create or replace function public.handle_new_user() returns trigger
language plpgsql security definer set search_path = public as $$
declare
  uname text := new.raw_user_meta_data ->> 'username';
begin
  if uname is null or uname !~ '^[A-Za-z0-9_]{3,20}$' then
    raise exception 'bad username';
  end if;
  if public._name_rule(uname) is not null then
    raise exception 'username not allowed';
  end if;
  insert into public.profiles (id, username) values (new.id, uname);
  return new;
end
$$;

-- Lets the sign-up screen say "not allowed" or "taken" before trying, instead of a generic error.
create or replace function public.signup_check(p_username text) returns json
language plpgsql stable security definer set search_path = public as $$
declare
  rule json;
begin
  if p_username is null or p_username !~ '^[A-Za-z0-9_]{3,20}$' then
    return json_build_object('ok', false, 'reason', 'invalid');
  end if;
  rule := public._name_rule(p_username);
  if rule is not null then
    return json_build_object('ok', false, 'reason', case when rule ->> 'kind' = 'reserved' then 'reserved' else 'blocked' end);
  end if;
  if exists (select 1 from public.profiles where lower(username) = lower(p_username)) then
    return json_build_object('ok', false, 'reason', 'taken');
  end if;
  return json_build_object('ok', true);
end
$$;

create or replace function public.username_available(p_username text) returns json
language plpgsql stable security definer set search_path = public as $$
declare
  me uuid := auth.uid();
  owner_id uuid;
  rule json;
begin
  if me is null then
    raise exception 'log in first';
  end if;
  if p_username is null or p_username !~ '^[A-Za-z0-9_]{3,20}$' then
    return json_build_object('ok', false, 'reason', 'invalid');
  end if;
  select id into owner_id from public.profiles where lower(username) = lower(p_username);
  if owner_id is not null and owner_id <> me then
    return json_build_object('ok', false, 'reason', 'taken');
  end if;
  if owner_id = me and exists (select 1 from public.profiles where id = me and username = p_username) then
    return json_build_object('ok', false, 'reason', 'yours');
  end if;
  rule := public._name_rule(p_username, case when public.is_owner() then array['bad'] else array['bad', 'reserved'] end);
  if rule is not null then
    return json_build_object('ok', false, 'reason', case when rule ->> 'kind' = 'reserved' then 'reserved' else 'blocked' end);
  end if;
  if owner_id = me then
    return json_build_object('ok', true, 'case_only', true);
  end if;
  return json_build_object('ok', true);
end
$$;

-- Bios get the bad-word check too (staff words are fine in a bio).
create or replace function public.check_bio(p_bio text) returns json
language sql stable security definer set search_path = public as $$
  select json_build_object('ok', public._bio_rule(p_bio) is null)
$$;

create or replace function public._enforce_bio() returns trigger
language plpgsql security definer set search_path = public as $$
begin
  if new.bio is distinct from old.bio and new.bio is not null and public._bio_rule(new.bio) is not null then
    new.bio := old.bio;
  end if;
  return new;
end
$$;
drop trigger if exists profiles_bio_automod on public.profiles;
create trigger profiles_bio_automod before update of bio on public.profiles for each row execute function public._enforce_bio();

-- Owner tools: edit the word list, find accounts whose names break the rules, and rename them.
create or replace function public.owner_words() returns json
language plpgsql stable security definer set search_path = public as $$
begin
  if not public.is_owner() then raise exception 'owner only'; end if;
  return coalesce((select json_agg(json_build_object('word', word, 'kind', kind, 'match', match) order by kind, word) from public.blocked_words), '[]'::json);
end
$$;

create or replace function public.owner_word_set(p_word text, p_kind text, p_match text, p_remove boolean default false) returns json
language plpgsql security definer set search_path = public as $$
declare
  w text := regexp_replace(lower(coalesce(p_word, '')), '[^a-z]', '', 'g');
begin
  if not public.is_owner() then raise exception 'owner only'; end if;
  if p_remove then
    delete from public.blocked_words where word = w;
  else
    if w !~ '^[a-z]{2,24}$' then raise exception 'word must be 2 to 24 letters'; end if;
    insert into public.blocked_words (word, kind, match) values (w, coalesce(p_kind, 'bad'), coalesce(p_match, 'anywhere'))
    on conflict (word) do update set kind = excluded.kind, match = excluded.match;
  end if;
  return json_build_object('ok', true, 'word', w);
end
$$;

create or replace function public.owner_name_test(p_name text) returns json
language plpgsql stable security definer set search_path = public as $$
begin
  if not public.is_owner() then raise exception 'owner only'; end if;
  return coalesce(public._name_rule(p_name), json_build_object('ok', true));
end
$$;

create or replace function public.owner_bad_names() returns json
language plpgsql stable security definer set search_path = public as $$
begin
  if not public.is_owner() then raise exception 'owner only'; end if;
  return coalesce((
    select json_agg(json_build_object('username', p.username, 'word', r ->> 'word', 'kind', r ->> 'kind', 'last_seen', p.last_seen) order by p.last_seen desc)
    from public.profiles p, lateral (select public._name_rule(p.username) as r) x
    where not p.is_owner and r is not null
  ), '[]'::json);
end
$$;

create or replace function public.owner_force_rename(p_username text) returns json
language plpgsql security definer set search_path = public, auth as $$
declare
  uid uuid;
  old_name text;
  new_name text;
  domain text;
begin
  if not public.is_owner() then raise exception 'owner only'; end if;
  select id, username into uid, old_name from public.profiles where lower(username) = lower(p_username) and not is_owner;
  if uid is null then raise exception 'no such user'; end if;
  loop
    new_name := 'Player' || (floor(random() * 9000000) + 1000000)::int;
    exit when not exists (select 1 from public.profiles where lower(username) = lower(new_name));
  end loop;
  select coalesce(nullif(split_part(email, '@', 2), ''), 'players.orbit.invalid') into domain from auth.users where id = uid;
  update public.profiles set username = new_name, username_changed_at = now() where id = uid;
  update auth.users set email = lower(new_name) || '@' || domain, updated_at = now(),
         raw_user_meta_data = coalesce(raw_user_meta_data, '{}'::jsonb) || jsonb_build_object('username', new_name) where id = uid;
  update auth.identities set identity_data = coalesce(identity_data, '{}'::jsonb) || jsonb_build_object('email', lower(new_name) || '@' || domain), updated_at = now()
   where user_id = uid and provider = 'email';
  update public.redemptions set username = new_name where user_id = uid;
  insert into public.key_log (event, username, detail) values ('force_renamed', new_name, 'was ' || old_name);
  return json_build_object('ok', true, 'username', new_name, 'old', old_name);
end
$$;

revoke execute on function public._leet(text), public._name_rule(text, text[]), public._bio_rule(text), public._enforce_bio(),
  public.signup_check(text), public.check_bio(text), public.owner_words(), public.owner_word_set(text, text, text, boolean),
  public.owner_name_test(text), public.owner_bad_names(), public.owner_force_rename(text) from public, anon;
grant execute on function public.signup_check(text) to anon, authenticated;
grant execute on function public.check_bio(text), public.owner_words(), public.owner_word_set(text, text, text, boolean),
  public.owner_name_test(text), public.owner_bad_names(), public.owner_force_rename(text) to authenticated;
