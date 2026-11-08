import hashlib
import base64
import calendar
import ipaddress
import json
import os
import re
import shutil
import struct
import subprocess
import sys
import threading
import time
import traceback
import urllib.error
import urllib.parse
import urllib.request
import uuid
import webbrowser
from pathlib import Path

APP_NAME = "Orbit Launcher"
APP_VERSION = "2.6.0"
APP_ID = "OrbitLauncher"
LAUNCH_FLAG = "--orbit-launch"
TOAST_FLAG = "--orbit-toast"
SETUP_FLAG = "--setup"
UNINSTALL_FLAG = "--uninstall"
IS_WINDOWS = os.name == "nt"
CREATE_NO_WINDOW = 0x08000000 if IS_WINDOWS else 0

if IS_WINDOWS:
    import ctypes
    import winreg

LOCALAPPDATA = Path(os.environ.get("LOCALAPPDATA", str(Path.home() / "AppData" / "Local")))
DATA_DIR = LOCALAPPDATA / APP_ID
SETTINGS_FILE = DATA_DIR / "settings.json"
PROFILES_DIR = DATA_DIR / "ModProfiles"
OLD_MODS_DIR = DATA_DIR / "Mods"
LOG_FILE = DATA_DIR / "launcher.log"
LAST_SERVER_FILE = DATA_DIR / "last_server.json"
PLAYTIME_FILE = DATA_DIR / "playtime.json"
SESSIONS_FILE = DATA_DIR / "sessions.json"
ACHIEVEMENTS_FILE = DATA_DIR / "achievements.json"
THUMBS_DIR = DATA_DIR / "Thumbs"
SHOW_FLAG = DATA_DIR / "show.flag"
MONITOR_FILE = DATA_DIR / "monitor.json"
GUI_FILE = DATA_DIR / "window.json"
CURRENT_FILE = DATA_DIR / "current.json"
PROBLEMS_FILE = DATA_DIR / "problems.json"
ROBLOX_VERSION_FILE = DATA_DIR / "roblox_version.json"
BACKGROUND_FILE = DATA_DIR / "background.json"
ATTACH_FLAG = "--orbit-attach"
BACKGROUND_FLAG = "--background"
RUN_KEY = r"Software\Microsoft\Windows\CurrentVersion\Run"
ICON_FILE = DATA_DIR / "roblox_icon.ico"
EXTENSIONS_DIR = DATA_DIR / "Extensions"
EXTENSION_NAME = "orbit_preview"
ROBLOX_LOGS = LOCALAPPDATA / "Roblox" / "logs"

PROTOCOLS = ["roblox-player", "roblox"]
MOD_MANIFEST = ".orbit_mods.json"
MOD_BACKUP_DIR = ".orbit_backup"
UPDATE_WATCH_SECONDS = 180
SHORTCUT_NAME = "Roblox (Orbit)"
INSTALL_DIR = LOCALAPPDATA / "Programs" / "Orbit"
INSTALLED_EXE = INSTALL_DIR / "OrbitLauncher.exe"
UPDATE_DIR = DATA_DIR / "Updates"
UNINSTALL_KEY = r"Software\Microsoft\Windows\CurrentVersion\Uninstall\OrbitLauncher"
PUBLISHER = "@stabzane"

CREDITS = [
    ("Founder/Owner", "@stabzane", 9544724076),
    ("Lead Developer", "@stabzane", 9544724076),
    ("Sounds/UI Designer", "@stabzane", 9544724076),
    ("Scripter", "@stabzane", 9544724076),
]

ACCENTS = {
    "Void": ["#9d6bff", "#d946ef"],
    "Nebula": ["#e879f9", "#f43f5e"],
    "Pulsar": ["#6366f1", "#22d3ee"],
    "Quasar": ["#38bdf8", "#818cf8"],
    "Aurora": ["#2dd4bf", "#a78bfa"],
    "Solar": ["#f59e0b", "#ef4444"],
}

ALLOWLIST = {
    "DFIntCSGLevelOfDetailSwitchingDistance",
    "DFIntCSGLevelOfDetailSwitchingDistanceL12",
    "DFIntCSGLevelOfDetailSwitchingDistanceL23",
    "DFIntCSGLevelOfDetailSwitchingDistanceL34",
    "FFlagHandleAltEnterFullscreenManually",
    "DFFlagTextureQualityOverrideEnabled",
    "DFIntTextureQualityOverride",
    "FIntDebugForceMSAASamples",
    "DFFlagDisableDPIScale",
    "FFlagDebugGraphicsPreferD3D11",
    "FFlagDebugSkyGray",
    "DFFlagDebugPauseVoxelizer",
    "DFIntDebugFRMQualityLevelOverride",
    "FIntFRMMaxGrassDistance",
    "FIntFRMMinGrassDistance",
    "FFlagDebugGraphicsPreferVulkan",
    "FFlagDebugGraphicsPreferOpenGL",
    "FIntGrassMovementReducedMotionFactor",
}

DEFAULT_PRESETS = {
    "graphics_api": "Automatic",
    "msaa": "Automatic",
    "texture_quality": "Automatic",
    "lighting_quality": "Automatic",
    "disable_dpi_scale": False,
    "exclusive_fullscreen": False,
    "gray_sky": False,
    "remove_grass": False,
    "low_poly_meshes": False,
}

DEFAULT_SETTINGS = {
    "presets": dict(DEFAULT_PRESETS),
    "custom_flags": {},
    "game_profiles": {},
    "apply_mods": True,
    "library": [],
    "launch_with": [],
    "performance": {"high_priority": False, "power_plan": False, "boost": False, "boost_level": "Max",
                    "boost_profiles": True, "fps_cap": None, "graphics_quality": None, "gpu_high": False,
                    "game_mode": False, "no_dvr": False, "gpu_applied": False, "bg_guard": True, "boost_backup": {}, "win_backup": {}},
    "smart_join": False,
    "sounds": {"pack": "Warp", "volume": 0.6},
    "last_seen_version": "",
    "saved_servers": [],
    "game_crosshairs": {},
    "font": "",
    "profile": {"roblox_id": None, "username": "", "display": ""},
    "recent_players": [],
    "emoji": "",
    "language": "en",
    "sync": {"folder": ""},
    "storage": {"auto_clean": False},
    "news_seen": [],
    "last_level": 0,
    "premium_key": "",
    "fps": {"enabled": False},
    "replay": {"enabled": False, "seconds": 30, "fps": 30},
    "overlay": {"keystrokes": False, "keys_pos": "Bottom right", "keys_cps": True, "crosshair": "",
                "crosshair_mode": "locked", "crosshair_size": 100},
    "hotkeys": {"enabled": True},
    "mod_profile": "Default",
    "discord": {
        "enabled": False,
        "client_id": "",
        "show_join_button": False,
        "show_game_icon": True,
        "webhook": "",
    },
    "session": {
        "server_popup": True,
        "track_playtime": True,
        "crash_rejoin": True,
        "server_badge": True,
        "badge_pos": "Top right",
        "badge_size": "Small",
        "start_with_windows": False,
        "badge_ping": True,
        "badge_timer": True,
        "break_minutes": 0,
        "sort_screenshots": False,
        "daily_minutes": 0,
        "auto_reconnect": True,
        "lag_alerts": True,
        "streamer_mode": False,
        "bedtime": "",
        "bedtime_action": "remind",
        "badge_fps": True,
        "session_report": True,
        "game_update_alerts": True,
    },
    "appearance": {
        "mode": "Dark",
        "accent": "Void",
        "custom_window_icon": False,
        "background": "Starfield",
        "bg_file": "",
        "bg_dim": 0.55,
        "tray": True,
        "close_to_tray": False,
        "custom_colors": ["#9d6bff", "#d946ef"],
        "splash": True,
        "ui_scale": "Normal",
    },
    "updates": {"auto": True, "roblox_predownload": True},
    "registration": {"registered": False, "backups": {}},
}
FREEFORM_KEYS = {"custom_flags", "backups", "game_profiles", "boost_backup", "win_backup", "game_crosshairs"}


def log(msg):
    line = time.strftime("%Y-%m-%d %H:%M:%S ") + str(msg)
    try:
        DATA_DIR.mkdir(parents=True, exist_ok=True)
        with open(LOG_FILE, "a", encoding="utf-8") as f:
            f.write(line + "\n")
    except OSError:
        pass
    if sys.stdout:
        try:
            print(line)
        except Exception:
            pass


def message_box(text, error=False):
    log(("ERROR: " if error else "") + text)
    if IS_WINDOWS:
        try:
            ctypes.windll.user32.MessageBoxW(None, text, APP_NAME, 0x10 if error else 0x40)
        except Exception:
            pass


def load_json(path, default):
    try:
        with open(path, encoding="utf-8") as f:
            return json.load(f)
    except (OSError, ValueError):
        return default


_SAVE_LOCK = threading.Lock()


def save_json(path, data):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_name(f"{path.name}.{os.getpid()}.{threading.get_ident()}.tmp")
    with _SAVE_LOCK:
        with open(tmp, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)
        for attempt in range(8):
            try:
                os.replace(tmp, path)
                return
            except PermissionError:
                if attempt == 7:
                    tmp.unlink(missing_ok=True)
                    raise
                time.sleep(0.05 * (attempt + 1))


def _merge(defaults, loaded):
    out = {}
    for key, value in defaults.items():
        if isinstance(value, dict) and key not in FREEFORM_KEYS:
            sub = loaded.get(key)
            out[key] = _merge(value, sub if isinstance(sub, dict) else {})
        else:
            out[key] = loaded.get(key, value)
    return out


def ensure_dirs():
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    if OLD_MODS_DIR.is_dir() and not PROFILES_DIR.exists():
        PROFILES_DIR.mkdir(parents=True)
        shutil.move(str(OLD_MODS_DIR), str(PROFILES_DIR / "Default"))
        log("Moved Mods into ModProfiles/Default")
    (PROFILES_DIR / "Default").mkdir(parents=True, exist_ok=True)


MAX_FPS_CAP = 240
UNLIMITED_FPS = 9999


def load_settings():
    loaded = load_json(SETTINGS_FILE, {})
    settings = _merge(DEFAULT_SETTINGS, loaded if isinstance(loaded, dict) else {})
    perf = settings.get("performance") or {}
    for holder in (perf, (perf.get("boost_backup") or {}).get("perf") or {}):
        cap = holder.get("fps_cap")
        if isinstance(cap, (int, float)) and cap > MAX_FPS_CAP and cap != UNLIMITED_FPS:
            holder["fps_cap"] = MAX_FPS_CAP
    return settings


def save_settings(settings):
    save_json(SETTINGS_FILE, settings)


def fetch_json(url, timeout=8):
    req = urllib.request.Request(url, headers={"User-Agent": APP_ID + "/" + APP_VERSION,
                                               "Accept": "application/json"})
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return json.loads(resp.read().decode("utf-8"))


def child_env(extra=None):
    env = {k: v for k, v in os.environ.items()
           if not (k.startswith("_PYI") or k.startswith("_MEI") or k in ("PYINSTALLER_RESET_ENVIRONMENT", "ORBIT_REEXEC"))}
    env["PYINSTALLER_RESET_ENVIRONMENT"] = "1"
    if is_frozen():
        mei = str(getattr(sys, "_MEIPASS", ""))
        if mei:
            env["PATH"] = os.pathsep.join(x for x in env.get("PATH", "").split(os.pathsep) if x and mei not in x)
    env.update(extra or {})
    return env


def stale_extraction():
    if not is_frozen() or os.environ.get("ORBIT_REEXEC"):
        return False
    built = (build_info() or {}).get("version")
    return bool(built) and built != APP_VERSION


def sys_tool(name):
    root = Path(os.environ.get("SystemRoot") or os.environ.get("windir") or r"C:\Windows")
    known = {"powershell": root / "System32" / "WindowsPowerShell" / "v1.0" / "powershell.exe",
             "explorer": root / "explorer.exe"}
    for candidate in (known.get(name), root / "System32" / f"{name}.exe", root / "Sysnative" / f"{name}.exe"):
        if candidate and candidate.exists():
            return str(candidate)
    return shutil.which(name) or name


def fmt_duration(seconds):
    seconds = int(seconds)
    h, m = seconds // 3600, (seconds % 3600) // 60
    if h:
        return f"{h}h {m}m"
    if m:
        return f"{m}m"
    return f"{seconds}s"


def fmt_ago(ts):
    delta = max(0, time.time() - ts)
    if delta < 90:
        return "just now"
    if delta < 3600:
        return f"{int(delta // 60)} min ago"
    if delta < 86400:
        return f"{int(delta // 3600)}h ago"
    return time.strftime("%b %d", time.localtime(ts))


HELPER_NAME = "OrbitHelper.exe"
ACTION_FLAG = "--orbit-action"
PREPARE_FLAG = "--prepare"


def is_helper():
    return is_frozen() and Path(sys.executable).name.lower() == HELPER_NAME.lower()


def helper_exe(version=APP_VERSION):
    return INSTALL_DIR / f"helper-{version}" / HELPER_NAME


def helper_ready():
    exe = helper_exe()
    return exe if exe.exists() and (exe.parent / "ready.txt").exists() else None


def ensure_helper():
    if not IS_WINDOWS or not is_frozen():
        return None
    if is_helper():
        return Path(sys.executable)
    exe = helper_ready()
    if not exe:
        src = resource_dir() / "helper.zip"
        if not src.exists():
            return None
        import zipfile
        final = helper_exe().parent
        tmp = final.with_name(final.name + ".tmp")
        shutil.rmtree(tmp, ignore_errors=True)
        started = time.time()
        with zipfile.ZipFile(src) as z:
            z.extractall(tmp)
        shutil.rmtree(final, ignore_errors=True)
        tmp.rename(final)
        (final / "ready.txt").write_text(APP_VERSION)
        exe = helper_exe()
        log(f"Unpacked the fast helper ({time.time() - started:.1f}s)")
    if not pids_named(HELPER_NAME):
        for old in INSTALL_DIR.glob("helper-*"):
            if old.is_dir() and old != exe.parent:
                shutil.rmtree(old, ignore_errors=True)
    return exe


def main_command(*args):
    if is_helper() and INSTALLED_EXE.exists():
        return [str(INSTALLED_EXE), *args]
    return self_command(*args)


def fast_command(*args):
    if is_helper() or not IS_WINDOWS or not is_frozen():
        return self_command(*args)
    exe = helper_ready()
    return [str(exe), *args] if exe else self_command(*args)


def self_command(*args):
    if getattr(sys, "frozen", False):
        return [sys.executable, *args]
    py = Path(sys.executable)
    pyw = py.with_name("pythonw.exe")
    return [str(pyw if pyw.exists() else py), str(Path(__file__).resolve()), *args]


def spawn_self(*args):
    fast = bool(args) and args[0] in (TOAST_FLAG, LAUNCH_FLAG, ATTACH_FLAG, BACKGROUND_FLAG, ACTION_FLAG)
    try:
        return subprocess.Popen(fast_command(*args) if fast else main_command(*args), creationflags=CREATE_NO_WINDOW,
                                env=child_env())
    except OSError as e:
        log(f"Could not start {args[:1]}: {e}")
        return None


_GAME_CACHE = {}
GAME_CACHE_FILE = DATA_DIR / "game_cache.json"
LOCATION_CACHE_FILE = DATA_DIR / "ip_locations.json"


def cached_game(place_id):
    entry = (load_json(GAME_CACHE_FILE, {}) or {}).get(str(place_id))
    if entry and time.time() - entry.get("at", 0) < 3 * 86400:
        return {k: v for k, v in entry.items() if k != "at"}
    return None


def game_info(place_id):
    place_id = str(place_id)
    if place_id in _GAME_CACHE:
        return _GAME_CACHE[place_id]
    disk = cached_game(place_id)
    if disk:
        _GAME_CACHE[place_id] = disk
        return disk
    info = {"name": f"Place {place_id}", "creator": None, "icon": None}
    try:
        universe = fetch_json(f"https://apis.roblox.com/universes/v1/places/{place_id}/universe")["universeId"]
        data = fetch_json(f"https://games.roblox.com/v1/games?universeIds={universe}")["data"][0]
        info["name"] = data.get("name") or info["name"]
        info["creator"] = (data.get("creator") or {}).get("name")
        icons = fetch_json("https://thumbnails.roblox.com/v1/games/icons?universeIds="
                           f"{universe}&returnPolicy=PlaceHolder&size=512x512&format=Png&isCircular=false")
        info["icon"] = icons["data"][0].get("imageUrl")
        info["universe"] = universe
        try:
            thumbs = fetch_json("https://thumbnails.roblox.com/v1/games/multiget/thumbnails?universeIds="
                                f"{universe}&countPerUniverse=1&defaults=true&size=768x432&format=Png&isCircular=false")
            info["thumb"] = thumbs["data"][0]["thumbnails"][0].get("imageUrl")
        except Exception:
            info["thumb"] = None
        _GAME_CACHE[place_id] = info
        try:
            cache = load_json(GAME_CACHE_FILE, {}) or {}
            cache[place_id] = {**info, "at": int(time.time())}
            if len(cache) > 300:
                cache = dict(sorted(cache.items(), key=lambda kv: kv[1].get("at", 0))[-300:])
            save_json(GAME_CACHE_FILE, cache)
        except Exception:
            pass
    except Exception as e:
        log(f"Game lookup failed for {place_id}: {e}")
    return info


def list_servers(place_id, pages=3):
    servers, cursor, note = [], "", None
    for _ in range(pages):
        url = (f"https://games.roblox.com/v1/games/{place_id}/servers/Public?sortOrder=Desc"
               f"&excludeFullGames=true&limit=100" + (f"&cursor={cursor}" if cursor else ""))
        try:
            data = fetch_json(url, timeout=10)
        except urllib.error.HTTPError as e:
            note = "Roblox is rate-limiting server lists right now. Try again in a minute." if e.code == 429 \
                else f"Roblox returned an error ({e.code})."
            break
        except Exception:
            note = "Couldn't reach Roblox."
            break
        for sv in data.get("data", []):
            servers.append({"id": sv.get("id"), "playing": sv.get("playing", 0), "max": sv.get("maxPlayers", 0),
                            "ping": sv.get("ping"), "fps": round(sv.get("fps") or 0, 1)})
        cursor = data.get("nextPageCursor")
        if not cursor:
            break
    return servers, note


def is_public_ip(ip):
    try:
        return ipaddress.ip_address(ip).is_global
    except ValueError:
        return False


def server_location(ip):
    if not is_public_ip(ip):
        return None
    cache = load_json(LOCATION_CACHE_FILE, {}) or {}
    hit = cache.get(ip)
    if hit and time.time() - hit[1] < 30 * 86400:
        return hit[0]
    try:
        d = fetch_json(f"https://ipinfo.io/{ip}/json", timeout=6)
    except Exception as e:
        log(f"Location lookup failed: {e}")
        return hit[0] if hit else None
    parts = []
    for part in (d.get("city"), d.get("region"), d.get("country")):
        if part and part not in parts:
            parts.append(part)
    location = ", ".join(parts) or None
    if location:
        cache[ip] = [location, int(time.time())]
        if len(cache) > 800:
            cache = dict(sorted(cache.items(), key=lambda kv: kv[1][1])[-800:])
        save_json(LOCATION_CACHE_FILE, cache)
    return location


def latest_roblox_version():
    try:
        return fetch_json("https://clientsettings.roblox.com/v2/client-version/WindowsPlayer").get("clientVersionUpload")
    except Exception as e:
        log(f"Version check failed: {e}")
        return None


def place_id_from_uri(uri):
    text = uri or ""
    for _ in range(3):
        text = urllib.parse.unquote(text)
    m = re.search(r"placeid[=:](\d+)", text, re.I)
    return m.group(1) if m else None


def parse_game_id(text):
    text = (text or "").strip()
    if text.isdigit():
        return text
    m = re.search(r"/games/(\d+)", text) or re.search(r"placeid=(\d+)", text, re.I)
    return m.group(1) if m else None


def rejoin_uri(place_id, job_id=None):
    uri = f"roblox://experiences/start?placeId={place_id}"
    if job_id:
        uri += f"&gameInstanceId={job_id}"
    return uri


def profile_for(settings, place_id=None):
    if place_id is not None:
        prof = settings.get("game_profiles", {}).get(str(place_id))
        if prof:
            presets = dict(DEFAULT_PRESETS)
            presets.update(prof.get("presets") or {})
            return presets, prof.get("custom_flags") or {}, prof.get("name")
    return settings["presets"], settings.get("custom_flags") or {}, None


def _flag_value(value):
    if isinstance(value, bool):
        return "True" if value else "False"
    return str(value)


def build_flags(settings, place_id=None):
    p, custom, _ = profile_for(settings, place_id)
    flags = {}

    api = p.get("graphics_api", "Automatic")
    if api == "Direct3D 11":
        flags["FFlagDebugGraphicsPreferD3D11"] = True
    elif api == "Vulkan":
        flags["FFlagDebugGraphicsPreferVulkan"] = True
    elif api == "OpenGL":
        flags["FFlagDebugGraphicsPreferOpenGL"] = True

    msaa = str(p.get("msaa", "Automatic"))
    if msaa != "Automatic":
        flags["FIntDebugForceMSAASamples"] = int(msaa.rstrip("x"))

    tq = str(p.get("texture_quality", "Automatic"))
    if tq != "Automatic":
        flags["DFFlagTextureQualityOverrideEnabled"] = True
        flags["DFIntTextureQualityOverride"] = int(tq.split(" ")[0])

    lq = str(p.get("lighting_quality", "Automatic"))
    if lq != "Automatic":
        flags["DFIntDebugFRMQualityLevelOverride"] = int(lq)

    if p.get("disable_dpi_scale"):
        flags["DFFlagDisableDPIScale"] = True
    if p.get("exclusive_fullscreen"):
        flags["FFlagHandleAltEnterFullscreenManually"] = False
    if p.get("gray_sky"):
        flags["FFlagDebugSkyGray"] = True
    if p.get("remove_grass"):
        flags["FIntFRMMinGrassDistance"] = 0
        flags["FIntFRMMaxGrassDistance"] = 0
    if p.get("low_poly_meshes"):
        for name in ("DFIntCSGLevelOfDetailSwitchingDistance",
                     "DFIntCSGLevelOfDetailSwitchingDistanceL12",
                     "DFIntCSGLevelOfDetailSwitchingDistanceL23",
                     "DFIntCSGLevelOfDetailSwitchingDistanceL34"):
            flags[name] = 0

    flags.update(custom)
    return {k: _flag_value(v) for k, v in flags.items()}


def write_flags(version_dir, flags):
    target = Path(version_dir) / "ClientSettings" / "ClientAppSettings.json"
    data = json.dumps(flags, indent=2)
    try:
        if target.exists() and target.read_text(encoding="utf-8") == data:
            return False
    except OSError:
        pass
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(data, encoding="utf-8")
    return True


def mods_dir(settings):
    return PROFILES_DIR / (settings.get("mod_profile") or "Default")


def list_mod_profiles():
    ensure_dirs()
    names = sorted((d.name for d in PROFILES_DIR.iterdir() if d.is_dir()), key=str.lower)
    names.remove("Default")
    return ["Default"] + names


def list_mods(folder):
    folder = Path(folder)
    if not folder.exists():
        return []
    return sorted(p.relative_to(folder).as_posix() for p in folder.rglob("*") if p.is_file())


def sync_mods(version_dir, folder=None, overrides=None):
    vdir = Path(version_dir)
    manifest_path = vdir / MOD_MANIFEST
    backup_root = vdir / MOD_BACKUP_DIR
    old = load_json(manifest_path, [])
    current = list_mods(folder) if folder else []
    overrides = {k: Path(v) for k, v in (overrides or {}).items() if v and Path(v).exists()}
    if overrides:
        current = sorted(set(current) | set(overrides))

    for rel in old:
        if rel in current:
            continue
        target, backup = vdir / rel, backup_root / rel
        try:
            if backup.exists():
                shutil.copy2(backup, target)
                backup.unlink()
            elif target.exists():
                target.unlink()
        except OSError as e:
            log(f"Could not restore {rel}: {e}")

    for rel in current:
        source = overrides.get(rel) or Path(folder) / rel
        target, backup = vdir / rel, backup_root / rel
        try:
            if rel not in old and target.exists() and not backup.exists():
                backup.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(target, backup)
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(source, target)
        except OSError as e:
            log(f"Could not apply mod {rel}: {e}")

    try:
        manifest_path.write_text(json.dumps(current), encoding="utf-8")
    except OSError:
        pass
    return len(current)


def version_roots():
    roots = [LOCALAPPDATA / "Roblox" / "Versions"]
    for env in ("ProgramFiles(x86)", "ProgramFiles"):
        if os.environ.get(env):
            roots.append(Path(os.environ[env]) / "Roblox" / "Versions")
    return [r for r in roots if r.is_dir()]


def all_version_dirs():
    dirs = []
    for root in version_roots():
        try:
            dirs += [d for d in root.iterdir() if d.is_dir() and d.name.startswith("version-")]
        except OSError:
            pass
    return dirs


def player_dirs():
    found = [d for d in all_version_dirs() if (d / "RobloxPlayerBeta.exe").exists()]
    found.sort(key=lambda d: (d / "RobloxPlayerBeta.exe").stat().st_mtime, reverse=True)
    return found


def mods_folder_for(settings, place_id=None):
    if not settings.get("apply_mods", True):
        return None
    if place_id is not None:
        for game in settings.get("library") or []:
            if str(game.get("pid")) == str(place_id) and game.get("mod_profile"):
                folder = PROFILES_DIR / game["mod_profile"]
                if folder.is_dir():
                    return folder
    return mods_dir(settings)


def apply_all(settings, version_dir=None, place_id=None):
    ensure_dirs()
    dirs = [Path(version_dir)] if version_dir else player_dirs()[:1]
    flags = build_flags(settings, place_id)
    folder = mods_folder_for(settings, place_id)
    for d in dirs:
        write_flags(d, flags)
        try:
            apply_system_boost(settings, d)
        except Exception as e:
            log(f"System boost failed: {e}")
        overrides = {}
        if settings.get("apply_mods", True):
            try:
                overrides.update(font_overrides(settings, d))
            except Exception as e:
                log(f"Font mod failed: {e}")
        emoji = emoji_source(settings.get("emoji") or "") if settings.get("apply_mods", True) else None
        if emoji:
            overrides["content/fonts/TwemojiMozilla.ttf"] = emoji
        cross = (settings.get("game_crosshairs") or {}).get(str(place_id)) if place_id is not None else None
        if cross and settings.get("apply_mods", True):
            src = crosshair_source(cross)
            if src:
                overrides["content/textures/MouseLockedCursor.png"] = src
        n = sync_mods(d, folder, overrides)
        _, _, prof = profile_for(settings, place_id)
        log(f"Applied {len(flags)} flag(s){' [' + prof + ' profile]' if prof else ''} "
            f"and {n} mod file(s) to {d.name}")
    return dirs


GBS_FILE = LOCALAPPDATA / "Roblox" / "GlobalBasicSettings_13.xml"
BOOST_KEYS = ("graphics_api", "msaa", "texture_quality", "lighting_quality", "remove_grass", "low_poly_meshes")
QUICK_PRESETS = {
    "Potato": {"graphics_api": "Direct3D 11", "msaa": "1x", "texture_quality": "0 (lowest)", "lighting_quality": "1",
               "remove_grass": True, "low_poly_meshes": True},
    "Balanced": {"graphics_api": "Direct3D 11", "msaa": "1x", "texture_quality": "2", "lighting_quality": "Automatic",
                 "remove_grass": True, "low_poly_meshes": False},
    "Quality": {"graphics_api": "Automatic", "msaa": "4x", "texture_quality": "3 (highest)", "lighting_quality": "21",
                "remove_grass": False, "low_poly_meshes": False},
    "Reset": {k: DEFAULT_PRESETS[k] for k in BOOST_KEYS},
}
WIN_TWEAKS = {
    "game_mode": [(r"Software\Microsoft\GameBar", "AutoGameModeEnabled", 1)],
    "no_dvr": [(r"System\GameConfigStore", "GameDVR_Enabled", 0),
               (r"Software\Microsoft\Windows\CurrentVersion\GameDVR", "AppCaptureEnabled", 0)],
}
GPU_PREF_KEY = r"Software\Microsoft\DirectX\UserGpuPreferences"


def _reg_get(path, name):
    try:
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER, path) as k:
            return winreg.QueryValueEx(k, name)[0]
    except OSError:
        return None


def _reg_set(path, name, value):
    kind = winreg.REG_SZ if isinstance(value, str) else winreg.REG_DWORD
    with winreg.CreateKeyEx(winreg.HKEY_CURRENT_USER, path, 0, winreg.KEY_SET_VALUE) as k:
        winreg.SetValueEx(k, name, 0, kind, value)


def _reg_del(path, name):
    try:
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER, path, 0, winreg.KEY_SET_VALUE) as k:
            winreg.DeleteValue(k, name)
    except OSError:
        pass


def write_gbs(perf):
    cap, quality = perf.get("fps_cap"), perf.get("graphics_quality")
    if not GBS_FILE.exists() or roblox_running():
        return False
    text = GBS_FILE.read_text(encoding="utf-8", errors="ignore")
    if cap is not None:
        cap = UNLIMITED_FPS if int(cap) >= UNLIMITED_FPS else max(30, min(MAX_FPS_CAP, int(cap)))
    elif (DATA_DIR / "GlobalBasicSettings_13.orbit-backup.xml").exists():
        m = re.search(r'<int name="FramerateCap">(-?\d+)</int>', text)
        if m and int(m.group(1)) > MAX_FPS_CAP:
            cap = MAX_FPS_CAP
    if cap is None and not quality:
        return False
    new = text
    if cap is not None:
        new = re.sub(r'(<int name="FramerateCap">)-?\d+(</int>)', rf"\g<1>{int(cap)}\g<2>", new)
    if quality:
        q = max(1, min(10, int(quality)))
        new = re.sub(r'(<token name="SavedQualityLevel">)\d+(</token>)', rf"\g<1>{q}\g<2>", new)
        new = re.sub(r'(<int name="GraphicsQualityLevel">)\d+(</int>)', rf"\g<1>{q}\g<2>", new)
    if new == text:
        return False
    backup = DATA_DIR / "GlobalBasicSettings_13.orbit-backup.xml"
    if not backup.exists():
        shutil.copy2(GBS_FILE, backup)
    GBS_FILE.write_text(new, encoding="utf-8")
    log(f"Set Roblox frame rate cap to {cap if cap is not None else 'unchanged'} and graphics quality to {quality or 'unchanged'}")
    return True


def apply_win_tweaks(perf):
    backup = perf.setdefault("win_backup", {})
    changed = False
    for key, entries in WIN_TWEAKS.items():
        for path, name, value in entries:
            slot = path + "|" + name
            if perf.get(key):
                if slot not in backup:
                    backup[slot] = _reg_get(path, name)
                if _reg_get(path, name) != value:
                    _reg_set(path, name, value)
                    changed = True
            elif slot in backup:
                old = backup.pop(slot)
                if old is None:
                    _reg_del(path, name)
                else:
                    _reg_set(path, name, old)
                changed = True
    return changed


def set_gpu_pref(version_dir, on):
    exe = str(Path(version_dir) / "RobloxPlayerBeta.exe") if version_dir else None
    try:
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER, GPU_PREF_KEY) as k:
            names, i = [], 0
            while True:
                try:
                    names.append(winreg.EnumValue(k, i)[0])
                    i += 1
                except OSError:
                    break
    except OSError:
        names = []
    for name in names:
        if name.lower().endswith("robloxplayerbeta.exe") and (not on or name != exe or not Path(name).exists()):
            _reg_del(GPU_PREF_KEY, name)
    if on and exe:
        _reg_set(GPU_PREF_KEY, exe, "GpuPreference=2;")


def apply_system_boost(settings, version_dir=None):
    if not IS_WINDOWS:
        return
    perf = settings.setdefault("performance", {})
    write_gbs(perf)
    before = json.dumps(perf.get("win_backup", {}), sort_keys=True)
    apply_win_tweaks(perf)
    if perf.get("gpu_high") or perf.get("gpu_applied"):
        set_gpu_pref(version_dir, bool(perf.get("gpu_high")))
        perf["gpu_applied"] = bool(perf.get("gpu_high"))
    if json.dumps(perf.get("win_backup", {}), sort_keys=True) != before:
        save_settings(settings)


def set_boost(settings, on, level="Max"):
    perf = settings["performance"]
    targets = [settings["presets"]]
    if perf.get("boost_profiles", True):
        targets += [g.setdefault("presets", {}) for g in settings["game_profiles"].values()]
    if on:
        if not perf.get("boost"):
            perf["boost_backup"] = {"presets": {k: settings["presets"].get(k) for k in BOOST_KEYS},
                                    "profiles": {pid: {k: g.get("presets", {}).get(k) for k in BOOST_KEYS}
                                                 for pid, g in settings["game_profiles"].items()},
                                    "perf": {k: perf.get(k) for k in ("high_priority", "power_plan", "gpu_high",
                                                                     "game_mode", "no_dvr", "fps_cap",
                                                                     "graphics_quality")}}
        preset = QUICK_PRESETS["Potato" if level == "Max" else "Balanced"]
        for t in targets:
            t.update(preset)
        perf.update({"boost": True, "boost_level": level, "high_priority": True, "power_plan": True,
                     "gpu_high": True, "game_mode": True, "no_dvr": True})
        if perf.get("fps_cap") is None:
            perf["fps_cap"] = 240
        if not perf.get("graphics_quality"):
            perf["graphics_quality"] = 1 if level == "Max" else 4
    else:
        backup = perf.pop("boost_backup", None) or {}
        settings["presets"].update({k: v for k, v in (backup.get("presets") or {}).items() if v is not None})
        for pid, old in (backup.get("profiles") or {}).items():
            if pid in settings["game_profiles"]:
                pre = settings["game_profiles"][pid].setdefault("presets", {})
                for k, v in old.items():
                    if v is None:
                        pre.pop(k, None)
                    else:
                        pre[k] = v
        for k, v in (backup.get("perf") or {}).items():
            perf[k] = v
        perf["boost"] = False
    save_settings(settings)
    if not roblox_running():
        apply_all(settings)
    else:
        apply_system_boost(settings, (player_dirs()[:1] or [None])[0])
    log(f"FPS boost {'on (' + level + ')' if on else 'off'}")


def apply_quick_preset(settings, name, place_id=None):
    if name not in QUICK_PRESETS:
        raise ValueError("Unknown preset")
    target = settings["game_profiles"][str(place_id)].setdefault("presets", {}) if place_id else settings["presets"]
    target.update(QUICK_PRESETS[name])
    save_settings(settings)


_PE32 = None


def process_table():
    global _PE32
    if not IS_WINDOWS:
        return None
    try:
        if _PE32 is None:
            class PE32(ctypes.Structure):
                _fields_ = [("dwSize", ctypes.c_ulong), ("cntUsage", ctypes.c_ulong), ("th32ProcessID", ctypes.c_ulong),
                            ("th32DefaultHeapID", ctypes.c_void_p), ("th32ModuleID", ctypes.c_ulong),
                            ("cntThreads", ctypes.c_ulong), ("th32ParentProcessID", ctypes.c_ulong),
                            ("pcPriClassBase", ctypes.c_long), ("dwFlags", ctypes.c_ulong),
                            ("szExeFile", ctypes.c_wchar * 260)]
            _PE32 = PE32
        k32 = ctypes.WinDLL("kernel32", use_last_error=True)
        k32.CreateToolhelp32Snapshot.restype = ctypes.c_void_p
        k32.CreateToolhelp32Snapshot.argtypes = [ctypes.c_ulong, ctypes.c_ulong]
        k32.Process32FirstW.argtypes = [ctypes.c_void_p, ctypes.POINTER(_PE32)]
        k32.Process32NextW.argtypes = [ctypes.c_void_p, ctypes.POINTER(_PE32)]
        k32.CloseHandle.argtypes = [ctypes.c_void_p]
        snap = k32.CreateToolhelp32Snapshot(0x2, 0)
        if not snap or snap == ctypes.c_void_p(-1).value:
            return None
        entry = _PE32()
        entry.dwSize = ctypes.sizeof(_PE32)
        out = []
        try:
            ok = k32.Process32FirstW(snap, ctypes.byref(entry))
            while ok:
                out.append((int(entry.th32ProcessID), int(entry.th32ParentProcessID), entry.szExeFile))
                ok = k32.Process32NextW(snap, ctypes.byref(entry))
        finally:
            k32.CloseHandle(snap)
        return out
    except Exception:
        return None


def pids_named(image):
    table = process_table()
    if table is not None:
        return [pid for pid, _, name in table if name.lower() == image.lower()]
    try:
        out = subprocess.run([sys_tool("tasklist"), "/FO", "CSV", "/NH", "/FI", f"IMAGENAME eq {image}"],
                             capture_output=True, text=True, timeout=15, creationflags=CREATE_NO_WINDOW).stdout
    except Exception:
        return []
    pids = []
    for row in out.splitlines():
        parts = [x.strip('"') for x in row.split('","')]
        if len(parts) > 1 and parts[1].isdigit():
            pids.append(int(parts[1]))
    return pids


