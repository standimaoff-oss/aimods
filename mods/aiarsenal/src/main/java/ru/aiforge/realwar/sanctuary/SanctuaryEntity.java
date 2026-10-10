package ru.aiforge.realwar.sanctuary;

import java.util.UUID;
import net.minecraft.core.BlockPos;
import net.minecraft.nbt.CompoundTag;
import net.minecraft.network.protocol.Packet;
import net.minecraft.network.protocol.game.ClientGamePacketListener;
import net.minecraft.network.syncher.EntityDataAccessor;
import net.minecraft.network.syncher.EntityDataSerializers;
import net.minecraft.network.syncher.SynchedEntityData;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.world.entity.Entity;
import net.minecraft.world.entity.EntityType;
import net.minecraft.world.damagesource.DamageSource;
import net.minecraft.world.level.Level;
import net.minecraft.world.level.levelgen.Heightmap;
import net.minecraft.core.particles.ParticleTypes;
import net.minecraft.util.Mth;
import net.minecraft.world.phys.Vec3;
import net.minecraftforge.network.NetworkHooks;
import ru.aiforge.realwar.ordnance.Ballistics;
import ru.aiforge.realwar.ordnance.ShellEntity;

/**
 * Sanctuary II (r31): Thanos' flagship from the Avengers films, unpiloted. It arrives through a rift when a remote
 * summons it, then obeys orders: HOLD, MOVE (advance to the point), SHELL_RAIN (every gun fires straight down on an
 * area around the point) and RECALL (return through the rift). Invulnerable here; it is not a crewed vehicle.
 */
public final class SanctuaryEntity extends Entity {
    public enum Order { HOLD, MOVE, SHELL_RAIN, RECALL }

    /** Rift opening time, ticks. */
    public static final int RIFT_TICKS = 100;
    /** Hover height above the ground under the goal, m (blocks). */
    public static final double HOVER_ALT = 60.0;
    /** Cruise speed, blocks per tick. */
    public static final double SPEED = 0.9;
    /** Shell rain: radius of the area, ticks between volleys, shells per volley, total rounds per order. */
    public static final double RAIN_RADIUS = 40.0;
    public static final int RAIN_PERIOD = 10;
    public static final int RAIN_PER_VOLLEY = 3;
    public static final int RAIN_ROUNDS = 150;

    private static final EntityDataAccessor<Integer> DATA_ORDER = SynchedEntityData.defineId(SanctuaryEntity.class, EntityDataSerializers.INT);
    private static final EntityDataAccessor<Integer> DATA_RIFT = SynchedEntityData.defineId(SanctuaryEntity.class, EntityDataSerializers.INT);

    private Vec3 goal = null;
    private Vec3 riftPos = Vec3.ZERO;
    private int rounds;
    private int cool;

    public SanctuaryEntity(EntityType<? extends SanctuaryEntity> type, Level level) {
        super(type, level);
        this.noPhysics = true;
        this.setNoGravity(true);
    }

    /** Hover point over (x, z): ground height plus the hover altitude. */
    public static Vec3 hoverAbove(ServerLevel sl, double x, double z) {
        BlockPos bp = BlockPos.containing(x, 0, z);
        int gy = sl.getHeight(Heightmap.Types.MOTION_BLOCKING, bp.getX(), bp.getZ());
        return new Vec3(x, gy + HOVER_ALT, z);
    }

    /** Summon: the rift opens at the point and the ship comes out of it, then waits there on HOLD. */
    public void summon(Vec3 at) {
        this.riftPos = at;
        this.setPos(at.x, at.y, at.z);
        this.goal = at;
        this.entityData.set(DATA_RIFT, RIFT_TICKS);
        this.entityData.set(DATA_ORDER, Order.HOLD.ordinal());
    }

    public void command(Order o, Vec3 point) {
        if (this.riftProgressTicks() > 0) return;
        this.entityData.set(DATA_ORDER, o.ordinal());
        if (o == Order.RECALL) {
            this.goal = this.riftPos;
        } else if (point != null) {
            this.goal = point;
        }
        if (o == Order.SHELL_RAIN) {
            this.rounds = RAIN_ROUNDS;
            this.cool = 0;
        }
    }

    public Order order() {
        return Order.values()[Mth.clamp(this.entityData.get(DATA_ORDER), 0, Order.values().length - 1)];
    }

    /** Ticks until the rift is fully open (0 once the ship is out). */
    public int riftProgressTicks() {
        return this.entityData.get(DATA_RIFT);
    }

    public int roundsLeft() {
        return this.rounds;
    }

