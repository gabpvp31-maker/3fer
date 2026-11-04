import { COLLIDERS, movePlayer, groundHeight, isExit, setPropColliders } from './physics.mjs';
const $ = id => document.getElementById(id);
const ui = Object.fromEntries(['start','status','retry','quality','veil','hud','description','lookhint','diagnostics'].map(id=>[id,$(id)]));
const THREE = window.THREE;
const scene = new THREE.Scene();
scene.background = new THREE.Color(0x98adba);
scene.fog = new THREE.Fog(0xb6b8a5, 42, 100);
scene.add(new THREE.HemisphereLight(0xe4edf1,0x55452e,1.05));
const sunlight = new THREE.DirectionalLight(0xffe7bd,1.45);
sunlight.position.set(-5,12,8);scene.add(sunlight);
const skyCanvas=document.createElement('canvas');skyCanvas.width=128;skyCanvas.height=256;
const skyPaint=skyCanvas.getContext('2d');const skyGradient=skyPaint.createLinearGradient(0,0,0,256);
skyGradient.addColorStop(0,'#4d7694');skyGradient.addColorStop(.5,'#a8bcc3');skyGradient.addColorStop(.65,'#c7c4ad');skyGradient.addColorStop(1,'#7a7961');skyPaint.fillStyle=skyGradient;skyPaint.fillRect(0,0,128,256);
const skyTexture=new THREE.CanvasTexture(skyCanvas);skyTexture.encoding=THREE.sRGBEncoding;
const sky=new THREE.Mesh(new THREE.SphereGeometry(85,24,16),new THREE.MeshBasicMaterial({map:skyTexture,side:THREE.BackSide,depthWrite:false,fog:false}));scene.add(sky);
const camera = new THREE.PerspectiveCamera(65, innerWidth/innerHeight,.08,90);
const renderer = new THREE.WebGLRenderer({antialias:false,powerPreference:'high-performance'});
renderer.outputEncoding = THREE.sRGBEncoding;
renderer.toneMapping=THREE.ACESFilmicToneMapping;renderer.toneMappingExposure=1.15;
renderer.setSize(innerWidth,innerHeight);
$('world').appendChild(renderer.domElement);
let stored = 'auto';
try { stored = localStorage.getItem('red-rocket-quality') || 'auto'; } catch {}
ui.quality.value = ['auto','low','balanced','high'].includes(stored) ? stored : 'auto';
let software = false;
const gl = renderer.getContext();
const info = gl.getExtension('WEBGL_debug_renderer_info');
if(info) software = /swiftshader|llvmpipe|software/i.test(gl.getParameter(info.UNMASKED_RENDERER_WEBGL));
const api = window.oficina = window.redRocket = {ready:false,state:'loading',quality:'low',changingQuality:false,camera,renderer,model:null,fps:0,drawCalls:0,triangles:0};
let dirty=true, lastRender=0, committedSelection=ui.quality.value;
let manifest, textures = {}, generation = 0, yaw=0,pitch=0,accumulator=0, previous=performance.now(), fpsTime=0, frames=0;
const keys=new Set();
function bounded(promise){let timer;return Promise.race([promise,new Promise((_,reject)=>{timer=setTimeout(()=>reject(Error('load timeout')),40000);})]).finally(()=>clearTimeout(timer));}
const effectiveQuality=()=>ui.quality.value==='auto' ? (software ? 'low':'balanced') : ui.quality.value;
function resetSpawn(){camera.position.fromArray(manifest.spawn.position); const target=new THREE.Vector3().fromArray(manifest.spawn.target);camera.lookAt(target);camera.rotation.order='YXZ';yaw=camera.rotation.y;pitch=camera.rotation.x;}
function clearInput(){keys.clear();accumulator=0;}
function pause(){if(api.state!=='playing')return;api.state='paused';dirty=true;clearInput();document.exitPointerLock?.();ui.start.textContent='Continuar exploração';ui.description.textContent='O posto espera. Continue quando quiser.';ui.veil.hidden=false;ui.hud.hidden=true;}
function title(){api.state='title';dirty=true;clearInput();document.exitPointerLock?.();resetSpawn();ui.start.textContent='Explorar mapa';ui.description.innerHTML='Um posto à beira da estrada.<br>Explore o pátio, a loja e a oficina.';ui.veil.hidden=false;ui.hud.hidden=true;}
async function setQuality(){
 const ticket=++generation;const selection=ui.quality.value;const quality=effectiveQuality();api.changingQuality=true;
 let next={};
 try {
  const tasks=[];
  const loadTexture=async(name,path,color)=>{
   const texture=await bounded(new THREE.TextureLoader().loadAsync(path));
   texture.flipY=false;texture.wrapS=texture.wrapT=THREE.RepeatWrapping;
   if(color)texture.encoding=THREE.sRGBEncoding;
   texture.anisotropy=quality==='low'?1:Math.min(4,renderer.capabilities.getMaxAnisotropy());next[name]=texture;
  };
  for(const [name,paths] of Object.entries(manifest.materials)){
   tasks.push(loadTexture(name,paths.color[quality==='low'?'low':'high'],true));
   if(quality==='high'){
    tasks.push(loadTexture(name+'_rough',paths.roughness,false));
    tasks.push(loadTexture(name+'_height',paths.height,false));
   }
  }
  const results=await Promise.allSettled(tasks);
  if(results.some(result=>result.status==='rejected'))throw Error('texture');
  if(ticket!==generation){Object.values(next).forEach(t=>t.dispose());return false;}
  api.model.traverse(object=>{if(!object.isMesh)return;
   const master=object.userData.pbrMaterial;
   const choose=material=>quality==='low'?material.userData.lightweight:material;
   object.material=Array.isArray(master)?master.map(choose):choose(master);
   for(const material of (Array.isArray(object.material)?object.material:[object.material])){
   const name=material.name.replace('runtime_','');
   material.map=next[name]||null;material.roughnessMap=next[name+'_rough']||null;
   material.bumpMap=next[name+'_height']||null;material.bumpScale=.012;material.needsUpdate=true;
  }});
  Object.values(textures).forEach(t=>t.dispose());textures=next;api.quality=quality;
  renderer.setPixelRatio(quality==='low'?(software?.5:.7):quality==='high'?Math.min(devicePixelRatio,1.5):1);renderer.setSize(innerWidth,innerHeight);
  committedSelection=selection;try{localStorage.setItem('red-rocket-quality',selection);}catch{}dirty=true;return true;
 } catch(error){Object.values(next).forEach(t=>t.dispose());if(ticket!==generation)return false;ui.quality.value=committedSelection;throw error;} finally{if(ticket===generation)api.changingQuality=false;}
}
async function load(){
 const loadTimer=setTimeout(()=>{if(!api.ready){ui.status.textContent='O carregamento demorou demais. Tente novamente ou escolha Leve.';ui.retry.hidden=false;}},45000);
 ui.retry.hidden=true;ui.start.disabled=true;ui.status.textContent='Carregando o posto…';api.state='loading';api.ready=false;
 try{
  if(!manifest){const response=await fetch('assets/runtime-manifest.json');if(!response.ok)throw Error('manifest');manifest=await response.json();}
  if(!api.model){
   const gltf=await bounded(new THREE.GLTFLoader().loadAsync(manifest.model));api.model=gltf.scene;
   const materials=new Map();
   api.model.traverse(object=>{if(!object.isMesh)return;
    const convert=source=>{if(!materials.has(source))materials.set(source,new THREE.MeshStandardMaterial({name:source.name,color:0xffffff,vertexColors:true,roughness:.84,metalness:source.name.includes('surface2')?.3:.03,side:THREE.DoubleSide}));return materials.get(source);};
    object.material=Array.isArray(object.material)?object.material.map(convert):convert(object.material);
    object.userData.pbrMaterial=object.material;
    for(const master of (Array.isArray(object.material)?object.material:[object.material]))if(!master.userData.lightweight){
     const simple=new THREE.MeshBasicMaterial({name:master.name,color:0xffffff,vertexColors:true,side:THREE.DoubleSide});
     simple.onBeforeCompile=shader=>{shader.vertexShader=shader.vertexShader.replace('#include <color_vertex>','#include <color_vertex>\n#ifdef USE_COLOR\n vColor.rgb *= .82 + .42 * max(dot(normalize(mat3(modelMatrix)*normal),normalize(vec3(-5.,12.,8.))),0.);\n#endif');};
     master.userData.lightweight=simple;
    }
    object.castShadow=false;object.receiveShadow=false;
   });materials.forEach((_,source)=>source.dispose());scene.add(api.model);api.model.updateMatrixWorld(true);
   api.model.traverse(object=>{object.matrixAutoUpdate=false;if(object.isMesh)object.frustumCulled=true;});
  }
  if(!manifest.colliders){const response=await fetch('assets/prop-colliders.json');if(!response.ok)throw Error('colliders');manifest.colliders=await response.json();}
  setPropColliders(manifest.colliders);
  await setQuality();resetSpawn();renderer.compile(scene,camera);sky.position.copy(camera.position);renderer.render(scene,camera);dirty=false;await new Promise(requestAnimationFrame);api.ready=true;api.state='title';ui.start.disabled=false;ui.status.textContent='Pronto para explorar.';
 }catch(error){console.warn('Não foi possível carregar o posto.',error);ui.status.textContent='Não foi possível carregar o posto. Extraia todo o ZIP e abra index.html novamente.';ui.retry.hidden=false;api.state='error';}finally{clearTimeout(loadTimer);}
}
function lock(){try{const promise=renderer.domElement.requestPointerLock?.();promise?.catch(()=>{ui.lookhint.hidden=false;});}catch{ui.lookhint.hidden=false;}}
ui.start.addEventListener('click',()=>{if(!api.ready)return;clearInput();api.state='playing';dirty=true;lastRender=0;ui.veil.hidden=true;ui.hud.hidden=false;lock();});
renderer.domElement.addEventListener('click',()=>{if(api.state==='playing')lock();});
ui.retry.addEventListener('click',load);
ui.quality.addEventListener('change',async()=>{if(!api.ready)return;try{if(await setQuality())ui.status.textContent='Pronto para explorar.';}catch{ui.status.textContent='Não foi possível alterar a qualidade. Tente novamente.';}});
document.addEventListener('pointerlockchange',()=>{ui.lookhint.hidden=document.pointerLockElement===renderer.domElement;if(!document.pointerLockElement&&api.state==='playing')pause();});
document.addEventListener('mousemove',event=>{if(api.state!=='playing'||document.pointerLockElement!==renderer.domElement)return;yaw-=event.movementX*.002;pitch=Math.max(-1.35,Math.min(1.35,pitch-event.movementY*.002));});
addEventListener('keydown',event=>{if(event.code==='F3'){event.preventDefault();ui.diagnostics.hidden=!ui.diagnostics.hidden;return;}if(event.code==='Escape'){pause();return;}if(api.state!=='playing')return;if(['ArrowLeft','ArrowRight','ArrowUp','ArrowDown','Space'].includes(event.code))event.preventDefault();keys.add(event.code);});
addEventListener('keyup',event=>keys.delete(event.code));addEventListener('blur',()=>{clearInput();pause();});document.addEventListener('visibilitychange',()=>{if(document.hidden){clearInput();pause();}});
addEventListener('resize',()=>{camera.aspect=innerWidth/innerHeight;camera.updateProjectionMatrix();renderer.setSize(innerWidth,innerHeight);dirty=true;});
function step(dt){
 yaw+=((keys.has('ArrowLeft')?1:0)-(keys.has('ArrowRight')?1:0))*1.6*dt;
 pitch=Math.max(-1.35,Math.min(1.35,pitch+((keys.has('ArrowUp')?1:0)-(keys.has('ArrowDown')?1:0))*1.3*dt));
 let forward=(keys.has('KeyW')?1:0)-(keys.has('KeyS')?1:0),right=(keys.has('KeyD')?1:0)-(keys.has('KeyA')?1:0);
 const length=Math.hypot(forward,right)||1,speed=(keys.has('ShiftLeft')||keys.has('ShiftRight')?5:3.2)*dt;
 const next=movePlayer(camera.position,{x:(right*Math.cos(yaw)-forward*Math.sin(yaw))/length*speed,z:(-right*Math.sin(yaw)-forward*Math.cos(yaw))/length*speed},COLLIDERS,.28);
 camera.position.set(next.x,1.7+groundHeight(next.x,next.z),next.z);camera.rotation.set(pitch,yaw,0,'YXZ');if(isExit(next.x,next.z))title();
}
function frame(now){
 requestAnimationFrame(frame);
 const elapsed=Math.max(0,(now-previous)/1000);previous=now;
 if(api.state==='playing'){
  accumulator=Math.min(accumulator+Math.min(elapsed,.1),.1);
  while(accumulator>=1/60&&api.state==='playing'){step(1/60);accumulator-=1/60;}
 }
 const interval=1000/(api.quality==='low'?30:60);
 const due=now-lastRender;
 if(!document.hidden&&(dirty||(api.state==='playing'&&due>=interval-.2))){
  sky.position.copy(camera.position);renderer.render(scene,camera);dirty=false;frames++;
  lastRender=now-(Math.max(0,due)%interval);
  api.drawCalls=renderer.info.render.calls;api.triangles=renderer.info.render.triangles;
 }
 fpsTime+=elapsed;
 if(fpsTime>=.5){
  api.fps=Math.round(frames/fpsTime);frames=0;fpsTime=0;
  if(!ui.diagnostics.hidden)ui.diagnostics.textContent=`${api.fps} FPS\n${api.drawCalls} chamadas\n${api.triangles.toLocaleString('pt-BR')} triângulos\n${api.quality} · ${renderer.domElement.width} × ${renderer.domElement.height}`;
 }
}
requestAnimationFrame(frame);load();
