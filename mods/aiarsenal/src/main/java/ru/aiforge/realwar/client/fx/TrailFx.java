package ru.aiforge.realwar.client.fx;

import java.util.ArrayList;
import java.util.Iterator;
import java.util.List;
import java.util.Random;
import net.minecraft.client.Minecraft;
import net.minecraft.client.multiplayer.ClientLevel;
import net.minecraft.core.BlockPos;
import net.minecraft.core.Position;
import net.minecraft.util.Mth;
import net.minecraft.world.entity.Entity;
import net.minecraft.world.level.ClipContext;
import net.minecraft.world.phys.BlockHitResult;
import net.minecraft.world.phys.HitResult;
import net.minecraft.world.phys.Vec3;
import ru.aiforge.realwar.RWConfig;
import ru.aiforge.realwar.client.particle.FxParticle;
import ru.aiforge.realwar.client.particle.FxSystem;
import ru.aiforge.realwar.client.particle.Sprites;
import ru.aiforge.realwar.handheld.AtMissileEntity;
import ru.aiforge.realwar.handheld.HandheldKind;
import ru.aiforge.realwar.missile.MissileEntity;
import ru.aiforge.realwar.missile.MissileType;
import ru.aiforge.realwar.network.TracerPacket;
import ru.aiforge.realwar.ordnance.Ballistics;
import ru.aiforge.realwar.ordnance.RocketEntity;

/**
 * Physically simulated smoke, propellant exhaust, muzzle blast, and tracer effects.
 * Features:
 *  - Thermal buoyancy with exponential cooling (hot nozzle gas rises rapidly, then drifts as it cools)
 *  - Non-linear aerodynamic jet drag (supersonic nozzle exit -> turbulent entrainment -> ambient drift)
 *  - Coherent altitude-sheared atmospheric wind + 3D spatial-temporal curl turbulence (vortex eddies)
 *  - Ground / terrain collision and radial surface cushioning
 *  - Multi-stage volumetric shading (incandescent nozzle scattering -> dense cordite grey -> lit cloud plume)
 */
public final class TrailFx {
    private static final Random R = new Random();
    private static final int PARTICLE_CAP = 9000;
    private static final List<Tracer> TRACERS = new ArrayList<Tracer>();

    private TrailFx() {
    }

    public static float q() {
        return ((Double)RWConfig.CLIENT.trailQuality.get()).floatValue();
    }

    public static boolean crowded() {
        return FxSystem.count() > PARTICLE_CAP;
    }

    // -------------------------------------------------------------------------
    // Atmospheric Wind & 3D Curl Turbulence Field
    // -------------------------------------------------------------------------
    private static double windX(ClientLevel level, double y) {
        long t = level != null ? level.getGameTime() : 0L;
        double gust = 1.0 + (level != null && level.isRaining() ? 0.65 : 0.0) + (level != null && level.isThundering() ? 0.55 : 0.0);
        double shear = 1.0 + 0.009 * Math.max(0.0, y - 62.0);
        double slow = Math.sin((double)t * 0.0017) * 0.0042 + Math.cos((double)t * 0.0053) * 0.0016;
        return slow * shear * gust;
    }

    private static double windZ(ClientLevel level, double y) {
        long t = level != null ? level.getGameTime() : 0L;
        double gust = 1.0 + (level != null && level.isRaining() ? 0.65 : 0.0) + (level != null && level.isThundering() ? 0.55 : 0.0);
        double shear = 1.0 + 0.009 * Math.max(0.0, y - 62.0);
        double slow = Math.cos((double)t * 0.0013 + 0.8) * 0.0038 + Math.sin((double)t * 0.0047) * 0.0015;
        return slow * shear * gust;
    }

