# Encuentros con personajes: plan de la funcionalidad

**Fecha:** 2026-11-26 · **Autor:** claude · **Estado:** propuesta, a la espera de que la apruebe el usuario.
**Guiones:** [guiones.md](guiones.md). **Contenido y fuentes de cada personaje:** [guía de personajes](../guiaPersonajes.md).
**Avance de modelos:** [lista_avance.md](../lista_avance.md).

Este plan **reemplaza** lo que dicen §1.3 (máquina de estados, botón "Hablar") y §1.4 (la ficha) de la guía de
personajes. El resto de la guía (arquetipos, fuentes, etiquetas, presupuesto, colocación) sigue valiendo.

---

## 1. Qué es (decisiones del usuario, 2026-11-26)

- **Los personajes no conversan entre ellos.** Cada uno habla solo con el jugador.
- Todos tienen algo que contar, **salvo los de la procesión de Guadalupe** (la imagen, los vecinos, el joven y el
  obispo Ramírez de Vergara, que van en ella).
- El jugador pasea y se los encuentra **haciendo su mecánica** (lo característico suyo: Ocaña pinta, Marta cuenta
  ajíes, el sirviente camina en sigilo…). Eso se ve sin tocar nada.
- Al acercarse aparece un aviso sencillo: **"Presiona I para interactuar"** (en el celular, un botón).
- Al interactuar, **la cámara se acomoda en una toma cinematográfica**, el personaje **se presenta**, **cuenta su
  historia** (o la de la que forma parte) y **explica por qué hace lo que hace** (su mecánica).
- Algunos son **custodios de un edificio histórico**: cuentan la historia del edificio y pueden **pedir una donación**
  para su mantenimiento. Pago con **Stripe**.
- Estilo del diálogo: **"Carta de 1809"** (`ui_ideas/encuentros_claude/`, propuesta 04): la frase llega escrita en un
  papel de la época, el rostro va en un **camafeo ovalado** y un **sello de lacre** cierra la carta.

---

## 2. El encuentro, paso a paso

```
PASEO      el personaje hace su mecánica (bucle propio). Lo ves desde lejos.
  │ < 8 m  ATENTO: gira la cabeza hacia ti (look-at, sin clip).
  │ < 3 m  y lo tienes delante (ángulo < 50°): aviso "Presiona I para interactuar".
  ▼ I / toque
TOMA       0,8 s: el control pasa a la cámara del encuentro; el personaje se vuelve hacia ti.
CARTA      presentación → historia → "por qué hago esto" → (menú).
  │        Menú al pie de la carta (enlaces escritos a mano):
  │          · "Cuénteme de este edificio"   (solo custodios y personajes con edificio)
  │          · "¿Quién lo cuenta?"            (solo fichas con versiones)
  │          · "Colaborar con su cuidado"     (solo custodios con fondo activo)
  │          · "Despedirse"
  ▼ Despedirse / Esc
SELLO      el lacre cierra la carta; estampa en la libreta; la cámara vuelve en 0,6 s.
ESPERA     20 s sin volver a ofrecer el aviso (el personaje sigue con su mecánica).
```

Reglas:
- **Nunca se abre solo.** El aviso aparece solo para el personaje más cercano que tienes delante.
- **Un toque / clic / I / espacio adelanta**: si la frase se está escribiendo, la completa; si ya está, pasa a la siguiente.
  La carta **no avanza sola** (a diferencia de la maqueta): el jugador lee a su ritmo.
