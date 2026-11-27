"""Genera juego/escenas/niveles/asamblea_1825.tscn (nivel de la Escena 1).

Uso (desde la raíz del repositorio):
    python3 herramientas/generar_nivel.py juego/escenas/niveles/asamblea_1825.tscn --modelos --blender

Opciones:
    --modelos          usa los muebles 3D de Poly Haven (juego/assets/modelos)
    --blender          usa la arquitectura horneada de blender/construir_casa_libertad.py
    --intensidad=1.8   intensidad de la luz horneada

ATENCIÓN: reescribe la escena desde cero. Si alguien editó el .tscn en el editor de Godot,
esos cambios se pierden. Las coordenadas coinciden con las de blender/construir_casa_libertad.py.
"""
import math
import sys

SALIDA = sys.argv[1]
MODELOS = "--modelos" in sys.argv
BLENDER = "--blender" in sys.argv  # arquitectura desde blender/construir_casa_libertad.py
INTENSIDAD = next((a.split("=")[1] for a in sys.argv if a.startswith("--intensidad=")), "3.0")
# En modo Blender estas piezas vienen en casa_libertad.glb; el resto sigue en Godot.
SOLO_GODOT = {"Pasamanos", "PasamanosCoro", "Solio"}
OMITIR = {"Patio/ArcadaOeste", "Patio/PiesDerechos", "Patio/Pileta", "SalaMayor/ParedEste", "SalaMayor/Vigas"}
omitidos = set()

ext = []      # (tipo, ruta, id)
subs = []     # texto de sub_resources
nodos = []    # texto de nodos


def ext_res(tipo, ruta, ident):
    ext.append(f'[ext_resource type="{tipo}" path="{ruta}" id="{ident}"]')
    return f'ExtResource("{ident}")'


def sub(tipo, ident, props):
    cuerpo = "\n".join(f"{k} = {v}" for k, v in props.items())
    subs.append(f'[sub_resource type="{tipo}" id="{ident}"]\n{cuerpo}')
    return f'SubResource("{ident}")'


def tf(x=0.0, y=0.0, z=0.0, rot=None):
    """rot: ('x'|'y'|'z', grados)"""
    if rot is None:
        filas = [1, 0, 0, 0, 1, 0, 0, 0, 1]
    else:
        eje, grados = rot
        c, s = math.cos(math.radians(grados)), math.sin(math.radians(grados))
        if eje == "x":
            filas = [1, 0, 0, 0, c, -s, 0, s, c]
        elif eje == "y":
            filas = [c, 0, s, 0, 1, 0, -s, 0, c]
        else:
            filas = [c, -s, 0, s, c, 0, 0, 0, 1]
    numeros = ", ".join(f"{v:.6g}" for v in filas + [x, y, z])
    return f"Transform3D({numeros})"


def nodo(nombre, tipo, padre=".", props=None, instancia=None, raiz=False):
    ruta = nombre if padre == "." else f"{padre}/{nombre}"
    if BLENDER and (ruta in OMITIR or padre in omitidos):
        omitidos.add(ruta)
        return
    cabecera = f'[node name="{nombre}"'
    if instancia:
        cabecera += f' parent="{padre}" instance={instancia}]'
    elif raiz:
        cabecera += f' type="{tipo}"]'
    else:
        cabecera += f' type="{tipo}" parent="{padre}"]'
    cuerpo = "\n".join(f"{k} = {v}" for k, v in (props or {}).items())
    nodos.append(cabecera + ("\n" + cuerpo if cuerpo else ""))


def v3(x, y, z):
    return f"Vector3({x:.6g}, {y:.6g}, {z:.6g})"


def caja(nombre, padre, centro, tam, mat, colision=True, rot=None):
    if BLENDER and padre in ("Patio", "SalaMayor") and nombre not in SOLO_GODOT:
        return
    props = {"transform": tf(*centro, rot=rot), "size": v3(*tam), "material": mat}
    if colision:
        props["use_collision"] = "true"
    nodo(nombre, "CSGBox3D", padre, props)


