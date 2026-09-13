"""Refine the saved hall and construct its immediate landscape in Blender.

Run: Blender --background --python-exit-code 1 --python scripts/build_heritage_site.py
Optional environment: HERITAGE_DRAFT=1 (fast hero only), HERITAGE_NO_RENDER=1.
Public photographs are reference only. All exported textures are generated here.
"""
import bpy
import json
import math
import os
import random
from pathlib import Path
from mathutils import Vector, Matrix
import numpy as np

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / 'models/heritage-hall'
OUTPUT = ROOT / 'public/models'
PREVIEWS = ROOT / 'public/previews'
bpy.ops.wm.open_mainfile(filepath=str(SOURCE / 'heritage-hall-detail.blend'))
scene = bpy.context.scene
hall = [o for o in scene.objects if o.type == 'MESH' and not o.name.startswith('RENDER ONLY')]
for o in list(scene.objects):
    if o not in hall:
        bpy.data.objects.remove(o, do_unlink=True)
site = bpy.data.collections.new('LANDSCAPE | Heritage Hall precinct')
scene.collection.children.link(site)
rng = random.Random(403039202)
metadata = json.loads((OUTPUT / 'heritage-hall.json').read_text())
cx, cz = metadata['origin']['x'], metadata['origin']['z']

def material(name, colour, rough=0.7, metal=0):
    m = bpy.data.materials.new(name)
    m.diffuse_color = (*colour, 1)
    m.use_nodes = True
    b = m.node_tree.nodes.get('Principled BSDF')
    b.inputs['Base Color'].default_value = (*colour, 1)
    b.inputs['Roughness'].default_value = rough
    b.inputs['Metallic'].default_value = metal
    return m

def surface(m, colour, variation=0.05, scale=1.0, bump=0.03):
    """Packed, repeatable original albedo + roughness maps; portable to glTF."""
    n = 512
    yy, xx = np.mgrid[0:n, 0:n] / n
    nrng = np.random.default_rng(71)
    pattern = np.zeros((n,n))
    for frequency, weight in [(7,.55),(19,.3),(59,.15),(181,.08)]:
        grid = nrng.normal(0,.5,(frequency,frequency))
        gx=xx*frequency;gy=yy*frequency;ix=gx.astype(int);iy=gy.astype(int)
        fx=gx-ix;fy=gy-iy;fx=fx*fx*(3-2*fx);fy=fy*fy*(3-2*fy)
        pattern += weight*((grid[iy%frequency,ix%frequency]*(1-fx)+grid[iy%frequency,(ix+1)%frequency]*fx)*(1-fy)
                           +(grid[(iy+1)%frequency,ix%frequency]*(1-fx)+grid[(iy+1)%frequency,(ix+1)%frequency]*fx)*fy)
    pattern += nrng.normal(0,.04,(n,n))
    pixels = np.ones((n,n,4), dtype=np.float32)
    pixels[:,:,:3] = np.clip(np.array(colour)[None,None,:] + pattern[:,:,None]*variation, 0.005, 1)
    im = bpy.data.images.new(m.name + ' | original surface', width=n, height=n)
    im.colorspace_settings.name = 'Non-Color'
    im.pixels.foreach_set(pixels.ravel())
    im.pack()
    nodes, links = m.node_tree.nodes, m.node_tree.links
    b = nodes.get('Principled BSDF')
    tex = nodes.new('ShaderNodeTexImage'); tex.image = im
    links.new(tex.outputs['Color'], b.inputs['Base Color'])
    noise = nodes.new('ShaderNodeTexNoise'); noise.inputs['Scale'].default_value = scale
    bump_node = nodes.new('ShaderNodeBump'); bump_node.inputs['Strength'].default_value = 0.22
    bump_node.inputs['Distance'].default_value = bump
    links.new(noise.outputs['Fac'], bump_node.inputs['Height'])
    links.new(bump_node.outputs['Normal'], b.inputs['Normal'])
    # Bump is a Blender-only enhancement. Browser receives the packed albedo.

for m in {m for o in hall for m in o.data.materials if m}:
    b = m.node_tree.nodes.get('Principled BSDF') if m.use_nodes else None
    if not b: continue
    if 'glazing' in m.name.lower():
        b.inputs['Metallic'].default_value = 0.12
        b.inputs['Roughness'].default_value = 0.20
        b.inputs['Coat Weight'].default_value = 0.38
        b.inputs['Coat Roughness'].default_value = 0.12
        b.inputs['Base Color'].default_value = (0.18, 0.30, 0.32, 1)
    elif 'pale-grey' in m.name:
        surface(m, (0.53,0.56,0.53), 0.055, 95, 0.015)
    elif 'metal roof' in m.name:
        surface(m, (0.40,0.44,0.42), 0.022, 130, 0.009)
        b.inputs['Roughness'].default_value = 0.45
    elif 'unverified' in m.name.lower():
        surface(m, (0.52,0.55,0.51), 0.04, 100, 0.018)

