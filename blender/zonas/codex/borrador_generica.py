# BORRADOR DE PAUSA 2026-11-12: NO VALIDADO NI EXPORTADO.
"""Manzanas sin foto: mínimo colonial de Calidad, determinista por id.

Huellas recortadas del kit. Un cuerpo por edificio y detalle solo a calle.
Puertas al terreno, zócalos interrumpidos y cubiertas trianguladas sin
atravesar entrantes. No se atribuyen detalles de monumentos sin foto.
"""
import os
import sys
import hashlib
sys.path.insert(0,os.path.join(os.path.dirname(os.path.abspath(__file__)),'..','..'))
sys.path.insert(0,os.path.dirname(os.path.abspath(__file__)))
from kit import *
from piezas_codex import prisma_seguro,trasladar


def construir(mid):
    m,col=iniciar('codex',mid)
    vistos=set();frentes_revision={}
    for e in m['edificios']:
        if e['id'] in vistos:continue
        vistos.add(e['id'])
        semilla=int(hashlib.sha256(e['id'].encode()).hexdigest()[:8],16)
        color=('#eee8da','#f2e9d9','#e9dfcb','#f3eadf')[semilla%4]
        pisos=1 if e['area_m2']<65 else 2
        alto=4.2*pisos
        c=Constructor(e['id']);h=e['huella'];ls=lados(h)
        z=max(altura_suelo(*p) for p in h);zb=min(altura_suelo(*p) for p in h)-.5
        prisma_seguro(c,h,zb,z+alto,'muro',color)
        calle=[l for l in ls if l['a_calle'] and l['largo']>=1.5]
        if not calle:
            # El detector omitía los frentes de numerosas huellas pequeñas.
            # Se elige el lado orientado hacia la calle más cercana; no se
            # exporta otra casa como una caja lisa. Es una aproximación sin foto.
            candidatos=[l for l in ls if l['largo']>=1.25]
            def distancia_calle(l):
                x=(l['a'][0]+l['b'][0])/2+l['normal'][0]*2
                y=(l['a'][1]+l['b'][1])/2+l['normal'][1]*2
                return datos.calle_cercana(x,y)[0]
            if candidatos:calle=[min(candidatos,key=distancia_calle)]
        mayor=max(calle,key=lambda l:l['largo']) if calle else None
        frentes_revision[e['id']]=mayor
        for l in calle:
            f=Fachada(c,l,z)
            n=max(1,min(16,int(f.largo/3.7)));paso=f.largo/n
            es_principal=l is mayor
            puerta_k=n//2
            for k in range(n):
                ss=(k+.5)*paso
                ancho=min(1.1,paso*.46)
                if es_principal and k==puerta_k:
                    pie=f.punto(ss,0);fp=trasladar(f,h=altura_suelo(pie.x,pie.y)+.12-z)
                    puerta(fp,ss,ancho=min(1.4,paso*.6),alto=2.8,
                           color='#65422d',color_moldura='#d0b697')
                    radio=min(1.4,paso*.6)/2+.25
                    for a,b in ((k*paso,ss-radio),(ss+radio,(k+1)*paso)):
                        if b>a:zocalo(f,.75,s0=a,s1=b,desde=zb-z,color='#ba9b78',sillares=False)
                else:
                    zocalo(f,.75,s0=k*paso,s1=(k+1)*paso,desde=zb-z,color='#ba9b78',sillares=False)
                    ventana(f,ss,1.25,ancho=ancho,alto=1.8,reja=True,color_moldura='#f2e9dc')
                if pisos==2:
                    ventana(f,ss,4.5,ancho=ancho,alto=2.65,color_moldura='#f2e9dc',
                            balcon='hierro' if paso>2.5 and (k==puerta_k or semilla%3==0) else None,
                            postigos=paso>3.1 and semilla%4==0)
            if pisos==2:imposta(f,4.0,alto=.15)
            cornisa(f,alto-.25,alto=.25,vuelo=.22,color='#f2e9dc')
            parapeto(f,alto,alto=.45,color=color)
        c.objeto(col)
    if '--revisar' in sys.argv:
        from kit import salida
        import bpy,math
        original=salida._luz_y_mundo
        def luz():
            original();sc=bpy.context.scene;sc.render.engine='CYCLES';sc.cycles.device='CPU';sc.cycles.samples=8;sc.cycles.use_denoising=True;sc.render.threads_mode='FIXED';sc.render.threads=8
        salida._luz_y_mundo=luz
        candidato=max(m['edificios'],key=lambda e:e['area_m2'])
        ll=lados(candidato['huella']);fr=frentes_revision[candidato['id']] or max(ll,key=lambda l:l['largo'])
        ff=Fachada(None,fr,max(altura_suelo(*p) for p in candidato['huella']))
        cams=[]
        for nombre,ss,dd,mirar in (('frente',ff.largo*.5,12,ff.largo*.5),('vereda',.3,2,ff.largo*.7)):
            p=ff.punto(ss,0,dd);q=ff.punto(mirar,3.6)
            cams.append((nombre,(p.x,p.y,altura_suelo(p.x,p.y)+1.6),tuple(q)))
        revisar('codex',mid,fotos=[],camaras_extra=cams,ancho=1000,alto=750)
    if '--solo-revision' not in sys.argv:exportar('codex',mid)
    return m