def _open_process(pid, access):
    k32 = ctypes.WinDLL("kernel32", use_last_error=True)
    k32.OpenProcess.restype = ctypes.c_void_p
    k32.OpenProcess.argtypes = [ctypes.c_ulong, ctypes.c_bool, ctypes.c_ulong]
    return k32, k32.OpenProcess(access, False, int(pid))


def kill_tree(pid):
    if not pid or not IS_WINDOWS:
        return
    pid = int(pid)
    table = process_table()
    if table is None:
        subprocess.run([sys_tool("taskkill"), "/PID", str(pid), "/T", "/F"], capture_output=True, timeout=20,
                       creationflags=CREATE_NO_WINDOW)
        return
    victims, frontier = [pid], [pid]
    while frontier:
        kids = [c for c, parent, _ in table if parent in frontier and c not in victims]
        victims += kids
        frontier = kids
    for victim in reversed(victims):
        try:
            k32, h = _open_process(victim, 0x0001)
            if h:
                k32.TerminateProcess.argtypes = [ctypes.c_void_p, ctypes.c_uint]
                k32.TerminateProcess(h, 1)
                k32.CloseHandle.argtypes = [ctypes.c_void_p]
                k32.CloseHandle(h)
        except Exception:
            pass


def set_priority(pid=None, image=None, cls=0x00008000):
    if not IS_WINDOWS:
        return 0
    done = 0
    targets = [pid] if pid else pids_named(image)
    for target in targets:
        try:
            k32, h = _open_process(target, 0x0200 | 0x1000)
            if h:
                k32.SetPriorityClass.argtypes = [ctypes.c_void_p, ctypes.c_ulong]
                done += bool(k32.SetPriorityClass(h, cls))
                k32.CloseHandle.argtypes = [ctypes.c_void_p]
                k32.CloseHandle(h)
        except Exception:
            pass
    return done


def set_power_throttle(pid, on):
    if not IS_WINDOWS:
        return False
    try:
        class PPTS(ctypes.Structure):
            _fields_ = [("Version", ctypes.c_ulong), ("ControlMask", ctypes.c_ulong), ("StateMask", ctypes.c_ulong)]
        st = PPTS(1, 1 if on else 0, 1 if on else 0)
        k32, h = _open_process(pid, 0x0200)
        if not h:
            return False
        k32.SetProcessInformation.argtypes = [ctypes.c_void_p, ctypes.c_int, ctypes.c_void_p, ctypes.c_ulong]
        ok = bool(k32.SetProcessInformation(h, 4, ctypes.byref(st), ctypes.sizeof(st)))
        k32.CloseHandle.argtypes = [ctypes.c_void_p]
        k32.CloseHandle(h)
        return ok
    except Exception:
        return False


class BackgroundGuard:
    def __init__(self, perf):
        self.perf = perf or {}
        self.dimmed = False
        self.stop_event = threading.Event()
        self.pids = []
        self.pids_at = 0

    def _pids(self):
        if time.time() - self.pids_at > 5:
            self.pids, self.pids_at = pids_named("RobloxPlayerBeta.exe"), time.time()
        return self.pids

    def apply(self, dim):
        normal = 0x00008000 if self.perf.get("high_priority") else 0x00000020
        for pid in self._pids():
            set_priority(pid=pid, cls=0x00004000 if dim else normal)
            set_power_throttle(pid, dim)
        self.dimmed = dim

    def run(self):
        while not self.stop_event.wait(0.35):
            try:
                if not self._pids():
                    continue
                front = roblox_in_front()
                if not front and not self.dimmed:
                    self.apply(True)
                elif front and self.dimmed:
                    self.apply(False)
            except Exception:
                pass
        if self.dimmed:
            self.apply(False)

    def start(self):
        threading.Thread(target=self.run, daemon=True).start()
        return self

    def stop(self):
        self.stop_event.set()


def raise_own_priority():
    if IS_WINDOWS:
        try:
            k32 = ctypes.windll.kernel32
            k32.GetCurrentProcess.restype = ctypes.c_void_p
            k32.SetPriorityClass.argtypes = [ctypes.c_void_p, ctypes.c_ulong]
            k32.SetPriorityClass(k32.GetCurrentProcess(), 0x00008000)
        except Exception:
            pass


def roblox_running():
    if not IS_WINDOWS:
        return False
    return bool(pids_named("RobloxPlayerBeta.exe"))


def our_command(exe=None):
    if exe:
        return f'"{exe}" {LAUNCH_FLAG} "%1"'
    cmd = fast_command(LAUNCH_FLAG)
    return " ".join(f'"{part}"' for part in cmd[:-1]) + f' {LAUNCH_FLAG} "%1"'


def should_claim_links(current):
    if current == our_command():
        return False
    low = (current or "").lower()
    if "orbithelper" in low or "orbitlauncher" in low:
        m = re.search(r"helper-(\d+(?:\.\d+)*)", low)
        path = re.match(r'\s*"([^"]+)"', current or "")
        if path and not Path(path.group(1)).exists():
            return True
        if m and parse_version(m.group(1)) > parse_version(APP_VERSION):
            return False
        return True
    return True


def _cmd_key(proto):
    return rf"Software\Classes\{proto}\shell\open\command"


def read_protocol_command(proto):
    try:
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER, _cmd_key(proto)) as k:
            return winreg.QueryValueEx(k, "")[0]
    except OSError:
        return None


def is_registered():
    if not IS_WINDOWS:
        return False
    return all(LAUNCH_FLAG in (read_protocol_command(p) or "") for p in PROTOCOLS)


def register_protocols(settings, exe=None):
    reg = settings["registration"]
    backups = reg.setdefault("backups", {})
    for proto in PROTOCOLS:
        current = read_protocol_command(proto)
        if current is None or LAUNCH_FLAG not in current:
            backups[proto] = current
        with winreg.CreateKey(winreg.HKEY_CURRENT_USER, rf"Software\Classes\{proto}") as base:
            winreg.SetValueEx(base, "", 0, winreg.REG_SZ, f"URL: {proto} Protocol")
            winreg.SetValueEx(base, "URL Protocol", 0, winreg.REG_SZ, "")
        with winreg.CreateKey(winreg.HKEY_CURRENT_USER, _cmd_key(proto)) as k:
            winreg.SetValueEx(k, "", 0, winreg.REG_SZ, our_command(exe))
    reg["registered"] = True
    save_settings(settings)
    log("Registered as Roblox protocol handler")


def _delete_tree(root, path):
    try:
        with winreg.OpenKey(root, path, 0, winreg.KEY_ALL_ACCESS) as k:
            while True:
                try:
                    sub = winreg.EnumKey(k, 0)
                except OSError:
                    break
                _delete_tree(root, path + "\\" + sub)
        winreg.DeleteKey(root, path)
    except OSError:
        pass


def unregister_protocols(settings):
    reg = settings["registration"]
    backups = reg.get("backups", {})
    players = player_dirs()
    fallback = f'"{players[0] / "RobloxPlayerBeta.exe"}" %1' if players else None
    for proto in PROTOCOLS:
        original = backups.get(proto, "missing")
        if original is None:
            _delete_tree(winreg.HKEY_CURRENT_USER, rf"Software\Classes\{proto}")
            continue
        if original == "missing" or not isinstance(original, str):
            original = fallback
        else:
            m = re.match(r'^"([^"]+)"', original)
            if m and not Path(m.group(1)).exists():
                original = fallback
        if original:
            with winreg.CreateKey(winreg.HKEY_CURRENT_USER, _cmd_key(proto)) as k:
                winreg.SetValueEx(k, "", 0, winreg.REG_SZ, original)
    reg["registered"] = False
    reg["backups"] = {}
    save_settings(settings)
    log("Restored the original Roblox protocol handler")


class WindowIcon:

    WM_SETICON = 0x0080

    def __init__(self, path):
        u = ctypes.windll.user32
        u.LoadImageW.restype = ctypes.c_void_p
        u.LoadImageW.argtypes = [ctypes.c_void_p, ctypes.c_wchar_p, ctypes.c_uint,
                                 ctypes.c_int, ctypes.c_int, ctypes.c_uint]
        u.FindWindowW.restype = ctypes.c_void_p
        u.FindWindowW.argtypes = [ctypes.c_wchar_p, ctypes.c_wchar_p]
        u.PostMessageW.argtypes = [ctypes.c_void_p, ctypes.c_uint, ctypes.c_size_t, ctypes.c_ssize_t]
        self.user32 = u
        LR_LOADFROMFILE, IMAGE_ICON = 0x10, 1
        self.big = u.LoadImageW(None, str(path), IMAGE_ICON, 32, 32, LR_LOADFROMFILE)
        self.small = u.LoadImageW(None, str(path), IMAGE_ICON, 16, 16, LR_LOADFROMFILE)
        if not self.big:
            log("Could not load the custom icon (is it a real .ico file?)")

    def apply(self):
        if not self.big:
            return
        hwnd = self.user32.FindWindowW(None, "Roblox")
        if hwnd:
            self.user32.PostMessageW(hwnd, self.WM_SETICON, 1, self.big)
            self.user32.PostMessageW(hwnd, self.WM_SETICON, 0, self.small or self.big)


def create_shortcut(location, name=SHORTCUT_NAME, launch=True, exe=None):
    if exe:
        cmd = [str(exe), LAUNCH_FLAG] if launch else [str(exe)]
    else:
        cmd = self_command(LAUNCH_FLAG) if launch else self_command()
    target, arguments = cmd[0], " ".join(a if a.startswith("--") else f'"{a}"' for a in cmd[1:])
    if launch and ICON_FILE.exists():
        icon = str(ICON_FILE)
    elif exe:
        icon = str(exe)
    elif getattr(sys, "frozen", False):
        icon = sys.executable
    elif not launch and app_icon_file().exists():
        icon = str(app_icon_file())
    else:
        players = player_dirs()
        icon = str(players[0] / "RobloxPlayerBeta.exe") if players else target

    def q(s):
        return "'" + str(s).replace("'", "''") + "'"

    ps = (f"$d=[Environment]::GetFolderPath('{location}');"
          f"$p=Join-Path $d {q(name + '.lnk')};"
          "$s=(New-Object -ComObject WScript.Shell).CreateShortcut($p);"
          f"$s.TargetPath={q(target)};$s.Arguments={q(arguments)};"
          f"$s.IconLocation={q(icon + ',0')};$s.Description={q(name)};"
          "$s.Save();Write-Output $p")
    out = subprocess.run([sys_tool("powershell"), "-NoProfile", "-ExecutionPolicy", "Bypass", "-Command", ps],
                         capture_output=True, text=True, creationflags=CREATE_NO_WINDOW)
    if out.returncode != 0:
        raise OSError(out.stderr.strip() or "PowerShell failed")
    return out.stdout.strip()


class DiscordIPC:
    def __init__(self, client_id):
        self.client_id = client_id
        self.pipe = None

    def connect(self):
        for i in range(10):
            try:
                self.pipe = open(rf"\\.\pipe\discord-ipc-{i}", "r+b", buffering=0)
            except OSError:
                continue
            try:
                self._send(0, {"v": 1, "client_id": self.client_id})
                return True
            except Exception as e:
                log(f"Discord handshake failed: {e}")
                self.close()
        return False

    def _read_exact(self, n):
        buf = b""
        while len(buf) < n:
            chunk = self.pipe.read(n - len(buf))
            if not chunk:
                raise OSError("Discord pipe closed")
            buf += chunk
        return buf

    def _send(self, op, payload):
        data = json.dumps(payload).encode("utf-8")
        self.pipe.write(struct.pack("<ii", op, len(data)) + data)
        _, length = struct.unpack("<ii", self._read_exact(8))
        reply = json.loads(self._read_exact(length).decode("utf-8"))
        if reply.get("evt") == "ERROR":
            log(f"Discord error: {reply.get('data')}")
        return reply

    def set_activity(self, activity):
        if not self.pipe and not self.connect():
            return False
        try:
            self._send(1, {"cmd": "SET_ACTIVITY", "args": {"pid": os.getpid(), "activity": activity},
                           "nonce": str(uuid.uuid4())})
            return True
        except Exception as e:
            log(f"Discord update failed: {e}")
            self.close()
            return False

    def close(self):
        if self.pipe:
            try:
                self.pipe.close()
            except OSError:
                pass
        self.pipe = None


def _pad(text):
    text = (text or "").strip()[:128]
    return text if len(text) >= 2 else (text + "  ")[:2]


def build_activity(discord, place_id, job_id, info, joined):
    act = {
        "details": _pad(info["name"]),
        "state": _pad(f"by {info['creator']}" if info.get("creator") else "Playing Roblox"),
        "timestamps": {"start": int(joined)},
        "assets": {"large_image": info["icon"] if discord.get("show_game_icon") and info.get("icon") else "roblox",
                   "large_text": _pad(info["name"])},
    }
    buttons = []
    if discord.get("show_join_button") and job_id and not load_settings()["session"].get("streamer_mode"):
        buttons.append({"label": "Join server",
                        "url": f"https://www.roblox.com/games/start?placeId={place_id}&gameInstanceId={job_id}"})
    buttons.append({"label": "See game page", "url": f"https://www.roblox.com/games/{place_id}"})
    act["buttons"] = buttons
    return act


JOIN_RE = re.compile(r"! Joining game '([0-9a-fA-F\-]{36})' place (\d+) at ([0-9.]+)")
UDMUX_RE = re.compile(r"UDMUX Address = ([0-9.]+), Port = \d+ \| RCC Server Address = ([0-9.]+)")
LOG_TS_RE = re.compile(r"^(\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2})(?:\.(\d+))?Z")
LEAVE_MARKERS = ("leaveUGCGameInternal", "Time to disconnect replication data")


def record_playtime(place_id, name, seconds):
    if seconds < 5:
        return
    data = load_json(PLAYTIME_FILE, {})
    entry = data.setdefault(str(place_id), {"name": None, "seconds": 0, "sessions": 0, "last_played": 0})
    if name:
        entry["name"] = name
    entry["name"] = entry.get("name") or f"Place {place_id}"
    entry["seconds"] = int(entry.get("seconds", 0) + seconds)
    entry["sessions"] = int(entry.get("sessions", 0)) + 1
    entry["last_played"] = int(time.time())
    save_json(PLAYTIME_FILE, data)


def record_session(game, seconds):
    if seconds < 5:
        return
    data = load_json(SESSIONS_FILE, [])
    if not isinstance(data, list):
        data = []
    entry = {"place_id": str(game["place_id"]), "job_id": game.get("job_id"),
             "name": game.get("name") or f"Place {game['place_id']}", "start": int(game["joined"]),
             "end": int(game["joined"] + seconds), "seconds": int(seconds), "location": game.get("location")}
    summary = ping_summary(game.get("pings") or [])
    if summary:
        entry["ping"] = summary
    if game.get("fps"):
        entry["fps"] = game["fps"]
    data.append(entry)
    save_json(SESSIONS_FILE, data[-1500:])


def process_running(image):
    if not IS_WINDOWS:
        return False
    return bool(pids_named(image))


class PerfBoost:
    def __init__(self, perf):
        self.perf = perf or {}
        self.prev_scheme = None
        self.priority_set = False

    @property
    def active(self):
        return bool(self.perf.get("high_priority") or self.perf.get("power_plan"))

    def begin(self):
        if not IS_WINDOWS or not self.perf.get("power_plan"):
            return
        try:
            out = subprocess.run([sys_tool("powercfg"), "/getactivescheme"], capture_output=True, text=True,
                                 creationflags=CREATE_NO_WINDOW).stdout
            m = re.search(r"([0-9a-fA-F-]{36})", out)
            self.prev_scheme = m.group(1) if m else None
            subprocess.run([sys_tool("powercfg"), "/setactive", "SCHEME_MIN"], capture_output=True, creationflags=CREATE_NO_WINDOW)
            log("Switched to the high performance power plan")
        except Exception as e:
            log(f"Power plan change failed: {e}")

    def tick(self):
        if self.priority_set or not IS_WINDOWS or not self.perf.get("high_priority") or not roblox_running():
            return
        self.priority_set = True
        n = set_priority(image="RobloxPlayerBeta.exe", cls=0x00008000)
        log(f"Set Roblox to above-normal priority ({n} process{'es' if n != 1 else ''})")

    def end(self):
        if self.prev_scheme:
            subprocess.run([sys_tool("powercfg"), "/setactive", self.prev_scheme], capture_output=True,
                           creationflags=CREATE_NO_WINDOW)
            log("Restored the previous power plan")
            self.prev_scheme = None


def start_companions(settings):
    started = []
    for app in settings.get("launch_with") or []:
        path = Path(app.get("path") or "")
        if not path.is_file() or process_running(path.name):
            continue
        try:
            subprocess.Popen([str(path)], cwd=str(path.parent), env=child_env())
            started.append(app)
            log(f"Started {path.name}")
        except OSError as e:
            log(f"Couldn't start {path.name}: {e}")
    return started


def close_companions(started):
    for app in started:
        if app.get("close_after"):
            name = Path(app.get("path") or "").name
            if name:
                subprocess.run([sys_tool("taskkill"), "/IM", name, "/T"], capture_output=True, creationflags=CREATE_NO_WINDOW)
                log(f"Closed {name}")


BADGE_FILE = DATA_DIR / "badge.json"


def spawn_toast(title, body):
    spawn_self(TOAST_FLAG, title, body)


def close_badge():
    data = load_json(BADGE_FILE, {}) or {}
    pid = data.get("pid")
    if pid and IS_WINDOWS:
        kill_tree(pid)
    BADGE_FILE.unlink(missing_ok=True)


BADGE_HIDDEN = DATA_DIR / "badge_hidden.flag"


def show_badge(title, body, ip=None, joined=None):
    close_badge()
    extra = []
    if ip:
        extra += ["--ip", str(ip)]
    if joined:
        extra += ["--joined", str(int(joined))]
    proc = spawn_self(TOAST_FLAG, title, body, "--badge", *extra)
    if proc:
        save_json(BADGE_FILE, {"pid": proc.pid})


class SessionMonitor:

    def __init__(self, settings, launch_time):
        self.settings = settings
        self.session = settings["session"]
        self.discord = settings["discord"]
        self.launch_time = launch_time
        self.ipc = None
        if self.discord.get("enabled") and self.discord.get("client_id", "").strip():
            self.ipc = DiscordIPC(self.discord["client_id"].strip())
        self.icon = None
        if IS_WINDOWS and settings["appearance"].get("custom_window_icon") and ICON_FILE.exists():
            try:
                self.icon = WindowIcon(ICON_FILE)
            except Exception as e:
                log(f"Custom window icon disabled: {e}")
        self.lock = threading.Lock()
        self.game = None
        self.crashed = None
        self.boost = PerfBoost(settings.get("performance"))

    @staticmethod
    def wanted(settings):
        s, d, a = settings["session"], settings["discord"], settings["appearance"]
        perf = settings.get("performance") or {}
        return (any(s.values()) or (d.get("enabled") and d.get("client_id", "").strip())
                or (a.get("custom_window_icon") and ICON_FILE.exists())
                or perf.get("high_priority") or perf.get("power_plan") or bool(settings.get("launch_with")))

    def _discord(self, activity):
        if self.ipc:
            with self.lock:
                self.ipc.set_activity(activity)

    def on_join(self, place_id, job_id, ip, at=None, quiet=False):
        if self.game:
            self.on_leave(at)
        joined = at or time.time()
        game = {"place_id": place_id, "job_id": job_id, "ip": ip, "joined": joined,
                "name": None, "located": False, "quiet": False, "pings": []}
        if not quiet or time.time() - joined < 6 * 3600:
            threading.Thread(target=self._ping_loop, args=(game,), daemon=True).start()
        if not getattr(self, "play_start", None):
            self.play_start = joined
        game["udmux"] = threading.Event()
        self.last_code = None
        cached = game_info(place_id) if place_id in _GAME_CACHE or cached_game(place_id) else None
        if cached:
            game["name"], game["icon"] = cached["name"], cached.get("icon")
        self.game = game
        self._publish(game)
        log(f"Joined place {place_id}" + (" (already in progress)" if quiet else ""))
        save_json(LAST_SERVER_FILE, {"place_id": place_id, "job_id": job_id, "name": game["name"], "time": int(joined)})
        threading.Thread(target=self._join_details, args=(game,), daemon=True).start()
        threading.Thread(target=self._locate_soon, args=(game,), daemon=True).start()

    def _locate_soon(self, game):
        game["udmux"].wait(2.5)
        self._locate(game)

    def _publish(self, game):
        if game is not None and self.game is game:
            save_json(CURRENT_FILE, {"place_id": game["place_id"], "job_id": game["job_id"], "name": game.get("name"),
                                     "joined": int(game["joined"]), "location": game.get("location"),
                                     "icon": game.get("icon"), "ip": game.get("ip"), "ping": game.get("ping")})

    def _join_details(self, game):
        info = game_info(game["place_id"])
        game["name"] = info["name"]
        game["icon"] = info.get("icon")
        self._publish(game)
        last = load_json(LAST_SERVER_FILE, {})
        if last.get("job_id") == game["job_id"]:
            last["name"] = info["name"]
            save_json(LAST_SERVER_FILE, last)
        if self.game is game:
            self._discord(build_activity(self.discord, game["place_id"], game["job_id"], info, game["joined"]))

    def _ping_loop(self, game):
        time.sleep(4)
        while self.game is game:
            ms = ping_ms(game.get("ip"))
            if self.game is not game:
                break
            game["pings"].append([int(time.time()), ms])
            del game["pings"][:-720]
            if ms is not None:
                game["ping"] = ms
                self._publish(game)
            time.sleep(10)

    def note_problem(self, line):
        m = DISCONNECT_RE.search(line)
        if not m:
            return
        code = int(m.group(1))
        if code in IGNORED_CODES or getattr(self, "last_code", None) == code:
            return
        self.last_code = code
        game = self.game or {}
        record_problem(explain_code(code), game, line)
        if code in RECONNECT_CODES and self.session.get("auto_reconnect", True) and game.get("place_id"):
            threading.Thread(target=self._reconnect, args=(dict(game), code), daemon=True).start()

    def _reconnect(self, game, code):
        now = time.time()
        recent = [t for t in getattr(self, "reconnects", []) if now - t < 600]
        if len(recent) >= 3:
            log("Auto-reconnect skipped: 3 reconnects in the last 10 minutes")
            spawn_toast("Not reconnecting again", "You've been disconnected a lot. Check your connection, then rejoin from Orbit.")
            return
        self.reconnects = recent + [now]
        time.sleep(3)
        same = code in (277, 266) and len(recent) == 0
        job = game.get("job_id") if same else None
        if not same:
            try:
                sv, _ = pick_server(game["place_id"], {game.get("job_id")})
                job = sv["id"] if sv else None
            except Exception:
                job = None
        log(f"Auto-reconnecting after error {code} ({'same server' if same else 'new server' if job else 'any server'})")
        spawn_toast("Reconnecting...", f"Lost connection (error {code}). Putting you back in {'the same server' if same else 'a fresh server'}.")
        spawn_self(LAUNCH_FLAG, rejoin_uri(game["place_id"], job))

    def on_udmux(self, ip):
        game = self.game
        if game and not game["located"]:
            game["ip"] = ip
        if game and game.get("udmux"):
            game["udmux"].set()

    def _locate(self, game):
        with self.lock:
            if game["located"]:
                return
            game["located"] = True
        started = time.time()
        location = server_location(game["ip"])
        game["location"] = location
        self._publish(game)
        log(f"Server location: {location or 'unknown'} ({game['ip']}, {time.time() - game['joined']:.1f}s after join,"
            f" lookup {time.time() - started:.1f}s)")
        if not location or self.game is not game:
            return
        for _ in range(15):
            if game["name"]:
                break
            time.sleep(0.2)
        streamer = self.session.get("streamer_mode")
        if self.session.get("server_popup") and not game.get("quiet") and not streamer:
            spawn_toast(game["name"] or "Joined a game", location)
            time.sleep(6.8 if (self.session.get("badge_pos") or "Top right") == "Top center" else 0.4)
        if self.session.get("server_badge", True) and self.game is game:
            show_badge(game["name"] or "Roblox", "Streamer mode" if streamer else location, game.get("ip"), game.get("joined"))

    def on_leave(self, at=None, record=True):
        game, self.game = self.game, None
        if not game:
            return
        bed = getattr(self, "bed", None) or {}
        if bed.get("hit") and not bed.get("closed") and self.session.get("bedtime_action") == "close":
            bed["closed"] = True
            threading.Thread(target=lambda: (time.sleep(4), close_roblox("bedtime, match over")), daemon=True).start()
        if getattr(self, "fps", None):
            game["fps"] = self.fps.summary()
        seconds = max(0, (at or time.time()) - game["joined"])
        close_badge()
        CURRENT_FILE.unlink(missing_ok=True)
        if record and self.session.get("track_playtime"):
            record_playtime(game["place_id"], game["name"], seconds)
            record_session(game, seconds)
        if record and seconds >= 120:
            try:
                _, line = write_session_report(game, seconds)
                if self.session.get("session_report", True):
                    spawn_toast(f"{game.get('name') or 'Session'} recap", line)
            except Exception as e:
                log(f"Session report failed: {e}")
        if record and self.session.get("sort_screenshots"):
            threading.Thread(target=sort_screenshots, daemon=True).start()
        self._discord(None)

    def check_bedtime(self, now=None):
        bt = (self.session.get("bedtime") or "").strip()
        m = re.fullmatch(r"(\d{1,2}):(\d{2})", bt)
        if not m:
            return
        now = now or time.time()
        lt = time.localtime(now)
        mins_now = lt.tm_hour * 60 + lt.tm_min
        target = int(m.group(1)) * 60 + int(m.group(2))
        diff = (mins_now - target) % 1440
        night = time.strftime("%Y-%m-%d", time.localtime(now - diff * 60)) if diff < 360 else \
            time.strftime("%Y-%m-%d", time.localtime(now + (1440 - diff) * 60))
        st = getattr(self, "bed", None) or {}
        if st.get("night") != night:
            st = {"night": night}
        close = self.session.get("bedtime_action") == "close"
        if 0 < 1440 - diff <= 10 and not st.get("warned"):
            st["warned"] = True
            spawn_toast("Bedtime in 10 minutes", "Finish up your match." if close else "Time to start wrapping up.")
        elif diff < 360:
            if not st.get("hit"):
                st["hit"], st["hit_at"] = True, now
                spawn_toast("It's bedtime", "Roblox closes when you leave this match, or in 15 minutes." if close else "Good night!")
                log(f"Bedtime reached ({bt})")
            elif close and now - st["hit_at"] >= 15 * 60 and not st.get("closed"):
                st["closed"] = True
                close_roblox("bedtime")
        self.bed = st

    def check_daily(self):
        limit = int(self.session.get("daily_minutes") or 0)
        if not limit:
            return
        today = time.strftime("%Y-%m-%d")
        state = load_json(DAILY_FILE, {}) or {}
        if state.get("date") == today and state.get("notified"):
            return
        played = today_seconds()
        if played >= limit * 60:
            save_json(DAILY_FILE, {"date": today, "notified": True})
            spawn_toast("You hit your daily goal", f"{fmt_duration(played)} played today. Nice session!")
            log(f"Daily goal reached ({fmt_duration(played)})")

    def check_break(self):
        minutes = int(self.session.get("break_minutes") or 0)
        if not minutes or not getattr(self, "play_start", None):
            return
        played = time.time() - self.play_start
        due = minutes * 60 * (getattr(self, "breaks", 0) + 1)
        if played >= due:
            self.breaks = getattr(self, "breaks", 0) + 1
            spawn_toast("Time for a quick break?", f"You've been playing for {fmt_duration(played)}.")
            log(f"Break reminder after {fmt_duration(played)}")

    def _candidate_logs(self):
        try:
            logs = [p for p in ROBLOX_LOGS.glob("*.log") if p.stat().st_mtime >= self.launch_time - 5]
        except OSError:
            return []
        logs = [p for p in logs if "crashhandler" not in p.name.lower() and "player" in p.name.lower()
                and not self._is_handoff(p)]
        return sorted(logs, key=lambda p: p.stat().st_mtime, reverse=True)

    def _is_handoff(self, path):
        cache = self.__dict__.setdefault("_handoff", {})
        if path in cache:
            return cache[path]
        try:
            size = path.stat().st_size
            if size > 8000:
                cache[path] = False
                return False
            text = path.read_text(encoding="utf-8", errors="ignore")
        except OSError:
            return False
        handoff = "Deeplinking NoReload!" in text
        if handoff or "SingleSurfaceApp" in text or "Joining game" in text:
            cache[path] = handoff
        return handoff

    def _newest_log(self):
        logs = self._candidate_logs()
        return logs[0] if logs else None

    @staticmethod
    def _line_time(line):
        m = LOG_TS_RE.match(line)
        if not m:
            return None
        try:
            return calendar.timegm(time.strptime(m.group(1), "%Y-%m-%dT%H:%M:%S")) + float("0." + (m.group(2) or "0"))
        except ValueError:
            return None

    def handle_line(self, line):
        m = JOIN_RE.search(line)
        if m:
            self.on_join(m.group(2), m.group(1), m.group(3), at=self._line_time(line))
            return
        m = UDMUX_RE.search(line)
        if m:
            self.on_udmux(m.group(1))
            return
        if "rror Code" in line or "isconnect" in line:
            self.note_problem(line)
        if any(marker in line for marker in LEAVE_MARKERS):
            self.on_leave(self._line_time(line))

    def _catch_up(self, fh):
        state = None
        for line in fh:
            m = JOIN_RE.search(line)
            if m:
                state = {"place": m.group(2), "job": m.group(1), "ip": m.group(3), "at": self._line_time(line)}
                continue
            m = UDMUX_RE.search(line)
            if m and state:
                state["ip"] = m.group(1)
                continue
            if state and any(marker in line for marker in LEAVE_MARKERS):
                state = None
        if state:
            at = state["at"] or time.time()
            self.on_join(state["place"], state["job"], state["ip"], at=at, quiet=time.time() - at > 45)

    def _open(self, path):
        fh = open(path, encoding="utf-8", errors="ignore")
        if path in self.positions:
            fh.seek(self.positions[path])
        else:
            try:
                created = path.stat().st_ctime
            except OSError:
                created = time.time()
            if created < self.launch_time - 5:
                self._catch_up(fh)
        return fh

    def run(self):
        self.positions = {}
        log_path = None
        deadline = time.time() + 90
        while not log_path and time.time() < deadline:
            log_path = self._newest_log()
            if not log_path:
                if self.icon:
                    self.icon.apply()
                self.boost.tick()
                time.sleep(1)
        if not log_path:
            log("No Roblox log appeared; session features disabled for this launch")
            return
        log(f"Watching {log_path.name}")
        if (self.settings.get("overlay") or {}).get("keystrokes"):
            start_keys()
        if (self.settings.get("overlay") or {}).get("crosshair"):
            start_crosshair_overlay()
        perf = self.settings.get("performance") or {}
        self.guard = BackgroundGuard(perf).start() if IS_WINDOWS and perf.get("bg_guard", True) else None
        if (self.settings.get("fps") or {}).get("enabled"):
            try:
                self.fps = FpsTracker()
                if not self.fps.start():
                    self.fps = None
            except Exception as e:
                log(f"FPS tracking failed to start: {e}")
                self.fps = None
        if (self.settings.get("replay") or {}).get("enabled"):
            threading.Thread(target=Replay.run_while_roblox, daemon=True).start()
        fh = self._open(log_path)
        last_check, not_running = 0, 0
        try:
            while True:
                line = fh.readline()
                if line:
                    self.handle_line(line)
                    continue
                time.sleep(0.5)
                if time.time() - last_check < 3:
                    continue
                last_check = time.time()
                if self.icon:
                    self.icon.apply()
                self.boost.tick()
                self.check_break()
                self.check_daily()
                self.check_bedtime()
                if getattr(self, "fps", None):
                    self.fps.poll(self.game)
                newer = self._newest_log()
                try:
                    current_mtime = log_path.stat().st_mtime
                except OSError:
                    current_mtime = 0
                if newer and newer != log_path and newer.stat().st_mtime > current_mtime + 4:
                    self.positions[log_path] = fh.tell()
                    fh.close()
                    log_path = newer
                    fh = self._open(log_path)
                    log(f"Following {log_path.name}")
                if getattr(self, "token", None) and monitor_claimed_by_other(self.token):
                    log("A newer Orbit launch took over session tracking")
                    self.handed_over = True
                    break
                not_running = 0 if roblox_running() else not_running + 1
                if not_running >= 3:
                    break
        finally:
            fh.close()
            handed = getattr(self, "handed_over", False)
            if self.game and self.session.get("crash_rejoin") and not handed:
                g = self.game
                self.crashed = {"place_id": g["place_id"], "job_id": g["job_id"],
                                "name": g["name"] or f"Place {g['place_id']}"}
            if self.game and not handed:
                try:
                    found = diagnose_exit(log_path, self.launch_time)
                    if found:
                        record_problem(found, self.game, None)
                        spawn_toast(found["title"], found["tip"])
                except Exception as e:
                    log(f"Crash check failed: {e}")
            self.on_leave(record=not handed)
            if not handed:
                close_keys()
                close_crosshair_overlay()
                Replay.stop()
            if getattr(self, "fps", None):
                self.fps.stop()
            if getattr(self, "guard", None):
                self.guard.stop()
            if self.ipc:
                self.ipc.close()


def bundled_extension_dir():
    base = Path(getattr(sys, "_MEIPASS", Path(__file__).resolve().parent))
    return base / EXTENSION_NAME


def install_extension():
    src = bundled_extension_dir()
    if not (src / "manifest.json").exists():
        raise FileNotFoundError(f"Extension files not found next to the launcher ({src})")
    dest = EXTENSIONS_DIR / EXTENSION_NAME
    if dest.exists():
        shutil.rmtree(dest)
    shutil.copytree(src, dest)
    log(f"Extension files copied to {dest}")
    return dest


def open_browser_extensions(browser):
    page = {"chrome": "chrome://extensions", "msedge": "edge://extensions"}[browser]
    if IS_WINDOWS:
        subprocess.Popen([sys_tool("cmd"), "/c", "start", "", browser, page], creationflags=CREATE_NO_WINDOW, env=child_env())


def watch_for_updates(settings, known, place_id):
    flags = build_flags(settings, place_id)
    new_dirs = set()
    end = time.time() + UPDATE_WATCH_SECONDS
    while time.time() < end:
        for d in all_version_dirs():
            if d in known:
                continue
            if d not in new_dirs:
                log(f"Roblox is updating into {d.name}")
                new_dirs.add(d)
            try:
                write_flags(d, flags)
            except OSError:
                pass
        time.sleep(0.3)
    for d in new_dirs:
        if (d / "RobloxPlayerBeta.exe").exists():
            apply_all(settings, d, place_id)


def start_roblox(settings, uri):
    players = player_dirs()
    if not players:
        message_box("Roblox isn't installed yet. Install it from roblox.com/download first, "
                    "then try again.", error=True)
        webbrowser.open("https://www.roblox.com/download")
        return None
    place_id = place_id_from_uri(uri)
    try:
        apply_all(settings, players[0], place_id)
    except Exception as e:
        log(f"Applying settings failed: {e}")
    exe = players[0] / "RobloxPlayerBeta.exe"
    args = [str(exe), uri] if uri else [str(exe), "--app"]
    known = set(all_version_dirs())
    launch_time = time.time()
    subprocess.Popen(args, cwd=str(exe.parent), env=child_env())
    log(f"Started {players[0].name}")
    updater = threading.Thread(target=watch_for_updates, args=(settings, known, place_id), daemon=True)
    updater.start()
    return launch_time, updater


_MONITOR_MUTEX = None


def acquire_monitor_lock(wait=0.0):
    global _MONITOR_MUTEX
    if not IS_WINDOWS:
        return True
    k32 = ctypes.WinDLL("kernel32", use_last_error=True)
    k32.CreateMutexW.restype = ctypes.c_void_p
    k32.CreateMutexW.argtypes = [ctypes.c_void_p, ctypes.c_bool, ctypes.c_wchar_p]
    k32.CloseHandle.argtypes = [ctypes.c_void_p]
    end = time.time() + wait
    while True:
        handle = k32.CreateMutexW(None, False, "Local\\OrbitLauncherSessionMonitor")
        if ctypes.get_last_error() != 183:
            _MONITOR_MUTEX = handle
            return True
        k32.CloseHandle(handle)
        if time.time() >= end:
            return False
        time.sleep(0.5)


def orbit_pids():
    table = process_table()
    if table is None:
        return set(pids_named("OrbitLauncher.exe")) | set(pids_named(HELPER_NAME))
    out = set()
    for pid, _, name in table:
        n = name.lower()
        if n.endswith(".exe") and n.startswith("orbit") and ("launcher" in n or "helper" in n):
            out.add(pid)
    return out


def window_pids():
    pids = set()
    for f in (GUI_FILE, BACKGROUND_FILE):
        data = load_json(f, {}) or {}
        pids |= {int(x) for x in data.get("pids", []) if str(x).isdigit()}
    return pids


def stop_stale_copies():
    if not IS_WINDOWS or not is_frozen():
        return
    keep = {os.getpid(), os.getppid()}
    gui = window_pids()
    if not gui:
        log("Orbit's window isn't registered yet; leaving other Orbit processes alone")
        return
    targets = orbit_pids() - keep - gui
    for pid in sorted(targets):
        kill_tree(pid)
    if targets:
        log("Stopped old Orbit trackers: " + ", ".join(str(p) for p in sorted(targets)))


