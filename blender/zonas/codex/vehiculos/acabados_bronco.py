"""Superficies continuas y ruedas del BRONCO, desde la referencia del usuario."""
import math

import bmesh
import bpy
from mathutils import Vector


def interpolar(perfil, x):
    """Hermite monótono: tangencias suaves, sin pasarse de los controles."""
    if x <= perfil[0][0]:
        return perfil[0][1]
    if x >= perfil[-1][0]:
        return perfil[-1][1]
    pendientes = [(b[1] - a[1]) / (b[0] - a[0]) for a, b in zip(perfil, perfil[1:])]
    tangentes = [pendientes[0]]
    for a, b in zip(pendientes, pendientes[1:]):
        tangentes.append(0 if a * b <= 0 else 2 * a * b / (a + b))
    tangentes.append(pendientes[-1])
    for i, (a, b) in enumerate(zip(perfil, perfil[1:])):
        if a[0] <= x <= b[0]:
            h = b[0] - a[0]
            t = (x - a[0]) / h
            return ((2*t**3 - 3*t*t + 1) * a[1] + (t**3 - 2*t*t + t) * h * tangentes[i]
                    + (-2*t**3 + 3*t*t) * b[1] + (t**3 - t*t) * h * tangentes[i+1])


def contorno_redondeado(perfil, radio=.045, pasos=3):
    """Filetes cuadráticos tangentes a ambos lados de cada esquina."""
    salida = []
    for i, punto in enumerate(perfil):
        b = Vector(punto)
        a = Vector(perfil[i - 1])
        c = Vector(perfil[(i + 1) % len(perfil)])
        distancia = min(radio, (a - b).length * .3, (c - b).length * .3)
        inicio = b + (a - b).normalized() * distancia
        final = b + (c - b).normalized() * distancia
        for j in range(pasos + 1):
            t = j / pasos
            salida.append(tuple((1-t)**2 * inicio + 2*t*(1-t)*b + t*t*final))
    return salida


def techo_curvo(crear_malla, materiales):
    altos = [(-3.18, 2.88), (-3.10, 3.02), (-2.94, 3.15),
             (2.40, 3.15), (2.61, 3.08), (2.76, 2.86)]
    anchos = [(-3.18, .92), (-3.10, 1), (-2.94, 1), (2.40, 1), (2.61, 1), (2.76, .96)]
    xs = []
    for a, b in zip(altos, altos[1:]):
        n = 1 if a[1] == b[1] else max(4, math.ceil((b[0] - a[0]) / .18))
        xs.extend(a[0] + (b[0] - a[0]) * j / n for j in range(n))
    xs.append(altos[-1][0])
    # Techo plano en el centro y hombros elípticos con tangencia horizontal.
    lado = [(.62 + .38 * math.sin(math.pi * i / 20),
             1 - math.cos(math.pi * i / 20)) for i in range(11)]
    perfil = [(-y, k) for y, k in reversed(lado)] + lado
    vs = []
    for x in xs:
        alto, ancho = interpolar(altos, x), interpolar(anchos, x)
        vs.extend((x, y * ancho, alto - k * (alto - 2.81)) for y, k in perfil)
    n = len(perfil)
    caras = [(i*n+j, i*n+j+1, (i+1)*n+j+1, (i+1)*n+j)
             for i in range(len(xs)-1) for j in range(n-1)]
    o = crear_malla("Techo de hombros curvos", vs, caras, materiales["techo"])
    for p in o.data.polygons:
        p.use_smooth = True
    mod = o.modifiers.new("Espesor techo", "SOLIDIFY")
    mod.thickness = .035
    bpy.context.view_layer.objects.active = o
    bpy.ops.object.modifier_apply(modifier=mod.name)
    for x in [xs[0], xs[-1]]:
        alto, ancho = interpolar(altos, x), interpolar(anchos, x)
        vertices = [(x, y * ancho, alto - k * (alto - 2.81)) for y, k in perfil]
        crear_malla("Cierre de techo", vertices, [tuple(range(len(vertices)))], materiales["techo"])


