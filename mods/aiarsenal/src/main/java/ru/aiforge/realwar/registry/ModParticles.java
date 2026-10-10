package ru.aiforge.realwar.registry;

import com.mojang.serialization.Codec;
import net.minecraft.core.particles.ParticleType;
import net.minecraftforge.registries.DeferredRegister;
import net.minecraftforge.registries.ForgeRegistries;
import net.minecraftforge.registries.RegistryObject;
import ru.aiforge.realwar.RealWar;
import ru.aiforge.realwar.particle.VSmokeOptions;

/** r27: Real War particle types. */
public final class ModParticles {
    public static final DeferredRegister<ParticleType<?>> PARTICLES = DeferredRegister.create(ForgeRegistries.PARTICLE_TYPES, RealWar.MODID);

    /** volumetric smoke puff, long-distance (overrideLimiter = true: shown even with reduced particle settings) */
    public static final RegistryObject<ParticleType<VSmokeOptions>> VSMOKE = PARTICLES.register("vsmoke",
            () -> new ParticleType<VSmokeOptions>(true, VSmokeOptions.DESERIALIZER) {
                @Override
                public Codec<VSmokeOptions> codec() {
                    return VSmokeOptions.CODEC;
                }
            });

    private ModParticles() {
    }
}
