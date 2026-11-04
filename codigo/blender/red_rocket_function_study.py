"""New Red Rocket Function study. Not final art, runtime export or inherited approval."""
import bpy, math, json, random, hashlib
from pathlib import Path
from mathutils import Vector
ROOT=Path(__file__).resolve().parents[1]/'design/red-rocket'
for sub in ['renders','images','plans','masks','runtime','meshes']:(ROOT/sub).mkdir(parents=True,exist_ok=True)
random.seed(2077)
bpy.ops.object.select_all(action='SELECT');bpy.ops.object.delete(use_global=False)
s=bpy.context.scene;s.unit_settings.system='METRIC';s.render.engine='CYCLES';s.cycles.samples=24;s.cycles.use_denoising=False;s.render.resolution_x=1280;s.render.resolution_y=800;s.render.resolution_percentage=100
s.view_settings.view_transform='AgX';s.world.use_nodes=True
world=s.world.node_tree.nodes.get('Background');world.inputs['Strength'].default_value=.25
sky=s.world.node_tree.nodes.new('ShaderNodeTexSky');sky.sky_type='NISHITA';sky.sun_elevation=.52;sky.sun_rotation=-.8;sky.sun_disc=False;sky.dust_density=2.0;s.world.node_tree.links.new(sky.outputs['Color'],world.inputs['Color'])
objects=[];ceilings=[];wall_records=[];opening_records=[]
def mat(name,a,b=None,scale=7,metal=0):
 m=bpy.data.materials.new(name);m.diffuse_color=(*a,1);m.use_nodes=True
 n=m.node_tree.nodes;l=m.node_tree.links;p=n.get('Principled BSDF');p.inputs['Base Color'].default_value=(*a,1);p.inputs['Roughness'].default_value=.78;p.inputs['Metallic'].default_value=metal
 if b:
  tex=n.new('ShaderNodeTexNoise');tex.inputs['Scale'].default_value=scale;tex.inputs['Detail'].default_value=3
  ramp=n.new('ShaderNodeValToRGB');ramp.color_ramp.elements[0].position=.3;ramp.color_ramp.elements[0].color=(*a,1);ramp.color_ramp.elements[1].position=.7;ramp.color_ramp.elements[1].color=(*b,1)
  l.new(tex.outputs['Fac'],ramp.inputs[0]);l.new(ramp.outputs[0],p.inputs['Base Color'])
  noise=n.new('ShaderNodeTexNoise');noise.inputs['Scale'].default_value=85
  bump=n.new('ShaderNodeBump');bump.inputs['Strength'].default_value=.25;bump.inputs['Distance'].default_value=.025;l.new(noise.outputs['Fac'],bump.inputs['Height']);l.new(bump.outputs['Normal'],p.inputs['Normal'])
 return m
red=mat('Faded vermilion enamel',(.19,.014,.009),(.43,.045,.021),15,.45)
cream=mat('Warm off-white tile',(.40,.38,.30),(.65,.62,.50),18)
blue=mat('Weathered petrol-blue metal',(.035,.095,.11),(.14,.28,.29),9,.4)
steel=mat('Aged aluminium',(.20,.23,.22),(.53,.57,.52),8,.65)
rust=mat('Oxidised dark iron',(.045,.032,.025),(.19,.09,.037),7,.6)
asphalt=mat('Cracked asphalt',(.04,.038,.032),(.13,.12,.09),3)
concrete=mat('Island concrete',(.22,.21,.17),(.49,.46,.36),9)
dirt=mat('Dry shoulder soil',(.13,.10,.06),(.30,.24,.14),4)
glass=mat('Dirty blue window glass',(.028,.065,.08),(.08,.15,.17),15,.25)
black=mat('Rubber and meter face',(.012,.015,.012));yellow=mat('Faded lane markings',(.46,.34,.11));bark=mat('Dead bark',(.10,.065,.035),(.28,.20,.10),12)
white=mat('Letter enamel',(.77,.74,.60));grass=mat('Dry brush',(.26,.22,.10))
def finish(o,name,material,bevel=0,category='prop',group='context'):
 o.name=name;o.data.materials.append(material);o['studyGroup']=group;o['category']=category
 if bevel:
  b=o.modifiers.new('Rounded construction edges','BEVEL');b.width=bevel;b.segments=2
  o.modifiers.new('Weighted normals','WEIGHTED_NORMAL')
 objects.append(o)
 if category=='ceiling':ceilings.append(o)
 return o
def box(name,pos,size,material,bevel=.025,category='prop',group='context'):
 bpy.ops.mesh.primitive_cube_add(size=1,location=pos);o=bpy.context.object;o.dimensions=size;bpy.ops.object.transform_apply(location=False,rotation=False,scale=True)
 return finish(o,name,material,bevel,category,group)
def cylinder(name,pos,r,depth,material,rot=(0,0,0),group='context',verts=32):
 bpy.ops.mesh.primitive_cylinder_add(vertices=verts,radius=r,depth=depth,location=pos,rotation=rot);o=finish(bpy.context.object,name,material,.015,'prop',group)
 for p in o.data.polygons:p.use_smooth=True
 return o
