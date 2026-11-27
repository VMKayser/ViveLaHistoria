"""Reconstrucción del escaneo y acabado pictórico propio para el caballo."""
import math
from collections import defaultdict

import bmesh
import bpy
import numpy as np
from mathutils import Matrix, Vector
from mathutils.kdtree import KDTree
from mathutils.noise import noise_vector

from kit_vehiculo_bpy import crear_vacio, hex_a_rgba_lineal, material_pbr
from piezas import esfera, loft, tubo


def activar(o):
    bpy.ops.object.select_all(action="DESELECT")
    o.select_set(True)
    bpy.context.view_layer.objects.active = o


def reconstruir(archivo, datos, raiz):
    bpy.ops.import_scene.gltf(filepath=str(archivo))
    objetos = [o for o in bpy.context.scene.objects if o != raiz]
    mallas = [o for o in objetos if o.type == "MESH"]
    escala = datos["escala"]
    conversion = Matrix.Diagonal((-escala,-escala,escala,1)) @ Matrix.Translation(
        -Vector(datos["centro_escaneo"]))
    bm = bmesh.new()
    for o in mallas:
        me = o.data.copy()
        me.transform(conversion @ o.matrix_world)
        bm.from_mesh(me)
        bpy.data.meshes.remove(me)
    bmesh.ops.remove_doubles(bm,verts=list(bm.verts),dist=.00013)
    bmesh.ops.holes_fill(bm,edges=[e for e in bm.edges if e.is_boundary],sides=0)
    bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces))
    ma = bpy.data.meshes.new("Superficie continua del escaneo")
    bm.to_mesh(ma)
    bm.free()
    o = bpy.data.objects.new("Pelaje modelado del caballo",ma)
    bpy.context.collection.objects.link(o)
    o.parent = raiz
    for original in objetos:
        bpy.data.objects.remove(original, do_unlink=True)
    bpy.data.orphans_purge(do_local_ids=True, do_linked_ids=True, do_recursive=True)
    activar(o)
    ma.remesh_voxel_size = .008
    bpy.ops.object.voxel_remesh()
    limpiar_superficie(o)
    for tipo, opciones in (("SMOOTH",{"factor": .74, "iterations": 5}),
                           ("DECIMATE", {"ratio": min(1, 19000/len(o.data.polygons)/2)})):
        mod = o.modifiers.new("Afinar superficie",tipo)
        for nombre, valor in opciones.items():
            setattr(mod,nombre,valor)
        bpy.ops.object.modifier_apply(modifier=mod.name)
    limpiar_superficie(o, triangular=True)
    for p in o.data.polygons:
        p.use_smooth = True
    for uv in list(o.data.uv_layers):
        o.data.uv_layers.remove(uv)
    return o


def limpiar_superficie(obj, triangular=False, descartar_islas=True):
    bm = bmesh.new()
    bm.from_mesh(obj.data)
    pendientes = set(bm.verts)
    islas = []
    while pendientes:
        v = pendientes.pop()
        isla, cola = [v], [v]
        while cola:
            actual = cola.pop()
            for e in actual.link_edges:
                candidato = e.other_vert(actual)
                if candidato in pendientes:
                    pendientes.remove(candidato)
                    cola.append(candidato)
                    isla.append(candidato)
        islas.append(isla)
    sueltas = [v for isla in islas if len(isla) < 40 for v in isla]
    if sueltas and descartar_islas:
        bmesh.ops.delete(bm,geom=sueltas,context="VERTS")
    if triangular:
        bmesh.ops.dissolve_degenerate(bm,dist=.00002,edges=list(bm.edges))
        bmesh.ops.triangulate(bm,faces=list(bm.faces))
        restos = [f for f in bm.faces if f.calc_area()<1e-11]
        bmesh.ops.delete(bm,geom=restos,context="FACES")
    bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces))
    bm.to_mesh(obj.data)
    bm.free()


def suave(a,b,x):
    t = max(0,min(1,(x-a)/(b-a)))
    return t*t*(3-2*t)


def mezclar(a,b,t):
    return (1-t)*a+t*b