    /**
     * Core physical smoke particle generator.
     *
     * @param level     Client world
     * @param pos       Initial spawn position
     * @param initVel   Initial jet/ejection velocity (blocks/tick)
     * @param s         Scale factor (1.0 = standard rocket / 120mm cannon)
     * @param thin      True for thin contrail / gunsmoke wisp; false for dense propellant plume
     * @param initTemp  Initial thermal temperature in [0..1] (controls buoyancy and warm scattering)
     * @param baseShade Target cooled smoke reflectance in [0.35..0.95]
     * @param dust      True if soil/dust (warmer tan/brown tint, lower buoyancy)
     * @param groundY   Optional known ground Y below the plume (Double.NaN if none)
     */
    public static FxParticle physicalSmoke(
            ClientLevel level,
            Vec3 pos,
            Vec3 initVel,
            double s,
            boolean thin,
            float initTemp,
            float baseShade,
            boolean dust,
            double groundY
    ) {
        if (level == null) {
            return null;
        }
        if (TrailFx.crowded() && R.nextBoolean()) {
            return null;
        }
        int baseLife = thin ? (38 + R.nextInt(28)) : (85 + R.nextInt(70));
        int life = Math.max(18, (int)((double)baseLife * (0.82 + 0.28 * Math.min(s, 2.5))));
        float size0 = (float)((thin ? 0.28 : 0.72) * s * (0.85 + 0.3 * R.nextDouble()));
        float size1 = (float)((thin ? 1.55 : 3.85 + R.nextDouble() * 1.45) * s);
        float a0 = thin ? 0.28f : (dust ? 0.52f : 0.66f);

        FxParticle p = new FxParticle(level, pos.x, pos.y, pos.z, Sprites.smoke(R.nextInt(4)), life, false, size0);
        p.velocity(initVel.x, initVel.y, initVel.z);
        float baseSpin = (R.nextFloat() - 0.5f) * (thin ? 0.07f : 0.055f);
        p.spin = baseSpin;
        float phase = R.nextFloat() * 6.2831855f;
        float turbAmp = (float)((thin ? 0.0018 : 0.0026) * (0.8 + 0.25 * Math.min(s, 2.2)));
        float coolRate = thin ? 0.14f : 0.085f;
        float darkCore = Math.max(0.24f, baseShade - (thin ? 0.12f : 0.32f));

        p.motion = (pp, age) -> {
            float f = (float)age / (float)life;
            float temp = initTemp * (float)Math.exp((double)(-age) * (double)coolRate);

            // 1. Thermal buoyancy (hot exhaust rises strongly, dust settles slightly as it cools)
            double buoy = dust
                    ? (0.0032 * (double)temp - 0.0006 * (double)f)
                    : (0.0092 * (double)temp + 0.0016 * (double)(1.0f - 0.45f * f));

            // 2. 3D curl-like vortex turbulence + altitude wind shear
            double px = pp.x();
            double py = pp.y();
            double pz = pp.z();
            double t = (double)age * 0.11 + (double)phase;
            double tx = Math.sin(py * 0.37 + t) * Math.cos(pz * 0.31 - t * 0.7) * (double)turbAmp;
            double ty = Math.cos(px * 0.33 - t * 0.8) * Math.sin(pz * 0.29 + t * 0.6) * (double)turbAmp * 0.75;
            double tz = Math.sin(px * 0.35 + t * 0.7) * Math.cos(py * 0.37 - t) * (double)turbAmp;

            double wx = TrailFx.windX(level, py) * (double)(0.35f + 0.65f * f);
            double wz = TrailFx.windZ(level, py) * (double)(0.35f + 0.65f * f);

            double vx = pp.getDeltaX() + tx + wx;
            double vy = pp.getDeltaY() + buoy + ty;
            double vz = pp.getDeltaZ() + tz + wz;

            // 3. Ground cushioning / horizontal billow when plume hits terrain
            if (!Double.isNaN(groundY)) {
                double floor = groundY + (double)(pp.size * 0.28f);
                if (py + vy < floor) {
                    if (vy < 0.0) {
                        double bounce = -vy * 0.45;
                        vy = bounce * 0.25 + 0.004;
                        double hLen = Math.hypot(vx, vz);
                        if (hLen > 1.0E-4) {
                            double boost = (hLen + bounce * 0.85) / hLen;
                            vx *= boost;
                            vz *= boost;
                        } else {
                            vx += Math.cos(phase + age) * bounce * 0.7;
                            vz += Math.sin(phase + age) * bounce * 0.7;
                        }
                    }
                    py = floor;
                }
            }

            // 4. Non-linear aerodynamic drag: rapid jet braking in early ticks, gentle drift later
            double drag = age < 6 ? 0.84 : (age < 16 ? 0.91 : 0.962);
            vx *= drag;
            vy *= drag;
            vz *= drag;

            pp.velocity(vx, vy, vz);
            pp.translate(vx, vy, vz);

            // Angular momentum decays as the eddy expands
            pp.spin = baseSpin * (1.0f - 0.65f * f);

            // 5. Turbulent entrainment radius growth: rapid initial expansion + sqrt(t) diffusion
            float inv = 1.0f - f;
            float grow = 1.0f - inv * inv * inv;
            pp.size = size0 + (size1 - size0) * (0.78f * grow + 0.22f * Mth.sqrt(f));

            // 6. Volumetric thermal & optical density shading
            if (dust) {
                float r = Mth.clamp(0.64f + 0.14f * temp + 0.06f * f, 0.0f, 1.0f);
                float g = Mth.clamp(0.56f + 0.08f * temp + 0.05f * f, 0.0f, 1.0f);
                float b = Mth.clamp(0.44f + 0.03f * temp + 0.05f * f, 0.0f, 1.0f);
                pp.color(r, g, b);
            } else {
                // Transition from dense dark cordite/soot core -> sunlit atmospheric plume,
                // with warm orange internal scattering while hot near the nozzle
                float coolBlend = Mth.clamp(f * 1.65f, 0.0f, 1.0f);
                float lum = Mth.lerp(coolBlend, darkCore, baseShade);
                float warmGlow = Math.max(0.0f, (temp - 0.42f) * 1.45f);
                float r = Mth.clamp(lum + 0.34f * warmGlow, 0.0f, 1.0f);
                float g = Mth.clamp(lum + 0.14f * warmGlow, 0.0f, 1.0f);
                float b = Mth.clamp(lum - 0.12f * warmGlow, 0.0f, 1.0f);
                pp.color(r, g, b);
            }

            float fadeIn = Math.min(1.0f, (float)(age + 1) / (thin ? 1.8f : 2.8f));
            float fadeOut = (1.0f - f) * (1.0f - 0.35f * f);
            pp.alpha(a0 * fadeIn * fadeOut);
        };
        FxSystem.add(p);
        return p;
    }