def curvar_cabina(datos):
    """Deforma conjuntamente chapas, marcos, cristales y piezas del morro."""
    ajustes = datos["acabados"]
    radio = ajustes["radio_esquina_frontal"]

    def transformar(co):
        x, y, z = co
        if x < 2.28 or z > 2.94:
            return Vector(co)
        t = max(0, min(1, (x - 2.28) / .55))
        peso = t*t*(3-2*t)
        f = max(0, min(1, (2.94-z) / .15))
        f = f*f*(3-2*f)
        frente_original = 3.17 - max(0, z-1.72)*.435
        desplazamiento = (interpolar(ajustes["perfil_frontal"], z) - frente_original) * peso * f
        # Redondeo en planta: la chapa frontal gira hacia los flancos.
        ancho = 1.07 - max(0, z-1.72)*.067
        ox, oy = x - (frente_original-radio), abs(y) - (ancho-radio)
        xx, yy = x, y
        if ox > 0 and oy > 0 and abs(y) < 1.17:
            largo = math.hypot(ox, oy)
            if largo > radio:
                k = radio / largo
                xx = frente_original-radio + ox*k
                yy = math.copysign(ancho-radio + oy*k, y)
        return Vector((x + (xx-x)*f + desplazamiento, y + (yy-y)*f, z))

    for o in list(bpy.context.scene.objects):
        if o.type != "MESH" or o.parent.name.startswith("rueda_"):
            continue
        if not any((o.matrix_world @ v.co).x > 2.28 for v in o.data.vertices):
            continue
        # Las superficies grandes reciben geometría suficiente para la curva.
        if any(n in o.name for n in ["Panel frontal", "Panel faros", "Chapa azul", "Cintura blanca",
                                    "Banda azul", "Pilar A", "Cristal de cabina", "Parabrisas", "Franja azul",
                                    "Parachoques delantero", "Labio superior parachoques"]):
            bm = bmesh.new()
            bm.from_mesh(o.data)
            for _ in range(3):
                edges = [e for e in bm.edges if e.calc_length() > .22 and
                         max((o.matrix_world @ v.co).x for v in e.verts) > 2.28]
                if not edges:
                    break
                bmesh.ops.subdivide_edges(bm, edges=edges, cuts=1, use_grid_fill=True)
            bm.to_mesh(o.data)
            bm.free()
            for p in o.data.polygons:
                p.use_smooth = True
        inversa = o.matrix_world.inverted()
        for v in o.data.vertices:
            v.co = inversa @ transformar(o.matrix_world @ v.co)
        o.data.update()


def torno(nombre, perfil, x, yc, zc, signo, mat, grupo, crear_malla,
          segmentos=64, cerrado=False, dibujo=False):
    vertices = []
    for r, d in perfil:
        for j in range(segmentos+1):
            # La costura UV queda en la zona de contacto con el suelo.
            t = math.tau*j/segmentos - math.pi/2
            rr = r
            if dibujo and r > .475 and abs(d) < .125:
                # Cortes transversales escalonados, además de los canales anulares.
                if (j + (1 if d < 0 else 0)) % 3 == 0:
                    rr -= .0025
            vertices.append((x+rr*math.cos(t), yc+signo*d, zc+rr*math.sin(t)))
    n = segmentos+1
    caras = []
    anillos = len(perfil) if cerrado else len(perfil)-1
    for i in range(anillos):
        k = (i+1) % len(perfil)
        for j in range(segmentos):
            caras.append((i*n+j, i*n+j+1, k*n+j+1, k*n+j))
    o = crear_malla(nombre, vertices, caras, mat, grupo)
    uv = o.data.uv_layers.new(name="UVMap")
    for p in o.data.polygons:
        p.use_smooth = True
        for loop in p.loop_indices:
            i, j = divmod(o.data.loops[loop].vertex_index, n)
            uv.data[loop].uv = (j/segmentos*8, i/max(1,len(perfil)-1)*2)
    # Un solo vértice geométrico en la costura angular, conservando los dos
    # extremos UV por esquina de cara. Así no aparece una raya en el flanco.
    bm = bmesh.new()
    bm.from_mesh(o.data)
    bmesh.ops.remove_doubles(bm, verts=list(bm.verts), dist=.000001)
    bmesh.ops.recalc_face_normals(bm, faces=list(bm.faces))
    bm.to_mesh(o.data)
    bm.free()
    return o


