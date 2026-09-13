"""Heritage Hall reference-backed exterior detail pass. Run in Blender Python.

All numerical architectural estimates are provisional: see REFERENCES.md.
No external photographs, textures, or runtime network access are used here.
"""
import bpy
import json
import math
import numpy as np
from pathlib import Path
from mathutils import Vector
from mathutils.geometry import tessellate_polygon

ROOT = Path(__file__).resolve().parents[1]
OSM_ID = 403039202
ESTIMATES = {
    'rear_height': 10.5,
    'middle_height': 11.3,
    'front_wall_height': 12.6,
    'canopy_eave_height': 15.0,
    'canopy_crown_rise': 0.9,
    'canopy_overhang': 2.4,
    'canopy_thickness': 0.24,
    'column_radius': 0.28,
    'column_count': 11,
    'entry_recess': 2.1,
    'glazing_module_width': 1.45,
    'cladding_panel_width': 2.8,
    'cladding_panel_height': 1.25,
    'clerestory_low': 12.6,
    'clerestory_high': 14.1,
    'entry_canopy_width': 10.0,
    'entry_canopy_projection': 4.1,
    'entry_canopy_height': 4.65,
}
data = json.loads((ROOT / 'src/data/campus.json').read_text())
way = next(e for e in data['elements'] if e['type'] == 'way' and e['id'] == OSM_ID)
scale = 111320 * math.cos(math.radians(4.3385))
points = [((p['lon'] - 101.137) * scale, -(p['lat'] - 4.3385) * 110540) for p in way['geometry']]
if points[0] == points[-1]:
    points.pop()
cx = (min(p[0] for p in points) + max(p[0] for p in points)) / 2
cz = (min(p[1] for p in points) + max(p[1] for p in points)) / 2
# Model in Blender X east, Y north; export converts to Three.js Y up.
outline = [(x - cx, cz - z) for x, z in points]

bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)
scene = bpy.context.scene
model = bpy.data.collections.new('HERITAGE HALL | Exterior detail study')
scene.collection.children.link(model)
scene.unit_settings.system = 'METRIC'
scene.unit_settings.length_unit = 'METERS'

def material(name, colour, roughness=0.65, metallic=0):
    mat = bpy.data.materials.new(name)
    mat.diffuse_color = (*colour, 1)
    mat.use_nodes = True
    bsdf = mat.node_tree.nodes.get('Principled BSDF')
    bsdf.inputs['Base Color'].default_value = (*colour, 1)
    bsdf.inputs['Roughness'].default_value = roughness
    bsdf.inputs['Metallic'].default_value = metallic
    return mat

concrete = material('Observed pale-grey wall | approximate colour', (0.60, 0.63, 0.61), 0.76)
plain = material('Unverified rear and side massing', (0.43, 0.48, 0.48))
roof = material('Estimated shallow metal roof', (0.34, 0.41, 0.40), 0.48, 0.3)
trim = material('Light structural columns and framing', (0.70, 0.73, 0.69), 0.4, 0.12)
glazing = material('Blue-grey glazing | reflective exterior approximation', (0.20, 0.40, 0.48), 0.16, 0.35)
glazing_light = material('Pale upper glazing | reflective exterior approximation', (0.40, 0.53, 0.51), 0.21, 0.28)
spandrel = material('Blue horizontal façade bands', (0.15, 0.37, 0.45), 0.30, 0.20)
joint = material('Recessed cladding joints', (0.29, 0.34, 0.34), 0.85)
rubber = material('Dark glazing seals', (0.055, 0.075, 0.075), 0.72)
soffit = material('Pale soffit panels', (0.65, 0.68, 0.64), 0.72)
steel = material('Entrance canopy framing', (0.58, 0.64, 0.65), 0.24, 0.7)
tile_light = material('Light paving inlay', (0.66, 0.63, 0.54), 0.85)
tile_dark = material('Grey paving field', (0.30, 0.34, 0.33), 0.90)
recess = material('Recessed entry shadow', (0.075, 0.10, 0.105), 0.8)
plinth = material('Footprint plinth', (0.36, 0.39, 0.36))