grass = material('Lawn | varied tropical turf', (0.18,0.25,0.07), 0.98)
surface(grass, (0.16,0.23,0.062), 0.065, 210, 0.015)
asphalt = material('Road | fine weathered asphalt', (0.13,0.145,0.15), 0.96)
surface(asphalt, (0.13,0.145,0.15), 0.065, 180, 0.025)
paving = material('Paths | warm concrete aggregate', (0.53,0.52,0.44), 0.87)
surface(paving, (0.53,0.52,0.44), 0.045, 120, 0.018)
curb = material('Kerbs | pale concrete', (0.64,0.66,0.61), 0.85)
stone = material('Sculpture steps | weathered pale stone', (0.56,0.59,0.52), 0.78)
surface(stone, (0.56,0.59,0.52), 0.06, 90, 0.012)
bronze = material('Sculpture | warm oxidised bronze', (0.085,0.062,0.040), 0.54, 0.72)
surface(bronze, (0.085,0.062,0.040), 0.04, 48, 0.012)
patina = material('Sculpture | recessed bronze patina', (0.055,0.073,0.050), 0.6, 0.65)
gold = material('Plaque | aged brass lettering', (0.47,0.32,0.095), 0.45, 0.7)
plaque_mat = material('Plaque | dark blue enamel', (0.025,0.046,0.067), 0.32, 0.3)
bark = material('Trees | pale branching bark', (0.28,0.255,0.19), 0.94)
surface(bark, (0.28,0.255,0.19), 0.10, 50, 0.035)
leaves = [material('Trees | leaf tone '+str(i), c, 0.82) for i,c in enumerate([
    (0.055,0.145,0.026), (0.105,0.235,0.042), (0.20,0.31,0.07), (0.085,0.18,0.037)])]
for m in leaves:
    m.use_backface_culling = False
    m.node_tree.nodes.get('Principled BSDF').inputs['Subsurface Weight'].default_value = 0.035
paint = material('Road | faded ivory paint', (0.75,0.74,0.63), 0.8)
metal = material('Site | brushed pole metal', (0.52,0.56,0.55), 0.3, 0.72)
dark = material('Site | dark fixtures', (0.045,0.055,0.047), 0.65, 0.4)

def mesh(name, vertices, faces, mat, collection=site):
    data = bpy.data.meshes.new(name)
    data.from_pydata(vertices, [], faces); data.update()
    obj = bpy.data.objects.new(name, data); collection.objects.link(obj)
    data.materials.append(mat)
    uv = data.uv_layers.new(name='Metre UV')
    for p in data.polygons:
        axes = [a for a in range(3) if a != max(range(3), key=lambda a: abs(p.normal[a]))]
        for i in p.loop_indices:
            co = data.vertices[data.loops[i].vertex_index].co
            uv.data[i].uv = (co[axes[0]]/4, co[axes[1]]/4)
    return obj

def own(obj, name, mat):
    for c in list(obj.users_collection): c.objects.unlink(obj)
    site.objects.link(obj); obj.name = name; obj.data.materials.append(mat)
    return obj

def box(name, pos, size, mat, bevel=0):
    bpy.ops.mesh.primitive_cube_add(size=1, location=pos)
    o = own(bpy.context.object, name, mat); o.dimensions = size
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    if bevel:
        mod = o.modifiers.new('Soft cast edges','BEVEL'); mod.width=bevel; mod.segments=2
    return o

def tube(name, points, radii, mat, sides=9):
    verts=[]; faces=[]
    for i,p in enumerate(points):
        p=Vector(p)
        direction=Vector(points[min(i+1,len(points)-1)])-Vector(points[max(0,i-1)])
        rot=direction.to_track_quat('Z','Y')
        for k in range(sides):
            v=rot @ Vector((radii[i]*math.cos(k*math.tau/sides),radii[i]*math.sin(k*math.tau/sides),0))
            verts.append(tuple(p+v))
    for i in range(len(points)-1):
        for k in range(sides):
            j=i*sides+k; faces.append((j,i*sides+(k+1)%sides,(i+1)*sides+(k+1)%sides,j+sides))
    faces.extend([tuple(reversed(range(sides))),tuple(range((len(points)-1)*sides,len(points)*sides))])
    o=mesh(name,verts,faces,mat)
    for p in o.data.polygons:p.use_smooth=True
    return o

def ellipsoid(name,pos,scale,mat,segments=20,rings=12):
    bpy.ops.mesh.primitive_uv_sphere_add(segments=segments,ring_count=rings,location=pos)
    o=own(bpy.context.object,name,mat);o.scale=scale
    for p in o.data.polygons:p.use_smooth=True
    return o

def join(objects,name):
    bpy.ops.object.select_all(action='DESELECT')
    for o in objects:o.select_set(True)
    bpy.context.view_layer.objects.active=objects[0];bpy.ops.object.join()
    o=bpy.context.object;o.name=name
    return o

def strip(name, points, width, z, mat):
    pts=[Vector((x,y)) for x,y in points];vs=[]
    for i,p in enumerate(pts):
        prev=(p-pts[max(0,i-1)]).normalized();nxt=(pts[min(len(pts)-1,i+1)]-p).normalized()
        direction=(prev+nxt).normalized()
        normal=Vector((-direction.y,direction.x))
        edge=Vector((-(nxt if nxt.length else prev).y,(nxt if nxt.length else prev).x))
        offset=normal*(width/2/max(0.55,normal.dot(edge)))
        vs.extend([(p.x+offset.x,p.y+offset.y,z),(p.x-offset.x,p.y-offset.y,z)])
    return mesh(name,vs,[(i*2,i*2+1,i*2+3,i*2+2) for i in range(len(pts)-1)],mat)