def monitor_active():
    if not IS_WINDOWS:
        return False
    k32 = ctypes.WinDLL("kernel32", use_last_error=True)
    k32.OpenMutexW.restype = ctypes.c_void_p
    k32.OpenMutexW.argtypes = [ctypes.c_uint, ctypes.c_bool, ctypes.c_wchar_p]
    k32.CloseHandle.argtypes = [ctypes.c_void_p]
    handle = k32.OpenMutexW(0x00100000, False, "Local\\OrbitLauncherSessionMonitor")
    if handle:
        k32.CloseHandle(handle)
        return True
    return False


def pid_alive(pid):
    if not pid or not IS_WINDOWS:
        return False
    try:
        k32, h = _open_process(pid, 0x1000)
        if not h:
            return ctypes.get_last_error() == 5
        code = ctypes.c_ulong()
        k32.GetExitCodeProcess.argtypes = [ctypes.c_void_p, ctypes.POINTER(ctypes.c_ulong)]
        k32.GetExitCodeProcess(h, ctypes.byref(code))
        k32.CloseHandle.argtypes = [ctypes.c_void_p]
        k32.CloseHandle(h)
        return code.value == 259
    except Exception:
        return True


class AutoAttach:
    def __init__(self, owner):
        self.owner = owner
        self.replaced = False
        self.spawned_at = 0
        self.last_guard = 0

    def tick(self):
        if time.time() - getattr(self, "last_periodic", 0) > 20:
            self.last_periodic = time.time()
            threading.Thread(target=periodic_jobs, args=(self.owner,), daemon=True).start()
        if time.time() - self.last_guard > 30:
            self.last_guard = time.time()
            self.guard_links()
            try:
                check_roblox_update(load_settings())
            except Exception as e:
                log(f"Roblox update check failed: {e}")
            try:
                if IS_WINDOWS and not roblox_running():
                    write_gbs(load_settings().get("performance") or {})
            except Exception as e:
                log(f"Frame rate cap check failed: {e}")
        if time.time() - getattr(self, "last_predownload", 0) > 20 * 60 and not roblox_running():
            self.last_predownload = time.time()
            threading.Thread(target=predownload_roblox, daemon=True).start()
        if not roblox_running():
            self.replaced = False
            self.seen = 0
            return
        self.seen = getattr(self, "seen", 0) + 1
        if self.seen < 2 or time.time() - self.spawned_at < 20:
            return
        if monitor_active():
            info = load_json(MONITOR_FILE, {}) or {}
            if parse_version(info.get("version", "0")) >= parse_version(APP_VERSION) and pid_alive(info.get("pid")):
                return
            if self.replaced:
                return
            self.replaced = True
            log(f"Replacing an outdated session tracker (v{info.get('version', '?')}, pid {info.get('pid')})")
            stop_stale_copies()
            time.sleep(2)
        log(f"Roblox is running; attaching session tracking ({self.owner})")
        spawn_self(ATTACH_FLAG)
        self.spawned_at = time.time()

    def guard_links(self):
        try:
            settings = load_settings()
            current = read_protocol_command(PROTOCOLS[0])
            if is_frozen() and settings["registration"].get("registered") and should_claim_links(current):
                register_protocols(settings)
                low = (current or "").lower()
                log("Pointed Roblox links at this Orbit version" if "orbit" in low
                    else "Another app had taken over Roblox links; switched them back to Orbit")
        except Exception as e:
            log(f"Link check failed: {e}")

    def loop(self, interval=5):
        while True:
            try:
                self.tick()
            except Exception as e:
                log(f"Auto-attach error: {e}")
            time.sleep(interval)


def attach_main():
    ensure_dirs()
    if not IS_WINDOWS or not acquire_monitor_lock(wait=3):
        return
    token = claim_monitor()
    settings = load_settings()
    if not SessionMonitor.wanted(settings):
        return
    log("Attached to running Roblox")
    monitor = SessionMonitor(settings, time.time() - 60)
    monitor.token = token
    monitor.boost.begin()
    try:
        monitor.run()
    except Exception:
        log("Session monitor crashed:\n" + traceback.format_exc())
    finally:
        monitor.boost.end()


_BG_MUTEX = None


def background_main():
    global _BG_MUTEX
    ensure_dirs()
    if not IS_WINDOWS:
        return
    k32 = ctypes.WinDLL("kernel32", use_last_error=True)
    k32.CreateMutexW.restype = ctypes.c_void_p
    k32.CreateMutexW.argtypes = [ctypes.c_void_p, ctypes.c_bool, ctypes.c_wchar_p]
    _BG_MUTEX = k32.CreateMutexW(None, False, "Local\\OrbitLauncherBackground")
    if ctypes.get_last_error() == 183:
        return
    save_json(BACKGROUND_FILE, {"pids": [os.getpid(), os.getppid()], "version": APP_VERSION})
    log(f"Background tracking started (v{APP_VERSION})")
    threading.Thread(target=hotkey_loop, args=("background",), daemon=True).start()
    threading.Thread(target=OverlayServer.start, daemon=True).start()
    AutoAttach("background").loop(interval=6)


def set_start_with_windows(on):
    if not IS_WINDOWS:
        return False
    if not is_frozen():
        raise OSError("Start with Windows only works in the installed app.")
    with winreg.CreateKey(winreg.HKEY_CURRENT_USER, RUN_KEY) as k:
        if on:
            cmd = fast_command(BACKGROUND_FLAG)
            winreg.SetValueEx(k, APP_NAME, 0, winreg.REG_SZ, " ".join(f'"{x}"' for x in cmd[:-1]) + f" {BACKGROUND_FLAG}")
        else:
            try:
                winreg.DeleteValue(k, APP_NAME)
            except OSError:
                pass
    if on and not pid_alive((load_json(BACKGROUND_FILE, {}) or {}).get("pids", [0])[0]):
        spawn_self(BACKGROUND_FLAG)
    elif not on:
        data = load_json(BACKGROUND_FILE, {}) or {}
        for pid in data.get("pids", []):
            kill_tree(pid)
        BACKGROUND_FILE.unlink(missing_ok=True)
    return on


HOTKEYS = {1: (0x52, "rejoin", "Ctrl+Alt+R", "Rejoin your current or last server"),
           2: (0x4E, "new", "Ctrl+Alt+N", "Hop to a new server in the same game"),
           3: (0x42, "badge", "Ctrl+Alt+B", "Show or hide the server badge"),
           4: (0x4F, "open", "Ctrl+Alt+O", "Open Orbit"),
           5: (0x53, "screenshot", "Ctrl+Alt+S", "Screenshot the Roblox window (saved and copied)"),
           6: (0x4A, "joinlink", "Ctrl+Alt+J", "Copy a link friends can use to join your server"),
           7: (0x43, "clip", "Ctrl+Alt+C", "Save an instant replay of the last 30 seconds"),
           8: (0x46, "joinfriend", "Ctrl+Alt+F", "Join the friend from your last friend alert")}


def current_game():
    cur = load_json(CURRENT_FILE, None) or {}
    if cur.get("place_id"):
        return cur
    return load_json(LAST_SERVER_FILE, None) or {}


def run_hotkey(action, force=False):
    if not force and not (load_settings().get("hotkeys") or {}).get("enabled", True):
        return
    log(f"Hotkey: {action}")
    game = current_game()
    if action == "rejoin" and game.get("place_id"):
        spawn_self(LAUNCH_FLAG, rejoin_uri(game["place_id"], game.get("job_id")))
    elif action == "new" and game.get("place_id"):
        pick, _ = pick_server(game["place_id"], {game.get("job_id")}, skip_full=False)
        if pick:
            spawn_self(LAUNCH_FLAG, rejoin_uri(game["place_id"], pick["id"]))
        else:
            spawn_toast("No other servers", "Couldn't find another open server right now.")
    elif action == "badge":
        if BADGE_HIDDEN.exists():
            BADGE_HIDDEN.unlink(missing_ok=True)
        else:
            BADGE_HIDDEN.write_text("1")
    elif action == "screenshot":
        r = take_roblox_screenshot()
        spawn_toast("Screenshot saved", "Copied to your clipboard too.") if r else spawn_toast("No Roblox window", "Open Roblox first.")
    elif action == "joinlink":
        link = join_link()
        if link:
            copy_to_clipboard(link)
            spawn_toast("Join link copied", "Paste it to a friend so they can join your server.")
        else:
            spawn_toast("Not in a game", "Join a server first, then copy the link.")
    elif action == "clip":
        r = Replay.save()
        spawn_toast("Replay saved" if r else "Replay isn't running", Path(r).name if r else "Turn on Instant replay in Boost first.")
    elif action == "launch":
        spawn_self(LAUNCH_FLAG, "")
    elif action == "joinfriend":
        fa = load_json(DATA_DIR / "friend_alert.json", None) or {}
        if fa.get("id") and time.time() - fa.get("at", 0) < 3600:
            spawn_self(LAUNCH_FLAG, follow_uri(fa["id"]))
        else:
            spawn_toast("No recent friend alert", "Turn on alerts for players in Library > Join a player.")
    elif action == "open":
        if pid_alive((load_json(GUI_FILE, {}) or {}).get("pids", [0])[0]):
            SHOW_FLAG.write_text(str(time.time()))
        else:
            spawn_self()


def hotkey_loop(owner):
    if not IS_WINDOWS or not (load_settings().get("hotkeys") or {}).get("enabled", True):
        return
    from ctypes import wintypes
    u = ctypes.windll.user32
    u.RegisterHotKey.argtypes = [ctypes.c_void_p, ctypes.c_int, ctypes.c_uint, ctypes.c_uint]
    mods = 0x0001 | 0x0002 | 0x4000
    ok = [i for i, (vk, *_rest) in HOTKEYS.items() if u.RegisterHotKey(None, i, mods, vk)]
    if not ok:
        return
    log(f"Hotkeys ready ({owner}): " + ", ".join(HOTKEYS[i][2] for i in ok))
    msg = wintypes.MSG()
    while u.GetMessageW(ctypes.byref(msg), None, 0, 0) > 0:
        if msg.message == 0x0312 and msg.wParam in HOTKEYS:
            threading.Thread(target=run_hotkey, args=(HOTKEYS[msg.wParam][1],), daemon=True).start()


def calendar_data():
    days = {}
    for x in _sessions():
        d = time.strftime("%Y-%m-%d", time.localtime(x.get("start", 0)))
        days[d] = days.get(d, 0) + int(x.get("seconds", 0))
    return days


def _ping_groups(sess):
    out = {}
    for x in sess:
        if x.get("ping") and x.get("location"):
            out.setdefault(x["location"], []).append(x["ping"]["avg"])
    return out


def game_stats(pid):
    pid = str(pid)
    sess = [x for x in _sessions() if str(x.get("place_id")) == pid]
    play = (load_json(PLAYTIME_FILE, {}) or {}).get(pid, {})
    info = game_info(pid)
    locs = {}
    for x in sess:
        if x.get("location"):
            locs[x["location"]] = locs.get(x["location"], 0) + 1
    total = max(play.get("seconds", 0), sum(x.get("seconds", 0) for x in sess))
    count = max(play.get("sessions", 0), len(sess))
    return {
        "pid": pid, "name": info["name"], "creator": info.get("creator"), "icon": info.get("icon"),
        "thumb": info.get("thumb"), "total": total, "sessions": count, "avg": int(total / count) if count else 0,
        "longest": max([x.get("seconds", 0) for x in sess] or [0]),
        "first": min([x["start"] for x in sess] or [0]), "last": max([x.get("end", 0) for x in sess] or [play.get("last_played", 0)]),
        "locations": sorted(locs.items(), key=lambda kv: -kv[1])[:8], "recent": list(reversed(sess))[:15],
        "ping_by_location": sorted(((loc, round(sum(v) / len(v)), len(v)) for loc, v in _ping_groups(sess).items()),
                                   key=lambda x: x[1])[:8],
        "last_ping": next((x["ping"] for x in reversed(sess) if x.get("ping")), None),
        "last_fps": next((x["fps"] for x in reversed(sess) if x.get("fps")), None),
    }


PACKS = {
    "crosshair_cyan_cross": ("Cyan Cross", "crosshair", "Bright cyan with a dark outline. Easy to see on any map. Great for BedWars."),
    "crosshair_green_plus": ("Green Plus", "crosshair", "A small, tight green plus for precise hits."),
    "crosshair_red_dot": ("Red Dot", "crosshair", "Just a dot. Keeps the middle of the screen clear."),
    "crosshair_white_circle": ("Circle Dot", "crosshair", "A ring with a center dot, good for bow and fireball aim."),
    "crosshair_yellow_t": ("Yellow T", "crosshair", "A T-shape with no top line, so you can see what's above you."),
    "crosshair_pink_chevron": ("Pink Chevron", "crosshair", "A small arrowhead that points at your target."),
    "cursor_void_ring": ("Void Ring", "cursor", "A glowing purple ring with a white center dot."),
    "cursor_dot": ("Dot", "cursor", "A tiny clean dot. Minimal and precise."),
    "cursor_crosshair": ("Crosshair", "cursor", "A thin crosshair for aiming games."),
    "cursor_neon_arrow": ("Neon Arrow", "cursor", "A purple arrow with a white edge. Easy to find on screen."),
    "cursor_big_cyan_dot": ("Big Cyan Dot", "cursor", "A larger dot that never gets lost in busy menus."),
    "cursor_green_ring": ("Green Ring", "cursor", "A green ring and dot, matching the Green Plus crosshair."),
    "death_soft_pop": ("Soft Pop", "sound", "A short, soft pop when you reset or die."),
    "death_warp": ("Warp Out", "sound", "A sci-fi warp swoosh."),
    "death_retro": ("Retro Blip", "sound", "A quick three-note retro blip."),
}
PACK_TARGETS = {
    "crosshair": ["content/textures/MouseLockedCursor.png"],
    "cursor": ["content/textures/Cursors/KeyboardMouse/ArrowFarCursor.png",
               "content/textures/Cursors/KeyboardMouse/ArrowCursor.png"],
    "sound": ["content/sounds/ouch.ogg"],
}


CROSSHAIR_DIR = DATA_DIR / "crosshairs"


def pack_file(pack_id):
    if pack_id in CHARSOUNDS:
        return resource_dir() / "ui" / "packs" / pack_id
    if str(pack_id).startswith("custom:"):
        return CROSSHAIR_DIR / (pack_id.split(":", 1)[1] + ".png")
    ext = ".ogg" if PACKS[pack_id][1] == "sound" else ".png"
    return resource_dir() / "ui" / "packs" / (pack_id + ext)


def crosshair_source(cid):
    if not cid:
        return None
    if str(cid).startswith("custom:") or (cid in PACKS and PACKS[cid][1] == "crosshair"):
        f = pack_file(cid)
        return f if f.exists() else None
    return None


def custom_crosshairs():
    CROSSHAIR_DIR.mkdir(parents=True, exist_ok=True)
    out = []
    for f in sorted(CROSSHAIR_DIR.glob("*.png"), key=lambda x: x.stat().st_mtime, reverse=True):
        meta = load_json(f.with_suffix(".json"), {}) or {}
        out.append({"id": "custom:" + f.stem, "name": meta.get("name") or f.stem, "kind": "crosshair", "custom": True,
                    "desc": "Made with the crosshair maker.", "design": meta.get("design"),
                    "data": "data:image/png;base64," + base64.b64encode(f.read_bytes()).decode()})
    return out


def save_custom_crosshair(name, data_url, design=None):
    m = re.match(r"data:image/png;base64,(.+)$", data_url or "", re.S)
    if not m:
        raise ValueError("That image didn't come through.")
    raw = base64.b64decode(m.group(1))
    if raw[:8] != b"\x89PNG\r\n\x1a\n" or len(raw) > 200_000:
        raise ValueError("That image isn't a valid crosshair.")
    w, h = struct.unpack(">II", raw[16:24])
    if not (16 <= w <= 256 and 16 <= h <= 256):
        raise ValueError("Crosshairs must be between 16 and 256 pixels.")
    clean = re.sub(r"[^A-Za-z0-9 _-]", "", name or "").strip()[:30] or "My crosshair"
    slug = re.sub(r"\s+", "-", clean.lower())
    CROSSHAIR_DIR.mkdir(parents=True, exist_ok=True)
    (CROSSHAIR_DIR / f"{slug}.png").write_bytes(raw)
    save_json(CROSSHAIR_DIR / f"{slug}.json", {"name": clean, "design": design, "at": int(time.time())})
    log(f"Saved custom crosshair '{clean}'")
    return "custom:" + slug


def delete_custom_crosshair(cid, settings):
    if not str(cid).startswith("custom:"):
        raise ValueError("Only your own crosshairs can be deleted.")
    slug = cid.split(":", 1)[1]
    (CROSSHAIR_DIR / f"{slug}.png").unlink(missing_ok=True)
    (CROSSHAIR_DIR / f"{slug}.json").unlink(missing_ok=True)
    settings["game_crosshairs"] = {k: v for k, v in (settings.get("game_crosshairs") or {}).items() if v != cid}
    save_settings(settings)


def pack_states(settings):
    folder = mods_dir(settings)
    out = []
    for c in custom_crosshairs():
        src = pack_file(c["id"])
        c["installed"] = all((folder / t).exists() and (folder / t).read_bytes() == src.read_bytes()
                             for t in PACK_TARGETS["crosshair"])
        out.append(c)
    for pid, (name, desc) in CHARSOUNDS.items():
        src = pack_file(pid)
        files = sorted(src.glob("*.mp3")) if src.is_dir() else []
        jump = src / "action_jump.mp3"
        out.append({"id": pid, "name": name, "kind": "charsound", "desc": desc,
                    "installed": bool(files) and all((folder / "content/sounds" / f.name).exists() and
                                                     (folder / "content/sounds" / f.name).stat().st_size == f.stat().st_size for f in files),
                    "data": "data:audio/mpeg;base64," + base64.b64encode(jump.read_bytes()).decode() if jump.exists() else ""})
    for pid, (name, kind, desc) in PACKS.items():
        src = pack_file(pid)
        installed = src.exists() and all((folder / t).exists() and (folder / t).stat().st_size == src.stat().st_size
                                          for t in PACK_TARGETS[kind])
        mime = "audio/ogg" if kind == "sound" else "image/png"
        data = f"data:{mime};base64," + base64.b64encode(src.read_bytes()).decode() if src.exists() else ""
        out.append({"id": pid, "name": name, "kind": kind, "desc": desc, "installed": installed, "data": data})
    return out


def install_pack(settings, pack_id, on=True):
    if pack_id in CHARSOUNDS:
        folder = mods_dir(settings)
        for f in pack_file(pack_id).glob("*.mp3"):
            dest = folder / "content" / "sounds" / f.name
            if on:
                dest.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(f, dest)
            else:
                dest.unlink(missing_ok=True)
        log(f"{'Installed' if on else 'Removed'} sound pack {pack_id}")
        return
    if str(pack_id).startswith("custom:"):
        if not pack_file(pack_id).exists():
            raise ValueError("That crosshair is gone.")
        kind = "crosshair"
    elif pack_id not in PACKS:
        raise ValueError("Unknown pack")
    else:
        kind = PACKS[pack_id][1]
    folder = mods_dir(settings)
    for target in PACK_TARGETS[kind]:
        dest = folder / target
        if on:
            dest.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(pack_file(pack_id), dest)
        else:
            dest.unlink(missing_ok=True)
    log(f"{'Installed' if on else 'Removed'} pack {pack_id} in mod profile {settings.get('mod_profile')}")


def health_checks(settings):
    checks = []

    def add(cid, title, ok, detail, fix=None, level="bad"):
        checks.append({"id": cid, "title": title, "ok": bool(ok), "detail": detail, "fix": fix,
                       "level": "ok" if ok else level})

    players = player_dirs()
    add("roblox", "Roblox is installed", bool(players),
        f"Found {players[0].name}" if players else "Roblox isn't installed.", "Download Roblox")
    frozen = is_frozen()
    add("installed", "Orbit is installed properly", running_installed_copy() or not frozen,
        "Running from the installed copy." if running_installed_copy() else
        ("Running from source (fine for testing)." if not frozen else f"Running from {Path(sys.executable).parent}. Install with OrbitSetup.exe so updates work."),
        None, "warn")
    if frozen and IS_WINDOWS:
        ours = read_protocol_command(PROTOCOLS[0]) == our_command()
        add("links", "Roblox Play links open through Orbit", ours,
            "Website Play buttons go through Orbit." if ours else "Play links currently open Roblox directly or another launcher.",
            "Use Orbit for links", "warn")
    excl = settings["presets"].get("exclusive_fullscreen")
    add("fullscreen", "Overlays can show over Roblox", not excl,
        "Exclusive fullscreen is off." if not excl else "Exclusive fullscreen (Alt+Enter) hides the server badge and banner.",
        "Turn off exclusive fullscreen", "warn")
    badge = settings["session"].get("server_badge", True)
    add("badge", "Server badge is on", badge, "Shows the server location while you play." if badge else "The badge is turned off.",
        "Turn on the badge", "warn")
    running = roblox_running()
    if running:
        info = load_json(MONITOR_FILE, {}) or {}
        tracking = monitor_active() and pid_alive(info.get("pid")) and \
            parse_version(info.get("version", "0")) >= parse_version(APP_VERSION)
        add("tracking", "Session tracking is running", tracking,
            "Orbit is watching your current session." if tracking else "Roblox is open but Orbit isn't tracking it.",
            "Start tracking")
    else:
        add("tracking", "Session tracking", True, "Starts automatically when you play.")
    if settings["session"].get("start_with_windows"):
        bg = (load_json(BACKGROUND_FILE, {}) or {}).get("pids", [0])[0]
        alive = pid_alive(bg)
        add("background", "Background helper is running", alive,
            "Tracks Roblox even when this window is closed." if alive else "Start with Windows is on but the helper isn't running.",
            "Start helper")
    if players:
        want = build_flags(settings)
        have = load_json(players[0] / "ClientSettings" / "ClientAppSettings.json", None)
        add("flags", "Your FastFlags are on the current Roblox", not want or have == want,
            "Roblox has your latest flags." if not want or have == want else "Roblox's flag file doesn't match your settings (Roblox may have updated).",
            "Re-apply now", "warn")
    recent = [x for x in (load_json(PROBLEMS_FILE, []) or []) if x.get("time", 0) > time.time() - 7 * 86400]
    add("problems", "No Roblox problems this week", not recent,
        "No crashes or disconnects recorded." if not recent else f"{len(recent)} problem(s) recorded. See Recent problems below.", None, "warn")
    if settings["discord"].get("enabled"):
        has_id = bool(settings["discord"].get("client_id", "").strip())
        add("discord", "Discord status is set up", has_id,
            "Ready." if has_id else "Discord status is on but there's no Application ID.", "Open Discord settings", "warn")
    if IS_WINDOWS:
        ps = Path(sys_tool("powershell"))
        add("tools", "Windows tools are reachable", ps.exists(), f"PowerShell: {ps}" if ps.exists() else
            "PowerShell wasn't found. Shortcuts and some fixes may not work.", None, "warn")
    return checks


def apply_health_fix(cid, settings):
    if cid == "roblox":
        webbrowser.open("https://www.roblox.com/download")
    elif cid == "links":
        register_protocols(settings)
    elif cid == "fullscreen":
        settings["presets"]["exclusive_fullscreen"] = False
        save_settings(settings)
    elif cid == "badge":
        settings["session"]["server_badge"] = True
        save_settings(settings)
    elif cid == "tracking":
        stop_stale_copies()
        spawn_self(ATTACH_FLAG)
    elif cid == "background":
        spawn_self(BACKGROUND_FLAG)
    elif cid == "flags":
        if roblox_running():
            write_flags(player_dirs()[0], build_flags(settings))
        else:
            apply_all(settings)
    return True


def roblox_cache_paths():
    temp = Path(os.environ.get("TEMP") or (LOCALAPPDATA / "Temp"))
    base = LOCALAPPDATA / "Roblox"
    paths = [temp / "Roblox", base / "Downloads", base / "rbx-storage", base / "http"]
    paths += list(base.glob("rbx-storage.db*"))
    cutoff = time.time() - 86400
    if ROBLOX_LOGS.is_dir():
        paths += [p for p in ROBLOX_LOGS.glob("*.log") if p.stat().st_mtime < cutoff]
    return [p for p in paths if p.exists()]


def path_size(p):
    try:
        if p.is_file():
            return p.stat().st_size
        return sum(f.stat().st_size for f in p.rglob("*") if f.is_file())
    except OSError:
        return 0


def repair(kind, settings):
    if kind in ("cache", "reinstall") and roblox_running():
        raise OSError("Close Roblox first, then try again.")
    if kind == "cache":
        freed = 0
        for p in roblox_cache_paths():
            freed += path_size(p)
            if p.is_dir():
                shutil.rmtree(p, ignore_errors=True)
            else:
                p.unlink(missing_ok=True)
        log(f"Cleared Roblox cache ({freed / 1048576:.1f} MB)")
        return f"Cleared {freed / 1048576:.1f} MB of Roblox cache."
    if kind == "reset_roblox":
        for d in player_dirs():
            (d / "ClientSettings" / "ClientAppSettings.json").unlink(missing_ok=True)
            sync_mods(d, None)
        log("Removed Orbit's flags and mods from Roblox")
        return "Roblox is back to stock. Orbit puts your flags and mods back next time you launch through it."
    if kind == "reset_flags":
        settings["presets"] = dict(DEFAULT_PRESETS)
        settings["custom_flags"] = {}
        save_settings(settings)
        return "Your default FastFlags are reset. Game profiles were kept."
    if kind == "reinstall":
        dest = Path(os.environ.get("TEMP") or LOCALAPPDATA) / "RobloxPlayerInstaller.exe"
        download_file("https://www.roblox.com/download/client?os=win", dest)
        subprocess.Popen([str(dest)], env=child_env())
        log("Started the official Roblox installer")
        return "The official Roblox installer is running."
    raise ValueError("Unknown repair")


DISCONNECT_RE = re.compile(r"(?:Error Code|[Dd]isconnect(?:ion)?(?: with)? reason(?: received)?)\s*[:=]?\s*(\d{3})")
IGNORED_CODES = {285, 286}
CODES = {
    260: ("Bad data from the server", "The game server sent something your Roblox couldn't read. Rejoining usually fixes it."),
    264: ("Signed in somewhere else", "The same account joined a game on another device or tab."),
    266: ("Connection timed out", "Your connection to the server stalled. Check your Wi-Fi or try a server with better ping."),
    267: ("Kicked by the game", "The game itself removed you. That's the game's rules, not Orbit or Roblox."),
    268: ("Kicked for unexpected behavior", "Roblox didn't like something on your client. Make sure no cheats or injectors are running."),
    271: ("Server closed", "The server shut down or the game kicked everyone."),
    272: ("Content failed to load", "Turn mods off in Orbit (Mods page) and try again; a broken mod file can cause this."),
    273: ("Account opened elsewhere", "Your account launched another Roblox session, which closed this one."),
    274: ("Server shutting down", "The game's developer shut the server down, often for an update."),
    275: ("Server closed for an update", "The game updated. Just join again."),
    277: ("Lost connection", "Your internet dropped or lagged too long. Try a closer server (Region hopper on the Servers page)."),
    278: ("Idle kick", "Roblox disconnects you after 20 minutes without moving."),
    279: ("Couldn't connect", "Your firewall, VPN or network blocked the connection. Try a different network or turn off your VPN."),
    280: ("Roblox is out of date", "Roblox needs an update. Launching through Orbit installs it."),
    282: ("Disconnected", "The server dropped you. Rejoin or try another server."),
    517: ("Server unavailable", "That server is gone or full. Try another one."),
    524: ("Not allowed to join", "That server is private, or you don't have access."),
    529: ("Roblox is having issues", "Roblox's own servers are struggling. Check status.roblox.com and try again soon."),
    610: ("Couldn't join that server", "The server ended or the link expired. Try joining the game normally."),
    772: ("Server full", "That server is full. Smart join or the Servers page can find one with room."),
    773: ("Teleport blocked", "The game tried to send you somewhere you can't go."),
}
CRASH_PATTERNS = [
    (re.compile(r"DXGI_ERROR_DEVICE_(?:REMOVED|HUNG|RESET)|[Dd]evice (?:removed|lost)|D3D11.*fail", re.I),
     "graphics", "Your graphics driver crashed", "Update your GPU driver, or set Graphics API to Direct3D 11 or Vulkan in FastFlags."),
    (re.compile(r"bad_alloc|out of memory|OutOfMemory|memory allocation failed", re.I),
     "memory", "Roblox ran out of memory", "Close other apps (browsers use a lot), or turn on FPS Boost to lower texture quality."),
    (re.compile(r"Vulkan.*(?:fail|error)|vkCreate\w+ failed", re.I),
     "vulkan", "Vulkan failed to start", "Set Graphics API back to Auto or Direct3D 11 in FastFlags."),
    (re.compile(r"Failed to load (?:texture|sound|font|mesh)|ContentProvider.*failed", re.I),
     "content", "Some game files failed to load", "If you use mods, turn them off on the Mods page and try again."),
]


def explain_code(code):
    title, tip = CODES.get(code, (f"Disconnected (error {code})", "Rejoin or try a different server."))
    return {"kind": "disconnect", "code": code, "title": title, "tip": tip}


def diagnose_exit(log_path, launch_time):
    text = ""
    if log_path and Path(log_path).exists():
        with open(log_path, "rb") as f:
            f.seek(max(0, Path(log_path).stat().st_size - 400_000))
            text = f.read().decode("utf-8", "ignore")
    for rx, kind, title, tip in CRASH_PATTERNS:
        if rx.search(text):
            return {"kind": kind, "title": title, "tip": tip}
    crash_logs = [p for p in ROBLOX_LOGS.glob("*CrashHandler*.log") if p.stat().st_mtime > launch_time] \
        if ROBLOX_LOGS.is_dir() else []
    codes = [int(c) for c in DISCONNECT_RE.findall(text[-60_000:]) if int(c) not in IGNORED_CODES]
    if codes and not crash_logs:
        return None
    if crash_logs:
        return {"kind": "crash", "title": "Roblox crashed",
                "tip": "No clear cause in the log. Try Clear cache on the Health page, update your GPU driver, or turn mods off."}
    return None


def record_problem(found, game, line):
    data = load_json(PROBLEMS_FILE, [])
    if not isinstance(data, list):
        data = []
    data.append({**found, "time": int(time.time()), "place_id": str(game.get("place_id") or ""),
                 "name": game.get("name"), "location": game.get("location"), "job_id": game.get("job_id"),
                 "line": (line or "").strip()[:240]})
    save_json(PROBLEMS_FILE, data[-50:])
    log(f"Problem: {found['title']}" + (f" (code {found.get('code')})" if found.get("code") else ""))