# ---------------------------------------------------------------- recursos
S_NIVEL = ext_res("Script", "res://scripts/niveles/nivel.gd", "s_nivel")
S_GESTOR = ext_res("Script", "res://scripts/misiones/gestor_misiones.gd", "s_gestor")
S_UI = ext_res("Script", "res://scripts/ui/interfaz.gd", "s_ui")
S_PERS = ext_res("Script", "res://scripts/interaccion/personaje.gd", "s_pers")
S_TOMA = ext_res("Script", "res://scripts/interaccion/objeto_tomable.gd", "s_toma")
S_INSP = ext_res("Script", "res://scripts/interaccion/objeto_inspeccionable.gd", "s_insp")
S_ENTR = ext_res("Script", "res://scripts/interaccion/punto_entrega.gd", "s_entr")
S_ZONA = ext_res("Script", "res://scripts/interaccion/zona_evento.gd", "s_zona")
S_ARC = ext_res("Script", "res://scripts/arquitectura/arcada.gd", "s_arc")
S_REP = ext_res("Script", "res://scripts/arquitectura/repetidor.gd", "s_rep")
JUGADOR = ext_res("PackedScene", "res://escenas/jugador.tscn", "e_jugador")
if BLENDER:
    S_HORNEADO = ext_res("Script", "res://scripts/arquitectura/materiales_horneados.gd", "s_horneado")
    GLB_CASA = ext_res("PackedScene", "res://assets/arquitectura/casa_libertad.glb", "g_casa")
    T_LUZ = ext_res("Texture2D", "res://assets/arquitectura/luz_horneada.png", "t_luz")
CIELO_HDR = ext_res("Texture2D", "res://assets/cielo/kloofendal_48d_partly_cloudy_puresky.hdr", "t_cielo")

M = {}
for nombre in ["cal", "zocalo", "empedrado", "baldosa", "madera_techo", "viga", "madera_mueble",
               "piedra", "teja", "agua", "papel", "terciopelo", "dorado", "vidrio", "retrato_bolivar"]:
    M[nombre] = ext_res("Material", f"res://materiales/{nombre}.tres", f"m_{nombre}")

MOD = {}
if MODELOS:
    for ident in ["gallinera_chair", "WoodenChair_01", "WoodenTable_01", "brass_candleholders",
                  "Chandelier_03", "large_castle_door", "wooden_lantern_01", "planter_pot_clay", "potted_plant_02"]:
        MOD[ident] = ext_res("PackedScene", f"res://assets/modelos/{ident}/{ident}.gltf", f"g_{ident}")