# Original procedural surface variation, embedded in GLB. Not photographic data.
rng = np.random.default_rng(403039202)
size = 256
noise = rng.normal(0, 0.008, (size, size, 1))
pixels = np.ones((size, size, 4), dtype=np.float32)
pixels[:, :, :3] = np.clip(np.array([0.60, 0.63, 0.61]) + noise, 0, 1)
image = bpy.data.images.new('Original subtle concrete surface', width=size, height=size)
image.colorspace_settings.name = 'Non-Color'
image.pixels.foreach_set(pixels.ravel())
image.pack()
texture = concrete.node_tree.nodes.new('ShaderNodeTexImage')
texture.image = image
concrete.node_tree.links.new(texture.outputs['Color'], concrete.node_tree.nodes.get('Principled BSDF').inputs['Base Color'])

# Repeated small parts are batched by architectural family/material, keeping
# browser draw calls modest while retaining named editable part families.
batches = {}
def detail_box(name, centre, dimensions, mat, rotation=None):
    key = (name, mat.name)
    verts, faces = batches.setdefault(key, ([], []))
    offset = len(verts)
    signs = [(-1,-1,-1),(1,-1,-1),(1,1,-1),(-1,1,-1),(-1,-1,1),(1,-1,1),(1,1,1),(-1,1,1)]
    for signs_xyz in signs:
        v = Vector(tuple(sign * dimension / 2 for sign, dimension in zip(signs_xyz, dimensions)))
        if rotation is not None:
            v = rotation @ v
        verts.append(tuple(v + Vector(centre)))
    for face in [(0,3,2,1),(4,5,6,7),(0,1,5,4),(1,2,6,5),(2,3,7,6),(3,0,4,7)]:
        faces.append(tuple(offset + i for i in face))

def detail_beam(name, a, b, width, depth, mat):
    direction = Vector(b) - Vector(a)
    detail_box(name, (Vector(a) + Vector(b)) / 2, (width, depth, direction.length), mat,
               direction.to_track_quat('Z', 'Y').to_matrix())

def detail_wall(name, a, b, low, high, thickness, mat):
    from mathutils import Matrix
    dx, dy = b[0] - a[0], b[1] - a[1]
    detail_box(name, ((a[0] + b[0]) / 2, (a[1] + b[1]) / 2, (low + high) / 2),
               (math.hypot(dx, dy), thickness, high-low), mat,
               Matrix.Rotation(math.atan2(dy, dx), 3, 'Z'))

def own(obj, name, mat):
    obj.name = name
    for collection in list(obj.users_collection):
        collection.objects.unlink(obj)
    model.objects.link(obj)
    obj.data.materials.append(mat)
    return obj

def mesh(name, verts, faces, mat):
    data = bpy.data.meshes.new(name)
    data.from_pydata(verts, [], faces)
    data.update()
    obj = bpy.data.objects.new(name, data)
    model.objects.link(obj)
    obj.data.materials.append(mat)
    # Metre-scale planar UVs for original generated material maps.
    uv = data.uv_layers.new(name='Architectural metres')
    for polygon in data.polygons:
        dominant = max(range(3), key=lambda axis: abs(polygon.normal[axis]))
        axes = [axis for axis in range(3) if axis != dominant]
        for loop_index in polygon.loop_indices:
            vertex = data.vertices[data.loops[loop_index].vertex_index].co
            uv.data[loop_index].uv = (vertex[axes[0]] / 3, vertex[axes[1]] / 3)
    return obj