    @Override
    protected void defineSynchedData() {
        this.entityData.define(DATA_ORDER, Order.HOLD.ordinal());
        this.entityData.define(DATA_RIFT, 0);
    }

    @Override
    public void tick() {
        super.tick();
        if (this.level().isClientSide) return;
        ServerLevel sl = (ServerLevel) this.level();
        int rift = this.riftProgressTicks();
        if (rift > 0) {
            this.entityData.set(DATA_RIFT, rift - 1);
            if (this.tickCount % 2 == 0) {
                sl.sendParticles(ParticleTypes.PORTAL, this.riftPos.x, this.riftPos.y, this.riftPos.z, 20, 6, 6, 6, 0.5);
            }
            return;
        }
        Vec3 p = this.position();
        if (this.goal != null) {
            Vec3 d = this.goal.subtract(p);
            double dist = d.length();
            if (dist > 0.5) {
                Vec3 step = dist <= SPEED ? d : d.normalize().scale(SPEED);
                this.setPos(p.x + step.x, p.y + step.y, p.z + step.z);
            }
        }
        this.setDeltaMovement(Vec3.ZERO);
        boolean reached = this.goal == null || this.position().distanceTo(this.goal) < 1.0;
        switch (this.order()) {
            case HOLD -> { }
            case MOVE -> {
                if (reached) this.entityData.set(DATA_ORDER, Order.HOLD.ordinal());
            }
            case SHELL_RAIN -> {
                if (reached && this.rounds > 0 && --this.cool <= 0) {
                    fireVolley(sl);
                    this.cool = RAIN_PERIOD;
                }
                if (this.rounds <= 0) this.entityData.set(DATA_ORDER, Order.HOLD.ordinal());
            }
            case RECALL -> {
                if (reached) {
                    sl.sendParticles(ParticleTypes.PORTAL, this.position().x, this.position().y, this.position().z, 60, 6, 6, 6, 0.6);
                    this.discard();
                }
            }
        }
    }

    /** Every gun fires straight down on a random point of the area: shells start high over it and fall. */
    private void fireVolley(ServerLevel sl) {
        Vec3 c = this.goal;
        for (int i = 0; i < RAIN_PER_VOLLEY && this.rounds > 0; i++, this.rounds--) {
            double a = this.random.nextDouble() * Math.PI * 2;
            double r = RAIN_RADIUS * Math.sqrt(this.random.nextDouble());
            double x = c.x + Math.cos(a) * r;
            double z = c.z + Math.sin(a) * r;
            Vec3 muzzle = new Vec3(x, this.getY() - 3.0, z);
            Vec3 dir = new Vec3((this.random.nextDouble() - 0.5) * 0.02, -1.0, (this.random.nextDouble() - 0.5) * 0.02).normalize();
            ShellEntity.fire(sl, Ballistics.Profile.MSTA_HE, muzzle, dir, -1);
        }
    }

    @Override
    public boolean hurt(DamageSource source, float amount) {
        return false;
    }

    @Override
    public boolean isPickable() {
        return false;
    }

    @Override
    public boolean isPushable() {
        return false;
    }

    @Override
    public boolean canBeCollidedWith() {
        return false;
    }

    @Override
    protected void readAdditionalSaveData(CompoundTag tag) {
        this.entityData.set(DATA_ORDER, tag.getInt("order"));
        this.entityData.set(DATA_RIFT, tag.getInt("rift"));
        this.rounds = tag.getInt("rounds");
        this.cool = tag.getInt("cool");
        if (tag.contains("gx")) this.goal = new Vec3(tag.getDouble("gx"), tag.getDouble("gy"), tag.getDouble("gz"));
        this.riftPos = new Vec3(tag.getDouble("rx"), tag.getDouble("ry"), tag.getDouble("rz"));
    }

    @Override
    protected void addAdditionalSaveData(CompoundTag tag) {
        tag.putInt("order", this.entityData.get(DATA_ORDER));
        tag.putInt("rift", this.riftProgressTicks());
        tag.putInt("rounds", this.rounds);
        tag.putInt("cool", this.cool);
        if (this.goal != null) {
            tag.putDouble("gx", this.goal.x);
            tag.putDouble("gy", this.goal.y);
            tag.putDouble("gz", this.goal.z);
        }
        tag.putDouble("rx", this.riftPos.x);
        tag.putDouble("ry", this.riftPos.y);
        tag.putDouble("rz", this.riftPos.z);
    }

    @Override
    public Packet<ClientGamePacketListener> getAddEntityPacket() {
        return NetworkHooks.getEntitySpawningPacket(this);
    }
}
