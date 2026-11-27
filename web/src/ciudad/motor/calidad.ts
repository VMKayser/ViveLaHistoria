// Niveles de calidad. El visor arranca en "alta" y baja de nivel solo si el equipo no sostiene los cuadros por
// segundo (PerformanceMonitor). La resolución NO cambia mientras se mueve la cámara: cada cambio redimensiona el
// lienzo y los búferes del compositor, y eso se ve como un destello blanco.

export type NivelCalidad = "alta" | "media" | "baja";

export type Calidad = {
  /** Rango de densidad de píxeles del lienzo. */
  dpr: [number, number];
  /** Lado del mapa de sombras. */
  sombra: number;
  /** Oclusión ambiental (N8AO): preset de calidad o "no". */
  oclusion: "low" | "performance" | "no";
  /** Antialias multimuestra (MSAA) del compositor: muy caro en GPU integradas (≈37 ms por cuadro con 4×). */
  muestras: number;
  /** Antialias de posproceso SMAA (≈2–3 ms): reemplaza al MSAA. */
  smaa: boolean;
  /** Distancia (m) hasta la que se dibujan rejas, cables y carpinterías. */
  distanciaDetalle: number;
  /** Radio (px) del filtro pintado (Kuwahara); 0 = sin filtro. */
  pintado: number;
};

export const CALIDADES: Record<NivelCalidad, Calidad> = {
  alta: { dpr: [1, 1.5], sombra: 3072, oclusion: "low", muestras: 0, smaa: true, distanciaDetalle: 420, pintado: 3.5 },
  media: { dpr: [1, 1.25], sombra: 2048, oclusion: "performance", muestras: 0, smaa: true, distanciaDetalle: 280, pintado: 2.5 },
  baja: { dpr: [0.75, 1], sombra: 1024, oclusion: "no", muestras: 0, smaa: false, distanciaDetalle: 160, pintado: 0 },
};

export function bajarNivel(n: NivelCalidad): NivelCalidad {
  return n === "alta" ? "media" : "baja";
}
