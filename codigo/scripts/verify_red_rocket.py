"""Exercise the exported map in Chromium, including a truly offline file URL."""
from pathlib import Path
import functools,http.server,json,threading,time,hashlib
from playwright.sync_api import sync_playwright

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'design/red-rocket/runtime'
OUT.mkdir(exist_ok=True)
handler=functools.partial(http.server.SimpleHTTPRequestHandler,directory=str(ROOT/'red-rocket'))
server=http.server.ThreadingHTTPServer(('127.0.0.1',0),handler)
threading.Thread(target=server.serve_forever,daemon=True).start()
url=f'http://127.0.0.1:{server.server_port}/'
checks={};errors=[];external=[];profiles=[]

def metrics(page):
 return page.evaluate('''()=>new Promise(resolve=>{
  const begin=performance.now(),frame=redRocket.renderer.info.render.frame;
  function sample(now){if(now-begin<2200){requestAnimationFrame(sample);return;}
   resolve({quality:redRocket.quality,fps:(redRocket.renderer.info.render.frame-frame)*1000/(now-begin),
    drawCalls:redRocket.renderer.info.render.calls,triangles:redRocket.renderer.info.render.triangles,
    textures:redRocket.renderer.info.memory.textures,
    resolution:[redRocket.renderer.domElement.width,redRocket.renderer.domElement.height]});}
  requestAnimationFrame(sample);
 })''')

