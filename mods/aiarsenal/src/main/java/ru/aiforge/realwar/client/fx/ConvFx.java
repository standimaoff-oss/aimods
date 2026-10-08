package ru.aiforge.realwar.client.fx;

import java.util.Random;
import net.minecraft.client.Minecraft;
import net.minecraft.client.multiplayer.ClientLevel;
import net.minecraft.core.BlockPos;
import net.minecraft.core.particles.BlockParticleOption;
import net.minecraft.core.particles.ParticleOptions;
import net.minecraft.core.particles.ParticleTypes;
import net.minecraft.sounds.SoundEvent;
import net.minecraft.sounds.SoundSource;
import net.minecraft.util.Mth;
import net.minecraft.world.level.block.state.BlockState;
import net.minecraft.world.phys.Vec3;
import ru.aiforge.realwar.RWConfig;
import ru.aiforge.realwar.blast.BlastPhysics;
import ru.aiforge.realwar.client.particle.FxParticle;
import ru.aiforge.realwar.client.particle.FxSystem;
import ru.aiforge.realwar.client.particle.Sprites;
import ru.aiforge.realwar.fx.CloudModel;
import ru.aiforge.realwar.network.ConventionalEffectPacket;
import ru.aiforge.realwar.registry.ModSounds;

/**
 * Multi-stage 3D volumetric explosion effect for bombs (FAB-250..5000, KAB-500, SC-50..1000),
 * cruise & ballistic missiles (Kh-101, Kalibr, Tomahawk, Iskander, Tochka), MLRS rockets
 * (Grad, Smerch, TOS-1A, Katyusha, Sturmtiger), ATGM/RPG warheads, and artillery/tank HE shells.
 *
 * Stages:
 *  0. Blinding 3D detonation flash + concentric volumetric plasma core spheres
 *  1. Supersonic 3D Wilson condensation dome + ground Mach-stem shockwave ring
 *  2. Boiling 3D volumetric fireball with toroidal vortex circulation & black-body cooling
 *  3. Ballistic incandescent shrapnel / ejecta streamers that leave physical smoke trails in flight
 *  4. Rising volumetric pyroclastic mushroom cap, convective suction stem, and radial base surge
 */
public final class ConvFx {
    private final ConventionalEffectPacket m;
    private final Random rnd;
    private int age;
    private final int maxAge;
    private boolean inRange;

    public ConvFx(ConventionalEffectPacket m) {
        this.m = m;
        this.rnd = new Random(m.seed());
        double r = Math.cbrt(Math.max(1.0f, m.massKg()));
        this.maxAge = Mth.clamp((int)(14.0 + r * 3.2), 16, 48);
    }

    private void add(FxParticle p) {
        if (p != null) {
            FxSystem.add(p);
        }
    }

    public boolean tick(ClientLevel level, Minecraft mc) {
        Vec3 c = new Vec3(this.m.x(), this.m.y(), this.m.z());
        if (this.age == 0) {
            double dist = mc.player == null ? 0.0 : mc.player.getEyePosition().distanceTo(c);
            this.inRange = dist <= (Double)RWConfig.CLIENT.maxEffectDistance.get();
            if (this.inRange) {
                this.spawnInitialDetonation(level, c);
            }
            this.schedule(level, mc, c, dist);
        } else if (this.inRange) {
            this.tickVolumetricPlume(level, c, this.age);
        }
        return ++this.age >= this.maxAge;
    }