def inside(p,poly):
    x,y=p; c=False
    for a,b in zip(poly,poly[1:]+poly[:1]):
        if (a[1]>y)!=(b[1]>y) and x<(b[0]-a[0])*(y-a[1])/(b[1]-a[1])+a[0]: c=not c
    return c

def local(p):return ((p['lon']-101.137)*111320*math.cos(math.radians(4.3385))-cx,(p['lat']-4.3385)*110540+cz)
ways=json.loads((ROOT/'src/data/campus.json').read_text())['elements']
footprints=[[local(p) for p in w['geometry']] for w in ways if w.get('tags',{}).get('building') and w.get('geometry')]
road_segments=[];road_count=0;path_count=0
lawn=mesh('Ground | Heritage precinct lawn',[(-147,-151,-0.09),(132,-151,-0.09),(132,96,-0.09),(-147,96,-0.09)],[(0,1,2,3)],grass)
for uv in lawn.data.uv_layers.active.data:uv.uv /= 5
# Preserve source centre-lines. Clip to a clearly bounded immediate precinct.
def clip(a,b):
    lo,hi=0.,1.;dx=b[0]-a[0];dy=b[1]-a[1]
    for p,q in [(-dx,a[0]+146),(dx,131-a[0]),(-dy,a[1]+150),(dy,95-a[1])]:
        if p==0:
            if q<0:return None
        elif p<0:lo=max(lo,q/p)
        else:hi=min(hi,q/p)
    if lo>hi:return None
    return [(a[0]+dx*lo,a[1]+dy*lo),(a[0]+dx*hi,a[1]+dy*hi)]

for way in ways:
    tags=way.get('tags',{});kind=tags.get('highway')
    if not kind or not way.get('geometry'):continue
    pts=[local(p) for p in way['geometry']]
    foot=kind in ('footway','path','steps','pedestrian','cycleway')
    width=1.65 if foot else 7.0 if tags.get('lanes')=='2' else 3.6 if tags.get('service')=='parking_aisle' else 4.6
    used=False; runs=[];run=[]
    for a,b in zip(pts,pts[1:]):
        seg=clip(a,b)
        if not seg:
            if len(run)>1:runs.append(run)
            run=[];continue
        a,b=seg;mid=((a[0]+b[0])/2,(a[1]+b[1])/2)
        if foot and any(inside(mid,poly) for poly in footprints):
            if len(run)>1:runs.append(run)
            run=[];continue
        if math.dist(a,b)<0.1:continue
        used=True;road_segments.append((a,b,width))
        if run and math.dist(run[-1],a)>.01:
            if len(run)>1:runs.append(run)
            run=[]
        if not run:run.append(a)
        run.append(b)
        if not foot and tags.get('lanes')=='2':
            d=Vector(b)-Vector(a);length=d.length;d.normalize()
            for t in np.arange(1,length-2,7):
                aa=Vector(a)+d*t;bb=aa+d*2.5
                strip('Road | centre dash',[aa,bb],0.11,0.03,paint)
    if len(run)>1:runs.append(run)
    for pts_run in runs:
        z=(.055+path_count*.001) if foot else (-.01+road_count*.001)
        strip(f'OSM {way["id"]} | '+('walkpath' if foot else 'road'),pts_run,width,z,paving if foot else asphalt)
        if tags.get('footway')!='crossing':
            pts_vec=[Vector(p) for p in pts_run]
            for side in (-1,1):
                edge=[]
                for i,p in enumerate(pts_vec):
                    d=(pts_vec[min(i+1,len(pts_vec)-1)]-pts_vec[max(0,i-1)]).normalized()
                    edge.append(p+Vector((-d.y,d.x))*(width/2+.08)*side)
                strip('Edge | '+('path edging' if foot else 'road kerb'),edge,.13,z+.012,curb)
    if used:
        if foot:path_count+=1
        else:road_count+=1

# Parking envelopes inferred between mapped parking aisles; bay spacing estimated.
from mathutils.geometry import tessellate_polygon
for label, poly in [('West',[(-134,-85),(-93,-22),(-48,-44),(-50,-55),(-80,-106),(-85,-109),(-103,-110),(-110,-109)]),
                    ('East',[(37,-64),(50,-76),(74,-49),(91,-10),(95,40),(91,46),(79,46),(75,38),(72,-8),(54,-45)])]:
    vecs=[Vector((x,y,-.035)) for x,y in poly];indices={tuple(v):i for i,v in enumerate(vecs)}
    tris=tessellate_polygon([vecs]);faces=[tuple(v if isinstance(v,int) else indices[tuple(v)] for v in tri) for tri in tris]
    obj=mesh('Parking | '+label+' envelope',vecs,faces,asphalt)
    for p in obj.data.polygons:
        if p.normal.z<0:p.flip()
for a,b in [((-94,-48),(-61,-66)),((-104,-63),(-72,-82)),((-115,-80),(-85,-98))]:
    av,bv=Vector(a),Vector(b);d=(bv-av).normalized();normal=Vector((-d.y,d.x))
    for t in np.arange(0,(bv-av).length,2.55):
        p=av+d*t
        strip('Parking | estimated bay marking',[p,p+normal*4.6],.065,-.020,paint)

