package ru.aiforge.realwar.artillery;

import net.minecraft.util.RandomSource;
import net.minecraft.world.phys.Vec3;

/**
 * r28: fire-mission rules of the artillery fire-control point (ПУ арты), pure functions so they can be tested
 * without a level.
 *
 * <ul>
 *   <li>COORD - по координатам: every linked battery fires its rounds at the one given point.</li>
 *   <li>SALVO - залп: one round per battery, fired in the same tick once every battery is aimed and loaded.</li>
 *   <li>MAP - удар по карте: rounds land at random points inside a square of the chosen size around the centre.</li>
 *   <li>ADJUST - корректировка: one round per battery; the observer then shifts the point and fires again.</li>
 * </ul>
 */
public final class FireMission {
    public static final int MAX_BATTERIES = 8;
    public static final double LINK_RADIUS = 300.0;
    public static final int MAX_ROUNDS = 6;
    public static final int[] SQUARES = {100, 200, 400};
    /** Ticks without any round fired before the mission is cancelled by the fire-control point. */
    public static final int STALL_TICKS = 1200;

    private FireMission() {
    }

    public enum Mode {
        COORD, SALVO, MAP, ADJUST;

        public Mode next() {
            return values()[(this.ordinal() + 1) % values().length];
        }

        public static Mode byOrdinal(int i) {
            return values()[Math.floorMod(i, values().length)];
        }
    }

    /** Rounds each battery fires in one mission for the chosen mode. */
    public static int roundsFor(Mode m, int rounds) {
        return m == Mode.SALVO || m == Mode.ADJUST ? 1 : Math.max(1, Math.min(MAX_ROUNDS, rounds));
    }

    /** Aim point of the next round of one battery. */
    public static Vec3 shotPoint(Mode m, double cx, double cz, int square, RandomSource r) {
        if (m != Mode.MAP) {
            return new Vec3(cx, 0.0, cz);
        }
        double half = Math.max(1, square) * 0.5;
        return new Vec3(cx + (r.nextDouble() * 2.0 - 1.0) * half, 0.0, cz + (r.nextDouble() * 2.0 - 1.0) * half);
    }

    /** Horizontal distance in blocks. */
    public static double distXZ(double ax, double az, double bx, double bz) {
        double dx = ax - bx;
        double dz = az - bz;
        return Math.sqrt(dx * dx + dz * dz);
    }

    /** Square size from the cycling index (100 / 200 / 400 m). */
    public static int square(int i) {
        return SQUARES[Math.floorMod(i, SQUARES.length)];
    }

    public static int nextSquareIndex(int i) {
        return Math.floorMod(i + 1, SQUARES.length);
    }
}
