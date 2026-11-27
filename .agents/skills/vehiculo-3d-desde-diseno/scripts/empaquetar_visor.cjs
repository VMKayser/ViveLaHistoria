#!/usr/bin/env node
/* Empaqueta un visor Three.js autónomo usando las dependencias locales del workspace (webpack + terser). */
const path = require('node:path');
const fs = require('node:fs');
const { createRequire } = require('node:module');

function parseArgs(argv) {
  const out = { copiar: [] };
  for (let i = 2; i < argv.length; i++) {
    if (argv[i] === '--copiar' && i + 1 < argv.length) {
      out.copiar.push(argv[++i]);
    } else if (argv[i].startsWith('--') && i + 1 < argv.length) {
      out[argv[i].slice(2)] = argv[++i];
    }
  }
  return out;
}

function buscarWebPackage(inicio) {
  let actual = path.resolve(inicio);
  while (true) {
    for (const rel of ['package.json', 'web/package.json']) {
      const p = path.join(actual, rel);
      const wp = path.join(path.dirname(p), 'node_modules/next/dist/compiled/webpack/webpack.js');
      if (fs.existsSync(p) && fs.existsSync(wp)) return p;
    }
    const padre = path.dirname(actual);
    if (padre === actual) return null;
    actual = padre;
  }
}

const args = parseArgs(process.argv);
if (!args.entrada || !args.salida) {
  console.error('Uso: node empaquetar_visor.cjs --entrada <visor.js> --salida <dir_publico> [--copiar <archivo> ...]');
  process.exit(2);
}

const pkg = args.package || buscarWebPackage(process.cwd());
if (!pkg) {
  console.error('No se encontró web/package.json con webpack y three instalados.');
  process.exit(1);
}

const requireWeb = createRequire(pkg);
const dirWeb = path.dirname(pkg);
const salidaDir = path.resolve(args.salida);
fs.mkdirSync(salidaDir, { recursive: true });

const empaquetador = requireWeb('next/dist/compiled/webpack/webpack');
empaquetador.init();
empaquetador.webpack(
  {
    mode: 'production',
    entry: path.resolve(args.entrada),
    output: {
      path: salidaDir,
      filename: 'visor.bundle.js',
    },
    resolve: { modules: [path.join(dirWeb, 'node_modules')] },
    optimization: { minimize: false },
    performance: { hints: false },
    devtool: false,
  },
  async (error, stats) => {
    if (error || stats.hasErrors()) {
      console.error(error || stats.toString({ all: false, errors: true }));
      process.exitCode = 1;
      return;
    }
    try {
      const bundle = path.join(salidaDir, 'visor.bundle.js');
      const { minify } = requireWeb('next/dist/compiled/terser');
      const min = await minify(fs.readFileSync(bundle, 'utf8'), {
        compress: { passes: 1 },
        mangle: true,
        format: { comments: /^!/ },
      });
      fs.writeFileSync(bundle, min.code);
      const licThree = path.join(dirWeb, 'node_modules/three/LICENSE');
      if (fs.existsSync(licThree)) {
        fs.copyFileSync(licThree, path.join(salidaDir, 'THREE-LICENSE.txt'));
      }
      for (const origen of args.copiar) {
        const abs = path.resolve(origen);
        fs.copyFileSync(abs, path.join(salidaDir, path.basename(abs)));
      }
      console.log(JSON.stringify({ bundle, bytes: fs.statSync(bundle).size }));
    } catch (e) {
      console.error(e);
      process.exitCode = 1;
    }
  }
);
