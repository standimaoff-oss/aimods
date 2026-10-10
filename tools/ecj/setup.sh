#!/bin/bash
# r27: offline-ish Java type check without Gradle/javac (Forge maven + JDK downloads are blocked in the sandbox).
#  - ECJ (Eclipse batch compiler) from the npm package @ctxo/lang-java-analyzer (fat jar with JDT core)
#  - Java runtime from PyPI jdk4py
#  - Forge-patched MC 1.20.1 sources (official names) found committed in a GitHub repo's ForgeGradle cache
#  - FML / EventBus / libraries from their GitHub repos (sparse, depth 1); a few hand stubs in tools/ecj/stubs
set -e
C=$HOME/.cache
T=$(cd "$(dirname "$0")" && pwd)
mkdir -p $C/ecj $C/jdk $C/mcsrc
if [ ! -f $C/ecj/package/jar/ctxo-jdt-analyzer-17.jar ]; then
  (cd $C/ecj && npm pack @ctxo/lang-java-analyzer@0.9.0 --silent && tar xzf ctxo-lang-java-analyzer-0.9.0.tgz)
fi
if [ ! -x $C/jdk/jdk4py/java-runtime/bin/java ]; then
  (cd $C/jdk && python3 -m pip download jdk4py --no-deps -d . -q && python3 -c "
import zipfile,glob; zipfile.ZipFile(glob.glob('jdk4py-*.whl')[0]).extractall('.')" && chmod +x jdk4py/java-runtime/bin/*)
fi
cd $C/mcsrc
S=$T/sclone.sh
if [ ! -d digi/.git ]; then
  git clone -q --filter=blob:none --no-checkout --depth 1 --sparse https://github.com/themodderg/The-Digimod.git digi
  (cd digi && git sparse-checkout set --no-cone 'build/tmp/.cache/expanded/zip_51348f0b239ab79c430d7ade20fd8068/**' && git checkout -q)
fi
$S forge MinecraftForge/MinecraftForge 1.20.1 '/fmlcore/src/main/java/**' '/fmlloader/src/main/java/**' '/javafmllanguage/src/main/java/**' &
$S eventbus MinecraftForge/EventBus 6.0 '/src/main/java/**' &
$S joml JOML-CI/JOML 1.10.5 '/src/**/*.java' &
$S brig Mojang/brigadier master '/src/main/java/**' &
$S gson google/gson gson-parent-2.10.1 '/gson/src/main/java/**' &
$S dfu Mojang/DataFixerUpper master '/src/main/java/**' &
$S slf4j qos-ch/slf4j v_2.0.7 '/slf4j-api/src/main/java/**' &
$S netty netty/netty netty-4.1.89.Final '/buffer/src/main/java/**' '/common/src/main/java/**' &
$S lwjgl LWJGL/lwjgl3 3.3.1 '/modules/lwjgl/core/src/main/java/**' '/modules/lwjgl/core/src/generated/java/**' '/modules/lwjgl/opengl/src/generated/java/**' '/modules/lwjgl/opengl/src/main/java/**' '/modules/lwjgl/glfw/src/generated/java/**' '/modules/lwjgl/glfw/src/main/java/**' &
$S guava google/guava v32.1.2 '/guava/src/**' &
$S clang apache/commons-lang rel/commons-lang-3.12.0 '/src/main/java/**' &
wait
echo setup done
# FML lifecycle events live in src/fmlcommon of the Forge repo
(cd $C/mcsrc/forge && git sparse-checkout add '/src/fmlcommon/java/**' && git checkout -q)
# Forge 47.4 backports missing from the 47.1 sources (check-only copy)
python3 - <<'PY'
import os
p = os.path.expanduser('~/.cache/mcsrc/digi/build/tmp/.cache/expanded/zip_51348f0b239ab79c430d7ade20fd8068/net/minecraft/resources/ResourceLocation.java')
s = open(p, encoding='utf-8').read()
if 'fromNamespaceAndPath' not in s:
    i = s.index('public class ResourceLocation'); j = s.index('{', i) + 1
    s = s[:j] + '''
   public static ResourceLocation fromNamespaceAndPath(String ns, String path) { return new ResourceLocation(ns, path); }
   public static ResourceLocation withDefaultNamespace(String path) { return new ResourceLocation(path); }
   public static ResourceLocation parse(String s) { return new ResourceLocation(s); }
''' + s[j:]
    open(p, 'w', encoding='utf-8').write(s)
PY
# mod access transformer (accesstransformer.cfg) reflected in the check-only copy: Camera methods are public for the mod
python3 - <<'PY'
import os, re
p = os.path.expanduser('~/.cache/mcsrc/digi/build/tmp/.cache/expanded/zip_51348f0b239ab79c430d7ade20fd8068/net/minecraft/client/Camera.java')
s = open(p, encoding='utf-8').read()
s = s.replace('protected void setPosition(Vec3 ', 'public void setPosition(Vec3 ', 1)
s = s.replace('private double getMaxZoom(double ', 'public double getMaxZoom(double ', 1)
open(p, 'w', encoding='utf-8').write(s)
PY
