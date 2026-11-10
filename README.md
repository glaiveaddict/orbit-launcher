# Orbit Launcher v2.16

A custom Roblox launcher for Windows, in the style of Bloxstrap.

**Credits**
- Founder/Owner - @stabzane
- Lead Developer - @stabzane
- Sounds/UI Designer - @stabzane
- Scripter - @stabzane

## The app
Orbit runs in its own app window with a black hole theme: a drifting starfield, an animated black hole on the Home page, purple-to-magenta glow accents, and glass panels that light up under your cursor. Pages slide in smoothly, and your settings save automatically as you change them.

Interactive bits:
- **Black hole**: hover over it and it spins up, pulls its disk inward and tilts toward your cursor. Click it for a flare.
- **Stars**: they drift with your mouse.
- **Feature cards** (hero, last server, stats, credits): they tilt in 3D under your cursor.
- **Launch button**: it's magnetic and leans toward your cursor.
- **Small touches**: the logo spins when you hover the title bar, credit avatars twirl, and game icons pop.

Accent colours (Appearance page): Void (default purple), Nebula, Pulsar, Quasar, Aurora and Solar, each in dark or light mode.

## Pages
- **Home**: launch Roblox, rejoin your last server, and make Roblox links from the website open through Orbit.
- **FastFlags**: allowlisted presets plus a box for extra flags in JSON. Use **Add game...** to give a game its own flag profile, like low graphics just for one laggy game.
- **Mods**: mod profiles. Each profile is its own folder of replacement files, and you switch between them from a dropdown. The originals are restored automatically.
- **Accounts**: save your Roblox accounts and switch between them in one click. Logins stay on your PC, encrypted with Windows.
- **Social**: your Orbit profile, Roblox friends who use Orbit (with one-click join), and a weekly and all-time playtime leaderboard.
- **Discord**: Rich Presence with the game name, icon and play timer, plus an optional Join button.
- **Session**: a server-location popup when you join, a play-time tracker with a stats table, and an offer to rejoin if Roblox closes mid-game.
- **Appearance**: dark or light theme, six accent colours, a custom icon on the Roblox window, and "Roblox (Orbit)" desktop and Start menu shortcuts.
- **Extensions**: installs the Orbit Item Preview browser extension.
- **Credits**

## Install & auto-updates (one-time setup, about 5 minutes)
GitHub builds Orbit for you and hosts the updates, so you never run `build.bat` or download zips again.

1. **Create the repo.** On github.com, click **New repository**, name it `orbit-launcher`, set it to **Public** (Orbit downloads updates without logging in, which needs a public repo), and click **Create repository**.
2. **Upload the files.** On the new repo page, click **uploading an existing file**. Drag in everything inside this folder, including the `.github` folder, then click **Commit changes**.
3. **Wait for the build.** Open the **Actions** tab, where "Build & release Orbit" runs for about 4 minutes. When it turns green, go to **Releases** and download **OrbitSetup.exe**.
4. **Install.** Run OrbitSetup.exe. Windows may say "Windows protected your PC" because the app isn't code-signed; click **More info** and then **Run anyway**. Setup installs Orbit to `%LOCALAPPDATA%\Programs\Orbit`, adds Start menu and desktop shortcuts, and opens it. Then right-click Orbit on your taskbar and choose **Pin to taskbar**.

That's it. From now on, Orbit checks for updates every time it opens:
- When a new version exists, it downloads in the background and a glowing **"vX ready · Restart"** button appears in the title bar.
- Click it to update right away, or ignore it and the update installs automatically the next time you open Orbit.
- You can turn auto-updates off, or check manually, on the **Credits** page under About & updates.

### Publishing a new version
1. Change `APP_VERSION` at the top of `orbit_launcher.py` (for example 1.5.0 → 1.6.0) and add a section to `CHANGELOG.md`.
2. Upload the changed files to the repo (**Add file → Upload files**).
3. GitHub builds and publishes the release, and every installed Orbit picks it up on its next launch.

### Uninstalling
Use Windows **Settings → Apps → Orbit Launcher → Uninstall**. It restores Roblox's normal link handler, removes the shortcuts, and asks whether to keep your settings.

### Running without installing
- **From source:** install Python 3.10–3.13 and run `orbit_launcher.py`. The first run offers to install `pywebview`.
- **Local .exe:** `build.bat` makes a local .exe. Copies built that way can't auto-update, because only the GitHub build knows where to look for updates.

## Good to know
- Since September 2025, Roblox ignores FastFlags that aren't on its allowlist, so FPS-unlock flags do nothing. Use the in-game **Maximum Frame Rate** setting instead.
- Game flag profiles apply when you join that game from the website or with Rejoin. Teleporting between games inside Roblox keeps the flags you launched with.
- Session features (popup, play time, crash rejoin, Discord, window icon) only work when Roblox is started through Orbit.
- The server popup looks up the server's IP on ipinfo.io. It can't show over exclusive fullscreen.
- If you leave a game by closing the window instead of using Leave, Orbit may still offer to rejoin. Just click No.
- Discord status and the session features read Roblox's log files. If a Roblox update changes the log format, the patterns at the top of the session section need updating.
- Updating from v1.0: your old Mods folder becomes the "Default" mod profile automatically.
- Everything is stored in `%LOCALAPPDATA%\OrbitLauncher`.