- **Volver a hablar** con alguien ya visitado empieza directamente en el menú, con un saludo corto ("¿Otra vez por
  aquí?"), sin repetir toda la historia.
- **La donación nunca interrumpe la historia**: es una opción del menú. El personaje la menciona **una vez**, en una
  frase, al final de la historia del edificio; si el jugador dice "Ahora no", no vuelve a pedir en esa sesión.

### 2.1 El aviso

- Texto: **Presiona I para interactuar** (la I en dorado, como la referencia), centrado en el tercio inferior,
  fuente Alegreya, sombra suave, sin caja. Aparece con un fundido de 0,2 s.
- Celular: el mismo texto sin "Presiona I", con un **botón redondo de acción** donde ya está el botón de acción del
  APK (`Interaccion.usar()`).
- Si el personaje tiene nombre conocido por el jugador (ya lo visitó), el aviso dice "Hablar con Mariana Zudáñez".

### 2.2 La toma cinematográfica

Cada personaje declara su toma en el JSON (`encuentro.camara`); si no la declara, se usa la de su arquetipo:

| Arquetipo | Toma por defecto |
|---|---|
| A fijo | Tres cuartos, a 2,2 m, altura 1,5 m, el personaje en el tercio izquierdo o derecho (el lado con más calle detrás), lente de 40°. |
| B patrullero | Igual que A, en el punto donde se detuvo. |
| C en altura | Contrapicado desde la vereda de enfrente: cámara a 1,4 m mirando al balcón; el balcón en el tercio superior. |
| D vehículo | Junto a la ventanilla o al pescante, a 1,8 m, con el caballo fuera de cuadro. |
| E horario | La de A, con más distancia (2,8 m) para que se vea el entorno nocturno. |

- **Sin atravesar muros**: antes de mover la cámara se hace un raycast del personaje al punto de la toma; si choca,
  se prueba el otro lado y luego más cerca (1,6 m). Nunca se deja la cámara dentro de un edificio.
- **El abajo queda libre** para la carta: el personaje se encuadra en la mitad superior (en la maqueta, `lejos: 0,72`).
- Durante el encuentro: se congela el tránsito a menos de 15 m (los coches esperan), se baja el volumen ambiente y,
  solo en la PC, se aplica una profundidad de campo suave al fondo.
- **Gestos por frase**: cada frase del guion puede pedir un gesto (`gesto`); si no pide nada, el personaje usa
  `hablar` en bucle. Los mudos usan su mecánica en vez de `hablar`.

### 2.3 La carta (UI "Carta de 1809", en Godot)

Se lleva a Godot la propuesta 04 de `ui_ideas/encuentros_claude/` (CSS en `estilos.css`, selector `[data-estilo="carta"]`):

- **Papel**: textura de papel de época en 9 cortes (`StyleBoxTexture`), con borde irregular; ocupa el ancho inferior
  (en el celular, todo el ancho; en la PC, máx. 900 px).
- **Camafeo**: retrato del personaje en un óvalo con marco dorado. Los retratos se renderizan **una vez** desde el
  modelo (hay un `herramientas/retrato.py` en la maqueta) y se guardan como PNG en `ciudad3d/personajes/retratos/`.
  Los mudos y las leyendas usan el mismo camafeo, con el nombre en cursiva ("Lo que se cuenta").
- **Nombre** en versalitas (Alegreya SC), **texto** en Cormorant Garamond o Alegreya con efecto de escritura
  (26 ms por letra, pausa en la puntuación; con "movimiento reducido", de golpe). Tamaño mínimo 15 px en el celular.
- **Etiqueta** del tipo (`hecho`, `testimonio`, `tradicion`, `leyenda`, `satira`) como un pequeño sello de tinta en la
  esquina, con el color de la guía (§1.5).
- **Fuentes** (`Q-0448-2`…) en el pie, discretas, siempre visibles.
- **Sello de lacre**: aparece al terminar y "cierra" la carta al despedirse.
- **Menú**: enlaces en tinta, subrayados, al pie del papel. En la PC también con 1-4.
- Las fuentes tipográficas (Alegreya, Alegreya SC, Cormorant Garamond) son OFL: se registran en `recursos/LICENCIAS.md`
  y se empaquetan (no se cargan de Google).

### 2.4 El narrador (personajes que no hablan)

Pedido del usuario (2026-11-26). Para los mudos, los niños y animales de leyenda, el pasquinero y los que huyen:

1. Al presionar I, **el personaje reacciona y se va**: hace su gesto (el sirviente, `silencio`: el dedo en los labios
   o la mano de "no moleste") y se aleja rápido (`caminar_rapido`) hasta perderse en la esquina o tras una columna.
2. La cámara **lo sigue con la mirada** mientras se va (1,5-2 s) y se queda en el lugar.
3. Entra la carta con la voz del **narrador**: el camafeo no muestra un rostro sino un **emblema de cronista** (pluma y
   tintero) y el nombre dice **"El cronista"**. Empieza siempre igual: **"Vaya, te encontraste con …"**, y sigue con
   quién era, su historia y el contexto.
4. El narrador **tutea** al jugador; los personajes que hablan lo tratan de **usted** (son de otra época).
5. Volver a ver al mismo mudo: vuelve a irse, y el cronista empieza en el menú ("Otra vez él…").
6. El cronista también puede cerrar la historia de un personaje que sí habla cuando hace falta contar lo que ese
   personaje no sabe (su propio final): esas frases van marcadas `quien: "cronista"` en el guion.

### 2.5 Libreta

Al sellar la carta, el personaje entra en la **libreta** (`Guardado`): estampa con nombre, año y fuente. Estampas
especiales: "Aprendiste a preguntar quién lo cuenta" (Jaime), "El saludo al oidor", "25 de mayo" (ruta completa), y
**"Benefactor de …"** (donación confirmada; ver §4.5).

---

## 3. Sistema en Godot

Sobre lo que ya existe (`Interaccion`, `Hora`, `Guardado`, `Puente`, `Jugador`), sin tocar `principal.gd` ni `ciudad.gd`:

| Pieza | Dónde | Qué hace |
|---|---|---|
| `contenido/personajes.json` | fuente única | Ficha de cada personaje (esquema de la guía §1.9) + bloque `encuentro` (abajo). Se genera desde `guiones.md` con un script, para que el texto se revise en Markdown. |
| `personaje.gd` (`class_name Personaje`) | `ciudad3d/scripts/personajes/` | Carga el GLB, maneja el `AnimationPlayer`, la mecánica (bucle propio), el look-at y la ruta. Registra su zona en `Interaccion`. |
| `director_personajes.gd` (autoload) | ídem | Activa/oculta por distancia, hora y época; presupuesto 6 (celular) / 10 (PC); elige el más cercano para el aviso. |
| `encuentro.gd` | ídem | Toma de cámara, bloqueo del control, congelar tránsito, recorrer el guion, menú, salida. |
| `carta.tscn` / `carta.gd` | `ciudad3d/escenas/ui/` | La UI de §2.3. |
| `aviso.tscn` | ídem | "Presiona I para interactuar" / botón táctil. |
| `donaciones.gd` | `ciudad3d/scripts/` | Abre el pago y consulta el resultado por `Puente` (web) o el navegador del sistema (APK). Ver §4. |

**Bloque `encuentro` del JSON:**

```json
"encuentro": {
  "camara": {"lado": "der", "distancia": 2.2, "altura": 1.5, "fov": 40},
  "edificio": "catedral",
  "fondo_donacion": "catedral",
  "guion": [
    {"seccion": "presentacion", "quien": "personaje", "texto": "…", "gesto": "saludar"},
    {"seccion": "historia", "texto": "…", "fuentes": ["Q-0127-2"], "tipo": "hecho"},
    {"seccion": "mecanica", "texto": "…", "gesto": "retroceder_mirar_cuadro"},
    {"seccion": "edificio", "texto": "…", "fuentes": ["Q 125"]},
    {"seccion": "donacion", "texto": "…"},
    {"seccion": "gracias", "texto": "…"},
    {"seccion": "regreso", "texto": "¿Otra vez por aquí?"}
  ]
}
```

**Tecla I** (decisión del usuario, 2026-11-26): no choca con nada (R/F siguen mirando arriba/abajo, Q/E girando). Intro (`interaccion.gd`) sigue como alternativa.

---

## 4. Donaciones con Stripe

### 4.1 Cómo se ve

1. El custodio termina la historia de su edificio y dice **una frase** (está en cada guion, sección `donacion`).
2. En el menú aparece **"Colaborar con su cuidado"**. Si el jugador lo elige, se abre un panel **fuera de la carta**
   (sobrio, sin estilo de época, para que quede claro que es un pago real):
   - qué edificio, **quién recibe el dinero** y **en qué se usa** (texto del fondo, ver §4.3);
   - montos sugeridos y monto libre;
   - enlace a la rendición de cuentas;
   - botón "Donar con Stripe".
3. Se abre **Stripe Checkout** (página de pago alojada por Stripe): en la web, en una pestaña nueva; en el APK, en el
   navegador del sistema. La ciudad no ve ni guarda datos de tarjeta.
4. Al volver, el juego consulta el resultado. Si se confirmó, el personaje agradece (sección `gracias` del guion) y se
   gana la estampa "Benefactor de …". **La donación no da ventajas de juego** (ni personajes, ni zonas): solo la estampa
   y, si el donante quiere, su nombre en un libro de benefactores.

### 4.2 Arquitectura

```
Godot (carta) ──Puente──▶ web: POST /api/donaciones/sesion {fondo, monto}
                              │  valida fondo y monto contra contenido/donaciones.json
                              │  crea Checkout Session (mode=payment, metadata: fondo, personaje)
                              ◀─ url de Checkout
Godot abre la url ──────────▶ Stripe Checkout ──▶ success_url = /donaciones/gracias?sesion=…
Stripe ──webhook──▶ POST /api/donaciones/webhook  (firma verificada con STRIPE_WEBHOOK_SECRET)
                              │  checkout.session.completed → registra la donación (fondo, monto, fecha)
Godot, al recuperar el foco ─▶ GET /api/donaciones/estado?sesion=… → "pagada" → agradecimiento + estampa
```

- Rutas nuevas en `web/src/app/api/donaciones/` (el sitio Next.js ya corre como servidor: tiene `api/revisiones`).
- Dependencia `stripe` (npm). Claves solo en variables de entorno del servidor; **nada de claves en Godot ni en el APK**.
- El registro de donaciones necesita almacenamiento persistente en el servidor donde se publique la web (por definir).
- Si el dinero va directo a cada institución, **Stripe Connect** (una cuenta conectada por institución) es lo más
  limpio: el dinero no pasa por el proyecto y cada una ve lo suyo.

### 4.3 `contenido/donaciones.json` (fondos)

```json
{"id": "catedral", "edificio": "Catedral Metropolitana", "custodio": "diego_de_ocana",
 "receptor": "…institución…", "uso": "…qué se paga con esto…", "activo": false,
 "montos": [5, 10, 25], "moneda": "usd", "cuenta_stripe": null, "rendicion_url": null}
```

Un fondo empieza **inactivo**: el custodio cuenta la historia del edificio igual, pero sin la frase de donación ni el
botón, hasta que el fondo tenga receptor y uso confirmados.

### 4.4 Custodios propuestos (un custodio por edificio)

| Edificio | Custodio | ¿Ya animado? | Donación |
|---|---|---|---|
| Catedral (y capilla de Guadalupe) | Fray Diego de Ocaña | sí | sí, si hay convenio |
| Palacio Arzobispal / Museo Eclesiástico | Benito María de Moxó | sí | sí, si hay convenio |
| Casa de la Libertad (Universidad) | Luis de Santillán, rector fundador | no (diseño listo) | sí, si hay convenio |
| San Francisco | Fray Francisco de Aroca | no | sí, si hay convenio |
| Santa Teresa | Gaspar de Villarroel | no (zona sin modelar) | sí, si hay convenio |
| San Felipe Neri | Fray José Antonio de San Alberto | no (por ubicar) | sí, si hay convenio |
| Santo Domingo (Colegio Junín) | Fray Domingo de Santo Tomás | sí | a decidir |
| Cabildo (Alcaldía) | Escribano de los portales | no | no propuesta (edificio municipal en uso) |
| Palacio de Gobierno | Jaime Zudáñez | sí | no propuesta (Gobernación en uso) |
| Santa Mónica | Gerónima de Villavicencio | no | a decidir |
| La Glorieta | Francisco Argandoña y Clotilde Urioste | sí | a decidir (falta fuente del edificio) |
| Plaza 25 de Mayo (la pila) | El aguatero | sí | no (espacio público) |

Otros personajes nombran el edificio que tienen detrás (Araujo la Catedral, Túpac Amaru la Universidad…) pero **solo
el custodio pide**: así el jugador no recibe tres pedidos frente a la misma puerta.

### 4.5 Lo que hay que decidir antes de cobrar (no es técnico)

1. **Quién recibe el dinero.** Pedir "para el mantenimiento de la Catedral" solo es honesto si el dinero llega a quien
   la mantiene (Arzobispado, Fundación Cultural del BCB, USFX, órdenes religiosas…) con un **convenio** y un uso
   declarado. Otra opción: que el fondo sea del proyecto y lo diga ("para seguir reconstruyendo la Catedral en 3D"). Lo
   que no se puede es dar a entender lo primero y hacer lo segundo.
2. **Stripe y Bolivia.** Hasta donde sé, Stripe no abre cuentas a empresas con sede en Bolivia: haría falta una
   entidad en un país donde opere (o usar otro procesador). **Hay que confirmarlo** en la lista de países de Stripe
   antes de contar con él.
3. **APK y Google Play.** Play exige su propio sistema de pago para lo digital; las donaciones tienen reglas propias
   (en general, solo a organizaciones benéficas reconocidas y fuera de la app). **Hay que revisar la política vigente**;
   mientras tanto, en el APK el botón abre la página de donación en el navegador.
4. **Moneda, montos y comprobante** (¿recibo?, ¿deducible?), y la página pública de rendición de cuentas.

---

## 5. Orden de trabajo propuesto

| Fase | Qué | Con quién |
|---|---|---|
| **0** | El usuario aprueba guiones, custodios, la tecla I y decide §4.5. | usuario |
| **1. Sistema** | Aviso I, toma de cámara, carta, director, libreta. Se prueba con los **ya animados de la plaza**: Mariana, Jaime, Quitacapas y zambito, Ocaña. Revisión a pie y en el celular. | claude |
| **2. Resto de animados** | Sirviente, aguatero, niño de las hornacinas, Moxó (balcón por confirmar), Domingo de Santo Tomás (zona por modelar: hasta entonces queda fuera), Argandoña y Clotilde (época `republica`). | claude (colocación con el dueño de cada manzana) |
| **3. Donaciones** | Rutas de Stripe en modo prueba, panel, estampa. Se activa fondo por fondo cuando §4.5 esté resuelto. | claude |
| **4. Personajes nuevos** | Modelos y animaciones del Lote 1-2 que faltan (Marta Zárate, Araujo, Santillán, Aroca, centinela, escribano…), en el orden de la guía §2. | codex y claude |

**Lo que no se hace:** que hablen entre ellos, que la carta avance sola, pedir donación fuera del menú, o dar ventajas
de juego por pagar.

---

## 6. Estado de los personajes (según `lista_avance.md`, 2026-11-26)

75 filas: **75 con diseño, 22 con modelo, 13 con animación comprobada.**

- **Con animación (13):** aguatero · Alonso Ramírez de Vergara (procesión) · Moxó · Clotilde Urioste · Francisco
  Argandoña · Quitacapas · Diego de Ocaña · Domingo de Santo Tomás · Jaime Zudáñez · Mariana Zudáñez · niño de las
  hornacinas · sirviente mudo · zambito (acompañante).
  → **11 personajes con historia propia ya tienen modelo y animación** (sin contar al obispo de la procesión ni al zambito).
- **Con modelo, sin animación (9):** cebrita · cochero de las carrozas · gato gordo · perro de San Roque · Virgen de
  Guadalupe y 4 vecinos de la procesión.
- **Ninguno está todavía en Godot** con su zona de interacción: los modelos animados están en
  `web/public/models/ciudad/*/personajes/` y `personas/`, con su visor; falta colocarlos (es la fase 1-2).
