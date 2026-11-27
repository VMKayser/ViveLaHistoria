// Cambia la pintura de una instancia sin alterar ruedas, clips ni otras instancias.
const pinturasPorModelo = new WeakMap();

export function aplicarVariante(modelo, id, variantes) {
  const paleta = variantes[id];
  if (!paleta) throw new RangeError(`Color desconocido: ${id}`);
  let pinturas = pinturasPorModelo.get(modelo);
  if (!pinturas) {
    pinturas = new Map();
    const clones = new Map();
    const nombres = new Map();
    for (const v of Object.values(variantes)) for (const k of ['principal', 'detalle'])
      nombres.set(`pintura_acento__${v[k].slice(1)}`, k);
    modelo.traverse(o => {
      if (!o.isMesh) return;
      const reemplazar = material => {
        const k = material.userData.pintura_bronco || nombres.get(material.name);
        if (!k) return material;
        if (!clones.has(material)) {
          const clon = material.clone();
          clon.userData.pintura_bronco = k;
          clones.set(material, clon); pinturas.set(clon, k);
        }
        return clones.get(material);
      };
      o.material = Array.isArray(o.material) ? o.material.map(reemplazar) : reemplazar(o.material);
    });
    if (pinturas.size !== 2) throw new Error('No se identifican las dos pinturas del autobús');
    pinturasPorModelo.set(modelo, pinturas);
  }
  for (const [material, k] of pinturas) {
    material.color.set(paleta[k]);
    material.name = `pintura_acento__${paleta[k].slice(1)}`;
  }
  const raiz = modelo.getObjectByName('autobus_bronco');
  if (raiz) raiz.userData.variante = id;
  return id;
}
