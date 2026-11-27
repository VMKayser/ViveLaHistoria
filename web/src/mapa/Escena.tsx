"use client";

import { memo, Suspense, useCallback, useEffect, useLayoutEffect, useMemo, useRef, useState } from "react";
import * as THREE from "three";
import { Canvas, useFrame, useThree, type ThreeEvent } from "@react-three/fiber";
import { Bvh, Line, MapControls, useGLTF } from "@react-three/drei";
import type { Calle, FotoIndice, LugarOSM, Ubicaciones } from "./tipos";
import { LineSegments2 } from "three/examples/jsm/lines/LineSegments2.js";
import { LineSegmentsGeometry } from "three/examples/jsm/lines/LineSegmentsGeometry.js";
import { LineMaterial } from "three/examples/jsm/lines/LineMaterial.js";
import { aWeb, rumbo as calcRumbo } from "./geo";

export type Modo = "mano" | "marcar";
export type PuntoMapa = { x: number; y: number; z: number };

const COLORES: Record<string, string> = {
  TERRAIN: "#bcc39d",
  BUILDINGS_OTHER: "#f6f1e8",
  BUILDINGS_RESIDENTIAL: "#f6e7d3",
  BUILDINGS_COMMERCIAL: "#f3dccb",
  BUILDINGS_PUBLIC: "#efe2b8",
  BUILDINGS_INDUSTRIAL: "#e2ddd6",
  BUILDINGS_UTILITY: "#e2ddd6",
  TREES: "#86ad6f",
  WATER: "#8fb8d8",
  BRIDGES: "#b9b2a6",
};

const COLOR_VIA: Record<string, string> = {
  primary: "#c2571a",
  trunk: "#c2571a",
  secondary: "#d07a2a",
  tertiary: "#d89a3f",
  pedestrian: "#7a6ad0",
  footway: "#9a8fd6",
  steps: "#9a8fd6",
  path: "#9a8fd6",
};
const COLOR_VIA_DEF = "#8c7f6c";

const RE_NOMBRES =
  /historic|tourism=(museum|attraction|viewpoint|artwork|gallery)|place_of_worship|leisure=park|amenity=(townhall|university|college|marketplace|theatre|arts_centre|hospital)|place=(neighbourhood|suburb|square)/;

/** Fondo para el modelo del lienzo, con materiales planos por tipo. */
function Lienzo(props: {
  objeto: React.RefObject<THREE.Object3D | null>;
  onMover: (p: PuntoMapa) => void;
  onBajar: (p: PuntoMapa, e: ThreeEvent<PointerEvent>) => void;
}) {
  const { scene } = useGLTF("/mapa/lienzo.glb");
  useMemo(() => {
    scene.traverse((o) => {
      const m = o as THREE.Mesh;
      if (!m.isMesh) return;
      const nombre = (Array.isArray(m.material) ? m.material[0] : m.material)?.name ?? "";
      m.material = new THREE.MeshLambertMaterial({ color: COLORES[nombre] ?? "#e8e2d6", flatShading: true });
    });
  }, [scene]);
  useEffect(() => {
    props.objeto.current = scene;
  }, [scene, props.objeto]);

  const aMapa = (p: THREE.Vector3): PuntoMapa => ({ x: p.x, y: -p.z, z: p.y });
  return (
    <primitive
      object={scene}
      onPointerMove={(e: ThreeEvent<PointerEvent>) => props.onMover(aMapa(e.point))}
      onPointerDown={(e: ThreeEvent<PointerEvent>) => props.onBajar(aMapa(e.point), e)}
    />
  );
}