def tube(name,points,r,material,group='context'):
 c=bpy.data.curves.new(name,'CURVE');c.dimensions='3D';c.resolution_u=8;c.bevel_depth=r;c.bevel_resolution=1;sp=c.splines.new('BEZIER');sp.bezier_points.add(len(points)-1)
 for p,co in zip(sp.bezier_points,points):p.co=co;p.handle_left_type=p.handle_right_type='AUTO'
 o=bpy.data.objects.new(name,c);s.collection.objects.link(o);c.materials.append(material);o['studyGroup']=group;o['category']='prop';objects.append(o);return o
def beam(name,a,b,width,material,group):
 mid=(Vector(a)+Vector(b))/2;o=box(name,mid,(width,width,(Vector(b)-Vector(a)).length),material,.015,group=group);o.rotation_euler=(Vector(b)-Vector(a)).to_track_quat('Z','Y').to_euler();return o
def text(name,body,pos,size,material=red,group='architecture'):
 c=bpy.data.curves.new(name,'FONT');c.body=body;c.align_x='CENTER';c.size=size;c.extrude=.014;c.bevel_depth=.002;c.resolution_u=6
 if 'lettering' in name.lower():c.font=bpy.data.fonts.load(str(ROOT/'fonts/OpenSans-ExtraBoldItalic.ttf') if (ROOT/'fonts/OpenSans-ExtraBoldItalic.ttf').exists() else '/usr/share/fonts/truetype/open-sans/OpenSans-ExtraBoldItalic.ttf')
 o=bpy.data.objects.new(name,c);s.collection.objects.link(o);o.location=pos;o.rotation_euler=(math.pi/2,0,0);c.materials.append(material);o['studyGroup']=group;o['category']='sign';objects.append(o);return o
# Terrain and road; the old playable assets remain untouched.
box('Terrain substrate',(0,0,-.28),(64,56,.5),dirt,0,'floor')
box('Station forecourt',(0,-.5,-.07),(40,35,.14),asphalt,.12,'floor')
box('Road strip',(0,-21,-.06),(64,7,.14),asphalt,.06,'floor')
for x in range(-28,29,7):box('Road dashed center',(x,-21,.018),(3,.13,.01),yellow,0,group='road')
for y in [-23.9,-18.1]:box('Road worn edge',(0,y,.018),(64,.08,.01),white,0,group='road')
brick=mat('Weathered terracotta brick',(.17,.075,.04),(.38,.21,.12),16)
# Structural shell. Front-facing single bay and the red personnel entrance match the photo.
box('Building slab',(5.5,8,.08),(19,12.4,.16),concrete,.07,'floor','architecture')
def wall(name,pos,size):
 o=box(name,pos,size,brick,.02,'architecture','architecture');wall_records.append(o);return o
def cut(id,wall_obj,kind,pos,size,destination):
 bpy.ops.mesh.primitive_cube_add(size=1,location=pos);c=bpy.context.object;c.dimensions=size;bpy.ops.object.transform_apply(location=False,rotation=False,scale=True)
 mod=wall_obj.modifiers.new(id+' structural aperture','BOOLEAN');mod.operation='DIFFERENCE';mod.solver='EXACT';mod.object=c;bpy.context.view_layer.objects.active=wall_obj;bpy.ops.object.modifier_apply(modifier=mod.name);bpy.data.objects.remove(c,do_unlink=True)
 opening_records.append({'id':id,'kind':kind,'wall':wall_obj.name,'position':list(pos),'dimensionsMeters':list(size),'widthMeters':size[0] if size[0]>1 else size[1],'heightMeters':size[2],'depthMeters':.3,'sillMeters':round(pos[2]-size[2]/2,3),'destination':destination,'approved':False})
front=wall('South facade',(5.5,2,2.1),(19,.3,4.2));back=wall('North facade',(5.5,14,2.1),(19,.3,4.2));west=wall('Shop west wall',(-4,8,2.1),(.3,12,4.2));east=wall('Garage east wall',(15,8,2.1),(.3,12,4.2));partition=wall('Shop garage partition',(5.2,8,2.1),(.22,12,4.2))
cut('D01',front,'door',(9.5,2,1.65),(6.7,1,3.3),'Garage repair bay with bench and lift')
cut('D02',front,'door',(3.8,2,1.3),(1.3,1,2.6),'Personnel entrance to shop and garage connection')
cut('W01',front,'window',(.45,2,1.85),(2.5,1,1.7),'Shop counter behind glass')
cut('W02',west,'window',(-4,7,1.85),(1,4.8,1.7),'Shop side glazing, rear position estimated')
cut('D03',partition,'door',(5.2,7,1.3),(1,1.5,2.6),'Shop to garage internal route, estimated')
cut('D04',back,'door',(10.5,14,1.3),(1.5,1,2.6),'Rear apron, estimated from functional circulation')
# Prefabricated silver structural framing over brick, separate from the actual cut walls.
for x in [-3.8,2.75,5.65,13.35,14.9]:
 box('Prefabricated facade pier',(x,1.74,2.08),(.31,.24,4.16),steel,.09,group='architecture')
 for z in [.42,1.25,2.08,2.91,3.74]:box('Pier rolled band',(x,1.58,z),(.36,.10,.06),rust,.015,group='architecture')
