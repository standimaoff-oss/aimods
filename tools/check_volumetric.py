#!/usr/bin/env python3
"""Static port checks; NOT a replacement for real client rendering tests."""
from pathlib import Path
import re
import unittest
import zipfile

ROOT = Path(__file__).resolve().parents[1]
JAVA = ROOT / 'mods/aiarsenal/src/main/java/ru/aiforge'
PORT = JAVA / 'arsenal/volumetric'
SHADERS = ROOT / 'mods/aiarsenal/src/main/resources/assets/aiarsenal/shaders/volpyro'

class PortTests(unittest.TestCase):
    def test_shaders_are_extracted_from_supplied_jar(self):
        with zipfile.ZipFile(ROOT / 'volpyro-1.5.6-nuclear (1).jar') as jar:
            files = [name for name in jar.namelist() if '/shaders/core/' in name and name.endswith(('.fsh', '.vsh'))]
            self.assertEqual(len(files), 4)
            for name in files:
                self.assertEqual((SHADERS / Path(name).name).read_bytes(), jar.read(name))

    def test_no_donor_gameplay_or_unmapped_symbols(self):
        for path in PORT.rglob('*.java'):
            text = path.read_text()
            self.assertNotRegex(text, r'\b[mf]_\d+_\b|com\.example\.volpyro|@Mod\("volpyro"\)')
            self.assertNotIn('VolPyroCommonConfig', text)
        self.assertNotIn('client.', (PORT / 'VolumetricParticles.java').read_text())
        self.assertNotIn('net.minecraft.client', (PORT / 'config/VolPyroClientConfig.java').read_text())

    def test_mod_smoke_emitters_are_routed(self):
        for path in JAVA.rglob('*.java'):
            if 'volumetric' in path.parts:
                continue
            self.assertNotRegex(path.read_text(), r'ParticleTypes\.(SMOKE|LARGE_SMOKE|CAMPFIRE_COSY_SMOKE|CAMPFIRE_SIGNAL_SMOKE)\b')
            self.assertNotIn('net.minecraft.core.particles.ru.', path.read_text())

    def test_qa_bridge_is_opt_in_and_clientbound(self):
        packet = (PORT / 'VisualQaPacket.java').read_text()
        self.assertIn('Boolean.getBoolean("aiarsenal.visualQa") && EFFECTS.contains(effect)', packet)
        self.assertIn('readUtf(16)', packet)
        self.assertIn('ctx.enqueueWork(', packet)
        network = (JAVA / 'arsenal/network/ArsenalNetwork.java').read_text()
        self.assertIn('VisualQaPacket.class, id++, NetworkDirection.PLAY_TO_CLIENT', network)
        commands = (PORT / 'VisualTestCommand.java').read_text()
        self.assertIn('requires(s -> s.hasPermission(2))', commands)

    def test_shaderpack_probe_is_double_opt_in_and_has_real_counters(self):
        renderer=(PORT/'client/render/VolumeGlRenderer.java').read_text()
        self.assertIn('Boolean.getBoolean("aiarsenal.visualQa")',renderer)
        self.assertIn('Boolean.getBoolean("aiarsenal.shaderpackVolumeProbe")',renderer)
        self.assertIn('return !blocked || shaderpackVolumeProbeEnabled();',renderer)
        self.assertIn('RenderLevelStageEvent.Stage.AFTER_LEVEL : RenderLevelStageEvent.Stage.AFTER_PARTICLES',renderer)
        effects=(PORT/'client/VolumetricEffects.java').read_text()
        self.assertIn('providerFallbackParticles=%d',effects)
        self.assertIn('VolumeGlRenderer.lastDrawStage()',effects)
        setup=(PORT/'client/VolumetricSetup.java').read_text()
        self.assertIn('shaderFallbackParticles++',setup)
        self.assertIn('VolumetricEffects.profile(x,y,z,vx,vy,vz,profile)',setup)
        driver=(ROOT/'tools/verify_shaderpack_game.py').read_text()
        for provider in ['provider_smoke','provider_muzzle','provider_powder','provider_cannon',
                         'provider_exhaust','provider_impact','fxsystem_smoke']:
            self.assertIn(provider,driver)
        self.assertIn('packetRaymarchObservations',driver)
        self.assertIn('productionShaderpackRenderer',driver)
        self.assertIn('failClosedRuntime',driver)
        self.assertIn('probe_off',driver)
        self.assertIn('probe_on',driver)

    def test_mod_smoke_routes_before_shaderpack_particle_fallback(self):
        system=(JAVA/'realwar/client/particle/FxSystem.java').read_text()
        add=system[system.index('public static void add(FxParticle p)'):]
        self.assertLess(add.index('VolumetricEffects.smoke('),add.index('if (ShaderPackCompatibility.blocked())'))
        tick=system[system.index('public static void tick('):system.index('public static void render(')]
        self.assertIn('VolumetricEffects.smoke(',tick)
        self.assertIn('providerFallbackParticles', (PORT/'client/VolumetricEffects.java').read_text())
        driver=(ROOT/'tools/verify_shaderpack_game.py').read_text()
        self.assertIn('fxsystem_smoke',driver)
        self.assertIn('safe_after==safe_before',driver)

    def test_renderer_has_failure_and_resource_cleanup(self):
        text = (PORT / 'client/render/VolumeGlRenderer.java').read_text()
        self.assertIn('try (GlStateSnapshot state', text)
        self.assertIn('public static void reset()', text)
        self.assertIn('GL20.glDeleteProgram', text)
        self.assertIn('failed = true', text)
        self.assertIn('Math.min(16, n2)', text)
        self.assertIn('if (list.isEmpty() && warmed) return;', text)
        self.assertIn('warmed = false;', text)
        manager = (PORT / 'client/sim/VolumetricFxManager.java').read_text()
        self.assertIn('MAX_RENDER_VOLUMES', manager)
        self.assertIn('rocketTracks.size() >= 64', manager)

if __name__ == '__main__':
    unittest.main(verbosity=2)