function Calles({ calles }: { calles: Calle[] }) {
  const linea = useMemo(() => {
    const pos: number[] = [];
    const col: number[] = [];
    const c = new THREE.Color();
    for (const calle of calles) {
      c.set(COLOR_VIA[calle.tipo] ?? COLOR_VIA_DEF);
      for (let i = 1; i < calle.puntos.length; i++) {
        const [ax, ay, az] = calle.puntos[i - 1],
          [bx, by, bz] = calle.puntos[i];
        pos.push(...aWeb(ax, ay, az), ...aWeb(bx, by, bz));
        col.push(c.r, c.g, c.b, c.r, c.g, c.b);
      }
    }
    const g = new LineSegmentsGeometry();
    g.setPositions(pos);
    g.setColors(col);
    // grosor en píxeles, igual a cualquier zoom
    const m = new LineMaterial({ vertexColors: true, linewidth: 2.5, transparent: true, opacity: 0.9 });
    const l = new LineSegments2(g, m);
    l.raycast = () => {};
    return l;
  }, [calles]);
  return <primitive object={linea} />;
}

function Flecha({ x, y, z, grados, color }: { x: number; y: number; z: number; grados: number; color: string }) {
  const r = (grados * Math.PI) / 180;
  const dx = Math.sin(r),
    dy = Math.cos(r);
  const L = 20;
  const fin: [number, number] = [x + dx * L, y + dy * L];
  const ala = (s: number): [number, number, number] => {
    const a = r + Math.PI + s * 0.45;
    return aWeb(fin[0] + Math.sin(a) * 4, fin[1] + Math.cos(a) * 4, z + 2);
  };
  return (
    <Line
      points={[aWeb(x, y, z + 2), aWeb(fin[0], fin[1], z + 2), ala(1), aWeb(fin[0], fin[1], z + 2), ala(-1)]}
      color={color}
      lineWidth={3}
      depthTest={false}
    />
  );
}

type Rayo = (clientX: number, clientY: number) => PuntoMapa | null;
type Controles = { enabled: boolean } | null;

/** Expone fuera del Canvas un raycast de pantalla -> punto del mapa, y los controles de cámara. */
function Rayador(props: {
  objeto: React.RefObject<THREE.Object3D | null>;
  rayo: React.RefObject<Rayo | null>;
  controles: React.RefObject<Controles>;
}) {
  const { camera, gl, controls } = useThree();
  useEffect(() => {
    const rc = Object.assign(new THREE.Raycaster(), { firstHitOnly: true });
    const v = new THREE.Vector2();
    props.rayo.current = (cx, cy) => {
      const r = gl.domElement.getBoundingClientRect();
      v.set(((cx - r.left) / r.width) * 2 - 1, -((cy - r.top) / r.height) * 2 + 1);
      rc.setFromCamera(v, camera);
      const hit = props.objeto.current ? rc.intersectObject(props.objeto.current, true)[0] : undefined;
      return hit ? { x: hit.point.x, y: -hit.point.z, z: hit.point.y } : null;
    };
    props.controles.current = controls as unknown as Controles;
  }, [camera, gl, controls, props.objeto, props.rayo, props.controles]);
  return null;
}

type Capa = React.RefObject<Map<HTMLElement, [number, number, number]>>;

/**
 * Capa HTML propia sobre el canvas (en vez de <Html> de drei, que crea una raíz React por marcador):
 * cada frame proyecta la posición 3D de cada elemento registrado y lo mueve con transform.
 */
function Proyector({ capa }: { capa: Capa }) {
  const v = useMemo(() => new THREE.Vector3(), []);
  useFrame(({ camera, size }) => {
    for (const [el, [x, y, z]] of capa.current) {
      v.set(x, y, z).project(camera);
      if (v.z > 1) {
        el.style.visibility = "hidden";
        continue;
      }
      el.style.visibility = "";
      el.style.transform = `translate(${((v.x + 1) / 2) * size.width}px, ${((1 - v.y) / 2) * size.height}px)`;
    }
  });
  return null;
}

function Anclado(props: { capa: Capa; pos: [number, number, number]; z: number; children: React.ReactNode }) {
  const ref = useRef<HTMLDivElement>(null);
  const { capa } = props;
  const [x, y, z] = props.pos;
  useLayoutEffect(() => {
    const el = ref.current;
    if (!el) return;
    const mapa = capa.current;
    mapa.set(el, [x, y, z]);
    return () => {
      mapa.delete(el);
    };
  }, [capa, x, y, z]);
  return (
    <div ref={ref} className="absolute left-0 top-0" style={{ zIndex: props.z, visibility: "hidden" }}>
      <div className="-translate-x-1/2 -translate-y-1/2">{props.children}</div>
    </div>
  );
}