for x in [6.03,12.97]:box('Garage inset jamb',(x,1.68,1.67),(.22,.35,3.34),cream,.08,group='architecture')
box('Garage rounded lintel',(9.5,1.64,3.52),(7.25,.40,.35),steel,.10,group='architecture')
for z in [3.40,3.60,3.80]:box('Garage lintel pressed rib',(9.5,1.39,z),(7.1,.045,.045),rust,.015,group='architecture')
for x in [3.09,4.51]:box('Red personnel doorway frame',(x,1.66,1.33),(.13,.25,2.66),red,.045,group='architecture')
box('Personnel door header',(3.8,1.65,2.69),(1.55,.24,.15),steel,.04,group='architecture')
# Open red door leaf lies along the left reveal, keeping the passage truly open.
box('Open red personnel door',(3.16,2.60,1.32),(.08,1.25,2.58),red,.035,group='architecture')
box('Door narrow glazed panel',(3.10,2.65,1.72),(.025,.35,.85),glass,.02,group='architecture')
# Curved metal awning over personnel door, full support against the facade.
verts=[];faces=[]
for dz in [0,.07]:
 for x in [2.95,4.65]:
  for j in range(13):
   a=math.pi*j/24;verts.append((x,1.85-.76*math.sin(a),2.73+.54*math.cos(a)+dz))
n=13
for side in range(2):
 start=side*26
 for j in range(12):faces.append((start+j,start+j+1,start+13+j+1,start+13+j))
for j in range(12):
 for edge in [0,13]:faces.append((edge+j,edge+j+1,26+edge+j+1,26+edge+j))
for j in [0,12]:faces.append((j,j+13,26+j+13,26+j))
mesh=bpy.data.meshes.new('Curved service awning');mesh.from_pydata(verts,[],faces);mesh.update();o=bpy.data.objects.new('Red personnel door awning',mesh);s.collection.objects.link(o);finish(o,o.name,red,0,'architecture','architecture')
box('Shop front glass',(.45,2.01,1.85),(2.38,.045,1.58),glass,.015,group='architecture')
box('Shop side glass',(-4.01,7,1.85),(.045,4.68,1.58),glass,.015,group='architecture')
for x in [-.84,.45,1.74]:box('Shop window mullion',(x,1.77,1.85),(.055,.14,1.8),steel,.018,group='architecture')
box('Shop window sill',(.45,1.72,.97),(2.85,.40,.12),steel,.025,group='architecture')
for i in range(10):box('Raised garage door slat',(9.5,2.25+i*.21,3.41),(6.5,.20,.055),steel,.015,group='architecture')
for z in [.23,.5,.77,1.04,1.31,1.58,1.85,2.12,2.39,2.66,2.93,3.2,3.47,3.74,4.01]:
 for x,w in [(-2.45,2.3),(2.45,.5),(5.2,.8),(14.10,1.4)]:box('Facade horizontal mortar',(x,1.843,z),(w,.011,.012),rust,0,group='architecture')
# Roof, narrow canopy and silver-edged red fascia, sloping gently upward to the left.
box('Building roof substrate',(5.5,8,4.24),(19.8,13,.22),rust,.08,'ceiling','architecture')
def rounded_prism(name,cx,cy,width,depth,z,thick,radius,material,category,group):
 loop=[]
 for x,y,start in [(cx+width/2-radius,cy+depth/2-radius,0),(cx-width/2+radius,cy+depth/2-radius,90),(cx-width/2+radius,cy-depth/2+radius,180),(cx+width/2-radius,cy-depth/2+radius,270)]:
  for i in range(9):
   a=math.radians(start+i*90/8);loop.append((x+math.cos(a)*radius,y+math.sin(a)*radius))
 n=len(loop);verts=[(x,y,z+dz) for dz in [-thick/2,thick/2] for x,y in loop];faces=[tuple(reversed(range(n))),tuple(range(n,n*2))]
 for i in range(n):faces.append((i,(i+1)%n,(i+1)%n+n,i+n))
 mesh=bpy.data.meshes.new(name);mesh.from_pydata(verts,[],faces);mesh.update();o=bpy.data.objects.new(name,mesh);s.collection.objects.link(o);return finish(o,name,material,.025,category,group)
# The small double bends visible in the reference are retained, not a generic wing polygon.
frontline=[(-18,-2.7),(-14,-2.9),(-10,-2.5),(-6,-1.7),(-2,-.6),(1,1.20),(5,1.20),(9,1.20),(13,1.20),(15.35,1.55)]
outline=frontline+[(15.35,14.5),(-4.40,14.5),(-4.40,5.4),(-18,5.4)]
def roof_z(x):return 4.38+max(0,-x)*.045
verts=[(x,y,roof_z(x)+dz) for dz in [-.17,.17] for x,y in outline];n=len(outline)
faces=[tuple(reversed(range(n))),tuple(range(n,n*2))]+[(i,(i+1)%n,(i+1)%n+n,i+n) for i in range(n)]
mesh=bpy.data.meshes.new('Continuous canopy and roof');mesh.from_pydata(verts,[],faces);mesh.update();o=bpy.data.objects.new('Continuous canopy roof substrate',mesh);s.collection.objects.link(o);finish(o,o.name,steel,.07,'ceiling','canopy')
for i in range(len(frontline)-1):
 x1,y1=frontline[i];x2,y2=frontline[i+1];z1=roof_z(x1);z2=roof_z(x2)
 # Broad silver band plus recessed red center strip. Segments meet at continuous substrate.
 beam('Roof red fascia segment',(x1,y1-.01,z1),(x2,y2-.01,z2),.30,red,'canopy')
 for dz in [-.23,.23]:tube('Canopy silver rolled edge',[(x1,y1-.04,z1+dz),(x2,y2-.04,z2+dz)],.095,steel,'canopy')
 beam('Fascia panel joint',(x1,y1-.16,z1-.24),(x1,y1-.16,z1+.24),.045,rust,'canopy')