    // -------------------------------------------------------------------------
    // Rocket, Missile & Handheld ATGM / RPG Trails
    // -------------------------------------------------------------------------
    public static void rocketTick(RocketEntity e) {
        ClientLevel level = Minecraft.getInstance().level;
        if (level == null || e.tickCount < 1) {
            return;
        }
        Ballistics.Profile p = e.profile();
        double s = p == Ballistics.Profile.GRAD ? 1.05
                : (p == Ballistics.Profile.SMERCH ? 1.95
                : (p == Ballistics.Profile.M13 ? 0.95 : 2.75));
        Vec3 a = new Vec3(e.xo, e.yo, e.zo);
        Vec3 b = e.position();
        Vec3 d = b.subtract(a);
        double len = d.length();
        if (len < 0.001 || len > 120.0) {
            return;
        }
        boolean burn = e.isBurning();
        Vec3 dir = d.scale(1.0 / len);
        if (e.tickCount < 2 && burn) {
            return;
        }
        double spacing = burn
                ? 1.25 * Math.sqrt(s) / Math.min((double)TrailFx.q(), 1.6)
                : 4.5 / Math.min((double)TrailFx.q(), 1.5);
        int n = Math.max(1, (int)Math.ceil(len / spacing));
        if (TrailFx.crowded() && R.nextInt(3) != 0) {
            n = 1;
        }
        double nozzleOff = p == Ballistics.Profile.SAM_48N6 ? 3.4 : (p == Ballistics.Profile.SMERCH ? 3.6 : 1.6);
        for (int i = 0; i < n; ++i) {
            double f = ((double)i + R.nextDouble()) / (double)n;
            Vec3 pos = a.add(d.scale(f)).subtract(dir.scale(nozzleOff));
            if (burn) {
                TrailFx.smoke(level, pos, dir, s, false);
                TrailFx.flame(level, pos, dir, s);
                continue;
            }
            TrailFx.smoke(level, pos, dir, s * 0.65, true);
        }
        if (burn) {
            Vec3 tail = b.subtract(dir.scale(nozzleOff + 0.25));
            TrailFx.nozzleDiamond(level, tail, dir, s);
        }
    }

    /**
     * Client physical exhaust trail for handheld rockets & ATGMs (RPG-7, Javelin, Igla, Stinger, TOW).
     */
    public static void handheldRocketTick(AtMissileEntity e) {
        if (!(e.level() instanceof ClientLevel level)) {
            return;
        }
        HandheldKind k = e.kind();
        Vec3 v = e.getDeltaMovement();
        double sp = v.length();
        Vec3 dir = sp > 1.0E-4 ? v.scale(1.0 / sp) : Vec3.directionFromRotation(e.getXRot(), e.getYRot());
        Vec3 prev = new Vec3(e.xo, e.yo, e.zo);
        Vec3 curr = e.position();

        // Javelin soft launch: ejection gas puff at tick 1, main flight motor ignition burst at tick 4
        if (k == HandheldKind.JAVELIN && e.tickCount == 1) {
            Vec3 back = curr.subtract(dir.scale(0.5));
            for (int i = 0; i < 10; ++i) {
                Vec3 jv = dir.scale(-0.12 - R.nextDouble() * 0.18)
                        .add(R.nextGaussian() * 0.05, R.nextGaussian() * 0.04 + 0.01, R.nextGaussian() * 0.05);
                TrailFx.physicalSmoke(level, back, jv, 0.65, false, 0.45f, 0.78f, false, Double.NaN);
            }
            return;
        }
        if (k == HandheldKind.JAVELIN && e.tickCount == 4) {
            Vec3 back = curr.subtract(dir.scale(0.6));
            FxParticle ign = new FxParticle(level, back.x, back.y, back.z, Sprites.flare(), 4, true, 2.2f);
            ign.fullBright = true;
            ign.motion = (pp, age) -> {
                pp.color(1.0f, 0.82f, 0.45f);
                pp.alpha(1.0f - (float)age / 4.0f);
            };
            FxSystem.add(ign);
            for (int i = 0; i < 14; ++i) {
                Vec3 jv = dir.scale(-0.22 - R.nextDouble() * 0.25)
                        .add(R.nextGaussian() * 0.08, R.nextGaussian() * 0.06, R.nextGaussian() * 0.08);
                TrailFx.physicalSmoke(level, back, jv, 0.85, false, 0.85f, 0.82f, false, Double.NaN);
            }
        }

        boolean motor = k == HandheldKind.RPG7 ? (e.tickCount <= 10) : (k != HandheldKind.JAVELIN || e.tickCount >= 4);
        double scale = k == HandheldKind.TOW ? 0.72 : (k == HandheldKind.JAVELIN ? 0.68 : 0.58);
        int steps = Math.max(2, Math.min(6, (int)Math.ceil(curr.distanceTo(prev) / 0.65)));
        for (int i = 0; i < steps; ++i) {
            double f = ((double)i + R.nextDouble()) / (double)steps;
            Vec3 pos = prev.lerp(curr, f).subtract(dir.scale(0.55));
            if (motor) {
                TrailFx.smoke(level, pos, dir, scale, false);
                TrailFx.flame(level, pos, dir, scale * 0.85);
            } else {
                // RPG-7 sustainer burnout / coasting smoke wisp
                TrailFx.smoke(level, pos, dir, scale * 0.55, true);
            }
        }
        if (motor) {
            TrailFx.nozzleDiamond(level, curr.subtract(dir.scale(0.6)), dir, scale * 0.85);
        }
    }

