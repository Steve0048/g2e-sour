// Game2Earn : pilote le jeu dans Chrome (Playwright) : node partie.js <dossier des captures> '<commandes JSON>'
// Commandes : texte = commande du jeu ; nombre = attente (ms) ; '!shot nom' capture ; '!key w 500' touche ; '!js ...' JavaScript ;
// '!lire /chemin dest' copie un fichier du jeu (par ex. une carte enregistrée).
const { chromium } = require('playwright');
(async () => {
  const b = await chromium.launch({ args: ['--use-gl=angle', '--use-angle=swiftshader', '--enable-unsafe-swiftshader', '--ignore-gpu-blocklist'] });
  const p = await b.newPage({ viewport: { width: 1280, height: 720 } });
  const logs = [];
  p.on('console', m => logs.push(m.type() + ' ' + m.text()));
  p.on('pageerror', e => logs.push('PAGEERROR ' + e.message));
  await p.goto('http://localhost:1337/', { waitUntil: 'load' });
  const dir = process.argv[2];
  const cmds = JSON.parse(process.argv[3]);
  for (let i = 0; i < 90; i++) { await p.waitForTimeout(1000); if (logs.some(l => l.includes('init: mainloop'))) break; }
  await p.waitForTimeout(3000);
  let n = 0;
  for (const c of cmds) {
    if (typeof c === 'number') { await p.waitForTimeout(c); continue; }
    if (c.startsWith('!shot')) { await p.screenshot({ path: `${dir}/${c.slice(6)}.png` }); continue; }
    if (c.startsWith('!key ')) { const [, k, ms] = c.split(' '); await p.keyboard.down(k); await p.waitForTimeout(+ms); await p.keyboard.up(k); continue; }
    if (c.startsWith('!lire ')) {
      const [, src, dest] = c.split(' ');
      const b64 = await p.evaluate(src => { const FSx = window.FS || Module.FS; const d = FSx.readFile(src); let s = ''; for (const x of d) s += String.fromCharCode(x); return btoa(s); }, src);
      require('fs').writeFileSync(dest, Buffer.from(b64, 'base64')); console.log('lu', src, Buffer.from(b64, 'base64').length); continue;
    }
    if (c.startsWith('!js ')) { console.log(await p.evaluate(c.slice(4))); continue; }
    await p.evaluate(c => BananaBread.execute(c), c);
  }
  console.log(logs.filter(l => !/ResizeObserver|ScriptProcessor|bufferSubData|too many errors|WebGL: INVALID/.test(l)).slice(-70).join('\n'));
  await b.close();
})();
