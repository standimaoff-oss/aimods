#!/bin/bash
# r27: tools/rwveh/run.sh for the bpy module (no Blender binary): concat Blender libs + optional prelude + script, exec in bpy.
# usage: tools/render/run_bpy.sh tools/rwveh/t34.py ["python prelude"]
R=/home/user/aimods/tools
B=$R/blender
mkdir -p /home/user/.cache/rwveh/raw /home/user/models
OUT=/home/user/.cache/rwveh/$(basename "$1" .py)_full.py
{ echo "import bpy, sys"; cat $B/lib.py $B/alib.py $B/arsenal_lib.py $B/rwveh_lib.py $B/armor_lib.py $B/ww2_lib.py; echo "${2:-}"; cat "$1"; } > "$OUT"
LD_LIBRARY_PATH=/home/user/.cache/stubs exec /home/user/.cache/bpyenv/bin/python -c "
import bpy, sys
src = open('$OUT', encoding='utf-8').read()
g = {'__name__': '__main__', '__file__': '$OUT'}
exec(compile(src, '$OUT', 'exec'), g)
" 2>&1 | grep -vE "^(Read|$)|Warning: .*rgba"
