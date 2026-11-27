/* Recoloración de pintura por instancia sin alterar materiales compartidos, luces ni ruedas. */
const pinturasPorInstancia = new WeakMap();

export function aplicarVariante(modelo, id, variantes, opciones = {}) {
  const paleta = variantes[id];
  if (!paleta) throw new RangeError(`Variante desconocida: ${id}`);
  const rolMaterial = opciones.rolMaterial || 'muro';
  const ranuras = opciones.ranuras || Object.keys(paleta).filter(k => typeof paleta[k] === 'string' && paleta[k].startsWith('#'));

  let pinturas = pinturasPorInstancia.get(modelo);
  if (!pinturas) {
    pinturas = new Map();
    const clones = new Map();
    const nombresConocidos = new Map();
    for (const v of Object.values(variantes)) {
      for (const ranura of ranuras) {
        if (typeof v[ranura] === 'string' && v[ranura].startsWith('#')) {
          const hex = v[ranura].slice(1).toLowerCase();
          nombresConocidos.set(`${rolMaterial}__${hex}`, ranura);
          nombresConocidos.set(`pintura_acento__${hex}`, ranura);
          nombresConocidos.set(`metal__${hex}`, ranura);
        }
      }
    }
    modelo.traverse(o => {
      if (!o.isMesh || !o.material) return;
      const reemplazar = mat => {
        const ranura = mat.userData?.pintura_vehiculo || nombresConocidos.get(mat.name.toLowerCase());
        if (!ranura) return mat;
        if (!clones.has(mat)) {
          const clon = mat.clone();
          clon.userData = { ...clon.userData, pintura_vehiculo: ranura, rol_base: clon.name.split('__')[0] };
          clones.set(mat, clon);
          pinturas.set(clon, ranura);
        }
        return clones.get(mat);
      };
      o.material = Array.isArray(o.material) ? o.material.map(reemplazar) : reemplazar(o.material);
    });
    if (pinturas.size !== ranuras.length) {
      throw new Error(`Se esperaban ${ranuras.length} pinturas recolorables y se hallaron ${pinturas.size}`);
    }
    pinturasPorInstancia.set(modelo, pinturas);
  }

  for (const [mat, ranura] of pinturas) {
    const hex = paleta[ranura];
    mat.color.set(hex);
    const prefijo = mat.userData.rol_base || rolMaterial;
    mat.name = `${prefijo}__${hex.slice(1).toLowerCase()}`;
  }
  modelo.traverse(o => {
    if (o.userData?.movimiento || (opciones.nombreRaiz && o.name === opciones.nombreRaiz)) {
      o.userData.variante = id;
    }
  });
  return id;
}
