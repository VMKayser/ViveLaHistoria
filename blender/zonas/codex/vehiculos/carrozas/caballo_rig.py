"""Esqueleto del caballo y ciclos sobre pezuñas de apoyo cinemático."""
import math

import bpy
from mathutils import Matrix, Vector

from caballo_malla import activar

SEGMENTOS = ("arranque", "articulacion", "cana", "casco")


def cadenas(datos):
    return [dict(pata,nombre=nombre,puntos=[Vector(co) for co in pata["puntos"]],
                 huesos=[f"{nombre}_{segmento}" for segmento in SEGMENTOS])
            for nombre,pata in datos["patas"].items()]


def armar(raiz, malla, puntos, patas):
    datos = bpy.data.armatures.new("Anatomía equina")
    rig = bpy.data.objects.new("Esqueleto equino",datos)
    bpy.context.collection.objects.link(rig)
    rig.parent = raiz
    rig.show_in_front = True
    datos.display_type = "OCTAHEDRAL"
    activar(rig)
    bpy.ops.object.mode_set(mode="EDIT")
    huesos = {}

    def agregar(nombre, a, b, padre=None, deforma=True):
        hueso = datos.edit_bones.new(nombre)
        hueso.head, hueso.tail = a,b
        hueso.use_deform = deforma
        if padre:
            hueso.parent = huesos[padre]
            hueso.use_connect = (hueso.parent.tail-hueso.head).length < .0001
        huesos[nombre] = hueso

    agregar("raiz_esqueleto",(0,0,0),(0,0,.34),deforma=False)
    jefe = {"cuerpo":"raiz_esqueleto","cuello":"cuerpo","nuca":"cuello","cabeza":"nuca",
            "cola_1":"cuerpo","cola_2":"cola_1","cola_3":"cola_2",
            "oreja_derecha":"cabeza","oreja_izquierda":"cabeza"}
    for nombre, (a,b) in puntos.items():
        agregar(nombre,a,b,jefe[nombre])
    for pata in patas:
        padre = "cuerpo"
        for nombre,(a,b) in zip(pata["huesos"],zip(pata["puntos"],pata["puntos"][1:])):
            agregar(nombre,a,b,padre)
            padre = nombre
    bpy.ops.object.mode_set(mode="OBJECT")

    mod = malla.modifiers.new("Piel equina","ARMATURE")
    mod.object = rig
    malla.parent = rig
    for pb in rig.pose.bones:
        pb.rotation_mode = "QUATERNION"
    activar(rig)
    return rig


def rot_y(angulo):
    return Matrix.Rotation(angulo,3,"Y")


def direccionar(resto, cabeza, punta):
    origen = resto.to_3x3().col[1].normalized()
    giro = origen.rotation_difference((punta-cabeza).normalized())
    nuevo = (giro.to_matrix() @ resto.to_3x3()).to_4x4()
    nuevo.translation = cabeza
    return nuevo


def objetivo(pata,ciclo,fase):
    base_x,base_y = pata["apoyo"]
    zancada = ciclo["zancada_m"]
    if zancada == 0:
        derecha = pata["nombre"].endswith("derecha")
        desfase = (.061 if derecha else -.022) if pata["nombre"].startswith("mano") else (.039 if derecha else -.074)
        return base_x+desfase,base_y,0.,0.,True
    t = (fase + pata[ciclo["desfase"]]) % 1
    apoyo = ciclo["apoyo"]
    mitad = apoyo*.5
    if t < apoyo:
        return base_x+zancada*(mitad-t),base_y,0.,0.,True
    s = (t-apoyo)/(1-apoyo)
    avance = s*s*(3-2*s)
    elevacion = ciclo["elevacion"]*math.sin(math.pi*s)**1.42
    pitch = math.copysign(1,zancada)*(-.30*math.sin(math.tau*s)-.13*math.sin(math.pi*s))
    return base_x+zancada*apoyo*(avance-.5),base_y,elevacion,pitch,False


def cadena_pose(pata, ciclo, fase, dz):
    a,b,c,d,e = pata["puntos"]
    x,y,z,pitch,apoya = objetivo(pata,ciclo,fase)
    giro_pie = rot_y(math.radians(pata["angulo_escaneo"])+pitch)
    suela = [giro_pie @ (p-d) for p in pata["suela"]]
    minimo = min(p.z for p in suela)
    piso = [p for p in suela if p.z < minimo+.009]
    reposo = Vector((x-sum(p.x for p in piso)/len(piso), y, z-minimo+.003))
    a1 = a+Vector((0,0,dz))
    rebote = (x-pata["apoyo"][0])
    frente = pata["nombre"].startswith("mano")
    viraje = -.68*rebote + (-.09 if frente else .01)
    b1 = a1+rot_y(viraje) @ (b-a)
    l2,l3 = (c-b).length,(d-c).length
    linea = reposo-b1
    distancia = linea.length
    extension = min(.081,max(0,distancia-(l2+l3-.009)))
    if extension:
        balanceo = linea.normalized()*extension
        a1 += balanceo
        b1 += balanceo
        linea = reposo-b1
        distancia = linea.length
    alcance = min(l2+l3-.002,distancia)
    if alcance < distancia:
        # Mantiene los segmentos a longitud fija y registra el alcance para la verificación.
        reposo = b1+linea.normalized()*alcance
    u = (reposo-b1).normalized()
    h = (alcance**2+l2**2-l3**2)/(2*alcance)
    amplitud = math.sqrt(max(0,l2*l2-h*h))
    flex = Vector((1 if frente else -1, 0, 0))
    flex = (flex-u*u.dot(flex)).normalized()
    c1 = b1+u*h+flex*amplitud
    e1 = reposo+giro_pie@(e-d)
    return [a1,b1,c1,reposo,e1],giro_pie,apoya,max(0,distancia-alcance)


