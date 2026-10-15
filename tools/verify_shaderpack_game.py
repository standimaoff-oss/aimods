#!/usr/bin/env python3
"""Real installed Oculus/Embeddium/Photon client. Exercise pack on/off, actual gun
reload with R, scopes, ordinary and nuclear visual packet fallbacks. The destructive
bomb/registry audit is separate. Software OpenGL does NOT reproduce an NVIDIA GPU.
"""
import json
import re
import subprocess
import time
import verify_game as g
from install_qa_client import prepare
from install_shaderpack_qa import install


def wait(test, seconds=180):
    end=time.monotonic()+seconds
    while time.monotonic()<end:
        value=test()
        if value:
            return value
        time.sleep(1)
    raise AssertionError('shader compatibility condition timed out')


def run():
    g.configure('server',server=True)
    client=g.RUNS/'client'; client.mkdir(parents=True,exist_ok=True)
    (client/'options.txt').write_text('''version:3465
lang:ru_ru
tutorialStep:none
onboardAccessibility:false
skipMultiplayerWarning:true
joinedFirstServer:true
renderDistance:2
simulationDistance:5
maxFps:20
guiScale:2
fov:0.0
graphicsMode:0
pauseOnLostFocus:false
soundCategory_master:0.5
chatOpacity:0.0
fullscreen:false
overrideWidth:900
overrideHeight:600
''')
    cmd=prepare(g); install(g)
    server,slog=g.launch('server',['bash','run.sh','nogui'],cwd=g.RUNS/'server')
    g.wait_log(server,slog,'Done (')
    player,log=g.launch('client',cmd,cwd=client)
    g.wait_log(server,slog,'TestPlayer joined the game')
    time.sleep(15)
    window=subprocess.check_output(['xdotool','search','--name','Minecraft'],text=True).splitlines()[-1]
    g.key('windowfocus','--sync',window)
    for command in ['time set 6000','gamerule doDaylightCycle false','gamerule doMobSpawning false',
                    'gamemode creative TestPlayer','fill -12 -61 -8 12 -61 30 minecraft:smooth_stone',
                    'tp TestPlayer 0.5 -60 0.5 0 0','clear TestPlayer']:
        g.command(command)

    def local(effect):
        offset=log.stat().st_size
        g.command('arsenal_visual_test client '+effect+' TestPlayer')
        return wait(lambda: next((line for line in log.read_text(errors='replace')[offset:].splitlines()
                                  if 'FX QA '+effect+':' in line), None))

    def status(active):
        line=local('status')
        assert 'active='+str(active).lower() in line,line
        return int(re.search(r'frames=(\d+)',line)[1])

    status(False)
    assert 'reason=active-shaderpack' in log.read_text(errors='replace'), 'pack failed to compile / API not detected'
    assert status(False)==0, 'raw volumetric draw ran with an active pack'
    # Pack compilation can outlast ReceivingLevelScreen. An acknowledged FX
    # packet alone does not mean gameplay input is enabled; verify the UI too.
    g.view_action(log,'view_first')
    g.view_action(log,'view_ready')
    time.sleep(3)
    g.screenshot('photon-initial')
    for weapon in ['ppsh41','mosin_pu','musket_1777']:
        ammo={'ppsh41':'mag_ppsh','mosin_pu':'round_762x54r','musket_1777':'paper_cartridge'}[weapon]
        g.command('clear TestPlayer')
        g.command('item replace entity TestPlayer hotbar.0 with aiarsenal:'+weapon+'{Ammo:0}')
        g.command('give TestPlayer aiarsenal:'+ammo+' 8')
        g.key('key','1');time.sleep(2)
        # Keep Oculus defaults. This also detects the R/reload-shaders key conflict;
        # never quietly rebind another mod merely to make this test pass.
        g.key('keydown','r');time.sleep(.3);g.key('keyup','r')
        capacity={'ppsh41':71,'mosin_pu':5,'musket_1777':1}[weapon]
        def fully_loaded():
            match=re.search(r'Ammo: (\d+)',g.command('data get entity TestPlayer SelectedItem'))
            return match and int(match[1])==capacity
        wait(fully_loaded)  # scoped Mosin loads individual rounds; first round is not completion
        local('status')  # wait for the client, including any shader reload, to respond
        g.key('mousedown','3');time.sleep(3)
        g.screenshot('photon-'+weapon+'-ads')
        if weapon=='mosin_pu':
            g.assert_scope_mask('photon-'+weapon+'-ads')
        before=int(re.search(r'Ammo: (\d+)',g.command('data get entity TestPlayer SelectedItem'))[1])
        g.key('mousedown','1')
        try:
            wait(lambda:int(re.search(r'Ammo: (\d+)',g.command('data get entity TestPlayer SelectedItem'))[1])<before,30)
        finally:
            g.key('mouseup','1');g.key('mouseup','3')
        time.sleep(3)
    for effect in ['blast','nuke','legacy_nuke']:
        g.command('arsenal_visual_test '+effect+' 0 -60 22')
        time.sleep(4)
        g.screenshot('photon-fallback-'+effect)
    assert status(False)==0, 'raw GL pass executed under Photon'
    toggles=[]
    for iteration in range(2):
        g.key('key','k')
        wait(lambda: 'active=true' in local('status'))
        local('unpack')
        assert 'FX UNPACK PASS' in log.read_text(errors='replace')
        local('smoke');time.sleep(3)
        assert status(True)>0, 'vanilla volumetrics did not resume when shaderpack was disabled'
        g.screenshot('photon-disabled-'+str(iteration))
        g.key('key','k')
        wait(lambda: 'active=false' in local('status'))
        before=status(False)
        g.command('arsenal_visual_test nuke 0 -60 22');time.sleep(3)
        after=status(False)
        assert after<=before,'raw GL draws continued after enabling the pack'
        toggles.append({'round':iteration,'framesBefore':before,'framesAfter':after})
        g.screenshot('photon-reenabled-'+str(iteration))
    text=log.read_text(errors='replace')
    assert player.poll() is None and server.poll() is None
    bad=re.findall(r'^.*(?:GL renderer disabled|OutOfMemoryError|EXCEPTION_ACCESS_VIOLATION|GL_INVALID|OpenGL Error).*$' ,text,re.M)
    assert not bad,'\n'.join(bad)
    (g.LOGS/'shaderpack-gameplay.json').write_text(json.dumps({'result':'PASS','toggles':toggles,
        'guns':['ppsh41','mosin_pu','musket_1777'],'reloadInput':'real R, Oculus defaults unchanged',
        'fallbackPackets':['blast','nuke','legacy_nuke'],
        'limits':'Linux llvmpipe, not Windows/NVIDIA; Photon SH_SKYLIGHT=false (32768-byte shared memory limit), default preset NOT VERIFIED; visual packets do not certify bomb physics or damage'},indent=2)+'\n')
    g.command('save-all flush')
    print('SHADERPACK COMPATIBILITY PASS',flush=True)


if __name__=='__main__':
    try:
        run()
    finally:
        g.cleanup()