    public static void missileTick(MissileEntity e) {
        ClientLevel level = Minecraft.getInstance().level;
        if (level == null || e.tickCount < 2 || e.mode() == 2) {
            return;
        }
        Vec3 a = new Vec3(e.xo, e.yo, e.zo);
        Vec3 b = e.position();
        Vec3 d = b.subtract(a);
        double len = d.length();
        if (len < 0.001 || len > 160.0) {
            return;
        }
        Vec3 dir = d.scale(1.0 / len);
        MissileType.Cls c = e.type().cls;
        boolean rv = e.mode() == 1;
        double s = rv ? 0.6 : c.trail;
        boolean burn = e.isBurning();
        if (!burn && !rv) {
            return;
        }
        double spacing = (rv ? 2.2 : 1.3 * Math.sqrt(s)) / Math.min((double)TrailFx.q(), 1.6);
        int n = Math.max(1, (int)Math.ceil(len / spacing));
        n = Math.min(n, 9);
        if (TrailFx.crowded() && R.nextInt(3) != 0) {
            n = 1;
        }
        double tailOff = rv ? 0.3 : c.length * 0.5 + 0.2;
        for (int i = 0; i < n; ++i) {
            double f = ((double)i + R.nextDouble()) / (double)n;
            Vec3 pos = a.add(d.scale(f)).subtract(dir.scale(tailOff));
            if (rv) {
                TrailFx.smooth(level, pos, dir, s);
                if (R.nextInt(2) != 0) continue;
                TrailFx.flame(level, pos, dir, s);
                continue;
            }
            TrailFx.smoke(level, pos, dir, s, false);
            TrailFx.flame(level, pos, dir, s);
        }
        if (burn && !rv) {
            Vec3 tail = b.subtract(dir.scale(tailOff + 0.4));
            TrailFx.nozzleDiamond(level, tail, dir, s);
        }
    }

    /**
     * Generic exhaust trail between two positions of any moving body (used by AI Arsenal missiles, ICBM stages and
     * drone boosters): physical smoke puffs + flame + glowing nozzle core.
     */
    public static void trail(ClientLevel level, Vec3 a, Vec3 b, double s, double tailOff, boolean core, boolean plasma) {
        if (level == null) {
            return;
        }
        Vec3 d = b.subtract(a);
        double len = d.length();
        if (len < 0.001 || len > 160.0) {
            return;
        }
        Vec3 dir = d.scale(1.0 / len);
        double spacing = (plasma ? 2.2 : 1.3 * Math.sqrt(s)) / Math.min((double)TrailFx.q(), 1.6);
        int n = Math.min(9, Math.max(1, (int)Math.ceil(len / spacing)));
        if (TrailFx.crowded() && R.nextInt(3) != 0) {
            n = 1;
        }
        for (int i = 0; i < n; ++i) {
            double f = ((double)i + R.nextDouble()) / (double)n;
            Vec3 pos = a.add(d.scale(f)).subtract(dir.scale(tailOff));
            if (plasma) {
                TrailFx.smooth(level, pos, dir, s);
                if (R.nextInt(2) == 0) {
                    TrailFx.flame(level, pos, dir, s);
                }
                continue;
            }
            TrailFx.smoke(level, pos, dir, s, false);
            TrailFx.flame(level, pos, dir, s);
        }
        if (core) {
            Vec3 tail = b.subtract(dir.scale(tailOff + 0.4));
            TrailFx.nozzleDiamond(level, tail, dir, s);
        }
    }

    private static void nozzleDiamond(ClientLevel level, Vec3 tail, Vec3 dir, double s) {
        FxParticle core = new FxParticle(level, tail.x, tail.y, tail.z, Sprites.flare(), 2, true, (float)(2.55 * s));
        core.fullBright = true;
        core.motion = (pp, age) -> {
            pp.color(1.0f, 0.85f, 0.55f);
            pp.alpha(0.96f * (1.0f - (float)age / 2.0f));
        };
        FxSystem.add(core);

        // Occasional incandescent propellant slag / spark ejected from the rocket nozzle
        if (!TrailFx.crowded() && R.nextInt(2) == 0) {
            int spLife = 6 + R.nextInt(7);
            FxParticle spark = new FxParticle(level, tail.x, tail.y, tail.z, Sprites.flare(), spLife, true, (float)(0.42 * s));
            spark.fullBright = true;
            double jv = 0.22 + R.nextDouble() * 0.25;
            spark.velocity(
                    -dir.x * jv + R.nextGaussian() * 0.06,
                    -dir.y * jv + R.nextGaussian() * 0.06,
                    -dir.z * jv + R.nextGaussian() * 0.06
            );
            spark.motion = (pp, age) -> {
                float f = (float)age / (float)spLife;
                pp.translate(pp.getDeltaX(), pp.getDeltaY() - 0.008 * age, pp.getDeltaZ());
                pp.scaleVelocity(0.88);
                pp.color(1.0f, 0.72f - 0.4f * f, 0.25f * (1.0f - f));
                pp.alpha(0.9f * (1.0f - f));
                pp.size = (float)(0.42 * s * (1.0f - 0.55f * f));
            };
            FxSystem.add(spark);
        }
    }