/** Un punto por foto. Se arrastra para moverlo; un clic abre la foto. */
function PuntoFoto(props: {
  archivo: string;
  web: string;
  pos: [number, number, number];
  desfase: [number, number];
  estado: "manual" | "gps-ok" | "gps";
  activo: boolean;
  capa: Capa;
  onArrastre: (archivo: string, e: PointerEvent) => void;
}) {
  const ref = useRef<HTMLButtonElement>(null);
  const { archivo, onArrastre } = props;
  useEffect(() => {
    const b = ref.current;
    if (!b) return;
    // escucha nativa: así el evento no llega a los controles de cámara (que escuchan en el contenedor)
    const bajar = (e: PointerEvent) => {
      if (e.button !== 0) return;
      e.stopPropagation();
      e.preventDefault();
      onArrastre(archivo, e);
    };
    b.addEventListener("pointerdown", bajar);
    return () => b.removeEventListener("pointerdown", bajar);
  }, [archivo, onArrastre]);

  const color = props.activo
    ? "bg-red-600 h-4 w-4"
    : props.estado === "gps"
      ? "bg-slate-500/90 hover:bg-slate-700 h-3.5 w-3.5"
      : props.estado === "gps-ok"
        ? "bg-amber-500 hover:bg-amber-400 h-3.5 w-3.5"
        : "bg-amber-700 hover:bg-amber-600 h-3.5 w-3.5";
  return (
    <Anclado capa={props.capa} pos={props.pos} z={props.activo ? 30 : props.estado === "gps" ? 10 : 20}>
      <div className="group pointer-events-auto relative" style={{ transform: `translate(${props.desfase[0]}px, ${props.desfase[1]}px)` }}>
        <button
          ref={ref}
          title={archivo}
          className={`block cursor-grab touch-none rounded-full border-2 border-white shadow-md active:cursor-grabbing ${color}`}
        />
        <span className="pointer-events-none absolute bottom-5 left-1/2 hidden -translate-x-1/2 overflow-hidden rounded border-2 border-white bg-white shadow-lg group-hover:block">
          {/* eslint-disable-next-line @next/next/no-img-element */}
          <img src={`/fotos/mini/${props.web}`} alt="" loading="lazy" className="block h-[90px] w-[120px] max-w-none object-cover" />
        </span>
      </div>
    </Anclado>
  );
}

type Props = {
  calles: Calle[];
  lugares: LugarOSM[];
  fotos: FotoIndice[];
  ubicaciones: Ubicaciones;
  modo: Modo;
  verGPS: boolean;
  verNombres: boolean;
  seleccion: string[];
  inicio: [number, number];
  onHover: (p: PuntoMapa | null) => void;
  onMarcar: (p: PuntoMapa, rumbo: number | null) => void;
  onFoto: (archivo: string) => void;
  onSoltar: (archivo: string, p: PuntoMapa) => void;
};

