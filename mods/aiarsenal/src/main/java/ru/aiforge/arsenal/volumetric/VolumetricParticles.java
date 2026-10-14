package ru.aiforge.arsenal.volumetric;

import net.minecraft.core.particles.SimpleParticleType;
import net.minecraftforge.registries.DeferredRegister;
import net.minecraftforge.registries.ForgeRegistries;
import net.minecraftforge.registries.RegistryObject;

/** Only a visual particle ID. Safe on dedicated servers; no donor gameplay registrations. */
public final class VolumetricParticles {
    public static final DeferredRegister<net.minecraft.core.particles.ParticleType<?>> TYPES =
        DeferredRegister.create(ForgeRegistries.PARTICLE_TYPES, "aiarsenal");
    public static final RegistryObject<SimpleParticleType> SMOKE = TYPES.register("volume_smoke", () -> new SimpleParticleType(true));
    private VolumetricParticles() {}
}
