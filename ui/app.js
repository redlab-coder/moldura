'use strict';
const $ = id => document.getElementById(id);
const token = document.querySelector('meta[name="moldura-token"]').content;
const defaults = () => ({cx:.5,cy:.5,zoom:1,rotation:0,brightness:1,contrast:1,saturation:1,sharpness:1});
const sliders = ['zoom','brightness','contrast','saturation','sharpness'];
const adjustmentNames={zoom:'Zoom',brightness:'Brilho',contrast:'Contraste',saturation:'Saturação',sharpness:'Nitidez'};
const templates=JSON.parse($('template-data').textContent);
let activeTemplate='square';
const spec=()=>templates[activeTemplate];
const capacity=()=>spec().capacity;
let photos = [], selected = null, revision = 0, sheetRevision = 0, debounce, editorTimer, toastTimer, importing = false, exporting = false, drag, liveFrame, closed=false;
const objectUrls = new Map();
const sheetCache = new Map();
const previewSources = new Map();
let orientedSource = null;
let syncTimer, restoreVersion=0;
const scratchPhoto=document.createElement('canvas');scratchPhoto.width=591;scratchPhoto.height=591;
const scratchHorizontal=document.createElement('canvas');scratchHorizontal.width=827;scratchHorizontal.height=591;
const sessionKey = 'moldura-session';
let restoring = false;
let openedSheet=null, sheetDownloading=false, sheetDialogUrl=null;
let authoritativeRevision=0;
let editingAllowed=false, releaseOwnership=null, acquiring=false, pendingRestore=null, sessionRevision=0, modelRevision=0;
const tabId=crypto.randomUUID();
const channel=typeof BroadcastChannel!=='undefined'?new BroadcastChannel('moldura:'+token):null;
const canEdit=()=>editingAllowed&&!closed&&!restoring;
async function api(path, data, raw=false, filename='') {
  const response = await fetch('/api/'+path, {method:'POST',headers:{'X-Moldura-Token':token,'Content-Type':raw?'application/octet-stream':'application/json',...(filename?{'X-Filename':encodeURIComponent(filename)}:{})},body:raw?data:JSON.stringify(data)});
  if (!response.ok) {const body = await response.json();const error=new Error(body.error || 'Não foi possível concluir.');error.status=response.status;throw error;}
  return response;
}
function toast(message) {if(closed)return; clearTimeout(toastTimer); $('toast').textContent=message; $('toast').hidden=false; toastTimer=setTimeout(()=>{if($('toast'))$('toast').hidden=true;},5500); }
function current() {return photos.find(p=>p.id===selected);}
function item(photo) {return {id:photo.id,edits:{...photo.edits},template:activeTemplate};}
const cm=mm=>(mm/10).toLocaleString('pt-BR',{maximumFractionDigits:2});
function updateTemplateUI() {
  const model=spec(),round=activeTemplate!=='square',ratio=model.visible_mm/model.cut_mm;
  document.querySelectorAll('[data-template]').forEach(button=>{button.setAttribute('aria-pressed',String(button.dataset.template===activeTemplate));button.disabled=!canEdit()||importing||exporting;});
  $('template-description').textContent=`${model.capacity} por folha`;
  $('template-description').title=round?`Visível: Ø ${cm(model.visible_mm)} cm. Corte: Ø ${cm(model.cut_mm)} cm.`:'Foto 5 × 5 cm. Corte 7 × 7 cm.';
  $('template-badge').textContent=(round?'Ø ':'')+cm(model.cut_mm)+(round?'':' × '+cm(model.cut_mm))+' cm';
  const guide=$('crop-guide');guide.style.inset=((1-ratio)*50)+'%';guide.style.borderRadius=round?'50%':'0';guide.querySelector('span').textContent=round?'Visível · Ø '+cm(model.visible_mm)+' cm':'5 × 5 cm';
  $('tile-frame').classList.toggle('round-template',round);
  const safe=$('safe-guide');safe.hidden=!round;
  if(round){const inset=(1-model.safe_mm[0]/model.cut_mm)*50;safe.style.inset=inset+'%';safe.title=`Área segura: Ø ${model.safe_mm.map(cm).join(' a ')} cm`;}
  $('hint').textContent=round?'Arraste para enquadrar':'Arraste para enquadrar';
  $('hint').title=round?`Amarelo: visível. Verde: área segura (Ø ${model.safe_mm.map(cm).join('–')} cm).`:'Centro: foto de 5 × 5 cm. Bordas espelhadas.';
  $('tile-image').setAttribute('aria-label',round?'Prévia circular com sangria automática':'Prévia da foto com bordas espelhadas');
}
function clampCrop(photo) {
  const e=photo.edits, rotated=e.rotation%180!==0;
  const w=rotated?photo.height:photo.width,h=rotated?photo.width:photo.height;
  const side=Math.min(w,h)/e.zoom;
  e.cx=Math.max(side/(2*w),Math.min(1-side/(2*w),e.cx));
  e.cy=Math.max(side/(2*h),Math.min(1-side/(2*h),e.cy));
  return {w,h,side};
}
function setImage(img, blob, key) {
  const previous=objectUrls.get(key), url=URL.createObjectURL(blob);
  img.src=url; objectUrls.set(key,url); if(previous) URL.revokeObjectURL(previous);
}
async function thumbnailBlob(blob) {
  const bitmap=await createImageBitmap(blob,{resizeWidth:128,resizeHeight:128,resizeQuality:'high'});
  const canvas=document.createElement('canvas');canvas.width=128;canvas.height=128;
  canvas.getContext('2d').drawImage(bitmap,0,0);bitmap.close();
  return new Promise(resolve=>canvas.toBlob(resolve,'image/png'));
}
function saveSession() {
  if(!canEdit())return;
  try{
    const latest=JSON.parse(localStorage.getItem(sessionKey));
    if(latest?.token===token&&(latest.sessionRevision||0)>sessionRevision){queueRestore(latest);return;}
    sessionRevision++;
    localStorage.setItem(sessionKey,JSON.stringify({token,sessionRevision,selected,template:activeTemplate,photos:photos.map(p=>({id:p.id,name:p.name,width:p.width,height:p.height,edits:{...p.edits}}))}));
  }catch(error){toast('Não foi possível guardar os ajustes. Mantenha esta aba aberta até exportar.');}
}
async function sourceFor(photo) {
  if(previewSources.has(photo.id))return previewSources.get(photo.id);
  const promise=(async()=>{
    const blob=await(await api('source',{id:photo.id})).blob();
    return createImageBitmap(blob);
  })();
  previewSources.set(photo.id,promise);
  try{
    const source=await promise;
    // Keep only three decoded editing proxies; originals remain in local temporary files.
    for(const [id,cached] of previewSources){if(previewSources.size<=3)break;if(id!==photo.id&&id!==selected){previewSources.delete(id);cached.then(bitmap=>bitmap.close()).catch(()=>{});}}
    return source;
  }catch(error){previewSources.delete(photo.id);throw error;}
}
function resolutionHint(photo) {
  const geometry=clampCrop(photo);$('resolution').hidden=geometry.side>=spec().visible_px;
  if(geometry.side<spec().visible_px){$('resolution').textContent='Este recorte pode perder definição.';$('resolution').title=`Recorte com aproximadamente ${Math.round(geometry.side)} px por lado. A exportação mantém 300 DPI.`;}
}
function drawLive() {
  if(liveFrame||closed)return;
  liveFrame=requestAnimationFrame(async()=>{
    liveFrame=null;const photo=current();if(!photo)return;const requested=revision;
    try {
      const source=await sourceFor(photo);if(requested!==revision||requested<=authoritativeRevision||current()?.id!==photo.id||closed)return;
      const e=photo.edits, rotated=e.rotation%180!==0;
      if(orientedSource?.id!==photo.id||orientedSource?.rotation!==e.rotation){
        const orientation=document.createElement('canvas');orientation.width=rotated?source.height:source.width;orientation.height=rotated?source.width:source.height;
        const oc=orientation.getContext('2d');oc.translate(orientation.width/2,orientation.height/2);oc.rotate(e.rotation*Math.PI/180);oc.drawImage(source,-source.width/2,-source.height/2);
        orientedSource={id:photo.id,rotation:e.rotation,canvas:orientation};
      }
      const orientation=orientedSource.canvas;
      const side=Math.min(orientation.width,orientation.height)/e.zoom;
      if(activeTemplate!=='square') {
        const model=spec(),size=model.cut_px,total=side*model.cut_mm/model.visible_mm;
        const canvas=$('tile-image');if(canvas.width!==size){canvas.width=size;canvas.height=size;}
        const ctx=canvas.getContext('2d');ctx.fillStyle='white';ctx.fillRect(0,0,size,size);
        const left=e.cx*orientation.width-total/2,top=e.cy*orientation.height-total/2;
        // A 3×3 reflected source plane supplies only pixels beyond the original.
        ctx.save();ctx.beginPath();ctx.arc(size/2,size/2,size/2,0,Math.PI*2);ctx.clip();
        ctx.filter=`brightness(${e.brightness}) contrast(${e.contrast}) saturate(${e.saturation})`;
        const scale=size/total;ctx.imageSmoothingQuality='high';
        for(let row=-1;row<=1;row++)for(let col=-1;col<=1;col++){
          ctx.save();ctx.translate((col*orientation.width-left)*scale,(row*orientation.height-top)*scale);ctx.scale(scale,scale);
          if(col!==0){ctx.translate(orientation.width,0);ctx.scale(-1,1);}if(row!==0){ctx.translate(0,orientation.height);ctx.scale(1,-1);}
          ctx.drawImage(orientation,0,0);ctx.restore();
        }
        ctx.restore();resolutionHint(photo);return;
      }
      const photoCanvas=scratchPhoto;
      const pc=photoCanvas.getContext('2d');pc.imageSmoothingQuality='high';
      // Interactive approximation; the authoritative Pillow preview replaces it on release.
      pc.filter=`brightness(${e.brightness}) contrast(${e.contrast}) saturate(${e.saturation})`;
      pc.drawImage(orientation,e.cx*orientation.width-side/2,e.cy*orientation.height-side/2,side,side,0,0,591,591);
      const canvas=$('tile-image');if(canvas.width!==827){canvas.width=827;canvas.height=827;}const ctx=canvas.getContext('2d');ctx.clearRect(0,0,827,827);ctx.drawImage(photoCanvas,118,118);
      ctx.save();ctx.translate(118,118);ctx.scale(-1,1);ctx.drawImage(photoCanvas,0,0,118,591,0,0,118,591);ctx.restore();
      ctx.save();ctx.translate(827,118);ctx.scale(-1,1);ctx.drawImage(photoCanvas,473,0,118,591,0,0,118,591);ctx.restore();
      const horizontal=scratchHorizontal;horizontal.getContext('2d').drawImage(canvas,0,118,827,591,0,0,827,591);
      ctx.save();ctx.translate(0,118);ctx.scale(1,-1);ctx.drawImage(horizontal,0,0,827,118,0,0,827,118);ctx.restore();
      ctx.save();ctx.translate(0,827);ctx.scale(1,-1);ctx.drawImage(horizontal,0,473,827,118,0,0,827,118);ctx.restore();
      resolutionHint(photo);
    }catch(error){toast(error.message);}
  });
}
function updateSliders() {
  const photo=current();
  for (const name of sliders) {const value=photo?photo.edits[name]:1; $(name).disabled=!photo||!canEdit(); $(name).value=value; $(name+'-value').textContent=name==='zoom'?value.toFixed(2).replace('.',',')+'×':(Math.round((value-1)*100)>0?'+':'')+Math.round((value-1)*100);const numeric=$(name+'-number');numeric.disabled=!photo||!canEdit();if(document.activeElement!==numeric)numeric.value=name==='zoom'?value.toFixed(2):Math.round((value-1)*100);$(name+'-zero').disabled=!photo||!canEdit();}
  for(const id of ['rotate','reset','center'])$(id).disabled=!photo||!canEdit();
  $('guides').disabled=!photo;
}
function renderLibrary() {
  const keepListFocus=document.activeElement?.classList.contains('photo-select');
  updateTemplateUI();
  $('count').textContent=photos.length;
  $('photo-list').replaceChildren();
  photos.forEach((photo,index)=>{
    const row=document.createElement('div'); row.className='photo-row'+(photo.id===selected?' active':'');
    const selectButton=document.createElement('button');selectButton.type='button';selectButton.className='photo-select';selectButton.setAttribute('aria-label','Editar '+photo.name);selectButton.onclick=()=>select(photo.id);
    const image=photo.thumb?document.createElement('img'):document.createElement('span');if(photo.thumb){image.src=photo.thumb;image.alt='';}else{image.className='photo-placeholder';image.innerHTML=MolduraIcons.svg(photo.previewError?'retry':'add-photo');}image.dataset.photo=photo.id;
    const detail=document.createElement('div'); detail.className='photo-detail';
    const name=document.createElement('strong'); name.textContent=photo.name; name.title=photo.name;
    const subtitle=document.createElement('small'); subtitle.textContent=photo.previewError?'Tentar prévia':`Folha ${Math.floor(index/capacity())+1}`;subtitle.title=`${photo.width} × ${photo.height} px`;
    const actions=document.createElement('div'); actions.className='row-actions';
    for(const [symbol,label,action,disabled] of [['up','Mover para cima',()=>move(index,-1),index===0],['down','Mover para baixo',()=>move(index,1),index===photos.length-1],['remove','Remover foto',()=>remove(photo.id),false]]) {
      const button=document.createElement('button');button.type='button';button.innerHTML=MolduraIcons.svg(symbol); button.setAttribute('aria-label',label+' '+photo.name);button.title=label; button.disabled=disabled||!canEdit()||importing; button.onclick=()=>action(); actions.append(button);
    }
    detail.append(name,subtitle);selectButton.append(image,detail);row.append(selectButton,actions);$('photo-list').append(row);
  });
  $('export').disabled=!photos.length||importing||exporting||restoring;
  const pages=Math.ceil(photos.length/capacity());
  $('export-label').textContent=exporting?'Preparando…':photos.length?`Exportar ${pages} folha${pages>1?'s':''}`:'Exportar JPG';
  $('export').setAttribute('aria-label',$('export-label').textContent);$('export').title=$('export-label').textContent;
  $('sheet-summary').textContent=photos.length?`${photos.length} foto${photos.length>1?'s':''} · ${pages} folha${pages>1?'s':''}`:'';
  for(const id of ['add','drop','empty-add'])$(id).disabled=!canEdit()||importing||exporting;
  if(keepListFocus)focusSelectedPhoto();
}
function select(id) {selected=id;revision++;renderLibrary();updateSliders();drawLive();renderEditor();saveSession();}
function focusSelectedPhoto(){
  const list=$('photo-list'),index=photos.findIndex(photo=>photo.id===selected),row=list.children[index];
  if(!row)return;row.querySelector('.photo-select')?.focus({preventScroll:true});
  const bounds=list.getBoundingClientRect(),rect=row.getBoundingClientRect();
  if(rect.top<bounds.top)list.scrollTop+=rect.top-bounds.top;
  else if(rect.bottom>bounds.bottom)list.scrollTop+=rect.bottom-bounds.bottom;
  if(rect.left<bounds.left)list.scrollLeft+=rect.left-bounds.left;
  else if(rect.right>bounds.right)list.scrollLeft+=rect.right-bounds.right;
}
const photoList=$('photo-list');
photoList.tabIndex=0;photoList.setAttribute('role','region');photoList.setAttribute('aria-label','Fotos. Use as setas para cima e para baixo para navegar.');
photoList.addEventListener('click',event=>{if(event.target.closest('.photo-select'))focusSelectedPhoto();else if(!event.target.closest('button'))photoList.focus({preventScroll:true});});
photoList.addEventListener('keydown',event=>{
  if(!['ArrowUp','ArrowDown'].includes(event.key)||event.altKey||event.ctrlKey||event.metaKey||event.shiftKey||event.target.closest('input,textarea,select,.row-actions')||!photos.length||importing||restoring)return;
  event.preventDefault();const index=photos.findIndex(photo=>photo.id===selected);
  const next=index<0?0:Math.max(0,Math.min(photos.length-1,index+(event.key==='ArrowDown'?1:-1)));
  if(next!==index)select(photos[next].id);focusSelectedPhoto();
});
async function renderEditor() {
  const photo=current(), request=++revision;
  $('empty-editor').hidden=!!photo; $('tile-frame').hidden=!photo; $('resolution').hidden=true;
  $('selected-name').textContent=photo?photo.name:'Escolha uma foto';
  $('retry-preview').hidden=!photo?.previewError;
  if(!photo) return;
  resolutionHint(photo);
  try {
    const blob=await (await api('preview',item(photo))).blob();
    if(request!==revision||selected!==photo.id||closed||drag) return;
    const bitmap=await createImageBitmap(blob);
    if(request!==revision||selected!==photo.id||closed||drag){bitmap.close();return;}
    const canvas=$('tile-image');if(canvas.width!==bitmap.width){canvas.width=bitmap.width;canvas.height=bitmap.height;}canvas.getContext('2d').drawImage(bitmap,0,0);bitmap.close();authoritativeRevision=request;
    const failed=photo.previewError;photo.previewError=false;$('retry-preview').hidden=true;
    // A thumbnail gets its own URL, so subsequent editor requests cannot revoke it.
    const small=await thumbnailBlob(blob);if(request!==revision||selected!==photo.id||closed)return;
    const prior=objectUrls.get('thumb-'+photo.id);photo.thumb=URL.createObjectURL(small);objectUrls.set('thumb-'+photo.id,photo.thumb);if(prior)URL.revokeObjectURL(prior);
    const thumb=document.querySelector(`img[data-photo="${photo.id}"]`);if(thumb)thumb.src=photo.thumb;if(failed||!thumb)renderLibrary();
  } catch(error) {if(request===revision){photo.previewError=true;$('retry-preview').hidden=false;renderLibrary();toast('A foto foi preservada. Tente carregar a prévia novamente.');}}
}
function changed() {
  revision++;updateSliders();drawLive();saveSession();
  clearTimeout(editorTimer);editorTimer=setTimeout(()=>{editorTimer=null;if(!drag)renderEditor();},180);
  clearTimeout(debounce);debounce=setTimeout(()=>{if(!drag)renderSheets();},450);
}
async function renderSheets() {
  const request=++sheetRevision, snapshots=photos.map(item), perPage=capacity(), template=activeTemplate;
  if(!snapshots.length) {sheetCache.clear();for(const [key,url] of objectUrls){if(key.startsWith('sheet-')){URL.revokeObjectURL(url);objectUrls.delete(key);}}$('sheets').innerHTML='<div class="empty-sheet">Suas folhas aparecerão aqui.</div>';return;}
  const fragment=document.createDocumentFragment();
  for(let i=0;i<snapshots.length;i+=perPage) {
    const index=i/perPage,cached=sheetCache.get(index);const card=cached?.card||document.createElement('div');card.className='sheet-card';if(!cached){const image=document.createElement('img');image.alt='Folha '+(index+1);const open=document.createElement('button');open.type='button';open.className='sheet-open';open.setAttribute('aria-label','Ampliar folha '+(index+1));open.title='Conferir folha';open.onclick=()=>openSheet(index);open.append(image);const labels=document.createElement('div');labels.className='sheet-label';card.append(open,labels);sheetCache.set(index,{card,fingerprint:null});}card.querySelector('.sheet-label').innerHTML=`<span>Folha ${String(index+1).padStart(2,'0')}</span><span>${Math.min(perPage,snapshots.length-i)} foto${snapshots.length-i>1?'s':''}</span>`;fragment.append(card);
  }
  $('sheets').replaceChildren(fragment);
  const cards=[...$('sheets').querySelectorAll('img')];
  cards.forEach((image,index)=>{
    const cached=sheetCache.get(index),pending=cached.fingerprint!==JSON.stringify([template,snapshots.slice(index*perPage,(index+1)*perPage)]);
    const open=image.closest('button');open.disabled=pending;open.setAttribute('aria-busy',String(pending));
  });
  try {
    for(let i=0;i<snapshots.length;i+=perPage) {
      if(request!==sheetRevision) return;
      const fingerprint=JSON.stringify([template,snapshots.slice(i,i+perPage)]);if(sheetCache.get(i/perPage)?.fingerprint===fingerprint)continue;
      const blob=await (await api('sheet',{items:snapshots.slice(i,i+perPage),template})).blob();
      if(request!==sheetRevision) return;
      setImage(cards[i/perPage],blob,'sheet-'+i/perPage);
      Object.assign(sheetCache.get(i/perPage),{fingerprint,blob,template,items:snapshots.slice(i,i+perPage)});
      cards[i/perPage].closest('button').disabled=false;cards[i/perPage].closest('button').setAttribute('aria-busy','false');
    }
    for(const [key,url] of objectUrls){if(key.startsWith('sheet-')&&Number(key.slice(6))>=cards.length){URL.revokeObjectURL(url);objectUrls.delete(key);}}
    for(const key of sheetCache.keys()){if(key>=cards.length)sheetCache.delete(key);}
  } catch(error) {if(request===sheetRevision)toast(error.message);}
}
async function importFiles(files) {
  if(importing||exporting||!canEdit()||!files.length) return;
  importing=true;renderLibrary();$('drop').disabled=true;$('add').disabled=true;
  const errors=[];let first=null;
  try {
    for(const file of files) {
      try {
        toast('Importando '+file.name+'…');
        const photo=await (await api('upload',file,true,file.name)).json();photo.edits=defaults();photos.push(photo);first??=photo.id;
        // Generate thumbnails without selecting every imported image.
        const blob=await (await api('thumbnail',item(photo))).blob();photo.thumb=URL.createObjectURL(blob);objectUrls.set('thumb-'+photo.id,photo.thumb);
      }catch(error){errors.push(file.name+': '+error.message);}
    }
  }finally{importing=false;$('files').value='';}
  if(!selected&&first) selected=first;
  renderLibrary();updateSliders();drawLive();renderEditor();renderSheets();saveSession();
  toast(errors.length?errors.join(' • '):'Fotos adicionadas.');
}
function move(index,offset) {if(!canEdit())return;const other=index+offset;if(other<0||other>=photos.length)return;[photos[index],photos[other]]=[photos[other],photos[index]];renderLibrary();renderSheets();saveSession();}
async function remove(id) {
  if(!canEdit()||importing)return;
  try {await api('delete',{id});photos=photos.filter(p=>p.id!==id);const url=objectUrls.get('thumb-'+id);if(url)URL.revokeObjectURL(url);objectUrls.delete('thumb-'+id);previewSources.get(id)?.then(bitmap=>bitmap.close()).catch(()=>{});previewSources.delete(id);if(selected===id)selected=photos[0]?.id||null;renderLibrary();updateSliders();drawLive();renderEditor();renderSheets();saveSession();}catch(error){toast(error.message);}
}
for(const id of ['add','drop','empty-add']) $(id).onclick=()=>$('files').click();
$('files').onchange=event=>importFiles([...event.target.files]);
for(const type of ['dragenter','dragover']) $('drop').addEventListener(type,event=>{event.preventDefault();$('drop').classList.add('drag-over');});
for(const type of ['dragleave','drop']) $('drop').addEventListener(type,event=>{event.preventDefault();$('drop').classList.remove('drag-over');if(type==='drop')importFiles([...event.dataTransfer.files]);});
for(const name of sliders) {
  const output=$(name+'-value'),controls=document.createElement('span');controls.className='precise-control';
  const numeric=document.createElement('input');numeric.type='number';numeric.id=name+'-number';numeric.min=name==='zoom'?'1':'-100';numeric.max=name==='zoom'?'5':name==='sharpness'?'200':'100';numeric.step=name==='zoom'?'0.01':'1';numeric.value=name==='zoom'?'1.00':'0';numeric.disabled=true;numeric.setAttribute('aria-label',name==='zoom'?'Zoom exato':`Valor exato de ${adjustmentNames[name].toLowerCase()}`);
  const zero=document.createElement('button');zero.type='button';zero.id=name+'-zero';zero.innerHTML=MolduraIcons.svg('reset');zero.disabled=true;zero.title=name==='zoom'?'Restaurar zoom':'Zerar este ajuste';zero.setAttribute('aria-label',zero.title+' '+name);
  controls.append(numeric,zero);output.classList.add('sr-only');output.after(controls);
  function apply(value) {const photo=current();if(!photo||!canEdit())return;photo.edits[name]=Math.max(Number($(name).min),Math.min(Number($(name).max),Math.round(value*100)/100));clampCrop(photo);changed();}
  $(name).oninput=()=>apply(Number($(name).value));
  numeric.oninput=()=>{if(numeric.value===''||!numeric.validity.valid)return;const value=Number(numeric.value);apply(name==='zoom'?value:1+value/100);};
  numeric.onchange=()=>{const photo=current();if(photo)numeric.value=name==='zoom'?photo.edits[name].toFixed(2):Math.round((photo.edits[name]-1)*100);};
  numeric.onkeydown=event=>{if(event.key==='Enter')numeric.blur();};
  zero.onclick=()=>apply(1);
  $(name).ondblclick=()=>apply(1);
}
$('rotate').onclick=()=>{const photo=current();if(!photo||!canEdit())return;const {cx,cy}=photo.edits;photo.edits.rotation=(photo.edits.rotation+90)%360;photo.edits.cx=1-cy;photo.edits.cy=cx;changed();};
$('reset').onclick=()=>{const photo=current();if(!photo||!canEdit())return;photo.edits=defaults();changed();};
$('center').onclick=()=>{const photo=current();if(!photo||!canEdit())return;photo.edits.cx=.5;photo.edits.cy=.5;changed();};
$('tile-frame').addEventListener('pointerdown',event=>{const photo=current();if(!photo||!canEdit())return;event.preventDefault();const geometry=clampCrop(photo);drag={x:event.clientX,y:event.clientY,cx:photo.edits.cx,cy:photo.edits.cy,id:photo.id,...geometry};$('tile-frame').setPointerCapture(event.pointerId);$('tile-frame').classList.add('dragging');});
$('tile-frame').addEventListener('pointermove',event=>{if(!drag)return;const photo=current();if(!photo||photo.id!==drag.id)return;const display=$('tile-frame').clientWidth*spec().visible_mm/spec().cut_mm;photo.edits.cx=drag.cx-(event.clientX-drag.x)*drag.side/(display*drag.w);photo.edits.cy=drag.cy-(event.clientY-drag.y)*drag.side/(display*drag.h);clampCrop(photo);changed();});
// Fine movement: one source pixel; Shift moves ten pixels.
$('tile-frame').addEventListener('keydown',event=>{const axes={ArrowLeft:[1,0],ArrowRight:[-1,0],ArrowUp:[0,1],ArrowDown:[0,-1]};if(!axes[event.key])return;const photo=current();if(!photo||!canEdit())return;event.preventDefault();const geometry=clampCrop(photo),step=event.shiftKey?10:1;photo.edits.cx+=axes[event.key][0]*step/geometry.w;photo.edits.cy+=axes[event.key][1]*step/geometry.h;clampCrop(photo);changed();});
for(const type of ['pointerup','pointercancel','lostpointercapture']) $('tile-frame').addEventListener(type,()=>{if(!drag)return;drag=null;$('tile-frame').classList.remove('dragging');changed();});
$('export').onclick=async()=>{
  if(!photos.length||exporting)return;exporting=true;renderLibrary();
  try {
    const snapshot=photos.map(item),template=activeTemplate,perPage=capacity(),response=await api('export',{items:snapshot,template}),blob=await response.blob(),url=URL.createObjectURL(blob),anchor=document.createElement('a');anchor.href=url;anchor.download=snapshot.length>perPage?'Moldura-folhas.zip':'Moldura-01.jpg';document.body.append(anchor);anchor.click();anchor.remove();setTimeout(()=>URL.revokeObjectURL(url),60000);toast(snapshot.length>perPage?'Download iniciado · ZIP com as folhas em JPG.':'Download iniciado · JPG a 300 DPI.');
  }catch(error){toast(error.message);}finally{exporting=false;renderLibrary();flushRestore();}
};
$('quit').onclick=async()=>{if(photos.length&&!confirm('Você já exportou suas folhas? Encerrar descarta as fotos e ajustes desta sessão.'))return;try{await api('quit',{});closed=true;photos=[];editingAllowed=false;releaseOwnership?.();channel?.close();localStorage.removeItem(sessionKey);clearInterval(heartbeat);clearTimeout(debounce);clearTimeout(editorTimer);clearTimeout(syncTimer);clearTimeout(toastTimer);cancelAnimationFrame(liveFrame);document.body.innerHTML='<main style="padding-top:100px;text-align:center"><h1>Até a próxima memória.</h1><p>O Moldura foi encerrado. Você pode fechar esta aba.</p></main>';}catch(error){toast(error.message);}};
async function refreshAppStatus(){
  const state=await(await api('heartbeat',{})).json();if(closed)return;
  const update=state.update,badge=$('update-status');
  const visible=['available','downloading','ready'].includes(update?.state);
  if(visible){
    const label=update.state==='downloading'?'Baixando atualização':'Atualização disponível';
    const detail=update.state==='ready'?`A versão ${update.version} está pronta e será instalada ao encerrar o Moldura.`:update.state==='downloading'?`A versão ${update.version} está sendo baixada em segundo plano.`:`A versão ${update.version} está disponível. O download será tentado novamente; você também pode verificar pela bandeja.`;
    if($('update-label').textContent!==label)$('update-label').textContent=label;
    if(badge.title!==detail){badge.title=detail;badge.setAttribute('aria-label',label+'. '+detail);}
  }
  badge.hidden=!visible;
}
const heartbeat=setInterval(()=>refreshAppStatus().catch(()=>{clearInterval(heartbeat);toast('A sessão foi encerrada. Abra o Moldura novamente.');}),20000);
refreshAppStatus().catch(()=>{});
async function restoreSession(saved) {
  if(!saved||saved.token!==token||!Array.isArray(saved.photos))return;
  const restoreRequest=++restoreVersion;
  restoring=true;revision++;sheetRevision++;clearTimeout(debounce);clearTimeout(editorTimer);
  try{
    sessionRevision=saved.sessionRevision||0;
    const changedModel=activeTemplate!==(saved.template||'square');activeTemplate=templates[saved.template]?saved.template:'square';updateTemplateUI();
    const previous=new Map(photos.map(p=>[p.id,p]));
    const keep=new Set(saved.photos.map(p=>p.id));
    for(const old of photos){if(!keep.has(old.id)){const url=objectUrls.get('thumb-'+old.id);if(url)URL.revokeObjectURL(url);objectUrls.delete('thumb-'+old.id);previewSources.get(old.id)?.then(bitmap=>bitmap.close()).catch(()=>{});previewSources.delete(old.id);}}
    photos=saved.photos.map(p=>({...p,edits:{...defaults(),...p.edits}}));selected=photos.some(p=>p.id===saved.selected)?saved.selected:photos[0]?.id||null;
    for(const photo of photos){
      if(restoreRequest!==restoreVersion||closed)return;
      const old=previous.get(photo.id);
      if(!changedModel&&old?.thumb&&JSON.stringify(old.edits)===JSON.stringify(photo.edits)){photo.thumb=old.thumb;continue;}
      try{const blob=await(await api('thumbnail',item(photo))).blob();if(restoreRequest!==restoreVersion||closed)return;photo.thumb=URL.createObjectURL(blob);const prior=objectUrls.get('thumb-'+photo.id);objectUrls.set('thumb-'+photo.id,photo.thumb);if(prior)URL.revokeObjectURL(prior);}catch(error){photo.previewError=true;}
    }
    if(!photos.some(p=>p.id===selected))selected=photos[0]?.id||null;
    renderLibrary();updateSliders();drawLive();renderEditor();renderSheets();
  }finally{if(restoreRequest===restoreVersion){restoring=false;refreshOwnershipUI();}}
}
async function chooseTemplate(template){
  if(importing||exporting||!canEdit()||!templates[template]||activeTemplate===template)return;
  activeTemplate=template;const change=++modelRevision;revision++;sheetRevision++;clearTimeout(editorTimer);clearTimeout(debounce);
  updateTemplateUI();renderLibrary();drawLive();renderEditor();renderSheets();saveSession();
  for(const photo of photos){try{const blob=await(await api('thumbnail',item(photo))).blob();if(modelRevision!==change||closed)return;const old=objectUrls.get('thumb-'+photo.id);photo.thumb=URL.createObjectURL(blob);photo.previewError=false;objectUrls.set('thumb-'+photo.id,photo.thumb);if(old)URL.revokeObjectURL(old);const thumb=document.querySelector(`img[data-photo="${photo.id}"]`);if(thumb)thumb.src=photo.thumb;}catch(error){photo.previewError=true;}}
}
document.querySelectorAll('[data-template]').forEach(button=>button.onclick=()=>chooseTemplate(button.dataset.template));

