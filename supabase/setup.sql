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
  return json_build_object('id', p.id, 'username', p.username, 'owner', p.is_owner,
    'banned', coalesce(p.banned_until > now(), false), 'banned_until', p.banned_until, 'ban_reason', p.ban_reason,
    'tester', p.is_owner or 'beta' = any (coalesce(p.badges, '{}')));
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
  if public._is_banned(me) then
    return json_build_object('ok', false, 'banned', true);
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
    showcase = case when p ? 'showcase' then public._clean_showcase(p -> 'showcase') else showcase end,
    status_at = case when p ? 'status' and nullif(left(regexp_replace(coalesce(p ->> 'status', ''), '[\r\n\t]+', ' ', 'g'), 60), '') is distinct from status then now() else status_at end,
    status = case when p ? 'status' then nullif(trim(left(regexp_replace(coalesce(p ->> 'status', ''), '[\r\n\t]+', ' ', 'g'), 60)), '') else status end,
    socials = case when p ? 'socials' then public._clean_socials(p -> 'socials') else socials end,
    socials_visibility = case when p ->> 'socials_visibility' in ('nobody', 'friends', 'crew', 'everyone') then p ->> 'socials_visibility' else socials_visibility end,
    friend_ids = case when jsonb_typeof(p -> 'friend_ids') = 'array'
                      then (select array_agg(x::bigint) from (select jsonb_array_elements_text(p -> 'friend_ids') x limit 1000) f where x ~ '^[0-9]{1,15}$')
                      else friend_ids end,
    achievements = case when jsonb_typeof(p -> 'achievements') = 'array'
                        then (select array_agg(x) from (select jsonb_array_elements_text(p -> 'achievements') x limit 100) a where x ~ '^[a-z0-9_]{2,30}$')
                        else achievements end,
    app_version = case when (p ->> 'app_version') ~ '^[0-9]+\.[0-9]+\.[0-9]+(-[a-z]+\.?[0-9]*)?$' then p ->> 'app_version' else app_version end,
    banner = case when p ? 'banner' then public._clean_banner(me, p ->> 'banner') else banner end,
    name_style = case when p ? 'name_style' then public._clean_name_style(me, p ->> 'name_style') else name_style end,
    last_seen = now()
  where id = me;
  insert into public.profile_days (user_id, day) values (me, current_date) on conflict do nothing;
  if ws is not null then
    insert into public.profile_weeks (user_id, week, seconds) values (me, ws, least(greatest(coalesce((p ->> 'week_seconds')::numeric, 0), 0), 604800)::int)
    on conflict (user_id, week) do update set seconds = excluded.seconds;
  end if;
  if (p ->> 'month_start') ~ '^\d{4}-\d{2}-01$' and (p ->> 'month_start')::date between (current_date - 40) and (current_date + 1) then
    insert into public.profile_months (user_id, month, seconds, games)
    values (me, (p ->> 'month_start')::date, least(greatest(coalesce((p ->> 'month_seconds')::numeric, 0), 0), 2678400)::int, public._clean_games(p -> 'month_games'))
    on conflict (user_id, month) do update set seconds = excluded.seconds, games = excluded.games;
  end if;
  return json_build_object('ok', true);
end
$$;

create or replace function public.get_profile(p_username text) returns json
language plpgsql security definer set search_path = public as $$
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
  if public._is_banned(p.id) and not (mine or public.is_owner()) then
    return json_build_object('found', true, 'private', true, 'banned', true, 'username', p.username);
  end if;
  if not (p.public_profile or mine or public.is_owner()) then
    return json_build_object('found', true, 'private', true, 'username', p.username);
  end if;
  select count(*) + 1 into rank_all from public.profiles q
   where q.on_leaderboard and q.total_seconds > p.total_seconds and not public._is_banned(q.id);
  if not mine and not public._is_banned(auth.uid()) then
    insert into public.profile_views (viewer, target, day) values (auth.uid(), p.id, current_date) on conflict do nothing;
    if random() < 0.02 then delete from public.profile_views where day < current_date - 30; end if;
  end if;
  return json_build_object(
    'found', true, 'private', false, 'mine', mine, 'username', p.username, 'created_at', p.created_at,
    'last_seen', p.last_seen, 'online', p.last_seen > now() - interval '5 minutes',
    'roblox_id', p.roblox_id, 'roblox_name', p.roblox_name, 'bio', p.bio, 'badges', public._badges(p.id, p.is_owner, p.badges),
    'total_seconds', p.total_seconds,
    'week_seconds', case when p.week_start = public._this_week() then p.week_seconds else 0 end,
    'level', p.level, 'level_title', p.level_title, 'top_games', p.top_games,
    'rank', case when p.on_leaderboard and p.total_seconds > 0 then rank_all end,
    'now_playing', case when p.share_activity and p.playing_at > now() - interval '5 minutes' then p.now_playing end,
    'public_profile', p.public_profile, 'on_leaderboard', p.on_leaderboard, 'share_activity', p.share_activity,
    'crew', public._crew_tag(p.id), 'banner', p.banner, 'name_style', p.name_style, 'showcase', coalesce(p.showcase, '[]'::jsonb),
    'banned', public._is_banned(p.id), 'ban_reason', case when public.is_owner() then p.ban_reason end,
    'status', p.status, 'status_at', p.status_at,
    'socials', case when mine or public.is_owner() or p.socials_visibility = 'everyone'
                         or (p.socials_visibility = 'crew' and public._crew_tag(p.id) is not null
                             and exists (select 1 from public.crew_members a join public.crew_members b on a.crew_id = b.crew_id
                                          where a.user_id = p.id and b.user_id = auth.uid()))
                         or (p.socials_visibility = 'friends' and (select v.roblox_id from public.profiles v where v.id = auth.uid()) = any (coalesce(p.friend_ids, '{}')))
                    then coalesce(p.socials, '{}'::jsonb) end,
    'socials_visibility', case when mine then coalesce(p.socials_visibility, 'nobody') end,
    'visitors_week', case when mine then (select count(distinct viewer) from public.profile_views v where v.target = p.id and v.day > current_date - 7) end,
    'visitors_total', case when mine then (select count(distinct viewer) from public.profile_views v where v.target = p.id) end);
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
    from public.profiles p where p.on_leaderboard and not public._is_banned(p.id)
  ), ranked as (
    select b.*, rank() over (order by b.secs desc) as pos from board b where b.secs > 0
  )
  select coalesce(json_agg(json_build_object('rank', r.pos, 'username', r.username, 'roblox_id', r.roblox_id, 'level', r.level,
                                             'seconds', r.secs, 'badges', public._badges(r.id, r.is_owner, r.badges), 'me', r.id = auth.uid(),
                                             'crew', public._crew_tag(r.id), 'name_style', r.name_style) order by r.pos, r.username), '[]'::json)
    into rows
    from (select * from ranked order by pos, username limit least(greatest(coalesce(p_limit, 50), 1), 100)) r;
  with board as (
    select p.*, case when p_period = 'week' then (case when p.week_start = wk then p.week_seconds else 0 end)::bigint
                     else p.total_seconds end as secs
    from public.profiles p where p.on_leaderboard and not public._is_banned(p.id)
  )
  select json_build_object('rank', (select count(*) + 1 from board b2 where b2.secs > b.secs), 'username', b.username,
                           'roblox_id', b.roblox_id, 'level', b.level, 'seconds', b.secs, 'badges', public._badges(b.id, b.is_owner, b.badges), 'me', true,
                           'crew', public._crew_tag(b.id), 'name_style', b.name_style)
    into mine from board b where b.id = auth.uid() and b.secs > 0;
  return json_build_object('period', p_period, 'rows', rows, 'me', mine,
                           'players', (select count(*) from public.profiles q where q.on_leaderboard and q.total_seconds > 0 and not public._is_banned(q.id)));
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
      'now_playing', case when p.share_activity and p.playing_at > now() - interval '5 minutes' then p.now_playing end,
      'crew', public._crew_tag(p.id), 'name_style', p.name_style, 'status', p.status)
      order by p.playing_at desc nulls last, p.last_seen desc)
    from public.profiles p
    where p.roblox_id = any (p_roblox_ids[1:300]) and p.id <> auth.uid() and p.public_profile and not public._is_banned(p.id)
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
  update public.profiles set badges = clean || coalesce(array(select b from unnest(badges) b
           where b not in ('beta', 'og', 'staff', 'creator', 'bug_hunter', 'verified', 'supporter')), '{}')
   where lower(username) = lower(p_username);
  if not found then
    raise exception 'no such user';
  end if;
  perform public._notify(p.id, 'badge', 'You got a new badge!', 'Check your profile to see it.', '{"page":"social"}'::jsonb)
     from public.profiles p where lower(p.username) = lower(p_username) and clean && array['beta', 'og', 'staff', 'creator', 'bug_hunter', 'verified', 'supporter'];
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

alter table public.blocked_words add column if not exists chat_ok boolean not null default false;
drop function if exists public._bio_rule(text);
create or replace function public._bio_rule(p_bio text, p_swears_ok boolean default false) returns json
language plpgsql stable security definer set search_path = public as $$
declare
  words text[] := regexp_split_to_array(public._leet(p_bio), '[^a-z]+');
  flat text := regexp_replace(public._leet(p_bio), '[^a-z]', '', 'g');
  r record;
begin
  for r in select w.word, w.match from public.blocked_words w where w.kind = 'bad' and not (p_swears_ok and w.chat_ok) loop
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

revoke execute on function public._leet(text), public._name_rule(text, text[]), public._bio_rule(text, boolean), public._enforce_bio(),
  public.signup_check(text), public.check_bio(text), public.owner_words(), public.owner_word_set(text, text, text, boolean),
  public.owner_name_test(text), public.owner_bad_names(), public.owner_force_rename(text) from public, anon;
grant execute on function public.signup_check(text) to anon, authenticated;
grant execute on function public.check_bio(text), public.owner_words(), public.owner_word_set(text, text, text, boolean),
  public.owner_name_test(text), public.owner_bad_names(), public.owner_force_rename(text) to authenticated;

-- ============================================================================
-- v2.17.0: reports, account bans, feedback, crews, profile showcase.
-- Safe to run again.
-- ============================================================================
alter table public.profiles add column if not exists banned_until timestamptz;
alter table public.profiles add column if not exists ban_reason text;
alter table public.profiles add column if not exists banner text;
alter table public.profiles add column if not exists name_style text;
alter table public.profiles add column if not exists showcase jsonb not null default '[]';

create or replace function public._is_banned(p_uid uuid) returns boolean
language sql stable security definer set search_path = public as $$
  select exists (select 1 from public.profiles where id = p_uid and banned_until is not null and banned_until > now())
$$;

create or replace function public._active() returns uuid
language plpgsql stable security definer set search_path = public as $$
declare
  me uuid := auth.uid();
begin
  if me is null then raise exception 'log in first'; end if;
  if public._is_banned(me) then raise exception 'account banned'; end if;
  return me;
end
$$;

