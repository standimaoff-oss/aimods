package ru.aiforge.realwar.artillery;

import java.util.function.Supplier;

import net.minecraft.core.BlockPos;
import net.minecraft.network.FriendlyByteBuf;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.world.phys.Vec3;
import net.minecraftforge.network.NetworkEvent;

/** r28: client -> server command of the fire-control screen; the server re-checks distance and block type. */
public record FireControlPacket(BlockPos pos, int action, double a, double b, int i) {
    public static void encode(FireControlPacket m, FriendlyByteBuf buf) {
        buf.writeBlockPos(m.pos);
        buf.writeVarInt(m.action);
        buf.writeDouble(m.a);
        buf.writeDouble(m.b);
        buf.writeVarInt(m.i);
    }

    public static FireControlPacket decode(FriendlyByteBuf buf) {
        return new FireControlPacket(buf.readBlockPos(), buf.readVarInt(), buf.readDouble(), buf.readDouble(), buf.readVarInt());
    }

    public static void handle(FireControlPacket m, Supplier<NetworkEvent.Context> ctx) {
        ctx.get().enqueueWork(() -> {
            ServerPlayer p = ctx.get().getSender();
            if (p == null || m.pos == null) return;
            if (p.distanceToSqr(Vec3.atCenterOf(m.pos)) > 64.0) return;
            if (p.level().getBlockEntity(m.pos) instanceof FireControlBlockEntity be) {
                be.handle(p, m.action, m.a, m.b, m.i);
            }
        });
        ctx.get().setPacketHandled(true);
    }
}
