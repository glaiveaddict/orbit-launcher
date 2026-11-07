# Changelog

## v1.6.9
- **Fix:** live tracking works again. v1.6.7 mistook real Roblox game logs for short helper logs and ignored them, so nothing showed during play.
- **Now playing card:** Home shows the game you're in, its server location and a live timer while you play.
- **Fix:** you now get the location banner even when Orbit attaches to a game that's already running.
- **Exclusive fullscreen warning:** Home and Stats tell you when exclusive fullscreen is blocking overlays, with a one-click fix.
- **Fix:** tracker processes left behind by very old Orbit versions (including script versions) are now shut down too.

## v1.6.8
- **The X button now fully closes Orbit.** No more hunting for the tray icon to quit.
- **Updates install when you close:** if an update has finished downloading, closing Orbit installs it, so the next time you open Orbit it's already on the new version.
- Want the old behavior back? Turn on **Close to the system tray** in Appearance.

## v1.6.7
- **Server badge:** a small pill at the top of your screen shows the game and server location for as long as you're in that server. Clicks pass through it, and it hides when you tab out of Roblox. Turn it off in Stats.
- **Fix:** old background trackers are now always replaced, even on PCs where Windows' process info service (WMI) doesn't respond. If one still won't let go, Orbit tracks your session anyway.

## v1.6.6
- **Fix:** Orbit now stays connected after you press **Launch Roblox**. Games you pick inside Roblox afterwards are tracked, including teleports between places.
- **Fix:** Orbit follows the real game log instead of the short helper log Roblox creates when you join from the website while Roblox is already open.
- **Fix:** old background trackers are replaced right away, so Launch no longer waits about 15 seconds.
- **Fix:** if Orbit starts while you're already in a game, it picks up that game and its play time from when you actually joined.
- **New location popup:** a banner slides down at the top of the screen when you join a server. It never takes focus away from Roblox.

## v1.6.5
- **Fix:** restarting after an update no longer shows "Orbit couldn't open its window" or "Failed to remove temporary directory". Each copy of Orbit now starts with its own clean files.
- **Fix:** closing Orbit while you're in a game no longer breaks session tracking.

## v1.6.4
- **Fix:** the title bar (minimize, maximize and close) is no longer cut off at the top of the window. The maximize button still makes Orbit fill the screen.

## v1.6.3
- **Fix:** the server location popup and stats now work even if an older copy of Orbit was still running. Orbit shuts down stale copies and takes over tracking.
- **Fix:** Orbit ignores Roblox's crash-handler log and always follows the real game log.
- **Live stats:** Home, Stats and Achievements refresh on their own while Orbit is open.

## v1.6.2
- **Setup fix:** setup no longer fails with "cannot find the file specified" on PCs where PowerShell isn't on the system PATH. Orbit now finds Windows tools directly.
- **Setup fix:** if a shortcut can't be created, setup still finishes and tells you.
- **Maximize:** Orbit and the installer can be maximized with the new title bar button or by double-clicking the title bar.

## v1.6.1
- **Fixes:** Orbit now logs every startup step and any window error, which makes problems much easier to track down.
- **Fixes:** session tracking no longer picks Roblox's crash-handler log by mistake.
- **Fixes:** every release is now tested on a real Windows machine before it's published.

## v1.6.0
- **Game library:** pin your favorite games with big thumbnails. One click plays them, and each game can use its own FastFlags and mod pack.
- **Server finder:** see every open server with player counts, ping and FPS, then join the emptiest server or the best ping.
- **Recent servers:** your last servers on the Home page, ready to rejoin.
- **Stats:** a weekly recap you can save as an image, plus a full session history with server locations.
- **Achievements:** 15 badges that unlock as you play, with a little celebration.
- **Screenshots:** your Roblox screenshots in a gallery with a full-size viewer.
- **Boost:** high priority for Roblox, a high performance power plan, and apps that open (and close) with Roblox.
- **Command palette:** press Ctrl+K to search pages, games and actions.
- **Sounds and backgrounds:** launch sound packs, a warp-speed background, nebula mode, or your own image.
- **System tray:** Orbit stays by the clock with quick Launch, Rejoin and Library options.
- **Backup & restore:** move all your settings, profiles, mods and stats to another PC in one file.

## v1.5.0
- **Installer:** OrbitSetup.exe installs Orbit for you, with no admin needed. It adds Start menu and desktop shortcuts and puts an uninstall entry in Windows Settings > Apps.
- **Auto-updates:** Orbit checks GitHub when it opens and downloads new versions in the background. A glowing button in the title bar installs them, and if you skip it they install the next time you open Orbit.
- **About & updates card** on the Credits page, with an auto-update switch and a "Check for updates" button.

## v1.4.0
- Hover effects: the black hole spins up, tilts toward your cursor and flares when you click it. The stars drift with your mouse, cards tilt in 3D, and the Launch button leans toward your cursor.

## v1.3.0
- Purple black hole theme: starfield, an animated accretion disk, glass panels and new accent colours.

## v1.2.0
- New app window with animations, plus an app icon you can pin to the taskbar.

## v1.1.0
- Mod profiles, per-game FastFlags, server location popup, rejoin last server, play-time tracking, crash rejoin, custom Roblox icon, themes and Credits.

## v1.0.0
- First release: FastFlags, mods, Roblox link handling and Discord Rich Presence.
