package ru.aiforge.realwar.sanctuary;

import java.util.UUID;
import net.minecraft.network.chat.Component;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.world.InteractionHand;
import net.minecraft.world.InteractionResultHolder;
import net.minecraft.world.entity.Entity;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.item.Item;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.level.Level;
import net.minecraft.world.phys.BlockHitResult;
import net.minecraft.world.phys.HitResult;
import net.minecraft.world.phys.Vec3;
import ru.aiforge.realwar.craft.CraftRegistry;

/**
 * Remote for Sanctuary II (r31).
 * - Right click on a point: the first use opens a rift there and the ship comes out; later uses send it to the point
 *   with the current order.
 * - Shift + right click: cycle the order (hold, advance, shell rain, recall).
 * The ship is linked by UUID in the stack's NBT.
 */
public class SanctuaryRemoteItem extends Item {
    public static final String TAG_SHIP = "ship";
    public static final String TAG_ORDER = "order";
    private static final double RANGE = 300.0;

    public SanctuaryRemoteItem(Item.Properties props) {
        super(props);
    }

    @Override
    public InteractionResultHolder<ItemStack> use(Level level, Player player, InteractionHand hand) {
        ItemStack st = player.getItemInHand(hand);
        if (level.isClientSide || !(level instanceof ServerLevel sl)) {
            return InteractionResultHolder.success(st);
        }
        var tag = st.getOrCreateTag();
        int order = tag.getInt(TAG_ORDER);
        if (player.isShiftKeyDown()) {
            order = (order + 1) % SanctuaryEntity.Order.values().length;
            tag.putInt(TAG_ORDER, order);
            player.displayClientMessage(Component.translatable("order.aiarsenal.sanctuary." + SanctuaryEntity.Order.values()[order].name().toLowerCase()), true);
            return InteractionResultHolder.success(st);
        }
        Vec3 point = pointOf(player, sl);
        SanctuaryEntity ship = linked(sl, tag);
        if (ship == null) {
            ship = CraftRegistry.SANCTUARY.get().create(sl);
            if (ship == null) return InteractionResultHolder.fail(st);
            Vec3 at = SanctuaryEntity.hoverAbove(sl, point.x, point.z);
            ship.summon(at);
            sl.addFreshEntity(ship);
            tag.putUUID(TAG_SHIP, ship.getUUID());
            player.displayClientMessage(Component.translatable("msg.aiarsenal.sanctuary.rift"), true);
        } else {
            SanctuaryEntity.Order o = SanctuaryEntity.Order.values()[order];
            ship.command(o, o == SanctuaryEntity.Order.RECALL ? null : SanctuaryEntity.hoverAbove(sl, point.x, point.z));
            player.displayClientMessage(Component.translatable("order.aiarsenal.sanctuary." + o.name().toLowerCase()), true);
        }
        return InteractionResultHolder.success(st);
    }

    private static SanctuaryEntity linked(ServerLevel sl, net.minecraft.nbt.CompoundTag tag) {
        if (!tag.hasUUID(TAG_SHIP)) return null;
        UUID id = tag.getUUID(TAG_SHIP);
        Entity e = sl.getEntity(id);
        return e instanceof SanctuaryEntity s && s.isAlive() ? s : null;
    }

    /** The block the player looks at, or a point 120 m ahead on the ground when looking at the sky. */
    private static Vec3 pointOf(Player player, ServerLevel sl) {
        HitResult hit = player.pick(RANGE, 0f, false);
        if (hit instanceof BlockHitResult b && hit.getType() == HitResult.Type.BLOCK) {
            return b.getLocation();
        }
        Vec3 ahead = player.getEyePosition().add(player.getLookAngle().scale(120.0));
        return new Vec3(ahead.x, 0, ahead.z);
    }
}
