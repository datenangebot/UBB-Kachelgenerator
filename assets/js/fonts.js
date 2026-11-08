/* Shared, local font catalog: no system-font substitution between PNG and PDF. */
window.UBBFonts = (() => {
  let catalog = [];
  const buffers = new Map();
  const ready = (async () => {
    const response = await fetch('api/index.php?action=fonts.list');
    const result = await response.json();
    if (!result.ok) throw Error(result.message || 'Schriften konnten nicht geladen werden.');
    catalog = result.data;
    const style = document.createElement('style');
    style.textContent = catalog.flatMap((font, index) => {
      font.cssFamily = 'UBBFont' + index;
      return font.faces.map(face => `@font-face{font-family:"${font.cssFamily}";font-style:normal;font-weight:${face.weight};src:url("${new URL('assets/fonts/' + face.file, document.baseURI).href}")}`);
    }).join('\n');
    document.head.append(style);
    await Promise.all(catalog.flatMap(font => font.faces.map(face => document.fonts.load(`${face.weight} 16px "${font.cssFamily}"`))));
  })();
  // The app reports loading failures; avoid an unhandled promise before it starts.
  ready.catch(() => {});
  function pick(stack = 'Arial', weight = 400) {
    const families = stack.split(',').map(name => name.trim().replace(/^['"]|['"]$/g, '').toLowerCase());
    let font;
    for (const name of families) {
      font = catalog.find(f => [f.family, ...(f.aliases || [])].some(alias => alias.toLowerCase() === name));
      if (font) break;
    }
    font ||= catalog[0];
    if (!font) throw Error('Schriftkatalog ist noch nicht geladen.');
    const face = [...font.faces].sort((a, b) => Math.abs(a.weight - Number(weight)) - Math.abs(b.weight - Number(weight)))[0];
    return {...font, face};
  }
  async function bytes(face) {
    if (!buffers.has(face.file)) buffers.set(face.file, fetch('assets/fonts/' + face.file).then(async response => {
      if (!response.ok) throw Error('Schriftdatei fehlt: ' + face.file);
      return new Uint8Array(await response.arrayBuffer());
    }));
    return buffers.get(face.file);
  }
  return {ready, pick, bytes, catalog: () => catalog};
})();
