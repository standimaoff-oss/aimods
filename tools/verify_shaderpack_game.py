#!/usr/bin/env python3
"""Real installed Oculus/Embeddium/Photon client. Exercise pack on/off, actual gun
reload with R, scopes, ordinary and nuclear visual packet fallbacks. The destructive
bomb/registry audit is separate. Software OpenGL does NOT reproduce an NVIDIA GPU.
"""
import json
import os
import traceback
import re
import subprocess
import time
import verify_game as g
from install_qa_client import prepare
from install_shaderpack_qa import install
from qa_log import tail_from
from shader_log import scan
import verify_context_game as context
from shaderpack_actions import powder_cannon, sturmtiger

PACK=os.environ.get('QA_SHADERPACK','photon')
REPORT={'result':'RUNNING','pack':PACK,'actions':[], 'toggles':[]}

def save():
    (g.LOGS/'shaderpack-gameplay.json').write_text(json.dumps(REPORT,indent=2)+'\n')



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
    (g.RUNS/'server/user_jvm_args.txt').write_text('-Xmx2560M\n-XX:+UseSerialGC\n-Daiarsenal.stressQa=true\n')
    server,slog=g.launch('server',['bash','run.sh','nogui'],cwd=g.RUNS/'server')
    g.wait_log(server,slog,'Done (')
    player,log=g.launch('client',cmd,cwd=client)
    context.SERVER,context.CLIENT=server,player
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
        return wait(lambda: next((line for line in tail_from(log,offset).splitlines()
                                  if 'FX QA '+effect+':' in line), None))

    def status(expect_pack_blocked):
        line=local('status')
        assert 'active=true' in line,line
        assert 'packBlocked='+str(expect_pack_blocked).lower() in line,line
        expected_backend='shaderpack-raymarch-probe' if expect_pack_blocked else 'raymarch'
        assert 'backend='+expected_backend in line,line
        if expect_pack_blocked:
            assert 'probe=true' in line,line
        return line

    def frames(line):
        return int(re.search(r'frames=(\d+)',line)[1])

    def image_diff(first, second, relative_region=(.25,.2,.75,.78)):
        from PIL import Image, ImageChops
        folder=g.OUT/'shots'
        prefix=os.environ.get('QA_PREFIX','review2')
        a=Image.open(folder/(prefix+'-'+first+'.png')).convert('RGB')
        b=Image.open(folder/(prefix+'-'+second+'.png')).convert('RGB')
        assert a.size==b.size,(a.size,b.size)
        w,h=a.size
        box=(int(w*relative_region[0]),int(h*relative_region[1]),
             int(w*relative_region[2]),int(h*relative_region[3]))
        difference=ImageChops.difference(a.crop(box),b.crop(box))
        pixels=list(difference.getdata())
        mean=sum(sum(pixel) for pixel in pixels)/(3*len(pixels))
        changed=sum(max(pixel)>=16 for pixel in pixels)/len(pixels)
        return {'meanRgbDelta':mean,'changedFraction':changed,'region':list(box)}

    def volume_observation(effect, pack_blocked=True):
        local('clear')
        before=status(pack_blocked)
        start=frames(before)
        assert int(re.search(r'volumes=(\d+)',before)[1])==0,before
        assert int(re.search(r'plumes=(\d+)',before)[1])==0,before
        ack=local(effect)
        assert 'FX QA '+effect+':' in ack,ack
        volume_count=int(re.search(r'volumes=(\d+)',ack)[1])
        plume_count=int(re.search(r'plumes=(\d+)',ack)[1])
        if effect=='trail': assert plume_count>0,ack
        else: assert volume_count>0,ack
        after=wait(lambda: (lambda line: line if frames(line)>start else None)(status(pack_blocked)),120)
        expected_stage='minecraft:after_level' if pack_blocked else 'minecraft:after_particles'
        assert 'lastStage='+expected_stage in after,after
        ordinal=len(REPORT.get('raymarchObservations',[]))+1
        screenshot_name=PACK+'-raymarch-'+f'{ordinal:02d}-'+effect
        row={'effect':effect,'framesBefore':start,'framesAfter':frames(after),
             'volumesAfterEmit':volume_count,'plumesAfterEmit':plume_count,
             'safeParticles':int(re.search(r'safeParticles=(\d+)',after)[1]),
             'providerFallbackParticles':int(re.search(r'providerFallbackParticles=(\d+)',after)[1]),
             'screenshot':screenshot_name,'ack':ack,'after':after}
        REPORT.setdefault('raymarchObservations',[]).append(row);save()
        g.screenshot(screenshot_name)
        return row

    initial=status(True)
    assert frames(initial)==0,'an idle/empty shaderpack probe should not submit volume draws: '+initial
    assert 'reason=active-shaderpack' in log.read_text(errors='replace'), 'pack failed to compile / API not detected'
    # Pack compilation can outlast ReceivingLevelScreen. An acknowledged FX
    # packet alone does not mean gameplay input is enabled; verify the UI too.
    g.view_action(log,'view_first')
    g.view_action(log,'view_ready')
    time.sleep(3)
    g.screenshot(PACK+'-initial')

    # Counters alone can lie if a draw occurs before Iris' final composite.
    # Require visible pixels in open air and no cloud leak
    # through a solid wall in front of the raymarched density.
    local('clear')
    g.screenshot(PACK+'-probe-open-baseline')
    before=status(True);start=frames(before)
    open_ack=local('smoke')
    assert int(re.search(r'volumes=(\d+)',open_ack)[1])>0,open_ack
    open_after=wait(lambda: (lambda line: line if frames(line)>start else None)(status(True)),120)
    assert 'lastStage=minecraft:after_level' in open_after,open_after
    g.screenshot(PACK+'-probe-open-volume')
    open_diff=image_diff(PACK+'-probe-open-baseline',PACK+'-probe-open-volume',(.25,.1,.75,.55))
    assert open_diff['meanRgbDelta']>0.5 and open_diff['changedFraction']>0.01,open_diff

    g.command('fill -8 -60 7 8 -52 7 minecraft:stone');time.sleep(2)
    local('clear')
    g.screenshot(PACK+'-probe-wall-baseline')
    before=status(True);start=frames(before)
    wall_ack=local('smoke')
    assert int(re.search(r'volumes=(\d+)',wall_ack)[1])>0,wall_ack
    wall_after=wait(lambda: (lambda line: line if frames(line)>start else None)(status(True)),120)
    assert 'lastStage=minecraft:after_level' in wall_after,wall_after
    g.screenshot(PACK+'-probe-wall-volume')
    wall_diff=image_diff(PACK+'-probe-wall-baseline',PACK+'-probe-wall-volume',(.25,.1,.75,.58))
    # Keep the crop strictly on the wall: shaderpacks may animate pixels in the
    # sky, the floor or the player's idle arm between F2 frames.
    assert wall_diff['meanRgbDelta']<2.5 and wall_diff['changedFraction']<0.015,wall_diff
    g.command('fill -8 -60 7 8 -52 7 minecraft:air');time.sleep(2)
    REPORT['depthOcclusion']={'open':open_diff,'wall':wall_diff,
        'openFrames':frames(open_after),'wallFrames':frames(wall_after),
        'screenshots':[PACK+'-probe-open-baseline',PACK+'-probe-open-volume',
                       PACK+'-probe-wall-baseline',PACK+'-probe-wall-volume']};save()

    # Exercise every registered volumetric-particle provider through the real
    # ParticleEngine dispatch. A PASS requires a raymarch frame and zero vanilla
    # CAMPFIRE_COSY_SMOKE fallback allocations for that provider.
    for effect in ['provider_smoke','provider_muzzle','provider_powder','provider_cannon',
                   'provider_exhaust','provider_impact','fxsystem_smoke']:
        before=status(True)
        fallback_before=int(re.search(r'providerFallbackParticles=(\d+)',before)[1])
        safe_before=int(re.search(r'safeParticles=(\d+)',before)[1])
        observation=volume_observation(effect,True)
        fallback_after=int(re.search(r'providerFallbackParticles=(\d+)',observation['after'])[1])
        safe_after=int(re.search(r'safeParticles=(\d+)',observation['after'])[1])
        assert fallback_after==fallback_before,{'effect':effect,'providerFallbackBefore':fallback_before,'providerFallbackAfter':fallback_after}
        if effect=='fxsystem_smoke':
            assert safe_after==safe_before,{'effect':effect,'safeBefore':safe_before,'safeAfter':safe_after}

    # Also stress direct smoke, fire/smoke blast, nuclear cloud and rocket trail
    # emitters under the same active pack (not merely particle sprites).
    for effect in ['smoke','blast','nuke','trail']:
        volume_observation(effect,True)
    local('clear')
    cleared=status(True)
    assert int(re.search(r'volumes=(\d+)',cleared)[1])==0 and int(re.search(r'plumes=(\d+)',cleared)[1])==0,cleared

    reload_log_start=log.stat().st_size
    for weapon in ['ppsh41','mosin_pu','musket_1777']:
        ammo={'ppsh41':'mag_ppsh','mosin_pu':'round_762x54r','musket_1777':'paper_cartridge'}[weapon]
        g.command('clear TestPlayer')
        g.command('item replace entity TestPlayer hotbar.0 with aiarsenal:'+weapon+'{Ammo:0}')
        g.command('give TestPlayer aiarsenal:'+ammo+' 8')
        g.key('key','1');time.sleep(2)
        wait(lambda: 'aiarsenal:'+weapon in g.command('data get entity TestPlayer SelectedItem'),30)
        local('status') # client packet barrier before a real R; no shader rebind
        # Keep Oculus defaults. Production context arbitration must prevent shader
        # rebuilds here; never quietly rebind another mod to make this test pass.
        g.key('keydown','r');time.sleep(.3);g.key('keyup','r')
        capacity={'ppsh41':71,'mosin_pu':5,'musket_1777':1}[weapon]
        def fully_loaded():
            match=re.search(r'Ammo: (\d+)',g.command('data get entity TestPlayer SelectedItem'))
            return match and int(match[1])==capacity
        wait(fully_loaded)  # scoped Mosin loads individual rounds; first round is not completion
        local('status')  # wait for the client, including any shader reload, to respond
        g.key('mousedown','3');time.sleep(3)
        g.screenshot(PACK+'-'+weapon+'-ads')
        if weapon=='mosin_pu':
            g.assert_scope_mask(PACK+'-'+weapon+'-ads')
        before=int(re.search(r'Ammo: (\d+)',g.command('data get entity TestPlayer SelectedItem'))[1])
        g.key('mousedown','1')
        try:
            wait(lambda:int(re.search(r'Ammo: (\d+)',g.command('data get entity TestPlayer SelectedItem'))[1])<before,30)
        finally:
            g.key('mouseup','1');g.key('mouseup','3')
        time.sleep(3)
    for index,id in enumerate(['cannon_fr6','cannon_ri12']):
        row={'id':'aiarsenal:'+id,'result':'RUNNING'};REPORT['actions'].append(row);save()
        powder_cannon(row,index);save()
    row={'id':'aiarsenal:sturmtiger_vehicle','vehicleAmmo':'aiarsenal:rocket_380','drivable':True,'result':'RUNNING'}
    REPORT['actions'].append(row);save()
    sturmtiger(row);save()
    reload_log=tail_from(log,reload_log_start)
    assert 'Destroying pipeline' not in reload_log,'R rebuilt Oculus pipeline while reloading a weapon'
    assert 'Shader reload key conflict:' in reload_log,'default R conflict was not exercised'
    REPORT['weaponReloadShaderRebuilds']=0;save()
    g.command('gamemode creative TestPlayer')
    g.command('clear TestPlayer')
    g.command('tp TestPlayer 0.5 -60 0.5 0 0')
    g.view_action(log,'view_first')
    REPORT['packetRaymarchObservations']=[]
    for effect in ['blast','nuke','legacy_nuke','bm21','bomber']:
        local('clear')
        before=status(True)
        start=frames(before)
        g.command('arsenal_visual_test '+effect+' 0 -60 22')
        # This client status packet is an ordered acknowledgment after the real effect packet.
        ack=status(True)
        if effect in ['nuke','legacy_nuke']:
            g.screenshot(PACK+'-flash-'+effect)
            REPORT.setdefault('flashObservations',[]).append(dict(effect=effect,clientAck=ack))
            save()
        after=wait(lambda: (lambda line: line if frames(line)>start else None)(status(True)),120)
        assert 'lastStage=minecraft:after_level' in after,after
        volume_count=int(re.search(r'volumes=(\d+)',after)[1])
        plume_count=int(re.search(r'plumes=(\d+)',after)[1])
        assert volume_count>0 or plume_count>0,{'effect':effect,'after':after}
        screenshot_name=PACK+'-raymarch-packet-'+effect
        g.screenshot(screenshot_name)
        REPORT['packetRaymarchObservations'].append(dict(effect=effect,framesBefore=start,
            framesAfter=frames(after),volumes=volume_count,plumes=plume_count,
            screenshot=screenshot_name,ack=ack,after=after));save()
    final_shader_status=status(True)
    assert frames(final_shader_status)>0, 'shaderpack raymarch probe never submitted a non-empty volume draw'
    # With empty hands and no vehicle, R must still perform Oculus' own action.
    offset=log.stat().st_size
    g.key('keydown','r');time.sleep(.2);g.key('keyup','r')
    wait(lambda:'Creating pipeline for dimension' in tail_from(log,offset))
    status(True)
    REPORT['unarmedShaderReload']='PASS';save()
    toggles=REPORT['toggles']
    for iteration in range(2):
        g.key('key','k')
        wait(lambda: 'packBlocked=false' in local('status'))
        local('unpack')
        assert 'FX UNPACK PASS' in log.read_text(errors='replace')
        disabled_observation=volume_observation('smoke',False)
        g.screenshot(PACK+'-disabled-'+str(iteration))
        if iteration==0:
            # Force FxSystem to own a smoke quad briefly, then turn the renderer
            # back on and enable the pack mid-lifetime. It must migrate to the
            # AFTER_LEVEL volume path without allocating a vanilla fallback.
            local('clear')
            disabled=local('off')
            assert 'active=false' in disabled,disabled
            queued=local('fxsystem_smoke')
            assert 'packBlocked=false' in queued and 'backend=disabled' in queued,queued
            assert int(re.search(r'volumes=(\d+)',queued)[1])==0,queued
            safe_before=int(re.search(r'safeParticles=(\d+)',queued)[1])
            enabled=local('on')
            assert 'active=true' in enabled and 'packBlocked=false' in enabled,enabled
            start=frames(enabled)
            g.key('key','k')
            transition=wait(lambda: (lambda line: line if 'packBlocked=true' in line
                and int(re.search(r'volumes=(\d+)',line)[1])>0
                and frames(line)>0 and frames(line)!=start else None)(local('status')),120)
            assert 'backend=shaderpack-raymarch-probe' in transition,transition
            assert 'lastStage=minecraft:after_level' in transition,transition
            assert int(re.search(r'safeParticles=(\d+)',transition)[1])==safe_before,transition
            REPORT['midEffectSmokeRebind']={'result':'PASS','rendererOffQueued':queued,
                'rendererOnBeforePack':enabled,'afterPackEnable':transition,
                'screenshot':PACK+'-toggle-smoke-to-volume'};save()
            g.screenshot(PACK+'-toggle-smoke-to-volume')
        else:
            g.key('key','k')
            wait(lambda: 'packBlocked=true' in local('status'))
        local('clear')
        reenabled_before=status(True)
        start=frames(reenabled_before)
        g.command('arsenal_visual_test nuke 0 -60 22')
        reenabled_after=wait(lambda: (lambda line: line if frames(line)>0 and frames(line)!=start else None)(status(True)),120)
        assert int(re.search(r'volumes=(\d+)',reenabled_after)[1])>0,reenabled_after
        toggles.append({'round':iteration,'disabledFrames':frames(disabled_observation['after']),
            'reenabledFramesBefore':start,'reenabledFramesAfter':frames(reenabled_after),
            'reenabledVolumes':int(re.search(r'volumes=(\d+)',reenabled_after)[1])});save()
        g.screenshot(PACK+'-reenabled-'+str(iteration))

    # Runtime negative control: with a real active pack and QA flag removed,
    # the production gate must reject raw GL, use its safe fallbacks, and recover
    # when the test-only property is restored.
    local('clear')
    guard_before=local('status')
    start=frames(guard_before)
    safe_before=int(re.search(r'safeParticles=(\d+)',guard_before)[1])
    provider_before=int(re.search(r'providerFallbackParticles=(\d+)',guard_before)[1])
    disabled_probe=local('probe_off')
    assert 'active=false' in disabled_probe and 'packBlocked=true' in disabled_probe
    assert 'probe=false' in disabled_probe and 'backend=particle-fallback' in disabled_probe,disabled_probe
    fallback_fx=local('fxsystem_smoke')
    fallback_provider=local('provider_smoke')
    assert int(re.search(r'safeParticles=(\d+)',fallback_fx)[1])==safe_before+1,fallback_fx
    assert int(re.search(r'providerFallbackParticles=(\d+)',fallback_provider)[1])==provider_before+1,fallback_provider
    time.sleep(2)
    fail_closed_after=local('status')
    assert frames(fail_closed_after)==start,{'before':guard_before,'after':fail_closed_after}
    restored_probe=local('probe_on')
    assert 'active=true' in restored_probe and 'probe=true' in restored_probe,restored_probe
    start=frames(restored_probe)
    smoke_ack=local('smoke')
    assert int(re.search(r'volumes=(\d+)',smoke_ack)[1])>0,smoke_ack
    restored_draw=wait(lambda: (lambda line: line if frames(line)>start else None)(status(True)),120)
    assert 'lastStage=minecraft:after_level' in restored_draw,restored_draw
    REPORT['failClosedRuntime']={'withProbeDisabled':disabled_probe,
        'fxSystemFallback':fallback_fx,'particleProviderFallback':fallback_provider,
        'noDrawAfter2s':fail_closed_after,'probeRestored':restored_probe,
        'afterLevelDrawRestored':restored_draw};save()

    text=log.read_text(errors='replace')
    assert player.poll() is None and server.poll() is None
    bad,diagnostics=scan(text)
    REPORT['thirdPartyDiagnostics']=diagnostics
    assert not bad,'\n'.join(bad)
    effects=json.loads(g.command('execute as TestPlayer run arsenal_stress playerstatus'))['effects']
    assert not {'minecraft:blindness','minecraft:nausea'}.intersection(effects),effects
    REPORT.update(result='PASS',shaderpackRaymarchProbe='PASS',
        productionShaderpackRenderer='still fail-closed; probe is QA-only',
        postCompositeHook='Forge 1.20.1 GameRenderer AFTER_LEVEL dispatch; Iris finalizeLevelRendering runs before LevelRenderer returns',
        framebufferDepth='main RenderTarget copied at AFTER_LEVEL; required open-air visibility and wall-occlusion pixel tests',
        testedShaderpack=PACK,raymarchPackets=['blast','nuke','legacy_nuke','bm21','bomber'],
        particleProviders=['smoke','muzzle','powder','cannon','exhaust','impact'],
        guns=['ppsh41','mosin_pu','musket_1777'],
        reloadInput='real R, Oculus defaults unchanged; cannons use real RMB',
        playerEffects=effects,
        limits='Linux llvmpipe only, not Windows/NVIDIA; Photon SH_SKYLIGHT=false (32768-byte shared memory limit), other packs publisher defaults; this QA-only raw-GL probe does not certify production Iris/Oculus integration, all GPUs/pack versions, or bomb physics/damage')
    save()
    g.command('save-all flush')
    print('SHADERPACK QA-ONLY AFTER_LEVEL RAYMARCH PROBE PASS',flush=True)


if __name__=='__main__':
    try:
        run()
    except BaseException as error:
        REPORT.update(result='FAIL',error=type(error).__name__+': '+str(error),traceback=traceback.format_exc())
        if os.environ.get('GITHUB_ACTIONS')=='true':
            print('::error title=Shaderpack gameplay::'+REPORT['error'].replace('%','%25').replace('\n','%0A').replace('\r','%0D'),flush=True)
        for row in REPORT['actions']:
            if row.get('result')=='RUNNING':row.update(result='FAIL',error=REPORT['error'])
        raise
    finally:
        save()
        if REPORT['result']=='FAIL' and context.CLIENT is not None and context.CLIENT.poll() is None:
            try:g.screenshot(PACK+'-failure')
            except Exception:pass
        g.cleanup()
