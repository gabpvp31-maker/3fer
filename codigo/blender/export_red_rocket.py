"""Export the explicitly requested Red Rocket without modifying the native source.

Metre-scale face UV projection preserves photographic tiling. Mesh reduction,
spatial batching and baked vertex occlusion keep the offline renderer light.
Run: blender -b -t 4 --python-exit-code 1 --python blender/export_red_rocket.py
"""
import bpy, collections, hashlib, json, math, sys, time
from pathlib import Path
import numpy as np
from mathutils import Vector
from mathutils.bvhtree import BVHTree

sys.path.insert(0, str(Path(__file__).resolve().parent))
from quantize_vertex_colors import quantize_vertex_colors
ROOT = Path(__file__).resolve().parents[1]
D = ROOT / 'design/red-rocket'
OUT = ROOT / 'red-rocket'
A = OUT / 'assets'
A.mkdir(parents=True, exist_ok=True)
sha = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()
source = D / 'layout-study.blend'
source_sha = sha(source)
authorization = json.loads((D / 'export-authorization.json').read_text())
assert authorization['sourceSha256'] == source_sha, 'Export authorization is stale'
assert authorization['userInstruction'] == 'então exporta'
for name in ['pbr-material-validation.json', 'reference-geometry-audit.json']:
    audit = json.loads((D / name).read_text())
    assert audit['sourceSha256'] == source_sha and not audit['issues'], name
bpy.ops.wm.open_mainfile(filepath=str(source))
scene = bpy.context.scene
scene.view_settings.view_transform = 'Standard'
scene.view_settings.look = 'None'
scene.view_settings.exposure = 0
scene.view_settings.gamma = 1
scene.render.image_settings.file_format = 'JPEG'
scene.render.image_settings.color_mode = 'RGB'
scene.render.image_settings.quality = 87
photo = json.loads((D / 'pbr-material-audit.json').read_text())['appliedMaterials']
recipes = {}
materials = {}
textures = {}

def image_pixels(filename):
    image = bpy.data.images.load(str(D / 'materials' / filename), check_existing=True)
    values = np.empty(image.size[0] * image.size[1] * 4, dtype=np.float32)
    image.pixels.foreach_get(values)
    return values.reshape((-1, 4)), tuple(image.size)

def write_color(name, values, size):
    image = bpy.data.images.new(name, width=size[0], height=size[1], alpha=False)
    image.pixels.foreach_set(values.ravel())
    image.update()
    result = {}
    for tier, dimension in [('high', 1024), ('low', 512)]:
        if image.size[0] != dimension:
            image.scale(dimension, max(1, round(dimension * size[1] / size[0])))
        path = A / f'{name}-{dimension}.jpg'
        image.save_render(str(path), scene=scene)
        result[tier] = str(path.relative_to(OUT))
    bpy.data.images.remove(image)
    return result

for index, recipe in enumerate(photo):
    key = 'surface' + str(index)
    # Both concretes share the same photographic recipe and material.
    if recipe['material'] == 'Island concrete':
        recipes[recipe['material']] = recipes['Old pale apron slabs']
        continue
    color, size = image_pixels(recipe['albedo'])
    color = color.copy()
    rgb = color[:, :3]
    if recipe['paintTint']:
        mask = np.clip((rgb[:, 0] - rgb[:, 2] - .025) / .185, 0, 1)[:, None]
        rgb[:] = np.asarray(recipe['paintTint']) * (1 - mask) + rgb * mask
    tint = {'Oxidised dark iron': (.45, .40, .34),
            'Weathered terracotta brick': (.65, .62, .55),
            'Old pale apron slabs': (.75, .71, .61),
            'Cracked asphalt': (.80, .76, .66)}.get(recipe['material'])
    if tint:
        rgb *= np.asarray(tint)
    if recipe['material'] == 'Aged aluminium':
        rgb[:] = np.asarray((.38, .41, .37)) * .6 + rgb * .4
    textures[key] = {'color': write_color(key, color, size)}
    # Data maps are copied byte-for-byte; their numeric values remain linear.
    for semantic in ['roughness', 'height']:
        path = A / (key + '-' + semantic + Path(recipe[semantic]).suffix)
        path.write_bytes((D / 'materials' / recipe[semantic]).read_bytes())
        textures[key][semantic] = str(path.relative_to(OUT))
    material = bpy.data.materials.new('runtime_' + key)
    material.diffuse_color = (1, 1, 1, 1)
    materials[key] = material
    recipes[recipe['material']] = (key, recipe['tileMeters'])
