"""Adapta el ROME a metros, talla el tiro y conserva sus poses de galope."""
from collections import defaultdict
import json
from pathlib import Path
import subprocess
import sys

import numpy as np

AQUI = Path(__file__).resolve().parent
REPO = AQUI.parents[4]
PUBLICO = REPO / "web/public/models/ciudad/codex/vehiculos/carrozas"
SKILL = REPO / ".agents/skills/vehiculo-3d-desde-diseno/scripts"
sys.path.insert(0, str(SKILL))

from generar_variantes_glb import color_lineal, escribir_glb, leer_glb

DATOS = json.loads((AQUI / "caballo_rome.json").read_text())
BINARIO = 0x004E4942
TIPOS = {5123: "<u2", 5125: "<u4", 5126: "<f4"}


def leer_accesor(doc, binario, indice):
    a = doc["accessors"][indice]
    vista = doc["bufferViews"][a["bufferView"]]
    tipo = TIPOS[a["componentType"]]
    columnas = {"SCALAR": 1, "VEC2": 2, "VEC3": 3}[a["type"]]
    inicio = vista.get("byteOffset", 0) + a.get("byteOffset", 0)
    item = np.dtype(tipo).itemsize
    stride = vista.get("byteStride", columnas * item)
    return np.ndarray((a["count"], columnas), dtype=tipo, buffer=binario,
                      offset=inicio, strides=(stride, item)).copy()


def origen():
    ruta = REPO / "autos/carrozas" / DATOS["fuente"]
    doc, bloques = leer_glb(ruta.read_bytes())
    binario = bloques[0][1]
    primitiva = doc["meshes"][0]["primitives"][0]
    atributos = primitiva["attributes"]
    posiciones = leer_accesor(doc, binario, atributos["POSITION"])
    color = leer_accesor(doc, binario, atributos["COLOR_0"])
    caras = leer_accesor(doc, binario, primitiva["indices"]).reshape(-1, 3)
    poses = [posiciones + leer_accesor(doc, binario, objetivo["POSITION"])
             for objetivo in primitiva["targets"]]

    def convertir(v):
        # Frente +Z en la fuente. La rotación lleva el frente a +X sin reflejar la malla.
        return v[:, (2, 1, 0)] * np.array([1, 1, -1]) * DATOS["escala"]

    return np.array([convertir(p) for p in poses]), color, caras


def suave(a, b, valor):
    t = np.clip((valor-a)/(b-a), 0, 1)
    return t*t*(3-2*t)


def patas(poses, caras, colores):
    base = poses[0]
    # El GLB duplica esquinas por color. Los vértices coincidentes reciben una única pata.
    unicos, indices = np.unique(base, axis=0, return_inverse=True)
    debajo = unicos[:, 1] < .76
    vecinos = defaultdict(set)
    for cara in indices[caras]:
        for a, b in zip(cara, np.roll(cara, -1)):
            if debajo[a] and debajo[b]:
                vecinos[a].add(b)
                vecinos[b].add(a)
    pendientes = set(np.flatnonzero(debajo))
    islas = []
    while pendientes:
        uno = pendientes.pop()
        isla, camino = {uno}, [uno]
        while camino:
            for otro in vecinos[camino.pop()] & pendientes:
                pendientes.remove(otro)
                isla.add(otro)
                camino.append(otro)
        if len(isla) > 20:
            islas.append(np.array(sorted(isla)))
    assert len(islas) == 4

    distancias = []
    for isla in islas:
        distancias.append(np.linalg.norm(base[:, None] - unicos[isla], axis=2).min(axis=1))
    distancias = np.array(distancias)
    asignacion = np.argmin(distancias, axis=0)

    # Cada postura de descanso toma la extremidad de la fase del galope que apoya su casco.
    muestras = {
        (True, True): (0, .515, .143, .50),
        (True, False): (3, .553, -.137, 0),
        (False, True): (11, -.833, .147, .75),
        (False, False): (13, -.782, -.144, .25),
    }
    grupos = []
    reposo = base.copy()
    for i, isla in enumerate(islas):
        centro = unicos[isla].mean(axis=0)
        frente, derecha = centro[0] > 0, centro[2] > 0
        frame, x, z, fase = muestras[frente, derecha]
        donante = poses[frame]
        es_pie = np.isin(indices, isla) & (colores[:, 0] < .13)
        cascos = np.flatnonzero(es_pie)
        assert len(cascos) > 10

        altura = base[:, 1]
        cerca = suave(.235, .05, distancias[i])
        peso = (asignacion == i) * suave(1.075, .75, altura) * cerca
        peso[np.isin(indices, isla)] = 1
        pie = donante[cascos]
        centro_pie = pie.mean(axis=0)
        empuje = np.array([x-centro_pie[0], .004-pie[:,1].min(), z-centro_pie[2]])
        ajuste = (donante-base) + suave(.82, .45, altura)[:, None]*empuje
        reposo += ajuste*peso[:, None]
        grupos.append((fase, frente, peso, cascos))
    return reposo, grupos