-- ---------- Profile showcase ----------
create or replace function public._clean_showcase(p jsonb) returns jsonb
language plpgsql immutable as $$
declare
  out jsonb := '[]'::jsonb;
  a jsonb;
begin
  if jsonb_typeof(p) <> 'array' then return out; end if;
  for a in select value from jsonb_array_elements(p) loop
    exit when jsonb_array_length(out) >= 3;
    if (a ->> 'id') ~ '^[a-z0-9_]{2,30}$' then
      out := out || jsonb_build_array(jsonb_build_object('id', a ->> 'id', 'title', left(coalesce(a ->> 'title', ''), 30),
                                                         'icon', left(coalesce(a ->> 'icon', ''), 8)));
    end if;
  end loop;
  return out;
end
$$;

alter table public.profiles add column if not exists unlocks text[] not null default '{}';
create or replace function public._clean_banner(p_uid uuid, p_banner text) returns text
language sql stable security definer set search_path = public as $$
  select case when p_banner in ('nebula', 'aurora', 'sunset', 'ocean', 'void', 'crimson', 'forest') then p_banner
              when p_banner in ('gold', 'galaxy', 'holo') and (public._has_premium(p_uid) or exists (select 1 from public.profiles where id = p_uid and is_owner)) then p_banner
              when ('banner:' || p_banner) = any (coalesce((select unlocks from public.profiles where id = p_uid), '{}')) then p_banner
              else null end
$$;

create or replace function public._clean_name_style(p_uid uuid, p_style text) returns text
language sql stable security definer set search_path = public as $$
  select case when p_style in ('gold', 'rainbow', 'aurora', 'fire')
                   and (public._has_premium(p_uid) or exists (select 1 from public.profiles where id = p_uid and is_owner)) then p_style
              when ('name:' || p_style) = any (coalesce((select unlocks from public.profiles where id = p_uid), '{}')) then p_style
              else null end
$$;

-- ---------- Crews ----------
create table if not exists public.crews (
  id uuid primary key default gen_random_uuid(),
  name text not null,
  tag text not null,
  code text not null,
  leader uuid references auth.users (id) on delete set null,
  created_at timestamptz not null default now()
);
create unique index if not exists crews_tag_key on public.crews (lower(tag));
create unique index if not exists crews_name_key on public.crews (lower(name));
create unique index if not exists crews_code_key on public.crews (code);
create table if not exists public.crew_members (
  user_id uuid primary key references auth.users (id) on delete cascade,
  crew_id uuid not null references public.crews (id) on delete cascade,
  joined_at timestamptz not null default now()
);
create index if not exists crew_members_crew on public.crew_members (crew_id);
alter table public.crews enable row level security;
alter table public.crew_members enable row level security;
revoke all on public.crews, public.crew_members from anon, authenticated;

create or replace function public._crew_tag(p_uid uuid) returns text
language sql stable security definer set search_path = public as $$
  select c.tag from public.crew_members m join public.crews c on c.id = m.crew_id where m.user_id = p_uid
$$;

create or replace function public._crew_code() returns text
language sql volatile as $$
  select string_agg(substr('ABCDEFGHJKLMNPQRSTUVWXYZ23456789', 1 + floor(random() * 32)::int, 1), '') from generate_series(1, 6)
$$;

create or replace function public._crew_name_problem(p_name text, p_tag text) returns text
language plpgsql stable security definer set search_path = public as $$
declare
  kinds text[] := case when public.is_owner() then array['bad'] else array['bad', 'reserved'] end;
begin
  if p_name is null or p_name !~ '^[A-Za-z0-9][A-Za-z0-9 ]{1,22}[A-Za-z0-9]$' then return 'name'; end if;
  if p_tag is null or p_tag !~ '^[A-Za-z0-9]{2,5}$' then return 'tag'; end if;
  if public._name_rule(replace(p_name, ' ', '_'), kinds) is not null or public._bio_rule(p_name) is not null
     or public._name_rule(p_tag, kinds) is not null then
    return 'blocked';
  end if;
  return null;
end
$$;

create or replace function public.crew_create(p_name text, p_tag text) returns json
language plpgsql security definer set search_path = public as $$
declare
  me uuid := public._active();
  problem text;
  cid uuid;
begin
  p_name := regexp_replace(trim(coalesce(p_name, '')), '\s+', ' ', 'g');
  p_tag := upper(trim(coalesce(p_tag, '')));
  if exists (select 1 from public.crew_members where user_id = me) then
    return json_build_object('ok', false, 'reason', 'in_crew');
  end if;
  problem := public._crew_name_problem(p_name, p_tag);
  if problem is not null then
    return json_build_object('ok', false, 'reason', problem);
  end if;
  begin
    insert into public.crews (name, tag, code, leader) values (p_name, p_tag, public._crew_code(), me) returning id into cid;
  exception when unique_violation then
    return json_build_object('ok', false, 'reason', 'taken');
  end;
  insert into public.crew_members (user_id, crew_id) values (me, cid);
  return json_build_object('ok', true, 'tag', p_tag);
end
$$;

create or replace function public.crew_join(p_code text) returns json
language plpgsql security definer set search_path = public as $$
declare
  me uuid := public._active();
  c public.crews;
begin
  if exists (select 1 from public.crew_members where user_id = me) then
    return json_build_object('ok', false, 'reason', 'in_crew');
  end if;
  select * into c from public.crews where code = upper(trim(coalesce(p_code, '')));
  if not found then
    return json_build_object('ok', false, 'reason', 'no_crew');
  end if;
  if (select count(*) from public.crew_members where crew_id = c.id) >= 50 then
    return json_build_object('ok', false, 'reason', 'full');
  end if;
  insert into public.crew_members (user_id, crew_id) values (me, c.id);
  perform public._notify(c.leader, 'crew', (select username from public.profiles where id = me) || ' joined [' || c.tag || ']', 'Say hi in crew chat!', '{"page":"social","tab":"crew"}'::jsonb);
  return json_build_object('ok', true, 'tag', c.tag, 'name', c.name);
end
$$;

create or replace function public.crew_leave() returns json
language plpgsql security definer set search_path = public as $$
declare
  me uuid := auth.uid();
  c public.crews;
  heir uuid;
begin
  if me is null then raise exception 'log in first'; end if;
  select c2.* into c from public.crews c2 join public.crew_members m on m.crew_id = c2.id where m.user_id = me;
  if not found then return json_build_object('ok', true); end if;
  delete from public.crew_members where user_id = me;
  if c.leader = me then
    select user_id into heir from public.crew_members where crew_id = c.id order by joined_at limit 1;
    if heir is null then
      delete from public.crews where id = c.id;
      return json_build_object('ok', true, 'disbanded', true);
    end if;
    update public.crews set leader = heir where id = c.id;
  end if;
  return json_build_object('ok', true);
end
$$;

create or replace function public._my_led_crew() returns uuid
language plpgsql stable security definer set search_path = public as $$
declare
  cid uuid;
begin
  select id into cid from public.crews where leader = public._active();
  if cid is null then raise exception 'crew leader only'; end if;
  return cid;
end
$$;

create or replace function public.crew_kick(p_username text) returns json
language plpgsql security definer set search_path = public as $$
declare
  cid uuid := public._my_crew_staff();
  leader uuid := (select leader from public.crews where id = cid);
  target uuid;
  trole text;
begin
  select p.id, m.role into target, trole from public.profiles p join public.crew_members m on m.user_id = p.id
   where lower(p.username) = lower(p_username) and m.crew_id = cid and p.id <> auth.uid();
  if target is null then return json_build_object('ok', false, 'reason', 'not_member'); end if;
  if target = leader or (auth.uid() <> leader and trole = 'officer') then return json_build_object('ok', false, 'reason', 'not_allowed'); end if;
  delete from public.crew_members where user_id = target;
  perform public._notify(target, 'crew', 'You were removed from [' || (select tag from public.crews where id = cid) || ']', null, '{"page":"social","tab":"crew"}'::jsonb);
  return json_build_object('ok', true);
end
$$;

create or replace function public.crew_new_code() returns json
language plpgsql security definer set search_path = public as $$
declare
  cid uuid := public._my_crew_staff();
  c text;
begin
  loop
    c := public._crew_code();
    exit when not exists (select 1 from public.crews where code = c);
  end loop;
  update public.crews set code = c where id = cid;
  return json_build_object('ok', true, 'code', c);
end
$$;

create or replace function public.crew_disband() returns json
language plpgsql security definer set search_path = public as $$
begin
  delete from public.crews where id = public._my_led_crew();
  return json_build_object('ok', true);
end
$$;

create or replace function public.crew_info(p_tag text default null) returns json
language plpgsql security definer set search_path = public as $$
declare
  me uuid := auth.uid();
  c public.crews;
  wk date := public._this_week();
  members json;
  tot bigint;
  wsum bigint;
  pos int;
begin
  if me is null then raise exception 'log in first'; end if;
  perform public._settle_crew_wars();
  if p_tag is null then
    select c2.* into c from public.crews c2 join public.crew_members m on m.crew_id = c2.id where m.user_id = me;
  else
    select * into c from public.crews where lower(tag) = lower(p_tag);
  end if;
  if not found then return json_build_object('found', false); end if;
  select coalesce(json_agg(json_build_object('username', p.username, 'roblox_id', p.roblox_id, 'level', p.level,
           'seconds', p.total_seconds, 'week_seconds', case when p.week_start = wk then p.week_seconds else 0 end,
           'leader', p.id = c.leader, 'badges', public._badges(p.id, p.is_owner, p.badges), 'name_style', p.name_style,
           'online', p.last_seen > now() - interval '5 minutes', 'status', p.status, 'role', m.role)
           order by (p.id = c.leader) desc, (m.role = 'officer') desc, p.total_seconds desc), '[]'::json),
         coalesce(sum(p.total_seconds), 0), coalesce(sum(case when p.week_start = wk then p.week_seconds else 0 end), 0)
    into members, tot, wsum
    from public.crew_members m join public.profiles p on p.id = m.user_id
   where m.crew_id = c.id and not public._is_banned(p.id);
  select count(*) + 1 into pos from (
    select m.crew_id, sum(p.total_seconds) s from public.crew_members m join public.profiles p on p.id = m.user_id
     where not public._is_banned(p.id) group by m.crew_id) x where x.s > tot;
  return json_build_object('found', true, 'name', c.name, 'tag', c.tag, 'created_at', c.created_at,
    'leader', (select username from public.profiles where id = c.leader), 'is_leader', c.leader = me,
    'mine', exists (select 1 from public.crew_members where user_id = me and crew_id = c.id),
    'code', case when c.leader = me or public.is_owner() or exists (select 1 from public.crew_members x where x.crew_id = c.id and x.user_id = me and x.role = 'officer') then c.code end,
    'is_officer', exists (select 1 from public.crew_members x where x.crew_id = c.id and x.user_id = me and x.role = 'officer'),
    'members', members, 'member_count', json_array_length(members), 'total_seconds', tot, 'week_seconds', wsum, 'rank', pos,
    'trophies', (select count(*) from public.crew_wars w where w.crew_id = c.id),
    'wins', coalesce((select json_agg(json_build_object('week', w.week, 'seconds', w.seconds) order by w.week desc) from (select * from public.crew_wars w where w.crew_id = c.id order by week desc limit 8) w), '[]'::json));
