# Encargo para crear una skill: vehículo 3D desde un diseño

Este documento es el encargo y la memoria técnica para un agente que vaya a **crear una skill reutilizable**.
No es una skill instalada. Su objetivo es reproducir el proceso que llevó al autobús BRONCO aprobado por el usuario:
interpretar una lámina, modelar un vehículo reconocible, corregir sus curvas y ruedas, preparar su movimiento y
entregar archivos que otro desarrollador pueda integrar.

## 1. Qué debe conseguir la skill

Dado un diseño de un auto, minibús u otro vehículo, producir:

- Un modelo Blender editable y reproducible desde fuentes, a escala humana y en metros.
- Un GLB con materiales, texturas necesarias, jerarquía, pivotes y animaciones portables.
- Un visor para inspeccionar todos los lados y comprobar el movimiento del archivo exportado.
- Variantes de color cuando se soliciten, manteniendo el mismo vehículo.
- Un contrato de integración con ejemplos, parámetros, pruebas y límites reales.

La fidelidad incluye silueta, proporciones, curvaturas, cantidad de ventanas y puertas, posición de ejes,
llantas, luces, espejos, franjas y gráficos. No basta con reproducir los colores sobre una caja.
Separar lo observado de lo interpretado: una lámina sin medidas ni lateral oculto no permite asegurar exactitud
de las partes que no muestra.

### Cuándo se activa

Solicitudes de modelar un vehículo 3D desde una imagen, una lámina de vistas, bocetos o fotos; corregir ese modelo;
preparar sus ruedas, dirección y exportación. No activarla para modelar edificios, diseñar un logo aislado ni
resolver tráfico, navegación o físicas de toda una ciudad.

### Cómo empaquetarla

Crear un `SKILL.md` conciso con frontmatter `name` y `description`, activadores claros y pasos obligatorios.
Por ejemplo, el nombre puede ser `vehiculo-3d-desde-diseno`. Mantener ejemplos largos, matemáticas y referencias
en archivos de apoyo; herramientas repetibles en `scripts/` o la estructura que exija el sistema de skills.
La skill debe funcionar fuera de este repositorio: detectar entorno y rutas, no incrustar el usuario del sistema
ni asumir que todos los vehículos son autobuses BRONCO.

## 2. Caso de referencia y fuentes que debe estudiar el agente

En este repositorio, partir de `blender/zonas/codex/vehiculos/`:

| Archivo | Qué enseña |
|---|---|
| `referencia.png` | Lámina original: perspectiva, lateral de acceso, frente y trasera |
| `bronco.json` | Proporciones, ejes, colores, límites y variantes declarados como datos |
| `autobus_bronco.py` | Construcción, materiales, validación, exportación y estudio de revisión |
| `acabados_bronco.py` | Curvas, techo, deformación coherente del frente, neumáticos y llantas |
| `rig_bronco.py` | Jerarquía, metadatos y clips de rodadura |
| `cinematica_vehiculo.mjs` | Movimiento, ruedas por distancia y dirección Ackermann |
| `autobus_animado.mjs` | Adaptación de la cinemática a los pivotes de Three.js |
| `movimiento.test.mjs` | Pruebas numéricas y del adaptador |
| `generar_variantes.py`, `variantes_blender.py` | Variantes sin reconstruir ni alterar el rig |
| `colores_bronco.mjs` | Recoloración por instancia, sin afectar materiales compartidos |
| `validar_glb.cjs`, `validar_variantes.cjs` | Verificación del archivo que realmente se entrega |
| `visor.js`, `preparar_visor.cjs` | Inspección y prueba del GLB, controles de escritorio y táctiles |
| `INTEGRACION_VEHICULOS.md` | Contrato completo para quien recibe el vehículo |

Los resultados están en `web/public/models/ciudad/codex/vehiculos/`.
La skill debe extraer el método de estas fuentes, no copiarlas como una receta que deforma el mismo autobús
para fingir cualquier auto. Cada nuevo diseño necesita su propio análisis y geometría.

## 3. Herramientas y entorno

Usar Blender y su API Python `bpy` para construir, nombrar, repetir y exportar de forma controlada.
Blender MCP puede servir para observar o trabajar en una sesión interactiva cuando esté conectado;
no es un requisito para obtener el modelo. No afirmar que se dispone de MCP sin comprobarlo.

