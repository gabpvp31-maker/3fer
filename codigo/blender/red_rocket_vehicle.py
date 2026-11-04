"""Original reference-guided retrofuturistic wreck; the unseen end is an estimate."""
import bpy,math
from mathutils import Vector,Matrix

def build_reference_wreck(ctx,paint):
 objects=ctx['objects'];scene=ctx['s'];finish=ctx['finish'];box=ctx['box'];tube=ctx['tube'];cyl=ctx['cylinder'];black=ctx['black'];steel=ctx['steel'];rust=ctx['rust'];glass=ctx['glass']
 for ob in list(objects):
  if ob.get('wreckInstance')==0:
   objects.remove(ob);bpy.data.objects.remove(ob,do_unlink=True)
 start=len(objects)
 sections=[(-3.0,.72,.42,.97),(-2.65,1.02,.32,1.10),(-1.8,1.15,.28,1.15),(-.8,1.14,.27,1.13),(.8,1.14,.27,1.13),(1.8,1.16,.30,1.22),(2.65,1.02,.38,1.18),(3.0,.65,.51,1.02)]
 n=32;verts=[];faces=[]
 for y,width,low,high in sections:
  for i in range(n):
   a=math.tau*i/n;sn=math.sin(a);cs=math.cos(a)
   x=width*math.copysign(abs(sn)**.52,sn);z=low+(high+.30-low)*(.5+.5*math.copysign(abs(cs)**.42,cs));verts.append((x,y,z))
 for j in range(len(sections)-1):
  for i in range(n):faces.append((j*n+i,j*n+(i+1)%n,(j+1)*n+(i+1)%n,(j+1)*n+i))
 faces.extend([tuple(reversed(range(n))),tuple(range((len(sections)-1)*n,len(sections)*n))])
 mesh=bpy.data.meshes.new('Pressed curved vintage tub');mesh.from_pydata(verts,[],faces);mesh.update();body=bpy.data.objects.new('Wreck 0 reference curved body',mesh);scene.collection.objects.link(body);finish(body,body.name,paint,0,'prop','wreck')
 for p in mesh.polygons:p.use_smooth=True
 def subtract(cutter,label):
  modifier=body.modifiers.new(label,'BOOLEAN');modifier.operation='DIFFERENCE';modifier.solver='EXACT';modifier.object=cutter;bpy.context.view_layer.objects.active=body;bpy.ops.object.modifier_apply(modifier=modifier.name);bpy.data.objects.remove(cutter,do_unlink=True)
 # A real oval cockpit recess with a surviving lower hull, not a dark painted opening.
 bpy.ops.mesh.primitive_cylinder_add(vertices=64,radius=1,depth=2,location=(0,.0,1.39));c=bpy.context.object;c.scale=(.81,1.13,1);bpy.ops.object.transform_apply(location=False,rotation=False,scale=True);subtract(c,'Open oval cockpit')
 for x in [-1.08,1.08]:
  for y in [-1.75,1.78]:
   bpy.ops.mesh.primitive_cylinder_add(vertices=40,radius=.53,depth=.65,location=(x,y,.46),rotation=(0,math.pi/2,0));subtract(bpy.context.object,'Actual rounded wheel arch')
 for x in [-1.08,1.08]:
  for y in [-1.75,1.78]:
   cyl('Wreck 0 narrow vintage tire',(x,y,.46),.46,.25,black,(0,math.pi/2,0),group='wreck',verts=40)
   face=x+(.135 if x>0 else -.135)
   cyl('Wreck 0 dished steel wheel',(face,y,.46),.29,.035,rust,(0,math.pi/2,0),group='wreck',verts=32)
   cyl('Wreck 0 small rounded hub',(face+(.025 if x>0 else -.025),y,.46),.14,.045,steel,(0,math.pi/2,0),group='wreck',verts=24)
 # Oval rolled lip, with large chrome windscreen bows and small surviving glass shards.
 tube('Wreck 0 oval cockpit seal',[(.84*math.cos(i*math.tau/48),1.16*math.sin(i*math.tau/48),1.395) for i in range(49)],.045,rust,'wreck')
 tube('Wreck 0 curved front windscreen bow',[(-.82,-.67,1.40),(-.68,-.89,1.87),(0,-1.02,2.17),(.68,-.89,1.87),(.82,-.67,1.40)],.033,steel,'wreck')
 tube('Wreck 0 windscreen centre stay',[(0,-1.12,1.41),(0,-1.09,1.77),(0,-1.02,2.17)],.024,rust,'wreck')
 tube('Wreck 0 broken rear canopy bow',[(-.81,.73,1.40),(-.62,.99,1.87),(-.18,1.07,2.06)],.028,rust,'wreck')
 for side in [-1,1]:
  pts=[(side*.81,-.69,1.43),(side*.66,-.90,1.85),(side*.37,-.91,1.50),(side*.61,-.79,1.57)]
  data=bpy.data.meshes.new('Broken curved windscreen glass');data.from_pydata(pts,[],[(0,1,2),(0,2,3)]);data.update();ob=bpy.data.objects.new('Wreck 0 windscreen glass remnant',data);scene.collection.objects.link(ob);finish(ob,ob.name,glass,0,'prop','wreck')
 for x in [-.39,.39]:
  box('Wreck 0 seat pedestal',(x,.25,.545),(.40,.50,.31),rust,.025,group='wreck')
  box('Wreck 0 exposed seat cushion',(x,.25,.80),(.59,.69,.20),black,.10,group='wreck')
  seat=box('Wreck 0 worn curved seat back',(x,.63,1.205),(.59,.17,.61),black,.11,group='wreck');seat.rotation_euler.x=-.12
 box('Wreck 0 aged dashboard',(0,-.86,1.36),(1.38,.22,.20),rust,.09,group='wreck')
 tube('Wreck 0 steering rim',[(-.38+.19*math.cos(i*math.tau/24),-.59,1.29+.19*math.sin(i*math.tau/24)) for i in range(25)],.018,black,'wreck')
 ctx['beam']('Wreck 0 steering column',(-.38,-.59,1.29),(-.38,-.89,1.25),.04,rust,'wreck')
 for a in [0,math.tau/3,math.tau*2/3]:ctx['beam']('Wreck 0 steering spoke',(-.38,-.59,1.29),(-.38+.19*math.cos(a),-.59,1.29+.19*math.sin(a)),.015,steel,'wreck')
 for side in [-1,1]:
  tube('Wreck 0 long side beltline',[(side*w*1.005,y,1.06+.03*math.cos(y)) for y,w,lo,hi in sections],.027,steel,'wreck')
  tube('Wreck 0 high rear-fender ridge',[(side*.91,1.0,1.43),(side*1.13,1.8,1.53),(side*.98,2.55,1.52),(side*.57,3,1.35)],.025,rust,'wreck')
 for y,sign in [(-2.96,-1),(2.96,1)]:
  tube('Wreck 0 wraparound chrome bumper',[(-1.02,y-sign*.20,.51),(-.80,y,.48),(0,y+sign*.08,.46),(.80,y,.48),(1.02,y-sign*.20,.51)],.065,steel,'wreck')
  for x in [-.60,.60]:
   bpy.ops.mesh.primitive_cylinder_add(vertices=24,radius=.15,depth=.5,location=(x,y,.84),rotation=(math.pi/2,0,0));subtract(bpy.context.object,'Actual vintage lamp recess')
   cyl('Wreck 0 recessed round lamp',(x,y,.84),.14,.06,black,(math.pi/2,0,0),group='wreck',verts=24)
  if sign<0:box('Wreck 0 oval grille',(0,y-.055,.72),(.88,.07,.20),rust,.08,group='wreck')
 bevel=body.modifiers.new('Rolled exposed sheet-metal edges','BEVEL');bevel.width=.025;bevel.segments=2;body.modifiers.new('Pressed panel normals','WEIGHTED_NORMAL')
 # Normalize once so all pieces, including wheels and seat, share one authored placement.
 transform=Matrix.Translation((4,-13,0))@Matrix.Rotation(-.2,4,'Z')
 for ob in objects[start:]:
  ob['studyGroup']='wreck';ob['category']='prop';ob['wreckInstance']=0;ob['provenance']='Original native reference-guided vintage tub, no imported game mesh';ob.matrix_world=transform@ob.matrix_basis
