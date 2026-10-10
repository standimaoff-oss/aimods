/*
 * Decompiled with CFR 0.152.
 */
package ru.aiforge.realwar.client;

import ru.aiforge.realwar.client.ClientRadiation;
import ru.aiforge.realwar.client.fx.ClientBlastManager;
import ru.aiforge.realwar.client.fx.TrailFx;
import ru.aiforge.realwar.network.ConventionalEffectPacket;
import ru.aiforge.realwar.network.NukeEffectPacket;
import ru.aiforge.realwar.network.RadiationSyncPacket;
import ru.aiforge.realwar.network.TracerPacket;

public final class ClientPackets {
    private ClientPackets() {
    }

    public static void nuke(NukeEffectPacket m) {
        ClientBlastManager.startNuke(m);
    }

    public static void conventional(ConventionalEffectPacket m) {
        ClientBlastManager.startConv(m);
    }

    public static void tracer(TracerPacket m) {
        TrailFx.addTracer(m);
    }

    /** r27: flash-bang: white flash, camera jolt and a tinnitus ring for the local player. */
    public static void flashbang(ru.aiforge.realwar.network.GrenadeFlashPacket m) {
        net.minecraft.client.Minecraft mc = net.minecraft.client.Minecraft.getInstance();
        if (mc.level == null || mc.player == null) return;
        ClientBlastManager.flash(mc.level, m.peak());
        ClientBlastManager.shake(mc.level, 2.5f * m.peak(), 14.0f);
        if (m.tinnitusTicks() > 0) {
            mc.player.playSound(ru.aiforge.realwar.registry.ModSounds.TINNITUS.get(), 0.35f + 0.5f * m.peak(), 1.0f);
        }
    }

    public static void radiation(RadiationSyncPacket m) {
        ClientRadiation.set(m.rate(), m.dose());
    }
}