# Forecourt lawn is retained between the access loop and the outer sidewalk.
# A short approach is estimated from the tour's sculpture platform view.
SX,SY=-5.,-83.
strip('Sculpture | approach path',[(SX,-61.7),(SX,SY+4.5)],2.1,0.06,paving)
def octagon(w,d,ch):return [(-w/2+ch,-d/2),(w/2-ch,-d/2),(w/2,-d/2+ch),(w/2,d/2-ch),(w/2-ch,d/2),(-w/2+ch,d/2),(-w/2,d/2-ch),(-w/2,-d/2+ch)]
def slab(name,w,d,z,height):
    pts=octagon(w,d,0.7);v=[(SX+x,SY+y,zz) for zz in (z,z+height) for x,y in pts]
    faces=[tuple(reversed(range(8))),tuple(range(8,16))]+[(i,(i+1)%8,(i+1)%8+8,i+8) for i in range(8)]
    o=mesh(name,v,faces,stone);bev=o.modifiers.new('Worn stone arris','BEVEL');bev.width=.025;bev.segments=2
    return o
slab('Sculpture | lower octagonal step',10.2,5.5,0.02,0.13)
slab('Sculpture | middle octagonal step',9.2,4.5,0.15,0.15)
slab('Sculpture | upper octagonal pedestal',8.0,3.5,0.30,0.16)
# Published pedestal width is ambiguous relative to visible stepped platform;
# 8m length/0.46m height retained; platform depth estimated from imagery.
for x in np.arange(-3.6,3.7,.43):
    strip('Sculpture | geometric step inlay',[(SX+x,SY+1.88),(SX+x+.28,SY+1.88),(SX+x+.28,SY+2.1),(SX+x+.08,SY+2.1)],.035,.309,curb)

# Sculptural figures are hand-built interpretations of observed poses, not scans.
figures=[]
def figure(name,x,direction,confucius=False):
    before=set(site.objects)
    def p(u,v,z):return (SX+x+direction*v,SY+u,z+.46)
    def e(label,pos,size,mat=bronze):return ellipsoid(name+' | '+label,p(*pos),size,mat)
    def limb(label,coords,rads,mat=bronze):return tube(name+' | '+label,[p(*q) for q in coords],rads,mat,12)
    box(name+' | cast block seat',p(0,-.08,.25),(.49,.53,.50),bronze,.025)
    # hips, jacket/robe chest, neck and three-quarter downward head
    e('hips',(0,0,.68),(.27,.31,.20))
    e('torso',(0,-.01,1.07),(.23,.32,.40))
    limb('neck',[(0,.04,1.35),(0,.10,1.47)],[.105,.085])
    head=e('face',(0,.13,1.59 if confucius else 1.55),(.125,.135,.185))
    e('nose',(0,.265,1.58 if confucius else 1.53),(.055,.038,.047))
    for u in (-.133,.133):e('ear',(u,.125,1.58 if confucius else 1.54),(.028,.03,.057))
    # Brows and inset eyes follow the forward axis.
    for u in (-.059,.059):
        e('eye recess',(u,.247,1.62 if confucius else 1.58),(.032,.015,.012),patina)
        limb('brow',[(u-.035,.237,1.65 if confucius else 1.61),(u+.032,.245,1.645 if confucius else 1.605)],[.012,.009])
    limb('mouth',[(-.04,.255,1.49 if not confucius else 1.53),(.04,.255,1.49 if not confucius else 1.53)],[.006,.006],patina)
    if confucius:
        # Sweeping seated robe, with folded skirt and narrow hanging beard.
        rings=[(.08,.38,.48,.17),(.25,.36,.43,.18),(.5,.33,.39,.20),(.70,.32,.30,.16),(1.05,.29,.23,-.02),(1.36,.25,.20,-.02)]
        vs=[];fs=[];count=48
        for z,ru,rv,v in rings:
            for i in range(count):
                a=i*math.tau/count;fold=1+.055*math.sin(a*13+z*2)
                vs.append(p(ru*math.sin(a)*fold,v+rv*math.cos(a)*fold,z))
        for j in range(len(rings)-1):
            for i in range(count):fs.append((j*count+i,j*count+(i+1)%count,(j+1)*count+(i+1)%count,(j+1)*count+i))
        fs.extend([tuple(reversed(range(count))),tuple(range((len(rings)-1)*count,len(rings)*count))])
        robe=mesh(name+' | flowing robe',vs,fs,bronze)
        for f in robe.data.polygons:f.use_smooth=True
        limb('left sleeve',[(-.25,-.02,1.30),(-.37,.17,1.02),(-.28,.43,.83)],[.17,.19,.15])
        limb('raised sleeve',[(.23,-.04,1.28),(.35,.11,1.10),(.21,.34,1.38)],[.17,.19,.12])
        e('hand at beard',(.15,.33,1.40),(.075,.065,.04))
        e('resting hand',(-.25,.47,.87),(.085,.065,.035))
        for k in range(13):
            u=(k-6)*.011
            limb('beard strand',[(u,.24,1.50),(u*.9,.25,1.38),(u*.35,.21,1.20)],[.016,.012,.003])
        e('bound hair',(0,.03,1.735),(.115,.13,.055))
        e('topknot',(0,-.025,1.795),(.055,.063,.035))
        for u in (-.19,.19):e('shoe',(u,.43,.055),(.12,.075,.06))
    else:
        # Einstein's crossed leg and chin-resting hand are visible in UTAR photos.
        limb('grounded leg',[(-.16,.10,.70),(-.18,.39,.45),(-.18,.41,.12)],[.15,.13,.085])
        limb('crossed leg',[(.15,.07,.70),(.20,.42,.64),(-.04,.58,.37)],[.15,.135,.09])
        e('grounded shoe',(-.18,.49,.065),(.16,.095,.065))
        e('crossed shoe',(-.03,.66,.34),(.15,.09,.06))
        limb('chin arm',[(.25,-.02,1.27),(.29,.40,.88),(.15,.29,1.39)],[.13,.11,.065])
        e('chin hand',(.12,.30,1.42),(.08,.048,.061))
        limb('resting arm',[(-.25,-.02,1.27),(-.30,.18,.90),(.02,.48,.79)],[.135,.12,.065])
        e('resting hand',(.015,.49,.81),(.08,.065,.041))
        for side in (-1,1):
            limb('jacket lapel',[(side*.09,.23,1.37),(side*.16,.25,1.20),(side*.06,.27,1.07)],[.032,.04,.022])
        for k in range(32):
            a=k*math.tau/32
            u=.14*math.sin(a);v=.12+.12*math.cos(a);z=1.68+.025*math.sin(a*5)
            limb('tousled hair',[(u,v,z),(u*1.18,v-.03,z+.055),(u*1.25,v-.09,z+.02)],[.032,.029,.008])
        limb('moustache',[(-.065,.252,1.505),(0,.276,1.513),(.065,.252,1.505)],[.012,.018,.012])
    result=join(list(set(site.objects)-before),name+' | interpreted bronze figure')
    # Joined primitives can retain a tiny active-object scale. Bake it before
    # voxel remeshing so 14 mm means world metres, not scaled local coordinates.
    bpy.context.view_layer.objects.active=result
    bpy.ops.object.transform_apply(location=False,rotation=True,scale=True)
    remesh=result.modifiers.new('Unify cast sculptural surface','REMESH');remesh.mode='VOXEL';remesh.voxel_size=.014;remesh.use_smooth_shade=True
    smooth=result.modifiers.new('Soften sculptural transitions','SMOOTH');smooth.factor=.55;smooth.iterations=3
    result['fidelity']='Photo-guided pose and approximate anatomy; not a scan or exact sculptural replica'
    figures.append(result)
