package ru.aiforge.realwar.grenade;

import net.minecraft.server.level.ServerLevel;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.util.Mth;
import net.minecraft.world.effect.MobEffectInstance;
import net.minecraft.world.effect.MobEffects;
import net.minecraft.world.level.ClipContext;
import net.minecraft.world.phys.Vec3;
import ru.aiforge.realwar.network.GrenadeFlashPacket;
import ru.aiforge.realwar.network.ModNetwork;

/**
 * r27: flash-bang effect. Players within 28 m get a white flash scaled by distance, line of sight and whether they
 * look towards the burst; close and unshielded players are blinded (vanilla blindness) and ring with tinnitus.
 */
public final class GrenadeFlash {
    public static final double RANGE = 28.0;

    private GrenadeFlash() {
    }

    public static void flash(ServerLevel sl, Vec3 at) {
        for (ServerPlayer sp : sl.players()) {
            Vec3 eye = sp.getEyePosition();
            double d = eye.distanceTo(at);
            if (d > RANGE) continue;
            boolean los = sl.clip(new ClipContext(at, eye, ClipContext.Block.COLLIDER, ClipContext.Fluid.NONE, sp)).getType()
                    == net.minecraft.world.phys.HitResult.Type.MISS;
            double facing = sp.getViewVector(1.0f).dot(at.subtract(eye).normalize());
            float peak = (float) Mth.clamp(1.0 - d / RANGE, 0.0, 1.0);
            peak *= los ? 1.0f : 0.25f;
            peak *= facing > 0.0 ? 1.0f : 0.5f;
            if (peak < 0.03f) continue;
            if (los && d < 14.0) {
                int ticks = (int) (peak * 140.0f);
                sp.addEffect(new MobEffectInstance(MobEffects.BLINDNESS, ticks, 0, false, false));
            }
            int ring = peak > 0.3f ? (int) (peak * 160.0f) : 0;   // tinnitus, ticks
            ModNetwork.sendToPlayer(sp, new GrenadeFlashPacket(peak, ring));
        }
    }
}
