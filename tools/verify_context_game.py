#!/usr/bin/env python3
"""Second-phase contextual actions in installed Minecraft, not catalogue smoke.
The launchpad and cannon interactions are invoked server-side through production
item/entity handlers. Craft triggers and Javelin locking use real mouse/keyboard.
No forced ammunition, lock, cooldown, flight progress or explosion packets.
"""
import json
import os
import re
import signal
import subprocess
import time
import traceback
import verify_game as g
from install_qa_client import prepare
from context_result import missile_complete, craft_fired, assert_complete

REPORT = dict(scope='contextual launchpad/craft/cannon/Javelin audit', expectedCases=0, cases=[],
              runOutcome={'status':'RUNNING'}, worldSaveReopen={'status':'NOT_RUN'},
              limitations=['Not complete acceptance of all 448 items or all craft weapons/flight modes.',
                           'Linux llvmpipe, not Windows NVIDIA/Oculus certification.'])
SERVER = CLIENT = None


def save():
    (g.LOGS/'context-gameplay.json').write_text(json.dumps(REPORT,indent=2)+'\n')


def wait(test, seconds=60):
    end=time.monotonic()+seconds
    while time.monotonic()<end:
        for process in [SERVER, CLIENT]:
            if process is not None and process.poll() is not None:
                raise RuntimeError('Minecraft JVM exited '+str(process.returncode))
        value=test()
        if value:return value
        time.sleep(.5)
    raise AssertionError('context action timed out')


def qa(command):
    return json.loads(g.command('execute as TestPlayer at @s run arsenal_context '+command))


def local(action):
    g.command('arsenal_visual_test client '+action+' TestPlayer')


def key(k):
    g.key('keydown',k);time.sleep(.2);g.key('keyup',k)


def reset_player(x,z,y=-60):
    g.key('mouseup','1');g.key('mouseup','3')
    g.command('ride TestPlayer dismount')
    g.command('gamemode creative TestPlayer')
    g.command(f'tp TestPlayer {x+.5} {y} {z+.5} 0 0')
    g.command('clear TestPlayer')
    g.key('key','1')
    g.command('effect give TestPlayer minecraft:resistance 99999 4 true')
    g.command('effect give TestPlayer minecraft:night_vision 99999 0 true')
    g.command('gamemode survival TestPlayer')
    local('view_first');time.sleep(1)


def missile(row,index):
    x,z=0,800+index*640
    reset_player(x,z)
    g.command(f'forceload add -16 {z-16} 32 {z+32}')
    row['load']=qa('preparemissile '+row['id'].split(':')[1]);save()
    wait(lambda:qa('missilestatus')['pad']=='READY',60)
    row['ready']='PASS';qa('launchmissile')
    wait(lambda:qa('missilestatus')['spawned']>0,60)
    row['launch']='PASS';g.screenshot('launch-'+row['id'].split(':')[1]);save()
    tx,tz=row['load']['targetX'],row['load']['targetZ']
    g.command('gamemode spectator TestPlayer')
    # Observe the target, outside the blast; do not touch projectile positions.
    g.command(f'tp TestPlayer {tx+75} 30 {tz-90} 40 30')
    def completed():
        row['observed']=qa('missilestatus');save()
        return missile_complete(row['observed'])
    wait(completed,360)
    g.screenshot('impact-'+row['id'].split(':')[1])
    g.command(f'forceload remove -16 {z-16} 32 {z+32}')
    row['method']='survival pad item placement -> consume missile -> real 150-tick load -> schedule -> flight/warheads -> destructive jobs finish'