figure('Einstein',-1.35,1)
figure('Confucius',1.35,-1,True)
box('Sculpture | chess table pedestal',(SX,SY,.46+.34),(.65,.65,.68),bronze,.018)
box('Sculpture | chess table 91cm',(SX,SY,.46+.735),(.91,.91,.05),bronze,.012)
for i in range(8):
    for j in range(8):
        box('Chessboard | square',(SX+(i-3.5)*.097,SY+(j-3.5)*.097,1.223),(.095,.095,.005),bronze if (i+j)%2 else patina)
for side in (-1,1):
    for row in (0,1):
        for k in range(8):
            x=SX+side*(.34-row*.105);y=SY+(k-3.5)*.098
            height=.055 if row else [.065,.083,.09,.105,.12,.09,.083,.065][k]
            tube('Chessboard | cast piece',[(x,y,1.23),(x,y,1.25),(x,y,1.23+height)],[.025,.012,.015],bronze,10)
            ellipsoid('Chessboard | piece crown',(x,y,1.23+height),(.02,.02,.019),bronze,12,8)
pv=[(SX+x,SY+3.30+y,z) for z in (.035,.40) for x,y in [(-1.25,-.625),(1.25,-.625),(1.25,.625),(-1.25,.625)]]
for k in range(4,8):
    x,y,z=pv[k];pv[k]=(x,y,.38+(y-SY-3.30)*math.tan(math.radians(12)))
mesh('Sculpture | sloping plaque stone support',pv,[(0,3,2,1),(4,5,6,7),(0,1,5,4),(1,2,6,5),(2,3,7,6),(3,0,4,7)],stone)
plaque=box('Sculpture | enamel plaque',(SX,SY+3.30,.40),(2.35,1.1,.035),plaque_mat,.015)
plaque.rotation_euler.x=math.radians(12)
bpy.context.view_layer.update()
for x in (-1.10,1.10):
    tube('Plaque | brass border',[plaque.matrix_world @ Vector((x,-.47,.022)),plaque.matrix_world @ Vector((x,.47,.022))],[.008,.008],gold,6)
# Legible title only; omit unverified miniature transcription and university logo.
bpy.ops.object.text_add(location=(SX+1.01,SY+3.58,.54),rotation=(0,0,math.pi))
t=bpy.context.object;t.data.body='UNIVERSALITY OF\nLEARNING AND THINKING';t.data.size=.105;t.data.space_line=1.35;t.data.extrude=.001
t.matrix_world=plaque.matrix_world @ Matrix.Translation((1.01,.3,.021)) @ Matrix.Rotation(math.pi,4,'Z')
own(t,'Sculpture | plaque title',gold)
bpy.context.view_layer.objects.active=t;bpy.ops.object.convert(target='MESH')

