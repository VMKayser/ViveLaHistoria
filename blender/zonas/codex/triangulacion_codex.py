"""Triangulación 2D de huellas cóncavas conservando sus entrantes."""


def triangular_huella(huella):
    pts=[tuple(p[:2]) for p in huella]
    if pts[0]==pts[-1]:pts.pop()
    def cruz(a,b,c):return (b[0]-a[0])*(c[1]-a[1])-(b[1]-a[1])*(c[0]-a[0])
    area=sum(a[0]*b[1]-b[0]*a[1] for a,b in zip(pts,pts[1:]+pts[:1]))
    if area<0:pts.reverse()
    ids=list(range(len(pts)));tris=[]
    while len(ids)>3:
        encontrado=False
        for k,i in enumerate(ids):
            ia,ib=ids[k-1],ids[(k+1)%len(ids)]
            a,b,c=pts[ia],pts[i],pts[ib]
            if cruz(a,b,c)<=1e-8:continue
            if any(cruz(a,b,pts[j])>=-1e-8 and cruz(b,c,pts[j])>=-1e-8
                   and cruz(c,a,pts[j])>=-1e-8 for j in ids if j not in (ia,i,ib)):
                continue
            tris.append((a,b,c));ids.pop(k);encontrado=True;break
        if not encontrado:
            # Los puntos intermedios sobre un mismo lado no definen una oreja.
            for k,i in enumerate(ids):
                if abs(cruz(pts[ids[k-1]],pts[i],pts[ids[(k+1)%len(ids)]]))<1e-8:
                    ids.pop(k);encontrado=True;break
            if not encontrado:raise ValueError('Huella no simple o degenerada')
    if len(ids)==3:tris.append(tuple(pts[i] for i in ids))
    return tris