function Escena(props: Props) {
  const { ubicaciones, fotos, modo, seleccion } = props;
  const arrastre = useRef<PuntoMapa | null>(null);
  const ultimo = useRef<PuntoMapa | null>(null);
  const [vista, setVista] = useState<{ a: PuntoMapa; b: PuntoMapa } | null>(null);

  const nombres = useMemo(() => props.lugares.filter((l) => RE_NOMBRES.test(l.tipo)), [props.lugares]);

  // Altura del terreno aproximada para los puntos GPS: la del lugar o calle conocido más cercano
  const alturaCerca = useMemo(() => {
    const pts = props.calles.flatMap((c) => c.puntos.filter((_, i) => i % 4 === 0));
    return (x: number, y: number) => {
      let mejor = 0,
        d = Infinity;
      for (const [px, py, pz] of pts) {
        const dd = (px - x) ** 2 + (py - y) ** 2;
        if (dd < d) {
          d = dd;
          mejor = pz;
        }
      }
      return mejor;
    };
  }, [props.calles]);

  const objeto = useRef<THREE.Object3D | null>(null);
  const rayo = useRef<Rayo | null>(null);
  const controles = useRef<Controles>(null);
  const [arrastrado, setArrastrado] = useState<{ archivo: string; p: PuntoMapa } | null>(null);

  // Un punto por foto: las ubicadas en su sitio y, si no, en su posición GPS
  const puntos = useMemo(() => {
    const lista: {
      archivo: string;
      web: string;
      x: number;
      y: number;
      z: number;
      rumbo: number | null;
      estado: "manual" | "gps-ok" | "gps";
    }[] = [];
    for (const f of fotos) {
      const u = ubicaciones[f.archivo];
      if (u)
        lista.push({
          archivo: f.archivo,
          web: f.web,
          x: u.x,
          y: u.y,
          z: u.z,
          rumbo: u.rumbo,
          estado: u.origen === "gps" ? "gps-ok" : "manual",
        });
      else if (f.gps)
        lista.push({
          archivo: f.archivo,
          web: f.web,
          x: f.gps.x,
          y: f.gps.y,
          z: alturaCerca(f.gps.x, f.gps.y) - 0.6,
          rumbo: null,
          estado: "gps",
        });
    }
    // Las fotos en la misma posición se abren en abanico (en píxeles) para poder agarrar cada una
    const porSitio = new Map<string, number[]>();
    lista.forEach((p, i) => {
      const k = `${Math.round(p.x)},${Math.round(p.y)}`;
      porSitio.set(k, [...(porSitio.get(k) ?? []), i]);
    });
    const desfases = new Map<string, [number, number]>();
    for (const idx of porSitio.values()) {
      const n = idx.length;
      idx.forEach((i, j) => {
        const ang = (j / n) * Math.PI * 2 - Math.PI / 2;
        const rad = n === 1 ? 0 : 9 + n * 1.6;
        desfases.set(lista[i].archivo, [Math.cos(ang) * rad, Math.sin(ang) * rad]);
      });
    }
    return lista.map((p) => ({ ...p, desfase: desfases.get(p.archivo) ?? ([0, 0] as [number, number]) }));
  }, [fotos, ubicaciones, alturaCerca]);

  const { onFoto, onSoltar, onHover } = props;
  const onArrastre = useCallback(
    (archivo: string, e0: PointerEvent) => {
      let movido = false;
      let ultimoP: PuntoMapa | null = null;
      const mover = (e: PointerEvent) => {
        if (!movido && Math.hypot(e.clientX - e0.clientX, e.clientY - e0.clientY) < 4) return;
        movido = true;
        if (controles.current) controles.current.enabled = false;
        const p = rayo.current?.(e.clientX, e.clientY);
        if (p) {
          ultimoP = p;
          setArrastrado({ archivo, p });
          onHover(p);
        }
      };
      const soltar = () => {
        window.removeEventListener("pointermove", mover);
        window.removeEventListener("pointerup", soltar);
        if (controles.current) controles.current.enabled = true;
        if (movido && ultimoP) onSoltar(archivo, ultimoP);
        else if (!movido) onFoto(archivo);
        setArrastrado(null);
      };
      window.addEventListener("pointermove", mover);
      window.addEventListener("pointerup", soltar);
    },
    [onFoto, onSoltar, onHover],
  );

  // Soltar el botón en cualquier parte termina el marcado
  const { onMarcar } = props;
  useEffect(() => {
    const fin = () => {
      const a = arrastre.current;
      if (!a) return;
      arrastre.current = null;
      setVista(null);
      const b = ultimo.current;
      const d = b ? Math.hypot(b.x - a.x, b.y - a.y) : 0;
      onMarcar(a, b && d > 3 ? calcRumbo(b.x - a.x, b.y - a.y) : null);
    };
    window.addEventListener("pointerup", fin);
    return () => window.removeEventListener("pointerup", fin);
  }, [onMarcar]);

  const capa = useRef(new Map<HTMLElement, [number, number, number]>());
  const sel = new Set(seleccion);
  const [ix, iy] = props.inicio;
  const objetivo = aWeb(ix, iy, 60);

  return (
    <div className="relative h-full w-full">
      <Canvas
        camera={{ position: [objetivo[0], 520, objetivo[2] + 330], fov: 45, near: 1, far: 8000 }}
        onPointerLeave={() => onHover(null)}
      >
        <color attach="background" args={["#cfe3ef"]} />
        <hemisphereLight args={["#ffffff", "#8f8068", 1.3]} />
        <directionalLight position={[500, 700, 250]} intensity={2.2} />
        <MapControls
          makeDefault
          target={objetivo}
          maxPolarAngle={Math.PI / 2.15}
          minDistance={15}
          maxDistance={2600}
          screenSpacePanning={false}
          // En modo marcar el clic izquierdo pone puntos: se mueve con botón derecho (girar) y central (desplazar)
          mouseButtons={
            modo === "mano"
              ? { LEFT: THREE.MOUSE.PAN, MIDDLE: THREE.MOUSE.DOLLY, RIGHT: THREE.MOUSE.ROTATE }
              : { LEFT: -1 as THREE.MOUSE, MIDDLE: THREE.MOUSE.PAN, RIGHT: THREE.MOUSE.ROTATE }
          }
        />

        <Suspense fallback={null}>
          <Bvh firstHitOnly>
            <Lienzo
              objeto={objeto}
              onMover={(p) => {
                ultimo.current = p;
                onHover(p);
                if (arrastre.current) setVista({ a: arrastre.current, b: p });
              }}
              onBajar={(p, e) => {
                if (modo !== "marcar" || e.button !== 0) return;
                e.stopPropagation();
                arrastre.current = p;
                ultimo.current = p;
              }}
            />
          </Bvh>
        </Suspense>
        <Calles calles={props.calles} />
        <Rayador objeto={objeto} rayo={rayo} controles={controles} />
        <Proyector capa={capa} />

        {vista && Math.hypot(vista.b.x - vista.a.x, vista.b.y - vista.a.y) > 3 && (
          <Flecha {...vista.a} grados={calcRumbo(vista.b.x - vista.a.x, vista.b.y - vista.a.y)} color="#dc2626" />
        )}

        {puntos.map((p) => {
          if (p.rumbo == null || (p.estado === "gps" && !props.verGPS)) return null;
          const d = arrastrado?.archivo === p.archivo ? arrastrado.p : null;
          const activo = sel.has(p.archivo) || !!d;
          return (
            <Flecha
              key={p.archivo}
              x={d?.x ?? p.x}
              y={d?.y ?? p.y}
              z={d?.z ?? p.z}
              grados={p.rumbo}
              color={activo ? "#dc2626" : "#b45309"}
            />
          );
        })}
      </Canvas>
      <div className="pointer-events-none absolute inset-0 overflow-hidden">
        {puntos.map((p) => {
          if (p.estado === "gps" && !props.verGPS && arrastrado?.archivo !== p.archivo) return null;
          const d = arrastrado?.archivo === p.archivo ? arrastrado.p : null;
          const activo = sel.has(p.archivo) || !!d;
          const x = d?.x ?? p.x,
            y = d?.y ?? p.y,
            z = d?.z ?? p.z;
          return (
            <PuntoFoto
              key={p.archivo}
              capa={capa}
              archivo={p.archivo}
              web={p.web}
              pos={aWeb(x, y, z + 2)}
              desfase={d ? [0, 0] : p.desfase}
              estado={p.estado}
              activo={activo}
              onArrastre={onArrastre}
            />
          );
        })}

        {props.verNombres &&
          nombres.map((l, i) => (
            <Anclado key={`n${i}`} capa={capa} pos={aWeb(l.x, l.y, l.z + 12)} z={1}>
              <span className="whitespace-nowrap rounded bg-white/75 px-1 text-[10px] text-stone-700">{l.nombre}</span>
            </Anclado>
          ))}
      </div>
    </div>
  );
}

export default memo(Escena);
