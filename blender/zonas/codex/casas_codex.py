"""Mínimo colonial para edificios sin foto: zócalo, portón, rejas, balcón,
cornisa/alero y cubierta de teja dentro de la huella. Colores deterministas
por id. No atribuye fidelidad fotográfica; las fachadas históricas se modelan
por separado. Un único constructor compartido por las manzanas de Codex.
"""
import hashlib,math
from kit import *
from piezas_codex import prisma_seguro,trasladar,recorte_estricto
from triangulacion_codex import triangular_huella


def _cortar(h,a,n,limite,signo):
    def d(p):return ((p[0]-a[0])*n[0]+(p[1]-a[1])*n[1]-limite)*signo
    out=[]
    for p,q in zip(h,h[1:]+h[:1]):
        dp,dq=d(p),d(q)
        if dp>=0:out.append(p)
        if (dp>=0)!=(dq>=0):
            t=dp/(dp-dq);out.append((p[0]+(q[0]-p[0])*t,p[1]+(q[1]-p[1])*t))
    return out


def cubierta_baja(c,h,z,color):
    """Dos faldones triangulados recortados, sin techos fuera de entrantes."""
    l=max(lados(h),key=lambda l:l['largo']);a=l['a'];nx,ny=l['normal']
    vv=[(p[0]-a[0])*nx+(p[1]-a[1])*ny for p in h];v0,v1=min(vv),max(vv);vm=(v0+v1)/2
    altura=min(1.85,max(.45,(v1-v0)*.18))
    def alto(p):
        v=(p[0]-a[0])*nx+(p[1]-a[1])*ny
        return z+.025+altura*(1-abs(v-vm)/max(.01,(v1-v0)/2))
    for tri in triangular_huella(h):
        for signo in (-1,1):
            mitad=_cortar(list(tri),a,(nx,ny),vm,signo)
            limpia=[]
            for p in mitad:
                if not limpia or math.dist(p,limpia[-1])>.00001:limpia.append(p)
            if len(limpia)>2 and math.dist(limpia[0],limpia[-1])<.00001:limpia.pop()
            if len(limpia)<3:continue
            area=abs(sum(p[0]*q[1]-q[0]*p[1] for p,q in zip(limpia,limpia[1:]+limpia[:1])))
            if area<.00001:continue
            c.poligono([(p[0],p[1],alto(p)) for p in limpia],'teja',color)
    # Hastiales y cierres apoyados directamente en el muro.
    for p,q in zip(h,h[1:]+h[:1]):
        c.poligono([(p[0],p[1],z),(q[0],q[1],z),(q[0],q[1],alto(q)),(p[0],p[1],alto(p))],'muro','#eee7da')