    private void spawnInitialDetonation(ClientLevel level, Vec3 c) {
        float q = ((Double)RWConfig.CLIENT.particleQuality.get()).floatValue();
        double r = Math.cbrt(Math.max(1.0f, this.m.massKg()));
        double x = c.x;
        double y = c.y;
        double z = c.z;

        // ---------------------------------------------------------------------
        // Stage 0: Blinding 3D Detonation Flash & Volumetric Plasma Core
        // ---------------------------------------------------------------------
        float flashSize = (float)(r * 4.4);
        FxParticle flash = new FxParticle(level, x, y + 0.15 * r, z, Sprites.flare(), 6, true, flashSize);
        flash.fullBright = true;
        flash.motion = (p, a) -> {
            float f = (float)a / 6.0f;
            p.size = flashSize * (1.15f - 0.55f * f);
            p.color(1.0f, 0.94f - 0.18f * f, 0.78f - 0.35f * f);
            p.alpha((1.0f - f) * 0.98f);
        };
        this.add(flash);

        float coreSize = (float)(r * 3.5);
        FxParticle core = new FxParticle(level, x, y + 0.1 * r, z, Sprites.glow(), 14, true, coreSize);
        core.fullBright = true;
        core.motion = (p, a) -> {
            float f = (float)a / 14.0f;
            p.size = coreSize * (0.55f + 0.65f * f);
            p.color(1.0f, 0.86f - 0.32f * f, 0.52f - 0.36f * f);
            p.alpha((1.0f - f) * 0.92f);
        };
        this.add(core);

        // ---------------------------------------------------------------------
        // Stage 1: 3D Volumetric Fireball Shells (Inner, Middle, Outer Lobes)
        // ---------------------------------------------------------------------
        int nFire = (int)(Math.max(24.0, Math.min(130.0, 32.0 * r / 1.8)) * (double)q);
        float[] col = new float[3];
        for (int i = 0; i < nFire; ++i) {
            // Stratified 3D spherical distribution
            double u = this.rnd.nextDouble() * 2.0 - 1.0;
            if (this.m.surface() && u < -0.25) {
                u = -u * 0.65; // hemisphere bias on surface impacts
            }
            double phi = this.rnd.nextDouble() * Math.PI * 2.0;
            double sn = Math.sqrt(Math.max(0.0, 1.0 - u * u));
            double shell = 0.25 + 0.75 * Math.cbrt(this.rnd.nextDouble());
            double rad0 = r * 0.32 * shell;

            double sp = (0.10 + 0.20 * this.rnd.nextDouble()) * Math.max(0.65, r / 3.4) * shell;
            double vx = sn * Math.cos(phi) * sp;
            double vy = u * sp + (0.04 + 0.03 * (1.0 - shell)) * Math.max(0.7, r / 4.5);
            double vz = sn * Math.sin(phi) * sp;

            int life = 14 + this.rnd.nextInt(18);
            float base = (float)(r * (0.52 + 0.58 * this.rnd.nextDouble()));
            float tempBias = (float)(1.05 - 0.32 * shell);

            FxParticle p2 = new FxParticle(
                    level,
                    x + sn * Math.cos(phi) * rad0,
                    y + Math.max(-0.2, u * rad0),
                    z + sn * Math.sin(phi) * rad0,
                    Sprites.glow(),
                    life,
                    true,
                    base * 0.65f
            );
            p2.fullBright = true;
            p2.velocity(vx, vy, vz);
            p2.spin = (this.rnd.nextFloat() - 0.5f) * 0.08f;
            p2.motion = (pp, a) -> {
                float f = (float)a / (float)life;
                // Toroidal vortex rise: hot center rises faster, outer lobes curl outward then inward
                double buoy = 0.006 * (double)(1.0f - f);
                pp.translate(pp.getDeltaX(), pp.getDeltaY() + buoy, pp.getDeltaZ());
                pp.scaleVelocity(a < 5 ? 0.84 : 0.90);
                double tNorm = Mth.clamp((double)(tempBias * (1.0f - f * 0.88f)), 0.05, 1.0);
                CloudModel.hotColor(tNorm, col);
                pp.color(col[0], col[1], col[2]);
                pp.alpha(0.72f * (1.0f - f * f));
                pp.size = base * (0.58f + 0.82f * Mth.sqrt(f));
            };
            this.add(p2);
        }

        // ---------------------------------------------------------------------
        // Stage 2: 3D Wilson Condensation Dome (Supersonic Shockwave Vapor Shell)
        // ---------------------------------------------------------------------
        if (r >= 1.35) {
            int nWilson = (int)(Math.min(72.0, 16.0 + 9.0 * r) * (double)q);
            int wLife = Mth.clamp((int)(8.0 + r * 2.2), 9, 22);
            double shockSpeed = (0.42 + 0.14 * r);
            for (int i = 0; i < nWilson; ++i) {
                double u = this.m.surface() ? (0.05 + 0.95 * this.rnd.nextDouble()) : (this.rnd.nextDouble() * 2.0 - 1.0);
                double phi = this.rnd.nextDouble() * Math.PI * 2.0;
                double sn = Math.sqrt(Math.max(0.0, 1.0 - u * u));
                double dx = sn * Math.cos(phi);
                double dy = u;
                double dz = sn * Math.sin(phi);
                float wSize = (float)(0.75 + 0.42 * r);
                FxParticle w = new FxParticle(
                        level,
                        x + dx * r * 0.4,
                        y + dy * r * 0.4,
                        z + dz * r * 0.4,
                        Sprites.smoke(i),
                        wLife,
                        false,
                        wSize
                );
                w.velocity(dx * shockSpeed, dy * shockSpeed, dz * shockSpeed);
                w.motion = (pp, a) -> {
                    float f = (float)a / (float)wLife;
                    pp.translate(pp.getDeltaX(), pp.getDeltaY(), pp.getDeltaZ());
                    pp.scaleVelocity(0.92);
                    pp.color(0.94f, 0.96f, 0.99f);
                    float env = (float)Math.sin((double)f * Math.PI);
                    pp.alpha(0.32f * env * (1.0f - 0.3f * f));
                    pp.size = wSize * (0.85f + 1.35f * f);
                };
                this.add(w);
            }
        }

        // ---------------------------------------------------------------------
        // Stage 3: Incandescent Ballistic Shrapnel & Fire-Streamers with Smoke Trails
        // ---------------------------------------------------------------------
        int nStreamers = (int)(Math.max(6.0, Math.min(32.0, 4.5 * r)) * (double)q);
        for (int i = 0; i < nStreamers; ++i) {
            double phi = this.rnd.nextDouble() * Math.PI * 2.0;
            double elev = (0.18 + 0.62 * this.rnd.nextDouble()) * (Math.PI * 0.5);
            double sp = (0.32 + 0.48 * this.rnd.nextDouble()) * Math.max(0.8, Math.sqrt(r) * 0.68);
            double vx = Math.cos(elev) * Math.cos(phi) * sp;
            double vy = Math.sin(elev) * sp + 0.08;
            double vz = Math.cos(elev) * Math.sin(phi) * sp;
            int sLife = 18 + this.rnd.nextInt(22);
            float emberSize = (float)(0.28 + 0.12 * Math.min(r, 4.0));

            FxParticle ember = new FxParticle(level, x, y + 0.25, z, Sprites.flare(), sLife, true, emberSize);
            ember.fullBright = true;
            ember.velocity(vx, vy, vz);
            ember.motion = (pp, a) -> {
                float f = (float)a / (float)sLife;
                double nvx = pp.getDeltaX() * 0.96;
                double nvy = pp.getDeltaY() * 0.96 - 0.026; // gravity arc
                double nvz = pp.getDeltaZ() * 0.96;
                pp.velocity(nvx, nvy, nvz);
                pp.translate(nvx, nvy, nvz);
                pp.color(1.0f, 0.78f - 0.45f * f, 0.32f * (1.0f - f));
                pp.alpha(0.95f * (1.0f - f));
                pp.size = emberSize * (1.0f - 0.45f * f);

                // Spawn trailing smoke wisp along the ballistic arc
                if (a % 2 == 0 && !TrailFx.crowded()) {
                    TrailFx.physicalSmoke(
                            level,
                            new Vec3(pp.x(), pp.y(), pp.z()),
                            new Vec3(-nvx * 0.15, 0.01, -nvz * 0.15),
                            0.28 * Math.min(2.2, Math.sqrt(r)),
                            true,
                            0.55f * (1.0f - f),
                            0.74f,
                            false,
                            Double.NaN
                    );
                }
            };
            this.add(ember);
        }

        // ---------------------------------------------------------------------
        // Stage 4: Immediate Volumetric Soot/Pyroclastic Core & Ground Mach Ring
        // ---------------------------------------------------------------------
        int nSmoke = (int)(Math.max(20.0, Math.min(95.0, 22.0 * r / 1.8)) * (double)q);
        double groundY = this.m.surface() ? y : Double.NaN;
        for (int i = 0; i < nSmoke; ++i) {
            double phi = this.rnd.nextDouble() * Math.PI * 2.0;
            double u = this.m.surface() ? (-0.1 + 1.1 * this.rnd.nextDouble()) : (this.rnd.nextDouble() * 2.0 - 1.0);
            double sn = Math.sqrt(Math.max(0.0, 1.0 - u * u));
            double rad = (0.15 + 0.65 * this.rnd.nextDouble()) * r;
            double sp = (0.06 + 0.14 * this.rnd.nextDouble()) * Math.max(0.7, r / 3.5);
            Vec3 spawn = new Vec3(x + sn * Math.cos(phi) * rad, y + Math.max(0.1, u * rad * 0.7), z + sn * Math.sin(phi) * rad);
            Vec3 vel = new Vec3(
                    sn * Math.cos(phi) * sp,
                    (0.10 + 0.24 * this.rnd.nextDouble()) * Math.max(0.75, r / 4.2),
                    sn * Math.sin(phi) * sp
            );
            float shade = 0.24f + 0.26f * this.rnd.nextFloat();
            TrailFx.physicalSmoke(level, spawn, vel, r * (0.48 + 0.35 * this.rnd.nextDouble()), false, 0.95f, shade, false, groundY);
        }

        // Block debris fountain
        BlockPos bp = BlockPos.containing(x, y - 0.5, z);
        BlockState below = level.getBlockState(bp);
        for (int dy = 0; dy < 3 && below.isAir(); ++dy) {
            below = level.getBlockState(bp.below(dy + 1));
        }
        if (!below.isAir()) {
            int nDebris = (int)(Math.min(130.0, 14.0 + 7.0 * r) * (double)q);
            for (int i = 0; i < nDebris; ++i) {
                double a = this.rnd.nextDouble() * Math.PI * 2.0;
                double sp = 0.16 + 0.38 * this.rnd.nextDouble() * Math.max(0.8, r / 4.8);
                level.addParticle(
                        (ParticleOptions)new BlockParticleOption(ParticleTypes.BLOCK, below),
                        x, y + 0.25, z,
                        Math.cos(a) * sp,
                        0.28 + 0.72 * this.rnd.nextDouble() * Math.max(0.8, r / 5.5),
                        Math.sin(a) * sp
                );
            }
        }

        // Surface Mach-stem dust shockwave ring + radial base surge
        if (this.m.surface()) {
            int nRing = (int)(Math.min(72.0, 16.0 + 3.8 * r) * (double)q);
            for (int i = 0; i < nRing; ++i) {
                double a = (double)i * (Math.PI * 2.0 / (double)nRing) + (this.rnd.nextDouble() - 0.5) * 0.18;
                double sp = (0.24 + 0.12 * this.rnd.nextDouble()) * Math.max(0.85, r / 3.4);
                Vec3 rPos = new Vec3(x + Math.cos(a) * r * 0.35, y + 0.25, z + Math.sin(a) * r * 0.35);
                Vec3 rVel = new Vec3(Math.cos(a) * sp, 0.025 + this.rnd.nextDouble() * 0.03, Math.sin(a) * sp);
                TrailFx.physicalSmoke(level, rPos, rVel, 0.55 + r * 0.26, false, 0.42f, 0.58f, true, y);
            }
        }
    }

