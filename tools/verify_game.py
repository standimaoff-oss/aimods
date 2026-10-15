#!/usr/bin/env python3
"""Run real Minecraft QA in an isolated cache directory (also used by Actions).
No generated/raster mockups: screenshots are exclusively Minecraft's F2 output.
Requires Java 17; client mode also needs a running X server and xdotool.
Runtime is disposable; never point MC_RUNS at a player's existing world.
"""
import json
import os
import re
from pathlib import Path
import shutil
import signal
import subprocess
import sys
import time

from rcon import run as rcon

ROOT = Path(__file__).resolve().parents[1]
MOD = ROOT / 'mods/aiarsenal'
OUT = ROOT / 'verification'
RUNS = Path(os.environ.get('MC_RUNS', str(Path.home() / '.cache/mc/qa-stage1')))
os.environ['MC_RUNS'] = str(RUNS)
LOGS = OUT / 'logs'
LOGS.mkdir(parents=True, exist_ok=True)
PROCESSES = []
HANDLES = []
# Private disposable QA server, bound to loopback (not a browser/API service).
PASSWORD = 'disposable-stage1-qa'


def gradle(*tasks):
    return [str(MOD / 'gradlew'), '--no-daemon', '--console=plain',
            '--project-cache-dir', str(RUNS / 'gradle-project'),
            '-Dorg.gradle.jvmargs=-Xmx1400m -XX:+UseSerialGC', *tasks]


def launch(name, command):
    log = LOGS / (name + '.log')
    handle = log.open('w')
    HANDLES.append(handle)
    process = subprocess.Popen(command, cwd=MOD, stdout=handle, stderr=subprocess.STDOUT, start_new_session=True)
    PROCESSES.append(process)
    return process, log


def wait_log(process, path, marker, seconds=900):
    end = time.monotonic() + seconds
    while time.monotonic() < end:
        text = path.read_text(errors='replace') if path.exists() else ''
        if marker in text:
            return
        if process.poll() is not None:
            raise RuntimeError(f'{path.name}: exited {process.returncode} before {marker}\n{text[-6000:]}')
        time.sleep(2)
    raise TimeoutError(f'{path.name}: no {marker} after {seconds}s')


def configure(name, server=False):
    folder = RUNS / name
    folder.mkdir(parents=True, exist_ok=True)
    # Refuse to overwrite user worlds. CI and local QA should use a fresh directory.
    if (folder / 'world').exists():
        raise RuntimeError(f'{folder}/world already exists; choose a fresh MC_RUNS directory')
    (folder / 'eula.txt').write_text('eula=true\n')
    properties = {
        'level-type': 'minecraft\\:flat', 'level-seed': '20261014',
        'generator-settings': json.dumps({'layers': [{'block': 'minecraft:bedrock', 'height': 1},
            {'block': 'minecraft:dirt', 'height': 2}, {'block': 'minecraft:grass_block', 'height': 1}],
            'biome': 'minecraft:plains', 'features': False, 'lakes': False}),
        'generate-structures': 'false', 'spawn-protection': '0',
    }
    if server:
        properties.update({'online-mode': 'false', 'enable-rcon': 'true', 'rcon.password': PASSWORD,
                           'rcon.port': '25575', 'server-ip': '127.0.0.1', 'view-distance': '2',
                           'simulation-distance': '2', 'gamemode': 'creative', 'difficulty': 'peaceful'})
    (folder / 'server.properties').write_text(''.join(f'{k}={v}\n' for k, v in properties.items()))
    return folder


def command(text, expect=None):
    answer = rcon('127.0.0.1', 25575, PASSWORD, text, 30)
    with (LOGS / 'rcon.log').open('a') as f:
        f.write(f'> {text}\n{answer}\n')
    print(text, '->', answer, flush=True)
    if expect and expect not in answer:
        raise AssertionError(f'Expected {expect!r}, got {answer!r}')
    return answer


def key(*args):
    subprocess.run(['xdotool', *args], check=True, timeout=30)