    /** Thin light-grey contrail of a turbofan / piston engine (cruise missiles and strike drones in cruise flight). */
    public static void engineWisp(ClientLevel level, Vec3 nozzle, Vec3 dir, double s) {
        if (level == null || R.nextFloat() > 0.65f * TrailFx.q()) {
            return;
        }
        TrailFx.smoke(level, nozzle, dir, 0.38 * s, true);
    }

    private static void smooth(ClientLevel level, Vec3 pos, Vec3 dir, double s) {
        TrailFx.smoke(level, pos, dir, s, true);
    }

    public static void padLaunch(ClientLevel level, Vec3 top, int padLevel, int tick) {
        double s = 1.0 + 0.9 * (double)padLevel;
        float qq = Math.min(TrailFx.q(), 1.6f);
        if (tick < 42) {
            int nf = (int)(3.5f * qq) + 1;
            for (int i = 0; i < nf; ++i) {
                Vec3 p = top.add((R.nextDouble() - 0.5) * 0.55 * (double)padLevel, 0.2 + R.nextDouble() * 0.5, (R.nextDouble() - 0.5) * 0.55 * (double)padLevel);
                TrailFx.flame(level, p, new Vec3(0.0, -1.0, 0.0), s * 1.15);
            }
            FxParticle core = new FxParticle(level, top.x, top.y + 0.4, top.z, Sprites.flare(), 2, true, (float)(3.4 * s));
            core.fullBright = true;
            core.motion = (pp, age) -> {
                pp.color(1.0f, 0.82f, 0.48f);
                pp.alpha(0.92f * (1.0f - (float)age / 2.0f));
            };
            FxSystem.add(core);
        }
        int ns = (int)((double)((float)(3 + padLevel * 2) * qq) * (tick < 32 ? 1.0 : 0.55));
        for (int i = 0; i < ns; ++i) {
            double a = R.nextDouble() * Math.PI * 2.0;
            double sp = (0.28 + R.nextDouble() * 0.60) * (0.8 + 0.32 * (double)padLevel);
            Vec3 v = new Vec3(Math.cos(a) * sp, 0.03 + R.nextDouble() * 0.06, Math.sin(a) * sp);
            boolean isDust = R.nextInt(3) == 0;
            TrailFx.physicalSmoke(
                    level,
                    top.add(Math.cos(a) * (double)padLevel * 0.5, 0.12, Math.sin(a) * (double)padLevel * 0.5),
                    v,
                    s * 1.08,
                    false,
                    isDust ? 0.35f : 0.88f,
                    0.86f,
                    isDust,
                    top.y
            );
        }
        if (tick < 52 && R.nextInt(2) == 0) {
            Vec3 v = new Vec3((R.nextDouble() - 0.5) * 0.06, 0.14 + R.nextDouble() * 0.11, (R.nextDouble() - 0.5) * 0.06);
            TrailFx.physicalSmoke(level, top.add(0.0, 0.5, 0.0), v, s * 1.35, false, 0.92f, 0.90f, false, top.y);
        }
    }

    static void smoke(ClientLevel level, Vec3 pos, Vec3 dir, double s, boolean thin) {
        double jetBack = (thin ? 0.04 : 0.11 + R.nextDouble() * 0.09) * Math.min(1.6, Math.sqrt(s));
        double spread = (thin ? 0.022 : 0.048) * Math.sqrt(s);
        Vec3 vel = new Vec3(
                -dir.x * jetBack + R.nextGaussian() * spread,
                -dir.y * jetBack * 0.65 + R.nextGaussian() * spread * 0.8,
                -dir.z * jetBack + R.nextGaussian() * spread
        );
        float shade = 0.78f + 0.18f * R.nextFloat();
        float initTemp = thin ? 0.35f : (0.78f + 0.22f * R.nextFloat());
        TrailFx.physicalSmoke(level, pos, vel, s, thin, initTemp, shade, false, Double.NaN);
    }

    static void flame(ClientLevel level, Vec3 pos, Vec3 dir, double s) {
        int life = 4 + R.nextInt(4);
        float size = (float)(1.6 * s * (0.8 + 0.45 * R.nextDouble()));
        FxParticle p = new FxParticle(level, pos.x, pos.y, pos.z, Sprites.glow(), life, true, size);
        p.fullBright = true;
        double back = 0.06 * Math.sqrt(s);
        p.velocity(-dir.x * back + R.nextGaussian() * 0.015, -dir.y * back + R.nextGaussian() * 0.015, -dir.z * back + R.nextGaussian() * 0.015);
        p.motion = (pp, age) -> {
            float f = (float)age / (float)life;
            pp.translate(pp.getDeltaX(), pp.getDeltaY(), pp.getDeltaZ());
            pp.scaleVelocity(0.82);
            pp.size = size * (1.05f - 0.65f * f);
            pp.color(1.0f, 0.82f - 0.48f * f, 0.42f - 0.32f * f);
            pp.alpha(0.9f * (1.0f - f));
        };
        FxSystem.add(p);
    }