def caminar(reposo, grupos, n=16):
    """Ciclo de cuatro apoyos con tramo plantado y recuperación del casco."""
    extension = DATOS["clips"]["paso"]["zancada_m"]
    apoyo = .64
    formas = []
    for frame in range(n):
        t = frame/n
        pose = reposo.copy()
        for desfase, frente, peso, _ in grupos:
            fase = (t+desfase) % 1
            avance = extension*(apoyo*.5-fase)
            levanta = 0
            if fase >= apoyo:
                swing = (fase-apoyo)/(1-apoyo)
                avance = extension*apoyo*(suave(0,1,swing)-.5)
                levanta = .116*np.sin(np.pi*swing)**1.35
            distal = peso*suave(.9,.18,reposo[:,1])
            articulacion = peso*np.maximum(0,1-abs(reposo[:,1]-.55)/.42)
            pose[:,0] += avance*distal - (.29 if frente else -.17)*levanta*articulacion
            pose[:,1] += levanta*distal
        # Respiración del tórax durante la marcha. La zona de los cascos queda plantada.
        pose[:,1] += .012*np.cos(4*np.pi*t)*suave(.55,1.1,reposo[:,1])
        formas.append(pose)
    return formas


def malla_correas():
    """Cintas de cuero y hebillas ancladas en la pechera del caballo."""
    puntos, caras = [], defaultdict(list)

    def cinta(coords, ancho, espesor, material, eje, cerrada=False):
        ini = len(puntos)
        coords = np.asarray(coords)
        for i, centro in enumerate(coords):
            ant, sig = (i-1) % len(coords), (i+1) % len(coords)
            if not cerrada:
                ant, sig = max(0,i-1), min(len(coords)-1,i+1)
            tangente = coords[sig]-coords[ant]
            tangente /= np.linalg.norm(tangente)
            lateral = np.asarray(eje) - np.dot(eje,tangente)*tangente
            lateral /= np.linalg.norm(lateral)
            normal = np.cross(tangente,lateral)
            for u,v in ((-1,-1),(1,-1),(1,1),(-1,1)):
                puntos.append(centro+u*lateral*ancho/2+v*normal*espesor/2)
        for j in range(len(coords) if cerrada else len(coords)-1):
            a, b = ini+4*j, ini+4*((j+1)%len(coords))
            for k in range(4):
                n = (k+1)%4
                caras[material].extend([(a+k,b+n,b+k),(a+k,a+n,b+n)])
        if not cerrada:
            fin = ini+4*(len(coords)-1)
            caras[material].extend([(ini,ini+2,ini+1),(ini,ini+3,ini+2),
                                    (fin,fin+1,fin+2),(fin,fin+2,fin+3)])
    cinta([(.477,1.079,-.263),(.592,1.06,-.246),(.686,1.048,-.16),(.714,1.045,0),
           (.686,1.048,.16),(.592,1.06,.246),(.477,1.079,.263)], .068,.021,"cuero",(0,1,0))
    cinta([(.217,.761,0),(.23,.803,-.180),(.23,.918,-.27),(.225,1.042,-.292),
           (.225,1.214,-.24),(.19,1.339,-.155),(.178,1.391,0),
           (.19,1.339,.155),(.225,1.214,.24),(.225,1.042,.292),
           (.23,.918,.27),(.23,.803,.180)],.073,.018,"cuero",(1,0,0),True)

    anclas = {}
    for signo, lado in ((-1,"izquierda"),(1,"derecha")):
        cinta([(.188,1.378,signo*.095),(.291,1.291,signo*.178),
               (.415,1.173,signo*.231),(.492,1.080,signo*.263)], .038,.015,"cuero",(0,0,signo))
        cinta([(.218,1.112,signo*.279),(.267,1.006,signo*.322),(.297,.979,signo*.327),
               (.328,1.013,signo*.313),(.273,1.105,signo*.281)], .032,.014,"cuero",(1,0,0))
        aro = [(.50+.030*np.cos(a),1.074+.030*np.sin(a),signo*.271)
               for a in np.linspace(0,2*np.pi,12,endpoint=False)]
        cinta(aro,.009,.009,"laton",(0,0,1),True)
        anclas[f"tiro_caballo_{lado}"] = (.50,1.074,signo*.273)
        anclas[f"cincha_caballo_{lado}"] = (.297,.979,signo*.327)
    return np.array(puntos), caras, anclas