def ping_summary(pings):
    vals = [v for _, v in pings if v is not None]
    if not pings or not vals:
        return None
    step = max(1, len(pings) // 60)
    return {"avg": round(sum(vals) / len(vals)), "min": min(vals), "max": max(vals),
            "loss": round(100 * (len(pings) - len(vals)) / len(pings)),
            "samples": [v for _, v in pings[::step]][:60]}


def pick_server(place_id, exclude=(), skip_full=True):
    servers, note = list_servers(place_id, pages=1)
    ok = [x for x in servers if x["id"] not in exclude and (not skip_full or x["playing"] <= x["max"] - 2)]
    if not ok:
        return None, note
    return sorted(ok, key=lambda x: (x["ping"] if x["ping"] is not None else 999, -x["playing"]))[0], note


US_EAST = {"Virginia", "New York", "New Jersey", "Georgia", "Florida", "North Carolina", "South Carolina", "Pennsylvania",
           "Massachusetts", "Maryland", "Delaware", "Connecticut", "District of Columbia", "Washington, D.C.", "Maine",
           "New Hampshire", "Vermont", "Rhode Island", "West Virginia", "Ohio", "Michigan", "Tennessee", "Kentucky"}
US_WEST = {"California", "Washington", "Oregon", "Nevada", "Arizona", "Utah", "Idaho", "Montana", "Wyoming",
           "New Mexico", "Alaska", "Hawaii"}
REGIONS = {
    "US East": lambda region, cc: cc == "US" and region in US_EAST,
    "US Central": lambda region, cc: cc == "US" and region not in US_EAST and region not in US_WEST,
    "US West": lambda region, cc: cc == "US" and region in US_WEST,
    "Europe": lambda region, cc: cc in {"GB", "DE", "NL", "FR", "PL", "ES", "IT", "SE", "IE", "BE", "AT", "CH",
                                        "DK", "FI", "NO", "PT", "CZ", "RO"},
    "Asia": lambda region, cc: cc in {"JP", "SG", "HK", "IN", "KR", "TW", "MY", "TH", "ID", "PH", "VN", "AE"},
    "Oceania": lambda region, cc: cc in {"AU", "NZ"},
    "South America": lambda region, cc: cc in {"BR", "AR", "CL", "CO", "PE"},
}


def in_region(location, name):
    parts = [x.strip() for x in (location or "").split(",")]
    if len(parts) < 2 or name not in REGIONS:
        return False
    return REGIONS[name](parts[-2] if len(parts) >= 3 else "", parts[-1])


class RegionHop:
    current = None

    def __init__(self, place_id, region, tries=8):
        self.place_id, self.region, self.tries = str(place_id), region, tries
        self.tried, self.seen = set(), []
        self.status, self.done, self.ok, self.cancelled = "Starting...", False, False, False

    def state(self):
        return {"region": self.region, "status": self.status, "done": self.done, "ok": self.ok,
                "tried": len(self.tried), "tries": self.tries, "seen": self.seen[-8:]}

    def run(self):
        try:
            self._run()
        except Exception as e:
            self.status = f"Stopped: {e}"
            log("Region hop error:\n" + traceback.format_exc())
        self.done = True

    def _run(self):
        cur = load_json(CURRENT_FILE, None) or {}
        if cur.get("place_id") == self.place_id and in_region(cur.get("location"), self.region):
            self.ok, self.status = True, f"You're already in {self.region} ({cur['location']})."
            return
        for attempt in range(self.tries):
            if self.cancelled:
                self.status = "Cancelled."
                return
            self.status = f"Finding a server ({attempt + 1}/{self.tries})..."
            sv, note = pick_server(self.place_id, self.tried | {cur.get("job_id")})
            if not sv:
                self.status = note or "No more open servers to try."
                return
            self.tried.add(sv["id"])
            self.status = f"Joining server {attempt + 1} of {self.tries}..."
            spawn_self(LAUNCH_FLAG, rejoin_uri(self.place_id, sv["id"]))
            end, location = time.time() + 55, None
            while time.time() < end and not self.cancelled:
                cur = load_json(CURRENT_FILE, None) or {}
                if cur.get("job_id") == sv["id"] and cur.get("location"):
                    location = cur["location"]
                    break
                time.sleep(1)
            if not location:
                self.seen.append("No answer")
                continue
            self.seen.append(location)
            if in_region(location, self.region):
                self.ok, self.status = True, f"Found one: {location}"
                spawn_toast(f"You're in {self.region}", location)
                return
            self.status = f"{location} isn't in {self.region}, trying another..."
            time.sleep(2)
        self.status = f"Tried {len(self.tried)} servers without finding {self.region}. This game may not have servers there right now."


def screenshot_game(path, sessions):
    t = path.stat().st_mtime
    for x in sessions:
        if x.get("start", 0) - 30 <= t <= x.get("end", 0) + 60:
            return x.get("name")
    return None


def sort_screenshots():
    sessions = _sessions()
    moved = 0
    for folder in screenshot_dirs():
        for f in list(folder.iterdir()):
            if not f.is_file() or f.suffix.lower() not in (".png", ".jpg", ".jpeg"):
                continue
            name = screenshot_game(f, sessions)
            if not name:
                continue
            clean = re.sub(r'[<>:"/\\|?*]', "", name).strip().strip(".")[:60] or "Other"
            dest = folder / clean / f.name
            if dest.exists():
                continue
            dest.parent.mkdir(exist_ok=True)
            try:
                f.rename(dest)
                moved += 1
            except OSError:
                continue
    if moved:
        log(f"Sorted {moved} screenshot(s) into game folders")
    return moved


MOD_ROOTS = ("content/", "PlatformContent/", "ExtraContent/")


def export_mod_pack(name, dest):
    import zipfile
    folder = PROFILES_DIR / name
    files = [f for f in folder.rglob("*") if f.is_file()] if folder.is_dir() else []
    if not files:
        raise ValueError("That mod profile is empty.")
    with zipfile.ZipFile(dest, "w", zipfile.ZIP_DEFLATED) as z:
        z.writestr("orbit_pack.json", json.dumps({"name": name, "made": int(time.time()), "version": APP_VERSION}))
        for f in files:
            z.write(f, "files/" + f.relative_to(folder).as_posix())
    return len(files)


def import_mod_pack(src):
    import zipfile
    with zipfile.ZipFile(src) as z:
        names = z.namelist()
        if "orbit_pack.json" not in names:
            raise ValueError("That file isn't an Orbit mod pack.")
        meta = json.loads(z.read("orbit_pack.json") or b"{}")
        total = sum(i.file_size for i in z.infolist())
        if total > 300 * 1024 * 1024:
            raise ValueError("That pack is too big (over 300 MB).")
        base = re.sub(r'[<>:"/\\|?*]', "", str(meta.get("name") or Path(src).stem)).strip().strip(".") or "Imported"
        name, n = base, 2
        while (PROFILES_DIR / name).exists():
            name, n = f"{base} ({n})", n + 1
        dest = (PROFILES_DIR / name).resolve()
        count = 0
        for item in names:
            if not item.startswith("files/") or item.endswith("/"):
                continue
            rel = item[len("files/"):]
            if not rel.startswith(MOD_ROOTS):
                continue
            target = (dest / rel).resolve()
            if not str(target).startswith(str(dest)):
                continue
            target.parent.mkdir(parents=True, exist_ok=True)
            with z.open(item) as fsrc, open(target, "wb") as fdst:
                shutil.copyfileobj(fsrc, fdst)
            count += 1
        if not count:
            shutil.rmtree(dest, ignore_errors=True)
            raise ValueError("That pack has no usable files.")
    log(f"Imported mod pack '{name}' ({count} files)")
    return name, count


def check_roblox_update(settings):
    players = player_dirs()
    if not players:
        return None
    current = players[0].name
    info = load_json(ROBLOX_VERSION_FILE, {}) or {}
    if info.get("version") == current:
        if not (players[0] / "ClientSettings" / "ClientAppSettings.json").exists() and build_flags(settings):
            write_flags(players[0], build_flags(settings))
            log(f"Put FastFlags back into {current}")
        return None
    previous = info.get("version")
    save_json(ROBLOX_VERSION_FILE, {"version": current, "previous": previous, "at": int(time.time())})
    if not previous:
        return None
    log(f"Roblox updated from {previous} to {current}")
    if roblox_running():
        write_flags(players[0], build_flags(settings))
    else:
        apply_all(settings, players[0])
    spawn_toast("Roblox updated", "Orbit put your FastFlags and mods back on the new version.")
    return current


class MiniApi:
    def __init__(self):
        self._window = None
        self._ping = {"ip": None, "ms": None, "at": 0}

    def state(self):
        cur = load_json(CURRENT_FILE, None)
        settings = load_settings()
        c = theme_colors(settings["appearance"])
        out = {"current": cur, "last": load_json(LAST_SERVER_FILE, None), "accent": accent_pair(settings["appearance"]),
               "light": settings["appearance"].get("mode") == "Light", "bg": c["bg"],
               "streamer": bool(settings["session"].get("streamer_mode"))}
        if cur and roblox_running():
            out["ping"] = self._ping["ms"] if self._ping.get("ip") == cur.get("job_id") else None
            if time.time() - self._ping["at"] > 5:
                self._ping["at"] = time.time()
                threading.Thread(target=self._measure, args=(cur.get("job_id"), cur.get("ip")), daemon=True).start()
        return out

    def _measure(self, job, ip):
        ms = ping_ms(ip)
        self._ping.update({"ip": job, "ms": ms})

    def rejoin(self):
        run_hotkey("rejoin", True)
        return True

    def hop(self):
        run_hotkey("new", True)
        return True

    def open_main(self):
        SHOW_FLAG.write_text(str(time.time()))
        return True

    def join_link(self):
        link = join_link()
        if link:
            copy_to_clipboard(link)
        return bool(link)

    def close(self):
        if self._window:
            self._window.destroy()
        return True


AVATAR_DIR = DATA_DIR / "avatars"


def avatar_url(user_id, size="420x420"):
    data = fetch_json(f"https://thumbnails.roblox.com/v1/users/avatar-headshot?userIds={int(user_id)}"
                      f"&size={size}&format=Png&isCircular=false", timeout=8)
    item = (data.get("data") or [{}])[0]
    return item.get("imageUrl") if item.get("state") == "Completed" else None


def avatar_file(user_id, refresh=False):
    AVATAR_DIR.mkdir(parents=True, exist_ok=True)
    f, meta_f = AVATAR_DIR / f"{int(user_id)}.png", AVATAR_DIR / f"{int(user_id)}.json"
    meta = load_json(meta_f, {}) or {}
    stale = refresh or meta.get("version") != APP_VERSION or time.time() - meta.get("at", 0) > 6 * 3600
    if f.exists() and not stale:
        return f
    try:
        url = avatar_url(user_id)
        if url:
            req = urllib.request.Request(url, headers={"User-Agent": f"{APP_NAME}/{APP_VERSION}"})
            with urllib.request.urlopen(req, timeout=10) as r:
                data = r.read(4_000_000)
            if data[:8] == b"\x89PNG\r\n\x1a\n":
                f.write_bytes(data)
                save_json(meta_f, {"at": int(time.time()), "version": APP_VERSION, "url": url})
                return f
    except Exception as e:
        log(f"Avatar refresh failed for {user_id}: {e}")
    if f.exists():
        return f
    bundled = resource_dir() / "ui" / "avatars" / f"{int(user_id)}.png"
    return bundled if bundled.exists() else None


GAME_KITS = {
    "bedwars": {
        "name": "BedWars", "place_id": "6872265039",
        "preset": {"graphics_api": "Direct3D 11", "msaa": "1x", "texture_quality": "1", "lighting_quality": "1",
                   "remove_grass": True, "low_poly_meshes": True},
        "crosshair": "crosshair_cyan_cross",
    },
}


def apply_game_kit(settings, kit_id, crosshair=None):
    kit = GAME_KITS[kit_id]
    pid = kit["place_id"]
    prof = settings["game_profiles"].setdefault(pid, {"name": kit["name"], "presets": dict(settings["presets"]),
                                                       "custom_flags": dict(settings["custom_flags"])})
    prof["name"] = kit["name"]
    prof.setdefault("presets", {}).update(kit["preset"])
    if not any(str(g.get("pid")) == pid for g in settings["library"]):
        settings["library"].append({"pid": pid, "name": kit["name"], "mod_profile": None})
    if crosshair and crosshair_source(crosshair):
        settings.setdefault("game_crosshairs", {})[pid] = crosshair
        settings["apply_mods"] = True
    save_settings(settings)
    log(f"Applied the {kit['name']} kit")
    return pid


DAILY_FILE = DATA_DIR / "daily.json"
KEYS_FILE = DATA_DIR / "keys.json"
KEYS_FLAG = "--keys"


def today_seconds():
    today = time.strftime("%Y-%m-%d")
    total = calendar_data().get(today, 0)
    cur = load_json(CURRENT_FILE, None) or {}
    if cur.get("joined") and time.strftime("%Y-%m-%d", time.localtime(cur["joined"])) == today:
        total += max(0, time.time() - cur["joined"])
    return int(total)


def start_keys():
    close_keys()
    proc = spawn_self(TOAST_FLAG, "keys", "", KEYS_FLAG)
    if proc:
        save_json(KEYS_FILE, {"pid": proc.pid})


def close_keys():
    data = load_json(KEYS_FILE, {}) or {}
    if data.get("pid") and IS_WINDOWS:
        kill_tree(data["pid"])
    KEYS_FILE.unlink(missing_ok=True)


def show_keys_window():
    import tkinter as tk
    import tkinter.font as tkfont
    settings = load_settings()
    ov = settings.get("overlay") or {}
    pos = ov.get("keys_pos") or "Bottom right"
    show_cps = ov.get("keys_cps", True)
    c = theme_colors(settings["appearance"])
    accent, accent2 = accent_pair(settings["appearance"])
    key = "#010203"
    root = tk.Tk()
    root.withdraw()
    root.overrideredirect(True)
    root.configure(bg=key)
    try:
        root.attributes("-topmost", True)
        root.attributes("-transparentcolor", key)
        root.attributes("-alpha", 0.0)
    except tk.TclError:
        pass
    u, g = 30, 4
    rows = [[None, ("W", 0x57), None], [("A", 0x41), ("S", 0x53), ("D", 0x44)]]
    W = 3 * u + 2 * g
    H = 2 * u + g + g + 20 + g + 24 + (g + 18 if show_cps else 0)
    cv = tk.Canvas(root, width=W, height=H, bg=key, highlightthickness=0, bd=0)
    cv.pack()
    f_key = tkfont.Font(family="Segoe UI Semibold", size=10)
    f_small = tkfont.Font(family="Segoe UI Semibold", size=8)
    boxes = []

    def box(x1, y1, x2, y2, label, vk, font=f_key):
        r = cv.create_rectangle(x1, y1, x2, y2, fill=c["panel"], outline=c["muted"], width=1)
        t = cv.create_text((x1 + x2) / 2, (y1 + y2) / 2, text=label, fill=c["fg"], font=font)
        boxes.append((r, t, vk))

    y = 0
    for row in rows:
        for i, k in enumerate(row):
            if k:
                x = i * (u + g)
                box(x, y, x + u, y + u, k[0], k[1])
        y += u + g
    box(0, y, W, y + 20, "SPACE", 0x20, f_small)
    y += 20 + g
    half = (W - g) // 2
    box(0, y, half, y + 24, "LMB", 0x01, f_small)
    box(half + g, y, W, y + 24, "RMB", 0x02, f_small)
    y += 24 + g
    cps_text = cv.create_text(W / 2, y + 8, text="0 | 0 CPS", fill=c["fg"], font=f_small) if show_cps else None
    state = {"alpha": 0.0, "hwnd": None, "xy": None, "down": {}, "clicks": {0x01: [], 0x02: []}}
    peak = 0.88
    u32 = ctypes.windll.user32 if IS_WINDOWS else None

    def target_xy():
        rect = roblox_rect() or (0, 0, root.winfo_screenwidth(), root.winfo_screenheight())
        L, T, R, B = rect
        m = 16
        if pos == "Bottom left":
            return (L + m, B - H - m - 60)
        if pos == "Top left":
            return (L + m, T + 110)
        if pos == "Top right":
            return (R - W - m, T + 110)
        return (R - W - m, B - H - m - 60)

    xy = target_xy()
    root.geometry(f"{W}x{H}+{xy[0]}+{xy[1]}")
    root.deiconify()
    root.update_idletasks()
    hwnd = _no_activate(root)
    state["hwnd"] = hwnd
    if hwnd and IS_WINDOWS:
        try:
            style = u32.GetWindowLongW(hwnd, -20)
            u32.SetWindowLongW(hwnd, -20, style | 0x00000020 | 0x00080000)
        except Exception:
            pass
    log(f"Keystrokes overlay at {xy} ({pos})")

    state["shown"] = True

    def poll():
        try:
            now = time.time()
            visible = roblox_in_front()
            if visible and not state["shown"]:
                overlay_show(hwnd, True)
                state["shown"] = True
                state["xy"] = None
            if not visible and state["alpha"] == 0.0 and state["shown"]:
                overlay_show(hwnd, False)
                state["shown"] = False
            target = peak if visible else 0.0
            state["alpha"] += (target - state["alpha"]) * 0.35
            if abs(state["alpha"] - target) < 0.02:
                state["alpha"] = target
            root.attributes("-alpha", state["alpha"])
            if state["alpha"] > 0:
                for r, t, vk in boxes:
                    down = bool(u32.GetAsyncKeyState(vk) & 0x8000) if u32 else False
                    if down != state["down"].get(vk):
                        state["down"][vk] = down
                        cv.itemconfigure(r, fill=accent if down else c["panel"], outline=accent2 if down else c["muted"])
                        cv.itemconfigure(t, fill="#ffffff" if down else c["fg"])
                        if down and vk in state["clicks"]:
                            state["clicks"][vk].append(now)
                if cps_text:
                    for vk in state["clicks"]:
                        state["clicks"][vk] = [x for x in state["clicks"][vk] if now - x <= 1.0]
                    cv.itemconfigure(cps_text, text=f"{len(state['clicks'][0x01])} | {len(state['clicks'][0x02])} CPS")
                nxy = target_xy()
                if nxy != state["xy"]:
                    state["xy"] = nxy
                    u32.SetWindowPos(ctypes.c_void_p(hwnd), ctypes.c_void_p(-1), nxy[0], nxy[1], 0, 0, 0x0001 | 0x0010) \
                        if u32 and hwnd else root.geometry(f"+{nxy[0]}+{nxy[1]}")
        except tk.TclError:
            return
        except Exception:
            if not state.get("logged"):
                state["logged"] = True
                log("Keystrokes error:\n" + traceback.format_exc())
        root.after(16 if state["alpha"] > 0 else 250, poll)

    poll()
    root.mainloop()


ROBLOX_DEPLOY_FILE = DATA_DIR / "roblox_deploy.json"
ROBLOX_CDN = "https://setup.rbxcdn.com/channel/common"
ROBLOX_PACKAGE_MAP = {
    "RobloxApp.zip": "", "Libraries.zip": "", "redist.zip": "", "shaders.zip": "shaders/", "ssl.zip": "ssl/",
    "WebView2.zip": "", "WebView2RuntimeInstaller.zip": None,
    "content-avatar.zip": "content/avatar/", "content-configs.zip": "content/configs/",
    "content-fonts.zip": "content/fonts/", "content-sky.zip": "content/sky/", "content-sounds.zip": "content/sounds/",
    "content-textures2.zip": "content/textures/", "content-models.zip": "content/models/",
    "content-textures3.zip": "PlatformContent/pc/textures/", "content-terrain.zip": "PlatformContent/pc/terrain/",
    "content-platform-fonts.zip": "PlatformContent/pc/fonts/",
    "content-platform-dictionaries.zip": "PlatformContent/pc/shared_compression_dictionaries/",
    "extracontent-luapackages.zip": "ExtraContent/LuaPackages/", "extracontent-translations.zip": "ExtraContent/translations/",
    "extracontent-models.zip": "ExtraContent/models/", "extracontent-textures.zip": "ExtraContent/textures/",
    "extracontent-places.zip": "ExtraContent/places/",
}
ROBLOX_APPSETTINGS = ('<?xml version="1.0" encoding="UTF-8"?>\r\n<Settings>\r\n\t<ContentFolder>content</ContentFolder>\r\n'
                      '\t<BaseUrl>http://www.roblox.com</BaseUrl>\r\n</Settings>\r\n')


def parse_pkg_manifest(text):
    lines = [x.strip() for x in text.splitlines()]
    if not lines or lines[0] != "v0":
        raise ValueError(f"Unexpected Roblox package manifest ({lines[:1]})")
    out, i = [], 1
    while i + 3 < len(lines):
        name, sig, packed, size = lines[i:i + 4]
        if not name or not sig:
            break
        if name == "RobloxPlayerLauncher.exe":
            break
        out.append({"name": name, "sig": sig.lower(), "packed": int(packed), "size": int(size)})
        i += 4
    return out


def _deploy_state(**kw):
    state = load_json(ROBLOX_DEPLOY_FILE, {}) or {}
    state.update(kw, at=int(time.time()))
    save_json(ROBLOX_DEPLOY_FILE, state)
    return state


def predownload_roblox(force=False):
    if not IS_WINDOWS and not force:
        return None
    settings = load_settings()
    if not settings["updates"].get("roblox_predownload", True) and not force:
        return None
    if not player_dirs():
        return None
    state = load_json(ROBLOX_DEPLOY_FILE, {}) or {}
    if state.get("state") == "downloading" and pid_alive(state.get("pid")) and time.time() - state.get("at", 0) < 900:
        return None
    latest = latest_roblox_version()
    if not latest:
        return None
    root = LOCALAPPDATA / "Roblox" / "Versions"
    final = root / latest
    if (final / "RobloxPlayerBeta.exe").exists():
        if state.get("version") != latest or state.get("state") not in ("ready", "current"):
            _deploy_state(state="current", version=latest, progress=1.0, error=None, pid=None)
        return None
    if roblox_running() and not force:
        return None
    if state.get("state") == "failed" and state.get("version") == latest and time.time() - state.get("at", 0) < 6 * 3600 and not force:
        return None
    import hashlib
    import zipfile
    _deploy_state(state="downloading", version=latest, progress=0.0, error=None, pid=os.getpid())
    log(f"Pre-downloading Roblox {latest}")
    dl = DATA_DIR / "rbx-download"
    stage = root / (latest + ".orbit-staging")
    try:
        with urllib.request.urlopen(urllib.request.Request(f"{ROBLOX_CDN}/{latest}-rbxPkgManifest.txt",
                                                           headers={"User-Agent": f"{APP_NAME}/{APP_VERSION}"}), timeout=20) as r:
            packages = parse_pkg_manifest(r.read().decode("utf-8", "ignore"))
        unknown = [p["name"] for p in packages if p["name"] not in ROBLOX_PACKAGE_MAP]
        if unknown or not any(p["name"] == "RobloxApp.zip" for p in packages):
            raise ValueError("Roblox changed its package layout (" + ", ".join(unknown or ["no RobloxApp.zip"]) + "). "
                             "Leaving this update to Roblox's own updater.")
        wanted = [p for p in packages if ROBLOX_PACKAGE_MAP[p["name"]] is not None]
        total = sum(p["packed"] for p in wanted) or 1
        done = 0
        dl.mkdir(parents=True, exist_ok=True)
        for p in wanted:
            f = dl / p["sig"]
            if not (f.exists() and f.stat().st_size == p["packed"]):
                h = hashlib.md5()
                req = urllib.request.Request(f"{ROBLOX_CDN}/{latest}-{p['name']}", headers={"User-Agent": f"{APP_NAME}/{APP_VERSION}"})
                with urllib.request.urlopen(req, timeout=30) as r, open(f.with_suffix(".part"), "wb") as out:
                    last = 0
                    while True:
                        chunk = r.read(1 << 16)
                        if not chunk:
                            break
                        out.write(chunk)
                        h.update(chunk)
                        done += len(chunk)
                        if time.time() - last > 1.5:
                            last = time.time()
                            _deploy_state(progress=round(min(done / total, 0.99) * 0.85, 3))
                        if roblox_running() and not force:
                            raise InterruptedError("Roblox started; pausing the pre-download until it closes.")
                if h.hexdigest() != p["sig"]:
                    f.with_suffix(".part").unlink(missing_ok=True)
                    raise ValueError(f"{p['name']} didn't download correctly (checksum mismatch).")
                os.replace(f.with_suffix(".part"), f)
            else:
                done += p["packed"]
        _deploy_state(progress=0.88)
        shutil.rmtree(stage, ignore_errors=True)
        stage.mkdir(parents=True)
        for p in wanted:
            dest = stage / ROBLOX_PACKAGE_MAP[p["name"]]
            dest.mkdir(parents=True, exist_ok=True)
            with zipfile.ZipFile(dl / p["sig"]) as z:
                for info in z.infolist():
                    name = info.filename.replace("\\", "/").lstrip("/")
                    if not name or name.endswith("/") or ".." in name.split("/"):
                        continue
                    target = dest / name
                    target.parent.mkdir(parents=True, exist_ok=True)
                    with z.open(info) as src, open(target, "wb") as out:
                        shutil.copyfileobj(src, out)
        (stage / "AppSettings.xml").write_text(ROBLOX_APPSETTINGS, encoding="utf-8")
        if not (stage / "RobloxPlayerBeta.exe").exists():
            raise ValueError("The download didn't include RobloxPlayerBeta.exe.")
        if (final / "RobloxPlayerBeta.exe").exists():
            shutil.rmtree(stage, ignore_errors=True)
        else:
            shutil.rmtree(final, ignore_errors=True)
            stage.rename(final)
            os.utime(final / "RobloxPlayerBeta.exe", None)
        try:
            apply_all(settings, final)
        except Exception as e:
            log(f"Applying settings to the new Roblox failed: {e}")
        shutil.rmtree(dl, ignore_errors=True)
        save_json(ROBLOX_VERSION_FILE, {"version": latest, "previous": (load_json(ROBLOX_VERSION_FILE, {}) or {}).get("version"),
                                        "at": int(time.time())})
        cleanup_old_roblox(root, keep={latest})
        _deploy_state(state="ready", progress=1.0, pid=None)
        log(f"Roblox {latest} is ready; next launch skips Roblox's updater")
        spawn_toast("Roblox update ready", "Orbit downloaded the new Roblox in the background. Your next launch is instant.")
        return latest
    except InterruptedError as e:
        _deploy_state(state="paused", error=str(e), pid=None)
        log(str(e))
    except Exception as e:
        shutil.rmtree(stage, ignore_errors=True)
        _deploy_state(state="failed", error=str(e)[:300], pid=None)
        log(f"Roblox pre-download failed: {e}")
    return None


def cleanup_old_roblox(root, keep):
    dirs = [d for d in root.iterdir() if d.is_dir() and d.name.startswith("version-") and (d / "RobloxPlayerBeta.exe").exists()]
    dirs.sort(key=lambda d: (d / "RobloxPlayerBeta.exe").stat().st_mtime, reverse=True)
    keepers = set(keep) | {d.name for d in dirs[:2]}
    for d in dirs:
        if d.name not in keepers:
            shutil.rmtree(d, ignore_errors=True)
            log(f"Removed old Roblox {d.name}")
    for d in root.glob("*.orbit-staging"):
        shutil.rmtree(d, ignore_errors=True)


RECONNECT_CODES = {266, 277, 279, 282}
FPS_LIVE_FILE = DATA_DIR / "fps_live.json"
TOOLS_DIR = DATA_DIR / "tools"
PRESENTMON = TOOLS_DIR / "PresentMon.exe"
FFMPEG = TOOLS_DIR / "ffmpeg.exe"
REPLAY_DIR = DATA_DIR / "replay"


def close_roblox(reason):
    pids = pids_named("RobloxPlayerBeta.exe")
    if not pids:
        return
    if IS_WINDOWS:
        u = ctypes.windll.user32
        WNDENUM = ctypes.WINFUNCTYPE(ctypes.c_bool, ctypes.c_void_p, ctypes.c_void_p)
        targets = set(pids)

        def cb(hwnd, _):
            pid = ctypes.c_ulong()
            u.GetWindowThreadProcessId(ctypes.c_void_p(hwnd), ctypes.byref(pid))
            if pid.value in targets and u.IsWindowVisible(ctypes.c_void_p(hwnd)):
                u.PostMessageW(ctypes.c_void_p(hwnd), 0x0010, 0, 0)
            return True
        u.EnumWindows(WNDENUM(cb), 0)
        for _ in range(16):
            time.sleep(0.5)
            if not pids_named("RobloxPlayerBeta.exe"):
                break
    for pid in pids_named("RobloxPlayerBeta.exe"):
        kill_tree(pid)
    log(f"Closed Roblox ({reason})")


def join_link(cur=None):
    cur = cur or load_json(CURRENT_FILE, None) or {}
    if not cur.get("place_id") or not cur.get("job_id"):
        return None
    return f"https://www.roblox.com/games/start?placeId={cur['place_id']}&gameInstanceId={cur['job_id']}"


def _png_bytes(width, height, bgra_rows):
    import zlib
    raw = bytearray()
    for row in bgra_rows:
        raw.append(0)
        rgb = bytearray(len(row) // 4 * 3)
        rgb[0::3], rgb[1::3], rgb[2::3] = row[2::4], row[1::4], row[0::4]
        raw += rgb

    def chunk(tag, data):
        return struct.pack(">I", len(data)) + tag + data + struct.pack(">I", zlib.crc32(tag + data) & 0xFFFFFFFF)
    return (b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", struct.pack(">IIBBBBB", width, height, 8, 2, 0, 0, 0))
            + chunk(b"IDAT", zlib.compress(bytes(raw), 6)) + chunk(b"IEND", b""))


def capture_rect(rect):
    L, T, R, B = rect
    w, h = max(1, R - L), max(1, B - T)
    u, g = ctypes.windll.user32, ctypes.windll.gdi32
    u.GetDC.restype = ctypes.c_void_p
    u.GetDC.argtypes = [ctypes.c_void_p]
    u.ReleaseDC.argtypes = [ctypes.c_void_p, ctypes.c_void_p]
    g.CreateCompatibleDC.restype = ctypes.c_void_p
    g.CreateCompatibleDC.argtypes = [ctypes.c_void_p]
    g.DeleteDC.argtypes = [ctypes.c_void_p]
    g.CreateCompatibleBitmap.restype = ctypes.c_void_p
    g.CreateCompatibleBitmap.argtypes = [ctypes.c_void_p, ctypes.c_int, ctypes.c_int]
    g.SelectObject.restype = ctypes.c_void_p
    g.SelectObject.argtypes = [ctypes.c_void_p, ctypes.c_void_p]
    g.BitBlt.argtypes = [ctypes.c_void_p, ctypes.c_int, ctypes.c_int, ctypes.c_int, ctypes.c_int, ctypes.c_void_p,
                         ctypes.c_int, ctypes.c_int, ctypes.c_uint]
    g.GetDIBits.argtypes = [ctypes.c_void_p, ctypes.c_void_p, ctypes.c_uint, ctypes.c_uint, ctypes.c_void_p,
                            ctypes.c_void_p, ctypes.c_uint]
    g.DeleteObject.argtypes = [ctypes.c_void_p]
    screen = u.GetDC(None)
    mem = g.CreateCompatibleDC(screen)
    bmp = g.CreateCompatibleBitmap(screen, w, h)
    old = g.SelectObject(mem, bmp)
    g.BitBlt(mem, 0, 0, w, h, screen, L, T, 0x00CC0020 | 0x40000000)
    bmi = ctypes.create_string_buffer(struct.pack("<IiiHHIIiiII", 40, w, -h, 1, 32, 0, 0, 0, 0, 0, 0) + b"\0" * 16)
    buf = ctypes.create_string_buffer(w * h * 4)
    g.GetDIBits(mem, bmp, 0, h, buf, bmi, 0)
    g.SelectObject(mem, old)
    g.DeleteObject(bmp)
    g.DeleteDC(mem)
    u.ReleaseDC(None, screen)
    return w, h, buf.raw


def take_roblox_screenshot(rect=None):
    if not IS_WINDOWS:
        return None
    rect = rect or roblox_rect()
    if not rect:
        return None
    L, T, R, B = rect
    if L < 0 and T < 0:
        L, T, R, B = L + 8, T + 8, R - 8, B - 8
    w, h, data = capture_rect((L, T, R, B))
    stride = w * 4
    png = _png_bytes(w, h, (data[i * stride:(i + 1) * stride] for i in range(h)))
    cur = load_json(CURRENT_FILE, None) or {}
    name = re.sub(r'[<>:"/\\|?*]', "", cur.get("name") or "Roblox").strip()[:60] or "Roblox"
    base = (screenshot_dirs() or [Path.home() / "Pictures" / "Roblox"])[0]
    dest = base / name / f"Orbit_{time.strftime('%Y%m%d_%H%M%S')}.png"
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_bytes(png)
    try:
        bottom_up = b"".join(data[i * stride:(i + 1) * stride] for i in range(h - 1, -1, -1))
        dib = struct.pack("<IiiHHIIiiII", 40, w, h, 1, 32, 0, len(bottom_up), 0, 0, 0, 0) + bottom_up
        _clipboard_put(8, dib)
    except Exception as e:
        log(f"Couldn't copy screenshot: {e}")
    log(f"Screenshot saved: {dest}")
    return str(dest)


def region_test():
    cache = load_json(LOCATION_CACHE_FILE, {}) or {}
    by_loc = {}
    for ip, val in cache.items():
        loc = val[0] if isinstance(val, list) and val else None
        if not loc:
            continue
        by_loc.setdefault(loc, [])
        if len(by_loc[loc]) < 2:
            by_loc[loc].append(ip)
    if not by_loc:
        return {"locations": [], "regions": [], "note": "Play a few games through Orbit first. The test pings Roblox servers you've been in before."}
    from concurrent.futures import ThreadPoolExecutor

    def test(item):
        loc, ips = item
        vals = []
        for ip in ips:
            for _ in range(2):
                v = ping_ms(ip)
                if v is not None:
                    vals.append(v)
        return {"location": loc, "ping": round(sorted(vals)[len(vals) // 2]) if vals else None, "samples": len(vals)}
    with ThreadPoolExecutor(max_workers=12) as ex:
        locs = list(ex.map(test, list(by_loc.items())[:40]))
    regions = []
    for name in REGIONS:
        vals = [x["ping"] for x in locs if x["ping"] is not None and in_region(x["location"], name)]
        if vals:
            regions.append({"region": name, "ping": min(vals), "servers": len(vals)})
    regions.sort(key=lambda x: x["ping"])
    locs.sort(key=lambda x: (x["ping"] is None, x["ping"] or 0))
    note = None if any(x["ping"] is not None for x in locs) else \
        "Roblox servers didn't answer pings from your network, so Orbit can't measure them right now."
    result = {"at": int(time.time()), "regions": regions, "locations": locs, "note": note}
    save_json(DATA_DIR / "region_test.json", result)
    return result


ROBLOX_UA = {"User-Agent": f"{APP_NAME}/{APP_VERSION}", "Accept": "application/json", "Content-Type": "application/json"}


def post_json(url, body, timeout=10):
    req = urllib.request.Request(url, data=json.dumps(body).encode(), headers=ROBLOX_UA, method="POST")
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return json.loads(r.read().decode("utf-8"))


def find_player(text):
    text = (text or "").strip().lstrip("@")
    m = re.search(r"roblox\.com/users/(\d+)", text)
    if m or text.isdigit():
        uid = int(m.group(1) if m else text)
        info = fetch_json(f"https://users.roblox.com/v1/users/{uid}")
        user = {"id": uid, "name": info.get("name"), "display": info.get("displayName")}
    else:
        if not re.fullmatch(r"[A-Za-z0-9_]{3,20}", text):
            raise ValueError("That doesn't look like a Roblox username.")
        data = post_json("https://users.roblox.com/v1/usernames/users", {"usernames": [text], "excludeBannedUsers": True})
        if not data.get("data"):
            raise ValueError(f'No Roblox player named "{text}".')
        d = data["data"][0]
        user = {"id": d["id"], "name": d["name"], "display": d.get("displayName")}
    status, game = "Unknown", None
    try:
        pres = post_json("https://presence.roblox.com/v1/presence/users", {"userIds": [user["id"]]})["userPresences"][0]
        status = {0: "Offline", 1: "Online", 2: "In a game", 3: "In Studio", 4: "Offline"}.get(pres.get("userPresenceType"), "Unknown")
        if pres.get("placeId") or (status == "In a game" and pres.get("lastLocation")):
            game = {"place_id": str(pres["placeId"]) if pres.get("placeId") else None, "name": pres.get("lastLocation")}
    except Exception as e:
        log(f"Presence lookup failed: {e}")
    try:
        user["avatar"] = avatar_url(user["id"], "150x150")
    except Exception:
        user["avatar"] = None
    user.update(status=status, game=game)
    return user


def follow_uri(user_id):
    return f"roblox://experiences/start?userId={int(user_id)}"


def parse_frame_times(cols, lines):
    idx = next((cols.index(c) for c in ("MsBetweenPresents", "msBetweenPresents", "FrameTime") if c in cols), None)
    if idx is None:
        return []
    out = []
    for line in lines:
        parts = line.split(",")
        try:
            ms = float(parts[idx])
        except (ValueError, IndexError):
            continue
        if 0 < ms < 1000:
            out.append(ms)
    return out


def summarize_frames(frames):
    if len(frames) < 30:
        return None
    avg = 1000 * len(frames) / sum(frames)
    worst = sorted(frames, reverse=True)[:max(1, len(frames) // 100)]
    low1 = 1000 / (sum(worst) / len(worst))
    step = max(1, len(frames) // 60)
    samples = [round(1000 * step / sum(frames[i:i + step])) for i in range(0, len(frames) - step + 1, step)][:60]
    return {"avg": round(avg), "low1": round(low1), "samples": samples}


class FpsTracker:
    def __init__(self):
        self.proc = None
        self.csv = None
        self.pos = 0
        self.cols = None
        self.frames = []
        self.game_frames = []

    def start(self):
        if not IS_WINDOWS or not PRESENTMON.exists():
            log("FPS tracking is on but PresentMon isn't set up yet")
            return False
        folder = DATA_DIR / "fps"
        folder.mkdir(parents=True, exist_ok=True)
        for old in sorted(folder.glob("session_*.csv"))[:-2]:
            old.unlink(missing_ok=True)
        self.csv = folder / f"session_{int(time.time())}.csv"
        for args in (["--process_name", "RobloxPlayerBeta.exe", "--output_file", str(self.csv), "--terminate_on_proc_exit",
                      "--stop_existing_session", "--session_name", "OrbitFPS", "--no_console_stats"],
                     ["-process_name", "RobloxPlayerBeta.exe", "-output_file", str(self.csv), "-terminate_on_proc_exit",
                      "-stop_existing_session", "-session_name", "OrbitFPS", "-no_top"]):
            self.proc = subprocess.Popen([str(PRESENTMON), *args], stdout=subprocess.DEVNULL, stderr=subprocess.PIPE,
                                         stdin=subprocess.DEVNULL, creationflags=CREATE_NO_WINDOW | 0x00004000)
            time.sleep(2.5)
            if self.proc.poll() is None:
                log("FPS tracking started")
                save_json(DATA_DIR / "fps_status.json", {"ok": True, "at": int(time.time())})
                return True
            err = (self.proc.stderr.read() or b"").decode("utf-8", "ignore").strip()
            log(f"PresentMon exited: {err[:300]}")
            if "access" in err.lower() or "denied" in err.lower() or "performance log users" in err.lower():
                save_json(DATA_DIR / "fps_status.json", {"error": "access", "at": int(time.time())})
                return False
        save_json(DATA_DIR / "fps_status.json", {"error": "start", "at": int(time.time())})
        return False

    def poll(self, game):
        if not self.csv or not self.csv.exists():
            return
        with open(self.csv, "rb") as f:
            f.seek(self.pos)
            chunk = f.read()
        cut = chunk.rfind(b"\n")
        if cut < 0:
            return
        self.pos += cut + 1
        lines = chunk[:cut].decode("utf-8", "ignore").splitlines()
        if self.cols is None and lines:
            self.cols = [c.strip() for c in lines[0].split(",")]
            lines = lines[1:]
        if not self.cols:
            return
        new = parse_frame_times(self.cols, lines)
        self.frames = (self.frames + new)[-4000:]
        if game is not None:
            self.game_frames = (self.game_frames + new)[-200000:]
        recent, total = [], 0.0
        for ms in reversed(self.frames):
            recent.append(ms)
            total += ms
            if total >= 1000:
                break
        if recent and total > 0:
            save_json(FPS_LIVE_FILE, {"fps": round(1000 * len(recent) / total), "at": int(time.time())})

    def summary(self):
        frames, self.game_frames = self.game_frames, []
        return summarize_frames(frames)

    def stop(self):
        if self.proc and self.proc.poll() is None:
            kill_tree(self.proc.pid)
        FPS_LIVE_FILE.unlink(missing_ok=True)


def fps_ready():
    if not IS_WINDOWS:
        return {"tool": False, "group": False}
    group = False
    try:
        out = subprocess.run([sys_tool("whoami"), "/groups"], capture_output=True, text=True, timeout=10,
                             creationflags=CREATE_NO_WINDOW).stdout
        group = "S-1-5-32-559" in out or ("S-1-5-32-544" in out and "S-1-16-12288" in out)
    except Exception:
        pass
    return {"tool": PRESENTMON.exists(), "group": group}


def github_asset(repo, pattern):
    rels = fetch_json(f"https://api.github.com/repos/{repo}/releases?per_page=15", timeout=15)
    for rel in rels:
        if rel.get("prerelease") or rel.get("draft"):
            continue
        for a in rel.get("assets", []):
            if re.fullmatch(pattern, a.get("name", "")):
                return a["browser_download_url"], a["name"]
    raise ValueError(f"Couldn't find a download for {repo}.")


def setup_presentmon():
    TOOLS_DIR.mkdir(parents=True, exist_ok=True)
    if not PRESENTMON.exists():
        url, name = github_asset("GameTechDev/PresentMon", r"PresentMon-\d+\.\d+\.\d+-x64\.exe")
        download_file(url, PRESENTMON)
        log(f"Downloaded {name}")
    if fps_ready()["group"]:
        return {"ready": True}
    user = f'{os.environ.get("USERDOMAIN", "")}\\{os.environ.get("USERNAME", "")}'.strip("\\").replace("'", "''")
    cmd = f"Add-LocalGroupMember -SID 'S-1-5-32-559' -Member '{user}' -ErrorAction SilentlyContinue"
    r = ctypes.windll.shell32.ShellExecuteW(None, "runas", sys_tool("powershell"),
                                            f'-NoProfile -WindowStyle Hidden -Command "{cmd}"', None, 0)
    if r <= 32:
        raise PermissionError("Windows didn't give the one-time permission. FPS tracking needs it to read frame timings.")
    save_json(DATA_DIR / "fps_status.json", {"pending_signout": True, "at": int(time.time())})
    return {"needs_signout": True}


class Replay:
    proc = None

    @classmethod
    def command(cls, fps, wrap, seg=5, source=("-f", "gdigrab", "-draw_mouse", "0", "-i", "title=Roblox")):
        return [str(FFMPEG), "-hide_banner", "-loglevel", "error", "-framerate" if source[1] == "gdigrab" else "-r", str(fps),
                *source, "-vf", "scale=-2:'min(1080,ih)'", "-c:v", "libx264", "-preset", "ultrafast", "-tune", "zerolatency",
                "-crf", "26", "-pix_fmt", "yuv420p", "-g", str(fps), "-f", "segment", "-segment_time", str(seg),
                "-segment_wrap", str(wrap), "-reset_timestamps", "1", str(REPLAY_DIR / "seg%02d.ts")]

    @classmethod
    def run_while_roblox(cls):
        rp = load_settings().get("replay") or {}
        if not FFMPEG.exists() or not IS_WINDOWS:
            log("Instant replay is on but ffmpeg isn't set up yet")
            return
        REPLAY_DIR.mkdir(parents=True, exist_ok=True)
        fps = max(15, min(60, int(rp.get("fps") or 30)))
        wrap = max(3, int((rp.get("seconds") or 30) / 5) + 2)
        while roblox_running():
            if (cls.proc is None or cls.proc.poll() is not None) and roblox_rect() and roblox_in_front():
                for f in REPLAY_DIR.glob("seg*.ts"):
                    f.unlink(missing_ok=True)
                cls.proc = subprocess.Popen(cls.command(fps, wrap), stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL,
                                            stderr=subprocess.DEVNULL, creationflags=CREATE_NO_WINDOW | 0x00004000)
                log("Instant replay recording started")
            time.sleep(3)
        cls.stop()

    @classmethod
    def stop(cls):
        if cls.proc and cls.proc.poll() is None:
            kill_tree(cls.proc.pid)
        cls.proc = None

    @classmethod
    def save(cls, seconds=None, name=None):
        if not FFMPEG.exists():
            return None
        seconds = seconds or int((load_settings().get("replay") or {}).get("seconds") or 30)
        segs = sorted(REPLAY_DIR.glob("seg*.ts"), key=lambda p: p.stat().st_mtime) if REPLAY_DIR.is_dir() else []
        segs = [p for p in segs if time.time() - p.stat().st_mtime < seconds + 20]
        if not segs:
            return None
        cur = load_json(CURRENT_FILE, None) or {}
        name = re.sub(r'[<>:"/\\|?*]', "", name or cur.get("name") or "Roblox").strip()[:60] or "Roblox"
        out_dir = Path.home() / "Videos" / "Orbit"
        out_dir.mkdir(parents=True, exist_ok=True)
        dest = out_dir / f"{name} {time.strftime('%Y-%m-%d %H-%M-%S')}.mp4"
        work = REPLAY_DIR / "save"
        shutil.rmtree(work, ignore_errors=True)
        work.mkdir(parents=True)
        parts = []
        for i, p in enumerate(segs):
            try:
                shutil.copy2(p, work / f"{i:03d}.ts")
                parts.append(work / f"{i:03d}.ts")
            except OSError:
                pass
        (work / "list.txt").write_text("".join(f"file '{x.name}'\n" for x in parts), encoding="utf-8")
        joined = work / "joined.mp4"
        run = lambda args: subprocess.run([str(FFMPEG), "-hide_banner", "-loglevel", "error", "-y", *args], capture_output=True,
                                          timeout=90, creationflags=CREATE_NO_WINDOW)
        r = run(["-f", "concat", "-safe", "0", "-i", str(work / "list.txt"), "-c", "copy", str(joined)])
        if r.returncode == 0:
            r = run(["-sseof", f"-{seconds}", "-i", str(joined), "-c", "copy", "-movflags", "+faststart", str(dest)])
        shutil.rmtree(work, ignore_errors=True)
        if r.returncode != 0 or not dest.exists():
            log(f"Replay save failed: {r.stderr.decode('utf-8', 'ignore')[:300]}")
            return None
        log(f"Replay saved: {dest}")
        return str(dest)


def setup_ffmpeg(progress=None):
    TOOLS_DIR.mkdir(parents=True, exist_ok=True)
    if FFMPEG.exists():
        return True
    import zipfile
    url = "https://github.com/BtbN/FFmpeg-Builds/releases/download/latest/ffmpeg-master-latest-win64-gpl.zip"
    z = TOOLS_DIR / "ffmpeg.zip"
    download_file(url, z, progress)
    with zipfile.ZipFile(z) as zf:
        member = next(n for n in zf.namelist() if n.endswith("/bin/ffmpeg.exe"))
        with zf.open(member) as src, open(FFMPEG.with_suffix(".part"), "wb") as out:
            shutil.copyfileobj(src, out)
    os.replace(FFMPEG.with_suffix(".part"), FFMPEG)
    z.unlink(missing_ok=True)
    log("Downloaded ffmpeg for instant replay")
    return True


FONTS = {
    "inter": ("Inter", "Inter-SemiBold.otf", "Clean and modern, very readable."),
    "poppins": ("Poppins", "Poppins-Medium.ttf", "Round and friendly geometric style."),
    "mono": ("DejaVu Mono", "DejaVuSansMono-Bold.ttf", "Bold monospace, like a terminal."),
}
FONT_DIR = DATA_DIR / "fonts"


def font_file(fid):
    if fid == "custom":
        found = sorted(FONT_DIR.glob("custom.*")) if FONT_DIR.is_dir() else []
        return found[0] if found else None
    if fid in FONTS:
        f = resource_dir() / "ui" / "fonts" / FONTS[fid][1]
        return f if f.exists() else None
    return None


def font_overrides(settings, version_dir):
    src = font_file(settings.get("font") or "")
    if not src:
        return {}
    out = {"content/fonts/CustomFont.ttf": src}
    vdir = Path(version_dir)
    families = vdir / "content" / "fonts" / "families"
    cache = DATA_DIR / "fontcache" / vdir.name
    cache.mkdir(parents=True, exist_ok=True)
    for fam in (families.glob("*.json") if families.is_dir() else []):
        try:
            backup = vdir / MOD_BACKUP_DIR / "content" / "fonts" / "families" / fam.name
            data = json.loads((backup if backup.exists() else fam).read_text(encoding="utf-8"))
            for face in data.get("faces", []):
                face["assetId"] = "rbxasset://fonts/CustomFont.ttf"
            dest = cache / fam.name
            dest.write_text(json.dumps(data), encoding="utf-8")
            out[f"content/fonts/families/{fam.name}"] = dest
        except Exception as e:
            log(f"Font family {fam.name} skipped: {e}")
    return out


CHARSOUNDS = {
    "charsounds_soft": ("Soft Steps", "Gentle jump, landing, walking and get-up sounds."),
    "charsounds_retro": ("Retro", "Chiptune-style jump, landing and footsteps."),
    "charsounds_quiet": ("Quiet", "Very soft movement sounds for focused play."),
}


def player_card(settings):
    from PIL import Image, ImageDraw, ImageFilter
    prof = settings.get("profile") or {}
    uid = prof.get("roblox_id")
    W, H = 1200, 675
    c1, c2 = accent_pair(settings["appearance"])
    a1, a2 = (tuple(int(x[i:i + 2], 16) for i in (1, 3, 5)) for x in (c1, c2))
    img = Image.new("RGB", (W, H), (8, 5, 16))
    glow = Image.new("RGB", (W, H), (0, 0, 0))
    gd = ImageDraw.Draw(glow)
    gd.ellipse([700, -300, 1500, 500], fill=a2)
    gd.ellipse([-300, 350, 600, 1100], fill=a1)
    img = Image.blend(img, glow.filter(ImageFilter.GaussianBlur(160)), 0.55)
    d = ImageDraw.Draw(img)
    av = avatar_file(uid) if uid else None
    if av:
        a = Image.open(av).convert("RGBA").resize((230, 230))
        mask = Image.new("L", (230, 230), 0)
        ImageDraw.Draw(mask).ellipse([0, 0, 229, 229], fill=255)
        ring = Image.new("RGBA", (250, 250), (0, 0, 0, 0))
        ImageDraw.Draw(ring).ellipse([0, 0, 249, 249], fill=a1 + (255,))
        img.paste(ring, (60, 60), ring)
        img.paste(a, (70, 70), mask)
    name = prof.get("display") or prof.get("username") or "Orbit player"
    if not av:
        d.ellipse([60, 60, 310, 310], fill=a1)
        d.ellipse([70, 70, 300, 300], fill=(20, 14, 34))
        d.text((185, 185), name[:1].upper(), font=_font(120, True), fill=(245, 240, 255), anchor="mm")
    d.text((340, 100), name[:22], font=_font(64, True), fill=(245, 240, 255))
    if prof.get("username"):
        d.text((344, 180), "@" + prof["username"], font=_font(30), fill=(190, 180, 220))
    lv = orbit_level()
    d.rounded_rectangle([340, 236, 340 + 24 + int(_font(26, True).getlength(f"LEVEL {lv['level']} · {lv['title'].upper()}")), 280], 20, fill=a1)
    d.text((352, 241), f"LEVEL {lv['level']} · {lv['title'].upper()}", font=_font(26, True), fill=(255, 255, 255))
    play = load_json(PLAYTIME_FILE, {}) or {}
    total = sum(e.get("seconds", 0) for e in play.values())
    sessions = _sessions()
    ach = achievements_state()
    done = sum(1 for x in ach["list"] if x["unlocked"])
    regions = {}
    for x in sessions:
        for rname in REGIONS:
            if x.get("location") and in_region(x["location"], rname):
                regions[rname] = regions.get(rname, 0) + 1
    fav = max(regions, key=regions.get) if regions else "-"
    since = min([x.get("start", time.time()) for x in sessions] or [time.time()])
    count = max(len(sessions), sum(e.get("sessions", 0) for e in play.values()))
    x = 60
    for label, val in (("PLAYED", fmt_duration(total)), ("SESSIONS", str(count)),
                       ("ACHIEVEMENTS", f"{done}/{len(ach['list'])}"), ("TOP REGION", fav)):
        d.rounded_rectangle([x, 340, x + 255, 470], 22, fill=(20, 14, 34), outline=a1, width=2)
        d.text((x + 22, 360), label, font=_font(20, True), fill=(170, 160, 200))
        d.text((x + 22, 395), val, font=_font(40, True), fill=(245, 240, 255))
        x += 275
    top = sorted(play.items(), key=lambda kv: -kv[1].get("seconds", 0))[:3]
    d.text((60, 505), "TOP GAMES", font=_font(20, True), fill=(170, 160, 200))
    for i, (pid, e) in enumerate(top):
        d.text((60 + i * 370, 540), f"{i + 1}. {(e.get('name') or pid)[:24]}", font=_font(30, True), fill=(245, 240, 255))
        d.text((60 + i * 370, 580), fmt_duration(e.get("seconds", 0)), font=_font(24), fill=a2)
    d.text((W - 60, H - 30), f"Orbit Launcher · playing since {time.strftime('%b %Y', time.localtime(since))}",
           font=_font(20), fill=(150, 140, 180), anchor="rs")
    out = Path.home() / "Pictures" / "Orbit"
    out.mkdir(parents=True, exist_ok=True)
    dest = out / f"Orbit player card {time.strftime('%Y-%m-%d')}.png"
    img.save(dest)
    return dest


def apply_jump_list():
    if not IS_WINDOWS or not is_frozen():
        return False
    import clr
    token = ", Version=4.0.0.0, Culture=neutral, PublicKeyToken=31bf3856ad364e35"
    for asm in ("WindowsBase", "PresentationCore", "PresentationFramework"):
        try:
            clr.AddReference(asm + token)
        except Exception:
            from System.Reflection import Assembly
            Assembly.Load(asm + token)
    from System.Threading import ApartmentState, Thread, ThreadStart
    from System.Windows.Shell import JumpList, JumpTask
    exe = str(helper_ready() or sys.executable)
    icon = str(INSTALLED_EXE if INSTALLED_EXE.exists() else sys.executable)
    tasks = [("Launch Roblox", "launch", "Start Roblox through Orbit"), ("Rejoin last server", "rejoin", "Go back to your last server"),
             ("New server", "new", "Hop to a fresh server in your current game"),
             ("Copy join link", "joinlink", "Copy a link friends can use to join your server")]
    errors = []

    def work():
        try:
            jl = JumpList()
            jl.ShowRecentCategory = False
            jl.ShowFrequentCategory = False
            for title, action, desc in tasks:
                t = JumpTask()
                t.Title = title
                t.Description = desc
                t.ApplicationPath = exe
                t.Arguments = f"{ACTION_FLAG} {action}"
                t.IconResourcePath = icon
                t.IconResourceIndex = 0
                jl.JumpItems.Add(t)
            jl.Apply()
        except Exception as e:
            errors.append(str(e))
    th = Thread(ThreadStart(work))
    th.SetApartmentState(ApartmentState.STA)
    th.Start()
    th.Join()
    if errors:
        raise RuntimeError(errors[0])
    log("Taskbar jump list ready")
    return True


PERIODIC_FILE = DATA_DIR / "periodic.json"
PRESENCE_FILE = DATA_DIR / "presence.json"
GAME_UPDATES_FILE = DATA_DIR / "game_updates.json"
LAST_REPORT_FILE = DATA_DIR / "last_report.json"
NEWS_FILE = DATA_DIR / "news_cache.json"
STORE_FILE = DATA_DIR / "store_cache.json"
OVERLAY_PORT = 17171
WEBHOOK_RE = re.compile(r"https://(?:ptb\.|canary\.)?discord(?:app)?\.com/api/webhooks/\d+/[\w-]+")


def claim_periodic(owner):
    st = load_json(PERIODIC_FILE, {}) or {}
    mine = st.get("pid") == os.getpid()
    if not mine and time.time() - st.get("at", 0) < 150 and pid_alive(st.get("pid")):
        return False
    save_json(PERIODIC_FILE, {"pid": os.getpid(), "owner": owner, "at": int(time.time())})
    return True


def presence_of(ids):
    out = {}
    for i in range(0, len(ids), 50):
        data = post_json("https://presence.roblox.com/v1/presence/users", {"userIds": ids[i:i + 50]})
        for p in data.get("userPresences", []):
            out[str(p.get("userId"))] = p
    return out


def check_friend_alerts():
    settings = load_settings()
    watch = [x for x in settings.get("recent_players", []) if x.get("alert")]
    if not watch:
        return
    pres = presence_of([int(x["id"]) for x in watch])
    old = load_json(PRESENCE_FILE, {}) or {}
    new = {}
    for u in watch:
        p = pres.get(str(u["id"])) or {}
        t = p.get("userPresenceType", 0)
        new[str(u["id"])] = t
        if t == 2 and old.get(str(u["id"])) not in (2, None):
            where = p.get("lastLocation") or "a game"
            save_json(DATA_DIR / "friend_alert.json", {"id": u["id"], "name": u.get("display") or u.get("name"), "at": int(time.time())})
            spawn_toast(f"{u.get('display') or u.get('name')} is playing", f"{where}. Press Ctrl+Alt+F to join them.")
            log(f"Friend alert: {u.get('name')} started playing {where}")
    save_json(PRESENCE_FILE, new)


def check_game_updates():
    settings = load_settings()
    if not settings["session"].get("game_update_alerts", True) or not settings.get("library"):
        return
    unis = {}
    for g in settings["library"]:
        info = game_info(g["pid"])
        if info.get("universe"):
            unis[str(info["universe"])] = info.get("name") or g.get("name")
    if not unis:
        return
    data = fetch_json("https://games.roblox.com/v1/games?universeIds=" + ",".join(list(unis)[:50]), timeout=10).get("data", [])
    seen = load_json(GAME_UPDATES_FILE, {}) or {}
    for d in data:
        uid, updated = str(d.get("id")), d.get("updated")
        if not updated:
            continue
        if seen.get(uid) and seen[uid] != updated:
            spawn_toast(f"{d.get('name') or unis.get(uid)} just updated", "New version is live. Rejoin to get it.")
            log(f"Game update: {d.get('name')} ({updated})")
        seen[uid] = updated
    save_json(GAME_UPDATES_FILE, seen)


def game_updated_times(settings):
    seen = load_json(GAME_UPDATES_FILE, {}) or {}
    out = {}
    for g in settings.get("library") or []:
        info = _GAME_CACHE.get(str(g["pid"])) or cached_game(g["pid"]) or {}
        stamp = seen.get(str(info.get("universe")))
        if stamp:
            try:
                from datetime import datetime
                out[str(g["pid"])] = int(datetime.fromisoformat(stamp.replace("Z", "+00:00")).timestamp())
            except Exception:
                pass
    return out


def lag_spikes(pings):
    vals, spikes = [], 0
    for _, p in pings:
        if p is None:
            continue
        if len(vals) >= 4:
            base = sorted(vals[-12:])[len(vals[-12:]) // 2]
            if p > max(150, base * 2.2, base + 80):
                spikes += 1
        vals.append(p)
    return spikes


def write_session_report(game, seconds):
    problems = [x for x in (load_json(PROBLEMS_FILE, []) or []) if x.get("time", 0) >= game.get("joined", 0) - 5]
    ping = ping_summary(game.get("pings") or [])
    rep = {"name": game.get("name") or "Roblox", "place_id": str(game.get("place_id")), "seconds": int(seconds),
           "location": game.get("location"), "ping": ping, "spikes": lag_spikes(game.get("pings") or []),
           "fps": game.get("fps"), "problems": [x.get("title") for x in problems][:5], "at": int(time.time())}
    save_json(LAST_REPORT_FILE, rep)
    parts = [fmt_duration(seconds)]
    if ping:
        parts.append(f"avg {ping['avg']} ms")
    if rep["spikes"]:
        parts.append(f"{rep['spikes']} lag spike{'s' if rep['spikes'] != 1 else ''}")
    if rep["fps"]:
        parts.append(f"{rep['fps']['avg']} fps")
    if rep["problems"]:
        parts.append(f"{len(rep['problems'])} disconnect{'s' if len(rep['problems']) != 1 else ''}")
    return rep, " · ".join(parts)


def orbit_level():
    play = load_json(PLAYTIME_FILE, {}) or {}
    minutes = sum(e.get("seconds", 0) for e in play.values()) // 60
    ach = sum(1 for x in achievements_state()["list"] if x["unlocked"])
    days = len(calendar_data())
    xp = int(minutes + ach * 100 + days * 25)
    level = 1
    while xp >= 60 * level * level:
        level += 1
    floor, ceil = 60 * (level - 1) ** 2, 60 * level * level
    titles = [(1, "Stargazer"), (5, "Comet"), (10, "Orbiter"), (15, "Nova"), (20, "Pulsar"), (30, "Quasar"), (40, "Black Hole")]
    title = [t for lv, t in titles if level >= lv][-1]
    return {"xp": xp, "level": level, "title": title, "progress": round((xp - floor) / max(1, ceil - floor), 3),
            "next": ceil - xp, "parts": {"minutes": minutes, "achievements": ach, "days": days}}


def dir_size(p):
    try:
        if p.is_file():
            return p.stat().st_size
        return sum(f.stat().st_size for f in p.rglob("*") if f.is_file())
    except OSError:
        return 0


def storage_report():
    root = LOCALAPPDATA / "Roblox" / "Versions"
    players = player_dirs()
    old_versions = [d for d in players[1:] if d.parent == root]
    logs = [p for p in ROBLOX_LOGS.glob("*.log") if p.stat().st_mtime < time.time() - 86400] if ROBLOX_LOGS.is_dir() else []
    temp = [p for p in (DATA_DIR / "rbx-download", DATA_DIR / "fps", DATA_DIR / "fontcache", REPLAY_DIR) if p.exists()]
    clips = Path.home() / "Videos" / "Orbit"
    shots = screenshot_dirs()
    cats = [
        ("old_versions", "Old Roblox versions", "Older copies of Roblox kept after updates.", sum(dir_size(d) for d in old_versions), True),
        ("logs", "Old Roblox logs", "Log files older than a day.", sum(dir_size(p) for p in logs), True),
        ("cache", "Roblox cache", "Downloaded game files. Roblox re-downloads what it needs.", sum(dir_size(p) for p in roblox_cache_paths() if "logs" not in str(p)), True),
        ("orbit_temp", "Orbit temporary files", "Leftover downloads, FPS data and replay buffers.", sum(dir_size(p) for p in temp), True),
        ("clips", "Replay clips", "Clips saved with Ctrl+Alt+C (Videos\\Orbit).", dir_size(clips) if clips.exists() else 0, False),
        ("screenshots", "Screenshots", "Your Roblox screenshots. Never cleaned automatically.", sum(dir_size(d) for d in shots), False),
    ]
    return [{"id": c, "title": t, "desc": d, "bytes": b, "auto": a} for c, t, d, b, a in cats]


def clean_storage(cat):
    if cat in ("old_versions", "cache") and roblox_running():
        raise OSError("Close Roblox first.")
    freed = 0
    if cat == "old_versions":
        root = LOCALAPPDATA / "Roblox" / "Versions"
        for d in [d for d in player_dirs()[1:] if d.parent == root]:
            freed += dir_size(d)
            shutil.rmtree(d, ignore_errors=True)
    elif cat == "logs":
        for p in ROBLOX_LOGS.glob("*.log"):
            if p.stat().st_mtime < time.time() - 86400:
                freed += dir_size(p)
                p.unlink(missing_ok=True)
    elif cat == "cache":
        for p in roblox_cache_paths():
            freed += dir_size(p)
            shutil.rmtree(p, ignore_errors=True) if p.is_dir() else p.unlink(missing_ok=True)
    elif cat == "orbit_temp":
        for p in (DATA_DIR / "rbx-download", DATA_DIR / "fps", DATA_DIR / "fontcache"):
            freed += dir_size(p)
            shutil.rmtree(p, ignore_errors=True)
        if not (Replay.proc and Replay.proc.poll() is None):
            freed += dir_size(REPLAY_DIR)
            shutil.rmtree(REPLAY_DIR, ignore_errors=True)
    elif cat == "clips":
        clips = Path.home() / "Videos" / "Orbit"
        for p in clips.glob("*.mp4") if clips.exists() else []:
            if p.stat().st_mtime < time.time() - 30 * 86400:
                freed += dir_size(p)
                p.unlink(missing_ok=True)
    else:
        raise ValueError("That can't be cleaned from here.")
    log(f"Cleaned {cat}: {freed / 1048576:.1f} MB")
    return freed


def sync_candidates():
    home = Path.home()
    out = []
    for env in ("OneDrive", "OneDriveConsumer", "OneDriveCommercial"):
        if os.environ.get(env) and Path(os.environ[env]).is_dir():
            out.append(("OneDrive", Path(os.environ[env])))
    for p in (home / "Google Drive", home / "My Drive", Path("G:/My Drive"), home / "Dropbox", home / "iCloudDrive"):
        try:
            if p.is_dir():
                out.append((p.name if p.name != "My Drive" else "Google Drive", p))
        except OSError:
            pass
    seen, uniq = set(), []
    for name, p in out:
        if str(p) not in seen:
            seen.add(str(p))
            uniq.append({"name": name, "path": str(p)})
    return uniq


def sync_file(settings):
    folder = (settings.get("sync") or {}).get("folder")
    return Path(folder) / "Orbit" / "Orbit-sync.orbitbackup" if folder else None


def run_sync(settings, force=False):
    f = sync_file(settings)
    if not f:
        return None
    meta = load_json(DATA_DIR / "sync.json", {}) or {}
    if not force and time.time() - meta.get("at", 0) < 6 * 3600:
        return None
    f.parent.mkdir(parents=True, exist_ok=True)
    tmp = f.with_suffix(".tmp")
    export_backup(tmp, settings)
    os.replace(tmp, f)
    save_json(DATA_DIR / "sync.json", {"at": int(time.time()), "file": str(f)})
    log(f"Synced backup to {f}")
    return str(f)


def emoji_source(style):
    if style == "windows" and IS_WINDOWS:
        f = Path(os.environ.get("WINDIR", "C:/Windows")) / "Fonts" / "seguiemj.ttf"
        return f if f.exists() else None
    return None


def raw_url(path):
    repo = update_repo()
    return f"https://raw.githubusercontent.com/{repo}/main/{path}" if repo else None


def fetch_news():
    url = raw_url("news.json")
    if not url:
        return load_json(NEWS_FILE, {"posts": []})
    try:
        data = fetch_json(url + f"?t={int(time.time() // 300)}", timeout=10)
        posts = [p for p in (data.get("posts") or []) if isinstance(p, dict) and p.get("id") and p.get("title")][:30]
        save_json(NEWS_FILE, {"posts": posts, "at": int(time.time())})
        return {"posts": posts}
    except Exception as e:
        log(f"News fetch failed: {e}")
        return load_json(NEWS_FILE, {"posts": []})


STORE_KINDS = {"crosshair", "cursor", "sound", "charsound", "font"}
STORE_ROOTS = ("content/", "PlatformContent/", "ExtraContent/")


def fetch_store():
    url = raw_url("store/index.json")
    if not url:
        return load_json(STORE_FILE, {"items": []})
    try:
        data = fetch_json(url + f"?t={int(time.time() // 300)}", timeout=10)
        items = []
        for it in data.get("items") or []:
            if not isinstance(it, dict) or it.get("kind") not in STORE_KINDS or not it.get("id") or not it.get("files"):
                continue
            if not re.fullmatch(r"[a-z0-9_-]{2,40}", str(it["id"])):
                continue
            it["preview_url"] = raw_url("store/" + it["preview"]) if it.get("preview") else None
            items.append(it)
        save_json(STORE_FILE, {"items": items, "at": int(time.time())})
        return {"items": items}
    except Exception as e:
        log(f"Store fetch failed: {e}")
        return load_json(STORE_FILE, {"items": []})


def install_store_item(settings, item_id):
    items = (load_json(STORE_FILE, {}) or {}).get("items") or []
    it = next((x for x in items if x.get("id") == item_id), None)
    if not it:
        raise ValueError("That item isn't in the store anymore.")
    folder = mods_dir(settings)
    count = 0
    for target, src in it["files"].items():
        if it["kind"] != "font" and not str(target).startswith(STORE_ROOTS):
            continue
        if ".." in str(target).split("/") or ".." in str(src).split("/"):
            continue
        url = raw_url("store/" + src)
        if it["kind"] == "font":
            FONT_DIR.mkdir(parents=True, exist_ok=True)
            for old in FONT_DIR.glob("custom.*"):
                old.unlink(missing_ok=True)
            ext = ".otf" if str(src).lower().endswith(".otf") else ".ttf"
            download_file(url, FONT_DIR / ("custom" + ext))
            settings["font"] = "custom"
        else:
            download_file(url, folder / target)
        count += 1
    settings["apply_mods"] = True
    save_settings(settings)
    log(f"Installed store item {item_id} ({count} files)")
    return count


class OverlayServer:
    started = False

    @classmethod
    def start(cls):
        if cls.started:
            return
        import http.server
        page = OVERLAY_HTML

        class Handler(http.server.BaseHTTPRequestHandler):
            def log_message(self, *a):
                pass

            def do_GET(self):
                path = self.path.split("?")[0]
                if path in ("/", "/overlay"):
                    body, ctype = page.encode("utf-8"), "text/html; charset=utf-8"
                elif path == "/state":
                    settings = load_settings()
                    cur = load_json(CURRENT_FILE, None) or {}
                    streamer = settings["session"].get("streamer_mode")
                    live = load_json(FPS_LIVE_FILE, None) or {}
                    st = {"game": cur.get("name"), "joined": cur.get("joined"), "ping": cur.get("ping"),
                          "location": None if streamer else cur.get("location"),
                          "region": next((r for r in REGIONS if in_region(cur.get("location"), r)), None),
                          "fps": live.get("fps") if time.time() - live.get("at", 0) < 5 else None,
                          "accent": accent_pair(settings["appearance"]), "level": orbit_level()["level"]}
                    body, ctype = json.dumps(st).encode(), "application/json"
                else:
                    self.send_response(404)
                    self.end_headers()
                    return
                self.send_response(200)
                self.send_header("Content-Type", ctype)
                self.send_header("Cache-Control", "no-store")
                self.send_header("Content-Length", str(len(body)))
                self.end_headers()
                self.wfile.write(body)

        try:
            srv = http.server.ThreadingHTTPServer(("127.0.0.1", OVERLAY_PORT), Handler)
        except OSError:
            return
        cls.started = True
        threading.Thread(target=srv.serve_forever, daemon=True).start()
        log(f"Stream overlay ready at http://127.0.0.1:{OVERLAY_PORT}/overlay")


OVERLAY_HTML = """<!DOCTYPE html><html><head><meta charset="utf-8"><style>
html,body{margin:0;background:transparent;font-family:'Segoe UI',system-ui,sans-serif;color:#fff;overflow:hidden}
.card{display:inline-flex;align-items:center;gap:14px;padding:12px 18px 12px 12px;border-radius:18px;background:rgba(10,6,20,.82);
border:2px solid var(--a);box-shadow:0 0 26px -6px var(--a);transition:opacity .5s,transform .5s}
.card.hide{opacity:0;transform:translateY(10px)}
.hole{width:44px;height:44px;border-radius:50%;background:radial-gradient(circle,#000 40%,var(--a) 46%,transparent 72%);flex:none}
.g{font-weight:700;font-size:20px;line-height:1.1}.s{font-size:14px;opacity:.85;margin-top:3px}
.chips{display:flex;gap:6px;margin-top:6px}.chip{font-size:13px;font-weight:700;padding:2px 9px;border-radius:99px;background:rgba(255,255,255,.1)}
.good{color:#4ade80}.mid{color:#fbbf24}.bad{color:#fb7185}
</style></head><body><div class="card hide" id="c"><div class="hole"></div><div><div class="g" id="g">Roblox</div><div class="s" id="s"></div>
<div class="chips"><span class="chip" id="t">0:00</span><span class="chip" id="p"></span><span class="chip" id="f"></span></div></div></div>
<script>
let st=null;const $=(i)=>document.getElementById(i);
const fmt=(x)=>{x=Math.max(0,Math.floor(x));const h=Math.floor(x/3600),m=Math.floor(x%3600/60),s=x%60;return h?`${h}:${String(m).padStart(2,"0")}:${String(s).padStart(2,"0")}`:`${m}:${String(s).padStart(2,"0")}`};
async function poll(){try{st=await (await fetch("/state",{cache:"no-store"})).json();}catch(e){}draw();}
function draw(){const c=$("c");if(!st||!st.game){c.classList.add("hide");return;}c.classList.remove("hide");
document.documentElement.style.setProperty("--a",st.accent[0]);$("g").textContent=st.game;
$("s").textContent=st.location||st.region||"";$("t").textContent=fmt(Date.now()/1000-st.joined);
const p=$("p");p.style.display=st.ping==null?"none":"";p.textContent=st.ping+" ms";p.className="chip "+(st.ping<80?"good":st.ping<150?"mid":"bad");
const f=$("f");f.style.display=st.fps==null?"none":"";f.textContent=st.fps+" fps";}
poll();setInterval(poll,2000);setInterval(draw,1000);
</script></body></html>"""


def share_to_discord(webhook, text=None, file=None):
    if not WEBHOOK_RE.fullmatch(webhook or ""):
        raise ValueError("That isn't a Discord webhook link. In Discord: channel settings > Integrations > Webhooks > Copy Webhook URL.")
    boundary = uuid.uuid4().hex
    parts = []
    payload = json.dumps({"content": text or "", "username": "Orbit Launcher"})
    parts.append(f'--{boundary}\r\nContent-Disposition: form-data; name="payload_json"\r\nContent-Type: application/json\r\n\r\n{payload}\r\n'.encode())
    if file:
        f = Path(file)
        parts.append(f'--{boundary}\r\nContent-Disposition: form-data; name="files[0]"; filename="{f.name}"\r\nContent-Type: image/png\r\n\r\n'.encode()
                     + f.read_bytes() + b"\r\n")
    parts.append(f"--{boundary}--\r\n".encode())
    req = urllib.request.Request(webhook, data=b"".join(parts), method="POST",
                                 headers={"Content-Type": f"multipart/form-data; boundary={boundary}", "User-Agent": f"{APP_NAME}/{APP_VERSION}"})
    with urllib.request.urlopen(req, timeout=20) as r:
        return r.status


def periodic_jobs(owner):
    if not claim_periodic(owner):
        return
    now = time.time()
    st = load_json(DATA_DIR / "periodic_runs.json", {}) or {}
    jobs = [("premium", 3600, lambda: load_settings().get("premium_key") and revoked_premium_ids(True)),
            ("friends", 60, check_friend_alerts), ("games", 30 * 60, check_game_updates),
            ("sync", 30 * 60, lambda: run_sync(load_settings())), ("clean", 24 * 3600, auto_clean)]
    for name, every, fn in jobs:
        if now - st.get(name, 0) >= every:
            st[name] = now
            try:
                fn()
            except Exception as e:
                log(f"Background job {name} failed: {e}")
    save_json(DATA_DIR / "periodic_runs.json", st)


def auto_clean():
    if not (load_settings().get("storage") or {}).get("auto_clean"):
        return
    for cat in ("logs", "orbit_temp") + (() if roblox_running() else ("old_versions",)):
        try:
            clean_storage(cat)
        except Exception as e:
            log(f"Auto clean {cat}: {e}")


_P = 2 ** 255 - 19
_L = 2 ** 252 + 27742317777372353535851937790883648493
_D = -121665 * pow(121666, _P - 2, _P) % _P
_I = pow(2, (_P - 1) // 4, _P)


def _inv(x):
    return pow(x, _P - 2, _P)


def _xrecover(y):
    xx = (y * y - 1) * _inv(_D * y * y + 1)
    x = pow(xx, (_P + 3) // 8, _P)
    if (x * x - xx) % _P:
        x = x * _I % _P
    if (x * x - xx) % _P:
        raise ValueError("not on curve")
    return x


_BY = 4 * _inv(5) % _P
_BX = _xrecover(_BY)
if _BX & 1:
    _BX = _P - _BX
_B = (_BX, _BY, 1, _BX * _BY % _P)


def _add(p, q):
    x1, y1, z1, t1 = p
    x2, y2, z2, t2 = q
    a = (y1 - x1) * (y2 - x2) % _P
    b = (y1 + x1) * (y2 + x2) % _P
    c = t1 * 2 * _D * t2 % _P
    d = z1 * 2 * z2 % _P
    e, f, g, h = b - a, d - c, d + c, b + a
    return (e * f % _P, g * h % _P, f * g % _P, e * h % _P)


def _mul(s, p):
    q = (0, 1, 1, 0)
    while s > 0:
        if s & 1:
            q = _add(q, p)
        p = _add(p, p)
        s >>= 1
    return q


def _enc(p):
    x, y, z, _ = p
    zi = _inv(z)
    x, y = x * zi % _P, y * zi % _P
    return (y | ((x & 1) << 255)).to_bytes(32, "little")


def _dec(s):
    y = int.from_bytes(s, "little")
    sign, y = y >> 255, y & ((1 << 255) - 1)
    if y >= _P:
        raise ValueError("bad point")
    x = _xrecover(y)
    if (x & 1) != sign:
        if x == 0:
            raise ValueError("bad point")
        x = _P - x
    return (x, y, 1, x * y % _P)


def _h(m):
    return hashlib.sha512(m).digest()


def _clamp(h):
    a = int.from_bytes(h[:32], "little")
    a &= (1 << 254) - 8
    return a | (1 << 254)


def ed_public(seed):
    return _enc(_mul(_clamp(_h(seed)), _B))


def ed_sign(seed, msg):
    h = _h(seed)
    a = _clamp(h)
    pub = _enc(_mul(a, _B))
    r = int.from_bytes(_h(h[32:] + msg), "little") % _L
    rr = _enc(_mul(r, _B))
    k = int.from_bytes(_h(rr + pub + msg), "little") % _L
    return rr + ((r + k * a) % _L).to_bytes(32, "little")


def ed_verify(pub, msg, sig):
    if len(sig) != 64 or len(pub) != 32:
        return False
    try:
        r, a = _dec(sig[:32]), _dec(pub)
    except ValueError:
        return False
    s = int.from_bytes(sig[32:], "little")
    if s >= _L:
        return False
    k = int.from_bytes(_h(sig[:32] + pub + msg), "little") % _L
    return _enc(_mul(s, _B)) == _enc(_add(r, _mul(k, a)))


OWNER_PUBKEY = bytes.fromhex("e77c7f03f5c7d8fab5587faf7e99491cac4b6177cbd6ffd8254c40974a8f73b4")
OWNER_KEY_FILE = DATA_DIR / "owner.key"
OWNER_ISSUED_FILE = DATA_DIR / "owner_issued.json"
PREMIUM_REVOKED_CACHE = DATA_DIR / "premium_revoked.json"
PREMIUM_PREFIX = "ORBIT-PREMIUM-"


def _b64u(b):
    return base64.urlsafe_b64encode(b).decode().rstrip("=")


def _unb64u(t):
    return base64.urlsafe_b64decode(t + "=" * (-len(t) % 4))


def owner_seed():
    try:
        data = json.loads(OWNER_KEY_FILE.read_text(encoding="utf-8"))
        seed = bytes.fromhex(data["seed"])
        return seed if len(seed) == 32 and ed_public(seed) == OWNER_PUBKEY else None
    except Exception:
        return None


def is_owner():
    return owner_seed() is not None


def roblox_user_by_name(name):
    name = (name or "").strip().lstrip("@")
    if not re.fullmatch(r"[A-Za-z0-9_]{3,20}", name):
        raise ValueError("Type the player's Roblox username.")
    data = post_json("https://users.roblox.com/v1/usernames/users", {"usernames": [name], "excludeBannedUsers": True})
    if not data.get("data"):
        raise ValueError(f'No Roblox player named "{name}".')
    return {"id": int(data["data"][0]["id"]), "name": data["data"][0]["name"]}


ROBLOX_ACCOUNT_FILE = DATA_DIR / "roblox_account.json"
_UID_RE = re.compile(rb"rbxuid=(\d+)|userid:(\d+)|\"UserId\"%3a(\d+)", re.I)
_UID_SEEN = {}


def current_roblox_uid():
    try:
        logs = sorted((f for f in ROBLOX_LOGS.glob("*Player*.log") if "CrashHandler" not in f.name),
                      key=lambda f: f.stat().st_mtime, reverse=True)[:6]
    except OSError:
        logs = []
    for f in logs:
        try:
            st = f.stat()
            sig = (str(f), st.st_size, st.st_mtime)
            if sig not in _UID_SEEN:
                with open(f, "rb") as fh:
                    data = fh.read(6_000_000)
                found = [next(g for g in m.groups() if g) for m in _UID_RE.finditer(data)]
                _UID_SEEN[sig] = int(found[-1]) if found else None
            uid = _UID_SEEN[sig]
        except OSError:
            continue
        if uid:
            if (load_json(ROBLOX_ACCOUNT_FILE, {}) or {}).get("id") != uid:
                save_json(ROBLOX_ACCOUNT_FILE, {"id": uid, "at": int(time.time())})
            return uid
    return (load_json(ROBLOX_ACCOUNT_FILE, {}) or {}).get("id")


def make_premium_key(name, days=0, uid=None):
    seed = owner_seed()
    if not seed:
        raise PermissionError("Only the owner can create premium keys.")
    now = int(time.time())
    payload = {"v": 2 if uid else 1, "id": uuid.uuid4().hex[:12], "for": (name or "").strip()[:40], "iat": now,
               "exp": now + int(days) * 86400 if days else 0}
    if uid:
        payload["uid"] = int(uid)
    body = json.dumps(payload, separators=(",", ":"), sort_keys=True).encode()
    code = PREMIUM_PREFIX + _b64u(body) + "." + _b64u(ed_sign(seed, body))
    issued = load_json(OWNER_ISSUED_FILE, []) or []
    issued.insert(0, {**payload, "code": code, "revoked": False})
    save_json(OWNER_ISSUED_FILE, issued[:500])
    log(f"Owner created a premium key for {payload['for'] or 'unnamed'} ({payload['id']})")
    return payload, code


def read_premium_key(code):
    code = (code or "").strip().replace(" ", "").replace("\n", "")
    if not code.startswith(PREMIUM_PREFIX) or "." not in code:
        return None
    try:
        body_t, sig_t = code[len(PREMIUM_PREFIX):].split(".", 1)
        body, sig = _unb64u(body_t), _unb64u(sig_t)
    except Exception:
        return None
    if not ed_verify(OWNER_PUBKEY, body, sig):
        return None
    try:
        data = json.loads(body)
    except ValueError:
        return None
    return data if isinstance(data, dict) and data.get("v") in (1, 2) and data.get("id") else None


def revoked_premium_ids(refresh=False, fetch=True):
    cache = load_json(PREMIUM_REVOKED_CACHE, {}) or {}
    if fetch and (refresh or time.time() - cache.get("at", 0) > 3600):
        url = raw_url("premium_revoked.json")
        if url:
            try:
                data = fetch_json(url + f"?t={int(time.time() // 300)}", timeout=8)
                cache = {"ids": [str(x) for x in (data.get("revoked") or [])], "at": int(time.time())}
                save_json(PREMIUM_REVOKED_CACHE, cache)
            except Exception as e:
                log(f"Couldn't check revoked premium keys: {e}")
    return set(cache.get("ids") or [])


def premium_status(settings, refresh=False, fetch=True):
    code = settings.get("premium_key") or ""
    if is_owner():
        return {"active": True, "owner": True, "for": "Owner", "exp": 0}
    if not code:
        return {"active": False, "reason": "none"}
    data = read_premium_key(code)
    if not data:
        return {"active": False, "reason": "invalid"}
    if data.get("exp") and time.time() > data["exp"]:
        return {"active": False, "reason": "expired", "for": data.get("for"), "exp": data["exp"]}
    if data["id"] in revoked_premium_ids(refresh, fetch):
        return {"active": False, "reason": "revoked", "for": data.get("for")}
    if data.get("uid") and current_roblox_uid() != data["uid"]:
        return {"active": False, "reason": "account", "for": data.get("for")}
    return {"active": True, "for": data.get("for"), "exp": data.get("exp") or 0, "id": data["id"], "since": data.get("iat")}


OWNER_GH_FILE = DATA_DIR / "owner_github.json"
GH_TOKEN_URL = ("https://github.com/settings/personal-access-tokens/new?name=Orbit%20owner%20panel"
                "&description=Lets%20Orbit%20turn%20premium%20keys%20off%20and%20on&expires_in=none&contents=write")


def _dpapi(data, protect=True):
    if not IS_WINDOWS:
        return data

    class BLOB(ctypes.Structure):
        _fields_ = [("cbData", ctypes.c_ulong), ("pbData", ctypes.POINTER(ctypes.c_char))]
    buf = ctypes.create_string_buffer(data, len(data))
    src, out = BLOB(len(data), ctypes.cast(buf, ctypes.POINTER(ctypes.c_char))), BLOB()
    crypt = ctypes.windll.crypt32
    fn = crypt.CryptProtectData if protect else crypt.CryptUnprotectData
    if not fn(ctypes.byref(src), None, None, None, None, 0x1, ctypes.byref(out)):
        raise OSError("Windows couldn't protect the GitHub token.")
    try:
        return ctypes.string_at(out.pbData, out.cbData)
    finally:
        ctypes.windll.kernel32.LocalFree(out.pbData)


def owner_gh_token():
    try:
        data = load_json(OWNER_GH_FILE, {}) or {}
        return _dpapi(base64.b64decode(data["token"]), False).decode() if data.get("token") else None
    except Exception:
        return None


def gh_api(method, path, token, body=None, timeout=15):
    req = urllib.request.Request("https://api.github.com" + path, method=method,
                                 data=json.dumps(body).encode() if body is not None else None,
                                 headers={"User-Agent": APP_ID + "/" + APP_VERSION, "Accept": "application/vnd.github+json",
                                          "Authorization": "Bearer " + token, "X-GitHub-Api-Version": "2022-11-28"})
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            return json.loads(r.read().decode("utf-8") or "{}")
    except urllib.error.HTTPError as e:
        if e.code == 401:
            raise PermissionError("GitHub didn't accept that token. It may have expired or been deleted.")
        if e.code in (403, 404):
            raise PermissionError("That token can't change files in the Orbit repo. Give it Contents: Read and write "
                                  "access to the orbit-launcher repository.")
        raise


def push_revoked(key_id, revoked, token):
    repo = update_repo()
    if not repo:
        raise RuntimeError("Orbit doesn't know its GitHub repo.")
    path = f"/repos/{repo}/contents/premium_revoked.json"
    try:
        cur = gh_api("GET", path, token)
        sha = cur.get("sha")
        ids = {str(x) for x in (json.loads(base64.b64decode(cur.get("content") or "e30=")).get("revoked") or [])}
    except urllib.error.HTTPError as e:
        if e.code != 404:
            raise
        sha, ids = None, set()
    ids = (ids | {key_id}) if revoked else (ids - {key_id})
    text = json.dumps({"revoked": sorted(ids)}, indent=2) + "\n"
    body = {"message": "Update premium keys", "content": base64.b64encode(text.encode()).decode()}
    if sha:
        body["sha"] = sha
    gh_api("PUT", path, token, body)
    save_json(PREMIUM_REVOKED_CACHE, {"ids": sorted(ids), "at": int(time.time())})
    log(f"Updated premium_revoked.json on GitHub ({len(ids)} turned off)")
    return ids


PREMIUM_LOCKED = "Boost is a Premium feature. Activate a premium key in Credits to use it."
PERF_PREMIUM = {"high_priority": False, "power_plan": False, "gpu_high": False, "game_mode": False, "no_dvr": False,
                "fps_cap": None, "graphics_quality": None}


def has_premium(settings, fetch=False):
    return premium_status(settings, fetch=fetch)["active"]


def enforce_premium(settings):
    if has_premium(settings):
        return False
    perf = settings.setdefault("performance", {})
    if not perf.get("boost") and all(perf.get(k) == v for k, v in PERF_PREMIUM.items()):
        return False
    if perf.get("boost"):
        set_boost(settings, False)
    perf.update(PERF_PREMIUM)
    save_settings(settings)
    try:
        apply_system_boost(settings, (player_dirs()[:1] or [None])[0])
    except Exception as e:
        log(f"Couldn't undo Boost settings: {e}")
    log("Boost features turned off (no premium)")
    return True


def claim_monitor():
    token = uuid.uuid4().hex
    save_json(MONITOR_FILE, {"token": token, "pid": os.getpid(), "version": APP_VERSION, "time": int(time.time())})
    return token


def monitor_claimed_by_other(token):
    data = load_json(MONITOR_FILE, {}) or {}
    return bool(data.get("token")) and data.get("token") != token


def ask_rejoin(info):
    try:
        import tkinter as tk
        from tkinter import messagebox
        root = tk.Tk()
        root.withdraw()
        root.attributes("-topmost", True)
        answer = messagebox.askyesno(APP_NAME, f"Roblox closed while you were in {info['name']}.\n\n"
                                               "Rejoin the same server?", parent=root)
        root.destroy()
        return answer
    except Exception:
        return False


def headless_main(uri):
    ensure_dirs()
    log(f"Launch requested: {uri[:80] + '...' if len(uri) > 80 else uri or '(no link)'}")
    if not IS_WINDOWS:
        message_box("Launching Roblox only works on Windows.", error=True)
        return
    updater, token, owns_monitor = None, None, None
    while True:
        settings = load_settings()
        try:
            enforce_premium(settings)
        except Exception as e:
            log(f"Premium check failed: {e}")
        started = start_roblox(settings, uri)
        if not started:
            return
        launch_time, updater = started
        if owns_monitor is None:
            token = claim_monitor()
            stop_stale_copies()
            owns_monitor = acquire_monitor_lock(wait=8)
            if not owns_monitor:
                log("An older tracker didn't let go; tracking this session anyway")
                owns_monitor = True
        if not owns_monitor or not SessionMonitor.wanted(settings):
            break
        monitor = SessionMonitor(settings, launch_time)
        monitor.token = token
        companions = start_companions(settings)
        monitor.boost.begin()
        try:
            monitor.run()
        except Exception:
            log("Session monitor crashed:\n" + traceback.format_exc())
        finally:
            monitor.boost.end()
            close_companions(companions)
        if monitor.crashed and ask_rejoin(monitor.crashed):
            uri = rejoin_uri(monitor.crashed["place_id"], monitor.crashed["job_id"])
            log("Rejoining after crash")
            continue
        break

    if updater:
        updater.join()
    settings = load_settings()
    if settings["registration"].get("registered") and not is_registered():
        try:
            register_protocols(settings)
        except OSError as e:
            log(f"Could not re-register: {e}")


ACHIEVEMENTS = [
    ("first_steps", "First Steps", "Play your first game through Orbit", "🚀"),
    ("tourist", "Tourist", "Play 5 different games", "🧭"),
    ("explorer", "Explorer", "Play 20 different games", "🌌"),
    ("regular", "Regular", "Play 25 sessions", "🎮"),
    ("server_hopper", "Server Hopper", "Play 100 sessions", "🛰️"),
    ("dedicated", "Dedicated", "Spend 10 hours in one game", "💜"),
    ("obsessed", "Obsessed", "Spend 50 hours in one game", "🔥"),
    ("marathon", "Marathon", "Play one session for 3 hours straight", "⏱️"),
    ("night_owl", "Night Owl", "Still playing past 3 AM", "🌙"),
    ("early_bird", "Early Bird", "Start a session between 5 and 8 AM", "☀️"),
    ("globetrotter", "Globetrotter", "Join servers in 5 different places", "🌍"),
    ("streak", "On a Roll", "Play 7 days in a row", "⚡"),
    ("weekender", "Weekend Warrior", "Play on 10 different weekend days", "🏖️"),
    ("veteran", "Veteran", "Reach 100 hours of total play time", "🏆"),
    ("legend", "Black Hole", "Reach 500 hours of total play time", "🕳️"),
]


def _sessions():
    data = load_json(SESSIONS_FILE, [])
    return data if isinstance(data, list) else []


def achievement_progress():
    play = load_json(PLAYTIME_FILE, {}) or {}
    sess = _sessions()
    total = sum(e.get("seconds", 0) for e in play.values())
    top = max([e.get("seconds", 0) for e in play.values()] or [0])
    count = max(len(sess), sum(e.get("sessions", 0) for e in play.values()))
    games = len(play)
    longest = max([x.get("seconds", 0) for x in sess] or [0])
    night = any(_hours_overlap(x, 3, 5) for x in sess)
    early = any(5 <= time.localtime(x["start"]).tm_hour < 8 for x in sess)
    places = len({x.get("location") for x in sess if x.get("location")})
    days = sorted({time.strftime("%Y-%m-%d", time.localtime(x["start"])) for x in sess})
    weekend = len({d for d in days if time.strptime(d, "%Y-%m-%d").tm_wday >= 5})
    streak = best = 0
    prev = None
    for d in days:
        t = time.mktime(time.strptime(d, "%Y-%m-%d"))
        streak = streak + 1 if prev is not None and 0 < t - prev <= 90000 else 1
        best, prev = max(best, streak), t
    h = 3600
    return {
        "first_steps": (count, 1), "tourist": (games, 5), "explorer": (games, 20), "regular": (count, 25),
        "server_hopper": (count, 100), "dedicated": (top / h, 10), "obsessed": (top / h, 50),
        "marathon": (longest / h, 3), "night_owl": (int(night), 1), "early_bird": (int(early), 1),
        "globetrotter": (places, 5), "streak": (best, 7), "weekender": (weekend, 10),
        "veteran": (total / h, 100), "legend": (total / h, 500),
    }


def _hours_overlap(sess, start_h, end_h):
    t = sess["start"]
    while t < sess["end"]:
        if start_h <= time.localtime(t).tm_hour < end_h:
            return True
        t += 600
    return False


def achievements_state():
    prog = achievement_progress()
    stored = load_json(ACHIEVEMENTS_FILE, {}) or {}
    out, new = [], []
    for aid, title, desc, icon in ACHIEVEMENTS:
        cur, goal = prog.get(aid, (0, 1))
        done = cur >= goal
        if done and aid not in stored:
            stored[aid] = int(time.time())
            new.append(aid)
        out.append({"id": aid, "title": title, "desc": desc, "icon": icon, "cur": round(min(cur, goal), 1),
                    "goal": goal, "unlocked": aid in stored, "at": stored.get(aid)})
    if new:
        save_json(ACHIEVEMENTS_FILE, stored)
    return {"list": out, "new": new}


def weekly_recap(now=None):
    now = now or time.time()
    week = [x for x in _sessions() if x.get("start", 0) >= now - 7 * 86400]
    if not week:
        return {"empty": True}
    by_game, by_day = {}, {}
    for x in week:
        g = by_game.setdefault(x["place_id"], {"name": x.get("name"), "seconds": 0})
        g["seconds"] += x.get("seconds", 0)
        day = time.strftime("%A", time.localtime(x["start"]))
        by_day[day] = by_day.get(day, 0) + x.get("seconds", 0)
    top_pid, top = max(by_game.items(), key=lambda kv: kv[1]["seconds"])
    earlier = {x["place_id"] for x in _sessions() if x.get("start", 0) < now - 7 * 86400}
    return {
        "empty": False, "total": sum(x.get("seconds", 0) for x in week), "sessions": len(week),
        "games": len(by_game), "new_games": len(set(by_game) - earlier),
        "top_game": top["name"], "top_pid": top_pid, "top_seconds": top["seconds"],
        "best_day": max(by_day.items(), key=lambda kv: kv[1])[0],
        "longest": max(x.get("seconds", 0) for x in week),
        "days_played": len({time.strftime("%Y-%m-%d", time.localtime(x["start"])) for x in week}),
        "range": time.strftime("%b %d", time.localtime(now - 6 * 86400)) + " – " + time.strftime("%b %d", time.localtime(now)),
    }


def _font(size, bold=False):
    from PIL import ImageFont
    names = (["segoeuib.ttf", "seguisb.ttf"] if bold else ["segoeui.ttf"]) + ["DejaVuSans-Bold.ttf" if bold else "DejaVuSans.ttf"]
    for name in names:
        for folder in (Path(os.environ.get("WINDIR", "C:/Windows")) / "Fonts", Path("/usr/share/fonts/truetype/dejavu")):
            if (folder / name).exists():
                return ImageFont.truetype(str(folder / name), size)
    return ImageFont.load_default(size)


def render_recap_png(recap, settings, dest):
    from PIL import Image, ImageDraw, ImageFilter
    accents = accent_pair(settings["appearance"])
    c1, c2 = (tuple(int(h[i:i + 2], 16) for i in (1, 3, 5)) for h in accents)
    W, H = 1200, 675
    img = Image.new("RGB", (W, H), (8, 6, 14))
    glow = Image.new("RGB", (W, H), (0, 0, 0))
    gd = ImageDraw.Draw(glow)
    gd.ellipse([700, -250, 1350, 400], fill=c1)
    gd.ellipse([-200, 420, 400, 900], fill=c2)
    img = Image.blend(img, glow.filter(ImageFilter.GaussianBlur(160)), 0.45)
    d = ImageDraw.Draw(img)
    import random
    rnd = random.Random(7)
    for _ in range(120):
        x, y, r = rnd.randint(0, W), rnd.randint(0, H), rnd.choice([1, 1, 1.5, 2])
        d.ellipse([x - r, y - r, x + r, y + r], fill=(230, 220, 255))
    d.text((70, 60), "ORBIT  ·  WEEKLY RECAP", font=_font(22, True), fill=c1)
    d.text((70, 96), recap["range"], font=_font(20), fill=(170, 160, 200))
    d.text((70, 150), fmt_duration(recap["total"]), font=_font(110, True), fill=(245, 240, 255))
    d.text((74, 280), "played this week", font=_font(28), fill=(170, 160, 200))
    cards = [("TOP GAME", recap["top_game"] or "-", fmt_duration(recap["top_seconds"])),
             ("SESSIONS", str(recap["sessions"]), f"{recap['days_played']} day(s) played"),
             ("BEST DAY", recap["best_day"], f"longest {fmt_duration(recap['longest'])}")]
    for i, (k, v, sub) in enumerate(cards):
        x0 = 70 + i * 360
        d.rounded_rectangle([x0, 390, x0 + 330, 590], radius=22, fill=(22, 17, 38), outline=c1, width=2)
        d.text((x0 + 26, 416), k, font=_font(18, True), fill=c1)
        val = v if len(v) <= 18 else v[:17] + "…"
        d.text((x0 + 26, 450), val, font=_font(36, True), fill=(245, 240, 255))
        d.text((x0 + 26, 530), sub, font=_font(20), fill=(170, 160, 200))
    d.text((W - 300, 624), "made with Orbit Launcher", font=_font(18), fill=(120, 110, 150))
    Path(dest).parent.mkdir(parents=True, exist_ok=True)
    img.save(dest)
    return dest


def pictures_dir():
    for p in (Path.home() / "OneDrive" / "Pictures", Path.home() / "Pictures"):
        if p.is_dir():
            return p
    return Path.home()


def screenshot_dirs():
    out = []
    for base in (Path.home() / "Pictures", Path.home() / "OneDrive" / "Pictures", Path.home() / "Videos"):
        if (base / "Roblox").is_dir():
            out.append(base / "Roblox")
    return out


def list_screenshots(game=None):
    files = []
    for folder in screenshot_dirs():
        subs = [folder] + [d for d in folder.iterdir() if d.is_dir()]
        for d in subs:
            if game and (d == folder or d.name != game):
                continue
            files += [p for p in d.iterdir() if p.suffix.lower() in (".png", ".jpg", ".jpeg") and p.is_file()]
    return sorted(files, key=lambda p: p.stat().st_mtime, reverse=True)


def screenshot_games():
    names = set()
    for folder in screenshot_dirs():
        names.update(d.name for d in folder.iterdir() if d.is_dir() and any(
            p.suffix.lower() in (".png", ".jpg", ".jpeg") for p in d.iterdir()))
    return sorted(names, key=str.lower)


def _is_screenshot(path):
    try:
        path = Path(path).resolve()
        return any(path.is_relative_to(d.resolve()) for d in screenshot_dirs())
    except (OSError, ValueError):
        return False


def has_pillow():
    import importlib.util
    return importlib.util.find_spec("PIL") is not None


def data_url(path, max_side=None, quality=82):
    import base64
    import hashlib
    path = Path(path)
    if max_side and has_pillow():
        THUMBS_DIR.mkdir(parents=True, exist_ok=True)
        key = hashlib.sha1(f"{path}|{path.stat().st_mtime}|{max_side}".encode()).hexdigest()
        thumb = THUMBS_DIR / f"{key}.jpg"
        if not thumb.exists():
            from PIL import Image
            with Image.open(path) as im:
                im = im.convert("RGB")
                im.thumbnail((max_side, max_side))
                im.save(thumb, "JPEG", quality=quality)
        path = thumb
    elif max_side and path.stat().st_size > 2_500_000:
        return None
    mime = "image/jpeg" if path.suffix.lower() in (".jpg", ".jpeg") else "image/png"
    return f"data:{mime};base64," + base64.b64encode(path.read_bytes()).decode()


def changelog_section(version):
    for base in (resource_dir(), Path(__file__).resolve().parent):
        f = base / "CHANGELOG.md"
        if f.exists():
            text = f.read_text(encoding="utf-8")
            m = re.search(rf"^## v?{re.escape(version)}\b.*?$(.*?)(?=^## |\Z)", text, re.S | re.M)
            return m.group(1).strip() if m else ""
    return ""


def background_file(settings):
    name = settings["appearance"].get("bg_file") or ""
    f = DATA_DIR / name
    return f if name and f.is_file() else None


BACKUP_FILES = ["settings.json", "playtime.json", "sessions.json", "achievements.json", "last_server.json",
                "roblox_icon.ico"]


def export_backup(dest, settings):
    import zipfile
    with zipfile.ZipFile(dest, "w", zipfile.ZIP_DEFLATED) as z:
        z.writestr("orbit_backup.json", json.dumps({"version": APP_VERSION, "made": int(time.time())}))
        for name in BACKUP_FILES:
            if (DATA_DIR / name).exists():
                z.write(DATA_DIR / name, name)
        bg = background_file(settings)
        if bg:
            z.write(bg, bg.name)
        for f in PROFILES_DIR.rglob("*"):
            if f.is_file():
                z.write(f, "ModProfiles/" + f.relative_to(PROFILES_DIR).as_posix())
    return dest


def import_backup(src):
    import zipfile
    with zipfile.ZipFile(src) as z:
        names = z.namelist()
        if "orbit_backup.json" not in names or "settings.json" not in names:
            raise ValueError("That file isn't an Orbit backup.")
        for name in names:
            target = (DATA_DIR / name).resolve()
            if not str(target).startswith(str(DATA_DIR.resolve())) or name.endswith("/"):
                continue
            target.parent.mkdir(parents=True, exist_ok=True)
            with z.open(name) as fsrc, open(target, "wb") as fdst:
                shutil.copyfileobj(fsrc, fdst)


_GUI_MUTEX = None


def acquire_gui_lock(wait=0.0):
    global _GUI_MUTEX
    if not IS_WINDOWS:
        return True
    k32 = ctypes.WinDLL("kernel32", use_last_error=True)
    k32.CreateMutexW.restype = ctypes.c_void_p
    k32.CreateMutexW.argtypes = [ctypes.c_void_p, ctypes.c_bool, ctypes.c_wchar_p]
    k32.CloseHandle.argtypes = [ctypes.c_void_p]
    end = time.time() + wait
    while True:
        handle = k32.CreateMutexW(None, False, "Local\\OrbitLauncherWindow")
        if ctypes.get_last_error() != 183:
            _GUI_MUTEX = handle
            return True
        k32.CloseHandle(handle)
        if time.time() >= end:
            return False
        time.sleep(0.4)


def start_tray(api):
    import importlib.util
    if not IS_WINDOWS or importlib.util.find_spec("pystray") is None or not has_pillow():
        return None
    import pystray
    from PIL import Image
    image = Image.open(app_icon_file()) if app_icon_file().exists() else Image.new("RGB", (64, 64), (157, 107, 255))

    def favorites():
        items = []
        for game in (load_settings().get("library") or [])[:8]:
            pid = str(game.get("pid"))
            items.append(pystray.MenuItem(game.get("name") or pid, lambda *_ , p=pid: api.play_game(p)))
        return items or [pystray.MenuItem("Add games in the Library tab", None, enabled=False)]

    def show(*_):
        api.show_window()

    def quit_app(*_):
        api._quitting = True
        icon.stop()
        api._window.destroy()

    menu = pystray.Menu(
        pystray.MenuItem("Open Orbit", show, default=True),
        pystray.Menu.SEPARATOR,
        pystray.MenuItem("Launch Roblox", lambda *_: api.launch("")),
        pystray.MenuItem("Rejoin last server", lambda *_: api.rejoin()),
        pystray.MenuItem("Library", pystray.Menu(favorites)),
        pystray.Menu.SEPARATOR,
        pystray.MenuItem("Quit Orbit", quit_app),
    )
    icon = pystray.Icon("OrbitLauncher", image, APP_NAME, menu)
    icon.run_detached()
    return icon


def resource_dir():
    return Path(getattr(sys, "_MEIPASS", Path(__file__).resolve().parent))


def build_info():
    return load_json(resource_dir() / "ui" / "build.json", {}) or {}


def update_repo():
    return (build_info().get("repo") or os.environ.get("ORBIT_UPDATE_REPO") or "").strip()


def parse_version(v):
    nums = [int(n) for n in re.findall(r"\d+", str(v))[:3]]
    return tuple(nums + [0] * (3 - len(nums)))


def is_frozen():
    return bool(getattr(sys, "frozen", False))


def check_app_update():
    repo = update_repo()
    if not repo:
        return {"error": "no_source"}
    try:
        rel = fetch_json(f"https://api.github.com/repos/{repo}/releases/latest", timeout=10)
    except Exception as e:
        log(f"Update check failed: {e}")
        return {"error": "Couldn't reach GitHub to check for updates."}
    version = str(rel.get("tag_name", "")).lstrip("vV")
    info = {"current": APP_VERSION, "version": version, "page": rel.get("html_url"),
            "notes": (rel.get("body") or "")[:2000], "available": parse_version(version) > parse_version(APP_VERSION)}
    assets = {a.get("name", "").lower(): a for a in rel.get("assets", [])}
    exe = assets.get("orbitlauncher.exe")
    sha = assets.get("orbitlauncher.exe.sha256")
    if exe:
        info.update(url=exe["browser_download_url"], size=exe.get("size", 0))
    if sha:
        info["sha_url"] = sha["browser_download_url"]
    info["manual"] = info["available"] and (not is_frozen() or not exe)
    return info


def download_file(url, dest, progress=None):
    req = urllib.request.Request(url, headers={"User-Agent": APP_ID + "/" + APP_VERSION})
    dest = Path(dest)
    dest.parent.mkdir(parents=True, exist_ok=True)
    part = dest.with_name(dest.name + ".part")
    with urllib.request.urlopen(req, timeout=30) as resp, open(part, "wb") as f:
        total = int(resp.headers.get("Content-Length") or 0)
        done = 0
        while True:
            chunk = resp.read(256 * 1024)
            if not chunk:
                break
            f.write(chunk)
            done += len(chunk)
            if progress and total:
                progress(done / total)
    os.replace(part, dest)
    return dest


def _sha256(path):
    import hashlib
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def download_app_update(info, progress=None):
    target = download_file(info["url"], UPDATE_DIR / "OrbitLauncher.exe", progress)
    if info.get("sha_url"):
        req = urllib.request.Request(info["sha_url"], headers={"User-Agent": APP_ID})
        with urllib.request.urlopen(req, timeout=15) as resp:
            expected = resp.read().decode("utf-8", "ignore").split()[0].strip().lower()
        if _sha256(target) != expected:
            target.unlink(missing_ok=True)
            raise OSError("The download was corrupted (checksum mismatch). Try again.")
    if target.stat().st_size < 1_000_000:
        target.unlink(missing_ok=True)
        raise OSError("The download looks incomplete. Try again.")
    save_json(UPDATE_DIR / "pending.json", {"version": info["version"]})
    log(f"Downloaded update {info['version']}")
    return target


def pending_update():
    pend = load_json(UPDATE_DIR / "pending.json", None)
    if pend and (UPDATE_DIR / "OrbitLauncher.exe").exists() and \
            parse_version(pend.get("version")) > parse_version(APP_VERSION):
        return pend["version"]
    return None


def swap_exe(new_exe, target_exe):
    target_exe, new_exe = Path(target_exe), Path(new_exe)
    old = target_exe.with_name(target_exe.stem + ".old.exe")
    try:
        old.unlink(missing_ok=True)
    except OSError:
        old = target_exe.with_name(f"{target_exe.stem}.old{int(time.time())}.exe")
    moved = False
    if target_exe.exists():
        os.replace(target_exe, old)
        moved = True
    try:
        shutil.copy2(new_exe, target_exe)
    except Exception:
        if moved:
            os.replace(old, target_exe)
        raise


def apply_pending_update(restart_args=(), restart=True):
    version = pending_update()
    if not version or not is_frozen():
        return False
    try:
        swap_exe(UPDATE_DIR / "OrbitLauncher.exe", sys.executable)
        (UPDATE_DIR / "OrbitLauncher.exe").unlink(missing_ok=True)
        (UPDATE_DIR / "pending.json").unlink(missing_ok=True)
        log(f"Updated to {version}")
        if restart:
            subprocess.Popen([sys.executable, *restart_args], env=child_env())
        return True
    except Exception as e:
        log(f"Applying update failed: {e}")
        return False


def cleanup_old_exes():
    if not is_frozen():
        return
    for old in Path(sys.executable).parent.glob(Path(sys.executable).stem + ".old*.exe"):
        try:
            old.unlink()
        except OSError:
            pass


def write_uninstall_entry(exe, version=APP_VERSION):
    if not IS_WINDOWS:
        return
    exe = Path(exe)
    with winreg.CreateKey(winreg.HKEY_CURRENT_USER, UNINSTALL_KEY) as k:
        for name, value in (("DisplayName", APP_NAME), ("DisplayVersion", version), ("Publisher", PUBLISHER),
                            ("DisplayIcon", f"{exe},0"), ("InstallLocation", str(exe.parent)),
                            ("UninstallString", f'"{exe}" {UNINSTALL_FLAG}')):
            winreg.SetValueEx(k, name, 0, winreg.REG_SZ, value)
        for name in ("NoModify", "NoRepair"):
            winreg.SetValueEx(k, name, 0, winreg.REG_DWORD, 1)
        try:
            winreg.SetValueEx(k, "EstimatedSize", 0, winreg.REG_DWORD, int(exe.stat().st_size / 1024))
        except OSError:
            pass


def installed_version():
    if not IS_WINDOWS:
        return None
    try:
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER, UNINSTALL_KEY) as k:
            return winreg.QueryValueEx(k, "DisplayVersion")[0] if INSTALLED_EXE.exists() else None
    except OSError:
        return None


def running_installed_copy():
    return is_frozen() and Path(sys.executable).resolve() == INSTALLED_EXE.resolve()


def startup_maintenance(settings):
    cleanup_old_exes()
    if not IS_WINDOWS or not is_frozen():
        return
    try:
        if running_installed_copy():
            write_uninstall_entry(sys.executable)
    except Exception as e:
        log(f"Startup maintenance: {e}")
    threading.Thread(target=prepare_fast_paths, args=(settings,), daemon=True).start()


def prepare_fast_paths(settings):
    try:
        ensure_helper()
    except Exception as e:
        log(f"Couldn't unpack the fast helper: {e}")
    try:
        if settings["registration"].get("registered") and should_claim_links(read_protocol_command(PROTOCOLS[0])):
            register_protocols(settings)
            log("Roblox links now go through the fast helper")
        if settings["session"].get("start_with_windows"):
            bg = load_json(BACKGROUND_FILE, {}) or {}
            with winreg.CreateKey(winreg.HKEY_CURRENT_USER, RUN_KEY) as k:
                winreg.SetValueEx(k, APP_NAME, 0, winreg.REG_SZ, " ".join(f'"{x}"' for x in fast_command(BACKGROUND_FLAG)[:-1]) + f" {BACKGROUND_FLAG}")
            if bg.get("version") != APP_VERSION or not pid_alive((bg.get("pids") or [0])[0]):
                for pid in bg.get("pids", []):
                    if pid not in (os.getpid(), os.getppid()):
                        kill_tree(pid)
                BACKGROUND_FILE.unlink(missing_ok=True)
                spawn_self(BACKGROUND_FLAG)
                log("Restarted the background helper on the new version")
    except Exception as e:
        log(f"Fast path setup: {e}")


def run_install(options, progress):
    if not is_frozen():
        raise OSError("Setup only works from the built OrbitSetup.exe.")
    warnings = []
    progress(.04, "Checking for the newest version...")
    source = Path(sys.executable)
    version = APP_VERSION
    info = check_app_update()
    if info.get("available") and info.get("url"):
        progress(.08, f"Downloading v{info['version']}...")
        source = download_app_update(info, lambda f: progress(.08 + f * .6, f"Downloading v{info['version']}... {int(f * 100)}%"))
        version = info["version"]
    progress(.72, "Installing...")
    INSTALL_DIR.mkdir(parents=True, exist_ok=True)
    swap_exe(source, INSTALLED_EXE)
    if source.parent == UPDATE_DIR:
        (UPDATE_DIR / "pending.json").unlink(missing_ok=True)
    if IS_WINDOWS:
        progress(.84, "Adding shortcuts...")
        for location in ["Programs"] + (["Desktop"] if options.get("desktop", True) else []):
            try:
                create_shortcut(location, APP_NAME, launch=False, exe=INSTALLED_EXE)
            except Exception as e:
                warnings.append(f"Couldn't add the {'Start menu' if location == 'Programs' else 'desktop'} shortcut")
                log(f"Shortcut ({location}) failed: {e}")
        progress(.93, "Registering with Windows...")
        try:
            write_uninstall_entry(INSTALLED_EXE, version)
            settings = load_settings()
            if settings["registration"].get("registered"):
                register_protocols(settings, exe=INSTALLED_EXE)
        except Exception as e:
            warnings.append("Couldn't register with Windows Settings > Apps")
            log(f"Registration failed: {e}")
        progress(.96, "Setting up the fast helper...")
        try:
            subprocess.run([str(INSTALLED_EXE), PREPARE_FLAG], timeout=120, env=child_env(),
                           creationflags=CREATE_NO_WINDOW)
        except Exception as e:
            log(f"Helper setup during install failed: {e}")
    progress(1, "Done")
    log(f"Installed {version} to {INSTALL_DIR}")
    return {"version": version, "path": str(INSTALLED_EXE), "warnings": warnings}


def run_uninstall():
    if not IS_WINDOWS:
        return
    u = ctypes.windll.user32
    if u.MessageBoxW(None, f"Uninstall {APP_NAME}?", APP_NAME, 0x4 | 0x20) != 6:
        return
    settings = load_settings()
    try:
        if is_registered():
            unregister_protocols(settings)
    except Exception as e:
        log(f"Uninstall: couldn't restore Roblox links: {e}")
    ps = ("foreach($f in 'Desktop','Programs'){$d=[Environment]::GetFolderPath($f);"
          f"foreach($n in '{APP_NAME}.lnk','{SHORTCUT_NAME}.lnk'){{Remove-Item -LiteralPath (Join-Path $d $n) "
          "-ErrorAction SilentlyContinue}}")
    subprocess.run([sys_tool("powershell"), "-NoProfile", "-Command", ps], creationflags=CREATE_NO_WINDOW)
    _delete_tree(winreg.HKEY_CURRENT_USER, UNINSTALL_KEY)
    if u.MessageBoxW(None, "Also delete your Orbit settings, mod profiles and play time?", APP_NAME, 0x4 | 0x20) == 6:
        shutil.rmtree(DATA_DIR, ignore_errors=True)
    if is_frozen() and Path(sys.executable).parent.resolve() == INSTALL_DIR.resolve():
        subprocess.Popen(f'"{sys_tool("cmd")}" /c ping 127.0.0.1 -n 3 > nul & rmdir /s /q "{INSTALL_DIR}"',
                         creationflags=CREATE_NO_WINDOW | 0x00000008)
    u.MessageBoxW(None, f"{APP_NAME} was uninstalled.", APP_NAME, 0x40)


def accent_pair(appearance):
    if appearance.get("accent") == "Custom":
        colors = appearance.get("custom_colors") or []
        if len(colors) == 2 and all(re.fullmatch(r"#[0-9a-fA-F]{6}", str(x)) for x in colors):
            return list(colors)
    return ACCENTS.get(appearance.get("accent"), ACCENTS["Void"])


def theme_colors(appearance):
    if appearance.get("mode") == "Light":
        c = dict(bg="#f3f0fb", panel="#ffffff", fg="#17122a", muted="#6a6386")
    else:
        c = dict(bg="#06040b", panel="#120e1f", fg="#f1edff", muted="#9c95b8")
    c["accent"] = accent_pair(appearance)[0]
    return c


def _no_activate(root):
    if not IS_WINDOWS:
        return
    try:
        u = ctypes.windll.user32
        u.GetParent.restype = ctypes.c_void_p
        u.GetParent.argtypes = [ctypes.c_void_p]
        u.GetWindowLongW.argtypes = [ctypes.c_void_p, ctypes.c_int]
        u.SetWindowLongW.argtypes = [ctypes.c_void_p, ctypes.c_int, ctypes.c_long]
        u.SetWindowPos.argtypes = [ctypes.c_void_p, ctypes.c_void_p, ctypes.c_int, ctypes.c_int,
                                   ctypes.c_int, ctypes.c_int, ctypes.c_uint]
        hwnd = u.GetParent(root.winfo_id()) or root.winfo_id()
        style = u.GetWindowLongW(hwnd, -20)
        u.SetWindowLongW(hwnd, -20, style | 0x08000000 | 0x00000080 | 0x00000008)
        u.SetWindowPos(hwnd, ctypes.c_void_p(-1), 0, 0, 0, 0, 0x0001 | 0x0002 | 0x0010 | 0x0040)
        return hwnd
    except Exception:
        return None


def show_toast(title, body, seconds=6.5):
    import tkinter as tk
    import tkinter.font as tkfont
    c = theme_colors(load_settings()["appearance"])
    accent2 = accent_pair(load_settings()["appearance"])[1]
    key = "#010203"
    root = tk.Tk()
    root.withdraw()
    root.overrideredirect(True)
    root.configure(bg=key)
    try:
        root.attributes("-topmost", True)
        root.attributes("-transparentcolor", key)
        root.attributes("-alpha", 0.0)
    except tk.TclError:
        pass
    f_title = tkfont.Font(family="Segoe UI Semibold", size=12)
    f_body = tkfont.Font(family="Segoe UI", size=10)
    f_tag = tkfont.Font(family="Segoe UI", size=8, weight="bold")
    title = title if len(title) <= 46 else title[:45] + "…"
    text_w = max(f_title.measure(title), f_body.measure("Server  " + body), f_tag.measure("ORBIT · SERVER LOCATION"))
    w, h, r = min(560, text_w + 104), 70, 22
    cv = tk.Canvas(root, width=w, height=h, bg=key, highlightthickness=0, bd=0)
    cv.pack()

    def rounded(x1, y1, x2, y2, rad, **kw):
        pts = [x1 + rad, y1, x2 - rad, y1, x2, y1, x2, y1 + rad, x2, y2 - rad, x2, y2, x2 - rad, y2,
               x1 + rad, y2, x1, y2, x1, y2 - rad, x1, y1 + rad, x1, y1]
        return cv.create_polygon(pts, smooth=True, splinesteps=24, **kw)

    rounded(1, 1, w - 1, h - 1, r, fill=c["accent"], outline="")
    rounded(2, 2, w - 2, h - 2, r - 1, fill=c["panel"], outline="")
    cx, cy = 37, h // 2
    cv.create_oval(cx - 20, cy - 20, cx + 20, cy + 20, fill=c["accent"], outline="")
    cv.create_oval(cx - 17, cy - 7, cx + 17, cy + 7, outline=accent2, width=3)
    cv.create_oval(cx - 9, cy - 9, cx + 9, cy + 9, fill="#05030a", outline="#f5f3ff", width=2)
    cv.create_arc(cx - 17, cy - 7, cx + 17, cy + 7, start=180, extent=180, style="arc", outline=accent2, width=3)
    tx = 72
    cv.create_text(tx, 17, text="ORBIT · SERVER LOCATION", anchor="w", font=f_tag, fill=c["accent"])
    cv.create_text(tx, 35, text=title, anchor="w", font=f_title, fill=c["fg"])
    cv.create_text(tx, 54, text="Server  ", anchor="w", font=f_body, fill=c["muted"])
    cv.create_text(tx + f_body.measure("Server  "), 54, text=body, anchor="w", font=f_body, fill=c["fg"])

    sw = root.winfo_screenwidth()
    x, y_end = (sw - w) // 2, 26
    state = {"y": -h - 10.0, "alpha": 0.0, "closing": False}
    root.geometry(f"{w}x{h}+{x}+{int(state['y'])}")
    root.deiconify()
    root.update_idletasks()
    _no_activate(root)

    def slide_in():
        if state["closing"]:
            return
        state["y"] += (y_end - state["y"]) * 0.22
        state["alpha"] = min(0.98, state["alpha"] + 0.1)
        root.geometry(f"{w}x{h}+{x}+{int(state['y'])}")
        try:
            root.attributes("-alpha", state["alpha"])
        except tk.TclError:
            pass
        if abs(state["y"] - y_end) > 0.5 or state["alpha"] < 0.98:
            root.after(15, slide_in)

    def slide_out(*_):
        state["closing"] = True
        state["y"] -= 6 + (state["y"] + h) * 0.12
        state["alpha"] = max(0.0, state["alpha"] - 0.08)
        try:
            root.geometry(f"{w}x{h}+{x}+{int(state['y'])}")
            root.attributes("-alpha", state["alpha"])
        except tk.TclError:
            pass
        if state["y"] <= -h or state["alpha"] <= 0:
            root.destroy()
            return
        root.after(15, slide_out)

    cv.bind("<Button-1>", slide_out)
    slide_in()
    root.after(int(seconds * 1000), slide_out)
    root.mainloop()


def roblox_in_front():
    if not IS_WINDOWS or os.environ.get("ORBIT_BADGE_ALWAYS"):
        return True
    try:
        u = ctypes.windll.user32
        u.GetForegroundWindow.restype = ctypes.c_void_p
        hwnd = u.GetForegroundWindow()
        buf = ctypes.create_unicode_buffer(64)
        u.GetWindowTextW.argtypes = [ctypes.c_void_p, ctypes.c_wchar_p, ctypes.c_int]
        u.GetWindowTextW(hwnd, buf, 64)
        return buf.value == "Roblox"
    except Exception:
        return True


def roblox_rect():
    if not IS_WINDOWS:
        return None
    try:
        u = ctypes.windll.user32
        u.FindWindowW.restype = ctypes.c_void_p
        u.FindWindowW.argtypes = [ctypes.c_wchar_p, ctypes.c_wchar_p]
        hwnd = u.FindWindowW(None, "Roblox")
        if not hwnd or u.IsIconic(ctypes.c_void_p(hwnd)):
            return None

        class RECT(ctypes.Structure):
            _fields_ = [("l", ctypes.c_long), ("t", ctypes.c_long), ("r", ctypes.c_long), ("b", ctypes.c_long)]
        rc = RECT()
        u.GetWindowRect(ctypes.c_void_p(hwnd), ctypes.byref(rc))
        if rc.r - rc.l < 200:
            return None
        return rc.l, rc.t, rc.r, rc.b
    except Exception:
        return None


def roblox_client_center():
    if not IS_WINDOWS:
        return None
    try:
        u = ctypes.windll.user32
        u.FindWindowW.restype = ctypes.c_void_p
        u.FindWindowW.argtypes = [ctypes.c_wchar_p, ctypes.c_wchar_p]
        hwnd = u.FindWindowW(None, "Roblox")
        if not hwnd or u.IsIconic(ctypes.c_void_p(hwnd)):
            return None

        class RECT(ctypes.Structure):
            _fields_ = [("l", ctypes.c_long), ("t", ctypes.c_long), ("r", ctypes.c_long), ("b", ctypes.c_long)]

        class POINT(ctypes.Structure):
            _fields_ = [("x", ctypes.c_long), ("y", ctypes.c_long)]
        rc, pt = RECT(), POINT(0, 0)
        u.GetClientRect(ctypes.c_void_p(hwnd), ctypes.byref(rc))
        u.ClientToScreen(ctypes.c_void_p(hwnd), ctypes.byref(pt))
        if rc.r < 200:
            return None
        return pt.x + rc.r // 2, pt.y + rc.b // 2
    except Exception:
        return None


def cursor_hidden():
    if not IS_WINDOWS:
        return False
    try:
        class POINT(ctypes.Structure):
            _fields_ = [("x", ctypes.c_long), ("y", ctypes.c_long)]

        class CURSORINFO(ctypes.Structure):
            _fields_ = [("cbSize", ctypes.c_uint), ("flags", ctypes.c_uint), ("hCursor", ctypes.c_void_p), ("pt", POINT)]
        ci = CURSORINFO()
        ci.cbSize = ctypes.sizeof(CURSORINFO)
        if not ctypes.windll.user32.GetCursorInfo(ctypes.byref(ci)):
            return False
        return not (ci.flags & 1) or not ci.hCursor
    except Exception:
        return False


def overlay_crosshair_for(settings, place_id=None):
    ov = settings.get("overlay") or {}
    cid = (settings.get("game_crosshairs") or {}).get(str(place_id)) if place_id else None
    return cid or ov.get("crosshair") or ""


def show_crosshair_window():
    import tkinter as tk
    settings = load_settings()
    ov = settings.get("overlay") or {}
    mode = ov.get("crosshair_mode") or "locked"
    size = max(50, min(200, int(ov.get("crosshair_size") or 100)))
    key = "#010203"
    root = tk.Tk()
    root.withdraw()
    root.overrideredirect(True)
    root.configure(bg=key)
    try:
        root.attributes("-topmost", True)
        root.attributes("-transparentcolor", key)
    except tk.TclError:
        pass
    side = int(64 * size / 100)
    cv = tk.Canvas(root, width=side, height=side, bg=key, highlightthickness=0, bd=0)
    cv.pack()
    state = {"cid": None, "img": None, "item": None, "shown": False, "xy": None, "place": None, "hwnd": None, "checked": 0}

    def load_image(cid):
        src = crosshair_source(cid)
        if not src:
            return None
        img = tk.PhotoImage(data=base64.b64encode(src.read_bytes()).decode())
        if size != 100:
            factor = size / 100
            if factor >= 1:
                img = img.zoom(round(factor))
            else:
                img = img.subsample(max(1, round(1 / factor)))
            if img.width() != side:
                cv.configure(width=img.width(), height=img.height())
        return img

    def refresh_choice():
        cur = load_json(CURRENT_FILE, None) or {}
        place = cur.get("place_id")
        cid = overlay_crosshair_for(load_settings(), place)
        if cid != state["cid"]:
            state["cid"] = cid
            state["img"] = load_image(cid) if cid else None
            cv.delete("all")
            if state["img"] is not None:
                cv.create_image(int(cv.cget("width")) // 2, int(cv.cget("height")) // 2, image=state["img"])

    root.geometry(f"{side}x{side}+-200+-200")
    root.deiconify()
    root.update_idletasks()
    hwnd = _no_activate(root)
    state["hwnd"] = hwnd
    if hwnd and IS_WINDOWS:
        try:
            u = ctypes.windll.user32
            style = u.GetWindowLongW(hwnd, -20)
            u.SetWindowLongW(hwnd, -20, style | 0x00000020 | 0x00080000)
        except Exception:
            pass
    overlay_show(hwnd, False)
    log(f"Crosshair overlay ready ({mode}, {size}%)")

    def tick():
        try:
            now = time.time()
            if now - state["checked"] > 2:
                state["checked"] = now
                refresh_choice()
            center = roblox_client_center() if roblox_in_front() else None
            want = bool(center and state["img"] is not None and (mode == "always" or cursor_hidden()))
            if want:
                w, h = int(cv.cget("width")), int(cv.cget("height"))
                xy = (center[0] - w // 2, center[1] - h // 2)
                if xy != state["xy"] or not state["shown"]:
                    state["xy"] = xy
                    if IS_WINDOWS and hwnd:
                        u = ctypes.windll.user32
                        u.SetWindowPos.argtypes = [ctypes.c_void_p, ctypes.c_void_p, ctypes.c_int, ctypes.c_int,
                                                   ctypes.c_int, ctypes.c_int, ctypes.c_uint]
                        u.SetWindowPos(ctypes.c_void_p(hwnd), ctypes.c_void_p(-1), xy[0], xy[1], 0, 0, 0x0001 | 0x0010)
                    else:
                        root.geometry(f"+{xy[0]}+{xy[1]}")
                if not state["shown"]:
                    overlay_show(hwnd, True)
                    state["shown"] = True
            elif state["shown"]:
                overlay_show(hwnd, False)
                state["shown"] = False
        except tk.TclError:
            return
        except Exception:
            if not state.get("logged"):
                state["logged"] = True
                log("Crosshair overlay error:\n" + traceback.format_exc())
        root.after(33 if state["shown"] else 120, tick)

    tick()
    root.mainloop()


CROSS_FLAG = "--crosshair"
CROSS_FILE = DATA_DIR / "crosshair_overlay.json"


def start_crosshair_overlay():
    close_crosshair_overlay()
    proc = spawn_self(TOAST_FLAG, "crosshair", "", CROSS_FLAG)
    if proc:
        save_json(CROSS_FILE, {"pid": proc.pid})


def close_crosshair_overlay():
    data = load_json(CROSS_FILE, {}) or {}
    if data.get("pid") and IS_WINDOWS:
        kill_tree(data["pid"])
    CROSS_FILE.unlink(missing_ok=True)


def overlay_show(hwnd, on):
    if not hwnd or not IS_WINDOWS:
        return
    try:
        u = ctypes.windll.user32
        u.ShowWindow.argtypes = [ctypes.c_void_p, ctypes.c_int]
        u.ShowWindow(ctypes.c_void_p(hwnd), 4 if on else 0)
        if on:
            u.SetWindowPos.argtypes = [ctypes.c_void_p, ctypes.c_void_p, ctypes.c_int, ctypes.c_int,
                                       ctypes.c_int, ctypes.c_int, ctypes.c_uint]
            u.SetWindowPos(ctypes.c_void_p(hwnd), ctypes.c_void_p(-1), 0, 0, 0, 0, 0x0001 | 0x0002 | 0x0010)
    except Exception:
        pass


def ping_ms(ip):
    if not ip or not IS_WINDOWS:
        return None
    try:
        out = subprocess.run([sys_tool("ping"), "-n", "1", "-w", "1500", str(ip)], capture_output=True, text=True,
                             timeout=5, creationflags=CREATE_NO_WINDOW).stdout
    except Exception:
        return None
    m = re.search(r"[=<]\s?(\d+)\s?ms", out, re.I)
    return int(m.group(1)) if m else None


def show_badge_window(title, body, ip=None, joined=None):
    import tkinter as tk
    import tkinter.font as tkfont
    settings = load_settings()
    appearance, sess = settings["appearance"], settings["session"]
    pos = sess.get("badge_pos") or "Top right"
    small = (sess.get("badge_size") or "Small") == "Small"
    show_ping = sess.get("badge_ping", True) and bool(ip)
    show_timer = sess.get("badge_timer", True) and bool(joined)
    joined = float(joined) if joined else None
    c = theme_colors(appearance)
    accent2 = accent_pair(appearance)[1]
    key = "#010203"
    root = tk.Tk()
    root.withdraw()
    root.overrideredirect(True)
    root.configure(bg=key)
    try:
        root.attributes("-topmost", True)
        root.attributes("-transparentcolor", key)
        root.attributes("-alpha", 0.0)
    except tk.TclError:
        pass
    f_name = tkfont.Font(family="Segoe UI Semibold", size=9 if small else 10)
    f_loc = tkfont.Font(family="Segoe UI", size=9 if small else 10)
    f_num = tkfont.Font(family="Segoe UI Semibold", size=9 if small else 10)
    h = 24 if small else 30
    dot = 7 if small else 9
    sep = "  ·  "
    x = 12 + dot * 2 + 6
    layout = []
    if not small:
        name = title if len(title) <= 28 else title[:27] + "…"
        layout += [("name", name, f_name, c["fg"]), ("sep", sep, f_loc, c["muted"])]
    layout.append(("loc", body, f_loc, c["fg"]))
    if show_ping:
        layout += [("sep", sep, f_loc, c["muted"]), ("ping", "··· ms", f_num, c["muted"], "999 ms")]
    if show_timer:
        layout += [("sep", sep, f_loc, c["muted"]), ("timer", "0:00", f_num, c["muted"], "0:00:00")]
    if sess.get("badge_fps", True) and (settings.get("fps") or {}).get("enabled"):
        layout += [("sep", sep, f_loc, c["muted"]), ("fps", "··· fps", f_num, c["muted"], "000 fps")]
    w = x + sum(f.measure(item[4] if len(item) > 4 else item[1]) for item in layout for f in [item[2]]) + 12
    cv = tk.Canvas(root, width=w, height=h, bg=key, highlightthickness=0, bd=0)
    cv.pack()
    r = h // 2
    pts = lambda x1, y1, x2, y2, rr: [x1 + rr, y1, x2 - rr, y1, x2, y1, x2, y1 + rr, x2, y2 - rr, x2, y2, x2 - rr, y2,
                                      x1 + rr, y2, x1, y2, x1, y2 - rr, x1, y1 + rr, x1, y1]
    border = cv.create_polygon(pts(0, 0, w - 1, h - 1, r), smooth=True, splinesteps=20, fill=c["accent"], outline="")
    cv.create_polygon(pts(1, 1, w - 2, h - 2, r - 1), smooth=True, splinesteps=20, fill=c["panel"], outline="")
    cx, cy = 12 + dot, h // 2
    cv.create_oval(cx - dot, cy - dot, cx + dot, cy + dot, fill=c["accent"], outline="")
    cv.create_oval(cx - dot // 2, cy - dot // 2, cx + dot // 2, cy + dot // 2, fill="#05030a", outline="#f5f3ff")
    cv.create_line(cx - dot - 2, cy + 2, cx + dot + 2, cy - 2, fill=accent2, width=2)
    items = {}
    for item in layout:
        kind, text, font, color = item[:4]
        items[kind] = cv.create_text(x, cy, text=text, anchor="w", font=font, fill=color)
        x += font.measure(item[4] if len(item) > 4 else text)
    state = {"alpha": 0.0, "xy": None, "hwnd": None, "ping": None, "pings": [], "flash": 0.0}
    lag_alerts = sess.get("lag_alerts", True)
    peak = 0.86

    def target_xy():
        rect = roblox_rect() or (0, 0, root.winfo_screenwidth(), root.winfo_screenheight())
        L, T, R, B = rect
        margin, top = 12, 66
        if pos == "Top left":
            xy = (L + margin, T + top)
        elif pos == "Bottom left":
            xy = (L + margin, B - h - margin - 8)
        elif pos == "Bottom right":
            xy = (R - w - margin, B - h - margin - 8)
        elif pos == "Top center":
            xy = (L + (R - L - w) // 2, T + 8)
        else:
            xy = (R - w - margin, T + top)
        return xy, rect

    def place():
        xy, rect = target_xy()
        if xy == state["xy"]:
            return
        state["xy"] = xy
        moved = False
        if state["hwnd"] and IS_WINDOWS:
            try:
                u = ctypes.windll.user32
                u.SetWindowPos.argtypes = [ctypes.c_void_p, ctypes.c_void_p, ctypes.c_int, ctypes.c_int,
                                           ctypes.c_int, ctypes.c_int, ctypes.c_uint]
                moved = bool(u.SetWindowPos(state["hwnd"], ctypes.c_void_p(-1), xy[0], xy[1], 0, 0, 0x0001 | 0x0010))
            except Exception:
                moved = False
        if not moved:
            root.geometry(f"{w}x{h}+{xy[0]}+{xy[1]}")

    first_xy, first_rect = target_xy()
    state["xy"] = first_xy
    root.geometry(f"{w}x{h}+{first_xy[0]}+{first_xy[1]}")
    root.deiconify()
    root.update_idletasks()
    hwnd = _no_activate(root)
    state["hwnd"] = hwnd
    if hwnd and IS_WINDOWS:
        try:
            u = ctypes.windll.user32
            style = u.GetWindowLongW(hwnd, -20)
            u.SetWindowLongW(hwnd, -20, style | 0x00000020 | 0x00080000)
        except Exception:
            pass
        state["xy"] = None
        place()
    log(f"Badge placed at {first_xy} ({w}x{h}, {pos}, anchored to {'Roblox' if roblox_rect() else 'screen'} {first_rect})")

    if show_ping:
        def pinger():
            while True:
                p = ping_ms(ip)
                state["ping"] = p
                if p is not None:
                    hist = state["pings"][-12:]
                    if lag_alerts and len(hist) >= 4:
                        base = sorted(hist)[len(hist) // 2]
                        if p > max(150, base * 2.2, base + 80):
                            state["flash"] = time.time() + 4
                            log(f"Lag spike: {p} ms (usual {base} ms)")
                    state["pings"] = hist + [p]
                time.sleep(4)
        threading.Thread(target=pinger, daemon=True).start()

    def refresh_numbers():
        flashing = time.time() < state["flash"]
        if flashing != state.get("flashing"):
            state["flashing"] = flashing
            cv.itemconfigure(border, fill="#fb7185" if flashing else c["accent"])
        if "fps" in items:
            live = load_json(FPS_LIVE_FILE, None) or {}
            f = live.get("fps") if time.time() - live.get("at", 0) < 5 else None
            cv.itemconfigure(items["fps"], text="··· fps" if f is None else f"{f} fps")
        if "ping" in items:
            p = state["ping"]
            color = c["muted"] if p is None else "#4ade80" if p < 80 else "#fbbf24" if p < 150 else "#fb7185"
            cv.itemconfigure(items["ping"], text="··· ms" if p is None else f"{p} ms", fill=color)
        if "timer" in items:
            sec = max(0, int(time.time() - joined))
            hh, mm, ss = sec // 3600, sec % 3600 // 60, sec % 60
            cv.itemconfigure(items["timer"], text=f"{hh}:{mm:02d}:{ss:02d}" if hh else f"{mm}:{ss:02d}")

    state["shown"] = True

    def tick():
        try:
            visible = roblox_in_front() and not BADGE_HIDDEN.exists()
            if visible and not state["shown"]:
                overlay_show(state["hwnd"], True)
                state["shown"] = True
                state["xy"] = None
            target = peak if visible else 0.0
            state["alpha"] += (target - state["alpha"]) * 0.35
            if abs(state["alpha"] - target) < 0.02:
                state["alpha"] = target
            if state["shown"]:
                place()
                refresh_numbers()
                root.attributes("-alpha", state["alpha"])
            if not visible and state["alpha"] == 0.0 and state["shown"]:
                overlay_show(state["hwnd"], False)
                state["shown"] = False
        except tk.TclError:
            return
        except Exception:
            if not state.get("logged"):
                state["logged"] = True
                log("Badge error:\n" + traceback.format_exc())
        root.after(250 if state["alpha"] in (0.0, peak) else 30, tick)

    tick()
    root.mainloop()


def ui_file():
    base = Path(getattr(sys, "_MEIPASS", Path(__file__).resolve().parent))
    return base / "ui" / "index.html"


def app_icon_file():
    base = Path(getattr(sys, "_MEIPASS", Path(__file__).resolve().parent))
    return base / "ui" / "orbit.ico"


def _clipboard_put(fmt, data):
    u, k = ctypes.windll.user32, ctypes.windll.kernel32
    k.GlobalAlloc.restype = ctypes.c_void_p
    k.GlobalAlloc.argtypes = [ctypes.c_uint, ctypes.c_size_t]
    k.GlobalLock.restype = ctypes.c_void_p
    k.GlobalLock.argtypes = [ctypes.c_void_p]
    k.GlobalUnlock.argtypes = [ctypes.c_void_p]
    u.SetClipboardData.argtypes = [ctypes.c_uint, ctypes.c_void_p]
    u.SetClipboardData.restype = ctypes.c_void_p
    for _ in range(10):
        if u.OpenClipboard(None):
            break
        time.sleep(0.05)
    else:
        return False
    try:
        u.EmptyClipboard()
        h = k.GlobalAlloc(0x0002, len(data))
        ptr = k.GlobalLock(h)
        ctypes.memmove(ptr, data, len(data))
        k.GlobalUnlock(h)
        return bool(u.SetClipboardData(fmt, h))
    finally:
        u.CloseClipboard()


def copy_to_clipboard(text):
    if IS_WINDOWS:
        try:
            if _clipboard_put(13, (str(text) + "\0").encode("utf-16-le")):
                return
        except Exception:
            pass
        subprocess.run([sys_tool("clip")], input=text.encode("utf-16-le"), creationflags=CREATE_NO_WINDOW)


def open_path(path):
    path = Path(path)
    if IS_WINDOWS:
        os.startfile(str(path))
    else:
        webbrowser.open(path.as_uri())


class Api:

    def __init__(self, mode="app"):
        ensure_dirs()
        self._settings = load_settings()
        if mode == "app":
            try:
                enforce_premium(self._settings)
            except Exception as e:
                log(f"Premium check failed: {e}")
        self._window = None
        self._mode = mode
        self._tray = None
        self._mini = None
        self._mini_api = None
        self._quitting = False
        self._tray_hint = False
        self._ready = threading.Event()
        self._ui_errors = []

    def ui_ready(self, mode=""):
        log(f"Window ready ({mode or self._mode}, v{APP_VERSION})")
        self._ready.set()
        return True

    def ui_error(self, message):
        text = str(message)[:3000]
        self._ui_errors.append(text[:600])
        log("Window error: " + text)
        return True

    def _js(self, code):
        try:
            self._window.evaluate_js(code)
        except Exception:
            pass

    @staticmethod
    def _err(e):
        log("UI action failed:\n" + traceback.format_exc())
        return {"error": str(e) or e.__class__.__name__}

    def get_state(self):
        s = self._settings
        players = player_dirs()
        return {
            "version": APP_VERSION,
            "is_windows": IS_WINDOWS,
            "settings": json.loads(json.dumps(s)),
            "default_presets": DEFAULT_PRESETS,
            "install": players[0].name if players else None,
            "registered": is_registered(),
            "last_server": load_json(LAST_SERVER_FILE, None),
            "mod_profiles": list_mod_profiles(),
            "playtime": load_json(PLAYTIME_FILE, {}),
            "icon_set": ICON_FILE.exists(),
            "allowlist": sorted(ALLOWLIST),
            "accents": ACCENTS,
            "quick_presets": QUICK_PRESETS,
            "regions": list(REGIONS),
            "owner": is_owner(),
            "premium": premium_status(self._settings, fetch=False),
            "game_updated": game_updated_times(self._settings),
            "packs_ready": (resource_dir() / "ui" / "packs").is_dir(),
            "credits": [{"role": r, "handle": h, "roblox_id": uid} for r, h, uid in CREDITS],
            "ext_path": str(EXTENSIONS_DIR / EXTENSION_NAME),
            "mode": self._mode,
            "update_source": update_repo(),
            "pending_update": pending_update(),
            "frozen": is_frozen(),
            "setup": {"installed_version": installed_version(), "path": str(INSTALL_DIR)},
            "has_pillow": has_pillow(),
            "tray": self._tray is not None,
            "screens_dirs": [str(d) for d in screenshot_dirs()],
        }

    def check_version(self):
        latest = latest_roblox_version()
        players = player_dirs()
        return {"latest": latest, "up_to_date": bool(latest and players and players[0].name == latest)}

    def save_settings(self, new):
        try:
            merged = _merge(DEFAULT_SETTINGS, new if isinstance(new, dict) else {})
            merged["registration"] = self._settings["registration"]
            merged["premium_key"] = self._settings.get("premium_key", "")
            if not has_premium(merged):
                perf = merged.setdefault("performance", {})
                perf.update(PERF_PREMIUM)
                perf["boost"] = bool(self._settings["performance"].get("boost"))
                for k in ("boost_backup", "win_backup", "gpu_applied"):
                    if k in self._settings["performance"]:
                        perf[k] = self._settings["performance"][k]
            self._settings = merged
            save_settings(merged)
            return True
        except Exception as e:
            return self._err(e)

    def launch(self, uri=""):
        try:
            if not player_dirs():
                return {"error": "Roblox isn't installed yet. Get it from roblox.com/download."}
            if IS_WINDOWS and is_frozen() and not helper_ready():
                ensure_helper()
            spawn_self(LAUNCH_FLAG, uri or "")
            return True
        except Exception as e:
            return self._err(e)

    def rejoin(self):
        last = load_json(LAST_SERVER_FILE, {}) or {}
        if not last.get("place_id"):
            return {"error": "No server to rejoin yet."}
        return self.launch(rejoin_uri(last["place_id"], last.get("job_id")))

    def apply_now(self):
        try:
            dirs = apply_all(self._settings)
            return dirs[0].name if dirs else None
        except Exception as e:
            return self._err(e)

    def toggle_registration(self):
        if not IS_WINDOWS:
            return {"error": "This only works on Windows."}
        try:
            if is_registered():
                unregister_protocols(self._settings)
            else:
                register_protocols(self._settings)
            return {"registered": is_registered()}
        except Exception as e:
            return self._err(e)

    def lookup_game(self, text):
        pid = parse_game_id(text)
        if not pid:
            return {"error": "That doesn't look like a Roblox game link or place ID."}
        info = game_info(pid)
        return {"pid": pid, "name": info["name"]}

    def game_icons(self, place_ids):
        from concurrent.futures import ThreadPoolExecutor
        ids = [str(p) for p in (place_ids or [])][:40]
        with ThreadPoolExecutor(6) as pool:
            icons = list(pool.map(lambda p: game_info(p).get("icon"), ids))
        return {pid: url for pid, url in zip(ids, icons) if url}

    def mods_list(self, name):
        return list_mods(PROFILES_DIR / name)

    def mod_profile_create(self, name):
        clean = re.sub(r'[<>:"/\\|?*]', "", name or "").strip().strip(".")
        if not clean:
            return {"error": "Pick a name with normal letters."}
        (PROFILES_DIR / clean).mkdir(parents=True, exist_ok=True)
        return {"name": clean, "profiles": list_mod_profiles()}

    def mod_profile_delete(self, name):
        if name and name != "Default":
            shutil.rmtree(PROFILES_DIR / name, ignore_errors=True)
        return {"profiles": list_mod_profiles()}

    def open_mods(self, name):
        folder = PROFILES_DIR / (name or "Default")
        folder.mkdir(parents=True, exist_ok=True)
        open_path(folder)

    def open_roblox_folder(self):
        players = player_dirs()
        if players:
            open_path(players[0])

    def open_log(self):
        if LOG_FILE.exists():
            open_path(LOG_FILE)

    def open_url(self, url):
        if str(url).startswith("https://"):
            webbrowser.open(url)

    def reset_playtime(self):
        try:
            PLAYTIME_FILE.unlink()
        except OSError:
            pass
        return True

    def choose_icon(self):
        try:
            import webview
            dialog = getattr(getattr(webview, "FileDialog", None), "OPEN", None) or webview.OPEN_DIALOG
            picked = self._window.create_file_dialog(dialog, file_types=("Icon files (*.ico)",))
            if not picked:
                return False
            path = picked[0] if isinstance(picked, (list, tuple)) else picked
            shutil.copy2(path, ICON_FILE)
            return True
        except Exception as e:
            return self._err(e)

    def remove_icon(self):
        try:
            ICON_FILE.unlink()
        except OSError:
            pass
        return True

    def make_shortcut(self, kind, location):
        if not IS_WINDOWS:
            return {"error": "Shortcuts only work on Windows."}
        try:
            if kind == "orbit":
                return {"path": create_shortcut(location, APP_NAME, launch=False)}
            return {"path": create_shortcut(location, SHORTCUT_NAME, launch=True)}
        except Exception as e:
            return self._err(e)

    def install_extension(self):
        try:
            return {"path": str(install_extension())}
        except Exception as e:
            return self._err(e)

    def open_browser_extensions(self, browser):
        if browser in ("chrome", "msedge"):
            open_browser_extensions(browser)

    def copy_text(self, text):
        copy_to_clipboard(str(text))
        return True

    def check_update(self):
        return check_app_update()

    def download_update(self):
        info = check_app_update()
        if info.get("error"):
            return info
        if not info.get("available"):
            return {"error": "You're already on the newest version."}
        if info.get("manual"):
            return {"error": "Automatic updates only work in the installed app.", "page": info.get("page")}
        try:
            last = [-1]

            def progress(f):
                pct = int(f * 100)
                if pct != last[0]:
                    last[0] = pct
                    self._js(f"window.updateProgress && updateProgress({pct})")
            download_app_update(info, progress)
            return {"version": info["version"]}
        except Exception as e:
            return self._err(e)

    def restart_to_update(self):
        if apply_pending_update(("--after-update",)):
            self._quitting = True
            if self._tray is not None:
                try:
                    self._tray.stop()
                except Exception:
                    pass
            self._window.destroy()
            return True
        return {"error": "No downloaded update to install."}

    def run_setup(self, options):
        try:
            def progress(f, text):
                self._js(f"window.setupProgress && setupProgress({f:.3f}, {json.dumps(text)})")
            return run_install(options or {}, progress)
        except Exception as e:
            return self._err(e)

    def finish_setup(self, launch):
        if launch and INSTALLED_EXE.exists():
            subprocess.Popen([str(INSTALLED_EXE)], env=child_env())
        self._window.destroy()

    def live_state(self):
        current = load_json(CURRENT_FILE, None)
        if current and not roblox_running():
            CURRENT_FILE.unlink(missing_ok=True)
            current = None
        return {"current": current, "playtime": load_json(PLAYTIME_FILE, {}), "last_server": load_json(LAST_SERVER_FILE, None),
                "registered": is_registered(), "install": (player_dirs()[:1] or [None])[0] and player_dirs()[0].name}

    def play_game(self, pid, smart=None):
        if not str(pid).isdigit():
            return {"error": "Unknown game."}
        if smart if smart is not None else self._settings.get("smart_join"):
            try:
                sv, _ = pick_server(pid)
                if sv:
                    log(f"Smart join picked a {sv['playing']}/{sv['max']} server at {sv['ping']} ms")
                    r = self.launch(rejoin_uri(pid, sv["id"]))
                    return {"smart": {"playing": sv["playing"], "max": sv["max"], "ping": sv["ping"]}} \
                        if r is True or (isinstance(r, dict) and not r.get("error")) else r
            except Exception as e:
                log(f"Smart join failed, joining normally: {e}")
        return self.launch(rejoin_uri(pid))

    def join_server(self, pid, job):
        if not str(pid).isdigit() or not re.fullmatch(r"[0-9a-fA-F-]{36}", str(job or "")):
            return {"error": "That server link looks wrong."}
        return self.launch(rejoin_uri(pid, job))

    def games_info(self, pids):
        from concurrent.futures import ThreadPoolExecutor
        ids = [str(p) for p in (pids or []) if str(p).isdigit()][:60]
        with ThreadPoolExecutor(6) as pool:
            infos = list(pool.map(game_info, ids))
        return {pid: {"name": i["name"], "icon": i.get("icon"), "thumb": i.get("thumb"), "creator": i.get("creator")}
                for pid, i in zip(ids, infos)}

    def servers(self, text):
        pid = parse_game_id(str(text))
        if not pid:
            return {"error": "Paste a game link (roblox.com/games/...) or a place ID."}
        info = game_info(pid)
        servers, note = list_servers(pid)
        return {"pid": pid, "name": info["name"], "thumb": info.get("thumb") or info.get("icon"),
                "servers": servers, "note": note}

    def recent_servers(self, limit=10):
        seen, out = set(), []
        for x in reversed(_sessions()):
            if x.get("job_id") and x["job_id"] not in seen:
                seen.add(x["job_id"])
                out.append(x)
            if len(out) >= limit:
                break
        return out

    def sessions(self, offset=0, count=40):
        data = list(reversed(_sessions()))
        return {"items": data[offset:offset + count], "total": len(data)}

    def achievements(self):
        return achievements_state()

    def weekly_recap(self):
        return weekly_recap()

    def export_recap(self):
        recap = weekly_recap()
        if recap.get("empty"):
            return {"error": "Play something this week first."}
        if not has_pillow():
            return {"error": "Saving the recap image needs the installed app (or 'pip install pillow')."}
        try:
            dest = pictures_dir() / "Orbit" / f"Orbit-recap-{time.strftime('%Y-%m-%d')}.png"
            render_recap_png(recap, self._settings, dest)
            open_path(dest)
            return {"path": str(dest)}
        except Exception as e:
            return self._err(e)

    def screenshots(self, offset=0, count=24, game=None):
        files = list_screenshots(game or None)
        roots = {d.resolve() for d in screenshot_dirs()}
        items = []
        for f in files[offset:offset + count]:
            try:
                items.append({"path": str(f), "name": f.name, "time": int(f.stat().st_mtime),
                              "thumb": data_url(f, max_side=480),
                              "game": None if f.parent.resolve() in roots else f.parent.name})
            except Exception:
                continue
        return {"items": items, "total": len(files), "games": screenshot_games() if not offset else None}

    def screenshot_full(self, path):
        if not _is_screenshot(path):
            return None
        return data_url(path, max_side=1920 if has_pillow() else None, quality=90)

    def open_screenshot(self, path):
        if _is_screenshot(path):
            open_path(path)

    def show_in_folder(self, path):
        if _is_screenshot(path) and IS_WINDOWS:
            subprocess.Popen([sys_tool("explorer"), "/select,", str(Path(path))], env=child_env())

    def open_screenshots_folder(self):
        dirs = screenshot_dirs()
        if dirs:
            open_path(dirs[0])

    def copy_image(self, path):
        if not _is_screenshot(path) or not IS_WINDOWS:
            return {"error": "Can't copy that file."}
        p = str(Path(path)).replace("'", "''")
        subprocess.run([sys_tool("powershell"), "-NoProfile", "-STA", "-Command",
                        "Add-Type -AssemblyName System.Windows.Forms,System.Drawing;"
                        f"[System.Windows.Forms.Clipboard]::SetImage([System.Drawing.Image]::FromFile('{p}'))"],
                       capture_output=True, creationflags=CREATE_NO_WINDOW)
        return True

    def whats_new(self):
        seen = self._settings.get("last_seen_version") or ""
        if seen == APP_VERSION:
            return None
        return {"version": APP_VERSION, "notes": changelog_section(APP_VERSION), "first": not seen}

    def mark_seen(self):
        self._settings["last_seen_version"] = APP_VERSION
        save_settings(self._settings)
        return True

    def _dialog(self, kind, **kw):
        import webview
        fd = getattr(webview, "FileDialog", None)
        const = getattr(fd, kind, None) if fd else None
        if const is None:
            const = getattr(webview, f"{kind}_DIALOG")
        return self._window.create_file_dialog(const, **kw)

    def choose_app(self):
        try:
            picked = self._dialog("OPEN", file_types=("Programs (*.exe)",))
            if not picked:
                return None
            path = Path(picked[0] if isinstance(picked, (list, tuple)) else picked)
            return {"path": str(path), "name": path.stem}
        except Exception as e:
            return self._err(e)

    def choose_background(self):
        try:
            picked = self._dialog("OPEN", file_types=("Images (*.png;*.jpg;*.jpeg;*.webp;*.gif)",))
            if not picked:
                return None
            src = Path(picked[0] if isinstance(picked, (list, tuple)) else picked)
            for old in DATA_DIR.glob("background.*"):
                old.unlink(missing_ok=True)
            dest = DATA_DIR / ("background" + src.suffix.lower())
            if has_pillow() and src.suffix.lower() != ".gif":
                from PIL import Image
                with Image.open(src) as im:
                    im = im.convert("RGB")
                    im.thumbnail((2200, 2200))
                    dest = DATA_DIR / "background.jpg"
                    im.save(dest, "JPEG", quality=88)
            else:
                shutil.copy2(src, dest)
            self._settings["appearance"]["bg_file"] = dest.name
            self._settings["appearance"]["background"] = "Image"
            save_settings(self._settings)
            return {"file": dest.name, "data": data_url(dest)}
        except Exception as e:
            return self._err(e)

    def background_data(self):
        f = background_file(self._settings)
        return data_url(f) if f else None

    def export_backup(self):
        try:
            name = f"Orbit-backup-{time.strftime('%Y-%m-%d')}.orbitbackup"
            picked = self._dialog("SAVE", save_filename=name, file_types=("Orbit backup (*.orbitbackup)",))
            if not picked:
                return None
            dest = Path(picked[0] if isinstance(picked, (list, tuple)) else picked)
            save_settings(self._settings)
            export_backup(dest, self._settings)
            return {"path": str(dest)}
        except Exception as e:
            return self._err(e)

    def import_backup(self):
        try:
            picked = self._dialog("OPEN", file_types=("Orbit backup (*.orbitbackup;*.zip)",))
            if not picked:
                return None
            import_backup(Path(picked[0] if isinstance(picked, (list, tuple)) else picked))
            self._settings = load_settings()
            return {"ok": True}
        except Exception as e:
            return self._err(e)

    def reload_ui(self):
        self._window.load_html(ui_file().read_text(encoding="utf-8"))

    def show_window(self):
        try:
            self._window.show()
            self._window.restore()
        except Exception:
            pass

    def minimize(self):
        self._window.minimize()

    def health(self):
        try:
            return health_checks(self._settings)
        except Exception as e:
            return self._err(e)

    def health_fix(self, cid):
        try:
            apply_health_fix(cid, self._settings)
            return True
        except Exception as e:
            return self._err(e)

    def repair(self, kind):
        try:
            return {"message": repair(kind, self._settings)}
        except Exception as e:
            return self._err(e)

    def calendar(self):
        return calendar_data()

    def game_stats(self, pid):
        try:
            return game_stats(pid)
        except Exception as e:
            return self._err(e)

    def packs(self):
        return pack_states(self._settings)

    def install_pack(self, pack_id, on=True):
        try:
            install_pack(self._settings, pack_id, bool(on))
            return pack_states(self._settings)
        except Exception as e:
            return self._err(e)

    def toggle_saved(self, server):
        saved = [x for x in self._settings.get("saved_servers", []) if x.get("job_id") != server.get("job_id")]
        if len(saved) == len(self._settings.get("saved_servers", [])):
            saved.insert(0, {k: server.get(k) for k in ("place_id", "job_id", "name", "location", "note")} |
                         {"saved": int(time.time())})
        self._settings["saved_servers"] = saved[:50]
        save_settings(self._settings)
        return saved

    def set_boost(self, on, level="Max"):
        if on and not has_premium(self._settings):
            return {"error": PREMIUM_LOCKED}
        try:
            set_boost(self._settings, bool(on), level if level in ("Max", "Balanced") else "Max")
            return {"settings": self._settings}
        except Exception as e:
            return self._err(e)

    def apply_system(self):
        if not has_premium(self._settings):
            enforce_premium(self._settings)
            return {"error": PREMIUM_LOCKED, "settings": self._settings}
        try:
            save_settings(self._settings)
            apply_system_boost(self._settings, (player_dirs()[:1] or [None])[0])
            return {"settings": self._settings, "pending": roblox_running()}
        except Exception as e:
            return self._err(e)

    def quick_preset(self, name, pid=None):
        if name == "Potato" and not has_premium(self._settings):
            return {"error": "The Potato preset is a Premium feature. Activate a premium key in Credits to use it."}
        try:
            apply_quick_preset(self._settings, name, pid)
            return {"settings": self._settings}
        except Exception as e:
            return self._err(e)

    def boost_status(self):
        perf = self._settings["performance"]
        gbs = GBS_FILE.exists()
        cap = None
        if gbs:
            m = re.search(r'<int name="FramerateCap">(-?\d+)</int>', GBS_FILE.read_text(encoding="utf-8", errors="ignore"))
            cap = int(m.group(1)) if m else None
        return {"gbs": gbs, "roblox_cap": cap, "running": roblox_running(), "windows": IS_WINDOWS,
                "boost": bool(perf.get("boost"))}

    def region_hop(self, pid, region):
        if RegionHop.current and not RegionHop.current.done:
            return {"error": "A region hop is already running."}
        if region not in REGIONS or not str(pid).isdigit():
            return {"error": "Pick a region and a game."}
        RegionHop.current = RegionHop(pid, region)
        threading.Thread(target=RegionHop.current.run, daemon=True).start()
        return RegionHop.current.state()

    def hop_state(self):
        return RegionHop.current.state() if RegionHop.current else None

    def hop_cancel(self):
        if RegionHop.current:
            RegionHop.current.cancelled = True
        return True

    def regions(self):
        return list(REGIONS)

    def problems(self):
        data = load_json(PROBLEMS_FILE, [])
        return list(reversed(data))[:20] if isinstance(data, list) else []

    def clear_problems(self):
        PROBLEMS_FILE.unlink(missing_ok=True)
        return True

    def sort_screenshots(self):
        try:
            return {"moved": sort_screenshots()}
        except Exception as e:
            return self._err(e)

    def export_mod_pack(self, name):
        try:
            picked = self._dialog("SAVE", save_filename=f"{name}.orbitpack", file_types=("Orbit mod pack (*.orbitpack)",))
            if not picked:
                return None
            dest = Path(picked[0] if isinstance(picked, (list, tuple)) else picked)
            return {"count": export_mod_pack(name, dest), "path": str(dest)}
        except Exception as e:
            return self._err(e)

    def import_mod_pack(self):
        try:
            picked = self._dialog("OPEN", file_types=("Orbit mod pack (*.orbitpack)",))
            if not picked:
                return None
            name, count = import_mod_pack(Path(picked[0] if isinstance(picked, (list, tuple)) else picked))
            return {"name": name, "count": count, "profiles": list_mod_profiles()}
        except Exception as e:
            return self._err(e)

    def toggle_mini(self):
        try:
            import webview
            if self._mini and self._mini_api._window:
                try:
                    self._mini.destroy()
                except Exception:
                    pass
                self._mini = None
                return False
            self._mini_api = MiniApi()
            html = (ui_file().parent / "mini.html").read_text(encoding="utf-8")
            sw = 1920
            try:
                sw = ctypes.windll.user32.GetSystemMetrics(0) if IS_WINDOWS else 1920
            except Exception:
                pass
            self._mini = webview.create_window("Orbit Mini", html=html, js_api=self._mini_api, width=320, height=118,
                                               x=sw - 340, y=60, resizable=False, frameless=True, easy_drag=True,
                                               on_top=True, background_color=theme_colors(self._settings["appearance"])["bg"])
            self._mini_api._window = self._mini
            self._mini.events.closed += lambda: setattr(self, "_mini", None)
            return True
        except Exception as e:
            return self._err(e)

    def avatars(self, refresh=False):
        out = {}
        for uid in {c[2] for c in CREDITS if len(c) > 2 and c[2]}:
            try:
                f = avatar_file(uid, refresh=bool(refresh))
                out[str(uid)] = data_url(f) if f else None
            except Exception as e:
                log(f"Avatar failed: {e}")
                out[str(uid)] = None
        return out

    def game_kits(self):
        return [{"id": k, "name": v["name"], "place_id": v["place_id"], "crosshair": v["crosshair"],
                 "applied": v["place_id"] in self._settings["game_profiles"]} for k, v in GAME_KITS.items()]

    def apply_kit(self, kit_id, crosshair=None):
        if not has_premium(self._settings):
            return {"error": PREMIUM_LOCKED}
        try:
            if kit_id not in GAME_KITS:
                return {"error": "Unknown game kit."}
            if crosshair and crosshair not in PACKS:
                crosshair = None
            apply_game_kit(self._settings, kit_id, crosshair)
            return {"settings": self._settings}
        except Exception as e:
            return self._err(e)

    def set_overlay_crosshair(self, cid, mode=None, size=None):
        ov = self._settings.setdefault("overlay", {})
        if cid is not None:
            if cid and not crosshair_source(cid):
                return {"error": "That crosshair isn't available."}
            ov["crosshair"] = cid or ""
        if mode in ("locked", "always"):
            ov["crosshair_mode"] = mode
        if size is not None:
            ov["crosshair_size"] = max(50, min(200, int(size)))
        save_settings(self._settings)
        if roblox_running() and ov.get("crosshair"):
            start_crosshair_overlay()
        elif not ov.get("crosshair"):
            close_crosshair_overlay()
        return {"settings": self._settings}

    def custom_crosshairs(self):
        return custom_crosshairs()

    def save_crosshair(self, name, data_url, design=None):
        try:
            cid = save_custom_crosshair(name, data_url, design)
            return {"id": cid, "list": custom_crosshairs()}
        except Exception as e:
            return self._err(e)

    def delete_crosshair(self, cid):
        try:
            delete_custom_crosshair(cid, self._settings)
            return {"list": custom_crosshairs(), "settings": self._settings}
        except Exception as e:
            return self._err(e)

    def set_game_crosshair(self, pid, cid):
        try:
            pid = str(pid)
            if not pid.isdigit():
                return {"error": "Unknown game."}
            gc = self._settings.setdefault("game_crosshairs", {})
            if cid:
                if not crosshair_source(cid):
                    return {"error": "That crosshair isn't available."}
                gc[pid] = cid
                self._settings["apply_mods"] = True
            else:
                gc.pop(pid, None)
            save_settings(self._settings)
            return {"settings": self._settings}
        except Exception as e:
            return self._err(e)

    def today(self):
        return {"seconds": today_seconds(), "limit": int(self._settings["session"].get("daily_minutes") or 0) * 60}

    def roblox_update_status(self):
        st = load_json(ROBLOX_DEPLOY_FILE, {}) or {}
        players = player_dirs()
        return {"installed": players[0].name if players else None, "state": st.get("state"), "version": st.get("version"),
                "progress": st.get("progress"), "error": st.get("error"), "at": st.get("at"),
                "enabled": self._settings["updates"].get("roblox_predownload", True)}

    def predownload_now(self):
        if roblox_running():
            return {"error": "Close Roblox first. Orbit pre-downloads updates while Roblox is closed."}
        threading.Thread(target=predownload_roblox, kwargs={"force": True}, daemon=True).start()
        return True

    def join_link(self):
        link = join_link()
        if not link:
            return {"error": "Join a server first."}
        copy_to_clipboard(link)
        return {"link": link}

    def region_test(self):
        try:
            return region_test()
        except Exception as e:
            return self._err(e)

    def last_region_test(self):
        return load_json(DATA_DIR / "region_test.json", None)

    def find_player(self, text):
        try:
            return find_player(text)
        except urllib.error.HTTPError as e:
            return {"error": "Roblox is busy right now. Try again in a few seconds." if e.code == 429
                    else f"Roblox returned an error ({e.code})."}
        except Exception as e:
            return self._err(e)

    def join_player(self, user):
        try:
            uid = int(user.get("id"))
            rp = [x for x in self._settings.get("recent_players", []) if x.get("id") != uid]
            rp.insert(0, {k: user.get(k) for k in ("id", "name", "display", "avatar")} | {"at": int(time.time())})
            self._settings["recent_players"] = rp[:12]
            save_settings(self._settings)
            r = self.launch(follow_uri(uid))
            return {"settings": self._settings} if r is True else r
        except Exception as e:
            return self._err(e)

    def forget_player(self, uid):
        self._settings["recent_players"] = [x for x in self._settings.get("recent_players", []) if x.get("id") != uid]
        save_settings(self._settings)
        return {"settings": self._settings}

    def fonts(self):
        out = []
        for fid, (name, fname, desc) in FONTS.items():
            f = font_file(fid)
            if f:
                out.append({"id": fid, "name": name, "desc": desc, "data": "data:font/otf;base64," + base64.b64encode(f.read_bytes()).decode()})
        cf = font_file("custom")
        if cf:
            out.append({"id": "custom", "name": "Your font", "desc": cf.name,
                        "data": "data:font/otf;base64," + base64.b64encode(cf.read_bytes()).decode()})
        return out

    def set_font(self, fid):
        if fid and not font_file(fid):
            return {"error": "That font isn't available."}
        self._settings["font"] = fid or ""
        if fid:
            self._settings["apply_mods"] = True
        save_settings(self._settings)
        return {"settings": self._settings}

    def choose_font(self):
        try:
            picked = self._dialog("OPEN", file_types=("Fonts (*.ttf;*.otf)",))
            if not picked:
                return None
            src = Path(picked[0] if isinstance(picked, (list, tuple)) else picked)
            if src.suffix.lower() not in (".ttf", ".otf") or src.stat().st_size > 15_000_000:
                return {"error": "Pick a .ttf or .otf font under 15 MB."}
            FONT_DIR.mkdir(parents=True, exist_ok=True)
            for old in FONT_DIR.glob("custom.*"):
                old.unlink(missing_ok=True)
            shutil.copy2(src, FONT_DIR / ("custom" + src.suffix.lower()))
            return self.set_font("custom")
        except Exception as e:
            return self._err(e)

    def set_profile(self, username):
        try:
            username = (username or "").strip()
            if not username:
                self._settings["profile"] = {"roblox_id": None, "username": "", "display": ""}
            else:
                u = find_player(username)
                self._settings["profile"] = {"roblox_id": u["id"], "username": u["name"], "display": u.get("display") or u["name"]}
            save_settings(self._settings)
            return {"settings": self._settings}
        except Exception as e:
            return self._err(e)

    def player_card(self):
        try:
            f = player_card(self._settings)
            return {"path": str(f), "data": data_url(f)}
        except Exception as e:
            return self._err(e)

    def fps_status(self):
        st = fps_ready()
        info = load_json(DATA_DIR / "fps_status.json", {}) or {}
        return {**st, "enabled": bool((self._settings.get("fps") or {}).get("enabled")),
                "pending_signout": bool(info.get("pending_signout")) and not st["group"], "error": info.get("error")}

    def fps_setup(self):
        try:
            r = setup_presentmon()
            self._settings.setdefault("fps", {})["enabled"] = True
            save_settings(self._settings)
            return {**r, "settings": self._settings}
        except Exception as e:
            return self._err(e)

    def replay_status(self):
        rp = self._settings.get("replay") or {}
        st = load_json(DATA_DIR / "ffmpeg_setup.json", {}) or {}
        return {"tool": FFMPEG.exists(), "enabled": bool(rp.get("enabled")), "recording": bool(Replay.proc and Replay.proc.poll() is None),
                "downloading": st.get("state") == "downloading", "progress": st.get("progress", 0), "error": st.get("error")}

    def replay_setup(self):
        def work():
            try:
                save_json(DATA_DIR / "ffmpeg_setup.json", {"state": "downloading", "progress": 0})
                last = {"p": -1}

                def prog(f):
                    if f - last["p"] >= 0.01:
                        last["p"] = f
                        save_json(DATA_DIR / "ffmpeg_setup.json", {"state": "downloading", "progress": round(f, 3)})
                setup_ffmpeg(prog)
                save_json(DATA_DIR / "ffmpeg_setup.json", {"state": "done", "progress": 1})
            except Exception as e:
                save_json(DATA_DIR / "ffmpeg_setup.json", {"state": "failed", "error": str(e)[:200]})
                log(f"ffmpeg setup failed: {e}")
        threading.Thread(target=work, daemon=True).start()
        return True

    def save_replay(self):
        r = Replay.save()
        return {"path": r} if r else {"error": "Nothing to save yet. Instant replay records while Roblox is open and in front."}

    def screenshot_now(self):
        r = take_roblox_screenshot()
        return {"path": r} if r else {"error": "Open Roblox first."}

    def toggle_alert(self, uid):
        for x in self._settings.get("recent_players", []):
            if x.get("id") == uid:
                x["alert"] = not x.get("alert")
        save_settings(self._settings)
        return {"settings": self._settings}

    def set_webhook(self, url):
        url = (url or "").strip()
        if url and not WEBHOOK_RE.fullmatch(url):
            return {"error": "That isn't a Discord webhook link."}
        self._settings["discord"]["webhook"] = url
        save_settings(self._settings)
        return {"settings": self._settings}

    def share_discord(self, kind):
        try:
            hook = self._settings["discord"].get("webhook")
            if not hook:
                return {"error": "Paste a Discord webhook link first."}
            name = (self._settings.get("profile") or {}).get("display") or "I"
            if kind == "card":
                share_to_discord(hook, f"{name}'s Orbit player card", player_card(self._settings))
            elif kind == "recap":
                recap = weekly_recap()
                if recap.get("empty"):
                    return {"error": "Play something this week first."}
                dest = pictures_dir() / "Orbit" / f"Orbit-recap-{time.strftime('%Y-%m-%d')}.png"
                render_recap_png(recap, self._settings, dest)
                share_to_discord(hook, f"{name}'s week on Roblox", dest)
            elif kind == "join":
                link = join_link()
                if not link:
                    return {"error": "Join a server first."}
                cur = load_json(CURRENT_FILE, None) or {}
                share_to_discord(hook, f"Join me in **{cur.get('name') or 'Roblox'}**: {link}")
            else:
                return {"error": "Unknown share."}
            return True
        except urllib.error.HTTPError as e:
            return {"error": f"Discord refused it ({e.code}). Check the webhook link."}
        except Exception as e:
            return self._err(e)

    def overlay_url(self):
        threading.Thread(target=OverlayServer.start, daemon=True).start()
        return f"http://127.0.0.1:{OVERLAY_PORT}/overlay"

    def news(self):
        return fetch_news()

    def mark_news(self, ids):
        self._settings["news_seen"] = list(dict.fromkeys(list(ids or []) + self._settings.get("news_seen", [])))[:200]
        save_settings(self._settings)
        return True

    def store(self):
        return fetch_store()

    def install_store_item(self, item_id):
        try:
            n = install_store_item(self._settings, item_id)
            return {"count": n, "settings": self._settings}
        except Exception as e:
            return self._err(e)

    def level(self):
        lv = orbit_level()
        lv["up"] = lv["level"] > (self._settings.get("last_level") or 0) and (self._settings.get("last_level") or 0) > 0
        if lv["level"] != self._settings.get("last_level"):
            self._settings["last_level"] = lv["level"]
            save_settings(self._settings)
        return lv

    def storage(self):
        try:
            return storage_report()
        except Exception as e:
            return self._err(e)

    def clean_storage(self, cat):
        try:
            return {"freed": clean_storage(cat)}
        except Exception as e:
            return self._err(e)

    def sync_info(self):
        meta = load_json(DATA_DIR / "sync.json", {}) or {}
        f = sync_file(self._settings)
        remote = None
        if f and f.exists():
            remote = int(f.stat().st_mtime)
        return {"candidates": sync_candidates(), "folder": (self._settings.get("sync") or {}).get("folder", ""),
                "last": meta.get("at"), "remote": remote, "remote_newer": bool(remote and remote > (meta.get("at") or 0) + 60)}

    def set_sync(self, folder):
        try:
            if folder and not Path(folder).is_dir():
                return {"error": "That folder doesn't exist."}
            self._settings["sync"] = {"folder": folder or ""}
            save_settings(self._settings)
            if folder:
                run_sync(self._settings, force=True)
            return {"settings": self._settings}
        except Exception as e:
            return self._err(e)

    def restore_sync(self):
        try:
            f = sync_file(self._settings)
            if not f or not f.exists():
                return {"error": "No synced backup found in that folder yet."}
            import_backup(f)
            save_json(DATA_DIR / "sync.json", {"at": int(time.time()), "file": str(f)})
            return True
        except Exception as e:
            return self._err(e)

    def set_emoji(self, style):
        if style and not emoji_source(style):
            return {"error": "Couldn't find Windows' emoji font on this PC."}
        self._settings["emoji"] = style or ""
        if style:
            self._settings["apply_mods"] = True
        save_settings(self._settings)
        return {"settings": self._settings}

    def last_report(self):
        return load_json(LAST_REPORT_FILE, None)

    def premium(self, refresh=False):
        st = premium_status(self._settings, bool(refresh))
        if not st["active"] and enforce_premium(self._settings):
            st = {**st, "settings": self._settings}
        return st

    def activate_premium(self, code):
        data = read_premium_key(code)
        if not data:
            return {"error": "That premium key isn't valid. Copy the whole key, starting with ORBIT-PREMIUM-."}
        if data.get("exp") and time.time() > data["exp"]:
            return {"error": "That premium key has expired."}
        if data["id"] in revoked_premium_ids(True):
            return {"error": "That premium key has been turned off by the owner."}
        if data.get("uid"):
            uid = current_roblox_uid()
            if not uid:
                return {"error": "Orbit can't tell which Roblox account you use yet. Join any Roblox game once, then try again."}
            if uid != data["uid"]:
                return {"error": f"This key belongs to {data.get('for') or 'someone else'}. It only works on their Roblox account."}
        self._settings["premium_key"] = code.strip()
        save_settings(self._settings)
        log(f"Premium activated ({data['id']})")
        return {"status": premium_status(self._settings), "settings": self._settings}

    def remove_premium(self):
        self._settings["premium_key"] = ""
        save_settings(self._settings)
        enforce_premium(self._settings)
        return {"status": premium_status(self._settings), "settings": self._settings}

    def owner_issue(self, name, days=0):
        if not is_owner():
            return {"error": "Owner only."}
        try:
            try:
                user = roblox_user_by_name(name)
            except urllib.error.URLError:
                return {"error": "Couldn't reach Roblox to check that username. Check your internet and try again."}
            payload, code = make_premium_key(user["name"], int(days or 0), user["id"])
            return {"key": payload, "code": code}
        except Exception as e:
            return self._err(e)

    def owner_keys(self):
        if not is_owner():
            return {"error": "Owner only."}
        issued = load_json(OWNER_ISSUED_FILE, []) or []
        fresh = time.time() - (load_json(PREMIUM_REVOKED_CACHE, {}) or {}).get("at", 0) > 300
        return {"issued": issued, "revoked_live": sorted(revoked_premium_ids(fresh)), "repo": update_repo()}

    def owner_revoke(self, key_id, revoked=True):
        if not is_owner():
            return {"error": "Owner only."}
        issued = load_json(OWNER_ISSUED_FILE, []) or []
        token = owner_gh_token()
        if token:
            try:
                ids = push_revoked(key_id, revoked, token)
            except Exception as e:
                return self._err(e)
        else:
            ids = {x["id"] for x in issued if x.get("revoked") and x["id"] != key_id} | revoked_premium_ids(True)
            ids = (ids | {key_id}) if revoked else (ids - {key_id})
        for x in issued:
            if x.get("id") == key_id:
                x["revoked"] = bool(revoked)
        save_json(OWNER_ISSUED_FILE, issued)
        text = json.dumps({"revoked": sorted(ids)}, indent=2)
        if token:
            return {"issued": issued, "pushed": True}
        copy_to_clipboard(text)
        repo = update_repo()
        if repo:
            webbrowser.open(f"https://github.com/{repo}/edit/main/premium_revoked.json")
        return {"issued": issued, "json": text}

    def owner_github(self):
        if not is_owner():
            return {"error": "Owner only."}
        data = load_json(OWNER_GH_FILE, {}) or {}
        return {"connected": bool(owner_gh_token()), "user": data.get("user"), "token_url": GH_TOKEN_URL}

    def owner_connect_github(self, token):
        if not is_owner():
            return {"error": "Owner only."}
        token = (token or "").strip()
        if not re.fullmatch(r"(github_pat_|ghp_)[A-Za-z0-9_]{20,}", token):
            return {"error": "That doesn't look like a GitHub token. It starts with github_pat_."}
        repo = update_repo()
        try:
            info = gh_api("GET", f"/repos/{repo}", token)
            if not (info.get("permissions") or {}).get("push"):
                raise PermissionError("That token can only read the repo. Give it Contents: Read and write.")
            try:
                user = gh_api("GET", "/user", token).get("login")
            except Exception:
                user = None
            user = user or repo.split("/")[0]
            save_json(OWNER_GH_FILE, {"token": base64.b64encode(_dpapi(token.encode())).decode(), "user": user})
            log(f"Owner panel connected to GitHub as {user}")
            return {"connected": True, "user": user}
        except Exception as e:
            return self._err(e)

    def owner_disconnect_github(self):
        OWNER_GH_FILE.unlink(missing_ok=True)
        return {"connected": False}

    def owner_backup_key(self):
        if not is_owner():
            return {"error": "Owner only."}
        try:
            picked = self._dialog("SAVE", save_filename="orbit-owner-key.key", file_types=("Orbit owner key (*.key)",))
            if not picked:
                return None
            dest = Path(picked[0] if isinstance(picked, (list, tuple)) else picked)
            shutil.copy2(OWNER_KEY_FILE, dest)
            return {"path": str(dest)}
        except Exception as e:
            return self._err(e)

    def import_owner_key(self):
        try:
            picked = self._dialog("OPEN", file_types=("Orbit owner key (*.key)",))
            if not picked:
                return None
            src = Path(picked[0] if isinstance(picked, (list, tuple)) else picked)
            data = json.loads(src.read_text(encoding="utf-8"))
            seed = bytes.fromhex(data.get("seed", ""))
            if len(seed) != 32 or ed_public(seed) != OWNER_PUBKEY:
                return {"error": "That isn't the owner key for this Orbit."}
            shutil.copy2(src, OWNER_KEY_FILE)
            log("Owner key imported")
            return {"owner": True}
        except Exception:
            return {"error": "That file isn't an owner key."}

    def hotkeys(self):
        return [{"keys": v[2], "desc": v[3]} for v in HOTKEYS.values()]

    def set_startup(self, on):
        try:
            set_start_with_windows(bool(on))
            self._settings["session"]["start_with_windows"] = bool(on)
            save_settings(self._settings)
            return {"on": bool(on)}
        except Exception as e:
            return self._err(e)

    def toggle_maximize(self):
        self._maximized = not getattr(self, "_maximized", False)
        try:
            if self._maximized:
                self._window.maximize()
            else:
                self._window.restore()
        except Exception as e:
            log(f"Maximize failed: {e}")
        return self._maximized

    def close(self):
        if self._tray is not None and self._settings["appearance"].get("close_to_tray") and not self._quitting:
            self._window.hide()
            if not self._tray_hint:
                self._tray_hint = True
                try:
                    self._tray.notify("Orbit is still running in the tray. Right-click the icon to quit.", APP_NAME)
                except Exception:
                    pass
            return "hidden"
        self._quitting = True
        if self._tray is not None:
            try:
                self._tray.stop()
            except Exception:
                pass
        if self._settings["updates"].get("auto", True) and pending_update():
            apply_pending_update(restart=False)
        log("Orbit closed")
        self._window.destroy()


def _has_webview():
    import importlib
    import importlib.util
    importlib.invalidate_caches()
    return importlib.util.find_spec("webview") is not None


def _ensure_webview():
    if _has_webview():
        return True
    if getattr(sys, "frozen", False) or not IS_WINDOWS:
        print("Orbit's window needs pywebview:  pip install pywebview")
        return False
    if ctypes.windll.user32.MessageBoxW(
            None, "Orbit's app window needs the 'pywebview' package (one-time install).\n\nInstall it now?",
            APP_NAME, 0x4 | 0x40) != 6:
        return False
    py = Path(sys.executable).with_name("python.exe")
    subprocess.run([str(py if py.exists() else sys.executable), "-m", "pip", "install", "pywebview"])
    if _has_webview():
        return True
    message_box("Installing pywebview failed. Open a terminal and run:\n\npip install pywebview", error=True)
    return False


def run_gui(mode="app", after_update=False, selftest=False):
    log(f"Opening {mode} window (v{APP_VERSION}{', self-test' if selftest else ''})")
    try:
        _run_gui(mode, after_update, selftest)
    except Exception:
        log("Window failed to open:\n" + traceback.format_exc())
        if selftest:
            _write_selftest(mode, False, [traceback.format_exc()])
        else:
            message_box("Orbit couldn't open its window. Details were saved to:\n" + str(LOG_FILE), error=True)


def _write_selftest(mode, ready, errors):
    out = os.environ.get("ORBIT_SELFTEST_OUT") or str(DATA_DIR / "selftest.json")
    save_json(out, {"mode": mode, "ready": ready, "errors": errors, "version": APP_VERSION})


def _run_gui(mode, after_update, selftest):
    if mode == "app" and not selftest:
        settings = load_settings()
        if settings["updates"].get("auto", True) and apply_pending_update(("--after-update",)):
            return
        if not acquire_gui_lock(wait=12 if after_update else 0):
            DATA_DIR.mkdir(parents=True, exist_ok=True)
            SHOW_FLAG.write_text(str(time.time()))
            return
        SHOW_FLAG.unlink(missing_ok=True)
        save_json(GUI_FILE, {"pids": [os.getpid(), os.getppid()], "version": APP_VERSION, "time": int(time.time())})
        startup_maintenance(settings)
    if not _ensure_webview():
        return
    import webview
    api = Api(mode)
    html = ui_file().read_text(encoding="utf-8")
    bg = theme_colors(api._settings["appearance"])["bg"]
    size = (1080, 700) if mode == "app" else (760, 600)
    title = APP_NAME if mode == "app" else f"{APP_NAME} Setup"
    window = webview.create_window(title, html=html, js_api=api, width=size[0], height=size[1],
                                   resizable=False, frameless=True, easy_drag=False, background_color=bg)
    api._window = window
    if selftest:
        def finish_selftest():
            ready = api._ready.wait(90)
            time.sleep(2)
            if mode == "app":
                table = process_table() or []
                me = os.getpid()
                try:
                    jl = apply_jump_list() or not is_frozen()
                except Exception as e:
                    log(f"Jump list check failed: {e}")
                    jl = False
                checks = {"jumplist": jl, "table": len(table) > 10 and any(pid == me for pid, _, _ in table),
                          "alive_self": pid_alive(me), "alive_bogus": not pid_alive(4_000_000_001 % 4_000_000),
                          "named": me in pids_named(Path(sys.executable).name) or not is_frozen(),
                          "priority": set_priority(pid=me) == 1, "roblox": roblox_running() is False,
                          "helper_zip": (resource_dir() / "helper.zip").exists() or not is_frozen()}
                log(f"Process checks: {checks}")
                api._ui_errors += [f"process check failed: {k}" for k, v in checks.items() if not v]
                r = api.toggle_mini()
                if r is not True:
                    api._ui_errors.append(f"mini player: {r}")
                time.sleep(2)
            _write_selftest(mode, ready, api._ui_errors)
            log(f"Self-test {'passed' if ready and not api._ui_errors else 'FAILED'} ({mode})")
            window.destroy()
        threading.Thread(target=finish_selftest, daemon=True).start()
    elif mode == "app":
        if api._settings["appearance"].get("close_to_tray"):
            try:
                api._tray = start_tray(api)
            except Exception as e:
                log(f"Tray icon unavailable: {e}")

        def watch_show_requests():
            while True:
                time.sleep(0.6)
                if SHOW_FLAG.exists():
                    SHOW_FLAG.unlink(missing_ok=True)
                    api.show_window()
        threading.Thread(target=watch_show_requests, daemon=True).start()
        threading.Thread(target=AutoAttach("window").loop, daemon=True).start()
        threading.Thread(target=hotkey_loop, args=("window",), daemon=True).start()
        threading.Thread(target=OverlayServer.start, daemon=True).start()

        def jump_list():
            time.sleep(4)
            try:
                apply_jump_list()
            except Exception as e:
                log(f"Jump list unavailable: {e}")
        threading.Thread(target=jump_list, daemon=True).start()
    icon = app_icon_file()
    try:
        webview.start(debug=bool(os.environ.get("ORBIT_DEBUG")), icon=str(icon) if icon.exists() else None)
    except TypeError:
        webview.start(debug=bool(os.environ.get("ORBIT_DEBUG")))
    if mode == "app" and not selftest:
        if api._tray is not None:
            try:
                api._tray.stop()
            except Exception:
                pass
        os._exit(0)


def _log_unhandled(kind, exc_type, exc, tb):
    log(f"Unhandled {kind} error:\n" + "".join(traceback.format_exception(exc_type, exc, tb)))


def main():
    sys.excepthook = lambda t, e, tb: _log_unhandled("main", t, e, tb)
    threading.excepthook = lambda a: _log_unhandled("thread", a.exc_type, a.exc_value, a.exc_traceback)
    args = sys.argv[1:]
    if stale_extraction():
        log(f"Restarting cleanly (started with files from v{build_info().get('version')})")
        subprocess.Popen([sys.executable, *args], env=child_env({"ORBIT_REEXEC": "1"}))
        return
    if ATTACH_FLAG in args:
        try:
            attach_main()
        except Exception:
            log("Attach failed:\n" + traceback.format_exc())
        return
    if BACKGROUND_FLAG in args:
        try:
            background_main()
        except Exception:
            log("Background mode failed:\n" + traceback.format_exc())
        return
    if ACTION_FLAG in args:
        i = args.index(ACTION_FLAG)
        ensure_dirs()
        try:
            run_hotkey(args[i + 1] if len(args) > i + 1 else "", True)
        except Exception:
            log("Action failed:\n" + traceback.format_exc())
        return
    if is_helper() and not any(f in args for f in (TOAST_FLAG, LAUNCH_FLAG)):
        if INSTALLED_EXE.exists():
            subprocess.Popen([str(INSTALLED_EXE), *args], env=child_env())
        return
    if PREPARE_FLAG in args:
        ensure_dirs()
        prepare_fast_paths(load_settings())
        log(f"Prepared v{APP_VERSION} (helper: {helper_ready() or 'none'})")
        return
    if "--selftest-spawn" in args:
        subprocess.Popen([sys.executable, "--selftest"], env=child_env())
        return
    setup_named = is_frozen() and "setup" in Path(sys.executable).stem.lower()
    if UNINSTALL_FLAG in args:
        run_uninstall()
    elif SETUP_FLAG in args or (setup_named and LAUNCH_FLAG not in args and TOAST_FLAG not in args):
        run_gui("setup", selftest="--selftest" in args)
    elif TOAST_FLAG in args:
        i = args.index(TOAST_FLAG)
        title = args[i + 1] if len(args) > i + 1 else APP_NAME
        body = args[i + 2] if len(args) > i + 2 else ""
        try:
            if KEYS_FLAG in args:
                show_keys_window()
            elif CROSS_FLAG in args:
                show_crosshair_window()
            elif "--badge" in args:
                def opt(flag):
                    return args[args.index(flag) + 1] if flag in args and len(args) > args.index(flag) + 1 else None
                show_badge_window(title, body, opt("--ip"), opt("--joined"))
            else:
                show_toast(title, body)
        except Exception:
            log("Toast failed:\n" + traceback.format_exc())
    elif LAUNCH_FLAG in args:
        i = args.index(LAUNCH_FLAG)
        uri = args[i + 1] if i + 1 < len(args) else ""
        try:
            headless_main(uri.strip())
        except Exception:
            log(traceback.format_exc())
            message_box("Something went wrong launching Roblox. Details are in:\n" + str(LOG_FILE), error=True)
    else:
        run_gui(after_update="--after-update" in args, selftest="--selftest" in args)


if __name__ == "__main__":
    main()
