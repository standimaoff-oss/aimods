package ru.aiforge.realwar.network;

import java.util.function.Supplier;
import net.minecraft.network.FriendlyByteBuf;
import net.minecraftforge.api.distmarker.Dist;
import net.minecraftforge.fml.DistExecutor;
import net.minecraftforge.network.NetworkEvent;
import ru.aiforge.realwar.client.ClientPackets;

/** r27: flash-bang result for one player: flash peak (0..1) and tinnitus length in ticks (0 = none). */
public record GrenadeFlashPacket(float peak, int tinnitusTicks) {
    public static void encode(GrenadeFlashPacket m, FriendlyByteBuf b) {
        b.writeFloat(m.peak);
        b.writeVarInt(m.tinnitusTicks);
    }

    public static GrenadeFlashPacket decode(FriendlyByteBuf b) {
        return new GrenadeFlashPacket(b.readFloat(), b.readVarInt());
    }

    public static void handle(GrenadeFlashPacket m, Supplier<NetworkEvent.Context> ctx) {
        ctx.get().enqueueWork(() -> DistExecutor.unsafeRunWhenOn((Dist) Dist.CLIENT, () -> () -> ClientPackets.flashbang(m)));
        ctx.get().setPacketHandled(true);
    }
}