def acabado(obj, patas):
    """Pinta albedo por regiones anatómicas y guarda la pintura por vértice."""
    paleta = {k:np.array(hex_a_rgba_lineal(v)[:3]) for k,v in {
        "castano":"#875139","dorado":"#ad6a44","sombra":"#61382d","crin":"#33242a",
        "hebra":"#62413b","morro":"#634345","belfo":"#805c58","lucero":"#ebcda7",
        "casco":"#4a403f","calcetin":"#cba686","cuero":"#332b2c",
    }.items()}
    mat = material_pbr("Pelaje castaño pintado", "#ffffff", .77)
    nodo = mat.node_tree.nodes.new("ShaderNodeVertexColor")
    nodo.layer_name = "Albedo Pintado"
    mat.node_tree.links.new(nodo.outputs["Color"],mat.node_tree.nodes["Principled BSDF"].inputs["Base Color"])
    obj.data.materials.clear()
    obj.data.materials.append(mat)
    capa = obj.data.color_attributes.new(name=nodo.layer_name,type="FLOAT_COLOR",domain="POINT")
    obj.data.color_attributes.active_color = capa
    salida = np.ones((len(obj.data.vertices),4),np.float32)
    for v in obj.data.vertices:
        x,y,z = v.co
        ruido = noise_vector(Vector((x*13,y*13,z*13)))[0]
        matiz = noise_vector(Vector((x*4,y*5,z*4)))[1]
        base = mezclar(paleta["castano"], paleta["dorado"], suave(-.045,.60,.16+matiz*.36))
        barriga = suave(1.014,.72,z)*suave(.42,.02,abs(x))
        lomo = suave(1.10,1.24,z)*suave(.47,.28,abs(x))
        base = mezclar(base,paleta["sombra"],.39*lomo)
        base = mezclar(base,paleta["sombra"],.46*barriga)
        crin = suave(.243,.350,x)*suave(1.070,1.187,z)*suave(.912,.853,x)
        # La crin cae más sobre el flanco derecho de la nuca y del cuello.
        borde = .388 + (z-1.19)*.92 + .013*math.sin(z*86) - (.084 if y>0 else 0)
        crin *= suave(.018,-.019,x-borde)
        cola = suave(-.619,-.736,x)*suave(.806,.870,z)
        frente = suave(.944,1.007,x)*suave(1.636,1.553,z)
        base = mezclar(base,paleta["morro"], frente*.84)
        belfo = suave(1.038,1.174,x)*suave(1.485,1.430,z)
        base = mezclar(base,paleta["belfo"], belfo*.64)
        mancha_x = .956+.75*(1.65-z)
        lista = suave(.041,.026,abs(y+.008+math.sin(z*25)*.006))*suave(1.408,1.487,z)
        lista *= suave(.050,.028,abs(x-mancha_x))*suave(1.72,1.678,z)
        base = mezclar(base,paleta["lucero"],.93*lista)
        fibras = .31*ruido+.42*math.sin(math.tau*(20*y+10*(x-.87*z))+2.0*matiz)
        veta = mezclar(paleta["crin"],paleta["hebra"],suave(-.18,.53,fibras+.13))
        base = mezclar(base,veta,max(crin,cola))
        if z<.43:
            miembro = min(patas, key=lambda p:distancia_segmento(v.co,puntos_distales(p))[0])
            a,b = miembro["puntos"][-2:]
            eje = (b-a).normalized()
            along = (v.co-a).dot(eje)
            if miembro["nombre"] in {"mano_izquierda","pata_izquierda"}:
                base = mezclar(base,paleta["calcetin"],.90*suave(.137,.048,z)
                               if miembro["nombre"].startswith("mano") else .73*suave(-.031,.014,along))
            base = mezclar(base,paleta["casco"],suave(.039,.075,along))
        salida[v.index,:3] = np.clip(base*(1+.075*ruido+.125*matiz), .01, .82)
    capa.data.foreach_set("color",salida.ravel())


def puntos_distales(pata):
    return pata["puntos"][-2:]


def distancia_segmento(p, segmento):
    a,b = segmento
    ab = b-a
    t = (p-a).dot(ab)/ab.length_squared
    return (p-(a+max(0,min(1,t))*ab)).length, t


