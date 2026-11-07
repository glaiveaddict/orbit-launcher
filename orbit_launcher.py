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
import urllib.parse
import urllib.request
import uuid
import webbrowser
from pathlib import Path

APP_NAME = "Orbit Launcher"
APP_VERSION = "1.5.0"
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
    },
    "appearance": {
        "mode": "Dark",
        "accent": "Void",
        "custom_window_icon": False,
    },
    "updates": {"auto": True},
    "registration": {"registered": False, "backups": {}},
}
FREEFORM_KEYS = {"custom_flags", "backups", "game_profiles"}


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
        subprocess.Popen(self_command(*args), creationflags=CREATE_NO_WINDOW)
    except OSError as e:
        log(f"Could not start {args[:1]}: {e}")


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
        _GAME_CACHE[place_id] = info
    except Exception as e:
        log(f"Game lookup failed for {place_id}: {e}")
    return info


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


def apply_all(settings, version_dir=None, place_id=None):
    ensure_dirs()
    dirs = [Path(version_dir)] if version_dir else player_dirs()[:1]
    flags = build_flags(settings, place_id)
    folder = mods_dir(settings) if settings.get("apply_mods", True) else None
    for d in dirs:
        write_flags(d, flags)
        n = sync_mods(d, folder)
        _, _, prof = profile_for(settings, place_id)
        log(f"Applied {len(flags)} flag(s){' [' + prof + ' profile]' if prof else ''} "
            f"and {n} mod file(s) to {d.name}")
    return dirs


