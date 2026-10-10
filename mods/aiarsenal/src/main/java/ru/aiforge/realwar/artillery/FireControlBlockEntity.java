package ru.aiforge.realwar.artillery;

import java.util.ArrayList;
import java.util.Comparator;
import java.util.List;
import java.util.UUID;

import net.minecraft.core.BlockPos;
import net.minecraft.nbt.CompoundTag;
import net.minecraft.nbt.ListTag;
import net.minecraft.network.protocol.Packet;
import net.minecraft.network.protocol.game.ClientboundBlockEntityDataPacket;
import net.minecraft.network.protocol.game.ClientGamePacketListener;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.world.entity.Entity;
import net.minecraft.world.level.block.entity.BlockEntity;
import net.minecraft.world.level.block.state.BlockState;
import net.minecraft.world.phys.AABB;
import net.minecraft.world.phys.Vec3;
import ru.aiforge.realwar.registry.ModBlockEntities;
import ru.aiforge.realwar.vehicle.LauncherVehicle;
import ru.aiforge.realwar.vehicle.LauncherVehicle.MissionState;

/**
 * r28: state and logic of the artillery fire-control point. Linked batteries (field guns and MLRS) get the aim point
 * of every round from the mission rules in {@link FireMission}; the vehicle itself slews, waits for reload and fires.
 */
public class FireControlBlockEntity extends BlockEntity {

    /** One linked battery; {@code left} is the rounds still to fire in the current mission. */
    public static final class Bat {
        public final UUID id;
        public int left;
        public String st = "";
        boolean aimed;

        Bat(UUID id) {
            this.id = id;
        }
    }

    private final List<Bat> bats = new ArrayList<>();
    private FireMission.Mode mode = FireMission.Mode.COORD;
    private FireMission.Mode runMode = FireMission.Mode.COORD;
    private int rounds = 2;
    private int squareIdx = 1;
    private double tx;
    private double tz;
    private boolean hasTarget;
    private boolean active;
    private String msg = "";

    // runtime only
    private UUID commander;
    private int stall;
    private int ticks;

    public static final int ACT_LINK = 0;
    public static final int ACT_UNLINK = 1;
    public static final int ACT_MODE = 2;
    public static final int ACT_ROUNDS = 3;
    public static final int ACT_SQUARE = 4;
    public static final int ACT_TARGET = 5;
    public static final int ACT_FIRE = 6;
    public static final int ACT_STOP = 7;
    public static final int ACT_ADJUST = 8;

    public FireControlBlockEntity(BlockPos pos, BlockState state) {
        super(ModBlockEntities.FIRE_CONTROL.get(), pos, state);
    }

    // ------------------------------------------------------------------ accessors (screen)
    public List<Bat> batteries() {
        return bats;
    }

    public FireMission.Mode mode() {
        return mode;
    }

    public int rounds() {
        return rounds;
    }

    public int squareIdx() {
        return squareIdx;
    }

    public double tx() {
        return tx;
    }

    public double tz() {
        return tz;
    }

    public boolean hasTarget() {
        return hasTarget;
    }

    public boolean active() {
        return active;
    }

    public String msg() {
        return msg;
    }

    // ------------------------------------------------------------------ commands from the screen
    /** Server side of {@code FireControlPacket}. */
    public void handle(ServerPlayer p, int action, double a, double b, int i) {
        if (!(this.level instanceof ServerLevel sl)) {
            return;
        }
        switch (action) {
            case ACT_LINK -> this.link(sl);
            case ACT_UNLINK -> {
                this.stop(sl);
                this.releaseAll(sl);
                this.bats.clear();
                this.msg = "fdc.msg.unlinked";
            }
            case ACT_MODE -> this.mode = FireMission.Mode.byOrdinal(i);
            case ACT_ROUNDS -> this.rounds = Math.max(1, Math.min(FireMission.MAX_ROUNDS, i));
            case ACT_SQUARE -> this.squareIdx = Math.floorMod(i, FireMission.SQUARES.length);
            case ACT_TARGET -> {
                if (Double.isFinite(a) && Double.isFinite(b) && Math.abs(a) < 29999000 && Math.abs(b) < 29999000) {
                    this.tx = a;
                    this.tz = b;
                    this.hasTarget = true;
                    this.msg = "fdc.msg.target";
                }
            }
            case ACT_FIRE -> this.start(p, this.mode);
            case ACT_STOP -> this.stop(sl);
            case ACT_ADJUST -> {
                if (this.hasTarget && Double.isFinite(a) && Double.isFinite(b)) {
                    this.tx += a;
                    this.tz += b;
                    this.start(p, FireMission.Mode.ADJUST);
                }
            }
            default -> {
            }
        }
        this.setChanged();
        this.sync(sl);
    }

