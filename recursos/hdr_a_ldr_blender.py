# Blender -b -P hdr_a_ldr.py -- entrada.hdr salida.ppm exposicion  -> imprime JSON con la posición del sol (u,v) y su elevación
import bpy, sys, json, math
import numpy as np
ent, sal, expo = sys.argv[sys.argv.index("--") + 1:][:3]
expo = float(expo)
img = bpy.data.images.load(ent)
w, h = img.size
a = np.array(img.pixels[:], dtype=np.float32).reshape(h, w, 4)[:, :, :3]   # fila 0 = abajo
lum = a @ np.array([0.2126, 0.7152, 0.0722], dtype=np.float32)
# sol: centroide de los píxeles más brillantes (ponderado por ángulo sólido)
v_idx = (np.arange(h) + 0.5) / h
omega = np.cos((v_idx - 0.5) * math.pi)[:, None]
umbral = lum.max() * 0.5
m = (lum >= umbral) * omega
ys, xs = np.mgrid[0:h, 0:w]
sw = m.sum()
u = float((m * (xs + 0.5)).sum() / sw / w)
v = float((m * (ys + 0.5)).sum() / sw / h)          # v=1 arriba
elev = (v - 0.5) * 180.0
# curva de tonos tipo ACES (Narkowicz) y a sRGB
x = a * expo
t = np.clip((x * (2.51 * x + 0.03)) / (x * (2.43 * x + 0.59) + 0.14), 0, 1)
s = np.where(t <= 0.0031308, t * 12.92, 1.055 * np.power(t, 1 / 2.4) - 0.055)
out = (np.clip(s, 0, 1) * 255 + 0.5).astype(np.uint8)[::-1]   # arriba primero
with open(sal, "wb") as f:
    f.write(b"P6\n%d %d\n255\n" % (w, h)); f.write(out.tobytes())
print("SOL " + json.dumps({"u": round(u, 4), "v": round(v, 4), "elevacion_grados": round(elev, 2), "pico": float(lum.max()), "media_cielo": float(lum[h//2:].mean())}))