for x,y,size in [(15.35,8,(.28,13,.47)),(5.5,14.5,(19.8,.28,.47))]:box('Building rear roof rim',(x,y,4.40),size,red,.06,'ceiling','architecture')
# Two pierced A-frames. Each solid tapered leg is cut by four real cylinders.
def frame_leg(name,foot,peak,y):
 top=roof_z(peak)-.17;side=-1 if foot<peak else 1
 def center(t):return foot+(peak-foot)*t+side*.52*math.sin(math.pi*t)
 samples=[j/12 for j in range(13)];points=[]
 for t in samples:points.append((center(t)-(.76-.26*t),.055+(top-.055)*t))
 for t in reversed(samples):points.append((center(t)+(.76-.26*t),.055+(top-.055)*t))
 n=len(points);verts=[(x,y+dy,z) for dy in [-.15,.15] for x,z in points]
 faces=[tuple(reversed(range(n))),tuple(range(n,n*2))]+[(i,(i+1)%n,(i+1)%n+n,i+n) for i in range(n)]
 mesh=bpy.data.meshes.new(name);mesh.from_pydata(verts,[],faces);mesh.update();leg=bpy.data.objects.new(name,mesh);s.collection.objects.link(leg);finish(leg,name,rust,.035,'architecture','canopy')
 for j,t in enumerate([.18,.38,.58,.78]):
  x=center(t);z=.055+(top-.055)*t;r=.32-.10*t
  bpy.ops.mesh.primitive_cylinder_add(vertices=24,radius=r,depth=1.0,location=(x,y,z),rotation=(math.pi/2,0,0));c=bpy.context.object
  m=leg.modifiers.new('Applied circular lightening hole','BOOLEAN');m.operation='DIFFERENCE';m.solver='EXACT';m.object=c;bpy.context.view_layer.objects.active=leg;bpy.ops.object.modifier_apply(modifier=m.name);bpy.data.objects.remove(c,do_unlink=True)
  probe=bpy.data.objects.new('Support aperture center',None);s.collection.objects.link(probe);probe.location=(x,y,z);probe['target']=leg.name;probe.hide_render=True
 box('A-frame foundation plate',(foot,y,.03),(1.45,.70,.06),steel,.025,group='canopy')
 return leg
for y in [-1.65,3.7]:
 frame_leg('A-frame leg left',-15,-10,y);frame_leg('A-frame leg right',-5,-10,y)
# Near-vertical all-red rocket and its three narrow outside pods.
axis=Vector((.14,-.035,.9895)).normalized();base=Vector((-10,1.05,9.35));rotation=axis.to_track_quat('Z','Y');rocket=[]
def rocket_point(x,y,z):return base+rotation@Vector((x,y,z))
def lathe(name,rings,material,offset=(0,0,0)):
 n=48;verts=[];faces=[];offset=Vector(offset)
 for h,r in rings:
  for i in range(n):
   a=math.tau*i/n;verts.append(tuple(rocket_point(r*math.cos(a)+offset.x,r*math.sin(a)+offset.y,h+offset.z)))
 for j in range(len(rings)-1):
  for i in range(n):faces.append((j*n+i,j*n+(i+1)%n,(j+1)*n+(i+1)%n,(j+1)*n+i))
 faces.extend([tuple(reversed(range(n))),tuple(range((len(rings)-1)*n,len(rings)*n))]);mesh=bpy.data.meshes.new(name);mesh.from_pydata(verts,[],faces);mesh.update();o=bpy.data.objects.new(name,mesh);s.collection.objects.link(o);finish(o,name,material,0,'prop','rocket');rocket.append(o)
 for p in mesh.polygons:p.use_smooth=True
 return o