    /** r28: links every artillery battery of the right kind near the point (nearest first, at most 8). */
    private void link(ServerLevel sl) {
        AABB box = new AABB(this.worldPosition).inflate(FireMission.LINK_RADIUS);
        Vec3 c = Vec3.atCenterOf(this.worldPosition);
        List<LauncherVehicle> found = sl.getEntitiesOfClass(LauncherVehicle.class, box,
                v -> v.missionCapable() && !v.isRemoved());
        found.sort(Comparator.comparingDouble(v -> v.distanceToSqr(c)));
        int added = 0;
        for (LauncherVehicle v : found) {
            if (this.bats.size() >= FireMission.MAX_BATTERIES) break;
            boolean known = false;
            for (Bat b : this.bats) {
                if (b.id.equals(v.getUUID())) known = true;
            }
            if (known) continue;
            this.bats.add(new Bat(v.getUUID()));
            added++;
        }
        this.msg = added > 0 ? "fdc.msg.linked" : (this.bats.isEmpty() ? "fdc.msg.nolink" : "fdc.msg.linked_none");
    }

    /** Starts a mission in the given mode; every battery gets its rounds and waits for its own aim and reload. */
    private void start(ServerPlayer p, FireMission.Mode m) {
        if (!(this.level instanceof ServerLevel sl)) {
            return;
        }
        if (this.bats.isEmpty()) {
            this.msg = "fdc.msg.nolink";
            return;
        }
        if (!this.hasTarget) {
            this.msg = "fdc.msg.notarget";
            return;
        }
        this.commander = p.getUUID();
        this.runMode = m;
        this.active = true;
        this.stall = 0;
        this.msg = "fdc.msg.started";
        int n = FireMission.roundsFor(m, this.rounds);
        for (Bat b : this.bats) {
            b.left = n;
            b.aimed = false;
            b.st = "PREP";
        }
        this.serverTick(sl);
    }

    private void stop(ServerLevel sl) {
        if (this.active) {
            this.active = false;
            this.msg = "fdc.msg.stopped";
        }
        this.releaseAll(sl);
        for (Bat b : this.bats) {
            b.left = 0;
            b.aimed = false;
        }
    }

    private void releaseAll(ServerLevel sl) {
        for (Bat b : this.bats) {
            Entity e = sl.getEntity(b.id);
            if (e instanceof LauncherVehicle lv) {
                lv.missionRelease();
            }
        }
    }