def craft(row,index):
    x,z=5000+index*192,0
    reset_player(x,z)
    if not row['air']:
        g.command('gamemode creative TestPlayer')
        for y in range(-60,-50):
            g.command(f'fill {x-48} {y} -48 {x+48} {y} 48 minecraft:water')
        g.command(f'tp TestPlayer {x+.5} -49 .5 0 90')
        g.command('gamemode survival TestPlayer')
    else:
        g.command(f'tp TestPlayer {x+.5} -58 .5 0 90')
    row['placed']=qa('preparecraft '+row['id']);save()
    local('view_back');time.sleep(3)
    initial=qa('craftstatus');assert initial['riding'] and initial['alive'],initial
    key('h');wait(lambda:qa('craftstatus')['engine'],30)
    row['engine']='PASS'
    def shoot():
        before=qa('craftstatus');assert before['selected']>=0,before
        assert before['loads'][before['selected']]['ammo']>0,before
        latest={}
        g.key('mousedown','1')
        try:
            def fired():
                latest.update(qa('craftstatus'));return craft_fired(before,latest)
            wait(fired,75)
        finally:g.key('mouseup','1')
        return {'before':before,'after':latest}
    row['firstShot']=shoot();save()
    row['service']=qa('servicecraft')
    slot=row['firstShot']['before']['selected']
    assert row['service']['loads'][slot]['ammo']==row['placed']['loads'][slot]['ammo'],row
    assert row['service']['fuel']>.99 and row['service']['kitsRemaining']==1,row
    time.sleep(2);row['repeatShot']=shoot();save()
    g.screenshot('craft-'+row['id'].split(':')[1])
    row['method']='survival item placement/boarding; real H and LMB; production service-kit interaction; real repeat LMB plus projectile/bullet proof'
    row['unverified']='other weapon slots, full flight/navigation, defensive AI, alternate presets, GUI servicing'
    g.command('ride TestPlayer dismount')


def cannon(row,index):
    reset_player(8000,500+index*128)
    row['placed']=qa('preparecannon '+row['id']);row['cycles']=[]
    for cycle in range(2):
        loaded=qa('loadcannon');assert loaded['loading']>0,loaded
        wait(lambda:qa('cannonstatus')['loading']==0,45)
        before=qa('cannonstatus');after=qa('firecannon')
        assert after['loading']==-1,after
        assert sum(after['spawned'].values())==sum(before['spawned'].values())+1,after
        row['cycles'].append(dict(loaded=loaded,before=before,after=after));save()
    g.screenshot('cannon-'+row['id'].split(':')[1])
    row['method']='survival cannon item placement -> real charge consumption/160-tick load -> ignition/tool wear -> cannonball spawn; twice'


def javelin(row,index):
    from verify_catalogue_game import number
    x,z=9000,800
    reset_player(x,z)
    g.command('item replace entity TestPlayer hotbar.0 with aiarsenal:javelin')
    g.command('give TestPlayer aiarsenal:javelin_missile 2')
    row['cycles']=[]
    for n in range(2):
        tag='context_javelin_'+str(n)
        g.command(f'summon minecraft:cow {x+.5} -60 {z+40.5} {{Tags:["{tag}"],NoAI:1b,PersistenceRequired:1b}}')
        g.command(f'tp TestPlayer {x+.5} -60 {z+.5} 0 1')
        g.key('mousedown','3')
        try:wait(lambda:number('Lock')>=100,30)
        finally:g.key('mouseup','3')
        def consumed():
            text=g.command('clear TestPlayer aiarsenal:javelin_missile 0')
            return ('Found 1 matching' in text) if n==0 else ('No items were found' in text)
        wait(consumed,20)
        wait(lambda:'CONTEXT_TARGET_GONE' in g.command(f'execute unless entity @e[tag={tag}] run say CONTEXT_TARGET_GONE'),45)
        row['cycles'].append(dict(lock=100,remainingAmmo=1-n,targetGone=True));save()
        time.sleep(2)
    g.screenshot('javelin-repeat')
    row['method']='actual RMB hold -> seeker lock -> release -> ammunition consumed -> target killed; twice'


