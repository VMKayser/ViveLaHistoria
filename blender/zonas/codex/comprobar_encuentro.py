"""Comprueba la unión de museo y portada con las huellas y calles actuales."""
import os,sys,math,json
sys.path.insert(0,os.path.join(os.path.dirname(os.path.abspath(__file__)),'..','..'))
sys.path.insert(0,os.path.dirname(os.path.abspath(__file__)))
from kit import datos,Fachada
from museo_codex import plano_museo,avance_museo,huellas_ala
from triangulacion_codex import triangular_huella


def area(h):return abs(sum(a[0]*b[1]-b[0]*a[1] for a,b in zip(h,h[1:]+h[:1])))/2 if len(h)>2 else 0


def interseccion(h,tri):
    if sum(a[0]*b[1]-b[0]*a[1] for a,b in zip(tri,tri[1:]+tri[:1]))<0:tri=list(reversed(tri))
    for a,b in zip(tri,tri[1:]+tri[:1]):
        res=[]
        def d(p):return (b[0]-a[0])*(p[1]-a[1])-(b[1]-a[1])*(p[0]-a[0])
        for p,q in zip(h,h[1:]+h[:1]):
            dp,dq=d(p),d(q)
            if dp>=-1e-8:res.append(p)
            if (dp>=0)!=(dq>=0):
                t=dp/(dp-dq);res.append((p[0]+t*(q[0]-p[0]),p[1]+t*(q[1]-p[1])))
        h=res
        if not h:break
    return h

cat=datos.edificio('M055','E03fe1d');f=Fachada(None,datos.lados(cat['huella'])[12],0)
_,l,union=plano_museo();avance=avance_museo()
alas=huellas_ala();ala=[p for h in alas for p in h]
solapes=[]
for m in datos.reparto()['manzanas']:
    for e in datos.manzana(m['id'])['edificios']:
        if e['id']=='E03fe1d':continue
        h=e['huella']
        if not h:continue
        if max(p[0] for p in h)<min(p[0] for p in ala) or min(p[0] for p in h)>max(p[0] for p in ala):continue
        if max(p[1] for p in h)<min(p[1] for p in ala) or min(p[1] for p in h)>max(p[1] for p in ala):continue
        a=sum(area(interseccion(h_ala,list(t))) for h_ala in alas for t in triangular_huella(h))
        if a>.01:solapes.append({'manzana':m['id'],'edificio':e['id'],'area_m2':round(a,3)})
calle=datos.calle_real_cercana((l['a'][0]+l['b'][0])/2,(l['a'][1]+l['b'][1])/2)
holguras=[]
for j in range(9):
    p=f.punto(union*(1-j/8),0,avance)
    cerca=datos.calle_real_cercana(p.x,p.y)
    holguras.append(cerca[0]-cerca[1]/2)
informe={'avance_museo_m':avance,'union_s':union,'solapes_ala':solapes,
         'calle_frente_museo':calle,'holgura_minima_ala_calzada_m':min(holguras)}
print(json.dumps(informe,ensure_ascii=False,indent=2),flush=True)
ruta=os.path.join(datos.RAIZ,'revisiones/codex/encuentro_geometria.json')
with open(ruta,'w') as fh:json.dump(informe,fh,ensure_ascii=False,indent=2)
assert not solapes,'El ala invade otra huella'
assert min(holguras)>=-.05,'El frente del ala invade una calzada'
