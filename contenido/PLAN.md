# Plan: libro "Olimpiadas Conoce tu Historia" leído y catalogado en 14 días

Fuente: `OLIMPIADAS CONOCE TU HISTORIA.pdf` (1226 págs., tres libros):

| Págs. PDF | Libro | Uso principal |
|---|---|---|
| 2–581 | Roberto Querejazu, *Historia de Chuquisaca 1538–1825* | cronología, personajes, trama del juego |
| 582–955 | Paola Revilla, *La autonomía revolucionaria de la Audiencia de Charcas hacia 1809* | detalle de 1809 |
| 956–1226 | *Sucre, cofre de encantos y recuerdos* | lugares, edificios, tradiciones |

Toda cita se hace con **página PDF** (`p0123`); en las fichas se anota también la página impresa del libro.

## Reglas de lectura

- **Nombres de época.** Un lugar puede aparecer con otro nombre (la Casa de la Libertad era el colegio/universidad
  de los jesuitas; la Catedral, "iglesia matriz"; la plaza, "plaza mayor"). Se busca con el diccionario de alias
  (`contenido/alias.json`), que crece a medida que se lee.
- **Nada in media res.** Al encontrar una mención se lee hacia atrás hasta el inicio del capítulo o episodio, y
  hacia adelante hasta que el episodio cierra.
- **Hecho ≠ leyenda ≠ ficción.** Cada dato lleva `tipo`: `hecho`, `tradicion` (leyenda, "se cuenta que") o, en el
  juego, `ficcion`. Si dos libros se contradicen, se anotan las dos versiones.
- **Citas literales** se corrigen contra la imagen de la página (el OCR puede tener erratas).

## Criterios acordados con el usuario (2026-11-11)

- **Lugares:** se registra todo lugar de la ciudad donde haya ocurrido algo relevante, histórico, curioso o
  llamativo, **esté dentro o fuera de la zona modelada**. Cuando aparece uno nuevo durante la lectura, se le abre
  ficha en `lugares/` (aunque sea con un solo dato). Al final se decide cuáles se implementan completos: no se podrá
  con todos.
- **Público:** general (todas las edades, turistas y nacionales).
- **Datos crudos sí:** la historia como fue, sin suavizar (ejecuciones, esclavitud, violencia), con su fuente.
- **Guía:** unos 60 s por parada como referencia, no obligatorio: lo que el tema pida.

## Calendario

| Día | Trabajo | Resultado |
|---|---|---|
| 1 | OCR completo, buscador, diccionario de alias, **primeras 10 fichas** (búsqueda dirigida) | `libro/paginas/`, `alias.json`, `lugares/*.md` |
| 2 | Revisión de las fichas con el usuario (contenido, tono, criterios); lista **provisoria** de lugares y formato de datos (JSON para el visor) | criterios + esquema |
| 3 | Querejazu págs. 2–150: lectura completa y catálogo | `catalogo/querejazu_01.jsonl` |
| 4 | Querejazu págs. 155–300 (el día 3 llegó hasta 154) | `catalogo/querejazu_02.jsonl` |
| 5 | Querejazu págs. 302–450 (el día 4 llegó hasta 301) | `catalogo/querejazu_03.jsonl` |
| 6 | Querejazu págs. 440–581 (empieza con el 25 de mayo de 1809 completo) | `catalogo/querejazu_04.jsonl` |
| 7 | Revilla págs. 582–770 | `catalogo/revilla_01.jsonl` |
| 8 | Revilla págs. 792–955 (anexos documentales; el día 7 llegó hasta 791) | `catalogo/revilla_02.jsonl` |
| 9 | Cofre de encantos págs. 956–1226 (texto y pies de foto) | `catalogo/cofre.jsonl` |
| 10 | Consolidación: personajes, cronología maestra, alias definitivos, contradicciones. **Se cierra la lista de lugares** con todo el libro leído | `personajes.json`, `cronologia.json`, lista cerrada |
| 11 | Fichas finales de los lugares (10 o más) + guion del guía (60–90 s por parada) | `lugares/*.json` |
| 12 | Trama del juego: 2–3 propuestas sobre la cronología; el usuario elige una | `juego/tramas.md` |
| 13 | Pistas y acertijos por lugar, cada uno con su fuente; orden del recorrido | `juego/pistas.json` |
| 14 | Verificación final (cada dato contra su página) y ajustes del usuario | entrega |

Días 3–9: unas 150 páginas por sesión. Si hace falta ganar tiempo, los tramos se pueden repartir entre agentes en
paralelo (más rápido y más caro), manteniendo el mismo formato de catálogo.

