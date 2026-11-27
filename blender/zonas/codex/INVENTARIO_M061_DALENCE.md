# Dalence M061 · R0088–R0095 · inventario antes de modelar

Ocho referencias completas, capturas y recortes examinados juntos.
Estaciones proyectadas desde el final de E00e8b2 hacia Nicolás Ortiz:
A = (−313,954; −344,044), u = (0,73946; −0,67320), longitud 70,60 m.
Cámaras R88…R95: −3,81 / 3,87 / 15,78 / 27,12 / 43,00 / 53,14 /
60,42 / 68,26 m. La pista R0093/M074 es un impacto a cero metros:
la referencia es el acceso UCB de esta misma secuencia, no otro edificio.

| Referencia | Edificio y tramo | Inventario |
|---|---|---|
| R0088 | E00e8b2, previo a estación 0 | Blanco #eeeae3, molduras verde gris #697875, basamento arenisca #c9955f. **Nueve** ranuras hexagonales, tres grupos de tres (el modelo tenía seis). Portón negro alineado con ventanal vertical de escalera. Tres ventanales rectangulares intermedios; dos arcos encima, mansarda diagonal y lucarna. Torre izquierda alta conservada. |
| R0088/89 | Ala derecha E00e8b2 | PB+2, dos balconeras granates por piso con arco rebajado y guardapolvo gris. PB: portón ancho a izquierda y puerta peatonal estrecha a derecha; no dos puertas iguales. Frisos grises, casetones bajo ventanas, zócalo bajo piedra. Árbol ralo enfrente. |
| R0089/90 | Patio cerrado, estaciones 0–10 | Muro blanco ciego de ~4,8 m sobre basamento de piedra de ~2,6 m; detrás, pabellón de cristal oscuro con dos hojas proyectantes. Teja posterior. No casas genéricas. |
| R0090/91 | Pilón, 10–15 m | Sillería arenisca #ac8965, altura ~14 m. Monograma negro: P en círculo, travesaño, fuste y rayos. No torre de viviendas ni ventanas. |
| R0090/91 | Bloque moderno, 15–27 m | Basamento pétreo + **tres** plantas altas, **cinco ventanas individuales por fila**. Carpintería gris verdosa y algunas hojas abiertas; bandas blancas profundas, pretil recto. Retorno hacia patio también con ventanas. |
| R0091/92/93 | Aulas UCB, 27–58 m | Basamento pétreo y tres plantas blancas; siete módulos de pares reconstruidos con solapes (no sumar las fotos): **14 + 14 + 12 ventanas**; el último módulo de la planta inferior alta es el panel institucional ciego, no dos vanos. Vidrio/montantes gris verdoso, hojas con lamas y dintel fino. Pilastras planas por par, bandas/cornisas entre pisos, respiraderos pequeños alternos; alero de teja con canes. PB: una ventana rectangular enrejada por módulo (seis), no duplicar la pareja de arriba; al final gran portón rojizo de **20 cuarterones**, marquesina blanca, medallón/nombre y placa verde del punto de encuentro. Comprobar cuenta final en mosaico de toda la secuencia. |
| R0094/95 | Esquina, 58 m hasta giro | Dos plantas, zócalo arenisca ~1,3 m, PB ciega con dos recuadros tapados y llagueado horizontal. Una balconera granate visible a la derecha; panel superior izquierdo ciego tras árbol. Guardapolvo curvo, pilastras, volutas/capiteles, cornisa gruesa y pretil. Árbol ralo grande, poste y semáforo existentes. El mirador al otro lado corresponde a Claude/AMP_S. |

La huella original de E311863 retrocede hasta ~20 m desde la calle: no
alcanza dibujar ventanas sobre esa pared. Se amplía el frente propio y se
recorta por las calles reales; el bloque posterior conserva su frente
Nicolás Ortiz. Funciones separadas por edificio y profundidad propia,
con cuerpos contiguos, sin duplicar un volumen dentro de otro. Patios con
piso para liberar el relleno al regenerar BASE. Colores por rol; sin
texturas ni fuentes de terceros. Un Blender y contexto cercano.

## Comprobación y afinado por comparación

- R0088/89: basamento de 4 m solo bajo la parte moderna; ala derecha con
  basamento de 1,2 m y muro blanco. Las cuatro balconeras son rebajadas,
  granate `#673445`, con paños bajos lisos. Garaje/escalera alineados.
- Árbol de esa ala colocado ante el portón, con bifurcación y hojas ralas;
  las copas esféricas anteriores no corresponden a estas referencias.
- R0091: poste delgado de alumbrado de ~8,6 m con brazo curvo, estación
  ~37 m y pie junto al bordillo. Seis conductores del haz están sujetos
  a ménsulas/aisladores; cada segmento comprobado contra arquitectura.
  El intento de continuar hasta el poste de E00 cruzaba el edificio y
  **no se añadió**: ambos extremos del haz quedan en ménsulas reales.
- R0093: no se acepta la antigua imagen negra tomada dentro del relleno.
  Con la BASE publicada de 13:04, el acceso queda visible; quitar los
  dos falsos vanos tras el rótulo. Cámara original conservada; mirada
  reconstruida del rumbo por tratarse de un impacto a cero metros.
- R0094/95 y 131002: misma cota de calle en el frente y el retorno de la
  esquina. La cota máxima posterior producía una astilla blanca sobre
  la cornisa. No hay frontón en este frente: el de 131002 pertenece a
  la casa de enfrente. Balconeras bajas de madera, sin rejas inventadas.
- El mirador del lado opuesto corresponde a Claude/AMP_S; no se modela
  ni se modifica desde M061. Interiores posteriores no visibles siguen
  siendo aproximaciones de volumen y cubierta.

## Repaso posterior · Nicolás Ortiz 131002

Dos banderolas azules oscuras, DERECHO y MEDICINA, con círculo y letras
ocre, sobre las dos primeras balconeras. Se modelan con trazos propios y
menos de 210 triángulos adicionales; la fachada sigue bajo 15.000.
Paño a 33 cm de la pared, sujeto a una barra que entra en ella y pasa
por delante de la cornisa: la primera prueba cortaba visualmente la
tela al atravesar esa moldura y se corrigió antes de publicar. Foto
131002 y tres vistas a 1,6 m repetidas; cero separaciones reales.
