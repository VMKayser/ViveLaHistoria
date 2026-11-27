# San Miguel (R0219) — inventario y planta, 2026-11-24 (modelado en SAN_MIGUEL.py)

Traspaso de codex a claude autorizado por el usuario ("hazlo tu, cambio de dueno"), hecho: espacio `SAN_MIGUEL` en el
reparto (con `mobiliario_propio`), nave quitada de codex `M037.py` y M037 reexportado, aviso #45 en `mensajes_claude.md`.
Causa del vacío: codex quitó `construir_san_miguel(col)` en 8c9390c; `san_miguel_codex.py` quedó sin llamar.

## Marco
Eje de Arenales: origen (-292.582,-40.463), u=(.771,-.637) hacia el SE (s), n=(.637,.771) hacia la calle (d).
Línea de fachada d≈-0.2 (eje de Arenales en d=6.0, ancho 12.5, vereda 2.95). Fachada a Junín en s≈0 (eje Junín s=-6.2).
Suelo: s40→57.18, s52→57.73, s64→58.30 (sube hacia el SE). Detrás (d<-16.5) está el convento de codex (Eeb6abd).
Teatro (codex): E627dd1 desde s=64.4 (d>-6), E469654 desde s=65.2.

## Planta (s, d)
- Nave: s 0–49.5, d -0.2..-16.4. Altar hacia Junín. Cuerpo NO (s 0–17) más alto: muro ~13 m, techo a dos aguas
  (cumbrera ~17,5) con hastial SE visible sobre la nave; nave s 17–49.5 con el alero bajando en escalones (~11→9,5 m),
  pináculos pequeños en cada escalón, gárgolas blancas (tubos) bajo el alero.
- Vanos altos sobre Arenales (130406/130413, de NO a SE): ventana cuadrada en nicho abocinado, ventana de arco grande,
  ventana cuadrada en nicho, [escalón] ventana de arco en recuadro moldurado + farol de brazo verde, [escalón] ventana
  con bandera boliviana, [escalón] otra ventana con bandera (130431) + farol de brazo; enredadera en la esquina SE.
- Planta baja junto a Junín: dos puertas de madera (s≈2,5 de 1,3×2,7; s≈6 de 2,0×3,0 con reja), letrero Café
  Valentino entre ellas, placa "Calle Arenales", flecha amarilla. Muro liso blanco, sin zócalo.
- Fachada principal SE (plano s=49.5, mira al atrio): hastial con tejaroz de tejas y canes rojizos, portada barroca
  blanca centrada en d≈-8.2 (puerta de arco de madera, columnas pareadas sobre pedestales, entablamento, hornacina con
  frontón, remate escalonado con pináculos en el ápice).
- Torre: s 47.2–52.4, d -11.0..-16.4 (sobresale ~3 m al atrio). Fuste blanco ~11 m, cornisa; cuerpo de campanas
  (2 arcos con campana por cara, pilastras, ~4 m), cornisa con 4 pináculos; segundo cuerpo menor (1 arco por cara,
  ~3,2 m); cupulín con linterna de óculos y cruz/pararrayos (~22 m en total). Filetes rosados.
- Atrio: s 49.5–59.0, piso +0,5 m de losas pardas, hasta d=-16.4. Frente a la calle: muro de sillares pardo-rosados
  ~1,1 m con reja de lanzas (~1,8 m, friso de volutas abajo) y pilares de sillar con capitel piramidal:
  pilar s=49.5 (contra la esquina), s=51.0–52.0, portón: pilares 53.6–54.5 y 56.4–57.3 (abajo sillar ocre, arriba
  blanco con juntas, cornisa, remate piramidal), reja de dos hojas con arco de volutas y cruz, gradas por dentro;
  reja de la terraza 57.3–59.0 con letrero redondo "Terraza San Miguel"; buganvillas y macetas sobre el muro;
  pizarra "Café Mirador San Miguel". Al fondo (d≈-16.3) fachada de dos plantas blanca con ventana roja, balcón y
  puerta de souvenirs.
- Casa del café (La Torre Café Mirador): s 59.0–64.35, d -0.2..-16.4, dos plantas (~3,8 + 3,4 m), techo a cuatro
  aguas, alero de tejas con canes rojizos en el frente y en el lado del atrio. Frente: puerta-ventana roja con balcón
  de hierro y macetas sobre losa con ménsulas de volutas; abajo ventana de arco rebajado con marco rojo y reja;
  zócalo de sillar ~1,1 m; esquinal de sillares en la esquina NO. Lado al atrio: 5–6 ventanas rojas arriba, ventanas y
  puerta de arco roja abajo.
- Faroles de poste negros con farol colgante: frente a la casa y junto al pilar derecho del portón, al bordillo.

Fotos: 130401, 130404, 130406, 130413, 130427, 130431, 130435, 130438, 130440, 130442, 130445, 130448.