def screenshot(name):
    src = RUNS / 'client/screenshots'
    before = set(src.glob('*.png'))
    key('key', 'F2')
    end = time.monotonic() + 60
    while time.monotonic() < end:
        fresh = set(src.glob('*.png')) - before
        if fresh:
            time.sleep(2)  # allow PNG writer to close the image
            path = max(fresh, key=lambda p: p.stat().st_mtime_ns)
            from PIL import Image, ImageStat
            with Image.open(path) as image:
                image.load()
                assert min(image.size) >= 480
                assert sum(ImageStat.Stat(image.convert('RGB')).mean) > 20, 'black screenshot'
            dest = OUT / 'shots' / (os.environ.get('QA_PREFIX', 'review2') + '-' + name + '.png')
            dest.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(path, dest)
            print('Minecraft F2:', dest, flush=True)
            return
        time.sleep(1)
    raise TimeoutError('No Minecraft F2 screenshot; desktop capture is NOT an acceptable fallback')


def gametest():
    configure('gameTestServer')
    process, log = launch('gametest', gradle('runGameTestServer'))
    code = process.wait(timeout=1200)
    text = log.read_text(errors='replace')
    if code or 'required tests passed' not in text:
        raise RuntimeError(f'GameTests failed (exit {code})\n{text[-9000:]}')
    print('\n'.join(line for line in text.splitlines() if 'required tests' in line), flush=True)


def client():
    configure('server', server=True)
    folder = RUNS / 'client'
    folder.mkdir(parents=True, exist_ok=True)
    (folder / 'options.txt').write_text('''tutorialStep:none
onboardAccessibility:false
skipMultiplayerWarning:true
joinedFirstServer:true
renderDistance:2
simulationDistance:5
maxFps:30
guiScale:2
fov:0.0
graphicsMode:0
renderClouds:"false"
pauseOnLostFocus:false
narrator:0
soundCategory_master:0.0
chatVisibility:0
chatOpacity:0.0
textBackgroundOpacity:0.0
fullscreen:false
overrideWidth:1000
overrideHeight:700
''')
    server, log = launch('server', gradle('runServer'))
    wait_log(server, log, 'Done (')
    player, client_log = launch('client', gradle('runClient', '-PautoJoin=127.0.0.1:25565'))
    wait_log(server, log, 'TestPlayer joined the game', 900)
    wait_log(player, client_log, 'Loaded', 120)
    time.sleep(15)
    window = subprocess.check_output(['xdotool', 'search', '--name', 'Minecraft'], text=True).splitlines()[-1]
    key('windowfocus', '--sync', window)
    for cmd in ['time set 6000', 'gamerule doDaylightCycle false', 'weather clear',
                'gamerule doWeatherCycle false', 'gamerule doMobSpawning false', 'gamemode creative TestPlayer',
                'fill -12 -61 -8 12 -61 25 minecraft:smooth_stone',
                'fill -8 -60 22 8 -53 22 minecraft:white_concrete',
                'fill -1 -57 21 1 -55 21 minecraft:red_concrete',
                'tp TestPlayer 0 -60 0 0 0', 'clear TestPlayer',
                'item replace entity TestPlayer hotbar.0 with aiarsenal:ppsh41{Ammo:71}',
                'give TestPlayer aiarsenal:mag_ppsh 3']:
        command(cmd)
    key('key', '1')
    time.sleep(8)
    screenshot('01-ppsh-first-person')
    key('mousedown', '3')
    time.sleep(4)
    screenshot('02-ppsh-aim')
    key('mouseup', '3')
    # Inspect the wide front cover and its attachment in third-person front view.
    key('key', 'F5')
    key('key', 'F5')
    command('tp TestPlayer 0 -60 0 25 5')
    time.sleep(4)
    screenshot('03-ppsh-third-person')
    key('key', 'F5')
    command('tp TestPlayer 0 -60 0 0 0')
    # Keep the real mouse held until the SERVER observes a shot, not for an arbitrary
    # short pulse that can fall between software-rendered frames. Always release on failure.
    fired = ''
    for attempt in range(2):
        key('windowfocus', '--sync', window)
        key('mousedown', '1')
        try:
            end = time.monotonic() + 4
            while time.monotonic() < end:
                time.sleep(0.2)
                fired = command('data get entity TestPlayer SelectedItem')
                match = re.search(r'Ammo: (\d+)', fired)
                if match and int(match[1]) < 71:
                    break
        finally:
            key('mouseup', '1')
        if match and int(match[1]) < 71:
            break
    time.sleep(3)  # settle queued release / recoil before reload
    fired = command('data get entity TestPlayer SelectedItem')
    match = re.search(r'Ammo: (\d+)', fired)
    if not (match and int(match[1]) < 71):
        screenshot('failure-ppsh-trigger')
        raise AssertionError(f'Firing did not consume rounds: {fired}')
    key('keydown', 'r')
    time.sleep(0.15)
    key('keyup', 'r')
    time.sleep(1)
    screenshot('04-ppsh-reload')
    time.sleep(5)
    screenshot('05-ppsh-reloaded')
    command('data get entity TestPlayer SelectedItem', 'Ammo: 71')
    if os.environ.get('QA_STAGE1C') == '1':
        ww2_weapons(client_log)
    if os.environ.get('QA_VOLUMETRIC') == '1':
        volumetric(player, client_log)
    command('stop')
    server.wait(timeout=90)


