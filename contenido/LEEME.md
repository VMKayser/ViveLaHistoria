# Contenido histórico: guía y juego

Material extraído de `OLIMPIADAS CONOCE TU HISTORIA.pdf`. El plan de 14 días está en `PLAN.md`.

## Herramientas

- `herramientas/ocr_libro.py`: OCR de las 1226 páginas → `libro/paginas/pNNNN.txt` (ya hecho; se puede reanudar).
  Usa tesseract local en `~/apps/tesseract` (instalado sin sudo).
- `herramientas/buscar.py "expr1" "expr2" --contexto 200`: busca sin distinguir tildes ni mayúsculas y une las
  palabras cortadas con guion.
- `libro/indice_querejazu.txt`: índice de capítulos y secciones de Querejazu, reconstruido a partir de los títulos.
- `herramientas/triaje.py 2 150`: menciones de lugares de Sucre y de otras ciudades por página (para decidir qué se lee
  completo y qué por encima).
- `herramientas/tanda.py 92 121 salida.txt --encima 95-99`: arma el texto de una tanda de lectura en un archivo.
- `catalogo/querejazu_01.jsonl` (Q 2–154, 178 datos) , `querejazu_02.jsonl` (Q 155–301, 163 datos) , `querejazu_03.jsonl` (Q 302–439, 106 datos) y `querejazu_04.jsonl` (Q 440–578, 138 datos); `revilla_01.jsonl` (R 582–791: texto completo de Revilla y anexos 1–3, 112 datos) y `revilla_02.jsonl` (R 792–955: anexos documentales, 30 datos). `cofre.jsonl` (C 956–1226, 98 datos; el OCR del Cofre se rehízo restando el fondo de pergamino: `ocr_libro.py 4 --rehacer 956-1226`). Formato en `PLAN.md`.
- `alias.json`: nombres de época de cada lugar (`buscar` = expresiones; `confirmado` = alias vistos, con su página).

Página = **página PDF**. Q = Querejazu (2–581), R = Revilla (582–955), C = *Cofre de encantos* (956–1226).
Calidad del OCR: Querejazu, muy buena; Revilla, texto original; *Cofre*, rehecho el 2026-11-21 (antes perdía las
palabras de los bordes por el fondo de pergamino); las páginas de fotos siguen dando basura: ver la imagen.

## Fichas (borrador; las del día 3 en adelante salen de la lectura completa)

| Ficha | Manzana | Lo más fuerte |
|---|---|---|
| `lugares/casa_libertad.md` | M037 | Universidad jesuita de 1624 → Asamblea de 1825 |
| `lugares/plaza_25_mayo.md` | P01 | Fundación, toros, 25 de mayo de 1809 |
| `lugares/catedral.md` | M055 | Virgen de Guadalupe, reloj de Londres, campanas de 1809 |
| `lugares/palacio_gobierno.md` | M055 | Asedio y renuncia del presidente Pizarro (⚠ identificación por confirmar) |
| `lugares/cabildo.md` | M037 | Toque de queda, la llave de la cárcel, Magdalena Téllez |
| `lugares/san_francisco.md` | M013 | El campanario de Lemoine; poema de la campana rajada |
| `lugares/san_miguel.md` | M028 | Iglesia de los jesuitas; cofradía de esclavos de Angola |
| `lugares/santo_domingo.md` | fuera (~80 m al este) | Las cuatro momias; Colegio Junín |
| `lugares/san_felipe_neri.md` | fuera (~60 m al sur) | Muerte de Pizarro y sus 1.800 onzas de oro |
| `lugares/recoleta.md` | fuera | Fundación, huaca del Tanga Tanga, cedro milenario |
| `lugares/santa_monica.md` | M027 | Primer convento de monjas; Juanita Zárate encerrada; la ventana regalada |
| `lugares/arzobispado.md` | ¿M063? | Palacio contiguo a la catedral; el balcón de los canónigos |
| `lugares/san_lazaro.md` | fuera | Primer templo; la reunión de 1544 y los diez degollados |
| `lugares/san_sebastian.md` | fuera | Parroquia de indios; rehenes chiriguanos |
| `lugares/san_agustin.md` | fuera | Capilla mayor vendida como panteón de la Audiencia |
| `lugares/hospital.md` | ? | Hospital de Santa Bárbara; el mercader que se quedó de mayordomo |
| `lugares/cerros.md` | fuera (telón de fondo) | Sicasica de oro, Churuquella de plata, tesoro yampara |
| `lugares/santa_clara.md` | fuera | La fundadora que hacía adobes; la marcha de las monjas (1758) |
| `lugares/santa_teresa.md` | fuera | Carmelitas; el corazón del arzobispo Molleda |
| `lugares/coliseo.md` | fuera (calle San Alberto) | Teatro colonial: Lope de Vega a un peso |
| `lugares/san_roque.md` | fuera | Ermita contra las pestes |
| `lugares/seminario.md` | ¿junto a la catedral? | Seminario San Cristóbal; guerra de colegios |
| `lugares/quirpinchaca.md` | fuera | La cabeza en la cruz y el pánico de 1780 |

