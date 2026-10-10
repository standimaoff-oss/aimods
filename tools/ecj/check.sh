#!/bin/bash
# r27: type-check the whole mod with ECJ against MC/Forge/library sources. Prints only errors in the mod's own files.
# usage: tools/ecj/check.sh [extra ecj args]      (run tools/ecj/setup.sh once per sandbox first)
C=$HOME/.cache
T=$(cd "$(dirname "$0")" && pwd)
R=$(cd "$T/../.." && pwd)
M=$C/mcsrc
MC=$M/digi/build/tmp/.cache/expanded/zip_51348f0b239ab79c430d7ade20fd8068
SP=$MC:$M/forge/src/fmlcommon/java:$M/forge/fmlcore/src/main/java:$M/forge/fmlloader/src/main/java:$M/forge/javafmllanguage/src/main/java:$M/eventbus/src/main/java
SP=$SP:$M/joml/src:$M/brig/src/main/java:$M/gson/gson/src/main/java:$M/dfu/src/main/java:$M/slf4j/slf4j-api/src/main/java
SP=$SP:$M/netty/buffer/src/main/java:$M/netty/common/src/main/java:$M/guava/guava/src:$M/clang/src/main/java
for d in core/src/main/java core/src/generated/java opengl/src/generated/java opengl/src/main/java glfw/src/generated/java glfw/src/main/java; do SP=$SP:$M/lwjgl/modules/lwjgl/$d; done
SP=$SP:$T/stubs
SRC=$R/mods/aiarsenal/src/main/java
OUT=$C/ecj/out.txt
$C/jdk/jdk4py/java-runtime/bin/java -Xmx6g -cp $C/ecj/package/jar/ctxo-jdt-analyzer-17.jar org.eclipse.jdt.internal.compiler.batch.Main \
  -17 -proceedOnError -nowarn -d none -encoding UTF-8 -sourcepath "$SP" "$@" $SRC > $OUT 2>&1
# ECJ prints "N. ERROR in <file> (at line L)" blocks; keep only blocks in our tree
python3 - "$OUT" "$SRC" <<'PY'
import sys, re
txt = open(sys.argv[1], encoding='utf-8', errors='replace').read()
blocks = re.split(r'\n-{10,}\n', txt)
ours = [b for b in blocks if re.search(r'ERROR in ' + re.escape(sys.argv[2]), b)]
for b in ours: print(b.strip()); print('-' * 40)
tail = [l for l in txt.splitlines() if re.match(r'^\d+ problems?', l)]
print('ERRORS IN MOD FILES:', len(ours), '|', tail[-1] if tail else '')
PY
