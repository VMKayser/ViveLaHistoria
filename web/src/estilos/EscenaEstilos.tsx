"use client";

import { useLayoutEffect, useMemo, useRef } from "react";
import { Canvas } from "@react-three/fiber";
import { OrbitControls } from "@react-three/drei";
import { EffectComposer, N8AO, TiltShift2, Vignette } from "@react-three/postprocessing";
import * as THREE from "three";
import { RoundedBoxGeometry } from "three/examples/jsm/geometries/RoundedBoxGeometry.js";
import { PRIMITIVAS, type Mat, type Prim } from "./escena";
import { type Estilo, type EstiloId } from "./estilos";
import { AcuarelaEffect, TintaEffect } from "./efectos";
import { voxelizar } from "./voxel";

// ---------------------------------------------------------------- geometrías

function hash3(x: number, y: number, z: number) {
  const s = Math.sin(x * 12.9898 + y * 78.233 + z * 37.719) * 43758.5453;
  return s - Math.floor(s);
}

const ORGANICOS: Mat[] = ["copa", "copa2", "copaRedonda"];

function geometria(estilo: EstiloId, p: Prim): THREE.BufferGeometry {
  const [sx, sy, sz] = p.s;
  const lowpoly = estilo === "lowpoly";
  const suave = estilo === "miniatura";
  let g: THREE.BufferGeometry;
  switch (p.t) {
    case "caja":
      if (suave) {
        const r = Math.min(0.22, Math.min(sx, sy, sz) * 0.3);
        return new RoundedBoxGeometry(sx, sy, sz, 3, r);
      }
      return new THREE.BoxGeometry(sx, sy, sz);
    case "cil": {
      const seg = p.seg === 4 ? 4 : lowpoly ? Math.min(p.seg ?? 7, 7) : Math.max(p.seg ?? 20, suave ? 24 : 16);
      g = new THREE.CylinderGeometry(0.5, 0.5, 1, seg);
      break;
    }
    case "cono": {
      const seg = p.seg === 4 ? 4 : lowpoly ? Math.min(p.seg ?? 6, 6) : Math.max(p.seg ?? 20, 16);
      g = new THREE.ConeGeometry(0.5, 1, seg);
      break;
    }
    case "esfera":
      if (lowpoly) {
        g = new THREE.IcosahedronGeometry(0.5, ORGANICOS.includes(p.m) ? 1 : 0);
        if (ORGANICOS.includes(p.m)) {
          // copa irregular: desplaza cada vértice según su posición (mantiene la malla cerrada)
          const a = g.attributes.position as THREE.BufferAttribute;
          for (let i = 0; i < a.count; i++) {
            const k = 0.85 + 0.3 * hash3(a.getX(i), a.getY(i), a.getZ(i));
            a.setXYZ(i, a.getX(i) * k, a.getY(i) * k, a.getZ(i) * k);
          }
        }
      } else g = new THREE.SphereGeometry(0.5, suave ? 32 : 24, suave ? 20 : 16);
      break;
  }
  g.scale(sx, sy, sz);
  g.computeVertexNormals();
  return g;
}

// ---------------------------------------------------------------- materiales

let gradiente: THREE.DataTexture | null = null;
function gradienteToon() {
  if (!gradiente) {
    gradiente = new THREE.DataTexture(new Uint8Array([90, 90, 90, 255, 175, 175, 175, 255, 255, 255, 255, 255]), 3, 1);
    gradiente.minFilter = gradiente.magFilter = THREE.NearestFilter;
    gradiente.needsUpdate = true;
  }
  return gradiente;
}

