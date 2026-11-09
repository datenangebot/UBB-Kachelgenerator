(() => {
'use strict';
const $ = (s, root=document) => root.querySelector(s);
const el = (tag, cls='', text='') => { const n=document.createElement(tag); if(cls)n.className=cls; n.textContent=text; return n; };
const page=document.body.dataset.page, token=$('meta[name="csrf-token"]').content;
const state={template:null,templates:[],backgrounds:[],photos:{},activePhotoId:null,fields:{},overrides:{},selected:null,selectedType:'element',editor:null};
const modal=id=>bootstrap.Modal.getOrCreateInstance($(id));
function toast(message){$('#app-toast .toast-body').textContent=message;bootstrap.Toast.getOrCreateInstance($('#app-toast')).show()}
async function api(action,options={}){const [name,...query]=action.split('&');const response=await fetch(`api/index.php?action=${encodeURIComponent(name)}${query.length?'&'+query.join('&'):''}`,{...options,headers:{...(options.body&&!(options.body instanceof FormData)?{'Content-Type':'application/json'}:{}),...(options.method==='POST'?{'X-CSRF-Token':token}:{}),...(options.headers||{})}});let json;try{json=await response.json()}catch{throw Error('Server antwortet nicht mit JSON.')}if(!json.ok)throw Error(`${json.message} (ID ${json.requestId})`);return json.data}
const post=(action,data)=>api(action,{method:'POST',body:JSON.stringify(data)});
const url=path=>path ? new URL(path,document.baseURI).href : '';
const assetUrl=asset=>asset?url(asset.split('/').map(encodeURIComponent).join('/')):'';
const fieldValue=(t,e,values)=>e.binding?.type==='field' ? (values[e.binding.fieldId]??'') : (e.binding?.text??'');
// Ascending paint order; equal indices retain the template's element order.
const orderedElements=t=>[...t.elements].sort((a,b)=>(Number(a.zIndex)||0)-(Number(b.zIndex)||0));
function setLayerOrder(elements){elements.forEach((element,index)=>{element.zIndex=index+1})}
function moveElementLayer(t,element,delta){
  const order=orderedElements(t),index=order.indexOf(element),destination=index+delta;
  if(index<0||destination<0||destination>=order.length)return false;
  order.splice(index,1);order.splice(destination,0,element);setLayerOrder(order);return true;
}
function photoElements(t=state.template){return t?.elements.filter(element=>element.type==='photo')||[]}
function defaultPhoto(element){return {background:null,positionX:Number(element.crop?.positionX??50),positionY:Number(element.crop?.positionY??50),zoom:Number(element.crop?.zoom??1)}}
function renderCanvas(t,target,values,photos,overrides,editor=false){
  target.className='tile-canvas';target.style.width=t.width+'px';target.style.height=t.height+'px';target.replaceChildren();
  const sorted=orderedElements(t);const textNodes=[];
  for(const e of sorted){const n=el('div','tile-element tile-'+e.type);n.dataset.elementId=e.id;
    Object.assign(n.style,{left:e.x+'px',top:e.y+'px',width:e.width+'px',height:e.height+'px',transform:`rotate(${e.rotation||0}deg)`,opacity:String(e.opacity??1),zIndex:String(e.zIndex||0)});
    if(e.type==='shape'){n.style.background=e.fillColor||'#000';n.style.borderRadius=(e.borderRadius||0)+'px'}
    if(e.type==='photo'){const photo=Object.prototype.hasOwnProperty.call(photos,e.id)?photos[e.id]:defaultPhoto(e),source=photo.background?.url||e.asset;if(source){const img=el('img');img.src=photo.background?url(source):assetUrl(source);img.style.objectPosition=`${photo.positionX}% ${photo.positionY}%`;img.style.transform=`scale(${photo.zoom})`;n.append(img)}else{n.style.background='#667085';n.append(el('div','photo-empty','Platzhalter'))}}
    if(e.type==='image'){if(e.asset){const img=el('img');img.src=assetUrl(e.asset);Object.assign(img.style,{width:'100%',height:'100%',objectFit:e.objectFit||'contain'});n.append(img)}else n.append(el('span','','Bild-Asset fehlt'))}
    if(e.type==='text'){const override=overrides[e.id]||{},font=UBBFonts.pick(e.fontFamily,e.fontWeight);n.style.left=(Number(e.x)+(Number(override.x)||0))+'px';n.style.top=(Number(e.y)+(Number(override.y)||0))+'px';n.style.alignItems=({top:'flex-start',middle:'center',bottom:'flex-end'})[e.verticalAlign]||'flex-start';const content=el('div','tile-text-content',fieldValue(t,e,values));Object.assign(content.style,{fontFamily:'"'+font.cssFamily+'"',fontWeight:String(font.face.weight),fontKerning:'none',fontVariantLigatures:'none',color:e.color||'#fff',textAlign:e.textAlign||'left',lineHeight:String(e.lineHeight||1.1),letterSpacing:(e.letterSpacing||0)+'px',whiteSpace:e.wrap===false?'pre':'pre-wrap',overflowWrap:e.wrap===false?'normal':'anywhere'});n.append(content);textNodes.push([e,n,content,override])}
    if(editor){n.dataset.editorElement='1';if(state.selectedType==='element'&&state.selected===e.id){n.classList.add('editor-selected');n.append(el('div','resize-handle'))}}
    target.append(n)
  }
  requestAnimationFrame(()=>{let warnings=[];for(const [e,n,c,o] of textNodes){const min=Number(e.minFontSize)||12,max=Number(e.maxFontSize)||72;const fits=size=>{c.style.fontSize=size+'px';const lineHeight=size*(Number(e.lineHeight)||1.1);const lines=Math.round(c.scrollHeight/lineHeight);return c.scrollWidth<=n.clientWidth+.5&&c.scrollHeight<=n.clientHeight+.5&&lines<=(Number(e.maxLines)||100)};let size=min,ok=true;if(o.mode==='manual'){size=Math.max(min,Math.min(max,Number(o.size)||max));ok=fits(size)}else{if(fits(max))size=max;else{let low=min,high=max;ok=fits(min);if(ok){for(let i=0;i<12;i++){const mid=(low+high)/2;if(fits(mid))low=mid;else high=mid}size=Math.floor(low*10)/10}}}c.style.fontSize=size+'px';n.classList.toggle('text-overflow',!ok);if(!ok)warnings.push({id:e.id,name:e.name||e.id})}if(!editor)showWarnings(warnings)})
}
function showWarnings(w){const box=$('#warnings');if(!box)return;box.classList.toggle('d-none',!w.length);box.textContent=w.length?'Text passt nicht in die Vorlage: '+w.map(x=>x.name).join(', ')+'. Inhalt kürzen oder Element im Template vergrößern.':'';for(const input of $('#fields').querySelectorAll('[data-field-id]')){const problem=w.some(x=>state.template?.elements.find(e=>e.id===x.id)?.binding?.fieldId===input.dataset.fieldId);input.classList.toggle('is-invalid',problem)}}
function fitCanvas(t,wrap,canvas){const available=Math.max(200,wrap.parentElement.clientWidth-40);const heightLimit=page==='templates'?590:Math.max(380,window.innerHeight-240);const scale=Math.min(available/t.width,heightLimit/t.height,1);wrap.style.width=Math.round(t.width*scale)+'px';wrap.style.height=Math.round(t.height*scale)+'px';canvas.style.transform=`scale(${scale})`;wrap.dataset.scale=scale}
function renderCurrent(){if(!state.template)return;const c=$('#canvas'),w=$('#preview-wrap');renderCanvas(state.template,c,state.fields,state.photos,state.overrides);fitCanvas(state.template,w,c);$('#canvas-size').textContent=`${state.template.width} × ${state.template.height} px`}
function activePhoto(){return state.photos[state.activePhotoId]||null}
function photoTarget(){return activePhoto()?{template:state.template,id:state.activePhotoId}:null}
function validPhotoTarget(target){return !!target&&target.template===state.template&&Object.prototype.hasOwnProperty.call(state.photos,target.id)}
function selectPhoto(id){
  if(!Object.prototype.hasOwnProperty.call(state.photos,id))return;
  state.activePhotoId=id;renderPhotoElements();syncPhoto();renderBackgrounds();
}
function renderPhotoElements(){
  $('#photo-element-list').replaceChildren(...photoElements().map(element=>{
    const photo=state.photos[element.id],card=el('div','generator-photo-card'+(state.activePhotoId===element.id?' active':''));
    const select=el('button','photo-element-select');select.type='button';select.dataset.photoId=element.id;select.setAttribute('aria-controls','photo-tools');select.setAttribute('aria-pressed',String(state.activePhotoId===element.id));
    const source=photo.background?url(photo.background.url):assetUrl(element.asset);
    if(source){const image=el('img');image.src=source;image.alt='';select.append(image)}else select.append(el('span','generator-photo-placeholder','Platzhalter'));
    const name=el('span','',element.name||element.id);name.append(el('small','',element.id));select.append(name);select.onclick=()=>selectPhoto(element.id);
    const choose=el('button','btn btn-sm btn-outline-primary mt-2','Bild wählen …');choose.type='button';choose.dataset.photoChoice=element.id;choose.setAttribute('aria-label','Bild für '+(element.name||element.id)+' auswählen');
    choose.onclick=()=>{selectPhoto(element.id);openPhotoGallery()};card.append(select,choose);return card;
  }));
}
function openPhotoGallery(){
  const target=photoTarget();if(!target)return;
  state.galleryTarget=target;
  const element=photoElements().find(element=>element.id===target.id);
  $('#gallery-modal .modal-title').textContent='Bild für „'+(element.name||element.id)+'“ auswählen';
  renderBackgrounds();modal('#gallery-modal').show();
}
function openPhotoUpload(target=photoTarget()){
  if(!validPhotoTarget(target))return;
  if($('#upload-submit').disabled)return toast('Ein Bild wird bereits hochgeladen.');
  state.uploadTarget=target;$('#upload-file').value='';
  const element=photoElements().find(element=>element.id===target.id);
  $('#upload-modal .modal-title').textContent='Bild für „'+(element.name||element.id)+'“ hochladen';modal('#upload-modal').show();
}
function setPhotoBackground(target,background){
  if(!validPhotoTarget(target))return false;
  state.photos[target.id].background=background;renderPhotoElements();syncPhoto();renderBackgrounds();renderCurrent();return true;
}
async function initGenerator(){
  state.templates=await api('templates.list');const select=$('#template-select');
  select.replaceChildren(...state.templates.map(t=>{const option=el('option','',t.name);option.value=t.id;return option}));
  select.addEventListener('change',()=>{if(select.value!=='__archive__')loadTemplate(select.value).catch(e=>toast(e.message))});
  state.backgrounds=await api('backgrounds.list');const params=new URLSearchParams(location.search);
  if(params.has('export'))await loadExport(params.get('export'));
  else if(state.templates.length)await loadTemplate(params.get('template')||(state.templates.some(t=>t.id==='standard-magenta')?'standard-magenta':state.templates[0].id));
  window.addEventListener('resize',renderCurrent);
  for(const [input,key] of [['#photo-zoom','zoom'],['#photo-x','positionX'],['#photo-y','positionY']])$(input).addEventListener('input',event=>{
    const photo=activePhoto();if(!photo)return;photo[key]=Number(event.target.value);syncPhoto();renderCurrent();
  });
  $('#photo-reset').onclick=()=>{const photo=activePhoto();if(!photo)return;Object.assign(photo,{positionX:50,positionY:50,zoom:1});syncPhoto();renderCurrent()};
  $('#background-default').onclick=()=>{
    const element=photoElements().find(element=>element.id===state.activePhotoId);if(!element)return;
    state.photos[element.id]=defaultPhoto(element);renderPhotoElements();syncPhoto();renderBackgrounds();renderCurrent();
  };
  $('#reset').onclick=()=>{if(state.template)applyTemplate(state.template,null,state.archived)};
  $('#gallery-upload').onclick=()=>{const target=state.galleryTarget;modal('#gallery-modal').hide();openPhotoUpload(target)};
  $('#gallery-search').oninput=renderBackgrounds;setupUpload();setupAdjust();setupExport();$('#preview-wrap').addEventListener('pointerdown',startPhotoDrag);
}
async function loadTemplate(id){applyTemplate(await api('templates.get&id='+encodeURIComponent(id)))}
async function loadExport(id){const saved=await api('exports.get&id='+encodeURIComponent(id));applyTemplate(saved.generatorState.template,saved.generatorState,true);$('#export-name').value=saved.filename.replace(/\.[^.]+$/,'');$('#export-format').value=saved.format;$('#export-scale').value=String(saved.scale||1);toast('Exportvariante geladen. Änderungen werden als neuer Export gespeichert.')}
function applyTemplate(t,restored=null,archived=false){
  if(t.schemaVersion!==1)throw Error('Unbekannte Template-Version.');
  state.template=structuredClone(t);state.archived=archived;
  state.fields=restored?{...restored.fields}:Object.fromEntries(t.fields.map(field=>[field.id,field.defaultValue]));state.overrides=restored?structuredClone({...restored.textOverrides}):{};
  state.photos=Object.fromEntries(photoElements().map(element=>{
    const saved=restored?(restored.version===1?{...restored.photo,background:restored.background}:restored.photos[element.id]):null;
    if(restored&&!saved)throw Error('Fotodaten dieses Exports fehlen.');
    const background=saved?.background?state.backgrounds.find(background=>background.filename===saved.background):null;
    if(saved?.background&&!background)throw Error('Ein Foto dieses Exports fehlt.');
    return [element.id,saved?{background,positionX:Number(saved.positionX),positionY:Number(saved.positionY),zoom:Number(saved.zoom)}:defaultPhoto(element)];
  }));
  state.activePhotoId=photoElements()[0]?.id||null;
  const select=$('#template-select');select.querySelector('[value="__archive__"]')?.remove();
  if(archived){const option=el('option','',t.name+' (Archivstand)');option.value='__archive__';select.append(option)}select.value=archived?'__archive__':t.id;
  $('#fields').replaceChildren();
  for(const field of [...t.fields].sort((a,b)=>a.order-b.order)){
    const block=el('div','mb-3'),row=el('div','d-flex justify-content-between align-items-center');row.append(el('label','form-label',field.label));
    const textElement=t.elements.find(element=>element.type==='text'&&element.binding?.fieldId===field.id);
    if(textElement){const button=el('button','btn btn-sm btn-outline-secondary','⚙');button.title='Feinjustierung';button.onclick=()=>openAdjust(textElement.id);row.append(button)}
    block.append(row);const input=el(field.inputType==='textarea'?'textarea':'input','form-control');input.dataset.fieldId=field.id;
    if(field.inputType==='textarea')input.rows=3;input.value=state.fields[field.id];input.oninput=()=>{state.fields[field.id]=input.value;renderCurrent()};block.append(input);$('#fields').append(block);
  }
  renderPhotoElements();syncPhoto();renderBackgrounds();renderCurrent();
}
function syncPhoto(){
  const photo=activePhoto();$('#photo-tools').dataset.activePhotoId=state.activePhotoId||'';$('#photo-tools').classList.toggle('d-none',!photo);$('#photo-empty-message').classList.toggle('d-none',!!photo);if(!photo)return;
  const element=photoElements().find(element=>element.id===state.activePhotoId);$('#photo-active-name').textContent=element.name||element.id;
  for(const [id,value] of [['#photo-zoom',photo.zoom],['#photo-x',photo.positionX],['#photo-y',photo.positionY]])$(id).value=value;
  $('#zoom-out').textContent=photo.zoom.toFixed(2)+'×';$('#x-out').textContent=photo.positionX+' %';$('#y-out').textContent=photo.positionY+' %';
}
function renderBackgrounds(){
  if(page!=='generator')return;const query=$('#gallery-search').value.toLowerCase();
  const target=state.galleryTarget||photoTarget(),current=validPhotoTarget(target)?state.photos[target.id]:null;
  $('#gallery-grid').replaceChildren(...state.backgrounds.filter(background=>background.filename.toLowerCase().includes(query)).map(background=>{
    const button=el('button','gallery-item'+(current?.background?.filename===background.filename?' selected':''));button.type='button';button.disabled=!current;
    const image=el('img');image.src=url(background.url);image.alt=background.filename;button.append(image);
    button.append(el('span','',background.filename));
    button.onclick=()=>{if(setPhotoBackground(target,background))modal('#gallery-modal').hide()};return button;
  }));
}
function setupUpload(){
  const input=$('#upload-file'),drop=$('#drop-zone');drop.ondragover=event=>{event.preventDefault();drop.classList.add('dragover')};drop.ondragleave=()=>drop.classList.remove('dragover');
  drop.ondrop=event=>{event.preventDefault();drop.classList.remove('dragover');input.files=event.dataTransfer.files};
  $('#upload-submit').onclick=async()=>{
    if(!input.files[0])return toast('Bitte Bild auswählen.');const target=state.uploadTarget;
    if(!validPhotoTarget(target))return toast('Bitte ein Foto-Element im aktuellen Template auswählen.');
    const form=new FormData();form.append('image',input.files[0]);const button=$('#upload-submit');button.disabled=true;
    try{
      const background=await api('backgrounds.upload',{method:'POST',body:form});state.backgrounds=await api('backgrounds.list');
      const assigned=setPhotoBackground(target,state.backgrounds.find(item=>item.filename===background.filename)||background);
      renderBackgrounds();if(state.uploadTarget===target){modal('#upload-modal').hide();input.value=''}
      toast(assigned?'Bild für das Foto-Element hochgeladen.':'Bild hochgeladen. Das ursprüngliche Foto-Element ist nicht mehr aktiv.');
    }catch(error){toast(error.message)}finally{button.disabled=false}
  };
}
function setupAdjust(){for(const id of ['#adjust-mode','#adjust-size','#adjust-x','#adjust-y'])$(id).addEventListener('input',()=>{const e=state.template.elements.find(x=>x.id===state.selected);if(!e)return;state.overrides[e.id]={mode:$('#adjust-mode').value,size:Number($('#adjust-size').value),x:Math.max(-100,Math.min(100,Number($('#adjust-x').value))),y:Math.max(-100,Math.min(100,Number($('#adjust-y').value)))};renderCurrent()});$('#adjust-reset').onclick=()=>{delete state.overrides[state.selected];openAdjust(state.selected);renderCurrent()}}
function openAdjust(id){const e=state.template.elements.find(x=>x.id===id);state.selected=id;const o=state.overrides[id]||{};$('#adjust-title').textContent=e.name+' – Feinjustierung';$('#adjust-mode').value=o.mode||'auto';$('#adjust-size').value=o.size||e.maxFontSize;$('#adjust-x').value=o.x||0;$('#adjust-y').value=o.y||0;$('#adjust-limits').textContent=`Min: ${e.minFontSize} px · Max: ${e.maxFontSize} px · max. ${e.maxLines} Zeilen · Offset ±100 px`;modal('#adjust-modal').show()}
function startPhotoDrag(event){
  if(event.button!==0)return;
  const node=event.target.closest('.tile-photo');if(!node)return;
  const id=node.dataset.elementId,element=photoElements().find(element=>element.id===id);if(!element)return;
  selectPhoto(id);const photo=state.photos[id];if(!photo.background&&!element.asset)return;
  const template=state.template,start=[event.clientX,event.clientY,photo.positionX,photo.positionY];
  const move=pointer=>{
    if(state.template!==template)return end();
    photo.positionX=Math.max(0,Math.min(100,start[2]+(pointer.clientX-start[0])/3));photo.positionY=Math.max(0,Math.min(100,start[3]+(pointer.clientY-start[1])/3));syncPhoto();renderCurrent();
  };
  const end=()=>{window.removeEventListener('pointermove',move);window.removeEventListener('pointerup',end);window.removeEventListener('pointercancel',end);window.removeEventListener('blur',end)};
  window.addEventListener('pointermove',move);window.addEventListener('pointerup',end);window.addEventListener('pointercancel',end);window.addEventListener('blur',end);event.preventDefault();
}
function showResult(saved){$('#result-name').textContent=saved.filename;$('#result-details').textContent=`${saved.width} × ${saved.height} · ${saved.format.toUpperCase()}`;const link=$('#result-download');link.href=url(saved.url);link.download=saved.filename;$('#export-modal').addEventListener('hidden.bs.modal',()=>modal('#result-modal').show(),{once:true});modal('#export-modal').hide()}
function setupExport(){
  const format=$('#export-format'),quality=$('#export-quality');
  format.onchange=()=>quality.disabled=format.value!=='jpg';format.onchange();
  quality.oninput=()=>$('#quality-out').textContent=quality.value+' %';
  $('#export-open').onclick=()=>{if(state.template){$('#export-error').classList.add('d-none');modal('#export-modal').show()}};
  $('#export-submit').onclick=async()=>{
    const button=$('#export-submit'),error=$('#export-error');let frozen,exportHost;
    button.disabled=true;button.textContent='Export läuft …';error.classList.add('d-none');
    try{
      await UBBFonts.ready;await document.fonts.ready;
      renderCurrent();await new Promise(r=>requestAnimationFrame(()=>requestAnimationFrame(r)));
      // Freeze both artwork and metadata together, even if the user edits during export.
      const photos=Object.fromEntries(photoElements().map(element=>{const photo=state.photos[element.id];return [element.id,{background:photo.background?.filename||null,positionX:photo.positionX,positionY:photo.positionY,zoom:photo.zoom}]}));
      const snapshot=structuredClone({version:2,template:state.template,fields:state.fields,photos,textOverrides:state.overrides});
      const scale=Number($('#export-scale').value),type=format.value,filename=$('#export-name').value.trim()||'UBB-Kachel';
      exportHost=el('div');Object.assign(exportHost.style,{position:'fixed',left:'-20000px',top:'0'});document.body.append(exportHost);
      frozen=$('#canvas').cloneNode(true);frozen.removeAttribute('id');Object.assign(frozen.style,{position:'relative',left:'0',top:'0',transform:'none'});exportHost.append(frozen);
      await Promise.all([...frozen.querySelectorAll('img')].map(i=>i.decode()));
      const opts={pixelRatio:scale,backgroundColor:type==='jpg'?'#ffffff':undefined,quality:Number(quality.value)/100,style:{transform:'none',position:'relative',left:'0',top:'0'}};
      const image=type==='jpg'?await fetch(await htmlToImage.toJpeg(frozen,opts)).then(r=>r.blob()):await htmlToImage.toBlob(frozen,opts);
      if(!image)throw Error('Bild konnte nicht erzeugt werden.');
      const blob=type==='pdf'?await UBBPDF.create(frozen,snapshot.template,scale):image;
      const form=new FormData();form.append('image',image,'export.'+(type==='jpg'?'jpg':'png'));
      if(type==='pdf')form.append('document',blob,'export.pdf');
      form.append('metadata',JSON.stringify({filename,format:type,scale,templateId:snapshot.template.id,generatorState:snapshot}));
      const saved=await api('exports.save',{method:'POST',body:form});
      const a=el('a');a.href=URL.createObjectURL(blob);a.download=saved.filename;a.click();setTimeout(()=>URL.revokeObjectURL(a.href),60000);showResult(saved);
    }catch(e){error.textContent=e.message;error.classList.remove('d-none')}
    finally{exportHost?.remove();button.disabled=false;button.textContent='Exportieren'}
  };
}
async function initExports(){const items=await api('exports.list');const draw=()=>{const q=$('#export-search').value.toLowerCase();$('#export-list').replaceChildren(...items.filter(x=>x.filename.toLowerCase().includes(q)).map(x=>{const card=el('div','archive-card');const img=el('img');img.src=url(x.previewUrl||x.url);img.alt='Exportvorschau';const body=el('div');body.append(el('div','filename',x.filename),el('div','text-secondary small',`${new Date(x.createdAt).toLocaleString('de-DE')} · ${x.templateName} · ${x.width} × ${x.height} · ${x.format.toUpperCase()}`));const view=el('a','btn btn-sm btn-outline-primary me-2 mt-2','Ansehen');view.href=url(x.url);view.target='_blank';view.rel='noopener';const download=el('a','btn btn-sm btn-primary me-2 mt-2','Herunterladen');download.href=url(x.url);download.download=x.filename;body.append(view,download);if(x.canRestore){const restore=el('a','btn btn-sm btn-outline-primary mt-2','Im Generator laden');restore.href='index.php?export='+encodeURIComponent(x.id);body.append(restore)}card.append(img,body);return card}))};$('#export-search').oninput=draw;draw()}
const slug=s=>s.toLowerCase().normalize('NFD').replace(/[\u0300-\u036f]/g,'').replace(/[^a-z0-9]+/g,'-').replace(/^-|-$/g,'').slice(0,60)||'template';
function newId(prefix,existing){let id=prefix,n=2;while(existing.some(x=>x.id===id))id=prefix+'-'+n++;return id}
function emptyTemplate(name,width,height){return {schemaVersion:1,id:slug(name),name,width,height,fields:[],elements:[]}}
function editorContent(t=state.editor){if(!t)return null;const {createdAt,updatedAt,...content}=t;return JSON.stringify(content)}
function editorSnapshot(){return {template:structuredClone(state.editor),selected:state.selected,type:state.selectedType}}
function groupEditorInput(input){if(state.editorGroup?.input!==input)state.editorGroup={input}}
function editorDirty(){return !!state.editor&&(state.editorNew||editorContent()!==state.editorSaved||state.assetUploads>0)}
function updateEditorControls(){
  if(!state.editor)return;
  $('#editor-undo').disabled=!state.editorUndo||!!state.editorBusy||state.assetUploads>0;
  for(const id of ['#editor-save','#editor-save-as','#editor-duplicate'])$(id).disabled=!!state.editorBusy||state.assetUploads>0;
  for(const button of document.querySelectorAll('[data-asset-picker]'))button.disabled=!!state.editorBusy||state.assetUploads>0;
  const status=$('#editor-status'),dirty=editorDirty();
  const text=state.editorBusy?'Speichern …':state.assetUploads>0?'Bild wird hochgeladen …':dirty?'Ungespeicherte Änderungen':'Gespeichert';
  if(status.textContent!==text)status.textContent=text;
  status.className='small '+(dirty?'text-warning-emphasis':'text-secondary');
}
function rememberEditorChange(){
  if(!state.editor)return;
  const content=editorContent(),previous=state.editorObserved;
  if(previous&&editorContent(previous.template)!==content){
    // A focused input or a complete drag is one editing step.
    if(!state.editorGroup||state.editorGroup!==state.editorLastGroup)state.editorUndo=previous;
    state.editorLastGroup=state.editorGroup;
    state.editorAllowLeave=false;
  }
  state.editorObserved=editorSnapshot();updateEditorControls();
}
function undoEditor(){
  if(!state.editorUndo||state.editorBusy||state.assetUploads>0)return;
  const previous=state.editorUndo;
  state.editor=structuredClone(previous.template);state.editorUndo=null;state.editorGroup=null;state.editorLastGroup=null;
  state.selected=previous.selected;state.selectedType=previous.type;state.editorObserved=editorSnapshot();
  $('#editor-name').value=state.editor.name;setEditorTab(previous.type,previous.selected);
}
function confirmEditorLeave(){
  return !(editorDirty()||state.editorBusy)||confirm('Es gibt ungespeicherte Änderungen im Template-Editor. Wirklich verlassen und diese Änderungen verwerfen?');
}
function setupEditorNavigation(){
  document.addEventListener('click',event=>{
    const link=event.target.closest('a[href]');
    if(!state.editor||!link||event.defaultPrevented||event.button!==0||event.metaKey||event.ctrlKey||event.shiftKey||event.altKey||link.hasAttribute('download')||(link.target&&link.target!=='_self'))return;
    const next=new URL(link.href,location.href);
    if(next.origin===location.origin&&next.pathname===location.pathname&&next.search===location.search&&next.hash!==location.hash)return;
    state.editorAllowLeave=false;
    if(!confirmEditorLeave()){event.preventDefault();event.stopImmediatePropagation();return}
    // The menu confirmation already covers the next full-page navigation.
    state.editorAllowLeave=true;
  },true);
  window.addEventListener('beforeunload',event=>{
    if(state.editorAllowLeave){state.editorAllowLeave=false;return}
    if(editorDirty()||state.editorBusy){event.preventDefault();event.returnValue=''}
  });
  $('#editor-view').addEventListener('focusin',event=>{
    if(event.target.matches('textarea,input:not([type=file]):not([type=checkbox])'))state.editorGroup={input:event.target};
  });
  $('#editor-view').addEventListener('focusout',event=>{if(state.editorGroup?.input===event.target)state.editorGroup=null});
  document.addEventListener('keydown',event=>{
    if(!state.editor||$('.modal.show')||!(event.ctrlKey||event.metaKey)||event.altKey||event.shiftKey||event.key.toLowerCase()!=='z'||event.target.closest('input,textarea,[contenteditable]'))return;
    if(state.editorUndo&&!state.editorBusy&&!state.assetUploads){event.preventDefault();undoEditor()}
  });
}
function setupEditorKeyboard(){
  const moves={ArrowLeft:[-1,0],ArrowRight:[1,0],ArrowUp:[0,-1],ArrowDown:[0,1]};
  const finish=()=>{if(state.editorNudge?.group===state.editorGroup)state.editorGroup=null;state.editorNudge=null};
  document.addEventListener('keydown',event=>{
    const delta=moves[event.key];
    if(!Array.isArray(delta)||event.defaultPrevented||event.isComposing||event.ctrlKey||event.metaKey||event.altKey||event.shiftKey||!state.editor||state.editorBusy||state.editorDragging||state.selectedType!=='element'||$('.modal.show')||event.target.closest('input,textarea,select,[contenteditable]'))return;
    const element=state.editor.elements.find(e=>e.id===state.selected);if(!element)return;
    event.preventDefault();
    if(!event.repeat||state.editorNudge?.key!==event.key||state.editorNudge?.element!==element||state.editorNudge?.editor!==state.editor)state.editorNudge={key:event.key,element,editor:state.editor,group:{}};
    state.editorGroup=state.editorNudge.group;
    element.x=Number(element.x)+delta[0];element.y=Number(element.y)+delta[1];renderEditor();
  });
  document.addEventListener('keyup',event=>{if(event.key===state.editorNudge?.key)finish()});
  window.addEventListener('blur',finish);
}
function setupAssetPicker(){
  $('#asset-picker-search').oninput=renderAssetPicker;$('#asset-picker-sort').onchange=renderAssetPicker;
  $('#asset-picker-upload').onchange=uploadPickerAsset;
  $('#asset-picker-modal').addEventListener('hidden.bs.modal',()=>{
    const context=state.assetPicker;state.assetPicker=null;
    if(context?.editor===state.editor)$('#editor-properties [data-asset-picker]')?.focus();
  });
  $('#asset-picker-modal').addEventListener('shown.bs.modal',()=>$('#asset-picker-search').focus());
}
async function openAssetPicker(element){
  const context={editor:state.editor,session:state.editorSession,element};state.assetPicker=context;state.assetItems=null;
  $('#asset-picker-upload').value='';$('#asset-picker-upload').disabled=state.assetUploads>0;$('#asset-picker-upload-status').textContent='';
  $('#asset-picker-search').value='';$('#asset-picker-grid').replaceChildren();
  $('#asset-picker-status').className='small text-secondary my-3';$('#asset-picker-status').textContent='Bilder werden geladen …';
  modal('#asset-picker-modal').show();
  try{
    const items=await api('assets.list');if(state.assetPicker!==context)return;
    state.assetItems=items;renderAssetPicker();
  }catch(e){if(state.assetPicker===context){$('#asset-picker-status').className='small text-danger my-3';$('#asset-picker-status').textContent=e.message}}
}
async function uploadPickerAsset(){
  const input=$('#asset-picker-upload'),file=input.files[0],context=state.assetPicker;
  if(!file||!context||state.editor!==context.editor||state.assetUploads)return;
  const form=new FormData();form.append('image',file);let selected=false;
  state.assetUploads++;input.disabled=true;updateEditorControls();renderAssetPicker();
  const status=$('#asset-picker-upload-status');status.className='small text-secondary mt-2';status.textContent='Bild wird hochgeladen …';
  try{
    const result=await api('assets.upload',{method:'POST',body:form});
    if(state.assetPicker===context&&state.editor===context.editor&&state.editor.elements.includes(context.element)){
      state.editorGroup=null;context.element.asset=result.asset;renderEditor();selected=true;
      toast('Bild hochgeladen und ausgewählt. Template speichern, um es dauerhaft zuzuordnen.');
    }else if(state.editorSession===context.session)toast('Bild hochgeladen. Es steht in der Bildauswahl zur Verfügung.');
  }catch(e){
    if(state.assetPicker===context){status.className='small text-danger mt-2';status.textContent=e.message}
  }finally{
    if(state.editorSession===context.session){state.assetUploads--;updateEditorControls()}
    if(state.assetPicker===context){input.value='';input.disabled=state.assetUploads>0;renderAssetPicker()}
  }
  if(selected&&state.assetPicker===context)modal('#asset-picker-modal').hide();
}
function renderAssetPicker(){
  const context=state.assetPicker;if(!context||!state.assetItems)return;
  const query=$('#asset-picker-search').value.trim().toLocaleLowerCase('de'),sort=$('#asset-picker-sort').value;
  const compare=new Intl.Collator('de',{numeric:true,sensitivity:'base'}).compare;
  const items=state.assetItems.filter(item=>(item.name+' '+item.filename).toLocaleLowerCase('de').includes(query)).sort((a,b)=>{
    const order=sort.startsWith('name')?compare(a.name,b.name)*(sort==='name-desc'?-1:1):(Date.parse(a.addedAt)-Date.parse(b.addedAt))*(sort==='oldest'?1:-1);
    return order||compare(a.asset,b.asset);
  });
  $('#asset-picker-status').textContent=items.length?`${items.length} ${items.length===1?'Bild':'Bilder'}`:query?'Keine passenden Bilder gefunden.':'Noch keine Template-Bilder vorhanden. Laden Sie zuerst ein Bild im Editor hoch.';
  $('#asset-picker-grid').replaceChildren(...items.map(item=>{
    const button=el('button','asset-choice'+(context.element.asset===item.asset?' selected':''));button.type='button';button.dataset.asset=item.asset;button.disabled=state.assetUploads>0;
    button.setAttribute('aria-label',item.name);button.setAttribute('aria-pressed',String(context.element.asset===item.asset));
    const img=el('img');img.src=url(item.url);img.alt='';img.loading='lazy';
    button.append(img,el('span','',item.name),el('small','',new Date(item.addedAt).toLocaleString('de-DE')));
    button.onclick=()=>{
      if(state.editor!==context.editor||!state.editor.elements.includes(context.element))return modal('#asset-picker-modal').hide();
      state.editorGroup=null;context.element.asset=item.asset;renderEditor();modal('#asset-picker-modal').hide();
    };
    return button;
  }));
}
async function initTemplates(){
  setupEditorNavigation();setupEditorKeyboard();setupAssetPicker();await loadCards();
  $('#new-template').onclick=async()=>{
    const name=prompt('Name des neuen Templates','Neues Template');if(!name)return;
    const basis=prompt('Grundlage: leer oder Template-ID','leer');let t;
    if(basis&&basis!=='leer'){t=structuredClone(await api('templates.get&id='+encodeURIComponent(basis)));t.id=slug(name);t.name=name}else t=emptyTemplate(name,1138,1138);
    const w=Number(prompt('Breite in Pixeln',t.width)),h=Number(prompt('Höhe in Pixeln',t.height));
    if(!Number.isFinite(w)||!Number.isFinite(h))return;t.width=w;t.height=h;openEditor(t,true);
  };
  $('#editor-close').onclick=()=>{
    if(!confirmEditorLeave())return;
    state.editor=null;state.editorUndo=null;state.editorObserved=null;state.editorSession++;state.assetUploads=0;
    location.hash='';$('#editor-view').classList.add('d-none');$('#template-list-view').classList.remove('d-none');loadCards();
  };
  $('#editor-undo').onclick=undoEditor;
  $('#editor-save').onclick=()=>saveEditor(false);$('#editor-save-as').onclick=()=>saveEditor(true);$('#editor-duplicate').onclick=()=>duplicateEditor();
  $('#editor-name').oninput=e=>{groupEditorInput(e.target);state.editor.name=e.target.value;rememberEditorChange()};
  $('#tab-elements').onclick=()=>setEditorTab('element');$('#tab-fields').onclick=()=>setEditorTab('field');
  $('#field-add').onclick=()=>{const id=newId('feld',state.editor.fields);state.editor.fields.push({id,label:'Neues Feld',inputType:'text',defaultValue:'',order:state.editor.fields.length*10+10});selectEditor('field',id)};
  $('#element-actions').onclick=e=>{const type=e.target.dataset.add;if(type)addElement(type)};
  $('#editor-canvas').addEventListener('pointerdown',editorPointerDown);window.addEventListener('resize',renderEditorCanvas);
  const id=new URLSearchParams(location.search).get('id');if(id)openEditor(await api('templates.get&id='+encodeURIComponent(id)));
}
async function loadCards(){
  const items=await api('templates.list'),grid=$('#template-cards');
  grid.replaceChildren(...items.map(t=>{
    const col=el('div','col-md-4 col-xl-3'),card=el('div','card h-100');
    const preview=el('div','card-img-top template-preview');preview.dataset.preview=t.id;
    const body=el('div','card-body');body.append(el('h3','card-title',t.name),el('p','small text-secondary',`${t.width} × ${t.height} px`));
    const edit=el('button','btn btn-sm btn-primary me-1 mb-1','Bearbeiten');edit.onclick=async()=>openEditor(await api('templates.get&id='+encodeURIComponent(t.id)));
    const dup=el('button','btn btn-sm btn-outline-primary me-1 mb-1','Duplizieren');dup.onclick=async()=>{const name=prompt('Name der Kopie',t.name+' Kopie');if(!name)return;try{await post('templates.duplicate',{sourceId:t.id,id:slug(name),name});await loadCards();toast('Template dupliziert')}catch(e){toast(e.message)}};
    const del=el('button','btn btn-sm btn-outline-danger mb-1','Löschen');del.onclick=async()=>{if(!confirm(`Template „${t.name}“ wirklich löschen?`))return;try{await post('templates.delete',{id:t.id});await loadCards();toast('Template gelöscht')}catch(e){toast(e.message)}};
    body.append(edit,dup,del);card.append(preview,body);col.append(card);return col
  }));
  await Promise.all(items.map(async t=>{try{const full=await api('templates.get&id='+encodeURIComponent(t.id));const preview=[...grid.querySelectorAll('[data-preview]')].find(x=>x.dataset.preview===t.id);if(!preview)return;const canvas=el('div');preview.append(canvas);const vals=Object.fromEntries(full.fields.map(f=>[f.id,f.defaultValue]));renderCanvas(full,canvas,vals,{},{});const scale=Math.min(preview.clientWidth/full.width,140/full.height);canvas.style.transform=`scale(${scale})`;canvas.style.left=Math.round((preview.clientWidth-full.width*scale)/2)+'px'}catch(e){console.error(e)}}))
}
function openEditor(t,isNew=false){
  if(t.schemaVersion!==1)return toast('Unbekannte Template-Version.');
  if(!confirmEditorLeave())return;
  state.editor=structuredClone(t);
  for(const element of state.editor.elements)if(element.type==='photo')element.crop={positionX:50,positionY:50,zoom:1,...element.crop};
  state.editorNew=isNew;state.editorSession=(state.editorSession||0)+1;state.assetUploads=0;state.editorBusy=false;
  state.editorSaved=isNew?null:editorContent();state.editorUndo=null;state.editorGroup=null;state.editorLastGroup=null;state.editorAllowLeave=false;
  state.selected=state.editor.elements[0]?.id||null;state.selectedType='element';state.editorObserved=editorSnapshot();
  $('#editor-view').inert=false;$('#editor-name').value=t.name;$('#template-list-view').classList.add('d-none');$('#editor-view').classList.remove('d-none');setEditorTab('element');
}
function setEditorTab(type,selected=null){state.selectedType=type;$('#editor-elements').classList.toggle('d-none',type!=='element');$('#editor-fields').classList.toggle('d-none',type!=='field');$('#element-actions').classList.toggle('d-none',type!=='element');$('#field-add').classList.toggle('d-none',type!=='field');$('#tab-elements').className='btn btn-sm '+(type==='element'?'btn-primary':'btn-outline-primary');$('#tab-fields').className='btn btn-sm '+(type==='field'?'btn-primary':'btn-outline-primary');state.selected=selected??(type==='element'?state.editor.elements:state.editor.fields)[0]?.id??null;renderEditor()}
function selectEditor(type,id){state.selectedType=type;state.selected=id;renderEditor()}
function renderEditor(){if(!state.editor)return;const t=state.editor;const list=$('#editor-elements');list.replaceChildren(...orderedElements(t).reverse().map(e=>{const row=el('div','editor-layer'+(state.selectedType==='element'&&state.selected===e.id?' active':''),`${e.name||e.id} · ${e.type}`);row.onclick=()=>selectEditor('element',e.id);return row}));$('#editor-fields').replaceChildren(...[...t.fields].sort((a,b)=>a.order-b.order).map(f=>{const row=el('div','editor-field'+(state.selectedType==='field'&&state.selected===f.id?' active':''),f.label);row.onclick=()=>selectEditor('field',f.id);return row}));renderEditorCanvas();renderProperties()}
function renderEditorCanvas(){const t=state.editor;if(!t)return;rememberEditorChange();const vals=Object.fromEntries(t.fields.map(f=>[f.id,f.defaultValue]));const canvas=$('#editor-canvas'),wrap=$('#editor-wrap');renderCanvas(t,canvas,vals,{},{},true);fitCanvas(t,wrap,canvas);$('#editor-size').textContent=`${t.width} × ${t.height} px`}
function editorPointerDown(ev){
  const node=ev.target.closest('[data-editor-element]');if(!node||state.editorBusy)return;
  const editor=state.editor,e=editor.elements.find(x=>x.id===node.dataset.elementId);if(!e)return;
  if(state.selected!==e.id||state.selectedType!=='element'){state.selected=e.id;state.selectedType='element';renderEditor()}
  const resize=ev.target.classList.contains('resize-handle'),group={};state.editorGroup=group;state.editorDragging=group;
  const start={x:ev.clientX,y:ev.clientY,ex:e.x,ey:e.y,w:e.width,h:e.height},scale=Number($('#editor-wrap').dataset.scale)||1;
  const move=p=>{
    if(state.editor!==editor)return end();
    const dx=(p.clientX-start.x)/scale,dy=(p.clientY-start.y)/scale;
    if(resize){e.width=Math.max(1,Math.round(start.w+dx));e.height=Math.max(1,Math.round(start.h+dy))}else{e.x=Math.round(start.ex+dx);e.y=Math.round(start.ey+dy)}
    renderEditorCanvas();renderProperties();
  };
  const end=()=>{if(state.editorGroup===group)state.editorGroup=null;if(state.editorDragging===group)state.editorDragging=null;window.removeEventListener('pointermove',move);window.removeEventListener('pointerup',end);window.removeEventListener('pointercancel',end);window.removeEventListener('blur',end)};
  window.addEventListener('pointermove',move);window.addEventListener('pointerup',end);window.addEventListener('pointercancel',end);window.addEventListener('blur',end);ev.preventDefault();
}
function property(container,obj,key,label,type='text',opts=null){
  const wrap=el('label');wrap.textContent=label;let input;
  if(opts){input=el('select','form-select form-select-sm');for(const option of opts){const op=el('option','',option);op.value=option;input.append(op)}}
  else{input=el('input','form-control form-control-sm');input.type=type;if(type==='number')input.step='any'}
  input.setAttribute('aria-label',label);input.value=obj[key]??'';
  const apply=()=>{
    const value=type==='number'?Number(input.value):input.value;if(obj[key]===value)return;
    if(obj.type==='text'&&['id','name'].includes(key)&&state.editor.elements.includes(obj))obj.naming={...textNaming(obj),[key]:'manual'};
    if(key==='id'&&state.selected===obj[key])state.selected=value;
    obj[key]=value;renderEditorCanvas();
  };
  input.oninput=()=>{if(input.matches('input,textarea'))groupEditorInput(input);apply()};
  input.onchange=()=>{
    apply();
    // Removing a focused input can fire change again on blur.
    if(['name','label','id','zIndex','order'].includes(key)){input.onchange=null;renderEditor()}
    else if(['fontFamily','fontWeight'].includes(key)){input.onchange=null;renderProperties()}
  };
  wrap.append(input);container.append(wrap);return input;
}
function textNaming(element){
  if(element.naming)return {id:element.naming.id==='auto'?'auto':'manual',name:element.naming.name==='auto'?'auto':'manual'};
  // Older templates have no naming flags. Only untouched generic defaults
  // can safely be inferred as automatic; existing descriptive names stay put.
  return {id:/^text(?:-\d+)?$/.test(element.id)?'auto':'manual',name:!element.name||['Text','Neuer Text'].includes(element.name)?'auto':'manual'};
}
function linkTextField(element,fieldId){
  const field=state.editor.fields.find(f=>f.id===fieldId);if(!field)return;
  const previousId=element.id,naming=textNaming(element);element.naming=naming;
  element.binding={...element.binding,type:'field',fieldId:field.id};
  if(naming.id==='auto'){
    element.id=newId(field.id,state.editor.elements.filter(other=>other!==element));
    if(state.selected===previousId)state.selected=element.id;
  }
  if(naming.name==='auto')element.name=field.label;
}
function assetChooser(box,element){
  const choose=el('button','btn btn-outline-secondary asset-choose mt-3');choose.type='button';choose.dataset.assetPicker='';choose.setAttribute('aria-label','Bild auswählen');choose.setAttribute('aria-haspopup','dialog');choose.setAttribute('aria-controls','asset-picker-modal');choose.disabled=state.assetUploads>0;
  if(element.asset){const img=el('img');img.src=assetUrl(element.asset);img.alt='Aktuelles Bild';choose.append(img)}
  const caption=el('span','','Bild auswählen …');if(element.asset)caption.append(el('small','',(state.assetItems||[]).find(item=>item.asset===element.asset)?.name||element.asset.split('/').pop()));
  choose.append(caption);choose.onclick=()=>openAssetPicker(element);box.append(choose);
  box.append(el('div','small text-secondary mt-1',element.type==='photo'?'Standardfoto: im Generator austauschbar, mit Bildausschnitt und Zoom.':'Festes Bild im Template, zum Beispiel ein Logo.'));
  if(element.type==='photo'&&element.asset){const clear=el('button','btn btn-sm btn-outline-secondary mt-2','Standardfoto entfernen');clear.onclick=()=>{delete element.asset;renderEditor()};box.append(clear)}
}
function propertySection(box,title){const section=el('section','editor-property-section');section.append(el('h3','',title));box.append(section);return section}
function propertyGrid(section){const grid=el('div','property-grid');section.append(grid);return grid}
function textBindingControls(section,element){
  const t=state.editor,label=el('label','','Textart'),kind=el('select','form-select form-select-sm');kind.setAttribute('aria-label','Textart');
  for(const [value,text] of [['static','Statischer Inhalt'],['field','Dynamisch']]){const option=el('option','',text);option.value=value;option.disabled=value==='field'&&!t.fields.length;kind.append(option)}
  kind.value=element.binding.type;label.append(kind);section.append(label);
  kind.onchange=()=>{
    state.editorGroup=null;
    if(kind.value==='field')linkTextField(element,t.fields.find(f=>f.id===element.binding.fieldId)?.id||t.fields[0]?.id);
    else element.binding={...element.binding,type:'static',text:element.binding.text??'Text'};
    renderEditor();
  };
  if(element.binding.type==='field'){
    const fieldLabel=el('label','','Feldverknüpfung'),select=el('select','form-select form-select-sm');select.setAttribute('aria-label','Feldverknüpfung');
    for(const field of t.fields){const option=el('option','',field.label);option.value=field.id;select.append(option)}
    select.value=element.binding.fieldId;fieldLabel.append(select);section.append(fieldLabel);
    select.onchange=()=>{state.editorGroup=null;linkTextField(element,select.value);renderEditor()};
  }else property(section,element.binding,'text','Statischer Inhalt');
}
function layerControls(grid,element){
  const layer=el('div','layer-controls'),buttons=el('div','layer-buttons');property(layer,element,'zIndex','Ebene','number');
  layer.append(buttons);grid.append(layer);
  for(const [label,delta,path] of [['Ebene ↑',1,'m5 14 7-7 7 7'],['Ebene ↓',-1,'m5 10 7 7 7-7']]){
    const button=el('button','btn btn-outline-secondary icon-button');button.type='button';button.setAttribute('aria-label',label);button.title=delta>0?'Eine Ebene nach vorne':'Eine Ebene nach hinten';
    const svg=document.createElementNS('http://www.w3.org/2000/svg','svg'),arrow=document.createElementNS('http://www.w3.org/2000/svg','path');
    for(const [key,value] of Object.entries({viewBox:'0 0 24 24',width:'16',height:'16',fill:'none',stroke:'currentColor','stroke-width':'2','stroke-linecap':'round','stroke-linejoin':'round','aria-hidden':'true'}))svg.setAttribute(key,value);
    arrow.setAttribute('d',path);svg.append(arrow);button.append(svg);button.onclick=()=>{if(moveElementLayer(state.editor,element,delta))renderEditor()};buttons.append(button);
  }
}
function renderProperties(){
  const box=$('#editor-properties');
  // Inputs already commit on input. Detach change handlers before removing a
  // focused control, so its blur cannot recursively rebuild this same panel.
  for(const input of box.querySelectorAll('input,textarea,select'))input.onchange=null;
  box.replaceChildren();const t=state.editor;
  const canvas=propertyGrid(propertySection(box,'Canvas-Eigenschaften'));
  property(canvas,t,'width','Canvas Breite','number');property(canvas,t,'height','Canvas Höhe','number');
  if(state.selectedType==='field'){
    const field=t.fields.find(f=>f.id===state.selected);if(!field)return;
    const section=propertySection(box,'Feldeigenschaften'),grid=propertyGrid(section);
    property(grid,field,'id','ID');property(grid,field,'label','Bezeichnung');property(grid,field,'inputType','Eingabetyp','text',['text','textarea']);property(grid,field,'order','Sortierung','number');
    property(section,field,'defaultValue','Standardwert');
    const remove=el('button','btn btn-outline-danger btn-sm mt-3','Feld löschen');remove.onclick=()=>{
      if(t.elements.some(element=>element.binding?.fieldId===field.id))return toast('Feld ist noch an Text gebunden.');
      t.fields=t.fields.filter(other=>other!==field);state.selected=t.fields[0]?.id;renderEditor();
    };section.append(remove);return;
  }
  const element=t.elements.find(e=>e.id===state.selected);if(!element)return;
  const identity=propertySection(box,element.type==='text'?'Textfeld-Eigenschaften':'Element-Eigenschaften');
  if(element.type==='text')textBindingControls(identity,element);
  const names=propertyGrid(identity);names.classList.add('mt-3');property(names,element,'id','ID');property(names,element,'name','Name');
  if(['image','photo'].includes(element.type)){
    const image=propertySection(box,'Bildauswahl');assetChooser(image,element);
    if(element.type==='image')property(image,element,'objectFit','Bildanpassung','text',['contain','cover']);
  }
  const position=propertyGrid(propertySection(box,'Positionierung'));
  for(const [key,label] of [['x','X'],['y','Y'],['rotation','Rotation']])property(position,element,key,label,'number');
  layerControls(position,element);
  const size=propertyGrid(propertySection(box,'Größe'));property(size,element,'width','Breite','number');property(size,element,'height','Höhe','number');
  if(element.type==='photo'){
    const crop=propertyGrid(propertySection(box,'Bildausschnitt'));
    for(const [key,label] of [['positionX','Bild X'],['positionY','Bild Y'],['zoom','Zoom']])property(crop,element.crop,key,label,'number');
  }
  const appearance=propertySection(box,element.type==='text'?'Schriftformate':'Darstellung'),formats=propertyGrid(appearance);
  if(element.type==='text'){
    const fonts=[...new Set([...UBBFonts.catalog().map(font=>font.family),element.fontFamily].filter(Boolean))];
    property(formats,element,'fontFamily','Schrift','text',fonts).parentElement.classList.add('property-wide');
    for(const [key,label,type,options] of [
      ['fontWeight','Gewicht','number'],['minFontSize','Min. Größe','number'],['maxFontSize','Max. Größe','number'],
      ['lineHeight','Zeilenhöhe','number'],['maxLines','Max. Zeilen','number'],['color','Farbe','color'],
      ['textAlign','Ausrichtung','text',['left','center','right']],['verticalAlign','Vertikal','text',['top','middle','bottom']],['letterSpacing','Zeichenabstand','number']
    ])property(formats,element,key,label,type,options);
    appearance.append(el('div','small text-secondary mt-2','Verwendete Schrift: '+UBBFonts.pick(element.fontFamily,element.fontWeight).family));
    const label=el('label','d-block mt-2'),wrap=el('input','form-check-input me-2');wrap.type='checkbox';wrap.checked=element.wrap!==false;
    wrap.onchange=()=>{element.wrap=wrap.checked;renderEditorCanvas()};label.append(wrap,document.createTextNode('Text umbrechen'));appearance.append(label);
  }else if(element.type==='shape'){
    property(formats,element,'fillColor','Farbe','color');property(formats,element,'borderRadius','Radius','number');
  }
  property(formats,element,'opacity','Deckkraft','number');
  const actions=propertySection(box,'Aktionen'),remove=el('button','btn btn-outline-danger btn-sm','Element löschen');
  remove.onclick=()=>{t.elements=t.elements.filter(other=>other!==element);state.selected=t.elements[0]?.id||null;renderEditor()};actions.append(remove);
}
function addElement(type){
  const t=state.editor,base={id:newId(type,t.elements),name:{text:'Text',shape:'Fläche',image:'Bild',photo:'Foto'}[type],type,x:100,y:100,width:300,height:150,rotation:0,opacity:1,zIndex:t.elements.length+1};
  if(type==='text'){
    Object.assign(base,{binding:{type:'static',text:'Neuer Text'},naming:{id:'auto',name:'auto'},fontFamily:'Arial, sans-serif',fontWeight:700,minFontSize:18,maxFontSize:72,lineHeight:1.1,maxLines:2,wrap:true,color:'#ffffff',textAlign:'left',verticalAlign:'middle',letterSpacing:0});
    if(t.fields.length)linkTextField(base,t.fields[0].id);
  }
  if(type==='shape')Object.assign(base,{fillColor:'#9f147e',borderRadius:0});
  if(type==='image')Object.assign(base,{asset:'',objectFit:'contain'});
  if(type==='photo')Object.assign(base,{crop:{positionX:50,positionY:50,zoom:1}});
  setLayerOrder([...orderedElements(t),base]);t.elements.push(base);selectEditor('element',base.id);
}
async function saveEditor(as){
  if(state.editorBusy)return;
  if(state.assetUploads)return toast('Bitte warten, bis der Bild-Upload abgeschlossen ist.');
  const t=structuredClone(state.editor);
  if(as){const name=prompt('Name für neues Template',t.name+' Kopie');if(!name)return;t.name=name;t.id=slug(name)}
  t.createOnly=as||state.editorNew;
  state.editorBusy=true;$('#editor-view').inert=true;updateEditorControls();
  try{
    const saved=await post('templates.save',t);
    state.editorUndo=!as&&state.editorUndo?.template.id===saved.id?state.editorUndo:null;
    state.editor=saved;state.editorNew=false;state.editorSaved=editorContent();state.editorGroup=null;state.editorLastGroup=null;
    state.editorObserved=editorSnapshot();$('#editor-name').value=saved.name;toast('Template gespeichert');renderEditor();
  }catch(e){toast(e.message)}finally{state.editorBusy=false;$('#editor-view').inert=false;updateEditorControls()}
}
async function duplicateEditor(){return saveEditor(true)}
document.fonts.ready.then(()=>{if(page==='generator')renderCurrent();else if(page==='templates')renderEditorCanvas()});
(async()=>{try{await UBBFonts.ready;if(page==='generator')await initGenerator();if(page==='templates')await initTemplates();if(page==='exports')await initExports()}catch(e){toast(e.message);console.error(e)}})();
})();