def prism(name, poly, bottom, top, mat):
    n = len(poly)
    vertices = [(x, y, bottom) for x, y in poly] + [(x, y, top) for x, y in poly]
    vecs = [Vector((x, y, 0)) for x, y in poly]
    triangles = tessellate_polygon([vecs])
    indices = {tuple(v): i for i, v in enumerate(vecs)}
    faces = []
    for triangle in triangles:
        ids = [v if isinstance(v, int) else indices[tuple(v)] for v in triangle]
        faces.extend([tuple(reversed(ids)), tuple(i + n for i in ids)])
    for i in range(n):
        j = (i + 1) % n
        faces.append((i, j, j + n, i + n))
    obj = mesh(name, vertices, faces, mat)
    # Recalculate normals to handle clockwise OSM rings consistently.
    bpy.context.view_layer.objects.active = obj
    obj.select_set(True)
    bpy.ops.object.mode_set(mode='EDIT')
    bpy.ops.mesh.select_all(action='SELECT')
    bpy.ops.mesh.normals_make_consistent(inside=False)
    bpy.ops.object.mode_set(mode='OBJECT')
    obj.select_set(False)
    return obj

def box(name, centre, dimensions, mat):
    bpy.ops.mesh.primitive_cube_add(size=1, location=centre)
    obj = own(bpy.context.object, name, mat)
    obj.dimensions = dimensions
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    return obj

def beam(name, a, b, width, depth, mat):
    direction = Vector(b) - Vector(a)
    obj = box(name, (Vector(a) + Vector(b)) / 2, (width, depth, direction.length), mat)
    obj.rotation_euler = direction.to_track_quat('Z', 'Y').to_euler()
    return obj

def wall(name, a, b, low, high, thickness, mat):
    direction = Vector((b[0] - a[0], b[1] - a[1]))
    obj = box(name, ((a[0] + b[0]) / 2, (a[1] + b[1]) / 2, (low + high) / 2),
              (direction.length, thickness, high - low), mat)
    obj.rotation_euler.z = math.atan2(direction.y, direction.x)
    return obj

prism('00 | Exact OSM outline / low plinth', outline, 0, 0.24, plinth)
rear = outline[0:5] + [outline[18], outline[19]]
middle = [outline[4], outline[5], outline[17], outline[18]]
front = outline[5:18]
prism('01 | Rear wing / unverified elevations', rear, 0.24, ESTIMATES['rear_height'], plain)
prism('02 | Middle volume / unverified elevations', middle, 0.24, ESTIMATES['middle_height'], plain)
prism('03 | Rear roof / provisional flat closure', rear, ESTIMATES['rear_height'], ESTIMATES['rear_height'] + 0.25, roof)
prism('04 | Middle roof / provisional flat closure', middle, ESTIMATES['middle_height'], ESTIMATES['middle_height'] + 0.25, roof)