# Three flagpoles visible in the official panorama; cloth colours are approximate.
flag_blue=material('Flag | blue',(0.025,.09,.28),.8)
flag_red=material('Flag | red',(0.48,.03,.035),.8)
flag_yellow=material('Flag | yellow',(0.65,.47,.045),.8)
flag_white=material('Flag | white',(.82,.84,.79),.8)
for i,x in enumerate((-9,-2,5)):
    y=-68
    box('Flags | concrete footing',(x,y,.13),(1.1,1.1,.3),stone,.08)
    tube('Flags | pole',[(x,y,.2),(x,y,10.5)],[.065,.042],metal,12)
    ellipsoid('Flags | finial',(x,y,10.55),(.08,.08,.08),metal,12,8)
    vs=[];fs=[]
    for v in range(15):
        for u in range(17):
            s=u/16;t=v/14
            vs.append((x+s*1.9,y+.16*math.sin(s*8+t*2)*s,10.35-t*1.05-.18*s))
    for v in range(14):
        for u in range(16):a=v*17+u;fs.append((a,a+1,a+18,a+17))
    o=mesh('Flags | approximate cloth '+str(i),vs,fs,flag_white)
    for m in (flag_red,flag_blue,flag_yellow,dark):o.data.materials.append(m)
    for k,p in enumerate(o.data.polygons):
        row,col=divmod(k,16)
        if i==1:p.material_index=2 if row<8 and col<8 else 1 if row%2==0 else 0
        elif i==2:p.material_index=0 if row<5 else 3 if row<10 else 4
    if i==1:
        # Malaysian crescent and fourteen-point star on the blue canton.
        def flag_point(px,pz):
            s=px/1.9;t=(10.35-pz-.18*s)/1.05
            return (x+px,y+.16*math.sin(s*8+t*2)*s-.012,pz)
        outer=[(.30+.17*math.cos(a),10.04+.17*math.sin(a)) for a in np.linspace(math.pi/3,5*math.pi/3,33)]
        inner=[(.36+.135*math.cos(a),10.04+.135*math.sin(a)) for a in np.linspace(5*math.pi/3,math.pi/3,33)]
        poly=[Vector(flag_point(px,pz)) for px,pz in outer+inner]
        # Triangulate in the flag's X/Z plane, then preserve its cloth offset.
        flat=[Vector((p.x,p.z,0)) for p in poly];idx={tuple(p):j for j,p in enumerate(flat)}
        tris=tessellate_polygon([flat]);faces=[tuple(v if isinstance(v,int) else idx[tuple(v)] for v in tri) for tri in tris]
        mesh('Flags | Malaysian crescent',poly,faces,flag_yellow)
        vv=[flag_point(.64,10.04)]
        for k in range(28):
            a=k*math.tau/28;r=.13 if k%2==0 else .063
            vv.append(flag_point(.64+math.cos(a)*r,10.04+math.sin(a)*r))
        mesh('Flags | fourteen-point star',vv,[(0,k+1,(k+1)%28+1) for k in range(28)],flag_yellow)
    o['fidelity']='Observed UTAR, Malaysia and Perak flagpole grouping. Simplified cloth motifs; tiny emblems omitted.'

def distance_segment(p,a,b):
    p,a,b=Vector(p),Vector(a),Vector(b);d=b-a
    return (p-(a+d*max(0,min(1,(p-a).dot(d)/d.length_squared)))).length

def clear_tree(x,y):
    if any(inside((x,y),poly) for poly in footprints):return False
    if any(distance_segment((x,y),a,b)<w/2+2.4 for a,b,w in road_segments):return False
    if abs(x-SX)<11 and -94<y<-59:return False
    return True

# Three original branching broadleaf templates, shared by all tree instances.
templates=[]
for variant in range(3):
    before=set(site.objects)
    height=[9.8,8.2,6.0][variant]
    trunk=tube('Tree template | trunk',[(0,0,0),(.08,-.03,2.1),(.15,.1,4.5),(0,.15,height*.78)],[.20,.17,.10,.025],bark)
    centres=[]
    for k in range(13):
        a=k*2.4+variant;r=2.7*(.65+.35*rng.random());z=height*.64+rng.uniform(-.7,1.3)
        tip=Vector((math.cos(a)*r,math.sin(a)*r,z));centres.append(tip)
        tube('Tree template | branch',[(.07,0,2.4+k*.14),tuple(tip*.65),tuple(tip)],[.085,.045,.008],bark,7)
    centres.extend([Vector((0,0,height-.8)),Vector((1,-.8,height-1.3)),Vector((-1,1,height-1.0))])
    for tone,mat in enumerate(leaves):
        vs=[];fs=[]
        for c in centres:
            for k in range(80):
                a=rng.uniform(0,math.tau);r=rng.random()**(1/3)
                z=rng.uniform(-1,1);rad=math.sqrt(1-z*z)
                centre=c+Vector((math.cos(a)*rad*r*1.75,math.sin(a)*rad*r*1.65,z*r*1.2))
                ang=rng.uniform(0,math.tau);length=rng.uniform(.12,.23);width=length*.48
                u=Vector((math.cos(ang)*length,math.sin(ang)*length,rng.uniform(-.06,.06)))
                v=Vector((-math.sin(ang)*width,math.cos(ang)*width,.035))
                j=len(vs);vs.extend([tuple(centre-u),tuple(centre+v),tuple(centre+u),tuple(centre-v)])
                fs.append((j,j+1,j+2,j+3))
        mesh('Tree template | leaf canopy',vs,fs,mat)
    template=join(list(set(site.objects)-before),'TREE_TEMPLATE_'+str(variant))
    # Bake transforms into the shared geometry, then instances only transform it.
    bpy.context.view_layer.objects.active=template
    bpy.ops.object.transform_apply(location=True,rotation=True,scale=True)
    templates.append(template)