def ww2_weapons(client_log):
    # Actual user input and real server health/ammo. No screenshots substituted with model renders.
    specs = [('mosin_pu', 5, 'round_762x54r'), ('k98k_zf39', 5, 'round_792x57'),
             ('c96', 10, 'clip_c96'), ('tt33', 8, 'mag_tt33')]
    command('tp TestPlayer 0 -60 0 0 0')
    # Peaceful despawns hostile targets: enable peaceful only after the suite.
    command('difficulty normal')
    command('kill @e[tag=qa_target]')
    command('summon minecraft:husk 0.5 -60 16.5 {NoAI:1b,Silent:1b,PersistenceRequired:1b,Tags:["qa_target"],Attributes:[{Name:"minecraft:generic.max_health",Base:1000d}],Health:1000f}')
    def ammo():
        text = command('data get entity TestPlayer SelectedItem')
        match = re.search(r'Ammo: (\d+)', text)
        assert match, text
        return int(match[1])
    def health():
        text = command('data get entity @e[tag=qa_target,limit=1] Health')
        match = re.search(r'data: ([0-9.]+)f', text)
        assert match, text
        return float(match[1])
    for name, cap, supply in specs:
        command('clear TestPlayer')
        command(f'item replace entity TestPlayer hotbar.0 with aiarsenal:{name}' + '{Ammo:' + str(cap) + '}')
        command(f'give TestPlayer aiarsenal:{supply} 32')
        command('tp TestPlayer 0 -60 0 0 0')
        key('key', '1');time.sleep(3)
        screenshot(name + '-01-in-hand')
        key('mousedown','3');time.sleep(2)
        screenshot(name + '-02-aim')
        before = health()
        # One semi-automatic trigger edge. Hold until the server acknowledges firing.
        key('mousedown','1')
        try:
            deadline=time.monotonic()+6
            while time.monotonic()<deadline:
                time.sleep(0.25)
                if ammo()<cap:break
            else:raise AssertionError(name + ': no shot from LMB')
        finally:key('mouseup','1')
        time.sleep(2)
        assert ammo()==cap-1, name + ': semi-auto must fire once per press'
        assert health()<before, name + ': ADS shot missed target'
        if name=='c96':
            # Fixed 10-round magazine: prove reload refusal, then empty it with real clicks.
            key('key','r');time.sleep(1)
            assert ammo()==9, 'C96 must refuse a clip into a partly loaded magazine'
            key('mouseup','3')
            for left in range(8,-1,-1):
                # A software frame can exceed a short click; acknowledge every semi-auto shot.
                key('mousedown','1')
                try:
                    end=time.monotonic()+6
                    while time.monotonic()<end:
                        time.sleep(.25)
                        if ammo()==left:break
                    else:raise AssertionError('C96 trigger edge not observed, expected '+str(left))
                finally:key('mouseup','1')
                time.sleep(2)  # release must be observed before the next rising edge
            assert ammo()==0, 'C96 empty-magazine setup must use real firing'
        before_log=client_log.stat().st_size
        key('keydown','r');time.sleep(.2);key('keyup','r')
        deadline=time.monotonic()+10
        while time.monotonic()<deadline:
            with client_log.open('rb') as f:
                f.seek(before_log);fresh=f.read().decode('utf-8',errors='replace')
            if 'WEAPON QA reload-start '+name in fresh:break
            time.sleep(.05)
        else:raise AssertionError(name + ': client did not acknowledge reload')
        time.sleep(.2)
        screenshot(name + '-03-reload')
        time.sleep(7)
        expected=9 if name=='tt33' else cap
        assert ammo()==expected, name + ': reload did not finish at expected capacity'
        screenshot(name + '-04-reloaded')
        key('mouseup','3')
    command('kill @e[tag=qa_target]')
    command('difficulty peaceful')


