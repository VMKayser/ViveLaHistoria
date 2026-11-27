#!/usr/bin/env python3
"""Copia al repositorio nuevo, byte a byte, los archivos de UN PR del manifiesto y verifica su huella.

Uso (desde la raíz del repo NUEVO, en la rama del PR):
  python3 -I migracion/incorporar.py PR04 --origen ../miCiudadCharcas [--local /ruta/al/miCIudad]

--origen: clon del repositorio anterior (basta `git clone --depth 1`; el script trae lo que falte de develop).
--local : solo ManuelRUa; carpeta de trabajo con los archivos que no están en ningún repositorio.
No hace git add ni commit: eso lo hace la persona responsable (ver MIGRATION_PLAN.md).
"""
import argparse, json, subprocess, sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[1]


def git(origen, *args, entrada=None):
    return subprocess.run(["git", "-C", str(origen), *args], capture_output=True, check=False, input=entrada)


def blob(origen, oid, commit):
    r = git(origen, "cat-file", "blob", oid)
    if r.returncode != 0:  # clon superficial: traer el commit que lo contiene
        git(origen, "fetch", "--depth", "1", "origin", commit)
        r = git(origen, "cat-file", "blob", oid)
    if r.returncode != 0:
        sys.exit(f"No encuentro el objeto {oid} en {origen}: ¿es un clon de {MAN['repo_anterior']}?")
    return r.stdout


def huella(ruta):
    return subprocess.run(["git", "hash-object", "--no-filters", "--", str(ruta)], capture_output=True, text=True, check=True).stdout.strip()


MAN = json.loads((RAIZ / "migracion" / "manifiesto.json").read_text())


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("pr")
    ap.add_argument("--origen", required=True, type=Path)
    ap.add_argument("--local", type=Path)
    ap.add_argument("--destino", type=Path, default=RAIZ, help="raíz del repo nuevo (por defecto, la de este script)")
    a = ap.parse_args()
    destino_raiz = a.destino.resolve()
    lista = [x for x in MAN["archivos"] if x["pr"] == a.pr]
    if not lista:
        sys.exit(f"{a.pr} no tiene archivos en el manifiesto")
    malos = 0
    for x in lista:
        dest = destino_raiz / x["ruta"]
        dest.parent.mkdir(parents=True, exist_ok=True)
        fuente = x["fuente"]
        if fuente.startswith("local:"):
            if not a.local:
                sys.exit(f"{x['ruta']} solo existe en el equipo de {fuente[6:]}: hace falta --local")
            datos = (a.local / x["ruta"]).read_bytes()
        else:
            datos = blob(a.origen, x["oid"], fuente[4:])
        dest.write_bytes(datos)
        dest.chmod(0o755 if x.get("modo") == "100755" else 0o644)
        if huella(dest) != x["oid"]:
            print("HUELLA DISTINTA:", x["ruta"]); malos += 1
    mb = sum(x["bytes"] for x in lista) / 1e6
    print(f"{a.pr}: {len(lista)} archivos, {mb:.1f} MB copiados; huellas distintas: {malos}")
    sys.exit(1 if malos else 0)


if __name__ == "__main__":
    main()