materials['vertex'] = bpy.data.materials.new('runtime_vertex')
materials['vertex'].diffuse_color = (1, 1, 1, 1)
print('TEXTURES_READY', len(textures), flush=True)

objects = [o for o in scene.objects if o.type in {'MESH', 'CURVE', 'FONT'} and not o.hide_render]
original_count = len(objects)
source_triangles = 0
evaluated = []
max_bounds_delta = 0
for ob in objects:
    if ob.type == 'FONT':
        ob.data.resolution_u = 2
        ob.data.bevel_resolution = 0
    if ob.type == 'CURVE':
        ob.data.resolution_u = min(ob.data.resolution_u, 4)
        ob.data.bevel_resolution = min(ob.data.bevel_resolution, 1)
    for modifier in ob.modifiers:
        if modifier.type == 'BEVEL':
            modifier.segments = min(modifier.segments, 1)
bpy.context.view_layer.update()
deps = bpy.context.evaluated_depsgraph_get()
records = []
for ob in objects:
    mesh = bpy.data.meshes.new_from_object(ob.evaluated_get(deps), depsgraph=deps)
    records.append((ob.name, ob.type, ob.get('studyGroup'), ob.matrix_world.copy(), mesh))
# Removing the authoring objects in one batch avoids rebuilding a thousands-object
# dependency graph for every small decimation operation.
bpy.data.batch_remove(ids=list(scene.objects))
empty = bpy.data.meshes.new('Export temporary empty')
temporary = bpy.data.objects.new('Export temporary object', empty)
scene.collection.objects.link(temporary)
bpy.context.view_layer.objects.active = temporary
for oi, (name, kind, study_group, matrix, mesh) in enumerate(records):
    mesh.calc_loop_triangles()
    source_triangles += len(mesh.loop_triangles)
    final_mesh = mesh
    if len(mesh.loop_triangles) > 70 and kind != 'FONT':
        original_bounds = [matrix @ v.co for v in mesh.vertices]
        temporary.data = mesh.copy()
        modifier = temporary.modifiers.new('Runtime contour reduction', 'DECIMATE')
        modifier.ratio = .38 if study_group not in {'rocket', 'canopy', 'wreck'} else .55
        bpy.ops.object.modifier_apply(modifier=modifier.name)
        candidate = temporary.data
        new_bounds = [matrix @ v.co for v in candidate.vertices]
        delta = max(abs(f(p[a] for p in original_bounds) - f(p[a] for p in new_bounds)) for a in range(3) for f in [min, max])
        if delta <= .055:
            final_mesh = candidate
            max_bounds_delta = max(max_bounds_delta, delta)
        temporary.data = empty
    runtime = bpy.data.objects.new(name + '_export', final_mesh)
    runtime.matrix_world = matrix
    runtime['sourceName'] = name
    evaluated.append(runtime)
    if oi % 500 == 0:
        print('REDUCING', oi, flush=True)
bpy.data.objects.remove(temporary, do_unlink=True)
print('REDUCED', source_triangles, len(evaluated), flush=True)

# Build one shared BVH for occlusion; no per-frame ray casting or shadow pass.
occlusion_vertices, occlusion_faces = [], []
for ob in evaluated:
    mesh = ob.data
    mesh.calc_loop_triangles()
    offset = len(occlusion_vertices)
    occlusion_vertices.extend(ob.matrix_world @ v.co for v in mesh.vertices)
    occlusion_faces.extend(tuple(offset + i for i in tri.vertices) for tri in mesh.loop_triangles)
