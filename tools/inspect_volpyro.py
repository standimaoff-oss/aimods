#!/usr/bin/env python3
"""Keep supplied-JAR client reference separate from executable mod sources."""
from pathlib import Path
import re
import sys
src, mapping = map(Path, sys.argv[1:3])
if not mapping.exists():
    candidates = list(Path('mods/aiarsenal/build').rglob('output.srg'))
    raise SystemExit(f'Expected {mapping}; found {candidates}')
names = {}
for line in mapping.read_text().splitlines():
    p = line.split()
    if p and p[0] == 'FD:':
        names[p[1].split('/')[-1]] = p[2].split('/')[-1]
    elif p and p[0] == 'MD:':
        names[p[1].split('/')[-1]] = p[3].split('/')[-1]
root = src / 'com/example/volpyro'
out = Path('notes/stage1/volpyro-reference')
# Do not import block/item/recipe registrations from the donor mod.
for part in ('client', 'config', 'sim'):
    for file in (root / part).rglob('*.java'):
        text = re.sub(r'\b[mf]_\d+_\b', lambda m: names.get(m[0], m[0]), file.read_text())
        dest = out / file.relative_to(root).with_suffix('.java.txt')
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_text(text)
print('Saved reference for review:', len(list(out.rglob('*.txt'))))
