# Guiones de los encuentros

**Fecha:** 2026-11-26 · **Autor:** claude · **Estado:** aprobados por el usuario el 2026-11-26: Mariana, Jaime, Quitacapas, Ocaña, el gato y el perro de San Roque. Revisados y ya puestos en la ciudad, **por aprobar y sin voz** (la carta avanza por tiempo de lectura): Moxó, Domingo de Santo Tomás, el aguatero, Francisco Argandoña, Clotilde Urioste, el niño del caballito y el sirviente mudo. El resto, borrador por revisar con el mismo método (cada dato contra el catálogo y fuentes; todo el contexto explicado, sin dar nada por sabido).
**Cómo funciona el encuentro:** [PLAN.md](PLAN.md). **De dónde sale cada dato:** [guía de personajes](../guiaPersonajes.md)
y `contenido/lugares/*.md`. Nada de lo que dicen estos guiones sale de otro lado: si una frase no tiene fuente en la
guía o en el catálogo, está marcada **(sin fuente)** o no se escribe.

## Cómo leer un guion

Cada línea es **una frase de la carta** y **un audio**. La carta avanza sola al terminar cada audio (un toque
adelanta). Las citas dentro de una frase van entre “ ”.

| Marca | Sección | Notas |
|---|---|---|
| **P** | Presentación | Quién es. |
| **H1…** | Historia | Su historia o la de la que forma parte. |
| **M** | Mecánica | Por qué hace lo que le viste hacer. |
| **E1…** | Edificio | Solo si tiene edificio. Se abre desde el menú ("Cuénteme de este edificio"). |
| **D** | Donación | Solo custodios con fondo activo. **Una** frase; después, el panel de pago (fuera de la carta). |
| **G** | Gracias | Si la donación se confirmó. |
| **R** | Regreso | Saludo corto al volver a hablarle. |
| **V** | Versiones | Pestañas de "¿Quién lo cuenta?" (texto en la guía). |
| *(cronista)* | | La frase la dice el narrador (tutea), no el personaje. |
| `gesto` | | Clip que hace el personaje con esa frase. Sin marca: `hablar`. |

Los personajes hablan de **usted**; el cronista, de **tú**.

**Orden:** primero los que ya tienen modelo y animación (entran en la fase 1-2 del plan), después los custodios que
faltan modelar, el resto de los lotes, la reserva y al final los acompañantes y animales.

---

## A. Ya animados

### 1. Mariana Zudáñez · `mariana_zudanez`
1809, 25 de mayo al anochecer · `hecho` (las frases, `testimonio`) · Palacio de Gobierno (M055) · sin donación · **aprobado 2026-11-26**.

**Lo que ves:** una mujer con el mantón cayéndole del hombro, inquieta, mirando hacia la plaza y llamando con la mano
(`reposo_inquieta`, `mirar_atras`, `llamar_mano`).

