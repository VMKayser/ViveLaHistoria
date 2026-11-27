"""Lector mínimo de GLB (glTF 2.0 binario) con numpy, sin Blender ni navegador.

Devuelve las primitivas en coordenadas de MUNDO (las del visor: x este, y arriba, z = −norte), con la jerarquía de
nodos aplicada, el material (nombre y color base lineal) y el nombre del objeto de Blender al que pertenecen.
Solo lo que exportan los agentes: posiciones y normales float32, índices u8/u16/u32, triángulos.
"""
import json
import struct

import numpy as np

_TIPOS = {5120: np.int8, 5121: np.uint8, 5122: np.int16, 5123: np.uint16, 5125: np.uint32, 5126: np.float32}
_COMP = {"SCALAR": 1, "VEC2": 2, "VEC3": 3, "VEC4": 4, "MAT4": 16}


def _accesor(j, binario, k):
    a = j["accessors"][k]
    vista = j["bufferViews"][a["bufferView"]]
    tipo = np.dtype(_TIPOS[a["componentType"]])
    n = _COMP[a["type"]]
    inicio = vista.get("byteOffset", 0) + a.get("byteOffset", 0)
    paso = vista.get("byteStride", 0)
    if paso and paso != tipo.itemsize * n:
        crudo = np.frombuffer(binario, np.uint8, a["count"] * paso, inicio).reshape(a["count"], paso)
        datos = crudo[:, : tipo.itemsize * n].copy().view(tipo).reshape(a["count"], n)
    else:
        datos = np.frombuffer(binario, tipo, a["count"] * n, inicio).reshape(a["count"], n)
    if a.get("normalized"):
        datos = datos.astype(np.float32) / np.iinfo(tipo).max
    return datos if n > 1 else datos.ravel()


def _matriz_local(nodo):
    if "matrix" in nodo:
        return np.array(nodo["matrix"], np.float64).reshape(4, 4).T
    t = np.array(nodo.get("translation", [0, 0, 0]), np.float64)
    x, y, z, w = nodo.get("rotation", [0, 0, 0, 1])
    s = np.array(nodo.get("scale", [1, 1, 1]), np.float64)
    r = np.array([
        [1 - 2 * (y * y + z * z), 2 * (x * y - z * w), 2 * (x * z + y * w)],
        [2 * (x * y + z * w), 1 - 2 * (x * x + z * z), 2 * (y * z - x * w)],
        [2 * (x * z - y * w), 2 * (y * z + x * w), 1 - 2 * (x * x + y * y)],
    ])
    m = np.eye(4)
    m[:3, :3] = r * s
    m[:3, 3] = t
    return m


def leer(ruta):
    """[(nombre_objeto, nombre_material, color_rgb_lineal, pos(N,3), nor(N,3), idx(M,3))] en coordenadas de mundo."""
    b = open(ruta, "rb").read()
    if b[:4] != b"glTF":
        raise ValueError(f"{ruta}: no es un GLB")
    n = struct.unpack("<I", b[12:16])[0]
    j = json.loads(b[20:20 + n])
    binario = b[20 + n + 8:] if len(b) > 20 + n else b""
    if "meshes" not in j:
        return []
    materiales = j.get("materials", [])
    res = []

    def visitar(k, padre, nombre_padre):
        nodo = j["nodes"][k]
        m = padre @ _matriz_local(nodo)
        nombre = nodo.get("name") or nombre_padre
        if "mesh" in nodo:
            normales_m = np.linalg.inv(m[:3, :3]).T
            for p in j["meshes"][nodo["mesh"]]["primitives"]:
                if p.get("mode", 4) != 4:
                    continue
                pos = _accesor(j, binario, p["attributes"]["POSITION"]).astype(np.float64)
                pos = pos @ m[:3, :3].T + m[:3, 3]
                if "NORMAL" in p["attributes"]:
                    nor = _accesor(j, binario, p["attributes"]["NORMAL"]).astype(np.float64) @ normales_m.T
                    nor /= np.maximum(np.linalg.norm(nor, axis=1, keepdims=True), 1e-12)
                else:
                    nor = np.zeros_like(pos)
                    nor[:, 1] = 1
                idx = _accesor(j, binario, p["indices"]).astype(np.uint32) if "indices" in p else np.arange(len(pos), dtype=np.uint32)
                if np.linalg.det(m[:3, :3]) < 0:          # escala negativa: se invierte el orden para conservar la cara
                    idx = idx.reshape(-1, 3)[:, [0, 2, 1]].ravel()
                mat = materiales[p["material"]] if "material" in p else {}
                color = mat.get("pbrMetallicRoughness", {}).get("baseColorFactor", [1, 1, 1, 1])[:3]
                res.append((nombre, mat.get("name", ""), np.array(color, np.float32), pos.astype(np.float32),
                            nor.astype(np.float32), idx.reshape(-1, 3)))
        for h in nodo.get("children", []):
            visitar(h, m, nombre)

    escena = j["scenes"][j.get("scene", 0)]
    for k in escena["nodes"]:
        visitar(k, np.eye(4), "")
    return res
