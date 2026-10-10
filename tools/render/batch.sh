#!/bin/bash
# usage: tools/render/batch.sh name...   (models/glb/<name>.glb -> ~/.cache/render/<name>_sheet.jpg)
# env: VIEWS=side,front,top,q34  RES=480  SAMPLES=8  GLB=<dir>
D=$(dirname "$(readlink -f "$0")")
GLB=${GLB:-/home/user/aimods/mods/aiarsenal/src/main/resources/assets/aiarsenal/models/glb}
O=/home/user/.cache/render; mkdir -p $O
VIEWS=${VIEWS:-side,front,top,q34}
for n in "$@"; do
  f=$n; [ -f "$f" ] || f=$GLB/$n.glb
  b=$(basename "$f" .glb)
  SAMPLES=${SAMPLES:-8} LD_LIBRARY_PATH=/home/user/.cache/stubs /home/user/.cache/bpyenv/bin/python "$D/render_glb.py" "$f" "$O/$b" "$VIEWS" "${RES:-480}" 2>&1 | grep -E "BBOX|Error|error" | head -5
  imgs=(); IFS=',' read -ra VV <<< "$VIEWS"; for v in "${VV[@]}"; do imgs+=("$O/${b}_$v.png"); done
  /home/user/.cache/bpyenv/bin/python "$D/sheet.py" "$O/${b}_sheet.jpg" "${imgs[@]}"
done
