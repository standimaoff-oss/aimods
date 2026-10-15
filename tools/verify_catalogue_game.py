#!/usr/bin/env python3
"""Destructive catalogue QA in a NEW disposable world, installed Forge/JAR only.
Every runtime item is enumerated, held, saved/loaded as NBT and its generic use paths
attempted. Those smoke checks are NOT full vehicle/tool acceptance. Firearm actions
use real mouse/R input; free-fall bombs use real entity physics, damage and blast jobs.
Reports remain incremental when an individual assertion fails or the JVM crashes.
"""
import json
import os
import re
import subprocess
import time
from pathlib import Path
import verify_game as g
from install_qa_client import prepare

ROWS = []
BOMBS = []
REPORT = g.LOGS / 'catalogue-gameplay.json'


def save():
    REPORT.write_text(json.dumps({'scope': 'catalogue smoke + firearm cycles + free-fall bombs',
        'items': ROWS, 'bombs': BOMBS,
        'limitations': ['Generic use is not proof of all contextual tool/vehicle features.',
            'Vehicle driving, every vehicle ammunition type, guided ordnance and remote-control cycles remain separate acceptance work.',
            'Linux llvmpipe cannot certify the Windows NVIDIA crash is fixed.']}, indent=2) + '\n')


def wait(test, seconds=30):
    end = time.monotonic() + seconds
    while time.monotonic() < end:
        if test():
            return
        time.sleep(.4)
    raise AssertionError('action did not reach its expected state before timeout')


def local(action):
    g.command('arsenal_visual_test client ' + action + ' TestPlayer')


def number(key):
    text = g.command('data get entity TestPlayer SelectedItem')
    match = re.search(r'\b' + key + r': (\d+)', text)
    return int(match[1]) if match else 0


def input_key(key):
    g.key('keydown', key)
    time.sleep(.3)
    g.key('keyup', key)


def fire():
    g.key('mousedown', '1')
    time.sleep(.22)
    g.key('mouseup', '1')


def equip(row, nbt=''):
    g.key('mouseup', '1'); g.key('mouseup', '3')
    local('view_first')
    g.command('ride TestPlayer dismount')
    g.command('tp TestPlayer 0.5 -60 0.5 0 0')
    g.command('clear TestPlayer')
    g.command('item replace entity TestPlayer hotbar.0 with ' + row['id'] + nbt)
    g.key('key', '1')
    time.sleep(.8)


def gun(row):
    equip(row, '{Ammo:0}')
    g.command('gamemode survival TestPlayer')
    g.command('effect give TestPlayer minecraft:resistance 9999 4 true')
    g.command('give TestPlayer ' + row['ammo'] + ' 16')
    # Genuine empty reload and state from the installed server, not an injected timer.
    input_key('r')
    wait(lambda: number('Ammo') > 0, max(20, row['reloadTicks'] / 20 + 10))
    if row['incremental']:
        time.sleep(row['capacity'] * row['reloadTicks'] / 20 + 3)
    row['emptyReload'] = 'PASS'
    g.screenshot(row['id'].split(':')[1] + '-loaded')
    if row['manpads']:
        # Engine-independent tagged aerial target, held stationary in a loaded chunk.
        # Seeking is real; Lock/Cool are never injected into the gun NBT.
        g.command('summon minecraft:bee 0.5 -48 30.5 {NoAI:1b,NoGravity:1b,PersistenceRequired:1b}')
        g.command('tp TestPlayer 0.5 -60 0.5 0 -19')
        g.key('mousedown', '3')
        wait(lambda: number('Lock') >= 100, 25)
    else:
        g.key('mousedown', '3')
        time.sleep(.6)
    before = number('Ammo')
    fire()
    wait(lambda: number('Ammo') < before, 8)
    row['shot'] = 'PASS'
    g.key('mouseup', '3')
    # Exercise the full empty->reload->fire cycle again, without manufacturing Ammo.
    # Large magazines are not artificially emptied: tactical reload is a distinct case.
    if row['capacity'] == 1:
        input_key('r')
        wait(lambda: number('Ammo') == 1, 20)
        row['repeatReload'] = 'PASS'
        if not row['manpads']:
            time.sleep(2)
            fire()
            wait(lambda: number('Ammo') == 0, 8)
            row['repeatShot'] = 'PASS'
    else:
        # Clip-fed weapons correctly reject partially-full reloads; existing logic tests
        # cover that contract. Do not call a rejected reload a successful reload.
        row['repeatReload'] = 'NOT_RUN (partial-magazine rules differ)'
        time.sleep(2)
        before = number('Ammo'); fire()
        wait(lambda: number('Ammo') < before, 8)
        row['repeatShot'] = 'PASS'
    g.command('gamemode creative TestPlayer')


