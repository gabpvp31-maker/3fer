"""Check native source geometry against the visible reference's defining features."""
import bpy,json,sys,hashlib
from pathlib import Path
import numpy as np
from mathutils import Vector
from mathutils.bvhtree import BVHTree
ROOT=Path(__file__).resolve().parents[1]/'design/red-rocket'
def bounds(obj):
 deps=bpy.context.evaluated_depsgraph_get();evaluated=obj.evaluated_get(deps);mesh=evaluated.to_mesh()
 pts=[obj.matrix_world@v.co for v in mesh.vertices];evaluated.to_mesh_clear()
 return np.array([tuple(p) for p in pts])
def check_scene():
 issues=[];measurements={};scene=bpy.context.scene
 body=scene.objects.get('Rocket red fuselage')
 if body is None:issues.append('Missing red rocket fuselage')
 else:
  pts=bounds(body);eig,axes=np.linalg.eigh(np.cov(pts.T));axis=axes[:,np.argmax(eig)];vertical=abs(float(axis[2]));measurements['rocketAxisVerticalDot']=vertical
  if vertical<.90:issues.append('Rocket must be near vertical, not low-angle')
  color=body.data.materials[0].diffuse_color
  if not(color[0]>color[1]*3 and color[0]>color[2]*3):issues.append('Rocket fuselage must use red enamel')
 legs=[o for o in scene.objects if o.name.startswith('A-frame leg')]
 probes=[o for o in scene.objects if o.name.startswith('Support aperture center')]
 measurements['aFrameLegs']=len(legs);measurements['holeProbes']=len(probes)
 if len(legs)!=4:issues.append('Expected four diagonal A-frame legs')
 if len(probes)!=16:issues.append('Expected sixteen support aperture probes')
 import bmesh
 structure=[]
 for leg in legs:
  evaluated=leg.evaluated_get(bpy.context.evaluated_depsgraph_get());mesh=evaluated.to_mesh();bm=bmesh.new();bm.from_mesh(mesh)
  bad=sum(not edge.is_manifold for edge in bm.edges);volume=bm.calc_volume(signed=True);structure.append({'id':leg.name,'nonManifoldEdges':bad,'signedVolume':volume})
  if bad or volume<=0:issues.append('Support leg must be a closed positive-volume solid: '+leg.name)
  bm.free();evaluated.to_mesh_clear()
 measurements['structuralSupports']=structure

 for probe in probes:
  target=scene.objects.get(probe.get('target',''))
  if target is None:issues.append('Aperture target missing');continue
  tree=BVHTree.FromObject(target,bpy.context.evaluated_depsgraph_get())
  origin=target.matrix_world.inverted()@(probe.location+Vector((0,-.5,0)))
  direction=(target.matrix_world.inverted().to_3x3()@Vector((0,1,0))).normalized()
  hit=tree.ray_cast(origin,direction,1.0)
  if hit[0] is not None:issues.append('Support aperture is blocked: '+probe.name)
 sign=[o for o in scene.objects if o.name.startswith('RR sign face')]
 if not sign:issues.append('Missing workshop rooftop letters')
 else:
  pts=np.concatenate([bounds(o) for o in sign]);measurements['signBounds']=[pts.min(axis=0).tolist(),pts.max(axis=0).tolist()]
  if pts[:,2].min()<4.5 or pts[:,0].mean()<3:issues.append('Lettering must be above workshop, not central canopy fascia')
 for id,x,z in [('D01',9.5,1.7),('D02',3.8,1.25)]:
  wall=scene.objects.get('South facade')
  if wall is None:issues.append('Missing front wall');continue
  tree=BVHTree.FromObject(wall,bpy.context.evaluated_depsgraph_get());inverse=wall.matrix_world.inverted();p=inverse@Vector((x,1.3,z));v=(inverse.to_3x3()@Vector((0,1,0))).normalized()
  if tree.ray_cast(p,v,1.4)[0] is not None:issues.append('Blocked structural aperture '+id)
 if any(o.name.startswith('Canopy structural column') for o in scene.objects):issues.append('Old blue-column canopy remains')
 if not scene.objects.get('Coolant price pylon'):issues.append('Missing coolant price pylon')
 if len([o for o in scene.objects if o.name.startswith('Suspended dispenser body')])!=3:issues.append('Expected three overhead dispenser bodies')
 vehicle=scene.objects.get('Wreck 0 reference curved body')
 if vehicle is None:issues.append('Missing reference-guided vintage car body')
 else:
  ev=vehicle.evaluated_get(bpy.context.evaluated_depsgraph_get());mesh=ev.to_mesh();bm=bmesh.new();bm.from_mesh(mesh);bad=sum(not e.is_manifold for e in bm.edges);volume=bm.calc_volume(signed=True);bm.free();ev.to_mesh_clear()
  tree=BVHTree.FromObject(vehicle,bpy.context.evaluated_depsgraph_get());hit=tree.ray_cast(Vector((0,0,2.5)),Vector((0,0,-1)),3)
  floorZ=None if hit[0] is None else float(hit[0].z)
  measurements['vintageVehicle']={'nonManifoldEdges':bad,'signedVolume':volume,'cockpitFloorZ':floorZ}
  if bad or volume<=0:issues.append('Vintage hull must be a closed positive-volume body')
  if floorZ is None or not .30<floorZ<.50:issues.append('Vintage cockpit must be a real recess with a surviving floor')
  tires=[o for o in scene.objects if o.name.startswith('Wreck 0 narrow vintage tire')]
  if len(tires)!=4:issues.append('Expected four complete vintage tires')
  for tire in tires:
   low=float(bounds(tire)[:,2].min())
   if abs(low)>.005:issues.append('Vintage wheel must contact the forecourt: '+tire.name)
 from bpy_extras.object_utils import world_to_camera_view
 framing={}
 for key in ['rocket','price','sign','wreck']:
  group=[o for o in scene.objects if o.get('studyGroup')==key and o.type in ['MESH','CURVE','FONT'] and (key!='wreck' or o.get('wreckInstance')==0)]
  if not group:issues.append('Missing framing group '+key);continue
  pts=np.concatenate([bounds(o) for o in group]);screen=[world_to_camera_view(scene,scene.camera,Vector(p)) for p in pts]
  limits=[min(p.x for p in screen),max(p.x for p in screen),min(p.y for p in screen),max(p.y for p in screen)];framing[key]=limits
  if limits[0]<.005 or limits[1]>.995 or limits[2]<.005 or limits[3]>.995 or any(p.z<=0 for p in screen):issues.append('Production camera clips '+key)
 measurements['framing']=framing
 return {'ok':not issues,'issues':issues,'measurements':measurements}
if __name__=='__main__':
 source=ROOT/'layout-study.blend';bpy.ops.wm.open_mainfile(filepath=str(source));result=check_scene();result['sourceSha256']=hashlib.sha256(source.read_bytes()).hexdigest()
 if '--negative-vehicle-check' in sys.argv:
  vehicle=bpy.context.scene.objects.get('Wreck 0 reference curved body')
  if vehicle:bpy.data.objects.remove(vehicle,do_unlink=True)
  negative=check_scene();assert not negative['ok'] and 'Missing reference-guided vintage car body' in negative['issues'];print('NEGATIVE_VEHICLE_CHECK_REJECTED',negative['issues']);sys.exit(0)
 if '--negative-check' in sys.argv:
  leg=next((o for o in bpy.context.scene.objects if o.name.startswith('A-frame leg')),None)
  if leg:bpy.data.objects.remove(leg,do_unlink=True)
  negative=check_scene();assert not negative['ok'],'Removing required support must fail';print('NEGATIVE_SUPPORT_CHECK_REJECTED',negative['issues']);sys.exit(0)
 (ROOT/'reference-geometry-audit.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result,indent=2))
 if not result['ok']:raise RuntimeError('Reference geometry checks failed')