# Front footprint wall segments: central bowed frontage is open at ground level.
for i, a in enumerate(front):
    b = front[(i + 1) % len(front)]
    mid_x, mid_y = (a[0] + b[0]) / 2, (a[1] + b[1]) / 2
    central_front = mid_y < -27 and abs(mid_x) < 25
    if central_front:
        # Recess the glazing and entry behind the observed colonnade.
        a_in = (a[0], a[1] + ESTIMATES['entry_recess'])
        b_in = (b[0], b[1] + ESTIMATES['entry_recess'])
        pane_count = max(1, round(math.dist(a_in, b_in) / ESTIMATES['glazing_module_width']))
        av, bv = Vector(a_in), Vector(b_in)
        for pane in range(pane_count):
            start = av.lerp(bv, pane / pane_count)
            end = av.lerp(bv, (pane + 1) / pane_count)
            for low, high, mat in [(4.2, 5.2, spandrel), (5.2, 8.1, glazing), (8.1, 9.0, spandrel), (9.0, 12.5, glazing_light)]:
                detail_wall('40 | Curtain-wall panes and spandrels', start, end, low, high, 0.09, mat)
            for boundary in [start, end]:
                detail_beam('41 | Glazing seals', (boundary.x, boundary.y-0.08, 4.2), (boundary.x, boundary.y-0.08, 12.5), 0.10, 0.055, rubber)
                detail_beam('42 | Aluminium mullions', (boundary.x, boundary.y-0.13, 4.2), (boundary.x, boundary.y-0.13, 12.5), 0.052, 0.11, trim)
        wall(f'11 | Recessed entrance {i:02}', (a[0], a[1] + 4.0), (b[0], b[1] + 4.0), 0.24, 4.0, 0.2, recess)
        for height in (4.2, 5.2, 6.65, 8.1, 9.0, 10.75, 12.5):
            detail_beam('43 | Horizontal transoms', (a_in[0], a_in[1]-0.13, height), (b_in[0], b_in[1]-0.13, height), 0.065, 0.12, trim)
    else:
        obj = wall(f'05 | Solid façade segment {i:02}', a, b, 0.24, ESTIMATES['front_wall_height'], 0.55, concrete)
        bevel = obj.modifiers.new('Subtle real-scale edge highlight', 'BEVEL')
        bevel.width = 0.028
        bevel.segments = 2
        if mid_y < -17:
            # Fine panel divisions seen in the front photographs; spacing estimated.
            outward = Vector((b[1]-a[1], a[0]-b[0])).normalized()
            if outward.y > 0:
                outward.negate()
            aa, bb = Vector(a) + outward * 0.285, Vector(b) + outward * 0.285
            for z in np.arange(1.25, 12.5, ESTIMATES['cladding_panel_height']):
                detail_beam('44 | Cladding horizontal reveals', (*aa, z), (*bb, z), 0.016, 0.018, joint)
            divisions = max(1, round(math.dist(a, b)/ESTIMATES['cladding_panel_width']))
            for panel in range(1, divisions):
                p = aa.lerp(bb, panel/divisions)
                detail_beam('45 | Cladding vertical reveals', (*p, 0.3), (*p, 12.5), 0.018, 0.018, joint)

    if mid_y < -17:
        # The high-resolution reference shows a glazed/screened strip above the
        # solid wings as well as above the middle curtain wall.
        a_high, b_high = Vector((a[0],a[1]+0.45)), Vector((b[0],b[1]+0.45))
        detail_wall('46 | Continuous upper clerestory', a_high,b_high,12.6,14.1,0.12,glazing_light)
        divisions = max(1, round(math.dist(a_high,b_high)/1.1))
        for index in range(divisions+1):
            p=a_high.lerp(b_high,index/divisions)
            detail_beam('47 | Clerestory vertical framing', (p.x,p.y-0.12,12.6),(p.x,p.y-0.12,14.1),0.055,0.08,trim)
        for z in (12.6,13.0,13.4,13.8,14.1):
            detail_beam('48 | Clerestory horizontal screen', (a_high.x,a_high.y-0.12,z),(b_high.x,b_high.y-0.12,z),0.045,0.10,trim)

# Canopy shell follows the front OSM footprint, expanded by an estimated overhang.
centre_y = sum(p[1] for p in front) / len(front)
canopy = []
for x, y in front:
    dx, dy = x, y - centre_y
    length = math.hypot(dx, dy)
    factor = 1 + ESTIMATES['canopy_overhang'] / max(length, 1)
    canopy.append((dx * factor, centre_y + dy * factor))

def roof_height(x, y):
    return ESTIMATES['canopy_eave_height'] + ESTIMATES['canopy_crown_rise'] * max(0, 1 - (x / 52) ** 2)

vertices = [(x, y, roof_height(x, y)) for x, y in canopy]
vertices.append((0, centre_y, roof_height(0, centre_y) + 0.15))
faces = [(len(canopy), (i + 1) % len(canopy), i) for i in range(len(canopy))]
canopy_obj = mesh('20 | Broad canopy / estimated profile', vertices, faces, roof)
solid = canopy_obj.modifiers.new('Roof sheet thickness', 'SOLIDIFY')
solid.thickness = ESTIMATES['canopy_thickness']
solid.use_even_offset = True
canopy_obj.data.materials.append(soffit)
solid.material_offset = 1
solid.material_offset_rim = 1
for i, a in enumerate(canopy):
    b = canopy[(i + 1) % len(canopy)]
    beam(f'21 | Canopy fascia {i:02}', (*a, roof_height(*a)), (*b, roof_height(*b)), 0.23, 0.2, trim)

