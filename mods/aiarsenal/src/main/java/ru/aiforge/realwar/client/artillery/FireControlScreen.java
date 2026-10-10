package ru.aiforge.realwar.client.artillery;

import java.util.Locale;

import net.minecraft.client.Minecraft;
import net.minecraft.client.gui.GuiGraphics;
import net.minecraft.client.gui.components.Button;
import net.minecraft.client.gui.components.EditBox;
import net.minecraft.client.gui.screens.Screen;
import net.minecraft.core.BlockPos;
import net.minecraft.network.chat.Component;
import net.minecraft.world.level.Level;
import net.minecraft.world.level.block.entity.BlockEntity;
import net.minecraft.world.phys.BlockHitResult;
import ru.aiforge.realwar.artillery.FireControlBlockEntity;
import ru.aiforge.realwar.artillery.FireControlPacket;
import ru.aiforge.realwar.artillery.FireMission;
import ru.aiforge.realwar.network.ModNetwork;

/**
 * r28: fire-control point screen. Battery list with live status, fire mode (coordinates / salvo / area / adjust),
 * rounds per gun, square size, target by coordinates or by the sight, fire, stop and adjustment steps of 50 m.
 */
public class FireControlScreen extends Screen {
    private static final int W = 300;
    private static final int H = 250;

    private final BlockPos pos;
    private EditBox boxX;
    private EditBox boxZ;
    private Button modeBtn;
    private Button squareBtn;
    private Button roundsBtn;
    private Button fireBtn;

    public FireControlScreen(BlockPos pos) {
        super(Component.translatable("screen.aiarsenal.fdc"));
        this.pos = pos;
    }

    private FireControlBlockEntity be() {
        Level l = this.minecraft == null ? null : this.minecraft.level;
        BlockEntity e = l == null ? null : l.getBlockEntity(this.pos);
        return e instanceof FireControlBlockEntity f ? f : null;
    }

    private void send(int action, double a, double b, int i) {
        ModNetwork.CHANNEL.sendToServer(new FireControlPacket(this.pos, action, a, b, i));
    }

    @Override
    protected void init() {
        int x0 = this.width / 2 - W / 2;
        int y0 = this.height / 2 - H / 2;
        int half = 146;
        // battery list is drawn at y0+20..y0+50
        this.addRenderableWidget(Button.builder(Component.translatable("gui.aiarsenal.rw.fdc.link"), b -> send(FireControlBlockEntity.ACT_LINK, 0, 0, 0))
                .bounds(x0 + 8, y0 + 58, half, 18).build());
        this.addRenderableWidget(Button.builder(Component.translatable("gui.aiarsenal.rw.fdc.unlink"), b -> send(FireControlBlockEntity.ACT_UNLINK, 0, 0, 0))
                .bounds(x0 + 146, y0 + 58, half, 18).build());

        this.modeBtn = this.addRenderableWidget(Button.builder(Component.empty(), b -> {
            FireControlBlockEntity f = be();
            FireMission.Mode next = f == null ? FireMission.Mode.COORD : f.mode().next();
            send(FireControlBlockEntity.ACT_MODE, 0, 0, next.ordinal());
        }).bounds(x0 + 8, y0 + 80, 180, 18).build());
        this.squareBtn = this.addRenderableWidget(Button.builder(Component.empty(), b -> {
            FireControlBlockEntity f = be();
            int next = FireMission.nextSquareIndex(f == null ? 1 : f.squareIdx());
            send(FireControlBlockEntity.ACT_SQUARE, 0, 0, next);
        }).bounds(x0 + 192, y0 + 80, 100, 18).build());
        this.roundsBtn = this.addRenderableWidget(Button.builder(Component.empty(), b -> {
            FireControlBlockEntity f = be();
            int n = f == null ? 2 : f.rounds();
            send(FireControlBlockEntity.ACT_ROUNDS, 0, 0, n >= FireMission.MAX_ROUNDS ? 1 : n + 1);
        }).bounds(x0 + 8, y0 + 102, 180, 18).build());

        this.boxX = new EditBox(this.font, x0 + 8, y0 + 124, 88, 18, Component.empty());
        this.boxZ = new EditBox(this.font, x0 + 100, y0 + 124, 88, 18, Component.empty());
        this.boxX.setMaxLength(12);
        this.boxZ.setMaxLength(12);
        this.addRenderableWidget(this.boxX);
        this.addRenderableWidget(this.boxZ);
        this.addRenderableWidget(Button.builder(Component.translatable("gui.aiarsenal.rw.fdc.setxy"), b -> {
            try {
                double x = Double.parseDouble(this.boxX.getValue().trim());
                double z = Double.parseDouble(this.boxZ.getValue().trim());
                send(FireControlBlockEntity.ACT_TARGET, x, z, 0);
            } catch (NumberFormatException ignored) {
                // not a number: keep the old point
            }
        }).bounds(x0 + 196, y0 + 124, 96, 18).build());
        this.addRenderableWidget(Button.builder(Component.translatable("gui.aiarsenal.rw.fdc.sight"), b -> {
            Minecraft mc = this.minecraft;
            if (mc != null && mc.hitResult instanceof BlockHitResult bh) {
                BlockPos p = bh.getBlockPos();
                send(FireControlBlockEntity.ACT_TARGET, p.getX() + 0.5, p.getZ() + 0.5, 0);
            }
        }).bounds(x0 + 8, y0 + 146, 284, 18).build());

        // adjustment steps of 50 m: north is -Z
        int ay = y0 + 168;
        this.addRenderableWidget(Button.builder(Component.translatable("gui.aiarsenal.rw.fdc.adj_n"), b -> send(FireControlBlockEntity.ACT_ADJUST, 0, -50, 0))
                .bounds(x0 + 8, ay, 70, 18).build());
        this.addRenderableWidget(Button.builder(Component.translatable("gui.aiarsenal.rw.fdc.adj_s"), b -> send(FireControlBlockEntity.ACT_ADJUST, 0, 50, 0))
                .bounds(x0 + 82, ay, 70, 18).build());
        this.addRenderableWidget(Button.builder(Component.translatable("gui.aiarsenal.rw.fdc.adj_w"), b -> send(FireControlBlockEntity.ACT_ADJUST, -50, 0, 0))
                .bounds(x0 + 156, ay, 66, 18).build());
        this.addRenderableWidget(Button.builder(Component.translatable("gui.aiarsenal.rw.fdc.adj_e"), b -> send(FireControlBlockEntity.ACT_ADJUST, 50, 0, 0))
                .bounds(x0 + 226, ay, 66, 18).build());

        this.fireBtn = this.addRenderableWidget(Button.builder(Component.translatable("gui.aiarsenal.rw.fdc.fire"), b -> send(FireControlBlockEntity.ACT_FIRE, 0, 0, 0))
                .bounds(x0 + 8, y0 + H - 24, 180, 20).build());
        this.addRenderableWidget(Button.builder(Component.translatable("gui.aiarsenal.rw.fdc.stop"), b -> send(FireControlBlockEntity.ACT_STOP, 0, 0, 0))
                .bounds(x0 + 192, y0 + H - 24, 50, 20).build());
        this.addRenderableWidget(Button.builder(Component.translatable("gui.cancel"), b -> this.onClose())
                .bounds(x0 + 246, y0 + H - 24, 46, 20).build());
    }

