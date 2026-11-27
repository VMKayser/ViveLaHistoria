#!/usr/bin/env python3
"""Inventario de metadatos internos (fechas, programa de origen, autoría y licencia) de los recursos incluidos.

No modifica ningún archivo: solo informa. Las fechas previas a la incorporación son procedencia legítima del
recurso (se desarrolló antes en el repositorio anterior) y se conservan.

Uso: python3 -I migracion/metadatos.py [raíz]   → migracion/metadatos.json y resumen por pantalla.
"""
import datetime, json, re, struct, subprocess, sys, zlib
from collections import Counter
from pathlib import Path

RAIZ = Path(sys.argv[1] if len(sys.argv) > 1 else Path(__file__).resolve().parents[1])
FECHA = re.compile(r"(19|20)\d\d[-:/](0[1-9]|1[0-2])[-:/](0[1-9]|[12]\d|3[01])")


def png(b):
    out, i = {}, 8
    while i + 8 <= len(b):
        n, t = struct.unpack(">I4s", b[i:i + 8]); d = b[i + 8:i + 8 + n]; i += 12 + n
        if t == b"tIME":
            out["tIME"] = "%04d-%02d-%02d %02d:%02d:%02d" % struct.unpack(">HBBBBB", d)
        elif t in (b"tEXt", b"zTXt", b"iTXt"):
            k, _, v = d.partition(b"\0")
            if t == b"zTXt": v = zlib.decompress(v[1:])
            elif t == b"iTXt": v = v.split(b"\0", 3)[-1] if v.count(b"\0") >= 3 else v
            out[k.decode("latin1")] = v.decode("utf8", "replace")[:200]
        elif t == b"eXIf":
            out["eXIf"] = len(d)
        if t == b"IEND": break
    return out


def exif(ruta):
    try:
        from PIL import Image
        with Image.open(ruta) as im:
            ex = im.getexif()
            tags = {0x0132: "DateTime", 0x0131: "Software", 0x013B: "Artist", 0x8298: "Copyright", 0x010F: "Make", 0x0110: "Model"}
            out = {v: str(ex.get(k)) for k, v in tags.items() if ex.get(k)}
            sub = ex.get_ifd(0x8769)
            for k, v in ((0x9003, "DateTimeOriginal"), (0x9004, "DateTimeDigitized")):
                if sub.get(k): out[v] = str(sub.get(k))
            if ex.get_ifd(0x8825): out["GPS"] = "sí"
            if "xmp" in im.info or b"http://ns.adobe.com/xap" in Path(ruta).read_bytes()[:200000]: out["XMP"] = "sí"
            return out
    except Exception as e:
        return {"error": str(e)[:80]}


def glb(b):
    if b[:4] != b"glTF": return {}
    n = struct.unpack("<I", b[12:16])[0]
    j = json.loads(b[20:20 + n])
    a = j.get("asset", {})
    out = {k: a[k] for k in ("generator", "copyright") if k in a}
    if a.get("extras"): out["extras"] = str(a["extras"])[:200]
    txt = json.dumps(j.get("extras", {})) + json.dumps([x.get("extras", {}) for x in j.get("scenes", [])])
    if FECHA.search(txt): out["fecha_en_extras"] = FECHA.search(txt).group(0)
    return out


def gltf(t):
    j = json.loads(t); a = j.get("asset", {})
    return {k: a[k] for k in ("generator", "copyright") if k in a}


def ttf(b):
    try:
        n = struct.unpack(">H", b[4:6])[0]
        for i in range(n):
            tag, _, off, _ = struct.unpack(">4sIII", b[12 + 16 * i:28 + 16 * i])
            if tag == b"head":
                c, m = struct.unpack(">qq", b[off + 20:off + 36])
                base = datetime.datetime(1904, 1, 1)
                return {"head.created": str(base + datetime.timedelta(seconds=c)), "head.modified": str(base + datetime.timedelta(seconds=m))}
    except Exception:
        pass
    return {}


def audio(ruta):
    try:
        r = subprocess.run(["ffprobe", "-v", "quiet", "-print_format", "json", "-show_format", str(ruta)], capture_output=True, text=True, timeout=20)
        return {k: v for k, v in json.loads(r.stdout).get("format", {}).get("tags", {}).items()}
    except Exception as e:
        return {"error": str(e)[:80]}


def blend(b):
    return {"cabecera": b[:12].decode("latin1", "replace")} if b[:7] == b"BLENDER" else {"cabecera": "comprimido"}


def analizar(ruta):
    suf = ruta.suffix.lower()
    if suf == ".png": return png(ruta.read_bytes())
    if suf in (".jpg", ".jpeg", ".webp"): return exif(ruta)
    if suf == ".glb": return glb(ruta.read_bytes()[:4_000_000])
    if suf == ".gltf": return gltf(ruta.read_text(errors="ignore"))
    if suf in (".ttf", ".otf"): return ttf(ruta.read_bytes())
    if suf in (".mp3", ".ogg", ".wav", ".opus"): return audio(ruta)
    if suf == ".blend": return blend(ruta.read_bytes()[:12])
    return None


def main():
    man = json.loads((Path(__file__).resolve().parent / "manifiesto.json").read_text())
    rep, con_fecha, programas, faltan = {}, [], Counter(), []
    for a in man["archivos"]:
        f = RAIZ / a["ruta"]
        if not f.exists():
            faltan.append(a["ruta"]); continue
        if f.read_bytes()[:40].startswith(b"version https://git-lfs"):
            rep[a["ruta"]] = {"error": "puntero LFS sin descargar (correr git lfs pull)"}; continue
        m = analizar(f)
        if m is None: continue
        rep[a["ruta"]] = m
        txt = json.dumps(m, ensure_ascii=False)
        if FECHA.search(txt) or "tIME" in m or "DateTime" in txt or "date" in txt.lower() or "head.created" in m:
            con_fecha.append(a["ruta"])
        for k in ("generator", "Software", "software", "encoder", "Software"):
            if k in m: programas[str(m[k])[:60]] += 1
    salida = {"generado": datetime.datetime.now().astimezone().isoformat(timespec="seconds"),
              "nota": "Inventario: no se modificó ningún archivo. Las fechas internas previas son procedencia.",
              "con_fecha_interna": len(con_fecha), "programas_de_origen": programas.most_common(), "faltan": faltan,
              "archivos": rep}
    (RAIZ / "migracion").mkdir(exist_ok=True)
    (RAIZ / "migracion" / "metadatos.json").write_text(json.dumps(salida, ensure_ascii=False, indent=1))
    print(f"analizados {len(rep)} · con fecha interna {len(con_fecha)} · faltan {len(faltan)}")
    for p, n in programas.most_common(12): print(f"  {n:4d} {p}")
    años = Counter(FECHA.search(json.dumps(rep[r])).group(0)[:7] for r in con_fecha if FECHA.search(json.dumps(rep[r])))
    print("  fechas internas por mes:", dict(sorted(años.items())))


if __name__ == "__main__":
    main()