// Only one tab edits this session. Other tabs can inspect it and explicitly take over.
function refreshOwnershipUI(){if(closed)return;$('session-banner').hidden=editingAllowed;updateTemplateUI();updateSliders();renderLibrary();}
function queueRestore(saved){if(!saved||saved.token!==token||(saved.sessionRevision||0)<=sessionRevision)return;pendingRestore=saved;clearTimeout(syncTimer);syncTimer=setTimeout(flushRestore,120);}
function flushRestore(){if(!pendingRestore||drag||importing||exporting||restoring||closed)return;const saved=pendingRestore;pendingRestore=null;if((saved.sessionRevision||0)<=sessionRevision)return;restoreSession(saved).catch(()=>toast('A sessão foi preservada. Tente novamente.'));}
function readSession(){try{return JSON.parse(localStorage.getItem(sessionKey));}catch(error){return null;}}
function tryAcquireEditor(){
  if(acquiring||editingAllowed||closed)return;
  if(!navigator.locks){editingAllowed=true;refreshOwnershipUI();return;}
  acquiring=true;
  navigator.locks.request('moldura-editor:'+token,{ifAvailable:true},async lock=>{
    acquiring=false;if(!lock){refreshOwnershipUI();return;}
    editingAllowed=true;
    const hold=new Promise(resolve=>{releaseOwnership=resolve;});
    const saved=readSession();
    if(saved?.token===token&&(saved.sessionRevision||0)>sessionRevision)await restoreSession(saved);
    refreshOwnershipUI();
    await hold;releaseOwnership=null;editingAllowed=false;
  }).catch(()=>{acquiring=false;toast('Não foi possível ativar a edição nesta aba.');});
}
function yieldEditor(){
  if(!editingAllowed)return false;
  if(importing||exporting)return false;
  saveSession();editingAllowed=false;drag=null;$('tile-frame').classList.remove('dragging');clearTimeout(editorTimer);clearTimeout(debounce);refreshOwnershipUI();releaseOwnership?.();return true;
}
if(channel)channel.onmessage=event=>{
  if(closed)return;
  if(event.data.type==='yield'&&editingAllowed){if(yieldEditor())channel.postMessage({type:'released',target:event.data.from});}
  if(event.data.type==='released'&&event.data.target===tabId){queueRestore(readSession());setTimeout(tryAcquireEditor,0);}
};
$('takeover').onclick=()=>{channel?.postMessage({type:'yield',from:tabId});tryAcquireEditor();setTimeout(tryAcquireEditor,250);};
window.addEventListener('focus',()=>{if(!editingAllowed)tryAcquireEditor();});
window.addEventListener('storage',event=>{if(event.key===sessionKey&&!closed){if(event.newValue){try{queueRestore(JSON.parse(event.newValue));}catch(error){}}else if(!editingAllowed){photos=[];selected=null;renderLibrary();renderEditor();renderSheets();}}});
window.addEventListener('pagehide',()=>{saveSession();editingAllowed=false;releaseOwnership?.();});
window.addEventListener('pageshow',event=>{if(event.persisted){queueRestore(readSession());tryAcquireEditor();}});