def ruedas_detalladas(datos, materiales, grupos, crear_malla, vacio, cilindro):
    zc = datos["centro_rueda_z"]
    # Perfil real de goma: talón, flanco convexo, hombro y canales de rodadura.
    medio = [(.303,-.178), (.332,-.184), (.38,-.185), (.426,-.175), (.463,-.151),
             (.481,-.120), (.488,-.098), (.490,-.078), (.482,-.070), (.490,-.061),
             (.490,-.028), (.482,-.020), (.490,-.011)]
    perfil = medio + [(r,-d) for r,d in reversed(medio)]
    perfil_llanta = [(.10,.201), (.14,.196), (.17,.174), (.205,.158), (.245,.156),
                     (.278,.186), (.293,.207), (.308,.209), (.313,.194), (.313,.151),
                     (.298,.141), (.277,.161), (.245,.141), (.205,.142), (.17,.158),
                     (.14,.180), (.10,.185)]
    for ie, x in enumerate(datos["ejes"]):
        for signo in [-1, 1]:
            nombre = f"rueda_{'trasera' if ie == 0 else 'delantera'}_{'derecha' if signo == -1 else 'izquierda'}"
            yc = signo*datos["semivia_ruedas"]
            if ie == 1:
                direccion = nombre.replace("rueda_", "direccion_")
                grupos[direccion] = vacio(direccion, (x,yc,zc), grupos["raiz"])
                grupos[nombre] = vacio(nombre, (0,0,0), grupos[direccion])
            else:
                grupos[nombre] = vacio(nombre, (x,yc,zc), grupos["raiz"])
            bpy.context.view_layer.update()
            torno("Neumático radial", perfil, x,yc,zc,signo, materiales["neumatico"],nombre,crear_malla,
                  segmentos=datos["acabados"]["segmentos_neumatico"], dibujo=True)
            llanta = torno("Llanta de acero embutido",perfil_llanta,x,yc,zc,signo,materiales["llanta"],
                           nombre,crear_malla,segmentos=64,cerrado=True)
            # Seis taladros auténticos atraviesan el plato cóncavo.
            cortes = []
            for j in range(6):
                t = math.tau*j/6
                xx, zz = x+.218*math.cos(t), zc+.218*math.sin(t)
                cortes.append(cilindro("Cortador ventilación",(xx,yc+signo*.17,zz),.040,.19,
                                      materiales["oscuro"],"Y",16,nombre))
            bpy.ops.object.select_all(action="DESELECT")
            for o in cortes:
                o.select_set(True)
            bpy.context.view_layer.objects.active = cortes[0]
            bpy.ops.object.join()
            mod = llanta.modifiers.new("Ventilaciones abiertas", "BOOLEAN")
            mod.operation, mod.solver, mod.object = "DIFFERENCE", "EXACT", cortes[0]
            bpy.context.view_layer.objects.active = llanta
            bpy.ops.object.modifier_apply(modifier=mod.name)
            bpy.data.objects.remove(cortes[0], do_unlink=True)
            # El labio ya está dibujado en el perfil de revolución. No biselar
            # de nuevo todas sus aristas (cuadruplica la malla sin mejorarla).
            # Aros finos en el flanco, sin el aspecto de discos planos apilados.
            for radio in [.346]:
                p = [(radio+.002*math.cos(t),.184+.002*math.sin(t))
                     for t in [math.tau*j/5 for j in range(5)]]
                torno("Relieve anular de flanco",p,x,yc,zc,signo,materiales["neumatico"],nombre,
                      crear_malla,segmentos=48,cerrado=True)
            cilindro("Buje de acero",(x,yc+signo*.216,zc),.096,.050,materiales["llanta"],"Y",48,nombre)
            cilindro("Centro del buje",(x,yc+signo*.243,zc),.068,.009,materiales["oscuro"],"Y",40,nombre)
            for j in range(6):
                t = math.tau*j/6
                xx, zz = x+.135*math.cos(t), zc+.135*math.sin(t)
                cilindro("Arandela",(xx,yc+signo*.206,zz),.024,.009,materiales["oscuro"],"Y",16,nombre)
                cilindro("Tuerca hexagonal",(xx,yc+signo*.220,zz),.018,.022,materiales["marco"],"Y",6,nombre)