def run():
    g.configure('server', server=True)
    client = g.RUNS / 'client'
    client.mkdir(parents=True, exist_ok=True)
    (client / 'options.txt').write_text('''version:3465
lang:ru_ru
tutorialStep:none
onboardAccessibility:false
skipMultiplayerWarning:true
joinedFirstServer:true
renderDistance:3
simulationDistance:5
maxFps:30
guiScale:2
fov:0.0
graphicsMode:0
renderClouds:"false"
pauseOnLostFocus:false
narrator:0
soundCategory_master:0.5
chatVisibility:0
chatOpacity:0.0
fullscreen:false
overrideWidth:1000
overrideHeight:700
''')
    cmd = prepare(g)
    args = g.RUNS / 'server/user_jvm_args.txt'
    args.write_text('-Xmx2048M\n-XX:+UseSerialGC\n-Daiarsenal.stressQa=true\n')
    server, server_log = g.launch('server', ['bash', 'run.sh', 'nogui'], cwd=g.RUNS / 'server')
    g.wait_log(server, server_log, 'Done (')
    player, client_log = g.launch('client', cmd, cwd=client)
    g.wait_log(server, server_log, 'TestPlayer joined the game')
    time.sleep(15)
    window = subprocess.check_output(['xdotool','search','--name','Minecraft'], text=True).splitlines()[-1]
    g.key('windowfocus','--sync',window)
    for command in ['time set 6000','gamerule doDaylightCycle false','weather clear','gamerule doWeatherCycle false',
                    'gamerule doMobSpawning false','gamerule keepInventory true','difficulty peaceful',
                    'gamemode creative TestPlayer','forceload add -32 -32 48 64',
                    'fill -12 -61 -8 12 -61 38 minecraft:smooth_stone','tp TestPlayer 0.5 -60 0.5 0 0']:
        g.command(command)
    g.command('arsenal_stress catalogue', expect='CATALOGUE')
    catalogue = json.loads((g.RUNS / 'server/logs/arsenal-catalogue.json').read_text())
    (g.LOGS / 'catalogue-inventory.json').write_text(json.dumps(catalogue, indent=2) + '\n')
    for entry in catalogue['items']:
        row = dict(entry, smoke='RUNNING', functional='NOT_VERIFIED')
        ROWS.append(row); save()
        try:
            assert row['nbtRoundtrip'], row
            equip(row)
            # Native F2 for EVERY item before consumption/equipment can empty the hand.
            g.screenshot('item-' + row['id'].split(':')[1])
            if 'ammo' in row:
                gun(row)
                row['functional'] = 'FIRE_RELOAD_CYCLE_PASS'
            else:
                row['genericUse'] = g.command('execute as TestPlayer at @s run arsenal_stress use', expect='USE ')
                time.sleep(2)
            assert player.poll() is None and server.poll() is None, 'Minecraft process exited'
            row['smoke'] = 'PASS'
        except Exception as ex:
            row['smoke'] = 'FAIL'; row['error'] = str(ex)
            if player.poll() is not None or server.poll() is not None:
                save(); raise
        finally:
            save()
        g.key('mouseup','1'); g.key('mouseup','3'); local('view_first')
        g.command('gamemode creative TestPlayer')
        g.command('ride TestPlayer dismount')
        # A fresh fixture for each item. QA never points at an existing player world.
        g.command('kill @e[type=!minecraft:player]')
        g.command('fill -10 -60 -6 10 -46 35 minecraft:air')
        g.command('fill -12 -61 -8 12 -61 38 minecraft:smooth_stone')
    local('view_first'); g.command('clear TestPlayer')
    for name in catalogue['freeFallBombs']:
        row = {'id': name, 'status': 'RUNNING'}; BOMBS.append(row); save()
        try:
            g.command('tp TestPlayer 0.5 -60 0.5 0 -10')
            g.command('fill -16 -61 -16 16 -61 48 minecraft:smooth_stone')
            g.command('execute as TestPlayer at @s run arsenal_stress drop ' + name, expect='DROPPED')
            last = {}
            def complete():
                last.update(json.loads(g.command('arsenal_stress bombstatus')))
                return last['removed'] and not last['activeBlasts'] and not last['legacyBusy']
            wait(complete, 240)
            row.update(last)
            assert last['removalReason'] == 'DISCARDED', last
            assert last['witnessDead'] or 0 <= last['witnessHealth'] < 20, 'bomb removed without damage to live witness'
            time.sleep(1)
            g.screenshot('bomb-' + name.lower().replace(':','-'))
            row['status'] = 'PASS'
        except Exception as ex:
            row['status'] = 'FAIL'; row['error'] = str(ex)
            if player.poll() is not None or server.poll() is not None:
                save(); raise
        finally:
            save()
    g.command('save-all flush', expect='Saved')
    # Clean server stop verifies saving a heavily exercised world; restart/rejoin is
    # deliberately a separate gate, not claimed by a successful save-all.
    g.command('stop'); server.wait(timeout=120)
    save()
    failures = [r for r in ROWS if r['smoke'] != 'PASS'] + [r for r in BOMBS if r['status'] != 'PASS']
    assert not failures, json.dumps(failures, indent=2)
    print('CATALOGUE PASS', len(ROWS), 'item smoke checks;', len(BOMBS), 'real free-fall detonations', flush=True)


if __name__ == '__main__':
    try:
        run()
    finally:
        save()
        g.cleanup()