end
$$;

create or replace function public.crew_board(p_period text default 'all') returns json
language plpgsql security definer set search_path = public as $$
declare
  wk date := public._this_week();
  mine uuid;
  rows json;
begin
  if auth.uid() is null then raise exception 'log in first'; end if;
  perform public._settle_crew_wars();
  select crew_id into mine from public.crew_members where user_id = auth.uid();
  with t as (
    select c.id, c.name, c.tag, count(*) as n,
           sum(case when p_period = 'week' then (case when p.week_start = wk then p.week_seconds else 0 end) else p.total_seconds end) as secs
      from public.crews c join public.crew_members m on m.crew_id = c.id join public.profiles p on p.id = m.user_id
     where not public._is_banned(p.id) group by c.id
  ), r as (select t.*, rank() over (order by secs desc) as pos from t where secs > 0)
  select coalesce(json_agg(json_build_object('rank', pos, 'name', name, 'tag', tag, 'members', n, 'seconds', secs, 'mine', id = mine,
           'trophies', (select count(*) from public.crew_wars w where w.crew_id = z.id)) order by pos, name), '[]'::json)
    into rows from (select * from r order by pos limit 50) z;
  return json_build_object('period', p_period, 'rows', rows, 'crews', (select count(*) from public.crews),
    'war_ends', (wk + 7)::timestamp at time zone 'UTC',
    'last_winner', (select json_build_object('tag', w.tag, 'name', w.name, 'seconds', w.seconds, 'week', w.week) from public.crew_wars w
                     where w.crew_id is not null or w.tag is not null order by w.week desc limit 1));
end
$$;

-- ---------- Reports ----------
create table if not exists public.reports (
  id bigint generated always as identity primary key,
  at timestamptz not null default now(),
  reporter uuid references auth.users (id) on delete set null,
  reporter_name text,
  target uuid references auth.users (id) on delete cascade,
  target_name text,
  reason text not null check (reason in ('name', 'bio', 'crew', 'cheating', 'other')),
  note text,
  status text not null default 'open' check (status in ('open', 'done', 'dismissed')),
  handled_at timestamptz
);
create index if not exists reports_open on public.reports (status, at desc);
alter table public.reports enable row level security;
revoke all on public.reports from anon, authenticated;

create or replace function public.report_player(p_username text, p_reason text, p_note text default null) returns json
language plpgsql security definer set search_path = public as $$
declare
  me uuid := public._active();
  t public.profiles;
begin
  select * into t from public.profiles where lower(username) = lower(p_username);
  if not found then return json_build_object('ok', false, 'reason', 'no_user'); end if;
  if t.id = me then return json_build_object('ok', false, 'reason', 'self'); end if;
  if p_reason not in ('name', 'bio', 'status', 'socials', 'crew', 'cheating', 'other') then return json_build_object('ok', false, 'reason', 'bad_reason'); end if;
  if exists (select 1 from public.reports where reporter = me and target = t.id and reason = p_reason and status = 'open') then
    return json_build_object('ok', true, 'already', true);
  end if;
  if (select count(*) from public.reports where reporter = me and at > now() - interval '1 day') >= 15 then
    return json_build_object('ok', false, 'reason', 'too_many');
  end if;
  insert into public.reports (reporter, reporter_name, target, target_name, reason, note)
  values (me, (select username from public.profiles where id = me), t.id, t.username, p_reason, nullif(left(trim(coalesce(p_note, '')), 300), ''));
  return json_build_object('ok', true);
end
$$;

create or replace function public.owner_reports(p_status text default 'open') returns json
language plpgsql stable security definer set search_path = public as $$
begin
  if not public.is_owner() then raise exception 'owner only'; end if;
  return coalesce((
    select json_agg(json_build_object('id', r.id, 'at', r.at, 'reporter', r.reporter_name, 'reason', r.reason, 'note', r.note, 'status', r.status,
             'target', coalesce(p.username, r.target_name), 'reported_name', r.target_name, 'bio', p.bio, 'crew', public._crew_tag(p.id),
             'banned', public._is_banned(p.id), 'reports_on_target', (select count(*) from public.reports r2 where r2.target = r.target and r2.status = 'open'))
             order by r.at desc)
    from (select * from public.reports where status = coalesce(p_status, 'open') order by at desc limit 200) r
    left join public.profiles p on p.id = r.target
  ), '[]'::json);
end
$$;

create or replace function public.owner_report_set(p_id bigint, p_status text) returns json
language plpgsql security definer set search_path = public as $$
declare
  t uuid;
  n int;
begin
  if not public.is_owner() then raise exception 'owner only'; end if;
  if p_status not in ('open', 'done', 'dismissed') then raise exception 'bad status'; end if;
  select target into t from public.reports where id = p_id;
  n := 0;
  -- Handling one report closes every open report about the same player.
  with upd as (
    update public.reports set status = p_status, handled_at = now()
     where (id = p_id or (p_status <> 'open' and target = t and status = 'open'))
     returning reporter, target_name)
  select count(*) into n from (
    select public._notify(u.reporter, 'report', 'Your report was handled', 'Thanks for reporting ' || u.target_name || '. The owner took care of it.', null)
      from (select distinct reporter, target_name from upd where reporter is not null and p_status = 'done') u) z;
  return json_build_object('ok', true);
end
$$;

create or replace function public.owner_clear_bio(p_username text) returns json
language plpgsql security definer set search_path = public as $$
begin
  if not public.is_owner() then raise exception 'owner only'; end if;
  update public.profiles set bio = null where lower(username) = lower(p_username);
  return json_build_object('ok', found);
end
$$;

create or replace function public.owner_crew_delete(p_tag text) returns json
language plpgsql security definer set search_path = public as $$
begin
  if not public.is_owner() then raise exception 'owner only'; end if;
  delete from public.crews where lower(tag) = lower(p_tag);
  insert into public.key_log (event, username, detail) values ('crew_deleted', null, 'crew [' || p_tag || ']');
  return json_build_object('ok', found);
end
$$;

-- ---------- Bans ----------
create or replace function public.owner_ban(p_username text, p_days int, p_reason text) returns json
language plpgsql security definer set search_path = public as $$
declare
  t public.profiles;
  until timestamptz := case when coalesce(p_days, 0) > 0 then now() + make_interval(days => p_days) else 'infinity'::timestamptz end;
begin
  if not public.is_owner() then raise exception 'owner only'; end if;
  select * into t from public.profiles where lower(username) = lower(p_username);
  if not found then raise exception 'no such user'; end if;
  if t.is_owner then raise exception 'you can''t ban the owner'; end if;
  update public.profiles set banned_until = until, ban_reason = nullif(left(trim(coalesce(p_reason, '')), 200), ''),
         now_playing = null where id = t.id;
  insert into public.key_log (event, username, detail)
  values ('banned', t.username, case when coalesce(p_days, 0) > 0 then p_days || ' days' else 'forever' end || coalesce(': ' || nullif(trim(p_reason), ''), ''));
  return json_build_object('ok', true, 'until', until);
end
$$;

create or replace function public.owner_unban(p_username text) returns json
language plpgsql security definer set search_path = public as $$
declare
  n text;
begin
  if not public.is_owner() then raise exception 'owner only'; end if;
  update public.profiles set banned_until = null, ban_reason = null where lower(username) = lower(p_username) returning username into n;
  if n is null then raise exception 'no such user'; end if;
  insert into public.key_log (event, username, detail) values ('unbanned', n, null);
  return json_build_object('ok', true);
end
$$;

create or replace function public.owner_bans() returns json
language plpgsql stable security definer set search_path = public as $$
begin
  if not public.is_owner() then raise exception 'owner only'; end if;
  return coalesce((select json_agg(json_build_object('username', username, 'until', banned_until, 'forever', banned_until = 'infinity'::timestamptz,
                    'reason', ban_reason) order by banned_until)
                   from public.profiles where banned_until > now()), '[]'::json);
end
$$;

-- ---------- Feedback ----------
create table if not exists public.feedback (
  id bigint generated always as identity primary key,
  at timestamptz not null default now(),
  user_id uuid references auth.users (id) on delete set null,
  username text,
  kind text not null check (kind in ('bug', 'idea', 'other', 'appeal')),
  message text not null,
  log text,
  version text,
  status text not null default 'new' check (status in ('new', 'seen', 'done'))
);
create index if not exists feedback_status on public.feedback (status, at desc);
alter table public.feedback enable row level security;
revoke all on public.feedback from anon, authenticated;

create or replace function public.send_feedback(p_kind text, p_message text, p_log text default null, p_version text default null) returns json
language plpgsql security definer set search_path = public as $$
declare
  me uuid := auth.uid();
begin
  if me is null then raise exception 'log in first'; end if;
  if public._is_banned(me) and p_kind <> 'appeal' then raise exception 'account banned'; end if;
  if p_kind not in ('bug', 'idea', 'other', 'appeal') then return json_build_object('ok', false, 'reason', 'bad_kind'); end if;
  if length(trim(coalesce(p_message, ''))) < 3 then return json_build_object('ok', false, 'reason', 'empty'); end if;
  if (select count(*) from public.feedback where user_id = me and at > now() - interval '1 hour') >= 5 then
    return json_build_object('ok', false, 'reason', 'too_many');
  end if;
  insert into public.feedback (user_id, username, kind, message, log, version)
  values (me, (select username from public.profiles where id = me), p_kind, left(trim(p_message), 2000), left(p_log, 60000), left(p_version, 20));
  return json_build_object('ok', true);
end
$$;

create or replace function public.owner_feedback(p_status text default 'new') returns json
language plpgsql stable security definer set search_path = public as $$
begin
  if not public.is_owner() then raise exception 'owner only'; end if;
  return coalesce((select json_agg(json_build_object('id', id, 'at', at, 'username', username, 'kind', kind, 'message', message,
                    'version', version, 'status', status, 'has_log', log is not null and log <> '') order by at desc)
                   from (select * from public.feedback where p_status = 'all' or status = p_status order by at desc limit 150) f), '[]'::json);
end
$$;

create or replace function public.owner_feedback_log(p_id bigint) returns text
language plpgsql stable security definer set search_path = public as $$
begin
  if not public.is_owner() then raise exception 'owner only'; end if;
  return (select log from public.feedback where id = p_id);
end
$$;

create or replace function public.owner_feedback_set(p_id bigint, p_status text) returns json
language plpgsql security definer set search_path = public as $$
begin
  if not public.is_owner() then raise exception 'owner only'; end if;
  update public.feedback set status = p_status where id = p_id;
  return json_build_object('ok', found);
end
$$;