# Interpolate the observed bowed frontage from actual outline vertices.
front_edge = sorted(outline[7:16], key=lambda p: p[0])
def frontage_y(x):
    for a, b in zip(front_edge, front_edge[1:]):
        if a[0] <= x <= b[0]:
            t = (x - a[0]) / (b[0] - a[0])
            return a[1] * (1 - t) + b[1] * t
    return front_edge[0 if x < front_edge[0][0] else -1][1]

for i in range(ESTIMATES['column_count']):
    x = -44 + i * 88 / (ESTIMATES['column_count'] - 1)
    y = frontage_y(x) - 0.8
    height = roof_height(x, y) - 0.15
    bpy.ops.mesh.primitive_cylinder_add(vertices=32, radius=ESTIMATES['column_radius'], depth=height - 0.24, location=(x, y, (height + 0.24) / 2))
    obj = own(bpy.context.object, f'30 | Front column {i + 1:02} / spacing estimated', trim)
    for poly in obj.data.polygons:
        poly.use_smooth = len(poly.vertices) == 4

# Interpolate the actual canopy triangles so underside detail cannot poke
# through the roof near its shallower rear edge.
def canopy_surface_z(x, y):
    for face in faces:
        a, b, c = [Vector(vertices[index]) for index in face]
        determinant = (b.y-c.y)*(a.x-c.x)+(c.x-b.x)*(a.y-c.y)
        if abs(determinant) < 1e-8:
            continue
        u = ((b.y-c.y)*(x-c.x)+(c.x-b.x)*(y-c.y))/determinant
        v = ((c.y-a.y)*(x-c.x)+(a.x-c.x)*(y-c.y))/determinant
        w = 1-u-v
        if min(u,v,w) >= -1e-5:
            return u*a.z+v*b.z+w*c.z
    return roof_height(x,y)

# Shallow rafters and soffit divisions are visible in the UTAR close-up and the
# titled 2008 photograph. Their spacing/profile are estimated, not engineering.
for x in np.arange(-44, 44.1, 3.4):
    low_y = frontage_y(x) - 1.3
    high_y = -4.0
    steps = np.linspace(low_y, high_y, 12)
    for a_y,b_y in zip(steps,steps[1:]):
        detail_beam('50 | Canopy soffit ribs', (x,a_y,canopy_surface_z(x,a_y)-0.43), (x,b_y,canopy_surface_z(x,b_y)-0.43), 0.16, 0.26, trim)
    for y in np.arange(low_y, high_y, 3.2):
        if x+3.3 < 45:
            detail_beam('51 | Soffit panel joints', (x,y,canopy_surface_z(x,y)-0.27), (x+3.3,y,canopy_surface_z(x+3.3,y)-0.27),0.018,0.018,joint)

# Framed glass canopy over the central front entrance, confirmed in both UTAR
# photographs. Keep its dimensions explicitly provisional.
entry_y = frontage_y(0)
canopy_back = entry_y + ESTIMATES['entry_recess'] - 0.2
canopy_front = canopy_back - ESTIMATES['entry_canopy_projection']
entry_h = ESTIMATES['entry_canopy_height']
for x in np.linspace(-5,5,7):
    detail_beam('60 | Entrance canopy cross-members',(x,canopy_front,entry_h),(x,canopy_back,entry_h+0.12),0.09,0.13,steel)
for y in (canopy_front, (canopy_front+canopy_back)/2, canopy_back):
    detail_beam('60 | Entrance canopy cross-members',(-5,y,entry_h),(5,y,entry_h),0.12,0.15,steel)
