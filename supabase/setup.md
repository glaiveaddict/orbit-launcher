# Orbit accounts setup

1. Make a free project at https://supabase.com (any name, pick the region closest to most players).
2. Authentication > Sign In / Providers > Email: leave Email on and turn **Confirm email** off.
3. SQL Editor > New query: paste everything in `setup.sql` and press Run.
4. Project Settings > API Keys: copy the **Project URL** and the **publishable** (anon) key. Never share the secret (service_role) key.
5. Put those two values in `ACCOUNT_URL` and `ACCOUNT_KEY` in `orbit_launcher.py`.
6. After you make your own Orbit account, run this once in the SQL Editor so the owner panel can see the key log:

```sql
update public.profiles set is_owner = true where username = 'stabzane';
```

## Updating to v2.16 (profiles, friends, leaderboard)
Open SQL Editor > New query, paste everything in `setup.sql` again and press Run. It only adds what's missing, so running it again is safe.

To give someone an extra badge (Beta Tester, OG, Staff, Creator, Bug Hunter, Verified or Supporter), open their profile in Orbit (Social > Look up a player) on the owner PC. Founder and Premium badges are automatic.
