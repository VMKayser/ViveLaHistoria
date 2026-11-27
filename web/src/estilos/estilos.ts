import type { Mat } from "./escena";

export type EstiloId = "lowpoly" | "toon" | "miniatura" | "acuarela" | "voxel";

/** colores tomados de las fotos de referencia */
const BASE: Record<Mat, string> = {
  suelo: "#8f8577", cal: "#f4f1ea", piedra: "#d39a63", piedraAtrio: "#b86e4f", pisoAtrio: "#c9b49a",
  teja: "#c8603f", balaustre: "#6f9c94", hierro: "#2f3b33", vano: "#3a3f4a", madera: "#6a3d2a",
  asfalto: "#5d5e63", linea: "#e8e2d0", acera: "#b9b3a8", baldosa: "#a3968c", baldosa2: "#6c6f78",
  cesped: "#6fa04a", copa: "#5f8f3a", copa2: "#7aa847", copaRedonda: "#3f7a35", tronco: "#6b5240",
  troncoBlanco: "#f2f0ea", palmera: "#7a6248", flor1: "#d24b6a", flor2: "#9a6bd1", flor3: "#e9c64a",
  bronce: "#6b5a3a", monumento: "#d8d0c0", estatua: "#b07a55", reloj: "#fbf8ef", gob: "#dfe4ea",
  pizarra: "#8b96a3", cupula: "#e4e8ee",
};

export interface Estilo {
  id: EstiloId;
  numero: number;
  nombre: string;
  resumen: string;
  referencias: string;
  pros: string;
  contras: string;
  paleta: Record<Mat, string>;
  fondo: string;
  niebla?: [string, number, number];
}

export const ESTILOS: Estilo[] = [
  {
    id: "lowpoly",
    numero: 1,
    nombre: "Low-poly facetado",
    resumen: "Caras planas visibles, pocas formas y colores cálidos y saturados, con luz de atardecer.",
    referencias: "Monument Valley, Alto's Adventure, ilustraciones low-poly de viajes",
    pros: "El más liviano: corre en cualquier celular y es el más rápido de producir en Blender.",
    contras: "Los ornamentos barrocos se simplifican mucho.",
    paleta: {
      ...BASE, cal: "#fff3df", piedra: "#f0a35e", piedraAtrio: "#d4664a", pisoAtrio: "#e6c39a", teja: "#e4572e",
      balaustre: "#45b0a5", cesped: "#a6cf5b", copa: "#4fa64a", copa2: "#8cc152", copaRedonda: "#2f8f55",
      asfalto: "#6a6478", acera: "#d8c7b4", baldosa: "#c7a993", baldosa2: "#8e7f9a", flor1: "#ff5f86",
      flor2: "#a57cff", flor3: "#ffcf3f", suelo: "#a77b5a", gob: "#f6e7d6", pizarra: "#7d7aa0", estatua: "#c97d4e",
    },
    fondo: "#ffcf9e",
    niebla: ["#ffcf9e", 90, 260],
  },
  {
    id: "toon",
    numero: 2,
    nombre: "Dibujo animado (cel shading)",
    resumen: "Sombras en tres bandas planas y contorno de tinta, como una película animada.",
    referencias: "Zelda: Wind Waker y Breath of the Wild, fondos de Studio Ghibli, Genshin Impact",
    pros: "Muy legible; la tinta destaca los ornamentos sin modelarlos al detalle.",
    contras: "El contorno es un posproceso: cuesta algo de rendimiento en celulares viejos.",
    paleta: {
      ...BASE, cal: "#fffaf0", piedra: "#f2b27c", piedraAtrio: "#d9785a", teja: "#ef6a45", balaustre: "#5cc2b4",
      cesped: "#7fcf55", copa: "#4cb04a", copa2: "#86d24f", copaRedonda: "#2e9e57", asfalto: "#5f6f86",
      baldosa: "#c9b6a6", baldosa2: "#7f8aa3", flor1: "#ff4f7b", flor2: "#b07cff", flor3: "#ffd23f",
      suelo: "#7e6a5a", gob: "#eef3fb", pizarra: "#6f86b3",
    },
    fondo: "#8fd3ff",
  },
  {
    id: "miniatura",
    numero: 3,
    nombre: "Maqueta / miniatura",
    resumen: "Volúmenes redondeados como de resina, luz suave de estudio, base de madera y desenfoque tilt-shift.",
    referencias: "Tiny Glade, dioramas y maquetas de museo, fotografía tilt-shift",
    pros: "Se lee como una maqueta de museo: ideal para la parte educativa.",
    contras: "La oclusión ambiental y el desenfoque son los efectos más pesados de los cinco.",
    paleta: {
      ...BASE, cal: "#f5efe4", piedra: "#e2b38a", piedraAtrio: "#cf8e72", pisoAtrio: "#ddcab2", teja: "#d77e5e",
      balaustre: "#8fb8ad", cesped: "#a8c98a", copa: "#86b071", copa2: "#a3c47e", copaRedonda: "#6f9e66",
      asfalto: "#8d8c92", acera: "#d7d0c4", baldosa: "#c8bbb0", baldosa2: "#9a9ca6", flor1: "#e88a9f",
      flor2: "#b9a0dc", flor3: "#f0d27a", suelo: "#8a6440", hierro: "#4a5550", troncoBlanco: "#f7f4ee",
    },
    fondo: "#e9e3d8",
  },
  {
    id: "acuarela",
    numero: 4,
    nombre: "Acuarela / ilustración",
    resumen: "Papel, pigmento granulado, colores lavados y bordes de tinta temblorosos, como un libro ilustrado.",
    referencias: "Guías de viaje dibujadas a mano, Okami, ilustración de libros de historia",
    pros: "Identidad única y muy ligada a patrimonio e historia.",
    contras: "Se lee peor a distancia; usa un shader propio que hay que mantener.",
    paleta: {
      ...BASE, cal: "#f7f1e3", piedra: "#d9a272", piedraAtrio: "#c27a5c", teja: "#cf6d4c", balaustre: "#7fa9a0",
      cesped: "#93b86a", copa: "#6f9d4f", copa2: "#9cbf63", copaRedonda: "#5b8a4d", asfalto: "#8a8790",
      baldosa: "#b9a99a", baldosa2: "#8b8d9a", suelo: "#a39580",
    },
    fondo: "#f3ecdc",
  },
  {
    id: "voxel",
    numero: 5,
    nombre: "Vóxel / bloques",
    resumen: "Todo construido con cubos de 40 cm, como bloques de construcción.",
    referencias: "Minecraft, Crossy Road, Teardown",
    pros: "Muy atractivo para estudiantes; se presta a actividades de construir la ciudad bloque a bloque.",
    contras: "Los detalles finos se pierden y la ciudad completa tiene muchísimos cubos.",
    paleta: {
      ...BASE, cal: "#eeeae0", piedra: "#d8914f", piedraAtrio: "#b8573d", teja: "#d65a35", balaustre: "#3fa39a",
      cesped: "#6cbf3c", copa: "#3f9a34", copa2: "#69b83a", copaRedonda: "#2f7f2f", asfalto: "#55565c",
      flor1: "#e8365d", flor2: "#9152e0", flor3: "#f5c518", baldosa: "#a69488", suelo: "#7a5a3c",
    },
    fondo: "#9fd8ff",
    niebla: ["#9fd8ff", 120, 300],
  },
];

export const estiloPorId = (id: string) => ESTILOS.find((e) => e.id === id) ?? ESTILOS[0];
