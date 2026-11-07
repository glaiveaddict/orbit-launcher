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
APP_VERSION = "1.9.1"
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
    ("Founder/Owner", "@stabzane"),
    ("Lead Developer", "@stabzane"),
    ("Sounds/UI Designer", "@stabzane"),
    ("Scripter", "@stabzane"),
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
                    "game_mode": False, "no_dvr": False, "gpu_applied": False, "boost_backup": {}, "win_backup": {}},
    "smart_join": False,
    "sounds": {"pack": "Warp", "volume": 0.6},
    "last_seen_version": "",
    "saved_servers": [],
    "hotkeys": {"enabled": True},
    "mod_profile": "Default",
    "discord": {
        "enabled": False,
        "client_id": "",
        "show_join_button": False,
        "show_game_icon": True,
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
    "updates": {"auto": True},
    "registration": {"registered": False, "backups": {}},
}
FREEFORM_KEYS = {"custom_flags", "backups", "game_profiles", "boost_backup", "win_backup"}


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


def save_json(path, data):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)
    os.replace(tmp, path)


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


def load_settings():
    loaded = load_json(SETTINGS_FILE, {})
    return _merge(DEFAULT_SETTINGS, loaded if isinstance(loaded, dict) else {})


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


def self_command(*args):
    if getattr(sys, "frozen", False):
        return [sys.executable, *args]
    py = Path(sys.executable)
    pyw = py.with_name("pythonw.exe")
    return [str(pyw if pyw.exists() else py), str(Path(__file__).resolve()), *args]


def spawn_self(*args):
    try:
        return subprocess.Popen(self_command(*args), creationflags=CREATE_NO_WINDOW, env=child_env())
    except OSError as e:
        log(f"Could not start {args[:1]}: {e}")
        return None


_GAME_CACHE = {}


def game_info(place_id):
    place_id = str(place_id)
    if place_id in _GAME_CACHE:
        return _GAME_CACHE[place_id]
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
    try:
        d = fetch_json(f"https://ipinfo.io/{ip}/json")
    except Exception as e:
        log(f"Location lookup failed: {e}")
        return None
    parts = []
    for part in (d.get("city"), d.get("region"), d.get("country")):
        if part and part not in parts:
            parts.append(part)
    return ", ".join(parts) or None


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


def sync_mods(version_dir, folder=None):
    vdir = Path(version_dir)
    manifest_path = vdir / MOD_MANIFEST
    backup_root = vdir / MOD_BACKUP_DIR
    old = load_json(manifest_path, [])
    current = list_mods(folder) if folder else []

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
        source, target, backup = Path(folder) / rel, vdir / rel, backup_root / rel
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
        n = sync_mods(d, folder)
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
    if (cap is None and not quality) or not GBS_FILE.exists() or roblox_running():
        return False
    text = GBS_FILE.read_text(encoding="utf-8", errors="ignore")
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
    cmd = self_command(LAUNCH_FLAG)
    return " ".join(f'"{part}"' for part in cmd[:-1]) + f' {LAUNCH_FLAG} "%1"'


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
    if discord.get("show_join_button") and job_id:
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
        self.game = game
        self._publish(game)
        log(f"Joined place {place_id}" + (" (already in progress)" if quiet else ""))
        save_json(LAST_SERVER_FILE, {"place_id": place_id, "job_id": job_id, "name": None, "time": int(joined)})
        threading.Thread(target=self._join_details, args=(game,), daemon=True).start()

    def _publish(self, game):
        if game is not None and self.game is game:
            save_json(CURRENT_FILE, {"place_id": game["place_id"], "job_id": game["job_id"], "name": game.get("name"),
                                     "joined": int(game["joined"]), "location": game.get("location"),
                                     "icon": game.get("icon"), "ip": game.get("ip")})

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
        time.sleep(1.5)
        self._locate(game)

    def _ping_loop(self, game):
        time.sleep(4)
        while self.game is game:
            ms = ping_ms(game.get("ip"))
            if self.game is not game:
                break
            game["pings"].append([int(time.time()), ms])
            del game["pings"][:-720]
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

    def on_udmux(self, ip):
        game = self.game
        if game and not game["located"]:
            game["ip"] = ip

    def _locate(self, game):
        with self.lock:
            if game["located"]:
                return
            game["located"] = True
        location = server_location(game["ip"])
        game["location"] = location
        self._publish(game)
        log(f"Server location: {location or 'unknown'} ({game['ip']})")
        if not location or self.game is not game:
            return
        for _ in range(10):
            if game["name"]:
                break
            time.sleep(0.5)
        if self.session.get("server_popup") and not game.get("quiet"):
            spawn_toast(game["name"] or "Joined a game", location)
            time.sleep(7)
        if self.session.get("server_badge", True) and self.game is game:
            show_badge(game["name"] or "Roblox", location, game.get("ip"), game.get("joined"))

    def on_leave(self, at=None, record=True):
        game, self.game = self.game, None
        if not game:
            return
        seconds = max(0, (at or time.time()) - game["joined"])
        close_badge()
        CURRENT_FILE.unlink(missing_ok=True)
        if record and self.session.get("track_playtime"):
            record_playtime(game["place_id"], game["name"], seconds)
            record_session(game, seconds)
        if record and self.session.get("sort_screenshots"):
            threading.Thread(target=sort_screenshots, daemon=True).start()
        self._discord(None)

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
        raise_own_priority()
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
    names = {Path(sys.executable).name.lower(), "orbitlauncher.exe"} if is_frozen() else {"orbitlauncher.exe"}
    pids = set()
    for name in names:
        pids |= set(pids_named(name))
    return pids