cielo_mat = sub("PanoramaSkyMaterial", "cielo_mat", {"panorama": CIELO_HDR, "energy_multiplier": "1.0"})
cielo = sub("Sky", "cielo", {"sky_material": cielo_mat, "radiance_size": "2"})
entorno = sub("Environment", "entorno", {
    "background_mode": "2", "sky": cielo,
    "ambient_light_source": "3", "ambient_light_energy": "0.55",
    "reflected_light_source": "2",
    "tonemap_mode": "4", "tonemap_exposure": "0.95",
    "ssao_enabled": "true",
    "glow_enabled": "true", "glow_intensity": "0.35", "glow_bloom": "0.04", "glow_hdr_threshold": "1.3",
    "fog_enabled": "true", "fog_light_color": "Color(0.74, 0.8, 0.88, 1)", "fog_density": "0.001",
    "fog_sky_affect": "0.0",
    "adjustment_enabled": "true", "adjustment_contrast": "1.06", "adjustment_saturation": "1.06",
})
mat_npc_real = sub("StandardMaterial3D", "mat_npc_real", {"albedo_color": "Color(0.14, 0.14, 0.2, 1)", "roughness": "0.8"})
mat_npc_fict = sub("StandardMaterial3D", "mat_npc_fict", {"albedo_color": "Color(0.45, 0.4, 0.33, 1)", "roughness": "0.85"})
malla_npc_real = sub("CapsuleMesh", "malla_npc_real", {"material": mat_npc_real, "radius": "0.28", "height": "1.75"})
malla_npc_fict = sub("CapsuleMesh", "malla_npc_fict", {"material": mat_npc_fict, "radius": "0.28", "height": "1.75"})
malla_credencial = sub("BoxMesh", "malla_credencial", {"material": M["papel"], "size": v3(0.22, 0.012, 0.3)})
malla_acta = sub("BoxMesh", "malla_acta", {"material": M["papel"], "size": v3(0.3, 0.006, 0.42)})
malla_lienzo = sub("QuadMesh", "malla_lienzo", {"material": M["retrato_bolivar"], "size": "Vector2(1.06, 1.4)"})
malla_marco_v = sub("BoxMesh", "malla_marco_v", {"material": M["dorado"], "size": v3(0.1, 1.6, 0.06)})
malla_marco_h = sub("BoxMesh", "malla_marco_h", {"material": M["dorado"], "size": v3(1.26, 0.1, 0.06)})
malla_placa = sub("BoxMesh", "malla_placa", {"material": M["piedra"], "size": v3(0.9, 0.55, 0.05)})
malla_viga = sub("BoxMesh", "malla_viga", {"material": M["viga"], "size": v3(12.4, 0.28, 0.22)})
malla_poste_baranda = sub("BoxMesh", "malla_poste_baranda", {"material": M["viga"], "size": v3(0.07, 0.85, 0.07)})
malla_vidrio = sub("BoxMesh", "malla_vidrio", {"material": M["vidrio"], "size": v3(0.04, 2.4, 1.6)})
malla_cadena = sub("CylinderMesh", "malla_cadena", {"material": M["dorado"], "top_radius": "0.015", "bottom_radius": "0.015", "height": "0.7", "radial_segments": "6"})
malla_agua = sub("CylinderMesh", "malla_agua", {"material": M["agua"], "top_radius": "1.32", "bottom_radius": "1.32", "height": "0.02", "radial_segments": "48"})
malla_mesa_sec = sub("BoxMesh", "malla_mesa_sec", {"material": M["madera_mueble"], "size": v3(1.4, 0.8, 0.8)})
forma_zona = sub("BoxShape3D", "forma_zona", {"size": v3(11.5, 3, 23)})
forma_baranda = sub("BoxShape3D", "forma_baranda", {"size": v3(0.12, 1.2, 11.8)})
forma_bancas = sub("BoxShape3D", "forma_bancas", {"size": v3(3.4, 1.0, 10.4)})

# ---------------------------------------------------------------- nivel
nodo("Asamblea1825", "Node3D", raiz=True, props={"script": S_NIVEL})
nodo("Entorno", "WorldEnvironment", props={"environment": entorno})
nodo("Sol", "DirectionalLight3D", props={
    "transform": "Transform3D(0.5039, -0.5902, 0.6307, 0.0000, 0.7302, 0.6833, -0.8638, -0.3443, 0.3679, 0, 20, 0)",
    "light_color": "Color(1, 0.95, 0.86, 1)", "light_energy": "1.7",
    "shadow_enabled": "true", "shadow_blur": "1.5", "directional_shadow_max_distance": "45.0"})

if BLENDER:
    nodo("Arquitectura", "Node3D", props={"script": S_HORNEADO, "luz_horneada": T_LUZ, "intensidad": INTENSIDAD})
    nodo("CasaLibertad", None, "Arquitectura", instancia=GLB_CASA)

