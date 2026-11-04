"""Verify photo maps actually feed the rendered shader, with portable packed images."""
import bpy,json,hashlib,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]/'design/red-rocket'
def audit():
 records=json.loads((ROOT/'pbr-material-audit.json').read_text())['appliedMaterials'];issues=[]
 def reaches(socket,filename,seen=None):
  seen=set() if seen is None else seen
  for link in socket.links:
   node=link.from_node
   if node.as_pointer() in seen:continue
   seen.add(node.as_pointer())
   if node.bl_idname=='ShaderNodeTexImage' and node.image and Path(node.image.filepath).name==filename:return True
   if any(reaches(i,filename,seen) for i in node.inputs):return True
  return False
 for row in records:
  m=bpy.data.materials.get(row['material']);bs=None if m is None else next((n for n in m.node_tree.nodes if n.bl_idname=='ShaderNodeBsdfPrincipled'),None)
  if bs is None:issues.append('Missing surface shader '+row['material']);continue
  for role,socket in [('albedo','Base Color'),('roughness','Roughness'),('height','Normal')]:
   if not reaches(bs.inputs[socket],row[role]):issues.append('Photo map not driving '+row['material']+' '+role)
   image=next((n.image for n in m.node_tree.nodes if n.bl_idname=='ShaderNodeTexImage' and n.image and Path(n.image.filepath).name==row[role]),None)
   if image is None or not image.packed_file:issues.append('Unpacked/missing image '+row[role]);continue
   expected='sRGB' if role=='albedo' else 'Non-Color'
   if image.colorspace_settings.name!=expected:issues.append('Wrong color space '+row[role])
   if max(image.size)>1024:issues.append('Unexpectedly oversized source image '+row[role])
 return {'ok':not issues,'issues':issues,'materialCount':len(records)}
source=ROOT/'layout-study.blend';bpy.ops.wm.open_mainfile(filepath=str(source));result=audit();result['sourceSha256']=hashlib.sha256(source.read_bytes()).hexdigest()
if '--negative-check' in sys.argv:
 m=bpy.data.materials['Faded vermilion enamel'];bs=next(n for n in m.node_tree.nodes if n.bl_idname=='ShaderNodeBsdfPrincipled')
 for link in list(bs.inputs['Base Color'].links):m.node_tree.links.remove(link)
 negative=audit();assert not negative['ok'];print('DISCONNECTED_ALBEDO_REJECTED',negative['issues']);sys.exit(0)
(ROOT/'pbr-material-validation.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result,indent=2))
if not result['ok']:raise RuntimeError('Photo material validation failed')