Ubicación según `web/public/mapa/lugares.json` (OSM en coordenadas del lienzo), 2026-11-11.

**Otros lugares históricos dentro de la zona** (candidatos, sin ficha todavía): Templo de **Santa Mónica** (M027;
era el monasterio de Nuestra Señora de los Remedios, el primer convento de monjas, Q 91 y Q 127), Universidad de San
Francisco Xavier (edificio central, M036), Teatro 3 de Febrero (M037), Museo Eclesiástico (M063), Archivo y
Biblioteca Nacionales (M061). **Fuera de la zona:** Santo Domingo, San Felipe Neri, La Merced, San Agustín, Santa
Clara, Santa Teresa, San Lázaro, Palacio Arzobispal (~140 m) y la Recoleta (~800 m).

La lista **se cierra el día 10**, con todo el libro leído.

## Errores que hay que vigilar (aprendidos al leer)

- **La "iglesia de la Compañía" no es la Casa de la Libertad:** es San Miguel (desde 1780). La Casa de la Libertad
  era la Universidad.
- **Mismo nombre, otra ciudad:** Querejazu cuenta episodios de Potosí, el Cuzco o La Paz con las mismas palabras
  ("la iglesia de los jesuitas", "la plaza"). Antes de asignar un hecho a un lugar de Sucre, leer el comienzo de la
  sección (ejemplos: la riña de Magdalena Téllez de 1660 ocurrió en Potosí; la ejecución de Q 319 es la de Túpac Amaru
  en el Cuzco).
- **La campana rajada de San Francisco** está en el libro solo como poema.
- **La fecha de fundación** está discutida dentro del mismo libro (1539 o 1540). Revilla da 1538 y aclara que no se halló el acta (R-0640-1).
- **Querejazu y Revilla no siempre coinciden:** el motín de 1785 (21 de julio en Q, 21 de junio en R, aunque la bibliografía de R cita un estudio sobre el 22 y 23 de julio), el acta de los
  doctores ("arrancada" en Q; "testada" en R y "borró con su propio puño" en la relación anónima de 1809), el acusador de Segovia (rector saliente en Q, canónigo Olaso en R).
  Las dos versiones van en el catálogo; se resuelven el día 10 mirando las páginas.
- **Revilla cita documentos de los dos bandos:** Tardío, Benavente o Cañete eran realistas y exageran (horcas,
  mantequilla, la lista de 69 europeos en los calzones de Lemoine): en la guía se cuentan como lo que decían.

## Hilos para la trama del juego (para el día 12)

1. **El oro perdido de Pizarro:** el presidente derrocado en 1809 muere escondido en San Felipe Neri (1815); sus 1.800
   onzas de oro no aparecen; un nieto dice que se hallaron "mitad en la casa, mitad en la finca".
2. **La huaca del Tanga Tanga:** el tesoro yampara del rescate de Atahuallpa, que se buscó cavando bajo la Recoleta
   (leyenda + hecho: las excavaciones y la orden de la Audiencia).
3. **La noche del 25 de mayo de 1809 en tiempo real:** de las 7 de la noche a las 3 de la mañana. Cada parada es un
   momento: la detención de Zudáñez, las campanas de San Francisco y la Catedral, los cañones, la cárcel del Cabildo,
   la renuncia. Personajes reales y novelescos: Quitacapas (peluquero carioca y jugador), Juan Antonio Paredes (el
   misterioso alcalde del Cuzco), Lemoine, Monteagudo con 19 años, la hermana de Zudáñez.
4. **El acta arrancada:** a fines de febrero de 1809 el presidente García Pizarro, por orden del virrey, arrancó con sus propias manos del libro de la Universidad el acta (del 12 de enero) sobre los pliegos de
   Carlota Joaquina; su descubrimiento fue uno de los detonantes (Q 428, Q 442). Puede ser el "documento perdido" que los jugadores reconstruyen.