# --- Patio ------------------------------------------------------------------
nodo("Patio", "Node3D")
P = "Patio"
caja("Piso", P, (0, -0.1, -0.6), (20.8, 0.2, 22), M["empedrado"])
caja("MuroOeste", P, (-10.6, 2.3, -0.6), (0.4, 4.6, 22), M["cal"])
caja("MuroEste", P, (10.6, 2.3, -0.6), (0.4, 4.6, 22), M["cal"])
caja("MuroSur", P, (0, 2.3, 10.6), (21.6, 4.6, 0.4), M["cal"])
caja("MuroNorteOeste", P, (-8.6, 2.3, -11.8), (4.4, 4.6, 0.4), M["cal"])
caja("MuroNorteEste", P, (8.6, 2.3, -11.8), (4.4, 4.6, 0.4), M["cal"])
# Zócalos pintados al pie de los muros del patio
caja("ZocaloOeste", P, (-10.38, 0.5, -0.6), (0.04, 1.0, 22), M["zocalo"], colision=False)
caja("ZocaloSur", P, (0, 0.5, 10.38), (20.8, 1.0, 0.04), M["zocalo"], colision=False)
caja("ZocaloNorteOeste", P, (-5.8, 0.5, -11.58), (9.2, 1.0, 0.04), M["zocalo"], colision=False)
caja("ZocaloNorteEste", P, (5.8, 0.5, -11.58), (9.2, 1.0, 0.04), M["zocalo"], colision=False)
caja("ZocaloEste", P, (10.38, 0.5, -0.6), (0.04, 1.0, 22), M["zocalo"], colision=False)

# Claustro oeste: arcada de piedra con corredor techado
nodo("ArcadaOeste", "CSGCombiner3D", P, {
    "transform": tf(-7.6, 0, -0.6, rot=("y", 90)), "use_collision": "true", "script": S_ARC,
    "largo": "22.0", "alto": "4.0", "grosor": "0.6", "numero_arcos": "6", "ancho_vano": "2.5",
    "alto_arranque": "2.3", "material_muro": M["piedra"]})
caja("TechoCorredorOeste", P, (-8.9, 4.1, -0.6), (3.2, 0.2, 22), M["madera_techo"])
caja("TejadoOeste", P, (-8.5, 4.55, -0.6), (4.4, 0.14, 22.4), M["teja"], colision=False, rot=("z", -15))

# Galería alta este: plataforma, escalones, baranda, pies derechos y alero de teja
caja("GaleriaAlta", P, (8.9, 0.75, -0.6), (3.4, 1.5, 14.8), M["piedra"])
caja("PisoGaleria", P, (8.9, 1.52, -0.6), (3.4, 0.04, 14.8), M["madera_mueble"], colision=False)
caja("Escalon1", P, (6.0, 0.25, 5.6), (0.8, 0.5, 1.6), M["piedra"])
caja("Escalon2", P, (6.8, 0.5, 5.6), (0.8, 1.0, 1.6), M["piedra"])
nodo("PostesBaranda", "Node3D", P, {"transform": tf(7.3, 1.5, -7.9), "script": S_REP,
                                     "cantidad": "Vector3i(1, 1, 25)", "separacion": v3(1, 1, 0.5)})
nodo("Poste", "MeshInstance3D", f"{P}/PostesBaranda", {"transform": tf(0, 0.425, 0), "mesh": malla_poste_baranda})
caja("Pasamanos", P, (7.3, 2.38, -1.9), (0.1, 0.08, 12.1), M["viga"], colision=False)
nodo("ColisionBaranda", "StaticBody3D", P, {"transform": tf(7.3, 2.1, -1.9)})
nodo("Forma", "CollisionShape3D", f"{P}/ColisionBaranda", {"shape": forma_baranda})
nodo("PiesDerechos", "Node3D", P, {"transform": tf(7.4, 1.5, -7.6), "script": S_REP,
                                    "cantidad": "Vector3i(1, 1, 5)", "separacion": v3(1, 1, 3.5)})
caja("PieDerecho", f"{P}/PiesDerechos", (0, 1.45, 0), (0.24, 2.9, 0.24), M["viga"])
caja("TechoGaleria", P, (8.9, 4.45, -0.6), (3.4, 0.15, 15.2), M["madera_techo"], colision=False)
caja("TejadoEste", P, (8.6, 4.75, -0.6), (4.6, 0.14, 15.6), M["teja"], colision=False, rot=("z", 15))

