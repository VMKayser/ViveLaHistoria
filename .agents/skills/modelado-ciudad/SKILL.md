---
name: modelado-ciudad
description: Modelar en 3D las manzanas y espacios del centro histórico de Sucre en el estilo del proyecto (fondo de animación pintado a mano), a partir de las huellas del lienzo y de las fotos ubicadas. Usar cuando haya que modelar, texturizar, corregir o revisar una manzana (M###), la plaza (P01) o la base urbana (BASE), o cuando se pregunte cómo se modela en este proyecto. La comparten Claude y Codex; cada uno trabaja solo en lo suyo.
---

# Modelado de la ciudad (Claude y Codex)

Lo modelan dos agentes en paralelo: **claude** y **codex**. Antes de nada:

1. Lee `AGENTS.md` (reglas del equipo y qué carpetas puedes tocar).
2. Lee `estilo/GUIA_ESTILO.md` y **mira** `estilo/referencia_estilo.png` con tu herramienta para ver imágenes.
3. Abre tu tarea: `coordinacion/TAREA_<AGENTE>.md` y tu estado `coordinacion/estado_<agente>.md`.

## Datos que ya existen (no regenerar sin pedirlo)

| archivo | qué es |
|---|---|
| `reparto/manzanas.json` | manzanas (M###) y espacios (P01, BASE): **dueño**, edificios con huella en metros, fotos asociadas |
| `reparto/reparto.png` | mapa del reparto (naranja claude al norte, azul codex al sur) |
| `reparto/edificios_lienzo.json` | huellas de todos los edificios del lienzo FBX en la zona |
| `reparto/terreno.json` | alturas del terreno (rejilla de 5 m); en el kit: `altura_suelo(x, y)` |
| `fotos/ubicaciones.json` | por foto: **dónde está lo fotografiado** (no desde dónde se tomó), calle y lugares cercanos |
| `fotos/IMG_*.jpg` | originales (4000 px); `web/public/fotos/medio/` versión de 1600 px para mirar |

**El punto de una foto es el lugar del objeto fotografiado.** Para saber qué es, cruza la foto con lo que hay en el
mapa en ese punto. Si ahí hay un templo y la foto muestra un templo, es ese.

Coordenadas: metros del lienzo, X este, Y norte, Z altura (Blender, Z arriba). Blender portable:
`~/apps/blender-5.2.3-linux-x64/blender` (no está en el PATH).

## Flujo por manzana

### 1. Comprobar que es tuya

Mira `dueno` en `reparto/manzanas.json` o en tu `TAREA_*.md`. **Si no es tuya, no la toques.** El kit también lo
verifica y corta la ejecución.

### 2. Ficha

```
python3 scripts/ficha_manzana.py M021
```

Genera en `revisiones/<dueño>/M021/`:
- `ficha.md`: edificios con id, medidas, desnivel y lados (y cuáles dan a la calle), más sus fotos
- `ficha_plano.png`: plano con ids, número de lado, fachadas a calle en rojo y fotos numeradas
- `ficha_fotos.jpg`: hoja con las fotos numeradas igual que en el plano

### 3. Mirar las fotos de verdad

Abre la hoja y luego cada foto en `web/public/fotos/medio/` (y el original en `fotos/` si necesitas un detalle). Para
cada edificio anota en la cabecera del script:
- qué fachada es (número de lado) y en qué fotos aparece
- pisos y altura estimada (un piso colonial mide de 4 a 4.5 m; usa puertas y barandas como escala)
- color real del muro y de las molduras (hex aproximado)
- zócalo: material y alto
- vanos por piso: cuántos, en qué posición, si son rectos o en arco, con reja, balcón o postigos
- portón: posición, ancho, arco, material
- remate: cornisa + pretil, alero de tejas con canes, almenas, frontón
- singularidades: torres, arquerías, cúpulas, escudos, faroles, árboles delante

Si un edificio no sale en ninguna foto: haz una versión sencilla y coherente con sus vecinos (`edificio_colonial`) y
márcalo como "sin foto" en tu estado.

### 4. Script de la manzana

Copia `blender/zonas/PLANTILLA.py` a `blender/zonas/<agente>/<MANZANA>.py`. Un script por manzana o espacio: es la
**fuente de verdad** y el GLB se regenera siempre desde ahí. Construye con el kit (`blender/kit/`):

- `edificio_colonial(...)`: punto de partida genérico (cuerpo, zócalo, vanos, cornisa o alero). Sirve para edificios
  sencillos o sin foto.
- Fachada a mano, para ser fiel: `c = Constructor(id)` → `c.prisma(...)` + `techo_plano(...)` → por cada lado a calle:
  `f = Fachada(c, lado, altura_suelo(...))` y piezas:
  `zocalo`, `imposta`, `cornisa`, `parapeto`, `pilastra`, `almenas`, `remate_bola`, `ventana` (arco, reja, balcón,
  postigos), `puerta`, `balcon_hierro`, `balcon_corrido`, `alero_tejas`, `arqueria`; y primitivas `f.caja`, `f.arco`,
  `f.timpano_arco`, `c.cilindro`, `c.esfera`, `c.poligono(..., grosor=)`.
- Al final: `c.objeto(col)`. Un objeto por edificio, nombrado con su id (`E78df12`); los objetos sueltos
  (árboles, faroles) se nombran `<MANZANA>_<cosa>_<n>`.
- Materiales: **solo los roles** de `blender/kit/paleta.py`, con color real opcional: `("muro", "#efe4cf")`. No
  inventes roles: si falta uno, pídelo en tu estado.
- Fachada local: `s` = a lo largo del lado (de a hacia b), `h` = altura sobre el suelo de esa fachada, `d` = salida
  hacia la calle.
- Si una pieza que necesitas no existe en el kit (por ejemplo una cúpula), constrúyela **dentro de tu script** o
  en `blender/zonas/<agente>/piezas_<agente>.py`. **No edites `blender/kit/`.**

### 5. Ejecutar, revisar y corregir

```
~/apps/blender-5.2.3-linux-x64/blender --background --python blender/zonas/<agente>/<MANZANA>.py
python3 scripts/comparar.py <agente> <MANZANA>
```

`revisar()` renderiza la manzana con contexto (suelo, volúmenes vecinos del lienzo y GLB ya exportados de **ambos**
agentes) desde una cámara frente a cada foto. `comparar.py` arma `comparacion_<foto>.jpg` (render | foto).
**Míralas** y corrige hasta que cuadren el número de pisos y vanos, las proporciones, los colores y el remate.
La cámara es aproximada: si no encuadra, usa `revisar(..., fotos=[], camaras_extra=[("frente", (x,y,z), (x,y,z))])`.
Cada render tarda unos 10 s; con muchas fotos, revisa primero un subconjunto (`fotos=[...]`).

Verificación mínima antes de dar una manzana por terminada:
- [ ] todas las fachadas a calle con foto, comparadas y fieles
- [ ] nada flota ni se hunde en la pendiente (el zócalo llega al suelo)
- [ ] no invade huellas de manzanas ajenas (los aleros y balcones pueden volar hasta 1 m sobre la vereda)
- [ ] triángulos dentro del presupuesto (lo dice `exportar` y queda en el manifiesto)
- [ ] actualizado `coordinacion/estado_<agente>.md`

### 6. Exportar

`exportar(AGENTE, MANZANA)` escribe `web/public/models/ciudad/<agente>/<MANZANA>.glb` (coordenadas absolutas,
Y arriba) y actualiza `web/public/models/ciudad/<agente>/manifiesto.json`. La ciudad (Godot, `ciudad3d/`) los toma al
correr `cd web && npm run ciudad` (empaqueta solo lo que cambió y exporta); después se recarga http://localhost:3000/ciudad.

Después: actualiza tu `coordinacion/estado_<agente>.md` y haz **commit solo de tus rutas** como dice la sección
"Git" de `AGENTS.md` (`git add <tus rutas>` + `git commit -m "[<agente>] <MANZANA>: ..." -- <tus rutas>`).

## Recursos de terceros y método rápido (pedido del usuario, 2026-11-12)

- **Recursos** (texturas, adornos, efectos): solo CC0 o licencias comerciales aprobadas por el usuario, registrados
  en `recursos/LICENCIAS.md` antes de usarse. Originales en `recursos/originales/` (no versionados). Las texturas las
  aplica el visor por ROL de material (relieve pintado triplanar, lavados de acuarela): en Blender basta con usar bien
  los roles (`cesped`, `adoquin`, `zocalo_piedra`, `piedra`, `agua`, `muro`…). Modelos de adorno CC0 (p. ej.
  Quaternius Stylized Nature MegaKit) se importan en el script del agente y se les reasignan roles de la paleta.
  Cielo, filtro pintado, cerros de fondo y bruma son del visor: no se hornean en los modelos.
- **Método** (cómo trabaja claude, más rápido y fiel): `coordinacion/METODO_CLAUDE.md`. Resumen: inventario por foto
  antes de modelar, un módulo por frente de cuadra con funciones por edificio, fachadas sobre el lado REAL del volumen
  recortado, `--sin-render` al iterar, renders solo de las cámaras de las correcciones, mosaicos para revisar, y
  auditoría automática (`blender/zonas/claude/auditoria.py -- <agente>`) antes de dar algo por terminado.

## Control de calidad antes de cada commit (pedido del usuario, 2026-11-13)

Lo ya hecho tiene que quedar limpio y coherente para pasear; esto es lo que garantiza que no se repitan los errores
que encontró el usuario (cables que cruzan muros, edificios "siameses", casas genéricas donde no van, muros blancos
del lienzo encima de lo modelado, árboles flotando, postes pegados a paredes).

1. Exporta con `--sin-render`.
2. `~/apps/blender-5.2.3-linux-x64/blender -b -P blender/kit/calidad.py -- <agente> <ID>` → `revisiones/<agente>/calidad.txt`.
   Tiene que dar **cero** en esa manzana (MURO_LIENZO, CABLE_MURO, POSTE_PEGADO, ARBOL_FLOTA, ARBOL_MURO, SIAMESES,
   RELLENO_PROHIB). Cada línea trae coordenadas: corrige en el script, no en el GLB.
3. Vistas a pie (1,6 m) por las veredas y en las esquinas; renders en la NVIDIA
   (`__NV_PRIME_RENDER_OFFLOAD=1 __GLX_VENDOR_LIBRARY_NAME=nvidia`).
4. Recién entonces commit + push.

Reglas de construcción que evitan los errores de raíz:
- Cada edificio vive dentro de su huella recortada; cornisas, aleros, letreros y balcones no cruzan la medianera.
- Zonas sin casas de relleno (atrios, explanadas, cuadras institucionales, tramos con foto sin modelar): en
  `reparto/manzanas.json → zonas_sin_relleno`. Huellas del visor: `python3 scripts/huellas.py` (nunca a mano).
- Postes en la vereda junto al bordillo (≥ 0,35 m de cualquier pared); cables de poste a poste o a una ménsula;
  árboles con el tronco en el suelo y la copa sin entrar en muros ni balcones.
- Piezas repetidas en módulos reutilizables (no copiar funciones entre scripts); datos en el reparto o en JSON.

## Qué NO hacer

- No modelar, exportar ni renderizar manzanas de otro dueño, ni escribir en carpetas del otro agente.
- No editar archivos compartidos: `blender/kit/`, `estilo/`, `reparto/`, `fotos/`, `scripts/`, `web/src/`, `AGENTS.md`,
  esta skill. Los cambios se piden en tu `estado_<agente>.md` (sección "Pedidos") y los decide el usuario.
- No pintar luz ni sombra en los colores, ni usar texturas fotográficas (el estilo lo pone el visor).
- No agregar autos ni gente. Cables, toldos, letreros y mercadería sí (pedidos por el usuario), siempre coherentes:
  cables anclados, toldos sin invadir la calzada, letreros dentro del vuelo permitido.
