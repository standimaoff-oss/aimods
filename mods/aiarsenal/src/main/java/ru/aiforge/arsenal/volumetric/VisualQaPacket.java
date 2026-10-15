package ru.aiforge.arsenal.volumetric;

import java.util.Set;
import java.util.function.Supplier;
import net.minecraft.network.FriendlyByteBuf;
import net.minecraftforge.api.distmarker.Dist;
import net.minecraftforge.fml.DistExecutor;
import net.minecraftforge.network.NetworkEvent;

/** Non-destructive QA bridge. Only a client explicitly launched with
 * -Daiarsenal.visualQa=true accepts it. Normal player clients ignore it,
 * including attempts to change their local renderer settings. */
public record VisualQaPacket(String effect) {
    public static final Set<String> EFFECTS = Set.of("smoke", "blast", "nuke", "trail",
            "clear", "status", "budget", "off", "on", "view_fov90", "view_fov70",
            "view_scale3", "view_scale2", "view_reload", "view_tabs", "view_modern");

    public void encode(FriendlyByteBuf buf) { buf.writeUtf(effect, 16); }
    public static VisualQaPacket decode(FriendlyByteBuf buf) { return new VisualQaPacket(buf.readUtf(16)); }

    public void handle(Supplier<NetworkEvent.Context> context) {
        if (Boolean.getBoolean("aiarsenal.visualQa") && EFFECTS.contains(effect)) {
            DistExecutor.unsafeRunWhenOn(Dist.CLIENT, () -> () ->
                    ru.aiforge.arsenal.volumetric.client.VolumetricEffects.runVisualQa(effect));
        }
        context.get().setPacketHandled(true);
    }
}