    // ------------------------------------------------------------------ server tick
    public void serverTick(ServerLevel sl) {
        if (!this.active) {
            return;
        }
        this.ticks++;
        ServerPlayer cmd = this.commander == null ? null : sl.getServer().getPlayerList().getPlayer(this.commander);
        boolean supplied = cmd != null && cmd.level() == sl && cmd.distanceToSqr(Vec3.atCenterOf(this.worldPosition)) <= 16.0 * 16.0;

        int n = this.bats.size();
        LauncherVehicle[] vs = new LauncherVehicle[n];
        MissionState[] st = new MissionState[n];
        boolean possible = false;
        boolean allDone = true;
        boolean allReady = true;

        // pass 1: find batteries, aim them at their next round, read their readiness
        for (int i = 0; i < n; i++) {
            Bat b = this.bats.get(i);
            Entity e = sl.getEntity(b.id);
            if (!(e instanceof LauncherVehicle)) {
                b.st = "LOST";
                continue;
            }
            LauncherVehicle lv = (LauncherVehicle) e;
            if (!lv.missionCapable() || lv.isRemoved()) {
                b.st = "LOST";
                continue;
            }
            vs[i] = lv;
            if (b.left <= 0) {
                b.st = "DONE";
                lv.missionRelease();
                continue;
            }
            allDone = false;
            if (supplied) lv.missionSupply(cmd);
            MissionState s = lv.missionReady();
            if (s == MissionState.DEAD) {
                b.st = "DEAD";
                b.left = 0;
                lv.missionRelease();
                continue;
            }
            if (FireMission.distXZ(lv.getX(), lv.getZ(), this.tx, this.tz) > lv.missionReachM()) {
                b.st = "RANGE";
                lv.missionRelease();
                continue;
            }
            possible = true;
            if (!b.aimed) {
                Vec3 p = FireMission.shotPoint(this.runMode, this.tx, this.tz, FireMission.square(this.squareIdx), sl.random);
                lv.missionAim(p);
                b.aimed = true;
            }
            s = lv.missionReady();
            st[i] = s;
            b.st = s.name();
            if (s != MissionState.READY) allReady = false;
        }

        if (allDone) {
            this.finish(sl, "fdc.msg.done");
            return;
        }
        if (!possible) {
            this.finish(sl, "fdc.msg.nopossible");
            return;
        }

        // pass 2: fire. A salvo waits until every battery with rounds left is ready, then all fire in one tick.
        boolean fired = false;
        boolean go = this.runMode != FireMission.Mode.SALVO || allReady;
        if (go) {
            for (int i = 0; i < n; i++) {
                Bat b = this.bats.get(i);
                LauncherVehicle lv = vs[i];
                if (lv == null || b.left <= 0 || st[i] != MissionState.READY) continue;
                if (lv.missionFire(sl) == MissionState.FIRED) {
                    b.left--;
                    b.aimed = false;
                    b.st = b.left > 0 ? "FIRED" : "DONE";
                    fired = true;
                }
            }
        }
        this.stall = fired ? 0 : this.stall + 1;
        if (this.stall > FireMission.STALL_TICKS) {
            this.finish(sl, "fdc.msg.stall");
            return;
        }
        if (this.ticks % 10 == 0) {
            this.sync(sl);
        }
    }

    private void finish(ServerLevel sl, String key) {
        this.active = false;
        this.msg = key;
        this.releaseAll(sl);
        for (Bat b : this.bats) {
            b.aimed = false;
        }
        this.setChanged();
        this.sync(sl);
    }

    /** Pushes the state to the clients that watch this block (screen refresh). */
    private void sync(ServerLevel sl) {
        BlockState s = this.getBlockState();
        sl.sendBlockUpdated(this.worldPosition, s, s, 3);
    }

    @Override
    public void setRemoved() {
        if (this.level instanceof ServerLevel sl) {
            this.releaseAll(sl);
        }
        super.setRemoved();
    }

    // ------------------------------------------------------------------ persistence and sync
    @Override
    protected void saveAdditional(CompoundTag tag) {
        super.saveAdditional(tag);
        ListTag list = new ListTag();
        for (Bat b : this.bats) {
            CompoundTag c = new CompoundTag();
            c.putUUID("u", b.id);
            c.putInt("l", b.left);
            c.putString("s", b.st);
            list.add(c);
        }
        tag.put("Bats", list);
        tag.putInt("Mode", this.mode.ordinal());
        tag.putInt("Rounds", this.rounds);
        tag.putInt("Sq", this.squareIdx);
        tag.putDouble("TX", this.tx);
        tag.putDouble("TZ", this.tz);
        tag.putBoolean("HasT", this.hasTarget);
        tag.putString("Msg", this.msg);
    }

    @Override
    public void load(CompoundTag tag) {
        super.load(tag);
        this.bats.clear();
        ListTag list = tag.getList("Bats", 10);
        for (int i = 0; i < list.size(); i++) {
            CompoundTag c = list.getCompound(i);
            Bat b = new Bat(c.getUUID("u"));
            b.left = c.getInt("l");
            b.st = c.getString("s");
            this.bats.add(b);
        }
        this.mode = FireMission.Mode.byOrdinal(tag.getInt("Mode"));
        this.rounds = Math.max(1, Math.min(FireMission.MAX_ROUNDS, tag.getInt("Rounds")));
        this.squareIdx = Math.floorMod(tag.getInt("Sq"), FireMission.SQUARES.length);
        this.tx = tag.getDouble("TX");
        this.tz = tag.getDouble("TZ");
        this.hasTarget = tag.getBoolean("HasT");
        this.msg = tag.getString("Msg");
        this.active = false;
    }

    @Override
    public Packet<ClientGamePacketListener> getUpdatePacket() {
        return ClientboundBlockEntityDataPacket.create(this);
    }
}
