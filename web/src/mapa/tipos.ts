export type Calle = { nombre: string; tipo: string; puntos: [number, number, number][] };
export type LugarOSM = { nombre: string; tipo: string; x: number; y: number; z: number };

export type FotoIndice = {
  archivo: string;
  web: string;
  fecha: string;
  gps: { lat: number; lon: number; x: number; y: number; metodo: string } | null;
};

/** Lo que se guarda por foto en fotos/ubicaciones.json. x/y/z = dónde está lo fotografiado, no la cámara. */
export type Ubicacion = {
  x: number; // metros al este del centro del lienzo
  y: number; // metros al norte
  z: number; // altura del terreno en el lienzo
  lat: number;
  lon: number;
  rumbo: number | null; // hacia dónde mira la cámara: 0 = norte, 90 = este
  calle: string;
  cerca: string[]; // lugares OSM con nombre a menos de 80 m
  origen: "manual" | "gps";
  nota: string;
  actualizado: string;
};

export type Ubicaciones = Record<string, Ubicacion>;
