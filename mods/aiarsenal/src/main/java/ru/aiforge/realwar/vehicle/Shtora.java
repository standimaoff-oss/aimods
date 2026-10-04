package ru.aiforge.realwar.vehicle;

import java.util.List;
import javax.annotation.Nullable;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.util.RandomSource;
import net.minecraft.world.entity.Entity;
import net.minecraft.world.phys.AABB;
import net.minecraft.world.phys.Vec3;

/**
 * r27: Shtora-1 optronic suppression complex of the T-90A, seen from the attacking missile.
 * <p>
 * The TShU-1-11 laser-warning heads detect the designator / rangefinder of a laser-guided (Hellfire), beam-riding
 * (Vikhr) or the launch of an IR-tracked SACLOS (TOW) missile. The tank raises the alarm, fires an aerosol salvo
 * towards the threat and the TShU-1-7 dazzlers swamp the SACLOS tracker. Like the real system it is not a hard kill:
 * each missile is defeated with {@link #P_DEFEAT} probability - a defeated missile flies to a point 9-16 m off the
 * tank; fire-and-forget IIR missiles (Javelin) and unguided rounds are not affected.
 */
public final class Shtora {
    public static final double RANGE = 3000.0;
    public static final float P_DEFEAT = 0.75f;
    /** gametest hook: forces the outcome (-1 = random, 0 = never, 1 = always). */
    public static int force = -1;

    private Shtora() {
    }

    /** Per-missile jamming state. */
    public static final class Jam {
        int vehicle = -1;
        boolean decided, defeated;
        Vec3 off = Vec3.ZERO;
        int nextScan;

        public boolean defeated() {
            return this.defeated;
        }
    }

    /**
     * @param want   current unit guidance direction of the missile (null = flying on)
     * @param threat position of the launcher / designator (where the aerosol salvo is aimed)
     * @return the (possibly corrupted) guidance direction
     */
    @Nullable
    public static Vec3 apply(ServerLevel sl, Entity missile, Jam j, @Nullable Vec3 want, Vec3 threat, int age) {
        if (want == null) return null;
        Vec3 p = missile.position();
        GunVehicle g = j.vehicle >= 0 && sl.getEntity(j.vehicle) instanceof GunVehicle gv && gv.isAlive() ? gv : null;
        if (g == null && age >= j.nextScan) {
            j.nextScan = age + 4;
            g = find(sl, p, want, threat);
            if (g != null) j.vehicle = g.getId();
        }
        if (g == null) return want;
        if (!g.shtoraWarn(threat)) return want;
        if (!j.decided) {
            j.decided = true;
            RandomSource r = sl.random;
            j.defeated = force >= 0 ? force == 1 : r.nextFloat() < P_DEFEAT;
            double a = r.nextDouble() * Math.PI * 2, d = 9.0 + r.nextDouble() * 7.0;
            j.off = new Vec3(Math.cos(a) * d, 2.0 + r.nextDouble() * 4.0, Math.sin(a) * d);
        }
        if (!j.defeated) return want;
        Vec3 to = g.getBoundingBox().getCenter().add(j.off).subtract(p);
        return to.lengthSqr() < 1e-6 ? want : to.normalize();
    }

    /** Shtora-equipped, live vehicle within a 9 m tube around the missile's guidance line, up to {@link #RANGE}. */
    @Nullable
    static GunVehicle find(ServerLevel sl, Vec3 p, Vec3 want, Vec3 threat) {
        Vec3 end = p.add(want.scale(RANGE));
        AABB box = new AABB(p, p.add(want.scale(600))).inflate(10);
        List<GunVehicle> l = sl.getEntitiesOfClass(GunVehicle.class, box, v -> GunVehicle.hasShtora(v.kind) && !v.dmg.dead());
        GunVehicle best = null;
        double bd = 1e9;
        for (GunVehicle v : l) {
            Vec3 c = v.getBoundingBox().getCenter();
            if (c.distanceTo(threat) < 15.0) continue;      // the launcher itself
            double t = c.subtract(p).dot(want);
            if (t < 0) continue;
            double off = p.add(want.scale(t)).distanceTo(c);
            if (off < 9.0 && t < bd) {
                bd = t;
                best = v;
            }
        }
        return best;
    }
}