revoke execute on function public._is_banned(uuid), public._active(), public._clean_showcase(jsonb), public._clean_banner(uuid, text),
  public._clean_name_style(uuid, text), public._crew_tag(uuid), public._crew_code(), public._crew_name_problem(text, text),
  public._my_led_crew(), public.crew_create(text, text), public.crew_join(text), public.crew_leave(), public.crew_kick(text),
  public.crew_new_code(), public.crew_disband(), public.crew_info(text), public.crew_board(text), public.report_player(text, text, text),
  public.owner_reports(text), public.owner_report_set(bigint, text), public.owner_clear_bio(text), public.owner_crew_delete(text),
  public.owner_ban(text, int, text), public.owner_unban(text), public.owner_bans(), public.send_feedback(text, text, text, text),
  public.owner_feedback(text), public.owner_feedback_log(bigint), public.owner_feedback_set(bigint, text) from public, anon;
grant execute on function public.crew_create(text, text), public.crew_join(text), public.crew_leave(), public.crew_kick(text),
  public.crew_new_code(), public.crew_disband(), public.crew_info(text), public.crew_board(text), public.report_player(text, text, text),
  public.owner_reports(text), public.owner_report_set(bigint, text), public.owner_clear_bio(text), public.owner_crew_delete(text),
  public.owner_ban(text, int, text), public.owner_unban(text), public.owner_bans(), public.send_feedback(text, text, text, text),
  public.owner_feedback(text), public.owner_feedback_log(bigint), public.owner_feedback_set(bigint, text) to authenticated;

-- ============================================================================
-- v2.18.0: status messages, profile visitors, weekly crew wars, crew Wrapped, crew chat.
-- Safe to run again.
-- ============================================================================
alter table public.profiles add column if not exists status text;
alter table public.profiles add column if not exists status_at timestamptz;

create table if not exists public.profile_weeks (
  user_id uuid not null references auth.users (id) on delete cascade,
  week date not null,
  seconds int not null default 0,
  primary key (user_id, week)
);
create table if not exists public.profile_months (
  user_id uuid not null references auth.users (id) on delete cascade,
  month date not null,
  seconds int not null default 0,
  games jsonb not null default '[]',
  primary key (user_id, month)
);
create table if not exists public.profile_views (
  viewer uuid not null references auth.users (id) on delete cascade,
  target uuid not null references auth.users (id) on delete cascade,
  day date not null default current_date,
  primary key (viewer, target, day)
);
create index if not exists profile_views_target on public.profile_views (target, day);
create table if not exists public.crew_wars (
  week date primary key,
  crew_id uuid references public.crews (id) on delete set null,
  tag text,
  name text,
  seconds bigint not null default 0,
  settled_at timestamptz not null default now()
);
create table if not exists public.crew_messages (
  id bigint generated always as identity primary key,
  crew_id uuid not null references public.crews (id) on delete cascade,
  user_id uuid references auth.users (id) on delete set null,
  username text,
  body text not null,
  at timestamptz not null default now(),
  deleted boolean not null default false
);
create index if not exists crew_messages_crew on public.crew_messages (crew_id, id desc);
alter table public.profile_weeks enable row level security;
alter table public.profile_months enable row level security;
alter table public.profile_views enable row level security;
alter table public.crew_wars enable row level security;
alter table public.crew_messages enable row level security;
revoke all on public.profile_weeks, public.profile_months, public.profile_views, public.crew_wars, public.crew_messages from anon, authenticated;

alter table public.reports drop constraint if exists reports_reason_check;
alter table public.reports add constraint reports_reason_check check (reason in ('name', 'bio', 'crew', 'cheating', 'chat', 'status', 'socials', 'other'));

-- Bad words are kept out of statuses the same way as bios.
create or replace function public._enforce_bio() returns trigger
language plpgsql security definer set search_path = public as $$
begin
  if new.bio is distinct from old.bio and new.bio is not null and public._bio_rule(new.bio) is not null then
    new.bio := old.bio;
  end if;
  if new.status is distinct from old.status and new.status is not null and public._bio_rule(new.status) is not null then
    new.status := old.status;
    new.status_at := old.status_at;
  end if;
  return new;
end
$$;
drop trigger if exists profiles_bio_automod on public.profiles;
create trigger profiles_bio_automod before update of bio, status on public.profiles for each row execute function public._enforce_bio();

create or replace function public._clean_games(p jsonb) returns jsonb
language plpgsql immutable as $$
declare
  out jsonb := '[]'::jsonb;
  g jsonb;
begin
  if jsonb_typeof(p) <> 'array' then return out; end if;
  for g in select value from jsonb_array_elements(p) loop
    exit when jsonb_array_length(out) >= 5;
    if (g ->> 'pid') ~ '^[0-9]{1,15}$' then
      out := out || jsonb_build_array(jsonb_build_object('pid', g ->> 'pid', 'name', left(coalesce(g ->> 'name', 'Game'), 60),
                                                         'seconds', least(greatest(coalesce((g ->> 'seconds')::numeric, 0), 0), 2678400)::int));
    end if;
  end loop;
  return out;
end
$$;

-- ---------- Weekly crew wars ----------
-- The crew with the most hours in a week (Monday to Sunday, UTC) wins a trophy. Settled the first time anyone
-- looks at crews after the week ends.
create or replace function public._settle_crew_wars() returns void
language plpgsql security definer set search_path = public as $$
declare
  last_week date := public._this_week() - 7;
  w record;
begin
  if exists (select 1 from public.crew_wars where week = last_week) then return; end if;
  select c.id, c.tag, c.name, sum(pw.seconds) as s into w
    from public.crews c join public.crew_members m on m.crew_id = c.id
    join public.profile_weeks pw on pw.user_id = m.user_id and pw.week = last_week
   where not public._is_banned(m.user_id)
   group by c.id having sum(pw.seconds) > 0 order by s desc limit 1;
  insert into public.crew_wars (week, crew_id, tag, name, seconds)
  values (last_week, w.id, w.tag, w.name, coalesce(w.s, 0)) on conflict (week) do nothing;
  if found and w.id is not null then
    perform public._notify(m.user_id, 'war', '🏆 [' || w.tag || '] won the weekly crew war!', 'Your crew played the most last week. The trophy is on your crew page.', '{"page":"social","tab":"crew"}'::jsonb)
       from public.crew_members m where m.crew_id = w.id;
  end if;
end
$$;

-- ---------- Crew Wrapped ----------
create or replace function public.crew_wrapped(p_which text default 'last', p_tag text default null) returns json
language plpgsql stable security definer set search_path = public as $$
declare
  me uuid := auth.uid();
  c public.crews;
  mon date := (date_trunc('month', now()) - case when p_which = 'this' then interval '0' else interval '1 month' end)::date;
  tot bigint;
  pos int;
begin
  if me is null then raise exception 'log in first'; end if;
  if p_tag is null then
    select c2.* into c from public.crews c2 join public.crew_members m on m.crew_id = c2.id where m.user_id = me;
  else
    select * into c from public.crews where lower(tag) = lower(p_tag);
  end if;
  if not found then return json_build_object('found', false); end if;
  select coalesce(sum(pm.seconds), 0) into tot from public.crew_members m join public.profile_months pm on pm.user_id = m.user_id and pm.month = mon
   where m.crew_id = c.id and not public._is_banned(m.user_id);
  select count(*) + 1 into pos from (
    select m.crew_id, sum(pm.seconds) s from public.crew_members m join public.profile_months pm on pm.user_id = m.user_id and pm.month = mon
     where not public._is_banned(m.user_id) group by m.crew_id) x where x.s > tot;
  return json_build_object('found', true, 'tag', c.tag, 'name', c.name, 'month', mon, 'total_seconds', tot,
    'rank', case when tot > 0 then pos end,
    'crews', (select count(distinct m.crew_id) from public.crew_members m join public.profile_months pm on pm.user_id = m.user_id and pm.month = mon where pm.seconds > 0),
    'members', (select count(*) from public.crew_members where crew_id = c.id),
    'active', (select count(*) from public.crew_members m join public.profile_months pm on pm.user_id = m.user_id and pm.month = mon where m.crew_id = c.id and pm.seconds > 0),
    'top', coalesce((select json_agg(x order by x.seconds desc) from (
        select p.username, p.roblox_id, p.name_style, pm.seconds from public.crew_members m join public.profiles p on p.id = m.user_id
          join public.profile_months pm on pm.user_id = m.user_id and pm.month = mon
         where m.crew_id = c.id and pm.seconds > 0 and not public._is_banned(p.id) order by pm.seconds desc limit 3) x), '[]'::json),
    'games', coalesce((select json_agg(g order by g.seconds desc) from (
        select gg ->> 'pid' as pid, max(gg ->> 'name') as name, sum((gg ->> 'seconds')::bigint) as seconds, count(distinct m.user_id) as players
          from public.crew_members m join public.profile_months pm on pm.user_id = m.user_id and pm.month = mon,
               jsonb_array_elements(pm.games) gg
         where m.crew_id = c.id and not public._is_banned(m.user_id)
         group by gg ->> 'pid' order by sum((gg ->> 'seconds')::bigint) desc limit 3) g), '[]'::json),
    'war_wins', (select count(*) from public.crew_wars w where w.crew_id = c.id and w.week >= mon and w.week < (mon + interval '1 month')::date));
end
$$;

-- ---------- Crew chat ----------
create or replace function public._my_crew() returns uuid
language sql stable security definer set search_path = public as $$
  select crew_id from public.crew_members where user_id = auth.uid()
$$;

create or replace function public.crew_chat_send(p_body text) returns json
language plpgsql security definer set search_path = public as $$
declare
  me uuid := public._active();
  cid uuid := public._my_crew();
  body text := trim(regexp_replace(coalesce(p_body, ''), '\r', '', 'g'));
  m public.crew_messages;
begin
  if cid is null then return json_build_object('ok', false, 'reason', 'no_crew'); end if;
  if public._chat_muted(me) is not null then
    return json_build_object('ok', false, 'reason', 'muted', 'until', public._chat_muted(me));
  end if;
  body := regexp_replace(body, '\n{3,}', E'\n\n', 'g');
  if length(body) < 1 then return json_build_object('ok', false, 'reason', 'empty'); end if;
  if length(body) > 300 then return json_build_object('ok', false, 'reason', 'long'); end if;
  if public._bio_rule(body) is not null then return json_build_object('ok', false, 'reason', 'blocked'); end if;
  if (select count(*) from public.crew_messages where user_id = me and at > now() - interval '30 seconds') >= 6 then
    return json_build_object('ok', false, 'reason', 'slow');
  end if;
  insert into public.crew_messages (crew_id, user_id, username, body)
  values (cid, me, (select username from public.profiles where id = me), body) returning * into m;
  perform public._mentions(body, me, 'crew chat', cid);
  delete from public.crew_messages where crew_id = cid and id < (select id from public.crew_messages where crew_id = cid order by id desc offset 500 limit 1);
  return json_build_object('ok', true, 'id', m.id);
end
$$;

create or replace function public.crew_chat_list(p_sig text default null) returns json
language plpgsql stable security definer set search_path = public as $$
declare
  me uuid := auth.uid();
  cid uuid := public._my_crew();
  sig text;
  leader uuid;
