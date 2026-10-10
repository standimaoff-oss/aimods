package ru.aiforge.realwar.grenade;

import net.minecraft.core.Direction;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.sounds.SoundSource;
import net.minecraft.world.entity.Entity;
import net.minecraft.world.entity.EntityType;
import net.minecraft.world.entity.LivingEntity;
import net.minecraft.world.entity.projectile.ThrowableItemProjectile;
import net.minecraft.world.item.Item;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.level.Level;
import net.minecraft.world.phys.BlockHitResult;
import net.minecraft.world.phys.HitResult;
import net.minecraft.world.phys.Vec3;
import ru.aiforge.realwar.field.Detonations;
import ru.aiforge.realwar.registry.ModEntities;
import ru.aiforge.realwar.registry.ModItems;
import ru.aiforge.realwar.registry.ModSounds;
import ru.aiforge.realwar.vehicle.SmokeScreen;

/**
 * r27: thrown hand grenade. It bounces off blocks (sound + damped velocity, stops on the ground), ignores entities
 * and goes off after its fuse. The kind travels as the synced item stack, so the client renders the right icon.
 */
public class GrenadeEntity extends ThrowableItemProjectile {
    public GrenadeEntity(EntityType<? extends GrenadeEntity> type, Level level) {
        super(type, level);
    }

    public GrenadeEntity(ServerLevel level, LivingEntity owner, ItemStack stack) {
        super(ModEntities.GRENADE.get(), owner, level);
        this.setItem(stack);
    }

    public GrenadeKind kind() {
        return GrenadeItem.kindOf(this.getItem());
    }

    @Override
    protected Item getDefaultItem() {
        return ModItems.grenade(GrenadeKind.RGD5).get();
    }

    @Override
    protected float getGravity() {
        return 0.035f;
    }

    @Override
    protected boolean canHitEntity(Entity e) {
        return false;
    }

    @Override
    public void tick() {
        super.tick();
        if (!this.level().isClientSide && this.level() instanceof ServerLevel sl && this.tickCount >= this.kind().fuse) {
            this.detonate(sl);
            this.discard();
        }
    }

    @Override
    protected void onHitBlock(BlockHitResult hit) {
        super.onHitBlock(hit);
        Direction d = hit.getDirection();
        Vec3 v = this.getDeltaMovement();
        Vec3 nv = switch (d.getAxis()) {
            case X -> new Vec3(-v.x * 0.45, v.y * 0.7, v.z * 0.7);
            case Y -> new Vec3(v.x * 0.7, (d == Direction.UP ? 1 : -1) * Math.abs(v.y) * 0.35, v.z * 0.7);
            default -> new Vec3(v.x * 0.7, v.y * 0.7, -v.z * 0.45);
        };
        Vec3 at = hit.getLocation().add(Vec3.atLowerCornerOf(d.getNormal()).scale(0.04));
        this.setPos(at.x, at.y, at.z);
        if (d == Direction.UP && nv.lengthSqr() < 0.01) {
            nv = Vec3.ZERO;                       // came to rest on the ground
        }
        this.setDeltaMovement(nv);
        if (v.lengthSqr() > 0.04 && !this.level().isClientSide) {
            this.level().playSound(null, at.x, at.y, at.z, ModSounds.GRENADE_BOUNCE.get(), SoundSource.BLOCKS, 0.6f, 1.0f);
        }
    }

    @Override
    protected void onHit(HitResult r) {
        if (r.getType() == HitResult.Type.BLOCK) {
            super.onHit(r);
        }
    }

    /** Goes off: blast / fragments / flash / smoke / fire. Server only. */
    private void detonate(ServerLevel sl) {
        GrenadeKind k = this.kind();
        Vec3 p = this.position();
        switch (k.effect) {
            case HE, FRAG -> {
                Detonations.queue(sl, p, k.kg, k.frag, 0, 0);
                sl.playSound(null, p.x, p.y, p.z, ModSounds.GRENADE_BLAST.get(), SoundSource.BLOCKS, 2.0f, 1.0f);
            }
            case FIRE -> {
                Detonations.queue(sl, p, k.kg, k.frag, k.fire, 0);
                sl.playSound(null, p.x, p.y, p.z, ModSounds.GRENADE_BLAST.get(), SoundSource.BLOCKS, 1.2f, 1.3f);
            }
            case FLASH -> {
                GrenadeFlash.flash(sl, p);
                sl.playSound(null, p.x, p.y, p.z, ModSounds.FLASHBANG.get(), SoundSource.BLOCKS, 3.0f, 1.0f);
            }
            case SMOKE -> {
                SmokeScreen.add(sl, p, 6.0, 500, new float[]{k.r, k.g, k.b});
                sl.playSound(null, p.x, p.y, p.z, ModSounds.SMOKE_HISS.get(), SoundSource.BLOCKS, 1.4f, 1.0f);
            }
        }
    }
}
