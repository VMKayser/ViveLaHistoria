#!/usr/bin/env python3
"""Arma el texto de una tanda de lectura en un solo archivo.

Uso: python3 contenido/herramientas/tanda.py 13 42 salida.txt [--encima 24-28,33-44]

Las páginas normales van completas (párrafos unidos en una línea). Las páginas "por encima" van solo con su primer
párrafo y los párrafos que nombran Chuquisaca/La Plata o un lugar de alias.json, marcadas [POR ENCIMA].
"""
import json
import re
import sys
import unicodedata
from pathlib import Path

BASE = Path(__file__).resolve().parent.parent
PAG = BASE / "libro" / "paginas"


def sin_tildes(s):
    return "".join(c for c in unicodedata.normalize("NFD", s.lower()) if unicodedata.category(c) != "Mn")


def parrafos(texto):
    texto = re.sub(r"(\w)-\s*\n\s*(\w)", r"\1\2", texto)
    bloques = re.split(r"\n\s*\n", texto)
    return [re.sub(r"\s+", " ", b).strip() for b in bloques if re.sub(r"\W", "", b)]


def rangos(s):
    out = set()
    for r in filter(None, s.split(",")):
        a, _, b = r.partition("-")
        out.update(range(int(a), int(b or a) + 1))
    return out


def main():
    args = sys.argv[1:]
    encima = set()
    if "--encima" in args:
        i = args.index("--encima")
        encima = rangos(args[i + 1])
        del args[i:i + 2]
    ini, fin, salida = int(args[0]), int(args[1]), args[2]
    alias = json.loads((BASE / "alias.json").read_text())
    claves = [x for k, v in alias.items() if not k.startswith("_") for x in v["buscar"]]
    rx = re.compile("|".join(claves + ["chuquisaca", "la plata", "charcas"]))
    out = []
    for p in range(ini, fin + 1):
        f = PAG / f"p{p:04d}.txt"
        if not f.exists():
            continue
        lineas = f.read_text(encoding="utf-8").split("\n", 1)
        ps = parrafos(lineas[1] if len(lineas) > 1 else "")
        if p in encima:
            ps = [x for j, x in enumerate(ps) if j == 0 or rx.search(sin_tildes(x))]
            out.append(f"=== p{p} [POR ENCIMA] ===")
        else:
            out.append(f"=== p{p} ===")
        out.extend(ps)
    Path(salida).write_text("\n".join(out) + "\n", encoding="utf-8")
    print(f"{salida}: {sum(len(x.split()) for x in out)} palabras")


if __name__ == "__main__":
    main()
