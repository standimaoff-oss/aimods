#!/bin/bash
# r27: finish rebuilt vehicles without the Blender binary: floatcheck -> quantized GLB -> LOD1 (decimated, no textures)
# usage: tools/render/finish_bpy.sh t34 kv2 ...   (expects /home/user/.cache/rwveh/raw/rw_<v>.glb + /home/user/models/rw_<v>.blend)
D=$(dirname "$(readlink -f "$0")")
T=/home/user/aimods/tools/rwveh
PY=/home/user/.cache/bpyenv/bin/python
R=/home/user/aimods/mods/aiarsenal/src/main/resources/assets/aiarsenal/models/glb
mkdir -p /home/user/.cache/rwveh/lod
for v in "$@"; do
  echo "== $v"
  LD_LIBRARY_PATH=/home/user/.cache/stubs $PY $D/blend_run.py /home/user/models/rw_$v.blend $T/floatcheck.py 0.02 2>&1 | grep -E "FLOATCHECK|FLOAT |NODE " | head -8
  $PY $T/glb_quant.py /home/user/.cache/rwveh/raw/rw_$v.glb $R/$v.glb
  K=1.0; [ $v = ratte ] && K=0.8
  raw=/home/user/.cache/rwveh/lod/rw_${v}_lod1.glb
  LD_LIBRARY_PATH=/home/user/.cache/stubs timeout 900 $PY $D/blend_run.py /home/user/models/rw_$v.blend $T/make_lod.py $raw $K 2>&1 | grep -E "LOD1|Error|Traceback"
  [ -f $raw ] && STRIP_IMAGES=1 $PY $T/glb_quant.py $raw $R/${v}_lod1.glb
  echo "  -> $(stat -c %s $R/$v.glb) / lod $(stat -c %s $R/${v}_lod1.glb 2>/dev/null) B"
done
echo FINISH_DONE
