"use client";

import { Suspense, useEffect, useState } from "react";
import { Canvas } from "@react-three/fiber";
import {
  Html,
  MapControls,
  Sky,
  useGLTF,
  ContactShadows,
} from "@react-three/drei";
import lugares from "@/data/lugares.json";

export type Lugar = (typeof lugares)[number];

const MODELO = "/models/piloto.glb";

function Modelo() {
  const { scene } = useGLTF(MODELO);
  return <primitive object={scene} />;
}

// Se muestra mientras no exista /models/piloto.glb
function Placeholder() {
  return (
    <group>
      <mesh rotation-x={-Math.PI / 2} receiveShadow>
        <planeGeometry args={[120, 120]} />
        <meshStandardMaterial color="#b7c99a" />
      </mesh>
      {[
        [0, 6, -18, 14, 12, 10, "#e8d8b8"],
        [22, 4, 4, 10, 8, 14, "#f0c9a0"],
        [-22, 3, 4, 10, 6, 14, "#d9b38c"],
      ].map(([x, y, z, w, h, d, c], i) => (
        <mesh key={i} position={[+x, +y, +z]} castShadow>
          <boxGeometry args={[+w, +h, +d]} />
          <meshStandardMaterial color={c as string} />
        </mesh>
      ))}
    </group>
  );
}

function Marcador({ lugar, activo, onSelect }: { lugar: Lugar; activo: boolean; onSelect: (l: Lugar) => void }) {
  return (
    <Html position={lugar.posicion as [number, number, number]} center zIndexRange={[100, 10]}>
      <button
        onClick={() => onSelect(lugar)}
        className={`whitespace-nowrap rounded-full px-3 py-1 text-xs font-semibold shadow-md transition ${
          activo ? "bg-amber-500 text-white" : "bg-white/90 text-stone-800 hover:bg-amber-100"
        }`}
      >
        {lugar.nombre}
      </button>
    </Html>
  );
}

export default function CityScene({
  seleccionado,
  onSelect,
}: {
  seleccionado: Lugar | null;
  onSelect: (l: Lugar) => void;
}) {
  const [hayModelo, setHayModelo] = useState<boolean | null>(null);

  useEffect(() => {
    fetch(MODELO, { method: "HEAD" })
      .then((r) => setHayModelo(r.ok))
      .catch(() => setHayModelo(false));
  }, []);

  return (
    <Canvas shadows camera={{ position: [60, 50, 60], fov: 40 }} dpr={[1, 2]}>
      <color attach="background" args={["#cfe8f5"]} />
      <Sky sunPosition={[100, 60, 50]} />
      <hemisphereLight args={["#ffffff", "#8a9a6a", 0.6]} />
      <directionalLight position={[50, 80, 30]} intensity={1.6} castShadow shadow-mapSize={[2048, 2048]}>
        <orthographicCamera attach="shadow-camera" args={[-80, 80, 80, -80, 1, 250]} />
      </directionalLight>

      <Suspense fallback={null}>
        {hayModelo === true && <Modelo />}
        {hayModelo === false && <Placeholder />}
        {hayModelo !== null &&
          lugares.map((l) => (
            <Marcador key={l.id} lugar={l} activo={seleccionado?.id === l.id} onSelect={onSelect} />
          ))}
      </Suspense>
      <ContactShadows position={[0, 0.01, 0]} scale={150} opacity={0.35} blur={2} far={30} />

      <MapControls makeDefault maxPolarAngle={Math.PI / 2.3} minDistance={10} maxDistance={250} />
    </Canvas>
  );
}