for index in range(6):
    x=-5+(index+0.5)*10/6
    detail_box('61 | Entrance canopy glass', (x,(canopy_front+canopy_back)/2,entry_h+0.065), (10/6-0.10,canopy_back-canopy_front-0.08,0.045),glazing_light)
for x in (-3.35,3.35):
    detail_beam('62 | Canopy suspension rods',(x,canopy_back,7.05),(x,canopy_front,entry_h),0.045,0.045,steel)

# Central doors and sidelights seen through the sheltered entrance. No rooms.
door_y=entry_y+3.84
for x in (-2.9,-1.2,1.2,2.9):
    width=1.0 if abs(x)>2 else 2.32
    detail_box('63 | Entry door and sidelight glass',(x,door_y,2.0),(width,0.06,3.45),glazing)
for x in (-3.45,-2.38,0,2.38,3.45):
    detail_box('64 | Entrance door frames',(x,door_y-0.06,2.0),(0.07,0.13,3.5),steel)
for z in (0.28,3.0,3.75):
    detail_box('64 | Entrance door frames',(0,door_y-0.06,z),(7.0,0.13,0.07),steel)
for x in (-0.24,0.24):
    detail_beam('65 | Door pull handles',(x,door_y-0.20,1.25),(x,door_y-0.20,1.93),0.035,0.045,steel)

# Small entrance apron only. Pattern is a visual interpretation of the visible
# light/dark paving; this is not a surveyed landscape or circulation plan.
detail_box('66 | Entrance apron base',(0,entry_y+0.15,0.27),(15.2,7.2,0.10),tile_dark)
for row in range(10):
    for column in range(21):
        x=(column-10)*0.7
        y=entry_y-3.0+row*0.7
        mat=tile_light if (row%3==0 or (column%3==0 and row%3==1)) else tile_dark
        detail_box('67 | Paving inlay pattern',(x,y,0.33),(0.682,0.682,0.025),mat)

for (name, material_name), (vertices, faces) in batches.items():
    mesh(name, vertices, faces, bpy.data.materials[material_name])

model_objects = list(model.objects)
for obj in model_objects:
    obj['osm_way_id'] = OSM_ID
    obj['review_status'] = 'Exterior detail study; measurements remain estimates; see REFERENCES.md'

output = ROOT / 'public/models'
previews = ROOT / 'public/previews'
source = ROOT / 'models/heritage-hall'
for directory in (output, previews, source):
    directory.mkdir(parents=True, exist_ok=True)
bpy.ops.object.select_all(action='DESELECT')
for obj in model_objects:
    obj.select_set(True)
bpy.context.view_layer.objects.active = model_objects[0]
bpy.ops.export_scene.gltf(filepath=str(output / 'heritage-hall.glb'), export_format='GLB', use_selection=True, export_apply=True, export_extras=True, export_yup=True)
metadata = {
    'osmWayId': OSM_ID, 'name': 'Heritage Hall', 'stage': 'exterior-detail-review',
    'origin': {'x': cx, 'z': cz}, 'units': 'metres', 'estimates': ESTIMATES,
    'referenceUrl': 'https://about.utar.edu.my/virtual-tour/utar-kampar-campus/',
    'notes': 'Detailed reference-backed front glazing, cladding, clerestory, soffit and entrance canopy. Rear elevations and dimensions remain unverified.',
    'meshCount': len(model_objects),
}
(output / 'heritage-hall.json').write_text(json.dumps(metadata, indent=2) + '\n')