    public static void launch(ClientLevel level, Vec3 muzzle, Vec3 dir, int big, double tubeLen) {
        double s = big == 0 ? 1.0 : (big == 1 ? 1.8 : 2.4);
        float qq = Math.min(TrailFx.q(), 1.6f);
        FxParticle flash = new FxParticle(level, muzzle.x, muzzle.y, muzzle.z, Sprites.flare(), 6, true, (float)(4.2 * s));
        flash.fullBright = true;
        flash.motion = (pp, age) -> {
            pp.color(1.0f, 0.85f, 0.55f);
            pp.alpha(1.0f - (float)age / 6.0f);
            pp.size = (float)(4.2 * s * (double)(1.0f - 0.4f * (float)age / 6.0f));
        };
        FxSystem.add(flash);

        Vec3 breech = muzzle.subtract(dir.scale(tubeLen));
        Vec3 back = dir.scale(-1.0);
        int nFire = (int)((float)(big == 2 ? 8 : 18) * qq);
        for (int i = 0; i < nFire; ++i) {
            Vec3 v = back.scale(0.5 + R.nextDouble() * 1.15 * s * 0.6)
                    .add((R.nextDouble() - 0.5) * 0.26, (R.nextDouble() - 0.5) * 0.26, (R.nextDouble() - 0.5) * 0.26);
            int life = 6 + R.nextInt(6);
            float size = (float)(1.35 * s * (0.6 + 0.6 * R.nextDouble()));
            FxParticle p = new FxParticle(level, breech.x, breech.y, breech.z, Sprites.glow(), life, true, size);
            p.fullBright = true;
            p.velocity(v.x, v.y, v.z);
            p.motion = (pp, age) -> {
                float f = (float)age / (float)life;
                pp.translate(pp.getDeltaX(), pp.getDeltaY(), pp.getDeltaZ());
                pp.scaleVelocity(0.82);
                pp.size = size * (0.8f + 0.55f * f);
                pp.color(1.0f, 0.76f - 0.42f * f, 0.34f - 0.26f * f);
                pp.alpha(0.85f * (1.0f - f));
            };
            FxSystem.add(p);
        }

        Vec3 g = TrailFx.groundBelow(level, breech);
        double gy = g != null ? g.y : Double.NaN;
        int nSmoke = (int)((double)(big == 2 ? 28 : 24) * 0.55 * (double)qq * (1.0 + (double)big * 0.4));
        for (int i = 0; i < nSmoke; ++i) {
            boolean fromBreech = i % 3 != 0;
            Vec3 o = fromBreech ? breech : muzzle;
            Vec3 axis = fromBreech ? back : dir;
            Vec3 v = axis.scale((0.18 + R.nextDouble() * 0.48) * s * (fromBreech ? 1.0 : 0.55))
                    .add(R.nextGaussian() * 0.09, R.nextDouble() * 0.07, R.nextGaussian() * 0.09);
            TrailFx.launchSmoke(level, o, v, s, 0.92f, gy);
        }
        if (g != null) {
            int nDust = (int)((double)(big == 2 ? 28 : 18) * 0.55 * (double)qq * (1.0 + (double)big * 0.5));
            for (int i = 0; i < nDust; ++i) {
                double a = R.nextDouble() * Math.PI * 2.0;
                double sp = (0.26 + R.nextDouble() * 0.52) * (0.8 + 0.5 * (double)big);
                Vec3 v = new Vec3(Math.cos(a) * sp, 0.03 + R.nextDouble() * 0.06, Math.sin(a) * sp)
                        .add(back.x * 0.32, 0.0, back.z * 0.32);
                TrailFx.launchSmoke(level, g.add(0.0, 0.25, 0.0), v, s * 1.12, 0.0f, g.y);
            }
        }
    }

    private static FxParticle launchSmoke(ClientLevel level, Vec3 o, Vec3 v, double s, float shadeHint) {
        return TrailFx.launchSmoke(level, o, v, s, shadeHint, Double.NaN);
    }

    private static FxParticle launchSmoke(ClientLevel level, Vec3 o, Vec3 v, double s, float shadeHint, double groundY) {
        boolean dust = shadeHint == 0.0f;
        float shade = 0.66f + 0.26f * R.nextFloat();
        return TrailFx.physicalSmoke(level, o, v, s, false, dust ? 0.35f : 0.82f, shade, dust, groundY);
    }

    private static Vec3 groundBelow(ClientLevel level, Vec3 from) {
        BlockHitResult h = level.clip(new ClipContext(from, from.add(0.0, -7.0, 0.0), ClipContext.Block.COLLIDER, ClipContext.Fluid.NONE, (Entity)Minecraft.getInstance().player));
        return h.getType() == HitResult.Type.MISS ? null : h.getLocation();
    }

