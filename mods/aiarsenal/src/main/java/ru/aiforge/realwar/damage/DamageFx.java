package ru.aiforge.realwar.damage;

import net.minecraft.core.particles.ParticleOptions;
import net.minecraft.core.particles.ParticleTypes;
import net.minecraft.util.RandomSource;
import net.minecraft.world.level.Level;
import net.minecraft.world.phys.Vec3;
import ru.aiforge.realwar.craft.CraftEntity;
import ru.aiforge.realwar.vehicle.VehicleEntity;

import static ru.aiforge.realwar.damage.DamageState.*;

/** r18: client-side damage effects (engine smoke, fire, burning wrecks) - plain level particles, common code. */
public final class DamageFx {
    private DamageFx() {
    }

    public static void vehicle(VehicleEntity v) {
        DamageState s = v.dmg;
        if (!s.any()) return;
        Level l = v.level();
        RandomSource r = l.random;
        int t = v.tickCount;
        VehicleDamage.Geo g = VehicleDamage.geo(v);
        double ez = g.engineFront() ? g.cz() + g.hz() * 0.6 : g.cz() - g.hz() * 0.7;
        Vec3 eng = v.localToWorld(g.cx(), g.cy() + g.hy() + 0.1, ez);
        if (s.hurtBit(ENGINE) && t % 3 == 0) puff(l, ParticleTypes.SMOKE, eng, r, 0.4, 0.05);
        // r27: volumetric smoke (aiarsenal:vsmoke, drawn up to 512 blocks) instead of campfire/large-smoke sprites
        if (s.broken(ENGINE) && !s.burning() && t % 5 == 0) vsmoke(l, eng, r, 0.30f, 0.55f, 4.0f, 110, 0.6f, 0.0f, 0.06);
        if (s.burning()) {
            for (int i = 0; i < 2; i++) puff(l, ParticleTypes.FLAME, eng, r, 0.6, 0.03);
            if (t % 4 == 0) vsmoke(l, eng.add(0, 0.4, 0), r, 0.10f, 0.7f, 5.5f, 170, 0.85f, 0.7f, 0.10);
            if (r.nextInt(6) == 0) puff(l, ParticleTypes.LAVA, eng, r, 0.5, 0);
        }
        if (s.dead()) {
            Vec3 top = g.yp() != null ? v.localToWorld(g.yp()[0], g.yp()[1] + 0.3, g.yp()[2]) : v.localToWorld(0, g.cy() + g.hy(), g.cz());
            if (t % 5 == 0) vsmoke(l, top, r, s.burning() ? 0.09f : 0.22f, 0.8f, 5.0f, 200, 0.75f, s.burning() ? 0.4f : 0.0f, 0.07);
            if (s.broken(TURRET_GONE) && s.burning()) for (int i = 0; i < 3; i++) puff(l, ParticleTypes.FLAME, top, r, 0.6, 0.06);
        }
        if (s.repairMod >= 0 && !s.burning() && t % 8 == 0 && Math.abs(v.speedMs) < 0.3) {
            Vec3 p = v.localToWorld((r.nextDouble() - 0.5) * g.hx() * 2, g.cy() + g.hy(), g.cz() + (r.nextDouble() - 0.5) * g.hz() * 2);
            l.addParticle(ParticleTypes.ELECTRIC_SPARK, p.x, p.y, p.z, 0, 0.05, 0);
        }
    }

    public static void craft(CraftEntity c) {
        DamageState s = c.dmg;
        if (!s.any()) return;
        Level l = c.level();
        RandomSource r = l.random;
        int t = c.tickCount;
        Vec3 eng = c.localToWorld(CraftDamage.enginePoint(c));
        boolean big = c.kind.water != null && c.kind.water.length() > 60;
        double sp = big ? 2.5 : 0.4;
        if (s.hurtBit(ENGINE) && t % 2 == 0) puff(l, ParticleTypes.SMOKE, eng, r, sp, 0.04);
        if (s.broken(ENGINE) && t % 4 == 0) vsmoke(l, eng, r, 0.28f, big ? 2.0f : 0.5f, 4.0f, big ? 220 : 100, 0.6f, 0.0f, 0.05);
        if (s.burning()) {
            Vec3 fp = c.localToWorld(CraftDamage.firePoint(c));
            for (int i = 0; i < (big ? 6 : 2); i++) puff(l, ParticleTypes.FLAME, fp, r, big ? 3.0 : 0.5, 0.04);
            if (t % 3 == 0) vsmoke(l, fp, r, 0.09f, big ? 2.5f : 0.6f, big ? 5.0f : 4.5f, big ? 300 : 150, 0.85f, 0.7f, 0.10);
        }
        for (int i = 0; i < N_GUNS; i++) {
            if (s.broken(GUN0 + i) && t % 4 == 0) {
                Vec3 p = CraftDamage.gunPoint(c, i);
                if (p != null) puff(l, ParticleTypes.LARGE_SMOKE, c.localToWorld(p), r, 0.8, 0.05);
            }
        }
        if (s.broken(WING_L) && t % 2 == 0) puff(l, ParticleTypes.LARGE_SMOKE, c.localToWorld(CraftDamage.wingRoot(c, true)), r, 0.2, 0.0);
        if (s.broken(WING_R) && t % 2 == 0) puff(l, ParticleTypes.LARGE_SMOKE, c.localToWorld(CraftDamage.wingRoot(c, false)), r, 0.2, 0.0);
        if ((s.broken(ROTOR) || s.broken(TAIL_ROTOR)) && t % 2 == 0) puff(l, ParticleTypes.LARGE_SMOKE, eng, r, 0.4, 0.05);
    }

    /** r27: one volumetric smoke puff (client side; the particle type has overrideLimiter so distance is no limit). */
    static void vsmoke(Level l, Vec3 c, RandomSource r, float shade, float size, float grow, int life, float alpha, float heat, double up) {
        float sh = shade * (0.85f + 0.3f * r.nextFloat());
        l.addParticle(new ru.aiforge.realwar.particle.VSmokeOptions(sh * 1.04f, sh, sh * 0.94f, size * (0.8f + 0.4f * r.nextFloat()), grow,
                        life + r.nextInt(Math.max(1, life / 3)), alpha, heat, 0.0025f),
                c.x + (r.nextDouble() - 0.5) * size, c.y, c.z + (r.nextDouble() - 0.5) * size,
                (r.nextDouble() - 0.5) * 0.03, up, (r.nextDouble() - 0.5) * 0.03);
    }

    static void puff(Level l, ParticleOptions p, Vec3 c, RandomSource r, double spread, double up) {
        ru.aiforge.realwar.particle.SmokeFx.add(l, p, c.x + (r.nextDouble() - 0.5) * spread, c.y + (r.nextDouble() - 0.5) * spread * 0.5, c.z + (r.nextDouble() - 0.5) * spread,
                (r.nextDouble() - 0.5) * 0.02, up, (r.nextDouble() - 0.5) * 0.02);
    }
}