# Pileta central
nodo("Pileta", "CSGCombiner3D", P, {"use_collision": "true"})
nodo("Taza", "CSGCylinder3D", f"{P}/Pileta", {"transform": tf(0, 0.3, 0), "radius": "1.5", "height": "0.6", "sides": "40", "material": M["piedra"]})
nodo("Hueco", "CSGCylinder3D", f"{P}/Pileta", {"transform": tf(0, 0.46, 0), "operation": "2", "radius": "1.32", "height": "0.6", "sides": "40", "material": M["piedra"]})
nodo("Pilar", "CSGCylinder3D", f"{P}/Pileta", {"transform": tf(0, 0.7, 0), "radius": "0.18", "height": "1.4", "sides": "20", "material": M["piedra"]})
nodo("Copa", "CSGCylinder3D", f"{P}/Pileta", {"transform": tf(0, 1.4, 0), "radius": "0.5", "height": "0.14", "sides": "28", "material": M["piedra"]})
nodo("Agua", "MeshInstance3D", P, {"transform": tf(0, 0.47, 0), "mesh": malla_agua, "cast_shadow": "0"})

caja("MesaCredencial", P, (3, 0.4, 3), (1.0, 0.8, 0.6), M["madera_mueble"])

# Portada de piedra de la Sala Mayor
caja("JambaOeste", P, (-1.38, 1.7, -11.55), (0.36, 3.4, 0.5), M["piedra"])
caja("JambaEste", P, (1.38, 1.7, -11.55), (0.36, 3.4, 0.5), M["piedra"])
caja("Dintel", P, (0, 3.6, -11.55), (3.2, 0.4, 0.5), M["piedra"])

# --- Sala Mayor -------------------------------------------------------------
nodo("SalaMayor", "Node3D")
S = "SalaMayor"
caja("Piso", S, (0, -0.1, -23.9), (12.4, 0.2, 24.6), M["baldosa"])
caja("ParedOeste", S, (-6.2, 3.5, -24), (0.4, 7, 24.4), M["cal"])
nodo("ParedEste", "CSGCombiner3D", S, {"use_collision": "true"})
caja("Muro", f"{S}/ParedEste", (6.2, 3.5, -24), (0.4, 7, 24.4), M["cal"], colision=False)
for i, z in enumerate([-16, -21, -26, -31]):
    nodo(f"Ventana{i + 1}", "CSGBox3D", f"{S}/ParedEste", {
        "transform": tf(6.2, 4.3, z), "operation": "2", "size": v3(0.6, 2.4, 1.6), "material": M["cal"]})
    nodo(f"Vidrio{i + 1}", "MeshInstance3D", S, {"transform": tf(6.3, 4.3, z), "mesh": malla_vidrio, "cast_shadow": "0"})
caja("ParedNorte", S, (0, 3.5, -36.2), (12.8, 7, 0.4), M["cal"])
caja("ParedSurOeste", S, (-3.8, 3.5, -11.8), (5.2, 7, 0.4), M["cal"])
caja("ParedSurEste", S, (3.8, 3.5, -11.8), (5.2, 7, 0.4), M["cal"])
caja("SobrePuerta", S, (0, 5.2, -11.8), (2.4, 3.6, 0.4), M["cal"])
caja("ZocaloOeste", S, (-5.98, 0.6, -24), (0.04, 1.2, 23.9), M["zocalo"], colision=False)
caja("ZocaloEste", S, (5.98, 0.6, -24), (0.04, 1.2, 23.9), M["zocalo"], colision=False)
caja("ZocaloNorte", S, (0, 0.6, -35.98), (11.9, 1.2, 0.04), M["zocalo"], colision=False)
caja("ZocaloSurOeste", S, (-3.6, 0.6, -12.02), (4.8, 1.2, 0.04), M["zocalo"], colision=False)
caja("ZocaloSurEste", S, (3.6, 0.6, -12.02), (4.8, 1.2, 0.04), M["zocalo"], colision=False)
# Artesonado: tablazón y vigas
caja("Artesonado", S, (0, 7.15, -24), (12.8, 0.3, 24.8), M["madera_techo"])
nodo("Vigas", "Node3D", S, {"transform": tf(0, 6.86, -12.6), "script": S_REP,
                             "cantidad": "Vector3i(1, 1, 24)", "separacion": v3(1, 1, -1.0)})
