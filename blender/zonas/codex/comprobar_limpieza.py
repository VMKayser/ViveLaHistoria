"""Verificaciones geométricas sin Blender: lotes y envolventes escalonadas.

Casos de regresión: parcela contenida, hueco interior, cuerpos contiguos
de distinta altura y torre apoyada en un cuerpo mayor. No exporta modelos.
"""
import importlib.util
import json
import math
from pathlib import Path
from parcelas_codex import diferencia_convexa,anillos_de_piezas,plan_parcela
from pavimentos_codex import _area
from volumenes_codex import cuerpo_escalonado


def rect(x,y,w,h):return [(x,y),(x+w,y),(x+w,y+h),(x,y+h)]
def area_firmada(h):return sum(a[0]*b[1]-a[1]*b[0] for a,b in zip(h,h[1:]+h[:1]))/2


class Captura:
    def __init__(self):self.caras=[]
    def poligono(self,p,*args):self.caras.append(p)
    def volumen(self):
        total=0
        for p in self.caras:
            a=p[0]
            for b,c in zip(p[1:-1],p[2:]):
                total+=sum(a[k]*(b[(k+1)%3]*c[(k+2)%3]-b[(k+2)%3]*c[(k+1)%3]) for k in range(3))/6
        return total


def comprobar():
    for hueco,esperada in ((rect(3,3,4,4),84),(rect(8,8,4,4),96),(rect(-1,-1,12,12),0),(rect(12,12,2,2),100)):
        piezas=diferencia_convexa(rect(0,0,10,10),hueco)
        assert math.isclose(sum(_area(p) for p in piezas),esperada,abs_tol=1e-7)
        rings=anillos_de_piezas(piezas)
        assert math.isclose(sum(area_firmada(h) for h in rings),esperada,abs_tol=1e-7)
    for tramos,volumen in (([(rect(0,0,10,10),5),(rect(4,4,2,2),10)],520),
                           ([(rect(0,0,5,10),5),(rect(5,0,5,10),8)],650),
                           ([(rect(0,0,8,8),4),(rect(4,4,6,6),7)],444)):
        c=Captura();cuerpo_escalonado(c,tramos,0,'#eeeeee')
        assert math.isclose(c.volumen(),volumen,abs_tol=1e-6),(c.volumen(),volumen)
    c=Captura();cuerpo_escalonado(c,[(rect(0,0,10,10),5)],0,'#eeeeee',vacios=[rect(3,3,4,4)])
    assert math.isclose(c.volumen(),420,abs_tol=1e-6),c.volumen()
    raiz=Path(__file__).resolve().parents[3]
    spec=importlib.util.spec_from_file_location('datos_sin_blender',raiz/'blender/kit/datos.py')
    datos=importlib.util.module_from_spec(spec);spec.loader.exec_module(datos)
    ids=sorted(p.stem for p in Path(__file__).parent.glob('M*.py') if 'from generica import construir' in p.read_text())
    informe=[]
    for mid in ids:
        m=datos.manzana(mid)
        if m['dueno']!='codex':continue
        for e in m['edificios']:
            plan=plan_parcela(e,datos);superficie=sum(_area(h) for h in plan['piezas'])
            assert math.isclose(sum(area_firmada(h) for h in plan['anillos']),superficie,abs_tol=.0001),(mid,e['id'])
            assert superficie<=_area(e['huella'])+.0001
            informe.append({'manzana':mid,'edificio':e['id'],'area_m2':superficie,'medianeras':plan['vecinos']})
    dest=raiz/'revisiones/codex/limpieza_20261113/parcelas.json';dest.parent.mkdir(parents=True,exist_ok=True)
    dest.write_text(json.dumps(informe,indent=2))
    print(f'8 regresiones y {len(informe)} parcelas: áreas, huecos, contornos y volúmenes correctos.')


if __name__=='__main__':comprobar()