positions=[]
# Dense backdrop and flanking rows observed; exact stems absent from local OSM.
for x in np.arange(-49,64,7.5):positions.append((float(x+rng.uniform(-1.5,1.5)),-110+rng.uniform(-2,2)))
for y in np.arange(-102,-61,8):positions.extend([(-46+rng.uniform(-2,2),float(y)),(30+rng.uniform(-2,2),float(y))])
for y in np.arange(-30,87,10):positions.extend([(-68+rng.uniform(-2,2),float(y)),(99+rng.uniform(-2,2),float(y))])
for x in np.arange(-133,127,11):positions.extend([(float(x),-143+rng.uniform(-2,2)),(float(x),88+rng.uniform(-2,2))])
positions.extend([(-29,-72),(-25,-89),(20,-81),(23,-96),(-38,-97),(-104,15),(-115,38),(-130,58)])
tree_count=0
for x,y in positions:
    if not clear_tree(x,y):continue
    template=templates[tree_count%3]
    o=bpy.data.objects.new('Tree | approximate planting '+str(tree_count),template.data);site.objects.link(o)
    o.location=(x,y,-.04);s=rng.uniform(.85,1.18);o.scale=(s,s,s*rng.uniform(.93,1.08));o.rotation_euler.z=rng.uniform(0,math.tau)
    o['tree_instance']=True;tree_count+=1
for o in templates:bpy.data.objects.remove(o,do_unlink=True)

# Low hedges around the side landscape, kept clear of the open sculpture lawn.
for x,y in [(-53,y) for y in range(-12,18,3)]+[(49,y) for y in range(-12,18,3)]:
    if clear_tree(x,y):ellipsoid('Planting | clipped shrub',(x,y,.7),(1.45,1.2,.85),leaves[1],12,8)

# Fine grass catches light in close-up without filling the whole campus with mesh.
vs=[];fs=[]
for i in range(20000):
    x=rng.uniform(-43,27);y=rng.uniform(-109,-64)
    if abs(x-SX)<5.4 and abs(y-SY)<4:continue
    if abs(x-SX)<1.25 and y>SY:continue
    h=rng.uniform(.035,.12);w=.016;a=rng.uniform(0,math.tau)
    j=len(vs);vs.extend([(x-w*math.cos(a),y-w*math.sin(a),-.075),(x+w*math.cos(a),y+w*math.sin(a),-.075),(x+.04,y+.02,h-.075)])
    fs.append((j,j+1,j+2))
mesh('Lawn | fine grass at sculpture',vs,fs,leaves[2])

for x,y in [(-40,-63),(24,-59),(-63,-90),(66,-25),(62,30),(-63,35),(40,-115)]:
    tube('Lighting | slender pole',[(x,y,0),(x,y,5.8)],[.07,.045],metal,10)
    box('Lighting | compact luminaire',(x+.25,y,5.78),(.7,.25,.10),dark,.025)

# Fine standing-seam treatment follows the existing canopy surface. The seam
# spacing is a material interpretation, not a measured roof assembly.
roof_object=next(o for o in hall if o.name.startswith('20 |'))
rv=[v.co.copy() for v in roof_object.data.vertices]
roof_parts=[]
def canopy_z(x,y):
    for f in roof_object.data.polygons:
        if len(f.vertices)!=3:continue
        a,b,c=[rv[i] for i in f.vertices]
        det=(b.y-c.y)*(a.x-c.x)+(c.x-b.x)*(a.y-c.y)
        if abs(det)<1e-8:continue
        u=((b.y-c.y)*(x-c.x)+(c.x-b.x)*(y-c.y))/det
        v=((c.y-a.y)*(x-c.x)+(a.x-c.x)*(y-c.y))/det
        if u>=-1e-5 and v>=-1e-5 and u+v<=1.00001:return u*a.z+v*b.z+(1-u-v)*c.z
    return None
roof_mat=roof_object.data.materials[0]
for x in np.arange(-48,49,.85):
    line=[]
    for y in np.arange(-39,1,.8):
        z=canopy_z(float(x),float(y))
        if z is not None:line.append((float(x),float(y),z+.025))
    if len(line)>1:roof_parts.append(tube('Roof | standing seams',line,[.019]*len(line),roof_mat,5))
if roof_parts:
    seams=join(roof_parts,'Roof | estimated standing seam treatment')
    site.objects.unlink(seams);hall[0].users_collection[0].objects.link(seams);hall.append(seams)

# Organise and batch site surfaces; retain linked tree mesh instances for glTF.
for prefix in ('OSM','Edge','Road | centre','Parking','Sculpture | geometric','Chessboard','Lighting','Flags','Planting'):
    objects=[o for o in site.objects if o.type=='MESH' and o.name.startswith(prefix)]
    if objects:join(objects,prefix+' | combined details')
site_objects=list(site.objects)
for o in site_objects:
    o['site_context']=True
    o['source_notes']='OSM alignments; UTAR photo-guided planting/sculpture; dimensions partly estimated. See SITE-REFERENCES.md.'