lathe('Rocket red fuselage',[(-1.30,.30),(-.9,.48),(0,.53),(1.5,.56),(3.0,.49),(4.1,.34),(4.9,.17),(5.35,.015)],red)
lathe('Rocket central exhaust',[(-1.50,.29),(-1.25,.37),(-1.1,.32)],rust)
for z,r in [(-.90,.50),(1.5,.575),(3.05,.50),(4.12,.35)]:lathe('Rocket panel seam',[(z-.025,r),(z+.025,r)],rust)
for k in range(3):
 a=math.tau*k/3;px=1.30*math.cos(a);py=1.30*math.sin(a)
 lathe('Rocket outer pod',[(-1.5,.21),(-1.25,.26),(-.4,.24),(.6,.20),(1.0,.12),(1.22,.015)],red,(px,py,0))
 # Broad sculpted swept web joining each pod to the main body.
 points=[(.45,-.8),(1.25,-1.1),(1.25,.55),(.48,.05)];verts=[]
 for d in [-.07,.07]:
  for r,z in points:verts.append(tuple(rocket_point(r*math.cos(a)-d*math.sin(a),r*math.sin(a)+d*math.cos(a),z)))
 mesh=bpy.data.meshes.new('Rocket swept web');mesh.from_pydata(verts,[],[(0,3,2,1),(4,5,6,7),(0,1,5,4),(1,2,6,5),(2,3,7,6),(3,0,4,7)]);mesh.update();o=bpy.data.objects.new('Rocket curved stabilizer',mesh);s.collection.objects.link(o);finish(o,o.name,red,.05,'prop','rocket');rocket.append(o)
 endpoint=rocket_point(px,py,-1.49);foot=(endpoint.x-.35,endpoint.y,roof_z(endpoint.x)-.02)
 beam('Rocket long mounting leg',foot,endpoint,.16,steel,'rocket')
# Rooftop lettering belongs to the workshop, and is not on the left canopy fascia.
fontpath=str(ROOT/'fonts/DejaVuSerifCondensed-BoldItalic.ttf') if (ROOT/'fonts/DejaVuSerifCondensed-BoldItalic.ttf').exists() else '/usr/share/fonts/truetype/dejavu/DejaVuSerifCondensed-BoldItalic.ttf'
font=bpy.data.fonts.load(fontpath);letters='RED ROCKET';widths=[]
for ch in letters:
 if ch==' ':widths.append(.7);continue
 t=text('RR layout glyph',ch,(0,0,0),3.1 if ch=='R' else 2.5,red,'sign');t.data.font=font;bpy.context.view_layer.update();widths.append(t.dimensions.x+.07);objects.remove(t);bpy.data.objects.remove(t,do_unlink=True)
total=sum(widths);cursor=8-total/2
for i,(ch,w) in enumerate(zip(letters,widths)):
 if ch==' ':cursor+=w;continue
 pos=(cursor+w/2,1.08,4.73);size=3.1 if ch=='R' else 2.5
 edge=text('RR sign frame '+ch,ch,pos,size,steel,'sign');edge.data.font=font;edge.data.fill_mode='NONE';edge.data.bevel_depth=.022;edge.data.extrude=.025
 if i not in [2,6]:
  face=text('RR sign face '+ch,ch,(pos[0],pos[1]-.045,pos[2]),size,red,'sign');face.data.font=font;face.data.extrude=.025
 beam('Sign rooftop bracket',(pos[0],1.30,4.55),(pos[0],1.30,4.83),.055,rust,'sign');cursor+=w
# Forecourt pricing landmark from the left of the reference image.
for x in [-16.6,-15.6]:box('Coolant pylon leg',(x,-7,.65),(.10,.14,1.30),rust,.02,group='price')
box('Coolant price pylon',(-16.1,-7,2.05),(2.45,.44,2.40),red,.25,group='price')
box('Coolant display surround',(-16.1,-7.245,2.05),(2.12,.07,2.06),steel,.10,group='price')
box('Coolant price face',(-16.1,-7.29,2.05),(1.94,.025,1.87),cream,.04,group='price')
for title,digits,z in [('CLASS C COOLANT','113  9/10',2.50),('CLASS A COOLANT','103  9/10',1.55)]:
 text('Coolant price class',title,(-16.1,-7.32,z+.23),.13,rust,'price');text('Coolant price digits',digits,(-16.1,-7.33,z-.14),.37,red,'price')
# Overhead dispensers and long sagging hoses replace unsupported generic pedestal pumps.
rounded_prism('Long service island',-9,-.30,14.5,2.2,.09,.18,.65,concrete,'floor','architecture')
for x in [-13,-8.5,-4]:
 z=roof_z(x)-.52
 box('Suspended dispenser body',(x,.3,z),(1.5,1.0,.55),red,.24,group='pump')
 box('Dispenser roof mount',(x,.3,z+.35),(.60,.45,.22),steel,.035,group='pump')
 for y in [-.7,1.3]:
  tube('Suspended dispensing hose',[(x+.4,.3,z-.1),(x+1.5,y,z-1.2),(x+2.3,y,z-1.3),(x+2.7,y,z-.6)],.043,black,'pump')
  beam('Dispensing metal nozzle',(x+2.7,y,z-.6),(x+2.85,y,z-.25),.07,steel,'pump')
 cylinder('Refuelling red bollard',(x,-.8,.72),.16,1.26,red,group='context')
 cylinder('Bollard silver base',(x,-.8,.14),.23,.20,steel,group='context')
# Functional interior destinations, kept clear of doorways.
box('Shop counter',(-.1,8.5,.60),(3,1.1,1.2),steel,.09,group='bench')
box('Counter metal top',(-.1,8.5,1.24),(3.15,1.2,.09),cream,.045,group='bench')
box('Red workshop bench',(9.6,12.3,.48),(3.8,.95,.96),red,.09,group='bench')
box('Workshop bench metal top',(9.6,12.3,1.02),(3.95,1.06,.12),steel,.04,group='bench')
box('Garage tool backing',(9.6,13.67,1.8),(3.8,.12,1.3),rust,.04,group='bench')
for x in [8.2,8.8,9.4,10,10.6]:box('Bench drawer handle',(x,11.78,.73),(.32,.045,.045),steel,.012,group='bench')
for x in [6,13.5]:
 cylinder('Garage lift post',(x,8.3,1.5),.16,3.0,rust,group='architecture');cylinder('Lift base',(x,8.3,.10),.32,.20,steel,group='architecture')
