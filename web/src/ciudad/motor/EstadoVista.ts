// Estado de la vista compartido entre la escena 3D (que lo escribe en cada cuadro) y la interfaz (minimapa,
// brújula, nombre de la calle), sin pasar por React: la interfaz lo lee en su propio ciclo de dibujo. Los pedidos en
// sentido contrario (ir a un punto desde el minimapa, girar al norte) se publican como órdenes.
import type { Limites, Modo } from "../tipos";

export type Orden =
  | { tipo: "ir"; x: number; z: number }   // web
  | { tipo: "desplazar"; dx: number; dz: number } // web, inmediato (arrastre del minimapa)
  | { tipo: "norte" }
  | { tipo: "zoom"; factor: number }
  /** Volver a una toma guardada (revisiones): posición de los ojos (web), rumbo e inclinación en radianes. */
  | { tipo: "toma"; x: number; y: number; z: number; rumbo: number; inclinacion: number };

/** Lo que la escena ofrece para enmarcar una zona (lo registra escena/Capturador). */
export interface ServicioCaptura {
  /** Copia del cuadro actual y datos 3D del marco (coordenadas 0–1 de la pantalla). */
  capturar(marco: { x0: number; y0: number; x1: number; y1: number }): Promise<{ lienzo: HTMLCanvasElement; datos: import("../revision/tipos").DatosEscena }>;
}

export type ImagenMapa = { lienzo: HTMLCanvasElement; limites: Limites };

export class EstadoVista {
  modo: Modo = "mapa";
  /** Posición del observador (web): el caminante, o el punto que mira la cámara aérea. */
  x = 0;
  z = 0;
  /** Altura de los ojos (web) e inclinación de la mirada (radianes), a pie. */
  y = 0;
  inclinacion = 0;
  /** Rumbo en radianes, sentido horario desde el norte. */
  rumbo = 0;
  /** Huella de lo que se ve en el suelo (vista aérea): 4 esquinas (x, z), o null. */
  huella: [number, number][] | null = null;
  /** Distancia de la cámara aérea a su objetivo (para la escala del minimapa). */
  distancia = 300;
  /** Imagen cenital de la ciudad para el minimapa (se genera una vez cargada). */
  mapa: ImagenMapa | null = null;
  /** Medición del último segundo (panel del taller). */
  rendimiento = { fps: 0, llamadas: 0, triangulos: 0 };
  /** Servicio de captura (null hasta que la escena lo registra). */
  captura: ServicioCaptura | null = null;

  private oyentesOrden = new Set<(o: Orden) => void>();
  private oyentesMapa = new Set<() => void>();

  ordenar(o: Orden) {
    this.oyentesOrden.forEach((f) => f(o));
  }

  alOrdenar(f: (o: Orden) => void) {
    this.oyentesOrden.add(f);
    return () => void this.oyentesOrden.delete(f);
  }

  ponerMapa(m: ImagenMapa) {
    this.mapa = m;
    this.oyentesMapa.forEach((f) => f());
  }

  alCambiarMapa(f: () => void) {
    this.oyentesMapa.add(f);
    return () => void this.oyentesMapa.delete(f);
  }
}
