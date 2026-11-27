/* Usa únicamente las dependencias three y webpack que ya tiene el proyecto. */
const path = require('node:path');
const fs = require('node:fs');
const { createRequire } = require('node:module');
const raiz = path.resolve(__dirname, '../../../..');
const requireWeb = createRequire(path.join(raiz, 'web/package.json'));
const empaquetador = requireWeb('next/dist/compiled/webpack/webpack');
empaquetador.init();
empaquetador.webpack({
  mode: 'production',
  entry: path.join(__dirname, 'visor.js'),
  output: {
    path: path.join(raiz, 'web/public/models/ciudad/codex/vehiculos'),
    filename: 'visor.bundle.js',
  },
  resolve: { modules: [path.join(raiz, 'web/node_modules')] },
  optimization: { minimize: false },
  performance: { hints: false },
  devtool: false,
}, async (error, stats) => {
  if (error || stats.hasErrors()) {
    console.error(error || stats.toString({ all: false, errors: true }));
    process.exitCode = 1;
  } else {
    try {
      const archivo = path.join(raiz, 'web/public/models/ciudad/codex/vehiculos/visor.bundle.js');
      const { minify } = requireWeb('next/dist/compiled/terser');
      const resultado = await minify(fs.readFileSync(archivo, 'utf8'), {
        compress: { passes: 1 }, mangle: true, format: { comments: /^!/ },
      });
      fs.writeFileSync(archivo, resultado.code);
      fs.copyFileSync(path.join(raiz, 'web/node_modules/three/LICENSE'),
        path.join(path.dirname(archivo), 'THREE-LICENSE.txt'));
      for (const nombre of ['autobus_animado.mjs', 'cinematica_vehiculo.mjs', 'colores_bronco.mjs',
        'GUIA_PARA_CREAR_SKILL_VEHICULOS.md', 'INTEGRACION_VEHICULOS.md'])
        fs.copyFileSync(path.join(__dirname, nombre), path.join(path.dirname(archivo), nombre));
      console.log('Visor local:', fs.statSync(archivo).size, 'bytes');
    } catch (e) { console.error(e); process.exitCode = 1; }
  }
});
