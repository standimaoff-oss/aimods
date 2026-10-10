package ru.aiforge.realwar.client.artillery;

import net.minecraft.client.Minecraft;
import net.minecraft.core.BlockPos;

/** r28: client entry point that opens the fire-control screen of a block (called only on the client). */
public final class FireControlClient {
    private FireControlClient() {
    }

    public static void open(BlockPos pos) {
        Minecraft.getInstance().setScreen(new FireControlScreen(pos));
    }
}