try:
 with sync_playwright() as p:
  browser=p.chromium.launch(executable_path='/usr/bin/chromium',headless=True,args=['--no-sandbox','--enable-unsafe-swiftshader','--use-angle=swiftshader'])
  page=browser.new_page(viewport={'width':1280,'height':800})
  page.set_default_timeout(90000)
  page.on('pageerror',lambda e:errors.append(str(e)))
  page.on('request',lambda r:external.append(r.url) if r.url.startswith(('http:','https:')) and not r.url.startswith(url) else None)
  begin=time.monotonic();page.goto(url)
  page.wait_for_function('window.redRocket?.ready === true')
  checks['httpLoadSeconds']=time.monotonic()-begin
  checks['initialCamera']=page.evaluate('redRocket.camera.position.toArray()')
  checks['modelMeshes']=page.evaluate('(()=>{let n=0;redRocket.model.traverse(o=>{if(o.isMesh)n++});return n})()')
  assert checks['modelMeshes']>0
  page.locator('#start').click();page.wait_for_function('redRocket.state==="playing"')
  before=page.evaluate('redRocket.camera.position.toArray()')
  page.keyboard.down('w');page.wait_for_timeout(450);page.keyboard.up('w')
  after=page.evaluate('redRocket.camera.position.toArray()')
  assert sum(abs(a-b) for a,b in zip(before,after))>.2
  checks['movement']=True
  page.keyboard.press('Escape');page.wait_for_function('redRocket.state==="paused"')
  page.wait_for_timeout(200);frame=page.evaluate('redRocket.renderer.info.render.frame')
  page.wait_for_timeout(350)
  assert page.evaluate('redRocket.renderer.info.render.frame')==frame
  checks['pausedRenderingStops']=True
  for mode in ['low','balanced','high']:
   page.locator('#quality').select_option(mode)
   page.wait_for_function('q=>redRocket.quality===q&&!redRocket.changingQuality',arg=mode)
   page.locator('#start').click();page.wait_for_function('redRocket.state==="playing"')
   page.evaluate('''()=>{redRocket.camera.position.set(-10,1.7,24);redRocket.camera.lookAt(-.6,3.5,-3)}''')
   page.wait_for_timeout(700)
   profiles.append(metrics(page))
   page.screenshot(path=str(OUT/f'{mode}-loaded.png'))
   page.keyboard.press('Escape');page.wait_for_function('redRocket.state==="paused"')
  checks['qualityModes']=True
  # Test failed-tier rollback rather than treating a successful load as sufficient.
  page.route('**/surface0-512.jpg',lambda route:route.abort())
  page.locator('#quality').select_option('low')
  page.wait_for_function('!redRocket.changingQuality')
  page.locator('#status').filter(has_text='Não foi possível alterar').wait_for()
  assert page.evaluate('redRocket.quality')=='high'
  assert page.locator('#quality').input_value()=='high'
  checks['failedQualityRollback']=True
  page.unroute('**/surface0-512.jpg')
  page.locator('#start').click();page.wait_for_function('redRocket.state==="playing"')
  # Frame the interior without altering movement state during the capture.
  page.evaluate('''()=>{redRocket.camera.position.set(9.5,1.86,-4);redRocket.camera.lookAt(9.6,1.4,-12.3)}''')
  # The game applies stored view angles every fixed step, so pause and explicitly render.
  page.keyboard.press('Escape');page.wait_for_function('redRocket.state==="paused"')
  page.evaluate('''()=>{document.getElementById('veil').hidden=true;redRocket.camera.position.set(9.5,1.86,-4);redRocket.camera.lookAt(9.6,1.4,-12.3);redRocket.renderer.render(redRocket.model.parent,redRocket.camera)}''')
  page.screenshot(path=str(OUT/'garage-loaded.png'))
  # A missing initial model produces a visible retry state.
  failure=browser.new_page();failure.route('**/map.glb',lambda route:route.abort())
  failure.goto(url);failure.wait_for_function('redRocket.state==="error"')
  assert failure.locator('#retry').is_visible();assert failure.locator('#start').is_disabled()
  failure.unroute('**/map.glb');failure.locator('#retry').click()
  failure.wait_for_function('redRocket.ready===true')
  checks['failedInitialLoadAndRetry']=True;failure.close()
  # This managed Chromium blocks file:// navigation by policy. A sandboxed
  # opaque-origin frame exercises the same offline/CORS constraints without
  # changing browser policy or granting cross-origin/file access.
  offline=browser.new_page(viewport={'width':1280,'height':800})
  offline.on('pageerror',lambda e:errors.append(str(e)))
  offline.goto('about:blank')
  requests=[]
  offline.on('request',lambda r:requests.append(r.url) if r.url.startswith(('http:','https:')) else None)
  html=(ROOT/'red-rocket/portable/index.html').read_text()
  begin=time.monotonic()
  offline.evaluate("""html=>{
   document.body.innerHTML='';const frame=document.createElement('iframe');
   frame.setAttribute('sandbox','allow-scripts allow-pointer-lock');
   frame.style.cssText='position:fixed;inset:0;width:100vw;height:100vh;border:0';
   frame.srcdoc=html;document.body.appendChild(frame);
  }""",html)
  frame=offline.locator('iframe').element_handle().content_frame()
  frame.wait_for_function('window.redRocket?.ready === true',timeout=90000)
  checks['offlineLoadSeconds']=time.monotonic()-begin
  checks['offlineMethod']='Sandboxed opaque-origin iframe. Direct file navigation is blocked by managed Chromium policy.'
  assert requests==[],requests
  frame.locator('#start').click();frame.wait_for_function('redRocket.state==="playing"')
  before=frame.evaluate('redRocket.camera.position.toArray()')
  offline.keyboard.down('w');offline.wait_for_timeout(400);offline.keyboard.up('w')
  assert before!=frame.evaluate('redRocket.camera.position.toArray()')
  checks['offlineMovement']=True;checks['offlineExternalRequests']=requests
  offline.screenshot(path=str(OUT/'offline-loaded.png'))
  browser.close()
 assert not errors,errors
 assert not external,external
 report={'passed':True,'device':'Chromium / SwiftShader software rendering; hardware GPU not measured', 'checks':checks,'profiles':profiles,'pageErrors':errors,'externalRequests':external}
 report['artifactHashes']={str(path.relative_to(ROOT)):hashlib.sha256(path.read_bytes()).hexdigest() for path in [ROOT/'red-rocket/src/app.mjs',ROOT/'red-rocket/src/physics.mjs',ROOT/'red-rocket/portable/index.html',ROOT/'red-rocket/assets/runtime-manifest.json',ROOT/'red-rocket/assets/map.glb',ROOT/'design/red-rocket/layout-study.blend']}
 (OUT/'browser-report.json').write_text(json.dumps(report,indent=2)+'\n')
 print(json.dumps(report),flush=True)
finally:
 server.shutdown()