- **P** «¡Usted, forastero! Soy Mariana Zudáñez. ¡Acaban de llevarse preso a mi hermano Jaime!» `gritar_brazo_alto`
- **H1** «Le explico. En España, Napoleón tiene prisionero a nuestro rey, Fernando Séptimo. Su hermana, la princesa Carlota, vive en Río de Janeiro con la corte de Portugal y pide que la obedezcamos en lugar del rey.» (Q 415-420)
- **H2** «En la ciudad se dice que el presidente de la Audiencia, don Ramón García Pizarro, y el arzobispo Moxó quieren entregarnos a Portugal. Mi hermano, que es abogado, y los oidores, los jueces de la Audiencia, se oponen.» (Q 441-442)
- **H3** «Por eso, esta noche el presidente mandó arrestar a seis de ellos a la vez. Solo encontraron a Jaime: estaba en casa, tomando chocolate con su amigo Patricio Malavia.» (Q 446-448)
- **H4** «Lo arrancaron de los brazos de nuestra madre y se lo llevaron con espadas y pistolas. Yo salí detrás gritando: “¡Paisanos, defiendan a mi hermano! ¡Lo llevan a la cárcel por leal y buen vasallo!”» (Q 448; C 1188)
- **H5** «Lo encerraron en la cárcel de la Audiencia, al fondo de la casa del presidente, aquí junto a la Catedral. Al decano de la Audiencia le advertí que, si no lo soltaban, la gente los iba a pasar a todos a cuchillo.» `senalar` (Q 448; C 1188)
- *(cronista)* **H6** «No exageraba: en media hora, miles de personas rodeaban la casa del presidente, y las campanas de San Francisco, San Miguel, La Merced y la Catedral tocaban a rebato.» (Q 448; C 1188)
- **M** «¿Que por qué no me quedo quieta? Porque esta noche, el que se queda quieto termina preso. ¡Ayúdeme a juntar gente!» `llamar_mano`
- **R** «¿Sigue aquí? Vaya a la casa del presidente: ahí lo tienen a mi hermano.»
- **Siguiente en la ruta del 25:** Jaime Zudáñez.
- **Fuentes:** Q-0441, Q-0446-1, Q-0448-2, R-0735-1, C-1188-1; edad: nació hacia 1770 ([Correo del Sur 2017](https://correodelsur.com/panorama/20170528/el-rol-de-las-mujeres--en-la-revolucion-de-1809.html)).

### 2. Jaime Zudáñez · `jaime_zudanez`
1809, 26 de mayo por la mañana · `testimonio` · Palacio de Gobierno (M055) · cuenta el edificio · sin donación · **aprobado 2026-11-26**.

**Lo que ves:** un abogado de levita golpeando con los dedos una cajita de madera (`tamborilear_caja`).

- **P** «Buenos días. Jaime Zudáñez, abogado de la Real Audiencia de Charcas y, desde anoche, para mi sorpresa, el héroe de la plaza.»
- **H1** «El presidente García Pizarro me culpaba de todos los alborotos de la ciudad. Dos días antes le escribió al gobernador de Potosí que yo era “el bribón” que lo causaba todo, y le pidió tropa.» (Q 443)
- **H2** «Anoche me encerró en la cárcel de su casa. Afuera, mi hermana Mariana levantó a medio pueblo.» (Q 448)
- **H3** «Pizarro se asustó. A las pocas horas me sacó por la puerta falsa, la de atrás, y me dijo: “Vaya usted y sosiegue a esa gente, que todo se ha acabado”.» (Q 449)
- **H4** «Pero no se acabó: la gente me llevó en hombros y siguió apedreando la casa. Al final derribaron la puerta falsa a cañonazos. A las tres de la madrugada, Pizarro firmó su renuncia. Ahora gobierna la Audiencia, en nombre del rey Fernando.» (Q 449-459)
- **M** «¿Esta caja? Es mantequilla de la cocina del presidente. Esta mañana la gente entró a su casa y encontró sogas colgadas y pozos cavados en el suelo, y yo voy diciendo por las calles que la mantequilla era para engrasar las sogas de las horcas donde nos iba a colgar.» `tamborilear_caja` (Q 460; R 731)
- *(cronista)* **M** «La verdad era más sencilla. Las sogas eran para secar charque, la carne salada; los pozos se habían cavado diez años antes para guardar nieve y enfriar la comida; y la mantequilla era solo mantequilla. Un alguacil de entonces escribió que Chuquisaca era “fácil en su fondo, aunque atolondrada”.» (Q 460; R 731; R 904)
- *(cronista)* **E1** «La casa del presidente de la Audiencia estaba aquí, a media cuadra de la Catedral. Tenía dos patios, una huerta, la cárcel al fondo y una puerta falsa por detrás.» (Q 198; Q 447; Q 543)
- *(cronista)* **E2** «En 1825, Antonio José de Sucre llegó a este palacio a las cinco de la tarde, bajo el arco triunfal más grande de la ciudad.» (Q 577)
- *(cronista)* **E3** «El edificio que ves hoy se levantó en 1892. Es la sede de la Gobernación de Chuquisaca.»
- **R** «Cuidado con lo que le cuenten en la plaza: esta mañana cada uno tiene su versión.»
- **Fuentes:** Q-0443-1, Q-0448-2, Q-0449-2, Q-0457-1, Q-0460-1, R-0731-1, R-0904-1; edificio: `lugares/palacio_gobierno.md` (ninguna fuente dice expresamente que la casa de 1809 sea el palacio actual); 1892: [Correo del Sur 2024](https://correodelsur.com/ecos/20240602/el-museo-subterraneo-del-gran-mariscal.html).

### 3. Francisco Ríos, «el Quitacapas» (y el zambito) · `quitacapas`
1809, 25-28 de mayo · `hecho`; sus jactancias, `testimonio` · sin donación · **aprobado 2026-11-26**.

**Lo que ves:** un mulato de unos veinte años, de capa negra forrada de carmesí, riéndose, mostrando una llave o
tirando monedas (`reir`, `mostrar_llave`, `lanzar_monedas`); a dos pasos, un muchacho con una capa doblada y un sable
(el zambito).

- **P** «¡Eh, amigo! Francisco Ríos, para servirle: barbero y guitarrero y, desde anoche, capitán de los cholos. Pero todos me dicen el Quitacapas.» `reir`
- **H1** «¿Por qué Quitacapas? Porque me hice famoso robando capas españolas de paño negro, forradas de terciopelo rojo. Una se la quité al hijo del gobernador de La Paz.» (R 733; C 1189)
- **H2** «Nací en Río de Janeiro; por eso algunos aquí me llaman el Portugués. Llegué a esta ciudad hace pocos días, huyendo de la justicia de La Paz.» (Q 453; R 904)
- **H3** «Anoche estaba jugando a los dados y tomando chicha en una chichería de la calle de San Francisco. Entraron gritando que la ciudad se había levantado: el presidente había hecho arrestar al abogado Zudáñez, y el pueblo estaba apedreando su casa.» (Q 453; R 733)
- **H4** «Salí. En la esquina de la Rumi Cruz, la cruz de piedra del atrio de la Catedral, rodeamos al capitán Ramón García Pérez, uno de los oficiales del presidente, y le arranqué la espada de la mano.» (Q 453; C 1148)
- **H5** «Después fuimos a la cárcel del Cabildo, al otro lado de la plaza. Le quité la llave al alcalde y solté a todos los presos. ¿Por qué? Porque creí que faltaban hombres para el servicio del Rey.» `mostrar_llave` (Q 455; R 733)
- **H6** «Don Juan Antonio Paredes, un alcalde del Cuzco que andaba por aquí, me nombró capitán de los cholos, es decir, de la gente del pueblo. Y este muchacho, el zambito, me sigue a todas partes cargando mi capa y mis espadas.» (Q 454-455)
- **M** «¿Y estas monedas? El arzobispo Moxó había huido esa noche. Cuando volvió, su gente me pagó tres mil pesos, un peso por cabeza, para que el pueblo lo recibiera con música. No hubo forma de repartirlos en orden, así que los tiré a puñados en la plaza.» `lanzar_monedas` (Q 450; Q 465)
- *(cronista)* **H7** «Lo acusaron de quedarse con la mayor parte. Él se jactaba de haber “mandado la ciudad siete días”.» (Q 465; C 1189)
- *(cronista)* **H8** «La cárcel que vació estaba en las casas del Cabildo, donde hoy está la Alcaldía; sobre el terreno de la antigua cárcel pública se levantó después el Teatro 3 de Febrero.» (Q 198)
- *(cronista)* **H9** «Volvió a caer preso, y en 1811 lo soltaron con la condición de servir como soldado en el ejército de Buenos Aires.» (C 1189)
- **R** «¡Otra vez usted! Agarre bien su capa, que por aquí se pierden.»
- **El zambito** no tiene carta: si le hablas, se esconde detrás de Ríos (`cargar_bulto`) y habla Ríos.
- **Fuentes:** Q-0453-1, Q-0454-1, Q-0455-1, Q-0465-1, R-0733-1, R-0904-1, C-1189-1; el teatro sobre la cárcel pública: [Correo del Sur 2019](https://correodelsur.com/ecos/20190203/el-emblematico-teatro-3-de-febrero.html) (una sola fuente).

### 4. Fray Diego de Ocaña · `diego_de_ocana` · **custodio de la Catedral**
La Plata, fines de 1601 · `hecho` (lo de pintar con ayuda de la Virgen, `testimonio`) · atrio de la Catedral (M055) · **donación: fondo `catedral`** · **aprobado 2026-11-26**.

**Lo que ves:** un fraile de hábito blanco y pardo pintando en un caballete; da un paso atrás y mira el cuadro
(`pintar`, `retroceder_mirar_cuadro`).

- **P** «Fray Diego de Ocaña, monje jerónimo del monasterio de Guadalupe, en Extremadura, España. Perdone las manos manchadas: estoy pintando.» `saludar`
- **H1** «Mi monasterio guarda una imagen muy querida, Nuestra Señora de Guadalupe. En 1599 me mandaron a las Indias con fray Martín de Posada a pedir limosnas para el monasterio y a extender su devoción.» (Q 126)
- **H2** «Fray Martín murió en el camino, en el puerto de Paita, en el Perú. Yo seguí solo, a pie y en mula, por Lima, Chile y el Tucumán, hasta la Villa Imperial de Potosí.» (Q 126)
- **H3** «En Potosí los fieles me pidieron un retrato grande de la Virgen. Yo jamás había pintado, pero lo intenté, y esa primera imagen quedó en el altar mayor del convento de San Francisco.» (Q 127)
- **H4** «Allí me conoció el obispo de esta ciudad, don Alonso Ramírez de Vergara, extremeño y devoto de la Virgen de Guadalupe. Me pidió otra imagen para la capilla que está levantando junto a la Catedral, donde quiere ser enterrado.» (Q 127; G p. 108)
- **H5** «El deán de la Catedral, don Juan de Larreátegui, me da alojamiento, y en su casa estoy pintando esta segunda Virgen.» (Q 127)
- **H6** «Nunca tuve maestro: solo sabía iluminar, es decir, pintar adornos en los libros. La estoy pintando con la ayuda de la misma Virgen.» (Q 127)
- **M** «¿Por qué me alejo del cuadro cada tanto? Para verlo entero, como lo verá la gente desde lejos, en su altar.» `retroceder_mirar_cuadro`
- **H7** «Cuando esté terminada la llevaremos en procesión a su capilla. Se detendrá aquí, en la plaza, en un teatro adornado con árboles, donde se representará una comedia que escribí sobre sus milagros.» (Q 128)
- *(cronista)* **H8** «Así fue. Las mujeres de la ciudad le regalaron joyas por cuarenta mil pesos: se dijo que ninguna quedó sin dar algo. El obispo le dio su cruz pectoral con siete grandes esmeraldas. Murió al año siguiente y lo enterraron en esa capilla.» (Q 127; G p. 110)
- *(cronista)* **H9** «Con el tiempo, el peso de tantas joyas dañó la pintura, y en 1784 gran parte se cubrió con una lámina de plata dorada. Lo que se ve de la pintura de Ocaña son los rostros de la Virgen y del Niño. Es la Virgen de Guadalupe, patrona de Sucre.»
- **E1** «En 1541 ya había aquí una iglesia rústica. En 1552 el Papa creó el obispado de La Plata, y esta iglesia pasó a ser catedral.» (Q 22; Q 53)
- **E2** «En 1559 los canónigos empezaron a construirla con una sola nave, muy larga y con malos cimientos. Las bóvedas se rajaron, y hace poco un temblor abrió la torre y hubo que derribarla.» (C 1144)
- **E3** «Por eso las campanas cuelgan de armazones casi a ras del suelo y apenas se oyen en la ciudad.» (Q 125-126)
- *(cronista)* **E4** «En 1686, el arzobispo Bartolomé González Poveda, que además presidía la Audiencia, se quejó de que la Catedral era tan larga que desde el fondo no se veía ni se oía el altar, y de que no tenía puerta principal ni torre.» (Q 220)
- *(cronista)* **E5** «Le agregó dos naves laterales, llevó el coro al centro, abrió la puerta principal y levantó una torre, con la portada de piedra que da a la plaza. Su sucesor, Diego Morcillo, terminó la torre y fundió las campanas en el mismo atrio.» (Q 220-221; C 1144)
- *(cronista)* **E6** «El reloj de la torre tiene su propia historia. En 1765, el arzobispo Pedro Miguel de Argandoña lo compró en Londres. No era el primero: ya había habido otro en 1615. Viajó en un barco inglés, desarmado en nueve cajones y tres barriles.» (C 1147)
- *(cronista)* **E7** «Hasta Jujuy, en el norte de la actual Argentina, llegó sin problemas. De ahí a La Plata casi no había caminos. Un tal Seterino Diez se comprometió a traerlo, abriendo camino y fabricando carretas, por cinco mil quinientos pesos.» (C 1148)
- *(cronista)* **E8** «Tardó siete años: el reloj llegó en 1772 y se colocó en la torre. Tenía una sola esfera; un fraile franciscano aficionado a la relojería, Donato Pascual, le agregó otras tres.» (C 1148; Q 270)
- **D** «Yo crucé medio mundo pidiendo limosna para un templo. Este también necesita quien lo cuide. Si quiere ayudar, aquí le dicen cómo.»
- **G** «Dios se lo pague. Ya ve: en esta ciudad nadie se queda sin dar algo.»
- **R** «Mire cómo va. Todavía le falta el manto.»
- **Fuentes:** Q-0126-1, Q-0127-1, Q-0127-2, Q-0128-1, Q-0220-1, C-1144-1, C-1147-1, G p. 108-110; Ocaña: «Comencé, pues, en casa del deán a hacer la imagen» ([Correo del Sur 2022](https://correodelsur.com/ecos/20220904/de-como-la-conocimos.html)); Potosí, oct. 1600 ([Correo del Sur 2018](https://correodelsur.com/ecos/20180902/guadalupe-en-potosi.html)); lámina de 1784, una sola fuente ([ABI](https://abi.bo/guadalupe-una-devocion-de-cuatro-siglos-que-nacio-en-la-charcas-colonial-y-aun-se-transforma-en-sucre/)). En conflicto, omitido: llegada (oct. o nov. de 1601) y precio del reloj (568 o 586 libras).

### 5. Benito María de Moxó · `moxo` · **custodio del Palacio Arzobispal**
1807-1809 · `hecho` · frente al Palacio Arzobispal, hoy Museo Eclesiástico (M063) · **donación: fondo `arzobispado`** · revisado 2026-11-26, **por aprobar** (sin voz todavía).

**Lo que ves:** un hombre bajo y miope de sotana morada mirando una piedra con lupa (`examinar_lupa`); a veces
encuentra un papel y lo arruga (`arrugar_papel`).

- **P** «Benito María de Moxó, arzobispo de La Plata. Acérquese, que de lejos no lo veo: soy corto de vista.» `saludar` (Q-0398-1)
- **H1** «Soy catalán, de Cervera. Llegué a esta ciudad el primer día de 1807, con cuarenta y cuatro años. Hablo cinco lenguas y escribo versos.» (G p. 308-318)
- **H2** «Pero lo que de verdad me quita el sueño es la naturaleza. En el palacio tengo un museo de los tres reinos: el animal, el vegetal y el mineral. Piedras, conchas, plantas… y también monedas y bustos de los reyes Borbones.» `examinar_lupa` (Q-0399-1)
- **H3** «Esta ciudad, en cambio, no me quiere. Me dejan pasquines, esos papeles sin firma que se burlan de uno, hasta dentro de las servilletas. Poco le falta para que vivamos en una perfecta anarquía.» `arrugar_papel` (R-0722-1)
- **M** «¿La lupa? Un naturalista mira de cerca. ¿El papel? Otro pasquín. Ya ni los leo enteros.» `arrugar_papel`
- *(cronista)* **H4** «La noche del 25 de mayo de 1809, la multitud que liberó a Jaime Zudáñez también vino por él, porque era el gran aliado del presidente Pizarro.» (Q-0450-1)
- *(cronista)* **H5** «Desde un balcón prometió dejar la mitra, es decir, renunciar a ser arzobispo, si la gente se iba. Esperó en la loma hasta las tres de la mañana y huyó a pie con dos clérigos.» (G p. 308-318)
- *(cronista)* **H6** «En el camino comió una fruta morada, le cayó mal y creyó que vomitaba sangre. Un clérigo robusto lo cargó en la espalda para cruzar el río. Murió en Salta en 1816.» (G p. 308-318)
- **E1** «Este palacio está pegado a la Catedral. Lo empezó el obispo Ramírez de Vergara, que murió en 1602 dejando cavados los cimientos, la piedra labrada y los cedros cortados.» (Q 129)
- **E2** «Hacia 1618, los canónigos se quejaban de tener que acompañar al arzobispo hasta la Catedral, “aunque la distancia no sea ni de mil pasos”. Ya ve que la pereza es antigua.» (Q 148)
- *(cronista)* **E3** «Su museo se mandó a España, para reponer el gabinete de historia natural del rey Fernando Séptimo, que habían destruido los franceses. Su biblioteca se remató en subasta. Hoy aquí está el Museo Eclesiástico.» (Q-0550-1)
- **D** «Un museo se cuida o se pierde: el mío terminó en subasta. Si quiere que este siga abierto, puede ayudar.»
- **G** «Muy agradecido. Le reservo una concha de las buenas.»
- **R** «¿Me trae otro pasquín? No, gracias.»
- **Fuentes:** Q-0398-1, Q-0399-1, Q-0450-1, Q-0550-1, R-0713-1, R-0722-1, G p. 308-318; `lugares/arzobispado.md`.

### 6. El sirviente mudo de los Lemoine · `sirviente_mudo` · **narrador**
1809, mayo · `tradicion` (memoria de la familia, 1910) · caminando pegado a la pared · sin donación · revisado 2026-11-26, **por aprobar**.

**Lo que ves:** un hombre de sombrero caminando despacio, pegado a la pared, mirando atrás (`mirar_atras`). Se le ve
asomar un papel del forro (`mostrar_forro`).

- *(cronista)* **P** «Vaya, te encontraste con el sirviente mudo de los Lemoine. No te dirá una palabra: no puede.»
- *(cronista)* **H1** «Justamente por eso lo eligió su ama, María Teresa Bustos de Lemoine. En los meses antes del 25 de mayo de 1809, los vecinos que preparaban el levantamiento se escribían en secreto, y él llevaba esas cartas cosidas en el forro de la ropa.» (R-0736-1)
- *(cronista)* **H2** «Las cartas no decían nombres de ciudades, sino palabras en clave: “Parra” era La Plata, esta ciudad, y “Viña” era Buenos Aires. Si alguien las leía, parecían hablar de vinos.» (R-0736-1)
- *(cronista)* **M** «Por eso camina pegado a la pared y se asusta si alguien se le acerca: si lo registran y encuentran las cartas, caen todos.»
- *(cronista)* **H3** «Cuando el gobernador Nieto descubrió una de esas cartas, desterró a María Teresa con sus seis hijos, a pie. Volvió a la ciudad en 1816, vestida de militar.» (R-0736-1)
- *(cronista)* **H4** «Todo esto lo cuenta una biografía que escribió la propia familia en 1910. Es memoria de familia: no hay otro papel que lo confirme.» (R-0736-1)
- **R** *(cronista)* «Otra vez él. Ni te miró.»
- **Fuentes:** R-0736-1. Base de la **misión del mensajero** (guía §7.3).

### 7. El aguatero de la pila · `aguatero` (+ el alcalde de aguas, sin carta)
1639 · `hecho` · en la plaza, del lado del Cabildo (P01/M037) · cuenta la plaza · sin donación · revisado 2026-11-26, **por aprobar**.

**Lo que ves:** un joven descalzo llenando botijas, unos cántaros de barro, y echándose el yugo al hombro
(`llenar_botija`, `cargar_yugo`).

- **P** «Buen día. Soy aguatero: llevo agua a las casas que no la tienen.» `saludar`
- **H1** «En esta ciudad el agua baja por cañerías y se reparte en sesenta pajas. Una paja es un chorrito del grosor de una paja de trigo: la tienen las casas principales y las fuentes públicas.» (Q-0204-1)
- **H2** «Cuando las fuentes se secan, mi amo, que tiene paja propia, me manda a vender la suya por las calles: un real por dos botijas.» `llenar_botija` (Q-0204-1)
- **M** «¿Por qué cargo esto todo el día? Porque soy esclavo, y en tiempo de sequía el agua vale plata. Para mi amo, yo soy un negocio que camina.» `cargar_yugo` (Q-0204-1)
- *(cronista)* **H3** «Había un alcalde de aguas, un vecino nombrado por el Cabildo, el gobierno de la ciudad, que vigilaba que nadie robara agua desviando las cañerías hacia su casa.» (Q-0204-1)
- *(cronista)* **E1** «En 1639, esta era la segunda fuente de la plaza: la primera, “costosa y artificiosa”, ya la habían quitado. Y no estaba en el centro, sino aquí, cerca del Cabildo.» (Q-0204-1)
- *(cronista)* **E2** «Siglos después, la plaza tuvo en el centro otra pila de piedra, a la que llamaron La Peregrina porque la cambiaron de lugar varias veces. Se retiró en 1925 y hoy está en la Recoleta.» (C-0970-1)
- **R** «¿Agua? Un real por dos botijas.»
- **Fuentes:** Q-0204-1, C-0970-1.

### 8. El niño del caballito de palo · `nino_hornacinas` · **narrador**
Leyenda colonial · `leyenda` (con versiones) · junto a San Francisco (M013) · revisado 2026-11-26, **por aprobar**.

**Lo que ves:** un niño flaco de pelo rojo galopando en un caballito de palo (`galopar_palo`), que se esconde y se
asoma (`ocultarse`, `asomarse`).

- *(cronista)* **P** «Vaya, te encontraste con el niño del caballito. Si es que era un niño.»
- *(cronista)* **H1** «Cuentan que una tarde apareció un niño desconocido, de pelo rojo, y se juntó a los trece nietos del sacristán de San Francisco, que jugaban a caballo en palos de madera.» (C-1039-1)
- *(cronista)* **H2** «Los niños notaron algo raro: su caballito corría solo, más rápido que todos, y él nunca se cansaba.» (C-1039-1)
- *(cronista)* **H3** «Cuando fray Jacobo salió con el pan para los mendigos y lo bendijo, el niño desapareció de golpe. En el suelo quedó una huella como de garra de halcón, y olor a azufre, el olor que la gente asociaba con el diablo.» (C-1039-1)
- *(cronista)* **M** «Por eso se esconde cuando te acercas. Y por eso, dicen, en este muro falta una cruz: se la llevó él.»
- *(cronista)* **H4** «¿Y las catorce hornacinas del muro, esos nichos en la pared? El párroco dice que son las estaciones del Vía Crucis; el escritor Tristán Marof, que recuerdan a trece frailes colgados; y la leyenda, lo que acabas de oír. Tú eliges.» (C-1039-1)
- **R** *(cronista)* «Ahí está otra vez. Mejor no lo sigas.»
- **Fuentes:** C-1039-1.

### 9. Fray Domingo de Santo Tomás · `domingo_de_santo_tomas` · **custodio de Santo Domingo**
1563-1570 · `hecho` · junto a la Catedral, de camino a Santo Domingo (a una cuadra, calle Bolívar, fuera de la zona) · donación: **a decidir** · revisado 2026-11-26, **por aprobar**.

**Lo que ves:** un anciano de hábito blanco y capa negra leyendo un libro (`leer_libro`).

- **P** «Fray Domingo de Santo Tomás, de la orden de predicadores, los dominicos. Fui el primer obispo que llegó en persona a esta ciudad, en 1563.» `saludar` (Q-0054-1)
- **H1** «Antes de ser obispo pasé muchos años en el Perú, aprendiendo la lengua de esta tierra, el quechua. Sin la lengua no hay entendimiento: no se puede enseñar, ni escuchar, ni defender a nadie.» (G p. 81-89)
- **H2** «La escribí en un libro, la primera gramática del quechua, que se imprimió en Valladolid en 1560, para que otros la aprendan.» `leer_libro` (G p. 81-89)
- **H3** «Y le escribí al rey: echar a los indios a las minas por la fuerza es condición de esclavos, y no ley de hombres libres.» (G p. 81-89)
- **M** «¿Por qué siempre leo? Porque una lengua se olvida si no se repasa. Y porque cada palabra que aprendo es una persona más a la que puedo entender.» `leer_libro`
- *(cronista)* **H4** «Cuando llegó, encontró la Catedral de una sola nave y sin torre, mucho más pequeña que la que ves. Vivió en el convento de su orden, a una cuadra de aquí, y murió en La Plata en 1570.» (Q-0054-1)
- *(cronista)* **E1** «Los dominicos empezaron su convento hacia 1545, en el solar que les dio Pizarro. Sesenta años después, en 1604, se le informó al rey que la casa “se está cayendo”.» (C 1137, Q 136-137)
- *(cronista)* **E2** «Hacia 1690, Pascual Serrano, a quien los papeles llaman “arquitecto indio”, abrió los arcos de la capilla de la Soledad, y artistas indígenas tallaron y doraron sus retablos.» (C 1138)
- *(cronista)* **E3** «Con la república, el convento fue Casa de Justicia, después Archivo Nacional, y hoy es el Colegio Junín.» (C 1139-1140)
- **R** «Allillanchu? Así se pregunta en quechua si uno está bien. ¿Se acuerda?»
- **Pendiente:** confirmar la forma escrita del saludo en quechua (guía #25).
- **Fuentes:** Q-0054-1, G p. 81-89; `lugares/santo_domingo.md`.

### 10. Francisco Argandoña · `francisco_argandona` (+ Clotilde Urioste, con su propia carta)
1907 · `hecho` (la prensa) · época `republica` · en la plaza, mirando pasar los automóviles · donación: **a decidir** · revisado 2026-11-26, **por aprobar**.

**Lo que ves:** un caballero elegante de principios del siglo XX que se inclina como anfitrión y señala la calle,
orgulloso (`reverencia_anfitrion`, `presentar_automovil`).

- **P** «Francisco Argandoña, para servirle. En Sucre nos llaman a mi esposa y a mí los príncipes de La Glorieta.» `reverencia_anfitrion`
- **H1** «Nací en Potosí en 1850. Hice fortuna con la plata y con un banco que lleva mi nombre: una ley de 1892 me autorizó a abrirlo, y hasta imprimió sus propios billetes.» (Wikipedia, «Francisco Argandoña»; ley de 22-X-1892)
- **H2** «¿Príncipes? No es un apodo. El papa León Trece nos dio el título en 1898, después de que sirviera a Bolivia como enviado ante la Santa Sede, la corte del papa, en Roma.» (Wikipedia, «Clotilde Urioste de Argandoña»)
- **H3** «Fuera de la ciudad, camino a Yotala, construimos nuestra casa de campo: La Glorieta, con jardines, torres y salones de baile. Mi esposa le dirá que lo mejor que hicimos fueron los orfanatos.» (`personas/principes_glorieta/LEEME.md`)
- **M** «¿Por qué miro la calle? El 6 de agosto de 1907 llegaron los automóviles que hice traer, y andan por estas calles angostas. Lo publicó el diario La Mañana. ¡La ciudad entera sale a verlos!» `presentar_automovil` (*La Mañana*, 8-VIII-1907, según Ossio)
- *(cronista)* **H4** «Francisco murió en 1910. Con él se terminó el principado: el título no pasaba a nadie más. Clotilde vivió hasta 1933.» (Wikipedia)
- **R** «¿Volvió a ver los automóviles? Yo tampoco me canso.»
- **Pendiente:** el número y la marca de los coches no están documentados: el guion no los dice. Fuentes de internet: pasarlas al catálogo antes de grabar la voz.
- **Fuentes:** `personas/principes_glorieta/LEEME.md`; [Wikipedia: Francisco Argandoña](https://en.wikipedia.org/wiki/Francisco_Argando%C3%B1a); [Wikipedia: Clotilde Urioste de Argandoña](https://en.wikipedia.org/wiki/Clotilde_Urioste_de_Argando%C3%B1a); [ley de 22-X-1892](https://www.lexivox.org/norms/BO-L-18921022-2.xhtml).

### 10b. Clotilde Urioste de Argandoña · `clotilde_urioste`
1907 · `hecho` / `testimonio` · época `republica` · junto a su esposo, en la plaza · revisado 2026-11-26, **por aprobar**.

**Lo que ves:** una señora de cuello alto y sombrilla cerrada que saluda a los que pasan (`saludar`, `paseo_beneficencia`).

- **P** «Clotilde Urioste de Argandoña. Mi esposo le habrá hablado de automóviles; yo prefiero hablarle de niños.» `saludar`
- **H1** «Nos casamos en 1874. Dios no nos dio hijos, pero nos dio con qué ayudar a muchos.» (Wikipedia, «Clotilde Urioste de Argandoña»)
- **H2** «Fundamos dos orfanatos, casas para niños sin padres: uno lleva el nombre de San Francisco y el otro, Santa Clotilde.» (Wikipedia, «Francisco Argandoña»)
- **H3** «Uno de los automóviles que llegaron en 1907 lo encargó mi esposo para mí. La gente hacía fila para verlo pasar.» `paseo_beneficencia` (recuerdo del P. Bernardo Gantier, en Veizaga Moscoso, ABNB 2017, p. 71)
- **M** «¿Por qué saludo a todos? Porque en esta ciudad nadie es un extraño. Y porque de cada saludo puede salir una ayuda para mis huérfanos.» `saludar`
- *(cronista)* **H4** «Al morir Francisco, en 1910, ella siguió con las obras de caridad durante más de veinte años. Murió en 1933.» (Wikipedia)
- **R** «Qué gusto verlo otra vez. ¿Ya pasó por La Glorieta?»
- **Fuentes:** [Wikipedia: Clotilde Urioste de Argandoña](https://en.wikipedia.org/wiki/Clotilde_Urioste_de_Argando%C3%B1a); [Wikipedia: Francisco Argandoña](https://en.wikipedia.org/wiki/Francisco_Argando%C3%B1a); [Veizaga Moscoso, ABNB, p. 71](https://archivoybibliotecanacionales.org.bo/images/Contenido/Publicaciones/Anuarios/2017-1.pdf).

---

## B. Custodios que faltan modelar

### 11. Luis de Santillán, rector fundador de la Universidad · `luis_de_santillan` · **custodio de la Casa de la Libertad**
1623-1624 · `hecho` · A · portada de la Casa de la Libertad (M037) · **donación: fondo `casa_libertad`**.
**Nuevo en la guía** (tiene diseño en `personas/luis_de_santillan/`, falta su ficha en `guiaPersonajes.md`).

**Lo que ves (mecánica propuesta):** un jesuita de sotana negra con un pliego sellado bajo el brazo, que señala la
portada y lo despliega (`desenrollar_titulo`, compartido con Túpac Amaru).

- **P** «Luis de Santillán, de la Compañía de Jesús, rector del Colegio de San Juan Bautista.»
- **H1** «El 23 de marzo de 1623 el Cabildo se reunió a campana tañida y le pedí ayuda para una universidad. Nos dio 800 pesos al año por doce años.»
- **H2** «Todavía no teníamos aulas: el padre Reyman enseñaba Artes dentro de la iglesia.»
- **H3** «El 15 de abril de 1624 tomamos posesión. La primera lección fue un discurso en latín sobre Virgilio; al terminar, chirimías y trompetas.»
- **M** «¿Este pliego? La patente de fundación. Seis cátedras y el nombre de su patrón: San Francisco Xavier.»
- **E1** *(cronista)* «En 1767 expulsaron a los jesuitas: salieron catorce padres y seis hermanos. La Audiencia cerró una semana para inventariar sus bienes.» (Q 279)
- **E2** *(cronista)* «En 1809 el claustro discutió aquí los "pliegos del Brasil"; el presidente arrancó del libro el acta con sus propias manos.» (Q 428)
- **E3** *(cronista)* «En 1825 se reunió en esta casa la Asamblea: "aquí se fundó la República de Bolivia, se bautizó a la patria, se le dio bandera y escudo".» (C 1155)
- **D** «Esta casa se fundó con la ayuda de la ciudad: 800 pesos al año. Hoy también vive de quienes la cuidan. Si quiere ayudar, aquí le dicen cómo.»
- **G** «Que Virgilio y San Francisco Xavier se lo paguen.»
- **R** «¿Viene a inscribirse? Hay seis días de plazo.»
- **Fuentes:** Q-0159-2, Q-0161-1, Q-0162-1, Q-0163-1, Q-0163-2; `lugares/casa_libertad.md`.

### 12. Fray Francisco de Aroca y los niños de la enramada · `francisco_de_aroca` · **custodio de San Francisco**
1539 · `hecho` · A · plazoleta de San Francisco (M013) · **donación: fondo `san_francisco`**.

**Lo que ves:** un franciscano hablando a cuatro o cinco niños sentados bajo un techo de ramas. Al acercarte, los
niños se dan vuelta a mirarte y uno saluda.

- **P** «Fray Francisco de Aroca, franciscano. Llegué en 1539, al año de fundarse la villa.» `invitar`
- **H1** «Aquí no hay iglesia todavía: solo esta enramada. Junto a los niños pobres y les enseño la doctrina para el bautismo.»
- **H2** «El general Pedro de Hinojosa me dio este solar. Algún día habrá aquí un templo con dos torres.»
- **M** «¿Por qué bajo unas ramas? Porque es lo que hay. Para enseñar alcanza con sombra y ganas.»
- **E1** *(cronista)* «El primer templo fue muy modesto: ahí enterraban a los conquistadores. Hacia 1580 se levantó la iglesia que sigue en pie.» (Q 137; la guía dice 1581: C-1035-1)
- **E2** *(cronista)* «En 1620 el claustro alto se vino abajo: el agua había comido las columnas de ladrillo. Un fraile halló una cantera de piedra blanca y con ella se rehicieron.» (Q 138)
- **E3** *(cronista)* «La noche del 25 de mayo de 1809, Juan Manuel Lemoine subió a este campanario sable en mano para tocar a rebato.» (Q 451)
- **D** «Empecé con cuatro palos y unas ramas. Lo que hoy ve sigue en pie porque siempre hubo quien lo cuidara. ¿Me ayuda?»
- **G** «Los niños le dan las gracias. ¡Digan gracias!»
- **R** «Siéntese, si quiere: hay lugar en el suelo.»
- **Fuentes:** C-1035-1, G p. 31; `lugares/san_francisco.md`.

### 13. Gaspar de Villarroel · `gaspar_de_villarroel` · **custodio de Santa Teresa**
1660-1665 · `hecho` (el terremoto, `testimonio` suyo) · A + escena · frente a Santa Teresa (**zona por modelar**) · **donación: fondo `santa_teresa`**.

**Lo que ves:** un anciano agustino, apoyado en el bastón, mirando una obra (`mirar_obra`).

- **P** «Gaspar de Villarroel, arzobispo. Nací en Quito, en una casa pobre, sin que mi madre tuviera un pañal en que envolverme.»
- **H1** «Siendo obispo de Santiago de Chile vino un terremoto. Quedé enterrado bajo los adobes gritando "¡Javier, Javier! ¿Dónde está nuestra amistad?", hasta que mi paje me sacó.»
- **H2** «Ahora levanto este convento para las carmelitas. Cuando vi la bóveda terminada lloré: sé que cuando acabe la obra me iré yo.»
- **M** «¿Por qué miro tanto esta obra? Porque es lo último que haré.»
- **H3** *(escena de 1663, opcional)* «Junté en la ciudad 25.000 pesos para salvar la vida de Magdalena Téllez. Los oidores empataron… y la ejecutaron igual.» *(no se muestra la ejecución)*
- **E1** *(cronista)* «Tres señoras pusieron 50.000 pesos para fundarlo y él, 160.000. Fue el tercer convento de monjas de la ciudad.» (Q 208)
- **E2** *(cronista)* «Murió en octubre de 1665, la noche en que llegaron las monjas fundadoras de Lima. Está enterrado al pie del altar mayor.» (Q 208)
- **E3** *(cronista)* «Aquí también se enterraron los ojos, la lengua y el corazón del arzobispo Molleda.» (Q-0265-1, G p. 269)
- **D** «Di casi todo lo que tenía para que estas paredes se levantaran. Si quiere ayudar a que sigan en pie, aquí le dicen cómo.»
- **G** «Dios le pague. Yo ya no lo veré terminado; usted sí.»
- **R** «Todavía falta. Siempre falta.»
- **Fuentes:** Q-0207-1, Q-0208-1, Q-0208-2, Q-0210-1, C-1004-2, C-1156-1, G p. 184-195; `lugares/santa_teresa.md`.

### 14. Fray José Antonio de San Alberto · `san_alberto` (+ niñas huérfanas, sin carta) · **custodio de San Felipe Neri**
1785-1804 · `hecho` (su opinión de los criollos, `testimonio`) · B · **San Felipe Neri por ubicar** · **donación: fondo `san_felipe_neri`**.

**Lo que ves:** un anciano carmelita de capa blanca caminando despacio con una bolsa de monedas; se detiene a dar
limosna (`dar_limosna`); lo siguen dos o tres niñas en fila, que se esconden detrás de él cuando te acercas.

- **P** «Fray José Antonio de San Alberto, arzobispo. Nací en Fresno, en Aragón.»
- **H1** «El día que entré a esta ciudad repartí treinta mil reales entre pobres, enfermos y presos. Vivo con muebles prestados: ¿para qué quiero otros?»
- **H2** «Fundé un colegio para mis niñas huérfanas y la casa de San Felipe Neri.»
- **M** «¿La bolsa? Doce mil pesos al año reparto en esta ciudad. Mi casa parecía un enjambre.»
- **H3** *(cronista)* «También escribió al rey que no convenía nombrar obispos nacidos en América, porque los criollos tenían "ideas, todas siempre de libertad".»
- **H4** *(cronista)* «Cuando quisieron llevárselo a Almería, la ciudad fue a pedirle que se quedara. En 1804 su cortejo se detuvo ante el colegio de sus huérfanas.»
- **E1** *(cronista)* «En 1809 el oidor Ussoz, perseguido por los soldados del presidente, corrió a esconderse en este convento, que quedaba muy cerca.» (Q 448)
- **E2** *(cronista)* «En 1815 el ex presidente Pizarro, ya anciano, se refugió aquí con siete baúles. Murió durante la siesta; los soldados se llevaron hasta las hebillas de sus zapatos.» (Q 548-549)
- **E3** *(cronista)* «En su cripta descansan juntos Pizarro y su amigo el arzobispo Moxó.» (Q 550)
- **D** «Viví de lo prestado y lo di todo. Esta casa también necesita ayuda. Si puede, aquí le dicen cómo.»
- **G** «Las niñas le cantarán algo. Bueno, cuando se animen.»
- **R** «¿Una limosna? No: a usted se la pido yo.»
- **Fuentes:** Q-0362-2, Q-0363-1, Q-0363-2, Q-0364-1, G p. 291-301; `lugares/san_felipe_neri.md`.

---

## C. Lotes 1 y 2 (sin modelo todavía)

### 15. María Antonia del Río · `maria_antonia_del_rio`
1809, noche del 25 · `testimonio` · C (balcón) · calle del Colegio Colorado (por ubicar).

**Lo que ves:** una mujer con un libro, asomada a un balcón con un candil; cuando pasas, te llama con la mano
(`llamar_mano`) y un globo: "¿Qué partido vence?".

- **P** «¡Usted, el de abajo! ¿Qué partido vence? ¡Vaya y ayude!» `inclinarse_baranda`
- **H1** «Soy María Antonia del Río. Mi marido es oidor de la Audiencia, José Agustín de Ussoz, y no está con el presidente. Yo tampoco.»
- **H2** «¿Qué pensaban, que íbamos a estar descuidados? Doscientos hombres de Yamparáes teníamos prontos, y ciento de Guata.»
- **M** «¿Por qué me asomo? Porque desde aquí veo pasar a todos y a todos les pregunto. Y el libro… tengo biblioteca propia, cosa rara para una mujer en esta ciudad.»
- **H3** *(cronista)* «Un comerciante encontró a un muchacho con espada en su puerta y lo llevó a casa de su padre: era Monteagudo.»
- **H4** *(cronista)* «En 1810 la familia fue desterrada. Algunos libros se salvaron del embargo porque eran de ella. Vagó cinco años por los Andes y murió hacia 1815.»
- **R** «¿Y? ¿Quién vence?»
- **Fuentes:** R-0735-1, R-0895-1, R-0668-1, Q-0451-2.

### 16. Marta Zárate, la frutera de los portales · `marta_zarate`
1808 · `hecho` · A · frente a los portales del Cabildo.

**Lo que ves:** una chola sentada tras sus canastas de fruta, contando ajíes (`contar_ajies`); al acercarte mira de
reojo las rejas del Cabildo y junta las manos (`suplicar`).

- **P** «Marta Zárate, frutera de esta plaza. ¿Fruta? ¿Ajíes?»
- **H1** «Me nombraron mayordoma del Corpus, ¡a mí, que vendo fruta! Y las otras me dijeron que si no daba el banquete me iban a echar el ají más picante.»
- **H2** «Le pedí al alcalde que me encerrara en el Cabildo: allí adentro estaba más segura.»
- **M** «¿Por qué cuento los ajíes? Por lo que le pasó a Bernarda Rodríguez. ¿Quiere que se lo cuente?»
- **H3** «Hace casi cien años la arrastraron de los cabellos hasta estos portales y la azotaron por orden del alcalde Ulloa, porque su criadita trajo 25 ajíes en vez de 35.»
- **H4** «Se probó que Bernarda había dado los 35: la niña cambió diez por una golosina. Por eso yo cuento dos veces.»
- **H5** «Y en 1786 una vendedora rica, la Abadesa, ponía los precios a todas. Tuvieron que abrir tres mercados nuevos para frenarla.»
- **R** «¿Cuántos ajíes por medio real?» → minijuego de monedas (guía #5).
- **Fuentes:** Q-0369-1, Q-0225-2, C-1159-1, Q-0359-1.

### 17. El cochero del arzobispo Molleda · `coche_molleda`
1755 · `hecho`, con versiones · D · vuelta a la plaza con parada frente al Arzobispado.

**Lo que ves:** un coche cerrado azul dando la vuelta despacio a la plaza. Al parar, una mano enguantada corre la
cortinilla unos centímetros.
**Al presionar I:** el cochero se vuelve y se lleva el dedo a los labios (`silencio_sentado`); habla en voz baja.

- **P** «Shh. Soy el cochero del señor arzobispo, don Gregorio de Molleda. Va adentro.»
- **H1** «Damos vueltas para que la gente lo vea pasar y crea que está bien. Tiene unos ataques… cada mes, con la luna. Después vuelve a estar lúcido.»
- **H2** «La Audiencia mandó a dos ministros con médicos, de noche. El vicario no los dejó pasar del segundo patio: dijo que sería como si entraran con cuchillos.»
- **M** «¿Por qué no paro nunca? Porque si el coche se queda quieto, alguien se asoma.»
- **H3** *(cronista)* «En noviembre de 1755 salió hacia Cochabamba en una litera de cuero. Murió allá en abril de 1756. Sus ojos, su lengua y su corazón se enterraron en Santa Teresa.»
- **V** Querejazu · García Quintanilla (guía #6).
- **R** «Shh. Otra vuelta.»
- **Fuentes:** Q-0257-2, Q-0263-1, Q-0264-1, Q-0265-1, G p. 264-269.

### 18. El centinela de la tienda reventada · `centinela_tienda`
1809, madrugada del 26 · `hecho` · A · una puerta de mercader frente a la plaza.

**Lo que ves:** un hombre de poncho con un garrote, firme frente a una puerta astillada con rollos de seda detrás. Si
llegas corriendo, levanta la mano (`alto`).

- **P** «¡Alto ahí! El cañonazo voló esta puerta, pero de aquí no sale nada.»
- **H1** «Bajamos quinientos con garrotes esta noche. Unos cuantos nos quedamos de guardia en esta tienda, toda la noche.»
- **H2** «Y no fuimos los únicos con cabeza fría: el oficial Manuel Yáñez no dejó salir a sus soldados del cuartel frente a la Rumi Cruz.»
- **M** «¿Por qué el garrote? Para que nadie diga mañana que el pueblo vino a robar.»
- **H3** *(al amanecer)* «Ya ve: no falta ni una hebra de seda.»
- **R** «Todo en orden.»
- **Fuentes:** C-1188-1.

### 19. Juan de Araujo, el maestro de capilla · `juan_de_araujo`
1680-1712 (escena en 1696) · `hecho` · A · gradas de la Catedral · cuenta la música de la Catedral · **sin donación** (el custodio es Ocaña).

**Lo que ves:** un clérigo de manteo y bonete marcando el compás en el aire (`dirigir`). Al acercarte se interrumpe y
frunce el ceño (`gruñir`).

- **P** «¿Usted también viene a molestar? Juan de Araujo, maestro de capilla de esta Catedral.»
- **H1** «En la fiesta de San Roque mis músicos no tenían dónde sentarse y lo dije bien alto… Terminé unas horas en la cárcel.»
- **H2** «El Cabildo me sacó: dijeron que dieciocho años de buena conducta valían algo.»
- **M** «¿Por qué dirijo al aire? Porque la música no espera a que haya silla.»
- **E1** «Esta Catedral tiene un chantre porque, dice el documento de su fundación, los indios de nada se dejan llevar como de la música.»
- **E2** *(cronista)* «Cuando murió, los niños del coro debían cantar sus obras como prueba para entrar. Hoy sus partituras se guardan en el Archivo Nacional de Bolivia.»
- **R** «¿Otra vez? Silencio, que ensayamos.»
- **Fuentes:** C-1144-1, G p. 56-57.

### 20. Bernardo Monteagudo · `monteagudo` (día y noche)
1809 / 1810 · `hecho` · A + E · Universidad (día) · tapia de la cárcel de la Audiencia (noche).

**Día. Lo que ves:** un estudiante con un sable al hombro y dos pistolas al cinto, señalando la Universidad.
- **P** «Bernardo Monteagudo, estudiante. Tengo diecinueve años y esta noche nadie me va a encerrar en casa.»
- **H1** «A los compañeros los cito en la tienda de aguardiente de mi padre: allí se habla de lo que no se puede hablar en las aulas.»
- **M** «¿El sable? Esta noche hace falta.»

**Noche (1810). Lo que ves:** agachado junto a una tapia, probando una llave (`probar_llave`, `mirar_lados`).
- **P** «Shh. Estoy preso en la cárcel de la Audiencia.»
- **H1** «Convencí al hortelano de que me prestara la llave de la huerta "para invitar a merendar a unas madamas". Se fue a comer un picante y a tomar chicha.»
- **H2** «Esta noche saltamos la tapia con el capitán Bartolomé Pizarro.»
- **M** *(al cerrar la carta, salta la tapia y desaparece: `trepar`)*
- *(cronista)* «Su origen, Chuquisaca o Tucumán, todavía se discute.»
- **Fuentes:** R-0729-1, R-0705-1, Q-0451-2, Q-0508-1, R-0895-1.

### 21. Vicente Túpac Amaru · `vicente_tupac_amaru`
1786 · `hecho` · A · portada de la Universidad (M037) · **sin donación** (el custodio es Santillán).

**Lo que ves:** un joven de garnacha negra y golilla desenrollando un título con sello, mirando la portada y a ti.

- **P** «Vicente Túpac Amaru. Hoy me recibo de abogado ante la Real Audiencia.» `desenrollar_titulo`
- **H1** «Mi padre, Blas, tallaba santos. Fue hasta Madrid a pedirle al rey una beca para mí… y la consiguió.»
- **H2** «Estudié en el Seminario, en esta Universidad y en la Academia Carolina.»
- **M** «¿Por qué no suelto este papel? Porque soy el primero de mi sangre en tenerlo.»
- **H3** *(cronista)* «Fue en 1786, cinco años después de las rebeliones de Túpac Amaru y Túpac Katari. Llevar ese apellido en la Audiencia no era poca cosa.» *(contexto general; ver guía #13)*
- **Fuentes:** Q-0321-1.

### 22. El oidor de golilla · `oidor_golilla`
Siglo XVIII · `hecho` · B · vereda de la Audiencia (M055).

**Lo que ves:** un hombre corpulento de golilla y bastón de plata caminando por el centro de la vereda. Si le cortas el
paso, se detiene y golpea el suelo dos veces señalando la calzada (`baston_ofendido`). Si bajas a la calzada, pasa
sin mirarte (estampa "El saludo al oidor"); si presionas I, habla.

- **P** «¿No sabe usted que a un oidor se lo saluda bajando de la acera?»
- **H1** «En La Plata manda la Audiencia, joven. El presidente manda poco.»
- **M** «¿Por qué camino por el medio? Porque la vereda es mía. Bueno: del rey, que es lo mismo.»
- **H2** «Y no me hable del oidor Ussoz, que en 1807 metió su caballo en el cementerio de la Catedral y usó una lápida de peldaño. El arzobispo lo tomó como un ultraje.»
- *(cronista)* «Mariano Moreno escribió que era menos peligroso desagradar al rey que a uno de estos oidores.»
- **Fuentes:** R-0642-1, Q-0404-1.

### 23. Malavia, Alcalá y el bedel Mostajo · `dialogo_1807`
1807 · `satira` · B "Sígueme" · poyos de la Jacoba (plaza) → salida al Prado.

**Lo que ves:** dos hombres hablando en voz baja; uno se toca el escapulario.
**Al presionar I:** el que habla es Malavia (un solo interlocutor, como pidió el usuario); Alcalá asiente.

- **P** «Patricio Malavia, procurador. Este es el viejo platero Alcalá.» `tocar_escapulario`
- **H1** «Aquí no: en la plaza todo se oye. Vamos al Prado. Llevo una copia de la arenga del rector dentro de mi escapulario.»
- *(en la salida al Prado)* **H2** «He mirado por todas partes y no suena ni una mosca. Podemos hablar con libertad.»
- **M** «¿Por qué en voz baja? Porque nos burlamos del discurso con que el rector recibió al arzobispo.»
- *(cronista)* «Esta escena salió de un panfleto anónimo de 1807: las personas existieron, la conversación es sátira.»
- **Mostajo (secreto, detrás del árbol):** **P** «¡Lo oí todo, escondido detrás del rosal! ¡Y lo voy a contar!» `espiar` · *(cronista)* «Al año se publicó una réplica que se burlaba del Diálogo: a las dos de la tarde nadie se sienta en esos poyos, que arden al sol.»
- **Fuentes:** R-0792-1, R-0792-2, R-0810-1, R-0658-1.

### 24. El escribano de los portales · `escribano` · cuenta el Cabildo
1631-1639 · `hecho` · A · portales del Cabildo (M037) · **sin donación** (Alcaldía en uso; a decidir).

**Lo que ves:** un hombre de negro con anteojos escribiendo en un atril y alisando un cartel en la pilastra.

- **P** «Escribano, para servirle. Somos cinco bajo estos portales.» `escribir`
- **H1** «En la pilastra pegamos los carteles del coliseo: "La famosísima comedia de La Despreciada Querida, de Lope de Vega… se representa hoy sábado".»
- **H2** «Un peso los pudientes, cuatro reales los pobres, y parte de la taquilla va al hospital.»
- **M** «¿Por qué escribo en la calle? Porque aquí está la gente, y los papeles del Cabildo, al lado.»
- **E1** «En la traza de la villa, en 1540, ya había "un solar, casa del Cabildo".» (Q 21-22)
- **E2** «Hoy es bueno y hermoso: cárcel pública, sala con dosel, capilla de la Virgen de Copacabana y una torrecilla con la campana del toque de queda.» (Q 198, C 1133)
- **E3** *(cronista)* «En 1809 el Quitacapas vació su cárcel; en 1825 el coronel López le entregó el mando de la ciudad libre. Hoy es la Alcaldía.» (Q 455, Q 573, C 1133)
- **Fuentes:** Q-0188-2, Q-0198-2, C-1133-1, C-1183-1; `lugares/cabildo.md`.

### 25. El pasquinero · `pasquinero` · **narrador**
1780-1809 · `hecho` · E (noche) · portales del Cabildo.

**Lo que ves (de noche):** una figura encapuchada pegando un papel con brocha y engrudo (`pegar_pasquin`).
**Al presionar I (o a menos de 6 m):** se vuelve apenas, se tapa la cara y **se va rápido** por la esquina. El papel
queda en la pared. Entra el cronista.

- *(cronista)* **P** «Vaya, casi lo atrapas. Te encontraste con un pasquinero.»
- *(cronista)* **H1** «En una ciudad sin imprenta, la crítica se escribía a mano y se pegaba de noche. La ciudad amanecía empapelada.»
- *(cronista)* **H2** «Lee lo que dejó:» → el pasquín de esa noche: «¿Qué importa que los Oidores tengáis grandes las orejas si no percibís las quejas…?» (o la adivinanza, o «Ya es llegado el tiempo de las venganzas», 1809).
- *(cronista)* **M** «Por eso huye: un pasquín sin firma vale; uno con nombre te lleva a la cárcel.» *(interpretación, sin fuente: marcarlo así o quitarlo)*
- **Fuentes:** R-0695-1, Q-0440-1. Base de los pasquines-acertijo (guía §7.5).

### 26. Gerónima de Villavicencio y Pedro Astete · `geronima` · cuenta Santa Mónica
1731-1732 · `hecho` (versiones, `testimonio`) · D + A · Santa Mónica (M027) · donación: **a decidir**.

**Lo que ves:** una joven con el manto recogido sosteniendo la puerta de una calesa y mirando nerviosa el portón
(`mirar_nerviosa`); el calesero, sentado, calma al caballo.

- **P** *(Gerónima)* «Gerónima de Villavicencio. ¡Hable bajo, que me buscan!»
- **H1** «En la corrida de la Virgen de Guadalupe, mi cuñado, el oidor Sagardía, me hizo una escena de celos delante de toda la plaza. Me refugié en este convento.»
- **H2** «Cuando volví por mis cosas, una monja me metió de un jalón en la clausura. Me escapé empujando a la portera y corrí por la calle de la Compañía.»
- **H3** «En la puerta de la iglesia estaba la calesa del presidente, que oía misa… y le pedí al calesero que me llevara.»
- **M** *(Pedro Astete)* «La llevé. ¿Qué iba a hacer? Me tuvieron quince días preso por eso.»
- *(cronista)* «Su excomunión se clavó en las puertas de la Catedral, la Compañía, San Francisco y Santa Mónica. Para devolverla al convento hizo falta media Audiencia.»
- **E1** *(cronista)* «Santa Mónica fue el primer convento de mujeres de la ciudad, fundado en 1577 en una casa mediana, solo con limosnas.» (Q 92-93)
- **E2** *(cronista)* «En 1585 llevaban cuatro meses sin encender el fogón: comían lo que cultivaban adentro.» (Q 94)
- **E3** *(cronista)* «Aquí el virrey Toledo hizo encerrar a Juanita Zárate, heredera mestiza del gobierno del Río de la Plata, por casarse sin permiso. Estuvo ocho o nueve años.»
- **Ambiente:** en el callejón de atrás, una pelota de cuero rebota en el alero de vez en cuando (Q-0224-2).
- **Fuentes:** Q-0246-1, Q-0248-1, Q-0249-1, Q-0250-1, Q-0253-1, Q-0257-1, Q-0108-1, C-1166-1, C-1168-1; `lugares/santa_monica.md`.

### 27. El campanero del Cabildo y la ronda de abogados · `campanero`, `ronda_abogados`
1639 / fines del s. XVIII · `hecho` · C + E / B + E.

**Campanero (atardecer, en la torrecilla):** **P** «Soy el campanero del Cabildo.» · **H** «A las ocho toco para los negros y los indios: a sus casas. A las nueve, para todos los demás.» · **M** «¿Por qué toco a esta hora? Porque esta campana es el reloj de la noche: después de ella, la calle es de la ronda.»
**Ronda (noche):** el jefe levanta el farol (`levantar_farol`): **P** «¿Quién vive?» · **H** «Somos abogados, pero en 1781 tomamos las armas: el Regimiento de Abogados peleó en Punilla contra Dámaso Catari.» · **M** «Desde entonces hacemos la ronda de noche, con farol y espadín.»
- **Fuentes:** Q-0198-2, C-1133-1, R-0650-1, Q-0353-1.

### 28. El refugiado del atrio · `refugiado_atrio` (+ el alguacil, sin carta)
c. 1620 · `hecho` · A · atrio de San Francisco (M013).

**Lo que ves:** un hombre agachado contra una columna del atrio, sin quitarle los ojos a un alguacil que va y viene
afuera sin cruzar la reja.

- **P** «No me mire tanto, que se da cuenta. Estoy acogido a sagrado.»
- **H1** «Mientras esté dentro del atrio, la justicia del rey no me puede tocar. Eso dice la Iglesia. El alguacil no se anima… por ahora.»
- **M** «¿Por qué no me muevo de esta columna? Porque un paso afuera y me lleva.»
- *(cronista)* «No siempre se respetó: la Audiencia sacó de aquí a Cristóbal de Cuéllar, y de Santa Bárbara a un esclavo que fue ahorcado. El arzobispo protestó.»
- *(cronista)* «En 1731 el criado Isidro Cabezas pidió asilo en este mismo convento y lo echaron a empellones.»
- **Fuentes:** G p. 138-140, Q-0253-2.

### 29. Manuel Antonio Tardío, el alguacil de 1809 · `tardio`
1809 · `testimonio` (realista) · B con cono de visión (misión del mensajero) · Catedral.

**Lo que ves:** un alguacil de levita oscura con una llave grande de hierro, vigilando.

- **P** «Manuel Antonio Tardío, alguacil de la Real Audiencia. ¿Qué hace usted en la calle a esta hora?»
- **H1** «Esta noche cerré con llave la torre de la Catedral para que dejaran de tocar a rebato… y a los pocos minutos volvieron a sonar.» (Q-0451-1)
- **H2** «Zudáñez paseó por las calles una caja de mantequilla "para embarnizar los cordeles de las horcas". Lo vi yo.»
- **M** «¿Por qué miro a todos? Porque alguien lleva cartas de casa en casa, y lo voy a encontrar.»
- *(cronista)* «Tardío era del bando del rey. Las "horcas" de su relato eran un pilastrón viejo donde los criados colgaban tocino.»
- **Fuentes:** Q-0451-1, R-0731-1, R-0904-1.

---

## D. Lote 3 y reserva (cuando se modele su zona)

### 30. Juana Azurduy en el K'uritambo · `juana_azurduy` (+ Indalecio Sandi, sin carta)
1862 · `hecho` · A · calle España (por ubicar). Personaje de respeto: ni chistes ni minijuego.

**Lo que ves:** una anciana pequeña sentada en un zaguán con una cajita de madera en las rodillas; a su lado, un niño.
Al acercarte abre apenas la cajita y la vuelve a cerrar (`abrir_cajita`).

- **P** «Juana Azurduy. Este es Indalecio, mi sobrino.»
- **H1** «En esta cajita guardo mi tesoro: los partes y las órdenes de mi guerra.»
- **H2** «Lo demás… un catre con phullus, una mesa con vajilla de barro y una silla.»
- **M** «¿Por qué la abro y la cierro? Para ver que siguen ahí.»
- *(cronista)* «Murió aquí el 25 de mayo de 1862, cincuenta y tres años justos después de la revolución de 1809.»
- **Fuentes:** C-1023-1.

### 31. Las tiendas redondas · `sastre`, `hojalatero`, `loro`
c. 1900-1950 · `tradicion` · A, época `republica`.

**Lo que ves:** el sastre balanceando una plancha de carbón en la acera (chispas); el hojalatero con farolitos al sol;
el loro en su lorera grita un apodo cuando pasas ("¡Pasta Dormida!", "¡Garibaldi Pum!").
- **Sastre P** «Pase, pase. Le tomo las medidas en un minuto.» · **M** «¿La plancha? La saco a la acera para avivar el carbón.»
- **Hojalatero P** «¿Un farolito? Los saco al sol para que brillen y los vean.»
- *(cronista, desde cualquiera de los dos)* «En las tiendas redondas una familia entera vivía detrás de una cortina, con catres de fierro, santos, gallinas y cuyes, y en el poyo, la negrita de la suerte.»
- **Loro:** no tiene carta: su "diálogo" es el globo con el apodo.
- **Fuentes:** C-1076-1, C-1042-1.

### 32. Reserva (guiones cortos, mismos datos que la guía §6)

| Personaje | P / H / M (resumen del guion) | Fuentes |
|---|---|---|
| **María Teresa Bustos y Juan Manuel Lemoine** (torre de San Francisco) | Él: «Subí sable en mano y toqué a rebato.» Ella: «Vendí mis joyas para comprar pólvora.» M: tocan la campana. | R-0736-1, Q-0451-1 |
| **Madre de los Zudáñez** | Sin carta: acompaña a Mariana unos pasos atrás. | — |
| **Beatriz Verasmendi** (San Roque) | «Voy a ponerme de arco triunfal desde mi balcón…» Realista convertida en devota de Sucre. | C-1118-1 |
| **El estudiante del Inisterio** | «Quien bebe medido se vuelve sabio; quien exagera, enloquece.» Minijuego de beber la medida justa. | C-1059-1 |
| **El político disfrazado de monja** (y la monja de la Casa Capellánica) | **Narrador**: al presionar I, las "monjas" bajan la cabeza y apuran el paso con sus cestos; el cronista: «Vaya: una de esas monjas tiene bigote…» | C-0985-1 |
| **El Encapuchado sin sombra** | **Narrador** (leyenda): crece y se desvanece; el cronista cuenta la leyenda. | C-1013-2 |
| **Juan Antonio Paredes** | Juega a la malilla y reparte coca, cigarros y aguardiente «a veces mezclado con pólvora». | Q-0454-1 |
| **Ramón García Pizarro** | «¡Viva Fernando Séptimo!» Preso 180 días, sale diciendo que perdona a todos. | Q-0407-2, Q-0483-2 |
| **Domingo Aníbarro** (balcón del Cabildo) | Tira 300 pesos a la plebe gritando «¡Viva la paz!». | R-0892-1 |
| **Arzobispo Borja** (1636) | Escena de su entrada: arcos, toro manso con dos disfrazados jugando a los naipes en el lomo, palo encebado. | Q-0150-1 a Q-0153-1, G p. 170 |
| **Castilla y Zamora** | Retrato que habla: «¿Era yo hijo de Felipe IV?» con versiones (Palma dice que sí; los documentos, que no). | G p. 207 |
| **Navarro de Villodres** | «Soy el último arzobispo del rey, y nunca pisé esta ciudad: el mariscal Sucre no me dejó pasar de La Paz.» | G p. 320-322 |

---

## E. Acompañantes y ambiente

| Personaje | Qué pasa al presionar I | Estado |
|---|---|---|
| Zambito | Se esconde tras el Quitacapas; habla Ríos. | modelo y animación |
| Alcalde de aguas | Habla el aguatero. | diseño |
| Alguacil de 1620 | Se detiene si te pones entre él y el refugiado; habla el refugiado. | diseño |
| Niños de la enramada · niñas huérfanas | Te miran / se esconden; habla Aroca / San Alberto. | diseño |
| Indalecio Sandi | Habla Juana. | diseño |
| Cochero de las carrozas | Es del tránsito: sin encuentro. | modelo |
| Alonso Ramírez de Vergara y los de la procesión | Fuera de los encuentros (decisión del usuario). | — |

## F. Investigados el 2026-11-26 (fuentes de internet, no del catálogo)

Estas fuentes no están en el catálogo (`contenido/catalogo/`). Hay que pasarlas como fichas nuevas antes de grabar las voces.

### 33. El gato de la plaza · `gato` · **narrador** (decorativo, comentario curioso) · **aprobado 2026-11-26**
Inspirado en Behemot, el gato de *El maestro y Margarita* (decisión del usuario). Sin historia de Sucre. No llamarlo
«gordo» ni compararlo con un cerdo (pedido del usuario).
**Lo que ves:** un gato negro enorme sentado en un poyo o en una ventana, que te sigue con la mirada.
**Al presionar I:** te mira, bosteza y se va despacio, sin apuro, como dueño de la calle.
- *(cronista)* «Vaya, te encontraste con el gato de la plaza. No es de ninguna casa: todas las casas son suyas.»
- *(cronista)* «A quien haya leído “El maestro y Margarita”, del ruso Mijaíl Bulgákov, le recordará a Behemot: un gato que andaba en dos patas, jugaba al ajedrez e intentó pagar su boleto del tranvía como cualquier pasajero.»
- *(cronista)* «Este, de momento, se conforma con mirar pasar a la gente.»
- **R** *(cronista)* «Otra vez el gato. Él no te recuerda.»
- **Fuente:** M. Bulgákov, *El maestro y Margarita*. Guiño literario, no historia de Sucre.

### 34. El perro de San Roque · `perro_san_roque` · **narrador** · **aprobado 2026-11-26**
**Lo que ves:** un perro esbelto, castaño y blanco (o negro), trotando con un pan en la boca.
**Al presionar I:** mueve la cola, te rodea una vez y sigue su camino con el pan, sin soltarlo.
- *(cronista)* «Vaya, te encontraste con el perro de San Roque. No, el pan no es para ti.»
- *(cronista)* «Cuenta la tradición que San Roque cuidaba apestados en Italia y se contagió. Se apartó solo a un bosque, y un perro le llevaba cada día un pan robado de la mesa de su amo.»
- *(cronista)* «Por eso San Roque era el santo contra las pestes. En 1639 La Plata ya tenía su ermita, cuidada por los pulperos: era el patrón del Cabildo contra las epidemias.» (Q 203)
- *(cronista)* «El arzobispo San Alberto la reconstruyó hacia 1790. En 1825, a la entrada de San Roque, Sucre recibió una llave de oro en el Templo de la Inmortalidad.» (Q 363, Q 575-577)
- *(cronista)* «Y cada 16 de agosto, en su fiesta, los vecinos todavía llevan a sus perros a misa a San Roque.»
- **Fuentes:** Q 203, Q 363, Q 575-577 (`lugares/san_roque.md`); la leyenda del perro, tradición hagiográfica ([Catholic.net](https://es.catholic.net/op/articulos/53593/cat/116/san-roque-y-su-perro.html)); la fiesta con perros en Sucre ([Correo del Sur, 2023](https://correodelsur.com/local/20230816/san-roque-amantes-de-los-canes-visitan-el-templo-este-16-de-agosto.html)).

### 35. La cebrita vial · `cebrita` · época actual
**Lo que ves:** una persona disfrazada de cebra ayudando a cruzar en una esquina; hace señas de "pase" y "alto".
**Al presionar I:** levanta una mano enguantada, te hace "alto", mira a los dos lados y después te invita a cruzar. Habla el cronista (la cebra no se quita la máscara).
- *(cronista)* «Vaya, te encontraste con una cebra. Debajo del disfraz hay una persona, casi siempre joven, que trabaja educando en la calle.»
- *(cronista)* «La idea nació en La Paz y llegó a Sucre en mayo de 2012: el Proyecto Cebras. Enseñan a cruzar por la cebra, la de la calzada, y a respetar al peatón.»
- *(cronista)* «En 2015 eran unas 110 en Sucre. Su financiamiento fue inestable: en 2019 se quedaron sin equipo, y volvieron a las calles gracias a patrocinadores y un acuerdo con la Alcaldía.»
- **M** *(cronista)* «¿Por qué no habla? La cebra no habla: hace señas. Así se hace entender en cualquier esquina y con cualquier ruido.»
- **Fuentes:** [Correo del Sur, 2023](https://correodelsur.com/local/20230604_cebras-11-anos-educando-en-las-calles-de-la-capital.html), [Correo del Sur, 2019](https://correodelsur.com/local/20190617/las-cebras-vuelven-a-las-calles-ahora-con-el-compromiso-de-la-alcaldia.html), [La Paz traffic zebras](https://en.wikipedia.org/wiki/La_Paz_traffic_zebras). **Pendiente:** confirmar si el programa sigue en 2026.

### 36. Hernando Siles Reyes · `hernando_siles` · época `republica`
Nacido en Sucre el 5 de agosto de 1882 (otra fuente da 1881). Abogado, profesor y político; presidente de Bolivia de
1926 a 1930. Fundó el Partido Nacionalista; renunció el 28 de mayo de 1930 ante un golpe inminente y murió exiliado en
Lima en 1942. Padre del presidente Hernán Siles Zuazo y de Luis Adolfo Siles Salinas.
**Propuesta de encuentro:** A, en la puerta de la Universidad o de la casa de gobierno, con un ejemplar de periódico.
- **P** «Hernando Siles. Nací en esta ciudad, en 1882. Abogado, profesor… y presidente de la República, de 1926 a 1930.»
- **H1** «Fundé mi propio partido, el Nacionalista. Quise hacer reformas sociales en un país que no estaba de acuerdo.»
- **H2** *(cronista)* «La crisis mundial de 1929 golpeó a Bolivia. En mayo de 1930, con un golpe en puerta, renunció y dejó el gobierno a su gabinete. Murió en el exilio, en Lima, en 1942.»
- **H3** *(cronista)* «Dos de sus hijos también fueron presidentes: Hernán Siles Zuazo y Luis Adolfo Siles Salinas.»
- **M** *(propuesta)* «¿El periódico? Para saber qué dicen de mí hoy. En política, conviene leer temprano.»
- **Falta:** el vínculo de Siles con un lugar de la zona (¿casa natal? ¿la calle Hernando Siles?). Sin eso, no hay dónde ponerlo.
- **Fuentes:** [Wikipedia](https://en.wikipedia.org/wiki/Hernando_Siles), [Biografías y Vidas](https://www.biografiasyvidas.com/biografia/s/siles_hernando.htm).

### 37. Guillermo Francovich · `guillermo_francovich` · época `republica`
Filósofo y dramaturgo, nacido en Sucre en 1901 y muerto en Río de Janeiro en 1990. Fue rector de la Universidad de San
Francisco Xavier, dirigió el Centro Regional de la UNESCO en La Habana y fue miembro de la Academia Boliviana de la
Lengua. Escribió *La filosofía en Bolivia* y *El pensamiento boliviano en el siglo XX* (1956).
**Propuesta de encuentro:** A, en la portada de la Universidad (Casa de la Libertad), leyendo; segundo rector junto a
Santillán, tres siglos después. Encaja como **custodio moderno** de la Universidad si se prefiere un rector del siglo XX.
- **P** «Guillermo Francovich. Nací en Sucre en 1901. Fui rector de esta Universidad de San Francisco Xavier.»
- **H1** «Me pasé la vida preguntando qué pensaba Bolivia. Escribí sobre la filosofía en Bolivia y sobre el pensamiento boliviano del siglo XX.»
- **H2** *(cronista)* «También escribió teatro, dirigió el centro de la UNESCO en La Habana y murió en Río de Janeiro en 1990.»
- **M** *(propuesta)* «¿Por qué leo en la puerta? Porque esta universidad empezó dando clases dentro de una iglesia, sin aulas. Se puede pensar en cualquier parte.»
- **Falta:** las fechas de su rectorado.
- **Fuentes:** [Biografías y Vidas](https://www.biografiasyvidas.com/biografia/f/francovich.htm), [La filosofía en Bolivia, 3.ª ed. (PDF, U. Hildesheim)](https://www.uni-hildesheim.de/media/koselleck/Geschichten_der_Philosophie/Spanisch/Voelker_Nationen/Bolivianische_Philosophie/1945_Francovich/1945_1987_Francovich.pdf).
