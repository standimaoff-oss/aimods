import copy
import json
from pathlib import Path
import tempfile
import unittest
from verify_reload_shader_delivery import check_run,check_shader,verify,RUNTIME,PACKS

SOURCE='a'*40

class MatrixDeliveryTest(unittest.TestCase):
    def metadata(self,kind='shader'):
        required=['Static and protocol tests','Build release JAR',RUNTIME.get(kind,'Minecraft GameTests'),
            'Archive evidence and binary','Preserve incremental evidence even on failure']
        if kind in ('catalogue','context'):required.append('Minecraft GameTests')
        names=['verify ('+p+')' for p in sorted(PACKS)] if kind=='shader' else ['verify']
        return dict(headSha=SOURCE,status='completed',conclusion='success',jobs=[dict(name=name,conclusion='success',
            steps=[dict(name=n,conclusion='success') for n in required]) for name in names])

    def test_complete_matrix(self):
        check_run(self.metadata(),SOURCE,'shader')
        check_run(self.metadata('catalogue'),SOURCE,'catalogue')

    def test_wrong_source_pending_and_failure_rejected(self):
        for field,value in [('headSha','b'*40),('status','in_progress'),('conclusion','failure')]:
            data=self.metadata();data[field]=value
            with self.assertRaises(AssertionError):check_run(data,SOURCE,'shader')

    def test_missing_pack_or_failed_job_rejected(self):
        data=self.metadata();data['jobs'].pop()
        with self.assertRaises(AssertionError):check_run(data,SOURCE,'shader')
        data=self.metadata();data['jobs'][1]['conclusion']='failure'
        with self.assertRaises(AssertionError):check_run(data,SOURCE,'shader')

    def test_gameplay_and_gametest_cannot_be_skipped(self):
        data=self.metadata();data['jobs'][0]['steps'][2]['conclusion']='skipped'
        with self.assertRaises(AssertionError):check_run(data,SOURCE,'shader')
        data=self.metadata('catalogue');data['jobs'][0]['steps'].pop()
        with self.assertRaises(AssertionError):check_run(data,SOURCE,'catalogue')

    def report(self):
        return dict(result='PASS',pack='photon',guns=['ppsh41','mosin_pu','musket_1777'],
          weaponReloadShaderRebuilds=0,unarmedShaderReload='PASS',playerEffects=[],
          actions=[dict(id='aiarsenal:'+id,result='PASS',cycles=[{},{}],aimChecks=['target=aiarsenal:'+id]*4)
            for id in ['cannon_fr6','cannon_ri12']]+[dict(id='aiarsenal:sturmtiger_vehicle',result='PASS',
              functional='MAIN_GUN_FIRE_RELOAD_REPEAT_PASS',mainGunShot='PASS',mainGunReload='PASS',mainGunRepeatShot='PASS',drive='PASS')],
          fallbackObservations=[dict(effect=e,before='safeParticles=0 safeCloudFrames=0',after='safeParticles=5 safeCloudFrames=5')
            for e in ['blast','nuke','legacy_nuke']],
          toggles=[dict(round=i,framesBefore=40,framesAfter=40) for i in range(2)])

    def test_shader_actions_and_safe_draws(self):
        check_shader(self.report(),'photon')
        for mutation in [lambda r:r.update(weaponReloadShaderRebuilds=1),
                         lambda r:r.update(unarmedShaderReload='FAIL'),
                         lambda r:r['actions'][0].update(cycles=[{}]),
                         lambda r:r['actions'][2].update(mainGunReload='NOT_VERIFIED'),
                         lambda r:r['fallbackObservations'][0].update(after='safeParticles=0 safeCloudFrames=0'),
                         lambda r:r.update(playerEffects=['minecraft:blindness']),
                         lambda r:r['toggles'][0].update(framesAfter=41)]:
            report=self.report();mutation(report)
            with self.assertRaises(AssertionError):check_shader(report,'photon')

    def test_unreviewed_candidate_stays_blocked(self):
        with tempfile.TemporaryDirectory() as folder:
            p=Path(folder)/'candidate.json';p.write_text(json.dumps(dict(reviewed=False)))
            with self.assertRaisesRegex(AssertionError,'review'):verify(p,folder,folder)
