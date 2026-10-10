package ru.aiforge.realwar.particle;

import net.minecraft.core.particles.ParticleOptions;
import net.minecraft.world.level.Level;
import ru.aiforge.realwar.client.particle.VolumeFx;

/**
 * r28: common-side entry point for smoke particles emitted by entities and blocks ({@code level.addParticle}).
 * Client only: the volumetric puff is built in {@link VolumeFx}, which is referenced only inside the client branch,
 * so a dedicated server never loads client classes through this helper.
 */
public final class SmokeFx {
    private SmokeFx() {
    }

    public static void add(Level lv, ParticleOptions type, double x, double y, double z, double vx, double vy, double vz) {
        if (lv.isClientSide) {
            VolumeFx.addVanilla(lv, type, x, y, z, vx, vy, vz);
        }
    }
}
