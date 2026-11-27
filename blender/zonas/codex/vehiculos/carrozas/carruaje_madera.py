"""Carruaje abierto: caja de roble enmarcada y pescante con faldón cóncavo."""
import math

import bpy
import numpy as np
from kit_vehiculo_bpy import crear_caja, crear_cilindro, crear_panel
from piezas import banda, curva_2d, esfera, redondeado, tubo, tubo_curvo
from carroza_azul import asiento


def veta(mat):
    """Albedo repetible de veta longitudinal, sin luces ni sombras impresas."""
    alto, ancho = 256, 512
    u, v = np.meshgrid(np.arange(ancho)/ancho, np.arange(alto)/alto)
    tau = math.tau
    ondulacion = .58*np.sin(tau*(2*u+2*v))+.34*np.sin(tau*(3*u-3*v))
    anillos = np.sin(tau*15*v+ondulacion) + .34*np.sin(tau*22*v+2*ondulacion)
    nudo_a = np.cos(tau*3*u)
    nudo_b = np.cos(tau*(11*v+.05*nudo_a))
    ruido = np.random.default_rng(25).normal(0, .007, u.shape)
    color = np.array([.584,.259,.121])[None,None,:]
    flujo = np.sin(tau*(43*v+1.6*u)+2.3*ondulacion+.66*nudo_b)
    ondulacion_larga = np.sin(tau*(7*v+u)+1.4*np.sin(tau*(u+2*v)))
    desviacion = .054*anillos + .034*nudo_a*nudo_b + .018*flujo + .031*ondulacion_larga + ruido
    pix = np.ones((alto,ancho,4), dtype=np.float32)
    pix[:,:,:3] = np.clip(color + desviacion[:,:,None] * [.95,.65,.36], .03, .9)
    imagen = bpy.data.images.new("Roble longitudinal pintado", width=ancho, height=alto, alpha=False)
    imagen.pixels.foreach_set(pix.reshape(-1))
    imagen.pack()
    nodes = mat.node_tree.nodes
    textura = nodes.new("ShaderNodeTexImage")
    textura.image = imagen
    mat.node_tree.links.new(textura.outputs["Color"], nodes["Principled BSDF"].inputs["Base Color"])


def tablero(centro, medidas, mat, p, fase, trasera=False):
    o = crear_caja("Tablero de roble encastrado",centro,medidas,mat,p,.015,3)
    # El cubo biselado ya está en escala métrica local. Las fibras viajan por X o por Y.
    uv = o.data.uv_layers.active or o.data.uv_layers.new(name="Albedo_roble")
    horizontal = 1 if trasera else 0
    for loop in o.data.loops:
        co = o.data.vertices[loop.vertex_index].co
        uv.data[loop.index].uv = (co[horizontal]*1.8+fase*.191, co.z*1.25+fase*.233)
    return o