Antes de trabajar, leer las instrucciones del workspace y detectar Blender, dependencias, rutas de salida,
presupuesto y estilo. Respetar la propiedad de archivos y las sesiones de otros agentes. Si otra persona usa
Blender, crear un proceso/archivo independiente y limitar memoria; no vaciar su escena.
En Mi Ciudad se trabaja en las rutas del agente y no se coloca el vehículo como si fuese una manzana.

Un solo Blender pesado a la vez; revisión con GPU si existe. Registrar recursos externos y licencias antes de usarlos.
El código y los datos son la fuente de verdad. Un retoque manual que no quede registrado no debe desaparecer
al regenerar el modelo.

## 4. Flujo que debe implementar

### A. Inventariar la referencia antes de modelar

Mirar la lámina completa y cada vista. Registrar por separado:

- Largo/ancho/alto aproximados, distancia entre ejes, voladizos y altura del piso.
- Número y forma exacta de ventanas, pilares, puertas y escalones.
- Perfil del morro, inclinación y curvatura de parabrisas, techo y esquinas en planta.
- Radio y ancho de neumáticos, proporción del aro, concavidad y ventilaciones de llantas.
- Posición, tamaño y forma de faros, pilotos, espejos, limpiaparabrisas y parachoques.
- Paleta de pintura principal y detalle, zonas blancas, goma, vidrio y metal.
- Gráficos, qué lados se ven, inconsistencias entre vistas y partes no documentadas.

Elegir qué vista gobierna cada dimensión. En BRONCO el lateral gobierna ejes, largo y vanos; frente y trasera
gobiernan sus propios elementos. Usar una escala estimada explícita si no hay cotas, sin presentarla como medida real.

### B. Definir estructura y coordenadas

Trabajar en metros. Definir el frente del vehículo y un origen útil a ras del suelo. En este caso:

- Blender: +X delante, +Y izquierda, +Z arriba.
- GLB: +X delante, +Y arriba, +Z derecha.

Separar funciones de geometría, datos de diseño, rig, exportación y revisión.
Nombrar piezas por su función, no con nombres de primitivas sin significado.
Las primitivas son herramientas; el resultado debe ser el diseño específico, no un ensamblaje genérico.

### C. Resolver primero la silueta y las curvas

Hacer una primera versión del volumen y revisarla de frente, lateral y trasera antes de dedicar tiempo a adornos.
Usar perfiles con tangencias suaves, lofts y hombros elípticos donde el diseño tenga curva.
Un chaflán grande de pocas caras no reproduce una transición redondeada.

Cuando una superficie vaya a curvarse, darle subdivisiones suficientes **antes de deformarla**.
Conservar la misma transformación para chapas, marcos, cristales, franjas y piezas adyacentes.
Cerrar el encuentro techo/parabrisas y las esquinas del morro. Resolver espesores sin duplicar caras coplanares.

Elegir normales y bordes duros por pieza. La suavidad de una curva no debe mezclar el normal de la cara exterior
con el canto de una chapa y producir reflejos de una supuesta abolladura.
Los umbrales del caso BRONCO (p. ej. 45° en chapa y 80° en algunas piezas de llanta) son ejemplos que deben evaluarse,
no reglas universales para cualquier modelo.

### D. Construir aberturas e interior visible

Las ventanas deben tener hueco, cristal y marco; una puerta abierta necesita caja, piso y escalones detrás.
Los pasos de rueda deben estar recortados y tener un cierre interior lógico. Evitar neumáticos atravesando el piso.
Añadir lo que se ve desde las vistas de uso: asientos a una altura coherente, tablero y volante cuando corresponda.
No convertir el interior no mostrado en una invención que tape las ventanas o altere la silueta.

### E. Modelar ruedas y llantas con volumen

Construir el neumático por revolución de un perfil con talón, flanco convexo, hombro y banda de rodadura.
Dar profundidad a los canales y usar suficiente resolución angular para la distancia de observación prevista.
Construir el plato cóncavo y los labios de la llanta; las ventilaciones importantes deben ser agujeros reales.
Añadir buje, arandelas y tuercas proporcionados al diseño.

