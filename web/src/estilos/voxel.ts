import { Euler, Matrix4, Quaternion, Vector3 } from "three";
import { LIMITES, type Mat, type Prim } from "./escena";

export interface Voxeles {
  tam: number;
  posiciones: Float32Array;
  mats: Mat[];
}

/** Convierte las primitivas en cubos de `tam` metros y deja solo los que tienen una cara a la vista. */
export function voxelizar(prims: readonly Prim[], tam: number): Voxeles {
  const [x0, x1] = LIMITES.x, [y0, y1] = LIMITES.y, [z0, z1] = LIMITES.z;
  const nx = Math.ceil((x1 - x0) / tam), ny = Math.ceil((y1 - y0) / tam), nz = Math.ceil((z1 - z0) / tam);
  const grid = new Uint8Array(nx * ny * nz);
  const idx = (i: number, j: number, k: number) => (i * ny + j) * nz + k;
  const lista: Mat[] = [];
  const inv = new Matrix4(), m = new Matrix4(), q = new Quaternion(), v = new Vector3();
  const uno = new Vector3(1, 1, 1);

  for (const p of prims) {
    let mi = lista.indexOf(p.m);
    if (mi < 0) mi = lista.push(p.m) - 1;
    q.setFromEuler(new Euler(...(p.r ?? [0, 0, 0])));
    m.compose(v.set(...p.p), q, uno);
    inv.copy(m).invert();
    const minimo = tam * 0.72; // así un objeto fino siempre alcanza el centro de algún cubo
    const hx = Math.max(p.s[0] / 2, minimo), hy = Math.max(p.s[1] / 2, minimo), hz = Math.max(p.s[2] / 2, minimo);
    let mnx = Infinity, mny = Infinity, mnz = Infinity, mxx = -Infinity, mxy = -Infinity, mxz = -Infinity;
    for (const sx of [-1, 1]) for (const sy of [-1, 1]) for (const sz of [-1, 1]) {
      v.set(sx * hx, sy * hy, sz * hz).applyMatrix4(m);
      mnx = Math.min(mnx, v.x); mny = Math.min(mny, v.y); mnz = Math.min(mnz, v.z);
      mxx = Math.max(mxx, v.x); mxy = Math.max(mxy, v.y); mxz = Math.max(mxz, v.z);
    }
    const e = inv.elements;
    const i0 = Math.max(0, Math.ceil((mnx - x0) / tam - 0.5)), i1 = Math.min(nx - 1, Math.floor((mxx - x0) / tam - 0.5));
    const j0 = Math.max(0, Math.ceil((mny - y0) / tam - 0.5)), j1 = Math.min(ny - 1, Math.floor((mxy - y0) / tam - 0.5));
    const k0 = Math.max(0, Math.ceil((mnz - z0) / tam - 0.5)), k1 = Math.min(nz - 1, Math.floor((mxz - z0) / tam - 0.5));
    for (let i = i0; i <= i1; i++) {
      const wx = x0 + (i + 0.5) * tam;
      for (let j = j0; j <= j1; j++) {
        const wy = y0 + (j + 0.5) * tam;
        for (let k = k0; k <= k1; k++) {
          const wz = z0 + (k + 0.5) * tam;
          const lx = (e[0] * wx + e[4] * wy + e[8] * wz + e[12]) / hx;
          const ly = (e[1] * wx + e[5] * wy + e[9] * wz + e[13]) / hy;
          const lz = (e[2] * wx + e[6] * wy + e[10] * wz + e[14]) / hz;
          let dentro: boolean;
          if (p.t === "caja") dentro = Math.abs(lx) <= 1 && Math.abs(ly) <= 1 && Math.abs(lz) <= 1;
          else if (p.t === "cil") dentro = Math.abs(ly) <= 1 && lx * lx + lz * lz <= 1;
          else if (p.t === "esfera") dentro = lx * lx + ly * ly + lz * lz <= 1;
          else {
            const f = (1 - ly) / 2;
            dentro = Math.abs(ly) <= 1 && (p.seg === 4 ? Math.abs(lx) + Math.abs(lz) <= f : lx * lx + lz * lz <= f * f);
          }
          if (dentro) grid[idx(i, j, k)] = mi + 1;
        }
      }
    }
  }

  const pos: number[] = [];
  const mats: Mat[] = [];
  const vacio = (i: number, j: number, k: number) =>
    i < 0 || j < 0 || k < 0 || i >= nx || j >= ny || k >= nz || grid[idx(i, j, k)] === 0;
  for (let i = 0; i < nx; i++) for (let j = 0; j < ny; j++) for (let k = 0; k < nz; k++) {
    const g = grid[idx(i, j, k)];
    if (!g) continue;
    if (j === 0) continue; // la cara inferior del terreno nunca se ve
    if (vacio(i + 1, j, k) || vacio(i - 1, j, k) || vacio(i, j + 1, k) || vacio(i, j - 1, k) || vacio(i, j, k + 1) || vacio(i, j, k - 1)) {
      pos.push(x0 + (i + 0.5) * tam, y0 + (j + 0.5) * tam, z0 + (k + 0.5) * tam);
      mats.push(lista[g - 1]);
    }
  }
  return { tam, posiciones: new Float32Array(pos), mats };
}