begin
  if me is null then raise exception 'log in first'; end if;
  if cid is null then return json_build_object('found', false); end if;
  select coalesce(max(id), 0) || ':' || count(*) filter (where deleted or hidden) into sig
    from (select id, deleted, hidden from public.crew_messages where crew_id = cid order by id desc limit 80) x;
  if sig = p_sig then return json_build_object('found', true, 'same', true, 'sig', sig); end if;
  select c.leader into leader from public.crews c where c.id = cid;
  return json_build_object('found', true, 'sig', sig, 'is_leader', leader = me or exists (select 1 from public.crew_members x where x.crew_id = cid and x.user_id = me and x.role = 'officer'), 'messages', coalesce((
    select json_agg(json_build_object('id', m.id, 'username', coalesce(p.username, m.username), 'at', m.at, 'body', m.body,
             'mine', m.user_id = me, 'leader', m.user_id = leader, 'name_style', p.name_style) order by m.id)
      from (select * from public.crew_messages where crew_id = cid and not deleted and not hidden order by id desc limit 80) m
      left join public.profiles p on p.id = m.user_id), '[]'::json));
end
$$;

create or replace function public.crew_chat_delete(p_id bigint) returns json
language plpgsql security definer set search_path = public as $$
declare
  m public.crew_messages;
begin
  select * into m from public.crew_messages where id = p_id;
  if not found then return json_build_object('ok', true); end if;
  if not (m.user_id = auth.uid() or public.is_owner()
          or exists (select 1 from public.crews c where c.id = m.crew_id and c.leader = auth.uid())
          or exists (select 1 from public.crew_members x where x.crew_id = m.crew_id and x.user_id = auth.uid() and x.role = 'officer')) then
    raise exception 'not allowed';
  end if;
  update public.crew_messages set deleted = true, body = '' where id = p_id;
  return json_build_object('ok', true);
end
$$;

create or replace function public.crew_chat_report(p_id bigint) returns json
language plpgsql security definer set search_path = public as $$
declare
  me uuid := public._active();
  m public.crew_messages;
  tag text;
begin
  select * into m from public.crew_messages where id = p_id and crew_id = public._my_crew() and not deleted;
  if not found then return json_build_object('ok', false, 'reason', 'gone'); end if;
  if m.user_id = me then return json_build_object('ok', false, 'reason', 'self'); end if;
  if exists (select 1 from public.reports where reporter = me and reason = 'chat' and note like '%#' || p_id) then
    return json_build_object('ok', true, 'already', true);
  end if;
  if (select count(*) from public.reports where reporter = me and at > now() - interval '1 day') >= 15 then
    return json_build_object('ok', false, 'reason', 'too_many');
  end if;
  select c.tag into tag from public.crews c where c.id = m.crew_id;
  insert into public.reports (reporter, reporter_name, target, target_name, reason, note)
  values (me, (select username from public.profiles where id = me), m.user_id, m.username, 'chat',
          left('[' || tag || '] chat: "' || m.body || '"', 290) || ' #' || p_id);
  perform public._flag_message('crew', p_id, me);
  return json_build_object('ok', true);
end
$$;

revoke execute on function public._clean_games(jsonb), public._settle_crew_wars(), public.crew_wrapped(text, text), public._my_crew(),
  public.crew_chat_send(text), public.crew_chat_list(text), public.crew_chat_delete(bigint), public.crew_chat_report(bigint) from public, anon;
grant execute on function public.crew_wrapped(text, text), public.crew_chat_send(text), public.crew_chat_list(text),
  public.crew_chat_delete(bigint), public.crew_chat_report(bigint) to authenticated;


-- ============================================================================
-- v2.19.0: owner stats, required updates, chat auto-mod and timeouts, global chat.
-- Safe to run again.
-- ============================================================================
alter table public.profiles add column if not exists app_version text;
alter table public.profiles add column if not exists chat_muted_until timestamptz;
alter table public.crew_messages add column if not exists hidden boolean not null default false;

create table if not exists public.profile_days (
  user_id uuid not null references auth.users (id) on delete cascade,
  day date not null,
  primary key (user_id, day)
);
create index if not exists profile_days_day on public.profile_days (day);
create table if not exists public.app_config (key text primary key, value jsonb, updated_at timestamptz not null default now());
create table if not exists public.global_messages (
  id bigint generated always as identity primary key,
  user_id uuid references auth.users (id) on delete set null,
  username text,
  body text not null,
  at timestamptz not null default now(),
  deleted boolean not null default false,
  hidden boolean not null default false
);
create table if not exists public.chat_flags (
  kind text not null check (kind in ('crew', 'global')),
  msg_id bigint not null,
  reporter uuid not null references auth.users (id) on delete cascade,
  at timestamptz not null default now(),
  primary key (kind, msg_id, reporter)
);
create table if not exists public.chat_strikes (
  id bigint generated always as identity primary key,
  user_id uuid not null references auth.users (id) on delete cascade,
  at timestamptz not null default now(),
  kind text,
  msg_id bigint
);
alter table public.profile_days enable row level security;
alter table public.app_config enable row level security;
alter table public.global_messages enable row level security;
alter table public.chat_flags enable row level security;
alter table public.chat_strikes enable row level security;
revoke all on public.profile_days, public.app_config, public.global_messages, public.chat_flags, public.chat_strikes from anon, authenticated;

-- ---------- Required update ----------
create or replace function public.app_min_version() returns json
language sql stable security definer set search_path = public as $$
  select coalesce((select value from public.app_config where key = 'min_version')::json, '{}'::json)
$$;

create or replace function public.owner_set_min_version(p_version text, p_message text default null) returns json
language plpgsql security definer set search_path = public as $$
begin
  if not public.is_owner() then raise exception 'owner only'; end if;
  if coalesce(trim(p_version), '') = '' then
    delete from public.app_config where key = 'min_version';
    return json_build_object('ok', true, 'cleared', true);
  end if;
  if trim(p_version) !~ '^[0-9]+\.[0-9]+\.[0-9]+(-[a-z]+\.?[0-9]*)?$' then raise exception 'version must look like 2.19.0'; end if;
  insert into public.app_config (key, value, updated_at)
  values ('min_version', jsonb_build_object('min', trim(p_version), 'message', nullif(left(trim(coalesce(p_message, '')), 200), '')), now())
  on conflict (key) do update set value = excluded.value, updated_at = now();
  return json_build_object('ok', true);
end
$$;

-- ---------- Chat auto-mod ----------
create or replace function public._chat_muted(p_uid uuid) returns timestamptz
language sql stable security definer set search_path = public as $$
  select chat_muted_until from public.profiles where id = p_uid and chat_muted_until > now()
$$;

-- Reports on chat messages are only counted for the owner to see. Nothing gets hidden or timed out automatically
-- (that could be abused with alts); the owner decides from the Reports card.
create or replace function public._flag_message(p_kind text, p_id bigint, p_reporter uuid) returns void
language plpgsql security definer set search_path = public as $$
begin
  insert into public.chat_flags (kind, msg_id, reporter) values (p_kind, p_id, p_reporter) on conflict do nothing;
end
$$;

-- ---------- Global chat ----------
-- Keeps people safe: no links, no swapping Discord/Snap/phone numbers with strangers.
create or replace function public._contact_rule(p_text text) returns boolean
language sql immutable as $$
  select coalesce(p_text, '') ~* '(https?://|www\.|discord\.gg|\.(com|net|org|gg|io|xyz|ly|me|co|tv)(\W|$)|@[a-z0-9-]+\.[a-z]{2,})'
      or coalesce(p_text, '') ~* '\m(discord|snap|snapchat|insta|instagram|ig|tiktok|whatsapp|telegram|kik|facetime|venmo|cashapp)\M'
      or coalesce(p_text, '') ~* '\m(add|dm|text|call|message|friend) me (on|at)\M(?!\s*roblox)|\mmy (number|phone|snap|insta|discord|address|location)\M'
      or regexp_replace(coalesce(p_text, ''), '[\s\-\.\(\)]', '', 'g') ~ '[0-9]{7,}'
$$;

drop function if exists public.global_chat_send(text);
create or replace function public.global_chat_send(p_body text, p_channel text default 'general') returns json
language plpgsql security definer set search_path = public as $$
declare
  me uuid := public._active();
  pr public.profiles;
  body text := trim(regexp_replace(coalesce(p_body, ''), '[\r\n\t]+', ' ', 'g'));
  last_at timestamptz;
  m bigint;
begin
  select * into pr from public.profiles where id = me;
  if public._chat_muted(me) is not null then return json_build_object('ok', false, 'reason', 'muted', 'until', public._chat_muted(me)); end if;
  if not pr.is_owner and pr.created_at > now() - interval '1 day' then
    return json_build_object('ok', false, 'reason', 'new_account', 'until', pr.created_at + interval '1 day');
  end if;
  if not exists (select 1 from public.chat_channels where id = p_channel) then return json_build_object('ok', false, 'reason', 'no_channel'); end if;
  if length(body) < 1 then return json_build_object('ok', false, 'reason', 'empty'); end if;
  if length(body) > 200 then return json_build_object('ok', false, 'reason', 'long'); end if;
  if public._bio_rule(body, true) is not null then return json_build_object('ok', false, 'reason', 'blocked'); end if;
  if not pr.is_owner and public._contact_rule(body) then return json_build_object('ok', false, 'reason', 'contact'); end if;
  select max(at) into last_at from public.global_messages where user_id = me;
  if not pr.is_owner and last_at > now() - interval '4 seconds' then return json_build_object('ok', false, 'reason', 'slow'); end if;
  if not pr.is_owner and (select count(*) from public.global_messages where user_id = me and at > now() - interval '1 minute') >= 8 then
    return json_build_object('ok', false, 'reason', 'slow');
  end if;
  insert into public.global_messages (user_id, username, body, channel) values (me, pr.username, body, p_channel) returning id into m;
  perform public._mentions(body, me, '#' || p_channel, null);
  if random() < 0.05 then
    delete from public.global_messages where id < (select id from public.global_messages order by id desc offset 3000 limit 1);
  end if;
  return json_build_object('ok', true, 'id', m);
end
$$;

drop function if exists public.global_chat_list(text);
create or replace function public.global_chat_list(p_sig text default null, p_channel text default 'general') returns json
language plpgsql stable security definer set search_path = public as $$
declare
  me uuid := auth.uid();
  sig text;
  pr public.profiles;
