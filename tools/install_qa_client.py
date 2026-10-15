#!/usr/bin/env python3
"""Install production Forge + built JAR, never put userdev classes on the client classpath.
Private loopback QA only; no account credentials, no public/offline server.
Requires minecraft-launcher-lib==7.1, Java 17 and internet access to official distribution hosts.
All Minecraft runtime files stay in MC_RUNS (outside the repository in CI).
"""
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import uuid

FORGE = '1.20.1-47.4.23'
INSTALLER_SHA1 = 'ed31ce02ac69176f34353235cb2508d5a0f1e088'


def prepare(game):
    from minecraft_launcher_lib import forge, command
    root = game.RUNS / 'installed'
    root.mkdir(parents=True, exist_ok=True)
    jars = [p for p in (game.MOD / 'build/libs').glob('aiarsenal-*.jar')
            if not p.name.endswith(('-sources.jar', '-javadoc.jar'))]
    assert len(jars) == 1, jars
    jar = jars[0]
    digest = hashlib.sha256(jar.read_bytes()).hexdigest()
    # Standard Forge processors + Mojang release libraries/assets, not ForgeGradle runClient.
    forge.install_forge_version(FORGE, root, java='java',
                                callback={'setStatus': lambda s: print(s, flush=True)})
    version = '1.20.1-forge-47.4.23'
    assert (root / 'versions' / version / (version + '.json')).is_file()
    client = game.RUNS / 'client'
    server = game.RUNS / 'server'
    for folder in (client, server):
        mods = folder / 'mods'
        mods.mkdir(parents=True, exist_ok=True)
        assert not list(mods.glob('*.jar')), 'refuse to mix existing mods into release QA'
        shutil.copy2(jar, mods / jar.name)
        assert hashlib.sha256((mods / jar.name).read_bytes()).hexdigest() == digest
    installer = root / 'forge-installer.jar'
    subprocess.run(['curl', '--fail', '--retry', '3', '-L',
                    f'https://maven.minecraftforge.net/net/minecraftforge/forge/{FORGE}/forge-{FORGE}-installer.jar',
                    '-o', str(installer)], check=True)
    assert hashlib.sha1(installer.read_bytes()).hexdigest() == INSTALLER_SHA1
    with (game.LOGS / 'installed-server-installer.log').open('w') as log:
        subprocess.run(['java', '-jar', str(installer), '--installServer', str(server)],
                       stdout=log, stderr=subprocess.STDOUT, check=True, timeout=900)
    (server / 'user_jvm_args.txt').write_text('-Xmx1024M\n-XX:+UseSerialGC\n')
    # Java UUID.nameUUIDFromBytes for the disposable offline TestPlayer, not an account token.
    offline_id = uuid.UUID(bytes=hashlib.md5(b'OfflinePlayer:TestPlayer').digest(), version=3)
    options = {'username': 'TestPlayer', 'uuid': str(offline_id), 'token': '0',
               'executablePath': 'java', 'gameDirectory': str(client),
               'quickPlayMultiplayer': '127.0.0.1:25565',
               'jvmArguments': ['-Xmx2048M', '-XX:+UseSerialGC', '-Daiarsenal.visualQa=true',
                                '-Dfml.earlyprogresswindow=false', '-Dfml.earlyWindowControl=false']}
    cmd = command.get_minecraft_command(version, root, options)
    assert 'forgeclientuserdev' not in ' '.join(cmd)
    assert 'forgeclient' in cmd and all('/build/classes' not in arg for arg in cmd)
    report = {'forge': FORGE, 'launcher_library': 'minecraft-launcher-lib==7.1',
              'jar': jar.name, 'sha256': digest, 'client_mods': str(client / 'mods'),
              'server_mods': str(server / 'mods'), 'launch_target': 'forgeclient',
              'classpath_kind': 'installed release libraries; no Gradle source sets',
              'installer_sha1': INSTALLER_SHA1}
    (game.LOGS / 'installed-provenance.json').write_text(json.dumps(report, indent=2) + '\n')
    # Contains only a dummy offline token; retain the exact invocation for packaging diagnosis.
    (game.LOGS / 'installed-command.json').write_text(json.dumps(cmd, indent=2) + '\n')
    return cmd
