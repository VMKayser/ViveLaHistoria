"""Genera los materiales de Godot (.tres) que reemplazan a los del .glb por nombre.

Uso:  python3 -I herramientas/generar_materiales.py
Cada material del modelo de Blender (revoque_blanco, tejas, ...) tiene aquí su
StandardMaterial3D con las texturas PBR de Poly Haven.
"""
from pathlib import Path

GODOT = Path(__file__).resolve().parent.parent / "godot"
SALIDA = GODOT / "materiales"

# nombre -> (carpeta de textura o None, propiedades extra)
MATERIALES = {
    "empedrado": ("empedrado", {"albedo_color": "Color(0.92, 0.88, 0.82, 1)"}),
    "plaza": ("empedrado", {"albedo_color": "Color(1.0, 0.95, 0.88, 1)"}),
    "losa": ("losa", {"albedo_color": "Color(0.9, 0.86, 0.8, 1)"}),
    "revoque_blanco": ("revoque_blanco", {"albedo_color": "Color(1.12, 1.1, 1.05, 1)"}),
    "revoque_ocre": ("revoque_ocre", {"albedo_color": "Color(1.0, 0.92, 0.8, 1)"}),
    "zocalo": ("revoque_blanco", {"albedo_color": "Color(0.58, 0.36, 0.26, 1)"}),
    "tejas": ("tejas", {}),
    "madera": ("madera_balcon", {"albedo_color": "Color(0.85, 0.75, 0.65, 1)"}),
    "madera_puerta": ("madera_puerta", {}),
    "piedra": ("piedra", {}),
    "piedra_revocada": ("piedra_revocada", {}),
    "cerro": ("piedra", {"albedo_color": "Color(0.4, 0.38, 0.28, 1)"}),
    "hierro": (None, {"albedo_color": "Color(0.04, 0.04, 0.045, 1)", "metallic": "0.6", "roughness": "0.55"}),
    "bronce": (None, {"albedo_color": "Color(0.5, 0.33, 0.17, 1)", "metallic": "1.0", "roughness": "0.38"}),
    "tela": (None, {"albedo_color": "Color(0.12, 0.08, 0.06, 1)", "roughness": "1.0"}),
    "agua": (None, {"albedo_color": "Color(0.06, 0.08, 0.09, 1)", "roughness": "0.06", "metallic_specular": "0.8"}),
    "ventana_luz": (None, {
        "albedo_color": "Color(0.1, 0.06, 0.03, 1)", "emission_enabled": "true",
        "emission": "Color(1.0, 0.55, 0.22, 1)", "emission_energy_multiplier": "1.6",
    }),
    "vidrio_farol": (None, {
        "albedo_color": "Color(0.3, 0.22, 0.12, 1)", "emission_enabled": "true",
        "emission": "Color(1.0, 0.68, 0.32, 1)", "emission_energy_multiplier": "3.0",
    }),
    "cera": (None, {
        "albedo_color": "Color(0.9, 0.85, 0.7, 1)", "emission_enabled": "true",
        "emission": "Color(1.0, 0.8, 0.5, 1)", "emission_energy_multiplier": "0.6",
    }),
}

MAPAS = [
    ("color", "albedo_texture", {}),
    ("normal", "normal_texture", {"normal_enabled": "true", "normal_scale": "1.0"}),
    ("orm", "orm_texture", {"ao_enabled": "true", "ao_light_affect": "0.4"}),
]


def material(nombre, carpeta, extra):
    ext, props = [], {}
    if carpeta:
        for i, (sufijo, prop, mas) in enumerate(MAPAS, start=1):
            ruta = GODOT / "assets" / "texturas" / carpeta / f"{carpeta}_{sufijo}.jpg"
            if not ruta.exists():
                continue
            ext.append(f'[ext_resource type="Texture2D" path="res://{ruta.relative_to(GODOT).as_posix()}" id="{i}"]')
            props[prop] = f'ExtResource("{i}")'
            props.update(mas)
    props.update(extra)
    cuerpo = "\n".join(f"{k} = {v}" for k, v in props.items())
    tipo = "ORMMaterial3D" if "orm_texture" in props else "StandardMaterial3D"
    cabecera = f'[gd_resource type="{tipo}" load_steps={len(ext) + 1} format=3]'
    return "\n".join([cabecera, "", *ext, "", "[resource]", f'resource_name = "{nombre}"', cuerpo, ""])


def main():
    SALIDA.mkdir(exist_ok=True)
    for nombre, (carpeta, extra) in MATERIALES.items():
        (SALIDA / f"{nombre}.tres").write_text(material(nombre, carpeta, extra), encoding="utf-8")
    print(f"{len(MATERIALES)} materiales en {SALIDA}")


if __name__ == "__main__":
    main()