def window_pids():
    pids = set()
    for f in (GUI_FILE, BACKGROUND_FILE):
        data = load_json(f, {}) or {}
        pids |= {int(x) for x in data.get("pids", []) if str(x).isdigit()}
    return pids


def stop_legacy_trackers(keep):
    keep_list = ",".join(str(x) for x in keep)
    script = (f"$keep=@({keep_list}); "
              "Get-CimInstance Win32_Process -Filter \"CommandLine LIKE '%--orbit-launch%'\" | "
              "Where-Object { $keep -notcontains $_.ProcessId -and $keep -notcontains $_.ParentProcessId } | "
              "ForEach-Object { Stop-Process -Id $_.ProcessId -Force -ErrorAction SilentlyContinue; "
              "\"$($_.ProcessId) $($_.Name)\" }")
    try:
        r = subprocess.run([sys_tool("powershell"), "-NoProfile", "-Command", script], capture_output=True, text=True,
                           timeout=40, creationflags=CREATE_NO_WINDOW)
        if r.stdout.strip():
            log("Stopped legacy Orbit trackers: " + "; ".join(r.stdout.split("\n")).strip("; "))
        if r.stderr.strip():
            log("Legacy tracker check: " + r.stderr.strip()[:300])
    except Exception as e:
        log(f"Legacy tracker check failed: {e}")


def stop_stale_copies():
    if not IS_WINDOWS or not is_frozen():
        return
    keep = {os.getpid(), os.getppid()}
    threading.Thread(target=stop_legacy_trackers, args=(keep,), daemon=True).start()
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
        if time.time() - self.last_guard > 30:
            self.last_guard = time.time()
            self.guard_links()
            try:
                check_roblox_update(load_settings())
            except Exception as e:
                log(f"Roblox update check failed: {e}")
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
            if is_frozen() and settings["registration"].get("registered") and \
                    read_protocol_command(PROTOCOLS[0]) != our_command():
                register_protocols(settings)
                log("Another app had taken over Roblox links; switched them back to Orbit")
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
    AutoAttach("background").loop(interval=6)


def set_start_with_windows(on):
    if not IS_WINDOWS:
        return False
    if not is_frozen():
        raise OSError("Start with Windows only works in the installed app.")
    with winreg.CreateKey(winreg.HKEY_CURRENT_USER, RUN_KEY) as k:
        if on:
            winreg.SetValueEx(k, APP_NAME, 0, winreg.REG_SZ, f'"{sys.executable}" {BACKGROUND_FLAG}')
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
           4: (0x4F, "open", "Ctrl+Alt+O", "Open Orbit")}


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
    }


PACKS = {
    "cursor_void_ring": ("Void Ring", "cursor", "A glowing purple ring with a white center dot."),
    "cursor_dot": ("Dot", "cursor", "A tiny clean dot. Minimal and precise."),
    "cursor_crosshair": ("Crosshair", "cursor", "A thin crosshair for aiming games."),
    "death_soft_pop": ("Soft Pop", "sound", "A short, soft pop when you reset or die."),
    "death_warp": ("Warp Out", "sound", "A sci-fi warp swoosh."),
    "death_retro": ("Retro Blip", "sound", "A quick three-note retro blip."),
}
PACK_TARGETS = {
    "cursor": ["content/textures/Cursors/KeyboardMouse/ArrowFarCursor.png",
               "content/textures/Cursors/KeyboardMouse/ArrowCursor.png"],
    "sound": ["content/sounds/ouch.ogg"],
}


def pack_file(pack_id):
    ext = ".png" if PACKS[pack_id][1] == "cursor" else ".ogg"
    return resource_dir() / "ui" / "packs" / (pack_id + ext)