# Curved red vending silhouette at the garage corner.
box('Red vending machine',(14.05,1.18,1.02),(.85,.70,2.04),red,.22,group='vending')
box('Vending recessed front',(14.05,.80,1.13),(.57,.04,1.15),rust,.10,group='vending')
box('Vending opening rim',(14.05,.77,1.13),(.43,.06,.85),steel,.08,group='vending')
box('Vending dark glass',(14.05,.73,1.13),(.32,.025,.72),glass,.05,group='vending')
text('Vending wordmark','COLA',(14.05,.79,1.81),.15,white,'vending')
box('Rear utility slab',(9,17,.06),(11,5,.12),concrete,.04,'floor')

# Reuse the project's own authored curved coupe as two static wreck studies.
# Keep the original geometry/source and omit only small loose trim/tread pieces.
car_manifest=json.loads((ROOT.parent/'props.json').read_text())['assets'][0]['acceptedMesh']
car_source=ROOT.parent/'oficina-do-vale.blend'
assert hashlib.sha256(car_source.read_bytes()).hexdigest()==car_manifest['sha256']
with bpy.data.libraries.load(str(car_source),link=False) as (available,loaded):
 loaded.objects=[name for name in car_manifest['objects'] if name in available.objects]
car_templates=[]
for ob in loaded.objects:
 if ob is None:continue
 wm=ob.matrix_world.copy();corners=[wm@Vector(v) for v in ob.bound_box]
 dims=[max(v[i] for v in corners)-min(v[i] for v in corners) for i in range(3)]
 if max(dims)<.4:continue
 if ob.type not in ['MESH','CURVE','FONT']:continue
 car_templates.append(ob)
from mathutils import Matrix
for instance,(target,yaw) in enumerate([((10,-11,0),.2),((-17,9,0),-1.0)]):
 transform=Matrix.Translation(target)@Matrix.Rotation(yaw+.45,4,'Z')@Matrix.Translation((4,.5,0))
 for template in car_templates:
  assert template.parent is None, 'Car source gained a parent; normalize before reuse'
  ob=template.copy();s.collection.objects.link(ob);ob.matrix_world=transform@template.matrix_basis;ob.name='Wreck '+str(instance)+' '+template.name;ob['studyGroup']='wreck';ob['category']='prop';ob['wreckInstance']=instance;objects.append(ob)
  for mod in ob.modifiers:
   if mod.type=='BEVEL':mod.segments=2
  if ob.type=='CURVE':ob.data=ob.data.copy();ob.data.bevel_resolution=1;ob.data.resolution_u=4
  if instance==1 and template.name.startswith(('Coupe pressed','Curved coupe roof')):
   ob.data=ob.data.copy();ob.data.materials.clear();ob.data.materials.append(red)
# Grounded dry grass ribbons at pavement edges, kept out of the arrival and garage route.
for center in [(-13,-9),(0,-12),(17,-3),(-16,10),(17,13)]:
 for plant in range(12):
  x=center[0]+random.uniform(-2,2);y=center[1]+random.uniform(-1.4,1.4);verts=[];faces=[]
  for blade in range(9):
   a=random.random()*math.tau;h=random.uniform(.24,.65);w=.022;dx=math.cos(a);dy=math.sin(a);start=len(verts)
   verts.extend([(x-dy*w,y+dx*w,.004),(x+dy*w,y-dx*w,.004),(x+dx*.13+dy*w/2,y+dy*.13-dx*w/2,h*.65),(x+dx*.13-dy*w/2,y+dy*.13+dx*w/2,h*.65),(x+dx*.29,y+dy*.29,h)])
   faces.extend([(start,start+1,start+2,start+3),(start+3,start+2,start+4)])
  mesh=bpy.data.meshes.new('Dry grass clump');mesh.from_pydata(verts,[],faces);mesh.update();ob=bpy.data.objects.new('Dry roadside tussock',mesh);s.collection.objects.link(ob);finish(ob,ob.name,grass,0,'prop','context')

for x,y in [(17,14),(18,12),(-14,11)]:
 cylinder('Oil barrel',(x,y,.55),.36,1.10,rust,group='context')
 for z in [.25,.8]:cylinder('Barrel rolled hoop',(x,y,z),.375,.045,steel,group='context')
# Curbed landscaping and dead roadside trees establish an open exterior.
def taper_branch(name,points,radii):
 c=bpy.data.curves.new(name,'CURVE');c.dimensions='3D';c.resolution_u=6;c.bevel_depth=1;c.bevel_resolution=2
 sp=c.splines.new('BEZIER');sp.bezier_points.add(len(points)-1)
 for p,co,r in zip(sp.bezier_points,points,radii):p.co=co;p.radius=r;p.handle_left_type=p.handle_right_type='AUTO'
 o=bpy.data.objects.new(name,c);s.collection.objects.link(o);c.materials.append(bark);o['studyGroup']='context';o['category']='prop';objects.append(o)