def pesos(obj, patas, articulaciones):
    """Cuatro influencias por vértice, con transiciones en las articulaciones."""
    nombres = ["cuerpo",*articulaciones]
    nombres = list(dict.fromkeys(nombres+[
        nombre for pata in patas for nombre in pata["huesos"]]))
    grupos = {k:obj.vertex_groups.new(name=k) for k in nombres}
    bruto_patas = [[] for _ in patas]
    pesos_por_vertice = []

    for v in obj.data.vertices:
        p = v.co
        x,y,z = p
        valores = defaultdict(float)
        valores["cuerpo"] = 1
        if x>.23 and z>.98:
            n = suave(.995,1.25,z)*suave(.23,.59,x)
            nuca = suave(1.29,1.56,z)*suave(.61,.81,x)
            cabeza = max(suave(.787,.974,x)*suave(1.33,1.46,z),
                         suave(1.59,1.75,z)*suave(.764,.864,x))
            valores.update(cuerpo=1-n,cuello=n*(1-nuca)*(1-cabeza),nuca=(n*nuca)*(1-cabeza))
            valores["cuerpo"] *= 1-cabeza
            valores["cabeza"] = cabeza
        if z>1.676:
            oreja = suave(1.681,1.755,z)*suave(.023,.056,abs(y+.006))
            valores["cabeza"] *= 1-oreja
            valores["oreja_derecha" if y<0 else "oreja_izquierda"] = oreja
        if x<-.586 and z>.814:
            cola = suave(-.590,-.74,x)*suave(.820,.963,z)*(1-suave(.09,.18,abs(y-.025)))
            punta = suave(-1.009,-1.157,x)
            media = suave(-.817,-.946,x)
            valores["cuerpo"] *= 1-cola
            valores.update(cola_1=cola*(1-media),cola_2=cola*media*(1-punta),cola_3=cola*media*punta)
        if z<1.19:
            opciones = []
            pierna = suave(1.188,.712,z)
            for j,pata in enumerate(patas):
                medidas = [distancia_segmento(p,seg) for seg in zip(pata["puntos"],pata["puntos"][1:])]
                menor = min(d for d,t in medidas)
                influye = pierna*suave(.36,.075,menor)
                if influye>.001:
                    opciones.append((menor,j,medidas,influye))
            if opciones:
                distancia,j,medidas,influye = min(opciones)
                pata = patas[j]
                for k in list(valores):
                    valores[k] *= 1-influye
                # En el casco la deformación se mantiene rígida por debajo del menudillo.
                t_pie = medidas[3][1]
                pie = suave(-.20,.35,t_pie)*suave(.10,.038,medidas[3][0])
                partes = [math.exp(-max(0,d-distancia)/.034) for d,t in medidas[:3]]
                suma = sum(partes)
                for k,nombre in enumerate(pata["huesos"][:3]):
                    valores[nombre] = influye*(1-pie)*partes[k]/suma
                valores[pata["huesos"][3]] = influye*pie
                if influye*pie>.87:
                    bruto_patas[j].append(p.copy())
        pesos_por_vertice.append(dict(valores))

    vecinos = [[] for _ in obj.data.vertices]
    for e in obj.data.edges:
        a,b = e.vertices
        vecinos[a].append(b)
        vecinos[b].append(a)
    for _ in range(3):
        suaves = []
        for j,pesos in enumerate(pesos_por_vertice):
            entorno = vecinos[j]
            if not entorno or max((peso for k,peso in pesos.items() if k.endswith("_casco")),default=0)>.91:
                suaves.append(pesos)
                continue
            media = defaultdict(float,{k:.55*v for k,v in pesos.items()})
            for otro in entorno:
                for nombre,peso in pesos_por_vertice[otro].items():
                    media[nombre] += .45*peso/len(entorno)
            suaves.append(media)
        pesos_por_vertice = suaves
    for j,valores in enumerate(pesos_por_vertice):
        relevantes = sorted(((k,w) for k,w in valores.items() if w>.002),key=lambda kw:-kw[1])[:4]
        total = sum(w for _,w in relevantes)
        for k,w in relevantes:
            grupos[k].add([j],w/total,"REPLACE")
    for pata,puntos in zip(patas,bruto_patas):
        pata["suela"] = puntos
        assert len(puntos)>10, f"Falta muestra de casco {pata['nombre']}"