function material(estilo: Estilo, m: Mat): THREE.Material {
  const color = new THREE.Color(estilo.paleta[m]);
  switch (estilo.id) {
    case "lowpoly":
      return new THREE.MeshStandardMaterial({ color, flatShading: true, roughness: 0.9 });
    case "toon":
      return new THREE.MeshToonMaterial({ color, gradientMap: gradienteToon() });
    case "miniatura":
      return new THREE.MeshStandardMaterial({ color, roughness: m === "hierro" || m === "bronce" ? 0.45 : 0.75 });
    default:
      return new THREE.MeshLambertMaterial({ color });
  }
}

// ---------------------------------------------------------------- primitivas instanciadas

function Primitivas({ estilo }: { estilo: Estilo }) {
  const grupos = useMemo(() => {
    const mapa = new Map<string, { muestra: Prim; matrices: THREE.Matrix4[] }>();
    const q = new THREE.Quaternion(), uno = new THREE.Vector3(1, 1, 1);
    for (const p of PRIMITIVAS) {
      const clave = `${p.t}|${p.s.join(",")}|${p.seg ?? ""}|${p.m}`;
      let g = mapa.get(clave);
      if (!g) mapa.set(clave, (g = { muestra: p, matrices: [] }));
      q.setFromEuler(new THREE.Euler(...(p.r ?? [0, 0, 0])));
      g.matrices.push(new THREE.Matrix4().compose(new THREE.Vector3(...p.p), q, uno));
    }
    const mats = new Map<Mat, THREE.Material>();
    return [...mapa.values()].map(({ muestra, matrices }) => {
      if (!mats.has(muestra.m)) mats.set(muestra.m, material(estilo, muestra.m));
      return { geo: geometria(estilo.id, muestra), mat: mats.get(muestra.m)!, matrices };
    });
  }, [estilo]);

  return (
    <>
      {grupos.map((g, i) => (
        <Instancias key={i} {...g} />
      ))}
    </>
  );
}

function Instancias({ geo, mat, matrices }: { geo: THREE.BufferGeometry; mat: THREE.Material; matrices: THREE.Matrix4[] }) {
  const ref = useRef<THREE.InstancedMesh>(null!);
  useLayoutEffect(() => {
    matrices.forEach((m, i) => ref.current.setMatrixAt(i, m));
    ref.current.instanceMatrix.needsUpdate = true;
    ref.current.computeBoundingSphere();
  }, [matrices]);
  return <instancedMesh ref={ref} args={[geo, mat, matrices.length]} castShadow receiveShadow />;
}

// ---------------------------------------------------------------- vóxeles

function Voxeles({ estilo }: { estilo: Estilo }) {
  const datos = useMemo(() => voxelizar(PRIMITIVAS, 0.4), []);
  const ref = useRef<THREE.InstancedMesh>(null!);
  const n = datos.mats.length;
  useLayoutEffect(() => {
    const m = new THREE.Matrix4(), c = new THREE.Color();
    for (let i = 0; i < n; i++) {
      const [x, y, z] = [datos.posiciones[i * 3], datos.posiciones[i * 3 + 1], datos.posiciones[i * 3 + 2]];
      ref.current.setMatrixAt(i, m.makeTranslation(x, y, z));
      c.set(estilo.paleta[datos.mats[i]]).offsetHSL(0, 0, (hash3(x, y, z) - 0.5) * 0.07);
      ref.current.setColorAt(i, c);
    }
    ref.current.instanceMatrix.needsUpdate = true;
    if (ref.current.instanceColor) ref.current.instanceColor.needsUpdate = true;
    ref.current.computeBoundingSphere();
  }, [datos, estilo, n]);
  const geo = useMemo(() => new THREE.BoxGeometry(datos.tam, datos.tam, datos.tam), [datos.tam]);
  return (
    <instancedMesh ref={ref} args={[geo, undefined, n]} castShadow receiveShadow>
      <meshLambertMaterial />
    </instancedMesh>
  );
}

// ---------------------------------------------------------------- luces y efectos por estilo