// Local viewing controls never change the exported geometry.
$('guides').onclick=()=>{const visible=$('guides').getAttribute('aria-pressed')!=='true';$('guides').setAttribute('aria-pressed',String(visible));$('tile-frame').classList.toggle('guides-off',!visible);};
$('retry-preview').onclick=()=>{renderEditor();renderSheets();};
function openSheet(index){
  const cached=sheetCache.get(index);if(!cached?.blob||!cached.items?.length)return;
  openedSheet={index,template:cached.template,items:cached.items.map(photo=>({...photo,edits:{...photo.edits}}))};
  if(sheetDialogUrl)URL.revokeObjectURL(sheetDialogUrl);sheetDialogUrl=URL.createObjectURL(cached.blob);
  $('sheet-dialog-title').textContent='Folha '+(index+1);$('sheet-dialog-image').src=sheetDialogUrl;
  $('download-sheet').disabled=sheetDownloading;$('download-sheet').setAttribute('aria-label',`Baixar folha ${index+1} em JPG`);
  if(!$('sheet-dialog').open)$('sheet-dialog').showModal();
}
$('sheet-dialog').addEventListener('close',()=>{openedSheet=null;if(sheetDialogUrl)URL.revokeObjectURL(sheetDialogUrl);sheetDialogUrl=null;});
$('download-sheet').onclick=async()=>{
  if(!openedSheet||sheetDownloading)return;
  const snapshot=openedSheet;sheetDownloading=true;$('download-sheet').disabled=true;$('download-sheet').setAttribute('aria-busy','true');
  try{
    const response=await api('export',{items:snapshot.items,template:snapshot.template}),blob=await response.blob();
    const url=URL.createObjectURL(blob),anchor=document.createElement('a');anchor.href=url;anchor.download=`Moldura-${String(snapshot.index+1).padStart(2,'0')}.jpg`;
    document.body.append(anchor);anchor.click();anchor.remove();setTimeout(()=>URL.revokeObjectURL(url),60000);
    toast(`Download iniciado · Folha ${snapshot.index+1} em JPG a 300 DPI.`);
  }catch(error){toast(error.message);}finally{sheetDownloading=false;$('download-sheet').disabled=!openedSheet;$('download-sheet').removeAttribute('aria-busy');}
};
$('help').onclick=()=>$('help-dialog').showModal();
document.querySelectorAll('[data-close-dialog]').forEach(button=>button.onclick=()=>button.closest('dialog').close());
document.querySelectorAll('dialog').forEach(dialog=>dialog.addEventListener('click',event=>{if(event.target===dialog){const rect=dialog.getBoundingClientRect();if(event.clientX<rect.left||event.clientX>rect.right||event.clientY<rect.top||event.clientY>rect.bottom)dialog.close();}}));
new ResizeObserver(entries=>{for(const entry of entries){const size=Math.max(120,Math.floor(Math.min(entry.contentRect.width,entry.contentRect.height)-38));$('tile-frame').style.setProperty('--preview-size',size+'px');}}).observe($('canvas-area'));
refreshOwnershipUI();
(async()=>{const saved=readSession();if(saved?.token===token)await restoreSession(saved);tryAcquireEditor();})();
