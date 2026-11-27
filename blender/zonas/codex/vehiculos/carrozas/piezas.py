"""Construcción de ruedas de radios, bastidor de giro y herrajes de carruaje."""
import math

import bpy
from mathutils import Vector

from kit_vehiculo_bpy import (
    crear_caja, crear_cilindro, crear_malla, crear_torno, crear_tubo, crear_vacio,
    interpolar_hermite, material_pbr,
)


def materiales(datos):
    metal = {"hierro": 0.30, "aro": 0.54, "laton": 0.64, "filete": 0.38}
    rugoso = {"capota": 0.88, "cuero": 0.67, "crema": 0.65, "piso": 0.84,
              "roble": 0.58, "azul": 0.42, "azul_borde": 0.42, "vidrio": 0.23}
    paleta = {}
    for nombre, color in datos["paleta"].items():
        m = material_pbr(f"{nombre}__{color[1:].lower()}", color, rugoso.get(nombre, 0.52),
                         metal.get(nombre, 0), alpha=0.49 if nombre == "vidrio" else 1)
        if nombre == "vidrio_farol":
            bsdf = m.node_tree.nodes.get("Principled BSDF")
            bsdf.inputs["Emission Color"].default_value = m.diffuse_color
            bsdf.inputs["Emission Strength"].default_value = .56
        paleta[nombre] = m
    return paleta


def loft(nombre, anillos, mat, padre):
    """Cierra un volumen con secciones homólogas, sin polos degenerados."""
    n = len(anillos[0])
    caras = [tuple(reversed(range(n)))]
    for i in range(len(anillos)-1):
        for k in range(n):
            a, b = i*n+k, i*n+(k+1) % n
            caras.append((a, b, b+n, a+n))
    caras.append(tuple(range((len(anillos)-1)*n, len(anillos)*n)))
    return crear_malla(nombre, [p for anillo in anillos for p in anillo], caras, mat, padre, True)


def redondeado(x0, x1, y0, y1, radio, pasos=5):
    salida = []
    for x, y, a in ((x1-radio, y1-radio, 0), (x0+radio, y1-radio, 90),
                    (x0+radio, y0+radio, 180), (x1-radio, y0+radio, 270)):
        for i in range(pasos+1):
            rad = math.radians(a + 90*i/pasos)
            salida.append((x+radio*math.cos(rad), y+radio*math.sin(rad)))
    return salida


def banda(nombre, perfil, mat, padre, ancho=.1, z_extra=0):
    """Pletina curvada en alzado, con espesor y canto superior e inferior."""
    return loft(nombre, [[(x, y-ancho/2, z), (x, y+ancho/2, z),
                          (x, y+ancho/2, z+z_extra), (x, y-ancho/2, z+z_extra)]
                         for x, y, z in perfil], mat, padre)


def curva_2d(perfil, etapas=36):
    a, b = perfil[0][0], perfil[-1][0]
    xs = [a+(b-a)*i/etapas for i in range(etapas+1)]
    return [(x, interpolar_hermite(perfil, x)) for x in xs]


def esfera(nombre, centro, escala, mat, padre, segmentos=16, anillos=8):
    bpy.ops.mesh.primitive_uv_sphere_add(segments=segmentos, ring_count=anillos, location=centro)
    obj = bpy.context.object
    obj.name = nombre
    obj.scale = escala
    from kit_vehiculo_bpy import vincular
    for cara in obj.data.polygons:
        cara.use_smooth = True
    return vincular(obj, mat, padre)


def tubo(nombre, puntos, radio, mat, padre, cerrado=False):
    return crear_tubo(nombre, puntos, radio, mat, padre, cerrado, resolucion=1)


def tubo_curvo(nombre, puntos, radio, mat, padre):
    """Interpola los tramos de una forja curva conservando sus extremos."""
    claves = [Vector(p) for p in puntos]
    muestras = []
    for j, (a,b) in enumerate(zip(claves,claves[1:])):
        m0 = .44*(b-claves[max(j-1,0)])
        m1 = .44*(claves[min(j+2,len(claves)-1)]-a)
        for n in range(5):
            t = n/5
            muestras.append(tuple((2*t**3-3*t**2+1)*a+(t**3-2*t**2+t)*m0
                                +(-2*t**3+3*t**2)*b+(t**3-t**2)*m1))
    muestras.append(tuple(claves[-1]))
    return tubo(nombre,muestras,radio,mat,padre)