def matrices_pose(rig, patas, nombre, ciclo, fase):
    poses = {}
    restos = {b.name:b.bone.matrix_local for b in rig.pose.bones}
    f = math.tau*fase
    if nombre == "reposo":
        dz = .007+.006*math.sin(f)
    elif nombre == "trote":
        dz = -.031+.029*math.cos(2*f-.20)
    else:
        dz = -.045+.010*math.cos(2*f-.45)
    reposo = nombre=="reposo"
    poses["raiz_esqueleto"] = restos["raiz_esqueleto"]
    poses["cuerpo"] = Matrix.Translation((0,0,dz)) @ restos["cuerpo"]

    def torsion(hueso,padre,y,z=0):
        rp, rh = restos[padre],restos[hueso]
        p = poses[padre] @ rp.inverted() @ rh
        giro = p.to_3x3().inverted() @ (rot_y(y) @ Matrix.Rotation(z,3,"Z")) @ p.to_3x3()
        poses[hueso] = p @ giro.to_4x4()

    torsion("cuello","cuerpo",(.014 if reposo else .043)*math.sin(f-.23))
    torsion("nuca","cuello",.023*math.sin(f+.5))
    torsion("cabeza","nuca",-.026*math.sin(f+.18),.018*math.cos(f))
    torsion("oreja_derecha","cabeza",.072*math.sin(f+.8),.038*math.cos(2*f))
    torsion("oreja_izquierda","cabeza",.063*math.sin(f-1.2),-.048*math.cos(2*f))
    padre = "cuerpo"
    for j in range(1,4):
        hueso = f"cola_{j}"
        torsion(hueso,padre,.054*math.sin(f-j*.61),(.056+.012*j)*math.sin(f-j*.87))
        padre = hueso

    resultado = []
    for pata in patas:
        nueva,giro_pie,apoya,error = cadena_pose(pata,ciclo,fase,dz)
        for j,h in enumerate(pata["huesos"]):
            if j == 3:
                matrices = (giro_pie @ restos[h].to_3x3()).to_4x4()
                matrices.translation = nueva[j]
                poses[h] = matrices
            else:
                poses[h] = direccionar(restos[h],nueva[j],nueva[j+1])
        resultado.append((pata["nombre"],apoya,error))
    return poses,resultado


def aplicar_pose(rig, poses):
    for hueso in rig.pose.bones:
        padre = hueso.parent
        if not padre:
            hueso.matrix_basis = hueso.bone.matrix_local.inverted() @ poses[hueso.name]
        else:
            hueso.matrix_basis = hueso.bone.convert_local_to_pose(
                poses[hueso.name],hueso.bone.matrix_local,
                parent_matrix=poses[padre.name],parent_matrix_local=padre.bone.matrix_local,invert=True)


def animar(rig, patas, clips):
    escena = bpy.context.scene
    escena.render.fps = 24
    escena.frame_start,escena.frame_end = 1,clips["reposo"]["fotogramas"]+1
    rig.animation_data_create()
    informe = {}
    # Un clip por pista NLA. Reposo queda arriba para que sea la postura al abrir Blender.
    for nombre,ciclo in reversed(list(clips.items())):
        error_contacto = 0
        for n in range(ciclo["fotogramas"]+1):
            poses,apoyos = matrices_pose(rig,patas,nombre,ciclo,n/ciclo["fotogramas"])
            aplicar_pose(rig,poses)
            error_contacto = max(error_contacto, *(error for _,a,error in apoyos if a))
            for h in rig.pose.bones:
                if h.name=="raiz_esqueleto":
                    continue
                h.keyframe_insert(data_path="rotation_quaternion",frame=1+n,group=h.name)
                h.keyframe_insert(data_path="location",frame=1+n,group=h.name)
        accion = rig.animation_data.action
        slot = rig.animation_data.action_slot
        accion.name = nombre
        accion.use_fake_user = True
        canales = accion.layers[0].strips[0].channelbag(slot).fcurves
        for canal in canales:
            for clave in canal.keyframe_points:
                clave.interpolation = "LINEAR"
        rig.animation_data.action = None
        pista = rig.animation_data.nla_tracks.new()
        pista.name = nombre
        tira = pista.strips.new(nombre,1,accion)
        tira.action_slot = slot
        tira.extrapolation = "HOLD"
        informe[nombre] = {
            "duracion_s": ciclo["fotogramas"]/24,
            "zancada_m": ciclo["zancada_m"],
            "error_maximo_alcance_apoyo_m": round(error_contacto,5),
        }
    escena.frame_set(1)
    return informe
