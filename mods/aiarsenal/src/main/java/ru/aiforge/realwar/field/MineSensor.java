package ru.aiforge.realwar.field;

import java.util.List;
import net.minecraft.core.BlockPos;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.world.level.block.state.BlockState;
import net.minecraft.world.phys.AABB;
import net.minecraftforge.event.TickEvent;
import net.minecraftforge.eventbus.api.SubscribeEvent;
import net.minecraftforge.fml.common.Mod;
import org.joml.Matrix4d;
import org.joml.Vector3d;
import ru.aiforge.realwar.damage.DamageState;
import ru.aiforge.realwar.damage.VehicleDamage;
import ru.aiforge.realwar.vehicle.VehicleEntity;

/**
 * r27: pressure sensor for vehicles. Driven vehicles move by setPos (no move()), so {@link MineBlock#entityInside} never
 * saw them and mines only worked against the hull box. Every server tick each vehicle's footprint is checked: an
 * armed PMN-2 / TM-62 under a track (or wheel) or under the hull goes off there, with the damage of the real charge.
 */
@Mod.EventBusSubscriber(modid = "aiarsenal")
public final class MineSensor {
    /** footprint codes besides TRACK_L / TRACK_R */
    public static final int NONE = -1, HULL = -2;

    private MineSensor() {
    }

    @SubscribeEvent
    public static void onLevelTick(TickEvent.LevelTickEvent e) {
        if (e.phase != TickEvent.Phase.END || !(e.level instanceof ServerLevel sl)) return;
        List<? extends VehicleEntity> vs = sl.getEntities(net.minecraft.world.level.entity.EntityTypeTest.forClass(VehicleEntity.class),
                v -> v.isAlive() && !v.dmg.dead());
        for (VehicleEntity v : vs) {
            AABB box = v.getBoundingBox().inflate(0.5, 0.3, 0.5);
            Matrix4d inv = new Matrix4d(v.bodyFrame()).invert();
            VehicleDamage.Geo g = VehicleDamage.geo(v);
            for (BlockPos p : BlockPos.betweenClosed(BlockPos.containing(box.minX, box.minY, box.minZ),
                    BlockPos.containing(box.maxX, box.maxY, box.maxZ))) {
                BlockState st = sl.getBlockState(p);
                if (!(st.getBlock() instanceof MineBlock mb) || !st.getValue(MineBlock.ARMED)) continue;
                if (mb.kind != MineBlock.Kind.PMN2 && mb.kind != MineBlock.Kind.TM62) continue;
                if (p.getY() > v.getY() + 0.5 || p.getY() < v.getY() - 1.5) continue;     // mine lies on the ground under it
                Vector3d l = inv.transformPosition(new Vector3d(p.getX() + 0.5, p.getY() + 0.1, p.getZ() + 0.5));
                int side = footprint(g, l);
                if (side == NONE) continue;
                mb.vehicleTrigger(sl, p, v, side);
            }
        }
    }

    /** Where a mine at hull-frame point l lies: under a track (tracked hulls), a wheel row (wheeled), the hull, or nowhere. */
    static int footprint(VehicleDamage.Geo g, Vector3d l) {
        double dx = Math.abs(l.x - g.cx()), dz = Math.abs(l.z - g.cz());
        if (dz > g.hz() + 0.3) return NONE;
        if (g.tracked()) {
            if (dx > g.hx() - g.trackW() && dx <= g.hx() + 0.3) return l.x > g.cx() ? DamageState.TRACK_L : DamageState.TRACK_R;
            if (dx <= g.hx() - g.trackW()) return HULL;
            return NONE;
        }
        if (dx > g.hx() * 0.55 && dx <= g.hx() + 0.3) return l.x > g.cx() ? DamageState.TRACK_L : DamageState.TRACK_R;   // wheel rows
        return dx <= g.hx() * 0.55 ? HULL : NONE;
    }
}