def pack_states(settings):
    folder = mods_dir(settings)
    out = []
    for pid, (name, kind, desc) in PACKS.items():
        src = pack_file(pid)
        installed = src.exists() and all((folder / t).exists() and (folder / t).stat().st_size == src.stat().st_size
                                          for t in PACK_TARGETS[kind])
        mime = "image/png" if kind == "cursor" else "audio/ogg"
        data = f"data:{mime};base64," + base64.b64encode(src.read_bytes()).decode() if src.exists() else ""
        out.append({"id": pid, "name": name, "kind": kind, "desc": desc, "installed": installed, "data": data})
    return out


def install_pack(settings, pack_id, on=True):
    if pack_id not in PACKS:
        raise ValueError("Unknown pack")
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
               "light": settings["appearance"].get("mode") == "Light", "bg": c["bg"]}
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

    def close(self):
        if self._window:
            self._window.destroy()
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
        if settings["registration"].get("registered") and \
                read_protocol_command(PROTOCOLS[0]) != our_command():
            register_protocols(settings)
    except Exception as e:
        log(f"Startup maintenance: {e}")


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
    raise_own_priority()
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
    w = x + sum(f.measure(item[4] if len(item) > 4 else item[1]) for item in layout for f in [item[2]]) + 12
    cv = tk.Canvas(root, width=w, height=h, bg=key, highlightthickness=0, bd=0)
    cv.pack()
    r = h // 2
    pts = lambda x1, y1, x2, y2, rr: [x1 + rr, y1, x2 - rr, y1, x2, y1, x2, y1 + rr, x2, y2 - rr, x2, y2, x2 - rr, y2,
                                      x1 + rr, y2, x1, y2, x1, y2 - rr, x1, y1 + rr, x1, y1]
    cv.create_polygon(pts(0, 0, w - 1, h - 1, r), smooth=True, splinesteps=20, fill=c["accent"], outline="")
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
    state = {"alpha": 0.0, "xy": None, "hwnd": None, "ping": None}
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
                moved = bool(u.SetWindowPos(state["hwnd"], ctypes.c_void_p(-1), xy[0], xy[1], 0, 0,
                                            0x0001 | 0x0010 | 0x0040))
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
                state["ping"] = ping_ms(ip)
                time.sleep(5)
        threading.Thread(target=pinger, daemon=True).start()

    def refresh_numbers():
        if "ping" in items:
            p = state["ping"]
            color = c["muted"] if p is None else "#4ade80" if p < 80 else "#fbbf24" if p < 150 else "#fb7185"
            cv.itemconfigure(items["ping"], text="··· ms" if p is None else f"{p} ms", fill=color)
        if "timer" in items:
            sec = max(0, int(time.time() - joined))
            hh, mm, ss = sec // 3600, sec % 3600 // 60, sec % 60
            cv.itemconfigure(items["timer"], text=f"{hh}:{mm:02d}:{ss:02d}" if hh else f"{mm}:{ss:02d}")

    def tick():
        try:
            visible = roblox_in_front() and not BADGE_HIDDEN.exists()
            target = peak if visible else 0.0
            state["alpha"] += (target - state["alpha"]) * 0.35
            if abs(state["alpha"] - target) < 0.02:
                state["alpha"] = target
            place()
            refresh_numbers()
            root.attributes("-alpha", state["alpha"])
            root.attributes("-topmost", True)
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


def copy_to_clipboard(text):
    if IS_WINDOWS:
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
            "packs_ready": (resource_dir() / "ui" / "packs").is_dir(),
            "credits": [{"role": r, "handle": h} for r, h in CREDITS],
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
            self._settings = merged
            save_settings(merged)
            return True
        except Exception as e:
            return self._err(e)

    def launch(self, uri=""):
        try:
            if not player_dirs():
                return {"error": "Roblox isn't installed yet. Get it from roblox.com/download."}
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
        try:
            set_boost(self._settings, bool(on), level if level in ("Max", "Balanced") else "Max")
            return {"settings": self._settings}
        except Exception as e:
            return self._err(e)

    def apply_system(self):
        try:
            save_settings(self._settings)
            apply_system_boost(self._settings, (player_dirs()[:1] or [None])[0])
            return {"settings": self._settings, "pending": roblox_running()}
        except Exception as e:
            return self._err(e)

    def quick_preset(self, name, pid=None):
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
                checks = {"table": len(table) > 10 and any(pid == me for pid, _, _ in table),
                          "alive_self": pid_alive(me), "alive_bogus": not pid_alive(4_000_000_001 % 4_000_000),
                          "named": me in pids_named(Path(sys.executable).name) or not is_frozen(),
                          "priority": set_priority(pid=me) == 1, "roblox": roblox_running() is False}
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
            if "--badge" in args:
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
