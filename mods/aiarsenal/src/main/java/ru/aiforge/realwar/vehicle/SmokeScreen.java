package ru.aiforge.realwar.vehicle;

import java.util.ArrayList;
import java.util.Iterator;
import java.util.List;
import net.minecraft.core.particles.ParticleTypes;
import net.minecraft.resources.ResourceKey;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.world.level.Level;
import net.minecraft.world.phys.Vec3;
import net.minecraftforge.event.TickEvent;
import net.minecraftforge.eventbus.api.SubscribeEvent;
import net.minecraftforge.fml.common.Mod;

/**
 * r20: smoke screens of the tank grenade dischargers (902G Shtora / 902V Tucha, M250 / M257, NbK 39) and the T-34's
 * MDSh smoke drums. Server side clouds that keep emitting long-lived campfire smoke for ~25 s, so they really block
 * the view of everybody (sights included).
 */
@Mod.EventBusSubscriber(modid = "aiarsenal")
public final class SmokeScreen {
    private record Cloud(ResourceKey<Level> dim, Vec3 pos, double r, int[] left, float[] rgb) {}

    private static final List<Cloud> CLOUDS = new ArrayList<>();
    public static final int LIFE = 500;

    private SmokeScreen() {
    }

    public static synchronized void add(ServerLevel sl, Vec3 pos, double r, int ticks) {
        add(sl, pos, r, ticks, new float[]{1.0f, 1.0f, 1.0f});
    }

    /** r27: coloured screen (smoke grenades); rgb is the albedo of the cloud, the lit shading is applied per puff. */
    public static synchronized void add(ServerLevel sl, Vec3 pos, double r, int ticks, float[] rgb) {
        if (CLOUDS.size() > 256) CLOUDS.remove(0);
        CLOUDS.add(new Cloud(sl.dimension(), pos, r, new int[]{ticks}, rgb));
        sl.sendParticles(ParticleTypes.EXPLOSION, pos.x, pos.y, pos.z, 1, 0, 0, 0, 0);
        // r27: volumetric burst - a ring of puffs thrown outwards by the bursting grenade, visible up to 512 blocks
        for (int i = 0; i < 10; i++) {
            double a = i * (Math.PI * 2 / 10) + sl.random.nextDouble() * 0.4;
            double sp = 0.12 + sl.random.nextDouble() * 0.1;
            float sh = 0.82f + sl.random.nextFloat() * 0.12f;
            ru.aiforge.realwar.particle.VSmokeOptions.send(sl, new ru.aiforge.realwar.particle.VSmokeOptions(rgb[0] * sh, rgb[1] * sh, rgb[2] * sh, (float) (r * 0.22 + 0.8), 2.2f, 220 + sl.random.nextInt(80), 0.85f, 0.0f, 0.0015f),
                    pos.x, pos.y - 0.4, pos.z, 0, Math.cos(a) * sp, 0.02, Math.sin(a) * sp, 1.0);
        }
    }

    public static synchronized int active() {
        return CLOUDS.size();
    }

    @SubscribeEvent
    public static void onLevelTick(TickEvent.LevelTickEvent e) {
        if (e.phase != TickEvent.Phase.END || !(e.level instanceof ServerLevel sl)) return;
        synchronized (SmokeScreen.class) {
            if (CLOUDS.isEmpty()) return;
            boolean emit = sl.getGameTime() % 10 == 0;
            Iterator<Cloud> it = CLOUDS.iterator();
            while (it.hasNext()) {
                Cloud c = it.next();
                if (c.dim != sl.dimension()) continue;
                if (--c.left[0] <= 0) {
                    it.remove();
                    continue;
                }
                if (!emit) continue;
                // r27: few big volumetric puffs (each ~4 m) instead of a swarm of campfire sprites; long-distance
                double grow = Math.min(1.0, (LIFE - c.left[0]) / 30.0 + 0.45);
                double r = c.r * grow;
                int n = c.left[0] > 100 ? 1 + sl.random.nextInt(2) : (sl.random.nextInt(3) == 0 ? 1 : 0);
                for (int i = 0; i < n; i++) {
                    double a = sl.random.nextDouble() * Math.PI * 2, d = Math.sqrt(sl.random.nextDouble()) * r * 0.8;
                    double x = c.pos.x + Math.cos(a) * d, z = c.pos.z + Math.sin(a) * d;
                    double y = c.pos.y - 0.6 + sl.random.nextDouble() * r * 0.35;
                    double wx = (sl.random.nextDouble() - 0.5) * 0.02, wz = (sl.random.nextDouble() - 0.5) * 0.02;
                    float sh = 0.80f + sl.random.nextFloat() * 0.14f;
                    ru.aiforge.realwar.particle.VSmokeOptions.send(sl, new ru.aiforge.realwar.particle.VSmokeOptions(c.rgb[0] * sh, c.rgb[1] * sh, c.rgb[2] * sh, (float) Math.max(1.6, r * 0.32), 2.2f, 240 + sl.random.nextInt(60), 0.85f, 0.0f, 0.0015f),
                            x, y, z, 0, wx, 0.004, wz, 1.0);
                }
            }
        }
    }
}