bvh = BVHTree.FromPolygons(occlusion_vertices, occlusion_faces, all_triangles=True)
sun_direction = Vector((-5, -8, 12)).normalized()
ambient_directions = [Vector((.7, 0, .7)), Vector((-.7, 0, .7)), Vector((0, .7, .7)), Vector((0, -.7, .7))]
groups = collections.defaultdict(lambda: {'verts': [], 'faces': [], 'uv': [], 'colors': [], 'smooth': []})
colliders = []
collider_excluded = ('Terrain', 'Station forecourt', 'Road ', 'Building slab', 'Long service island', 'Broken concrete', 'Rear utility', 'Shop front glass', 'Shop side glass', 'Distant')

for oi, ob in enumerate(evaluated):
    mesh = ob.data
    mesh.calc_loop_triangles()
    normal_matrix = ob.matrix_world.to_3x3().inverted().transposed()
    world = [ob.matrix_world @ v.co for v in mesh.vertices]
    shade = []
    for vertex, point in zip(mesh.vertices, world):
        normal = (normal_matrix @ vertex.normal).normalized()
        origin = point + normal * .025
        occluded = sum(1 for direction in ambient_directions if direction.dot(normal) > -.15 and bvh.ray_cast(origin, direction, 2.8)[0] is not None)
        sun_blocked = bvh.ray_cast(origin, sun_direction, 40)[0] is not None
        shade.append(max(.32, 1 - occluded * .09 - (.23 if sun_blocked else 0)))
    for triangle in mesh.loop_triangles:
        material = mesh.materials[triangle.material_index] if mesh.materials else None
        recipe = recipes.get(material.name if material else '')
        key, meters = recipe if recipe else ('vertex', [1, 1])
        # Four broad spatial cells cap the material batches without flattening silhouettes.
        center = sum((world[i] for i in triangle.vertices), Vector()) / 3
        cell = (int(center.x >= 0), int(center.y >= 0))
        group = groups[(key, *cell)]
        normal = (normal_matrix @ triangle.normal).normalized()
        axis = max(range(3), key=lambda a: abs(normal[a]))
        axes = (1, 2) if axis == 0 else (0, 2) if axis == 1 else (0, 1)
        base = tuple(material.diffuse_color[:3]) if material and not recipe else (1, 1, 1)
        first = len(group['verts'])
        for i in triangle.vertices:
            p = world[i]
            group['verts'].append(tuple(p))
            group['uv'].append((p[axes[0]] / meters[0], p[axes[1]] / meters[1]))
            group['colors'].append(tuple(c * shade[i] for c in base) + (1,))
        group['faces'].append((first, first + 1, first + 2))
        group['smooth'].append(mesh.polygons[triangle.polygon_index].use_smooth)
    # Ground-level closed props block walking. Structural wall apertures are handled
    # separately below, so broad bounds never close a real entrance.
    bounds = [ob.matrix_world @ Vector(v) for v in ob.bound_box]
    lo = [min(p[a] for p in bounds) for a in range(3)]
    hi = [max(p[a] for p in bounds) for a in range(3)]
    name = ob['sourceName']
    if not name.startswith(collider_excluded) and lo[2] < .5 and hi[2] > .55 and hi[0] - lo[0] > .12 and hi[1] - lo[1] > .12 and not name.startswith(('South facade', 'North facade', 'Shop west wall', 'Garage east wall', 'Shop garage partition', 'Background', 'Dense', 'Ground', 'Dry', 'Wreck ', 'Vintage')):
        colliders.append({'x': (lo[0]+hi[0])/2, 'z': -(lo[1]+hi[1])/2, 'hx': (hi[0]-lo[0])/2, 'hz': (hi[1]-lo[1])/2, 'yaw': 0, 'name': name})
    if oi % 500 == 0:
        print('PROJECTED', oi, flush=True)

for ob in list(scene.objects):
    bpy.data.objects.remove(ob, do_unlink=True)
