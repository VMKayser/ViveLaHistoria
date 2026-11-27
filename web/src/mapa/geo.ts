// Conversión lat/lon <-> metros del lienzo urban-export. Mismas constantes que blender/scripts/geo.py.
// Mapa (Blender): X = este, Y = norte, Z = altura. Web (three): (x, z, -y).

const LAT0 = -19.046;
const LON0 = -65.2578;
const R = 6378137;
const DX = 4.69;
const DY = 3.09;
const KX = (Math.PI / 180) * R * Math.cos((LAT0 * Math.PI) / 180);
const KY = (Math.PI / 180) * R;

export function aMetros(lat: number, lon: number): [number, number] {
  return [(lon - LON0) * KX + DX, (lat - LAT0) * KY + DY];
}

export function aLatLon(x: number, y: number): [number, number] {
  return [LAT0 + (y - DY) / KY, LON0 + (x - DX) / KX];
}

/** Punto del mapa (x este, y norte, z altura) -> posición three.js */
export function aWeb(x: number, y: number, z: number): [number, number, number] {
  return [x, z, -y];
}

/** Rumbo en grados (0 = norte, 90 = este) del vector (dx este, dy norte) */
export function rumbo(dx: number, dy: number): number {
  return ((Math.atan2(dx, dy) * 180) / Math.PI + 360) % 360;
}

export function nombreRumbo(g: number): string {
  return ["N", "NE", "E", "SE", "S", "SO", "O", "NO"][Math.round(g / 45) % 8];
}