for x,y in [(-14,13),(18,-8),(21,18),(18,24),(-16,22)]:
 taper_branch('Weathered irregular tree trunk',[(x,y,0),(x+.13,y-.12,1.8),(x-.12,y+.2,3.8),(x+.28,y+.1,5.2)],[.23,.16,.09,.018])
 for k in range(5):
  a=k*1.7;z=2+k*.5;ex=x+math.cos(a)*(1.3+random.random());ey=y+math.sin(a)*(1.3+random.random())
  taper_branch('Tapered broken branch',[(x,y,z),(x+(ex-x)*.6,y+(ey-y)*.6,z+.5),(ex,ey,z+1.5)],[.09,.05,.006])
for i in range(42):
 x,y=random.choice([(-16,16),(20,-9),(20,20),(-15,-17)]);x+=random.uniform(-3,3);y+=random.uniform(-3,3)
 bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=1,radius=1,location=(x,y,.12));o=bpy.context.object;o.scale=(random.uniform(.15,.5),random.uniform(.15,.45),random.uniform(.08,.18));finish(o,'Shoulder stones',concrete,0,'prop','context')
for i in range(20):
 x,y=random.choice([(-13,15),(18,19),(17,-11)]);x+=random.uniform(-3,3);y+=random.uniform(-3,3)
 for k in range(3):
  a=k*2.1;tube('Dry grass stems',[(x,y,.01),(x+math.cos(a)*.1,y+math.sin(a)*.1,.35)],.012,grass)
# Uneven asphalt fracture lines and failed road paint soften the clean new-station appearance.
for k in range(24):
 x=random.uniform(-16,16);y=random.uniform(-16,0);pts=[(x,y,.006)]
 for j in range(4):x+=random.uniform(-.6,.6);y+=random.uniform(.25,.85);pts.append((x,y,.006))
 tube('Forecourt asphalt fracture',pts,.009,rust,'road')
# Distant terrain is a visual backdrop only, outside the walkable station bounds.
verts=[];faces=[];n=80
for r in [24,90]:
 for i in range(n):
  a=math.tau*i/n;h=0 if r==24 else 2.5+1.4*math.sin(a*4)+.5*math.cos(a*11);verts.append((math.cos(a)*r,math.sin(a)*r,h-.15))
for i in range(n):faces.append((i,(i+1)%n,(i+1)%n+n,i+n))
mesh=bpy.data.meshes.new('Low terrain horizon');mesh.from_pydata(verts,[],faces);mesh.update();o=bpy.data.objects.new('Distant dry terrain backdrop',mesh);s.collection.objects.link(o);finish(o,o.name,dirt,0,'backdrop','context')
# Clear approach and a secondary route around the islands.
for x in [-11,-7,-3,1]:box('Worn forecourt parking line',(x,-12,.012),(.06,3,.012),yellow,0,group='road')
import sys
sys.path.insert(0,str(Path(__file__).resolve().parent))
from red_rocket_similarity import refine_reference
refine_reference(globals())
bpy.ops.object.light_add(type='SUN',location=(-12,-15,25));sun=bpy.context.object;sun.rotation_euler=(math.radians(27),math.radians(-20),math.radians(-35));sun.data.energy=3.0;sun.data.color=(1.0,.88,.74);sun.data.angle=.10
bpy.ops.object.light_add(type='AREA',location=(-8,-5,16));fill=bpy.context.object;fill.data.energy=1000;fill.data.shape='DISK';fill.data.size=18
bpy.ops.object.light_add(type='AREA',location=(9,7,3.4));interior=bpy.context.object;interior.data.energy=70;interior.data.color=(1,.72,.45);interior.data.size=3
bpy.ops.object.camera_add(location=(-10,-24,1.7));camera=bpy.context.object;s.camera=camera;camera.data.lens=17.66;camera.rotation_euler=(Vector((-.6,3,3.5))-camera.location).to_track_quat('-Z','Y').to_euler()
bpy.context.view_layer.update()
# Fast authoring check only: never overwrite the reviewed source or evidence package.
if '--preview' in sys.argv:
 s.render.resolution_x=800;s.render.resolution_y=500;s.cycles.samples=8;s.render.filepath=str(ROOT/'renders'/'draft-proportions.png');bpy.ops.render.render(write_still=True);print('DRAFT_PREVIEW_ONLY_COMPLETE',flush=True);raise SystemExit(0)
# Save proxy-free native study before render-only visibility/camera changes.
source=ROOT/'layout-study.blend';bpy.ops.wm.save_as_mainfile(filepath=str(source));source_sha=hashlib.sha256(source.read_bytes()).hexdigest()
metadata=[];deps=bpy.context.evaluated_depsgraph_get();triangles=0
for o in objects:
 evaluated=o.evaluated_get(deps)
 if o.type in ['MESH','CURVE','FONT']:
  mesh=evaluated.to_mesh();mesh.calc_loop_triangles();triangles+=len(mesh.loop_triangles);verts=[o.matrix_world@v.co for v in mesh.vertices];evaluated.to_mesh_clear()
  metadata.append({'id':o.name,'group':o.get('studyGroup'),'category':o.get('category'),'bounds':[[min(v[k] for v in verts) for k in range(3)],[max(v[k] for v in verts) for k in range(3)]]})
