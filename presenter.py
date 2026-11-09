import ctypes, time, tkinter as tk
from ctypes import wintypes as w
root = tk.Tk(); root.title("Roblox"); root.geometry("640x360+50+50"); root.update()
hwnd = root.winfo_id()
class MODE(ctypes.Structure): _fields_ = [("W", w.UINT), ("H", w.UINT), ("Num", w.UINT), ("Den", w.UINT), ("Fmt", w.UINT), ("Scan", w.UINT), ("Scale", w.UINT)]
class DESC(ctypes.Structure): _fields_ = [("Buf", MODE), ("Count", w.UINT), ("Quality", w.UINT), ("Usage", w.UINT), ("BufCount", w.UINT), ("Wnd", ctypes.c_void_p), ("Windowed", w.BOOL), ("Swap", w.UINT), ("Flags", w.UINT)]
d = DESC(MODE(640, 360, 60, 1, 28, 0, 0), 1, 0, 0x20, 1, hwnd, 1, 0, 0)
sc, dev, ctx, fl = ctypes.c_void_p(), ctypes.c_void_p(), ctypes.c_void_p(), ctypes.c_uint()
hr = ctypes.windll.d3d11.D3D11CreateDeviceAndSwapChain(None, 5, None, 0, None, 0, 7, ctypes.byref(d), ctypes.byref(sc), ctypes.byref(dev), ctypes.byref(fl), ctypes.byref(ctx))
print("create hr", hex(hr & 0xffffffff), flush=True)
vt = ctypes.cast(ctypes.cast(sc, ctypes.POINTER(ctypes.c_void_p))[0], ctypes.POINTER(ctypes.c_void_p))
present = ctypes.WINFUNCTYPE(ctypes.c_long, ctypes.c_void_p, w.UINT, w.UINT)(vt[8])
end = time.time() + 60
n = 0
while time.time() < end:
    present(sc, 1, 0); n += 1
    root.update()
print("presented", n, flush=True)
