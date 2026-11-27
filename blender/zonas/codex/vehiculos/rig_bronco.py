"""Contrato del vehículo y clips de rodadura portables en Blender/glTF."""
import math

import bpy


def preparar_movimiento(datos, grupos):
    configuracion = dict(datos["movimiento"], radio_rueda=datos["radio_rueda"],
                         eje_trasero=datos["ejes"][0], eje_delantero=datos["ejes"][1],
                         semivia=datos["semivia_ruedas"])
    grupos["raiz"]["movimiento"] = configuracion
    grupos["raiz"]["animacion"] = "Rodadura por distancia; dirección Ackermann. Clips: 1 vuelta por segundo."
    escena = bpy.context.scene
    escena.render.fps = 24
    escena.frame_start, escena.frame_end = 1, 25
    for nombre, objeto in grupos.items():
        if not nombre.startswith("rueda_"):
            continue
        objeto.rotation_mode = "XYZ"
        objeto.animation_data_create()
        for clip, signo in [("rodar_adelante", 1), ("rodar_atras", -1)]:
            objeto.animation_data.action = None
            for frame in range(1, 26):
                # En Blender +Y produce rodadura hacia +X; en glTF se vuelve -Z.
                objeto.rotation_euler.y = signo * math.tau * (frame-1) / 24
                objeto.keyframe_insert(data_path="rotation_euler", index=1, frame=frame)
            accion = objeto.animation_data.action
            accion.name = f"{clip}_{nombre}"
            slot = objeto.animation_data.action_slot
            objeto.animation_data.action = None
            pista = objeto.animation_data.nla_tracks.new()
            pista.name = clip
            tira = pista.strips.new(clip, 1, accion)
            tira.action_slot = slot
            tira.extrapolation = "NOTHING"
        objeto.rotation_euler.y = 0
    escena.frame_set(1)
    return configuracion
