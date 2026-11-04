"""Reference-guided canopy profile and setting. Native study, no runtime export."""
import bpy,math,random
from mathutils import Vector

def rebuild_setting(ctx):
 rng=random.Random(11102015);objects=ctx['objects'];s=ctx['s'];finish=ctx['finish'];box=ctx['box'];mat=ctx['mat'];cyl=ctx['cylinder'];roof_z=ctx['roof_z'];steel=ctx['steel'];rust=ctx['rust'];red=ctx['red']
 for ob in list(objects):
  if ob.name.startswith(('Roof red fascia segment','Canopy silver rolled edge','Fascia panel joint','Road worn edge','Worn forecourt parking line')):
   objects.remove(ob);bpy.data.objects.remove(ob,do_unlink=True)
 # Wide pressed sheet-metal fascia with a folded cross-section and a thin inset red band.
 profile=[(-.12,-.35),(-.24,-.28),(-.28,-.19),(-.28,.19),(-.23,.30),(-.10,.35),(.10,.32),(.13,.20),(.13,-.23),(.07,-.32)]
 line=ctx['frontline']
 for i in range(len(line)-1):
  a=Vector((*line[i],roof_z(line[i][0])));b=Vector((*line[i+1],roof_z(line[i+1][0])));direction=b-a;normal=Vector((-direction.y,direction.x,0)).normalized();verts=[]
  for p in [a,b]:
   for y,z in profile:verts.append(tuple(p+normal*y+Vector((0,0,z))))
  n=len(profile);faces=[tuple(reversed(range(n))),tuple(range(n,n*2))]+[(j,(j+1)%n,(j+1)%n+n,j+n) for j in range(n)]
  mesh=bpy.data.meshes.new('Folded silver canopy fascia');mesh.from_pydata(verts,[],faces);mesh.update();import bmesh;bm=bmesh.new();bm.from_mesh(mesh);bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces));bm.to_mesh(mesh);bm.free();ob=bpy.data.objects.new('Wide profiled metallic fascia',mesh);s.collection.objects.link(ob);finish(ob,ob.name,steel,.018,'ceiling','canopy')
  center=(a+b)/2-normal*.281
  panel=box('Inset red fascia panel',center,(direction.length-.05,.006,.31),red,.002,group='canopy');panel.rotation_euler.z=math.atan2(direction.y,direction.x)
  for p in [a,b]:
   for z in [-.25,.25]:
    q=p-normal*.26+Vector((0,0,z));cyl('Fascia panel fastener',q,.018,.018,rust,(math.pi/2,0,0),group='canopy',verts=8)
 # Keep highlights legible on weathered metal rather than using concrete-scale normal bumps.
 for node in steel.node_tree.nodes:
  if node.bl_idname=='ShaderNodeBump':node.inputs['Distance'].default_value=.0015
  if node.bl_idname=='ShaderNodeBsdfPrincipled':node.inputs['Roughness'].default_value=.52
 # Chipped concrete paving atop the unchanged, continuous floor substrate.
 concrete=mat('Old pale apron slabs',(.22,.205,.17),(.42,.39,.31),5)
 for x in [-9,-6,-3,0,3,6,9,12]:
  for y in [-8,-5,-2]:
   if rng.random()<.17:continue
   w=2.94;d=2.94;clip=rng.uniform(.08,.34)
   loop=[(-w/2+clip,-d/2),(w/2,-d/2),(w/2,d/2-clip),(w/2-clip,d/2),(-w/2,d/2),(-w/2,-d/2+clip)]
   n=len(loop);verts=[(x+a,y+b,z) for z in [-.028,.004] for a,b in loop];faces=[tuple(reversed(range(n))),tuple(range(n,n*2))]+[(j,(j+1)%n,(j+1)%n+n,j+n) for j in range(n)]
   mesh=bpy.data.meshes.new('Chipped apron slab');mesh.from_pydata(verts,[],faces);mesh.update();ob=bpy.data.objects.new('Broken concrete paving slab',mesh);s.collection.objects.link(ob);finish(ob,ob.name,concrete,.003,'floor','context')
 # Worn roadside paint is broken into short pieces; it does not become a raised barrier.
 paint=mat('Dust-covered road paint',(.27,.25,.18),(.43,.40,.29),12)
 for y in [-23.9,-18.1]:
  x=-31
  while x<31:
   length=rng.uniform(.3,1.8)
   if rng.random()>.28:box('Fragmented road-edge paint',(x+length/2,y,.012),(length,.055,.002),paint,0,group='road')
   x+=length+rng.uniform(.08,.6)
 # Grass ribbons share one mesh per bed, avoiding thousands of independent objects.
 dry=mat('Dense dry straw',(.20,.16,.075),(.47,.39,.20),9)
 beds=[(-19,-11,-17,13),(15.5,22,-15,17),(-20,24,17,27),(-11,-5,-14,-11)]
 for bi,(xmin,xmax,ymin,ymax) in enumerate(beds):
  verts=[];faces=[]
  for plant in range(210):
   x=rng.uniform(xmin,xmax);y=rng.uniform(ymin,ymax)
   for blade in range(6):
    a=rng.random()*math.tau;h=rng.uniform(.25,.75);w=rng.uniform(.009,.02);dx=math.cos(a);dy=math.sin(a);j=len(verts)
    verts += [(x-dy*w,y+dx*w,.004),(x+dy*w,y-dx*w,.004),(x+dx*.12+dy*w*.5,y+dy*.12-dx*w*.5,h*.6),(x+dx*.12-dy*w*.5,y+dy*.12+dx*w*.5,h*.6),(x+dx*.27,y+dy*.27,h)]
    faces += [(j,j+1,j+2,j+3),(j+3,j+2,j+4)]
  mesh=bpy.data.meshes.new('Combined dry grass bed');mesh.from_pydata(verts,[],faces);mesh.update();ob=bpy.data.objects.new('Dense roadside grass bed '+str(bi),mesh);s.collection.objects.link(ob);finish(ob,ob.name,dry,0,'prop','context')
 # A deciduous tree belt in the background replaces the empty horizon.
 bark=ctx['bark']
 def branch(verts,faces,points,radii):
  sides=7;start=len(verts)
  for i,(p,r) in enumerate(zip(points,radii)):
   tangent=Vector(points[min(i+1,len(points)-1)])-Vector(points[max(0,i-1)])
   if tangent.length<.001:tangent=Vector((0,0,1))
   rotation=tangent.to_track_quat('Z','Y')
   for k in range(sides):verts.append(tuple(Vector(p)+rotation@Vector((math.cos(k*math.tau/sides)*r,math.sin(k*math.tau/sides)*r,0))))
  for i in range(len(points)-1):
   for k in range(sides):faces.append((start+i*sides+k,start+i*sides+(k+1)%sides,start+(i+1)*sides+(k+1)%sides,start+(i+1)*sides+k))
  faces.extend([tuple(reversed(range(start,start+sides))),tuple(range(start+(len(points)-1)*sides,start+len(points)*sides))])
 positions=[(rng.uniform(-29,29),rng.uniform(19,27)) for _ in range(23)]+[(rng.uniform(-29,-22),rng.uniform(-9,20)) for _ in range(7)]+[(rng.uniform(23,29),rng.uniform(-5,20)) for _ in range(7)]
 for ti,(x,y) in enumerate(positions):
  r=math.hypot(x,y);a=math.atan2(y,x);ground=max(-.03,(2.5+1.4*math.sin(a*4)+.5*math.cos(a*11))*max(0,(r-24)/66)-.15);h=rng.uniform(5,10);verts=[];faces=[]
  branch(verts,faces,[(x,y,ground),(x+.17,y-.10,ground+h*.45),(x-.2,y+.2,ground+h*.8),(x+.25,y,ground+h)],[.20,.14,.075,.012])
  for k in range(8):
   z=ground+h*rng.uniform(.3,.8);a=rng.random()*math.tau;length=rng.uniform(1.0,2.7);end=(x+math.cos(a)*length,y+math.sin(a)*length,z+rng.uniform(.8,1.9))
   branch(verts,faces,[(x,y,z),(x+(end[0]-x)*.5,y+(end[1]-y)*.5,z+.45),end],[.07,.035,.004])
   branch(verts,faces,[(x+(end[0]-x)*.6,y+(end[1]-y)*.6,z+.6),(end[0]+.6*math.sin(a),end[1]-.6*math.cos(a),end[2]-.1)],[.023,.003])
  mesh=bpy.data.meshes.new('Leafless deciduous tree');mesh.from_pydata(verts,[],faces);mesh.update();ob=bpy.data.objects.new('Background leafless tree '+str(ti),mesh);s.collection.objects.link(ob);finish(ob,ob.name,bark,0,'prop','context')
  for polygon in mesh.polygons:polygon.use_smooth=True
 # Clear the core entrance: ground dressing remains outside the declared main walking route.
 s.world.node_tree.nodes.get('Background').inputs['Strength'].default_value=.48