def run():
    global SERVER,CLIENT
    g.configure('server',server=True)
    client=g.RUNS/'client';client.mkdir(parents=True,exist_ok=True)
    (client/'options.txt').write_text('''version:3465
lang:ru_ru
tutorialStep:none
onboardAccessibility:false
skipMultiplayerWarning:true
joinedFirstServer:true
renderDistance:4
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
    cmd=prepare(g)
    (g.RUNS/'server/user_jvm_args.txt').write_text('-Xmx2560M\n-XX:+UseSerialGC\n-Daiarsenal.stressQa=true\n')
    SERVER,server_log=g.launch('server',['bash','run.sh','nogui'],cwd=g.RUNS/'server');g.wait_log(SERVER,server_log,'Done (')
    CLIENT,client_log=g.launch('client',cmd,cwd=client);g.wait_log(SERVER,server_log,'TestPlayer joined the game');time.sleep(15)
    window=subprocess.check_output(['xdotool','search','--name','Minecraft'],text=True).splitlines()[-1]
    g.key('windowfocus','--sync',window)
    for command in ['time set 6000','gamerule doDaylightCycle false','weather clear','gamerule doWeatherCycle false',
                    'gamerule doMobSpawning false','gamerule naturalRegeneration false','gamerule keepInventory true','difficulty peaceful']:
        g.command(command)
    local('unpack');g.wait_log(CLIENT,client_log,'FX UNPACK PASS',60)
    inventory=qa('inventory');REPORT['inventory']=inventory
    cases=([(dict(id='aiarsenal:'+id),missile,i) for i,id in enumerate(inventory['missiles'])]+
           [(dict(row),craft,i) for i,row in enumerate(inventory['craft'])]+
           [(dict(id='aiarsenal:'+id),cannon,i) for i,id in enumerate(['cannon_fr6','cannon_ri12'])]+
           [(dict(id='aiarsenal:javelin'),javelin,0)])
    REPORT['expectedCases']=len(cases);save()
    for row,action,index in cases:
        row['status']='RUNNING';REPORT['cases'].append(row);save()
        try:
            action(row,index);row['status']='PASS'
            print('CONTEXT PASS',row['id'],flush=True)
        except Exception as error:
            row.update(status='FAIL',error=repr(error),traceback=traceback.format_exc())
            print('CONTEXT FAIL',row['id'],repr(error),flush=True)
            if SERVER.poll() is not None or CLIENT.poll() is not None:raise
        finally:
            g.key('mouseup','1');g.key('mouseup','3');save()
    g.command('arsenal_stress catalogue',expect='CATALOGUE')
    g.command('arsenal_stress archive',expect='ARCHIVE SAVED')
    g.command('save-all flush',expect='Saved');g.command('stop');SERVER.wait(timeout=120)
    os.killpg(CLIENT.pid,signal.SIGTERM);CLIENT.wait(timeout=45)
    SERVER,reopen_server=g.launch('server-reopen',['bash','run.sh','nogui'],cwd=g.RUNS/'server');g.wait_log(SERVER,reopen_server,'Done (')
    CLIENT,reopen_client=g.launch('client-reopen',cmd,cwd=client);g.wait_log(SERVER,reopen_server,'TestPlayer joined the game');time.sleep(10)
    g.command('arsenal_stress archivecheck',expect='ARCHIVE VERIFIED 448')
    REPORT['worldSaveReopen']=dict(status='PASS',archivedItems=448);save()
    for path in [server_log,reopen_server,client_log,reopen_client]:
        text=path.read_text(errors='replace')
        bad=re.findall(r'^.*(?:Failed to store chunk|ConcurrentModificationException|Exception ticking|Exception in server tick loop|OutOfMemoryError|EXCEPTION_ACCESS_VIOLATION|GL renderer disabled|OpenGL Error|GL_INVALID|\[Render thread/ERROR\]|Ошибка в задаче взрыва).*$',text,re.M)
        assert not bad,path.name+': '+'\n'.join(bad[-20:])
    g.command('stop');SERVER.wait(timeout=120)
    assert_complete(REPORT)


if __name__=='__main__':
    try:
        run();REPORT['runOutcome']={'status':'PASS'}
    except BaseException as error:
        REPORT['runOutcome']={'status':'FAIL','error':repr(error)};raise
    finally:
        save();g.cleanup()