def construir(g, m):
    c, i, d = (g[k] for k in ("carroceria", "interior", "decoracion"))
    veta(m["roble"])
    x0, x1 = -1.96, .33
    w, z0, z1, z2 = .593, 1.192, 1.57, 1.95
    crear_caja("Piso de madera de la caja",(-.82,0,1.23),(2.31,1.14,.107),m["piso"],c,.035)
    for j in range(9):
        y = (j-4)*.123
        crear_caja("Tabla de piso",(-.82,y,1.287),(2.246,.119,.014),m["piso"],i,.004)
    for s in (-1,1):
        y = s*w
        for k in range(5):
            x = x0+(x1-x0)*(k+.5)/5
            for j, (abajo, arriba) in enumerate(((z0,z1),(z1,z2))):
                tablero((x,y,(abajo+arriba)/2),(.423,.054,arriba-abajo-.043),
                        m["roble"],c,k+j*5+(s+1)*3)
                tubo("Bocel empotrado del tablero",[(u,y+s*.029,z) for u,z in
                     redondeado(x-.199,x+.199,abajo+.030,arriba-.028,.025,3)],
                     .006,m["filete"],d,True)
        for z, a in ((z0,.090),(z1,.048),(z2,.068)):
            crear_caja("Travesaño del enmarcado",((x0+x1)/2,y,z),(x1-x0+.04,.086,a),
                       m["hierro"],c,.014)
        for k in range(6):
            crear_caja("Montante del enmarcado",(x0+(x1-x0)*k/5,y,(z0+z2)/2),
                       (.041,.083,z2-z0),m["hierro"],c,.009)
        tubo("Baranda lateral de la plataforma",[(x,s*.611,z) for x,z in [
             (x0,1.58),(x0-.062,1.605),(x0-.076,1.998),(x0-.052,2.06),
             (-1.86,2.064),(-1.24,2.064),(-.97,2.055),(-.915,1.982)]],.020,m["hierro"],d)
        tubo("Baranda detrás del pescante",[(x,s*.61,z) for x,z in [
             (-.66,1.966),(-.65,2.050),(-.578,2.076),(.28,2.076),(.351,2.045),(.349,1.963)]],
             .018,m["hierro"],d)
    for k in range(3):
        y = (k-1)*.388
        for j,(abajo,arriba) in enumerate(((z0,z1),(z1,z2))):
            tablero((x0,y,(abajo+arriba)/2),(.058,.354,arriba-abajo-.038),m["roble"],c,k+2*j,True)
            tubo("Bocel trasero",[(x0-.032,v,z) for v,z in
                 redondeado(y-.165,y+.165,abajo+.030,arriba-.028,.025,3)],.006,m["filete"],d,True)
    for z in (z0,z1,z2):
        crear_caja("Travesaño trasero",(x0,0,z),(.080,1.235,.065),m["hierro"],c,.013)
    for y in (-.579,-.194,.194,.579):
        crear_caja("Montante trasero",(x0,y,1.57),(.081,.048,.762),m["hierro"],c,.010)
    tubo("Pasamanos trasero",[(x0-.073,y,2.067) for y in (-.605,.605)],.019,m["hierro"],d)

    for x, s in ((-1.61,-1),(.02,1)):
        crear_caja("Bastidor de banca",(x,0,1.79),(.48,1.113,.085),m["piso"],i,.015)
        for y in (-.469,.469):
            crear_caja("Pie de banca",(x,y,1.523),(.089,.075,.49),m["hierro"],i,.013)
        asiento(x,1.876,.445,1.078,i,m["crema"],m["costura"])
        banca(x+s*.20,.522,2.204,s,m,i,d)
    for s in (-1,1):
        y = s*.451
        superior = curva_2d([(.31,1.938),(.49,1.995),(.64,2.13),(.71,2.36),
                             (.83,2.39),(1.04,2.376),(1.085,2.081),(1.23,1.73),
                             (1.43,1.742),(1.62,1.915),(1.9,2.216)],40)
        inferior = curva_2d([(.31,1.25),(.79,1.231),(1.18,1.257),
                             (1.40,1.684),(1.67,1.974),(1.90,2.179)],40)
        contorno = [(x,s*(.451-.041*max(0,x-1.1)),z) for x,z in inferior+superior[::-1]]
        crear_panel("Faldón cóncavo del pescante",contorno,m["negro"],c,.047,False)
        for perfil in (superior,inferior):
            tubo("Filete del faldón negro",[(x,s*(.479-.041*max(0,x-1.1)),z)
                 for x,z in perfil],.008,m["filete"],d)
        rejilla(.798,y+s*.034,1.61,False,g,m)
        tubo("Asa de subida", [(1.13,s*.466,1.556),(1.16,s*.482,1.689),
             (1.245,s*.483,1.714),(1.305,s*.485,1.634),(1.304,s*.484,1.556)],.012,m["hierro"],d)
        for z,x in ((.70,-.688),(.93,-.722)):
            tubo("Colgador forjado del estribo",[(x,s*.37,1.228),(x,s*.505,z+.04),(x,s*.673,z)],
                 .020,m["hierro"],d)
            crear_caja("Pisadera",(x,s*.648,z),(.205,.218,.043),m["hierro"],d,.018)
    for s in (-1,1):
        tubo_curvo("Puntal fijo de la caja del cochero",[(.67,s*.298,1.00),(.583,s*.315,1.167),
             (.522,s*.392,1.258),(.49,s*.442,1.302)],.039,m["hierro"],c)
    crear_caja("Viga transversal de apoyo de la caja",(.55,0,1.225),
               (.145,.915,.078),m["oro"],c,.014)
    banda("Faldón frontal bajo el asiento",[(1.08,0,1.43),(1.20,0,1.62),(1.42,0,1.76)],
          m["negro"],c,.862,.235)
    p = [(x,0,z) for x,z in curva_2d([(1.172,1.704),(1.4,1.759),(1.68,2.024),(1.9,2.21)],22)]
    banda("Reposapiés elevado",p,m["cuero"],c,.91,.039)
    rejilla(1.412,0,1.571,True,g,m)
    for y in (-.37,.37):
        tubo("Manija del reposapiés",[(x,y,z) for x,z in [
             (1.63,2.005),(1.65,2.09),(1.74,2.167),(1.817,2.174),(1.836,2.154)]],.016,m["hierro"],d)

    crear_caja("Apoyo del pescante",(.873,0,2.357),(.568,.936,.078),m["hierro"],c,.018)
    asiento(.874,2.454,.526,.875,i,m["crema"],m["costura"])
    for s in (-1,1):
        for z in (2.506,2.611):
            tubo("Guardabrazo del pescante",[(x,s*y,h) for x,y,h in [
                 (.582,.453,2.364),(.558,.471,z),(.63,.493,z+.014),(1.063,.488,z+.011),
                 (1.13,.459,z-.009),(1.133,.444,2.393)]],.015,m["hierro"],d)
        crear_caja("Remache de asiento",(.825,s*.464,2.374),(.092,.031,.049),m["filete"],d,.009)
    tubo("Travesaño del respaldo de cochero",[(.581,y,2.635) for y in (-.47,.47)],.017,m["hierro"],d)
    tubo("Palanca de freno",[(.63,-.2,2.00),(.64,-.208,2.235),(.57,-.204,2.51),
         (.492,-.202,2.652)],.012,m["hierro"],d)
    pomo = esfera("Empuñadura del freno",(.477,-.202,2.667),(.023,.020,.044),m["cuero"],d)
    pomo.rotation_euler.y = .24