def volumetric(player, client_log):
    def local(effect):
        before = client_log.stat().st_size
        # Dedicated opt-in client bridge: no dependence on chat focus or dropped X11 keys.
        command('arsenal_visual_test client ' + effect + ' TestPlayer', 'Client QA sent: ' + effect)
        end = time.monotonic() + 90
        while time.monotonic() < end:
            with client_log.open('rb') as stream:
                stream.seek(before)
                text = stream.read().decode('utf-8', errors='replace')
            if 'FX QA ' + effect + ':' in text:
                return text
            if player.poll() is not None:
                raise RuntimeError('Client exited during FX QA')
            time.sleep(1)
        screenshot('failure-fx-' + effect)
        raise TimeoutError('No client confirmation for FX ' + effect)

    command('clear TestPlayer')
    # Remove the close wall from weapon QA so it cannot hide a smoke volume behind its depth.
    command('fill -8 -60 21 8 -53 22 minecraft:air')
    command('tp TestPlayer 0 -60 0 0 0')
    local('clear')
    local('smoke')
    time.sleep(3)
    status = local('status')
    assert 'active=true' in status, status
    frames = re.search(r'frames=(\d+)', status)
    assert frames and int(frames[1]) > 0, status
    screenshot('06-volumetric-smoke')
    local('clear')
    command('arsenal_visual_test blast 0 -60 18', 'Visual test sent')
    time.sleep(1.2)
    screenshot('07-volumetric-blast')
    time.sleep(3)
    screenshot('08-volumetric-blast-smoke')
    local('clear')
    command('arsenal_visual_test bm21 0 -60 18', 'Visual test sent')
    time.sleep(2)
    screenshot('09-volumetric-bm21')
    local('clear')
    command('arsenal_visual_test bomber 0 -60 18', 'Visual test sent')
    time.sleep(2)
    screenshot('10-volumetric-bomber')
    local('clear')
    local('trail')
    time.sleep(1)
    screenshot('11-volumetric-trail')
    local('clear')
    command('tp TestPlayer 0 -60 0 0 -12')
    command('arsenal_visual_test nuke 0 -60 100', 'Visual test sent')
    time.sleep(9)
    screenshot('12-volumetric-nuke')
    time.sleep(8)
    screenshot('13-volumetric-nuke-late')
    local('clear')
    command('arsenal_visual_test legacy_nuke 0 -60 100', 'Visual test sent')
    time.sleep(10)
    screenshot('14-volumetric-arsenal-nuke')
    local('clear')
    local('budget')
    disabled = local('off')
    assert 'active=false' in disabled, disabled
    command('particle aiarsenal:volume_smoke 0 -59 12 1 1 1 0.01 12 force TestPlayer')
    time.sleep(2)
    screenshot('15-fallback-smoke')
    local('on')
    status = local('status')
    assert 'active=true' in status and 'volumes=0 plumes=0' in status, status
    text = client_log.read_text(errors='replace')
    assert 'FX BUDGET PASS' in text
    assert 'VolPyro shader ready: volumetric_raymarch.fsh' in text
    assert 'VolPyro shader ready: volumetric_composite.fsh' in text
    assert 'GL renderer disabled' not in text and 'GLSL compile failed' not in text


def cleanup():
    for process in reversed(PROCESSES):
        if process.poll() is None:
            os.killpg(process.pid, signal.SIGTERM)
            try:
                process.wait(timeout=20)
            except subprocess.TimeoutExpired:
                os.killpg(process.pid, signal.SIGKILL)
                process.wait(timeout=10)
    for handle in HANDLES:
        handle.close()
    for kind in ('server', 'client', 'gameTestServer'):
        path = RUNS / kind / 'logs/latest.log'
        if path.exists():
            shutil.copy2(path, LOGS / (kind + '-latest.log'))


if __name__ == '__main__':
    try:
        {'gametest': gametest, 'client': client}[sys.argv[1]]()
    finally:
        cleanup()
