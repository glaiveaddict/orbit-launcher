# Changelog

## v2.1.1
- **Fix: PC freezing when you tab out of Roblox.** The Unlimited frame rate option let Roblox push your graphics card so hard (especially on loading screens and teleports) that Windows couldn't draw the desktop or other apps. Unlimited is gone: the highest cap is now 240 (Roblox's own maximum), and anyone who had Unlimited is moved to 240 automatically, even if they launch Roblox without Orbit.
- **Overlays step aside properly:** the server badge and keystrokes overlay now fully hide whenever Roblox isn't the window in front, instead of staying as invisible always-on-top windows, and no longer re-assert "always on top" several times a second.
- Orbit's background helpers run at normal priority again.

## v2.1.0
- **Crosshair maker:** design your own shift-lock crosshair on the Mods page. Pick a style (cross, dot, circle, T or X), color, length, gap, thickness, outline, opacity and center dot, with a live preview over a BedWars-style map. Save it and use it everywhere or for one game.
- **Per-game crosshairs:** every game in your Library can have its own crosshair. It switches in when you launch that game from Orbit and switches back for everything else. The BedWars kit now uses this too.
- **Roblox updates ahead of time:** when Roblox releases an update, Orbit downloads and installs it in the background while Roblox is closed, so launching never sits on Roblox's "Updating" screen. Every file is checked, and if Roblox ever changes how its update is packaged, Orbit steps aside and lets Roblox update itself. Status is on the Health page.
- **Keystrokes and clicks overlay:** W A S D, Space and your mouse buttons light up on the Roblox screen, with clicks per second. Turn it on in Stats and pick a corner.
- **Daily play goal:** pick 1 to 6 hours. A progress ring at the top of Stats shows today's time, and a popup lets you know when you reach it.
- **Theme gallery:** eight ready-made looks in Appearance, including Neon Tokyo, Bed Wars, Emerald, Inferno, Glacier, Gold Rush and Sakura.
- **Fix:** the Library could show each game twice when it refreshed.

## v2.0.0
- **Much faster:** the server location popup, the in-game badge and launching Roblox from the website no longer wait for the whole app to unpack every time. Orbit now keeps a small, always-ready helper for this background work, so they start almost instantly.
- **Location in about a second:** Orbit looks up the server as soon as Roblox connects instead of waiting, remembers server locations and game names it has seen before, and shows the badge together with the popup instead of 7 seconds later.
- **Your Roblox avatar in Credits:** @stabzane's credits now show the real Roblox avatar, refreshed with every Orbit update (and every few hours). Click it to open the profile.
- **Shift-lock crosshairs:** 6 new high-visibility crosshairs (Cyan Cross, Green Plus, Red Dot, Circle Dot, Yellow T, Pink Chevron) with dark outlines so they stay visible on bright skies and wool. They replace the crosshair you see in shift lock and first person.
- **More cursors:** Neon Arrow, Big Cyan Dot and Green Ring.
- **BedWars kit:** one click on the Boost page gives BedWars its own FPS-focused profile (low textures and lighting, no grass, low-detail meshes, Direct3D 11), installs the crosshair you pick and adds BedWars to your Library.
- Packs on the Mods page are now split into Crosshairs, Cursors and Sounds.

## v1.9.1
- **Fix:** the server badge and live tracking could stop working with FPS Boost on. With Roblox on high priority and an unlimited frame rate, Windows' own tools slowed down so much that Orbit mistook its tracker for a dead one and replaced it, and the badge never got drawn. Orbit now checks processes directly (instantly, no slow Windows tools) and keeps its own badge and tracker responsive.
- **Gentler priority:** Roblox now gets above-normal priority instead of high, so your PC, Discord and overlays stay smooth.
- A warning on the Boost page when the frame rate cap is set to Unlimited.

## v1.9.0
- **FPS Boost:** one button on the Boost page sets Roblox and Windows up for the most frames. It switches to performance-friendly graphics flags, sets Roblox's own frame rate cap and graphics quality, gives Roblox high priority and the high performance power plan, runs it on your fastest GPU, turns on Game Mode and turns off Xbox background recording. Pick Max FPS or Balanced. Turning it off puts every old setting back.
- **Fine-tune:** choose a frame rate cap (60, 144, 240 or unlimited) and Roblox graphics quality yourself, and toggle each Windows tweak on its own.
- **Quick presets:** Potato, Balanced, Quality or Reset on the FastFlags page, per game too.
- **Smart join:** Play buttons can pick the open server with the best ping.
- **Region hopper:** pick a region (US East, Europe, Asia...) and Orbit hops through servers until it lands in one there.
- **Ping history:** every session records your ping. Game pages show a ping graph and your average ping per server location.
- **Crash reader:** when Roblox crashes or kicks you, Orbit reads the log and explains why (lost connection, graphics driver, out of memory, error codes) in Health > Recent problems.
- **Roblox update watch:** when Roblox updates, Orbit puts your FastFlags and mods back automatically and lets you know.
- **Share your setup:** copy a theme code for friends, and export or import mod profiles as .orbitpack files.
- **Screenshot sorting:** move screenshots into folders by game, automatically after each session if you like, and filter by game.
- **Interface size:** Compact, Normal or Large.
- **Mini player:** a small always-on-top window with the game, server location, ping, timer, Rejoin and New server. Open it with the button at the top.
- **Fix:** turning off the startup animation no longer leaves a blank screen.

## v1.8.0
- **Live ping and session timer on the server badge:** see your ping to the server (green, yellow or red) and how long you've been in it, right on the Roblox screen. Both can be turned off in Stats.
- **Health page:** checks that Roblox, links, overlays, tracking and the background helper are all working, with a Fix button for anything that isn't.
- **Repair tools:** clear Roblox's cache, put Roblox back to stock, reset your FastFlags, or reinstall Roblox with the official installer.
- **Global hotkeys:** Ctrl+Alt+R rejoins, Ctrl+Alt+N hops to a new server, Ctrl+Alt+B shows or hides the badge, Ctrl+Alt+O opens Orbit. Works while you're in game.
- **Saved servers:** star any server in your history and join it again from the Library.
- **Play calendar:** a heatmap of the last six months with your current and best streak.
- **Game pages:** click any game in Stats or the Library for its total time, longest session, favorite server locations and session history.
- **Break reminders:** optional popup after 30 minutes to 2 hours of play.
- **Custom accent color:** pick your own two colors. The in-game badge and banner use them too.
- **Orbit packs:** original cursors and death sounds you can preview and install in one click from Mods.
- **Startup animation:** a quick black hole intro when Orbit opens (can be turned off in Appearance).

## v1.7.3
- **Fix:** the server badge now appears where you choose (top right by default) instead of getting stuck in the top-left corner behind Roblox's menu button.

## v1.7.2
- Internal: better on-screen checks for the server badge in the automatic Windows tests.

## v1.7.1
- **Fix:** the server badge now recovers from drawing errors instead of silently staying invisible, and logs where it places itself.

## v1.7.0
- **Works however you open Roblox:** while Orbit is open, it notices Roblox running and turns on tracking, the location banner and the server badge, even if you started Roblox from its own app or another launcher.
- **Start with Windows (optional):** a tiny background helper with no window, so all of this works even when Orbit is closed. Turn it on in Stats.
- **Link guard:** if another launcher takes over the Roblox Play links, Orbit switches them back.
- **New server badge:** smaller and on the side of the Roblox window, below Roblox's top bar, and it follows the window. Choose top left, top right, bottom left, bottom right or center, in Small (location only) or Normal (with the game name).

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
