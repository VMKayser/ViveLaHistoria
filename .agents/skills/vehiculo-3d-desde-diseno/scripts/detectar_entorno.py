#!/usr/bin/env python3
"""Detecta binarios de Blender, Node, GPU, memoria libre y sesiones activas sin rutas fijas."""
import glob
import json
import os
import shutil
import subprocess
from pathlib import Path


def buscar_blender():
    env_bin = os.environ.get("BLENDER_BIN")
    if env_bin and Path(env_bin).is_file():
        return env_bin
    en_path = shutil.which("blender")
    if en_path:
        return en_path
    home = Path.home()
    patrones = [
        str(home / "apps" / "blender*" / "blender"),
        "/opt/blender*/blender",
        "/snap/bin/blender",
        "/Applications/Blender.app/Contents/MacOS/Blender",
    ]
    candidatos = []
    for p in patrones:
        candidatos.extend(glob.glob(p))
    candidatos = [c for c in sorted(candidatos, reverse=True) if Path(c).is_file()]
    return candidatos[0] if candidatos else None


def memoria_gib():
    meminfo = Path("/proc/meminfo")
    if not meminfo.exists():
        return {}
    datos = {}
    for linea in meminfo.read_text().splitlines():
        if ":" in linea:
            k, v = linea.split(":", 1)
            partes = v.strip().split()
            if partes and partes[0].isdigit():
                datos[k] = round(int(partes[0]) / (1024 * 1024), 2)
    return {
        "total_gib": datos.get("MemTotal"),
        "disponible_gib": datos.get("MemAvailable"),
    }


def procesos_blender_activos():
    try:
        salida = subprocess.check_output(["ps", "-eo", "pid,comm,args"], text=True)
    except Exception:
        return []
    activos = []
    for linea in salida.splitlines()[1:]:
        partes = linea.strip().split(None, 2)
        if len(partes) >= 2 and "blender" in partes[1].lower():
            activos.append({"pid": int(partes[0]), "comando": partes[2] if len(partes) > 2 else partes[1]})
    return activos


def detectar_gpu():
    nvidia = shutil.which("nvidia-smi")
    if not nvidia:
        return {"nvidia": False}
    try:
        out = subprocess.check_output(
            [nvidia, "--query-gpu=name,memory.total", "--format=csv,noheader"],
            text=True,
            timeout=3,
        ).strip()
        return {
            "nvidia": bool(out),
            "detalle": out,
            "prefijo_render": "__NV_PRIME_RENDER_OFFLOAD=1 __GLX_VENDOR_LIBRARY_NAME=nvidia",
        }
    except Exception:
        return {"nvidia": False}


def buscar_dependencias_web(inicio: Path):
    actual = inicio.resolve()
    for base in [actual, *actual.parents]:
        for candidato in [base / "package.json", base / "web" / "package.json"]:
            if candidato.is_file():
                nm = candidato.parent / "node_modules"
                return {
                    "package_json": str(candidato),
                    "three": (nm / "three").is_dir(),
                    "gltf_validator": (nm / "gltf-validator").is_dir(),
                    "webpack_next": (nm / "next" / "dist" / "compiled" / "webpack").is_dir(),
                }
    return {}


def main():
    mem = memoria_gib()
    blenders = procesos_blender_activos()
    hilos_recomendados = 2 if (mem.get("disponible_gib") or 8) < 4 or blenders else 4
    informe = {
        "blender": buscar_blender(),
        "node": shutil.which("node"),
        "python": shutil.which("python3"),
        "gpu": detectar_gpu(),
        "memoria": mem,
        "procesos_blender_activos": blenders,
        "hilos_blender_recomendados": hilos_recomendados,
        "dependencias_web": buscar_dependencias_web(Path.cwd()),
    }
    print(json.dumps(informe, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