    /**
     * Dynamic multi-tick evolution of the 3D explosion:
     *  - Secondary boiling fireball lobes inside the rising cap (ticks 1..14)
     *  - Toroidal rolling mushroom cap & convective suction stem (ticks 2..maxAge)
     */
    private void tickVolumetricPlume(ClientLevel level, Vec3 c, int tick) {
        if (TrailFx.crowded()) {
            return;
        }
        float q = ((Double)RWConfig.CLIENT.particleQuality.get()).floatValue();
        double r = Math.cbrt(Math.max(1.0f, this.m.massKg()));
        double progress = (double)tick / (double)this.maxAge;
        double capHeight = r * (0.45 + 1.85 * Math.pow(progress, 0.72));
        double capRadius = r * (0.35 + 0.85 * Math.sqrt(progress));
        double groundY = this.m.surface() ? c.y : Double.NaN;

        // 1. Sustained boiling 3D fireball lobes inside the rising cap (especially heavy bombs & thermobaric)
        if (tick <= Math.min(18, this.maxAge / 2)) {
            int nLobes = Math.max(1, (int)((1.5 + 0.65 * r) * (double)q * (1.0 - progress)));
            float[] col = new float[3];
            for (int i = 0; i < nLobes; ++i) {
                double phi = this.rnd.nextDouble() * Math.PI * 2.0;
                double rad = this.rnd.nextDouble() * capRadius * 0.75;
                double dy = (this.rnd.nextDouble() - 0.35) * r * 0.55;
                double lx = c.x + Math.cos(phi) * rad;
                double ly = c.y + capHeight + dy;
                double lz = c.z + Math.sin(phi) * rad;

                int life = 10 + this.rnd.nextInt(12);
                float base = (float)(r * (0.45 + 0.45 * this.rnd.nextDouble()));
                FxParticle lobe = new FxParticle(level, lx, ly, lz, Sprites.glow(), life, true, base * 0.7f);
                lobe.fullBright = true;
                // Toroidal circulation: up in the middle, rolling outward at the top
                double outSp = (dy > 0.0 ? 0.05 : -0.025) * Math.max(0.7, r / 4.0);
                lobe.velocity(Math.cos(phi) * outSp, 0.07 + 0.04 * this.rnd.nextDouble(), Math.sin(phi) * outSp);
                lobe.motion = (pp, a) -> {
                    float f = (float)a / (float)life;
                    pp.translate(pp.getDeltaX(), pp.getDeltaY(), pp.getDeltaZ());
                    pp.scaleVelocity(0.90);
                    double tNorm = Mth.clamp(0.88 - 0.45 * progress - 0.55 * (double)f, 0.05, 1.0);
                    CloudModel.hotColor(tNorm, col);
                    pp.color(col[0], col[1], col[2]);
                    pp.alpha(0.62f * (1.0f - f));
                    pp.size = base * (0.65f + 0.65f * f);
                };
                this.add(lobe);
            }
        }

        // 2. Toroidal rolling pyroclastic mushroom cap
        int nCap = Math.max(1, (int)((1.2 + 0.55 * r) * (double)q));
        for (int i = 0; i < nCap; ++i) {
            double phi = this.rnd.nextDouble() * Math.PI * 2.0;
            double ringR = (0.35 + 0.65 * this.rnd.nextDouble()) * capRadius;
            double dy = (this.rnd.nextDouble() - 0.5) * r * 0.5;
            Vec3 pos = new Vec3(c.x + Math.cos(phi) * ringR, c.y + capHeight + dy, c.z + Math.sin(phi) * ringR);
            // Vortex ring velocity: outward at top of cap, curling down/inward at lower rim
            double radialV = (dy >= 0.0 ? 0.055 : -0.02) * Math.max(0.7, r / 3.8);
            double upV = (0.06 + 0.08 * (1.0 - ringR / Math.max(0.1, capRadius))) * Math.max(0.7, r / 4.5);
            Vec3 vel = new Vec3(Math.cos(phi) * radialV, upV, Math.sin(phi) * radialV);
            float temp = (float)Mth.clamp(0.85 - 0.55 * progress, 0.25, 0.90);
            float shade = 0.28f + 0.28f * this.rnd.nextFloat();
            TrailFx.physicalSmoke(level, pos, vel, r * (0.45 + 0.30 * this.rnd.nextDouble()), false, temp, shade, false, groundY);
        }

        // 3. Central convective suction stem (dust & smoke column drawn up into the mushroom cap)
        if (this.m.surface() && r >= 1.6 && tick % 2 == 0) {
            double stemPhi = this.rnd.nextDouble() * Math.PI * 2.0;
            double stemR = (0.1 + 0.35 * this.rnd.nextDouble()) * r * 0.45;
            double stemH = this.rnd.nextDouble() * capHeight * 0.85;
            Vec3 sPos = new Vec3(c.x + Math.cos(stemPhi) * stemR, c.y + 0.2 + stemH, c.z + Math.sin(stemPhi) * stemR);
            // Inward suction + strong upward chimney draft
            Vec3 sVel = new Vec3(-Math.cos(stemPhi) * 0.025, 0.11 + 0.06 * this.rnd.nextDouble(), -Math.sin(stemPhi) * 0.025);
            TrailFx.physicalSmoke(level, sPos, sVel, r * 0.38, false, 0.55f, 0.56f, true, groundY);
        }
    }

