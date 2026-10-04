package ru.aiforge.arsenal.network;

import net.minecraft.resources.ResourceLocation;
import net.minecraftforge.network.NetworkDirection;
import net.minecraftforge.network.NetworkRegistry;
import net.minecraftforge.network.simple.SimpleChannel;
import ru.aiforge.arsenal.AiArsenal;

/** Arsenal network channel (drones, launchers, detonator, nuclear effects). */
public final class ArsenalNetwork {
    private static final String PROTOCOL = "1";
    public static final SimpleChannel CHANNEL = NetworkRegistry.newSimpleChannel(
            ResourceLocation.fromNamespaceAndPath(AiArsenal.MODID, "arsenal"), () -> PROTOCOL, PROTOCOL::equals, PROTOCOL::equals);
    private static int id;

    private ArsenalNetwork() {
    }

    public static void register() {
        CHANNEL.messageBuilder(ControlPacket.class, id++, NetworkDirection.PLAY_TO_SERVER)
                .encoder(ControlPacket::encode).decoder(ControlPacket::decode).consumerMainThread(ControlPacket::handle).add();
        CHANNEL.messageBuilder(DesignatePacket.class, id++, NetworkDirection.PLAY_TO_SERVER)
                .encoder(DesignatePacket::encode).decoder(DesignatePacket::decode).consumerMainThread(DesignatePacket::handle).add();
        CHANNEL.messageBuilder(LauncherPacket.class, id++, NetworkDirection.PLAY_TO_SERVER)
                .encoder(LauncherPacket::encode).decoder(LauncherPacket::decode).consumerMainThread(LauncherPacket::handle).add();
        CHANNEL.messageBuilder(DetonatorPacket.class, id++, NetworkDirection.PLAY_TO_SERVER)
                .encoder(DetonatorPacket::encode).decoder(DetonatorPacket::decode).consumerMainThread(DetonatorPacket::handle).add();
        CHANNEL.messageBuilder(SessionPacket.class, id++, NetworkDirection.PLAY_TO_CLIENT)
                .encoder(SessionPacket::encode).decoder(SessionPacket::decode).consumerMainThread(SessionPacket::handle).add();
        CHANNEL.messageBuilder(NukeFxPacket.class, id++, NetworkDirection.PLAY_TO_CLIENT)
                .encoder(NukeFxPacket::encode).decoder(NukeFxPacket::decode).consumerMainThread(NukeFxPacket::handle).add();
        CHANNEL.messageBuilder(ChargeListPacket.class, id++, NetworkDirection.PLAY_TO_CLIENT)
                .encoder(ChargeListPacket::encode).decoder(ChargeListPacket::decode).consumerMainThread(ChargeListPacket::handle).add();
    }
}
