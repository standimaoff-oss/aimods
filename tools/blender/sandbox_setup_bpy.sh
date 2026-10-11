#!/bin/bash
# Headless bpy для сред без apt и без доступа к download.blender.org (только github/pypi/npm).
# Ставит bpy с PyPI и собирает заглушки X11/GL, нужные для импорта модуля. Не для продакшена.
# Результат: $C/env.sh (LD_LIBRARY_PATH, BPY_PY).  Использование: bash tools/blender/sandbox_setup_bpy.sh
set -u
C=/home/user/.cache
mkdir -p $C && cd $C
[ -x $C/bpyenv/bin/python ] || python3 -m venv $C/bpyenv
$C/bpyenv/bin/pip install -q --upgrade pip
$C/bpyenv/bin/pip install -q bpy==5.0.1 || exit 1
X=$C/xlibs; mkdir -p $X/lib $X/ext; cd $X
if [ ! -f imgui_bundle.whl ]; then $C/bpyenv/bin/pip download -q --no-deps --only-binary=:all: imgui-bundle -d . && mv imgui_bundle-*.whl imgui_bundle.whl; fi
cd ext && unzip -q -o ../imgui_bundle.whl 'imgui_bundle.libs/*' && cp imgui_bundle.libs/*.so.* ../lib/ && cd ../lib
ln -sf libGLX-c14481bc.so.0.0.0 libGLX.so.0; ln -sf libOpenGL-4c5f8d52.so.0.0.0 libOpenGL.so.0; ln -sf libGLdispatch-64b28464.so.0.0.0 libGLdispatch.so.0
cd $X
BP=$C/bpyenv/lib/python3.11/site-packages/bpy
for f in $(find $BP -name "*.so*" -type f); do nm -D --undefined-only "$f" 2>/dev/null | awk '{print $2}'; done | sed 's/@.*//' | sort -u > undef.txt
gen() { local so=$1 re=$2 c=/tmp/stub_$1.c; : > $c
  grep -E "$re" undef.txt | while read s; do echo "int $s(void){return 0;}" >> $c; done
  echo "int stub_anchor_$RANDOM(void){return 0;}" >> $c; gcc -shared -fPIC -Wl,-soname,$so -w $c -o lib/$so; }
gen libXrender.so.1 '^XRender'
gen libXi.so.6 '^XI[A-Z]|^XGetDeviceControl|^XQueryDevicePointer|^XListInputDevices|^XFreeDeviceList|^XFreeDeviceInfo|^XGetDeviceProperty|^XChangeDeviceProperty|^XOpenDevice|^XCloseDevice|^XSelectExtensionEvent|^XGetSelectedExtensionEvents|^XIQueryDevice|^XFreeDeviceState|^XGetExtensionVersion|^XQueryDeviceState|^_XiGet'
gen libSM.so.6 '^Sm[A-Z]|^Smc|^Sms|^SM[A-Z]'
gen libICE.so.6 '^Ice'
gen libXt.so.6 '^Xt[A-Z]'
gen libXfixes.so.3 '^XFixes'
printf 'V_0.5.0 { global: *; local: *; };\n' > xkb.map
(grep -E '^xkb_' undef.txt | while read s; do echo "int $s(void){return 0;}"; done; echo 'int xkb_stub_anchor(void){return 0;}') > /tmp/xkb_full.c
gcc -shared -fPIC -Wl,-soname,libxkbcommon.so.0 -Wl,--version-script=xkb.map -w /tmp/xkb_full.c -o lib/libxkbcommon.so.0
echo 'int __gl_stub_anchor(void){return 0;}' > /tmp/stub_gl.c
gcc -shared -fPIC -Wl,-soname,libGL.so.1 -Wl,--no-as-needed /tmp/stub_gl.c -Llib -l:libOpenGL.so.0 -l:libGLX.so.0 -o lib/libGL.so.1
printf 'export LD_LIBRARY_PATH=%s/lib:%s/lib\nexport BPY_PY=%s/bpyenv/bin/python\n' $X $BP $C > $C/env.sh
echo SETUP_DONE
