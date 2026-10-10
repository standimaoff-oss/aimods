#!/bin/bash
# sclone <dir> <repo> <ref> <paths...>
d=$1; repo=$2; ref=$3; shift 3
if [ -d "$d/.git" ]; then echo "$d exists"; exit 0; fi
git clone -q --filter=blob:none --no-checkout --depth 1 --branch "$ref" --sparse "https://github.com/$repo.git" "$d" || { echo "FAIL clone $d"; exit 1; }
cd "$d" && git sparse-checkout set --no-cone "$@" && git checkout -q 2>&1 | tail -1
echo "$d: $(find . -name '*.java' | wc -l) java"
