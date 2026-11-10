import os, json, time, importlib.util, tempfile
from pathlib import Path
tmp = Path(tempfile.mkdtemp()); os.environ["LOCALAPPDATA"] = str(tmp)
spec = importlib.util.spec_from_file_location("ol", "orbit_launcher.py"); ol = importlib.util.module_from_spec(spec); spec.loader.exec_module(ol)
ol.ensure_dirs()
print("LIVE accounts_on:", ol.accounts_on(), ol.ACCOUNT_URL)
for path in ("/auth/v1/settings",):
    try:
        st = ol._sb("GET", path)
        print("LIVE auth settings: autoconfirm =", st.get("mailer_autoconfirm"), "| signup disabled =", st.get("disable_signup"), "| email on =", (st.get("external") or {}).get("email"))
    except Exception as e:
        print("LIVE settings error:", e)
seed = os.urandom(32); ol.OWNER_PUBKEY = ol.ed_public(seed); ol.OWNER_KEY_FILE.write_text(json.dumps({"seed": seed.hex()}))
ol.revoked_premium_ids = lambda *a, **k: set()
api = ol.Api()
r = api.account_signup("orbit_selftest", "Selftest-Orbit-2026")
print("LIVE signup:", r.get("error") or r["account"])
if r.get("error"):
    r = api.account_login("orbit_selftest", "Selftest-Orbit-2026")
    print("LIVE login:", r.get("error") or r["account"])
print("LIVE wrong password:", (api.account_logout(), api.account_login("orbit_selftest", "nope-nope"))[1].get("error"))
r = api.account_login("orbit_selftest", "Selftest-Orbit-2026"); print("LIVE login again:", r.get("error") or r["account"]["user"]["username"])
print("LIVE dup signup:", api.account_signup("ORBIT_SELFTEST", "whatever123").get("error"))
_, code = ol.make_premium_key("orbit_selftest", 1)
r = api.activate_premium(code); print("LIVE redeem:", r.get("error") or r["status"]["active"])
print("LIVE status:", ol.premium_status(api._settings, True))
print("LIVE owner call (should say not owner):", api.owner_keylog("").get("error") if ol.is_owner() else "skip")
d = ol._load_account(); d["exp"] = 0; ol.save_json(ol.ACCOUNT_FILE, d)
print("LIVE refresh token:", bool(ol.account_token()), "| account check:", api.account(True).get("logged_in"))
api.account_logout(); print("LIVE after logout:", api.account())
