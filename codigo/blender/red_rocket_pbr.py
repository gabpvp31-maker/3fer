"""Photo-based CC0 PBR surfaces, world-scale box projection and paint recolouring."""
import bpy,json,hashlib
from pathlib import Path

def apply_photo_materials(ctx):
 root=ctx['ROOT'];folder=root/'materials';sources=json.loads((folder/'sources.json').read_text())
 for name,record in sources['files'].items():assert hashlib.sha256((folder/name).read_bytes()).hexdigest()==record['sha256'],name
 applied=[]
 def setup(name,albedo,rough,height,meters,paint=None,tint=None,metal=.0,relief=.006,photoWeight=1):
  material=bpy.data.materials.get(name)
  if material is None:return
  material.use_nodes=True;n=material.node_tree.nodes;l=material.node_tree.links;n.clear()
  output=n.new('ShaderNodeOutputMaterial');bs=n.new('ShaderNodeBsdfPrincipled');bs.inputs['Metallic'].default_value=metal;l.new(bs.outputs[0],output.inputs[0])
  geometry=n.new('ShaderNodeNewGeometry');mapping=n.new('ShaderNodeVectorMath');mapping.operation='MULTIPLY';mapping.inputs[1].default_value=(1/meters[0],1/meters[1],1/meters[0]);l.new(geometry.outputs['Position'],mapping.inputs[0])
  def photo(filename,color):
   image=bpy.data.images.load(str(folder/filename),check_existing=True);image.colorspace_settings.name='sRGB' if color else 'Non-Color';image.pack()
   node=n.new('ShaderNodeTexImage');node.image=image;node.projection='BOX';node.projection_blend=.12;node.extension='REPEAT';l.new(mapping.outputs[0],node.inputs['Vector']);return node
  color=photo(albedo,True);color_socket=color.outputs['Color']
  if paint:
   sep=n.new('ShaderNodeSeparateColor');sep.mode='RGB';l.new(color_socket,sep.inputs[0]);difference=n.new('ShaderNodeMath');difference.operation='SUBTRACT';l.new(sep.outputs['Red'],difference.inputs[0]);l.new(sep.outputs['Blue'],difference.inputs[1])
   mask=n.new('ShaderNodeMapRange');mask.inputs['From Min'].default_value=.025;mask.inputs['From Max'].default_value=.21;l.new(difference.outputs[0],mask.inputs['Value'])
   mix=n.new('ShaderNodeMixRGB');mix.inputs[1].default_value=(*paint,1);l.new(mask.outputs[0],mix.inputs[0]);l.new(color_socket,mix.inputs[2]);color_socket=mix.outputs[0]
  if tint:
   multiply=n.new('ShaderNodeMixRGB');multiply.blend_type='MULTIPLY';multiply.inputs[0].default_value=1;multiply.inputs[2].default_value=(*tint,1);l.new(color_socket,multiply.inputs[1]);color_socket=multiply.outputs[0]
  if photoWeight<1:
   mix=n.new('ShaderNodeMixRGB');mix.inputs[0].default_value=photoWeight;mix.inputs[1].default_value=(.38,.41,.37,1);l.new(color_socket,mix.inputs[2]);color_socket=mix.outputs[0]
  l.new(color_socket,bs.inputs['Base Color']);roughness=photo(rough,False);l.new(roughness.outputs['Color'],bs.inputs['Roughness'])
  bump=n.new('ShaderNodeBump');bump.inputs['Strength'].default_value=.55;bump.inputs['Distance'].default_value=relief;h=photo(height,False);l.new(h.outputs['Color'],bump.inputs['Height']);l.new(bump.outputs[0],bs.inputs['Normal'])
  applied.append({'material':material.name,'albedo':albedo,'roughness':rough,'height':height,'projection':'world-scale triplanar box','tileMeters':meters,'reliefMeters':relief,'paintTint':paint,'colorSpace':{'albedo':'sRGB','roughness':'Non-Color','height':'Non-Color'},'packed':True})
 rust=('rusty_metal_04_diff_1k.jpg','rusty_metal_04_rough_1k.jpg','rusty_metal_04_disp_1k.png')
 setup('Faded vermilion enamel',*rust,[1.5,1.5],paint=(.36,.036,.018),metal=.10,relief=.002)
 setup('Faded blue exposed-body enamel',*rust,[1.5,1.5],paint=(.045,.14,.18),metal=.12,relief=.002)
 setup('Aged aluminium',*rust,[1.5,1.5],metal=.65,relief=.0015,photoWeight=.4)
 setup('Oxidised dark iron',*rust,[1.5,1.5],tint=(.45,.40,.34),metal=.20,relief=.003)
 setup('Weathered terracotta brick','Bricks052_1K-JPG_Color.jpg','Bricks052_1K-JPG_Roughness.jpg','Bricks052_1K-JPG_Displacement.jpg',[1.25,1.25],tint=(.65,.62,.55),relief=.009)
 for name in ['Old pale apron slabs','Island concrete']:
  setup(name,'Concrete034_1K-JPG_Color.jpg','Concrete034_1K-JPG_Roughness.jpg','Concrete034_1K-JPG_Displacement.jpg',[1.1,.55],tint=(.75,.71,.61),relief=.005)
 setup('Cracked asphalt','asphalt_02_diff_1k.jpg','asphalt_02_rough_1k.jpg','asphalt_02_disp_1k.png',[2.5,2.5],tint=(.80,.76,.66),relief=.009)
 assert len(applied)==8,applied
 (root/'pbr-material-audit.json').write_text(json.dumps({'sources':'materials/sources.json','appliedMaterials':applied,'runtimeExported':False},indent=2)+'\n')