begin
  if me is null then raise exception 'log in first'; end if;
  select coalesce(max(id), 0) || ':' || count(*) filter (where deleted or hidden) || ':' ||
         (select count(*) from public.message_reactions r where r.msg_id = any (array_agg(x.id))) into sig
    from (select id, deleted, hidden from public.global_messages where channel = p_channel order by id desc limit 100) x;
  select * into pr from public.profiles where id = me;
  if sig = p_sig then
    return json_build_object('same', true, 'sig', sig, 'online', (select count(*) from public.profiles where last_seen > now() - interval '5 minutes'));
  end if;
  return json_build_object('sig', sig, 'online', (select count(*) from public.profiles where last_seen > now() - interval '5 minutes'),
    'muted_until', public._chat_muted(me),
    'new_until', case when not pr.is_owner and pr.created_at > now() - interval '1 day' then pr.created_at + interval '1 day' end,
    'messages', coalesce((
      select json_agg(json_build_object('id', m.id, 'username', coalesce(p.username, m.username), 'at', m.at, 'body', m.body, 'mine', m.user_id = me,
               'crew', public._crew_tag(m.user_id), 'name_style', p.name_style, 'level', p.level, 'owner', coalesce(p.is_owner, false),
               'badges', public._badges(p.id, p.is_owner, p.badges), 'kind', m.kind, 'meta', m.meta,
               'roblox_id', case when m.kind = 'lfg' then p.roblox_id end,
               'playing', case when m.kind = 'lfg' and p.share_activity and p.playing_at > now() - interval '5 minutes' then p.now_playing end,
               'mentions_me', m.body ~* ('@' || pr.username || '\M'),
               'reactions', (select json_object_agg(e, json_build_object('n', n, 'mine', mine)) from (
                   select r.emoji e, count(*) n, bool_or(r.user_id = me) mine from public.message_reactions r where r.msg_id = m.id group by r.emoji) rr)) order by m.id)
        from (select * from public.global_messages g where g.channel = p_channel and not g.deleted and not g.hidden and not public._is_banned(g.user_id) order by g.id desc limit 100) m
        left join public.profiles p on p.id = m.user_id), '[]'::json),
    'channels', (select json_agg(json_build_object('id', id, 'name', name, 'emoji', emoji) order by sort, id) from public.chat_channels));
end
$$;

create or replace function public.global_chat_delete(p_id bigint) returns json
language plpgsql security definer set search_path = public as $$
begin
  update public.global_messages set deleted = true, body = '' where id = p_id and (user_id = auth.uid() or public.is_owner());
  if not found then raise exception 'not allowed'; end if;
  return json_build_object('ok', true);
end
$$;

create or replace function public.global_chat_report(p_id bigint) returns json
language plpgsql security definer set search_path = public as $$
declare
  me uuid := public._active();
  m public.global_messages;
begin
  select * into m from public.global_messages where id = p_id and not deleted and not hidden;
  if not found then return json_build_object('ok', false, 'reason', 'gone'); end if;
  if m.user_id = me then return json_build_object('ok', false, 'reason', 'self'); end if;
  if exists (select 1 from public.chat_flags where kind = 'global' and msg_id = p_id and reporter = me) then
    return json_build_object('ok', true, 'already', true);
  end if;
  if (select count(*) from public.reports where reporter = me and at > now() - interval '1 day') >= 15 then
    return json_build_object('ok', false, 'reason', 'too_many');
  end if;
  insert into public.reports (reporter, reporter_name, target, target_name, reason, note)
  values (me, (select username from public.profiles where id = me), m.user_id, m.username, 'chat', left('Global chat: "' || m.body || '"', 290) || ' #g' || p_id);
  perform public._flag_message('global', p_id, me);
  return json_build_object('ok', true);
end
$$;

-- ---------- Owner tools ----------
create or replace function public.owner_hidden_messages() returns json
language plpgsql stable security definer set search_path = public as $$
begin
  if not public.is_owner() then raise exception 'owner only'; end if;
  return coalesce((select json_agg(x order by x.at desc) from (
    select 'global' as kind, g.id, g.username, g.body, g.at, null::text as crew,
           (select count(*) from public.chat_flags f where f.kind = 'global' and f.msg_id = g.id) as flags
      from public.global_messages g where g.hidden and not g.deleted
    union all
    select 'crew', c.id, c.username, c.body, c.at, (select tag from public.crews where id = c.crew_id),
           (select count(*) from public.chat_flags f where f.kind = 'crew' and f.msg_id = c.id)
      from public.crew_messages c where c.hidden and not c.deleted
    order by 5 desc limit 100) x), '[]'::json);
end
$$;

create or replace function public.owner_message_set(p_kind text, p_id bigint, p_action text) returns json
language plpgsql security definer set search_path = public as $$
begin
  if not public.is_owner() then raise exception 'owner only'; end if;
  if p_kind = 'global' then
    if p_action = 'restore' then update public.global_messages set hidden = false where id = p_id;
    else update public.global_messages set deleted = true, hidden = false, body = '' where id = p_id; end if;
  else
    if p_action = 'restore' then update public.crew_messages set hidden = false where id = p_id;
    else update public.crew_messages set deleted = true, hidden = false, body = '' where id = p_id; end if;
  end if;
  if p_action = 'restore' then
    delete from public.chat_flags where kind = p_kind and msg_id = p_id;
    delete from public.chat_strikes where kind = p_kind and msg_id = p_id;
  end if;
  return json_build_object('ok', true);
end
$$;

create or replace function public.owner_chat_mute(p_username text, p_hours int) returns json
language plpgsql security definer set search_path = public as $$
declare
  n text;
begin
  if not public.is_owner() then raise exception 'owner only'; end if;
  if exists (select 1 from public.profiles where lower(username) = lower(p_username) and is_owner) then raise exception 'you can''t time out the owner'; end if;
  update public.profiles set chat_muted_until = case when coalesce(p_hours, 0) > 0 then now() + make_interval(hours => p_hours) end
   where lower(username) = lower(p_username) and not is_owner returning username into n;
  if n is null then raise exception 'no such user'; end if;
  insert into public.key_log (event, username, detail) values (case when coalesce(p_hours, 0) > 0 then 'muted' else 'unmuted' end, n,
    case when coalesce(p_hours, 0) > 0 then p_hours || ' hours' end);
  return json_build_object('ok', true);
end
$$;

create or replace function public.owner_chat_mutes() returns json
language plpgsql stable security definer set search_path = public as $$
begin
  if not public.is_owner() then raise exception 'owner only'; end if;
  return coalesce((select json_agg(json_build_object('username', username, 'until', chat_muted_until) order by chat_muted_until)
                   from public.profiles where chat_muted_until > now()), '[]'::json);
end
$$;

create or replace function public.owner_stats() returns json
language plpgsql stable security definer set search_path = public as $$
begin
  if not public.is_owner() then raise exception 'owner only'; end if;
  return json_build_object(
    'online', (select count(*) from public.profiles where last_seen > now() - interval '5 minutes'),
    'playing', (select count(*) from public.profiles where now_playing is not null and playing_at > now() - interval '5 minutes'),
    'accounts', (select count(*) from public.profiles),
    'new_today', (select count(*) from public.profiles where created_at >= current_date),
    'active_today', (select count(*) from public.profile_days where day = current_date),
    'active_week', (select count(distinct user_id) from public.profile_days where day > current_date - 7),
    'premium', (select count(distinct user_id) from public.redemptions where not disabled and (expires_at is null or expires_at > now())),
    'banned', (select count(*) from public.profiles where banned_until > now()),
    'muted', (select count(*) from public.profiles where chat_muted_until > now()),
    'crews', (select count(*) from public.crews),
    'open_reports', (select count(*) from public.reports where status = 'open'),
    'new_feedback', (select count(*) from public.feedback where status = 'new'),
    'hidden_messages', (select count(*) from public.global_messages where hidden and not deleted) + (select count(*) from public.crew_messages where hidden and not deleted),
    'messages_today', (select count(*) from public.global_messages where at >= current_date) + (select count(*) from public.crew_messages where at >= current_date),
    'signups', (select json_agg(json_build_object('day', d::date, 'n', (select count(*) from public.profiles where created_at >= d and created_at < d + interval '1 day')) order by d)
                  from generate_series(current_date - 13, current_date, interval '1 day') d),
    'active', (select json_agg(json_build_object('day', d::date, 'n', (select count(*) from public.profile_days where day = d::date)) order by d)
                 from generate_series(current_date - 13, current_date, interval '1 day') d),
    'versions', coalesce((select json_agg(json_build_object('version', v, 'n', n) order by n desc) from (
                   select coalesce(app_version, 'older') v, count(*) n from public.profiles where last_seen > now() - interval '7 days' group by 1) x), '[]'::json),
    'min_version', public.app_min_version());
end
$$;

revoke execute on function public.app_min_version(), public.owner_set_min_version(text, text), public._chat_muted(uuid),
  public._flag_message(text, bigint, uuid), public._contact_rule(text), public.global_chat_send(text, text), public.global_chat_list(text, text),
  public.global_chat_delete(bigint), public.global_chat_report(bigint), public.owner_hidden_messages(), public.owner_message_set(text, bigint, text),
  public.owner_chat_mute(text, int), public.owner_chat_mutes(), public.owner_stats() from public, anon;
grant execute on function public.app_min_version() to anon, authenticated;
grant execute on function public.owner_set_min_version(text, text), public.global_chat_send(text, text), public.global_chat_list(text, text),
  public.global_chat_delete(bigint), public.global_chat_report(bigint), public.owner_hidden_messages(), public.owner_message_set(text, bigint, text),
  public.owner_chat_mute(text, int), public.owner_chat_mutes(), public.owner_stats() to authenticated;


-- ============================================================================
-- v2.20.0: cussing in global chat (slurs and sexual words stay blocked), socials on profiles.
-- Safe to run again.
-- ============================================================================
alter table public.profiles add column if not exists socials jsonb not null default '{}';
alter table public.profiles add column if not exists socials_visibility text not null default 'nobody';
alter table public.profiles add column if not exists friend_ids bigint[];

-- Everyday swear words are fine in global chat. Slurs and sexual words are not (chat_ok stays false for those).
update public.blocked_words set chat_ok = true
 where word in ('fuck', 'fuk', 'fvck', 'shit', 'bitch', 'ass', 'asshole', 'bastard', 'dick', 'prick', 'wank', 'twat') and not chat_ok;

create or replace function public._clean_socials(p jsonb) returns jsonb
language plpgsql stable security definer set search_path = public as $$
declare
  out jsonb := '{}'::jsonb;
  k text;
  v text;
begin
  if jsonb_typeof(p) <> 'object' then return out; end if;
  for k, v in select key, trim(value) from jsonb_each_text(p) loop
    if k in ('discord', 'snapchat', 'instagram', 'tiktok', 'youtube', 'twitch', 'x')
       and v ~ '^@?[A-Za-z0-9_.#-]{2,40}$' and public._bio_rule(v) is null and v !~* '(\.com|\.gg|\.net|https?)' then
      out := out || jsonb_build_object(k, v);
    end if;
  end loop;
  return out;
end
$$;

create or replace function public.owner_clear_socials(p_username text) returns json
language plpgsql security definer set search_path = public as $$
begin
  if not public.is_owner() then raise exception 'owner only'; end if;
  update public.profiles set socials = '{}'::jsonb where lower(username) = lower(p_username);
  return json_build_object('ok', found);
end
$$;

create or replace function public.owner_word_chat(p_word text, p_ok boolean) returns json
language plpgsql security definer set search_path = public as $$
begin
  if not public.is_owner() then raise exception 'owner only'; end if;
  update public.blocked_words set chat_ok = coalesce(p_ok, false) where word = lower(p_word);
  return json_build_object('ok', found);
