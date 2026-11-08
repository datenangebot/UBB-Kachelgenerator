/* Raster artwork and genuine, embedded PDF text, positioned by the preview DOM. */
window.UBBPDF = (() => {
  async function create(canvas, template, scale) {
    const P = PDFLib, doc = await P.PDFDocument.create();
    doc.registerFontkit(fontkit);
    doc.setCreator('UBB Kachelgenerator');
    doc.setTitle(template.name);
    // CSS pixels are 1/96 inch, PDF points are 1/72 inch.
    const unit = .75 * scale, width = template.width * unit, height = template.height * unit;
    const page = doc.addPage([width, height]);
    const fonts = new Map();
    const clone = canvas.cloneNode(true);
    Object.assign(clone.style, {position:'relative', left:'0', top:'0', transform:'none', pointerEvents:'none'});
    clone.removeAttribute('id');
    const host = document.createElement('div');
    Object.assign(host.style, {position:'fixed', left:'-20000px', top:'0'});
    document.body.append(host); host.append(clone);
    try {
      await Promise.all([...clone.querySelectorAll('img')].map(img => img.decode()));
      page.drawRectangle({x:0, y:0, width, height, color:P.rgb(238/255,238/255,238/255)});
      let artwork = [];
      async function drawArtwork() {
        if (!artwork.length) return;
        const ids = new Set(artwork);
        const png = await htmlToImage.toPng(clone, {
          pixelRatio:scale, backgroundColor:'transparent',
          style:{position:'relative', left:'0', top:'0', transform:'none', background:'transparent'},
          filter:node => !node.dataset?.elementId || ids.has(node.dataset.elementId)
        });
        page.drawImage(await doc.embedPng(png), {x:0, y:0, width, height});
        artwork = [];
      }
      for (const node of clone.children) {
        const element = template.elements.find(e => e.id === node.dataset.elementId);
        if (element.type !== 'text') { artwork.push(element.id); continue; }
        await drawArtwork();
        const content = node.querySelector('.tile-text-content');
        if (!content.textContent) continue;
        const selected = UBBFonts.pick(element.fontFamily, element.fontWeight);
        if (!fonts.has(selected.face.file)) {
          const bytes = await UBBFonts.bytes(selected.face);
          fonts.set(selected.face.file, {pdf:await doc.embedFont(bytes, {subset:true, features:{liga:false,kern:false}}), parsed:fontkit.create(bytes)});
        }
        const font = fonts.get(selected.face.file);
        const css = getComputedStyle(content), size = parseFloat(css.fontSize);
        const text = content.firstChild;
        // Measure without rotation; apply that same rotation to the PDF graphics state.
        const transform = node.style.transform;
        node.style.transform = 'none';
        const origin = clone.getBoundingClientRect();
        const marker = document.createElement('span');
        Object.assign(marker.style, {display:'inline-block', width:'0', height:'0', padding:'0', margin:'0', verticalAlign:'baseline'});
        content.prepend(marker);
        const range = document.createRange();
        range.setStart(text,0); range.setEnd(text,Math.min(1,text.length));
        const first = range.getBoundingClientRect();
        const baselineOffset = marker.getBoundingClientRect().top - first.top;
        marker.remove();
        const centerX = (parseFloat(node.style.left) + element.width/2) * unit;
        const centerY = height - (parseFloat(node.style.top) + element.height/2) * unit;
        const radians = -(Number(element.rotation)||0) * Math.PI/180, c = Math.cos(radians), s = Math.sin(radians);
        page.pushOperators(P.pushGraphicsState(), P.concatTransformationMatrix(c,s,-s,c,centerX-c*centerX+s*centerY,centerY-s*centerX-c*centerY));
        const rgb = css.color.match(/[\d.]+/g).map(Number);
        const segments = new Intl.Segmenter('de', {granularity:'grapheme'}).segment(text.textContent);
        for (const {segment, index} of segments) {
          if (/^[\s\u200b]+$/u.test(segment)) continue;
          for (const char of segment) {
            if (!font.parsed.hasGlyphForCodePoint(char.codePointAt(0))) throw Error(`Die Schrift ${selected.family} enthält das Zeichen „${char}“ nicht. Bitte eine passende Schrift im Template auswählen.`);
          }
          range.setStart(text,index); range.setEnd(text,index+segment.length);
          const rect = range.getBoundingClientRect();
          page.drawText(segment, {
            x:(rect.left-origin.left)*unit, y:height-(rect.top-origin.top+baselineOffset)*unit,
            size:size*unit, font:font.pdf, color:P.rgb(rgb[0]/255,rgb[1]/255,rgb[2]/255),
            opacity:(Number(element.opacity??1))*(rgb[3]??1)
          });
        }
        page.pushOperators(P.popGraphicsState());
        node.style.transform = transform;
      }
      await drawArtwork();
      return new Blob([await doc.save({useObjectStreams:false})], {type:'application/pdf'});
    } finally { host.remove(); }
  }
  return {create};
})();