def transportar(origen, formas, puntos):
    """Interpola el movimiento de las cintas desde los vértices cercanos del tórax."""
    cuerpo = np.unique(origen, axis=0, return_index=True)[1]
    cuerpo = cuerpo[(origen[cuerpo,0] > -.11) & (origen[cuerpo,0] < .74) & (origen[cuerpo,1] > .78)]
    dist = np.linalg.norm(puntos[:,None]-origen[cuerpo],axis=2)
    indices = np.argsort(dist,axis=1)[:,:4]
    pesos = 1/np.take_along_axis(dist,indices,axis=1).clip(.014)**2
    pesos /= pesos.sum(axis=1)[:,None]
    deltas = formas-origen
    return puntos[None] + np.sum(deltas[:,cuerpo[indices]]*pesos[None,:,:,None],axis=2)


class Glb:
    def __init__(self):
        self.doc = {k: [] for k in ("nodes","materials","meshes","animations","bufferViews","accessors")}
        self.doc["asset"] = {
            "version":"2.0", "generator":"Mi Ciudad | ROME Galope",
            "copyright":"Horse model by Mirada from ROME (3 Dreams of Black) / three.js",
        }
        self.doc["scene"] = 0
        self.doc["scenes"] = [{"nodes":[0],"name":"ROME Galope"}]
        self.binario = bytearray()

    def accesor(self, valores, tipo="VEC3", formato=5126, destino=None):
        valores = np.asarray(valores,dtype=TIPOS[formato])
        planos = valores.reshape((-1,1 if tipo=="SCALAR" else 3))
        datos = planos.tobytes()
        vista = {"buffer":0,"byteOffset":len(self.binario),"byteLength":len(datos)}
        if destino:
            vista["target"] = destino
        self.binario.extend(datos)
        self.binario.extend(b"\0"*(-len(datos)%4))
        self.doc["bufferViews"].append(vista)
        self.doc["accessors"].append({
            "bufferView":len(self.doc["bufferViews"])-1,"componentType":formato,
            "count":len(planos),"type":tipo,
            "min":planos.min(axis=0).tolist(),"max":planos.max(axis=0).tolist(),
        })
        return len(self.doc["accessors"])-1

    def material(self, nombre, hex_srgb, variante=False):
        color = color_lineal(hex_srgb)
        mat = {"name":f"{nombre}__{hex_srgb[1:]}", "pbrMetallicRoughness":{
            "baseColorFactor":[*color,1], "metallicFactor":.24 if nombre=="laton" else 0,
            "roughnessFactor":.64 if nombre in ("laton","cuero") else .93,
        }}
        if variante:
            mat["extras"] = {"pintura_vehiculo":nombre}
        self.doc["materials"].append(mat)
        return len(self.doc["materials"])-1

    def malla(self, nombre, poses, caras, materiales, nombres):
        base = self.accesor(poses[0],destino=34962)
        objetivos = [{"POSITION":self.accesor(p-poses[0],destino=34962)} for p in poses[1:]]
        primitivas = []
        for rol, indices in caras.items():
            primitivas.append({
                "attributes":{"POSITION":base},"indices":self.accesor(indices,"SCALAR",5123,34963),
                "material":materiales[rol],"targets":objetivos,
            })
        self.doc["meshes"].append({
            "name":nombre,"primitives":primitivas,"weights":[0]*len(objetivos),
            "extras":{"targetNames":nombres},
        })
        self.doc["nodes"].append({"name":nombre,"mesh":len(self.doc["meshes"])-1})
        return len(self.doc["nodes"])-1

    def animacion(self, nombre, poses, duracion, nodos, cantidad_formas, anclas):
        t = self.accesor(np.linspace(0,duracion,len(poses)),"SCALAR")
        pesos = np.zeros((len(poses),cantidad_formas),np.float32)
        for i, pose in enumerate(poses):
            if pose:
                pesos[i,pose-1] = 1
        canales, samplers = [], []

        def canal(objetos, camino, co, tipo):
            s = len(samplers)
            samplers.append({"input":t,"output":self.accesor(co,tipo),"interpolation":"LINEAR"})
            canales.extend({"sampler":s,"target":{"node":objeto,"path":camino}} for objeto in objetos)

        canal(nodos,"weights",pesos,"SCALAR")
        for nodo, posiciones in anclas:
            canal([nodo],"translation",posiciones[poses],"VEC3")
        self.doc["animations"].append({"name":nombre,"samplers":samplers,"channels":canales})

    def guardar(self, ruta):
        self.doc["buffers"] = [{"byteLength":len(self.binario)}]
        ruta.write_bytes(escribir_glb(self.doc,[(BINARIO,self.binario)]))