def export(objects,path):
    bpy.ops.object.select_all(action='DESELECT')
    for o in objects:o.hide_set(False);o.select_set(True)
    bpy.context.view_layer.objects.active=objects[0]
    bpy.ops.export_scene.gltf(filepath=str(path),export_format='GLB',use_selection=True,export_apply=True,export_extras=True,export_yup=True)
    if path.stat().st_size>40*1024*1024:
        raise RuntimeError(f'{path.name} exceeds the 40 MB asset budget; inspect modifier scale and mesh duplication.')

export(hall,OUTPUT/'heritage-hall.glb')
export(site_objects,OUTPUT/'heritage-hall-site.glb')
metadata.update(stage='exterior-and-landscape-review',meshCount=len(hall),
    notes='Refined hall materials and photo-guided precinct. Rear elevations remain simplified. Sculpture is an interpreted model, not a scan.',
    site={'asset':'/models/heritage-hall-site.glb','treeCount':tree_count,'roadWays':road_count,'pathWays':path_count,
          'sculpture':{'x':SX,'z':-SY,'height':2.3},'bounds':{'min':[-147,-.1,-96],'max':[132,16,151]}})
(OUTPUT/'heritage-hall.json').write_text(json.dumps(metadata,indent=2)+'\n')

# Daylight presentation rig. Building + site remain the editable master.
rig=bpy.data.collections.new('RENDER ONLY | Daylight cameras');scene.collection.children.link(rig)
scene.world.use_nodes=True
nodes=scene.world.node_tree.nodes;nodes.clear()
out=nodes.new('ShaderNodeOutputWorld');bg=nodes.new('ShaderNodeBackground');sky=nodes.new('ShaderNodeTexSky')
sky.sky_type='MULTIPLE_SCATTERING';sky.sun_elevation=math.radians(32);sky.sun_rotation=math.radians(135);sky.air_density=1.1
bg.inputs['Strength'].default_value=.035
scene.world.node_tree.links.new(sky.outputs['Color'],bg.inputs['Color']);scene.world.node_tree.links.new(bg.outputs[0],out.inputs[0])
bpy.ops.object.light_add(type='SUN',location=(-70,-90,120));sun=bpy.context.object;sun.name='RENDER ONLY | afternoon sun'
sun.rotation_euler=(math.radians(30),math.radians(-25),math.radians(-35));sun.data.energy=2.1;sun.data.angle=math.radians(3)
bpy.ops.object.camera_add();camera=bpy.context.object;camera.name='RENDER ONLY | review camera';scene.camera=camera;camera.data.lens=44
for o in (sun,camera):
    for c in list(o.users_collection):c.objects.unlink(o)
    rig.objects.link(o)
scene.render.engine='CYCLES';scene.cycles.samples=24 if os.getenv('HERITAGE_DRAFT') else 48
scene.cycles.use_denoising=True;scene.cycles.max_bounces=6
scene.render.resolution_x=1400;scene.render.resolution_y=900;scene.render.resolution_percentage=65 if os.getenv('HERITAGE_DRAFT') else 100
scene.render.image_settings.file_format='PNG';scene.view_settings.view_transform='AgX'
scene.view_settings.look='AgX - Medium High Contrast'
backdrop=mesh('RENDER ONLY | ground continuation',[(-1500,-1500,-.6),(1500,-1500,-.6),(1500,1500,-.6),(-1500,1500,-.6)],[(0,1,2,3)],grass,rig)
for uv in backdrop.data.uv_layers.active.data:uv.uv /= 5
views={
    'site':((133,-204,124),(-2,-38,4),44),
    'arrival':((1,-99,5.5),(0,-16,9),31),
    'sculpture':((SX-6.5,SY+8,3.9),(SX,SY,1.45),48),
    'elevated':((100,-132,82),(0,-10,6),48),
    'front':((0,-118,11),(0,-18,8),37),
    'rear':((0,116,40),(0,0,7),43),
    'side':((128,-20,40),(0,0,7),43),
    'entrance':((17,-69,7),(0,-31,4.8),43),
    'facade':((45,-78,16),(12,-26,8),48),
}
def view(name):
    pos,target,lens=views[name];camera.location=pos;camera.data.lens=lens
    camera.rotation_euler=(Vector(target)-camera.location).to_track_quat('-Z','Y').to_euler()
    scene.render.filepath=str(PREVIEWS/f'heritage-hall-{name}.png')
view('site')
for screen in bpy.data.screens:
    for area in screen.areas:
        if area.type=='VIEW_3D':
            area.spaces.active.region_3d.view_distance=205
            area.spaces.active.region_3d.view_location=(0,-35,4)
            area.spaces.active.region_3d.view_rotation=camera.rotation_euler.to_quaternion()
            area.spaces.active.shading.type='MATERIAL'
            area.spaces.active.clip_end=2500
bpy.ops.object.select_all(action='DESELECT')
scene['reference_notes']='See SITE-REFERENCES.md. Landscaping and figure anatomy are approximations; OSM road centre-lines retained.'
bpy.ops.wm.save_as_mainfile(filepath=str(SOURCE/'heritage-hall-landscape.blend'))
print('HERITAGE_SITE_EXPORTED '+json.dumps(metadata['site']),flush=True)
if not os.getenv('HERITAGE_NO_RENDER'):
    selected = os.getenv('HERITAGE_VIEWS')
    for name in (selected.split(',') if selected else ['site'] if os.getenv('HERITAGE_DRAFT') else views):
        view(name);bpy.ops.render.render(write_still=True)
print('HERITAGE_SITE_COMPLETE',flush=True)
