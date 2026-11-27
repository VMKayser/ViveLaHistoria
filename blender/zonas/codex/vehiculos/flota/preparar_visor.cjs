const fs = require('node:fs');
const path = require('node:path');
const { spawnSync } = require('node:child_process');

const raiz = path.resolve(__dirname, '../../../../..');
const flota = path.join(raiz, 'web/public/models/ciudad/codex/vehiculos/flota');
const disenos = require('./disenos.json');
const idPedido = process.argv[2];
if (idPedido && !Object.hasOwn(disenos, idPedido)) throw new Error(`Vehículo desconocido: ${idPedido}`);
const salida = idPedido ? path.join(flota, idPedido) : flota;
const seleccion = idPedido ? [[idPedido, disenos[idPedido]]] : Object.entries(disenos);
fs.mkdirSync(path.join(salida, 'referencias'), { recursive: true });

const vehiculos = seleccion.map(([id, entrada]) => {
  const d = entrada.datos ? require(path.join(__dirname, entrada.datos)) : entrada;
  const ficha = JSON.parse(fs.readFileSync(path.join(flota, id + '.ficha.json')));
  const lamina = d.archivo_lamina ?? `generadas/${d.referencia}_diseno_miciudad.png`;
  fs.copyFileSync(path.join(raiz, 'autos', lamina),
    path.join(salida, 'referencias', id + '.png'));
  const prefijo = idPedido ? '../' : '';
  const { nombre, largo, ancho, alto, ejes, radio_rueda, semivia_ruedas } = d;
  return { id, nombre, largo, ancho, alto, ejes, radio_rueda, semivia_ruedas, triangulos: ficha.triangulos,
    ...(d.tipo_direccion === 'tornamesa' ? { tipo: 'remolque' } : {}),
    glb: `${prefijo}${id}.glb`, blend: `${prefijo}${id}.blend`, ficha: `${prefijo}${id}.ficha.json` };
});
const titulo = idPedido ? vehiculos[0].nombre : undefined;
fs.writeFileSync(path.join(salida, 'catalogo.json'), JSON.stringify({ titulo, vehiculos }, null, 2) + '\n');
const guiaPropia = idPedido && path.join(__dirname, idPedido, 'INTEGRACION.md');
const guia = guiaPropia && fs.existsSync(guiaPropia) ? guiaPropia : path.join(__dirname, 'INTEGRACION.md');
const html = fs.readFileSync(path.join(__dirname, 'index.html'), 'utf8');
fs.writeFileSync(path.join(salida, 'index.html'), idPedido ? html.replace('../index.html', '../../index.html') : html);
const empaquetar = path.join(raiz, '.agents/skills/vehiculo-3d-desde-diseno/scripts/empaquetar_visor.cjs');
const proceso = spawnSync(process.execPath,
  [empaquetar, '--entrada', path.join(__dirname, 'visor.js'), '--salida', salida, '--copiar', guia],
  { cwd: raiz, stdio: 'inherit' });
if (proceso.error) throw proceso.error;
process.exitCode = proceso.status ?? 1;