def accesorios(raiz, rig):
    cuero = material_pbr("Cuero de los arreos","#443034",.73)
    vivo = material_pbr("Borde de cuero bruñido","#795046",.60)
    oro = material_pbr("Hebillas de latón envejecido","#b98a51",.45,.56)
    iris = material_pbr("Iris castaño del caballo","#51302b",.3)
    pupila = material_pbr("Pupila del caballo","#25202a",.27)
    belfo = material_pbr("Interior de ollares","#4b3031",.78)

    def banda(nombre, puntos, ancho, esp, material):
        secciones = [[(x+dx,y,z+dz) for dx,dz in
            ((-esp,-ancho),(-esp,ancho),(esp,ancho),(esp,-ancho))]
            for x,y,z in puntos]
        return loft(nombre,secciones,material,raiz)

    # Pechera cruzada delante del pecho y cincha dorsal a nivel del enganche.
    pechera = [(.593,-.205,1.034),(.726,-.183,1.041),(.783,-.095,1.064),
        (.795,0,1.067),(.783,.095,1.064),(.728,.183,1.038),(.595,.206,1.031)]
    banda("Pechera de cuero ancho",pechera,.026,.010,cuero)
    for delta in (-.023,.023):
        tubo("Costura de la pechera",[(x+.011,y,z+delta) for x,y,z in pechera],.0037,vivo,raiz)
    tubo("Cincha de sillín",[(.342,-.158,.861),(.367,-.235,.946),(.389,-.243,1.023),
         (.388,-.189,1.135),(.384,-.100,1.225),(.389,0,1.251),(.392,.112,1.219),
         (.398,.195,1.149),(.395,.235,1.027),(.393,.216,.94),(.378,.146,.862)],.019,cuero,raiz)
    esfera("Sillín de tiro",(.389,0,1.248),(.116,.117,.037),cuero,raiz)
    for s,lado in ((-1,"derecha"),(1,"izquierda")):
        tubo("Correa de sostén de la pechera",[(.422,s*.114,1.24),(.518,s*.144,1.179),
             (.655,s*.186,1.042)],.013,cuero,raiz)
        tubo("Correa de la vara",[(.409,s*.218,1.055),(.369,s*.281,.984),
             (.316,s*.307,.980),(.347,s*.294,1.065),(.409,s*.218,1.055)],.010,vivo,raiz)
        tubo("Hebilla de la pechera",[(.57+.026*math.cos(j*math.tau/16),s*.219,
             1.032+.027*math.sin(j*math.tau/16)) for j in range(16)],.007,oro,raiz,True)
        for nombre,co,hueso in (
            ("tiro",(.57,s*.224,1.033),"cuerpo"),
            ("cincha",(.340,s*.298,.992),"cuerpo"),
            ("bocado",(1.085,s*.070,1.443),"cabeza"),
        ):
            a = crear_vacio(f"{nombre}_caballo_{lado}",co,raiz)
            bpy.context.view_layer.update()
            fijar_a_hueso(a, rig, hueso)
        for nombre, puntos, radio, material in [
            ("Testera",[(.870,s*.056,1.711),(.867,s*.081,1.647),(.914,s*.083,1.572),
                        (.993,s*.071,1.505),(1.091,s*.063,1.438)],.009,cuero),
            ("Aro de bocado",[(1.08+.025*math.cos(j*math.tau/18),s*.068,
                        1.443+.025*math.sin(j*math.tau/18)) for j in range(18)],.005,oro),
        ]:
            tubo(nombre,puntos,radio,material,raiz,nombre=="Aro de bocado")
        # El escaneo proporciona la cuenca. Iris y pupila pequeños, colocados al ras.
        esfera("Iris visible",(.932, s*.087-.008,1.607),(.023,.010,.018),iris,raiz,12,7)
        esfera("Pupila visible",(.936, s*.095-.008,1.607),(.012,.004,.009),pupila,raiz,12,7)
        esfera("Ollar", (1.149,s*.049-.009,1.474),(.022,.012,.012),belfo,raiz,12,7)
    tubo("Frontalera",[(.911,-.080,1.627),(.946,-.050,1.643),(.966,0,1.647),
         (.944,.05,1.641),(.911,.081,1.628)],.009,cuero,raiz)
    tubo("Muserola",[(1.053,-.073,1.461),(1.092,-.061,1.492),(1.113,0,1.505),
         (1.093,.058,1.49),(1.05,.068,1.459)],.010,cuero,raiz)
    bpy.context.view_layer.update()

    # Los arreos acompañan al hueso que los sostiene. Conserva su posición de reposo.
    fijos = []
    for o in list(raiz.children):
        if o.type not in {"CURVE","MESH"} or o.name.startswith("Pelaje"):
            continue
        if o.name.startswith(("Testera","Frontalera","Aro de bocado","Muserola","Iris","Pupila","Ollar")):
            fijar_a_hueso(o, rig, "cabeza")
        else:
            fijos.append(o)
    for o in fijos:
        fijar_a_hueso(o, rig, "cuerpo")
    consolidar_arreo(rig)


def consolidar_arreo(rig):
    curvas = [o for o in rig.children if o.parent_type=="BONE" and o.type=="CURVE"]
    if curvas:
        activar(curvas[0])
        for o in curvas:
            o.select_set(True)
        bpy.ops.object.convert(target="MESH")
    por_material = defaultdict(list)
    for o in rig.children:
        if o.parent_type=="BONE" and o.type=="MESH":
            por_material[(o.parent_bone,o.data.materials[0].name)].append(o)
    for (hueso,mat),objetos in por_material.items():
        activo = objetos[0]
        activar(activo)
        for o in objetos:
            o.select_set(True)
        if len(objetos)>1:
            bpy.ops.object.join()
        activo.name = f"{hueso} · {mat}"
        for uv in list(activo.data.uv_layers):
            activo.data.uv_layers.remove(uv)
        limpiar_superficie(activo, triangular=True, descartar_islas=False)


def fijar_a_hueso(o, rig, hueso):
    mundo = o.matrix_world.copy()
    o.parent = rig
    o.parent_type = "BONE"
    o.parent_bone = hueso
    bpy.context.view_layer.update()
    o.matrix_world = mundo
