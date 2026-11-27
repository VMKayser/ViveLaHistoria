# Geometría, Curvaturas y Materiales de Vehículos 3D

Referencia técnica para los pasos C, D, E y F de `vehiculo-3d-desde-diseno`.

## 1. Superficies curvas sin faceteado ni abolladuras

- **Perfiles longitudinales y transversales:** usar interpolación cúbica de Hermite monótona (Fritsch-Carlson) sobre puntos clave medidos desde la vista lateral y frontal. Evita oscilaciones (sobreimpulsos) en transiciones capó → parabrisas → techo.
- **Invernadero (tumblehome) y costado:** los automóviles reales estrechan su cabina hacia el techo (`y` disminuye entre la línea de cintura y el riel del techo) y recogen ligeramente el faldón inferior hacia el bastidor. Modelar la sección transversal con al menos 4–6 niveles verticales (`faldón`, `panza`, `cintura`, `marco inferior`, `riel de techo`, `hombro elíptico`).
- **Subdividir antes de redondear en planta:** cuando el frente o la cola se curvan en planta (esquinas redondeadas entre flanco y frente/trasera), subdividir previamente paneles, capó, parrilla y **parachoques** en segmentos cortos (`<= 0.12–0.20 m`) para que acompañen la misma función de deformación sin despegar matrículas ni ópticas.
- **Encuentros estancos:** construir siempre el cintillo superior del parabrisas/luneta y los pilares A/B/C/D cerrando contra el hombro del techo. No tapar huecos con planos sueltos coplanares (producen *z-fighting* en WebGL).
- **Normales y bordes duros:** tras aplicar `SOLIDIFY` o biseles finos, marcar como bordes duros (`edge.smooth = False`) las aristas cuyo ángulo diedro supere el umbral de la pieza (`~45°` en paneles de carrocería, `~75°–80°` en platos curvos de llanta). Así la cara exterior se sombrea suave pero no se promedia con el canto de espesor.

## 2. Recorte de pasos de rueda y aberturas

- El arco del guardabarros debe recortar tanto el panel inferior de chapa como cualquier moldura o faldón que pase a esa altura.
- Cerrar cada paso de rueda por dentro con una bóveda oscura (`interior`) y tramos de piso delantero/central/trasero para impedir ver el suelo o las ruedas del lado opuesto a través de la carrocería.
- Cada ventana lleva: hueco real entre pilares, burlete perimetral (`goma` o `marco`) y lámina de cristal (`vidrio`, opacidad `~0.30–0.38`, `Roughness ~0.20`).

## 3. Ruedas y llantas por revolución

1. **Neumático:** perfil cerrado o simétrico `(radio, desplazamiento_axial)` con:
   - Talón interior en contacto con el labio de la llanta.
   - Flanco convexo suave.
   - Hombro redondeado y banda de rodadura con 2–4 canales anulares reales (`~4–8 mm` de profundidad) más cortes transversales escalonados opcionales.
   - Costura angular colocada en `t = -π/2` (punto inferior contra el suelo). Crear capa UV continua por cara y soldar después los vértices coincidentes (`remove_doubles`), manteniendo intactos los dos valores UV de cierre.
2. **Llanta:** perfil torneado cerrado con labio exterior escalonado, garganta y plato cóncavo o abombado según referencia.
   - Cortar las perforaciones de ventilación con cilindros o prismas perfilados mediante modificador `BOOLEAN` (`DIFFERENCE`, solver `EXACT`) antes de consolidar.
   - Añadir tapa/buje central y el número real de tuercas/espárragos del vehículo (p. ej. 4, 5 o 6).

## 4. Materiales, espacio de color y limpieza UV

- En glTF 2.0, `pbrMetallicRoughness.baseColorFactor` se almacena en **RGB lineal**, mientras que las paletas de diseño suelen expresarse en hex **sRGB**:
  $$c_{\text{lin}} = \begin{cases} c / 12.92 & c \le 0.04045 \\ ((c + 0.055)/1.055)^{2.4} & c > 0.04045 \end{cases}$$
- Eliminar capas UV de todas las mallas consolidadas que solo usan color base constante; conservar UV y exportar tangentes unitarias en las mallas que llevan textura de normales (como la goma del neumático).
- Empaquetar cualquier textura (`image.pack()`) dentro de Blender antes de exportar y verificar su licencia en el repositorio.