## Modo de lectura (acordado con el usuario, 2026-11-11)

- **Tandas de 30 páginas** (se unen en un archivo temporal y se leen de una vez; no por terminal, que corta a ~12).
- **Triaje por sección, no por frase:** antes de cada tramo, un script marca en cada página las menciones de lugares
  de Sucre (con los alias). Las secciones sobre Sucre se leen **completas**; las de otra ciudad o de política general
  (Potosí, Lima, guerras lejanas) se leen **por encima** (título, primer párrafo y menciones) y quedan anotadas así.
- **Nada de saltar frases:** no ahorra (la página entra entera al contexto) y pierde remates, fechas y el "en Potosí…".
- **Avance guardado por tanda:** al cerrar cada tanda se anota abajo, para retomar sin repetir si la sesión se corta.

### Avance

| Tramo | Páginas | Lectura | Catálogo | Fecha |
|---|---|---|---|---|
| 1 | Q 2–31 | completa 13–23 y 29–31; por encima 2–12 (preliminares) y 24–28 (guerras fuera) | 30 datos | 2026-11-12 |
| 2 | Q 32–61 | completa 32, 46–47, 53–61; por encima 33–45 y 48–52 (guerras civiles fuera; se leyeron los pasajes de La Plata) | 35 datos | 2026-11-12 |
| 3 | Q 62–91 | completa salvo 77–80 (mita en Potosí, por encima) | 35 datos | 2026-11-12 |
| 4 | Q 92–121 | completa salvo 95–99 (campaña chiriguana, por encima con pasajes de Chuquisaca) | 39 datos | 2026-11-12 |
| 5 | Q 122–154 | completa salvo 139–141 (piratas) y 144–146 (Oruro, yanaconas: por encima); se extendió a 154 para cerrar la sección de los arzobispos | 39 datos | 2026-11-12 |
| 6 | Q 155–184 | completa 155–163 y 169–175; por encima 164–168 y 176–184 (Potosí, visitadores) | 24 datos (`querejazu_02`) | 2026-11-12 |
| 7 | Q 185–214 | completa | 55 datos | 2026-11-12 |
| 8 | Q 215–244 | completa 215–224; por encima 225–244 (Paraguay, Cochabamba, Oruro: solo lo que pasó en Chuquisaca) | 23 datos | 2026-11-12 |
| 9 | Q 245–274 | completa | 34 datos | 2026-11-12 |
| 10 | Q 275–301 | completa (sección de Catari se corta en 301: el día 5 empieza en 302) | 27 datos | 2026-11-12 |
| 11 | Q 302–331 | completa 302–312; por encima 313–331 (Túpac Amaru, Túpac Catari, Cochabamba) | 20 datos (`querejazu_03`) | 2026-11-12 |
| 12 | Q 332–361 | completa 345–361; por encima 332–344 (Oruro) | 27 datos | 2026-11-12 |
| 13 | Q 362–391 | completa 362–370 y 391; por encima 371–390 (Europa e invasiones inglesas) | 17 datos | 2026-11-12 |
| 14 | Q 392–421 | completa | 25 datos | 2026-11-12 |
| 15 | Q 422–439 | completa (se corta antes de los conciliábulos y la noche del 25 de mayo: el día 6 empieza en 440) | 17 datos | 2026-11-12 |
| 16 | Q 440–469 | completa (la noche del 25 de mayo de 1809 entera) | 44 datos (`querejazu_04`) | 2026-11-12 |
| 17 | Q 470–499 | completa salvo 471–475 (La Paz, por encima) | 23 datos | 2026-11-12 |
| 18 | Q 500–529 | completa | 26 datos | 2026-11-12 |
| 19 | Q 530–559 | completa | 29 datos | 2026-11-12 |
| 20 | Q 560–581 | completa: **Querejazu terminado** (fin en 578; 579–581 son portadas de Revilla) | 16 datos | 2026-11-12 |
| 21 | R 582–611 | completa (preliminares: prólogo, prefacio, introducción historiográfica; texto impreso = pág. PDF − 579) | 8 datos (`revilla_01`) | 2026-11-20 |
| 22 | R 612–641 | completa (cap. I: Charcas, la Audiencia, distancias, sociedad, economía, fundación de La Plata) | 17 datos | 2026-11-20 |
| 23 | R 642–671 | completa (Audiencia, Arzobispado, Universidad, Academia Carolina, libros y bibliotecas) | 22 datos | 2026-11-20 |
| 24 | R 672–701 | completa (tomismo y tiranicidio, Villava y la mita, casos de criollos, pasquines) | 18 datos | 2026-11-20 |
| 25 | R 702–731 | completa (proclamas, tertulias, conflictos de autoridades, Goyeneche y Carlota, la noche del 25 de mayo) | 23 datos | 2026-11-20 |
| 26 | R 732–761 | completa (el pueblo y las mujeres del 25 de mayo, Audiencia Gobernadora, La Paz, revolucionarios trashumantes) | 21 datos | 2026-11-20 |
| 27 | R 762–791 | completa: **texto de Revilla terminado** (fin en 773); desde 774, índice de anexos y anexos 1–3 (inventarios de bibliotecas: se leen por encima, solo curiosidades). El día 8 empieza en 792 | 6 datos | 2026-11-20 |
| 28 | R 792–821 | completa (anexos 4–6: Diálogo Alcalá-Malavia, Carta apologética, pasquines de 1780) | 6 datos (`revilla_02`) | 2026-11-20 |
| 29 | R 822–851 | completa (anexos 6–12: décimas, Villava, Carlota, Diálogo Atahuallpa-Fernando, carta del Tribunal, Moxó) | 7 datos | 2026-11-20 |
| 30 | R 852–881 | completa (anexos 12–17: vistas del fiscal, informe de la Audiencia, crónica realista, relación anónima, confesión de Paredes) | 6 datos | 2026-11-20 |
| 31 | R 882–911 | completa (anexos 17–22: Paredes, Arenales, testigos realistas en Potosí, inventario de Nieto, Tardío, prólogo de Moreno) | 9 datos | 2026-11-20 |
| 32 | R 912–955 | completa 912–931 (anexos 22–25, cronología, léxico); por encima 932–955 (lista de documentos y bibliografía): **Revilla terminado** | 2 datos | 2026-11-20 |
| 33 | C 956–985 | **OCR del Cofre rehecho** (fondo de pergamino: se resta el fondo antes de tesseract, `ocr_libro.py --rehacer`). Completa: preliminares 956–964, siete colinas, Munay Pata y la Recoleta | 20 datos (`cofre`) | 2026-11-21 |
| 34 | C 986–1015 | completa (Munay Pata: fiestas, leyendas; Ch'arki Pata, quebradas, Santa Teresa) | 14 datos | 2026-11-21 |
| 35 | C 1016–1045 | completa (K'uri Pata, K'uritambo y Juana Azurduy, Cruz Verde, San Sebastián, San Francisco) | 12 datos | 2026-11-21 |
| 36 | C 1046–1075 | completa (K'uri Pata, Sura Pata: plaza Libertad y su obelisco, hospital de Santa Bárbara, agua del Inisterio) | 12 datos | 2026-11-21 |
| 37 | C 1076–1105 | completa (Alalay Pata: tiendas redondas, cruces de barrio, Tablada, Cementerio General, Todos Santos; semblanza de Fidel Torricos, siglo XX) | 5 datos | 2026-11-21 |
| 38 | C 1106–1135 | completa (Huayra Pata: San Roque, barricadas de 1809, entrada de Sucre, doña Beatriz Verasmendi; comienzo de Q'honchu Pata: los Aymoro, la Plaza Mayor en 1639) | 11 datos | 2026-11-21 |
| 39 | C 1136–1165 | completa (Q'honchu Pata: mercado y oficios de 1639, Santo Domingo, Catedral, jesuitas, gallos, patíbulo, q'apachegas, Santa Mónica) | 12 datos | 2026-11-21 |
| 40 | C 1166–1195 | completa (historias de Santa Mónica, coliseo de comedias, el 25 de mayo y el Quitacapas según su causa) | 10 datos | 2026-11-21 |
| 41 | C 1196–1226 | completa (epílogo, plano de Luján 1777, antología poética y musical, glosario, bibliografía): **Cofre terminado. LIBRO COMPLETO LEÍDO** | 3 datos | 2026-11-21 |

## Formato del catálogo (una línea por dato)

```json
{"id": "Q-0123-1", "libro": "querejazu", "pag_pdf": 123, "pag_libro": 120,
 "tipo": "hecho|tradicion|curiosidad|cita", "fecha": "1809-05-25",
 "lugares": ["casa_libertad"], "personajes": ["jaime_zudanez"],
 "resumen": "…", "cita": "texto literal opcional", "interes": 1}
```

`interes`: 1 = contexto, 2 = útil para el guía, 3 = llamativo (gancho para el recorrido o el juego).
