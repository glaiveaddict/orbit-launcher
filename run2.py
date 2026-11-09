import os, sys, time, shutil, subprocess, importlib.util, glob
from pathlib import Path
spec = importlib.util.spec_from_file_location("ol", "orbit_launcher.py"); ol = importlib.util.module_from_spec(spec); spec.loader.exec_module(ol)
ol.ensure_dirs()
fake = Path(sys.executable).with_name("RobloxPlayerBeta.exe"); shutil.copy(sys.executable, fake)
p = subprocess.Popen([str(fake), "presenter.py"]); time.sleep(4)
url, name = ol.github_asset("GameTechDev/PresentMon", r"PresentMon-\d+\.\d+\.\d+-x64\.exe"); ol.download_file(url, ol.PRESENTMON); print("got", name)
pm = str(ol.PRESENTMON)
print(subprocess.run([pm, "--help"], capture_output=True, text=True, timeout=20).stdout[:3500])
tests = {
 "all": ["--output_file", "all.csv", "--stop_existing_session", "--session_name", "T1", "--no_console_stats", "--timed", "6", "--terminate_after_timed"],
 "named": ["--process_name", "RobloxPlayerBeta.exe", "--output_file", "named.csv", "--stop_existing_session", "--session_name", "T2", "--no_console_stats", "--timed", "6", "--terminate_after_timed"],
 "v1": ["--process_name", "RobloxPlayerBeta.exe", "--output_file", "v1.csv", "--stop_existing_session", "--session_name", "T3", "--no_console_stats", "--v1_metrics", "--timed", "6", "--terminate_after_timed"],
}
for k, a in tests.items():
    r = subprocess.run([pm, *a], capture_output=True, text=True, timeout=40)
    print("==", k, "rc", r.returncode, "out:", r.stdout[-600:], "err:", r.stderr[-600:])
    print("files:", glob.glob("*.csv"))
    for f in glob.glob(k + "*.csv"):
        lines = open(f, errors="ignore").read().splitlines()
        print(f, len(lines), "lines"); print("\n".join(lines[:3]))
        if k == "all": print("apps:", sorted({l.split(",")[0] for l in lines[1:]})[:20])
p.kill()
