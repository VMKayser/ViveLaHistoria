"""Cuatro GLB del mismo vehículo: cambia solo la pintura y su identificador.

Se conserva exactamente el bloque binario (geometría, normales, UV, textura,
keyframes) y la jerarquía. El original azul y su alias son idénticos byte a byte.
"""
import copy
import hashlib
import json
import shutil
import struct
from pathlib import Path

DIRECTORIO = Path(__file__).resolve().parent
RAIZ = DIRECTORIO.parents[3]
SALIDA = RAIZ / "web/public/models/ciudad/codex/vehiculos"


def color_lineal(h):
    c = [int(h.lstrip("#")[i:i+2], 16)/255 for i in (0, 2, 4)]
    return [v/12.92 if v <= .04045 else ((v+.055)/1.055)**2.4 for v in c]


def leer_glb(datos):
    magic, version, largo = struct.unpack_from("<III", datos)
    assert magic == 0x46546C67 and version == 2 and largo == len(datos)
    bloques = []
    cursor = 12
    while cursor < largo:
        n, tipo = struct.unpack_from("<II", datos, cursor)
        bloques.append((tipo, datos[cursor+8:cursor+8+n]))
        cursor += 8+n
    assert bloques[0][0] == 0x4E4F534A
    return json.loads(bloques[0][1]), bloques[1:]


def escribir_glb(documento, bloques):
    texto = json.dumps(documento, ensure_ascii=False, separators=(",", ":")).encode()
    texto += b" " * (-len(texto) % 4)
    cuerpo = struct.pack("<II", len(texto), 0x4E4F534A) + texto
    cuerpo += b"".join(struct.pack("<II", len(b), tipo)+b for tipo, b in bloques)
    return struct.pack("<III", 0x46546C67, 2, 12+len(cuerpo))+cuerpo


def main():
    datos = json.loads((DIRECTORIO / "bronco.json").read_text())
    base = (SALIDA / "autobus_bronco.glb").read_bytes()
    documento, bloques = leer_glb(base)
    originales = {"principal": datos["colores"]["azul"], "detalle": datos["colores"]["azul_claro"]}
    for k, h in originales.items():
        assert datos["variantes"]["azul"][k] == h
    indices = {}
    for k, h in originales.items():
        candidatos = [i for i, m in enumerate(documento["materials"])
                      if m.get("name") == "pintura_acento__"+h.lstrip("#")]
        assert len(candidatos) == 1, f"No se identifica la pintura {k} del maestro azul"
        indices[k] = candidatos[0]
    manifiesto = {"version": 1, "predeterminado": "azul", "maestro": "autobus_bronco.glb",
                  "controlador": "autobus_animado.mjs", "variantes": []}
    for id_color, variante in datos["variantes"].items():
        destino = SALIDA / f"autobus_bronco_{id_color}.glb"
        if id_color == "azul":
            shutil.copyfile(SALIDA / "autobus_bronco.glb", destino)
        else:
            nuevo = copy.deepcopy(documento)
            for k, indice in indices.items():
                m = nuevo["materials"][indice]
                m["name"] = "pintura_acento__"+variante[k].lstrip("#")
                factor = m["pbrMetallicRoughness"]["baseColorFactor"]
                m["pbrMetallicRoughness"]["baseColorFactor"] = color_lineal(variante[k])+[factor[3]]
                m.setdefault("extras", {})["pintura_bronco"] = k
            raiz = next(n for n in nuevo["nodes"] if n.get("name") == "autobus_bronco")
            raiz.setdefault("extras", {})["variante"] = id_color
            destino.write_bytes(escribir_glb(nuevo, bloques))
        manifiesto["variantes"].append({"id": id_color, **variante,
            "glb": destino.name, "blend": f"autobus_bronco_{id_color}.blend",
            "bytes_glb": destino.stat().st_size,
            "sha256_glb": hashlib.sha256(destino.read_bytes()).hexdigest()})
        print(destino.name, destino.stat().st_size, "bytes")
    (SALIDA / "autobus_bronco.variantes.json").write_text(json.dumps(manifiesto, ensure_ascii=False, indent=2)+"\n")


if __name__ == "__main__":
    main()