def ruedas_y_bastidor(datos, grupos, mat):
    raiz, deco = grupos["raiz"], grupos["decoracion"]
    xt, xd = datos["ejes"]
    rt, rd = (datos["radios_ruedas"][k] for k in ("trasera", "delantera"))
    semi = datos["semivia_ruedas"]
    dorado = "oro" in mat
    color_radios = mat["oro" if dorado else "azul"]
    color_aro = mat["oro" if dorado else "azul_borde"]
    metal = mat["hierro"]
    pivote = crear_vacio("tornamesa_delantera", (xd, 0, rd), raiz)
    grupos["tornamesa"] = pivote
    for eje, x, r, padre in (("trasera", xt, rt, raiz), ("delantera", xd, rd, pivote)):
        bpy.context.view_layer.update()
        crear_cilindro(f"Eje de rueda {eje}", (x, 0, r), .039, 2*semi, metal, padre, lados=16)
        for s, lado in ((1, "izquierda"), (-1, "derecha")):
            nombre = f"{eje}_{lado}"
            if eje == "delantera":
                direccion = crear_vacio(f"direccion_{nombre}", (0, s*semi, 0), pivote)
                ancla = (0, 0, 0)
            else:
                direccion, ancla = raiz, (x, s*semi, r)
            rueda = crear_vacio(f"rueda_{nombre}", ancla, direccion)
            grupos[f"rueda_{nombre}"] = rueda
            bpy.context.view_layer.update()
            y = s*semi
            # Dos secciones torneadas distintas, banda de hierro y llanta de madera.
            for sufijo, perfil, material in (
                ("Aro de hierro", [(r-.016,-.045),(r-.006,-.043),(r,-.031),(r,.031),
                                    (r-.006,.043),(r-.016,.045),(r-.025,.038),(r-.025,-.038)], mat["aro"]),
                ("Llanta de madera", [(r-.022,-.037),(r-.015,-.026),(r-.015,.026),(r-.022,.039),
                                      (r-.048,.037),(r-.065,.025),(r-.065,-.025),(r-.048,-.037)], color_aro),
                ("Cubo", [(.087,-.080),(.103,-.056),(.100,-.031),(.078,-.021),(.078,.033),
                          (.094,.054),(.094,.076),(.077,.097),(.055,.100),(.040,.089),
                          (.038,-.080)], metal if dorado else color_aro),
            ):
                crear_torno(f"{sufijo} {nombre}", perfil, x, y, r, s, material, rueda, 48, cerrado=True)
            if not dorado:
                crear_torno(f"Filo de latón {nombre}", [(r-.020,.043),(r-.016,.045),
                            (r-.013,.044),(r-.017,.041)], x, y, r, s, mat["laton"], rueda, 48, cerrado=True)
            esfera(f"Tuerca de {nombre}", (x, y+s*.099, r), (.048,.023,.048),
                   mat["hierro" if dorado else "laton"], rueda)
            if dorado:
                for i in range(6):
                    a = i * math.tau/6
                    crear_cilindro("Remache del cubo", (x+.065*math.cos(a), y+s*.089, r+.065*math.sin(a)),
                                  .010, .015, mat["aro"], rueda, lados=8)
            n = datos["radios"][eje]
            for i in range(n):
                a = (i+.26)*math.tau/n
                u = Vector((math.cos(a), 0, math.sin(a)))
                v = Vector((-math.sin(a), 0, math.cos(a)))
                w = Vector((0,1,0))
                secciones = []
                for largo, grueso, ancho, canal in ((.065,.028,.023,.005),(.116,.024,.019,.010),
                        (r*.57,.015,.016,.005),(r-.068,.018,.019,-.005),(r-.040,.024,.023,-.006)):
                    centro = Vector((x, y+s*canal, r)) + largo*u
                    secciones.append([tuple(centro+v*ancho*math.cos(j*math.tau/8)+w*grueso*math.sin(j*math.tau/8))
                                      for j in range(8)])
                loft(f"Radio torneado {nombre}", secciones, color_radios, rueda)

    color_chasis = mat["oro"] if dorado else metal
    for s in [-1, 1]:
        y = s*.33
        perfil = [(xt-.22,rt+.10),(xt+.32,rt+.05),(.30,.68),(xd-.37,rd+.24),(xd-.04,rd+.31)]
        banda("Larguero curvo del bastidor", [(x,y,z) for x,z in curva_2d(perfil, 22)],
              color_chasis, deco, .075, .065)
        for eje, x, r, padre in (("posterior",xt,rt,deco),("anterior",xd,rd,pivote)):
            for i in range(4):
                z0 = r+.106+i*.017
                perfil = [(x-.34+i*.030,z0+.055),(x-.18,z0+.014),(x,z0),(x+.18,z0+.014),(x+.34-i*.030,z0+.055)]
                banda(f"Ballesta {eje}", [(u,s*.45,z) for u,z in curva_2d(perfil, 14)], metal, padre, .043, .012)
            crear_caja("Abrazadera de ballesta", (x,s*.45,r+.145), (.12,.061,.22), metal, padre, .009)
            for extremo in (-1, 1):
                crear_caja("Gemela de la ballesta", (x+extremo*.295,s*.45,r+.218),
                           (.052,.063,.13),metal,padre,.010)
        # La corona carga la caja mediante una cama fija estrecha, libre de las ruedas al girar.
        tubo_curvo("Cartabón entre la caja y la corona",[
            (xd-.20,s*.28,rd+.281),(xd-.28,s*.31,rd+.43),
            (xd-.47,s*.34,rd+.628),(xd-.64,s*.35,rd+.730)],.046,metal,deco)
        tubo_curvo("Pendolón posterior del bastidor",[
            (xt+.17,s*.333,rt+.12),(xt+.095,s*.394,rt+.225),
            (xt+.07,s*.435,rt+(.51 if dorado else .292))],.042,color_chasis,deco)
    for x,z in ((xt+.16,rt+.16),(xd-.16,rd+.31),(xd-.59,rd+.69)):
        crear_caja("Travesaño de la caja al bastidor",(x,0,z),(.085,.76,.071),color_chasis,deco,.012)
    for rr, zz in ((.31,rd+.225),(.265,rd+.257),(.10,rd+.273)):
        crear_cilindro("Corona de tornamesa", (xd,0,zz), rr,.036,metal,pivote,eje="Z",lados=32)

    inicio = datos["enganche"]["inicio_varas_desde_eje_m"]
    tiro = crear_vacio("tiro", padre=pivote)
    varas = crear_vacio("varas_caballo", padre=tiro)
    bpy.context.view_layer.update()
    for s in (-1, 1):
        # La horquilla corta es visible con la carroza sola. Las varas continúan hacia el caballo.
        p0 = (xd+inicio, s*.44, rd+.443)
        tubo_curvo("Horquilla curva del tiro", [(xd-.20,s*.32,rd+.27), (xd+.22,s*.39,rd+.32),
             (xd+inicio-.14,s*.44,rd+.421), p0], .033, color_chasis, tiro)
        crear_caja("Herraje de horquilla", p0, (.10,.09,.074), metal, tiro, .012)
        p1 = (xd+datos["enganche"]["distancia_al_eje_delantero_m"]+.28,s*.36, .99)
        tubo_curvo("Vara de tiro para un caballo", [p0, (xd+inicio+.36,s*.43,1.01),
             (p1[0]-.22,s*.38,1.005),p1], .026, color_chasis, varas)
        crear_cilindro("Pasador de la vara", p1, .017, .060, metal, varas, lados=12)
        lado = "izquierda" if s>0 else "derecha"
        crear_vacio(f"vara_punta_{lado}", (p1[0]-xd,p1[1],p1[2]-rd), varas)
        crear_vacio(f"tirante_{lado}", (inicio-.13,s*.365,.38), tiro)
    crear_cilindro("Balancín de los tiros", (xd+inicio-.13,0,rd+.38), .036,
                  .76, metal, tiro, lados=16)
    crear_caja("Travesaño frontal", (xd+inicio-.18,0,rd+.37), (.072,1.04,.059), color_chasis, tiro, .014)