def paleta(glb, colores, caras):
    colores_originales, ids, cuentas = np.unique(colores.round(5),axis=0,return_inverse=True,return_counts=True)
    assert len(colores_originales)==6 and (ids[caras]==ids[caras[:,0],None]).all()
    roles = ("pelaje","casco","hocico","crin","marca","ojo")
    principales = DATOS["variantes"][DATOS["variante_predeterminada"]]
    materiales = {}
    grupos = {}
    for rol,i in zip(roles,np.argsort(-cuentas)):
        color = colores_originales[i]
        srgb = np.where(color<=.0031308,12.92*color,1.055*color**(1/2.4)-.055)
        hex_color = "#" + "".join(f"{v:02x}" for v in np.round(srgb*255).astype(int))
        materiales[rol] = glb.material(rol,principales.get(rol,hex_color),rol in principales)
        grupos[rol] = caras[ids[caras[:,0]]==i]
    return materiales,grupos


def preparar():
    PUBLICO.mkdir(parents=True,exist_ok=True)
    original, colores, caras = origen()
    reposo, grupos = patas(original,caras,colores)
    paso = caminar(reposo,grupos)
    # Las poses ROME se conservan. Se levanta solo el exceso que atravesaba el suelo.
    galope = [p+np.array([0,max(0,.002-p[:,1].min()),0]) for p in original]
    poses = np.array([reposo,*paso,*galope])
    nombres = [f"paso_{i+1:02d}" for i in range(len(paso))] + [f"rome_{i+1:02d}" for i in range(len(galope))]
    correa, caras_correa, puntos_ancla = malla_correas()
    arreo = transportar(reposo,poses,correa)
    anclas = transportar(reposo,poses,np.asarray(list(puntos_ancla.values())))

    glb = Glb()
    glb.doc["nodes"].append({"name":DATOS["id"],"children":[], "extras":{
        "clips":DATOS["clips"],"avance_desde_lanza_m":DATOS["avance_desde_lanza_m"],
        "variante":DATOS["variante_predeterminada"],"unidades":"metros","frente":"+X",
    }})
    materiales, grupos_caras = paleta(glb,colores,caras)
    materiales["cuero"] = glb.material("cuero","#482b28")
    materiales["laton"] = glb.material("laton","#ac7949")
    caballo = glb.malla("Cuerpo ROME",poses,grupos_caras,materiales,nombres)
    arreos = glb.malla("Pechera y cincha",arreo,caras_correa,materiales,nombres)
    glb.doc["nodes"][0]["children"].extend([caballo,arreos])
    nodos_ancla = []
    for i,(nombre,co) in enumerate(puntos_ancla.items()):
        nodo = len(glb.doc["nodes"])
        glb.doc["nodes"].append({"name":nombre,"translation":list(co)})
        glb.doc["nodes"][0]["children"].append(nodo)
        nodos_ancla.append((nodo,anclas[:,i]))
    primero = len(paso)+1
    for nombre, ciclo in (
        ("reposo",[0,0]),("paso",[*range(1,primero),1]),
        ("galope",[*range(primero,len(poses)),primero]),
    ):
        glb.animacion(nombre,ciclo,DATOS["clips"][nombre]["duracion_s"],[caballo,arreos],len(nombres),nodos_ancla)

    maestro = PUBLICO / "caballo_rome.glb"
    glb.guardar(maestro)
    ficha = {
        "id":DATOS["id"], "fuente":DATOS["fuente"],"autor":"Mirada / Google Data Arts Team",
        "triangulos_rome":len(caras),"triangulos_arreos":sum(map(len,caras_correa.values())),
        "formas_galope":len(galope),"clips":DATOS["clips"],"anclajes":list(puntos_ancla),
        "dimensiones_reposo_m":np.ptp(reposo,axis=0).round(3).tolist(),
        "avance_desde_lanza_m":DATOS["avance_desde_lanza_m"],
        "apoyos_reposo_m": [round(float(reposo[cascos,1].min()),5) for _,_,_,cascos in grupos],
    }
    (PUBLICO/"caballo_rome.ficha.json").write_text(json.dumps(ficha,indent=2,ensure_ascii=False)+"\n")
    subprocess.run([sys.executable,str(SKILL/"generar_variantes_glb.py"),"--datos",str(AQUI/"caballo_rome.json"),
                    "--maestro",str(maestro),"--salida",str(PUBLICO)],check=True)
    ruta = PUBLICO/"caballo_rome.variantes.json"
    manifiesto = json.loads(ruta.read_text())
    manifiesto.update(controlador="caballo_rome.mjs",blend="caballo_rome.blend")
    for variante in manifiesto["variantes"]:
        del variante["blend"]
    ruta.write_text(json.dumps(manifiesto,indent=2,ensure_ascii=False)+"\n")


if __name__ == "__main__":
    preparar()
