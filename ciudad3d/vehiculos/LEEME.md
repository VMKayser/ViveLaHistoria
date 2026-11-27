# Vehículos

Los vehículos circulan con física real (`scripts/trafico.gd`, `scripts/trafico/`). **Flota mezclada** (pedido del usuario,
2026-11-26: lo moderno con lo viejo es parte del encanto): micros BRONCO, seis autos modernos, dos clásicos, el turismo
con remolque de pasajeros y dos carrozas con caballo y cochero. Todo sale de una sola fuente,
`web/scripts/vehiculos_trafico.json`: qué vehículos, sus colores (cada unidad sale de un color de su lista), qué material
es pintura, faro o piloto, masa, y la **flota** (qué sale a la calle y con qué peso; `remolque` engancha uno detrás).

Cadena: GLB de codex (`web/public/models/ciudad/codex/vehiculos/`, solo lectura) → `web/scripts/preparar_vehiculos.mjs`
(`npm run trafico`: kits fundidos por función con tres niveles de detalle, en `web/public/trafico/`) →
`herramientas/vehiculos.mjs` (`datos/vehiculos/*.bin` + `datos/vehiculos.json` con tipos, flota y caballo). `npm run
ciudad` corre lo último solo. Un vehículo nuevo: sumarlo a `vehiculos_trafico.json` (material → tipo de vértice,
variantes de color) y a `flota`.

| Pieza | Qué hace |
|---|---|
| `scripts/trafico/kit_vehiculo.gd` | Mallas por pieza y nivel (cuerpo, vidrio, rueda, `ruedad` si la delantera es de otro tamaño, `tornamesa`), medidas, un material por color |
| `scripts/trafico/vehiculo.gd` | VehicleBody3D con conductor (persecución pura + IDM + cruces). Carrozas: el eje delantero gira entero con las ruedas, las varas y el caballo; tiros del arnés y riendas de los puños del cochero a la boca |
| `scripts/trafico/caballo.gd` | Caballo ROME (`vehiculos/caballo.glb`, de `preparar_vehiculos.mjs`, color en los vértices): reposo, paso y galope con la cadencia según la zancada de cada clip (los cascos no patinan); pelaje por unidad |
| `scripts/trafico/remolque.gd` | Remolque sin física propia: sigue al ojo de la lanza (tractriz con tornamesa), ruedas apoyadas por rayos, choca con el caminante y los demás; los de atrás lo ven como obstáculo |

- Cochero: `blender/zonas/claude/personajes/cochero/construir.py` (figura sentada, color por cara, puños y asiento en
  cada pescante); `preparar_vehiculos.mjs` lo funde al cuerpo de las carrozas con `"cochero": true`.
- Los clips `rodar_*` de los GLB de codex son del visor: aquí las ruedas las mueve la física (o la distancia, en las de
  la tornamesa y el remolque). El caballo sí usa sus clips.
- Pruebas: `SUCRE_TRAFICO_TIPO="carroza_azul,turismo_abierto"` deja solo esos tipos en la calle (con `SUCRE_TRAFICO_MIRAR`).

Carriles (`datos/red.json`, de `web/scripts/red_vial.py`, `npm run trafico`): los micros van por el centro de la calzada
en las calles de sentido único, doblan en los cruces con arcos de `RADIO_GIRO` y las esquinas de la plaza se suavizan.
Después de cambiar la red, `python3 web/scripts/red_vial_revisar.py` simula al conductor en cada cruce y lista los que
se salen de la calzada (debe dar 0). En Godot, `SUCRE_TRAFICO_REGISTRO=1` muestra el `desvio` de cada micro respecto de
su carril (lo normal: < 0,5 m).
