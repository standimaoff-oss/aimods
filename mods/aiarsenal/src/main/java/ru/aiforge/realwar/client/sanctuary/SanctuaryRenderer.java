package ru.aiforge.realwar.client.sanctuary;

import com.mojang.blaze3d.vertex.PoseStack;
import com.mojang.math.Axis;
import net.minecraft.client.renderer.MultiBufferSource;
import net.minecraft.client.renderer.entity.EntityRenderer;
import net.minecraft.client.renderer.entity.EntityRendererProvider;
import net.minecraft.client.renderer.texture.OverlayTexture;
import net.minecraft.resources.ResourceLocation;
import ru.aiforge.realwar.client.render.GlbAssets;
import ru.aiforge.realwar.client.render.GlbRenderer;
import ru.aiforge.realwar.glb.Pose;
import ru.aiforge.realwar.sanctuary.SanctuaryEntity;

/** Sanctuary II: GLB model, grows out of the rift while the rift is open. */
public class SanctuaryRenderer extends EntityRenderer<SanctuaryEntity> {
    private static final ResourceLocation MODEL = new ResourceLocation("aiarsenal", "models/glb/sanctuary.glb");
    private static final ResourceLocation WHITE = new ResourceLocation("minecraft", "textures/misc/white.png");

    public SanctuaryRenderer(EntityRendererProvider.Context ctx) {
        super(ctx);
        this.shadowRadius = 0f;
    }

    @Override
    public void render(SanctuaryEntity e, float yaw, float pt, PoseStack ps, MultiBufferSource buf, int light) {
        GlbAssets.Loaded lm = GlbAssets.get(MODEL);
        if (lm == null) return;
        Pose pose = lm.scratch();
        pose.compute();
        ps.pushPose();
        float open = e.riftProgressTicks() > 0 ? 1f - e.riftProgressTicks() / (float) SanctuaryEntity.RIFT_TICKS : 1f;
        float s = Math.max(0.05f, open);
        ps.scale(s, s, s);
        ps.mulPose(Axis.YP.rotationDegrees(-e.getYRot()));
        GlbRenderer.render(lm, pose, ps, buf, light, OverlayTexture.NO_OVERLAY);
        ps.popPose();
        super.render(e, yaw, pt, ps, buf, light);
    }

    @Override
    public ResourceLocation getTextureLocation(SanctuaryEntity e) {
        return WHITE;
    }
}
