"""Acceptance checks bind the actual GLB, photographic tiers and portable build."""
import hashlib,json,struct,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
GAME=ROOT/'red-rocket'

class RedRocketExport(unittest.TestCase):
 def test_geometry_and_texture_budget_with_native_provenance(self):
  manifest=json.loads((GAME/'assets/runtime-manifest.json').read_text())
  self.assertEqual(manifest['schema'],'red-rocket.runtime.v1')
  native=hashlib.sha256((ROOT/'design/red-rocket/layout-study.blend').read_bytes()).hexdigest()
  self.assertEqual(manifest['statistics']['authoringSourceSha256'],native)
  data=(GAME/manifest['model']).read_bytes()
  magic,version,size=struct.unpack_from('<III',data)
  self.assertEqual((magic,version,size),(0x46546c67,2,len(data)))
  length=struct.unpack_from('<I',data,12)[0];gltf=json.loads(data[20:20+length])
  triangles=0;batches=0
  for mesh in gltf['meshes']:
   for primitive in mesh['primitives']:
    triangles+=gltf['accessors'][primitive['indices']]['count']//3;batches+=1
    for attribute in ['POSITION','NORMAL','TEXCOORD_0','COLOR_0']:
     self.assertIn(attribute,primitive['attributes'])
  self.assertEqual(triangles,manifest['statistics']['runtimeTriangles'])
  self.assertLessEqual(triangles,150000);self.assertLessEqual(batches+1,50)
  self.assertFalse(gltf.get('images'),'High-tier images must load lazily')
  self.assertLess(manifest['statistics']['lowBytes'],8_000_000)
  for name,digest in manifest['hashes'].items():
   self.assertEqual(hashlib.sha256((GAME/name).read_bytes()).hexdigest(),digest,name)
  self.assertEqual(len(manifest['materials']),7)
  from PIL import Image
  for material in manifest['materials'].values():
   for tier,size in [('low',512),('high',1024)]:
    with Image.open(GAME/material['color'][tier]) as image:
     self.assertEqual(image.size[0],size)
     self.assertIn(image.size[1],[size,size//2])

 def test_offline_document_has_no_runtime_fetch_or_module_import(self):
  html=(GAME/'portable/index.html').read_text()
  self.assertIn('RED<br>ROCKET',html)
  self.assertIn('data:model/gltf-binary;base64,',html)
  self.assertNotIn('type="module"',html)
  self.assertNotIn("fetch('assets/",html)
  self.assertNotIn('src="vendor/',html)
  self.assertNotIn('src="src/',html)