function Luces({ id }: { id: EstiloId }) {
  const sol = {
    lowpoly: { color: "#ffe2b8", i: 2.6, cielo: "#ffe9cc", tierra: "#7a6a8a", hi: 1.0, pos: [55, 45, 70] },
    toon: { color: "#fff6e0", i: 2.4, cielo: "#e6f4ff", tierra: "#8a9a70", hi: 1.0, pos: [40, 70, 60] },
    miniatura: { color: "#fff1dc", i: 2.0, cielo: "#f4efe8", tierra: "#b9a68c", hi: 1.3, pos: [-30, 80, 60] },
    acuarela: { color: "#fff4e2", i: 1.7, cielo: "#f6efe0", tierra: "#c9bba0", hi: 1.5, pos: [40, 70, 55] },
    voxel: { color: "#fffaf0", i: 2.4, cielo: "#dff1ff", tierra: "#8b7a5a", hi: 1.0, pos: [45, 75, 55] },
  }[id];
  return (
    <>
      <hemisphereLight args={[sol.cielo, sol.tierra, sol.hi]} />
      <directionalLight
        position={sol.pos as [number, number, number]}
        color={sol.color}
        intensity={sol.i}
        castShadow
        shadow-mapSize={[4096, 4096]}
        shadow-bias={-0.0004}
        shadow-normalBias={0.04}
        shadow-radius={id === "miniatura" || id === "acuarela" ? 6 : 2}
      >
        <orthographicCamera attach="shadow-camera" args={[-95, 95, 95, -95, 1, 300]} />
      </directionalLight>
    </>
  );
}

function Efectos({ estilo }: { estilo: Estilo }) {
  const tinta = useMemo(() => new TintaEffect({ color: "#2b1f1a", grosor: 1.7, umbral: 0.02 }), []);
  const acuarela = useMemo(() => new AcuarelaEffect({ papel: estilo.fondo }), [estilo.fondo]);
  switch (estilo.id) {
    case "toon":
      return (
        <EffectComposer multisampling={4}>
          <primitive object={tinta} />
        </EffectComposer>
      );
    case "miniatura":
      return (
        <EffectComposer multisampling={4}>
          <N8AO aoRadius={2.5} intensity={2.5} distanceFalloff={1} />
          <TiltShift2 blur={0.22} taper={0.55} start={[0.5, 0.0]} end={[0.5, 1.0]} />
          <Vignette offset={0.25} darkness={0.45} />
        </EffectComposer>
      );
    case "acuarela":
      return (
        <EffectComposer multisampling={0}>
          <primitive object={acuarela} />
        </EffectComposer>
      );
    case "voxel":
      return (
        <EffectComposer multisampling={4}>
          <N8AO aoRadius={1.2} intensity={2} halfRes />
        </EffectComposer>
      );
    default:
      return (
        <EffectComposer multisampling={4}>
          <Vignette offset={0.3} darkness={0.35} />
        </EffectComposer>
      );
  }
}

// ---------------------------------------------------------------- escena

export default function EscenaEstilos({ estilo }: { estilo: Estilo }) {
  return (
    <Canvas
      key={estilo.id}
      shadows={estilo.id === "miniatura" || estilo.id === "acuarela" ? "soft" : true}
      dpr={[1, 2]}
      camera={{ position: [14, 36, 66], fov: 40, near: 0.5, far: 600 }}
      gl={{ antialias: false, preserveDrawingBuffer: true }}
    >
      <color attach="background" args={[estilo.fondo]} />
      {estilo.niebla && <fog attach="fog" args={estilo.niebla} />}
      <Luces id={estilo.id} />
      {estilo.id === "voxel" ? <Voxeles estilo={estilo} /> : <Primitivas estilo={estilo} />}
      <Efectos estilo={estilo} />
      <OrbitControls
        makeDefault
        target={[-5, 11, 0]}
        maxPolarAngle={Math.PI / 2.05}
        minDistance={8}
        maxDistance={180}
        enableDamping
      />
    </Canvas>
  );
}
