package ru.aiforge.realwar.client.render;

import net.minecraft.client.model.HumanoidModel;
import net.minecraft.world.entity.HumanoidArm;

/** One-arm firing stance. False is essential: vanilla must NOT pose the other arm like a crossbow. */
public final class PistolPose {
    private PistolPose() {}
    public static final HumanoidModel.ArmPose HOLD = HumanoidModel.ArmPose.create("AIARSENAL_PISTOL", false,
            (model, entity, arm) -> {
                var hand = arm == HumanoidArm.RIGHT ? model.rightArm : model.leftArm;
                hand.xRot = -(float)Math.PI / 2f + model.head.xRot;
                hand.yRot = model.head.yRot;
                hand.zRot = 0;
            });
}
