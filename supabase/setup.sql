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
