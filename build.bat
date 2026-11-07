@echo off

python -m pip install --upgrade pyinstaller pywebview
if errorlevel 1 goto :fail

python -m PyInstaller --noconfirm --onefile --noconsole --name OrbitLauncher --icon ui\orbit.ico ^
  --add-data "ui;ui" --add-data "orbit_preview;orbit_preview" orbit_launcher.py
if errorlevel 1 goto :fail

echo.
echo Done! Your app is at dist\OrbitLauncher.exe
echo Move it somewhere permanent (e.g. Documents\Orbit), open it, then right-click its
echo taskbar icon and choose "Pin to taskbar".
pause
exit /b 0

:fail
echo.
echo Build failed - see the messages above.
pause
exit /b 1