nodo("Viga", "MeshInstance3D", f"{S}/Vigas", {"mesh": malla_viga})
caja("CornisaOeste", S, (-5.82, 6.8, -24), (0.36, 0.4, 24.4), M["viga"], colision=False)
caja("CornisaEste", S, (5.82, 6.8, -24), (0.36, 0.4, 24.4), M["viga"], colision=False)
# Coro alto con baranda
caja("Coro", S, (0, 3.6, -13.5), (11.98, 0.3, 3), M["madera_mueble"])
caja("PilarCoroOeste", S, (-3, 1.725, -14.85), (0.3, 3.45, 0.3), M["viga"])
caja("PilarCoroEste", S, (3, 1.725, -14.85), (0.3, 3.45, 0.3), M["viga"])
nodo("BarandaCoro", "Node3D", S, {"transform": tf(-5.85, 3.75, -14.95), "script": S_REP,
                                   "cantidad": "Vector3i(40, 1, 1)", "separacion": v3(0.3, 1, 1)})
nodo("Poste", "MeshInstance3D", f"{S}/BarandaCoro", {"transform": tf(0, 0.425, 0), "mesh": malla_poste_baranda})
caja("PasamanosCoro", S, (0, 4.62, -14.95), (11.9, 0.08, 0.12), M["viga"], colision=False)
# Mesa de la presidencia con paño de terciopelo
caja("MesaPresidencia", S, (0, 0.425, -32), (4, 0.85, 1.2), M["madera_mueble"])
caja("Pano", S, (0, 0.88, -32), (4.1, 0.06, 1.32), M["terciopelo"], colision=False)
caja("Faldon", S, (0, 0.52, -31.33), (4.1, 0.72, 0.03), M["terciopelo"], colision=False)

if MODELOS:
    nodo("Solio", "Node3D", S, {"transform": tf(0, 0, -34.4)}, instancia=MOD["WoodenChair_01"])
    # Sillas de los diputados: dos bloques de 3 x 4
    for lado, x in (("Oeste", -4.0), ("Este", 2.0)):
        nodo(f"Sillas{lado}", "Node3D", S, {"transform": tf(x, 0, -15.8), "script": S_REP,
                                              "cantidad": "Vector3i(3, 1, 4)", "separacion": v3(1.0, 1, -2.6)})
        nodo("Silla", "Node3D", f"{S}/Sillas{lado}", {"transform": tf(0, 0, 0, rot=("y", 180))},
             instancia=MOD["gallinera_chair"])
    nodo("Candelabros", "Node3D", S, {"transform": tf(-1.3, 0.91, -32.2)}, instancia=MOD["brass_candleholders"])
    for i, z in enumerate([-17, -24, -30.5]):
        nodo(f"Arana{i + 1}", "Node3D", S, {"transform": tf(0, 6.05, z)}, instancia=MOD["Chandelier_03"])
        nodo(f"Cadena{i + 1}", "MeshInstance3D", S, {"transform": tf(0, 6.4, z), "mesh": malla_cadena})
else:
    caja("Solio", S, (0, 0.9, -34.4), (1, 1.8, 0.8), M["viga"])
    for lado, x in (("Oeste", -3.0), ("Este", 3.0)):
        for fila, z in enumerate([-16, -18.6, -21.2, -23.8]):
            caja(f"Banca{lado}{fila + 1}", S, (x, 0.25, z), (3.4, 0.5, 0.6), M["madera_mueble"])
for lado, x in (("Oeste", -3.0), ("Este", 3.0)):
    nodo(f"ColisionSillas{lado}", "StaticBody3D", S, {"transform": tf(x, 0.5, -19.9)})
    nodo("Forma", "CollisionShape3D", f"{S}/ColisionSillas{lado}", {"shape": forma_bancas})

# Interior más oscuro y cálido que el exterior (sin efecto si el renderizador no lo soporta)
nodo("LuzInterior", "ReflectionProbe", S, {
    "transform": tf(0, 3.5, -24), "size": v3(12, 7, 24), "interior": "true",
    "ambient_mode": "2", "ambient_color": "Color(0.62, 0.5, 0.38, 1)", "ambient_color_energy": "1.1"})