def roblox_running():
    if not IS_WINDOWS:
        return False
    try:
        out = subprocess.run(["tasklist", "/FI", "IMAGENAME eq RobloxPlayerBeta.exe", "/NH"],
                             capture_output=True, text=True, creationflags=CREATE_NO_WINDOW).stdout
        return "RobloxPlayerBeta.exe" in out
    except Exception:
        return False


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
    out = subprocess.run(["powershell", "-NoProfile", "-ExecutionPolicy", "Bypass", "-Command", ps],
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


def spawn_toast(title, body):
    spawn_self(TOAST_FLAG, title, body)


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

    @staticmethod
    def wanted(settings):
        s, d, a = settings["session"], settings["discord"], settings["appearance"]
        return (any(s.values()) or (d.get("enabled") and d.get("client_id", "").strip())
                or (a.get("custom_window_icon") and ICON_FILE.exists()))

    def _discord(self, activity):
        if self.ipc:
            with self.lock:
                self.ipc.set_activity(activity)

    def on_join(self, place_id, job_id, ip):
        if self.game:
            self.on_leave()
        game = {"place_id": place_id, "job_id": job_id, "ip": ip, "joined": time.time(),
                "name": None, "located": False}
        self.game = game
        log(f"Joined place {place_id}")
        save_json(LAST_SERVER_FILE, {"place_id": place_id, "job_id": job_id, "name": None,
                                     "time": int(time.time())})
        threading.Thread(target=self._join_details, args=(game,), daemon=True).start()

    def _join_details(self, game):
        info = game_info(game["place_id"])
        game["name"] = info["name"]
        last = load_json(LAST_SERVER_FILE, {})
        if last.get("job_id") == game["job_id"]:
            last["name"] = info["name"]
            save_json(LAST_SERVER_FILE, last)
        if self.game is game:
            self._discord(build_activity(self.discord, game["place_id"], game["job_id"], info, game["joined"]))
        time.sleep(max(0.0, 4 - (time.time() - game["joined"])))
        self._locate(game)

    def on_udmux(self, ip):
        game = self.game
        if game and not game["located"]:
            game["ip"] = ip
            threading.Thread(target=self._locate, args=(game,), daemon=True).start()

    def _locate(self, game):
        if not self.session.get("server_popup"):
            return
        with self.lock:
            if game["located"]:
                return
            game["located"] = True
        location = server_location(game["ip"])
        if not location or self.game is not game:
            return
        for _ in range(10):
            if game["name"]:
                break
            time.sleep(0.5)
        spawn_toast(f"Joined {game['name'] or 'a game'}", f"Server location: {location}")

    def on_leave(self):
        game, self.game = self.game, None
        if not game:
            return
        if self.session.get("track_playtime"):
            record_playtime(game["place_id"], game["name"], time.time() - game["joined"])
        self._discord(None)

    def _newest_log(self):
        try:
            logs = [p for p in ROBLOX_LOGS.glob("*.log") if p.stat().st_mtime >= self.launch_time - 5]
        except OSError:
            return None
        players = [p for p in logs if "player" in p.name.lower()] or logs
        return max(players, key=lambda p: p.stat().st_ctime, default=None)

    def handle_line(self, line):
        m = JOIN_RE.search(line)
        if m:
            self.on_join(m.group(2), m.group(1), m.group(3))
            return
        m = UDMUX_RE.search(line)
        if m:
            self.on_udmux(m.group(1))
            return
        if any(marker in line for marker in LEAVE_MARKERS):
            self.on_leave()

    def run(self):
        log_path = None
        deadline = time.time() + 90
        while not log_path and time.time() < deadline:
            log_path = self._newest_log()
            if not log_path:
                if self.icon:
                    self.icon.apply()
                time.sleep(1)
        if not log_path:
            log("No Roblox log appeared; session features disabled for this launch")
            return
        log(f"Watching {log_path.name}")
        fh = open(log_path, encoding="utf-8", errors="ignore")
        last_check, not_running = 0, 0
        try:
            while True:
                line = fh.readline()
                if line:
                    self.handle_line(line)
                    continue
                time.sleep(1)
                if time.time() - last_check < 5:
                    continue
                last_check = time.time()
                if self.icon:
                    self.icon.apply()
                newer = self._newest_log()
                if newer and newer != log_path:
                    self.on_leave()
                    fh.close()
                    log_path = newer
                    fh = open(log_path, encoding="utf-8", errors="ignore")
                    log(f"Switched to {log_path.name}")
                not_running = 0 if roblox_running() else not_running + 1
                if not_running >= 2:
                    break
        finally:
            fh.close()
            if self.game and self.session.get("crash_rejoin"):
                g = self.game
                self.crashed = {"place_id": g["place_id"], "job_id": g["job_id"],
                                "name": g["name"] or f"Place {g['place_id']}"}
            self.on_leave()
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
        subprocess.Popen(["cmd", "/c", "start", "", browser, page], creationflags=CREATE_NO_WINDOW)


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
    subprocess.Popen(args, cwd=str(exe.parent))
    log(f"Started {players[0].name}")
    updater = threading.Thread(target=watch_for_updates, args=(settings, known, place_id), daemon=True)
    updater.start()
    return launch_time, updater


_MONITOR_MUTEX = None


def acquire_monitor_lock():
    global _MONITOR_MUTEX
    if not IS_WINDOWS:
        return True
    k32 = ctypes.WinDLL("kernel32", use_last_error=True)
    k32.CreateMutexW.restype = ctypes.c_void_p
    k32.CreateMutexW.argtypes = [ctypes.c_void_p, ctypes.c_bool, ctypes.c_wchar_p]
    _MONITOR_MUTEX = k32.CreateMutexW(None, False, "Local\\OrbitLauncherSessionMonitor")
    return ctypes.get_last_error() != 183


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
    owns_monitor = acquire_monitor_lock()
    updater = None
    while True:
        settings = load_settings()
        started = start_roblox(settings, uri)
        if not started:
            return
        launch_time, updater = started
        if not owns_monitor or not SessionMonitor.wanted(settings):
            break
        monitor = SessionMonitor(settings, launch_time)
        try:
            monitor.run()
        except Exception:
            log("Session monitor crashed:\n" + traceback.format_exc())
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


def apply_pending_update(restart_args=()):
    version = pending_update()
    if not version or not is_frozen():
        return False
    try:
        swap_exe(UPDATE_DIR / "OrbitLauncher.exe", sys.executable)
        (UPDATE_DIR / "OrbitLauncher.exe").unlink(missing_ok=True)
        (UPDATE_DIR / "pending.json").unlink(missing_ok=True)
        log(f"Updated to {version}")
        subprocess.Popen([sys.executable, *restart_args])
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
        create_shortcut("Programs", APP_NAME, launch=False, exe=INSTALLED_EXE)
        if options.get("desktop", True):
            create_shortcut("Desktop", APP_NAME, launch=False, exe=INSTALLED_EXE)
        progress(.93, "Registering with Windows...")
        write_uninstall_entry(INSTALLED_EXE, version)
        settings = load_settings()
        if settings["registration"].get("registered"):
            register_protocols(settings, exe=INSTALLED_EXE)
    progress(1, "Done")
    log(f"Installed {version} to {INSTALL_DIR}")
    return {"version": version, "path": str(INSTALLED_EXE)}


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
    subprocess.run(["powershell", "-NoProfile", "-Command", ps], creationflags=CREATE_NO_WINDOW)
    _delete_tree(winreg.HKEY_CURRENT_USER, UNINSTALL_KEY)
    if u.MessageBoxW(None, "Also delete your Orbit settings, mod profiles and play time?", APP_NAME, 0x4 | 0x20) == 6:
        shutil.rmtree(DATA_DIR, ignore_errors=True)
    if is_frozen() and Path(sys.executable).parent.resolve() == INSTALL_DIR.resolve():
        subprocess.Popen(f'cmd /c ping 127.0.0.1 -n 3 > nul & rmdir /s /q "{INSTALL_DIR}"',
                         creationflags=CREATE_NO_WINDOW | 0x00000008)
    u.MessageBoxW(None, f"{APP_NAME} was uninstalled.", APP_NAME, 0x40)


def theme_colors(appearance):
    if appearance.get("mode") == "Light":
        c = dict(bg="#f3f0fb", panel="#ffffff", fg="#17122a", muted="#6a6386")
    else:
        c = dict(bg="#06040b", panel="#120e1f", fg="#f1edff", muted="#9c95b8")
    c["accent"] = ACCENTS.get(appearance.get("accent"), ACCENTS["Void"])[0]
    return c


def show_toast(title, body, seconds=7):
    import tkinter as tk
    c = theme_colors(load_settings()["appearance"])
    root = tk.Tk()
    root.overrideredirect(True)
    try:
        root.attributes("-topmost", True)
        root.attributes("-alpha", 0.0)
    except tk.TclError:
        pass
    root.configure(bg=c["accent"])
    inner = tk.Frame(root, bg=c["panel"])
    inner.pack(fill="both", expand=True, padx=(4, 0))
    tk.Label(inner, text=APP_NAME.upper(), bg=c["panel"], fg=c["accent"],
             font=("Segoe UI", 8, "bold")).pack(anchor="w", padx=14, pady=(12, 0))
    tk.Label(inner, text=title, bg=c["panel"], fg=c["fg"], font=("Segoe UI Semibold", 11),
             wraplength=290, justify="left").pack(anchor="w", padx=14)
    tk.Label(inner, text=body, bg=c["panel"], fg=c["muted"], font=("Segoe UI", 10),
             wraplength=290, justify="left").pack(anchor="w", padx=14, pady=(2, 14))
    root.update_idletasks()
    w, h = 330, root.winfo_reqheight()
    x, y = root.winfo_screenwidth() - w - 18, root.winfo_screenheight() - h - 58
    state = {"y": y + 30, "alpha": 0.0}

    def slide_in():
        state["y"] += (y - state["y"]) * 0.25
        state["alpha"] = min(0.97, state["alpha"] + 0.12)
        root.geometry(f"{w}x{h}+{x}+{int(state['y'])}")
        try:
            root.attributes("-alpha", state["alpha"])
        except tk.TclError:
            pass
        if abs(state["y"] - y) > 0.5 or state["alpha"] < 0.97:
            root.after(16, slide_in)

    def fade_out():
        state["alpha"] -= 0.08
        if state["alpha"] <= 0:
            root.destroy()
            return
        try:
            root.attributes("-alpha", state["alpha"])
        except tk.TclError:
            root.destroy()
            return
        root.after(16, fade_out)

    root.geometry(f"{w}x{h}+{x}+{state['y']}")
    for widget in (root, inner, *inner.winfo_children()):
        widget.bind("<Button-1>", lambda e: fade_out())
    slide_in()
    root.after(int(seconds * 1000), fade_out)
    root.mainloop()


def ui_file():
    base = Path(getattr(sys, "_MEIPASS", Path(__file__).resolve().parent))
    return base / "ui" / "index.html"


def app_icon_file():
    base = Path(getattr(sys, "_MEIPASS", Path(__file__).resolve().parent))
    return base / "ui" / "orbit.ico"


def copy_to_clipboard(text):
    if IS_WINDOWS:
        subprocess.run(["clip"], input=text.encode("utf-16-le"), creationflags=CREATE_NO_WINDOW)


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
            "credits": [{"role": r, "handle": h} for r, h in CREDITS],
            "ext_path": str(EXTENSIONS_DIR / EXTENSION_NAME),
            "mode": self._mode,
            "update_source": update_repo(),
            "pending_update": pending_update(),
            "frozen": is_frozen(),
            "setup": {"installed_version": installed_version(), "path": str(INSTALL_DIR)},
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
        if apply_pending_update():
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
            subprocess.Popen([str(INSTALLED_EXE)])
        self._window.destroy()

    def minimize(self):
        self._window.minimize()

    def close(self):
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


def run_gui(mode="app"):
    if mode == "app":
        settings = load_settings()
        if settings["updates"].get("auto", True) and apply_pending_update():
            return
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
    icon = app_icon_file()
    try:
        webview.start(debug=bool(os.environ.get("ORBIT_DEBUG")), icon=str(icon) if icon.exists() else None)
    except TypeError:
        webview.start(debug=bool(os.environ.get("ORBIT_DEBUG")))


def main():
    args = sys.argv[1:]
    setup_named = is_frozen() and "setup" in Path(sys.executable).stem.lower()
    if UNINSTALL_FLAG in args:
        run_uninstall()
    elif SETUP_FLAG in args or (setup_named and LAUNCH_FLAG not in args and TOAST_FLAG not in args):
        run_gui("setup")
    elif TOAST_FLAG in args:
        i = args.index(TOAST_FLAG)
        title = args[i + 1] if len(args) > i + 1 else APP_NAME
        body = args[i + 2] if len(args) > i + 2 else ""
        try:
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
        run_gui()


if __name__ == "__main__":
    main()