# Presentation elements are excluded from GLB, but retained in the editable file.
bpy.ops.object.select_all(action='DESELECT')
bpy.ops.mesh.primitive_plane_add(size=1000, location=(0, 0, -0.03))
ground = bpy.context.object
ground.name = 'RENDER ONLY | studio ground'
ground.data.materials.append(material('Studio neutral', (0.19, 0.23, 0.24), 0.85))
scene.world.use_nodes = True
scene.world.node_tree.nodes['Background'].inputs['Color'].default_value = (0.65, 0.74, 0.82, 1)
scene.world.node_tree.nodes['Background'].inputs['Strength'].default_value = 0.55
bpy.ops.object.light_add(type='SUN', location=(60, -80, 120))
sun = bpy.context.object
sun.name = 'RENDER ONLY | warm sun'
sun.rotation_euler = (math.radians(25), math.radians(-25), math.radians(-30))
sun.data.energy = 2.3
sun.data.angle = math.radians(7)
bpy.ops.object.camera_add()
camera = bpy.context.object
camera.name = 'RENDER ONLY | review camera'
camera.data.type = 'ORTHO'
camera.data.ortho_scale = 125
camera.data.lens = 45
scene.camera = camera
scene.render.engine = 'CYCLES'
scene.cycles.samples = 48
scene.cycles.use_denoising = True
scene.render.resolution_x = 1200
scene.render.resolution_y = 800
scene.render.resolution_percentage = 100
scene.render.image_settings.file_format = 'PNG'
scene.view_settings.view_transform = 'AgX'
views = {
    'front': ((0, -170, 22), (0, -5, 7)),
    'rear': ((0, 170, 40), (0, 0, 7)),
    'side': ((170, 0, 45), (0, 0, 7)),
    'elevated': ((110, -145, 110), (0, 0, 5)),
    'entrance': ((18, -78, 11), (0, -32, 4.8)),
    'facade': ((50, -90, 20), (15, -28, 9)),
}
for name, (location, target) in views.items():
    camera.data.ortho_scale = 125 if name in ('front','rear','side','elevated') else 30 if name=='entrance' else 56
    camera.location = location
    camera.rotation_euler = (Vector(target) - camera.location).to_track_quat('-Z', 'Y').to_euler()
    scene.render.filepath = str(previews / f'heritage-hall-{name}.png')
    bpy.ops.render.render(write_still=True)

# Organise the editable source into comprehensible architectural families.
families = {}
for obj in model_objects:
    prefix = int(obj.name.split(' | ')[0])
    family = ('01 Footprint and unresolved wings' if prefix < 5 else
              '02 Primary frontage' if prefix < 20 else
              '03 Canopy and columns' if prefix < 40 else
              '04 Glazing, cladding and clerestory' if prefix < 50 else
              '05 Soffit detailing' if prefix < 60 else '06 Entrance assembly')
    if family not in families:
        families[family] = bpy.data.collections.new(family)
        model.children.link(families[family])
    model.objects.unlink(obj)
    families[family].objects.link(obj)
for obj in (ground, sun, camera):
    obj.hide_set(True)  # Viewport only: presentation rig still participates in renders.
bpy.ops.object.select_all(action='DESELECT')
location,target=views['elevated']
camera.location=location
camera.rotation_euler=(Vector(target)-camera.location).to_track_quat('-Z','Y').to_euler()
camera.data.ortho_scale=125
scene.render.filepath=str(previews/'heritage-hall-elevated.png')
for screen in bpy.data.screens:
    for area in screen.areas:
        if area.type=='VIEW_3D':
            area.spaces.active.region_3d.view_distance=145
            area.spaces.active.region_3d.view_location=(0,0,7)
            area.spaces.active.region_3d.view_rotation=camera.rotation_euler.to_quaternion()
            area.spaces.active.region_3d.view_perspective='PERSP'
            area.spaces.active.clip_start=0.05
            area.spaces.active.clip_end=2000
            area.spaces.active.shading.type='MATERIAL'
            area.spaces.active.overlay.show_floor=False
            area.spaces.active.overlay.show_axis_x=False
            area.spaces.active.overlay.show_axis_y=False
scene['reference_notes']='See models/heritage-hall/REFERENCES.md. Front detail study; rear elevations and dimensions remain unverified.'
bpy.ops.wm.save_as_mainfile(filepath=str(source/'heritage-hall-detail.blend'))
print('HERITAGE_BUILD_COMPLETE ' + json.dumps(metadata))