    // -------------------------------------------------------------------------
    // Small Arms, Autocannons, Tank Main Guns & Artillery Muzzle Smoke
    // -------------------------------------------------------------------------
    /**
     * Physical muzzle flash + cordite gunsmoke for handheld firearms (pistols, SMGs, rifles, LMGs, snipers).
     */
    public static void smallArmsShot(ClientLevel level, Vec3 muzzle, Vec3 dir, Vec3 right, float caliberScale) {
        if (level == null) {
            return;
        }
        float s = Mth.clamp(caliberScale, 0.45f, 1.6f);
        // 1. Muzzle flash star + hot gas core
        FxParticle f = new FxParticle(level, muzzle.x + dir.x * 0.18, muzzle.y + dir.y * 0.18, muzzle.z + dir.z * 0.18,
                Sprites.flare(), 2, true, (0.55f + R.nextFloat() * 0.28f) * s);
        f.fullBright = true;
        f.motion = (pp, age) -> {
            pp.color(1.0f, 0.84f, 0.48f);
            pp.alpha(0.95f * (1.0f - (float)age / 2.0f));
        };
        FxSystem.add(f);

        if (TrailFx.crowded()) {
            return;
        }

        // 2. Forward high-velocity cordite smoke puffs that brake rapidly in air and curl upward
        int count = s > 1.05f ? 5 : 3;
        for (int i = 0; i < count; ++i) {
            double jet = (0.14 + R.nextDouble() * 0.22) * (double)s;
            Vec3 vel = dir.scale(jet).add(
                    R.nextGaussian() * 0.022 * s,
                    R.nextGaussian() * 0.018 * s + 0.008,
                    R.nextGaussian() * 0.022 * s
            );
            Vec3 spawn = muzzle.add(dir.scale(0.12 + 0.14 * i));
            TrailFx.physicalSmoke(level, spawn, vel, 0.34 * (double)s, true, 0.65f, 0.76f + R.nextFloat() * 0.14f, false, Double.NaN);
        }

        // 3. Ejection-port / breech gas wisp drifting sideways
        if (right != null) {
            Vec3 port = muzzle.subtract(dir.scale(0.42)).add(right.scale(0.12));
            Vec3 pvel = right.scale(0.05 + R.nextDouble() * 0.04).add(0.0, 0.015, 0.0);
            TrailFx.physicalSmoke(level, port, pvel, 0.22 * (double)s, true, 0.45f, 0.82f, false, Double.NaN);
        }
    }

    public static void muzzleFlash(ClientLevel level, Vec3 m, Vec3 dir) {
        FxParticle f = new FxParticle(level, m.x + dir.x * 0.3, m.y + dir.y * 0.3, m.z + dir.z * 0.3, Sprites.flare(), 2, true, 1.35f + R.nextFloat() * 0.5f);
        f.fullBright = true;
        f.motion = (pp, age) -> {
            pp.color(1.0f, 0.82f, 0.46f);
            pp.alpha(1.0f - (float)age / 2.0f);
        };
        FxSystem.add(f);

        if (!TrailFx.crowded()) {
            int n = R.nextInt(2) + 1;
            for (int i = 0; i < n; ++i) {
                Vec3 vel = dir.scale(0.14 + R.nextDouble() * 0.16)
                        .add(R.nextGaussian() * 0.025, 0.01 + R.nextDouble() * 0.02, R.nextGaussian() * 0.025);
                TrailFx.physicalSmoke(level, m.add(dir.scale(0.2)), vel, 0.48, true, 0.68f, 0.76f, false, Double.NaN);
            }
        }
    }

    /**
     * Gun discharge: blinding muzzle fireball, muzzle-brake lateral gas jets, expanding vortex ring of cordite smoke,
     * and ground shockwave dust ring (big = 120-155 mm tank/howitzer main gun).
     */
    public static void gunBlast(ClientLevel level, Vec3 m, Vec3 dir, boolean big, boolean brake) {
        float s = big ? 1.15f : 0.65f;
        // 1. Multi-stage muzzle fireball along the bore axis
        int flashes = big ? 4 : 2;
        for (int k = 0; k < flashes; ++k) {
            Vec3 fp = m.add(dir.scale(0.5 + (double)k * 0.85 * (double)s));
            float fs = (3.4f - 0.55f * (float)k) * s;
            int flife = 3 + (big ? 2 : 1);
            FxParticle f = new FxParticle(level, fp.x, fp.y, fp.z, k == 0 ? Sprites.flare() : Sprites.glow(), flife, true, fs);
            f.fullBright = true;
            f.motion = (pp, age) -> {
                float u = (float)age / (float)flife;
                pp.color(1.0f, 0.82f - 0.38f * u, 0.44f - 0.30f * u);
                pp.alpha(1.0f - u);
                pp.size = fs * (0.9f + 0.35f * u);
            };
            FxSystem.add(f);
        }

        // 2. Physical cordite smoke plume + lateral muzzle-brake jets
        Vec3 side = new Vec3(-dir.z, 0.0, dir.x);
        if (side.lengthSqr() > 1.0E-4) {
            side = side.normalize();
        } else {
            side = new Vec3(1.0, 0.0, 0.0);
        }
        Vec3 g = TrailFx.groundBelow(level, m);
        double gy = g != null ? g.y : (m.y - 1.6);

        int n = TrailFx.crowded() ? 8 : (big ? 28 : 14);
        for (int i = 0; i < n; ++i) {
            boolean jet = brake && i % 3 != 0;
            Vec3 v;
            Vec3 spawn;
            if (jet) {
                int sign = (i % 2 == 0) ? 1 : -1;
                double lat = (0.32 + R.nextDouble() * 0.28) * (double)s;
                v = side.scale((double)sign * lat)
                        .add(dir.scale(0.06 + R.nextDouble() * 0.08))
                        .add(R.nextGaussian() * 0.04, R.nextGaussian() * 0.03 + 0.015, R.nextGaussian() * 0.04);
                spawn = m.add(side.scale((double)sign * 0.35));
            } else {
                double fwd = (0.22 + R.nextDouble() * 0.48) * (double)s;
                v = dir.scale(fwd).add(R.nextGaussian() * 0.075 * s, R.nextGaussian() * 0.055 * s + 0.02, R.nextGaussian() * 0.075 * s);
                spawn = m.add(dir.scale(R.nextDouble() * 1.4 * (double)s));
            }
            float shade = 0.64f + R.nextFloat() * 0.20f;
            TrailFx.physicalSmoke(level, spawn, v, (double)s * (big ? 1.15 : 0.85), false, 0.88f, shade, false, gy);
        }

        // 3. Ground overpressure dust ring kicked up underneath the gun barrel
        int nDust = TrailFx.crowded() ? 4 : (big ? 14 : 6);
        for (int i = 0; i < nDust; ++i) {
            double a = R.nextDouble() * Math.PI * 2.0;
            double r = 0.8 + R.nextDouble() * (big ? 2.2 : 1.2);
            double sp = (0.16 + R.nextDouble() * 0.22) * (double)s;
            Vec3 dp = new Vec3(m.x + dir.x * 1.5 + Math.cos(a) * r, gy + 0.2, m.z + dir.z * 1.5 + Math.sin(a) * r);
            Vec3 dv = new Vec3(Math.cos(a) * sp + dir.x * 0.12, 0.025 + R.nextDouble() * 0.035, Math.sin(a) * sp + dir.z * 0.12);
            TrailFx.physicalSmoke(level, dp, dv, (double)s * 0.95, false, 0.35f, 0.62f, true, gy);
        }
    }

