# Rig, Clips NLA y Cinemática de Vehículos

Referencia técnica para los pasos G, H e I de `vehiculo-3d-desde-diseno`.

## 1. Sistema de coordenadas y pivotes

| Entorno | Frente | Arriba | Derecha | Dirección delantera | Rodadura adelante |
|---|---|---|---|---|---|
| **Blender** | `+X` | `+Z` | `-Y` | Giro en `+Z` (izq.) | Giro en `+Y` |
| **GLB / Three.js** | `+X` | `+Y` | `+Z` | Giro en `+Y` (izq.) | Giro en `-Z` |

Jerarquía mínima bajo el nodo raíz `<id_vehiculo>`:

```text
<id_vehiculo>  (origen en suelo z=0, centro longitudinal x=0)
├── carroceria
├── interior
├── cristales
├── decoracion
├── direccion_delantera_derecha      pivote en (eje_delantero, -semivia, centro_rueda_z)
│   └── rueda_delantera_derecha      pivote local (0, 0, 0)
├── direccion_delantera_izquierda    pivote en (eje_delantero, +semivia, centro_rueda_z)
│   └── rueda_delantera_izquierda    pivote local (0, 0, 0)
├── rueda_trasera_derecha            pivote en (eje_trasero, -semivia, centro_rueda_z)
└── rueda_trasera_izquierda          pivote en (eje_trasero, +semivia, centro_rueda_z)
```

El nodo raíz guarda en `extras.movimiento` (`userData.movimiento` en Three.js):
`radio_rueda`, `eje_trasero`, `eje_delantero`, `semivia`, `velocidad_maxima`, `retroceso_maximo`, `aceleracion`, `frenada`, `direccion_maxima`, `rapidez_direccion`, `velocidad_demo`, `radio_demo`.

## 2. Clips NLA portables

Para motores que inspeccionan clips pregrabados, exportar desde pistas NLA dos acciones de 1 segundo a 24 FPS (fotogramas `1..25`, 25 muestras explícitas):
- `rodar_adelante`: `rotation_euler.y = +2π * (frame - 1) / 24` en Blender (`-2π` alrededor de `Z` en GLB).
- `rodar_atras`: `rotation_euler.y = -2π * (frame - 1) / 24` en Blender (`+2π` alrededor de `Z` en GLB).

Nunca crear un clip de una vuelta con solo 2 claves (`0°` y `360°`), ya que ambos quaternions representan la misma rotación y el exportador glTF colapsa el giro a reposo.

## 3. Cinemática Ackermann y rodadura por distancia (GLB: +X frente, +Z derecha)

Sean:
- $L = x_{\text{del}} - x_{\text{tras}} > 0$: batalla (distancia entre ejes).
- $h > 0$: semivía lateral de ruedas.
- $r > 0$: radio geométrico de rodadura.
- $\delta$: ángulo de dirección virtual central ($\delta > 0$ gira hacia la izquierda, $-Z$).
- $\psi$: rumbo alrededor de $+Y$.
- $ds$: arco firmado recorrido por el centro del **eje trasero**.

Curvatura instantánea:
$$k = \frac{\tan(\delta)}{L}$$

Integración exacta sin deriva al pasar de curva a recta ($\operatorname{sinc}(u) = \sin(u)/u$, con $\operatorname{sinc}(0) = 1$):
$$\Delta\psi = ds \cdot k, \qquad \psi_{\text{medio}} = \psi + \frac{\Delta\psi}{2}$$
$$\Delta x_{\text{tras}} = ds \cdot \operatorname{sinc}\!\left(\frac{\Delta\psi}{2}\right) \cos(\psi_{\text{medio}}), \qquad \Delta z_{\text{tras}} = -ds \cdot \operatorname{sinc}\!\left(\frac{\Delta\psi}{2}\right) \sin(\psi_{\text{medio}})$$
$$\psi \leftarrow \psi + \Delta\psi, \qquad x = x_{\text{tras}} - x_{\text{eje\_tras}}\cos\psi, \qquad z = z_{\text{tras}} + x_{\text{eje\_tras}}\sin\psi$$

Para cada rueda $i$ con desplazamiento lateral $z_i \in \{+h\text{ (der)}, -h\text{ (izq)}\}$ y longitudinal $x_i \in \{L\text{ (del)}, 0\text{ (tras)}\}$:
$$ds_i = ds \sqrt{(1 + k z_i)^2 + (k x_i)^2}$$
$$\delta_i = \begin{cases} \operatorname{atan2}(k L,\, 1 + k z_i) & \text{delanteras} \\ 0 & \text{traseras} \end{cases}$$
$$\theta_{\text{rodadura}, i}^{\text{GLB}} \leftarrow \theta_{\text{rodadura}, i}^{\text{GLB}} - \frac{ds_i}{r}$$

Reglas operativas:
- Subdividir `dt` en pasos internos $h \le 1/120\text{ s}$ con integración trapezoidal de velocidad y dirección: garantiza trayectoria idéntica a 30, 60 y 120 FPS.
- Si `velocidadObjetivo` tiene signo opuesto a `velocidad` actual, frenar primero hasta `0` con desaceleración `frenada` antes de invertir la marcha.
- No ejecutar `THREE.AnimationMixer` sobre los pivotes de rueda mientras actúe `VehiculoAnimado`.