end
$$;

create or replace function public.owner_words() returns json
language plpgsql stable security definer set search_path = public as $$
begin
  if not public.is_owner() then raise exception 'owner only'; end if;
  return coalesce((select json_agg(json_build_object('word', word, 'kind', kind, 'match', match, 'chat_ok', chat_ok) order by kind, word) from public.blocked_words), '[]'::json);
end
$$;

revoke execute on function public._clean_socials(jsonb), public.owner_clear_socials(text), public.owner_word_chat(text, boolean) from public, anon;
grant execute on function public.owner_clear_socials(text), public.owner_word_chat(text, boolean) to authenticated;


-- ============================================================================
-- v2.21.0: chat channels, LFG posts, reactions, @mentions, inbox, Orbit Pass,
-- achievement rarity, crew officers and game nights. Safe to run again.
-- ============================================================================
alter table public.profiles add column if not exists achievements text[];
alter table public.crew_members add column if not exists role text not null default 'member';
alter table public.global_messages add column if not exists channel text not null default 'general';
alter table public.global_messages add column if not exists kind text not null default 'msg';
alter table public.global_messages add column if not exists meta jsonb;
create index if not exists global_messages_channel on public.global_messages (channel, id desc);

create table if not exists public.chat_channels (id text primary key check (id ~ '^[a-z0-9-]{2,20}$'), name text not null, emoji text, sort int not null default 100);
insert into public.chat_channels (id, name, emoji, sort) values
  ('general', 'General', '💬', 1), ('lfg', 'Looking for group', '🎮', 2), ('trading', 'Trading', '💱', 3),
  ('bedwars', 'BedWars', '🛏️', 10), ('blox-fruits', 'Blox Fruits', '🍎', 11), ('grow-a-garden', 'Grow a Garden', '🌱', 12), ('steal-the-crown', 'Steal The Crown!', '👑', 13)
on conflict (id) do nothing;

create table if not exists public.message_reactions (
  msg_id bigint not null references public.global_messages (id) on delete cascade,
  user_id uuid not null references auth.users (id) on delete cascade,
  emoji text not null check (emoji in ('🔥', '😂', '👍', '❤️', '😮', '💀')),
  primary key (msg_id, user_id, emoji)
);
create table if not exists public.inbox (
  id bigint generated always as identity primary key,
  user_id uuid not null references auth.users (id) on delete cascade,
  at timestamptz not null default now(),
  kind text not null,
  title text not null,
  body text,
  link jsonb,
  read boolean not null default false
);
create index if not exists inbox_user on public.inbox (user_id, id desc);
create table if not exists public.pass_claims (
  user_id uuid not null references auth.users (id) on delete cascade,
  season text not null,
  tier int not null,
  track text not null check (track in ('free', 'premium')),
  at timestamptz not null default now(),
  primary key (user_id, season, tier, track)
);
create table if not exists public.crew_events (
  id bigint generated always as identity primary key,
  crew_id uuid not null references public.crews (id) on delete cascade,
  title text not null,
  place_id text,
  game text,
  at timestamptz not null,
  created_by uuid references auth.users (id) on delete set null,
  created_at timestamptz not null default now()
);
create table if not exists public.crew_event_rsvps (
  event_id bigint not null references public.crew_events (id) on delete cascade,
  user_id uuid not null references auth.users (id) on delete cascade,
  primary key (event_id, user_id)
);
alter table public.chat_channels enable row level security;
alter table public.message_reactions enable row level security;
alter table public.inbox enable row level security;
alter table public.pass_claims enable row level security;
alter table public.crew_events enable row level security;
alter table public.crew_event_rsvps enable row level security;
revoke all on public.chat_channels, public.message_reactions, public.inbox, public.pass_claims, public.crew_events, public.crew_event_rsvps from anon, authenticated;

-- ---------- Inbox ----------
create or replace function public._notify(p_uid uuid, p_kind text, p_title text, p_body text, p_link jsonb) returns int
language plpgsql security definer set search_path = public as $$
begin
  if p_uid is null then return 0; end if;
  insert into public.inbox (user_id, kind, title, body, link) values (p_uid, p_kind, left(p_title, 120), left(p_body, 300), p_link);
  if random() < 0.02 then delete from public.inbox where at < now() - interval '30 days'; end if;
  return 1;
end
$$;

create or replace function public._mentions(p_body text, p_from uuid, p_where text, p_crew uuid) returns void
language plpgsql security definer set search_path = public as $$
declare
  who text;
  t uuid;
  fromname text := (select username from public.profiles where id = p_from);
begin
  for who in select distinct lower(m[1]) from regexp_matches(coalesce(p_body, ''), '@([A-Za-z0-9_]{3,20})', 'g') m limit 5 loop
    select id into t from public.profiles where lower(username) = who and id <> p_from and not public._is_banned(id);
    if t is null then continue; end if;
    if p_crew is not null and not exists (select 1 from public.crew_members where user_id = t and crew_id = p_crew) then continue; end if;
    perform public._notify(t, 'mention', fromname || ' mentioned you in ' || p_where, left(p_body, 200),
                           case when p_crew is null then jsonb_build_object('page', 'chat', 'channel', substr(p_where, 2)) else '{"page":"social","tab":"crew"}'::jsonb end);
  end loop;
end
$$;

create or replace function public.inbox_list() returns json
language plpgsql security definer set search_path = public as $$
declare
  out json;
begin
  if auth.uid() is null then raise exception 'log in first'; end if;
  select coalesce(json_agg(json_build_object('id', id, 'at', at, 'kind', kind, 'title', title, 'body', body, 'link', link, 'read', read) order by id desc), '[]'::json)
    into out from (select * from public.inbox where user_id = auth.uid() order by id desc limit 50) i;
  return json_build_object('items', out, 'unread', (select count(*) from public.inbox where user_id = auth.uid() and not read));
end
$$;

create or replace function public.inbox_count() returns int
language sql stable security definer set search_path = public as $$
  select count(*)::int from public.inbox where user_id = auth.uid() and not read
$$;

create or replace function public.inbox_read_all() returns json
language plpgsql security definer set search_path = public as $$
begin
  update public.inbox set read = true where user_id = auth.uid() and not read;
  return json_build_object('ok', true);
end
$$;

-- ---------- Reactions + LFG ----------
create or replace function public.global_chat_react(p_id bigint, p_emoji text) returns json
language plpgsql security definer set search_path = public as $$
declare
  me uuid := public._active();
begin
  if p_emoji not in ('🔥', '😂', '👍', '❤️', '😮', '💀') then return json_build_object('ok', false, 'reason', 'bad_emoji'); end if;
  if not exists (select 1 from public.global_messages where id = p_id and not deleted and not hidden) then return json_build_object('ok', false, 'reason', 'gone'); end if;
  if exists (select 1 from public.message_reactions where msg_id = p_id and user_id = me and emoji = p_emoji) then
    delete from public.message_reactions where msg_id = p_id and user_id = me and emoji = p_emoji;
    return json_build_object('ok', true, 'on', false);
  end if;
  if (select count(*) from public.message_reactions where msg_id = p_id and user_id = me) >= 3 then return json_build_object('ok', false, 'reason', 'too_many_reactions'); end if;
  insert into public.message_reactions (msg_id, user_id, emoji) values (p_id, me, p_emoji);
  return json_build_object('ok', true, 'on', true);
end
$$;

create or replace function public.global_lfg_post(p_channel text, p_place_id text, p_game text, p_need int, p_note text) returns json
language plpgsql security definer set search_path = public as $$
declare
  me uuid := public._active();
  pr public.profiles;
  note text := trim(regexp_replace(coalesce(p_note, ''), '[\r\n\t]+', ' ', 'g'));
  m bigint;
begin
  select * into pr from public.profiles where id = me;
  if public._chat_muted(me) is not null then return json_build_object('ok', false, 'reason', 'muted', 'until', public._chat_muted(me)); end if;
  if not pr.is_owner and pr.created_at > now() - interval '1 day' then return json_build_object('ok', false, 'reason', 'new_account', 'until', pr.created_at + interval '1 day'); end if;
  if not exists (select 1 from public.chat_channels where id = p_channel) then return json_build_object('ok', false, 'reason', 'no_channel'); end if;
  if pr.roblox_id is null then return json_build_object('ok', false, 'reason', 'no_roblox'); end if;
  if length(note) > 120 then return json_build_object('ok', false, 'reason', 'long'); end if;
  if public._bio_rule(note || ' ' || coalesce(p_game, ''), true) is not null then return json_build_object('ok', false, 'reason', 'blocked'); end if;
  if not pr.is_owner and public._contact_rule(note) then return json_build_object('ok', false, 'reason', 'contact'); end if;
  if not pr.is_owner and exists (select 1 from public.global_messages where user_id = me and kind = 'lfg' and at > now() - interval '2 minutes') then
    return json_build_object('ok', false, 'reason', 'slow');
  end if;
  insert into public.global_messages (user_id, username, body, channel, kind, meta)
  values (me, pr.username, coalesce(nullif(note, ''), 'Looking for players'), p_channel, 'lfg',
          jsonb_build_object('place_id', case when p_place_id ~ '^[0-9]{1,15}$' then p_place_id end, 'game', left(coalesce(p_game, 'a game'), 60),
                             'need', least(greatest(coalesce(p_need, 1), 1), 20), 'until', now() + interval '30 minutes'))
  returning id into m;
  return json_build_object('ok', true, 'id', m);
end
$$;

-- ---------- Achievement rarity ----------
create or replace function public.achievement_rarity() returns json
language sql stable security definer set search_path = public as $$
  with players as (select achievements from public.profiles where achievements is not null and last_seen > now() - interval '30 days')
  select json_build_object('players', (select count(*) from players),
    'pct', coalesce((select json_object_agg(a, round(100.0 * n / greatest((select count(*) from players), 1), 1))
                     from (select a, count(*) n from players, unnest(achievements) a group by a) x), '{}'::json))
$$;

-- ---------- Orbit Pass ----------
insert into public.app_config (key, value) values
  ('season', '{"id": "s1", "name": "Season 1: Supernova", "starts": "2026-11-09", "ends": "2027-01-11"}'::jsonb)
on conflict (key) do nothing;

create or replace function public._pass_tiers() returns jsonb
language sql immutable as $$
  select '[
    {"tier": 1, "hours": 1,  "free": "badge:s1_player",  "premium": "badge:s1_supernova"},
    {"tier": 2, "hours": 3,  "free": "banner:frostbite", "premium": "name:ice"},
    {"tier": 3, "hours": 6,  "free": "name:mint",        "premium": "banner:supernova"},
    {"tier": 4, "hours": 10, "free": "banner:midnight",  "premium": "name:galaxy"},
    {"tier": 5, "hours": 15, "free": "badge:s1_grinder", "premium": "banner:prism"},
    {"tier": 6, "hours": 25, "free": "name:sunset",      "premium": "name:chrome"},
    {"tier": 7, "hours": 40, "free": "banner:eclipse",   "premium": "badge:s1_elite"},
    {"tier": 8, "hours": 60, "free": "badge:s1_legend",  "premium": "banner:singularity"}
  ]'::jsonb