    /** Tracer streak + thin supersonic hot wake behind a tank or artillery shell. */
    public static void shellTick(ru.aiforge.realwar.ordnance.ShellEntity e) {
        ClientLevel level = Minecraft.getInstance().level;
        if (level == null || e.tickCount < 1) {
            return;
        }
        Vec3 a = new Vec3(e.xo, e.yo, e.zo);
        Vec3 b = e.position();
        Vec3 d = b.subtract(a);
        double len = d.length();
        if (len < 0.01 || len > 200.0) {
            return;
        }
        Vec3 dir = d.scale(1.0 / len);
        boolean art = e.profile().tntKg >= 3.5;
        if (!art || e.tickCount <= 8) {
            int n = Math.min(12, (int)Math.ceil(len / 0.8));
            for (int i = 0; i < n; ++i) {
                double t = (double)i / (double)n;
                FxParticle f = new FxParticle(level, a.x + d.x * t, a.y + d.y * t, a.z + d.z * t,
                        Sprites.flare(), 2, true, art ? 0.28f : 0.38f);
                f.fullBright = true;
                f.motion = (pp, age) -> {
                    pp.color(1.0f, 0.58f, 0.22f);
                    pp.alpha(0.92f - 0.42f * (float)age);
                };
                FxSystem.add(f);
            }
        }
        // Subtle aerodynamic smoke wake during early flight
        if (e.tickCount <= 14 && !TrailFx.crowded() && R.nextInt(2) == 0) {
            Vec3 mid = a.lerp(b, R.nextDouble());
            TrailFx.physicalSmoke(level, mid, dir.scale(-0.04), art ? 0.38 : 0.28, true, 0.30f, 0.80f, false, Double.NaN);
        }
    }

    public static void addTracer(TracerPacket m) {
        Tracer t = new Tracer();
        t.pos = new Vec3(m.x(), m.y(), m.z());
        t.vel = new Vec3(m.vx(), m.vy(), m.vz());
        t.life = m.life();
        if (TRACERS.size() < 400) {
            TRACERS.add(t);
        }
    }

    public static void clear() {
        TRACERS.clear();
    }

    public static void tick(ClientLevel level) {
        Iterator<Tracer> it = TRACERS.iterator();
        while (it.hasNext()) {
            BlockHitResult h;
            Tracer t = it.next();
            Vec3 from = t.pos;
            t.vel = new Vec3(t.vel.x * 0.985, t.vel.y * 0.985 - 0.02, t.vel.z * 0.985);
            Vec3 to = from.add(t.vel);
            if (level.hasChunkAt(BlockPos.containing((Position)to)) && (h = level.clip(new ClipContext(from, to, ClipContext.Block.COLLIDER, ClipContext.Fluid.NONE, null))).getType() != HitResult.Type.MISS) {
                it.remove();
                continue;
            }
            int n = 4;
            for (int i = 0; i < n; ++i) {
                Vec3 p = from.add(t.vel.scale(((double)i + 0.5) / (double)n));
                FxParticle g = new FxParticle(level, p.x, p.y, p.z, Sprites.glow(), 4, true, 0.55f);
                g.fullBright = true;
                g.motion = (pp, age) -> {
                    float f = (float)age / 4.0f;
                    pp.color(1.0f, 0.55f - 0.25f * f, 0.15f);
                    pp.alpha(0.95f * (1.0f - f));
                    pp.size = 0.55f * (1.0f - 0.5f * f);
                };
                FxSystem.add(g);
            }
            FxParticle c = new FxParticle(level, to.x, to.y, to.z, Sprites.flare(), 2, true, 0.8f);
            c.fullBright = true;
            c.motion = (pp, age) -> {
                pp.color(1.0f, 0.92f, 0.7f);
                pp.alpha(1.0f - (float)age / 2.0f);
            };
            FxSystem.add(c);
            t.pos = to;
            if (--t.life > 0) continue;
            it.remove();
        }
    }

    private static final class Tracer {
        Vec3 pos;
        Vec3 vel;
        int life;

        private Tracer() {
        }
    }
}