def rejilla(x,y,z,frente,g,m):
    grupo = g["decoracion"]
    orienta = (lambda h,v,e=0:(x+e,y+h,z+v)) if frente else (
               lambda h,v,e=0:(x+h,y+math.copysign(e,y),z+v))
    for h in np.linspace(-.101,.101,9):
        tubo("Varilla vertical de rejilla",[orienta(h,-.128),orienta(h,.128)],.0045,m["hierro"],grupo)
    for v in np.linspace(-.122,.122,10):
        tubo("Varilla horizontal de rejilla",[orienta(-.102,v,.008),orienta(.102,v,.008)],
             .0045,m["hierro"],grupo)
    tubo("Marco de rejilla",[orienta(h,v,.015) for h,v in redondeado(-.121,.121,-.143,.143,.011)],
         .009,m["filete"],grupo,True)


def banca(x,w,z,s,m,i,d):
    for y in (-w+.046,w-.046):
        tubo("Tubo del respaldo",[(x-s*.06,y,1.80),(x,y,2.032),(x+s*.067,y,2.289)],
             .019,m["hierro"],d)
    respaldo = crear_caja("Respaldo crema abombado",(x+s*.067,0,z),(.121,w*2,.273),m["crema"],i,.056,4)
    respaldo.rotation_euler.y = s*.17
    for y in np.linspace(-w+.084,w-.084,9):
        tubo("Costura vertical del respaldo",[(x+s*u,y,h) for u,h in [
             (.005,z-.104),(-.002,z-.077),(.009,z+.061),(.023,z+.113)]],.0027,m["costura"],i)
