package ru.aiforge.realwar.gametest;

import net.minecraft.core.particles.ParticleTypes;
import net.minecraft.gametest.framework.GameTest;
import net.minecraft.gametest.framework.GameTestHelper;
import net.minecraft.util.RandomSource;
import net.minecraftforge.gametest.GameTestHolder;
import net.minecraftforge.gametest.PrefixGameTestTemplate;
import ru.aiforge.realwar.particle.VSmokeOptions;

/** r28: the vanilla smoke -> volumetric preset mapping (VSmokeOptions.vanillaPreset) used by sendVanilla and SmokeFx. */
@GameTestHolder("aiarsenal")
@PrefixGameTestTemplate(false)
public final class SmokeTests {
    private SmokeTests() {
    }

    @GameTest(template = "arena", batch = "rw_smoke", timeoutTicks = 20)
    public static void smokeTypesMapToVolumetricPresets(GameTestHelper h) {
        RandomSource r = RandomSource.create(7);
        for (var t : new net.minecraft.core.particles.SimpleParticleType[]{ParticleTypes.SMOKE, ParticleTypes.LARGE_SMOKE,
                ParticleTypes.CAMPFIRE_COSY_SMOKE, ParticleTypes.CAMPFIRE_SIGNAL_SMOKE}) {
            VSmokeOptions o = VSmokeOptions.vanillaPreset(t, r);
            h.assertTrue(o != null, "r28: дымовой тип без пресета объёма: " + t);
            h.assertTrue(o.size() > 0.0f && o.grow() >= 1.0f, "r28: размер/рост пресета вне диапазона");
            h.assertTrue(o.life() >= 20, "r28: время жизни пуфа слишком короткое");
            h.assertTrue(o.alpha() > 0.0f && o.alpha() <= 1.0f, "r28: непрозрачность пресета вне 0..1");
        }
        h.succeed();
    }

    @GameTest(template = "arena", batch = "rw_smoke", timeoutTicks = 20)
    public static void nonSmokeTypesKeepVanilla(GameTestHelper h) {
        h.assertTrue(VSmokeOptions.vanillaPreset(ParticleTypes.FLAME, RandomSource.create(1)) == null,
                "r28: огонь не должен превращаться в дымовой пуф");
        h.assertTrue(VSmokeOptions.vanillaPreset(ParticleTypes.EXPLOSION, RandomSource.create(1)) == null,
                "r28: взрыв не должен превращаться в дымовой пуф");
        h.succeed();
    }
}
