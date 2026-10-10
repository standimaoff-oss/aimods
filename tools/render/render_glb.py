# usage: python render_glb.py in.glb out_prefix [views] [res]
import bpy, sys, math, os
from mathutils import Vector
args = sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else sys.argv[1:]
src, out = args[0], args[1]
views = (args[2] if len(args) > 2 else 'side,front,top,q34').split(',')
res = int(args[3]) if len(args) > 3 else 640
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=src)
objs = [o for o in bpy.data.objects if o.type == 'MESH']
mn = Vector((1e9, 1e9, 1e9)); mx = Vector((-1e9, -1e9, -1e9))
for o in objs:
    for c in o.bound_box:
        w = o.matrix_world @ Vector(c)
        mn = Vector(map(min, mn, w)); mx = Vector(map(max, mx, w))
ctr = (mn + mx) / 2; size = (mx - mn)
print("BBOX", tuple(round(v, 3) for v in mn), tuple(round(v, 3) for v in mx), "size", tuple(round(v, 3) for v in size))
sc = bpy.context.scene
sc.render.engine = 'CYCLES'
sc.cycles.device = 'CPU'
sc.cycles.samples = int(os.environ.get('SAMPLES', '16'))
sc.cycles.use_denoising = False
sc.render.resolution_x = res; sc.render.resolution_y = int(res * 0.62)
sc.render.film_transparent = False
world = bpy.data.worlds.new("W"); sc.world = world
world.use_nodes = True
bg = world.node_tree.nodes['Background']; bg.inputs[0].default_value = (0.75, 0.8, 0.88, 1); bg.inputs[1].default_value = 0.9
sun = bpy.data.lights.new("sun", 'SUN'); sun.energy = 3.0
so = bpy.data.objects.new("sun", sun); sc.collection.objects.link(so)
so.rotation_euler = (math.radians(40), math.radians(15), math.radians(-35))
cam = bpy.data.cameras.new("cam"); cam.type = 'ORTHO'
co = bpy.data.objects.new("cam", cam); sc.collection.objects.link(co); sc.camera = co
R = max(size) * 2.5
# glTF import: Y-up -> Blender Z-up; model forward +Z(gltf) -> -Y(blender)
dirs = {'side': Vector((1, 0, 0)), 'sideR': Vector((-1, 0, 0)), 'front': Vector((0, -1, 0)), 'rear': Vector((0, 1, 0)),
        'top': Vector((0, 0, 1)), 'q34': Vector((1, -1.2, 0.8)).normalized(), 'q34r': Vector((-1, 1.2, 0.7)).normalized(),
        'low': Vector((1, -0.6, 0.15)).normalized()}
for v in views:
    d = dirs[v]
    co.location = ctr + d * R
    look = (ctr - co.location).normalized()
    up = Vector((0, 0, 1)) if v != 'top' else Vector((0, 1, 0))
    rot = look.to_track_quat('-Z', 'Y')
    if v == 'top':
        from mathutils import Euler
        co.rotation_euler = Euler((0, 0, math.radians(-90)))
        rot = co.rotation_euler.to_quaternion()
    co.rotation_euler = rot.to_euler()
    ext = {'side': max(size.y, size.z), 'sideR': max(size.y, size.z), 'front': max(size.x, size.z), 'rear': max(size.x, size.z), 'top': max(size.x, size.y)}.get(v, max(size) * 1.1)
    cam.ortho_scale = ext * 1.15 if v not in ('q34', 'q34r', 'low') else max(size) * 1.25
    sc.render.filepath = f"{out}_{v}.png"
    bpy.ops.render.render(write_still=True)
    print("WROTE", sc.render.filepath)
