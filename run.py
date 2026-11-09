import os, sys, time, shutil, subprocess, importlib.util
from pathlib import Path
spec = importlib.util.spec_from_file_location("ol", "orbit_launcher.py"); ol = importlib.util.module_from_spec(spec); spec.loader.exec_module(ol)
ol.ensure_dirs()
fake = Path(sys.executable).with_name("RobloxPlayerBeta.exe"); shutil.copy(sys.executable, fake)
p = subprocess.Popen([str(fake), "presenter.py"])
time.sleep(4)
print("fps_ready before:", ol.fps_ready())
t = ol.FpsTracker(); ok = t.start(); print("tracker start:", ok, "tool:", ol.PRESENTMON.exists())
for i in range(12):
    time.sleep(1); t.poll({"place_id": "1"})
    live = ol.load_json(ol.FPS_LIVE_FILE, None); print("live", i, live, "cols", (t.cols or [])[:12] if i == 0 else "")
print("all cols:", t.cols)
print("summary:", {k: v for k, v in t.summary().items() if k != "samples"})
print("status:", ol.load_json(ol.DATA_DIR / "fps_status.json", {}))
t.stop(); p.kill()
print("log tail:", ol.LOG_FILE.read_text(errors="ignore")[-800:])
