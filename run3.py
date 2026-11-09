import json, urllib.request, zipfile, io
from PIL import Image
get = lambda u: urllib.request.urlopen(urllib.request.Request(u, headers={"User-Agent": "Mozilla/5.0"}), timeout=60).read()
ver = json.loads(get("https://clientsettings.roblox.com/v2/client-version/WindowsPlayer"))["clientVersionUpload"]
z = zipfile.ZipFile(io.BytesIO(get(f"https://setup.rbxcdn.com/{ver}-content-sky.zip")))
for n in z.namelist():
    d = z.read(n); info = ""
    try:
        im = Image.open(io.BytesIO(d)); info = f"{im.format} {im.size} {im.mode}"
    except Exception as e:
        info = d[:4]
    print("SKYPKG", n, len(d), info)
import os
os.makedirs("out", exist_ok=True)
for n in z.namelist():
    if n.lower().endswith((".jpg", ".png")):
        open(os.path.join("out", n.replace("/", "_")), "wb").write(z.read(n))
