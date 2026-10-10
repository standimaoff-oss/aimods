"""r27: run a Blender-style script against a .blend with the bpy module (replacement for `blender -b x.blend --python s.py -- args`).
usage: python blend_run.py model.blend script.py [args...]"""
import bpy, sys
blend, script = sys.argv[1], sys.argv[2]
bpy.ops.wm.open_mainfile(filepath=blend)
sys.argv = ["blender", "-b", blend, "--python", script, "--"] + sys.argv[3:]
exec(compile(open(script, encoding="utf-8").read(), script, "exec"), {"__name__": "__main__", "__file__": script})
