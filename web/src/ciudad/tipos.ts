// Tipos compartidos del visor de la ciudad.

/** Un GLB exportado por un agente (web/public/models/ciudad/<agente>/manifiesto.json). */
export type Modelo = { agente: string; id: string; url: string; triangulos: number; actualizado: string };

/** mapa = vista aérea navegable; peaton = recorrido a pie en primera persona. */
export type Modo = "mapa" | "peaton";

/** Rectángulo en coordenadas web (x este, z = −norte). */
export type Limites = { x0: number; z0: number; x1: number; z1: number };

export const AGENTES = ["claude", "codex"] as const;

/** Zona de trabajo (reparto/manzanas.json → zona) en metros del lienzo: xmin, ymin, xmax, ymax. */
export const ZONA_LIENZO = [-350, -410, -50, 110] as const;

/** Punto de llegada por defecto: Plaza 25 de Mayo / San Francisco (metros del lienzo). */
export const CENTRO_LIENZO: [number, number] = [-205, -150];
