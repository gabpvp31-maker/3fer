"""Package verified offline gameplay and reproducible Blender/runtime sources."""
from pathlib import Path
import hashlib,json,zipfile

ROOT=Path(__file__).resolve().parents[1]
GAME=ROOT/'red-rocket'
D=ROOT/'design/red-rocket'
DEST=Path('/workspace')

def digest(path):return hashlib.sha256(path.read_bytes()).hexdigest()

def package():
 report=json.loads((D/'runtime/browser-report.json').read_text())
 assert report['passed'] and not report['pageErrors']
 assert (D/'runtime/browser-report.json').stat().st_mtime >= max((GAME/'src/app.mjs').stat().st_mtime,(GAME/'portable/index.html').stat().st_mtime), 'Browser verification is stale'
 for name,sha in report['artifactHashes'].items():assert digest(ROOT/name)==sha, 'Verified artifact changed: '+name
 manifest=json.loads((GAME/'assets/runtime-manifest.json').read_text())
 native=digest(D/'layout-study.blend')
 assert manifest['statistics']['authoringSourceSha256']==native
 for name,sha in manifest['hashes'].items():assert digest(GAME/name)==sha,name
 archives=[]
 play=DEST/'red-rocket-jogavel.zip'
 with zipfile.ZipFile(play,'w',zipfile.ZIP_DEFLATED,compresslevel=6) as z:
  z.write(GAME/'portable/index.html','index.html')
  z.writestr('LEIA-ME.txt','RED ROCKET — MAPA JOGÁVEL\n\nExtraia o ZIP e abra index.html no Chrome, Edge ou Firefox atualizado.\nFunciona offline, sem servidor e sem instalar programas.\nWASD: andar. Shift: correr. Mouse ou setas: olhar. Esc: pausar. F3: desempenho.\nEscolha Leve em computadores mais lentos.\nRecriação de fã; modelo autoral e texturas CC0, sem assets extraídos de Fallout.\n')
  z.write(GAME/'vendor/LICENSE-three.txt','LICENSE-three.txt')
  z.write(D/'materials/sources.json','licencas-texturas.json')
 archives.append(play)
 source=DEST/'red-rocket-fontes.zip'
 files=[]
 for path in GAME.rglob('*'):
  if path.is_file() and not any(part in {'portable','__pycache__'} for part in path.relative_to(GAME).parts):files.append(path)
 files.extend(ROOT/'blender'/name for name in [
  'red_rocket_function_study.py','red_rocket_similarity.py','red_rocket_vehicle.py',
  'red_rocket_setting.py','red_rocket_pbr.py','collect_red_rocket_study.py',
  'audit_red_rocket_reference.py','audit_red_rocket_pbr.py','export_red_rocket.py',
  'room_contracts.py','validate_room.py','quantize_vertex_colors.py'])
 files.extend(ROOT/name for name in ['design/oficina-do-vale.blend','design/props.json',
  'scripts/package_red_rocket.py','scripts/verify_red_rocket.py','tests/red-rocket-physics.test.mjs',
  'tests/test_red_rocket_export.py','docs/superpowers/specs/2026-11-04-red-rocket-photo-textures.md'])
 for path in D.rglob('*'):
  if not path.is_file() or path.suffix in {'.blend1','.log'} or path.name=='draft-proportions.png':continue
  rel=path.relative_to(D)
  if rel.parts[0]=='references' and path.name not in {'primary-reference.json','red-rocket-sanctuary-gameplay.webp'}:continue
  files.append(path)
 with zipfile.ZipFile(source,'w',zipfile.ZIP_DEFLATED,compresslevel=6) as z:
  z.writestr('LEIA-ME.txt','FONTES DO RED ROCKET\n\nModelo: design/red-rocket/layout-study.blend (Blender 4.3.2).\nJogo modular: red-rocket/index.html; execute um servidor estático nessa pasta.\nJogo offline: gere com python3 red-rocket/scripts/build_portable.py.\nReceita de autoria/exportação: blender/.\nO Blender antigo design/oficina-do-vale.blend é necessário para reconstruir o carro traseiro.\nA versão jogável autossuficiente é entregue separadamente em red-rocket-jogavel.zip.\nDocumentação: red-rocket/README.md.\n')
  for path in sorted(set(files)):z.write(path,str(path.relative_to(ROOT)))
 archives.append(source)
 results=[]
 for path in archives:
  with zipfile.ZipFile(path) as z:
   assert z.testzip() is None,path
   if path==play:assert z.read('index.html')==(GAME/'portable/index.html').read_bytes()
   else:assert hashlib.sha256(z.read('design/red-rocket/layout-study.blend')).hexdigest()==native
  assert path.stat().st_size<99_000_000,'Split large archive before GitHub upload'
  results.append({'filename':path.name,'bytes':path.stat().st_size,'sha256':digest(path)})
 (DEST/'red-rocket-downloads.json').write_text(json.dumps(results,indent=2)+'\n')
 print(json.dumps(results),flush=True)

if __name__=='__main__':package()
