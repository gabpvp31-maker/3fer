"""Create a self-contained offline Red Rocket HTML; never overwrite the old ZIP."""
from pathlib import Path
import base64, json, re, zipfile

ROOT = Path(__file__).resolve().parents[1]

def data_url(path, mime):
    return 'data:' + mime + ';base64,' + base64.b64encode((ROOT / path).read_bytes()).decode('ascii')

def script(source):
    return '<script>' + re.sub(r'</script', r'<\\/script', source, flags=re.I) + '</script>'

def build():
    manifest = json.loads((ROOT / 'assets/runtime-manifest.json').read_text())
    manifest['model'] = data_url(manifest['model'], 'model/gltf-binary')
    for item in manifest['materials'].values():
        for tier, path in item['color'].items():
            item['color'][tier] = data_url(path, 'image/jpeg')
        for semantic in ['roughness', 'height']:
            path = item[semantic]
            item[semantic] = data_url(path, 'image/png' if path.endswith('.png') else 'image/jpeg')
    manifest['colliders'] = json.loads((ROOT / 'assets/prop-colliders.json').read_text())
    physics = re.sub(r'^export ', '', (ROOT / 'src/physics.mjs').read_text(), flags=re.M)
    app = re.sub(r'^import .*?;\n', '', (ROOT / 'src/app.mjs').read_text(), count=1)
    original = "if(!manifest){const response=await fetch('assets/runtime-manifest.json');if(!response.ok)throw Error('manifest');manifest=await response.json();}"
    assert original in app, 'Update portable bundler after changing the loader'
    app = app.replace(original, 'if(!manifest)manifest=PORTABLE_MANIFEST;')
    colliders = "if(!manifest.colliders){const response=await fetch('assets/prop-colliders.json');if(!response.ok)throw Error('colliders');manifest.colliders=await response.json();}"
    assert colliders in app
    app = app.replace(colliders, "if(!manifest.colliders)throw Error('Missing embedded collisions');")
    html = (ROOT / 'index.html').read_text()
    html = html.replace('<link rel="stylesheet" href="src/style.css">', '<style>' + (ROOT / 'src/style.css').read_text() + '</style>')
    start = html.index('<script src="vendor/three.min.js">')
    html = html[:start] + ''.join(script((ROOT / f).read_text()) for f in ['vendor/three.min.js', 'vendor/GLTFLoader.js']) + script('(()=>{\nconst PORTABLE_MANIFEST=' + json.dumps(manifest) + ';\n' + physics + '\ntry{\n' + app + '\n}catch(error){document.getElementById("status").textContent="Não foi possível iniciar o mapa. Use um navegador atualizado com WebGL ativado.";console.error(error);}})();') + '</body></html>'
    folder = ROOT / 'portable'
    folder.mkdir(exist_ok=True)
    (folder / 'index.html').write_text(html)
    print('RED_ROCKET_PORTABLE_READY', len(html.encode()), flush=True)

if __name__ == '__main__':
    build()