# --- Luces ------------------------------------------------------------------
nodo("Luces", "Node3D")
for i, z in enumerate([-17, -24, -30.5]):
    nodo(f"LuzArana{i + 1}", "OmniLight3D", "Luces", {
        "transform": tf(0, 5.2, z), "light_color": "Color(1, 0.74, 0.46, 1)",
        "light_energy": "1.4", "omni_range": "10.0", "omni_attenuation": "1.4",
        "light_cull_mask": "4294967293" if BLENDER else "4294967295"})
nodo("LuzCoro", "OmniLight3D", "Luces", {
    "transform": tf(0, 2.6, -13.6), "light_color": "Color(1, 0.74, 0.46, 1)",
    "light_energy": "0.6", "omni_range": "6.0", "light_cull_mask": "4294967293" if BLENDER else "4294967295"})

# --- Personajes -------------------------------------------------------------
nodo("Personajes", "Node3D")
for nombre, ident, (x, y, z), real, extra in [
    ("Mendizabal", "mendizabal", (-3, 0, 4), True, {"tipo_firma": '"firma"'}),
    ("DiputadoPeru", "diputado_peru", (-5.8, 0, -6), False, {"tipo_firma": '"firma"'}),
    ("DiputadoRioPlata", "diputado_rioplata", (9.2, 1.5, -3), False, {"tipo_firma": '"firma"'}),
    ("Olaneta", "olaneta", (-4.2, 0, -28), True, {"tipo_firma": '"firma"'}),
    ("Serrano", "serrano", (0, 0, -33.2), True, {"tipo_firma": '"firma_presidente"', "firmas_requeridas": "3"}),
]:
    props = {"transform": tf(x, y, z), "script": S_PERS, "id_interaccion": f'"{ident}"'}
    props.update(extra)
    nodo(nombre, "StaticBody3D", "Personajes", props)
    nodo("Modelo", "MeshInstance3D", f"Personajes/{nombre}", {
        "transform": tf(0, 0.875, 0), "mesh": malla_npc_real if real else malla_npc_fict})

# --- Objetos ----------------------------------------------------------------
nodo("Objetos", "Node3D")
nodo("Credencial", "StaticBody3D", "Objetos", {
    "transform": tf(3, 0.807, 3), "script": S_TOMA, "id_interaccion": '"credencial"',
    "nombre_visible": '"la credencial de diputado"', "ficha_id": '"f_convocatoria"'})
nodo("Modelo", "MeshInstance3D", "Objetos/Credencial", {"mesh": malla_credencial})
nodo("Acta", "StaticBody3D", "Objetos", {
    "transform": tf(0.9, 0.915, -31.75), "script": S_TOMA, "id_interaccion": '"acta"',
    "nombre_visible": '"el Acta de la Independencia"', "ficha_id": '"f_acta"',
    "solo_en_mision": '"m4_firmas"', "modo": "1"})
nodo("Modelo", "MeshInstance3D", "Objetos/Acta", {"mesh": malla_acta})
nodo("RetratoBolivar", "StaticBody3D", "Objetos", {
    "transform": tf(0, 3.1, -35.93), "script": S_INSP, "id_interaccion": '"retrato_bolivar"',
    "nombre_visible": '"el retrato de Bolívar"', "ficha_id": '"f_retratos"'})
nodo("Lienzo", "MeshInstance3D", "Objetos/RetratoBolivar", {"transform": tf(0, 0, 0.02), "mesh": malla_lienzo})
nodo("MarcoOeste", "MeshInstance3D", "Objetos/RetratoBolivar", {"transform": tf(-0.58, 0, 0.02), "mesh": malla_marco_v})
nodo("MarcoEste", "MeshInstance3D", "Objetos/RetratoBolivar", {"transform": tf(0.58, 0, 0.02), "mesh": malla_marco_v})
nodo("MarcoArriba", "MeshInstance3D", "Objetos/RetratoBolivar", {"transform": tf(0, 0.75, 0.02), "mesh": malla_marco_h})
nodo("MarcoAbajo", "MeshInstance3D", "Objetos/RetratoBolivar", {"transform": tf(0, -0.75, 0.02), "mesh": malla_marco_h})
nodo("PlacaManzana", "StaticBody3D", "Objetos", {
    "transform": tf(-2.4, 1.6, 10.37), "script": S_INSP, "id_interaccion": '"placa_manzana"',
    "nombre_visible": '"la placa del edificio"', "ficha_id": '"f_manzana_jesuitica"'})
