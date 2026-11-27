# Observaciones #22–#26 · 2026-11-13

## P01 · #23

Se comprobaron las vistas de Claude `paseo3/Plaza_040…060.jpg`: cuña SE sin
suelo entre vereda y paseo, y rendijas en las otras esquinas. El recorte
anterior prolongaba tangentes de calles curvas. Se conserva el polígono
del reparto y se restan corredores **finitos**, con un solape oculto bajo
la vereda. Verificación por rayos de todo el interior y el perímetro;
auditoría de calzada independiente. No se modifica BASE.

## Nave de San Miguel, Arenales · #24

Referencias 130427, 130431, 130435 y 130438 abiertas completas antes de
modelar. Son tomas solapadas de un mismo muro; no se suman como cuatro
fachadas. La asociación al edificio del lienzo no define su posición:
falta la franja sobre Arenales, delante de Eeb6abd.

- Paño blanco cálido `#eeeae3`, aproximadamente 9–10 m, casi ciego;
  zócalo apenas visible de unos 20 cm. Sin puertas ni ventanas bajas.
- Un solo vano alto rectangular, ~1,0 × 1,45 m, carpintería oscura,
  marco blanco grueso y bandera boliviana colgada de asta oblicua.
- Cornisa de tres filetes bajo alero corto de teja rojiza; dos aguas
  paralelas a la calle. Fondo y pendiente posterior estimados.
- Dos salientes blancos pequeños bajo la cornisa (tubos/gárgolas),
  farol verde colgado de brazo doble junto al extremo del atrio.
- Haz de cables sujeto a fachada a media altura, con grampas; sin
  tendidos libres que terminen en el aire.
- Enredadera estrecha que trepa por el extremo junto a la reja. La
  vegetación y el portal del atrio vecino se distinguen del muro ciego.

Huella propia recortada por Arenales, unida al cuerpo posterior donde
coinciden; no se añade otra portada ni otra torre. El templo de R0036/37
ya se conserva en M027. Verificar cobertura, encuentro y cámara a pie.

## Junín oeste · #22

130357 y 130401 examinadas completas junto a R0034/R0035. Atención a la
identidad del muro: el paño largo blanco que aparece a la derecha en
`paseo3/Junin_040.jpg` corresponde al frente del convento Eeb6abd/M037,
con ventanas altas y accesos separados; no al frente con portada
barroca de Eaeb297/M027, que ya tiene sus dos plantas detalladas.
Comprobación de cotas: la cota máxima de Eeb6abd es 58,1209 m, pero
Junín está a 55,43–55,51 m. Los vanos habían quedado 2,6 m demasiado
altos. Se reconstruye el frente a partir de la cota máxima **de su calle**,
con zócalo de 0,9 m, dos puertas, tres vanos altos junto al sol; dos arcos
en el quiebre y seis pares de vanos en la prolongación sin foto frontal
completa. No se añaden balcones residenciales ausentes de la referencia.
Eaeb297/M027 conserva su portada barroca de R0035 y sus dos plantas; no
se confunde con el muro de enfrente. M036 es una huella interior.

Mobiliario nuevo sobre los lados reales del eje: dos postes/seis vanos de
cable por vereda (M027 NO y M037 SE), tres y cuatro faroles respectivamente.
Pies a la cota de acera, junto al bordillo; extremos en aisladores y cada
segmento comprobado contra la geometría con BVH. No se inventan árboles
sobre una acera de 1,5 m donde estas fotos no los muestran.

## Cubiertas M055 · #26

Pedido posterior del usuario: retirar viviendas genéricas indebidas de la
cuadra Catedral/Gobernación. Reabiertas 130715/724/736/741: dos cuerpos
institucionales continuos ante la plaza, sin tiendas entre ellos.

La BASE actual coloca casas ante esos frentes: 194 rayos interceptados,
137 frente a Gobernación, 53 frente al paño blanco y 4 junto al atrio.
Diagnóstico e imágenes guardados; se pidió a Claude retirar su relleno.
En lo propio: retirada la casa inventada E749b6b; área despejada con piso,
sin atribuir exactitud documental a su distribución interior. Suelo de
enlace a la acera para evitar huecos y futuras viviendas automáticas.
Faldones de teja sobre la nave y el ala ya existentes de E03fe1d, con
pendiente posterior estimada; atrio descubierto, torres, portada y
Gobernación conservados. E1e60e8 pertenece a M061, no a M055; no se
confunde con la nave ni se retira su geometría por cercanía en la vista aérea.

La comprobación local `--sin-relleno` es solo diagnóstica: oculta BASE_relleno
en memoria. **No prueba que el visor real esté despejado**. La validación
con BASE regenerada queda pendiente hasta que Claude la publique.

## Teatro 3 de Febrero · repaso posterior a #22

130452/130521 completas y ampliación del original (3264 px) examinadas.
Once ejes sobre Arenales: tres accesos en 3.º/7.º/11.º; el último es el
portal principal, más ancho y con nombre institucional en tres líneas.
Ocho ventanas inferiores de medio punto con rejas; once puertas-ventanas
altas entre pilastras dobles, con antepechos de seis balaustres grises.
Frontones triangulares sobre los vanos altos; capiteles vegetales, dos
cornisas dentadas, friso de recuadros y remates curvos del pretil con
pedestales dobles sobre cada par de pilastras. Portones de madera muy
oscura con cuarterones y dovelas grises separadas por juntas claras.
Abanicos de hierro de dos arcos y nueve radios en las ocho rejas bajas;
tres faroles verdes suspendidos de ménsulas en los entrepaños altos.
Nombre institucional dibujado con trazos geométricos propios, sin fuentes
ni imágenes externas.

Zócalo gris pétreo ~1,1 m en ambas fotos, muro blanco #eeeae7, gris de
relieves #747b7f y balaustres #555c60, madera #50362a. Retorno sin foto
frontal: continuidad estimada. La cota máxima del lote es 61,537 m; el
frente baja de 61,249 a 58,354 m. La referencia anterior al máximo dejaba
el zócalo de ~4 m en el extremo bajo. Se hace seguir el datum al terreno
del frente, sin modificar BASE ni afirmar que las cotas sean levantadas.
El acceso principal no puede atravesar la imposta; los altos de puerta
del kit son arranques del arco, no altura total. Comprobar la altura
total con radio y clave antes de comparar de nuevo.

Datum final del Teatro: interpolación **lineal** entre las cotas extremas de
Arenales. Conserva continuidad de las cornisas largas y sus dentículos;
el seguimiento no lineal anterior producía separaciones de unos 9 cm.
Pase final por contactos: cero separaciones; dos vistas finales a 1,6 m
examinadas, fuentes y GLB coherentes.