$$;

create or replace function public._season_hours(p_uid uuid) returns numeric
language sql stable security definer set search_path = public as $$
  select round(coalesce(sum(w.seconds), 0) / 3600.0, 1) from public.profile_weeks w, public.app_config c
   where c.key = 'season' and w.user_id = p_uid
     and w.week >= date_trunc('week', (c.value ->> 'starts')::date)::date and w.week < (c.value ->> 'ends')::date
$$;

create or replace function public.pass_info() returns json
language plpgsql stable security definer set search_path = public as $$
declare
  me uuid := auth.uid();
  sz jsonb := (select value from public.app_config where key = 'season');
begin
  if me is null then raise exception 'log in first'; end if;
  if sz is null then return json_build_object('found', false); end if;
  return json_build_object('found', true, 'season', sz, 'hours', public._season_hours(me), 'tiers', public._pass_tiers(),
    'premium', public._has_premium(me) or exists (select 1 from public.profiles where id = me and is_owner),
    'claimed', coalesce((select json_agg(c.tier || ':' || c.track) from public.pass_claims c where c.user_id = me and c.season = sz ->> 'id'), '[]'::json),
    'ended', now() >= (sz ->> 'ends')::date);
end
$$;

create or replace function public.pass_claim(p_tier int, p_track text) returns json
language plpgsql security definer set search_path = public as $$
declare
  me uuid := public._active();
  sz jsonb := (select value from public.app_config where key = 'season');
  t jsonb;
  reward text;
begin
  select x into t from jsonb_array_elements(public._pass_tiers()) x where (x ->> 'tier')::int = p_tier;
  if t is null or p_track not in ('free', 'premium') then return json_build_object('ok', false, 'reason', 'bad_tier'); end if;
  if public._season_hours(me) < (t ->> 'hours')::numeric then return json_build_object('ok', false, 'reason', 'locked'); end if;
  if p_track = 'premium' and not (public._has_premium(me) or exists (select 1 from public.profiles where id = me and is_owner)) then
    return json_build_object('ok', false, 'reason', 'premium');
  end if;
  if now() >= (sz ->> 'ends')::date then return json_build_object('ok', false, 'reason', 'season_over'); end if;
  insert into public.pass_claims (user_id, season, tier, track) values (me, sz ->> 'id', p_tier, p_track) on conflict do nothing;
  if not found then return json_build_object('ok', true, 'already', true); end if;
  reward := t ->> p_track;
  if reward like 'badge:%' then
    update public.profiles set badges = array(select distinct unnest(coalesce(badges, '{}') || array[substr(reward, 7)])) where id = me;
  else
    update public.profiles set unlocks = array(select distinct unnest(coalesce(unlocks, '{}') || array[reward])) where id = me;
  end if;
  return json_build_object('ok', true, 'reward', reward);
end
$$;

create or replace function public.owner_season_set(p_name text, p_starts date, p_ends date) returns json
language plpgsql security definer set search_path = public as $$
begin
  if not public.is_owner() then raise exception 'owner only'; end if;
  if p_ends <= p_starts then raise exception 'the season has to end after it starts'; end if;
  update public.app_config set value = value || jsonb_build_object('name', left(trim(p_name), 40), 'starts', p_starts, 'ends', p_ends), updated_at = now()
   where key = 'season';
  return json_build_object('ok', true);
end
$$;

create or replace function public.my_unlocks() returns json
language sql stable security definer set search_path = public as $$
  select to_json(coalesce(unlocks, '{}')) from public.profiles where id = auth.uid()
$$;

-- ---------- Crew officers ----------
create or replace function public._my_crew_staff() returns uuid
language plpgsql stable security definer set search_path = public as $$
declare
  me uuid := public._active();
  cid uuid;
begin
  select c.id into cid from public.crews c join public.crew_members m on m.crew_id = c.id
   where m.user_id = me and (c.leader = me or m.role = 'officer');
  if cid is null then raise exception 'crew leader only'; end if;
  return cid;
end
$$;

create or replace function public.crew_set_role(p_username text, p_role text) returns json
language plpgsql security definer set search_path = public as $$
declare
  cid uuid := public._my_led_crew();
  t uuid;
begin
  if p_role not in ('officer', 'member') then return json_build_object('ok', false, 'reason', 'bad_role'); end if;
  update public.crew_members m set role = p_role from public.profiles p
   where p.id = m.user_id and lower(p.username) = lower(p_username) and m.crew_id = cid and m.user_id <> auth.uid()
   returning m.user_id into t;
  if t is null then return json_build_object('ok', false, 'reason', 'not_member'); end if;
  if p_role = 'officer' then
    perform public._notify(t, 'crew', 'You''re now an officer of [' || (select tag from public.crews where id = cid) || ']', 'You can kick members, delete chat messages, reset the join code and schedule game nights.', '{"page":"social","tab":"crew"}'::jsonb);
  end if;
  return json_build_object('ok', true);
end
$$;

-- ---------- Game nights ----------
create or replace function public.crew_event_create(p_title text, p_place_id text, p_game text, p_at timestamptz) returns json
language plpgsql security definer set search_path = public as $$
declare
  cid uuid := public._my_crew_staff();
  title text := trim(coalesce(p_title, ''));
  eid bigint;
begin
  if length(title) < 3 or length(title) > 60 then return json_build_object('ok', false, 'reason', 'title'); end if;
  if public._bio_rule(title, true) is not null then return json_build_object('ok', false, 'reason', 'blocked'); end if;
  if p_at < now() or p_at > now() + interval '60 days' then return json_build_object('ok', false, 'reason', 'when'); end if;
  if (select count(*) from public.crew_events where crew_id = cid and at > now()) >= 10 then return json_build_object('ok', false, 'reason', 'too_many_events'); end if;
  insert into public.crew_events (crew_id, title, place_id, game, at, created_by)
  values (cid, title, case when p_place_id ~ '^[0-9]{1,15}$' then p_place_id end, left(p_game, 60), p_at, auth.uid()) returning id into eid;
  insert into public.crew_event_rsvps (event_id, user_id) values (eid, auth.uid()) on conflict do nothing;
  perform public._notify(m.user_id, 'event', '📅 New game night: ' || title, to_char(p_at at time zone 'UTC', 'Dy Mon DD HH24:MI') || ' UTC. RSVP on your crew page.', '{"page":"social","tab":"crew"}'::jsonb)
     from public.crew_members m where m.crew_id = cid and m.user_id <> auth.uid();
  return json_build_object('ok', true, 'id', eid);
end
$$;

create or replace function public.crew_event_rsvp(p_id bigint, p_going boolean) returns json
language plpgsql security definer set search_path = public as $$
declare
  me uuid := public._active();
begin
  if not exists (select 1 from public.crew_events e join public.crew_members m on m.crew_id = e.crew_id where e.id = p_id and m.user_id = me) then
    return json_build_object('ok', false, 'reason', 'gone');
  end if;
  if p_going then insert into public.crew_event_rsvps (event_id, user_id) values (p_id, me) on conflict do nothing;
  else delete from public.crew_event_rsvps where event_id = p_id and user_id = me; end if;
  return json_build_object('ok', true);
end
$$;

create or replace function public.crew_event_delete(p_id bigint) returns json
language plpgsql security definer set search_path = public as $$
begin
  delete from public.crew_events e where e.id = p_id and (e.created_by = auth.uid() or e.crew_id = (
    select c.id from public.crews c join public.crew_members m on m.crew_id = c.id where m.user_id = auth.uid() and (c.leader = auth.uid() or m.role = 'officer')));
  if not found then raise exception 'not allowed'; end if;
  return json_build_object('ok', true);
end
$$;

create or replace function public.crew_events() returns json
language plpgsql stable security definer set search_path = public as $$
declare
  me uuid := auth.uid();
  cid uuid := public._my_crew();
begin
  if cid is null then return json_build_object('found', false); end if;
  return json_build_object('found', true, 'events', coalesce((
    select json_agg(json_build_object('id', e.id, 'title', e.title, 'place_id', e.place_id, 'game', e.game, 'at', e.at,
             'host', h.username, 'host_roblox_id', h.roblox_id, 'mine', e.created_by = me,
             'going', (select coalesce(json_agg(p.username order by p.username), '[]'::json) from public.crew_event_rsvps r join public.profiles p on p.id = r.user_id where r.event_id = e.id),
             'me_going', exists (select 1 from public.crew_event_rsvps r where r.event_id = e.id and r.user_id = me)) order by e.at)
      from public.crew_events e left join public.profiles h on h.id = e.created_by
     where e.crew_id = cid and e.at > now() - interval '3 hours'), '[]'::json));
end
$$;

create or replace function public.owner_channel_set(p_id text, p_name text, p_emoji text, p_remove boolean default false) returns json
language plpgsql security definer set search_path = public as $$
begin
  if not public.is_owner() then raise exception 'owner only'; end if;
  if p_remove then
    if p_id = 'general' then raise exception 'General can''t be removed'; end if;
    delete from public.chat_channels where id = p_id;
  else
    insert into public.chat_channels (id, name, emoji) values (lower(p_id), left(trim(p_name), 30), left(p_emoji, 8))
    on conflict (id) do update set name = excluded.name, emoji = excluded.emoji;
  end if;
  return json_build_object('ok', true);
end
$$;

revoke execute on function public._notify(uuid, text, text, text, jsonb), public._mentions(text, uuid, text, uuid), public.inbox_list(), public.inbox_count(),
  public.inbox_read_all(), public.global_chat_react(bigint, text), public.global_lfg_post(text, text, text, int, text), public.achievement_rarity(),
  public._pass_tiers(), public._season_hours(uuid), public.pass_info(), public.pass_claim(int, text), public.owner_season_set(text, date, date), public.my_unlocks(),
  public._my_crew_staff(), public.crew_set_role(text, text), public.crew_event_create(text, text, text, timestamptz), public.crew_event_rsvp(bigint, boolean),
  public.crew_event_delete(bigint), public.crew_events(), public.owner_channel_set(text, text, text, boolean) from public, anon;
grant execute on function public.inbox_list(), public.inbox_count(), public.inbox_read_all(), public.global_chat_react(bigint, text),
  public.global_lfg_post(text, text, text, int, text), public.achievement_rarity(), public.pass_info(), public.pass_claim(int, text),
  public.owner_season_set(text, date, date), public.my_unlocks(), public.crew_set_role(text, text), public.crew_event_create(text, text, text, timestamptz),
  public.crew_event_rsvp(bigint, boolean), public.crew_event_delete(bigint), public.crew_events(), public.owner_channel_set(text, text, text, boolean) to authenticated;


-- ============================================================================
-- v2.21.1: no more automatic hiding or timeouts from chat reports. The owner decides.
-- ============================================================================
update public.global_messages set hidden = false where hidden and not deleted;
update public.crew_messages set hidden = false where hidden and not deleted;