    private void schedule(ClientLevel level, Minecraft mc, Vec3 c, double dist) {
        if (mc.player == null) {
            return;
        }
        double r = Math.cbrt(this.m.massKg());
        double range = 90.0 + 60.0 * r;
        if (dist > range * 1.6) {
            return;
        }
        int delay = (int)(dist / 343.0 * 20.0);
        float vol = (float)CloudModel.clamp(1.3 - dist / range, 0.15, 1.0);
        SoundEvent s = this.m.massKg() < 40.0f ? (SoundEvent)ModSounds.BLAST_SMALL.get() : (this.m.massKg() < 400.0f ? (SoundEvent)ModSounds.BLAST_MEDIUM.get() : (SoundEvent)ModSounds.BLAST_LARGE.get());
        float pitch = (float)(1.05 - 0.06 * Math.log10(Math.max(1.0, (double)this.m.massKg())));
        ClientBlastManager.later(delay, () -> {
            if (mc.player == null || mc.level == null) {
                return;
            }
            Vec3 pp = mc.player.position();
            Vec3 dir = c.subtract(pp);
            double len = dir.length();
            Vec3 pos = len < 6.0 ? c : pp.add(dir.scale(6.0 / len));
            mc.level.playLocalSound(pos.x, pos.y, pos.z, s, SoundSource.AMBIENT, vol, pitch, false);
            double p = BlastPhysics.overpressure(Math.max(1.0, dist), this.m.massKg(), this.m.surface());
            if (p > 3.0) {
                ClientBlastManager.shake(mc.level, (float)CloudModel.clamp(Math.sqrt(p) * 0.25, 0.2, 5.0), 18.0f + (float)r);
            }
        });
        double fluence = BlastPhysics.thermalFluence((double)this.m.massKg() / 1000000.0 * 0.3, Math.max(1.0, dist));
        if (fluence > 0.6 && ((Boolean)RWConfig.CLIENT.flashEffect.get()).booleanValue()) {
            ClientBlastManager.flash(level, (float)CloudModel.clamp(fluence / 4.0, 0.0, 0.5));
        }
    }
}
