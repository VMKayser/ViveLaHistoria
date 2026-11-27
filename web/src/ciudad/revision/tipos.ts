// Revisiones: correcciones que el usuario (o un revisor) marca en el visor enmarcando una zona de la pantalla.
// Se guardan en coordinacion/revisiones/<id>/revision.json junto a las imágenes. Coordenadas "lienzo" = metros,
// X este, Y norte, Z altura (las mismas de Blender y de reparto/).

export const CATEGORIAS = {
  fachada: "Fachada (vanos, molduras, color)",
  techo: "Techo o altura",
  volumen: "Volumen / forma del edificio",
  piso: "Calle, vereda o piso",
  mobiliario: "Postes, cables, faroles, bancos",
  vegetacion: "Árboles y plantas",
  falta: "Falta algo que existe",
  sobra: "Sobra algo que no existe",
  otro: "Otro",
} as const;
export type Categoria = keyof typeof CATEGORIAS;

export type Prioridad = "alta" | "media" | "baja";
export type EstadoRevision = "pendiente" | "en_curso" | "resuelta" | "descartada";

export type Punto3 = { x: number; y: number; z: number };

/** Lo que la escena sabe del encuadre (se calcula en el navegador). */
export type DatosEscena = {
  camara: {
    modo: "mapa" | "peaton";
    lienzo: Punto3;
    rumbo_grados: number;        // 0 = norte, 90 = este
    inclinacion_grados: number;  // + arriba
    fov_vertical_grados: number;
    aspecto: number;             // ancho / alto de la pantalla
  };
  /** Rectángulo en la pantalla, 0–1 desde arriba a la izquierda. */
  marco: { x0: number; y0: number; x1: number; y1: number };
  /** Lo que se ve en el centro del marco (punto 3D) y en sus esquinas; null si el rayo no toca nada. */
  centro: Punto3 | null;
  /** true si el centro no tocaba nada y se tomó el punto más cercano dentro del marco (o uno a 25 m en el rayo). */
  centro_aproximado?: boolean;
  esquinas: (Punto3 | null)[];
  distancia_m: number | null;
  calle: string;
};

/** Lo que agrega el servidor a partir de reparto/manzanas.json. */
export type Lugar = {
  manzana: string | null;
  edificio: string | null;
  espacio: string | null;
  asignado: string | null;   // agente dueño
  lat: number | null;
  lon: number | null;
};

export type Revision = {
  id: string;
  creada: string;
  autor: string;
  estado: EstadoRevision;
  categoria: Categoria;
  prioridad: Prioridad;
  comentario: string;
  lugar: Lugar;
  escena: DatosEscena;
  archivos: {
    captura: string;            // pantalla completa con el marco dibujado
    recorte: string;            // solo lo enmarcado
    referencia: string | null;  // foto adjunta por el revisor
    fotos_proyecto: string[];   // fotos de fotos/ elegidas como referencia
  };
  resolucion: { agente: string; fecha: string; nota: string; commit?: string } | null;
};

/** Lo que manda el formulario (el servidor completa id, fecha, lugar y archivos). */
export type NuevaRevision = Pick<Revision, "autor" | "categoria" | "prioridad" | "comentario" | "escena"> & {
  fotos_proyecto: string[];
};
