#!/usr/bin/env python3
"""CI-only third-party compatibility fixture. Download publisher files from Modrinth,
verify the published SHA-512, and record exact version/file metadata. No redistribution
of third-party JARs or shader packs in Git or our release. Not a hardware GPU test.
"""
import hashlib
import json
from urllib.parse import urlencode
from urllib.request import Request, urlopen


def get(url):
    with urlopen(Request(url, headers={'User-Agent': 'aimods-stability-qa/1.0 (github.com/standimaoff-oss/aimods)'}), timeout=120) as response:
        return response.read()


def install(game):
    client = game.RUNS / 'client'
    provenance = []
    for project, fragment, folder in [('oculus', '1.8.0', 'mods'),
                                       ('embeddium', '0.3.31', 'mods'),
                                       ('photon-shader', '1.3b', 'shaderpacks')]:
        query = urlencode({'game_versions': json.dumps(['1.20.1'])})
        versions = json.loads(get('https://api.modrinth.com/v2/project/' + project + '/version?' + query))
        candidates = [(v, f) for v in versions for f in v['files']
                      if fragment in f['filename'].lower() and (folder != 'mods' or 'forge' in v['loaders'])]
        assert candidates, 'requested historical fixture unavailable: ' + project + ' ' + fragment
        version, file = next(((v, f) for v, f in candidates if f.get('primary')), candidates[0])
        data = get(file['url'])
        assert hashlib.sha512(data).hexdigest() == file['hashes']['sha512'], 'third-party checksum mismatch'
        dest = client / folder / file['filename']
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_bytes(data)
        provenance.append({'project': project, 'version_id': version['id'], 'version': version['version_number'],
                           'file': file['filename'], 'url': file['url'], 'sha512': file['hashes']['sha512']})
        if folder == 'shaderpacks':
            config = client / 'config/oculus.properties'
            config.parent.mkdir(parents=True, exist_ok=True)
            config.write_text('enableShaders=true\nshaderPack=' + file['filename'] + '\n')
    (game.LOGS / 'shaderpack-provenance.json').write_text(json.dumps(provenance, indent=2) + '\n')