(ROOT/'study-objects.json').write_text(json.dumps({'sourceSha256':source_sha,'triangles':triangles,'objects':metadata},indent=2))
(ROOT/'study-openings.json').write_text(json.dumps(opening_records,indent=2))
manifest={'sourceSha256':source_sha,'generator':'Blender 4.3.2 native Function study','referenceStatus':'Reference-guided revision against references/primary-reference.json; metric dimensions and unseen rear/interior remain estimates.','captures':[]}
def render(relative):
 s.render.filepath=str(ROOT/relative);bpy.ops.render.render(write_still=True);manifest['captures'].append({'path':relative,'sha256':hashlib.sha256((ROOT/relative).read_bytes()).hexdigest(),'sourceSha256':source_sha,'camera':{'location':list(camera.location),'rotationEuler':list(camera.rotation_euler),'type':camera.data.type,'lensMm':camera.data.lens,'orthoScale':camera.data.ortho_scale},'resolution':[s.render.resolution_x,s.render.resolution_y],'world':s.get('reviewWorld','authoring')})
render('renders/concept-perspective.png')
# A closer review viewpoint follows the source screenshot; it is not the runtime camera.
original_camera=(camera.location.copy(),camera.rotation_euler.copy(),camera.data.lens)
camera.location=(-15,-21,1.7);camera.data.lens=20;camera.rotation_euler=(Vector((-.5,3,5.1))-camera.location).to_track_quat('-Z','Y').to_euler()
render('renders/reference-framing.png')
camera.location=(4,-2.5,2.3);camera.data.lens=32;camera.rotation_euler=(Vector((5.4,2,2.5))-camera.location).to_track_quat('-Z','Y').to_euler()
render('renders/material-closeup.png')
camera.location=original_camera[0];camera.rotation_euler=original_camera[1];camera.data.lens=original_camera[2]
# Top-down engineering images derived from actual geometry, separate upper layer.
clay=mat('Engineering gray',(.64,.64,.64));s.view_layers[0].material_override=clay;s.render.resolution_x=1100;s.render.resolution_y=1000;s.cycles.samples=8
camera.data.type='ORTHO';camera.data.ortho_scale=65;camera.location=(0,0,65);camera.rotation_euler=(0,0,0);camera.rotation_euler=(Vector((0,0,0))-camera.location).to_track_quat('-Z','Y').to_euler()
for o in ceilings+rocket:o.hide_render=True
render('plans/lower-room.png')
for o in ceilings+rocket:o.hide_render=False
render('plans/reflected-ceiling.png')
# Front elevation makes the garage/shop destinations and canopy extent reviewable.
camera.location=(0,-45,4);camera.rotation_euler=(Vector((0,4,4))-camera.location).to_track_quat('-Z','Y').to_euler();camera.data.ortho_scale=36
render('plans/south-elevation.png')
s.view_layers[0].material_override=None;s.render.resolution_x=800;s.render.resolution_y=650;s.cycles.samples=16
# Isolated studies use a neutral background, recorded in each capture.
background=s.world.node_tree.nodes.get('Background')
for link in list(background.inputs['Color'].links):s.world.node_tree.links.remove(link)
background.inputs['Color'].default_value=(.38,.38,.38,1);background.inputs['Strength'].default_value=.6;s['reviewWorld']='neutral studio backdrop for isolated mesh review'

for name,groups,pos,target in [
 ('rocket',{'rocket'},(-20,-15,13.5),(-9.5,1,10.2)),
 ('canopy',{'canopy'},(-29,-25,12),(-5,3,2.8)),
 ('pump',{'pump'},(-18,-8,6),(-11.8,.3,3.6)),
 ('workshop',{'bench'},(4,7,3.2),(9.6,12.3,.6)),
 ('price',{'price'},(-20,-12,3.5),(-16.1,-7,1.7)),
 ('sign',{'sign'},(7,-20,8),(8,1,5.8)),
 ('vending',{'vending'},(11,-4,2.7),(14.05,1.18,1)),
 ('wreck',{'wreck'},(-4,-21,4),(4,-13,1.0))]:
 for o in objects:
  visible=o.get('studyGroup') in groups
  if name=='pump' and visible:
   points=[o.matrix_world@Vector(v) for v in o.bound_box];visible=max(v.x for v in points)<-9.5
  if name=='wreck':visible=visible and o.get('wreckInstance')==0
  if name=='workshop':visible=o.name.startswith(('Red workshop bench','Workshop bench metal top','Bench drawer handle'))
  o.hide_render=not visible
 camera.data.type='PERSP';camera.data.lens=45;camera.location=pos;camera.rotation_euler=(Vector(target)-camera.location).to_track_quat('-Z','Y').to_euler();render('images/'+name+'-study.png')
(ROOT/'study-render-manifest.json').write_text(json.dumps(manifest,indent=2))
print('RED_ROCKET_FUNCTION_STUDY_COMPLETE',source_sha,'triangles',triangles,'objects',len(objects),'openings',len(opening_records),flush=True)