Una textura no corrige un neumático cilíndrico ni una llanta plana. El microrelieve acompaña la geometría.
En BRONCO se usó solamente un normal OpenGL de goma CC0 de ambientCG, con color base constante.
Usar UV de revolución, conservar la costura UV por esquina de cara y soldar los vértices geométricos de cierre;
colocar la costura donde sea menos visible, como el contacto con el suelo.

### F. Materiales y gráficos

Mantener pintura principal, pintura de detalle y superficies fijas claramente identificadas.
No hornear iluminación de estudio en el albedo. Conservar el estilo de la referencia y del proyecto.
Los recursos de terceros deben tener una licencia compatible y registrada. Incluir lo que use el GLB dentro del archivo
o entregar dependencias explícitas. No entregar rutas a texturas existentes solo en la máquina del agente.

Separar materiales antes de consolidar mallas. Mantener UV y tangentes válidas en las superficies con normal map;
eliminar UV sobrantes donde no se usan. Validar los nombres/roles que consume el proyecto.
Redibujar gráficos como geometría si eso encaja en el estilo, indicando si no son un calco exacto del original.

### G. Preparar el rig sin perder el centrado de ruedas

Cada rueda debe tener un pivote exactamente en su eje. Las delanteras necesitan dos movimientos independientes:

```text
raíz del vehículo
├── carrocería / interior / cristales / decoración
├── dirección delantera derecha
│   └── rodadura delantera derecha
├── dirección delantera izquierda
│   └── rodadura delantera izquierda
├── rodadura trasera derecha
└── rodadura trasera izquierda
```

En BRONCO: dirección +Z en Blender / +Y en GLB; rodadura hacia delante +Y en Blender / −Z en GLB.
Probar los signos con un punto de contacto; no asumir que ambos motores comparten ejes.
No unir las ruedas a los lotes estáticos de la carrocería.

Si se entregan clips de una vuelta, insertar suficientes muestras intermedias. Una rotación de 0° a 360° con solo
dos quaternions idénticos puede exportarse sin movimiento. En este caso hay 25 muestras en un segundo y dos clips,
`rodar_adelante` y `rodar_atras`, exportados desde pistas NLA y verificados en el binario final.

### H. Rodadura natural y dirección

Vincular el giro a distancia firmada, no a un incremento fijo por fotograma:

```text
ángulo de rodadura = distancia recorrida por esa rueda / radio
```

En curvas, calcular el arco de cada rueda. La dirección Ackermann da más ángulo a la delantera interior.
Usar el eje trasero como referencia del modelo cinemático para no desplazar lateralmente el vehículo al girar.
Controlar aceleración, frenada, cambio de sentido y velocidad del volante. Frenar antes de invertir la marcha.
Un teletransporte no debe generar vueltas ficticias; al parar, las ruedas deben quedar quietas.

Probar a distintas tasas de dibujo. No ejecutar un AnimationMixer sobre los mismos pivotes que escribe un controlador
por distancia. Distinguir claramente el modelo cinemático en plano de una simulación con pendientes y colisiones.

Para reproducir el cálculo en otro motor, sean `L` la batalla, `h` la semivía, `δ` el ángulo de la rueda delantera virtual central,
`ψ` el rumbo y `ds` el arco firmado del centro del eje trasero. Con X delante y Z derecha:

```text
k = tan(δ) / L
z_i = +h para rueda derecha, −h para izquierda
x_i = L para rueda delantera, 0 para trasera
ds_i = ds × sqrt((1 + k × z_i)^2 + (k × x_i)^2)
δ_i = atan2(k × L, 1 + k × z_i) en las delanteras; 0 detrás
rodadura_i(GLB) -= ds_i / radio

dψ = ds × k
dx_trasero = ds × sinc(dψ/2) × cos(ψ + dψ/2)
dz_trasero = −ds × sinc(dψ/2) × sin(ψ + dψ/2)
ψ_nuevo = ψ + dψ
```

Aquí `sinc(a) = sin(a)/a`, con valor 1 al acercarse a cero. Convertir después la posición del eje trasero al origen
visual del modelo usando su desplazamiento local. Este cálculo conserva también el signo en reversa.
Comparar orientaciones físicas, no componentes crudas de quaternion: `q` y `−q` representan la misma rotación.

### I. Variantes de color