    @Override
    public boolean isPauseScreen() {
        return false;
    }

    @Override
    public void tick() {
        FireControlBlockEntity f = be();
        if (f == null) {
            this.onClose();
            return;
        }
        this.modeBtn.setMessage(Component.translatable("gui.aiarsenal.rw.fdc.mode",
                Component.translatable("gui.aiarsenal.rw.fdc.mode." + f.mode().name().toLowerCase(Locale.ROOT))));
        this.squareBtn.setMessage(Component.translatable("gui.aiarsenal.rw.fdc.square", FireMission.square(f.squareIdx())));
        this.roundsBtn.setMessage(Component.translatable("gui.aiarsenal.rw.fdc.rounds", f.rounds()));
        this.fireBtn.active = !f.active();
    }

    @Override
    public void render(GuiGraphics g, int mx, int my, float pt) {
        this.renderBackground(g);
        int x0 = this.width / 2 - W / 2;
        int y0 = this.height / 2 - H / 2;
        g.fill(x0, y0, x0 + W, y0 + H, 0xE0101418);
        g.fill(x0, y0, x0 + W, y0 + 1, 0xFFE8C46A);
        g.drawString(this.font, this.title, x0 + 8, y0 + 6, 0xFFE8C46A, false);

        FireControlBlockEntity f = be();
        if (f != null) {
            int y = y0 + 20;
            if (f.batteries().isEmpty()) {
                g.drawString(this.font, Component.translatable("gui.aiarsenal.rw.fdc.none"), x0 + 8, y, 0xFF9098A0, false);
            } else {
                for (FireControlBlockEntity.Bat bt : f.batteries()) {
                    if (y >= y0 + 52) break;
                    Component st = Component.translatable("gui.aiarsenal.rw.fdc.st." + (bt.st.isEmpty() ? "prep" : bt.st.toLowerCase(Locale.ROOT)));
                    g.drawString(this.font, Component.translatable("gui.aiarsenal.rw.fdc.bat", bt.id.toString().substring(0, 4), st, bt.left),
                            x0 + 8, y, 0xFFB8C0C8, false);
                    y += 10;
                }
            }
            Component tgt = f.hasTarget()
                    ? Component.translatable("gui.aiarsenal.rw.fdc.target", (int) f.tx(), (int) f.tz())
                    : Component.translatable("gui.aiarsenal.rw.fdc.target_none");
            g.drawString(this.font, tgt, x0 + 8, y0 + 196, f.hasTarget() ? 0xFFFFFFFF : 0xFF9098A0, false);
            String key = f.msg().isEmpty() ? "idle" : f.msg().replace("fdc.msg.", "");
            g.drawString(this.font, Component.translatable("gui.aiarsenal.rw.fdc.msg." + key), x0 + 8, y0 + 208, 0xFFE8C46A, false);
            g.drawString(this.font, Component.translatable("gui.aiarsenal.rw.fdc.hint"), x0 + 8, y0 + 220, 0xFF707880, false);
        }
        super.render(g, mx, my, pt);
    }
}