def casa_minima(e,col,completar_laterales=False):
    semilla=int(hashlib.sha256(e['id'].encode()).hexdigest()[:8],16)
    color=('#eee8da','#f2e9d9','#e9dfcb','#f3eadf')[semilla%4]
    pisos=1 if e['area_m2']<65 else 2;alto=4.2*pisos
    caracter=semilla%5  # colonial, neoclásica, republicana, mirador, comercial
    from parcelas_codex import plan_parcela,volumen_colonial,recortar_detalles,lucernario_si_ciego
    plan=plan_parcela(e);h=plan['principal']
    c=Constructor(e['id']+'_detalles');cuerpo=Constructor(e['id'])
    ls=[]
    for ring in plan['exteriores']:
        for l in lados(ring):
            l['i']=len(ls);ls.append(l)
    puntos=[p for ring in plan['anillos'] for p in ring]
    z=max(altura_suelo(*p) for p in puntos);zb=min(altura_suelo(*p) for p in puntos)-.5
    volumen_colonial(cuerpo,plan,zb,z+alto,color,('#b56948','#bf7655','#ac6548')[semilla%3])
    calle=[l for l in ls if l['a_calle'] and l['largo']>=1.25]
    if not calle:
        candidatos=[l for l in ls if l['largo']>=1.25]
        def distancia(l):
            x=(l['a'][0]+l['b'][0])/2+l['normal'][0]*2
            y=(l['a'][1]+l['b'][1])/2+l['normal'][1]*2
            return datos.calle_cercana(x,y)[0]
        if candidatos:calle=[min(candidatos,key=distancia)]
    if not calle:raise ValueError('Huella sin ningún lado habitable: '+e['id'])
    mayor=max(calle,key=lambda l:l['largo'])
    # En huellas pequeñas se necesita además un vano con reja; si el portón
    # ocupa toda la cara, la ventana va en el retorno más cercano a la calle.
    if mayor['largo']<2.8 and len(calle)==1:
        candidatos=[l for l in ls if l is not mayor and l['largo']>=1.25]
        if candidatos:calle.append(max(candidatos,key=lambda l:l['largo']))
    if completar_laterales:
        elegidos={l['i'] for l in calle}
        calle.extend(l for l in ls if l['largo']>=1.25 and l['i'] not in elegidos)
    deseados={l['i']:max(1,min(16,int(l['largo']/3.6))) for l in calle}
    escala=min(1,24/max(1,sum(deseados.values())))
    for l in calle:
        f=Fachada(c,l,z);n=max(1,int(deseados[l['i']]*escala));paso=f.largo/n
        principal=l is mayor;puerta_k=n//2
        # Un solo eje ancho: portón y ventana propios, no únicamente una puerta.
        if n==1 and principal and f.largo>=2.8:
            s=f.largo*.66;w=min(1.2,f.largo*.31)
            p=f.punto(s,0);fp=trasladar(f,h=altura_suelo(p.x,p.y)+.10-z,d=.02)
            puerta(fp,s,ancho=w,alto=2.65,rol='metal' if caracter==4 else 'madera',color='#767b75' if caracter==4 else '#65422d',color_moldura='#d0b697')
            for a,b in ((0,s-w/2-.18),(s+w/2+.18,f.largo)):
                if b>a:zocalo(f,.75,s0=a,s1=b,desde=zb-z,color='#ba9b78',sillares=False)
            ventana(trasladar(f,d=.02),f.largo*.22,1.25,ancho=min(.95,f.largo*.27),alto=1.75,reja=True,color_moldura='#f2e9dc')
            posiciones=[f.largo*.25,f.largo*.72] if f.largo>4 else [f.largo*.5]
        else:
            posiciones=[]
            for k in range(n):
                s=(k+.5)*paso;w=min(1.2,paso*.48);posiciones.append(s)
                if principal and k==puerta_k:
                    p=f.punto(s,0);fp=trasladar(f,h=altura_suelo(p.x,p.y)+.10-z,d=.02)
                    puerta(fp,s,ancho=min(1.4,paso*.62),alto=2.8,rol='metal' if caracter==4 else 'madera',color='#767b75' if caracter==4 else '#65422d',color_moldura='#d0b697')
                    radio=min(1.4,paso*.62)/2+.20
                    for a,b in ((k*paso,s-radio),(s+radio,(k+1)*paso)):
                        if b>a:zocalo(f,.75,s0=a,s1=b,desde=zb-z,color='#ba9b78',sillares=False)
                else:
                    zocalo(f,.75,s0=k*paso,s1=(k+1)*paso,desde=zb-z,color='#ba9b78',sillares=False)
                    ventana(trasladar(f,d=.02),s,1.25,ancho=w,alto=1.8,reja=True,color_moldura='#f2e9dc')
        if pisos==2:
            for k,s in enumerate(posiciones):
                w=min(1.2,paso*.45)
                mirador=caracter==3 and principal and k==len(posiciones)//2 and paso>2.5
                if mirador:
                    w=min(1.9,paso*.65)
                    f.caja(s-w/2,s+w/2,4.5,7.25,-.02,.45,'madera','#77503a')
                    ventana(trasladar(f,d=.46),s,5.0,ancho=w-.16,alto=1.9,
                            color_carpinteria='#77503a',color_moldura='#77503a')
                    for ds in (-w*.37,w*.37):
                        from piezas_codex import rama
                        rama(c,f.punto(s+ds,4.08,-.01),f.punto(s+ds,4.5,.43),.055,.055,'madera','#77503a')
                    alero_tejas(f,7.28,s0=s-w/2-.10,s1=s+w/2+.10,vuelo=.6,fondo=.5,pendiente=16)
                else:
                    ventana(trasladar(f,d=.02),s,4.6,ancho=w,alto=2.35,color_moldura='#f2e9dc',postigos=(caracter==0 and paso>3.2))
                if principal and k==len(posiciones)//2 and not mirador:
                    balcon_hierro(f,max(.1,s-w*.7),min(f.largo-.1,s+w*.7),4.6,vuelo=.55)
                    for ds in (-w*.5,w*.5):
                        from piezas_codex import rama
                        rama(c,f.punto(s+ds,4.18,.01),f.punto(s+ds,4.5,.5),.045,.045,'madera','#70503a')
                    if caracter in (0,1) and w>.8:
                        p=f.punto(s,4.6,.42)
                        c.cilindro(p.x,p.y,p.z,p.z+.25,.09,'teja','#b96f4d',lados=8,radio_arriba=.13)
                        from piezas_codex import rama
                        for j in range(3):
                            dx=(j-1)*.07
                            q=f.punto(s+dx,5.05,.42)
                            rama(c,(p.x,p.y,p.z+.21),q,.012,.007,'follaje','#4e7039')
                            c.esfera(*q,.055,'flor','#d9885b' if semilla%2 else '#dca8a6',segmentos=6)
            imposta(f,4.0,alto=.15)
        if principal and f.largo>4:
            from frentes_codex import farol_muro
            farol_muro(f,min(.65,f.largo*.1),3.15)
        cornisa(f,alto-.25,alto=.25,vuelo=.20,color='#f2e9dc')
        if caracter==1:
            for j in range(n+1):
                ss=j*f.largo/n
                pilastra(f,ss,zb-z,alto-.25,ancho=.22,vuelo=.10,color='#e5cfaa')
                f.caja(ss-.18,ss+.18,alto-.7,alto-.53,-.02,.18,'moldura','#e5cfaa')
        if caracter in (0,3):
            alero_tejas(f,alto,vuelo=.32,fondo=.8,pendiente=16)
        else:
            parapeto(f,alto,alto=.48 if caracter==2 else .36,color=color)
            if caracter==2:
                for j in range(n+1):
                    ss=j*f.largo/n
                    f.caja(ss-.1,ss+.1,alto,alto+.6,-.22,.02,'moldura','#f2e9dc')
                    c.esfera(*f.punto(ss,alto+.68,-.10),.10,'piedra','#d8c4a5',segmentos=6)
                for j in range(n):
                    ss=(j+.5)*f.largo/n
                    f.arco(ss,.13,.045,alto+.23,-.02,.055,'moldura','#dbc5a3',medio=False,segmentos=6)
        if caracter==4 and principal:
            ss=f.largo*.66 if n==1 and f.largo>=2.8 else (puerta_k+.5)*paso
            for j in range(12):
                hh=.35+j*.18;p=f.punto(ss,0)
                ff=trasladar(f,h=altura_suelo(p.x,p.y)+.10-z)
                ff.caja(ss-.38,ss+.38,hh,hh+.018,.07,.085,'metal','#92958a')
    recortar_detalles(c,e,datos)
    lucernario_si_ciego(cuerpo,c)
    principal_obj=cuerpo.objeto(col)
    c.objeto(col)
    return principal_obj,mayor