Si solo cambia la pintura, conservar geometría, UV, texturas, rig, clips y parámetros de marcha.
Mantener pilotos, faros, goma, cristales, zonas blancas y gráficos en sus colores propios.
Para archivos GLB separados, se puede preservar el bloque binario y cambiar únicamente materiales y metadatos.
Recordar que `baseColorFactor` almacena valores lineales: convertir desde los hex sRGB de la paleta.

Para cambiar colores de instancias en ejecución, clonar solo los materiales de pintura de cada instancia;
no recolorear por accidente todos los vehículos que comparten una caché de materiales.
Entregar nombres claros, un manifiesto de variantes y un selector de revisión.

### J. Verificar el producto exportado y corregir

Revisar el GLB real, además del Blender. Usar las cámaras del diseño, una vista a altura humana y un detalle de rueda.
Inspeccionar curvas, parachoques, encuentros, aberturas, normales, reflejos, z-fighting, iluminación de goma y texturas.
Comparar lado a lado y corregir hasta que coincidan los elementos observables.

Comprobaciones mínimas:

- Escala, límites y contacto con el suelo; sin triángulos degenerados ni valores no finitos.
- Conteo de triángulos y mallas dentro del presupuesto elegido para ese vehículo.
- gltf-validator sin errores ni advertencias; tangentes unitarias, UV y normal map correctos.
- Pivotes y padres de dirección presentes; clips con una vuelta completa, eje y sentido correctos.
- Rodadura en recta y retroceso; arcos de curvas; frenada; teletransporte; consistencia a 30/60/120 FPS.
- Prueba en el visor real, teclado y mandos táctiles simultáneos, con tamaños de escritorio y celular.
- Variantes con el mismo binario y clips; verificación visual de los colores y de sus archivos descargables.

No aumentar el presupuesto para ocultar subdivisiones inútiles: localizar su coste y conservarlas donde aporten forma.
Si la calidad pedida justifica otro presupuesto, declararlo y medirlo. El BRONCO final tiene 68.848 triángulos,
45 mallas y 20 materiales; es un caso de referencia, no un límite obligatorio de la futura skill.

## 5. Fallos reales que la skill debe prevenir

| Fallo | Corrección que funcionó |
|---|---|
| Frente demasiado recto y techo con grandes chaflanes | Perfil suave y hombros curvos en geometría; comparar la silueta lateral |
| Franjas onduladas o chapa con apariencia abollada | Normales coherentes y bordes duros donde termina la cara exterior |
| Parachoques aplanado al redondear esquinas, matrícula aparentemente flotante | Subdividir también el parachoques antes de deformarlo y revisar sus apoyos |
| Ranura entre techo y parabrisas | Construir el cintillo de encuentro, no esconderla con otro plano coplanar |
| Moldura atravesando el hueco de rueda | Recortar la moldura con el mismo paso de rueda |
| Llantas como discos y ventilaciones pintadas | Plato por revolución y perforaciones reales |
| Raya visible de costura en el flanco | Soldar el cierre geométrico conservando UV por cara y situar la costura abajo |
| Clip de una vuelta que no gira | Muestrear la vuelta completa y comprobar quaternions exportados |
| Ruedas que giran estando parado | Rodadura calculada a partir de distancia, con pruebas de parada |
| Todas las ruedas girando igual en curvas | Arcos independientes y dirección Ackermann |
| Un color cambiado en todos los vehículos | Materiales de pintura clonados por instancia |
| Modelo aprobado en Blender pero roto en web | Cargar el GLB final y probarlo en navegador |

## 6. Entrega y criterio de aceptación de la skill

La skill debe conducir hasta un resultado concreto y revisable, no terminar en un plan.
Su entrega debe incluir fuentes, datos, referencia conservada, `.blend`, GLB, texturas/licencias, pruebas,
visor y guía de integración. Registrar los supuestos y lo pendiente. No afirmar que el tráfico ya está integrado
si solo se entregó el vehículo y su prueba independiente.

En un workspace compartido, respetar el reparto de rutas y hacer commits explícitos de las rutas propias.
La skill no debe imponer confirmaciones adicionales para tareas reversibles ya autorizadas.
Si el usuario pide cambios, incorporar la corrección en las fuentes y repetir solo las verificaciones afectadas.

Antes de dar por creada la skill, probarla con otro diseño pequeño: debe obtener su propia silueta y proporciones,
no otra copia coloreada de BRONCO. Evaluar el parecido, los acabados y la reutilización del resultado.
