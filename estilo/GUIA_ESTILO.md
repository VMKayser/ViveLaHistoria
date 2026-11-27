# Guía de estilo — Mi Ciudad 3D (Sucre)

Referencia visual: `estilo/referencia_estilo.png` (elegida por el usuario). **Mírala antes de modelar cualquier cosa.**

## 1. En una frase

Sucre real, edificio por edificio, pintada como un **fondo de película de animación japonesa dibujado a mano**.
Hay que hacerla fiel en forma, proporciones y colores, pero con luz cálida de tarde, sombras frías de color
lavanda, materiales que parecen pintados y nada de suciedad ni desorden realista.

## 2. Qué se ve en la referencia

- **Escena:** una casona colonial blanca de dos pisos con alero de tejas y canes de madera, un portón de hierro forjado
  entre pilares de sillares de arenisca rematados con bolas, un patio al fondo, una torre campanario blanca con
  cúpula, un muro bajo de piedra con reja y un jardín con flores naranjas.
- **Luz:** sol de media tarde, cálido y lateral, que viene desde arriba a la izquierda. El cielo es azul saturado,
  con cúmulos blancos y esponjosos.
- **Sombras:** el rasgo más importante. En los muros blancos las sombras **no son grises**: son **lavanda o azul
  grisáceo** (`#9198a6`–`#b3a5a1`), mientras que la parte al sol es crema cálida (`#fae6d5`). Bajo los aleros hay una
  banda de sombra marcada. El follaje proyecta sombras moteadas sobre las paredes.
- **Superficies:** pintadas a mano. Las paredes de cal tienen manchas suaves y desconchados sutiles, y los sillares
  muestran juntas claras con variación de tono entre piedras. No hay texturas fotográficas ni ruido.
- **Formas:** arquitectura fiel pero algo "blanda". Los bordes se ven ligeramente suavizados, las piezas son gruesas
  y legibles (canes de madera, marcos de ventana y remates de bola) y no hay detalle microscópico.
- **Color:** saturado pero armónico. Paleta cálida (crema, terracota, arenisca, madera rojiza) contra cielo azul y
  verdes profundos. El negro puro no existe: el hierro es marrón muy oscuro.

## 3. Reglas para modelar

1. **La fidelidad manda.** La planta sale de la huella del lienzo. El número de pisos, las ventanas, puertas,
   balcones, zócalos, cornisas, aleros, torres y arcos salen **de las fotos**. Si la foto muestra 5 ventanas,
   van 5. Los colores reales de cada fachada (blanca, crema, ocre con molduras amarillas, etc.) se respetan con
   `material(rol, "#color")`.
2. **Estilizar es simplificar, no inventar.** Se exageran un poco los elementos característicos: aleros con canes
   visibles, molduras gruesas, rejas legibles y remates de bola. Nunca se agrega lo que no está en las fotos.
3. **Se omite** el ruido urbano: autos, gente, toldos y puestos ambulantes, carteles publicitarios y
   antenas. **Excepción pedida por el usuario (2026-11-06): postes de luz, cables y semáforos SÍ van** (son muy
   característicos de las calles de Sucre en las fotos): postes de hormigón junto al bordillo, varios cables negros
   por vano con flecha, acometidas a las fachadas, faroles de brazo curvo. Los letreros importantes (nombre de un museo o una placa histórica) se dejan como una placa simple
   con el rol `letrero`, sin texto.
4. **Se incluye** lo que da identidad: faroles coloniales, rejas, balcones, portones, árboles de la calle y de las
   plazas, fuentes y monumentos.
5. **Las alturas del lienzo no sirven** (casi todas son 4 m o 10 m por defecto). Estima la altura con las fotos:
   un piso colonial mide de 4 a 4.5 m, la planta baja con zócalo de 4.5 a 5 m y una ventana alta unos 2.2 m.
6. **Escala humana:** una puerta mide de 2.2 a 3.2 m y una baranda de balcón 1 m. Úsalas para verificar las
   proporciones contra la foto.

## 4. Paleta (albedo = color propio del material, sin luz)

Definida en `blender/kit/paleta.py`. El nombre del material es el **rol**. Si la fachada real tiene otro color, se
usa `rol__rrggbb`.

| rol | color | uso |
|---|---|---|
| `muro` | `#f3e6d3` | cal blanca cálida |
| `moldura` | `#f7efe3` | cornisas, marcos y pilastras de yeso |
| `pintura_acento` | `#e7c46a` | molduras pintadas (ocre amarillo típico de Sucre) |
| `zocalo_piedra` | `#c9935f` | basamento de sillares |
| `piedra` | `#e8c39a` | pilares, remates, losas de balcón y portadas de piedra |
| `azotea` | `#d8c3a5` | techos planos |
| `teja` | `#c0643a` | tejas de terracota |
| `madera` | `#5a3422` | canes, vigas y portones |
| `marco_ventana` | `#6a3622` | carpintería |
| `vidrio` | `#3a4550` | vidrio oscuro, sin reflejos |
| `hierro` | `#2b2522` | rejas, balcones y faroles |
| `metal` | `#8f8a7e` | campanas y metal claro |
| `vereda` / `calzada` / `adoquin` | `#d9a77c` / `#8b7a6d` / `#b98b69` | suelos |
| `cesped` / `follaje` / `follaje_claro` / `tronco` / `flor` | `#7fa046` / `#4d6b2a` / `#8fae45` / `#4a3626` / `#e8742c` | vegetación |
| `agua` | `#6fa8c9` | fuentes |
| `letrero` | `#efe2c4` | placas sin texto |

Colores de **luz** de la referencia (los usa el visor, no se pintan en el modelo): muro al sol `#fae6d5`, muro en
sombra `#9198a6`, cielo alto `#4793d9`, cielo bajo `#86b6e6`, sol `#fff0d8`.

## 5. Cómo se logra el aspecto en la web

El modelo trae solo **geometría + materiales por rol**. El visor web (responsabilidad de Claude) agrega el estilo:

- un sombreado tipo animación (rampa de luz suave con 3 tonos, sombras teñidas de lavanda y luz cálida)
- variación pintada por rol (manchas de cal en `muro` y variación entre sillares en `zocalo_piedra`/`piedra`)
- un sol de tarde con sombras proyectadas, oclusión ambiental y cielo con nubes

Por eso **nadie pinta luces ni sombras en los colores del modelo** ni hornea texturas fotográficas.

## 6. Presupuesto

- Casa típica: hasta unos 15 000 triángulos. Un monumento (catedral, templo o casa histórica principal) puede
  llegar a 60 000.
- Las fachadas que no dan a la calle van lisas (solo muro). El detalle se pone donde se ve.
- Sin bisel por defecto (`biselar=0`). Se puede usar bisel de 0.02–0.04 solo en piezas grandes de monumentos.
- Total por agente: hasta unos 1.5 millones de triángulos en toda su zona.