nodo("Modelo", "MeshInstance3D", "Objetos/PlacaManzana", {"mesh": malla_placa})
nodo("MesaSecretaria", "StaticBody3D", "Objetos", {
    "transform": tf(4.6, 0, -29), "script": S_ENTR, "id_interaccion": '"mesa_secretaria"',
    "nombre_visible": '"la mesa de la Secretaría"', "solo_en_mision": '"m5_entrega"'})
if MODELOS:
    nodo("Modelo", "Node3D", "Objetos/MesaSecretaria", {"transform": tf(0, 0, 0, rot=("y", 90))},
         instancia=MOD["WoodenTable_01"])
else:
    nodo("Modelo", "MeshInstance3D", "Objetos/MesaSecretaria", {"transform": tf(0, 0.4, 0), "mesh": malla_mesa_sec})
nodo("Soporte", "Marker3D", "Objetos/MesaSecretaria", {"transform": tf(0, 0.56 if MODELOS else 0.81, 0)})

if MODELOS:
    nodo("Decoracion", "Node3D")
    nodo("PuertaSur1", "Node3D", "Decoracion", {"transform": tf(-5.5, 0, 10.3, rot=("y", 180))}, instancia=MOD["large_castle_door"])
    nodo("PuertaSur2", "Node3D", "Decoracion", {"transform": tf(5.5, 0, 10.3, rot=("y", 180))}, instancia=MOD["large_castle_door"])
    for i, (x, z) in enumerate([(-9.6, 9.6), (9.6, 9.6), (-6.6, -10.8), (6.6, -10.8)]):
        nodo(f"Maceta{i + 1}", "Node3D", "Decoracion", {"transform": tf(x, 0, z)}, instancia=MOD["potted_plant_02"])
    for i, (x, z) in enumerate([(-3.4, 9.6), (3.4, 9.6)]):
        nodo(f"MacetaBarro{i + 1}", "Node3D", "Decoracion", {"transform": tf(x, 0, z)}, instancia=MOD["planter_pot_clay"])
    for i, (x, y, z) in enumerate([(3.3, 0.8, 3.1), (9.9, 1.54, -6.5), (9.9, 1.54, 3.5), (-1.9, 0.91, -32.3)]):
        nodo(f"Farol{i + 1}", "Node3D", "Decoracion", {"transform": tf(x, y, z)}, instancia=MOD["wooden_lantern_01"])

# --- Zona, jugador, lógica --------------------------------------------------
nodo("ZonaSalaMayor", "Area3D", props={"transform": tf(0, 1.5, -24), "script": S_ZONA,
                                        "id_zona": '"sala_mayor"', "mensaje_al_entrar": '"Sala Mayor de la Universidad · Chuquisaca, 1825"'})
nodo("Forma", "CollisionShape3D", "ZonaSalaMayor", {"shape": forma_zona})
nodo("Jugador", None, instancia=JUGADOR, props={"transform": tf(0, 0.05, 8)})
nodo("GestorMisiones", "Node", props={"script": S_GESTOR})
nodo("Interfaz", "CanvasLayer", props={"script": S_UI})

texto = f"[gd_scene load_steps={len(ext) + len(subs) + 1} format=3]\n\n"
texto += "\n".join(ext) + "\n\n" + "\n\n".join(subs) + "\n\n" + "\n\n".join(nodos) + "\n"
open(SALIDA, "w", encoding="utf-8").write(texto)
print(f"{SALIDA}: {len(ext)} recursos externos, {len(subs)} internos, {len(nodos)} nodos")
