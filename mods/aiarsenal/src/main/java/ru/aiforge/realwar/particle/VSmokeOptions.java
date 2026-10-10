package ru.aiforge.realwar.particle;

import com.mojang.brigadier.StringReader;
import com.mojang.brigadier.exceptions.CommandSyntaxException;
import com.mojang.serialization.Codec;
import com.mojang.serialization.codecs.RecordCodecBuilder;
import java.util.Locale;
import net.minecraft.core.particles.ParticleOptions;
import net.minecraft.core.particles.ParticleTypes;
import net.minecraft.core.particles.ParticleType;
import net.minecraft.core.registries.BuiltInRegistries;
import net.minecraft.network.FriendlyByteBuf;
import net.minecraft.util.RandomSource;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.server.level.ServerPlayer;
import ru.aiforge.realwar.registry.ModParticles;

/**
 * r27: one volumetric smoke puff ({@code aiarsenal:vsmoke}). Colour r g b, start size (m, sprite half-size), growth
 * factor over the life, life (ticks), centre opacity, heat (emission at birth, 0..1), rise (buoyancy, blocks/tick^2).
 * The client provider spawns an FxParticle drawn by VolumeFx (flat sprite when volumetric smoke is off).
 * Command: /particle aiarsenal:vsmoke 0.8 0.8 0.8 2 2.5 200 0.8 0 0.002 ~ ~2 ~ 0 0 0 0 1
 */
public record VSmokeOptions(float r, float g, float b, float size, float grow, int life, float alpha, float heat, float rise)
        implements ParticleOptions {
    public static final Codec<VSmokeOptions> CODEC = RecordCodecBuilder.create(i -> i.group(
            Codec.FLOAT.fieldOf("r").forGetter(VSmokeOptions::r),
            Codec.FLOAT.fieldOf("g").forGetter(VSmokeOptions::g),
            Codec.FLOAT.fieldOf("b").forGetter(VSmokeOptions::b),
            Codec.FLOAT.fieldOf("size").forGetter(VSmokeOptions::size),
            Codec.FLOAT.fieldOf("grow").forGetter(VSmokeOptions::grow),
            Codec.INT.fieldOf("life").forGetter(VSmokeOptions::life),
            Codec.FLOAT.fieldOf("alpha").forGetter(VSmokeOptions::alpha),
            Codec.FLOAT.fieldOf("heat").forGetter(VSmokeOptions::heat),
            Codec.FLOAT.fieldOf("rise").forGetter(VSmokeOptions::rise)
    ).apply(i, VSmokeOptions::new));

    @SuppressWarnings("deprecation")
    public static final ParticleOptions.Deserializer<VSmokeOptions> DESERIALIZER = new ParticleOptions.Deserializer<VSmokeOptions>() {
        @Override
        public VSmokeOptions fromCommand(ParticleType<VSmokeOptions> type, StringReader rd) throws CommandSyntaxException {
            float[] v = {0.8f, 0.8f, 0.8f, 1.5f, 2.0f, 120.0f, 0.8f, 0.0f, 0.002f};
            for (int k = 0; k < v.length && rd.canRead(); k++) {
                rd.expect(' ');
                v[k] = rd.readFloat();
            }
            return new VSmokeOptions(v[0], v[1], v[2], v[3], v[4], (int) v[5], v[6], v[7], v[8]);
        }

        @Override
        public VSmokeOptions fromNetwork(ParticleType<VSmokeOptions> type, FriendlyByteBuf buf) {
            return new VSmokeOptions(buf.readFloat(), buf.readFloat(), buf.readFloat(), buf.readFloat(), buf.readFloat(),
                    buf.readVarInt(), buf.readFloat(), buf.readFloat(), buf.readFloat());
        }
    };

    /** grey/white smoke screen puff */
    public static VSmokeOptions screen(float shade, float size, int life) {
        return new VSmokeOptions(shade, shade, shade * 0.98f, size, 2.2f, life, 0.85f, 0.0f, 0.0015f);
    }

    /**
     * r28: volumetric preset for a vanilla smoke type (the same look as VolumeFx.vanilla used to give), or null when
     * the type is not a smoke type. Only smoke types are mapped; everything else keeps its vanilla particle.
     */
    public static VSmokeOptions vanillaPreset(ParticleOptions type, RandomSource r) {
        if (type == ParticleTypes.SMOKE) {
            return new VSmokeOptions(0.36f, 0.36f, 0.35f, 0.7f, 2.8f, 70 + r.nextInt(30), 0.7f, 0.0f, 0.0015f);
        }
        if (type == ParticleTypes.LARGE_SMOKE) {
            return new VSmokeOptions(0.22f, 0.21f, 0.2f, 0.5f, 3.0f, 45 + r.nextInt(20), 0.6f, 0.0f, 0.001f);
        }
        if (type == ParticleTypes.CAMPFIRE_COSY_SMOKE) {
            return new VSmokeOptions(0.55f, 0.55f, 0.54f, 0.9f, 3.0f, 110 + r.nextInt(40), 0.65f, 0.0f, 0.0012f);
        }
        if (type == ParticleTypes.CAMPFIRE_SIGNAL_SMOKE) {
            return new VSmokeOptions(0.6f, 0.6f, 0.59f, 1.0f, 3.6f, 220 + r.nextInt(80), 0.7f, 0.0f, 0.0018f);
        }
        return null;
    }

    /**
     * r28: drop-in for {@code sl.sendParticles(type, x, y, z, count, dx, dy, dz, speed)}. Smoke types become volumetric
     * puffs (see {@link #vanillaPreset}); any other type is sent as before.
     */
    public static void sendVanilla(ServerLevel sl, ParticleOptions type, double x, double y, double z, int count,
                                   double dx, double dy, double dz, double speed) {
        VSmokeOptions o = vanillaPreset(type, sl.random);
        if (o == null) {
            sl.sendParticles(type, x, y, z, count, dx, dy, dz, speed);
        } else {
            send(sl, o, x, y, z, count, dx, dy, dz, speed);
        }
    }

    @Override
    public ParticleType<?> getType() {
        return ModParticles.VSMOKE.get();
    }

    @Override
    public void writeToNetwork(FriendlyByteBuf buf) {
        buf.writeFloat(this.r);
        buf.writeFloat(this.g);
        buf.writeFloat(this.b);
        buf.writeFloat(this.size);
        buf.writeFloat(this.grow);
        buf.writeVarInt(this.life);
        buf.writeFloat(this.alpha);
        buf.writeFloat(this.heat);
        buf.writeFloat(this.rise);
    }

    @Override
    public String writeToString() {
        return String.format(Locale.ROOT, "%s %.3f %.3f %.3f %.2f %.2f %d %.2f %.2f %.4f", BuiltInRegistries.PARTICLE_TYPE.getKey(this.getType()),
                this.r, this.g, this.b, this.size, this.grow, this.life, this.alpha, this.heat, this.rise);
    }

    /**
     * Sends puffs to every player within 512 blocks (the plain sendParticles reaches only 32 blocks - smoke screens and
     * burning vehicles must be visible from far away). count = 0: one puff with velocity (dx, dy, dz) * speed;
     * count > 0: gaussian spread (dx, dy, dz) around the point, random velocity * speed (vanilla semantics).
     */
    public static void send(ServerLevel sl, VSmokeOptions o, double x, double y, double z, int count, double dx, double dy, double dz, double speed) {
        for (ServerPlayer p : sl.players()) {
            sl.sendParticles(p, o, true, x, y, z, count, dx, dy, dz, speed);
        }
    }
}
