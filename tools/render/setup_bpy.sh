#!/bin/bash
# r27: headless Blender (bpy 5.0.1 wheel, cp311) for the sandbox without X/GL libs.
# Creates ~/.cache/bpyenv (bpy + numpy + pillow) and ~/.cache/stubs (no-op X11/GL shared libs so `import bpy` works).
# Use:  LD_LIBRARY_PATH=~/.cache/stubs ~/.cache/bpyenv/bin/python script.py      (Cycles CPU only; EEVEE needs real GL)
set -e
H=/home/user/.cache
if [ ! -x $H/bpyenv/bin/python ]; then
  python3.11 -m venv $H/bpyenv
  $H/bpyenv/bin/pip install -q bpy==5.0.1 numpy pillow
fi
mkdir -p $H/stubs
D=$(dirname "$(readlink -f "$0")")
for so in libXrender.so.1 libXfixes.so.3 libXi.so.6 libxkbcommon.so.0 libSM.so.6 libICE.so.6 libGL.so.1 libXt.so.6; do
  [ -f $H/stubs/$so ] || gcc -shared -fPIC -Wl,-soname,$so -o $H/stubs/$so "$D/stub.c"
done
LD_LIBRARY_PATH=$H/stubs $H/bpyenv/bin/python -c "import bpy; print('bpy', bpy.app.version_string)"