runtime_objects = []
for (key, x, y), data in sorted(groups.items()):
    mesh = bpy.data.meshes.new(f'batch_{key}_{x}_{y}')
    unique, indices, shared = [], {}, []
    for point in data['verts']:
        token = tuple(round(v, 5) for v in point)
        if token not in indices:
            indices[token] = len(unique)
            unique.append(point)
        shared.append(indices[token])
    mesh.from_pydata(unique, [], [tuple(shared[i] for i in face) for face in data['faces']])
    mesh.update()
    uv = mesh.uv_layers.new(name='PhotographicMeterScale')
    uv.data.foreach_set('uv', np.asarray(data['uv'], dtype=np.float32).ravel())
    colors = mesh.color_attributes.new(name='Color', type='BYTE_COLOR', domain='CORNER')
    colors.data.foreach_set('color', np.asarray(data['colors'], dtype=np.float32).ravel())
    # Restore shared smooth normals across duplicated face vertices.
    normal_sums = collections.defaultdict(lambda: Vector())
    for polygon, smooth in zip(mesh.polygons, data['smooth']):
        polygon.use_smooth = smooth
        if smooth:
            for i in polygon.vertices:
                normal_sums[tuple(round(v, 5) for v in mesh.vertices[i].co)] += polygon.normal
    normals = []
    for polygon in mesh.polygons:
        for i in polygon.vertices:
            normals.append(normal_sums[tuple(round(v, 5) for v in mesh.vertices[i].co)].normalized() if polygon.use_smooth else polygon.normal)
    mesh.normals_split_custom_set(normals)
    mesh.materials.append(materials[key])
    ob = bpy.data.objects.new(mesh.name, mesh)
    scene.collection.objects.link(ob)
    runtime_objects.append(ob)
triangles = sum(len(o.data.polygons) for o in runtime_objects)
assert triangles <= 150000, triangles
assert len(runtime_objects) <= 50, len(runtime_objects)
bpy.ops.object.select_all(action='SELECT')
bpy.context.view_layer.objects.active = runtime_objects[0]
bpy.ops.export_scene.gltf(filepath=str(A / 'map.glb'), export_format='GLB', use_selection=True, export_apply=True, export_yup=True, export_normals=True, export_materials='EXPORT', export_animations=False, export_cameras=False, export_lights=False, export_vertex_color='ACTIVE')

color_quantization = quantize_vertex_colors(A / 'map.glb')
print('COLOR_STORAGE', json.dumps(color_quantization), flush=True)
layout = json.loads((D / 'room-layout.json').read_text())
camera = layout['productionCamera']
convert = lambda p: [p[0], p[2], -p[1]]
manifest = {'schema': 'red-rocket.runtime.v1', 'model': 'assets/map.glb', 'materials': textures,
    'spawn': {'position': convert(camera['location']), 'target': convert(camera['target'])},
    'lighting': {'method': 'Photographic PBR tiles, vertex occlusion and fixed hemisphere/sun; zero dynamic shadow passes', 'dynamicShadowPasses': 0},
    'statistics': {'sourceTriangles': 301370, 'runtimeTriangles': color_quantization['triangles'], 'trianglesBeforeDegenerateRemoval': triangles, 'sourceObjects': original_count, 'runtimeBatches': len(runtime_objects), 'maxBoundsDeltaMeters': max_bounds_delta, 'authoringSourceSha256': source_sha}, 'hashes': {}}
(A / 'prop-colliders.json').write_text(json.dumps(colliders, indent=2) + '\n')
for path in sorted(A.iterdir()):
    if path.name != 'runtime-manifest.json':
        manifest['hashes'][str(path.relative_to(OUT))] = sha(path)
manifest['statistics']['lowBytes'] = (A / 'map.glb').stat().st_size + sum((OUT / item['color']['low']).stat().st_size for item in textures.values())
assert manifest['statistics']['lowBytes'] < 8_000_000, manifest['statistics']['lowBytes']
(A / 'runtime-manifest.json').write_text(json.dumps(manifest, indent=2) + '\n')
(A / 'prop-colliders.json').write_text(json.dumps(colliders, indent=2) + '\n')
(D / 'runtime/export-report.json').write_text(json.dumps(manifest, indent=2) + '\n')
assert sha(source) == source_sha, 'Native source was modified'
print('RED_ROCKET_EXPORT_COMPLETE', json.dumps(manifest['statistics']), flush=True)
