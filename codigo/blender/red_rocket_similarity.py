"""Reference-driven visual-study refinement; no runtime export or approval changes."""
import bpy,math,random
from mathutils import Vector

def refine_reference(ctx):
 objects=ctx['objects'];s=ctx['s'];box=ctx['box'];tube=ctx['tube'];beam=ctx['beam'];cylinder=ctx['cylinder'];mat=ctx['mat'];finish=ctx['finish'];roof_z=ctx['roof_z']
 steel=ctx['steel'];rust=ctx['rust'];red=ctx['red'];black=ctx['black'];cream=ctx['cream'];grass=ctx['grass']
 rng=random.Random(10112015)
 # Peeling enamel uses larger coherent paint/rust regions, not coarse foam-like bump.
 def enamel(material,paint,fade):
  material.diffuse_color=(*paint,1);material.use_nodes=True;n=material.node_tree.nodes;l=material.node_tree.links;n.clear()
  out=n.new('ShaderNodeOutputMaterial');bs=n.new('ShaderNodeBsdfPrincipled');bs.inputs['Metallic'].default_value=.52;bs.inputs['Roughness'].default_value=.67;l.new(bs.outputs[0],out.inputs[0])
  tex=n.new('ShaderNodeTexNoise');tex.inputs['Scale'].default_value=5;tex.inputs['Detail'].default_value=4;tex.inputs['Roughness'].default_value=.72
  ramp=n.new('ShaderNodeValToRGB');cr=ramp.color_ramp;cr.elements[0].position=.22;cr.elements[0].color=(*fade,1);cr.elements[1].position=.54;cr.elements[1].color=(*paint,1)
  for pos,col in [(.61,(.11,.055,.025,1)),(.70,(.29,.20,.12,1)),(.79,(.35,.36,.30,1))]:cr.elements.new(pos).color=col
  l.new(tex.outputs['Fac'],ramp.inputs[0]);l.new(ramp.outputs['Color'],bs.inputs['Base Color'])
  fine=n.new('ShaderNodeTexNoise');fine.inputs['Scale'].default_value=190;fine.inputs['Detail'].default_value=2
  bump=n.new('ShaderNodeBump');bump.inputs['Strength'].default_value=.27;bump.inputs['Distance'].default_value=.002;l.new(fine.outputs['Fac'],bump.inputs['Height']);l.new(bump.outputs[0],bs.inputs['Normal'])
 enamel(red,(.34,.033,.016),(.51,.14,.065))
 carpaint=mat('Faded blue exposed-body enamel',(.06,.17,.19));enamel(carpaint,(.055,.16,.17),(.20,.32,.30))
 # Mortar and bricks use metre-scale projections that work on axis-aligned front/side walls.
 brick=bpy.data.materials.get('Weathered terracotta brick');n=brick.node_tree.nodes;l=brick.node_tree.links;n.clear()
 out=n.new('ShaderNodeOutputMaterial');bs=n.new('ShaderNodeBsdfPrincipled');bs.inputs['Roughness'].default_value=.94;l.new(bs.outputs[0],out.inputs[0])
 geo=n.new('ShaderNodeNewGeometry');sep=n.new('ShaderNodeSeparateXYZ');l.new(geo.outputs['Position'],sep.inputs[0]);add=n.new('ShaderNodeMath');add.operation='ADD';l.new(sep.outputs['X'],add.inputs[0]);l.new(sep.outputs['Y'],add.inputs[1]);combine=n.new('ShaderNodeCombineXYZ');l.new(add.outputs[0],combine.inputs['X']);l.new(sep.outputs['Z'],combine.inputs['Y'])
 bricks=n.new('ShaderNodeTexBrick');bricks.inputs['Scale'].default_value=1;bricks.inputs['Brick Width'].default_value=.34;bricks.inputs['Row Height'].default_value=.135;bricks.inputs['Mortar Size'].default_value=.012;bricks.inputs['Mortar Smooth'].default_value=.01
 bricks.inputs['Color1'].default_value=(.24,.105,.052,1);bricks.inputs['Color2'].default_value=(.12,.065,.034,1);bricks.inputs['Mortar'].default_value=(.31,.29,.23,1)
 l.new(combine.outputs[0],bricks.inputs['Vector']);l.new(bricks.outputs['Color'],bs.inputs['Base Color']);bump=n.new('ShaderNodeBump');bump.inputs['Strength'].default_value=.5;bump.inputs['Distance'].default_value=.008;bump.invert=True;l.new(bricks.outputs['Fac'],bump.inputs['Height']);l.new(bump.outputs[0],bs.inputs['Normal'])
 # Strip the nearby wreck's intact glazing/roof to match the open abandoned silhouette.
 for ob in list(objects):
  if ob.name.startswith('Facade horizontal mortar') or (ob.name.startswith('Wreck 0 ') and any(x in ob.name for x in ['Curved coupe roof','Cracked windshield','Side glass panel','Rear window'])):
   objects.remove(ob);bpy.data.objects.remove(ob,do_unlink=True);continue
  if ob.name.startswith('Wreck 0 Coupe pressed'):
   ob.data=ob.data.copy();ob.data.materials.clear();ob.data.materials.append(carpaint)
  if ob.name.startswith(('Road dashed center','Road worn edge','Worn forecourt parking line')):
   ob.dimensions.z=.002;ob.location.z=.012
 # Pale fractured forecourt, embedded dirt patches and broken pavement edges.
 old=bpy.data.materials.get('Cracked asphalt');n=old.node_tree.nodes
 ramp=next((node for node in n if node.bl_idname=='ShaderNodeValToRGB'),None)
 if ramp:
  ramp.color_ramp.elements[0].color=(.15,.14,.11,1);ramp.color_ramp.elements[1].color=(.33,.30,.23,1)
 for node in n:
  if node.bl_idname=='ShaderNodeBump':node.inputs['Distance'].default_value=.012
 soil=mat('Dust and old gravel between concrete',(.17,.145,.09),(.31,.28,.19),9)
 leafmats=[mat('Dry roof ivy olive',(.19,.21,.095),(.35,.33,.18),15),mat('Dry roof ivy straw',(.30,.24,.12),(.49,.43,.24),14)]
 def leaf(name,center,a,length,width,material,group='context'):
  c=Vector(center);u=Vector((math.cos(a),math.sin(a),rng.uniform(-.8,.8))).normalized();v=Vector((-math.sin(a),math.cos(a),rng.uniform(-.8,.8))).normalized();points=[c-u*length*.5,c-u*length*.2+v*width,c+u*length*.3+v*width*.65,c+u*length*.5,c+u*length*.3-v*width*.65,c-u*length*.2-v*width,c+Vector((0,0,.012))]
  mesh=bpy.data.meshes.new(name);mesh.from_pydata(points,[],[(i,(i+1)%6,6) for i in range(6)]);mesh.update();ob=bpy.data.objects.new(name,mesh);s.collection.objects.link(ob);finish(ob,name,material,0,'prop',group)
 # All vines originate on the actual canopy surface. Their tips remain above head clearance.
 for i,(x0,y0) in enumerate([(-17.5,-2.73),(-15.4,-2.83),(-12,-2.70),(-8,-2.1),(-6,-1.7),(-4,-1.1),(-2.6,-.77),(-1.4,-.24),(1,1.2),(3,1.2),(7.7,1.2),(12.6,1.2)]):
  for strand in range(9):
   x=x0+rng.uniform(-.45,.45);y=y0-.12-rng.uniform(0,.12);z=roof_z(x)+.18;drop=rng.uniform(.45,1.30)
   tube('Roof-rooted hanging vine',[(x,y+.25,z),(x+.12,y,z-.27),(x-.12,y-.08,z-drop*.65),(x+.05,y-.12,z-drop)],.012,rust,'canopy')
   for j in range(12):
    t=j/12;center=(x+.12*math.sin(t*6),y-.05-t*.12,z-.17-drop*t)
    leaf('Hanging dry ivy leaf',center,rng.random()*math.tau,.19,.067,leafmats[(i+j)%2],'canopy')
 # Pavement weeds: low shrubs with many small leaves, not rigid sticks.
 for cx,cy in [(-16,-10),(-11,-13),(-2,-11),(16,-4),(18,10),(-16,10),(6,-16)]:
  for shrub in range(12):
   x=cx+rng.uniform(-1.5,1.5);y=cy+rng.uniform(-1.0,1.0);h=rng.uniform(.35,.80)
   tube('Dry shrub stem',[(x,y,.006),(x+.05,y,h*.7),(x+.18,y+.05,h)],.011,rust)
   for k in range(20):
    a=rng.random()*math.tau;t=rng.uniform(.15,.95);center=(x+math.cos(a)*.18,y+math.sin(a)*.18,h*t)
    leaf('Dry shrub leaf',center,a,.22,.055,leafmats[k%2])
 # Irregular dirt/gravel patches are overlays; the closed ground slab stays intact.
 for i in range(28):
  x,y=rng.choice([(-16,-10),(17,-5),(-13,7),(-4,-12),(8,-15)]);x+=rng.uniform(-2,2);y+=rng.uniform(-1.3,1.3);rx=rng.uniform(.25,1.0);ry=rng.uniform(.15,.6)
  points=[]
  for j in range(9):
   a=j*math.tau/9;r=rng.uniform(.7,1);points.append((x+math.cos(a)*rx*r,y+math.sin(a)*ry*r,.003))
  mesh=bpy.data.meshes.new('Irregular soil in broken paving');mesh.from_pydata(points,[],[tuple(range(9))]);mesh.update();ob=bpy.data.objects.new('Dust in pavement break',mesh);s.collection.objects.link(ob);finish(ob,ob.name,soil,0,'prop','context')
 # Reference industrial equipment: vent fans, pipes and meter housings stay clear of apertures.
 for x in [2.1,5.0]:
  box('Wall vent housing',(x,1.7275,2.55),(.73,.25,.78),steel,.10,group='architecture')
  cylinder('Wall ventilation fan',(x,1.58,2.55),.30,.05,black,(math.pi/2,0,0),group='architecture',verts=32)
  for r in [.10,.20,.30]:
   tube('Vent concentric grille',[(x+math.cos(a)*r,1.54,2.55+math.sin(a)*r) for a in [j*math.tau/24 for j in range(25)]],.012,steel,'architecture')
  for a in [j*math.pi/4 for j in range(4)]:beam('Vent grille crossbar',(x+math.cos(a)*.3,1.52,2.55+math.sin(a)*.3),(x-math.cos(a)*.3,1.52,2.55-math.sin(a)*.3),.018,steel,'architecture')
  box('Facade meter case',(x,1.71,1.22),(.32,.28,.48),cream,.07,group='architecture')
  tube('Meter conduit',[(x,1.825,.3),(x,1.825,.95),(x+.22,1.825,1.2),(x+.22,1.825,2.15)],.025,rust,'architecture')
 for x in [6.04,12.96]:
  tube('Garage external conduit',[(x,1.37,.2),(x,1.37,3.7),(x+.15,1.37,3.95),(9.5,1.37,3.95)],.027,steel,'architecture')
  for z in [.5,1.5,2.5,3.65]:beam('Conduit support bracket',(x,1.505,z),(x,1.37,z),.032,steel,'architecture')
 # A small concrete landscape curb mirrors the rounded entrance edge, outside the main route.
 tube('Rounded entrance curb',[(-18,-14,.075),(-15,-14,.075),(-12,-13.5,.075),(-11,-12.5,.075),(-12,-11.9,.075)],.10,ctx['concrete'])
 # Thin distant infrastructure fills the empty skyline visible behind the station.
 tx,ty=25,21
 for dx,dy in [(-1.9,-1.9),(-1.9,1.9),(1.9,-1.9),(1.9,1.9)]:
  beam('Distant pylon tapered leg',(tx+dx,ty+dy,0),(tx+dx*.32,ty+dy*.32,11),.08,steel,'context')
 for z in [2,4,6,8]:
  w=1.9-(z/11)*1.3
  for y in [-w,w]:
   beam('Distant pylon lattice',(tx-w,ty+y,z),(tx+w*.8,ty+y*.8,z+2),.045,steel,'context');beam('Distant pylon lattice',(tx+w,ty+y,z),(tx-w*.8,ty+y*.8,z+2),.045,steel,'context')
 for z,w in [(8,4.4),(10.6,3.2)]:beam('Transmission cross arm',(tx-w,ty,z),(tx+w,ty,z),.08,steel,'context')
 for dx in [-3,3]:tube('Distant sagging transmission cable',[(tx+dx,ty,10.6),(2+dx,ty+1,8.0),(-26+dx,ty+2,9.6)],.017,rust)
 # Original procedural blue sky and cloud layers; the same world lights the authored scene.
 world=s.world;nodes=world.node_tree.nodes;links=world.node_tree.links;bg=nodes.get('Background')
 coord=nodes.new('ShaderNodeTexCoord');sep=nodes.new('ShaderNodeSeparateXYZ');links.new(coord.outputs['Normal'],sep.inputs[0])
 height=nodes.new('ShaderNodeMapRange');height.inputs['From Min'].default_value=-.08;height.inputs['From Max'].default_value=.85;links.new(sep.outputs['Z'],height.inputs['Value'])
 sky=nodes.new('ShaderNodeValToRGB');sky.color_ramp.elements[0].color=(.46,.61,.74,1);sky.color_ramp.elements[1].color=(.055,.22,.46,1);links.new(height.outputs[0],sky.inputs[0])
 stretch=nodes.new('ShaderNodeVectorMath');stretch.operation='MULTIPLY';stretch.inputs[1].default_value=(2.0,2.0,5.0);links.new(coord.outputs['Normal'],stretch.inputs[0])
 noise=nodes.new('ShaderNodeTexNoise');noise.inputs['Scale'].default_value=2.1;noise.inputs['Detail'].default_value=4.5;noise.inputs['Roughness'].default_value=.67;links.new(stretch.outputs[0],noise.inputs['Vector'])
 cloud=nodes.new('ShaderNodeValToRGB');cloud.color_ramp.elements[0].position=.48;cloud.color_ramp.elements[0].color=(0,0,0,1);cloud.color_ramp.elements[1].position=.67;cloud.color_ramp.elements[1].color=(.95,.95,.95,1);links.new(noise.outputs['Fac'],cloud.inputs[0])
 mix=nodes.new('ShaderNodeMixRGB');links.new(cloud.outputs['Color'],mix.inputs[0]);links.new(sky.outputs['Color'],mix.inputs[1]);mix.inputs[2].default_value=(.86,.88,.86,1);links.new(mix.outputs[0],bg.inputs['Color']);bg.inputs['Strength'].default_value=.70
 s['reviewWorld']='authored procedural blue sky and clouds'
 # The closest vehicle now has a bespoke vintage hull, not the earlier coupe shell.
 from red_rocket_vehicle import build_reference_wreck
 build_reference_wreck(ctx,carpaint)
 # Wider rounded prefabricated corners and the visible pressed-metal garage header.
 for ob in objects:
  if ob.name.startswith('Prefabricated facade pier') and (ob.location.x<-3 or ob.location.x>14):
   ob.dimensions.x=.64;ob.dimensions.y=.34
 for x in [7.25,9.5,11.75]:
  box('Garage upper pressed-metal panel',(x,1.69,3.89),(2.19,.20,.48),steel,.055,group='architecture')
  for z in [3.68,4.10]:box('Garage header panel rolled seam',(x,1.56,z),(2.14,.035,.035),rust,.012,group='architecture')
 # Dimensional lettering has a deeper metal return, as visible on the primary reference.
 for ob in objects:
  if ob.name.startswith('RR sign frame'):ob.data.extrude=.06;ob.data.bevel_depth=.028
 from red_rocket_setting import rebuild_setting
 rebuild_setting(ctx)
 from red_rocket_pbr import apply_photo_materials
 apply_photo_materials(ctx)
 # Render quality is separate from the mesh; no denoiser is assumed available.
 s.cycles.samples=64;s.cycles.use_adaptive_sampling=True;s.cycles.adaptive_threshold=.035
